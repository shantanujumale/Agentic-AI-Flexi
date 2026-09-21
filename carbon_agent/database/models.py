"""
SQLAlchemy ORM Models for Emission Factors, Users, Logs, and Action Plans.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class EmissionFactor(Base):
    """
    Stores scientific, verified emission factors with full provenance.
    Never invent factors: every entry has a source and reference year.
    """
    __tablename__ = "emission_factors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)  # transportation, energy, household_fuel, food, waste
    activity = Column(String(100), nullable=False, unique=True, index=True)  # e.g., petrol_car_km
    unit = Column(String(50), nullable=False)  # km, kWh, kg, day
    emission_factor = Column(Float, nullable=False)  # kg CO2e per unit
    factor_unit = Column(String(50), nullable=False)  # kg CO2e/km
    region = Column(String(50), default="Global")  # India, Global, etc.
    source = Column(String(150), nullable=False)  # e.g., CEA India v19, UK DEFRA 2023
    reference_year = Column(Integer, nullable=False)  # 2023
    notes = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "activity": self.activity,
            "unit": self.unit,
            "emission_factor": self.emission_factor,
            "factor_unit": self.factor_unit,
            "region": self.region,
            "source": self.source,
            "reference_year": self.reference_year,
            "notes": self.notes
        }


class UserProfile(Base):
    """
    User metadata, preferences, and active emission reduction target.
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, default="default_user")
    region = Column(String(50), default="India")
    target_reduction_pct = Column(Float, default=20.0)  # e.g. 20%
    created_at = Column(DateTime, default=datetime.utcnow)

    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    action_plans = relationship("UserActionPlan", back_populates="user", cascade="all, delete-orphan")


class ActivityLog(Base):
    """
    Historical monthly carbon activity log and calculated footprint breakdown.
    """
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    month_year = Column(String(20), nullable=False)  # e.g. "2026-01"
    inputs_json = Column(Text, nullable=False)  # Normalized inputs JSON
    total_monthly_kg_co2e = Column(Float, nullable=False)
    annualized_kg_co2e = Column(Float, nullable=False)
    category_breakdown_json = Column(Text, nullable=False)  # JSON {transportation: x, electricity: y...}
    details_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfile", back_populates="activity_logs")


class ReductionAction(Base):
    """
    Catalog of domain-validated carbon reduction actions with difficulty, cost, and formula assumptions.
    """
    __tablename__ = "reduction_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(String(50), unique=True, nullable=False)  # e.g. "carpool_commute"
    category = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    formula_type = Column(String(50), nullable=False)  # pct_reduction, modal_shift, solar_offset, diet_shift
    default_reduction_pct = Column(Float, nullable=False)  # e.g., 25.0%
    difficulty = Column(String(20), nullable=False)  # Easy, Medium, Hard
    cost_tier = Column(String(20), nullable=False)  # Free, Low, Investment
    assumptions = Column(Text, nullable=False)

    def to_dict(self):
        return {
            "action_id": self.action_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "formula_type": self.formula_type,
            "default_reduction_pct": self.default_reduction_pct,
            "difficulty": self.difficulty,
            "cost_tier": self.cost_tier,
            "assumptions": self.assumptions
        }


class UserActionPlan(Base):
    """
    Generated personalized action plan tailored to reach a reduction target.
    """
    __tablename__ = "user_action_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    target_reduction_pct = Column(Float, nullable=False)
    baseline_co2e = Column(Float, nullable=False)
    target_co2e = Column(Float, nullable=False)
    projected_savings_kg = Column(Float, nullable=False)
    plan_json = Column(Text, nullable=False)  # JSON list of selected action dicts
    status = Column(String(30), default="ACTIVE")  # ACTIVE, COMPLETED, ARCHIVED
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserProfile", back_populates="action_plans")
