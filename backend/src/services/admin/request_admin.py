import os

import httpx
from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from markupsafe import Markup

from src.database import AsyncSessionLocal
from src.models.apartment import Apartment
from src.models.request import GuestRequest, RequestStatus
from src.models.user import UserRole, User
from src.services.audit_mixin import AuditMixin


def approve_button_formatter(model, _):
    if model.status == RequestStatus.NEW:
        return Markup(
            f'''
            <button class="btn btn-success btn-sm" onclick="completeRequest({model.id})">
                <i class="fa-solid fa-check"></i> Пропустити
            </button>
            '''
        )
    return ""


def status_formatter(value):
    colors = {
        RequestStatus.NEW: "green",
        RequestStatus.COMPLETED: "gray",
        RequestStatus.REJECTED: "red",
        RequestStatus.EXPIRED: "black",
    }
    color = colors.get(value, "gray")

    return Markup(
        f'<span style="background-color:{color}; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;">'
        f'{value.upper()}'
        f'</span>'
    )


def address_formatter(m, _):
    if not m.user or not m.user.apartment or not m.user.apartment.building:
        return "-"

    return f"{m.user.apartment.building.address}, кв. {m.user.apartment.number}"


class RequestAdmin(AuditMixin, ModelView, model=GuestRequest):
    name = "Пропуск"
    name_plural = "Пропуски (Заявки)"
    icon = "fa-solid fa-list-check"

    list_template = "refresh.html"

    can_create = False
    can_delete = False
    can_export = False

    column_list = [
        GuestRequest.id,
        "actions",
        GuestRequest.status,
        GuestRequest.visit_date,
        GuestRequest.type,
        GuestRequest.value,
        "user.phone_number",
        "address_info"
    ]

    column_searchable_list = [
        GuestRequest.value,
        GuestRequest.comment
    ]

    column_default_sort = ("created_at", True)

    form_columns = [GuestRequest.status, GuestRequest.comment]

    column_formatters = {
        GuestRequest.status: lambda m, a: status_formatter(m.status),
        "address_info": address_formatter,
        "actions": approve_button_formatter,
    }

    async def on_model_change(self, data, model, is_created, request):
        new_status = data.get("status")
        status_str = str(new_status)

        await super().on_model_change(data, model, is_created, request)

        is_completed = status_str in ["COMPLETED", "completed", "RequestStatus.COMPLETED"]

        if not is_created and is_completed:
            try:
                async with AsyncSessionLocal() as session:
                    stmt = select(User).where(User.id == model.user_id)
                    result = await session.execute(stmt)
                    user = result.scalars().first()

                if user and user.telegram_id:
                    bot_token = os.getenv("BOT_TOKEN")
                    msg_text = (
                        f"✅ **Ваш гість заїхав!**\n\n"
                        f"🚗 Авто: {model.value}\n"
                        f"🕒 {model.visit_date.strftime('%H:%M')}"
                    )

                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"https://api.telegram.org/bot{bot_token}/sendMessage",
                            json={
                                "chat_id": user.telegram_id,
                                "text": msg_text,
                                "parse_mode": "Markdown"
                            }
                        )
                else:
                    print(f"DEBUG: User not found (id={model.user_id}) or no telegram_id.")

            except Exception as e:
                print(f"ERROR: {e}")
                import traceback
                traceback.print_exc()

    def list_query(self, request):
        query = super().list_query(request)

        return query.options(
            selectinload(GuestRequest.user)
            .selectinload(User.apartment)
            .selectinload(Apartment.building)
        )

    def is_accessible(self, request: Request) -> bool:
        role = request.session.get("role")
        return role in [UserRole.ADMIN, UserRole.SUPERUSER, UserRole.GUARD]
