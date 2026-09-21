"""
Unit tests for Agent behaviours: Input Parsing, Validation, Analysis, Reduction Planning, and Monitoring.
"""
import pytest
from carbon_agent.agents.input_agent import InputIntentAgent
from carbon_agent.agents.validation_agent import ValidationAgent
from carbon_agent.agents.analysis_agent import EmissionAnalysisAgent
from carbon_agent.agents.reduction_agent import ReductionPlanningAgent
from carbon_agent.agents.monitoring_agent import MonitoringAgent
from carbon_agent.tools.carbon_calculator import calculate_carbon_footprint
from carbon_agent.database.seed import seed_all


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    seed_all()


def test_input_agent_parsing():
    agent = InputIntentAgent()
    text = "I travel around 25 km every day on my bike and use around 150 units of electricity every month."
    res = agent.parse_user_text(text)
    struct = res["structured_data"]

    assert "transportation" in struct
    # 25 km daily -> approx 760 km monthly
    assert struct["transportation"]["motorcycle_km"] > 700
    assert "electricity" in struct
    assert struct["electricity"]["consumption_kwh"] == 150.0
    assert "transport_motorcycle" in res["detected_intents"]


def test_validation_agent_bounds():
    agent = ValidationAgent()
    # Test impossible negative numbers
    invalid_data = {
        "transportation": {"petrol_car_km": -50},
        "electricity": {"consumption_kwh": -10}
    }
    val = agent.validate_and_normalize(invalid_data)
    assert not val["is_valid"]
    assert len(val["errors"]) >= 2

    # Test valid data normalization
    valid_data = {
        "transportation": {"petrol_car_km": 300},
        "electricity": {"consumption_kwh": 180},
        "food": {"diet_type": "vegetarian"}
    }
    val_ok = agent.validate_and_normalize(valid_data)
    assert val_ok["is_valid"]
    assert val_ok["normalized_data"]["transportation"]["petrol_car_km"] == 300.0


def test_emission_analysis_agent():
    agent = EmissionAnalysisAgent()
    activity = {
        "transportation": {"petrol_car_km": 500},
        "electricity": {"consumption_kwh": 80}
    }
    calc = calculate_carbon_footprint(activity)
    analysis = agent.analyze(calc)

    assert analysis["total_monthly_kg_co2e"] > 0
    assert analysis["dominant_category"] in calc["categories"]
    assert "benchmarks" in analysis


def test_reduction_planning_agent():
    agent = ReductionPlanningAgent()
    activity = {
        "transportation": {"petrol_car_km": 600},
        "electricity": {"consumption_kwh": 250},
        "food": {"diet_type": "heavy_meat"},
        "waste": {"waste_kg": 40}
    }
    calc = calculate_carbon_footprint(activity)
    plan = agent.plan_reduction(calc, activity, target_pct=20.0)

    assert plan["required_reduction_kg"] > 0
    assert plan["projected_savings_kg_co2e"] > 0
    assert len(plan["actions"]) > 0
    assert plan["actions_count"] == len(plan["actions"])


def test_monitoring_agent_evaluation():
    agent = MonitoringAgent()
    current_log = {
        "month_year": "2026-03",
        "total_monthly_kg_co2e": 220.0,
        "categories": {"transportation": 80, "electricity": 140}
    }
    historical_logs = [
        {"month_year": "2026-01", "total_monthly_kg_co2e": 280.0, "categories": {"transportation": 120, "electricity": 160}},
        {"month_year": "2026-02", "total_monthly_kg_co2e": 250.0, "categories": {"transportation": 100, "electricity": 150}}
    ]
    eval_res = agent.evaluate_progress(current_log, historical_logs, target_reduction_pct=20.0)

    assert eval_res["status"] in ["TARGET_EXCEEDED", "MAKING_PROGRESS"]
    assert eval_res["actual_reduction_kg"] == 60.0  # 280 - 220
