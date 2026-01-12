"""Auth health endpoint tests."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(auth_client: TestClient) -> None:
    """測試健康檢查端點。"""
    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.unit
def test_readiness_check(auth_client: TestClient) -> None:
    """測試就緒檢查端點。"""
    response = auth_client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.unit
def test_root(auth_client: TestClient) -> None:
    """測試根路徑。"""
    response = auth_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Baby Weight Recorder Auth Service"
    assert "version" in data
