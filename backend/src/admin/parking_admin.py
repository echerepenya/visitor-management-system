from sqladmin import ModelView
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from markupsafe import Markup

from src.helpers.date import datetime_formatter
from src.models.apartment import Apartment
from src.models.parking import GuestParkingRequest, ParkingStatus
from src.models.user import User


def parking_status_formatter(value: ParkingStatus) -> Markup:
    colors = {
        ParkingStatus.new: "blue",
        ParkingStatus.keyfob_issued_entry: "orange",
        ParkingStatus.parked: "green",
        ParkingStatus.keyfob_issued_exit: "orange",
        ParkingStatus.completed: "gray",
        ParkingStatus.expired: "black",
    }
    
    names = {
        ParkingStatus.new: "Нова",
        ParkingStatus.keyfob_issued_entry: "Брелок видано (в'їзд)",
        ParkingStatus.parked: "На парковці",
        ParkingStatus.keyfob_issued_exit: "Брелок видано (виїзд)",
        ParkingStatus.completed: "Завершено",
        ParkingStatus.expired: "Прострочено",
    }

    color = colors.get(value, "gray")
    name = names.get(value, value.name if value else "Невідомо")

    return Markup(
        f'<span style="background-color:{color}; color:white; padding:4px 8px; border-radius:4px; font-weight:bold;">'
        f'{name}'
        f'</span>'
    )


class GuestParkingAdmin(ModelView, model=GuestParkingRequest):
    name = "Гостьова парковка"
    name_plural = "Гостьові парковки"
    icon = "fa-solid fa-square-parking"

    can_create = False
    can_edit = False
    can_delete = False
    can_export = False

    page_size = 50
    page_size_options = [50, 100, 200]

    column_list = [
        "created_at",
        GuestParkingRequest.license_plate,
        "user.full_name",
        "user.phone_number",
        GuestParkingRequest.status,
        "updated_at",
    ]

    column_labels = {
        "created_at": "Створено",
        "license_plate": "Номер авто",
        "user.full_name": "Мешканець",
        "user.phone_number": "Телефон",
        "status": "Статус",
        "updated_at": "Оновлено",
    }

    column_searchable_list = [
        GuestParkingRequest.license_plate,
        "user.phone_number",
        "user.full_name",
    ]

    column_default_sort = ("created_at", True)

    column_formatters = {
        GuestParkingRequest.status: lambda m, a: parking_status_formatter(m.status),
        "created_at": lambda m, a: datetime_formatter(m.created_at),
        "updated_at": lambda m, a: datetime_formatter(m.updated_at),
    }

    def list_query(self, request):
        query = super().list_query(request)
        return query.options(
            selectinload(GuestParkingRequest.user)
            .selectinload(User.apartment)
            .selectinload(Apartment.building)
        )

    def is_accessible(self, request: Request) -> bool:
        return request.session.get('user', {}).get("is_admin")
