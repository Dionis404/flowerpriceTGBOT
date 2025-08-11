# price_checker.py
import aiohttp
import asyncio
import json
import os
from datetime import datetime
from typing import Optional, Dict

from aiogram import Bot
from config import (
    COIN_ID, PRICE_CHANGE_THRESHOLD, CHECK_INTERVAL,
    GROUP_CHAT_ID, UP_IMAGE, DOWN_IMAGE
)

PRICE_FILE = "last_price.json"
CURRENCIES = ["usd", "rub", "uah"]  # порядок: USD, RUB, UAH


def load_last_price() -> Optional[Dict[str, float]]:
    """Загружает последнюю цену из файла (или None)."""
    if not os.path.exists(PRICE_FILE):
        return None
    try:
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Приведём значения к float на всякий случай
        return {k: float(v) for k, v in data.items()}
    except Exception:
        return None


def save_last_price(price: Dict[str, float]):
    """Сохраняет текущую цену в файл (тихо, без сообщений)."""
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(price, f)


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
                    return None
                data = await resp.json()
                coin = data.get(COIN_ID, {})
                # Если чего-то нет — возвращаем None
                if not all(c in coin for c in CURRENCIES):
                    return None
                return {c: float(coin[c]) for c in CURRENCIES}
    except Exception:
        return None


async def check_price_and_notify(bot: Bot):
    """
    Основная функция: загружает старую цену, получает новую, сравнивает.
    Если сработал порог — отправляет одно сообщение в GROUP_CHAT_ID с картинкой.
    Всегда сохраняет новую цену в файл в конце (чтобы помнить при перезапуске).
    """
    last = load_last_price()
    current = await fetch_current_prices()
    if current is None:
        # API не доступен или формат ответа неправильный — ничего не делаем
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

    # Собираем те валюты, которые превысили порог
    triggers = {c: pct for c, pct in changes.items() if abs(pct) >= PRICE_CHANGE_THRESHOLD}

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
            line = f"{emoji_map.get(c,'')} {c.upper()}: — → {new:.6f}"
        else:
            pct = ((new - old) / old) * 100 if old != 0 else 0.0
            sign = "+" if pct > 0 else ""
            line = f"{emoji_map.get(c,'')} {c.upper()}: {old:.6f} → {new:.6f} ({sign}{pct:.2f}%)"
        lines.append(line)

    caption = (
        f"{'📈 Цена выросла!' if trigger_percent > 0 else '📉 Цена упала!'}\n\n"
        + "\n".join(lines)
        + f"\n\n📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    )

    # Отправляем: если картинка есть — отправляем фото с подписью, иначе простое сообщение
    try:
        if os.path.exists(img_path):
            with open(img_path, "rb") as ph:
                await bot.send_photo(chat_id=GROUP_CHAT_ID, photo=ph, caption=caption)
        else:
            await bot.send_message(chat_id=GROUP_CHAT_ID, text=caption)
    except Exception:
        # Не падаем при ошибке отправки — просто логируем в консоль
        print("Ошибка при отправке уведомления (группа):", exc_info=True)

    # Сохраняем новую цену (в любом случае)
    save_last_price(current)


# Небольшая обёртка для фонового запуска (используется в bot.py)
async def price_monitor_loop(bot: Bot):
    while True:
        try:
            await check_price_and_notify(bot)
        except Exception as e:
            print("Ошибка в price_monitor_loop:", e)
        await asyncio.sleep(CHECK_INTERVAL)
