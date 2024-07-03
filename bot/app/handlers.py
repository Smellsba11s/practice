#docker-compose up --build
from aiogram import Router, F
from aiogram.filters.state import StateFilter
from aiogram.filters import CommandStart
import logging
from aiogram import types
import random
import sqlite3


from backend.resume import get_resume, get_links as get_resume_links, insert_resume
from backend.vacancy import get_vacancy, get_links as get_vacancy_links, insert_vacancy
from backend import vacancy_average
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import app.keyboard as kb

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

router = Router()
#пустые списки фильтров
education_filters = []
schedule_filters = []
experience_filters = []

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

# хэндлер для обработки выбора "Вакансии"
@router.callback_query(F.data == "choose_vacancies")
async def choose_vacancies(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer('')
    await callback_query.message.answer("Введите запрос для поиска в базе данных:")
    await state.set_state(Filters.keyword)
    await state.update_data(context="vacancies")

# хэндлер для обработки выбора "Резюме"
@router.callback_query(F.data == "choose_resume")
async def choose_resume(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer('')
    await callback_query.message.answer("Введите запрос для поиска в базе данных:")
    await state.set_state(Filters.keyword)
    await state.update_data(context="resume")

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
            [InlineKeyboardButton(text="Запарсить информацию в бд", callback_data="parse_info_db")]
        ])

        await message.reply(f"Таблица {keyword} найдена\nВсего {total_rows} записей\nВыберите действие:", reply_markup=keyboard)
    else:
        await message.reply(f"Таблица {keyword} не найдена, давайте запарсим информацию.")
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

# Обработка выбора нижнего предела зарплаты через инлайн-клавиатуру
@router.callback_query(F.data.startswith("salary_from_"))
async def process_inline_salary_from(callback_query: CallbackQuery, state: FSMContext):
    salary_from_map = {
        "salary_from_25000": 25000,
        "salary_from_50000": 50000,
        "salary_from_100000": 100000,
        "salary_from_any": None
    }
    salary_from_value = salary_from_map[callback_query.data]
    await state.update_data(salary_from=salary_from_value)
    await state.set_state(Filters.salary_to)
    data = await state.get_data()
    context = data.get("context")
    if context == "vacancies":
        await state.set_state(Filters.parse_count)
        await callback_query.message.edit_text("Выберите количество записей для парсинга:", reply_markup=kb.inline_parse_count)
        await callback_query.answer('')
    elif context == "resume":
        await callback_query.message.answer("Выберите верхний предел зарплаты или напишите свой:", reply_markup=kb.inline_salary_to)
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

    try:
        count = int(callback_query.data.split('_')[1])
    except (IndexError, ValueError):
        await callback_query.message.reply("Ошибка: некорректное значение для количества записей.")
        return

    await state.update_data(parse_count=count)

    data = await state.get_data()
    keyword = data.get('keyword')
    context = data.get("context")
    alt_keyword = data.get('alt_keyword')

    await callback_query.message.reply("Начинаем парсить информацию...")

    if context == "vacancies":
        await perform_parsing_vacancies(callback_query.message, state, keyword, count, alt_keyword)
    elif context == "resume":
        await perform_parsing_resumes(callback_query.message, state, keyword, count, alt_keyword)

    await callback_query.message.reply("Парсинг завершен. Хотите вернуться к началу?")

