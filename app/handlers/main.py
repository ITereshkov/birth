from __future__ import annotations

from datetime import date, datetime, timedelta

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, PreCheckoutQuery, ReactionTypeEmoji

from app.keyboards.common import (
    HIDE_MENU,
    MAIN_MENU,
    after_save_keyboard,
    categories_keyboard,
    period_keyboard,
    settings_keyboard,
    type_choice_keyboard,
    cancel_only_keyboard,
)
from app.models.entities import TxType
from app.repositories.factory import RepositoryFactory
from app.repositories.user_index import UserIndexRepository
from app.services.ai_analysis import AIAnalysisService
from app.services.exporter import ExportService
from app.services.premium import PremiumService
from app.services.reports import ReportService
from app.utils.date_utils import (
    format_human_date,
    month_range,
    now_msk,
    now_utc,
    parse_user_date,
    today_range,
    week_range,
)
from app.utils.parser import parse_entry
from .states import OperationStates, PeriodStates

router = Router()


def _type_from_text(text: str) -> TxType | None:
    return TxType.EXPENSE if text == "➖ Расход" else TxType.INCOME if text == "➕ Доход" else None


def _period_range(period: str) -> tuple[date, date]:
    if period == "today":
        dr = today_range()
    elif period == "week":
        dr = week_range()
    else:
        dr = month_range()
    return dr.start_date, dr.end_date


async def _show_start(message: Message) -> None:
    await message.answer(
        "👋 Привет! Я ФинАгент — бот для записи личных финансов.\n"
        "💼 Помогаю фиксировать доходы/расходы, видеть итоги за день/неделю/месяц и понимать, куда уходят деньги.\n\n"
        "🧭 Как пользоваться:\n"
        "1) Нажми ➖ Расход или ➕ Доход\n"
        "2) Введи сумму\n"
        "3) Выбери категорию — готово ✅\n\n"
        "👇 Начнем:",
        reply_markup=MAIN_MENU,
    )


@router.message(Command("start"))
async def cmd_start(message: Message, repo_factory: RepositoryFactory, index_repo: UserIndexRepository) -> None:
    user_id = message.chat.id
    repo = repo_factory.user_repo(user_id)
    repo.ensure_profile(user_id)
    index_repo.ensure_user(user_id)
    await _show_start(message)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "❓ Нужна помощь? Просто нажмите кнопки меню снизу.\n"
        "📌 Без ручного ввода категорий: выберите сумму → категорию кнопками.",
        reply_markup=MAIN_MENU,
    )


@router.message(F.text.in_(["➖ Расход", "➕ Доход"]))
async def start_operation(message: Message, state: FSMContext) -> None:
    tx_type = _type_from_text(message.text)
    await state.set_state(OperationStates.waiting_amount)
    await state.update_data(tx_type=tx_type.value, source_message_id=message.message_id)
    await message.answer("Введите сумму одной строкой, например: 1250", reply_markup=HIDE_MENU)
    await message.answer("Если передумали — нажмите отмену.", reply_markup=cancel_only_keyboard())


