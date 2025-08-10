# price_checker.py
import aiohttp
from config import COINGECKO_ID

async def get_flower_price():
    """
    Получает цену токена Flower в USD, RUB, UAH с CoinGecko.
    Возвращает словарь с ценами.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": COINGECKO_ID,
        "vs_currencies": "usd,rub,uah"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get(COINGECKO_ID, {})
            else:
                return None
