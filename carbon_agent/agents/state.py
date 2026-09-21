"""
Centralized State Management for the Agentic AI Carbon System.
Maintains user context across all agents and Gradio components.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class UserState(BaseModel):
    """
    Central user state schema holding all pipeline data.
    """
    user_profile: Dict[str, Any] = Field(
        default_factory=lambda: {
            "username": "default_user",
            "region": "India",
            "target_reduction_pct": 20.0
        }
    )
    # Raw structured activity inputs before/after validation
    raw_inputs: Dict[str, Any] = Field(default_factory=dict)
    normalized_activity_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation results
    validation_status: Dict[str, Any] = Field(
        default_factory=lambda: {"is_valid": True, "errors": [], "warnings": []}
    )

    # Core calculated carbon accounting data
    carbon_results: Dict[str, Any] = Field(default_factory=dict)

    # Analysis Agent output
    emission_analysis: Dict[str, Any] = Field(default_factory=dict)

    # ML Prediction Agent output
    prediction: Dict[str, Any] = Field(default_factory=dict)

    # Reduction Planning Agent output
    reduction_plan: Dict[str, Any] = Field(default_factory=dict)

    # What-If Simulation results
    simulation_results: Dict[str, Any] = Field(default_factory=dict)

    # Historical monthly logs and progress alerts
    history: List[Dict[str, Any]] = Field(default_factory=list)
    feedback_alerts: List[Dict[str, Any]] = Field(default_factory=list)

    # Agent execution traces for UI transparency
    agent_traces: List[Dict[str, Any]] = Field(default_factory=list)

    def log_trace(self, agent_name: str, action: str, details: Any):
        """Append an execution trace for agent transparency."""
        self.agent_traces.append({
            "agent": agent_name,
            "action": action,
            "details": details
        })
