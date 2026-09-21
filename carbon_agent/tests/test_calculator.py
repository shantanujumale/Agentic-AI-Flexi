"""
Unit tests for deterministic Carbon Calculation Engine.
"""
import pytest
from carbon_agent.tools.carbon_calculator import (
    calculate_transportation,
    calculate_electricity,
    calculate_household_fuel,
    calculate_food,
    calculate_waste,
    calculate_carbon_footprint,
    DAYS_PER_MONTH
)
from carbon_agent.database.seed import seed_all


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    seed_all()


def test_transportation_calculation():
    # 100 km petrol car @ 0.1705 kg/km = 17.05 kg
    # 50 km motorcycle @ 0.1030 kg/km = 5.15 kg
    res = calculate_transportation({"petrol_car_km": 100, "motorcycle_km": 50})
    assert res["monthly_kg_co2e"] == pytest.approx(22.2, 0.1)
    assert res["items"]["petrol_car"]["kg_co2e"] == pytest.approx(17.05, 0.05)
    assert res["items"]["motorcycle"]["kg_co2e"] == pytest.approx(5.15, 0.05)


def test_electricity_with_solar_offset():
    # 200 kWh gross @ 0.82 kg/kWh = 164.0 kg
    # 50 kWh solar offset -> net grid = 150 kWh * 0.82 + 50 * 0.04 = 123.0 + 2.0 = 125.0 kg
    res = calculate_electricity({"consumption_kwh": 200, "solar_kwh": 50})
    assert res["monthly_kg_co2e"] == pytest.approx(125.0, 0.1)
    assert res["items"]["net_grid_kwh"] == 150.0


def test_household_fuel():
    # 1 cylinder (14.2 kg) @ 2.983 kg CO2e/kg = 42.36 kg
    res = calculate_household_fuel({"lpg_cylinders": 1.0})
    assert res["monthly_kg_co2e"] == pytest.approx(42.36, 0.1)


def test_dietary_footprint():
    # Vegan diet = 2.89 kg/day * 30.4167 days = 87.9 kg
    vegan_res = calculate_food({"diet_type": "vegan"})
    assert vegan_res["monthly_kg_co2e"] == pytest.approx(2.89 * DAYS_PER_MONTH, 0.1)

    # Heavy meat = 7.19 kg/day * 30.4167 = 218.7 kg
    meat_res = calculate_food({"diet_type": "heavy_meat"})
    assert meat_res["monthly_kg_co2e"] > vegan_res["monthly_kg_co2e"]


def test_waste_with_circular_credits():
    # 50 kg waste with 20% recycled (10 kg) and 20% composted (10 kg)
    # Landfill: 30 kg * 0.586 = 17.58 kg
    # Recycled credit: 10 kg * -0.32 = -3.20 kg
    # Composted credit: 10 kg * -0.18 = -1.80 kg
    # Net: 17.58 - 3.20 - 1.80 = 12.58 kg
    res = calculate_waste({"waste_kg": 50, "recycling_pct": 20, "composting_pct": 20})
    assert res["monthly_kg_co2e"] == pytest.approx(12.58, 0.2)


def test_full_footprint_aggregation():
    data = {
        "transportation": {"petrol_car_km": 300},
        "electricity": {"consumption_kwh": 150},
        "household_fuel": {"lpg_kg": 14.2},
        "food": {"diet_type": "vegetarian"},
        "waste": {"waste_kg": 30, "recycling_pct": 20}
    }
    footprint = calculate_carbon_footprint(data)
    assert footprint["total_monthly_kg_co2e"] > 0
    assert footprint["annualized_kg_co2e"] == pytest.approx(footprint["total_monthly_kg_co2e"] * 12.0, 0.05)
    total_pct = sum(footprint["breakdown_percentages"].values())
    assert total_pct == pytest.approx(100.0, 0.5)
