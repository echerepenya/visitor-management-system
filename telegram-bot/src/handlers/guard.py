import logging
import httpx
from aiogram import Router, F
from aiogram.types import Message
from src.config import HEADERS, API_URL

router = Router()

logger = logging.getLogger(__name__)


@router.message(F.text == "📊 Заявки на пропуск")
async def cmd_orders_count(message: Message):
    count = 0
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/telegram/orders/new-count", headers=HEADERS, timeout=10.0)
            if response.status_code == 200:
                count = response.json().get("count", 0)
    except Exception as e:
        logger.error(f"Error fetching new pass requests: {e}")

    await message.answer(
        f"📊 **Нових заявок: {count}**\n\n"
        "Повний список та деталі за посиланням:\n"
        "🌐 https://lipinka2guard.manidat.com"
    )
