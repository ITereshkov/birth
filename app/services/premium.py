from __future__ import annotations

from datetime import datetime, timedelta

from app.models.entities import UserProfile


FREE_MONTHLY_LIMIT = 100


class PremiumService:
    def is_premium(self, profile: UserProfile, now: datetime) -> bool:
        return bool(profile.premium_until and profile.premium_until > now)

    def can_add_transaction(self, profile: UserProfile, month_count: int, now: datetime) -> bool:
        if self.is_premium(profile, now):
            return True
        return month_count < FREE_MONTHLY_LIMIT

    def extend_for_30_days(self, from_dt: datetime | None = None) -> datetime:
        base = from_dt if from_dt and from_dt > datetime.utcnow() else datetime.utcnow()
        return base + timedelta(days=30)
