import httpx
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)

from src.config import HEADERS, API_URL
from src.keyboards import kb_pass_types, kb_main, kb_cancel
from src.states import PassState

router = Router()


@router.message(F.text == "🎫 Замовити перепустку")
async def start_pass_flow(message: Message, state: FSMContext):
    await state.set_state(PassState.waiting_for_type)
    await message.answer("Хто до вас прямує?", reply_markup=kb_pass_types)


@router.message(PassState.waiting_for_type)
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


@router.message(PassState.waiting_for_value)
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
            resp = await client.post(f"{API_URL}/requests/", json=payload, headers=HEADERS, timeout=10.0)

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
