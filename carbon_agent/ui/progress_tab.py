"""
Tab 6: Progress Tracking & Monitoring Tab.
Maintains historical monthly logs, renders longitudinal trajectories,
and triggers the agentic monitoring feedback loop.
"""
from datetime import datetime
import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, List
from carbon_agent.agents.monitoring_agent import MonitoringAgent
from carbon_agent.tools.database_tools import save_activity_log, get_user_history

monitoring_agent = MonitoringAgent()


def create_progress_trajectory_chart(trajectory: List[Dict[str, Any]], target_co2e: float = None) -> go.Figure:
    """Renders longitudinal emission trajectory with target reference line."""
    if not trajectory:
        return go.Figure().update_layout(title="No historical logs recorded yet.")

    months = [t["month"] for t in trajectory]
    values = [t["co2e"] for t in trajectory]

    fig = go.Figure()

    # User emission trajectory line
    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines+markers+text",
            name="Monthly Footprint",
            line=dict(color="#10b981", width=3),
            marker=dict(size=9, color="#065f46"),
            text=[f"{v:.1f}" for v in values],
            textposition="top center"
        )
    )

    # If target reference exists, draw horizontal target line
    if target_co2e is not None and len(values) > 0:
        fig.add_trace(
            go.Scatter(
                x=months,
                y=[target_co2e] * len(months),
                mode="lines",
                name=f"Target ({target_co2e:.1f} kg)",
                line=dict(color="#f59e0b", width=2, dash="dash")
            )
        )

    fig.update_layout(
        title=dict(text="Longitudinal Emission Trajectory (kg CO₂e/month)", font=dict(size=16, family="Inter, sans-serif")),
        yaxis=dict(title="Monthly CO₂e (kg)", gridcolor="#f1f5f9"),
        xaxis=dict(title="Month", gridcolor="#f1f5f9"),
        height=380,
        margin=dict(t=40, b=20, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def render_progress_tab(state: gr.State):
    """Render components for the Progress Tracking tab."""
    gr.Markdown("### 📈 Monthly Progress Tracking & Agentic Feedback Loop")
    gr.Markdown(
        "Log consecutive months of lifestyle data. The **Monitoring Agent** continuously analyzes your trajectory, "
        "detects category drifts, and updates strategic recommendations."
    )

    with gr.Row():
        with gr.Column(scale=2):
            month_input = gr.Textbox(
                label="Log Month (YYYY-MM)",
                value=datetime.now().strftime("%Y-%m"),
                placeholder="2026-03"
            )
            log_notes = gr.Textbox(label="Optional Monthly Notes", placeholder="e.g., Summer cooling wave, started carpooling...")
            record_log_btn = gr.Button("💾 Commit Current Calculation as Monthly Log", variant="primary")

        with gr.Column(scale=1):
            refresh_history_btn = gr.Button("🔄 Reload History from Database", variant="secondary")

    feedback_alert_box = gr.Markdown("### 🔔 Monitoring Agent Feedback\n*No logs recorded yet in this session.*")
    trajectory_plot = gr.Plot(label="Longitudinal Trajectory")
    history_table = gr.DataFrame(label="Historical Activity & Footprint Logbook", interactive=False)

    def on_commit_log(month_str, notes, current_state):
        current_state = current_state or {}
        carbon_res = current_state.get("carbon_results", {})
        norm_inputs = current_state.get("normalized_activity_data") or current_state.get("raw_inputs", {})

        if not carbon_res:
            return (
                "> [!WARNING]\n> No active carbon calculation found. Please compute footprint in **Tab 1** first.",
                go.Figure(),
                pd.DataFrame(),
                current_state
            )

        user_prof = current_state.get("user_profile", {})
        username = user_prof.get("username", "default_user")

        # Save to database
        log_id = save_activity_log(
            username=username,
            month_year=month_str,
            inputs=norm_inputs,
            carbon_results=carbon_res,
            notes=notes
        )

        # Retrieve updated history
        updated_history = get_user_history(username)
        current_state["history"] = updated_history

        # Run Monitoring Agent & Feedback Loop
        current_log = {
            "month_year": month_str,
            "total_monthly_kg_co2e": carbon_res["total_monthly_kg_co2e"],
            "categories": carbon_res["categories"]
        }
        past_logs = [h for h in updated_history if h["month_year"] != month_str]

        eval_res = monitoring_agent.evaluate_progress(
            current_log=current_log,
            historical_logs=past_logs,
            target_reduction_pct=user_prof.get("target_reduction_pct", 20.0)
        )
        current_state["feedback_alerts"] = eval_res["alerts"]

        # Format feedback message
        alert_md = f"### 🔔 Monitoring Agent Status: `{eval_res['status']}`\n\n"
        for alt in eval_res["alerts"]:
            prefix = "✅" if alt["level"] == "SUCCESS" else ("⚠️" if alt["level"] in ["WARNING", "ALERT"] else "ℹ️")
            alert_md += f"{prefix} **{alt['level']}:** {alt['text']}\n\n"

        # Trajectory Plot
        target_co2e = None
        if eval_res.get("baseline_total"):
            target_co2e = eval_res["baseline_total"] * (1.0 - (user_prof.get("target_reduction_pct", 20.0) / 100.0))

        chart = create_progress_trajectory_chart(eval_res["trajectory"], target_co2e=target_co2e)

        # Build DataFrame for display
        df_rows = []
        for h in updated_history:
            cats = h.get("categories", {})
            df_rows.append({
                "Month": h["month_year"],
                "Total (kg)": round(h["total_monthly_kg_co2e"], 1),
                "Transport": round(cats.get("transportation", 0.0), 1),
                "Electricity": round(cats.get("electricity", 0.0), 1),
                "Fuel": round(cats.get("household_fuel", 0.0), 1),
                "Food": round(cats.get("food", 0.0), 1),
                "Waste": round(cats.get("waste", 0.0), 1),
                "Notes": h.get("notes", "") or ""
            })
        table_df = pd.DataFrame(df_rows)

        return alert_md, chart, table_df, current_state

    def on_reload_history(current_state):
        current_state = current_state or {}
        user_prof = current_state.get("user_profile", {})
        username = user_prof.get("username", "default_user")
        history = get_user_history(username)
        current_state["history"] = history

        trajectory = [{"month": h["month_year"], "co2e": h["total_monthly_kg_co2e"]} for h in history]
        chart = create_progress_trajectory_chart(trajectory)

        df_rows = []
        for h in history:
            cats = h.get("categories", {})
            df_rows.append({
                "Month": h["month_year"],
                "Total (kg)": round(h["total_monthly_kg_co2e"], 1),
                "Transport": round(cats.get("transportation", 0.0), 1),
                "Electricity": round(cats.get("electricity", 0.0), 1),
                "Fuel": round(cats.get("household_fuel", 0.0), 1),
                "Food": round(cats.get("food", 0.0), 1),
                "Waste": round(cats.get("waste", 0.0), 1),
                "Notes": h.get("notes", "") or ""
            })
        table_df = pd.DataFrame(df_rows)
        msg = f"### 🔔 History Reloaded: Found {len(history)} monthly records."
        return msg, chart, table_df, current_state

    record_log_btn.click(
        fn=on_commit_log,
        inputs=[month_input, log_notes, state],
        outputs=[feedback_alert_box, trajectory_plot, history_table, state]
    )

    refresh_history_btn.click(
        fn=on_reload_history,
        inputs=[state],
        outputs=[feedback_alert_box, trajectory_plot, history_table, state]
    )

    return record_log_btn
