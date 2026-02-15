from sqladmin import ModelView
from starlette.requests import Request
from sqlalchemy import select, or_

from src.models.car import Car
from src.models.user import User, UserRole
from src.services.audit_mixin import AuditMixin


class CarAdmin(AuditMixin, ModelView, model=Car):
    name = "Авто"
    name_plural = "Авто"

    icon = "fa-solid fa-car"
    column_list = [
        Car.plate_number,
        Car.model,
        "owner.full_name",
        "owner.phone_number",
        "owner.apartment.building.address",
        "owner.apartment.number"
    ]
    form_columns = [Car.plate_number, Car.model, Car.owner, Car.notes]

    can_export = False

    form_ajax_refs = {
        "owner": {
            "fields": ["phone_number"],
            "placeholder": "Пошук мешканця...",
            "filter": User.role == UserRole.RESIDENT,
        }
    }

    def is_accessible(self, request: Request) -> bool:
        return "token" in request.session
