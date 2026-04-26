from sqladmin import ModelView
from starlette.requests import Request

from src.helpers.date import datetime_formatter
from src.models.audit_log import AuditLog


class AuditLogAdmin(ModelView, model=AuditLog):
    name = "Лог"
    name_plural = "Логи"

    column_list = [AuditLog.created_at, AuditLog.admin_username, AuditLog.action, AuditLog.target_model,
                   AuditLog.details]
    icon = "fa-solid fa-list-check"

    can_create = False
    can_edit = False
    can_delete = False
    can_export = False

    page_size = 50
    page_size_options = [50, 100, 200]

    column_default_sort = ("created_at", True)

    column_formatters = {
        "created_at": lambda m, a: datetime_formatter(m.created_at)
    }

    def is_accessible(self, request: Request) -> bool:
        return request.session.get('user', {}).get("is_superadmin")
