# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, CHECK_INTERVAL
from handlers import private_message_handler
from price_checker import price_monitor_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем обработчик ЛС
dp.message.register(private_message_handler)  # aiogram 3.x стиль


async def main():
    # Запускаем фоновую задачу мониторинга цен
    asyncio.create_task(price_monitor_loop(bot))

    # Запускаем polling (при необходимости можно использовать webhook)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
