from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)

from src.config import API_URL, HEADERS, logger, TIMEZONE
from src.translations import REQUEST_TYPE_TRANSLATION

router = Router()


@router.message(StateFilter(None))
async def handle_text_lookup(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ''

    if not text or text in ["🎫 Замовити перепустку", "👮 Контакти охорони", "ℹ️ Мій статус"]:
        return

    if len(text) > 15:
        await message.answer("Це не схоже на номер авто. Спробуйте ще раз.")
        return

    msg = await message.answer("🔍 Шукаю авто...")

    try:
        async with httpx.AsyncClient() as client:
            # run "smart" search in cars table and in GuestRequests
            resp = await client.post(f"{API_URL}/telegram/car-search/{quote(text)}", headers=HEADERS, json={"telegram_id": message.from_user.id}, timeout=5.0)

            if resp.status_code == 422:
                await message.answer("Це не схоже на номер авто. Спробуйте ще раз.")
                return

            if resp.status_code != 200:
                await msg.edit_text("⚠️ Помилка сервера при пошуку.")
                return

            data = resp.json()

            if data.get("found"):
                user_data = await state.get_data()
                is_detailed_info_allowed = user_data.get("role", "resident") == "guard" or user_data.get("is_admin", False)

                info = data["info"]

                building = info.get('building')
                apartment = f", {info.get('apartment')}" if info.get('apartment') else None

                if building:
                    address = f"{building}{apartment if apartment else ''}" if is_detailed_info_allowed else building
                else:
                    address = "Немає адреси"

                phone = f"📞 `{info.get('phone')}`" if is_detailed_info_allowed else ''
                owner = f"Власник: `{info.get('owner')}`" if is_detailed_info_allowed else ''

                # -- ВАРІАНТ 1: ЗНАЙДЕНО (Мешканець) --
                if data["type"] != "guest":
                    res_text = (
                        f"🚙 **АВТО МЕШКАНЦЯ**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"🏠 **{address}**\n"
                        f"{owner}\n"
                        f"{phone}"
                    )

                    await msg.edit_text(res_text)

                # -- ВАРІАНТ 2: ЗНАЙДЕНО (Гість) --
                else:
                    invited_at_raw = info.get('invited_at')
                    if invited_at_raw:
                        dt = datetime.fromisoformat(invited_at_raw)
                        local_dt = dt.astimezone(ZoneInfo(TIMEZONE))

                        invited_at = local_dt.strftime("%d.%m.%Y %H:%M")
                    else:
                        invited_at = "невідомо"

                    guest_text = (
                        f"🚕 **ГІСТЬ (ЗАЯВКА)**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"Тип заявки: {REQUEST_TYPE_TRANSLATION.get(info.get('request_type'), 'Невідомий')} від {invited_at}\n"
                        f"🏠 **{address}**\n"
                        f"{phone}"
                    )

                    await msg.edit_text(guest_text)
            else:
                # -- ВАРІАНТ 3: НЕ ЗНАЙДЕНО --
                await msg.edit_text(
                    f"⛔️ **Авто `{data.get('plate', text)}` НЕ знайдено**\n"
                    f"Немає в базі мешканців та немає заявок."
                )

    except Exception as e:
        logger.error(f"car-search error for user {message.from_user.id}: {e}")
        await msg.edit_text("⚠️ Помилка з'єднання. Спробуйте пізніше.")
