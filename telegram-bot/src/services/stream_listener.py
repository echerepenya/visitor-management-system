import json
import asyncio
import logging
from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from src.config import REDIS_CONSUMER_NAME
from src.handlers.auth import force_logout_user
from src.handlers.notify import notify_guards, notify_resident_closed, notify_resident_expired

STREAM_NAME = "vms_stream"
GROUP_NAME = "bot_workers"


handlers = {
    "new_guest_request": notify_guards,
    "request_closed": notify_resident_closed,
    "request_expired": notify_resident_expired,
    "user_deleted": force_logout_user
}


async def handle_event(bot, data, storage):
    event = data.get('event')
    handler = handlers.get(event)

    if not handler:
        logging.warning(f"Невідомий тип події: {event}")
        return

    await handler(bot, data, storage)


async def listen_redis_stream(bot: Bot, redis: Redis, storage: RedisStorage):
    try:
        await redis.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
    except ResponseError as e:
        if "BUSYGROUP" not in str(e): raise

    logging.info(f"🎧 Bot is listening to Redis Stream: {STREAM_NAME}")

    while True:
        try:
            messages = await redis.xreadgroup(
                GROUP_NAME, REDIS_CONSUMER_NAME, {STREAM_NAME: ">"}, count=10, block=2000
            )

            for stream_name, msg_list in messages:
                for msg_id, msg_data in msg_list:
                    payload_str = msg_data.get("payload")

                    if payload_str:
                        data = json.loads(payload_str)
                        await handle_event(bot=bot, data=data, storage=storage)

                    await redis.xack(STREAM_NAME, GROUP_NAME, msg_id)

        except Exception as e:
            logging.error(f"Помилка читання Redis Stream: {e}")
            await asyncio.sleep(5)
