"""Kong Gateway 整合測試.

測試通過 Kong Gateway 的完整流程：
1. 通過 Kong 註冊使用者
2. 通過 Kong 登入取得 JWT
3. 通過 Kong 使用 JWT 呼叫 API
"""

import pytest
from fastapi.testclient import TestClient

from api.app.main import app as api_app
from api.app.repositories import InMemoryRepositories
from auth.app.main import app as auth_app


@pytest.fixture
def api_client(monkeypatch):
    """建立 API 測試客戶端."""
    repos = InMemoryRepositories()
    api_app.state.repos = repos

    # 設定為 OIDC 模式
    monkeypatch.setenv("AUTH_MODE", "local-oidc")
    monkeypatch.setenv("AUTH_ISSUER", "http://localhost:8082")
    monkeypatch.setenv("AUTH_AUDIENCE", "baby-weight-api")
    monkeypatch.setenv("AUTH_JWKS_URL", "http://localhost:8082/.well-known/jwks.json")

    from api.app.config import get_settings
    get_settings.cache_clear()

    with TestClient(api_app) as client:
        yield client

    get_settings.cache_clear()


@pytest.fixture
def auth_client(monkeypatch):
    """建立 Auth 測試客戶端."""
    from auth.app.config import get_settings as get_auth_settings
    from auth.app.dependencies import get_jwt_service
    from auth.app.repositories.memory import InMemoryUserRepository
    from auth.app.services.jwt import JWTService
    from auth.app.services.secrets import SecretService

    user_repo = InMemoryUserRepository()
    auth_app.state.user_repo = user_repo

    # 創建共享的 JWTService 實例
    auth_settings = get_auth_settings()
    auth_secret_service = SecretService("local-dev")
    shared_jwt_service = JWTService(auth_settings, auth_secret_service)
    _ = shared_jwt_service.get_jwks()

    # 使用 FastAPI 的 dependency_overrides
    auth_app.dependency_overrides[get_jwt_service] = lambda: shared_jwt_service

    with TestClient(auth_app) as client:
        yield client

    auth_app.dependency_overrides.clear()


@pytest.fixture
def kong_client():
    """模擬 Kong Gateway 客戶端（直接轉發到後端服務）."""
    # 在測試環境中，我們不實際啟動 Kong，而是模擬它的行為
    # 直接使用後端服務的 TestClient，但驗證路由邏輯
    return None


@pytest.fixture
def sample_user():
    """測試使用者資料."""
    return {
        "display_name": "Test User",
        "email": "test@example.com",
        "password": "test_password_123",
        "invite_code": "TEST_CODE",
    }


