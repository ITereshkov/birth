from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➖ Расход"), KeyboardButton(text="➕ Доход")],
        [KeyboardButton(text="📊 Итоги"), KeyboardButton(text="📋 Операции")],
        [KeyboardButton(text="📂 Экспорт"), KeyboardButton(text="🤖 Анализ")],
        [KeyboardButton(text="⭐ Premium"), KeyboardButton(text="⚙️ Настройки")],
    ],
    resize_keyboard=True,
)

HIDE_MENU = ReplyKeyboardRemove()


def type_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Доход", callback_data="type:income"),
                InlineKeyboardButton(text="✅ Расход", callback_data="type:expense"),
            ],
            [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="cancel:menu")],
        ]
    )


def categories_keyboard(
    categories: list[str],
    tx_type: str,
    page: int,
    page_size: int = 6,
) -> InlineKeyboardMarkup:
    start = page * page_size
    chunk = categories[start : start + page_size]
    rows: list[list[InlineKeyboardButton]] = []
    for category in chunk:
        rows.append([InlineKeyboardButton(text=category.title(), callback_data=f"cat:{tx_type}:{page}:{category}")])

    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"catpage:{tx_type}:{page - 1}"))
    if start + page_size < len(categories):
        nav.append(InlineKeyboardButton(text="▶️ Ещё", callback_data=f"catpage:{tx_type}:{page + 1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="➕ Новая категория", callback_data=f"catnew:{tx_type}")])
    rows.append([InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="cancel:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сегодня", callback_data="period:today"),
                InlineKeyboardButton(text="Неделя", callback_data="period:week"),
                InlineKeyboardButton(text="Месяц", callback_data="period:month"),
            ],
            [InlineKeyboardButton(text="Выбрать даты", callback_data="period:custom")],
            [
                InlineKeyboardButton(text="📋 Список операций", callback_data="menu:ops"),
                InlineKeyboardButton(text="➕ Добавить", callback_data="menu:add"),
            ],
            [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="cancel:menu")],
        ]
    )


def after_save_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="↩️ Отменить", callback_data="tx:undo"),
                InlineKeyboardButton(text="✏️ Категория", callback_data="tx:recat"),
            ],
            [
                InlineKeyboardButton(text="➕ Ещё", callback_data="menu:add"),
                InlineKeyboardButton(text="📊 Итоги", callback_data="menu:summary"),
            ],
            [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="cancel:menu")],
        ]
    )


def settings_keyboard(notifications_enabled: bool) -> InlineKeyboardMarkup:
    state = "ВКЛ" if notifications_enabled else "ВЫКЛ"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔔 Уведомления: {state}", callback_data="settings:toggle_notify")],
            [InlineKeyboardButton(text="🏷 Категории", callback_data="settings:categories")],
            [InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="cancel:menu")],
        ]
    )


def cancel_only_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Вернуться в меню", callback_data="cancel:menu")]])
