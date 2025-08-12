# handlers.py
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from config import CHAT_LINK, PRIVATE_MESSAGE_TEXT, GROUP_CHAT_ID
from price_checker import fetch_current_prices, CURRENCIES
from datetime import datetime
import logging
import random

# Список вариантов ответов для команды /price
PRICE_RESPONSE_TEMPLATES = [
    """Ах, курс валют. Золото меркнет перед точными цифрами. Запомните:  
{currency_lines}
Теперь идите и используйте их с умом… во благо моей казны.""",

    """Простолюдины, внимайте! Сегодня мои казначеи установили следующие курсы:  
{currency_lines}
Любая прибыль с обмена — в королевскую казну, разумеется.""",

    """Запишите, крестьяне, дабы не тратить моё время на расспросы:  
{currency_lines}
И помните — ваши монеты уже мысленно принадлежат мне.""",

    """Казна требует точности! Сегодняшние курсы:  
{currency_lines}
Любая выгода с обмена — моя. Даже не думайте иначе."""
]
# Список вариантов ответов для личных сообщений
PRIVATE_MESSAGE_RESPONSE_TEMPLATES = [
    """🚫 Сегодня я не намерен тратить время на простолюдинов!  
👉 Хочешь что-то сказать — пиши в чат: _Перейти в чат_""",

    """🚫 Моё время слишком ценно для бесед с фермерами!  
👉 Если уж настаиваешь — пиши в чат: _Перейти в чат_""",

    """🚫 Я не вижу причин тратить своё драгоценное время на вас.  
👉 Оставь своё послание здесь: _Перейти в чат_""",

    """🚫 У меня нет ни желания, ни терпения общаться с крестьянами.  
👉 Если это важно, изложи в чате: _Перейти в чат_"""
]

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
    
    # Формируем строки с курсами для подстановки в шаблон
    lines = []
    emoji_map = {"usd": "🇺🇸", "rub": "🇷🇺", "uah": "🇺🇦"}
    for c in CURRENCIES:
        price = current.get(c)
        if price is not None:
            line = f"{emoji_map.get(c,'')} {c.upper()}: {price:.6f}"
        else:
            line = f"{emoji_map.get(c,'')} {c.upper()}: —"
        lines.append(line)
    
    # Выбираем случайный шаблон ответа и подставляем в него курсы
    template = random.choice(PRICE_RESPONSE_TEMPLATES)
    currency_lines = "\n".join(lines)
    caption = (
        template.format(currency_lines=currency_lines)
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
        random.choice(PRIVATE_MESSAGE_RESPONSE_TEMPLATES),
        reply_markup=kb.as_markup()
    )
    logger.debug("Отправлен ответ на личное сообщение пользователю %s (%s)",
                 message.from_user.username, message.from_user.id)
