"""Secret Manager 服務."""

import json
import logging
import os

from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretService:
    """Secret Manager 服務."""

    def __init__(self, project_id: str):
        """初始化."""
        self._project_id = project_id
        self._client: secretmanager.SecretManagerServiceClient | None = None

    def _get_client(self) -> secretmanager.SecretManagerServiceClient:
        """取得 Secret Manager 客戶端（延遲初始化）."""
        if self._client is None:
            self._client = secretmanager.SecretManagerServiceClient()
        return self._client

    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """取得 Secret 值.

        Args:
            secret_id: Secret ID（完整名稱或簡短名稱）
            version: Secret 版本，預設 "latest"

        Returns:
            Secret 值（字串）
        """
        # 如果 secret_id 是完整名稱（projects/.../secrets/...），直接使用
        # 否則構建完整名稱
        if secret_id.startswith("projects/"):
            name = f"{secret_id}/versions/{version}"
        else:
            name = f"projects/{self._project_id}/secrets/{secret_id}/versions/{version}"

        try:
            response = self._get_client().access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to get secret {secret_id}: {e}")
            raise

    def get_jwt_private_key(self) -> str:
        """取得 JWT 私鑰.

        Returns:
            JWT 私鑰（PEM 格式）

        Raises:
            ValueError: 無法取得私鑰（非開發模式）
        """
        # 優先從環境變數讀取（Cloud Run 會自動注入）
        env_key = os.getenv("JWT_PRIVATE_KEY")
        if env_key:
            return env_key

        # 本地開發模式：返回空字串（JWTService 會生成臨時私鑰）
        if self._project_id == "local-dev":
            logger.info("Using temporary JWT key for local development")
            return ""

        # 否則從 Secret Manager 讀取
        try:
            secret_id = os.getenv("JWT_PRIVATE_KEY_SECRET_ID", "jwt-private-key-dev")
            return self.get_secret(secret_id)
        except Exception as e:
            logger.warning(f"Failed to load JWT private key from Secret Manager: {e}")
            # 開發模式允許使用臨時私鑰
            if os.getenv("ENVIRONMENT", "dev") == "dev":
                return ""
            raise

    def get_invite_codes(self) -> list[str]:
        """取得邀請碼列表.

        Returns:
            邀請碼列表
        """
        # 優先從環境變數讀取（Cloud Run 會自動注入）
        env_codes = os.getenv("INVITE_CODES")
        if env_codes:
            try:
                return json.loads(env_codes)
            except json.JSONDecodeError:
                # 如果不是 JSON，假設是逗號分隔的字串
                return [code.strip() for code in env_codes.split(",") if code.strip()]

        # 本地開發模式：使用預設邀請碼
        if self._project_id == "local-dev":
            logger.info("Using default invite codes for local development")
            return ["DEV_CODE", "TEST_CODE"]

        # 否則從 Secret Manager 讀取
        try:
            secret_id = os.getenv("INVITE_CODES_SECRET_ID", "invite-codes-dev")
            codes_str = self.get_secret(secret_id)
            try:
                return json.loads(codes_str)
            except json.JSONDecodeError:
                # 如果不是 JSON，假設是逗號分隔的字串
                return [code.strip() for code in codes_str.split(",") if code.strip()]
        except Exception as e:
            logger.warning(f"Failed to load invite codes from Secret Manager: {e}, using defaults")
            return ["DEV_CODE", "TEST_CODE"]
