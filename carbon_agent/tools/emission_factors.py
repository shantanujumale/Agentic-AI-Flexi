"""
Emission Factor Lookup Service.
Fetches verified emission factors directly from SQLite database with caching and provenance.
"""
from typing import Dict, Any, Optional
from carbon_agent.database.database import get_db
from carbon_agent.database.models import EmissionFactor

_EMISSION_FACTOR_CACHE: Dict[str, Dict[str, Any]] = {}


def load_emission_factors(force_reload: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Loads all verified emission factors from SQLite into an in-memory dictionary.
    """
    global _EMISSION_FACTOR_CACHE
    if _EMISSION_FACTOR_CACHE and not force_reload:
        return _EMISSION_FACTOR_CACHE

    factors = {}
    with get_db() as session:
        records = session.query(EmissionFactor).all()
        for r in records:
            factors[r.activity] = {
                "id": r.id,
                "category": r.category,
                "activity": r.activity,
                "unit": r.unit,
                "emission_factor": r.emission_factor,
                "factor_unit": r.factor_unit,
                "region": r.region,
                "source": r.source,
                "reference_year": r.reference_year,
                "notes": r.notes
            }
    _EMISSION_FACTOR_CACHE = factors
    return _EMISSION_FACTOR_CACHE


def get_factor(activity_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve factor metadata by activity key.
    """
    factors = load_emission_factors()
    return factors.get(activity_key)


def get_factor_value(activity_key: str, default: float = 0.0) -> float:
    """
    Returns purely the numeric emission factor value (kg CO2e per unit).
    """
    record = get_factor(activity_key)
    if record:
        return float(record["emission_factor"])
    return default


def get_all_factors_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """
    Return all emission factor records for a specific category.
    """
    factors = load_emission_factors()
    return {k: v for k, v in factors.items() if v["category"] == category}
