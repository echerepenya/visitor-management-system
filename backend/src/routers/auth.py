import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm

from src.database import get_db
from src.models.user import User, UserRole
from src.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    username_input = form_data.username
    password_input = form_data.password

    stmt = select(User).where(User.username == username_input)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if (not user) or (not verify_password(password_input, user.hashed_password)):
        logging.info("Guard user is not found or password is incorrect")
        return False

    if not user.role == UserRole.GUARD:
        logging.warning("User is found but its role is not Guard")
        return False

    return {
        "access_token": create_access_token(data={"sub": form_data.username}),
        "role:": user.role.value,
        "token_type": "bearer"
    }
