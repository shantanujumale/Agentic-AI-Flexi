"""
Tab 5: AI Reduction Planner Tab.
Formulates goal-driven, constraint-aware action plans using greedy hotspot prioritization.
"""
import gradio as gr
from typing import Dict, Any
from carbon_agent.agents.reduction_agent import ReductionPlanningAgent
from carbon_agent.tools.database_tools import save_user_action_plan

reduction_agent = ReductionPlanningAgent()


def render_planner_tab(state: gr.State):
    """Render components for the AI Reduction Planner tab."""
    gr.Markdown("### 🎯 AI Emission Reduction Planner")
    gr.Markdown(
        "Define an emission reduction target and declare your operational constraints. "
        "The **Reduction Planning Agent** mathematically prioritizes your largest hotspots and selects a feasible bundle of actions."
    )

    with gr.Row():
        with gr.Column(scale=2):
            target_slider = gr.Slider(
                label="Target Reduction Percentage (%)",
                minimum=10,
                maximum=50,
                value=20,
                step=5
            )
        with gr.Column(scale=1):
            diff_filter = gr.Dropdown(
                label="Maximum Difficulty",
                choices=["Easy", "Medium", "Hard"],
                value="Hard"
            )
        with gr.Column(scale=1):
            cost_filter = gr.Dropdown(
                label="Budget Constraint",
                choices=["Free", "Low", "Investment"],
                value="Investment"
            )

    with gr.Row():
        generate_plan_btn = gr.Button("🚀 Generate Personalized Action Plan", variant="primary", scale=3)
        save_plan_btn = gr.Button("💾 Save Plan to Profile", variant="secondary", scale=1)

    plan_summary_md = gr.Markdown("")
    plan_cards_md = gr.Markdown("")
    save_status_md = gr.Markdown(visible=False)

    def on_generate_plan(target_pct, max_diff, max_cost, current_state):
        current_state = current_state or {}
        carbon_res = current_state.get("carbon_results", {})
        activity_data = current_state.get("normalized_activity_data") or current_state.get("raw_inputs", {})

        if not carbon_res:
            return (
                "> [!WARNING]\n> No active calculation found. Please calculate your footprint in **Tab 1 — Carbon Calculator** first.",
                "",
                current_state
            )

        plan = reduction_agent.plan_reduction(
            current_footprint=carbon_res,
            activity_data=activity_data,
            target_pct=target_pct,
            max_difficulty=max_diff,
            max_cost_tier=max_cost
        )
        current_state["reduction_plan"] = plan

        base_val = plan["baseline_monthly_kg_co2e"]
        req_val = plan["required_reduction_kg"]
        proj_val = plan["projected_savings_kg_co2e"]
        ach_pct = plan["projected_reduction_pct"]
        is_met = plan["is_target_fully_met"]

        summary_box = (
            f"### 📋 Plan Feasibility & Target Alignment\n\n"
            f"- **Current Baseline:** `{base_val:.1f} kg CO₂e/month`\n"
            f"- **Reduction Target ({target_pct}%):** Cut `{req_val:.1f} kg CO₂e/month`\n"
            f"- **Projected Plan Savings:** **`{proj_val:.1f} kg CO₂e/month`** (*{ach_pct}% total reduction*)\n"
            f"- **Target Feasibility Status:** {'✅ **FULLY ACHIEVED**' if is_met else '⚠️ **PARTIALLY ACHIEVED** (expand constraints to hit 100%)'}\n"
            f"- **Annualized Carbon Savings:** **`{plan['projected_savings_annualized_kg_co2e']:.1f} kg CO₂e/year`**\n"
        )

        cards_box = "### 🛠️ Recommended Action Bundle\n\n"
        for idx, act in enumerate(plan["actions"], 1):
            cards_box += (
                f"#### {idx}. {act['title']} `[{act['category'].upper()}]`\n"
                f"- **Proposed Routine:** {act['proposed_activity']}\n"
                f"- **Baseline:** {act['baseline_activity']}\n"
                f"- **Estimated Monthly Reduction:** **`{act['estimated_monthly_saving_kg_co2e']} kg CO₂e/month`**\n"
                f"- **Difficulty / Cost Tier:** `{act['difficulty']}` | `{act['cost_tier']}`\n"
                f"- **Underlying Assumptions:** *{act['assumptions']}*\n\n"
                "---\n"
            )

        cards_box += f"\n> [!NOTE]\n> *{plan['disclaimer']}*"

        return summary_box, cards_box, current_state

    def on_save_plan(current_state):
        current_state = current_state or {}
        plan = current_state.get("reduction_plan")
        if not plan:
            return gr.update(value="⚠️ No plan generated yet. Generate a plan first.", visible=True)

        user_prof = current_state.get("user_profile", {})
        username = user_prof.get("username", "default_user")

        plan_id = save_user_action_plan(
            username=username,
            target_reduction_pct=plan["target_reduction_pct"],
            baseline_co2e=plan["baseline_monthly_kg_co2e"],
            target_co2e=plan["projected_monthly_kg_co2e"],
            projected_savings_kg=plan["projected_savings_kg_co2e"],
            plan_items=plan["actions"]
        )
        return gr.update(value=f"✅ Plan successfully saved to profile with ID #{plan_id}.", visible=True)

    generate_plan_btn.click(
        fn=on_generate_plan,
        inputs=[target_slider, diff_filter, cost_filter, state],
        outputs=[plan_summary_md, plan_cards_md, state]
    )

    save_plan_btn.click(
        fn=on_save_plan,
        inputs=[state],
        outputs=[save_status_md]
    )

    return generate_plan_btn
