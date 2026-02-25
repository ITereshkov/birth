from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TxType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass(slots=True)
class Transaction:
    id: int
    amount: float
    category: str
    tx_type: TxType
    happened_at: datetime
    comment: str | None = None


@dataclass(slots=True)
class UserProfile:
    user_id: int
    timezone: str
    currency: str
    premium_until: datetime | None
    notifications_enabled: bool
