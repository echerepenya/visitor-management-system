import asyncio
import logging
import re
import time
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx
from aiogram.exceptions import TelegramBadRequest
from redis.asyncio import Redis
from aiogram import Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import settings
from src.keyboards import ContactOwnerCB, ReplySenderCB, SendMsgCB, MESSAGES_MAP, CancelCB, SelectCarCB
from src.translations import REQUEST_TYPE_TRANSLATION

router = Router()

logger = logging.getLogger(__name__)

CAR_MESSAGE_KEYBOARD_EXPIRATION_SECONDS = 120


async def remove_expired_keyboard(bot: Bot, chat_id: int, message_id: int, keyboard_lifetime_seconds: int) -> None:
    await asyncio.sleep(keyboard_lifetime_seconds)
    try:
        await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e) or "message to edit not found" in str(e):
            pass
        else:
            logger.warning(f"Не вдалося прибрати клавіатуру (TelegramBadRequest): {e}")
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні клавіатури: {e}")


async def render_car_card(data: dict, user_data: dict):
    """
    Формує текст та клавіатуру для картки автомобіля.
    Повертає (text, reply_markup)
    """
    is_detailed_info_allowed = user_data.get("role") == "guard" or user_data.get("is_admin", False)
    info = data.get("info", {})
    plate = data.get("plate", "Невідомо")

    building = info.get('building')
    apartment = f", {info.get('apartment')}" if info.get('apartment') else ""

    if building:
        address = f"{building}{apartment}" if is_detailed_info_allowed else building
    else:
        address = "Немає адреси"

    phone = f"📞 `{info.get('phone')}`" if is_detailed_info_allowed and info.get('phone') else ""
    owner = f"Власник: `{info.get('owner')}`" if is_detailed_info_allowed and info.get('owner') else ""

    reply_markup = None

    # -- ВАРІАНТ 1: МЕШКАНЕЦЬ --
    if data.get("type") == "resident":
        text = (
            f"🚙 **АВТО МЕШКАНЦЯ**\n\n"
            f"Номер: `{plate}`\n"
            f"🏠 **{address}**\n"
            f"{owner}\n"
            f"{phone}"
        )

        target_tg_id = info.get("owner_telegram_id")
        # Кнопка зв'язку доступна тільки для мешканців, і не для свого власного авто
        if target_tg_id and user_data.get("role") == 'resident' and str(target_tg_id) != str(user_data.get("telegram_id")):
            builder = InlineKeyboardBuilder()
            builder.button(
                text="💬 Надіслати повідомлення власнику",
                callback_data=ContactOwnerCB(
                    target_id=target_tg_id,
                    plate=plate,
                    timestamp=int(time.time())
                )
            )
            reply_markup = builder.as_markup()

    # -- ВАРІАНТ 2: ГІСТЬ (ЗАЯВКА) --
    elif data.get("type") == "guest":
        invited_at_raw = info.get('invited_at')
        if invited_at_raw:
            dt = datetime.fromisoformat(invited_at_raw)
            local_dt = dt.astimezone(ZoneInfo(settings.TZ))
            invited_at = local_dt.strftime("%d.%m.%Y %H:%M")
        else:
            invited_at = "невідомо"

        text = (
            f"🚕 **ГІСТЬ (ЗАЯВКА)**\n\n"
            f"Номер: `{plate}`\n"
            f"Тип: {REQUEST_TYPE_TRANSLATION.get(info.get('request_type'), 'Невідомий')}\n"
            f"Створено: {invited_at}\n"
            f"🏠 **{address}**\n"
            f"{phone}"
        )

    # -- ВАРІАНТ 3: НЕ ЗНАЙДЕНО --
    else:
        text = f"⛔️ **Авто `{plate}` НЕ знайдено**\nНемає в базі мешканців та немає заявок."

    return text, reply_markup


