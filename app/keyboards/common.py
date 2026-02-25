from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def tx_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Это доход", callback_data="confirm:income"),
                InlineKeyboardButton(text="Это расход", callback_data="confirm:expense"),
            ]
        ]
    )


def quick_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить ещё", callback_data="quick:add")],
            [InlineKeyboardButton(text="📊 Баланс", callback_data="quick:balance")],
            [InlineKeyboardButton(text="📤 Экспорт", callback_data="quick:export")],
            [InlineKeyboardButton(text="🤖 Анализ", callback_data="quick:analyze")],
        ]
    )


def period_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сегодня", callback_data=f"period:{prefix}:today"),
                InlineKeyboardButton(text="Неделя", callback_data=f"period:{prefix}:week"),
                InlineKeyboardButton(text="Месяц", callback_data=f"period:{prefix}:month"),
            ],
            [InlineKeyboardButton(text="Выбрать даты", callback_data=f"period:{prefix}:custom")],
        ]
    )


def premium_buy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Купить Premium ⭐️", callback_data="premium:buy")]]
    )


def category_create_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Создать категорию", callback_data="category:create")]]
    )
