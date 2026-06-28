from sqladmin import BaseView, expose
from sqlalchemy import select, func, distinct, cast, Date, case
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from datetime import datetime, timezone

from src.database import AsyncSessionLocal
from src.models.apartment import Apartment
from src.models.building import Building
from src.models.car import Car
from src.models.request import GuestRequest, RequestStatus
from src.models.user import User, UserRole


class DashboardView(BaseView):
    name = "Дашборд"
    icon = "fa-solid fa-gauge-high"

    def is_accessible(self, request: Request) -> bool:
        return bool(request.session.get("user", {}).get("is_admin"))

    @expose("/dashboard", methods=["GET"])
    async def dashboard(self, request: Request) -> Response:
        if not self.is_accessible(request):
            return RedirectResponse(url="/admin/login", status_code=302)
        async with AsyncSessionLocal() as session:
            stats = await _get_stats(session)
        return await self.templates.TemplateResponse(
            request, "sqladmin/dashboard.html", {"stats": stats}
        )


async def _get_stats(session: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start.replace(day=today_start.day - today_start.weekday())
    month_start = today_start.replace(day=1)

    # --- Residents ---
    total_residents = await session.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.RESIDENT,
            User.is_deleted.is_(False),
        )
    )
    telegram_connected = await session.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.RESIDENT,
            User.is_deleted.is_(False),
            User.telegram_id.is_not(None),
        )
    )
    residents_with_cars = await session.scalar(
        select(func.count(distinct(Car.owner_id)))
    )
    new_residents_month = await session.scalar(
        select(func.count(User.id)).where(
            User.role == UserRole.RESIDENT,
            User.is_deleted.is_(False),
            User.created_at >= month_start,
        )
    )

    # --- Cars ---
    total_cars = await session.scalar(select(func.count(Car.id)))
    rfid_cars = await session.scalar(
        select(func.count(Car.id)).where(Car.has_rfid.is_(True))
    )

    # --- Requests by time period ---
    req_today = await session.scalar(
        select(func.count(GuestRequest.id)).where(GuestRequest.created_at >= today_start)
    )
    req_week = await session.scalar(
        select(func.count(GuestRequest.id)).where(GuestRequest.created_at >= week_start)
    )
    req_month = await session.scalar(
        select(func.count(GuestRequest.id)).where(GuestRequest.created_at >= month_start)
    )
    req_total = await session.scalar(select(func.count(GuestRequest.id)))

    # --- Requests by status ---
    status_rows = (
        await session.execute(
            select(GuestRequest.status, func.count(GuestRequest.id)).group_by(GuestRequest.status)
        )
    ).all()
    by_status = {row[0].value: row[1] for row in status_rows}

    # --- Requests by type ---
    type_rows = (
        await session.execute(
            select(GuestRequest.type, func.count(GuestRequest.id)).group_by(GuestRequest.type)
        )
    ).all()
    by_type = {row[0].value: row[1] for row in type_rows}

    # --- Completed requests per guard ---
    # One query with conditional aggregation to avoid N+1 per time period
    guard_rows = (
        await session.execute(
            select(
                User.full_name,
                User.username,
                func.count(GuestRequest.id).label("total"),
                func.count(
                    case((GuestRequest.updated_at >= month_start, GuestRequest.id), else_=None)
                ).label("this_month"),
                func.count(
                    case((GuestRequest.updated_at >= week_start, GuestRequest.id), else_=None)
                ).label("this_week"),
            )
            .join(GuestRequest, GuestRequest.completed_by == User.id)
            .where(GuestRequest.status == RequestStatus.COMPLETED)
            .group_by(User.id, User.full_name, User.username)
            .order_by(func.count(GuestRequest.id).desc())
        )
    ).all()

    total_completed = by_status.get("completed", 0)
    by_guard = [
        {
            "display_name": row.full_name or row.username or "—",
            "username": row.username or "",
            "total": row.total,
            "this_month": row.this_month,
            "this_week": row.this_week,
            "pct": round(row.total / total_completed * 100) if total_completed else 0,
        }
        for row in guard_rows
    ]

    # --- Records ---
    most_active_row = (
        await session.execute(
            select(User.full_name, User.phone_number, func.count(GuestRequest.id).label("cnt"))
            .join(GuestRequest, GuestRequest.user_id == User.id)
            .where(User.is_deleted.is_(False))
            .group_by(User.id, User.full_name, User.phone_number)
            .order_by(func.count(GuestRequest.id).desc())
            .limit(1)
        )
    ).first()

    most_cars_row = (
        await session.execute(
            select(User.full_name, func.count(Car.id).label("cnt"))
            .join(Car, Car.owner_id == User.id)
            .group_by(User.id, User.full_name)
            .order_by(func.count(Car.id).desc())
            .limit(1)
        )
    ).first()

    most_residents_row = (
        await session.execute(
            select(Building.address, Apartment.number, func.count(User.id).label("cnt"))
            .join(Building, Apartment.building_id == Building.id)
            .join(User, User.apartment_id == Apartment.id)
            .where(User.is_deleted.is_(False), User.role == UserRole.RESIDENT)
            .group_by(Apartment.id, Building.address, Apartment.number)
            .order_by(func.count(User.id).desc())
            .limit(1)
        )
    ).first()

    busiest_day_row = (
        await session.execute(
            select(
                cast(GuestRequest.created_at, Date).label("day"),
                func.count(GuestRequest.id).label("cnt"),
            )
            .group_by(cast(GuestRequest.created_at, Date))
            .order_by(func.count(GuestRequest.id).desc())
            .limit(1)
        )
    ).first()

    # --- Infrastructure ---
    total_buildings = await session.scalar(select(func.count(Building.id)))
    total_apartments = await session.scalar(select(func.count(Apartment.id)))
    occupied_apts = await session.scalar(
        select(func.count(distinct(User.apartment_id))).where(
            User.apartment_id.is_not(None),
            User.is_deleted.is_(False),
            User.role == UserRole.RESIDENT,
        )
    )
    total_admins = await session.scalar(
        select(func.count(User.id)).where(
            User.is_admin.is_(True),
            User.is_deleted.is_(False),
        )
    )

    # --- Derived metrics ---
    completed = by_status.get("completed", 0)
    expired = by_status.get("expired", 0)
    resolved = completed + expired
    completion_rate = round(completed / resolved * 100) if resolved > 0 else 0
    telegram_pct = round(telegram_connected / total_residents * 100) if total_residents else 0
    rfid_pct = round(rfid_cars / total_cars * 100) if total_cars else 0
    empty_apartments = (total_apartments or 0) - (occupied_apts or 0)

    return {
        # Residents
        "total_residents": total_residents or 0,
        "telegram_connected": telegram_connected or 0,
        "telegram_pct": telegram_pct,
        "residents_with_cars": residents_with_cars or 0,
        "new_residents_month": new_residents_month or 0,
        # Cars
        "total_cars": total_cars or 0,
        "rfid_cars": rfid_cars or 0,
        "no_rfid_cars": (total_cars or 0) - (rfid_cars or 0),
        "rfid_pct": rfid_pct,
        # Requests — time
        "req_today": req_today or 0,
        "req_week": req_week or 0,
        "req_month": req_month or 0,
        "req_total": req_total or 0,
        # Requests — breakdown
        "by_status": by_status,
        "by_type": by_type,
        "completion_rate": completion_rate,
        "by_guard": by_guard,
        # Records
        "most_active": {
            "name": most_active_row[0] or most_active_row[1],
            "count": most_active_row[2],
        } if most_active_row else None,
        "most_cars": {
            "name": most_cars_row[0],
            "count": most_cars_row[1],
        } if most_cars_row else None,
        "most_residents_apt": {
            "address": most_residents_row[0],
            "number": most_residents_row[1],
            "count": most_residents_row[2],
        } if most_residents_row else None,
        "busiest_day": {
            "date": busiest_day_row[0].strftime("%d.%m.%Y") if hasattr(busiest_day_row[0], "strftime") else str(busiest_day_row[0]),
            "count": busiest_day_row[1],
        } if busiest_day_row else None,
        # Infrastructure
        "total_buildings": total_buildings or 0,
        "total_apartments": total_apartments or 0,
        "empty_apartments": empty_apartments,
        "total_admins": total_admins or 0,
    }
