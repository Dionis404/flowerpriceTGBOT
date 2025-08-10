# handlers.py
from aiogram import Router, types
from config import CHAT_LINK

router = Router()

@router.message(lambda msg: msg.chat.type == "private")
async def handle_private_message(message: types.Message):
    """
    Обработка ЛС — бот отвечает и отправляет в нужный чат.
    """
    text = (
        "🚫 У меня нет желания общаться с фермерами!\n"
        f"👉 Пиши в чат: {CHAT_LINK}"
    )
    await message.answer(text, parse_mode="HTML")
