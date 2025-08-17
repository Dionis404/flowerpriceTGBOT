# price_checker.py
import aiohttp
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict
import random
# Список вариантов ответов для случая, когда цена выросла
PRICE_UP_RESPONSE_TEMPLATES = [
    """Ха! Цены растут, а значит, моя казна полнеет:  
{currency_lines}
Продолжайте в том же духе, крестьяне, и я буду… слегка доволен.""",

    """Прекрасно! Ваши жалкие монеты сегодня стоят больше:  
{currency_lines}
Всё это, разумеется, работает на моё богатство.""",

    """Видите, простолюдины? Даже рынок склоняется перед моей властью:  
{currency_lines}
Но не льстите себе — выгоду получу я, а не вы.""",

    """Цены растут, и вместе с ними — моё настроение:  
{currency_lines}
Убедитесь, что разница окажется в королевской казне."""
]
# Список вариантов ответов для случая, когда цена упала
PRICE_DOWN_RESPONSE_TEMPLATES = [
    """Хм… цены упали. Кто-то из вас снова облажался:  
{currency_lines}
Надеюсь, вы компенсируете убытки… из своего кармана, разумеется.""",

    """Падение цен? Прекрасно… для меня это лишь повод поднять налоги:  
{currency_lines}
Ваши потери — моя выгода. Таков порядок.""",

    """Цены снизились? Пф, жалкие цифры не меняют сути:  
{currency_lines}
Вы всё равно должны мне прежнее количество золота.""",

    """Упали цены? Значит, мне придётся вытрясти с вас ещё больше:  
{currency_lines}
Так что готовьтесь платить… и платить щедро."""
]
from aiogram import Bot
from config import (
    COIN_ID, UP_IMAGE, DOWN_IMAGE
)
from settings import load_settings, load_groups, get_group_ids
from utils import format_currency_lines


logger = logging.getLogger(__name__)

PRICE_FILE = "last_price.json"
CURRENCIES = ["usd", "rub", "uah"]  # порядок: USD, RUB, UAH


def load_last_price() -> Optional[Dict[str, float]]:
    """Загружает последнюю цену из файла (или None)."""
    if not os.path.exists(PRICE_FILE):
        logger.debug("Файл с последней ценой не найден")
        return None
    try:
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Приведём значения к float на всякий случай
        result = {k: float(v) for k, v in data.items()}
        logger.debug("Последняя цена загружена: %s", result)
        return result
    except Exception as e:
        logger.warning("Ошибка при загрузке последней цены: %s", e)
        return None


def save_last_price(price: Dict[str, float]):
    """Сохраняет текущую цену в файл (тихо, без сообщений)."""
    try:
        with open(PRICE_FILE, "w", encoding="utf-8") as f:
            json.dump(price, f)
        logger.debug("Цена сохранена в файл: %s", price)
    except Exception as e:
        logger.warning("Ошибка при сохранении цены в файл: %s", e)


