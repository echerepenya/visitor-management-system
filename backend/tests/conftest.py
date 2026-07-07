import os
import subprocess
import time
import uuid

os.environ.setdefault("TZ", "UTC")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("SUPERUSER_PASSWORD", "test")
os.environ.setdefault("BOT_TOKEN", "test")
os.environ.setdefault("SECRET_KEY", "test")

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import src.models  # noqa: F401 - registers all model tables on Base.metadata
from src.database import Base

# Tests run against a real ephemeral Postgres container (matching the production
# dialect) rather than SQLite, since some queries (e.g. `cast(datetime_col, Date)`)
# rely on Postgres-specific semantics that SQLite doesn't emulate correctly.
_PG_USER = "test"
_PG_PASSWORD = "test"
_PG_DB = "test"


@pytest.fixture(scope="session")
def postgres_dsn():
    container_name = f"vms-test-pg-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "docker", "run", "-d", "--rm",
            "--name", container_name,
            "-e", f"POSTGRES_USER={_PG_USER}",
            "-e", f"POSTGRES_PASSWORD={_PG_PASSWORD}",
            "-e", f"POSTGRES_DB={_PG_DB}",
            "-P",
            "postgres:15-alpine",
        ],
        check=True,
        capture_output=True,
    )

    try:
        port_line = subprocess.run(
            ["docker", "port", container_name, "5432/tcp"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        host_port = port_line.rsplit(":", 1)[-1]

        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            ready = subprocess.run(
                ["docker", "exec", container_name, "pg_isready", "-U", _PG_USER],
                capture_output=True,
            )
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Postgres test container did not become ready in time")

        yield f"postgresql+asyncpg://{_PG_USER}:{_PG_PASSWORD}@localhost:{host_port}/{_PG_DB}"
    finally:
        subprocess.run(["docker", "stop", container_name], capture_output=True)


@pytest.fixture
async def db_session(postgres_dsn):
    engine = create_async_engine(postgres_dsn)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
