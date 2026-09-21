"""
Agent 3: Emission Analysis Agent.
Analyzes computed footprint, ranks categories, computes benchmarks,
and diagnoses key hotspots with traceable deterministic reasoning.
"""
from typing import Dict, Any, List
from carbon_agent.config.settings import BENCHMARKS


class EmissionAnalysisAgent:
    """
    Analyzes calculated carbon footprints, establishes category dominance,
    compares with national/global per-capita benchmarks, and pinpoints reduction priorities.
    """

    def __init__(self):
        self.name = "Emission Analysis Agent"

    def analyze(
        self,
        carbon_results: Dict[str, Any],
        historical_records: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Produce a diagnostic analysis of the carbon footprint.
        """
        total_monthly = carbon_results.get("total_monthly_kg_co2e", 0.0)
        annualized = carbon_results.get("annualized_kg_co2e", 0.0)
        categories = carbon_results.get("categories", {})
        percentages = carbon_results.get("breakdown_percentages", {})

        # 1. Identify dominant category (Hotspot)
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        dominant_cat, dominant_val = sorted_categories[0] if sorted_categories else ("none", 0.0)
        dominant_pct = percentages.get(dominant_cat, 0.0)

        # 2. Benchmark Comparisons
        india_monthly = BENCHMARKS["india_monthly_kg_co2e"]
        global_monthly = BENCHMARKS["global_monthly_kg_co2e"]
        paris_monthly = BENCHMARKS["paris_target_monthly_kg_co2e"]

        india_diff_pct = round(((total_monthly - india_monthly) / india_monthly) * 100.0, 1) if india_monthly else 0.0
        global_diff_pct = round(((total_monthly - global_monthly) / global_monthly) * 100.0, 1) if global_monthly else 0.0

        # 3. Longitudinal / Historical comparison if previous logs exist
        trend_summary = "No previous logs found for longitudinal trend analysis."
        delta_previous_month = None
        if historical_records and len(historical_records) > 0:
            prev_log = historical_records[-1]
            prev_total = prev_log.get("total_monthly_kg_co2e", 0.0)
            diff = round(total_monthly - prev_total, 2)
            pct_change = round((diff / prev_total * 100.0), 1) if prev_total > 0 else 0.0
            delta_previous_month = {
                "previous_total": prev_total,
                "difference_kg": diff,
                "percentage_change": pct_change
            }
            if diff > 0:
                trend_summary = f"Emissions increased by {diff:.1f} kg CO2e (+{pct_change}%) compared to last logged month ({prev_log.get('month_year')})."
            elif diff < 0:
                trend_summary = f"Emissions decreased by {abs(diff):.1f} kg CO2e ({pct_change}%) compared to last logged month ({prev_log.get('month_year')}). Good progress!"
            else:
                trend_summary = f"Emissions remained stable compared to last logged month ({prev_log.get('month_year')})."

        # 4. Generate domain-grounded diagnostic insights
        insights = []
        if dominant_cat == "transportation":
            insights.append(
                f"Transportation is your primary emission driver ({dominant_pct}% of total). "
                "Commuting with fossil-fuel internal combustion vehicles creates concentrated per-kilometer emissions. "
                "Prioritize carpooling, transitioning commute segments to metro/electric transit, or EV adoption."
            )
        elif dominant_cat == "electricity":
            insights.append(
                f"Electricity consumption is your primary emission driver ({dominant_pct}% of total). "
                "Because India's national grid has an intensity of ~0.82 kg CO2e/kWh (heavily coal-reliant), "
                "reducing air conditioning power or adopting rooftop solar yields exceptionally high carbon payback."
            )
        elif dominant_cat == "food":
            insights.append(
                f"Food and diet represents your largest footprint category ({dominant_pct}% of total). "
                "Animal agriculture produces substantial methane and requires significant feed conversion energy. "
                "Introducing plant-based days can swiftly reduce this category by 20-30%."
            )
        elif dominant_cat == "household_fuel":
            insights.append(
                f"Household fuel (LPG / PNG) is significant ({dominant_pct}% of total). "
                "Thermal cooking energy produces ~2.98 kg CO2e per kg of LPG. "
                "Induction cooking powered by clean electricity is an effective alternative."
            )
        elif dominant_cat == "waste":
            insights.append(
                f"Waste is responsible for {dominant_pct}% of your footprint. "
                "Organic waste in landfills generates potent anaerobic methane. "
                "Segregating dry waste and composting food scraps can almost eliminate this category."
            )

        return {
            "total_monthly_kg_co2e": total_monthly,
            "annualized_kg_co2e": annualized,
            "dominant_category": dominant_cat,
            "dominant_category_percentage": dominant_pct,
            "ranked_categories": sorted_categories,
            "benchmarks": {
                "india_average_monthly": round(india_monthly, 1),
                "india_comparison_pct": india_diff_pct,
                "global_average_monthly": round(global_monthly, 1),
                "global_comparison_pct": global_diff_pct,
                "paris_1_5c_target_monthly": round(paris_monthly, 1)
            },
            "historical_trend": trend_summary,
            "delta_previous_month": delta_previous_month,
            "insights": insights
        }
