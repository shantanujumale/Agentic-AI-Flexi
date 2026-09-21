"""
Deterministic Carbon Calculation Engine.
Calculates personal carbon footprints strictly using verified emission factors from SQLite.
Never allows LLMs to calculate or invent emission factors.
"""
from typing import Dict, Any, List
from carbon_agent.tools.emission_factors import get_factor_value, get_factor

DAYS_PER_MONTH = 30.4167  # Standard monthly average (365 / 12)


def calculate_transportation(transport_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate monthly CO2e for transportation activities.
    Supports km/month for petrol car, diesel car, motorcycle, EV, bus, train, and flights.
    """
    petrol_car_km = float(transport_data.get("petrol_car_km", 0.0) or 0.0)
    diesel_car_km = float(transport_data.get("diesel_car_km", 0.0) or 0.0)
    motorcycle_km = float(transport_data.get("motorcycle_km", 0.0) or 0.0)
    electric_car_km = float(transport_data.get("electric_car_km", 0.0) or 0.0)
    bus_km = float(transport_data.get("bus_km", 0.0) or 0.0)
    train_km = float(transport_data.get("train_km", 0.0) or 0.0)
    flight_domestic_km = float(transport_data.get("flight_domestic_km", 0.0) or 0.0)
    flight_longhaul_km = float(transport_data.get("flight_longhaul_km", 0.0) or 0.0)

    f_petrol_car = get_factor_value("petrol_car_km", 0.1705)
    f_diesel_car = get_factor_value("diesel_car_km", 0.1684)
    f_motorcycle = get_factor_value("motorcycle_km", 0.1030)
    f_ev = get_factor_value("electric_car_km", 0.0530)
    f_bus = get_factor_value("city_bus_km", 0.0890)
    f_train = get_factor_value("train_km", 0.0350)
    f_flight_dom = get_factor_value("flight_domestic_km", 0.2540)
    f_flight_lh = get_factor_value("flight_longhaul_km", 0.1950)

    co2e_petrol_car = petrol_car_km * f_petrol_car
    co2e_diesel_car = diesel_car_km * f_diesel_car
    co2e_motorcycle = motorcycle_km * f_motorcycle
    co2e_ev = electric_car_km * f_ev
    co2e_bus = bus_km * f_bus
    co2e_train = train_km * f_train
    co2e_flight_dom = flight_domestic_km * f_flight_dom
    co2e_flight_lh = flight_longhaul_km * f_flight_lh

    total = (
        co2e_petrol_car + co2e_diesel_car + co2e_motorcycle +
        co2e_ev + co2e_bus + co2e_train +
        co2e_flight_dom + co2e_flight_lh
    )

    return {
        "monthly_kg_co2e": round(total, 2),
        "items": {
            "petrol_car": {"km": petrol_car_km, "factor": f_petrol_car, "kg_co2e": round(co2e_petrol_car, 2)},
            "diesel_car": {"km": diesel_car_km, "factor": f_diesel_car, "kg_co2e": round(co2e_diesel_car, 2)},
            "motorcycle": {"km": motorcycle_km, "factor": f_motorcycle, "kg_co2e": round(co2e_motorcycle, 2)},
            "electric_car": {"km": electric_car_km, "factor": f_ev, "kg_co2e": round(co2e_ev, 2)},
            "city_bus": {"km": bus_km, "factor": f_bus, "kg_co2e": round(co2e_bus, 2)},
            "train_metro": {"km": train_km, "factor": f_train, "kg_co2e": round(co2e_train, 2)},
            "flight_domestic": {"km": flight_domestic_km, "factor": f_flight_dom, "kg_co2e": round(co2e_flight_dom, 2)},
            "flight_longhaul": {"km": flight_longhaul_km, "factor": f_flight_lh, "kg_co2e": round(co2e_flight_lh, 2)},
        }
    }


def calculate_electricity(electricity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate monthly CO2e for grid electricity and rooftop solar offset.
    """
    kwh = float(electricity_data.get("consumption_kwh", 0.0) or 0.0)
    solar_kwh = float(electricity_data.get("solar_kwh", 0.0) or 0.0)

    f_grid = get_factor_value("electricity_grid", 0.8200)
    f_solar = get_factor_value("solar_rooftop_offset", 0.0400)

    # Net grid electricity consumed
    net_grid_kwh = max(0.0, kwh - solar_kwh)
    grid_co2e = net_grid_kwh * f_grid
    solar_lifecycle_co2e = solar_kwh * f_solar
    total = grid_co2e + solar_lifecycle_co2e

    return {
        "monthly_kg_co2e": round(total, 2),
        "items": {
            "gross_grid_kwh": kwh,
            "solar_generated_kwh": solar_kwh,
            "net_grid_kwh": round(net_grid_kwh, 2),
            "grid_emission_factor": f_grid,
            "solar_emission_factor": f_solar,
            "grid_co2e": round(grid_co2e, 2),
            "solar_co2e": round(solar_lifecycle_co2e, 2)
        }
    }


def calculate_household_fuel(fuel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate monthly CO2e from LPG cylinders and Piped Natural Gas (PNG).
    """
    lpg_kg = float(fuel_data.get("lpg_kg", 0.0) or 0.0)
    # If cylinders were provided, 1 standard cylinder = 14.2 kg
    if "lpg_cylinders" in fuel_data and fuel_data["lpg_cylinders"]:
        lpg_kg += float(fuel_data["lpg_cylinders"]) * 14.2

    natural_gas_scm = float(fuel_data.get("natural_gas_scm", 0.0) or 0.0)

    f_lpg = get_factor_value("lpg_kg", 2.9830)
    f_gas = get_factor_value("natural_gas_scm", 1.9680)

    co2e_lpg = lpg_kg * f_lpg
    co2e_gas = natural_gas_scm * f_gas
    total = co2e_lpg + co2e_gas

    return {
        "monthly_kg_co2e": round(total, 2),
        "items": {
            "lpg": {"kg": lpg_kg, "factor": f_lpg, "kg_co2e": round(co2e_lpg, 2)},
            "natural_gas": {"scm": natural_gas_scm, "factor": f_gas, "kg_co2e": round(co2e_gas, 2)}
        }
    }


def calculate_food(food_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate monthly dietary CO2e based on verified dietary patterns.
    """
    diet_type = str(food_data.get("diet_type", "vegetarian")).lower().strip()
    factor_key_map = {
        "heavy_meat": "diet_heavy_meat",
        "medium_meat": "diet_medium_meat",
        "pescatarian": "diet_pescatarian",
        "vegetarian": "diet_vegetarian",
        "vegan": "diet_vegan"
    }
    factor_key = factor_key_map.get(diet_type, "diet_vegetarian")
    daily_factor = get_factor_value(factor_key, 3.8100)

    monthly_co2e = daily_factor * DAYS_PER_MONTH

    return {
        "monthly_kg_co2e": round(monthly_co2e, 2),
        "items": {
            "diet_type": diet_type,
            "daily_factor_kg_co2e": daily_factor,
            "days_per_month": DAYS_PER_MONTH
        }
    }


def calculate_waste(waste_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate monthly solid waste emissions including credits for recycling and composting.
    """
    waste_kg = float(waste_data.get("waste_kg", 0.0) or 0.0)
    recycling_pct = float(waste_data.get("recycling_pct", 0.0) or 0.0)
    composting_pct = float(waste_data.get("composting_pct", 0.0) or 0.0)

    recycled_kg = waste_kg * (min(100.0, max(0.0, recycling_pct)) / 100.0)
    composted_kg = waste_kg * (min(100.0, max(0.0, composting_pct)) / 100.0)
    landfill_kg = max(0.0, waste_kg - recycled_kg - composted_kg)

    f_landfill = get_factor_value("general_landfill_waste", 0.5860)
    f_recycle_credit = get_factor_value("recycled_material_credit", -0.3200)
    f_compost_credit = get_factor_value("composted_organic_credit", -0.1800)

    landfill_co2e = landfill_kg * f_landfill
    recycle_offset = recycled_kg * f_recycle_credit  # Negative offset
    compost_offset = composted_kg * f_compost_credit  # Negative offset

    net_waste_co2e = max(0.0, landfill_co2e + recycle_offset + compost_offset)

    return {
        "monthly_kg_co2e": round(net_waste_co2e, 2),
        "items": {
            "total_waste_kg": waste_kg,
            "landfill_kg": round(landfill_kg, 2),
            "recycled_kg": round(recycled_kg, 2),
            "composted_kg": round(composted_kg, 2),
            "landfill_emissions": round(landfill_co2e, 2),
            "recycle_avoided": round(abs(recycle_offset), 2),
            "compost_avoided": round(abs(compost_offset), 2)
        }
    }


def calculate_carbon_footprint(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Master deterministic carbon accounting function.
    Aggregates transportation, electricity, fuel, food, and waste.
    """
    transport = calculate_transportation(activity_data.get("transportation", {}))
    electricity = calculate_electricity(activity_data.get("electricity", {}))
    fuel = calculate_household_fuel(activity_data.get("household_fuel", {}))
    food = calculate_food(activity_data.get("food", {}))
    waste = calculate_waste(activity_data.get("waste", {}))

    c_trans = transport["monthly_kg_co2e"]
    c_elec = electricity["monthly_kg_co2e"]
    c_fuel = fuel["monthly_kg_co2e"]
    c_food = food["monthly_kg_co2e"]
    c_waste = waste["monthly_kg_co2e"]

    total_monthly = round(c_trans + c_elec + c_fuel + c_food + c_waste, 2)
    annualized = round(total_monthly * 12.0, 2)

    categories = {
        "transportation": c_trans,
        "electricity": c_elec,
        "household_fuel": c_fuel,
        "food": c_food,
        "waste": c_waste
    }

    # Percentages
    pcts = {}
    if total_monthly > 0:
        for k, v in categories.items():
            pcts[k] = round((v / total_monthly) * 100.0, 1)
    else:
        pcts = {k: 0.0 for k in categories}

    calculation_notes = [
        "Transportation: Calculated with UK DEFRA 2023 & CEA India v19 factor intensities.",
        "Electricity: Calculated with CEA India National Grid CO2 Baseline Database v19 (0.82 kg CO2e/kWh).",
        "Household Fuel: LPG combustion calculated at 2.983 kg CO2e/kg (IPCC/DEFRA 2023).",
        "Food: Based on meta-analysis by Poore & Nemecek (Science 2018 / Our World in Data).",
        "Waste: Landfill methane burden (0.586 kg CO2e/kg) minus certified recycling and composting avoidance credits."
    ]

    return {
        "total_monthly_kg_co2e": total_monthly,
        "annualized_kg_co2e": annualized,
        "categories": categories,
        "breakdown_percentages": pcts,
        "details": {
            "transportation": transport["items"],
            "electricity": electricity["items"],
            "household_fuel": fuel["items"],
            "food": food["items"],
            "waste": waste["items"]
        },
        "calculation_notes": calculation_notes
    }
