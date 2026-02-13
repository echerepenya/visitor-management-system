from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from sqladmin.authentication import AuthenticationBackend
from fastapi import Request, Security, HTTPException
from sqlalchemy import select
from starlette import status

from src.database import AsyncSessionLocal
from src.models.user import User, UserRole
import os
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

SERVER_API_KEY = os.getenv("API_KEY")


async def get_api_key(api_key_in_header: str = Security(api_key_header)):
    """
    Checks if the provided api key in header is equal to SERVER_API_KEY
    """
    if api_key_in_header == SERVER_API_KEY:
        return api_key_in_header

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    if not isinstance(password, str):
        password = str(password)

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
