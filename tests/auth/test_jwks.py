"""JWKS 端點測試."""

import base64

import pytest
from fastapi.testclient import TestClient

from auth.app.main import app
from auth.app.repositories.memory import InMemoryUserRepository


@pytest.fixture
def client():
    """建立測試客戶端."""
    # 設定測試用的 repository
    user_repo = InMemoryUserRepository()
    app.state.user_repo = user_repo
    return TestClient(app)


def test_jwks_endpoint(client):
    """測試 JWKS 端點返回正確格式."""
    response = client.get("/.well-known/jwks.json")
    assert response.status_code == 200

    data = response.json()
    assert "keys" in data
    assert isinstance(data["keys"], list)
    assert len(data["keys"]) > 0

    # 檢查第一個 key 的格式
    key = data["keys"][0]
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert "kid" in key
    assert "n" in key  # 模數
    assert "e" in key  # 指數
    assert key["alg"] == "RS256"


def test_jwks_key_format(client):
    """測試 JWKS 中的 key 格式正確."""
    response = client.get("/.well-known/jwks.json")
    assert response.status_code == 200

    data = response.json()
    key = data["keys"][0]

    # 驗證 n 和 e 是有效的 base64url 編碼
    try:
        # 添加填充並解碼
        n_padded = key["n"] + "=" * (4 - len(key["n"]) % 4)
        e_padded = key["e"] + "=" * (4 - len(key["e"]) % 4)
        base64.urlsafe_b64decode(n_padded)
        base64.urlsafe_b64decode(e_padded)
    except Exception as e:
        pytest.fail(f"Invalid base64url encoding: {e}")


def test_jwks_has_kid(client):
    """測試 JWKS 包含有效的 kid."""
    response = client.get("/.well-known/jwks.json")
    assert response.status_code == 200

    data = response.json()
    key = data["keys"][0]

    # kid 應該存在且為非空字串
    assert "kid" in key
    assert isinstance(key["kid"], str)
    assert len(key["kid"]) > 0

    # 注意：在本地開發模式下，每次可能生成新的臨時私鑰，
    # 所以 kid 可能不同，這是正常的


def test_jwks_contains_valid_rsa_key(client):
    """測試 JWKS 包含有效的 RSA 公鑰信息."""
    response = client.get("/.well-known/jwks.json")
    assert response.status_code == 200

    data = response.json()
    key = data["keys"][0]

    # 驗證 n 和 e 存在且為字串
    assert isinstance(key["n"], str)
    assert isinstance(key["e"], str)
    assert len(key["n"]) > 0
    assert len(key["e"]) > 0

    # 驗證 base64url 編碼格式（無填充或正確填充）
    # n 和 e 應該是 base64url 編碼的整數
    try:
        # 嘗試解碼 n（模數，應該很長）
        n_padded = key["n"] + "=" * (4 - len(key["n"]) % 4)
        n_bytes = base64.urlsafe_b64decode(n_padded)
        assert len(n_bytes) > 0

        # 嘗試解碼 e（指數，通常很短，通常是 65537 = 0x010001）
        e_padded = key["e"] + "=" * (4 - len(key["e"]) % 4)
        e_bytes = base64.urlsafe_b64decode(e_padded)
        assert len(e_bytes) > 0
    except Exception as e:
        pytest.fail(f"Invalid base64url encoding in JWKS: {e}")
