"""
Agent 4: ML Prediction Agent.
Orchestrates machine learning inference, provides transparent model metrics,
and communicates data confidence clearly without fabricating past records.
"""
from typing import Dict, Any, List
from carbon_agent.ml.predict import predict_next_month_emissions


class MLPredictionAgent:
    """
    Interfaces with the machine learning inference pipeline.
    Ensures model evaluation metrics are reported and explains historical data sufficiency.
    """

    def __init__(self):
        self.name = "ML Prediction Agent"

    def predict(
        self,
        activity_data: Dict[str, Any],
        carbon_results: Dict[str, Any],
        history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Produce a forecast of next month's CO2e emissions.
        """
        history = history or []
        prediction_result = predict_next_month_emissions(activity_data, carbon_results, history)

        history_count = len(history)
        if history_count == 0:
            reliability_note = (
                "Initial forecast based on pre-trained supervised regression models on historical activity benchmarks. "
                "Reliability will increase as you log consecutive monthly data points."
            )
            confidence_tier = "Moderate (Benchmark-Informed)"
        elif history_count < 3:
            reliability_note = (
                f"Prediction utilizes {history_count} previous personal month(s) combined with benchmark activity weights. "
                "Three or more consecutive logs will yield personalized autoregressive trends."
            )
            confidence_tier = "Moderate"
        else:
            reliability_note = (
                f"Prediction successfully incorporates personal autoregressive lag-1 and rolling 3-month momentum across {history_count} logged records."
            )
            confidence_tier = "High (Personalized Time-Series)"

        prediction_result["reliability_note"] = reliability_note
        prediction_result["confidence_tier"] = confidence_tier
        prediction_result["user_history_count"] = history_count

        return prediction_result
