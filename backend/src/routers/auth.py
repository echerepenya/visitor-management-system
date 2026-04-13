import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm

from src.config import settings
from src.database import get_db
from src.models.user import User, UserRole
from src.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def verify_telegram_webapp_data(init_data: str) -> dict | None:
    """Перевірка цифрового підпису Telegram WebApp"""
    vals = dict(parse_qsl(init_data))
    if 'hash' not in vals:
        return None

    auth_hash = vals.pop('hash')
    # Сортуємо за алфавітом і склеюємо в рядок key=value
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(vals.items())])

    # Крок 1: секретний ключ на основі токена
    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()

    # Крок 2: підпис даних цим ключем
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != auth_hash:
        return None

    return vals


@router.post("/telegram-webapp")
async def telegram_webapp_login(payload: dict, db: AsyncSession = Depends(get_db)):
    init_data = payload.get("init_data")
    if not init_data or not isinstance(init_data, str):
        raise HTTPException(status_code=400, detail="Missing init_data")

    tg_data = verify_telegram_webapp_data(init_data)
    if not tg_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram signature")

    try:
        tg_user = json.loads(tg_data['user'])
        tg_id = tg_user['id']
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid user data in init_data")

    stmt = select(User).where(User.telegram_id == tg_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="Користувача не знайдено. Будь ласка, зареєструйтесь у боті.")

    token = create_access_token(data={"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "full_name": user.full_name
        }
    }


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    username_input = form_data.username
    password_input = form_data.password

    stmt = select(User).where(User.username == username_input)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(password_input, user.hashed_password) or user.is_deleted:
        logging.info(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": form_data.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.value,
            "full_name": user.full_name
        }
    }
