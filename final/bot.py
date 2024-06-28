 # aiogram 2.13
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import sqlite3
from vacancy import get_links, get_vacancy, insert_vacancy

API_TOKEN = '7149953071:AAHKMeOAy9RSovs2RdXMJ3rIhDdGrnCa1oE'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Класс для состояний формы
class Form(StatesGroup):
    keyword = State()
    education = State()
    salary = State()
    schedule = State()

# Пустые списки фильтров
education_filters = []
schedule_filters = []

# Команда /start
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await Form.keyword.set()
    await message.reply("Введите запрос:")

# Обработка ввода запроса
@dp.message_handler(state=Form.keyword)
async def process_keyword(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['keyword'] = message.text
    
    # Переход к выбору образования
    await Form.next()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    buttons = [
        "Высшее", "Среднее профессиональное", "Не указано или не нужно"
    ]
    markup.add(*buttons)
    await message.reply("Выберите образование:", reply_markup=markup)

# Обработка выбора образования
@dp.message_handler(lambda message: message.text in ["Высшее", "Среднее профессиональное", "Не указано или не нужно"], state=Form.education)
async def process_education(message: types.Message, state: FSMContext):
    education_map = {
        "Высшее": "higher",
        "Среднее профессиональное": "special_secondary",
        "Не указано или не нужно": "not_required_or_not_specified"
    }

    # Проверяем, что выбранный текст присутствует в education_map
    if message.text in education_map:
        filter_value = education_map[message.text]
        education_filters.clear()  # Очищаем текущий список фильтров
        education_filters.append(filter_value)  # Добавляем выбранный фильтр

        await message.reply(f"Выбрано образование: {message.text}")

        # Продолжаем на следующий шаг (выбор ЗП)
        await Form.salary.set()
        markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        buttons = [
            "до 30 000", "30 000 - 60 000", "более 60 000", "неважно"
        ]
        markup.add(*buttons)
        await message.reply("Выберите ЗП или напишите число:", reply_markup=markup)
    else:
        await message.reply("Пожалуйста, используйте кнопки для выбора образования.")

# Обработка выбора ЗП
@dp.message_handler(state=Form.salary)
async def process_salary(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text.lower() == "неважно":
            data['salary'] = None
        else:
            try:
                data['salary'] = int(message.text)
            except ValueError:
                await message.reply("Пожалуйста, введите число или 'Неважно'.")
                return

    # Переход к выбору типа занятости
    await Form.next()
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    buttons = [
        "Полный день", "Удаленная работа", "Гибкий график", 
        "Сменный график", "Вахтовая работа", "далее"
    ]
    markup.add(*buttons)
    await message.reply("Выберите тип занятости:", reply_markup=markup)

# Обработка выбора типа занятости
@dp.message_handler(lambda message: message.text in ["Полный день", "Удаленная работа", "Гибкий график", "Сменный график", "Вахтовая работа", "далее"], state=Form.schedule)
async def process_schedule(message: types.Message, state: FSMContext):
    if message.text == "далее":
        async with state.proxy() as data:
            if 'keyword' not in data or 'salary' not in data:
                await message.reply("Произошла ошибка. Пожалуйста, начните заново, используя команду /start.")
                await state.finish()
                return

            keyword = data['keyword']
            salary = data['salary']

        await state.finish()

        # Добавим логирование для проверки ссылок
        logging.info(f"Полученные фильтры: keyword={keyword}, education_filters={education_filters}, schedule_filters={schedule_filters}")
        
        # Подключаемся к базе данных
        conn = sqlite3.connect('bd_vacancy/vacancy.db')
        cursor = conn.cursor()
        
        # Создаем таблицу, если она не существует
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {keyword}
                   (id INTEGER PRIMARY KEY, title TEXT, company TEXT, salary TEXT, experience TEXT, busyness TEXT, education TEXT, link TEXT)''')
        
        # Подготавливаем список для результатов
        results_count = 0
        
        # Итерируемся по ссылкам и собираем результаты
        for link in get_links(keyword, education_filters, salary, schedule_filters):
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

                # Добавляем вакансию в базу данных
                insert_vacancy(cursor, keyword, vacancy)
                conn.commit()
                
                results_count += 1
                if results_count >= 10:
                    break  # Выходим из цикла после получения 10 результатов

            else:
                logging.warning(f"Не удалось получить данные по ссылке: {link}")

        conn.close()
    else:
        schedule_map = {
            "Полный день": "fullDay",
            "Удаленная работа": "remote",
            "Гибкий график": "flexible",
            "Сменный график": "shift",
            "Вахтовая работа": "flyInFlyOut"
        }
        filter_value = schedule_map[message.text]
        if filter_value in schedule_filters:
            schedule_filters.remove(filter_value)
        else:
            schedule_filters.append(filter_value)
        await message.reply(f"Текущие фильтры занятости: {', '.join(schedule_filters)}")

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)