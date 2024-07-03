from aiogram import Router,  F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.Class import Filters


from backend.vacancy import get_vacancy, get_links as get_vacancy_links, insert_vacancy

import sqlite3
import logging
router = Router()







async def perform_parsing_vacancies(message: Message, state: FSMContext, keyword: str, count: int, alt_keyword: str, salary_from: int, education_filters, schedule_filters, experience_filters):
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

    logging.info(f"Полученные фильтры: keyword={keyword}, education_filters={schedule_filters}, schedule_filters={education_filters}, experience_filters={experience_filters}, salary_from={salary_from}, count={count}")

    results_count = 0
    for link in get_vacancy_links(alt_keyword, education_filters, salary_from, schedule_filters, experience_filters):
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
            [InlineKeyboardButton(text="Далее", callback_data="next_page")],
            [InlineKeyboardButton(text="Назад", callback_data="restart")]
        ])
        await message.reply("Хотите продолжить просмотр?", reply_markup=keyboard)
    else:
        await message.reply("Больше вакансий не найдено.")

# хэндлер для обработки выбора "Вакансии"
@router.callback_query(F.data == "choose_vacancies")
async def choose_vacancies(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer('')
    await callback_query.message.answer("Введите запрос для поиска в базе данных:")
    await state.set_state(Filters.keyword)
    await state.update_data(context="vacancies")