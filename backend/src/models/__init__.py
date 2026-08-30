from .user import User, UserRole
from .apartment import Apartment
from .building import Building
from .car import Car
from .request import GuestRequest, RequestType, RequestStatus
from .parking import GuestParkingRequest, ParkingStatus, KeyfobStatus, KeyfobState
from .user_activity_log import UserActivityLog
from .audit_log import AuditLog
from .system_settings import SystemSettings

import os
from importlib import import_module

base_dir = os.path.dirname(__file__)

__all__ = []
for root, _, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".py") and not file.startswith("__"):
            relative_path = os.path.relpath(os.path.join(root, file), base_dir)
            module_name = "src.models." + relative_path[:-3].replace(os.sep, ".")
            module = import_module(module_name)

            __all__.append(os.path.basename(file)[:-3])
            globals()[os.path.basename(file)[:-3]] = module
