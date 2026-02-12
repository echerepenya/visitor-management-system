from sqladmin import ModelView
from starlette.requests import Request

from src.models.car import Car
from src.services.audit_mixin import AuditMixin


class CarAdmin(AuditMixin, ModelView, model=Car):
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

    def is_accessible(self, request: Request) -> bool:
        return "token" in request.session
