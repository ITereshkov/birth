from __future__ import annotations

import logging
from datetime import datetime

import pytz
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LabeledPrice, Message, PreCheckoutQuery

from app.keyboards.common import (
    category_create_keyboard,
    period_keyboard,
    premium_buy_keyboard,
    quick_actions_keyboard,
    tx_type_keyboard,
)
from app.models.entities import TxType
from app.repositories.factory import RepositoryFactory
from app.repositories.user_index import UserIndexRepository
from app.services.ai_analysis import AIAnalysisService
from app.services.exporter import ExportService
from app.services.premium import PremiumService
from app.services.reports import ReportService
from app.utils.date_utils import month_range, today_range, week_range
from app.utils.parser import parse_entry
from .states import CustomRangeStates, SetupStates, TransactionStates

logger = logging.getLogger(__name__)
router = Router()


def _now_user_tz(timezone: str) -> datetime:
    tz = pytz.timezone(timezone)
    return datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(tz).replace(tzinfo=None)


def _is_premium(premium_service: PremiumService, profile, now: datetime) -> bool:
    return premium_service.is_premium(profile, now)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, repo_factory: RepositoryFactory, index_repo: UserIndexRepository) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    repo.ensure_profile(user_id)
    index_repo.ensure_user(user_id)
    await state.set_state(SetupStates.waiting_timezone)
    await message.answer(
        "Привет! Я ваш личный финансовый агент 💼\n"
        "Отправляйте записи так: `5800 зп`, `-1200 еда`, `+5000 подработка`.\n"
        "Выберите таймзону (например Europe/Moscow).\n\n"
        "📱 Чтобы быстро открывать бота: закрепите чат или добавьте веб-ярлык Telegram на главный экран.",
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(SetupStates.waiting_timezone)
async def setup_timezone(message: Message, state: FSMContext, repo_factory: RepositoryFactory, index_repo: UserIndexRepository) -> None:
    tz = message.text.strip()
    try:
        pytz.timezone(tz)
    except Exception:
        await message.answer("Не узнал таймзону. Пример: Europe/Moscow")
        return
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    repo.update_timezone(user_id, tz)
    index_repo.update_timezone(user_id, tz)
    await state.clear()
    await message.answer("Отлично! Таймзона сохранена. Напишите первую запись 💰")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/balance — баланс за период\n"
        "/export — выгрузка в Excel (Premium)\n"
        "/analize — ИИ-анализ (Premium)\n"
        "/premium — статус и покупка\n"
        "/consult — консультация\n\n"
        "Примеры ввода:\n"
        "`5800 зп`, `-1200 еда`, `+15000 фриланс`, `1200 такси вчера`, `2500 продукты 25.02`\n\n"
        "📱 Чтобы не потерять бота: закрепите чат или вынесите Telegram на главный экран.",
        parse_mode=ParseMode.MARKDOWN,
    )


@router.message(Command("consult"))
async def cmd_consult(message: Message, consult_url: str) -> None:
    await message.answer(f"Записаться на консультацию: {consult_url}")


