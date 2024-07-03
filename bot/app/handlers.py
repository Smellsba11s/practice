#docker-compose up --build
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram import types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


import app.handlers_vacancy as vac
import app.handlers_resume as res
from app.Class import Filters
import app.keyboard as kb


from backend import vacancy_average
import sqlite3


router = Router()
#пустые списки фильтров

education_filters = []
schedule_filters = []
experience_filters = []



@router.message(lambda message: message.sticker is not None)
async def send_same_sticker(message: Message):
    sticker = message.sticker
    await message.answer_sticker(sticker.file_id)

# хэндлер для команды /start
@router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    education_filters.clear()
    schedule_filters.clear()
    experience_filters.clear()
    await message.answer("Выберите опцию:", reply_markup= kb.start_keyboard)



# Обработка ввода запроса
@router.message(Filters.keyword)
async def process_keyword(message: Message, state: FSMContext):
    keyword = message.text.lower().replace(" ", "_")  # Заменяем пробелы на подчеркивания
    alt_keyword = keyword.replace('_',' ')
    await state.update_data(alt_keyword=alt_keyword)
    await state.update_data(keyword=keyword)
    data = await state.get_data()
    context = data.get("context")
    conn = sqlite3.connect('bd_vacancy/vacancy.db' if context == "vacancies" else 'bd_resume/resume.db')
    cursor = conn.cursor()

    # Проверка наличия таблицы
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{keyword}';")
    table_exists = cursor.fetchone()

    if table_exists:
        cursor.execute(f"SELECT COUNT(*) FROM {keyword}")
        total_rows = cursor.fetchone()[0]
        await state.update_data(keyword=keyword, total_rows=total_rows)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Выдать 10 случайных результатов", callback_data="random_10")],
            [InlineKeyboardButton(text="Посчитать среднюю зарплату", callback_data="average_salary")],
            [InlineKeyboardButton(text="Добавить новую информацию", callback_data="parse_info_db")]
        ])

        await message.reply(f"{keyword} найдена в базе данных\nВсего {total_rows} записей\nВыберите действие:", reply_markup=keyboard)
    else:
        await message.reply(f"{keyword} не найдена в базе данных, давайте добавим информацию")
        await state.set_state(Filters.experience)
        await message.answer("Выберите опыт работы:", reply_markup=kb.inline_experience)

    conn.close()


