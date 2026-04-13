import logging
import os
import sys
import socket

TIMEZONE = os.getenv("TZ", "Europe/Kyiv")
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://backend:8000/api")
API_KEY = os.getenv("API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://vms-redis:6379/0")
LIVING_COMPLEX_NAME = os.getenv("LIVING_COMPLEX_NAME")
GUARD_DASHBOARD_URL = os.getenv("GUARD_DASHBOARD_URL")

HOSTNAME = socket.gethostname()
REDIS_CONSUMER_NAME = os.getenv("REDIS_CONSUMER_NAME", f"bot_consumer_{HOSTNAME}")

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
