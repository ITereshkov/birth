from aiogram.fsm.state import State, StatesGroup


class OperationStates(StatesGroup):
    waiting_amount = State()
    waiting_type = State()
    waiting_category = State()
    waiting_new_category = State()


class PeriodStates(StatesGroup):
    waiting_start = State()
    waiting_end = State()
