"""
Agent 5: Reduction Planning Agent.
Builds personalized, constraint-aware action plans to meet user-defined reduction targets.
Calculates required reduction and bundles feasible actions using deterministic calculations.
"""
from typing import Dict, Any, List, Optional
from carbon_agent.tools.database_tools import get_all_reduction_actions
from carbon_agent.tools.carbon_calculator import get_factor_value


class ReductionPlanningAgent:
    """
    Formulates personalized, mathematically grounded emission reduction strategies.
    Ensures actions prioritize the user's primary emission categories and respect lifestyle constraints.
    """

    def __init__(self):
        self.name = "Reduction Planning Agent"

    def plan_reduction(
        self,
        current_footprint: Dict[str, Any],
        activity_data: Dict[str, Any],
        target_pct: float = 20.0,
        max_difficulty: str = "Hard",  # Easy, Medium, Hard
        max_cost_tier: str = "Investment"  # Free, Low, Investment
    ) -> Dict[str, Any]:
        """
        Generate a feasible action plan to achieve the target emission reduction percentage.
        """
        current_total = current_footprint.get("total_monthly_kg_co2e", 0.0)
        categories = current_footprint.get("categories", {})

        target_pct = float(target_pct)
        required_reduction_kg = round(current_total * (target_pct / 100.0), 2)
        target_co2e = round(max(0.0, current_total - required_reduction_kg), 2)

        difficulty_ranks = {"Easy": 1, "Medium": 2, "Hard": 3}
        cost_ranks = {"Free": 1, "Low": 2, "Investment": 3}

        allowed_diff_level = difficulty_ranks.get(max_difficulty, 3)
        allowed_cost_level = cost_ranks.get(max_cost_tier, 3)

        # Retrieve action catalog
        catalog = get_all_reduction_actions()

        # Sort categories by footprint size (hotspots first)
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

        evaluated_actions: List[Dict[str, Any]] = []

        # Quantify potential savings for each catalog action based on user's actual baseline
        for item in catalog:
            action_id = item["action_id"]
            cat = item["category"]
            cat_emissions = categories.get(cat, 0.0)

            # Skip if user has practically zero emissions in this category
            if cat_emissions <= 1.0:
                continue

            # Check user constraints
            item_diff = difficulty_ranks.get(item["difficulty"], 2)
            item_cost = cost_ranks.get(item["cost_tier"], 2)
            if item_diff > allowed_diff_level or item_cost > allowed_cost_level:
                continue

            # Deterministic estimate based on action formula
            est_reduction_kg = 0.0
            baseline_str = ""
            proposed_str = ""
            frequency_str = ""

            if action_id == "carpool_commute":
                p_km = float(activity_data.get("transportation", {}).get("petrol_car_km", 0.0) or 0.0)
                d_km = float(activity_data.get("transportation", {}).get("diesel_car_km", 0.0) or 0.0)
                car_km = p_km + d_km
                if car_km > 30:
                    saved_km = car_km * 0.30
                    factor = 0.1705 if p_km >= d_km else 0.1684
                    est_reduction_kg = round(saved_km * factor, 2)
                    baseline_str = f"Solo driving ~{car_km:.0f} km/month"
                    proposed_str = f"Carpool 3 days/wk to save ~{saved_km:.0f} vehicle-km/month"
                    frequency_str = "3 days per week"

            elif action_id == "modal_shift_metro_bus":
                p_km = float(activity_data.get("transportation", {}).get("petrol_car_km", 0.0) or 0.0)
                d_km = float(activity_data.get("transportation", {}).get("diesel_car_km", 0.0) or 0.0)
                car_km = p_km + d_km
                if car_km > 50:
                    shifted_km = car_km * 0.40
                    # Swap car emission (0.1705) for metro (0.035)
                    saved_rate = 0.1705 - 0.0350
                    est_reduction_kg = round(shifted_km * saved_rate, 2)
                    baseline_str = f"Private car commute: {car_km:.0f} km/month"
                    proposed_str = f"Shift {shifted_km:.0f} km/month to metro / rapid electric bus"
                    frequency_str = "Daily commute trips"

            elif action_id == "ev_transition":
                p_km = float(activity_data.get("transportation", {}).get("petrol_car_km", 0.0) or 0.0)
                d_km = float(activity_data.get("transportation", {}).get("diesel_car_km", 0.0) or 0.0)
                car_km = p_km + d_km
                if car_km > 100:
                    car_co2e = categories.get("transportation", 0.0)
                    est_reduction_kg = round(car_co2e * 0.60, 2)
                    baseline_str = f"ICE Car travel: {car_km:.0f} km/month"
                    proposed_str = "Switch to battery electric vehicle (BEV)"
                    frequency_str = "Permanent vehicle upgrade"

            elif action_id == "ac_thermostat_24c":
                elec_kwh = float(activity_data.get("electricity", {}).get("consumption_kwh", 0.0) or 0.0)
                if elec_kwh > 80:
                    saved_kwh = elec_kwh * 0.18
                    grid_factor = get_factor_value("electricity_grid", 0.82)
                    est_reduction_kg = round(saved_kwh * grid_factor, 2)
                    baseline_str = f"Current grid electricity: {elec_kwh:.0f} kWh/month"
                    proposed_str = f"Set AC thermostat to 24°C - 26°C (saves ~{saved_kwh:.0f} kWh/month)"
                    frequency_str = "Daily operational habit"

            elif action_id == "led_efficient_appliances":
                elec_kwh = float(activity_data.get("electricity", {}).get("consumption_kwh", 0.0) or 0.0)
                if elec_kwh > 50:
                    saved_kwh = elec_kwh * 0.12
                    grid_factor = get_factor_value("electricity_grid", 0.82)
                    est_reduction_kg = round(saved_kwh * grid_factor, 2)
                    baseline_str = f"Current electricity use: {elec_kwh:.0f} kWh/month"
                    proposed_str = f"Replace inefficient lights with 5-star LEDs (saves ~{saved_kwh:.0f} kWh)"
                    frequency_str = "Permanent appliance retrofit"

            elif action_id == "rooftop_solar_pv":
                elec_kwh = float(activity_data.get("electricity", {}).get("consumption_kwh", 0.0) or 0.0)
                if elec_kwh > 100:
                    solar_gen = elec_kwh * 0.65
                    # Net reduction = displaced grid (0.82) minus solar lifecycle (0.04) = 0.78 kg/kWh
                    est_reduction_kg = round(solar_gen * (0.8200 - 0.0400), 2)
                    baseline_str = f"100% grid power ({elec_kwh:.0f} kWh/month)"
                    proposed_str = f"Generate {solar_gen:.0f} kWh/month via 2 kW rooftop solar PV"
                    frequency_str = "Continuous generation"

            elif action_id == "dietary_flexitarian_shift":
                diet = str(activity_data.get("food", {}).get("diet_type", "vegetarian")).lower()
                if diet in ["heavy_meat", "medium_meat"]:
                    food_co2e = categories.get("food", 0.0)
                    est_reduction_kg = round(food_co2e * 0.25, 2)
                    baseline_str = f"Current diet: {diet.replace('_', ' ').title()}"
                    proposed_str = "Adopt 2-3 meatless plant-based days per week"
                    frequency_str = "3 days per week"

            elif action_id == "food_waste_prevention":
                food_co2e = categories.get("food", 0.0)
                if food_co2e > 20:
                    est_reduction_kg = round(food_co2e * 0.15, 2)
                    baseline_str = "Standard grocery and meal consumption"
                    proposed_str = "Portion planning and systematic leftover utilization"
                    frequency_str = "Ongoing weekly routine"

            elif action_id == "dry_waste_segregation_recycling":
                waste_kg = float(activity_data.get("waste", {}).get("waste_kg", 0.0) or 0.0)
                curr_rec = float(activity_data.get("waste", {}).get("recycling_pct", 0.0) or 0.0)
                if waste_kg > 5 and curr_rec < 80:
                    additional_recycle_kg = waste_kg * (0.70 - (curr_rec / 100.0))
                    if additional_recycle_kg > 0:
                        # Avoided landfill (0.586) + recycle credit (0.32) = 0.906 kg CO2e/kg
                        est_reduction_kg = round(additional_recycle_kg * 0.906, 2)
                        baseline_str = f"Recycling rate: {curr_rec:.0f}% of {waste_kg:.0f} kg waste"
                        proposed_str = "Segregate 70%+ of dry paper, cardboard, and plastic"
                        frequency_str = "Daily disposal habit"

            elif action_id == "home_composting_wet_waste":
                waste_kg = float(activity_data.get("waste", {}).get("waste_kg", 0.0) or 0.0)
                curr_comp = float(activity_data.get("waste", {}).get("composting_pct", 0.0) or 0.0)
                if waste_kg > 5 and curr_comp < 60:
                    additional_compost_kg = waste_kg * (0.50 - (curr_comp / 100.0))
                    if additional_compost_kg > 0:
                        est_reduction_kg = round(additional_compost_kg * (0.586 + 0.180), 2)
                        baseline_str = f"Composting rate: {curr_comp:.0f}%"
                        proposed_str = "Aerobic home/community composting of organic kitchen scraps"
                        frequency_str = "Daily kitchen composting"

            if est_reduction_kg > 0.5:
                evaluated_actions.append({
                    "action_id": action_id,
                    "title": item["title"],
                    "category": cat,
                    "baseline_activity": baseline_str,
                    "proposed_activity": proposed_str,
                    "estimated_monthly_saving_kg_co2e": est_reduction_kg,
                    "frequency": frequency_str,
                    "difficulty": item["difficulty"],
                    "cost_tier": item["cost_tier"],
                    "assumptions": item["assumptions"]
                })

        # Sort candidate actions by saving potential (greedy selection)
        evaluated_actions.sort(key=lambda x: x["estimated_monthly_saving_kg_co2e"], reverse=True)

        selected_plan: List[Dict[str, Any]] = []
        accumulated_savings = 0.0

        for act in evaluated_actions:
            selected_plan.append(act)
            accumulated_savings += act["estimated_monthly_saving_kg_co2e"]
            if accumulated_savings >= required_reduction_kg:
                break

        achieved_pct = round((accumulated_savings / current_total * 100.0), 1) if current_total > 0 else 0.0
        target_met = accumulated_savings >= required_reduction_kg

        return {
            "target_reduction_pct": target_pct,
            "required_reduction_kg": required_reduction_kg,
            "baseline_monthly_kg_co2e": current_total,
            "projected_monthly_kg_co2e": round(max(0.0, current_total - accumulated_savings), 2),
            "projected_savings_kg_co2e": round(accumulated_savings, 2),
            "projected_savings_annualized_kg_co2e": round(accumulated_savings * 12.0, 2),
            "projected_reduction_pct": achieved_pct,
            "is_target_fully_met": target_met,
            "actions_count": len(selected_plan),
            "actions": selected_plan,
            "disclaimer": (
                "Estimated savings are deterministic calculations based on specified behavioral models "
                "and certified emission factors. Actual reductions depend on consistent adoption and operational conditions."
            )
        }
