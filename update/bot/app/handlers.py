from aiogram import Router, F
from aiogram.filters.state import StateFilter
from aiogram.filters import CommandStart
import logging
import sys
import os
import random
import sqlite3

# Получаем абсолютный путь к родительской директории
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Добавляем этот путь в sys.path
sys.path.append(parent_dir)

# Теперь можно импортировать модули
from vacancy import get_vacancy, get_links, insert_vacancy
from salary_average import calculate_average_salary
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import app.keyboard as kb
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

router = Router()

class Filters(StatesGroup):
    keyword = State()
    education = State()
    salary = State()
    schedule = State()
    parse_count = State()

# Пустые списки фильтров
education_filters = []
schedule_filters = []

# Начало работы бота
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(Filters.keyword)
    await message.reply("Введите запрос для поиска в базе данных:")

# Обработка ввода запроса
@router.message(Filters.keyword)
async def process_keyword(message: Message, state: FSMContext):
    keyword = message.text
    await state.update_data(keyword=keyword)
    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()
    
    # Проверка наличия таблицы
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{keyword}';")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Получаем количество строк в таблице
        cursor.execute(f"SELECT COUNT(*) FROM {keyword}")
        total_rows = cursor.fetchone()[0]
        await state.update_data(keyword=keyword, total_rows=total_rows)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Выдать 10 случайных результатов", callback_data="random_10")],
            [InlineKeyboardButton(text="Посчитать среднюю зарплату", callback_data="average_salary")],
            [InlineKeyboardButton(text="Запарсить информацию в бд", callback_data="parse_info_db")]
        ])
        
        await message.reply(f"Таблица {keyword} найдена\nВсего {total_rows} вакансий\nВыберите действие:", reply_markup=keyboard)
    else:
        await message.reply(f"Таблица {keyword} не найдена, давайте запарсим информацию.")
        await state.set_state(Filters.education)
        await message.answer("Выберите образование:", reply_markup=kb.inline_education)
    
    conn.close()

# Обработка выбора образования через инлайн-клавиатуру
@router.callback_query(F.data.startswith("education_"))
async def process_inline_education(callback_query: CallbackQuery, state: FSMContext):
    education_map = {
        "education_higher": "Высшее",
        "education_special_secondary": "Среднее профессиональное",
        "education_not_required_or_not_specified": "Не указано или не нужно"
    }
    education_text = education_map[callback_query.data]
    education_filters.clear()
    education_filters.append(callback_query.data.split("_")[1])
    await state.update_data(education=education_text)
    await state.set_state(Filters.salary)
    await callback_query.message.edit_text(f"Выбрано образование: {education_text}")
    await callback_query.message.answer("Выберите ЗП или напишите число:", reply_markup=kb.inline_salary)
    await callback_query.answer('')

# Обработка выбора зарплаты через инлайн-клавиатуру
@router.callback_query(F.data.startswith("salary_"))
async def process_inline_salary(callback_query: CallbackQuery, state: FSMContext):
    salary_map = {
        "salary_50000": 50000,
        "salary_100000": 100000,
        "salary_150000": 150000,
        "salary_any": "Неважно"
    }
    salary_value = salary_map[callback_query.data]
    data = await state.get_data()
    if salary_value == "Неважно":
        data['salary'] = None
    else:
        data['salary'] = salary_value
    await state.update_data(salary=str(salary_value))
    await state.set_state(Filters.schedule)
    await callback_query.message.edit_text(f"Выбрана ЗП: {salary_value}")
    await callback_query.message.answer("Выберите тип занятости:", reply_markup=kb.inline_schedule)
    await callback_query.answer('')

# Обработка выбора типа занятости через инлайн-клавиатуру
@router.callback_query(F.data.startswith("schedule_"))
async def process_inline_schedule(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "schedule_next":
        await state.set_state(Filters.parse_count)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="10", callback_data="parse_10")],
            [InlineKeyboardButton(text="25", callback_data="parse_25")],
            [InlineKeyboardButton(text="50", callback_data="parse_50")]
        ])
        await callback_query.message.edit_text("Выберите сколько запарсить:", reply_markup=keyboard)
    else:
        schedule_map = {
            "schedule_fullDay": "Полный день",
            "schedule_remote": "Удаленная работа",
            "schedule_flexible": "Гибкий график",
            "schedule_shift": "Сменный график",
            "schedule_flyInFlyOut": "Вахтовая работа"
        }
        schedule_text = schedule_map[callback_query.data]
        filter_value = callback_query.data.split("_")[1]
        if filter_value in schedule_filters:
            schedule_filters.remove(filter_value)
        else:
            schedule_filters.append(filter_value)
        await callback_query.message.reply(f"Текущие фильтры занятости: {', '.join(schedule_filters)}")
    await callback_query.answer('')

