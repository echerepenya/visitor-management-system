import httpx
from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.types import (
    Message,
)

from src.config import API_URL, HEADERS

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

    telegram_id = message.from_user.id

    try:
        async with httpx.AsyncClient() as client:
            # run "smart" search in cars table and in GuestRequests
            resp = await client.get(f"{API_URL}/cars/check/{text}", headers=HEADERS, timeout=5.0)

            if resp.status_code != 200:
                await msg.edit_text("⚠️ Помилка сервера при пошуку.")
                return

            data = resp.json()

            if data.get("found"):
                bot_user_data_response = await client.get(
                    f"{API_URL}/auth/telegram/{telegram_id}",
                    headers=HEADERS,
                    timeout=5.0
                )

                if bot_user_data_response.status_code == 404:
                    await message.answer("❌ Вас не знайдено в базі даних. Зверніться до адміністратора.")
                    return

                if bot_user_data_response.status_code != 200:
                    await message.answer("⚠️ Помилка отримання даних від сервера.")
                    return

                bot_user_data = bot_user_data_response.json()
                bot_user_role = bot_user_data.get("role", "resident")

                print(data["type"])

                # -- ВАРІАНТ 1: ЗНАЙДЕНО (Мешканець) --
                if data["type"] != "guest":
                    info = data["info"]
                    res_text = (
                        f"🚙 **АВТО МЕШКАНЦЯ**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"Власник: {info.get('owner')}\n"
                        f"🏠 **{info.get('address')}**\n"
                        # f"📞 `{info.get('phone')}`" if bot_user_role in ['guard', 'admin', 'superdamin'] else ''
                    )
                    await msg.edit_text(res_text)

                # -- ВАРІАНТ 2: ЗНАЙДЕНО (Гість) --
                elif data["type"] == "guest":
                    info = data["info"]
                    guest_text = (
                        f"🚕 **ГІСТЬ (ЗАЯВКА)**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"Запросив: {info.get('invited_by')}\n"
                        f"🏠 **{info.get('address')}**\n"
                        f"💬 Комент: {info.get('comment')}"
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