@router.message(OperationStates.waiting_amount)
async def receive_amount(message: Message, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    parsed = parse_entry(message.text)
    if not parsed:
        await message.answer("⚠️ Не понял сумму. Введите число, например: 1250", reply_markup=HIDE_MENU)
        return

    data = await state.get_data()
    tx_type = TxType(data["tx_type"])
    category_hint = parsed.category
    await state.update_data(amount=parsed.amount, category_hint=category_hint, source_message_id=message.message_id)
    await _show_categories(message, state, repo_factory, tx_type, page=0)


async def _show_categories(
    message: Message,
    state: FSMContext,
    repo_factory: RepositoryFactory,
    tx_type: TxType,
    page: int,
) -> None:
    user_id = message.chat.id
    repo = repo_factory.user_repo(user_id)
    categories = repo.list_categories(tx_type)
    await state.set_state(OperationStates.waiting_category)
    await state.update_data(tx_type=tx_type.value, category_page=page)
    await message.answer(
        "🏷 Выберите категорию:",
        reply_markup=categories_keyboard(categories, tx_type.value, page),
    )


@router.callback_query(F.data.startswith("catpage:"))
async def cb_cat_page(callback: CallbackQuery, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    _, tx_type, page = callback.data.split(":")
    await _show_categories(callback.message, state, repo_factory, TxType(tx_type), int(page))
    await callback.answer()


@router.callback_query(F.data.startswith("catnew:"))
async def cb_cat_new(callback: CallbackQuery, state: FSMContext) -> None:
    tx_type = callback.data.split(":")[1]
    await state.set_state(OperationStates.waiting_new_category)
    await state.update_data(tx_type=tx_type)
    await callback.message.answer("Введите название новой категории одной строкой", reply_markup=HIDE_MENU)
    await callback.message.answer("Если передумали — нажмите отмену.", reply_markup=cancel_only_keyboard())
    await callback.answer()


@router.message(OperationStates.waiting_new_category)
async def create_new_category(message: Message, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    category = message.text.strip().lower()
    if not category:
        await message.answer("⚠️ Название пустое. Введите категорию текстом.")
        return
    data = await state.get_data()
    tx_type = TxType(data["tx_type"])
    user_id = message.chat.id
    repo = repo_factory.user_repo(user_id)
    repo.add_category(category, tx_type)
    await state.update_data(selected_category=category, source_message_id=message.message_id)
    await _save_operation(message, state, repo_factory)


@router.callback_query(F.data.startswith("cat:"))
async def cb_choose_category(callback: CallbackQuery, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    _, tx_type, _page, category = callback.data.split(":", maxsplit=3)
    await state.update_data(tx_type=tx_type, selected_category=category)
    await _save_operation(callback.message, state, repo_factory)
    await callback.answer()


async def _save_operation(message: Message, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    data = await state.get_data()
    user_id = message.chat.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    today = now_msk().date()
    month_count = repo.month_tx_count(today.year, today.month)

    tx_type = TxType(data["tx_type"])
    amount = float(data["amount"])
    category = str(data["selected_category"]).lower()

    source_message_id = data.get("source_message_id")
    tx_id = repo.add_transaction(amount, category, tx_type, now_utc())
    await state.clear()
    await state.update_data(last_tx_id=tx_id)

    if tx_type == TxType.INCOME and source_message_id:
        try:
            await message.bot.set_message_reaction(
                chat_id=user_id,
                message_id=int(source_message_id),
                reaction=[ReactionTypeEmoji(emoji="🔥")],
            )
        except Exception:
            pass

    human_date = format_human_date(now_msk().date())
    if tx_type == TxType.INCOME:
        text = (
            "🔥 Так держать!\n"
            f"➕ +{amount:.2f} ₽\n"
            f"🏷 Категория: {category}\n"
            f"📅 {human_date}\n\n"
            "✅ Записал."
        )
    else:
        text = (
            "📉 Расход записан!\n"
            f"➖ -{amount:.2f} ₽\n"
            f"🏷 Категория: {category}\n"
            f"📅 {human_date}\n\n"
            "✅ Готово."
        )
    await message.answer(text, reply_markup=after_save_keyboard())


@router.callback_query(F.data == "tx:undo")
async def cb_undo(callback: CallbackQuery, repo_factory: RepositoryFactory) -> None:
    user_id = callback.from_user.id
    repo = repo_factory.user_repo(user_id)
    last = repo.get_last_transaction()
    if not last:
        await callback.message.answer("⚠️ Нечего отменять")
    else:
        created = datetime.fromisoformat(last["created_at"])
        if datetime.utcnow() - created <= timedelta(minutes=5):
            repo.delete_transaction(int(last["id"]))
            await callback.message.answer("✅ Последняя операция отменена")
        else:
            await callback.message.answer("⚠️ Можно отменить только свежую операцию (до 5 минут).")
    await callback.answer()


@router.callback_query(F.data == "tx:recat")
async def cb_recat(callback: CallbackQuery) -> None:
    await callback.message.answer("⚠️ Для смены категории проще отменить и добавить заново.")
    await callback.answer()


async def _send_summary(message: Message, repo_factory: RepositoryFactory, report_service: ReportService, period: str) -> None:
    start, end = _period_range(period)
    repo = repo_factory.user_repo(message.chat.id)
    summary = report_service.summarize(repo, start, end)

    period_label = {"today": "сегодня", "week": "неделю", "month": "месяц"}.get(period, "период")
    top = ", ".join([f"{name}: {amt:.0f}₽" for name, amt in summary["top_expenses"]]) or "—"
    await message.answer(
        f"📊 Итоги за {period_label}\n"
        f"➕ Доходы: {summary['income']:.2f} ₽\n"
        f"➖ Расходы: {summary['expense']:.2f} ₽\n"
        f"💠 Разница: {summary['difference']:.2f} ₽\n"
        f"🏷 Топ-расходы: {top}",
        reply_markup=period_keyboard(),
    )


@router.message(F.text == "📊 Итоги")
@router.message(Command("balance"))
async def show_summary(message: Message, repo_factory: RepositoryFactory, report_service: ReportService) -> None:
    await _send_summary(message, repo_factory, report_service, "today")


@router.callback_query(F.data.startswith("period:"))
async def cb_period(callback: CallbackQuery, state: FSMContext, repo_factory: RepositoryFactory, report_service: ReportService) -> None:
    period = callback.data.split(":")[1]
    if period == "custom":
        await state.set_state(PeriodStates.waiting_start)
        await callback.message.answer("Введите дату начала: ГГГГ-ММ-ДД", reply_markup=HIDE_MENU)
        await callback.message.answer("Если передумали — нажмите отмену.", reply_markup=cancel_only_keyboard())
        await callback.answer()
        return

    await _send_summary(callback.message, repo_factory, report_service, period)
    await callback.answer()


@router.message(PeriodStates.waiting_start)
async def custom_start(message: Message, state: FSMContext) -> None:
    start = parse_user_date(message.text)
    if not start:
        await message.answer("⚠️ Формат даты: ГГГГ-ММ-ДД")
        return
    await state.update_data(start_date=start.isoformat())
    await state.set_state(PeriodStates.waiting_end)
    await message.answer("Введите дату конца: ГГГГ-ММ-ДД", reply_markup=HIDE_MENU)
    await message.answer("Если передумали — нажмите отмену.", reply_markup=cancel_only_keyboard())


@router.message(PeriodStates.waiting_end)
async def custom_end(message: Message, state: FSMContext, repo_factory: RepositoryFactory, report_service: ReportService) -> None:
    end = parse_user_date(message.text)
    if not end:
        await message.answer("⚠️ Формат даты: ГГГГ-ММ-ДД")
        return

    data = await state.get_data()
    start = date.fromisoformat(data["start_date"])
    repo = repo_factory.user_repo(message.chat.id)
    summary = report_service.summarize(repo, start, end)
    await message.answer(
        f"📊 Итоги за период\n"
        f"➕ Доходы: {summary['income']:.2f} ₽\n"
        f"➖ Расходы: {summary['expense']:.2f} ₽\n"
        f"💠 Разница: {summary['difference']:.2f} ₽",
        reply_markup=period_keyboard(),
    )
    await state.clear()


@router.message(F.text == "📋 Операции")
async def show_operations(message: Message, repo_factory: RepositoryFactory) -> None:
    repo = repo_factory.user_repo(message.chat.id)
    start, end = _period_range("month")
    txs = repo.get_transactions_by_date_range(start, end)[:10]
    if not txs:
        await message.answer("📋 Пока операций нет")
        return
    lines = ["📋 Последние операции:"]
    for row in txs:
        sign = "+" if row["type"] == TxType.INCOME.value else "-"
        icon = "🔥" if row["type"] == TxType.INCOME.value else "📉"
        lines.append(f"{icon} {row['occurred_date']} {sign}{float(row['amount']):.2f} ₽ • {row['category']}")
    await message.answer("\n".join(lines))


@router.message(F.text == "📂 Экспорт")
@router.message(Command("export"))
async def cmd_export(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService, export_service: ExportService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    dr = month_range()
    out_path = export_service.export_xlsx(repo, dr.start_date, dr.end_date, repo_factory.user_db_dir / f"export_{user_id}.xlsx")
    await message.answer_document(FSInputFile(out_path), caption="✅ Файл Excel готов")


@router.message(F.text == "🤖 Анализ")
@router.message(Command("analize"))
async def cmd_analize(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService, ai_service: AIAnalysisService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    dr = month_range()
    text = ai_service.analyze(repo, dr.start_date, dr.end_date)
    await message.answer(f"🤖 Анализ:\n{text}")


@router.message(F.text == "⭐ Premium")
@router.message(Command("premium"))
async def cmd_premium(message: Message, repo_factory: RepositoryFactory, premium_service: PremiumService) -> None:
    user_id = message.from_user.id
    repo = repo_factory.user_repo(user_id)
    profile = repo.get_profile(user_id)
    now = datetime.utcnow()
    await message.answer("✅ Все функции сейчас бесплатны: экспорт, анализ и уведомления уже доступны.")


@router.callback_query(F.data == "premium:buy")
async def cb_buy_premium(callback: CallbackQuery) -> None:
    await callback.message.answer("✅ Сейчас оплачивать ничего не нужно — все функции бесплатны.")
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
    await message.answer(f"✅ Premium активирован до {premium_until:%d.%m.%Y}")


@router.message(F.text == "⚙️ Настройки")
@router.message(Command("settings"))
async def cmd_settings(message: Message, repo_factory: RepositoryFactory) -> None:
    repo = repo_factory.user_repo(message.chat.id)
    profile = repo.get_profile(message.chat.id)
    await message.answer("⚙️ Настройки", reply_markup=settings_keyboard(profile.notifications_enabled))


@router.callback_query(F.data == "settings:toggle_notify")
async def cb_toggle_notify(callback: CallbackQuery, repo_factory: RepositoryFactory, premium_service: PremiumService) -> None:
    repo = repo_factory.user_repo(callback.from_user.id)
    profile = repo.get_profile(callback.from_user.id)
    repo.set_notifications_enabled(callback.from_user.id, not profile.notifications_enabled)
    profile = repo.get_profile(callback.from_user.id)
    await callback.message.answer("✅ Настройки обновлены", reply_markup=settings_keyboard(profile.notifications_enabled))
    await callback.answer()


@router.callback_query(F.data == "settings:categories")
async def cb_settings_categories(callback: CallbackQuery, repo_factory: RepositoryFactory) -> None:
    repo = repo_factory.user_repo(callback.from_user.id)
    income = ", ".join(repo.list_categories(TxType.INCOME)[:10])
    expense = ", ".join(repo.list_categories(TxType.EXPENSE)[:10])
    await callback.message.answer(f"🏷 Доходы: {income}\n🏷 Расходы: {expense}")
    await callback.answer()


@router.callback_query(F.data == "menu:summary")
async def cb_menu_summary(callback: CallbackQuery, repo_factory: RepositoryFactory, report_service: ReportService) -> None:
    await _send_summary(callback.message, repo_factory, report_service, "today")
    await callback.answer()


@router.callback_query(F.data == "menu:add")
async def cb_menu_add(callback: CallbackQuery) -> None:
    await callback.message.answer("Выберите тип операции в меню: ➖ Расход или ➕ Доход", reply_markup=MAIN_MENU)
    await callback.answer()


@router.callback_query(F.data == "menu:ops")
async def cb_menu_ops(callback: CallbackQuery, repo_factory: RepositoryFactory) -> None:
    await show_operations(callback.message, repo_factory)
    await callback.answer()


@router.callback_query(F.data == "back:menu")
async def cb_back_menu(callback: CallbackQuery) -> None:
    await callback.message.answer("Главное меню 👇", reply_markup=MAIN_MENU)
    await callback.answer()


@router.message(F.text)
async def free_text_input(message: Message, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    text = message.text.strip()
    if text.startswith("/"):
        return

    parsed = parse_entry(text)
    if not parsed:
        return

    await state.update_data(amount=parsed.amount, category_hint=parsed.category, source_message_id=message.message_id)
    if parsed.tx_type is None:
        await state.set_state(OperationStates.waiting_type)
        await message.answer("❓ Это доход или расход?", reply_markup=type_choice_keyboard())
        return

    await state.update_data(tx_type=parsed.tx_type.value)
    await _show_categories(message, state, repo_factory, parsed.tx_type, page=0)


@router.callback_query(OperationStates.waiting_type, F.data.startswith("type:"))
async def cb_choose_type(callback: CallbackQuery, state: FSMContext, repo_factory: RepositoryFactory) -> None:
    action = callback.data.split(":")[1]
    if action == "cancel":
        await state.clear()
        await callback.message.answer("Операция отменена")
        await callback.answer()
        return

    tx_type = TxType(action)
    await state.update_data(tx_type=tx_type.value)
    await _show_categories(callback.message, state, repo_factory, tx_type, page=0)
    await callback.answer()




@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню 👇", reply_markup=MAIN_MENU)


@router.callback_query(F.data == "cancel:menu")
async def cb_cancel_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Ок, отменил. Вы вернулись в главное меню 👇", reply_markup=MAIN_MENU)
    await callback.answer()

@router.message(Command("consult"))
async def cmd_consult(message: Message, consult_url: str) -> None:
    await message.answer(f"Записаться на консультацию: {consult_url}", parse_mode=ParseMode.HTML)
