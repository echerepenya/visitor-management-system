import logging
from typing import Any, Callable, Awaitable

from src.api import api_client
from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.config import settings

logger = logging.getLogger(__name__)


class StateRecoveryMiddleware(BaseMiddleware):
    """
    Restores FSM state for users who lost it (e.g. due to state wipe bug).
    Calls /telegram/get-me on each incoming update when 'role' key is absent.
    Skips /start and contact-share events (those are the normal auth flow).
    """

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.text and event.text.startswith("/start"):
                return await handler(event, data)
            if event.contact:
                return await handler(event, data)
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            return await handler(event, data)

        if not user:
            return await handler(event, data)

        state: FSMContext | None = data.get("state")
        if state is None:
            return await handler(event, data)

        state_data = await state.get_data()
        if state_data.get("role"):
            return await handler(event, data)

        try:
            response = await api_client.post(
                "/telegram/get-me",
                json={"telegram_id": user.id},
            )

            if response.status_code == 200:
                payload = response.json()
                await state.update_data(
                    role=payload.get("role"),
                    name=payload.get("full_name"),
                    is_admin=payload.get("is_admin", False),
                    telegram_id=user.id,
                )
                logger.info("State recovered for user %s (role=%s)", user.id, payload.get("role"))

        except Exception as exc:
            logger.warning("State recovery failed for user %s: %s", user.id, exc)

        return await handler(event, data)
