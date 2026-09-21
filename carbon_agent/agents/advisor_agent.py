"""
Agent 7: AI Carbon Advisor.
Tool-augmented conversational agent that interprets user queries,
executes deterministic Python tools for any numerical or simulation questions,
and presents grounded advice with full tool-calling transparency.
"""
import re
from typing import Dict, Any, List, Tuple
from carbon_agent.tools.carbon_calculator import calculate_carbon_footprint
from carbon_agent.tools.emission_factors import get_factor, load_emission_factors
from carbon_agent.tools.simulator import simulate_scenario
from carbon_agent.agents.analysis_agent import EmissionAnalysisAgent
from carbon_agent.agents.prediction_agent import MLPredictionAgent
from carbon_agent.agents.reduction_agent import ReductionPlanningAgent
from carbon_agent.tools.database_tools import get_user_history


class CarbonAdvisorAgent:
    """
    Intelligent conversational advisor with tool-calling capabilities.
    Strictly forbids hallucinating numerical calculations.
    """

    def __init__(self):
        self.name = "AI Carbon Advisor"
        self.analysis_agent = EmissionAnalysisAgent()
        self.prediction_agent = MLPredictionAgent()
        self.reduction_agent = ReductionPlanningAgent()

    def respond(
        self,
        query: str,
        user_state: Dict[str, Any],
        chat_history: List[Tuple[str, str]] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Processes user query, dispatches to tools, and synthesizes a verified answer.
        Returns:
            (response_text, tool_calls_executed)
        """
        query_clean = query.strip()
        query_lower = query_clean.lower()
        tool_calls: List[Dict[str, Any]] = []

        activity_data = user_state.get("normalized_activity_data") or user_state.get("raw_inputs") or {}
        carbon_results = user_state.get("carbon_results") or {}
        history = user_state.get("history") or []

        # If footprint hasn't been calculated yet, compute it deterministically
        if not carbon_results and activity_data:
            tool_calls.append({
                "tool": "calculate_carbon_footprint",
                "input": "user_state.normalized_activity_data",
                "reason": "Calculate baseline carbon footprint before answering question"
            })
            carbon_results = calculate_carbon_footprint(activity_data)
            user_state["carbon_results"] = carbon_results

        # 1. "What happens if I reduce electricity/car by X%" (What-If Simulation)
        scenario_match = re.search(r'what\s*happens\s*if\s*i\s*reduce\s*(?:my\s*)?(\w+)\s*(?:by|to)?\s*(\d+(?:\.\d+)?)\s*%', query_lower)
        if scenario_match or "what if" in query_lower or "simulate" in query_lower:
            target_area = scenario_match.group(1) if scenario_match else ""
            pct_val = float(scenario_match.group(2)) if scenario_match else 20.0

            mods = {}
            if "elec" in target_area or "power" in target_area:
                mods["electricity_reduction_pct"] = pct_val
            elif "car" in target_area or "transport" in target_area or "drive" in target_area:
                mods["transport_reduction_pct"] = pct_val
            else:
                # Check for other keywords
                if "electricity" in query_lower:
                    mods["electricity_reduction_pct"] = pct_val
                elif "car" in query_lower or "transport" in query_lower:
                    mods["transport_reduction_pct"] = pct_val
                elif "diet" in query_lower or "meat" in query_lower:
                    mods["new_diet_type"] = "vegetarian"
                elif "solar" in query_lower:
                    mods["add_solar_kwh_month"] = 150.0
                else:
                    mods["electricity_reduction_pct"] = 20.0

            tool_calls.append({
                "tool": "simulate_scenario",
                "input": {"baseline_activity": "current", "modifications": mods},
                "reason": "Compute deterministic counterfactual scenario"
            })
            sim_res = simulate_scenario(activity_data, mods)

            resp = (
                f"### 🧪 Deterministic What-If Simulation Result\n\n"
                f"* **Current Baseline Footprint:** {sim_res['baseline_monthly_kg_co2e']:.2f} kg CO₂e/month\n"
                f"* **Simulated Scenario Footprint:** {sim_res['scenario_monthly_kg_co2e']:.2f} kg CO₂e/month\n"
                f"* **Calculated Monthly Reduction:** **{sim_res['reduction_kg_co2e']:.2f} kg CO₂e/month** "
                f"(*{sim_res['reduction_pct']}% reduction*)\n"
                f"* **Projected Annual Impact:** **{sim_res['annualized_reduction_kg_co2e']:.2f} kg CO₂e saved per year**\n\n"
                f"**Category Breakdown Impact:**\n"
            )
            for cat, details in sim_res["category_deltas"].items():
                if details["reduction_kg"] != 0:
                    resp += f"- **{cat.replace('_', ' ').title()}:** {details['baseline']:.1f} → {details['scenario']:.1f} kg CO₂e ({details['pct_change']}% change)\n"
            return resp, tool_calls

        # 2. "Why is my carbon footprint high?" / "Explain my carbon footprint"
        if any(w in query_lower for w in ["why", "high", "explain", "breakdown", "hotspot", "largest", "contributes the most", "contribute"]):
            tool_calls.append({
                "tool": "analyze_emissions",
                "input": {"carbon_results": "current", "historical_records": len(history)},
                "reason": "Identify dominant categories, percentages, and benchmark variances"
            })
            analysis = self.analysis_agent.analyze(carbon_results, history)

            total = analysis["total_monthly_kg_co2e"]
            dom_cat = analysis["dominant_category"]
            dom_pct = analysis["dominant_category_percentage"]
            bench = analysis["benchmarks"]

            resp = (
                f"### 📊 Diagnostic Analysis of Your Carbon Footprint\n\n"
                f"Your total footprint is **{total:.2f} kg CO₂e/month** (**{analysis['annualized_kg_co2e']:.2f} kg CO₂e/year**).\n\n"
                f"#### 🔍 Key Findings:\n"
                f"1. **Primary Driver:** **{dom_cat.replace('_', ' ').title()}** is your single largest contributor, representing **{dom_pct}%** of your total emissions.\n"
                f"2. **Benchmark Comparison:**\n"
                f"   - Compared to the **India National Average** (~{bench['india_average_monthly']} kg/mo), your emissions are "
                f"{'+' if bench['india_comparison_pct'] >= 0 else ''}{bench['india_comparison_pct']}%.\n"
                f"   - Compared to the **Global Per-Capita Average** (~{bench['global_average_monthly']} kg/mo), your emissions are "
                f"{'+' if bench['global_comparison_pct'] >= 0 else ''}{bench['global_comparison_pct']}%.\n\n"
                f"#### 💡 Why This Category Matters:\n"
            )
            for insight in analysis["insights"]:
                resp += f"{insight}\n\n"

            resp += "👉 *Recommendation: Check the **AI Reduction Planner** tab to generate a custom roadmap targeting this category.*"
            return resp, tool_calls

        # 3. "What is my predicted emission next month?" / "Forecast"
        if any(w in query_lower for w in ["predict", "future", "forecast", "next month", "trend"]):
            tool_calls.append({
                "tool": "predict_future_emissions",
                "input": {"activity_data": "current", "carbon_results": "current"},
                "reason": "Execute machine learning inference across lag-1 and seasonal activity features"
            })
            pred = self.prediction_agent.predict(activity_data, carbon_results, history)

            pred_val = pred["predicted_next_month_kg_co2e"]
            model = pred["model_used"]
            r2 = pred["r2"]
            rmse = pred["rmse"]
            diff = pred["delta_from_current"]

            resp = (
                f"### 🤖 Machine Learning Emission Forecast\n\n"
                f"* **Predicted Next Month Emission:** **{pred_val:.2f} kg CO₂e**\n"
                f"* **Expected Change from Current:** **{'+' if diff >= 0 else ''}{diff:.2f} kg CO₂e** ({pred['pct_delta_from_current']}%)\n"
                f"* **ML Algorithm Selected:** `{model}` (Evaluation $R^2 = {r2:.4f}$, $RMSE = {rmse:.2f}$)\n"
                f"* **Confidence Tier:** {pred['confidence_tier']}\n\n"
                f"📌 *Methodology Note:* {pred['reliability_note']}"
            )
            return resp, tool_calls

        # 4. "How can I reduce..." / "What should I focus on first?" / "Action plan"
        if any(w in query_lower for w in ["how can i reduce", "reduce", "action", "focus on first", "plan", "strategy"]):
            target_pct = user_state.get("user_profile", {}).get("target_reduction_pct", 20.0)
            tool_calls.append({
                "tool": "generate_reduction_plan",
                "input": {"target_pct": target_pct, "constraints": "default"},
                "reason": "Evaluate action catalog and select mathematically optimal intervention bundle"
            })
            plan = self.reduction_agent.plan_reduction(carbon_results, activity_data, target_pct=target_pct)

            resp = (
                f"### 🎯 Tailored Emission Reduction Strategy (Target: {target_pct}%)\n\n"
                f"To achieve a **{target_pct}% reduction**, you need to cut **{plan['required_reduction_kg']:.2f} kg CO₂e/month**.\n"
                f"The agentic solver identified **{plan['actions_count']} high-impact actions** projected to save "
                f"**{plan['projected_savings_kg_co2e']:.2f} kg CO₂e/month**:\n\n"
            )
            for idx, act in enumerate(plan["actions"][:3], 1):
                resp += (
                    f"**{idx}. {act['title']}** ({act['category'].capitalize()})\n"
                    f"   - **Action:** {act['proposed_activity']}\n"
                    f"   - **Estimated Saving:** `{act['estimated_monthly_saving_kg_co2e']} kg CO₂e/mo`\n"
                    f"   - **Difficulty / Cost:** {act['difficulty']} | {act['cost_tier']}\n\n"
                )
            resp += f"🔍 *{plan['disclaimer']}*"
            return resp, tool_calls

        # 5. Emission Factor Queries (e.g. "What is the emission factor for petrol / electricity?")
        if "factor" in query_lower or "emission of" in query_lower or "intensity" in query_lower:
            factors = load_emission_factors()
            matched_key = None
            for k in factors.keys():
                words = k.split("_")
                if any(w in query_lower for w in words if len(w) > 3):
                    matched_key = k
                    break

            if matched_key:
                fact = factors[matched_key]
                tool_calls.append({
                    "tool": "get_emission_factor",
                    "input": matched_key,
                    "reason": "Lookup verified factor and provenance from SQLite"
                })
                resp = (
                    f"### 📑 Emission Factor Details (`{matched_key}`)\n\n"
                    f"* **Factor Value:** `{fact['emission_factor']} {fact['factor_unit']}`\n"
                    f"* **Category:** {fact['category'].capitalize()}\n"
                    f"* **Official Source:** {fact['source']} (Reference Year: {fact['reference_year']})\n"
                    f"* **Region:** {fact['region']}\n"
                    f"* **Methodological Notes:** {fact['notes']}"
                )
                return resp, tool_calls

        # Fallback to holistic summary
        tool_calls.append({
            "tool": "analyze_emissions",
            "input": "summary",
            "reason": "Provide overview of current state"
        })
        analysis = self.analysis_agent.analyze(carbon_results, history)
        resp = (
            f"### 🤖 Carbon Advisor Overview\n\n"
            f"Here is a summary of your active carbon profile:\n"
            f"- **Current Footprint:** {analysis['total_monthly_kg_co2e']:.2f} kg CO₂e/month ({analysis['annualized_kg_co2e']:.2f} kg CO₂e/year)\n"
            f"- **Top Hotspot:** {analysis['dominant_category'].replace('_', ' ').title()} ({analysis['dominant_category_percentage']}%)\n\n"
            f"You can ask me specific questions like:\n"
            f"- *'Why is my carbon footprint high?'*\n"
            f"- *'What happens if I reduce electricity consumption by 20%?'*\n"
            f"- *'What is my predicted emission next month?'*\n"
            f"- *'How can I reduce transportation emissions?'*"
        )
        return resp, tool_calls
