"""認證 API 測試."""

import pytest
from fastapi.testclient import TestClient

from auth.app.main import app
from auth.app.models import UserCreate
from auth.app.repositories.memory import InMemoryUserRepository


@pytest.fixture
def client():
    """建立測試客戶端."""
    # 設定測試用的 repository
    user_repo = InMemoryUserRepository()
    app.state.user_repo = user_repo
    return TestClient(app)


@pytest.fixture
def sample_user_create():
    """建立測試用的 UserCreate."""
    return UserCreate(
        display_name="Test User",
        email="test@example.com",
        password="test_password_123",
        invite_code="TEST_CODE",
    )


def test_register_success(client, sample_user_create, monkeypatch):
    """測試成功註冊."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    response = client.post("/auth/register", json=sample_user_create.model_dump())
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == sample_user_create.email
    assert data["display_name"] == sample_user_create.display_name
    assert "id" in data
    assert "internal_user_id" in data
    assert "hashed_password" not in data  # 不應返回密碼


def test_register_invalid_invite_code(client, sample_user_create, monkeypatch):
    """測試無效邀請碼."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            # 只接受 TEST_CODE
            return code.strip().upper() == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        # 需要傳入 SecretService，但我們會覆蓋 validate 方法
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    # 使用無效的邀請碼
    invalid_data = sample_user_create.model_dump()
    invalid_data["invite_code"] = "INVALID_CODE"

    response = client.post("/auth/register", json=invalid_data)
    assert response.status_code == 400
    assert "Invalid invite code" in response.json()["detail"]


def test_register_duplicate_email(client, sample_user_create, monkeypatch):
    """測試重複 Email."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    # 第一次註冊
    response1 = client.post("/auth/register", json=sample_user_create.model_dump())
    assert response1.status_code == 201

    # 第二次註冊相同 Email
    response2 = client.post("/auth/register", json=sample_user_create.model_dump())
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"]


def test_login_success(client, sample_user_create, monkeypatch):
    """測試成功登入."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.jwt import JWTService
    from auth.app.services.secrets import SecretService

    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    class MockJWTService(JWTService):
        def create_token(self, *args, **kwargs) -> str:
            return "mock_jwt_token"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    def get_mock_jwt_service(settings, secret_service):
        return MockJWTService(settings, secret_service)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)
    monkeypatch.setattr("auth.app.dependencies.get_jwt_service", get_mock_jwt_service)

    # 先註冊
    register_response = client.post(
        "/auth/register", json=sample_user_create.model_dump()
    )
    assert register_response.status_code == 201

    # 登入
    login_response = client.post(
        "/auth/token",
        json={
            "email": sample_user_create.email,
            "password": sample_user_create.password,
        },
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    # Token 應該是有效的 JWT（即使 mock 失敗，實際的 JWT Service 也會生成有效 token）
    assert len(data["access_token"]) > 0
    # 驗證是 JWT 格式（三個部分用 . 分隔）
    assert len(data["access_token"].split(".")) == 3


def test_login_invalid_email(client):
    """測試無效 Email 登入."""
    response = client.post(
        "/auth/token",
        json={"email": "nonexistent@example.com", "password": "password"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_invalid_password(client, sample_user_create, monkeypatch):
    """測試無效密碼登入."""
    from auth.app.services.invite import InviteCodeService
    from auth.app.services.secrets import SecretService

    class MockInviteService(InviteCodeService):
        def validate(self, code: str) -> bool:
            return code == "TEST_CODE"

    def get_mock_invite_service(*args, **kwargs):
        mock_secret = SecretService("local-dev")
        return MockInviteService(mock_secret)

    monkeypatch.setattr("auth.app.dependencies.get_invite_service", get_mock_invite_service)

    # 先註冊
    register_response = client.post(
        "/auth/register", json=sample_user_create.model_dump()
    )
    assert register_response.status_code == 201

    # 使用錯誤密碼登入
    login_response = client.post(
        "/auth/token",
        json={
            "email": sample_user_create.email,
            "password": "wrong_password",
        },
    )
    assert login_response.status_code == 401
    assert "Invalid email or password" in login_response.json()["detail"]
