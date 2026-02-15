from sqladmin import ModelView
from starlette.requests import Request
from wtforms import PasswordField, validators

from src.models.user import User, RestrictedUser
from src.security import get_password_hash
from src.services.audit_mixin import AuditMixin


class BaseUserAdmin(AuditMixin, ModelView):
    name = "Користувач"
    name_plural = "Користувачі"
    icon = "fa-solid fa-user"

    can_export = False
    can_view_details = False

    column_searchable_list = [User.phone_number]

    column_list = ["phone_number", "full_name", "apartment", "role", "username", "is_admin", "is_superadmin"]
    form_columns = ["phone_number", "full_name", "apartment", "role", "username", "hashed_password", "is_admin", "is_superadmin"]

    column_labels = {
        "phone_number": "Телефон",
        "full_name": "Ім'я",
        "apartment": "Квартира",
        "role": "Роль",
    }

    form_ajax_refs = {
        "apartment": {
            "fields": ["number"],
            "order_by": "id",
            "limit": 20,
        }
    }

    def list_query(self, request):
        from sqlalchemy.orm import selectinload
        from src.models.appartment import Apartment
        return super().list_query(request).options(
            selectinload(self.model.apartment).selectinload(Apartment.building)
        )

    async def on_model_change(self, data, model, is_created, request):
        password = data.get("hashed_password")

        if password:
            data["hashed_password"] = get_password_hash(password)
        elif not is_created:
            if "hashed_password" in data:
                del data["hashed_password"]


class RestrictedUserAdmin(BaseUserAdmin, model=RestrictedUser):
    name = "Користувач"
    name_plural = "Користувачі"

    column_list = ["phone_number", "full_name", "apartment", "role"]
    form_columns = ["phone_number", "full_name", "apartment", "role"]

    column_formatters = {
        "apartment": lambda m, a: str(m.apartment) if m.apartment else "-"
    }

    def is_accessible(self, request: Request) -> bool:
        return not request.session.get("is_superadmin")

    def is_visible(self, request: Request):
        return not request.session.get("is_superadmin")


class SuperUserAdmin(BaseUserAdmin, model=User):
    name = "Користувач "
    name_plural = "Користувачі "

    column_list = ["phone_number", "full_name", "apartment", "role", "username", "is_admin", "is_superadmin"]
    form_columns = ["phone_number", "full_name", "apartment", "role", "username", "hashed_password", "is_admin", "is_superadmin"]

    column_formatters = {
        "apartment": lambda m, a: str(m.apartment) if m.apartment else "-"
    }

    form_overrides = dict(hashed_password=PasswordField)
    form_args = {
        "hashed_password": {
            "label": "Пароль",
            "description": "Залиште пустим, щоб не змінювати пароль",
            "validators": [validators.Optional()],
            "render_kw": {"required": False},
        },
        "apartment": {
            "label": "Квартира (Пошук)"
        }
    }

    def is_accessible(self, request: Request) -> bool:
        return request.session.get("is_superadmin")

    def is_visible(self, request: Request):
        return request.session.get("is_superadmin")
