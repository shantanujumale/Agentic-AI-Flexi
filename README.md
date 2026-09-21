# Agentic AI Personal Carbon Footprint Calculator and Intelligent Emission Reduction System

An academic-grade, modular, agentic AI personal carbon footprint calculation, machine learning forecasting, and emission reduction planning application built with **Gradio**, **Python**, **Scikit-learn**, **XGBoost**, **Plotly**, and **SQLite/SQLAlchemy**.

Designed specifically for academic rigor (suitable for B.Tech AIML capstone/projects) with strict adherence to certified greenhouse gas (GHG) accounting standards.

---

## 🌟 Key Features

1. **Deterministic Carbon Accounting Engine**:
   - Strictly forbids LLMs from hallucinating emission factors or performing core arithmetic.
   - Grounded in official environmental standards:
     - **Electricity**: CEA India National Grid CO₂ Baseline Database v19 (2023) — $0.82\text{ kg CO}_2\text{e/kWh}$.
     - **Transportation**: UK Department for Energy Security and Net Zero (DESNZ / DEFRA 2023) & IPCC Guidelines.
     - **Household Cooking**: IPCC / DEFRA combustion factors for LPG ($2.983\text{ kg CO}_2\text{e/kg}$) and Natural Gas ($1.968\text{ kg CO}_2\text{e/m}^3$).
     - **Dietary Footprints**: Meta-analysis by Poore & Nemecek (*Science*, 2018 / Our World in Data).
     - **Circular Waste**: IPCC & US EPA WARM model accounting for landfill methane burden with certified recycling ($-0.32\text{ kg CO}_2\text{e/kg}$) and composting ($-0.18\text{ kg CO}_2\text{e/kg}$) avoidance credits.

2. **Multi-Agent Architecture**:
   - **Input / Intent Agent**: Parses natural language narratives (e.g. *"I drive 25 km daily by bike and use 180 units of electricity"*) into structured activity JSON without inventing missing data.
   - **Data Validation Agent**: Enforces physical sanity bounds, detects anomalies, and normalizes frequencies to standardized monthly units.
   - **Emission Analysis Agent**: Performs hotspot diagnostic ranking and compares user emissions against Indian national (~158 kg/mo) and global per-capita (~392 kg/mo) benchmarks.
   - **ML Prediction Agent**: Evaluates 5 candidate regression algorithms (Linear Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost), benchmarks them with MAE, RMSE, and $R^2$, auto-selects the optimal model via Joblib, and forecasts future emissions across lag features.
   - **Reduction Planning Agent**: Calculates the exact mathematical reduction required to achieve user-defined targets (e.g., 20%, 30%), filters by difficulty and budget preferences, and greedily prioritizes high-impact interventions.
   - **What-If Scenario Simulator**: Simulates counterfactual decisions (e.g., *-30% car travel*, *modal shift to metro*, *rooftop solar net-metering*, *dietary shift*) with side-by-side delta visualization.
   - **Monitoring Agent & Feedback Loop**: Stores longitudinal monthly records in SQLite, tracks progress against targets, detects category drifts and emission surges, and re-evaluates strategic recommendations.
   - **AI Carbon Advisor**: Tool-augmented conversational agent that dispatches to deterministic Python tools before answering numerical questions, displaying execution traces.

3. **Modern Gradio 6 UI**:
   - 6 dedicated tabs: Calculator, Visual Dashboard, AI Advisor, What-If Simulator, Reduction Planner, and Progress Tracking.
   - Custom modern emerald/slate glassmorphism CSS theme and interactive Plotly charts.

---

## 🏛️ System Architecture

```
User Input (Form / Natural Language)
   │
   ▼
[ Agent 1: Input / Intent Agent ]
   │
   ▼
[ Agent 2: Data Validation Agent ]
   │
   ▼
[ Deterministic Carbon Calculation Engine ] ◄── Certified SQLite Database
   │                                             (CEA v19, IPCC, DEFRA)
   ├───────────────────────────────┐
   ▼                               ▼
[ Agent 3: Emission Analysis ]   [ Agent 4: ML Prediction Agent ]
   │                             (LR, DT, RF, GBDT, XGBoost)
   ▼                               │
[ Agent 5: Reduction Planning ] ◄──┘
   │
   ▼
[ What-If Scenario Simulator ]
   │
   ▼
[ Agent 6: Monitoring Agent & Feedback Loop ]
   │
   ▼
User Progress / Continuous Re-evaluation
```

---

## 📁 Project Structure

