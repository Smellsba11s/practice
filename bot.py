import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from vacancy import get_links, get_vacancy

API_TOKEN = '7149953071:AAHKMeOAy9RSovs2RdXMJ3rIhDdGrnCa1oE'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

class Form(StatesGroup):
    keyword = State()
    education = State()
    salary = State()
    schedule = State()

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
        "Высшее", "Среднее профессиональное", "Не указано или не нужно", "далее"
    ]
    markup.add(*buttons)
    await message.reply("Выберите образование:", reply_markup=markup)

# Обработка выбора образования
@dp.message_handler(lambda message: message.text in ["Высшее", "Среднее профессиональное", "Не указано или не нужно", "далее"], state=Form.education)
async def process_education(message: types.Message, state: FSMContext):
    if message.text == "далее":
        await Form.next()
        markup = types.ReplyKeyboardRemove()
        await message.reply("Выберите ЗП или напишите число:", reply_markup=markup)
    else:
        education_map = {
            "Высшее": "higher",
            "Среднее профессиональное": "special_secondary",
            "Не указано или не нужно": "not_required_or_not_specified"
        }
        filter_value = education_map[message.text]
        if filter_value in education_filters:
            education_filters.remove(filter_value)
        else:
            education_filters.append(filter_value)
        await message.reply(f"Текущие фильтры образования: {', '.join(education_filters)}")

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

        links = list(get_links(keyword, education_filters, salary, schedule_filters))[:10]
        if not links:
            await message.reply("Не найдено вакансий по вашему запросу.")
            return

        for link in links:
            logging.info(f"Проверка ссылки: {link}")
            vacancy = get_vacancy(link)
            if vacancy:
                formatted_vacancy = (
                    f"Профессия: {vacancy['title']}\n"
                    f"Название компании: {vacancy['name']}\n"
                    f"Тэги: {', '.join(vacancy['tags'])}\n"
                    f"Зарплата: {vacancy['salary']}\n"
                    f"Опыт работы: {vacancy['experience']}\n"
                    f"Занятость: {vacancy['busyness']}\n"
                    f"Ссылка: {vacancy['link']}"
                )
                await message.reply(formatted_vacancy)
            else:
                logging.warning(f"Не удалось получить данные по ссылке: {link}")
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
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)