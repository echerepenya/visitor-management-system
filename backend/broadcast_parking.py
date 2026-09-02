import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, or_
from src.config import settings
from src.models.user import User, UserRole
import httpx

MESSAGE_TEXT = """Шановні мешканці! 📢

Повідомляємо, що в нашому боті запрацювала функція постановки авто на гостьову парковку. Система запроваджується для можливості ідентифікації мешканця, який хоче поставити машину на стоянку, а також для контролю видачі брелоків і наявності вільних місць.

Коротка інструкція:
1️⃣ В головному меню бота натисніть «Більше» ➡️ «Гостьова парковка».
2️⃣ Бот покаже кількість вільних місць.
3️⃣ Введіть номер автомобіля.
4️⃣ Протягом 30 хвилин підійдіть до вказаного поста охорони та візьміть брелок.
5️⃣ Поставте машину на парковку та поверніть брелок охороні.
6️⃣ Для виїзду — знову зверніться до поста охорони.
"""


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    print("Fetching residents from the database...")
    async with engine.connect() as conn:
        stmt = select(User.telegram_id).where(
            or_(User.role == UserRole.RESIDENT, User.is_resident_contact.is_(True)),
            User.telegram_id.isnot(None),
            User.is_deleted.is_(False)
        )
        result = await conn.execute(stmt)
        telegram_ids = [row[0] for row in result.all()]

    print(f"Found {len(telegram_ids)} residents.")
    
    if not telegram_ids:
        print("No users to broadcast to.")
        return

    bot_token = settings.BOT_TOKEN
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    print("Starting broadcast...")
    success_count = 0
    fail_count = 0
    
    async with httpx.AsyncClient() as client:
        for tg_id in telegram_ids:
            payload = {
                "chat_id": tg_id,
                "text": MESSAGE_TEXT,
                "parse_mode": "HTML"
            }
            # Note: We do NOT send reply_markup so we don't break the existing keyboard
            try:
                response = await client.post(api_url, json=payload)
                if response.status_code == 200:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f"Failed to send to {tg_id}: {response.text}")
            except Exception as e:
                fail_count += 1
                print(f"Error sending to {tg_id}: {e}")
            
            # Simple rate limit protection (Telegram allows ~30 msgs/sec for broadcasting)
            await asyncio.sleep(0.05)

    print(f"Broadcast completed. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    asyncio.run(main())
