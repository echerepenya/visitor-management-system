from sqladmin import ModelView
from starlette.requests import Request

from src.models.building import Building
from src.services.audit_mixin import AuditMixin


class BuildingAdmin(AuditMixin, ModelView, model=Building):
    name = "Будинок"
    name_plural = "Будинки"

    page_size = 25
    page_size_options = [25, 50, 100, 200]

    icon = "fa-solid fa-building"
    column_list = [Building.id, Building.address]
    column_labels = {
        "address": "Будинок"
    }

    form_columns = [Building.address]

    can_export = False

    def is_accessible(self, request: Request) -> bool:
        return request.session.get('user', {}).get("is_superadmin")
