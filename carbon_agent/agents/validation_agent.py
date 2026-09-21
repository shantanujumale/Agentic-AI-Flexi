"""
Agent 2: Data Validation Agent.
Validates numeric ranges, units, impossible physical values, and normalizes frequencies to standard monthly units.
"""
from typing import Dict, Any, List, Tuple
from carbon_agent.config.settings import VALIDATION_BOUNDS

DAYS_PER_MONTH = 30.4167
WEEKS_PER_MONTH = 4.3452


class ValidationAgent:
    """
    Validates physical feasibility and normalizes inputs to standard monthly units.
    """

    def __init__(self):
        self.name = "Data Validation Agent"

    def validate_and_normalize(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate activity data and normalize to monthly units.
        Returns:
            {
                "is_valid": bool,
                "normalized_data": dict,
                "warnings": list,
                "errors": list
            }
        """
        errors: List[str] = []
        warnings: List[str] = []
        normalized: Dict[str, Any] = {
            "transportation": {},
            "electricity": {},
            "household_fuel": {},
            "food": {},
            "waste": {}
        }

        # 1. Transportation Validation
        raw_trans = activity_data.get("transportation", {})
        if raw_trans:
            # Petrol car
            if "petrol_car_km" in raw_trans:
                val = float(raw_trans["petrol_car_km"] or 0.0)
                if val < 0:
                    errors.append("Petrol car distance cannot be negative.")
                elif val > 20000:
                    warnings.append(f"Petrol car travel of {val:.0f} km/month is unusually high (over 650 km/day).")
                normalized["transportation"]["petrol_car_km"] = max(0.0, val)

            # Diesel car
            if "diesel_car_km" in raw_trans:
                val = float(raw_trans["diesel_car_km"] or 0.0)
                if val < 0:
                    errors.append("Diesel car distance cannot be negative.")
                elif val > 20000:
                    warnings.append(f"Diesel car travel of {val:.0f} km/month is exceptionally high.")
                normalized["transportation"]["diesel_car_km"] = max(0.0, val)

            # Motorcycle
            if "motorcycle_km" in raw_trans:
                val = float(raw_trans["motorcycle_km"] or 0.0)
                if val < 0:
                    errors.append("Motorcycle distance cannot be negative.")
                elif val > 15000:
                    warnings.append(f"Motorcycle travel of {val:.0f} km/month is very high.")
                normalized["transportation"]["motorcycle_km"] = max(0.0, val)

            # Electric vehicle
            if "electric_car_km" in raw_trans:
                val = float(raw_trans["electric_car_km"] or 0.0)
                if val < 0:
                    errors.append("EV distance cannot be negative.")
                normalized["transportation"]["electric_car_km"] = max(0.0, val)

            # Bus & Train
            for k in ["bus_km", "train_km", "flight_domestic_km", "flight_longhaul_km"]:
                if k in raw_trans:
                    val = float(raw_trans[k] or 0.0)
                    if val < 0:
                        errors.append(f"{k} cannot be negative.")
                    normalized["transportation"][k] = max(0.0, val)

        # 2. Electricity Validation
        raw_elec = activity_data.get("electricity", {})
        if raw_elec:
            kwh = float(raw_elec.get("consumption_kwh", 0.0) or 0.0)
            solar_kwh = float(raw_elec.get("solar_kwh", 0.0) or 0.0)

            if kwh < 0:
                errors.append("Electricity consumption cannot be negative.")
            elif kwh > VALIDATION_BOUNDS["electricity_kwh_per_month"]["max"]:
                warnings.append(f"Electricity consumption ({kwh} kWh/month) exceeds typical residential range.")

            if solar_kwh < 0:
                errors.append("Solar generation cannot be negative.")
            elif solar_kwh > kwh:
                warnings.append(f"Solar generation ({solar_kwh} kWh) exceeds consumption ({kwh} kWh). Excess will be credited.")

            normalized["electricity"]["consumption_kwh"] = max(0.0, kwh)
            normalized["electricity"]["solar_kwh"] = max(0.0, solar_kwh)

        # 3. Household Fuel Validation
        raw_fuel = activity_data.get("household_fuel", {})
        if raw_fuel:
            lpg_kg = float(raw_fuel.get("lpg_kg", 0.0) or 0.0)
            if "lpg_cylinders" in raw_fuel and raw_fuel["lpg_cylinders"]:
                cyls = float(raw_fuel["lpg_cylinders"])
                if cyls < 0:
                    errors.append("LPG cylinders cannot be negative.")
                elif cyls > 8:
                    warnings.append(f"{cyls} LPG cylinders per month is exceptionally high for a single household.")
                lpg_kg += cyls * 14.2

            if lpg_kg < 0:
                errors.append("LPG consumption cannot be negative.")
            elif lpg_kg > VALIDATION_BOUNDS["lpg_kg_per_month"]["max"]:
                warnings.append(f"LPG consumption ({lpg_kg} kg/month) is unusually high.")

            gas_scm = float(raw_fuel.get("natural_gas_scm", 0.0) or 0.0)
            if gas_scm < 0:
                errors.append("Natural gas volume cannot be negative.")

            normalized["household_fuel"]["lpg_kg"] = max(0.0, lpg_kg)
            normalized["household_fuel"]["natural_gas_scm"] = max(0.0, gas_scm)

        # 4. Food Validation
        raw_food = activity_data.get("food", {})
        diet_type = raw_food.get("diet_type", "vegetarian")
        valid_diets = ["heavy_meat", "medium_meat", "pescatarian", "vegetarian", "vegan"]
        if diet_type not in valid_diets:
            warnings.append(f"Unrecognized diet '{diet_type}', default to 'vegetarian'.")
            diet_type = "vegetarian"
        normalized["food"]["diet_type"] = diet_type

        # 5. Waste Validation
        raw_waste = activity_data.get("waste", {})
        if raw_waste:
            w_kg = float(raw_waste.get("waste_kg", 0.0) or 0.0)
            r_pct = float(raw_waste.get("recycling_pct", 0.0) or 0.0)
            c_pct = float(raw_waste.get("composting_pct", 0.0) or 0.0)

            if w_kg < 0:
                errors.append("Waste quantity cannot be negative.")
            elif w_kg > VALIDATION_BOUNDS["waste_kg_per_month"]["max"]:
                warnings.append(f"Waste generation ({w_kg} kg/month) is very high.")

            if r_pct < 0 or r_pct > 100:
                errors.append("Recycling percentage must be between 0% and 100%.")
            if c_pct < 0 or c_pct > 100:
                errors.append("Composting percentage must be between 0% and 100%.")
            if (r_pct + c_pct) > 100:
                warnings.append("Sum of recycling and composting exceeds 100%. Capping to 100% total diversion.")
                total_diverted = r_pct + c_pct
                r_pct = (r_pct / total_diverted) * 100.0
                c_pct = (c_pct / total_diverted) * 100.0

            normalized["waste"]["waste_kg"] = max(0.0, w_kg)
            normalized["waste"]["recycling_pct"] = max(0.0, min(100.0, r_pct))
            normalized["waste"]["composting_pct"] = max(0.0, min(100.0, c_pct))

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "normalized_data": normalized,
            "warnings": warnings,
            "errors": errors
        }