@router.message(StateFilter(None))
async def handle_text_lookup(message: Message, state: FSMContext):
    original_text = message.text.strip() if message.text else ''

    if not original_text or original_text in ["🎫 Замовити перепустку", "👮 Контакти охорони", "ℹ️ Мій статус"]:
        return

    text = re.sub(r'[\W_]+', '', original_text)

    if len(text) < 3 or len(text) > 15:
        await message.answer("Це не схоже на номер авто. Введіть від 3 до 15 символів.")
        return

    user_data = await state.get_data()

    last_search_message_id = user_data.get("last_search_msg_id")
    if last_search_message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=last_search_message_id,
                reply_markup=None
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e) or "message to edit not found" in str(e):
                pass
            else:
                logger.warning(f"TelegramBadRequest при очищенні попереднього пошуку: {e}")

        await state.update_data(last_search_msg_id=None)

    msg = await message.answer("🔍 Шукаю авто...")

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Executing car search: {text} for user {message.from_user.id}")
            resp = await client.post(
                f"{settings.API_URL}/telegram/car-search/{quote(text)}",
                headers=settings.HEADERS,
                json={"telegram_id": message.from_user.id},
                timeout=5.0
            )

            if resp.status_code == 422:
                await msg.edit_text("⚠️ Неправильний формат номера. Спробуйте ще раз.")
                return

            if resp.status_code != 200:
                await msg.edit_text("⚠️ Помилка сервера при пошуку.")
                return

            data = resp.json()

            if data.get("found"):
                # --- ВАРІАНТ: ЗНАЙДЕНО КІЛЬКА (для охорони) ---
                if data.get("multiple"):
                    logger.info(f"Multiple cars found for {text}")
                    builder = InlineKeyboardBuilder()

                    for car_plate in data["cars"]:
                        builder.button(
                            text=f"🚙 {car_plate}",
                            callback_data=SelectCarCB(plate=car_plate)
                        )
                    builder.adjust(1)

                    reply_markup = builder.as_markup()
                    await msg.edit_text(
                        "🔢 **Знайдено кілька збігів.**\nОберіть потрібне авто:",
                        reply_markup=reply_markup
                    )

                    await state.update_data(last_search_msg_id=msg.message_id)
                    return

                # --- ВАРІАНТ: ТОЧНИЙ ЗБІГ ---
                logger.info(f"The car {data.get('plate', text)} was found exactly")
                res_text, reply_markup = await render_car_card(data, user_data)
                sent_msg = await msg.edit_text(res_text, reply_markup=reply_markup)

                if reply_markup:
                    await state.update_data(last_search_msg_id=sent_msg.message_id)

                    asyncio.create_task(remove_expired_keyboard(
                        bot=message.bot,
                        chat_id=sent_msg.chat.id,
                        message_id=sent_msg.message_id,
                        keyboard_lifetime_seconds=CAR_MESSAGE_KEYBOARD_EXPIRATION_SECONDS
                    ))
            else:
                # --- ВАРІАНТ: НЕ ЗНАЙДЕНО ---
                await msg.edit_text(
                    f"⛔️ **Авто `{data.get('plate', text)}` НЕ знайдено**\n"
                    f"Немає в базі мешканців та немає заявок."
                )

    except Exception as e:
        logger.error(f"car-search error for user {message.from_user.id}: {e}")
        await msg.edit_text("⚠️ Помилка з'єднання. Спробуйте пізніше.")


@router.callback_query(SelectCarCB.filter())
async def process_car_selection(call: CallbackQuery, callback_data: SelectCarCB, state: FSMContext):
    exact_plate = callback_data.plate

    await call.message.edit_text(f"🔍 Завантажую дані для {exact_plate}...")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.API_URL}/telegram/car-search/{quote(exact_plate)}?exact=true",
                headers=settings.HEADERS,
                json={"telegram_id": call.from_user.id},
                timeout=5.0
            )

            data = resp.json()

            if data.get("found") and not data.get("multiple"):
                user_data = await state.get_data()
                res_text, reply_markup = await render_car_card(data, user_data)
                sent_msg = await call.message.edit_text(res_text, reply_markup=reply_markup)

                if reply_markup:
                    msg_id = sent_msg.message_id if isinstance(sent_msg, Message) else call.message.message_id

                    await state.update_data(last_search_msg_id=msg_id)

                    asyncio.create_task(remove_expired_keyboard(
                        bot=call.bot,
                        chat_id=call.message.chat.id,
                        message_id=msg_id,
                        keyboard_lifetime_seconds=CAR_MESSAGE_KEYBOARD_EXPIRATION_SECONDS
                    ))
            else:
                await call.message.edit_text("⚠️ Авто більше не знайдено.")

    except Exception as e:
        logger.error(f"Error fetching exact car {exact_plate}: {e}")
        await call.message.edit_text("⚠️ Помилка з'єднання з сервером.")


