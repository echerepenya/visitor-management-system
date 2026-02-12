from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy import select

from src.config import settings
from src.database import engine, AsyncSessionLocal
from src.routers import cars, auth, requests
from src.models.user import User, UserRole
from src.security import authentication_backend, get_password_hash
from src.services.admin.apartment_admin import ApartmentAdmin
from src.services.admin.audit_log_admin import AuditLogAdmin
from src.services.admin.building_admin import BuildingAdmin
from src.services.admin.car_admin import CarAdmin
from src.services.admin.request_admin import RequestAdmin
from src.services.admin.user_admin import UserAdmin

app = FastAPI(title="Visitor Management System")

app.include_router(auth.router)
app.include_router(cars.router)
app.include_router(requests.router)

admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(BuildingAdmin)
admin.add_view(ApartmentAdmin)
admin.add_view(UserAdmin)
admin.add_view(CarAdmin)
admin.add_view(AuditLogAdmin)
admin.add_view(RequestAdmin)


@app.on_event("startup")
async def create_superuser():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalars().first()

        if not user:
            print("Creating superuser...")
            admin_user = User(
                username="admin",
                phone_number="0000000000",
                hashed_password=get_password_hash(settings.SUPERUSER_PASSWORD),
                role=UserRole.SUPERUSER,
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
