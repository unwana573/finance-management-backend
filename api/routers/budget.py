from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from api.core.database import get_db
from api.core.dependencies import get_current_user
from api.models import User
from api.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetSummaryResponse
from api.services.budget_service import BudgetService

router = APIRouter(prefix="/budget", tags=["Budget"])


@router.get("/summary", response_model=BudgetSummaryResponse)
def get_budget_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns total budget, total spent, remaining, percent used
    and full category breakdown with progress bar data.
    Never returns 404 — safe to call on page load even for new users.
    If budget_exists=False, prompt the user to create a budget.
    """
    return BudgetService(db).get_summary(current_user.id)


@router.get("", response_model=BudgetResponse)
def get_budget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns full budget object for the current month. Returns 404 if not set."""
    return BudgetService(db).get_current(current_user.id)


@router.get("/month", response_model=BudgetResponse)
def get_budget_by_month(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns budget for a specific month. Example: /budget/month?year=2026&month=3"""
    return BudgetService(db).get_by_month(current_user.id, year, month)


@router.post("", response_model=BudgetResponse, status_code=201)
def create_budget(
    body: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).create(current_user.id, body)


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    body: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).update(current_user.id, budget_id, body)


@router.patch("/categories/{budget_id}/{category_id}")
def update_category_limit(
    budget_id: int,
    category_id: int,
    limit: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return BudgetService(db).update_category(current_user.id, budget_id, category_id, limit)