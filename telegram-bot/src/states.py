from aiogram.fsm.state import State, StatesGroup


class PassState(StatesGroup):
    waiting_for_type = State()  # Taxi, Guest, etc.
    waiting_for_value = State()  # car plate number


class SecurityState(StatesGroup):
    waiting_for_full_search = State()

class ParkingState(StatesGroup):
    waiting_for_plate = State()
