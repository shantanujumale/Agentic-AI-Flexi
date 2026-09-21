"""
Agent 6: Monitoring Agent & Feedback Loop.
Tracks longitudinal progress, monitors performance against reduction targets,
detects category drift or emission surges, and triggers adaptive plan re-evaluation.
"""
from typing import Dict, Any, List, Optional
from carbon_agent.tools.database_tools import get_user_history, save_activity_log


class MonitoringAgent:
    """
    Continually observes user activity trends, benchmarks target achievement,
    and executes the agentic feedback loop when new monthly data is logged.
    """

    def __init__(self):
        self.name = "Monitoring Agent"

    def evaluate_progress(
        self,
        current_log: Dict[str, Any],
        historical_logs: List[Dict[str, Any]],
        target_reduction_pct: float = 20.0
    ) -> Dict[str, Any]:
        """
        Evaluates progress against reduction targets and flags anomalies or trends.
        """
        current_total = current_log.get("total_monthly_kg_co2e", 0.0)
        current_categories = current_log.get("categories", {})

        alerts: List[Dict[str, str]] = []

        if not historical_logs or len(historical_logs) == 0:
            return {
                "status": "INITIAL_BASELINE_ESTABLISHED",
                "message": "First monthly footprint recorded as your baseline benchmark.",
                "total_records": 1,
                "alerts": [
                    {
                        "level": "INFO",
                        "text": "Baseline established. Future monthly submissions will be tracked against this benchmark."
                    }
                ],
                "trend": "BASELINE",
                "trajectory": []
            }

        baseline_record = historical_logs[0]
        baseline_total = baseline_record.get("total_monthly_kg_co2e", current_total)
        previous_record = historical_logs[-1]
        previous_total = previous_record.get("total_monthly_kg_co2e", current_total)

        # Delta from baseline
        baseline_diff = round(current_total - baseline_total, 2)
        baseline_pct_change = round((baseline_diff / baseline_total * 100.0), 1) if baseline_total > 0 else 0.0

        # Delta from previous month
        mom_diff = round(current_total - previous_total, 2)
        mom_pct = round((mom_diff / previous_total * 100.0), 1) if previous_total > 0 else 0.0

        # Target goal evaluation
        required_reduction_kg = baseline_total * (target_reduction_pct / 100.0)
        actual_reduction_kg = baseline_total - current_total

        if actual_reduction_kg >= required_reduction_kg:
            status = "TARGET_EXCEEDED"
            alerts.append({
                "level": "SUCCESS",
                "text": f"Outstanding! You reduced emissions by {actual_reduction_kg:.1f} kg CO2e ({abs(baseline_pct_change)}%), surpassing your {target_reduction_pct}% target!"
            })
        elif actual_reduction_kg > 0:
            status = "MAKING_PROGRESS"
            alerts.append({
                "level": "PROGRESS",
                "text": f"Good progress: Reduced by {actual_reduction_kg:.1f} kg CO2e ({abs(baseline_pct_change)}%). You are on track toward your {target_reduction_pct}% target."
            })
        elif baseline_diff == 0:
            status = "STEADY"
            alerts.append({
                "level": "INFO",
                "text": "Emissions are identical to your baseline."
            })
        else:
            status = "TARGET_MISSED_EMISSIONS_UP"
            alerts.append({
                "level": "WARNING",
                "text": f"Emissions increased by {baseline_diff:.1f} kg CO2e (+{baseline_pct_change}%) above baseline. Immediate re-evaluation recommended."
            })

        # Category drift detection (> 15% increase in any category)
        prev_categories = previous_record.get("categories", {})
        for cat, curr_val in current_categories.items():
            prev_val = prev_categories.get(cat, 0.0)
            if prev_val > 5.0 and curr_val > prev_val * 1.15:
                cat_delta = curr_val - prev_val
                alerts.append({
                    "level": "ALERT",
                    "text": f"Category Drift: {cat.replace('_', ' ').title()} emissions surged by +{cat_delta:.1f} kg CO2e compared to previous record."
                })

        # Trajectory list for plotting
        trajectory = []
        for h in historical_logs:
            trajectory.append({
                "month": h.get("month_year", ""),
                "co2e": h.get("total_monthly_kg_co2e", 0.0)
            })
        trajectory.append({
            "month": current_log.get("month_year", "Current"),
            "co2e": current_total
        })

        return {
            "status": status,
            "baseline_total": baseline_total,
            "current_total": current_total,
            "baseline_diff_kg": baseline_diff,
            "baseline_pct_change": baseline_pct_change,
            "month_over_month_diff_kg": mom_diff,
            "month_over_month_pct": mom_pct,
            "target_reduction_pct": target_reduction_pct,
            "actual_reduction_kg": round(actual_reduction_kg, 2),
            "alerts": alerts,
            "trajectory": trajectory,
            "total_records": len(trajectory)
        }
