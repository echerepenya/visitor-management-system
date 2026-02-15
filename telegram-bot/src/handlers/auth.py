import httpx
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
)

from src.config import HEADERS, API_URL, LIVING_COMPLEX_NAME
from src.keyboards import kb_auth, kb_main

router = Router()


# /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Entry point. Reset status and asks for credentials
    """
    await state.clear()
    await message.answer(
        "👋 **Вітаю! Я бот вашого ЖК.**\n\n"
        "Я допоможу вам пропускати гостей та перевіряти авто.\n"
        "Для початку роботи мені потрібно підтвердити, що ви є мешканцем.\n"
        "\n"
        "Натискаючи кнопку «Надіслати номер телефону», ви надаєте згоду на обробку "
        "ваших персональних даних (телефон, ПІБ, адреса, авто) для забезпечення пропускного режиму.\n"
        "\n"
        f"Дані зберігаються у ініціативної групи ЖК {LIVING_COMPLEX_NAME}, надаються в користування охоронній компанії "
        "і можуть бути видалені по вашому запиту.\n",
        reply_markup=kb_auth
    )


# Contact is shared with bot
@router.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):
    """
    Processes shared credentials
    """
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer(
            "⛔️ **Помилка безпеки!**\n\n"
            "Ви надіслали чужий контакт або переслали повідомлення.\n"
            "Будь ласка, натисніть саме кнопку **'📱 Надіслати номер телефону'** внизу екрану.",
            reply_markup=kb_auth
        )
        return

    payload = {
        "phone": contact.phone_number,
        "telegram_id": message.from_user.id,
        "first_name": message.from_user.first_name or "Unknown"
    }

    await message.answer("⏳ Перевіряю в базі...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_URL}/telegram/login", json=payload, headers=HEADERS, timeout=10.0)

            if response.status_code == 200:
                data = response.json()

                await message.answer(
                    f"✅ **Авторизація успішна!**\n\n"
                    f"👤 **{data.get('name')}**\n"
                    f"🏠 {data.get('apartment')}\n\n"
                    f"Тепер ви можете:\n"
                    f"🔹 Вводити номер авто для перевірки\n"
                    f"🔹 Створювати заявки на пропуск гостей",
                    reply_markup=kb_main
                )
            elif response.status_code == 404:
                await message.answer(
                    "❌ **Ваш номер не знайдено в базі мешканців.**\n\n"
                    "Будь ласка, зверніться до ініціативної групи вашого будинку або охорони, щоб додати ваш номер телефону в систему.",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await message.answer(f"⚠️ Помилка сервера: {response.text}")

        except httpx.RequestError as e:
            await message.answer(f"⚠️ Помилка з'єднання з сервером: {e}")