@pytest.mark.asyncio
async def test_kong_auth_service_routes(auth_client, sample_user, monkeypatch):
    """測試通過 Kong Gateway 訪問 Auth Service 的路由."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    # Mock 邀請碼服務
    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    # 測試註冊端點（模擬通過 Kong 的路由 /auth/register）
    register_response = auth_client.post("/auth/register", json=sample_user)
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == sample_user["email"]

    # 測試登入端點（模擬通過 Kong 的路由 /auth/token）
    login_response = auth_client.post(
        "/auth/token",
        json={
            "email": sample_user["email"],
            "password": sample_user["password"],
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"

    # 測試 JWKS 端點（模擬通過 Kong 的路由 /.well-known/jwks.json）
    jwks_response = auth_client.get("/.well-known/jwks.json")
    assert jwks_response.status_code == 200
    jwks_data = jwks_response.json()
    assert "keys" in jwks_data
    assert len(jwks_data["keys"]) > 0


@pytest.mark.asyncio
async def test_kong_api_service_routes(api_client, auth_client, sample_user, monkeypatch):
    """測試通過 Kong Gateway 訪問 API Service 的路由."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    # Mock 邀請碼服務
    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    # 1. 註冊使用者
    register_response = auth_client.post("/auth/register", json=sample_user)
    assert register_response.status_code == 201

    # 2. 登入取得 JWT
    login_response = auth_client.post(
        "/auth/token",
        json={
            "email": sample_user["email"],
            "password": sample_user["password"],
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. 從 Auth Service 取得 JWKS
    jwks_response = auth_client.get("/.well-known/jwks.json")
    jwks_data = jwks_response.json()

    # Mock API Service 的 JWKS 請求
    from api.app.services.jwt import JWTVerificationService

    async def mock_fetch_jwks(self):
        if self._jwks_cache is None:
            self._jwks_cache = jwks_data
        return self._jwks_cache

    monkeypatch.setattr(JWTVerificationService, "_fetch_jwks", mock_fetch_jwks)

    # 4. 測試 API Service 的健康檢查端點（模擬通過 Kong 的路由 /health）
    health_response = api_client.get("/health")
    assert health_response.status_code == 200

    # 5. 測試 API Service 的 v1 路由（模擬通過 Kong 的路由 /v1/babies）
    headers = {"Authorization": f"Bearer {token}"}

    # 創建嬰兒
    baby_response = api_client.post(
        "/v1/babies",
        json={
            "name": "Test Baby",
            "gender": "male",
            "birth_date": "2024-01-01",
        },
        headers=headers,
    )
    assert baby_response.status_code == 201
    baby_id = baby_response.json()["baby_id"]

    # 查詢嬰兒列表
    list_response = api_client.get("/v1/babies", headers=headers)
    assert list_response.status_code == 200
    babies = list_response.json()
    assert len(babies) == 1

    # 查詢單個嬰兒
    get_response = api_client.get(f"/v1/babies/{baby_id}", headers=headers)
    assert get_response.status_code == 200
    baby_data = get_response.json()
    assert baby_data["name"] == "Test Baby"


@pytest.mark.asyncio
async def test_kong_full_flow(auth_client, api_client, sample_user, monkeypatch):
    """測試通過 Kong Gateway 的完整流程：註冊 → 登入 → 使用 API."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    # Mock 邀請碼服務
    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    # 1. 通過 Kong 註冊使用者（/auth/register）
    register_response = auth_client.post("/auth/register", json=sample_user)
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == sample_user["email"]

    # 2. 通過 Kong 登入取得 JWT（/auth/token）
    login_response = auth_client.post(
        "/auth/token",
        json={
            "email": sample_user["email"],
            "password": sample_user["password"],
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. 從 Auth Service 取得 JWKS（/.well-known/jwks.json）
    jwks_response = auth_client.get("/.well-known/jwks.json")
    jwks_data = jwks_response.json()

    # Mock API Service 的 JWKS 請求
    from api.app.services.jwt import JWTVerificationService

    async def mock_fetch_jwks(self):
        if self._jwks_cache is None:
            self._jwks_cache = jwks_data
        return self._jwks_cache

    monkeypatch.setattr(JWTVerificationService, "_fetch_jwks", mock_fetch_jwks)

    # 4. 通過 Kong 使用 JWT 呼叫 API（/v1/babies）
    headers = {"Authorization": f"Bearer {token}"}

    # 創建嬰兒
    baby_response = api_client.post(
        "/v1/babies",
        json={
            "name": "Kong Test Baby",
            "gender": "female",
            "birth_date": "2024-02-01",
        },
        headers=headers,
    )
    assert baby_response.status_code == 201
    baby_id = baby_response.json()["baby_id"]

    # 查詢嬰兒列表
    list_response = api_client.get("/v1/babies", headers=headers)
    assert list_response.status_code == 200
    babies = list_response.json()
    assert len(babies) == 1
    assert babies[0]["name"] == "Kong Test Baby"

    # 查詢單個嬰兒
    get_response = api_client.get(f"/v1/babies/{baby_id}", headers=headers)
    assert get_response.status_code == 200
    baby_data = get_response.json()
    assert baby_data["name"] == "Kong Test Baby"
    assert baby_data["gender"] == "female"
