from sqladmin import ModelView
from starlette.requests import Request

from src.models.audit_log import AuditLog
from src.models.user import UserRole


class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [AuditLog.created_at, AuditLog.admin_username, AuditLog.action, AuditLog.target_model,
                   AuditLog.details]
    icon = "fa-solid fa-list-check"

    can_create = False
    can_edit = False
    can_delete = False

    column_default_sort = ("created_at", True)

    def is_accessible(self, request: Request) -> bool:
        return request.session.get("role") == UserRole.SUPERUSER
