import asyncio
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from src.api import api_client

from src.config import settings
from src.keyboards import kb_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    
    logger.info("Fetching residents from backend...")
    try:
        resp = await api_client.get("/telegram/residents")
        resp.raise_for_status()
        telegram_ids = resp.json()
    except Exception as e:
        logger.error(f"Failed to get residents: {e}")
        await bot.session.close()
        return

    logger.info(f"Found {len(telegram_ids)} residents. Starting broadcast...")
    
    text = (
        "🎉 **Головне меню оновлено!**\n\n"
        "В рамках підготовки до запуску послуги **Гостьова парковка**, ми оновили головне меню бота. "
        "Нова кнопка вже додана у розділ «Додаткові сервіси», але деякий час вона буде неактивною — це потрібно для тестування і навчання охорони.\n\n"
        "Слідкуйте за оновленнями!"
    )
    
    success_count = 0
    for tg_id in telegram_ids:
        try:
            await bot.send_message(chat_id=tg_id, text=text, reply_markup=kb_main)
            success_count += 1
            await asyncio.sleep(0.05)  # rate limit protection
        except Exception as e:
            logger.warning(f"Failed to send to {tg_id}: {e}")
            
    logger.info(f"Broadcast completed. Successfully sent to {success_count}/{len(telegram_ids)} residents.")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
