from passlib.context import CryptContext
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models.user import User, UserRole
import os
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    if not isinstance(password, str):
        logger.warning(f"Warning: Password is not a string! Type: {type(password)}")
        password = str(password)

    if len(password.encode('utf-8')) > 72:
        logger.warning("Password is too long for bcrypt (>72 bytes). Truncating.")

    return pwd_context.hash(password[:72])


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username_input = form.get("username")
        password_input = form.get("password")

        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.username == username_input)
            result = await session.execute(stmt)
            user = result.scalars().first()

        if (not user) or (not verify_password(password_input, user.hashed_password)):
            return False

        if user.role == UserRole.RESIDENT:
            return False

        request.session.update({
            "token": user.username,
            "role": user.role.value,
            "user_id": user.id
        })
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


authentication_backend = AdminAuth(secret_key=SECRET_KEY)
