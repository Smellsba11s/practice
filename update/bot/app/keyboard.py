from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Клавиатура для выбора образования
education = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Высшее')], 
    [KeyboardButton(text='Среднее профессиональное')], 
    [KeyboardButton(text='Не указано или не нужно')]
],
                     resize_keyboard=True,
                     input_field_placeholder='Выберите образование.')

# Клавиатура для выбора зарплаты
salary = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='50000')], 
    [KeyboardButton(text='100000')], 
    [KeyboardButton(text='150000')],
    [KeyboardButton(text='Не важно')]
],
                     resize_keyboard=True,
                     input_field_placeholder='Выберите минимальную зарплату.')

# Клавиатура для выбора типа занятости
schedule = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Полный день')], 
    [KeyboardButton(text='Удаленная работа')], 
    [KeyboardButton(text='Гибкий график')],
    [KeyboardButton(text='Сменный график')], 
    [KeyboardButton(text='Вахтовая работа')], 
    [KeyboardButton(text='далее')]
],
                     resize_keyboard=True,
                     input_field_placeholder='Выберите тип занятости.')

# Inline клавиатура для выбора образования
inline_education = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Высшее", callback_data="education_higher")],
    [InlineKeyboardButton(text="Среднее профессиональное", callback_data="education_special_secondary")],
    [InlineKeyboardButton(text="Не указано или не нужно", callback_data="education_not_required_or_not_specified")]
])

# Inline клавиатура для выбора зарплаты
inline_salary = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="50000", callback_data="salary_50000")],
    [InlineKeyboardButton(text="100000", callback_data="salary_100000")],
    [InlineKeyboardButton(text="150000", callback_data="salary_150000")],
    [InlineKeyboardButton(text="Не важно", callback_data="salary_any")]
])

# Inline клавиатура для выбора типа занятости
inline_schedule = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Полный день", callback_data="schedule_fullDay")],
    [InlineKeyboardButton(text="Удаленная работа", callback_data="schedule_remote")],
    [InlineKeyboardButton(text="Гибкий график", callback_data="schedule_flexible")],
    [InlineKeyboardButton(text="Сменный график", callback_data="schedule_shift")],
    [InlineKeyboardButton(text="Вахтовая работа", callback_data="schedule_flyInFlyOut")],
    [InlineKeyboardButton(text="Далее", callback_data="schedule_next")]
])

# Inline клавиатура для списка автомобилей (пример)
cars = ['Tesla', 'Mercedes', 'BMW']

async def inline_cars():
    keyboard = InlineKeyboardBuilder()
    for car in cars:
        keyboard.add(InlineKeyboardButton(text=car, callback_data=f"car_{car.lower()}"))
    return keyboard.adjust(2).as_markup()
