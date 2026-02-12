import asyncio
import logging
import os
import sys

import httpx
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://backend:8000/api")

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


class PassState(StatesGroup):
    waiting_for_type = State()  # Taxi, Guest, etc.
    waiting_for_value = State()  # car plate number


# --- keyboards ---

# 1. Auth Button
kb_auth = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Надіслати номер телефону", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Натисніть кнопку знизу..."
)

# 2. Main menu
kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎫 Замовити перепустку")],
        [KeyboardButton(text="👮 Контакти охорони"), KeyboardButton(text="ℹ️ Мій статус")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Введіть номер авто для пошуку..."
)

# 3. Visitor types
kb_pass_types = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚗 Гість на авто"), KeyboardButton(text="🚕 Таксі")],
        [KeyboardButton(text="🛵 Доставка"), KeyboardButton(text="🚶 Пішки")],
        [KeyboardButton(text="❌ Скасувати")]
    ],
    resize_keyboard=True
)

# 4. Cancel button
kb_cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Скасувати")]],
    resize_keyboard=True
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()


# ==========================================
# 1. ЛОГІКА АВТОРИЗАЦІЇ
# ==========================================

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """
    Точка входу. Скидає всі стани і просить авторизацію.
    """
    await state.clear()
    await message.answer(
        "👋 **Вітаю! Я бот вашого ЖК.**\n\n"
        "Я допоможу вам пропускати гостей та перевіряти авто.\n"
        "Для початку роботи мені потрібно підтвердити, що ви є мешканцем.",
        reply_markup=kb_auth
    )


@dp.message(F.contact)
async def handle_contact(message: Message, state: FSMContext):
    """
    Processes shared contact
    """
    contact = message.contact

    payload = {
        "phone": contact.phone_number,
        "telegram_id": message.from_user.id,
        "first_name": message.from_user.first_name or "Unknown"
    }

    await message.answer("⏳ Перевіряю в базі...")

    async with httpx.AsyncClient() as client:
        try:
            # Стукаємо на наш новий ендпоінт авторизації
            response = await client.post(f"{API_URL}/auth/telegram", json=payload, timeout=10.0)

            if response.status_code == 200:
                data = response.json()
                # Успіх
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
                # Немає в базі
                await message.answer(
                    "❌ **Ваш номер не знайдено в базі мешканців.**\n\n"
                    "Будь ласка, зверніться до голови ОСББ або охорони, щоб додати ваш номер телефону в систему.",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                # Помилка сервера
                await message.answer(f"⚠️ Помилка сервера: {response.text}")

        except httpx.RequestError as e:
            await message.answer(f"⚠️ Помилка з'єднання з сервером: {e}")


# 2. Creating a guest request
@dp.message(F.text == "🎫 Замовити перепустку")
async def start_pass_flow(message: Message, state: FSMContext):
    await state.set_state(PassState.waiting_for_type)
    await message.answer("Хто до вас прямує?", reply_markup=kb_pass_types)


@dp.message(PassState.waiting_for_type)
async def pass_type_chosen(message: Message, state: FSMContext):
    text = message.text

    if text == "❌ Скасувати":
        await state.clear()
        await message.answer("Скасовано.", reply_markup=kb_main)
        return

    type_map = {
        "🚗 Гість на авто": "guest_car",
        "🚕 Таксі": "taxi",
        "🛵 Доставка": "delivery",
        "🚶 Пішки": "guest_foot"
    }

    selected_type = type_map.get(text)
    if not selected_type:
        await message.answer("Будь ласка, оберіть варіант із меню.")
        return

    await state.update_data(pass_type_code=selected_type, pass_type_text=text)

    if selected_type in ["guest_car", "taxi"]:
        prompt = "✍️ Введіть **номер авто**:"
    else:
        prompt = "✍️ Введіть **ім'я гостя** або назву служби доставки:"

    await state.set_state(PassState.waiting_for_value)
    await message.answer(prompt, reply_markup=kb_cancel)


@dp.message(PassState.waiting_for_value)
async def pass_value_chosen(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("Скасовано.", reply_markup=kb_main)
        return

    value = message.text.strip()
    data = await state.get_data()

    payload = {
        "telegram_id": message.from_user.id,
        "type": data['pass_type_code'],
        "value": value,
        "comment": "Створено через Telegram"
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{API_URL}/requests/", json=payload, timeout=10.0)

            if resp.status_code == 201:
                await message.answer(
                    f"✅ **Заявку успішно створено!**\n\n"
                    f"Тип: {data['pass_type_text']}\n"
                    f"Інфо: **{value}**\n\n"
                    f"Охорона вже бачить цю інформацію.",
                    reply_markup=kb_main
                )
            elif resp.status_code == 404:
                await message.answer("❌ Помилка авторизації. Натисніть /start", reply_markup=kb_main)
            else:
                await message.answer(f"⚠️ Помилка: {resp.text}", reply_markup=kb_main)

    except Exception as e:
        await message.answer(f"⚠️ Помилка з'єднання: {e}", reply_markup=kb_main)

    await state.clear()


# 3. Informational buttons
@dp.message(F.text == "👮 Контакти охорони")
async def cmd_contacts(message: Message):
    await message.answer(
        "👮 **Пост охорони (цілодобово):**\n"
        "📞 +380 50 123 45 67\n"
        "📍 В'їзд №1"
    )


@dp.message(F.text == "ℹ️ Мій статус")
async def cmd_me(message: Message):
    # Тут можна зробити запит на API, щоб показати актуальну інфу
    await message.answer("Ваш статус: ✅ Активний мешканець")


# 4. Car search by plain text enter
@dp.message(StateFilter(None))
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
            resp = await client.get(f"{API_URL}/cars/check/{text}", timeout=5.0)

            if resp.status_code != 200:
                await msg.edit_text("⚠️ Помилка сервера при пошуку.")
                return

            data = resp.json()

            if data.get("found"):
                # -- ВАРІАНТ 1: ЗНАЙДЕНО (Мешканець) --
                if data["type"] == "resident":
                    info = data["info"]
                    res_text = (
                        f"🚙 **АВТО МЕШКАНЦЯ**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"Власник: {info.get('owner')}\n"
                        f"🏠 **{info.get('address')}**\n"
                        f"📞 `{info.get('phone')}`"
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


async def main():
    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped!")
