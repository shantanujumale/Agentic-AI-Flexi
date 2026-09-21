"""
Agentic AI Personal Carbon Footprint Calculator and Intelligent Emission Reduction System.
Main Gradio Application Entry Point.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gradio as gr
from carbon_agent.database.seed import seed_all
from carbon_agent.agents.state import UserState
from carbon_agent.ui.theme import CUSTOM_CSS
from carbon_agent.ui.calculator_tab import render_calculator_tab
from carbon_agent.ui.dashboard_tab import render_dashboard_tab
from carbon_agent.ui.advisor_tab import render_advisor_tab
from carbon_agent.ui.simulator_tab import render_simulator_tab
from carbon_agent.ui.planner_tab import render_planner_tab
from carbon_agent.ui.progress_tab import render_progress_tab


def build_app():
    """Constructs the integrated multi-agent Gradio Blocks interface."""
    # Ensure database tables and certified factors are seeded
    seed_all()

    with gr.Blocks(
        title="Agentic AI Carbon Footprint & Emission Reduction System"
    ) as demo:
        # Centralized Session State Object
        state = gr.State(value=UserState().model_dump())

        # Header Section
        gr.HTML(
            """
            <div class="app-header">
                <h1>🌿 Agentic AI Personal Carbon Footprint System</h1>
                <p>An intelligent multi-agent system for deterministic carbon accounting, ML forecasting, counterfactual simulation, and goal-based reduction planning.</p>
            </div>
            """
        )

        with gr.Tabs():
            with gr.TabItem("🧮 1. Carbon Calculator"):
                render_calculator_tab(state)

            with gr.TabItem("📊 2. Visual Dashboard & Benchmarks"):
                render_dashboard_tab(state)

            with gr.TabItem("🤖 3. AI Carbon Advisor"):
                render_advisor_tab(state)

            with gr.TabItem("🧪 4. What-If Simulator"):
                render_simulator_tab(state)

            with gr.TabItem("🎯 5. AI Reduction Planner"):
                render_planner_tab(state)

            with gr.TabItem("📈 6. Progress Tracking & Feedback Loop"):
                render_progress_tab(state)

        gr.HTML(
            """
            <div style="text-align: center; margin-top: 30px; font-size: 0.85rem; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                Agentic AI Personal Carbon Footprint Calculator & Emission Reduction System | Powered by CEA India v19, IPCC & DEFRA Standards | Built with Gradio & Scikit-learn
            </div>
            """
        )

    return demo


demo = build_app()

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7865,
        theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="slate"),
        css=CUSTOM_CSS,
        share=False
    )

