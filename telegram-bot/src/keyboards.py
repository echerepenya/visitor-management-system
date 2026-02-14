from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


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
