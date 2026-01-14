"""邀請碼驗證服務."""

import logging

from auth.app.services.secrets import SecretService

logger = logging.getLogger(__name__)


class InviteCodeService:
    """邀請碼驗證服務."""

    def __init__(self, secret_service: SecretService):
        """初始化."""
        self._secret_service = secret_service
        self._cached_codes: list[str] | None = None

    def _get_codes(self) -> list[str]:
        """取得邀請碼列表（帶快取）."""
        if self._cached_codes is None:
            try:
                self._cached_codes = self._secret_service.get_invite_codes()
            except Exception as e:
                logger.warning(f"Failed to load invite codes: {e}, using empty list")
                self._cached_codes = []
        return self._cached_codes

    def validate(self, code: str) -> bool:
        """驗證邀請碼.

        Args:
            code: 邀請碼

        Returns:
            是否有效
        """
        codes = self._get_codes()
        # 不區分大小寫比較
        return code.strip().upper() in [c.upper() for c in codes]

    def refresh_cache(self) -> None:
        """重新載入邀請碼（清除快取）."""
        self._cached_codes = None
