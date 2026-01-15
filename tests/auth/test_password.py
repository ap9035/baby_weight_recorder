"""密碼雜湊服務測試."""

from auth.app.services.password import hash_password, verify_password


def test_hash_password():
    """測試密碼雜湊."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0
    assert hashed.startswith("$2b$")  # bcrypt hash format


def test_verify_password():
    """測試密碼驗證."""
    password = "test_password_123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_hash_different_passwords():
    """測試不同密碼產生不同雜湊."""
    password1 = "password1"
    password2 = "password2"

    hashed1 = hash_password(password1)
    hashed2 = hash_password(password2)

    assert hashed1 != hashed2


def test_hash_same_password_different_hash():
    """測試相同密碼每次雜湊都不同（salt 不同）."""
    password = "same_password"
    hashed1 = hash_password(password)
    hashed2 = hash_password(password)

    # 雜湊值應該不同（因為 salt）
    assert hashed1 != hashed2

    # 但驗證都應該成功
    assert verify_password(password, hashed1) is True
    assert verify_password(password, hashed2) is True
