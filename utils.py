# utils.py
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Сопоставление валют с эмодзи
CURRENCY_EMOJI_MAP = {
    "usd": ""
}

def format_currency_lines(current: Dict[str, float], last: Optional[Dict[str, float]] = None) -> str:
    """
    Форматирует строки с курсами валют для отображения в сообщениях.
    
    Args:
        current: Словарь с текущими значениями курсов
        last: Словарь с предыдущими значениями курсов (опционально)
        
    Returns:
        str: Отформатированные строки с курсами
    """
    lines = []
    currencies = ["usd"]
    
    for c in currencies:
        old = last.get(c) if last else None
        new = current.get(c)
        if old is None:
            line = f"{c.upper()}: — → {new:.4f}"
        else:
            pct = ((new - old) / old) * 100 if old != 0 else 0.0
            sign = "+" if pct > 0 else ""
            line = f"{c.upper()}: {old:.4f} → {new:.4f} ({sign}{pct:.2f}%)"
        lines.append(line)
    
    return "\n".join(lines)