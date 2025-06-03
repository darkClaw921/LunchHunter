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
def debug_only(record):
    return record["level"].name == "DEBUG"
logger.add("logs/app.log", rotation="100 MB", retention="10 days",
           format="{time:YYYY-MM-DD HH:mm}:{level}:{file}:{line}:{function}:{message}", level="INFO", filter=debug_only)


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
    
    logger.info(f"""Bot started 
    username: {bot_info.username}
    id: {bot_info.id}
    first_name: {bot_info.first_name}
    last_name: {bot_info.last_name}
    is_bot: {bot_info.is_bot}
    is_premium: {bot_info.is_premium}
    language_code: {bot_info.language_code}""")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 