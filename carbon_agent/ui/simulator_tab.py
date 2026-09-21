"""
Tab 4: What-If Simulator Tab.
Enables counterfactual simulations of lifestyle, operational, and dietary interventions.
"""
import gradio as gr
import plotly.graph_objects as go
from typing import Dict, Any
from carbon_agent.tools.simulator import simulate_scenario


def create_simulation_comparison_chart(sim_result: Dict[str, Any]) -> go.Figure:
    """Creates a side-by-side grouped bar chart of baseline vs scenario emissions."""
    categories = list(sim_result["category_deltas"].keys())
    cat_labels = [c.replace("_", " ").title() for c in categories]

    baseline_vals = [sim_result["category_deltas"][c]["baseline"] for c in categories]
    scenario_vals = [sim_result["category_deltas"][c]["scenario"] for c in categories]

    fig = go.Figure(data=[
        go.Bar(name="Baseline", x=cat_labels, y=baseline_vals, marker_color="#94a3b8"),
        go.Bar(name="Simulated Scenario", x=cat_labels, y=scenario_vals, marker_color="#10b981")
    ])

    fig.update_layout(
        barmode="group",
        title=dict(text="Category Comparison: Baseline vs Simulated Scenario (kg CO₂e)", font=dict(size=15, family="Inter, sans-serif")),
        yaxis=dict(title="kg CO₂e / month", gridcolor="#f1f5f9"),
        xaxis=dict(gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380,
        margin=dict(t=50, b=20, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def render_simulator_tab(state: gr.State):
    """Render components for the What-If Simulator tab."""
    gr.Markdown("### 🧪 Counterfactual What-If Scenario Simulator")
    gr.Markdown(
        "Experiment with behavioural modifications, renewable adoption, and dietary shifts. "
        "The **Simulation Engine** dynamically recalculates your footprint and measures the exact carbon savings."
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("#### 🚗 Transportation Interventions")
            sim_car_red = gr.Slider(label="Reduce Car Commute (%)", minimum=0, maximum=80, value=25, step=5)
            sim_modal_shift = gr.Slider(label="Shift Car Travel to Metro/Bus (%)", minimum=0, maximum=80, value=20, step=5)
            sim_ev_switch = gr.Checkbox(label="Transition Car to Electric Vehicle (EV)", value=False)

            gr.Markdown("#### ⚡ Energy Interventions")
            sim_elec_red = gr.Slider(label="Reduce Grid Electricity Consumption (%)", minimum=0, maximum=60, value=15, step=5)
            sim_solar_add = gr.Slider(label="Add Rooftop Solar PV Generation (kWh/mo)", minimum=0, maximum=350, value=0, step=25)

        with gr.Column(scale=1):
            gr.Markdown("#### 🥗 Dietary Interventions")
            sim_diet_choice = gr.Dropdown(
                label="Adopt Alternative Dietary Pattern",
                choices=[
                    ("Keep Current Baseline", "keep_current"),
                    ("Vegan (100% Plant-Based)", "vegan"),
                    ("Vegetarian (Lacto-Ovo)", "vegetarian"),
                    ("Pescatarian (Fish & Dairy)", "pescatarian"),
                    ("Medium Meat (Reduce Heavy Meat)", "medium_meat")
                ],
                value="keep_current"
            )

            gr.Markdown("#### ♻️ Circular Waste Interventions")
            sim_recycle = gr.Slider(label="Increase Dry Waste Recycling (%)", minimum=0, maximum=100, value=50, step=5)
            sim_compost = gr.Slider(label="Increase Organic Kitchen Composting (%)", minimum=0, maximum=100, value=40, step=5)

            sim_btn = gr.Button("🚀 Run What-If Simulation", variant="primary", size="lg")

    with gr.Row():
        sim_kpi_base = gr.Markdown("### 📍 Baseline\n# -- kg")
        sim_kpi_scen = gr.Markdown("### 🎯 Scenario\n# -- kg")
        sim_kpi_save = gr.Markdown("### 📉 Monthly Savings\n# -- kg")
        sim_kpi_annual = gr.Markdown("### 🌍 Annualized Savings\n# -- kg")

    sim_chart = gr.Plot(label="Scenario Comparison Chart")
    sim_table = gr.Markdown("")

    def on_run_simulation(
        car_red, modal_shift, ev_switch,
        elec_red, solar_add,
        diet_choice,
        rec_pct, comp_pct,
        current_state
    ):
        current_state = current_state or {}
        baseline_activity = current_state.get("normalized_activity_data") or current_state.get("raw_inputs")

        if not baseline_activity:
            empty_fig = go.Figure().update_layout(title="No baseline activity found. Please calculate footprint in Tab 1.")
            return (
                "### 📍 Baseline\n# --",
                "### 🎯 Scenario\n# --",
                "### 📉 Monthly Savings\n# --",
                "### 🌍 Annualized Savings\n# --",
                empty_fig,
                "> [!WARNING]\n> Please configure and calculate your baseline footprint in **Tab 1 — Carbon Calculator** first.",
                current_state
            )

        modifications = {
            "transport_reduction_pct": car_red,
            "modal_shift_to_metro_pct": modal_shift,
            "switch_to_ev": ev_switch,
            "electricity_reduction_pct": elec_red,
            "add_solar_kwh_month": solar_add,
            "new_recycling_pct": rec_pct,
            "new_composting_pct": comp_pct
        }

        if diet_choice != "keep_current":
            modifications["new_diet_type"] = diet_choice

        # Run deterministic simulation tool
        sim_res = simulate_scenario(baseline_activity, modifications)
        current_state["simulation_results"] = sim_res

        base_val = sim_res["baseline_monthly_kg_co2e"]
        scen_val = sim_res["scenario_monthly_kg_co2e"]
        red_val = sim_res["reduction_kg_co2e"]
        pct_val = sim_res["reduction_pct"]
        ann_val = sim_res["annualized_reduction_kg_co2e"]

        kpi_b = f"### 📍 Baseline\n# **{base_val:.1f} kg**"
        kpi_s = f"### 🎯 Scenario\n# **{scen_val:.1f} kg**"
        kpi_r = f"### 📉 Monthly Savings\n# **{red_val:.1f} kg**\n*(-{pct_val}%)*"
        kpi_a = f"### 🌍 Annual Savings\n# **{ann_val:.1f} kg**\n*({ann_val/1000.0:.2f} tonnes/yr)*"

        chart = create_simulation_comparison_chart(sim_res)

        table_md = "#### 📋 Category-by-Category Impact Analysis\n\n"
        table_md += "| Category | Baseline CO₂e (kg) | Scenario CO₂e (kg) | Net Reduction (kg) | % Change |\n"
        table_md += "| :--- | :---: | :---: | :---: | :---: |\n"
        for cat, d in sim_res["category_deltas"].items():
            table_md += f"| **{cat.replace('_', ' ').title()}** | {d['baseline']:.2f} kg | {d['scenario']:.2f} kg | {d['reduction_kg']:.2f} kg | -{d['pct_change']}% |\n"

        return kpi_b, kpi_s, kpi_r, kpi_a, chart, table_md, current_state

    sim_btn.click(
        fn=on_run_simulation,
        inputs=[
            sim_car_red, sim_modal_shift, sim_ev_switch,
            sim_elec_red, sim_solar_add,
            sim_diet_choice,
            sim_recycle, sim_compost,
            state
        ],
        outputs=[sim_kpi_base, sim_kpi_scen, sim_kpi_save, sim_kpi_annual, sim_chart, sim_table, state]
    )

    return sim_btn
