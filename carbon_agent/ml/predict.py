"""
ML Inference Pipeline.
Loads persisted model artifact and predicts future monthly emissions using feature vectors.
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
from carbon_agent.config.settings import MODEL_PATH, MODELS_DIR
from carbon_agent.ml.train import train_and_benchmark_models, FEATURE_COLUMNS

_MODEL = None
_METADATA = None

DIET_CODE_MAP = {
    "vegan": 1,
    "vegetarian": 2,
    "pescatarian": 3,
    "medium_meat": 4,
    "heavy_meat": 5
}


def load_model_and_metadata():
    """Load model artifact and associated benchmarking metadata."""
    global _MODEL, _METADATA
    if _MODEL is not None and _METADATA is not None:
        return _MODEL, _METADATA

    if not MODEL_PATH.exists():
        train_and_benchmark_models()

    _MODEL = joblib.load(MODEL_PATH)
    meta_path = MODELS_DIR / "model_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            _METADATA = json.load(f)
    else:
        _METADATA = {"best_model_name": "Trained Regressor", "metrics": {}}

    return _MODEL, _METADATA


def extract_features_from_state(
    activity_data: Dict[str, Any],
    carbon_results: Dict[str, Any],
    history: List[Dict[str, Any]] = None,
    target_month_idx: Optional[int] = None
) -> pd.DataFrame:
    """
    Constructs feature row from user activity and historical records.
    """
    if target_month_idx is None:
        target_month_idx = (datetime.now().month % 12) + 1

    trans = activity_data.get("transportation", {})
    # Determine dominant transport km & factor
    p_km = float(trans.get("petrol_car_km", 0.0) or 0.0)
    d_km = float(trans.get("diesel_car_km", 0.0) or 0.0)
    m_km = float(trans.get("motorcycle_km", 0.0) or 0.0)
    ev_km = float(trans.get("electric_car_km", 0.0) or 0.0)
    b_km = float(trans.get("bus_km", 0.0) or 0.0)
    t_km = float(trans.get("train_km", 0.0) or 0.0)

    total_km = p_km + d_km + m_km + ev_km + b_km + t_km
    # Weighted average efficiency factor
    if total_km > 0:
        weighted_factor = (
            p_km * 0.1705 + d_km * 0.1684 + m_km * 0.1030 +
            ev_km * 0.0530 + b_km * 0.0890 + t_km * 0.0350
        ) / total_km
    else:
        weighted_factor = 0.1705

    elec = activity_data.get("electricity", {})
    gross_kwh = float(elec.get("consumption_kwh", 0.0) or 0.0)
    solar_kwh = float(elec.get("solar_kwh", 0.0) or 0.0)
    net_kwh = max(0.0, gross_kwh - solar_kwh)

    fuel = activity_data.get("household_fuel", {})
    lpg_kg = float(fuel.get("lpg_kg", 0.0) or 0.0)

    food = activity_data.get("food", {})
    diet_str = food.get("diet_type", "vegetarian").lower()
    diet_code = DIET_CODE_MAP.get(diet_str, 2)

    waste = activity_data.get("waste", {})
    waste_kg = float(waste.get("waste_kg", 0.0) or 0.0)
    recycling_pct = float(waste.get("recycling_pct", 0.0) or 0.0)

    current_co2e = carbon_results.get("total_monthly_kg_co2e", 0.0)

    # Calculate lag1 and rolling 3m
    if history and len(history) > 0:
        lag1_co2e = history[-1].get("total_monthly_kg_co2e", current_co2e)
        past_totals = [h.get("total_monthly_kg_co2e", current_co2e) for h in history[-3:]]
        rolling_3m_co2e = float(np.mean(past_totals))
    else:
        lag1_co2e = current_co2e
        rolling_3m_co2e = current_co2e

    feature_dict = {
        "month_idx": [target_month_idx],
        "transport_km": [total_km],
        "vehicle_efficiency_factor": [weighted_factor],
        "electricity_kwh": [net_kwh],
        "lpg_kg": [lpg_kg],
        "diet_code": [diet_code],
        "waste_kg": [waste_kg],
        "recycling_pct": [recycling_pct],
        "lag1_co2e": [lag1_co2e],
        "rolling_3m_co2e": [rolling_3m_co2e]
    }
    return pd.DataFrame(feature_dict)[FEATURE_COLUMNS]


def predict_next_month_emissions(
    activity_data: Dict[str, Any],
    carbon_results: Dict[str, Any],
    history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Predict next month's carbon footprint using trained ML model.
    """
    model, metadata = load_model_and_metadata()
    X = extract_features_from_state(activity_data, carbon_results, history)

    predicted_val = float(model.predict(X)[0])
    predicted_val = round(max(0.0, predicted_val), 2)

    current_co2e = carbon_results.get("total_monthly_kg_co2e", 0.0)
    diff = round(predicted_val - current_co2e, 2)
    pct_diff = round((diff / current_co2e * 100.0), 1) if current_co2e > 0 else 0.0

    return {
        "predicted_next_month_kg_co2e": predicted_val,
        "model_used": metadata.get("best_model_name", "Linear Regression"),
        "mae": metadata.get("metrics", {}).get("mae", 0.0),
        "rmse": metadata.get("metrics", {}).get("rmse", 0.0),
        "r2": metadata.get("metrics", {}).get("r2", 0.0),
        "delta_from_current": diff,
        "pct_delta_from_current": pct_diff,
        "target_month_feature": int(X["month_idx"].values[0]),
        "features_used": {col: float(X[col].values[0]) for col in FEATURE_COLUMNS}
    }
