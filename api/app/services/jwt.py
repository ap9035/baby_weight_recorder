"""JWT 驗證服務."""

import logging
from typing import Any

import httpx
from jose import jwt
from jose.exceptions import JWTError

from api.app.config import Settings

logger = logging.getLogger(__name__)


class JWTVerificationService:
    """JWT 驗證服務."""

    def __init__(self, settings: Settings):
        """初始化."""
        self._settings = settings
        self._jwks_cache: dict[str, Any] | None = None

    async def _fetch_jwks(self) -> dict[str, Any]:
        """取得 JWKS（帶快取）."""
        if self._jwks_cache is None:
            jwks_url = self._settings.effective_jwks_url
            logger.info(f"Fetching JWKS from {jwks_url}")

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(jwks_url, timeout=5.0)
                    response.raise_for_status()
                    self._jwks_cache = response.json()
                    logger.info(f"JWKS fetched successfully: {len(self._jwks_cache.get('keys', []))} keys")
                except Exception as e:
                    logger.error(f"Failed to fetch JWKS from {jwks_url}: {e}")
                    raise

        return self._jwks_cache

    async def verify_token(self, token: str) -> dict[str, Any]:
        """驗證 JWT Token.

        Args:
            token: JWT Token 字串

        Returns:
            JWT Payload（claims）

        Raises:
            JWTError: Token 無效或驗證失敗
        """
        # 取得 JWKS
        jwks = await self._fetch_jwks()

        # 取得未驗證的 header（需要 kid）
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # 如果有 kid，記錄日誌（但不強制要求匹配，讓 python-jose 自動處理）
        if kid:
            key_found = any(key.get("kid") == kid for key in jwks.get("keys", []))
            if not key_found:
                logger.warning(
                    f"Token kid '{kid}' not found in JWKS, "
                    f"but will try all keys in JWKS for verification"
                )

        # 驗證並解碼 token（python-jose 會自動從 JWKS 中找到對應的 key）
        # 如果 kid 不匹配，python-jose 會嘗試所有 key 直到找到能驗證的
        payload = jwt.decode(
            token,
            jwks,  # 傳入完整的 JWKS 字典
            algorithms=["RS256"],
            audience=self._settings.auth_audience,
            issuer=self._settings.auth_issuer,
        )

        return payload

    def clear_cache(self) -> None:
        """清除 JWKS 快取（用於測試或重新載入）."""
        self._jwks_cache = None
