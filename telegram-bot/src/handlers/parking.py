import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.states import ParkingState
from src.keyboards import kb_main, kb_additional_services, kb_cancel
from src.api import backend_request
from src.utils import normalize_plate

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "📂 Додаткові сервіси")
async def cmd_additional_services(message: Message):
    await message.answer("Оберіть сервіс:", reply_markup=kb_additional_services)

@router.message(F.text == "◀️ Головне меню")
async def cmd_back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Головне меню", reply_markup=kb_main)

@router.message(F.text == "🅿️ Гостьова парковка")
async def cmd_parking(message: Message, state: FSMContext):
    # Fetch status first
    status_resp = await backend_request("/api/telegram/parking/status", method="GET")
    if status_resp and status_resp.get("free_spots", 0) <= 0:
        await message.answer("На жаль, наразі немає вільних гостьових паркомісць. Спробуйте пізніше.", reply_markup=kb_additional_services)
        return
        
    free_spots = status_resp.get("free_spots", 0) if status_resp else "?"
    
    await message.answer(
        f"🅿️ **Гостьова парковка**\nВільних місць: **{free_spots}/11**\n\n"
        "Введіть номер авто (без пробілів, лише букви та цифри):",
        reply_markup=kb_cancel
    )
    await state.set_state(ParkingState.waiting_for_plate)

@router.message(ParkingState.waiting_for_plate)
async def process_parking_plate(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("Скасовано.", reply_markup=kb_additional_services)
        return

    plate = normalize_plate(message.text)
    if not plate:
        await message.answer("Некоректний формат номера. Спробуйте ще раз або натисніть Скасувати.")
        return

    # Call backend to create request
    resp = await backend_request(
        f"/api/telegram/parking/create-request?plate={plate}",
        method="POST",
        json_data={"telegram_id": message.from_user.id}
    )

    if resp and resp.get("status") == "ok":
        await message.answer(
            f"✅ Місце для авто **{plate}** заброньовано на 30 хвилин!\n\n"
            "Зверніться до охорони (Пост 2) для отримання брелока від шлагбаума.",
            reply_markup=kb_main
        )
    else:
        err = resp.get("detail", "Помилка") if isinstance(resp, dict) else "Помилка сервера"
        await message.answer(f"❌ Не вдалося створити заявку: {err}", reply_markup=kb_additional_services)

    await state.clear()
