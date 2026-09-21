"""
Unit tests for Machine Learning Pipeline: Training, Benchmarking, Evaluation, and Prediction.
"""
import pytest
from carbon_agent.ml.train import train_and_benchmark_models, load_dataset
from carbon_agent.ml.evaluate import compute_metrics
from carbon_agent.ml.predict import predict_next_month_emissions
import numpy as np


def test_dataset_integrity():
    df = load_dataset()
    assert len(df) >= 50
    assert "total_co2e" in df.columns
    assert not df.isnull().values.any()


def test_compute_metrics():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([105.0, 195.0, 302.0])
    metrics = compute_metrics(y_true, y_pred)
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0
    assert metrics["r2"] > 0.95


def test_training_and_model_selection():
    results = train_and_benchmark_models()
    assert "best_model_name" in results
    assert "best_metrics" in results
    assert results["best_metrics"]["r2"] > 0.90
    assert len(results["all_benchmarks"]) == 5  # LR, DT, RF, GBDT, XGBoost


def test_predict_pipeline():
    activity = {
        "transportation": {"petrol_car_km": 400},
        "electricity": {"consumption_kwh": 200},
        "household_fuel": {"lpg_kg": 14.2},
        "food": {"diet_type": "vegetarian"},
        "waste": {"waste_kg": 30}
    }
    carbon_results = {"total_monthly_kg_co2e": 350.0}
    pred = predict_next_month_emissions(activity, carbon_results)

    assert pred["predicted_next_month_kg_co2e"] > 0
    assert "model_used" in pred
    assert "r2" in pred
    assert pred["r2"] > 0.90
