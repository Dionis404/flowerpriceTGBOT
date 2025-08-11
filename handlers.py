# handlers.py
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def private_message_handler(message: types.Message):
    """
    Обработчик личных сообщений.
    Отвечает только в приватному чату и предлагает ссылку на групповой чат.
    """
    if message.chat.type != "private":
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="Перейти в чат", url="https://t.me/+fhJvtNvdAttkNTky")

    await message.answer(
        "🚫 У меня нет желания общаться с фермерами!\n\n"
        "👉 Пиши в чат:",
        reply_markup=kb.as_markup()
    )
