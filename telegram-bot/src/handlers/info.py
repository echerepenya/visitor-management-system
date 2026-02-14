import os

from aiogram import Router, F
from aiogram.types import (
    Message,
)

router = Router()

GUARD_CONTACT_PHONE=os.getenv("GUARD_CONTACT_PHONE", 112)


@router.message(F.text == "👮 Контакти охорони")
async def cmd_contacts(message: Message):
    await message.answer(
        "👮 **Пост охорони (цілодобово):**\n"
        f"📞 {GUARD_CONTACT_PHONE}\n"
    )


@router.message(F.text == "ℹ️ Мій статус")
async def cmd_me(message: Message):
    await message.answer("Ваш статус: ✅ Активний мешканець")  # TODO fetch real status from DB