@router.callback_query(F.data == "parse_info_db")
async def parse_info_db(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer() 
    await state.set_state(Filters.experience)
    await callback_query.message.answer("Выберите опыт работы:", reply_markup=kb.inline_experience)
    await callback_query.answer('')

@router.callback_query(F.data.startswith("experience_"))
async def process_inline_experience(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "experience_next":
        await state.update_data(experience=experience_filters)
        await state.set_state(Filters.education)
        data = await state.get_data()
        context = data.get("context")
        if context == "vacancies":
            await callback_query.message.answer("Выберите образование:", reply_markup=kb.inline_education_vacancy)
            await callback_query.answer('')
        elif context == 'resume':
            await callback_query.message.answer("Выберите образование:", reply_markup=kb.inline_education_resume)
            await callback_query.answer('')     
    else:
        experience_map = {
            "experience_moreThan6": "Больше 6 лет",
            "experience_between3And6": "Больше 3, но меньше 6 лет",
            "experience_noExperience": "Нет опыта",
            "experience_between1And3": "Больше года, меньше 3 лет"
        }
        exp_code = callback_query.data.split("_")[1]
        if exp_code in experience_filters:
            experience_filters.remove(exp_code)
        else:
            experience_filters.append(exp_code)

        selected_experience_text = f"Выбранный опыт работы: {', '.join([experience_map[f'experience_{e}'] for e in experience_filters])}"

        await callback_query.message.edit_text(selected_experience_text, reply_markup=kb.inline_experience)
        await callback_query.answer('')

@router.callback_query(F.data == "experience_next")
async def experience_next(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(experience=experience_filters)
    await state.set_state(Filters.education)
    data = await state.get_data()
    context = data.get("context")
    if context == "vacancies":
        await callback_query.message.answer("Выберите образование:", reply_markup=kb.inline_education_vacancy)
        await callback_query.answer('')
    elif context == 'resume':
        await callback_query.message.answer("Выберите образование:", reply_markup=kb.inline_education_resume)
        await callback_query.answer('')     

@router.callback_query(F.data.startswith("education_"))
async def process_inline_education(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    context = data.get("context")
    if callback_query.data == "education_next":
        await state.update_data(education=education_filters)
        await state.set_state(Filters.schedule)
        await callback_query.message.answer("Выберите тип занятости:", reply_markup=kb.inline_schedule)
        await callback_query.answer('')
    else:
        if context == "vacancies":
            education_map = {
                "special_secondary": "Среднее профессиональное",
                "higher": "Высшее",
                "not_required_or_not_specified": "Не требуется или не указано"
            }
        elif context == "resume":
            education_map = {
                "secondary": "Среднее",
                "special_secondary": "Среднее профессиональное",
                "unfinished_higher": "Незаконченное высшее",
                "candidate": "Кандидат наук",
                "bachelor": "Бакалавр",
                "master": "Магистр",
                "higher": "Высшее",
                "doctor": "Доктор наук",
                "not_required_or_not_specified": "Не требуется или не указано"
            }

        education_code = callback_query.data.split("_", 1)[1]
        if education_code in education_filters:
            education_filters.remove(education_code)
        else:
            education_filters.append(education_code)

        selected_education_text = f"Выбранное образование: {', '.join([education_map.get(e, e) for e in education_filters])}"
        if context == 'vacancies': markup = kb.inline_education_vacancy 
        else: markup = kb.inline_education_resume
        await callback_query.message.edit_text(selected_education_text, reply_markup=markup)
        await callback_query.answer('')


@router.callback_query(F.data == "education_next")
async def education_next(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(education=education_filters)
    await state.set_state(Filters.schedule)
    await callback_query.answer('')
    await callback_query.message.answer("Выберите тип занятости:", reply_markup=kb.inline_schedule)
    await callback_query.answer('')

@router.callback_query(F.data.startswith("schedule_"))
async def process_inline_schedule(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "schedule_next":
        await state.update_data(schedule=schedule_filters)
        await state.set_state(Filters.salary_from)
        await callback_query.answer('')
        await callback_query.message.answer("Выберите нижний предел зарплаты или напишите свой:", reply_markup=kb.inline_salary_from)
    else:
        schedule_map = {
            "schedule_fullDay": "Полный день",
            "schedule_remote": "Удаленная работа",
            "schedule_flexible": "Гибкий график",
            "schedule_shift": "Сменный график",
            "schedule_flyInFlyOut": "Вахтовая работа"
        }
        schedule_code = callback_query.data.split("_")[1]
        if schedule_code in schedule_filters:
            schedule_filters.remove(schedule_code)
        else:
            schedule_filters.append(schedule_code)

        selected_schedule_text = f"Текущие фильтры занятости: {', '.join([schedule_map[f'schedule_{s}'] for s in schedule_filters])}"

        await callback_query.message.edit_text(selected_schedule_text, reply_markup=kb.inline_schedule)
        await callback_query.answer('')


@router.callback_query(F.data.startswith("salary_to_"))
async def process_inline_salary_to(callback_query: CallbackQuery, state: FSMContext):
    salary_to_map = {
        "salary_to_50000": 50000,
        "salary_to_75000": 75000,
        "salary_to_125000": 125000,
        "salary_to_any": None
    }
    salary_to_value = salary_to_map[callback_query.data]
    await state.update_data(salary_to=salary_to_value)
    await state.set_state(Filters.parse_count)
    await callback_query.message.edit_text("Выберите количество записей для парсинга:", reply_markup=kb.inline_parse_count)
    await callback_query.answer('')


# Обработка выбора количества записей для парсинга через инлайн-клавиатуру
@router.callback_query(F.data.startswith("parse_"))
async def parse_vacancies_or_resumes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer() 
    count = int(callback_query.data.split('_')[1])
    await state.update_data(parse_count=count)

    data = await state.get_data()
    keyword = data.get('keyword')
    context = data.get("context")
    alt_keyword = data.get('alt_keyword')
    salary_from = data.get('salary_from')
    salary_to = data.get('salary_to')
    await callback_query.message.reply("Начинаем парсить информацию...")

    if context == "vacancies":
        await vac.perform_parsing_vacancies(callback_query.message, state, keyword, count, alt_keyword, salary_from, education_filters, schedule_filters, experience_filters)
    elif context == "resume":
        await res.perform_parsing_resumes(callback_query.message, state, keyword, count, alt_keyword, salary_from, salary_to, education_filters,schedule_filters,experience_filters)


@router.callback_query(F.data == "next_page")
async def handle_next_page_resumes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  
    data = await state.get_data()
    keyword = data.get('keyword')
    context = data.get('context')
    salary_from = data.get('salary_from')
    salary_to = data.get('salary_to')
    count = data.get('parse_count')
    alt_keyword = keyword.replace('_',' ')
    if context == 'resume': await res.perform_parsing_resumes(callback_query.message, state, keyword, count, alt_keyword, salary_from, salary_to, education_filters,schedule_filters,experience_filters)
    else: await vac.perform_parsing_vacancies(callback_query.message, state, keyword, count, alt_keyword, salary_from, education_filters, schedule_filters, experience_filters)

@router.callback_query(F.data == "restart")
async def handle_restart(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer('')
    await callback_query.message.answer("Начнем заново. Введите /start чтобы начать.")

@router.callback_query(F.data == "random_10")
async def handle_random_10(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keyword = data.get('keyword').lower()
    context = data.get("context")
    conn = sqlite3.connect('bd_vacancy/vacancy.db' if context == "vacancies" else 'bd_resume/resume.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {keyword} ORDER BY RANDOM() LIMIT 10;")
    results = cursor.fetchall()

    if context == "vacancies":
        for result in results:
            formatted_vacancy = (
                f"Профессия: {result[1]}\n" 
                f"Название компании: {result[2]}\n"  
                f"Зарплата: {result[3]}\n"
                f"Опыт работы: {result[4]}\n"
                f"Занятость: {result[5]}\n"
                f"Образование: {result[6]}\n"
                f"Ссылка: {result[7]}"
            )
            await callback_query.message.reply(formatted_vacancy)
    else:
        for result in results:
            formatted_resume = (
                f"Имя: {result[1]}\n"  
                f"Пол: {result[2]}\n"  
                f"Возраст: {result[3]}\n" 
                f"Зарплата: {result[4]}\n"
                f"Опыт работы: {result[5]}\n"
                f"Тэги: {result[6]}\n"
                f"Занятость: {result[7]}\n"
                f"График работы: {result[8]}\n"
                f"Ссылка: {result[9]}"
            )
            await callback_query.message.reply(formatted_resume)
    conn.close()
    await callback_query.answer('')

@router.callback_query(F.data == "average_salary")
async def handle_average_salary(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keyword = data.get('keyword').lower()
    context = data.get("context")
    
    if context == "vacancies":
        # Используем функцию из vacancy_average для подсчета средней зарплаты
        average_salary = vacancy_average.calculate_average_salary_vacancy(keyword)
        if average_salary is not None:
            await callback_query.message.reply(f"Средняя зарплата: {average_salary:.2f} рублей")
        else:
            await callback_query.message.reply("Нет данных о зарплатах для расчета.")
    elif context == "resume":
        # Используем функцию из vacancy_average для подсчета средней зарплаты
        average_salary = vacancy_average.calculate_average_salary_resume(keyword)
        if average_salary is not None:
            await callback_query.message.reply(f"Средняя зарплата: {average_salary:.2f} рублей")
        else:
            await callback_query.message.reply("Нет данных о зарплатах для расчета.")

    await callback_query.answer('')

