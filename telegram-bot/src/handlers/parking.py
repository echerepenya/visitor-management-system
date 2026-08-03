import logging
from src.api import api_client
import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.states import ParkingState, MenuState
from src.keyboards import kb_main, kb_additional_services, kb_cancel
from src.config import settings

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📂 Більше...")
async def cmd_additional_services(message: Message, state: FSMContext):
    await state.set_state(MenuState.additional_services)
    await message.answer("Оберіть сервіс:", reply_markup=kb_additional_services)


@router.message(F.text == "◀️ Головне меню")
async def cmd_back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Головне меню", reply_markup=kb_main)


@router.message(F.text == "🅿️ Гостьова парковка")
async def cmd_parking(message: Message, state: FSMContext):
    await message.answer(
        "🚧 **Сервіс гостьової парковки на етапі тестування.**\n\n"
        "Кнопка додана для підготовки та навчання охорони. "
        "Повноцінний запуск відбудеться найближчим часом. Дякуємо за терпіння!",
        reply_markup=kb_additional_services
    )
    return
    
    # Fetch status first
    # status_resp = None
    # try:
    #     response = await api_client.get("/telegram/parking/status")
    #     if response.status_code == 200:
    #         status_resp = response.json()
    # except Exception as e:
    #     logger.error(f"Error fetching parking status: {e}")
    # 
    # if status_resp and status_resp.get("free_spots", 0) <= 0:
    #     await message.answer("На жаль, наразі немає вільних гостьових паркомісць. Спробуйте пізніше.",
    #                          reply_markup=kb_additional_services)
    #     return
    # 
    # free_spots = status_resp.get("free_spots", 0) if status_resp else "?"
    # 
    # await message.answer(
    #     f"🅿️ **Гостьова парковка**\nВільних місць: **{free_spots}/11**\n\n"
    #     "Введіть номер авто (без пробілів, лише букви та цифри):",
    #     reply_markup=kb_cancel
    # )
    # await state.set_state(ParkingState.waiting_for_plate)


@router.message(ParkingState.waiting_for_plate)
async def process_parking_plate(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("Скасовано.", reply_markup=kb_additional_services)
        return

    plate = re.sub(r'[\W_]+', '', message.text or '')
    if len(plate) < 3 or len(plate) > 15:
        await message.answer("Некоректний формат номера. Спробуйте ще раз або натисніть Скасувати.")
        return

    try:
        response = await api_client.post(
            f"/telegram/parking/create-request?plate={plate}",
            json={"telegram_id": message.from_user.id}
        )

        try:
            resp = response.json()
        except:
            resp = {"detail": "Помилка сервера"}

    except Exception as e:
        logger.error(f"Error creating parking request: {e}")
        resp = {"detail": "Помилка з'єднання"}

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
