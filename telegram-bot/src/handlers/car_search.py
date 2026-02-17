import httpx
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import (
    Message,
)

from src.config import API_URL, HEADERS
from src.translations import REQUEST_TYPE_TRANSLATION

router = Router()


@router.message(StateFilter(None))
async def handle_text_lookup(message: Message):
    text = message.text.strip()

    if text in ["🎫 Замовити перепустку", "👮 Контакти охорони", "ℹ️ Мій статус"]:
        return

    if len(text) > 15:
        await message.answer("Це не схоже на номер авто. Спробуйте ще раз.")
        return

    msg = await message.answer("🔍 Шукаю авто...")

    try:
        async with httpx.AsyncClient() as client:
            # run "smart" search in cars table and in GuestRequests
            resp = await client.get(f"{API_URL}/telegram/car-search/{text}", headers=HEADERS, timeout=5.0)

            if resp.status_code != 200:
                await msg.edit_text("⚠️ Помилка сервера при пошуку.")
                return

            data = resp.json()

            if data.get("found"):
                # find user role who made the query to return data depending on rights
                user_resp = await client.get(f"{API_URL}/telegram/user/{message.from_user.id}", headers=HEADERS, timeout=5.0)
                try:
                    user_data = user_resp.json()
                except:
                    user_data = None

                user_role = user_data.get('role') if user_data else 'resident'

                info = data["info"]

                building = info.get('building')
                apartment = f", {info.get('apartment')}" if info.get('apartment') else None

                if building:
                    address = f"{building}{apartment if apartment else ''}" if user_role == 'guard' else building
                else:
                    address = "Немає адреси"

                phone = f"📞 `{info.get('phone')}`" if user_role == 'guard' else ''
                owner = f"Власник: {info.get('owner')}`" if user_role == 'guard' else ''

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
                elif data["type"] == "guest":
                    guest_text = (
                        f"🚕 **ГІСТЬ (ЗАЯВКА)**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"Тип заявки: `{REQUEST_TYPE_TRANSLATION.get(info.get('request_type'), 'Невідомий')}`\n"
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
        await msg.edit_text(f"⚠️ Помилка з'єднання: {e}")
