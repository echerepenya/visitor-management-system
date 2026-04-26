from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from markupsafe import Markup

from src.helpers.date import datetime_formatter
from src.models.apartment import Apartment
from src.models.request import GuestRequest, RequestStatus
from src.models.user import User
from src.services.audit_mixin import AuditMixin
from src.translations import REQUEST_TYPE_TRANSLATION


def status_formatter(value):
    colors = {
        RequestStatus.NEW: "green",
        RequestStatus.COMPLETED: "gray",
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


def request_type_formatter(value: str) -> str:
    return REQUEST_TYPE_TRANSLATION.get(value, value)


class RequestAdmin(AuditMixin, ModelView, model=GuestRequest):
    name = "Заявка на пропуск"
    name_plural = "Заявки на пропуск"
    icon = "fa-solid fa-list-check"

    can_create = False
    can_edit = False
    can_delete = False
    can_export = False

    page_size = 50
    page_size_options = [50, 100, 200]

    column_list = [
        "request_created_at",
        "request_type",
        GuestRequest.value,
        "address_info",
        "user.phone_number",
        GuestRequest.status,
        "request_updated_at",
        "completed_by_user.full_name"
    ]

    column_labels = {
        "request_created_at": "Створено",
        "request_type": "Тип",
        "value": "Номер / Ім'я",
        "address_info": "Адреса",
        "user.phone_number": "Телефон",
        "status": "Статус",
        "request_updated_at": "Оновлено",
        "completed_by_user.full_name": "Пропустив"
    }

    column_searchable_list = [
        GuestRequest.value,
        "user.phone_number"
    ]

    column_default_sort = ("created_at", True)

    form_columns = [GuestRequest.status, GuestRequest.comment]

    column_formatters = {
        GuestRequest.status: lambda m, a: status_formatter(m.status),
        "address_info": address_formatter,
        "request_created_at": lambda m, a: datetime_formatter(m.created_at),
        "request_updated_at": lambda m, a: datetime_formatter(m.updated_at),
        "request_type": lambda m, a: request_type_formatter(m.type.value)
    }

    def list_query(self, request):
        query = super().list_query(request)

        return query.options(
            selectinload(GuestRequest.user)
            .selectinload(User.apartment)
            .selectinload(Apartment.building)
        )

    def is_accessible(self, request: Request) -> bool:
        return request.session.get('user', {}).get("is_admin")
