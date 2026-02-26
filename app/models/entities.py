from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TxType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass(slots=True)
class UserProfile:
    user_id: int
    currency: str
    premium_until: datetime | None
    notifications_enabled: bool
