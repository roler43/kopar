import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

from config import BOT_TOKEN
from database import db

# Импортируем хендлеры
from handlers import start, subscription, profile, flood, support, promo  # Добавлен promo
from admin_panel import router as admin_router
from payment import crypto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("data", exist_ok=True)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрируем роутеры
dp.include_router(start.router)
dp.include_router(subscription.router)
dp.include_router(profile.router)
dp.include_router(flood.router)
dp.include_router(support.router)
dp.include_router(promo.router)  # Добавлен роутер промокодов
dp.include_router(admin_router)

async def shutdown():
    """Закрытие соединений при остановке"""
    await crypto.close()

async def main():
    logger.info("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен!")