# Выдать 10 случайных результатов
@router.callback_query(F.data == "random_10")
async def random_10(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keyword = data.get('keyword')
    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {keyword}")
    rows = cursor.fetchall()
    conn.close()

    random_rows = random.sample(rows, min(10, len(rows)))

    for row in random_rows:
        formatted_vacancy = (
            f"Профессия: {row[1]}\n"
            f"Название компании: {row[2]}\n"
            f"Зарплата: {row[3]}\n"
            f"Опыт работы: {row[4]}\n"
            f"Занятость: {row[5]}\n"
            f"Образование: {row[6]}\n"
            f"Ссылка: {row[7]}"
        )
        await callback_query.message.reply(formatted_vacancy)

    await callback_query.answer('')

# Посчитать среднюю зарплату
@router.callback_query(F.data == "average_salary")
async def average_salary(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keyword = data.get('keyword')
    average_salary = calculate_average_salary(keyword)
    await callback_query.message.reply(f"Средняя зарплата по запросу {keyword}: {average_salary:.2f} рублей")
    await callback_query.answer('')

# Обработка нажатия кнопки "Запарсить информацию в бд"
@router.callback_query(F.data == "parse_info_db")
async def parse_info_db(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(Filters.education)
    await callback_query.message.edit_text("Выберите образование:", reply_markup=kb.inline_education)
    await callback_query.answer('')

# Обработка ввода количества вакансий для парсинга через инлайн-клавиатуру
@router.callback_query(F.data.startswith("parse_"))
async def parse_vacancies(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Это нужно сделать сразу
    count = int(callback_query.data.split('_')[1])
    data = await state.get_data()
    keyword = data.get('keyword')
    await state.update_data(parse_count=count)

    await callback_query.message.reply("Начинаем парсить информацию...")
    await perform_parsing(callback_query.message, state, keyword, count)
    await callback_query.message.reply("Парсинг завершен. Хотите вернуться к началу?")

async def perform_parsing(message: Message, state: FSMContext, keyword: str, count: int):
    data = await state.get_data()
    offset = data.get('offset', 0)
    shown_links = data.get('shown_links', set())

    logging.info(f"Полученные фильтры: keyword={keyword}, education_filters={education_filters}, schedule_filters={schedule_filters}, offset={offset}")

    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {keyword}
               (id INTEGER PRIMARY KEY, title TEXT, company TEXT, salary TEXT, experience TEXT, busyness TEXT, education TEXT, link TEXT)''')

    results_count = 0

    for link in get_links(keyword, education_filters, data.get('salary'), schedule_filters, offset):
        if results_count >= count:
            break

        if link in shown_links:
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

            shown_links.add(link)  # Добавить ссылку в список показанных
            results_count += 1

    conn.close()

    new_offset = offset + 1  # Увеличиваем смещение на 1, чтобы перейти на следующую страницу
    await state.update_data(offset=new_offset, shown_links=shown_links)  # Обновить данные состояния

    if results_count > 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее", callback_data="next_page")],
            [InlineKeyboardButton(text="Назад", callback_data="restart")]
        ])
        await message.reply("Хотите продолжить просмотр?", reply_markup=keyboard)
    else:
        await message.reply("Больше вакансий не найдено.")
        await state.clear()

@router.callback_query(F.data == "next_page")
async def handle_next_page(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Это нужно сделать сразу
    data = await state.get_data()
    keyword = data.get('keyword')
    salary = data.get('salary')
    
    await display_vacancies(callback_query.message, state, keyword, salary)

async def display_vacancies(message: Message, state: FSMContext, keyword: str, salary: int):
    data = await state.get_data()
    offset = data.get('offset', 0)
    shown_links = data.get('shown_links', set())

    logging.info(f"Полученные фильтры: keyword={keyword}, education_filters={education_filters}, schedule_filters={schedule_filters}, offset={offset}")

    conn = sqlite3.connect('bd_vacancy/vacancy.db')
    cursor = conn.cursor()

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {keyword}
               (id INTEGER PRIMARY KEY, title TEXT, company TEXT, salary TEXT, experience TEXT, busyness TEXT, education TEXT, link TEXT)''')

    results_count = 0

    for link in get_links(keyword, education_filters, salary, schedule_filters, offset):
        if results_count >= 10:
            break

        if link in shown_links:
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

            shown_links.add(link)  # Добавить ссылку в список показанных
            results_count += 1

    conn.close()

    new_offset = offset + 1  # Увеличиваем смещение на 1, чтобы перейти на следующую страницу
    await state.update_data(offset=new_offset, shown_links=shown_links)  # Обновить данные состояния

    if results_count > 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Далее", callback_data="next_page")],
            [InlineKeyboardButton(text="Назад", callback_data="restart")]
        ])
        await message.reply("Хотите продолжить просмотр?", reply_markup=keyboard)
    else:
        await message.reply("Больше вакансий не найдено.")
        await state.clear()

@router.callback_query(F.data == "restart")
async def handle_restart(callback_query: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer('')
    await callback_query.message.answer("Начнем заново. Введите /start чтобы начать.")
