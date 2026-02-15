from sqladmin import ModelView
from starlette.requests import Request
from sqlalchemy.orm import selectinload

from src.models.appartment import Apartment
from src.services.audit_mixin import AuditMixin


class ApartmentAdmin(AuditMixin, ModelView, model=Apartment):
    name = "Квартира"
    name_plural = "Квартири"
    icon = "fa-solid fa-door-closed"
    can_export = False

    column_list = [Apartment.number, "building.address", "residents_count"]

    column_labels = {
        Apartment.number: "Номер",
        "building.address": "Будинок",
        "residents_count": "Мешканців"
    }

    column_formatters = {
        "residents_count": lambda m, a: f"{len(m.residents)} 👤"
    }

    def list_query(self, request):
        return super().list_query(request).options(
            selectinload(Apartment.building),
            selectinload(Apartment.residents)
        )

    form_columns = [Apartment.building, Apartment.number]

    def is_accessible(self, request: Request) -> bool:
        return request.session.get("is_superadmin")
