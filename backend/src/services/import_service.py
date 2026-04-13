import csv
import io
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.building import Building
from src.models.apartment import Apartment
from src.models.user import User, UserRole
from src.models.car import Car
from src.utils import normalize_phone, normalize_plate

logger = logging.getLogger(__name__)


async def import_customers_and_cars_from_csv(file_content: bytes, db: AsyncSession):
    decoded_content = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded_content))

    stats = {"users_created": 0, "cars_created": 0, "errors": 0}

    for row in reader:
        try:
            building_addr = row.get("building", "").strip()
            apt_num = row.get("apartment", "").strip()
            phone = normalize_phone(row.get("phone", "").strip())
            full_name = row.get("fullname", "").strip()
            plate = normalize_plate(row.get("car_number", "").strip())
            car_model = row.get("car_model", "").strip()
            car_note = row.get("car_notes", "").strip()

            if not phone:
                continue

            # 1. Building
            stmt = select(Building).where(Building.address == building_addr)
            res = await db.execute(stmt)
            building = res.scalar_one_or_none()
            if not building and building_addr:
                raise ValueError("Building not found")

            # 2. Apartment
            apartment = None
            if building and apt_num:
                stmt = select(Apartment).where(Apartment.building_id == building.id, Apartment.number == apt_num)
                res = await db.execute(stmt)
                apartment = res.scalar_one_or_none()
                if not apartment:
                    raise ValueError("Apartment not found")

            # 3. User
            stmt = select(User).where(User.phone_number == phone)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()

            if not user:
                user = User(
                    phone_number=phone,
                    full_name=full_name,
                    role=UserRole.RESIDENT,
                    apartment_id=apartment.id if apartment else None,
                    is_agreed_processing_personal_data=True
                )
                db.add(user)
                await db.flush()
                stats["users_created"] += 1
            else:
                # Update apartment if not set or changed? 
                # Requirement: "перевіряємо чи існує кастомер, якщо існує, перевіряєм його авто"
                if apartment and user.apartment_id != apartment.id:
                    user.apartment_id = apartment.id
                if full_name and not user.full_name:
                    user.full_name = full_name

            # 4. Car
            if plate:
                stmt = select(Car).where(Car.plate_number == plate)
                res = await db.execute(stmt)
                car = res.scalar_one_or_none()

                if not car:
                    car = Car(
                        plate_number=plate,
                        model=car_model,
                        notes=car_note,
                        owner_id=user.id
                    )
                    db.add(car)
                    await db.flush()
                    stats["cars_created"] += 1
                else:
                    logger.warning(f"Car already exists: {plate}")

        except Exception as e:
            logger.error(f"Error importing row {row}: {e}")
            stats["errors"] += 1
            continue

    await db.commit()
    return stats
