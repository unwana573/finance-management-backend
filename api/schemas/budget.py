from typing import List, Optional
from pydantic import BaseModel


class BudgetItemCreate(BaseModel):
    category_id: int
    limit: float


class BudgetItemResponse(BaseModel):
    id: int
    category_id: int
    category_name: Optional[str] = None
    limit: float
    spent: float = 0.0
    remaining: float = 0.0
    percent_used: float = 0.0

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    month: int
    year: int
    items: List[BudgetItemCreate]


class BudgetUpdate(BaseModel):
    items: List[BudgetItemCreate]


class BudgetResponse(BaseModel):
    id: int
    month: int
    year: int
    total_budget: float
    total_spent: float
    remaining: float
    items: List[BudgetItemResponse]

    class Config:
        from_attributes = True


class BudgetSummaryResponse(BaseModel):
    """
    Always returns data even if no budget is set.
    Use this for the Budget page on load.
    budget_exists = False means user hasn't created a budget yet —
    show a prompt to create one.
    """
    budget_exists: bool
    month: int
    year: int
    total_budget: float
    total_spent: float
    remaining: float
    percent_used: float
    categories: List[BudgetItemResponse]