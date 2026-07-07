from datetime import datetime, timedelta, timezone

import pytest

from src.admin import dashboard as dashboard_module
from src.admin.dashboard import _get_stats
from src.models.building import Building
from src.models.apartment import Apartment
from src.models.user import User, UserRole
from src.models.car import Car
from src.models.request import GuestRequest, RequestStatus, RequestType

# Calendar dates where the old `today_start.replace(day=day - weekday())` formula
# produced a non-positive day and raised "ValueError: day is out of range for month".
MONTH_BOUNDARY_CRASH_DATES = [
    datetime(2024, 2, 1, tzinfo=timezone.utc),
    datetime(2024, 9, 1, tzinfo=timezone.utc),
    datetime(2025, 6, 1, tzinfo=timezone.utc),
    datetime(2026, 7, 1, tzinfo=timezone.utc),
    datetime(2026, 11, 1, tzinfo=timezone.utc),
]


def _freeze_now(monkeypatch, fixed_now: datetime) -> None:
    class _FrozenDateTime:
        @staticmethod
        def now(tz=None):
            return fixed_now

    monkeypatch.setattr(dashboard_module, "datetime", _FrozenDateTime)


async def _make_resident(session, *, phone_number, full_name, apartment=None, created_at=None) -> User:
    user = User(
        phone_number=phone_number,
        role=UserRole.RESIDENT,
        full_name=full_name,
        apartment=apartment,
        created_at=created_at,
    )
    session.add(user)
    await session.flush()
    return user


async def _make_guard(session, *, username, full_name) -> User:
    guard = User(
        phone_number=username,
        role=UserRole.GUARD,
        username=username,
        full_name=full_name,
    )
    session.add(guard)
    await session.flush()
    return guard


async def _make_request(session, *, user, created_at, status=RequestStatus.NEW, type_=RequestType.GUEST_CAR,
                         completed_by=None, updated_at=None) -> GuestRequest:
    req = GuestRequest(
        user=user,
        type=type_,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        completed_by=completed_by,
    )
    session.add(req)
    await session.flush()
    return req


async def test_get_stats_on_empty_db_returns_zeroed_stats(db_session):
    stats = await _get_stats(db_session)

    assert stats["total_residents"] == 0
    assert stats["req_today"] == 0
    assert stats["req_week"] == 0
    assert stats["req_month"] == 0
    assert stats["completion_rate"] == 0
    assert stats["by_guard"] == []
    assert stats["most_active"] is None
    assert stats["busiest_day"] is None


@pytest.mark.parametrize("fixed_now", MONTH_BOUNDARY_CRASH_DATES)
async def test_get_stats_does_not_crash_at_month_boundary(db_session, monkeypatch, fixed_now):
    _freeze_now(monkeypatch, fixed_now)

    stats = await _get_stats(db_session)

    assert stats["req_week"] == 0
    assert stats["req_month"] == 0


async def test_week_start_is_monday_of_current_week(db_session, monkeypatch):
    fixed_now = datetime(2026, 7, 8, 15, 0, tzinfo=timezone.utc)  # Wednesday
    _freeze_now(monkeypatch, fixed_now)

    building = Building(address="Test 1")
    apartment = Apartment(number="1", building=building)
    session = db_session
    session.add_all([building, apartment])
    await session.flush()

    resident = await _make_resident(session, phone_number="380501112233", full_name="Resident", apartment=apartment)

    week_start = datetime(2026, 7, 6, tzinfo=timezone.utc)  # Monday of that week, same month as fixed_now

    in_this_week = await _make_request(session, user=resident, created_at=week_start)
    in_previous_week = await _make_request(
        session, user=resident, created_at=week_start - timedelta(seconds=1)
    )
    await session.commit()

    stats = await _get_stats(session)

    assert stats["req_week"] == 1
    assert stats["req_month"] == 2


