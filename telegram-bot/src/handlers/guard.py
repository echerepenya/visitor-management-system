import logging
from aiogram import Router, F
from aiogram.types import Message
from src.api import api_client

router = Router()

logger = logging.getLogger(__name__)


@router.message(F.text == "📊 Заявки на пропуск")
async def cmd_orders_count(message: Message):
    count = 0
    try:
        response = await api_client.get("/telegram/orders/new-count")
        if response.status_code == 200:
            count = response.json().get("count", 0)
    except Exception as e:
        logger.error(f"Error fetching new pass requests: {e}")

    await message.answer(
        f"📊 **Нових заявок: {count}**\n\n"
        "Повний список та деталі за посиланням:\n"
        "🌐 https://lipinka2guard.manidat.com"
    )
