"""
Global Configuration and Constants for Agentic AI Carbon Footprint Calculator.
"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
ML_DIR = BASE_DIR / "ml"
MODELS_DIR = ML_DIR / "models"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Database configuration
DATABASE_FILE = DATABASE_DIR / "carbon_accounting.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_FILE.as_posix()}")

# API Keys (optional for LLM mode)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Regional & Benchmark Standards
# Sources:
# - India Per Capita: MoEFCC / World Bank (approx 1.9 tonnes / 1900 kg CO2e / year)
# - Global Per Capita: Our World in Data / Global Carbon Project (approx 4.7 tonnes / 4700 kg CO2e / year)
# - Paris Agreement 1.5°C Budget target by 2030: approx 2.0-2.3 tonnes / year per person
BENCHMARKS = {
    "india_annual_kg_co2e": 1900.0,
    "india_monthly_kg_co2e": 1900.0 / 12.0,
    "global_annual_kg_co2e": 4700.0,
    "global_monthly_kg_co2e": 4700.0 / 12.0,
    "paris_target_annual_kg_co2e": 2200.0,
    "paris_target_monthly_kg_co2e": 2200.0 / 12.0,
}

# Physical Sanity & Range Validation Bounds
VALIDATION_BOUNDS = {
    "distance_km_per_day": {"min": 0.0, "max": 1200.0, "default_unit": "km/day"},
    "electricity_kwh_per_month": {"min": 0.0, "max": 10000.0, "default_unit": "kWh/month"},
    "lpg_kg_per_month": {"min": 0.0, "max": 150.0, "default_unit": "kg/month"},
    "natural_gas_scm_per_month": {"min": 0.0, "max": 250.0, "default_unit": "m3/month"},
    "waste_kg_per_month": {"min": 0.0, "max": 500.0, "default_unit": "kg/month"},
    "recycling_rate_pct": {"min": 0.0, "max": 100.0, "default_unit": "%"},
}

# Default App Settings
DEFAULT_REGION = os.getenv("DEFAULT_REGION", "India")
MODEL_FILENAME = "best_emission_model.joblib"
MODEL_PATH = MODELS_DIR / MODEL_FILENAME