@router.message(Command("premium"))
async def cmd_premium(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    now = datetime.utcnow()
    if _is_premium(premium_service, profile, now):
        await message.answer(f"Premium активен до {profile.premium_until:%d.%m.%Y}")
    else:
        await message.answer("Сейчас у вас Free. Лимит: 100 записей/месяц.", reply_markup=premium_buy_keyboard())


@router.callback_query(F.data == "premium:buy")
async def cb_buy_premium(callback: CallbackQuery) -> None:
    await callback.message.answer_invoice(
        title="Premium на 30 дней",
        description="Безлимит, экспорт, уведомления и ИИ-анализ",
        payload="premium_30_days",
        currency="XTR",
        prices=[LabeledPrice(label="Premium", amount=100)],
        provider_token="",
    )
    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    premium_until = premium_service.extend_for_30_days(profile.premium_until)
    repo.set_premium_until(user_id, premium_until)
    await message.answer(f"Оплата прошла успешно! Premium активен до {premium_until:%d.%m.%Y}")


async def _send_balance(message: Message, repo_factory: RepositoryFactory, report_service: ReportService, period: str = "month") -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    now = _now_user_tz(profile.timezone)
    if period == "today":
        dr = today_range(now.date())
    elif period == "week":
        dr = week_range(now.date())
    else:
        dr = month_range(now.date())
    summary = report_service.summarize(repo, dr.start, dr.end)
    await message.answer(
        f"Период: {period}\n"
        f"Доходы: {summary['income']:.2f} ₽\n"
        f"Расходы: {summary['expense']:.2f} ₽\n"
        f"Cash flow: {summary['cash_flow']:.2f} ₽\n"
        f"Баланс: {summary['balance']:.2f} ₽"
    )


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    await message.answer("Выберите период", reply_markup=period_keyboard("balance"))


@router.message(Command("export"))
async def cmd_export(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService, export_service: ExportService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    now = _now_user_tz(profile.timezone)
    if not premium_service.is_premium(profile, datetime.utcnow()):
        await message.answer("Экспорт доступен только в Premium.", reply_markup=premium_buy_keyboard())
        return
    dr = month_range(now.date())
    out_path = export_service.export_xlsx(repo, dr.start, dr.end, repo_factory.user_db_dir / f"export_{user_id}.xlsx")
    await message.answer_document(FSInputFile(out_path), caption="Ваш Excel-отчёт готов")


@router.message(Command("analize"))
async def cmd_analize(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService, ai_service: AIAnalysisService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    if not premium_service.is_premium(profile, datetime.utcnow()):
        await message.answer("ИИ-анализ доступен только в Premium.", reply_markup=premium_buy_keyboard())
        return
    now = _now_user_tz(profile.timezone)
    dr = month_range(now.date())
    text = ai_service.analyze(repo, dr.start, dr.end)
    await message.answer(f"🤖 ИИ-анализ:\n{text}")


@router.callback_query(F.data.startswith("period:"))
async def cb_period(callback: CallbackQuery, repo_factory: RepositoryFactory, report_service: ReportService, state: FSMContext) -> None:
    _, target, period = callback.data.split(":")
    if period == "custom":
        await state.set_state(CustomRangeStates.waiting_start)
        await state.update_data(period_target=target)
        await callback.message.answer("Введите дату начала в формате ГГГГ-ММ-ДД")
        await callback.answer()
        return
    if target == "balance":
        await _send_balance(callback.message, repo_factory, report_service, period)
    await callback.answer()


@router.message(CustomRangeStates.waiting_start)
async def custom_start(message: Message, state: FSMContext) -> None:
    try:
        datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.answer("Неверный формат. Пример: 2026-02-01")
        return
    await state.update_data(start=message.text.strip())
    await state.set_state(CustomRangeStates.waiting_end)
    await message.answer("Введите дату конца в формате ГГГГ-ММ-ДД")


@router.message(CustomRangeStates.waiting_end)
async def custom_end(message: Message, state: FSMContext, repo_factory: RepositoryFactory, report_service: ReportService) -> None:
    try:
        end = datetime.strptime(message.text.strip(), "%Y-%m-%d")
    except ValueError:
        await message.answer("Неверный формат. Пример: 2026-02-28")
        return
    data = await state.get_data()
    start = datetime.strptime(data["start"], "%Y-%m-%d")
    target = data.get("period_target", "balance")
    if target == "balance":
        user_id = message.from_user.id
        repo = repo_factory.user_repo(user_id)
        summary = report_service.summarize(repo, start, end)
        await message.answer(
            f"Доходы: {summary['income']:.2f} ₽\nРасходы: {summary['expense']:.2f} ₽\nБаланс: {summary['balance']:.2f} ₽"
        )
    await state.clear()


@router.callback_query(F.data.startswith("quick:"))
async def cb_quick(callback: CallbackQuery) -> None:
    action = callback.data.split(":", maxsplit=1)[1]
    if action == "add":
        await callback.message.answer("Отправьте следующую запись, например: -450 кофе")
    elif action == "balance":
        await callback.message.answer("Выберите период", reply_markup=period_keyboard("balance"))
    elif action == "export":
        await callback.message.answer("Вызовите команду /export")
    elif action == "analyze":
        await callback.message.answer("Вызовите команду /analize")
    await callback.answer()


@router.message(F.text)
async def capture_transaction(
    message: Message,
    state: FSMContext,
    repo_factory: RepositoryFactory,
    premium_service: PremiumService,
) -> None:
    text = message.text.strip()
    if text.startswith("/"):
        return
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    now = _now_user_tz(profile.timezone)
    parsed = parse_entry(text, now)
    if not parsed:
        return

    month_count = repo.month_tx_count(now.year, now.month)
    if not premium_service.can_add_transaction(profile, month_count, datetime.utcnow()):
        await message.answer("Лимит Free: 100 записей/месяц. Подключите Premium.", reply_markup=premium_buy_keyboard())
        return

    await state.update_data(pending_amount=parsed.amount, pending_category=parsed.category, pending_date=parsed.tx_date.isoformat())

    if parsed.tx_type is None:
        await state.set_state(TransactionStates.waiting_tx_type)
        await message.answer("Уточните тип операции", reply_markup=tx_type_keyboard())
        return

    await _save_transaction(message, state, repo_factory, parsed.tx_type)


@router.callback_query(TransactionStates.waiting_tx_type, F.data.startswith("confirm:"))
async def cb_confirm_type(callback: CallbackQuery, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    tx_type_name = callback.data.split(":")[1]
    tx_type = TxType.INCOME if tx_type_name == "income" else TxType.EXPENSE
    await _save_transaction(callback.message, state, repo_factory, tx_type)
    await callback.answer()


async def _save_transaction(message: Message, state: FSMContext, repo_factory: RepositoryFactory, tx_type: TxType) -> None:
    data = await state.get_data()
    user_id = message.chat.id
    repo = repo_factory.user_repo(user_id)
    amount = float(data["pending_amount"])
    category = str(data["pending_category"]).strip().lower()
    tx_date = datetime.fromisoformat(data["pending_date"])

    if not repo.category_exists(category, tx_type):
        await state.set_state(TransactionStates.waiting_category_confirm)
        await state.update_data(pending_type=tx_type.value)
        await message.answer(f"Категория «{category}» не найдена.", reply_markup=category_create_keyboard())
        return

    repo.add_transaction(amount=amount, category=category, tx_type=tx_type, happened_at=tx_date)
    await state.clear()
    action = "доход" if tx_type == TxType.INCOME else "расход"
    await message.answer(
        f"Зафиксирован {action}: {amount:.2f} ₽ в категории '{category}' ({tx_date:%d.%m.%Y})",
        reply_markup=quick_actions_keyboard(),
    )


@router.callback_query(TransactionStates.waiting_category_confirm, F.data == "category:create")
async def cb_create_category(callback: CallbackQuery, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    data = await state.get_data()
    tx_type = TxType(data["pending_type"])
    user_id = callback.from_user.id
    repo = repo_factory.user_repo(user_id)
    category = str(data["pending_category"]).lower()
    repo.add_category(category, tx_type)
    await callback.message.answer(f"Категория «{category}» создана, сохраняю запись...")
    await _save_transaction(callback.message, state, repo_factory, tx_type)
    await callback.answer()
