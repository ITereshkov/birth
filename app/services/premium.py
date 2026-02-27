from __future__ import annotations

from datetime import datetime, timedelta

from app.models.entities import UserProfile


FREE_MONTHLY_LIMIT = 100


class PremiumService:
    """Все функции открыты: сервис оставлен для совместимости интерфейсов."""

    def is_premium(self, profile: UserProfile, now: datetime) -> bool:
        return True

    def can_add_transaction(self, profile: UserProfile, month_count: int, now: datetime) -> bool:
        return True

    def extend_for_30_days(self, from_dt: datetime | None = None) -> datetime:
        base = from_dt if from_dt and from_dt > datetime.utcnow() else datetime.utcnow()
        return base + timedelta(days=30)