```
carbon_agent/
├── app.py                      # Master Gradio application entry point
├── config/
│   ├── __init__.py
│   └── settings.py             # Global constants, benchmarks, physical bounds
├── database/
│   ├── __init__.py
│   ├── database.py             # SQLAlchemy engine & session management
│   ├── models.py               # ORM schemas (EmissionFactor, UserProfile, ActivityLog, etc.)
│   └── seed.py                 # Seeds verified emission factors and reduction actions
├── data/
│   ├── emission_factors.csv    # Official verified factors with full provenance
│   └── historical_data.csv     # Multi-month activity benchmark dataset for ML training
├── tools/
│   ├── __init__.py
│   ├── emission_factors.py     # SQLite factor lookup and caching service
│   ├── carbon_calculator.py    # Core deterministic carbon accounting engine
│   ├── simulator.py            # What-If scenario engine
│   └── database_tools.py       # Data access and log persistence tools
├── ml/
│   ├── __init__.py
│   ├── evaluate.py             # Computes MAE, RMSE, and R² scores
│   ├── train.py                # Multi-model benchmarking and Joblib serializer
│   ├── predict.py              # Time-series feature engineering and inference pipeline
│   └── models/                 # Model artifacts and evaluation metadata
├── agents/
│   ├── __init__.py
│   ├── state.py                # Central UserState Pydantic model
│   ├── input_agent.py          # Natural language entity & intent extractor
│   ├── validation_agent.py     # Physical bounds and sanity validator
│   ├── analysis_agent.py       # Hotspot diagnostics and benchmark comparisons
│   ├── prediction_agent.py     # ML forecasting coordinator
│   ├── reduction_agent.py      # Goal-based reduction planner
│   ├── monitoring_agent.py     # Longitudinal progress monitor and feedback loop
│   └── advisor_agent.py        # Tool-augmented AI Carbon Advisor
├── ui/
│   ├── __init__.py
│   ├── theme.py                # Custom CSS styling and design system
│   ├── calculator_tab.py       # Tab 1: Carbon Calculator
│   ├── dashboard_tab.py        # Tab 2: Visual Dashboard & Benchmarks
│   ├── advisor_tab.py          # Tab 3: AI Carbon Advisor
│   ├── simulator_tab.py        # Tab 4: What-If Simulator
│   ├── planner_tab.py          # Tab 5: AI Reduction Planner
│   └── progress_tab.py         # Tab 6: Progress Monitoring & Feedback Loop
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py      # 100% deterministic accounting formula tests
│   ├── test_agents.py          # Unit tests for multi-agent interactions
│   └── test_ml.py              # ML training, evaluation, and inference tests
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Installation
Ensure Python 3.10+ is installed. Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Database Initialization & Seeding
Initialize the SQLite database with certified emission factors and validated reduction actions:

```bash
python -m carbon_agent.database.seed
```

### 3. ML Model Training & Benchmarking
Train and evaluate candidate models (Linear Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost) and save the optimal model artifact:

```bash
python -m carbon_agent.ml.train
```

### 4. Running Automated Tests
Run the comprehensive unit and integration test suite:

```bash
pytest carbon_agent/tests -v
```

### 5. Launch the Application
Start the interactive Gradio web application:

```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:7865/
```

---

## 🧪 Mathematical Formulations

### Carbon Accounting Formulas
- **Transportation**:
  $$\text{CO}_2\text{e}_{\text{trans}} = \sum_i \text{Distance}_i \times \text{Factor}_i$$
- **Electricity**:
  $$\text{CO}_2\text{e}_{\text{elec}} = \max(0, \text{kWh}_{\text{gross}} - \text{kWh}_{\text{solar}}) \times 0.820 + \text{kWh}_{\text{solar}} \times 0.040$$
- **Household Cooking**:
  $$\text{CO}_2\text{e}_{\text{fuel}} = \text{LPG (kg)} \times 2.983 + \text{PNG (m}^3) \times 1.968$$
- **Diet**:
  $$\text{CO}_2\text{e}_{\text{food}} = \text{DailyFactor}_{\text{diet}} \times 30.4167$$
- **Circular Waste**:
  $$\text{CO}_2\text{e}_{\text{waste}} = \max(0, W_{\text{landfill}} \times 0.586 - W_{\text{recycled}} \times 0.320 - W_{\text{composted}} \times 0.180)$$

### Reduction Target Optimization
$$\text{Required Savings} = \text{Baseline CO}_2\text{e} \times \frac{\text{Target \%}}{100}$$

The **Reduction Planning Agent** greedily selects interventions $\mathcal{A} \subset \text{Catalog}$ that minimize difficulty while satisfying:
$$\sum_{a \in \mathcal{A}} \Delta \text{CO}_2\text{e}_a \ge \text{Required Savings}$$

---

## 🛡️ Reliability and Scientific Integrity
1. **Zero Math Hallucinations**: LLMs never calculate footprint numbers. All calculations are executed by deterministic Python modules.
2. **Certified Factors**: Every single emission factor in SQLite is tagged with its origin (CEA India, IPCC, DEFRA, Our World in Data) and reference year.
3. **Reproducible ML**: Time-series feature engineering with deterministic random states and cross-model validation (MAE, RMSE, $R^2$).
