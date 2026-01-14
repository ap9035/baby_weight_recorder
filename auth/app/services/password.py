"""密碼雜湊服務."""

import bcrypt
from passlib.context import CryptContext


def _get_pwd_context() -> CryptContext:
    """取得密碼雜湊上下文（延遲初始化以避免 bcrypt 版本檢測問題）."""
    return CryptContext(
        schemes=["bcrypt"],
        bcrypt__rounds=12,
        deprecated="auto",
    )


def hash_password(password: str) -> str:
    """雜湊密碼.

    Args:
        password: 原始密碼

    Returns:
        雜湊後的密碼
    """
    # 直接使用 bcrypt 避免 passlib 的初始化問題
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼.

    Args:
        plain_password: 原始密碼
        hashed_password: 雜湊後的密碼

    Returns:
        是否匹配
    """
    # 直接使用 bcrypt 避免 passlib 的初始化問題
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False
