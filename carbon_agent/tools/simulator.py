"""
What-If Scenario Simulation Engine.
Enables deterministic counterfactual simulations comparing modified lifestyle scenarios against baseline.
"""
from typing import Dict, Any
import copy
from carbon_agent.tools.carbon_calculator import calculate_carbon_footprint


def simulate_scenario(
    baseline_activity: Dict[str, Any],
    modifications: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Simulate impact of specific changes against a baseline activity configuration.
    
    Supported modifications:
    - transport_reduction_pct: float (0 - 100)
    - modal_shift_to_metro_pct: float (0 - 100)
    - switch_to_ev: bool
    - electricity_reduction_pct: float (0 - 100)
    - add_solar_kwh_month: float (>= 0)
    - new_diet_type: str (heavy_meat, medium_meat, pescatarian, vegetarian, vegan)
    - new_recycling_pct: float (0 - 100)
    - new_composting_pct: float (0 - 100)
    """
    baseline_calc = calculate_carbon_footprint(baseline_activity)
    baseline_total = baseline_calc["total_monthly_kg_co2e"]

    # Deep copy baseline to mutate into scenario
    scenario_activity = copy.deepcopy(baseline_activity)

    # 1. Transportation modifications
    trans = scenario_activity.setdefault("transportation", {})
    t_red_pct = float(modifications.get("transport_reduction_pct", 0.0) or 0.0)
    if t_red_pct > 0:
        multiplier = max(0.0, 1.0 - (t_red_pct / 100.0))
        for key in ["petrol_car_km", "diesel_car_km", "motorcycle_km"]:
            if key in trans:
                trans[key] = round(float(trans[key] or 0.0) * multiplier, 2)

    modal_shift_pct = float(modifications.get("modal_shift_to_metro_pct", 0.0) or 0.0)
    if modal_shift_pct > 0:
        shift_ratio = min(1.0, modal_shift_pct / 100.0)
        p_km = float(trans.get("petrol_car_km", 0.0) or 0.0)
        d_km = float(trans.get("diesel_car_km", 0.0) or 0.0)
        shifted_km = (p_km + d_km) * shift_ratio
        trans["petrol_car_km"] = round(p_km * (1.0 - shift_ratio), 2)
        trans["diesel_car_km"] = round(d_km * (1.0 - shift_ratio), 2)
        trans["train_km"] = round(float(trans.get("train_km", 0.0) or 0.0) + shifted_km, 2)

    if modifications.get("switch_to_ev", False):
        p_km = float(trans.get("petrol_car_km", 0.0) or 0.0)
        d_km = float(trans.get("diesel_car_km", 0.0) or 0.0)
        total_ice_km = p_km + d_km
        trans["petrol_car_km"] = 0.0
        trans["diesel_car_km"] = 0.0
        trans["electric_car_km"] = round(float(trans.get("electric_car_km", 0.0) or 0.0) + total_ice_km, 2)

    # 2. Electricity modifications
    elec = scenario_activity.setdefault("electricity", {})
    e_red_pct = float(modifications.get("electricity_reduction_pct", 0.0) or 0.0)
    if e_red_pct > 0:
        multiplier = max(0.0, 1.0 - (e_red_pct / 100.0))
        elec["consumption_kwh"] = round(float(elec.get("consumption_kwh", 0.0) or 0.0) * multiplier, 2)

    add_solar = float(modifications.get("add_solar_kwh_month", 0.0) or 0.0)
    if add_solar > 0:
        elec["solar_kwh"] = round(float(elec.get("solar_kwh", 0.0) or 0.0) + add_solar, 2)

    # 3. Diet modifications
    new_diet = modifications.get("new_diet_type")
    if new_diet:
        food = scenario_activity.setdefault("food", {})
        food["diet_type"] = str(new_diet).strip()

    # 4. Waste modifications
    waste = scenario_activity.setdefault("waste", {})
    if "new_recycling_pct" in modifications and modifications["new_recycling_pct"] is not None:
        waste["recycling_pct"] = float(modifications["new_recycling_pct"])
    if "new_composting_pct" in modifications and modifications["new_composting_pct"] is not None:
        waste["composting_pct"] = float(modifications["new_composting_pct"])

    # Calculate new footprint
    scenario_calc = calculate_carbon_footprint(scenario_activity)
    scenario_total = scenario_calc["total_monthly_kg_co2e"]

    abs_reduction = round(baseline_total - scenario_total, 2)
    pct_reduction = round((abs_reduction / baseline_total * 100.0), 1) if baseline_total > 0 else 0.0

    # Category deltas
    cat_deltas = {}
    for cat, base_val in baseline_calc["categories"].items():
        scen_val = scenario_calc["categories"].get(cat, 0.0)
        c_diff = round(base_val - scen_val, 2)
        c_pct = round((c_diff / base_val * 100.0), 1) if base_val > 0 else 0.0
        cat_deltas[cat] = {
            "baseline": base_val,
            "scenario": scen_val,
            "reduction_kg": c_diff,
            "pct_change": c_pct
        }

    return {
        "baseline_monthly_kg_co2e": baseline_total,
        "scenario_monthly_kg_co2e": scenario_total,
        "reduction_kg_co2e": abs_reduction,
        "reduction_pct": pct_reduction,
        "annualized_reduction_kg_co2e": round(abs_reduction * 12.0, 2),
        "category_deltas": cat_deltas,
        "modified_activity": scenario_activity,
        "scenario_calculation": scenario_calc
    }
