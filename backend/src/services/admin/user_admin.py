from sqladmin import ModelView
from starlette.requests import Request
from wtforms import PasswordField, validators

from src.models.user import User, UserRole
from src.security import get_password_hash
from src.services.audit_mixin import AuditMixin


class UserAdmin(AuditMixin, ModelView, model=User):
    icon = "fa-solid fa-user"
    column_list = [User.phone_number, User.role, User.full_name, User.apartment]
    form_columns = [User.phone_number, User.full_name, User.role, User.apartment, User.username, User.hashed_password, User.is_active]

    form_overrides = dict(hashed_password=PasswordField)
    form_args = {
        "hashed_password": {
            "label": "Пароль",
            "description": "Залиште пустим, щоб не змінювати пароль",
            "validators": [validators.Optional()],
            "render_kw": {"required": False},
        }
    }

    def is_accessible(self, request: Request) -> bool:
        return request.session.get("role") in [UserRole.SUPERUSER, UserRole.ADMIN]

    async def on_model_change(self, data, model, is_created, request):
        password = data.get("hashed_password")

        if password:
            data["hashed_password"] = get_password_hash(password)
        elif not is_created:
            if "hashed_password" in data:
                del data["hashed_password"]
