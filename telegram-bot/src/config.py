import logging
import os
import sys

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://backend:8000/api")
API_KEY = os.getenv("API_KEY")
LIVING_COMPLEX_NAME = os.getenv("LIVING_COMPLEX_NAME")

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
