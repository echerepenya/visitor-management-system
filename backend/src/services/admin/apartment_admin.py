from sqladmin import ModelView
from starlette.requests import Request

from src.models.appartment import Apartment
from src.models.user import UserRole
from src.services.audit_mixin import AuditMixin


class ApartmentAdmin(AuditMixin, ModelView, model=Apartment):
    icon = "fa-solid fa-door-closed"
    column_list = [Apartment.number, Apartment.building, "residents"]
    form_columns = [Apartment.building, Apartment.number]

    def is_accessible(self, request: Request) -> bool:
        return request.session.get("role") in [UserRole.SUPERUSER, UserRole.ADMIN]
