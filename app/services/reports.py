from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.models.entities import TxType
from app.repositories.user_db import UserRepository


class ReportService:
    def summarize(self, repo: UserRepository, start: date, end: date) -> dict[str, Any]:
        txs = repo.get_transactions_by_date_range(start, end)
        income = sum(float(r["amount"]) for r in txs if r["type"] == TxType.INCOME.value)
        expense = sum(float(r["amount"]) for r in txs if r["type"] == TxType.EXPENSE.value)

        expense_by_category: dict[str, float] = defaultdict(float)
        for row in txs:
            if row["type"] == TxType.EXPENSE.value:
                expense_by_category[str(row["category"])] += float(row["amount"])

        top_expenses = sorted(expense_by_category.items(), key=lambda item: item[1], reverse=True)[:3]

        return {
            "income": income,
            "expense": expense,
            "difference": income - expense,
            "transactions": txs,
            "top_expenses": top_expenses,
        }
