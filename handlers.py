# handlers.py
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from config import CHAT_LINK, PRIVATE_MESSAGE_TEXT, GROUP_CHAT_ID
from price_checker import fetch_current_prices, CURRENCIES
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def price_command_handler(message: types.Message):
    """
    Обработчик команды /price.
    Отправляет текущий курс монеты.
    """
    logger.info("Обработчик price_command_handler вызван")
    logger.info("Пользователь %s (%s) из чата %s (%s) запросил курс",
                 message.from_user.username, message.from_user.id,
                 message.chat.title, message.chat.id)
    
    # Получаем текущие цены
    current = await fetch_current_prices()
    
    if current is None:
        await message.answer("❌ Не удалось получить текущий курс. Попробуйте позже.")
        logger.warning("Не удалось получить текущий курс для пользователя %s (%s) из чата %s (%s)",
                         message.from_user.username, message.from_user.id,
                         message.chat.title, message.chat.id)
        return
    
    # Формируем сообщение с курсами
    lines = []
    emoji_map = {"usd": "🇺🇸", "rub": "🇷🇺", "uah": "🇺🇦"}
    for c in CURRENCIES:
        price = current.get(c)
        if price is not None:
            line = f"{emoji_map.get(c,'')} {c.upper()}: {price:.6f}"
        else:
            line = f"{emoji_map.get(c,'')} {c.upper()}: —"
        lines.append(line)
    
    caption = (
        "📈 Текущий курс\n\n"
        + "\n".join(lines)
        + f"\n\n📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    
    await message.answer(caption)
    logger.info("Отправлен курс пользователю %s (%s) из чата %s (%s)",
                 message.from_user.username, message.from_user.id,
                 message.chat.title, message.chat.id)



# Отладочные обработчики удалены
async def private_message_handler(message: types.Message):
    """
    Обработчик личных сообщений.
    Отвечает только в приватному чату и предлагает ссылку на групповой чат.
    """
    logger.info("Обработчик private_message_handler вызван")
    if message.chat.type != "private":
        logger.debug("Сообщение не из личного чата, игнорируем")
        return

    logger.info("Получено личное сообщение от пользователя %s (%s)",
                 message.from_user.username, message.from_user.id)

    kb = InlineKeyboardBuilder()
    kb.button(text="Перейти в чат", url=CHAT_LINK)

    await message.answer(
        PRIVATE_MESSAGE_TEXT,
        reply_markup=kb.as_markup()
    )
    logger.debug("Отправлен ответ на личное сообщение пользователю %s (%s)",
                 message.from_user.username, message.from_user.id)

