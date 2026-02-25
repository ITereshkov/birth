from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from app.models.entities import TxType
from app.repositories.user_db import UserRepository


class ReportService:
    def summarize(self, repo: UserRepository, start: datetime, end: datetime) -> dict[str, Any]:
        txs = repo.get_transactions(start, end)
        income = sum(r["amount"] for r in txs if r["type"] == TxType.INCOME.value)
        expense = sum(r["amount"] for r in txs if r["type"] == TxType.EXPENSE.value)
        by_category: dict[str, float] = defaultdict(float)
        for row in txs:
            key = f"{row['type']}:{row['category']}"
            by_category[key] += float(row["amount"])
        return {
            "income": income,
            "expense": expense,
            "cash_flow": income - expense,
            "balance": income - expense,
            "transactions": txs,
            "by_category": dict(by_category),
        }
