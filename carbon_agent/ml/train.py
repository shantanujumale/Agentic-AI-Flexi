"""
ML Model Training and Benchmarking Pipeline.
Trains 5 candidate regression models:
1. Linear Regression
2. Decision Tree Regressor
3. Random Forest Regressor
4. Gradient Boosting Regressor
5. XGBoost Regressor

Evaluates on MAE, RMSE, and R2; automatically selects and persists the best model via Joblib.
"""
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor

from carbon_agent.config.settings import DATA_DIR, MODELS_DIR, MODEL_PATH
from carbon_agent.ml.evaluate import compute_metrics

FEATURE_COLUMNS = [
    "month_idx",
    "transport_km",
    "vehicle_efficiency_factor",
    "electricity_kwh",
    "lpg_kg",
    "diet_code",
    "waste_kg",
    "recycling_pct",
    "lag1_co2e",
    "rolling_3m_co2e"
]
TARGET_COLUMN = "total_co2e"


def load_dataset() -> pd.DataFrame:
    """Load benchmark historical activity data."""
    csv_path = DATA_DIR / "historical_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {csv_path}")
    return pd.read_csv(csv_path)


def train_and_benchmark_models() -> Dict[str, Any]:
    """
    Trains all candidate models, benchmarks performance, and saves the top-ranked model.
    """
    df = load_dataset()
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Deterministic train/test split for reproducibility
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    candidate_models = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(max_depth=6, random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, learning_rate=0.08, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42)
    }

    benchmark_results = {}
    fitted_models = {}

    for name, model in candidate_models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test.values, y_pred)
        benchmark_results[name] = metrics
        fitted_models[name] = model

    # Select best model: prioritize highest R², breaking ties by lowest RMSE
    best_name = max(
        benchmark_results.keys(),
        key=lambda k: (benchmark_results[k]["r2"], -benchmark_results[k]["rmse"])
    )
    best_model = fitted_models[best_name]
    best_metrics = benchmark_results[best_name]

    # Save model artifact
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)

    # Save metadata
    metadata = {
        "best_model_name": best_name,
        "metrics": best_metrics,
        "all_benchmarks": benchmark_results,
        "feature_columns": FEATURE_COLUMNS,
        "samples_count": len(df)
    }
    meta_path = MODELS_DIR / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "best_model_name": best_name,
        "best_metrics": best_metrics,
        "all_benchmarks": benchmark_results,
        "saved_path": str(MODEL_PATH)
    }


if __name__ == "__main__":
    results = train_and_benchmark_models()
    print(f"Top Model: {results['best_model_name']}")
    print(f"Metrics: {results['best_metrics']}")
    print("All Models:")
    for m, vals in results["all_benchmarks"].items():
        print(f" - {m:20s}: R²={vals['r2']:.4f}, RMSE={vals['rmse']:.2f}, MAE={vals['mae']:.2f}")