async def perform_parsing_vacancies(message: Message, state: FSMContext, keyword: str, count: int, alt_keyword: str):
    data = await state.get_data()
    offset = data.get('offset', 0)
    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()   
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {keyword}
    (id INTEGER PRIMARY KEY, title TEXT, company TEXT, salary TEXT, experience TEXT, busyness TEXT, education TEXT, link TEXT)''')

    cursor.execute(f'SELECT link FROM {keyword}')
    # Получаем все строки результата
    rows = cursor.fetchall()
    # Преобразуем строки в список ссылок
    shown_links = [row[0] for row in rows]

    logging.info(f"Полученные фильтры: keyword={keyword}, education_filters={education_filters}, schedule_filters={schedule_filters}, offset={offset}")

    results_count = 0

    for link in get_vacancy_links(alt_keyword, education_filters, data.get('salary'), schedule_filters, offset):
        if results_count >= count:
            break

        if link in shown_links:
            logging.info(f"Пропуск существующей ссылки: {link}")
            continue  # Пропустить уже показанные ссылки

        logging.info(f"Парсим вакансию по ссылке: {link}")

        vacancy = get_vacancy(link, education_filters)
        if vacancy:
            formatted_vacancy = (
                f"Профессия: {vacancy['title']}\n"
                f"Название компании: {vacancy['name']}\n"
                f"Тэги: {', '.join(vacancy['tags'])}\n"
                f"Зарплата: {vacancy['salary']}\n"
                f"Опыт работы: {vacancy['experience']}\n"
                f"Занятость: {vacancy['busyness']}\n"
                f"Образование: {vacancy['education']}\n"
                f"Ссылка: {vacancy['link']}"
            )
            await message.reply(formatted_vacancy)

            insert_vacancy(cursor, keyword, vacancy)
            conn.commit()

            results_count += 1

    conn.close()


    if results_count > 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее", callback_data="next_page_vacancies")],
            [InlineKeyboardButton(text="Назад", callback_data="restart")]
        ])
        await message.reply("Хотите продолжить просмотр?", reply_markup=keyboard)
    else:
        await message.reply("Больше вакансий не найдено.")


async def perform_parsing_resumes(message: Message, state: FSMContext, keyword: str, count: int, alt_keyword: str):
    keyword = keyword.lower()
    print(alt_keyword)
    data = await state.get_data()
    offset = data.get('offset', 0)
    conn = sqlite3.connect('bd_resume/resume.db')
    cursor = conn.cursor()
    
    # Создание таблицы если она не существует
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {keyword} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        sex TEXT,
        age TEXT,
        salary TEXT,
        experience TEXT,
        tags TEXT,
        employment TEXT,
        schedule TEXT,
        link TEXT
    )''')
    logging.info(f"Table {keyword} is created or already exists.")
    
    cursor.execute(f'SELECT link FROM {keyword}')
    rows = cursor.fetchall()
    shown_links = [row[0] for row in rows]

    logging.info(f"Filters: keyword={keyword}, education_filters={education_filters}, schedule_filters={schedule_filters}, experience_filters={experience_filters}, salary_from={data.get('salary_from')}, salary_to={data.get('salary_to')}, offset={offset}")

    results_count = 0

    for link in get_resume_links(alt_keyword, experience_filters, schedule_filters, education_filters, data.get('salary_from'), data.get('salary_to')):
        if results_count >= count:
            break

        if link in shown_links:
            logging.info(f"Пропуск существующей ссылки: {link}")
            continue

        logging.info(f"Парсинг резюме: {link}")

        resume = get_resume(link)
        if resume:
            formatted_resume = (
                f"Имя: {resume['name']}\n"
                f"Пол: {resume['sex']}\n"
                f"Возраст: {resume['age']}\n"
                f"Зарплата: {resume['salary']}\n"
                f"Опыт работы: {resume['experience']}\n"
                f"Тэги: {', '.join(resume['tags'])}\n"
                f"Занятость: {', '.join(resume['employment_list'])}\n"
                f"График работы: {', '.join(resume['schedule_list'])}\n"
                f"Ссылка: {resume['link']}"
            )
            await message.reply(formatted_resume)

            if insert_resume(cursor, keyword, resume):
                conn.commit()
                results_count += 1
            else:
                logging.info(f"Не удалось вставить резюме: {resume['link']}")

    conn.close()

    if results_count > 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее", callback_data="next_page_resumes")],
            [InlineKeyboardButton(text="Назад", callback_data="restart")]
        ])
        await message.reply("Хотите продолжить просмотр?", reply_markup=keyboard)
    else:
        await message.reply("Больше резюме не найдено.")
  

@router.callback_query(F.data == "next_page_vacancies")
async def handle_next_page_vacancies(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  
    data = await state.get_data()
    keyword = data.get('keyword')
    count = data.get('parse_count')
    alt_keyword = keyword.replace('_',' ')
    await perform_parsing_vacancies(callback_query.message, state, keyword, count, alt_keyword)

@router.callback_query(F.data == "next_page_resumes")
async def handle_next_page_resumes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  
    data = await state.get_data()
    keyword = data.get('keyword')
    count = data.get('parse_count')
    alt_keyword = keyword.replace('_',' ')
    await perform_parsing_resumes(callback_query.message, state, keyword, count, alt_keyword)


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

    for result in results:
        formatted_result = f"Результат: {result}"
        await callback_query.message.reply(formatted_result)

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

