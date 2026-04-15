import datetime
import json
import logging

from sqladmin import ModelView
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import PasswordField, validators
from sqlalchemy import select, or_

from src.models.user import User, RestrictedUser
from src.security import get_password_hash
from src.services.audit_mixin import AuditMixin
from src.database import get_redis, AsyncSessionLocal
from src.utils import normalize_phone


class BaseUserAdmin(AuditMixin, ModelView):
    name = "Користувач"
    name_plural = "Користувачі"
    icon = "fa-solid fa-user"

    can_export = False
    can_view_details = False

    page_size = 25
    page_size_options = [25, 50, 100, 200]

    column_searchable_list = [User.phone_number]

    column_list = ["phone_number", "full_name", "apartment", "role", "username", "is_admin", "is_superadmin", "is_resident_contact"]
    form_columns = ["phone_number", "full_name", "apartment", "role", "username", "hashed_password", "is_admin", "is_superadmin", "is_resident_contact"]

    column_labels = {
        "phone_number": "Телефон",
        "full_name": "Ім'я",
        "apartment": "Квартира",
        "role": "Роль",
        "is_admin": "Адміністратор",
        "address_info": "Адреса"
    }

    form_args = {
        "apartment": {
            "label": "Квартира (Пошук)",
            "validators": [validators.Optional()],
            "render_kw": {
                "data-allow-clear": "true",
                "data-placeholder": "Оберіть квартиру...",
                "style": "width: 100%"
            }
        }
    }

    form_ajax_refs = {
        "apartment": {
            "fields": ["number"],
            "order_by": "id",
            "limit": 200,
        }
    }

    def list_query(self, request):
        from sqlalchemy.orm import selectinload
        from src.models.apartment import Apartment
        return super().list_query(request).options(
            selectinload(self.model.apartment).selectinload(Apartment.building)
        )

    async def on_model_change(self, data, model, is_created, request):
        current_admin_id = request.session.get('user', {}).get('id')
        if is_created:
            data['created_by'] = current_admin_id
        else:
            data['updated_by'] = current_admin_id

        # 1. Handle password hashing
        password = data.get("hashed_password")
        if password:
            data["hashed_password"] = get_password_hash(password)
        elif not is_created:
            if "hashed_password" in data:
                del data["hashed_password"]

        # 2. Uniqueness check (Phone and Username)
        phone = data.get("phone_number")
        username = data.get("username")
        
        conditions = []
        if phone:
            normalized_phone = normalize_phone(phone)
            data["phone_number"] = normalized_phone
            conditions.append(User.phone_number == normalized_phone)
        if username:
            conditions.append(User.username == username)
        
        if conditions:
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(or_(*conditions))
                if not is_created:
                    stmt = stmt.where(User.id != model.id)
                
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    raise ValueError("Користувач з таким телефоном або логіном вже існує")

    async def delete_model(self, request: Request, pk: str):
        db_session = request.state.session
        user = await db_session.get(self.model, int(pk))

        if not user:
            return None

        current_user_session = request.session.get('user', {})
        is_current_user_superadmin = current_user_session.get("is_superadmin", False)

        if not is_current_user_superadmin and user.is_admin:
            request.session.setdefault("flash_messages", []).append(
                {"message": "У вас недостатньо прав для видалення адміністратора", "category": "error"}
            )
            return RedirectResponse(
                request.headers.get("referer", "/admin"),
                status_code=302
            )

        if user.is_deleted:
            request.session.setdefault("flash_messages", []).append(
                {"message": "Цей користувач вже відмічений як видалений", "category": "error"}
            )
            return RedirectResponse(
                request.headers.get("referer", "/admin"),
                status_code=302
            )

        if user.is_superadmin:
            request.session.setdefault("flash_messages", []).append(
                {"message": "Неможливо видалити суперадміністратора", "category": "error"}
            )
            return RedirectResponse(
                request.headers.get("referer", "/admin"),
                status_code=302
            )

        if user.is_admin:
            user.is_deleted = True
            user.deleted_at = datetime.datetime.now(tz=datetime.timezone.utc)
            user.deleted_by = current_user_session.get('id')

            db_session.add(user)
            await db_session.commit()

            request.session.setdefault("flash_messages", []).append(
                {"message": f"Адміністратор {user.username} деактивований", "category": "info"}
            )
            return RedirectResponse(request.headers.get("referer", "/admin"), status_code=302)

        return await super().delete_model(request, pk)

    async def after_model_delete(self, model, request):
        await super().after_model_delete(model, request)

        if model.telegram_id:
            try:
                redis = await get_redis()
                event_data = {
                    'event': 'user_deleted',
                    'telegram_id': model.telegram_id
                }
                await redis.xadd("vms_stream", {"payload": json.dumps(event_data)})
            except Exception as e:
                logging.error(f"Error sending user_deleted event to Redis: {e}")


class RestrictedUserAdmin(BaseUserAdmin, model=RestrictedUser):
    identity = "restricted-user"

    name = "Користувач"
    name_plural = "Користувачі"

    column_list = ["phone_number", "full_name", "address_info", "role", "is_admin"]
    form_columns = ["phone_number", "full_name", "apartment"]

    column_formatters = {
        "address_info": lambda m, a: str(m.apartment) if m.apartment else "-"
    }

    def list_query(self, request: Request):
        return super().list_query(request).where(self.model.is_deleted == False)

    def count_query(self, request: Request):
        return super().count_query(request).where(self.model.is_deleted == False)

    def is_accessible(self, request: Request) -> bool:
        return not request.session.get('user', {}).get("is_superadmin")

    def is_visible(self, request: Request):
        return not request.session.get('user', {}).get("is_superadmin")


class SuperUserAdmin(BaseUserAdmin, model=User):
    identity = "super-user"

    name = "Користувач "
    name_plural = "Користувачі "

    can_export = True

    column_list = ["phone_number", "full_name", "apartment", "role", "username", "is_admin", "is_superadmin", "is_resident_contact", "is_deleted"]
    form_columns = ["phone_number", "full_name", "apartment", "role", "username", "hashed_password", "is_admin", "is_superadmin", "is_resident_contact", "is_deleted"]

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
            "label": "Квартира (Пошук)",
            "validators": [validators.Optional()],
            "render_kw": {
                "data-allow-clear": "true",
                "data-placeholder": "Оберіть квартиру...",
                "style": "width: 100%"
            }
        }
    }

    def is_accessible(self, request: Request) -> bool:
        return request.session.get('user', {}).get("is_superadmin")

    def is_visible(self, request: Request):
        return request.session.get('user', {}).get("is_superadmin")