async def test_get_stats_full_fixture(db_session):
    session = db_session

    building = Building(address="Main St 1")
    apartment_occupied = Apartment(number="1", building=building)
    apartment_empty = Apartment(number="2", building=building)
    session.add_all([building, apartment_occupied, apartment_empty])
    await session.flush()

    resident = await _make_resident(
        session, phone_number="380501112233", full_name="Alice", apartment=apartment_occupied,
    )
    guard = await _make_guard(session, username="guard1", full_name="Guard One")

    car_with_rfid = Car(plate_number="AA1234BB", owner=resident, has_rfid=True)
    car_without_rfid = Car(plate_number="CC5678DD", owner=resident, has_rfid=False)
    session.add_all([car_with_rfid, car_without_rfid])
    await session.flush()

    now = datetime.now(timezone.utc)

    completed_req = await _make_request(
        session, user=resident, created_at=now, status=RequestStatus.COMPLETED,
        completed_by=guard.id, updated_at=now,
    )
    expired_req = await _make_request(
        session, user=resident, created_at=now, status=RequestStatus.EXPIRED,
    )
    new_req = await _make_request(
        session, user=resident, created_at=now, status=RequestStatus.NEW,
    )
    await session.commit()

    stats = await _get_stats(session)

    assert stats["total_residents"] == 1
    assert stats["total_cars"] == 2
    assert stats["rfid_cars"] == 1
    assert stats["rfid_pct"] == 50
    assert stats["req_total"] == 3
    assert stats["by_status"] == {"completed": 1, "expired": 1, "new": 1}
    assert stats["completion_rate"] == 50  # 1 completed / (1 completed + 1 expired)
    assert stats["empty_apartments"] == 1

    assert len(stats["by_guard"]) == 1
    assert stats["by_guard"][0]["display_name"] == "Guard One"
    assert stats["by_guard"][0]["total"] == 1
    assert stats["by_guard"][0]["pct"] == 100

    assert stats["most_active"] == {"name": "Alice", "count": 3}
    assert stats["most_cars"] == {"name": "Alice", "count": 2}


async def test_by_guard_daily_buckets_last_5_days(db_session, monkeypatch):
    fixed_now = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)  # Wednesday
    _freeze_now(monkeypatch, fixed_now)

    session = db_session
    resident = await _make_resident(session, phone_number="380501112233", full_name="Alice")
    guard1 = await _make_guard(session, username="guard1", full_name="Guard One")
    guard2 = await _make_guard(session, username="guard2", full_name="Guard Two")

    def at(day, hour=10):
        return datetime(2026, 7, day, hour, tzinfo=timezone.utc)

    # Guard One: 2 completions today (07-08), 1 completion on 07-06
    await _make_request(session, user=resident, created_at=at(8), status=RequestStatus.COMPLETED,
                         completed_by=guard1.id, updated_at=at(8, 9))
    await _make_request(session, user=resident, created_at=at(8), status=RequestStatus.COMPLETED,
                         completed_by=guard1.id, updated_at=at(8, 11))
    await _make_request(session, user=resident, created_at=at(6), status=RequestStatus.COMPLETED,
                         completed_by=guard1.id, updated_at=at(6))

    # Guard Two: 1 completion on 07-05 (inside window), 1 on 07-02 (outside the 5-day window)
    await _make_request(session, user=resident, created_at=at(5), status=RequestStatus.COMPLETED,
                         completed_by=guard2.id, updated_at=at(5))
    await _make_request(session, user=resident, created_at=at(2), status=RequestStatus.COMPLETED,
                         completed_by=guard2.id, updated_at=at(2))
    await session.commit()

    stats = await _get_stats(session)
    daily = stats["by_guard_daily"]

    assert daily["day_labels"] == ["04.07", "05.07", "06.07", "07.07", "08.07"]

    guards_by_name = {g["display_name"]: g for g in daily["guards"]}
    assert set(guards_by_name) == {"Guard One", "Guard Two"}

    guard_one = guards_by_name["Guard One"]
    assert guard_one["counts"] == [0, 0, 1, 0, 2]
    assert guard_one["total"] == 3

    guard_two = guards_by_name["Guard Two"]
    assert guard_two["counts"] == [0, 1, 0, 0, 0]
    assert guard_two["total"] == 1  # the 07-02 completion falls outside the window and is excluded

    # sorted by total desc
    assert daily["guards"][0]["display_name"] == "Guard One"
