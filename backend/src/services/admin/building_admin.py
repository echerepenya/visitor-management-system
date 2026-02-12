from sqladmin import ModelView
from starlette.requests import Request

from src.models.building import Building
from src.models.user import UserRole
from src.services.audit_mixin import AuditMixin


class BuildingAdmin(AuditMixin, ModelView, model=Building):
    icon = "fa-solid fa-building"
    column_list = [Building.id, Building.address, "apartments"]
    form_columns = [Building.address]

    def is_accessible(self, request: Request) -> bool:
        return request.session.get("role") == UserRole.SUPERUSER
