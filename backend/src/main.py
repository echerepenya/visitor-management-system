import os

from fastapi import FastAPI, Depends
from sqladmin import Admin
from sqlalchemy import select
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from src.config import settings
from src.database import engine, AsyncSessionLocal
from src.routers import cars, auth, requests
from src.models.user import User, UserRole
from src.security import authentication_backend, get_password_hash, get_api_key
from src.services.admin.apartment_admin import ApartmentAdmin
from src.services.admin.audit_log_admin import AuditLogAdmin
from src.services.admin.building_admin import BuildingAdmin
from src.services.admin.car_admin import CarAdmin
from src.services.admin.user_admin import SuperUserAdmin, RestrictedUserAdmin

app = FastAPI(title="Visitor Management System API")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your_super_secret_key_change_me")
)

app.include_router(auth.router, prefix='/api', dependencies=[Depends(get_api_key)])
app.include_router(cars.router, prefix="/api", dependencies=[Depends(get_api_key)])
app.include_router(requests.router, prefix="/api")


admin = Admin(app, engine, authentication_backend=authentication_backend, title="Адмін панель")
admin.add_view(BuildingAdmin)
admin.add_view(ApartmentAdmin)
admin.add_view(RestrictedUserAdmin)
admin.add_view(SuperUserAdmin)
admin.add_view(CarAdmin)
admin.add_view(AuditLogAdmin)


@app.on_event("startup")
async def create_superuser():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "sadmin"))
        user = result.scalars().first()

        if not user:
            print("Creating superuser...")
            admin_user = User(
                username="sadmin",
                phone_number="000000000000",
                hashed_password=get_password_hash(settings.SUPERUSER_PASSWORD),
                role=UserRole.RESIDENT,
                is_agreed_processing_personal_data=True,
                is_admin=True,
                is_superadmin=True
            )
            session.add(admin_user)
            await session.commit()
