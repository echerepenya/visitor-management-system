import logging

import httpx
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
)

from src.config import settings
from src.keyboards import kb_auth, kb_main, kb_guard_dashboard

router = Router()

logger = logging.getLogger(__name__)


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
        f"Дані зберігаються у ініціативної групи ЖК {settings.LIVING_COMPLEX_NAME}, надаються в користування охоронній компанії "
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
            response = await client.post(f"{settings.API_URL}/telegram/login", json=payload, headers=settings.HEADERS, timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                role = data.get('role')

                await state.update_data(
                    role=role,
                    name=data.get('name'),
                    is_admin=data.get('is_admin')
                )

                if role == 'guard':
                    await message.answer(
                        f"✅ **Авторизація успішна!**\n\n"
                        f"👤 **{data.get('name')}**",
                        reply_markup=ReplyKeyboardRemove()
                    )

                    await message.answer(
                        f"Ви увійшли як співробітник охоронної компанії. Вводьте текст в поле нижче щоб перевірити авто по номеру, "
                        f"та використовуйте кнопку меню для переходу на сторінку з заявками.",
                        reply_markup=kb_guard_dashboard
                    )
                else:
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
                logger.error(f"Login error for {message.from_user.id}: {response.status_code} {response.text}")
                await message.answer("⚠️ Помилка сервера. Спробуйте пізніше.")

        except httpx.RequestError as e:
            logger.error(f"Connection error for {message.from_user.id}: {e}")
            await message.answer("⚠️ Помилка з'єднання. Спробуйте пізніше.")


async def force_logout_user(bot: Bot, data: dict, storage: RedisStorage):
    tg_id = data.get("telegram_id")
    if not tg_id:
        return

    key = StorageKey(
        bot_id=bot.id,
        chat_id=tg_id,
        user_id=tg_id
    )

    await storage.set_data(key=key, data={})

    await storage.set_state(key=key, state=None)
