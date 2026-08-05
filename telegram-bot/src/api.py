import logging
from typing import Optional
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


class BackendAPI:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                headers=settings.HEADERS,
                timeout=10.0
            )
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client is not None and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None

    @classmethod
    async def request(cls, method: str, endpoint: str, **kwargs) -> httpx.Response:
        client = cls.get_client()
        url = f"{settings.API_URL}{endpoint}"
        return await client.request(method, url, **kwargs)

    @classmethod
    async def get(cls, endpoint: str, **kwargs) -> httpx.Response:
        return await cls.request("GET", endpoint, **kwargs)

    @classmethod
    async def post(cls, endpoint: str, **kwargs) -> httpx.Response:
        return await cls.request("POST", endpoint, **kwargs)
        
    @classmethod
    async def put(cls, endpoint: str, **kwargs) -> httpx.Response:
        return await cls.request("PUT", endpoint, **kwargs)
        
    @classmethod
    async def delete(cls, endpoint: str, **kwargs) -> httpx.Response:
        return await cls.request("DELETE", endpoint, **kwargs)


api_client = BackendAPI()
