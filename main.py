import asyncio
# import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.handlers import routers
from app.database import Database
from aiogram.client.default import DefaultBotProperties

from loguru import logger
# Настраиваем логирование
logger.add("logs/app.log", rotation="100 MB", retention="10 days",
           format="{time}:{level}:{file}:{line}:{function}:{message}", level="INFO")

# Загружаем переменные окружения
load_dotenv()

async def main():
    # Инициализируем базу данных
    db = Database(os.getenv("DATABASE_NAME", "lunch_hunter.db"))
    await db.create_tables()
    
    # Инициализируем бота и диспетчер
    bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN,
        ),)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем все роутеры
    for router in routers:
        dp.include_router(router)
    
    # Пропускаем накопившиеся апдейты и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    bot_info=await bot.get_me()
    logger.info(f"Bot started {bot_info}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 