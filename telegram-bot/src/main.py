import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from redis.asyncio import Redis

from src.config import BOT_TOKEN, logger, REDIS_URL
from src.handlers import auth, passes, car_search, info
from src.services.stream_listener import listen_redis_stream


async def main():
    redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    redis_storage = RedisStorage(redis=redis_client)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher(storage=redis_storage)

    dp["redis"] = redis_client

    dp.include_router(auth.router)
    dp.include_router(passes.router)
    dp.include_router(info.router)
    dp.include_router(car_search.router)

    stream_task = asyncio.create_task(
        listen_redis_stream(bot, redis_client, redis_storage)
    )

    await bot.delete_webhook(drop_pending_updates=True)

    print('Bot is starting...')
    try:
        await dp.start_polling(bot)
    finally:
        stream_task.cancel()
        await bot.session.close()
        await redis_client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped!")
