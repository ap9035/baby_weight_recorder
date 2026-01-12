"""Pytest configuration and fixtures."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from api.app.main import app as api_app
from api.app.repositories import InMemoryRepositories
from auth.app.main import app as auth_app


@pytest.fixture
def repos() -> InMemoryRepositories:
    """建立 InMemory Repositories."""
    return InMemoryRepositories()


@pytest.fixture
def api_client(repos: InMemoryRepositories) -> Generator[TestClient, None, None]:
    """建立 API 測試客戶端（使用 InMemory Repository）."""
    # 設定 app state
    api_app.state.repos = repos

    with TestClient(api_app) as client:
        yield client


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    """建立 Auth 測試客戶端。"""
    with TestClient(auth_app) as client:
        yield client


@pytest.fixture
def dev_headers() -> dict[str, str]:
    """Dev 模式認證 headers."""
    return {"Authorization": "Bearer dev"}


@pytest.fixture
async def setup_dev_user(repos: InMemoryRepositories) -> dict[str, Any]:
    """設定 dev 使用者並回傳相關資訊."""
    await repos.init_dev_data()
    return {
        "internal_user_id": "01DEV000000000000000000000",
        "provider_iss": "http://localhost",
        "provider_sub": "dev-user",
    }
