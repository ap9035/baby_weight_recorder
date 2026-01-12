"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from api.app.main import app as api_app
from auth.app.main import app as auth_app


@pytest.fixture
def api_client() -> TestClient:
    """建立 API 測試客戶端。"""
    return TestClient(api_app)


@pytest.fixture
def auth_client() -> TestClient:
    """建立 Auth 測試客戶端。"""
    return TestClient(auth_app)
