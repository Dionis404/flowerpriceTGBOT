# handlers.py
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from config import CHAT_LINK, PRIVATE_MESSAGE_TEXT, GROUP_CHAT_ID
from price_checker import fetch_current_prices, CURRENCIES
from settings import load_settings, save_settings, is_admin, add_admin, remove_admin, add_group, remove_group, load_groups
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
        # Список вариантов ответов при ошибке получения курса
        PRICE_ERROR_TEMPLATES = [
            "❌ Даже мои казначеи не смогли добыть данные о курсе. Вернитесь, когда они перестанут бездельничать.",
            "❌ Курс недоступен. Видимо, ваши жалкие рынки сегодня спят. Попробуйте позже.",
            "❌ Не удалось узнать курс. Моё терпение ограничено, так что приходите, когда будет информация."
        ]
        await message.answer(random.choice(PRICE_ERROR_TEMPLATES))
        logger.warning("Не удалось получить текущий курс для пользователя %s (%s) из чата %s (%s)",
                         message.from_user.username, message.from_user.id,
                         message.chat.title, message.chat.id)
        return
    
    # Формируем строки с курсами для подстановки в шаблон
    lines = []
    emoji_map = {"usd": ""}
    for c in CURRENCIES:
        price = current.get(c)
        if price is not None:
            line = f"{c.upper()}: {price:.4f}"
        else:
            line = f"{c.upper()}: —"
        lines.append(line)
    
    # Выбираем случайный шаблон ответа и подставляем в него курсы
    template = random.choice(PRICE_RESPONSE_TEMPLATES)
    currency_lines = "\n".join(lines)
    caption = template.format(currency_lines=currency_lines)
    
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
    logger.info("Тип чата: %s, текст сообщения: %s", message.chat.type, message.text)
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
async def set_threshold_handler(message: types.Message):
    """Обработчик команды /set_threshold для изменения порога изменения цены"""
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    # Парсинг аргумента команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /set_threshold <значение>")
        return
    
    try:
        new_threshold = float(args[1])
        if new_threshold <= 0:
            await message.answer("❌ Порог должен быть положительным числом")
            return
    except ValueError:
        await message.answer("❌ Неверный формат числа")
        return
    
    # Загрузка текущих настроек
    settings = load_settings()
    if not settings:
        settings = {"price_change_threshold": 15.0, "check_interval": 60}
    
    settings["price_change_threshold"] = new_threshold
    save_settings(settings)
    
    await message.answer(f"✅ Порог изменения цены установлен на {new_threshold}%")


async def add_group_handler(message: types.Message):
    """Обработчик команды /add_group для добавления новой группы"""
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    # Парсинг аргументов команды
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("❌ Использование: /add_group <id> <название>")
        return
    
    try:
        group_id = int(args[1])
        group_name = args[2]
    except ValueError:
        await message.answer("❌ Неверный формат ID группы")
        return
    
    # Добавление новой группы
    if add_group(group_id, group_name):
        await message.answer(f"✅ Группа '{group_name}' добавлена")
    else:
        await message.answer("❌ Ошибка при добавлении группы (возможно, группа уже существует)")


async def remove_group_handler(message: types.Message):
    """Обработчик команды /remove_group для удаления группы"""
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    # Парсинг аргументов команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /remove_group <id>")
        return
    
    try:
        group_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID группы")
        return
    
    # Удаление группы
    groups = load_groups()
    if not groups or "group_chats" not in groups:
        await message.answer("❌ Файл групп не найден")
        return
    
    group_name = None
    for group in groups["group_chats"]:
        if group["id"] == group_id:
            group_name = group["name"]
            break
    
    if remove_group(group_id):
        await message.answer(f"✅ Группа '{group_name}' удалена")
    else:
        await message.answer("❌ Группа не найдена")


async def list_groups_handler(message: types.Message):
    """Обработчик команды /list_groups для отображения списка групп"""
    # Проверка прав администратора (опционально)
    # if not is_admin(message.from_user.id):
    #     await message.answer("❌ У вас нет прав для выполнения этой команды")
    #     return
    
    # Загрузка текущих групп
    groups = load_groups()
    if not groups or "group_chats" not in groups:
        await message.answer("❌ Файл групп не найден")
        return
    
    # Формирование списка групп
    if not groups["group_chats"]:
        await message.answer("📭 Список групп пуст")
        return
    
    lines = ["📝 Список отслеживаемых групп:"]
    for group in groups["group_chats"]:
        lines.append(f"  • {group['name']} (ID: {group['id']})")
    
    await message.answer("\n".join(lines))


async def add_admin_handler(message: types.Message):
    """Обработчик команды /add_admin для добавления администратора"""
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    # Парсинг аргументов команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /add_admin <id>")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
        return
    
    # Добавление администратора
    if add_admin(user_id):
        await message.answer(f"✅ Пользователь {user_id} добавлен в список администраторов")
    else:
        await message.answer("❌ Ошибка при добавлении администратора (возможно, пользователь уже является администратором)")


async def remove_admin_handler(message: types.Message):
    """Обработчик команды /remove_admin для удаления администратора"""
    # Проверка прав администратора
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    # Парсинг аргументов команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Использование: /remove_admin <id>")
        return
    
    try:
        user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID пользователя")
        return
    
    # Удаление администратора
    if remove_admin(user_id):
        await message.answer(f"✅ Пользователь {user_id} удален из списка администраторов")
    else:
        await message.answer("❌ Пользователь не найден в списке администраторов")
    logger.debug("Отправлен ответ на личное сообщение пользователю %s (%s)",
                 message.from_user.username, message.from_user.id)
