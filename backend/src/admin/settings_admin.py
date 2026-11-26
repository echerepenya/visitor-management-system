from sqladmin import BaseView, expose
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from src.database import AsyncSessionLocal
from src.models.system_settings import SystemSettings
from src.models.user import User, UserRole

class SettingsView(BaseView):
    name = "Налаштування"
    icon = "fa-solid fa-cog"

    def is_accessible(self, request: Request) -> bool:
        return bool(request.session.get("user", {}).get("is_superadmin"))

    @expose("/settings", methods=["GET", "POST"])
    async def settings_page(self, request: Request) -> Response:
        if not self.is_accessible(request):
            return RedirectResponse(url="/admin/login", status_code=302)

        async with AsyncSessionLocal() as session:
            settings = await self._get_settings(session)

            if request.method == "POST":
                form = await request.form()
                guest_parking_spots = int(form.get("guest_parking_spots", 11))
                guest_parking_post_id = form.get("guest_parking_post_id")
                
                settings.guest_parking_spots = guest_parking_spots
                if guest_parking_post_id and guest_parking_post_id.isdigit():
                    settings.guest_parking_post_id = int(guest_parking_post_id)
                else:
                    settings.guest_parking_post_id = None
                
                await session.commit()
                return RedirectResponse(url=request.url.path, status_code=302)

            guards = await self._get_guards(session)

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/settings.html",
            {"settings": settings, "guards": guards},
        )

    async def _get_settings(self, session: AsyncSession) -> SystemSettings:
        stmt = select(SystemSettings).where(SystemSettings.id == 1)
        result = await session.execute(stmt)
        settings = result.scalars().first()
        if not settings:
            settings = SystemSettings(id=1)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
        return settings

    async def _get_guards(self, session: AsyncSession):
        stmt = select(User).where(User.role == UserRole.GUARD)
        result = await session.execute(stmt)
        return result.scalars().all()
