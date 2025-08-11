# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # загружает .env при локальной разработке

BOT_TOKEN = os.getenv("BOT_TOKEN")                 # токен бота
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))  # ID группового чата (отрицательный для супергрупп)
COIN_ID = os.getenv("COIN_ID", "flower-2")         # id на CoinGecko (по умолчанию flower-2)
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", "15"))  # порог в %
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # интервал проверки в секундах
CHAT_LINK = os.getenv("CHAT_LINK", "https://t.me/+fhJvtNvdAttkNTky")  # ссылка на чат
PRIVATE_MESSAGE_TEXT = os.getenv("PRIVATE_MESSAGE_TEXT", "🚫 У меня нет желания общаться с фермерами!\n\n👉 Пиши в чат:")  # текст сообщения в личке
ASSETS_DIR = os.getenv("ASSETS_DIR", "assets")     # папка с картинками
UP_IMAGE = os.path.join(ASSETS_DIR, "up.png")
DOWN_IMAGE = os.path.join(ASSETS_DIR, "down.png")

# Базовая валидация
if not BOT_TOKEN or GROUP_CHAT_ID == 0:
    raise RuntimeError("Не заданы BOT_TOKEN или GROUP_CHAT_ID в переменных окружения")
if GROUP_CHAT_ID > 0:
    raise RuntimeError("GROUP_CHAT_ID должен быть отрицательным числом (ID супергруппы)")