async def fetch_current_prices() -> Optional[Dict[str, float]]:
    """
    Получает текущие цены через CoinGecko /simple/price.
    Возвращает словарь вида {'usd': float, 'rub': float, 'uah': float} или None.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": COIN_ID, "vs_currencies": ",".join(CURRENCIES)}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    logger.warning("API вернул статус %s", resp.status)
                    return None
                data = await resp.json()
                coin = data.get(COIN_ID, {})
                # Если чего-то нет — возвращаем None
                if not all(c in coin for c in CURRENCIES):
                    logger.warning("Не все валюты получены из API: %s", coin)
                    return None
                result = {c: float(coin[c]) for c in CURRENCIES}
                logger.debug("Текущие цены получены: %s", result)
                return result
    except Exception as e:
        logger.warning("Ошибка при получении цен: %s", e)
        return None


async def check_price_and_notify(bot: Bot):
    """
    Основная функция: загружает старую цену, получает новую, сравнивает.
    Если сработал порог — отправляет одно сообщение в GROUP_CHAT_ID с картинкой.
    Всегда сохраняет новую цену в файл в конце (чтобы помнить при перезапуске).
    """
    logger.debug("Проверка цены начата")
    last = load_last_price()
    current = await fetch_current_prices()
    
    if current is None:
        # API не доступен или формат ответа неправильный — ничего не делаем
        logger.warning("Не удалось получить текущие цены")
        return

    # Если нет сохранённой прошлой цены — просто сохраним и уйдём
    if not last:
        save_last_price(current)
        return

    # Вычисляем процентные изменения по всем валютам (если возможно)
    changes = {}
    for c in CURRENCIES:
        old = last.get(c)
        new = current.get(c)
        if old is None or old == 0:
            continue
        pct = ((new - old) / old) * 100
        changes[c] = pct

    # Загружаем настройки
    settings = load_settings()
    price_change_threshold = settings.get("price_change_threshold", 15.0) if settings else 15.0
    
    # Собираем те валюты, которые превысили порог
    triggers = {c: pct for c, pct in changes.items() if abs(pct) >= price_change_threshold}

    if not triggers:
        # Ничего не сработало — просто сохраняем новую цену
        save_last_price(current)
        return

    # Выберем валюту с наибольшим абсолютным изменением для определения направления (up/down)
    trigger_currency = max(triggers.keys(), key=lambda k: abs(triggers[k]))
    trigger_percent = triggers[trigger_currency]

    # Выберем картинку по знаку изменения
    img_path = UP_IMAGE if trigger_percent > 0 else DOWN_IMAGE

    # Сформируем текст сообщения — показываем все 3 валюты (старое -> новое и процент)
    lines = []
    emoji_map = {"usd": "🇺🇸", "rub": "🇷🇺", "uah": "🇺🇦"}
    for c in CURRENCIES:
        old = last.get(c)
        new = current.get(c)
        if old is None:
            line = f"{emoji_map.get(c,'')} {c.upper()}: — → {new:.2f}"
        else:
            pct = ((new - old) / old) * 100 if old != 0 else 0.0
            sign = "+" if pct > 0 else ""
            line = f"{emoji_map.get(c,'')} {c.upper()}: {old:.2f} → {new:.2f} ({sign}{pct:.2f}%)"
        lines.append(line)

    # Если цена выросла, используем случайный шаблон ответа
    if trigger_percent > 0:
        template = random.choice(PRICE_UP_RESPONSE_TEMPLATES)
        currency_lines = "\n".join(lines)
        caption = template.format(currency_lines=currency_lines)
    else:
        # Если цена упала, используем случайный шаблон ответа
        template = random.choice(PRICE_DOWN_RESPONSE_TEMPLATES)
        currency_lines = "\n".join(lines)
        caption = template.format(currency_lines=currency_lines)

    # Отправляем уведомления во все группы
    logger.info("Получение списка групп для отправки уведомлений")
    group_ids = get_group_ids()
    logger.info("Список групп для отправки уведомлений: %s", group_ids)
    if not group_ids:
        # Если группы не настроены, отправляем в группу по умолчанию из config.py
        from config import GROUP_CHAT_ID
        group_ids = [GROUP_CHAT_ID]
        logger.info("Группы не настроены, используем группу по умолчанию: %s", GROUP_CHAT_ID)
    else:
        logger.info("Используем все зарегистрированные группы: %s", group_ids)
    
    logger.info("Начало отправки уведомлений в %d групп(ы)", len(group_ids))
    for group_id in group_ids:
        try:
            logger.info("Отправка уведомления в группу %s", group_id)
            if os.path.exists(img_path):
                # Проверяем, что файл изображения не пустой
                if os.path.getsize(img_path) > 0:
                    with open(img_path, "rb") as ph:
                        await bot.send_photo(chat_id=group_id, photo=ph, caption=caption)
                        logger.info("Уведомление с изображением отправлено в группу %s", group_id)
                else:
                    logger.warning("Файл изображения пустой: %s", img_path)
                    await bot.send_message(chat_id=group_id, text=caption)
                    logger.info("Уведомление без изображения отправлено в группу %s", group_id)
            else:
                logger.warning("Файл изображения не найден: %s", img_path)
                await bot.send_message(chat_id=group_id, text=caption)
                logger.info("Уведомление без изображения отправлено в группу %s", group_id)
        except Exception as e:
            # Не падаем при ошибке отправки — просто логируем в консоль
            logger.error("Ошибка при отправке уведомления в группу %s: %s", group_id, e)
    logger.info("Завершена отправка уведомлений в %d групп(ы)", len(group_ids))

    # Сохраняем новую цену (в любом случае)
    save_last_price(current)
    logger.debug("Проверка цены завершена")


# Небольшая обёртка для фонового запуска (используется в bot.py)
async def price_monitor_loop(bot: Bot):
    logger.info("Начало цикла мониторинга цен")
    while True:
        try:
            await check_price_and_notify(bot)
        except Exception as e:
            logger.error("Ошибка в price_monitor_loop: %s", e)
        
        # Загружаем интервал проверки из настроек
        settings = load_settings()
        check_interval = settings.get("check_interval", 60) if settings else 60
        
        logger.debug("Ожидание следующей итерации мониторинга")
        await asyncio.sleep(check_interval)
