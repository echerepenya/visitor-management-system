from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


class DbSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        async with AsyncSessionLocal() as session:
            request.state.session = session
            return await call_next(request)


redis_client: Redis | None = None


async def init_redis():
    global redis_client
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    print("✅ Redis connection established")


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        print("🛑 Redis connection closed")


async def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis is not initialized")
    return redis_client
