import os
from typing import AsyncGenerator

import pytest

try:
    from app.main import app as fastapi_app
except Exception:
    fastapi_app = None

try:
    import httpx
except ImportError:
    httpx = None


@pytest.fixture(scope="session")
def app():
    if fastapi_app is None:
        pytest.skip("FastAPI app not importable (app.main:app).")
    return fastapi_app


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/sales")


@pytest.fixture
async def client(app) -> AsyncGenerator:
    if httpx is None:
        pytest.skip("httpx not installed")
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