@router.callback_query(ContactOwnerCB.filter())
async def select_message_to_owner(call: CallbackQuery, callback_data: ContactOwnerCB):
    current_time = int(time.time())
    if current_time - callback_data.timestamp > CAR_MESSAGE_KEYBOARD_EXPIRATION_SECONDS:
        await call.message.edit_reply_markup(reply_markup=None)
        await call.answer("⏳ Час дії кнопки вийшов. Зробіть пошук авто наново.", show_alert=True)
        return

    """Вибір варіанту повідомлення власнику"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⚠️ Заважає виїхати",
        callback_data=SendMsgCB(msg_type="block", target_id=callback_data.target_id, plate=callback_data.plate)
    )
    builder.button(
        text="🚶 Підійдіть до авто",
        callback_data=SendMsgCB(msg_type="come", target_id=callback_data.target_id, plate=callback_data.plate)
    )
    builder.button(
        text="👍 Гарне паркування",
        callback_data=SendMsgCB(msg_type="praise", target_id=callback_data.target_id, plate=callback_data.plate)
    )
    builder.button(
        text="❌ Скасувати",
        callback_data=CancelCB(target_id=callback_data.target_id, plate=callback_data.plate)
    )
    builder.adjust(1)

    await call.message.edit_reply_markup(reply_markup=builder.as_markup())
    await call.answer()


@router.callback_query(SendMsgCB.filter())
async def send_message_to_owner(
        call: CallbackQuery,
        callback_data: SendMsgCB,
        bot: Bot,
        redis: Redis
):
    """Відправка повідомлення та перевірка спаму"""
    sender_id = call.from_user.id
    target_id = callback_data.target_id
    plate = callback_data.plate

    spam_key = f"spam_lock:{sender_id}:{plate}"

    is_locked = await redis.get(spam_key)
    if is_locked:
        await call.answer("⏳ Ви вже відправляли повідомлення щодо цього авто. Зачекайте 15 хвилин.", show_alert=True)
        return

    logger.info(f"CAR_MESSAGE: User {sender_id} sent '{callback_data.msg_type}' to {target_id} for car {plate}")

    await redis.setex(spam_key, 900, "locked")

    msg_text = MESSAGES_MAP.get(callback_data.msg_type, "").format(plate=plate)

    reply_markup = None
    if callback_data.msg_type in ["block", "come"]:
        reply_builder = InlineKeyboardBuilder()
        reply_builder.button(
            text="✅ Отримав, вже йду!",
            callback_data=ReplySenderCB(sender_id=sender_id, plate=plate)
        )
        reply_markup = reply_builder.as_markup()

    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"📨 **Повідомлення від сусіда:**\n\n{msg_text}",
            reply_markup=reply_markup
        )
        await call.message.edit_text(
            call.message.text + f"\n\n✅ *Повідомлення успішно надіслано.*",
            reply_markup=None
        )
        await call.answer("Надіслано!", show_alert=False)
    except Exception as e:
        logger.error(f"Failed to send peer message to {target_id}: {e}")
        await call.answer("❌ Не вдалося надіслати (можливо, користувач заблокував бота).", show_alert=True)
        await redis.delete(spam_key)


@router.callback_query(CancelCB.filter())
async def cancel_message_selection(call: CallbackQuery, callback_data: CancelCB):
    """Повертає початкову кнопку 'Надіслати повідомлення'"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💬 Надіслати повідомлення власнику",
        callback_data=ContactOwnerCB(target_id=callback_data.target_id, plate=callback_data.plate, timestamp=int(time.time()))
    )

    reply_markup = builder.as_markup()
    await call.message.edit_reply_markup(reply_markup=reply_markup)
    await call.answer("Скасовано")

    asyncio.create_task(remove_expired_keyboard(
        bot=call.bot,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        keyboard_lifetime_seconds=CAR_MESSAGE_KEYBOARD_EXPIRATION_SECONDS
    ))


@router.callback_query(ReplySenderCB.filter())
async def owner_reply_handler(call: CallbackQuery, callback_data: ReplySenderCB, bot: Bot):
    """Обробка натискання 'Отримав, йду' від власника авто"""
    try:
        await bot.send_message(
            chat_id=callback_data.sender_id,
            text=f"✅ Власник авто `{callback_data.plate}` отримав повідомлення і вже прямує до машини!"
        )
        await call.message.edit_reply_markup(reply_markup=None)
        await call.answer("Відповідь надіслано сусіду!", show_alert=True)

        logger.info(f"CAR_MESSAGE_REPLY: Owner of {callback_data.plate} replied to {callback_data.sender_id}")
    except Exception as e:
        logger.error(f"Failed to send reply to sender {callback_data.sender_id}: {e}")
        await call.answer("❌ Не вдалося надіслати відповідь.", show_alert=True)
