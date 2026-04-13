from sqladmin import ModelView
from starlette.requests import Request
from sqlalchemy import select, or_
from fastapi import HTTPException

from src.models.car import Car
from src.models.user import User, UserRole
from src.services.audit_mixin import AuditMixin
from src.database import AsyncSessionLocal
from src.utils import normalize_plate


class CarAdmin(AuditMixin, ModelView, model=Car):
    name = "Авто"
    name_plural = "Авто"

    can_export = False
    can_view_details = False

    page_size = 25
    page_size_options = [25, 50, 100, 200]

    column_searchable_list = ["plate_number", "owner.phone_number"]

    icon = "fa-solid fa-car"
    column_list = [
        "plate_number",
        "model",
        "owner.full_name",
        "owner.phone_number",
        "owner.apartment.building.address",
        "owner.apartment.number"
    ]

    column_labels = {
        "plate_number": "Номер авто",
        "model": "Марка",
        "owner": "Власник (Пошук по телефону)",
        "owner.full_name": "Власник",
        "owner.phone_number": "Телефон",
        "owner.apartment.building.address": "Будинок",
        "owner.apartment.number": "Квартира",
        "notes": "Додаткові нотатки"
    }

    form_columns = ["plate_number", "model", "owner", "notes"]

    form_ajax_refs = {
        "owner": {
            "fields": ["phone_number"],
            "placeholder": "Пошук мешканця...",
            "filter": User.role == UserRole.RESIDENT,
        }
    }

    def is_accessible(self, request: Request) -> bool:
        return request.session.get('user', {}).get("is_admin")

    async def on_model_change(self, data, model, is_created, request):
        plate_number = data.get("plate_number")

        if plate_number is not None and isinstance(plate_number, str):
            plate_number = normalize_plate(plate_number)
        else:
            raise ValueError("Номер авто не може бути пустим")

        if plate_number:
            async with AsyncSessionLocal() as session:
                stmt = select(Car).where(Car.plate_number == plate_number)
                if not is_created:
                    stmt = stmt.where(Car.id != model.id)
                    
                result = await session.execute(stmt)
                if result.scalar_one_or_none():
                    raise ValueError("Авто з таким номером вже зареєстровано")
