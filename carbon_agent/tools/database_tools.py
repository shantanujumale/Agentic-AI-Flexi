"""
Database access tools for storing and retrieving user activity logs, profiles, and action plans.
"""
import json
from typing import Dict, Any, List, Optional
from carbon_agent.database.database import get_db
from carbon_agent.database.models import UserProfile, ActivityLog, ReductionAction, UserActionPlan


def get_or_create_user(username: str = "default_user", region: str = "India") -> Dict[str, Any]:
    """Retrieve existing user or create a new user profile."""
    with get_db() as session:
        user = session.query(UserProfile).filter_by(username=username).first()
        if not user:
            user = UserProfile(username=username, region=region, target_reduction_pct=20.0)
            session.add(user)
            session.flush()
        return {
            "id": user.id,
            "username": user.username,
            "region": user.region,
            "target_reduction_pct": user.target_reduction_pct,
            "created_at": str(user.created_at)
        }


def update_user_target(username: str, target_pct: float) -> bool:
    """Update target emission reduction percentage for user."""
    with get_db() as session:
        user = session.query(UserProfile).filter_by(username=username).first()
        if user:
            user.target_reduction_pct = float(target_pct)
            return True
        return False


def save_activity_log(
    username: str,
    month_year: str,
    inputs: Dict[str, Any],
    carbon_results: Dict[str, Any],
    notes: Optional[str] = None
) -> int:
    """Persist calculated monthly carbon footprint record."""
    with get_db() as session:
        user = session.query(UserProfile).filter_by(username=username).first()
        if not user:
            user = UserProfile(username=username, region="India", target_reduction_pct=20.0)
            session.add(user)
            session.flush()

        # Check if record for this month already exists to update or create
        existing = session.query(ActivityLog).filter_by(user_id=user.id, month_year=month_year).first()
        if existing:
            existing.inputs_json = json.dumps(inputs)
            existing.total_monthly_kg_co2e = carbon_results["total_monthly_kg_co2e"]
            existing.annualized_kg_co2e = carbon_results["annualized_kg_co2e"]
            existing.category_breakdown_json = json.dumps(carbon_results["categories"])
            existing.details_json = json.dumps(carbon_results.get("details", {}))
            existing.notes = notes
            log_id = existing.id
        else:
            new_log = ActivityLog(
                user_id=user.id,
                month_year=month_year,
                inputs_json=json.dumps(inputs),
                total_monthly_kg_co2e=carbon_results["total_monthly_kg_co2e"],
                annualized_kg_co2e=carbon_results["annualized_kg_co2e"],
                category_breakdown_json=json.dumps(carbon_results["categories"]),
                details_json=json.dumps(carbon_results.get("details", {})),
                notes=notes
            )
            session.add(new_log)
            session.flush()
            log_id = new_log.id

        return log_id


def get_user_history(username: str = "default_user", limit: int = 12) -> List[Dict[str, Any]]:
    """Retrieve chronological history of user activity logs."""
    with get_db() as session:
        user = session.query(UserProfile).filter_by(username=username).first()
        if not user:
            return []

        logs = (
            session.query(ActivityLog)
            .filter_by(user_id=user.id)
            .order_by(ActivityLog.month_year.asc())
            .limit(limit)
            .all()
        )

        history = []
        for log in logs:
            history.append({
                "id": log.id,
                "month_year": log.month_year,
                "total_monthly_kg_co2e": log.total_monthly_kg_co2e,
                "annualized_kg_co2e": log.annualized_kg_co2e,
                "categories": json.loads(log.category_breakdown_json),
                "inputs": json.loads(log.inputs_json),
                "notes": log.notes,
                "created_at": str(log.created_at)
            })
        return history


def get_all_reduction_actions() -> List[Dict[str, Any]]:
    """Retrieve the action catalog from database."""
    with get_db() as session:
        actions = session.query(ReductionAction).all()
        return [a.to_dict() for a in actions]


def save_user_action_plan(
    username: str,
    target_reduction_pct: float,
    baseline_co2e: float,
    target_co2e: float,
    projected_savings_kg: float,
    plan_items: List[Dict[str, Any]]
) -> int:
    """Save an actionable emission reduction plan."""
    with get_db() as session:
        user = session.query(UserProfile).filter_by(username=username).first()
        if not user:
            user = UserProfile(username=username, region="India", target_reduction_pct=target_reduction_pct)
            session.add(user)
            session.flush()

        plan = UserActionPlan(
            user_id=user.id,
            target_reduction_pct=target_reduction_pct,
            baseline_co2e=baseline_co2e,
            target_co2e=target_co2e,
            projected_savings_kg=projected_savings_kg,
            plan_json=json.dumps(plan_items),
            status="ACTIVE"
        )
        session.add(plan)
        session.flush()
        return plan.id


def get_latest_action_plan(username: str = "default_user") -> Optional[Dict[str, Any]]:
    """Fetch the latest active reduction plan."""
    with get_db() as session:
        user = session.query(UserProfile).filter_by(username=username).first()
        if not user:
            return None

        plan = (
            session.query(UserActionPlan)
            .filter_by(user_id=user.id, status="ACTIVE")
            .order_by(UserActionPlan.created_at.desc())
            .first()
        )
        if not plan:
            return None

        return {
            "id": plan.id,
            "target_reduction_pct": plan.target_reduction_pct,
            "baseline_co2e": plan.baseline_co2e,
            "target_co2e": plan.target_co2e,
            "projected_savings_kg": plan.projected_savings_kg,
            "plan_items": json.loads(plan.plan_json),
            "status": plan.status,
            "created_at": str(plan.created_at)
        }
