from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Inline клавиатура для выбора образования
inline_education_resume = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Среднее", callback_data="education_secondary")],
    [InlineKeyboardButton(text="Среднее профессиональное", callback_data="education_special_secondary")],
    [InlineKeyboardButton(text="Незаконченное высшее", callback_data="education_unfinished_higher")],
    [InlineKeyboardButton(text="Кандидат наук", callback_data="education_candidate")],
    [InlineKeyboardButton(text="Бакалавр", callback_data="education_bachelor")],
    [InlineKeyboardButton(text="Магистр", callback_data="education_master")],
    [InlineKeyboardButton(text="Высшее", callback_data="education_higher")],
    [InlineKeyboardButton(text="Доктор наук", callback_data="education_doctor")],
    [InlineKeyboardButton(text="Не требуется или не указано", callback_data="education_not_required_or_not_specified")],
    [InlineKeyboardButton(text="Далее", callback_data="education_next")]
])
inline_education_vacancy = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Среднее профессиональное", callback_data="education_special_secondary")],
    [InlineKeyboardButton(text="Высшее", callback_data="education_higher")],
    [InlineKeyboardButton(text="Не требуется или не указано", callback_data="education_not_required_or_not_specified")],
    [InlineKeyboardButton(text="Далее", callback_data="education_next")]
])

# Inline клавиатура для выбора зарплаты (нижний предел)
inline_salary_from = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="25000", callback_data="salary_from_25000")],
    [InlineKeyboardButton(text="50000", callback_data="salary_from_50000")],
    [InlineKeyboardButton(text="100000", callback_data="salary_from_100000")],
    [InlineKeyboardButton(text="Не важно", callback_data="salary_from_any")]
])

# Inline клавиатура для выбора зарплаты (верхний предел)
inline_salary_to = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="50000", callback_data="salary_to_50000")],
    [InlineKeyboardButton(text="75000", callback_data="salary_to_75000")],
    [InlineKeyboardButton(text="125000", callback_data="salary_to_125000")],
    [InlineKeyboardButton(text="Не важно", callback_data="salary_to_any")]
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

# Inline клавиатура для выбора опыта работы
inline_experience = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Больше 6 лет", callback_data="experience_moreThan6")],
    [InlineKeyboardButton(text="Больше 3, но меньше 6 лет", callback_data="experience_between3And6")],
    [InlineKeyboardButton(text="Нет опыта", callback_data="experience_noExperience")],
    [InlineKeyboardButton(text="Больше года, меньше 3 лет", callback_data="experience_between1And3")],
    [InlineKeyboardButton(text="Далее", callback_data="experience_next")]
])

# Inline клавиатура для выбора количества записей для парсинга
inline_parse_count = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="10", callback_data="parse_10")],
    [InlineKeyboardButton(text="25", callback_data="parse_25")],
    [InlineKeyboardButton(text="50", callback_data="parse_50")]
])

# Inline клавиатура для выбора "Вакансии" или "Резюме"
start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Вакансии", callback_data="choose_vacancies")],
    [InlineKeyboardButton(text="Резюме", callback_data="choose_resume")]
])