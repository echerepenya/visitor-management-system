import os

import httpx
from aiogram import Router, F
from aiogram.types import (
    Message,
)

from src.config import HEADERS, API_URL
from src.translations import ROLE_TRANSLATION

router = Router()

GUARD_CONTACT_PHONE=os.getenv("GUARD_CONTACT_PHONE", 112)


@router.message(F.text == "👮 Контакти охорони")
async def cmd_contacts(message: Message):
    await message.answer(
        "👮 **Пост охорони (цілодобово):**\n"
        f"📞 {GUARD_CONTACT_PHONE}\n"
    )


@router.message(F.text == "ℹ️ Мій статус")
async def cmd_me(message: Message):
    telegram_id = message.from_user.id

    url = f"{API_URL}/auth/telegram/{telegram_id}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers=HEADERS,
                timeout=5.0
            )

            if response.status_code == 404:
                await message.answer("❌ Вас не знайдено в базі даних. Зверніться до адміністратора.")
                return

            if response.status_code != 200:
                await message.answer("⚠️ Помилка отримання даних від сервера.")
                return

            data = response.json()

            role_en = data.get("role", "resident")
            role_ua = ROLE_TRANSLATION.get(role_en, role_en)
            full_name = data.get("full_name") or "Не вказано"
            phone = data.get("phone_number")

            text = (
                f"👤 **Ваш профіль:**\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🏷 **Роль:** {role_ua}\n"
                f"📱 **Телефон:** {phone}\n"
                f"👤 **Ім'я:** {full_name}\n"
            )

            building = data.get("building")
            if building:
                text += f"🏠 **Будинок:** {building}\n"

            apt_num = data.get("apartment_number")
            if apt_num:
                text += f"🏠 **Квартира:** {apt_num}\n"

            await message.answer(text)

        except Exception as e:
            print(f"Error connecting to backend: {e}")
            await message.answer("⚠️ Сервіс тимчасово недоступний.")
