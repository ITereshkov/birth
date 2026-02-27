from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot

from app.repositories.factory import RepositoryFactory
from app.repositories.user_index import UserIndexRepository
from app.services.facts import FACTS
from app.services.premium import PremiumService
from app.utils.date_utils import at_20_msk, now_msk

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        bot: Bot,
        factory: RepositoryFactory,
        index_repo: UserIndexRepository,
        premium_service: PremiumService,
    ) -> None:
        self.bot = bot
        self.factory = factory
        self.index_repo = index_repo
        self.premium_service = premium_service

    async def run_scheduler(self) -> None:
        while True:
            try:
                await self._tick()
            except Exception:
                logger.exception("Ошибка планировщика уведомлений")
            await asyncio.sleep(60)

    async def _tick(self) -> None:
        now = datetime.utcnow()
        if not at_20_msk(now.replace(tzinfo=ZoneInfo("UTC"))):
            return

        today = now_msk().date()
        for row in self.index_repo.all_users():
            user_id = int(row["user_id"])
            repo = self.factory.user_repo(user_id)
            profile = repo.get_profile(user_id)

            if not profile.notifications_enabled:
                continue
            if not self.premium_service.is_premium(profile, datetime.utcnow()):
                continue

            if not repo.has_transactions_on_date(today):
                await self.bot.send_message(user_id, "⚠️ Внесите расход за сегодня 💸")

            last_fact = row["last_fact_at"]
            should_send_fact = True
            if last_fact:
                last_dt = datetime.fromisoformat(last_fact)
                should_send_fact = datetime.utcnow() - last_dt >= timedelta(days=random.randint(3, 7))
            if should_send_fact:
                await self.bot.send_message(user_id, f"💡 Финансовый факт: {random.choice(FACTS)}")
                self.index_repo.set_last_fact_at(user_id, datetime.utcnow())
