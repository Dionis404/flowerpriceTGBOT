# config.py
import os
from dotenv import load_dotenv

# Загружает файл .env в локальной среде (только если он есть)
load_dotenv()

# Читаем переменные окружения — безопасно для production и CI
BOT_TOKEN = os.getenv("BOT_TOKEN")           # обязателен
CHAT_ID = int(os.getenv("CHAT_ID", "0"))     # по умолчанию 0, приведи к int
COINGECKO_ID = os.getenv("COINGECKO_ID", "flower-2")
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", "1"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
CHAT_LINK = os.getenv("CHAT_LINK", "https://t.me/+fhJvtNvdAttkNTky")

# Базовая валидация (можешь расширить)
if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN")
