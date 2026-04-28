import logging

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage

from src.keyboards import kb_guard_dashboard

logger = logging.getLogger(__name__)


async def notify_guards(bot: Bot, data: dict, storage: RedisStorage):
    guard_ids = data.get("guard_telegram_ids", [])
    if not guard_ids:
        return

    text = "🆕 Створено нову заявку!\n"

    for tg_id in guard_ids:
        try:
            await bot.send_message(chat_id=tg_id, text=text, parse_mode="Markdown", reply_markup=kb_guard_dashboard)
        except Exception as e:
            logger.warning(f"Не вдалося відправити сповіщення охоронцю {tg_id}: {e}")


async def notify_resident_closed(bot: Bot, data: dict, storage: RedisStorage):
    tg_id = data.get("resident_telegram_id")
    if not tg_id:
        return

    icon = "🚗" if "car" in data["type"] else "🚶‍♂️"

    text = (
        f"✅ Вашого гостя пропущено!\n\n"
        f"Гість/Авто: {icon} {data['value']}\n"
        f"Пропустив: {data['processed_by']}"
    )

    try:
        await bot.send_message(chat_id=tg_id, text=text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Не вдалося відправити сповіщення мешканцю {tg_id}: {e}")


async def notify_resident_expired(bot: Bot, data: dict, storage: RedisStorage):
    tg_id = data.get("resident_telegram_id")
    icon = "🚗" if "car" in data["type"] else "🚶‍♂️"

    text = (
        f"⌛ <b>Термін дії заявки вичерпано</b>\n\n"
        f"Заявка на {icon} <b>{data['value']}</b> була активна понад {data['expiration_hours']} годин "
        f"і автоматично переведена в статус <b>Прострочена</b>."
    )

    try:
        await bot.send_message(chat_id=tg_id, text=text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Не вдалося відправити сповіщення мешканцю {tg_id}: {e}")
