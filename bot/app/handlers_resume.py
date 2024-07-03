
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import app.keyboard as kb
from app.Class import Filters

from backend.resume import get_resume, get_links as get_resume_links, insert_resume

import sqlite3
import logging


router = Router()


async def perform_parsing_resumes(message: Message, state: FSMContext, keyword: str, count: int, alt_keyword: str, salary_from: int, salary_to:int, education_filters, schedule_filters, experience_filters):
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

    logging.info(f"Filters: keyword={keyword}, education_filters={education_filters}, schedule_filters={schedule_filters}, experience_filters={experience_filters}, salary_from={salary_from}, salary_to={salary_to}, count={count}")

    results_count = 0

    for link in get_resume_links(alt_keyword, experience_filters, schedule_filters, education_filters, salary_from, salary_to):
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
            [InlineKeyboardButton(text="Далее", callback_data="next_page")],
            [InlineKeyboardButton(text="Назад", callback_data="restart")]
        ])
        await message.reply("Хотите продолжить просмотр?", reply_markup=keyboard)
    else:
        await message.reply("Больше резюме не найдено.")

# хэндлер для обработки выбора "Резюме"
@router.callback_query(F.data == "choose_resume")
async def choose_resume(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer('')
    await callback_query.message.answer("Введите запрос для поиска в базе данных:")
    await state.set_state(Filters.keyword)
    await state.update_data(context="resume")

# Верхний предел зарплаты
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