# bot.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from config import BOT_TOKEN, CHECK_INTERVAL
from handlers import private_message_handler, price_command_handler, set_threshold_handler, add_group_handler, remove_group_handler, list_groups_handler, add_admin_handler, remove_admin_handler
from price_checker import price_monitor_loop

# Настройка логирования с более подробным форматом
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем обработчик команды /price
logger.info("Регистрация обработчика команды /price")
dp.message.register(price_command_handler, Command("price"))

# Регистрируем обработчик ЛС
logger.info("Регистрация обработчика личных сообщений")
dp.message.register(private_message_handler, lambda message: message.chat.type == "private" and (not message.text or not message.text.startswith('/')))

# Регистрируем обработчики новых команд
logger.info("Регистрация обработчиков новых команд")
dp.message.register(set_threshold_handler, Command("set_threshold"))
dp.message.register(add_group_handler, Command("add_group"))
dp.message.register(remove_group_handler, Command("remove_group"))
dp.message.register(list_groups_handler, Command("list_groups"))
dp.message.register(add_admin_handler, Command("add_admin"))
dp.message.register(remove_admin_handler, Command("remove_admin"))


@dp.shutdown()
async def on_shutdown():
    logger.info("Бот останавливается...")


async def main():
    logger.info("Инициализация бота...")
    
    # Запускаем фоновую задачу мониторинга цен
    price_monitor_task = asyncio.create_task(price_monitor_loop(bot))
    logger.info("Фоновая задача мониторинга цен запущена")

    # Запускаем polling (при необходимости можно использовать webhook)
    try:
        logger.info("Бот запускается...")
        logger.info("Зарегистрированные обработчики: %s", dp.message.handlers)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Ошибка при запуске бота: %s", e, exc_info=True)
        raise
    finally:
        logger.info("Бот останавливается...")
        # Отменяем фоновую задачу при завершении работы бота
        price_monitor_task.cancel()
        try:
            await price_monitor_task
        except asyncio.CancelledError:
            pass  # Это ожидаемо при отмене задачи
        await bot.session.close()
        logger.info("Бот успешно остановлен")


if __name__ == "__main__":
    asyncio.run(main())
