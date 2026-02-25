from aiogram.fsm.state import State, StatesGroup


class SetupStates(StatesGroup):
    waiting_timezone = State()


class TransactionStates(StatesGroup):
    waiting_tx_type = State()
    waiting_category_confirm = State()


class CustomRangeStates(StatesGroup):
    waiting_start = State()
    waiting_end = State()
