import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from database.session import engine, Base
from bot.handlers import admin, teacher, student, common, ai
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.i18n import I18nMiddleware
from utils.config import Config
from utils.logging import setup_logging

# Create tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Education Bot...")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register middlewares
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    
    # Register handlers
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(teacher.router)
    dp.include_router(student.router)
    dp.include_router(ai.router)
    
    # Create database tables
    await create_tables()
    
    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())