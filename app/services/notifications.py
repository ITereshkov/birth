from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta

import pytz
from aiogram import Bot

from app.repositories.factory import RepositoryFactory
from app.repositories.user_index import UserIndexRepository
from app.services.facts import FACTS
from app.services.premium import PremiumService

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
        now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
        for row in self.index_repo.all_users():
            user_id = int(row["user_id"])
            tz_name = row["timezone"] or "Europe/Moscow"
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.timezone("Europe/Moscow")
            local_now = now_utc.astimezone(tz)
            if local_now.hour != 20 or local_now.minute > 2:
                continue

            repo = self.factory.user_repo(user_id)
            profile = repo.get_profile(user_id)
            if not self.premium_service.is_premium(profile, datetime.utcnow()):
                continue

            naive_local = local_now.replace(tzinfo=None)
            if not repo.has_transactions_on_date(naive_local):
                await self.bot.send_message(user_id, "Внесите расход за сегодня 💸")

            last_fact = row["last_fact_at"]
            should_send_fact = True
            if last_fact:
                last_dt = datetime.fromisoformat(last_fact)
                should_send_fact = datetime.utcnow() - last_dt >= timedelta(days=random.randint(3, 7))
            if should_send_fact:
                await self.bot.send_message(user_id, f"Финансовый факт дня: {random.choice(FACTS)}")
                self.index_repo.set_last_fact_at(user_id, datetime.utcnow())
