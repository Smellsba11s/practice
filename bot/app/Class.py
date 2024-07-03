from aiogram.fsm.state import StatesGroup, State
class Filters(StatesGroup):
    alt_keyword = State()
    keyword = State()
    context = State()
    experience = State()
    education = State()
    salary_from = State()
    salary_to = State()
    schedule = State()
    parse_count = State()