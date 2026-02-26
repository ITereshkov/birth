from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from app.config import load_settings
from app.handlers.main import router
from app.repositories.factory import RepositoryFactory
from app.repositories.user_index import UserIndexRepository
from app.services.ai_analysis import AIAnalysisService
from app.services.exporter import ExportService
from app.services.notifications import NotificationService
from app.services.premium import PremiumService
from app.services.reports import ReportService


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def run() -> None:
    load_dotenv()
    setup_logging()
    settings = load_settings()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    repo_factory = RepositoryFactory(settings.user_db_dir)
    index_repo = UserIndexRepository(settings.users_index_path)
    report_service = ReportService()
    premium_service = PremiumService()
    export_service = ExportService(report_service, settings.export_template_path)
    ai_service = AIAnalysisService(
        api_key=settings.openai_api_key,
        report_service=report_service,
        openrouter_api_key=settings.openrouter_api_key,
        openrouter_model=settings.openrouter_model,
    )

    dp.include_router(router)
    dp["repo_factory"] = repo_factory
    dp["index_repo"] = index_repo
    dp["report_service"] = report_service
    dp["premium_service"] = premium_service
    dp["export_service"] = export_service
    dp["ai_service"] = ai_service
    dp["consult_url"] = settings.consult_url

    notifier = NotificationService(bot, repo_factory, index_repo, premium_service)
    scheduler_task = asyncio.create_task(notifier.run_scheduler())

    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run())
