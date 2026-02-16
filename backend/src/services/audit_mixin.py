from src.database import AsyncSessionLocal
from src.models.audit_log import AuditLog
from src.security import get_current_user

from sqlalchemy.orm.exc import DetachedInstanceError
from src.database import AsyncSessionLocal
from src.security import get_current_user


class AuditMixin:
    """
    Automatic logging of model changes.
    """

    async def after_model_change(self, data, model, is_created, request):
        action = "CREATE" if is_created else "UPDATE"
        token = request.session.get("token")

        try:
            details = str(data)
        except DetachedInstanceError:
            obj_id = getattr(data, 'id', 'Unknown')
            details = f"{model.__tablename__} ID: {obj_id} (Detached)"
        except Exception as e:
            details = f"Error serializing data: {str(e)}"

        async with AsyncSessionLocal() as session:
            admin_user = "Unknown"
            if token:
                try:
                    current_u = await get_current_user(token, session)
                    admin_user = current_u.username
                except Exception:
                    pass

            log = AuditLog(
                admin_username=admin_user,
                action=action,
                target_model=self.model.__tablename__,
                details=details
            )
            session.add(log)
            await session.commit()

    async def after_model_delete(self, model, request):
        token = request.session.get("token")

        try:
            obj_id = model.id
        except DetachedInstanceError:
            obj_id = "Unknown (Detached)"

        async with AsyncSessionLocal() as session:
            admin_user = "Unknown"
            if token:
                try:
                    current_u = await get_current_user(token, session)
                    admin_user = current_u.username
                except Exception:
                    pass

            log = AuditLog(
                admin_username=admin_user,
                action="DELETE",
                target_model=self.model.__tablename__,
                details=f"Deleted ID: {obj_id}"
            )
            session.add(log)
            await session.commit()
