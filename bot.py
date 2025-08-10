# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, CHAT_ID, PRICE_CHANGE_THRESHOLD, CHECK_INTERVAL
from price_checker import get_flower_price
from handlers import router

# Храним последнюю цену для отслеживания изменений
last_price = None

async def check_price(bot: Bot):
    global last_price
    while True:
        price_data = await get_flower_price()
        if price_data:
            usd = price_data.get("usd")
            rub = price_data.get("rub")
            uah = price_data.get("uah")

            if last_price is None:
                last_price = usd  # Первая установка
            else:
                change_percent = ((usd - last_price) / last_price) * 100

                # Проверяем изменение цены
                if abs(change_percent) >= PRICE_CHANGE_THRESHOLD:
                    sign = "📈" if change_percent > 0 else "📉"
                    msg = (
                        f"{sign} Цена Flower изменилась на {change_percent:.2f}%\n\n"
                        f"💵 USD: {usd:.4f}\n"
                        f"💴 RUB: {rub:.4f}\n"
                        f"💶 UAH: {uah:.4f}"
                    )
                    await bot.send_message(CHAT_ID, msg)
                    last_price = usd  # Обновляем цену

        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(router)

    # Запускаем проверку цены
    asyncio.create_task(check_price(bot))

    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
