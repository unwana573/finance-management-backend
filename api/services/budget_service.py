from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.repositories.budget_repo import BudgetRepository, BudgetItemRepository
from api.models import Transaction, TransactionType, Category
from api.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetItemResponse, BudgetSummaryResponse


class BudgetService:
    def __init__(self, db: Session):
        self.budget_repo = BudgetRepository(db)
        self.item_repo = BudgetItemRepository(db)
        self.db = db

    def _spent_for_category(self, user_id: int, category_id: int, year: int, month: int) -> float:
        result = (
            self.db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.type == TransactionType.expense,
                func.extract("year", Transaction.date) == year,
                func.extract("month", Transaction.date) == month,
            )
            .scalar()
        )
        return float(result or 0)

    def _category_name(self, category_id: int) -> str:
        cat = self.db.query(Category).filter(Category.id == category_id).first()
        return cat.name if cat else "Uncategorised"

    def get_current(self, user_id: int) -> BudgetResponse:
        now = datetime.utcnow()
        budget = self.budget_repo.get_by_month(user_id, now.year, now.month)
        if not budget:
            raise HTTPException(status_code=404, detail="No budget set for this month")
        return self._build_response(user_id, budget)

    def get_by_month(self, user_id: int, year: int, month: int) -> BudgetResponse:
        budget = self.budget_repo.get_by_month(user_id, year, month)
        if not budget:
            raise HTTPException(status_code=404, detail=f"No budget set for {year}-{month:02d}")
        return self._build_response(user_id, budget)

    def get_summary(self, user_id: int) -> BudgetSummaryResponse:
        """
        Always returns budget summary for the current month.
        If no budget is set, returns zeros — never 404.
        Safe to call on page load for new users.
        """
        now = datetime.utcnow()
        budget = self.budget_repo.get_by_month(user_id, now.year, now.month)

        if not budget:
            return BudgetSummaryResponse(
                budget_exists=False,
                month=now.month,
                year=now.year,
                total_budget=0.0,
                total_spent=0.0,
                remaining=0.0,
                percent_used=0.0,
                categories=[],
            )

        response = self._build_response(user_id, budget)
        percent_used = round(
            (response.total_spent / response.total_budget * 100), 1
        ) if response.total_budget > 0 else 0.0

        return BudgetSummaryResponse(
            budget_exists=True,
            month=response.month,
            year=response.year,
            total_budget=response.total_budget,
            total_spent=response.total_spent,
            remaining=response.remaining,
            percent_used=percent_used,
            categories=response.items,
        )

    def create(self, user_id: int, body: BudgetCreate) -> BudgetResponse:
        existing = self.budget_repo.get_by_month(user_id, body.year, body.month)
        if existing:
            raise HTTPException(status_code=409, detail="Budget already exists for this month")

        budget = self.budget_repo.create({
            "user_id": user_id,
            "month": body.month,
            "year": body.year,
        })
        for item in body.items:
            self.item_repo.create({
                "budget_id": budget.id,
                "category_id": item.category_id,
                "limit": item.limit,
            })
        return self._build_response(user_id, budget)

    def update(self, user_id: int, budget_id: int, body: BudgetUpdate) -> BudgetResponse:
        budget = self.budget_repo.get(budget_id)
        if not budget or budget.user_id != user_id:
            raise HTTPException(status_code=404, detail="Budget not found")
        for item in body.items:
            self.item_repo.upsert(budget.id, item.category_id, item.limit)
        return self._build_response(user_id, budget)

    def update_category(self, user_id: int, budget_id: int, category_id: int, limit: float):
        budget = self.budget_repo.get(budget_id)
        if not budget or budget.user_id != user_id:
            raise HTTPException(status_code=404, detail="Budget not found")
        return self.item_repo.upsert(budget.id, category_id, limit)

    def _build_response(self, user_id: int, budget) -> BudgetResponse:
        item_responses = []
        total_budget = 0.0
        total_spent = 0.0

        for item in budget.items:
            spent = self._spent_for_category(
                user_id, item.category_id, budget.year, budget.month
            )
            limit = float(item.limit)
            remaining = limit - spent
            percent_used = round((spent / limit) * 100, 1) if limit > 0 else 0.0
            total_budget += limit
            total_spent += spent

            item_responses.append(BudgetItemResponse(
                id=item.id,
                category_id=item.category_id,
                category_name=self._category_name(item.category_id),
                limit=limit,
                spent=spent,
                remaining=remaining,
                percent_used=percent_used,
            ))

        return BudgetResponse(
            id=budget.id,
            month=budget.month,
            year=budget.year,
            total_budget=total_budget,
            total_spent=total_spent,
            remaining=total_budget - total_spent,
            items=item_responses,
        )