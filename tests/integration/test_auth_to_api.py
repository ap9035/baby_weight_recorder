"""Auth → API 整合測試.

測試完整的認證流程：
1. 註冊使用者
2. 登入取得 JWT
3. 使用 JWT 呼叫 API
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

    # 設定為 OIDC 模式（在測試前設定環境變數）
    monkeypatch.setenv("AUTH_MODE", "local-oidc")
    monkeypatch.setenv("AUTH_ISSUER", "http://localhost:8082")
    monkeypatch.setenv("AUTH_AUDIENCE", "baby-weight-api")
    monkeypatch.setenv("AUTH_JWKS_URL", "http://localhost:8082/.well-known/jwks.json")

    # 清除 settings cache 以重新載入
    from api.app.config import get_settings

    get_settings.cache_clear()

    with TestClient(api_app) as client:
        yield client

    # 清理
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
    # 觸發私鑰生成
    _ = shared_jwt_service.get_jwks()

    # 使用 FastAPI 的 dependency_overrides
    auth_app.dependency_overrides[get_jwt_service] = lambda: shared_jwt_service

    with TestClient(auth_app) as client:
        yield client

    # 清理
    auth_app.dependency_overrides.clear()


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
async def test_register_login_and_use_api(auth_client, api_client, sample_user, monkeypatch):
    """測試完整流程：註冊 → 登入 → 使用 API."""
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
    user_data = register_response.json()
    assert user_data["email"] == sample_user["email"]

    # 2. 登入取得 JWT
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
    token = token_data["access_token"]

    # 3. 從 Auth Service 的實際端點取得 JWKS（確保使用相同的 JWTService 實例）
    jwks_response = auth_client.get("/.well-known/jwks.json")
    assert jwks_response.status_code == 200
    jwks_data = jwks_response.json()

    # Mock API Service 的 JWTVerificationService 的 _fetch_jwks 方法
    from api.app.services.jwt import JWTVerificationService

    async def mock_fetch_jwks(self):
        """Mock JWKS 取得方法，直接返回 Auth Service 的 JWKS."""
        if self._jwks_cache is None:
            self._jwks_cache = jwks_data
        return self._jwks_cache

    monkeypatch.setattr(JWTVerificationService, "_fetch_jwks", mock_fetch_jwks)

    # 4. 使用 JWT 呼叫 API
    # 注意：Auth Service 簽發的 token 中包含 internal_user_id claim
    # 所以 API Service 可以直接使用，不需要 Identity Link
    headers = {"Authorization": f"Bearer {token}"}

    # 測試建立嬰兒
    baby_response = api_client.post(
        "/v1/babies",
        json={
            "name": "Test Baby",
            "gender": "male",
            "birth_date": "2024-01-01",
        },
        headers=headers,
    )
    assert baby_response.status_code == 201, (
        f"Expected 201, got {baby_response.status_code}: {baby_response.text}"
    )
    baby_data = baby_response.json()
    assert "baby_id" in baby_data
    baby_id = baby_data["baby_id"]

    # 查詢剛創建的嬰兒以取得完整數據
    get_baby_response = api_client.get(f"/v1/babies/{baby_id}", headers=headers)
    assert get_baby_response.status_code == 200
    full_baby_data = get_baby_response.json()
    assert full_baby_data["name"] == "Test Baby"

    # 5. 測試查詢嬰兒列表
    list_response = api_client.get("/v1/babies", headers=headers)
    assert list_response.status_code == 200
    babies = list_response.json()
    assert len(babies) == 1
    assert babies[0]["name"] == "Test Baby"
