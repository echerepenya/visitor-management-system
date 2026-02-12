from src.database import AsyncSessionLocal
from src.models.audit_log import AuditLog


class AuditMixin:
    """
    Automatic logging of model changes.
    """

    async def after_model_change(self, data, model, is_created, request):
        action = "CREATE" if is_created else "UPDATE"
        user = request.session.get("token", "Unknown")
        details = f"{action} {model}"

        async with AsyncSessionLocal() as session:
            log = AuditLog(
                admin_username=user,
                action=action,
                target_model=self.model.__tablename__,
                details=str(data)
            )
            session.add(log)
            await session.commit()

    async def after_model_delete(self, model, request):
        user = request.session.get("token", "Unknown")

        async with AsyncSessionLocal() as session:
            log = AuditLog(
                admin_username=user,
                action="DELETE",
                target_model=self.model.__tablename__,
                details=f"Deleted ID: {model.id}"
            )
            session.add(log)
            await session.commit()
