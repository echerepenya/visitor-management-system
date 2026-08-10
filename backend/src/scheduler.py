from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.services.pass_requests import check_expired_requests
from src.services.parking import check_expired_parking_requests
from src.database import AsyncSessionLocal
import logging

scheduler = AsyncIOScheduler()

async def run_parking_checks():
    async with AsyncSessionLocal() as db:
        await check_expired_parking_requests(db)

async def start_scheduler():
    scheduler.add_job(check_expired_requests, "interval", minutes=1)
    scheduler.add_job(run_parking_checks, "interval", minutes=1)
    
    scheduler.start()
