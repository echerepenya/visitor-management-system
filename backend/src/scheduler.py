from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.services.pass_requests import check_expired_requests

scheduler = AsyncIOScheduler()


async def start_scheduler():
    scheduler.add_job(check_expired_requests, "interval", minutes=1)

    scheduler.start()
