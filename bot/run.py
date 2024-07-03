#docker-compose up --build
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.handlers_vacancy import router as vacancy_router
from app.handlers_resume import router as resume_router
import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from app.handlers import router

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    dp.include_router(vacancy_router)
    dp.include_router(resume_router)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
