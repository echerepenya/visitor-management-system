from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx
from redis.asyncio import Redis
from aiogram import Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import API_URL, HEADERS, logger, TIMEZONE
from src.keyboards import ContactOwnerCB, ReplySenderCB, SendMsgCB, MESSAGES_MAP, CancelCB
from src.translations import REQUEST_TYPE_TRANSLATION

router = Router()


@router.message(StateFilter(None))
async def handle_text_lookup(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ''

    if not text or text in ["🎫 Замовити перепустку", "👮 Контакти охорони", "ℹ️ Мій статус"]:
        return

    if len(text) > 15:
        await message.answer("Це не схоже на номер авто. Спробуйте ще раз.")
        return

    msg = await message.answer("🔍 Шукаю авто...")

    try:
        async with httpx.AsyncClient() as client:
            # run "smart" search in cars table and in GuestRequests
            resp = await client.post(f"{API_URL}/telegram/car-search/{quote(text)}", headers=HEADERS, json={"telegram_id": message.from_user.id}, timeout=5.0)

            if resp.status_code == 422:
                await message.answer("Це не схоже на номер авто. Спробуйте ще раз.")
                return

            if resp.status_code != 200:
                await msg.edit_text("⚠️ Помилка сервера при пошуку.")
                return

            data = resp.json()

            if data.get("found"):
                user_data = await state.get_data()
                is_detailed_info_allowed = user_data.get("role", "resident") == "guard" or user_data.get("is_admin", False)

                info = data["info"]

                building = info.get('building')
                apartment = f", {info.get('apartment')}" if info.get('apartment') else None

                if building:
                    address = f"{building}{apartment if apartment else ''}" if is_detailed_info_allowed else building
                else:
                    address = "Немає адреси"

                phone = f"📞 `{info.get('phone')}`" if is_detailed_info_allowed else ''
                owner = f"Власник: `{info.get('owner')}`" if is_detailed_info_allowed else ''

                # -- ВАРІАНТ 1: ЗНАЙДЕНО (Мешканець) --
                if data["type"] != "guest":
                    res_text = (
                        f"🚙 **АВТО МЕШКАНЦЯ**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"🏠 **{address}**\n"
                        f"{owner}\n"
                        f"{phone}"
                    )

                    target_tg_id = info.get("owner_telegram_id")
                    reply_markup = None

                    if target_tg_id and target_tg_id != message.from_user.id and user_data.get("role") != 'guard':
                        builder = InlineKeyboardBuilder()
                        builder.button(
                            text="💬 Надіслати повідомлення власнику",
                            callback_data=ContactOwnerCB(target_id=target_tg_id, plate=data['plate'])
                        )
                        reply_markup = builder.as_markup()

                    await msg.edit_text(res_text, reply_markup=reply_markup)

                # -- ВАРІАНТ 2: ЗНАЙДЕНО (Гість) --
                else:
                    invited_at_raw = info.get('invited_at')
                    if invited_at_raw:
                        dt = datetime.fromisoformat(invited_at_raw)
                        local_dt = dt.astimezone(ZoneInfo(TIMEZONE))

                        invited_at = local_dt.strftime("%d.%m.%Y %H:%M")
                    else:
                        invited_at = "невідомо"

                    guest_text = (
                        f"🚕 **ГІСТЬ (ЗАЯВКА)**\n\n"
                        f"Номер: `{data['plate']}`\n"
                        f"Тип заявки: {REQUEST_TYPE_TRANSLATION.get(info.get('request_type'), 'Невідомий')} від {invited_at}\n"
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
        logger.error(f"car-search error for user {message.from_user.id}: {e}")
        await msg.edit_text("⚠️ Помилка з'єднання. Спробуйте пізніше.")


@router.callback_query(ContactOwnerCB.filter())
async def select_message_to_owner(call: CallbackQuery, callback_data: ContactOwnerCB):
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
        callback_data=ContactOwnerCB(target_id=callback_data.target_id, plate=callback_data.plate)
    )
    await call.message.edit_reply_markup(reply_markup=builder.as_markup())
    await call.answer("Скасовано")


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
