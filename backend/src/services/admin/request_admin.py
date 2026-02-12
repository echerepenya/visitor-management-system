import httpx
from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from markupsafe import Markup

from src.models.appartment import Apartment
from src.models.request import GuestRequest, RequestStatus
from src.models.user import UserRole, User
from src.services.audit_mixin import AuditMixin


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

    can_create = False
    can_delete = False
    can_export = False

    column_list = [
        GuestRequest.id,
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
    }

    async def on_model_change(self, data, model, is_created, request):
        # 1. Виконуємо стандартне збереження
        await super().on_model_change(data, model, is_created, request)

        # 2. Перевіряємо, чи це зміна статусу на COMPLETED
        # is_created == False (бо це редагування існуючої заявки)
        if not is_created and model.status == RequestStatus.COMPLETED:

            # 3. Отримуємо Telegram ID мешканця
            # Нам треба "підвантажити" юзера, бо в model може бути тільки ID
            # Але часто ORM вже тримає зв'язок. Перевіримо:
            user = model.user
            if user and user.telegram_id:

                # 4. Відправляємо повідомлення в Telegram
                # Ми робимо це напряму через API Telegram, щоб не залежати від контейнера бота
                message_text = (
                    f"✅ **Ваш гість прибув!**\n\n"
                    f"Охорона підтвердила в'їзд/вхід:\n"
                    f"🚗 {model.value}\n"
                    f"🕒 {model.visit_date.strftime('%H:%M')}"
                )

                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    async with httpx.AsyncClient() as client:
                        await client.post(url, json={
                            "chat_id": user.telegram_id,
                            "text": message_text,
                            "parse_mode": "Markdown"
                        })
                except Exception as e:
                    print(f"Failed to send notification: {e}")

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
