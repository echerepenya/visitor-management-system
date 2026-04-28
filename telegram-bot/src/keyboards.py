from aiogram.filters.callback_data import CallbackData


from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton,
)

from src.config import settings

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

# 3. Visitor type selection
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

# 5. Guard menu
login_url = f"{settings.GUARD_DASHBOARD_URL}/login/"

kb_guard_dashboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Відкрити журнал заявок",
                web_app=WebAppInfo(url=login_url)
            )
        ]
    ],
    resize_keyboard=True
)


# CAR_MESSAGE keyboards
class ContactOwnerCB(CallbackData, prefix="contact_owner"):
    target_id: int
    plate: str


class SendMsgCB(CallbackData, prefix="send_msg"):
    msg_type: str
    target_id: int
    plate: str


class CancelCB(CallbackData, prefix="cancel_msg"):
    target_id: int
    plate: str


class ReplySenderCB(CallbackData, prefix="reply_sender"):
    sender_id: int
    plate: str


MESSAGES_MAP = {
    "block": "⚠️ **Увага!** Ваше авто ({plate}) заважає виїхати. Будь ласка, підійдіть до машини.",
    "come": "🚶 Будь ласка, підійдіть до вашого авто ({plate}).",
    "praise": "👍 Сусід передає, що ваше авто ({plate}) дуже круто запарковане! Дякуємо за повагу до інших."
}
