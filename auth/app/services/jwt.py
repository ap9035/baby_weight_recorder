"""JWT 服務."""

import base64
import hashlib
import logging
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from auth.app.config import Settings, get_settings
from auth.app.services.secrets import SecretService

logger = logging.getLogger(__name__)


class JWTService:
    """JWT 服務."""

    def __init__(self, settings: Settings, secret_service: SecretService):
        """初始化."""
        self._settings = settings
        self._secret_service = secret_service
        self._private_key: rsa.RSAPrivateKey | None = None

    def _get_private_key(self) -> rsa.RSAPrivateKey:
        """取得 JWT 私鑰（延遲載入並快取）."""
        if self._private_key is None:
            try:
                key_pem = self._secret_service.get_jwt_private_key()
                # 如果為空字串，表示使用臨時私鑰（本地開發模式）
                if not key_pem or key_pem.strip() == "":
                    raise ValueError("Empty key, using temporary key")
                self._private_key = serialization.load_pem_private_key(
                    key_pem.encode("utf-8") if isinstance(key_pem, str) else key_pem,
                    password=None,
                )
            except (ValueError, Exception) as e:
                logger.warning(f"Failed to load JWT private key: {e}")
                # 開發模式或本地模式：生成臨時私鑰
                if (
                    self._settings.environment == "dev"
                    or self._settings.gcp_project_id == "local-dev"
                ):
                    logger.warning("Using temporary RSA key for dev/local mode")
                    self._private_key = rsa.generate_private_key(
                        public_exponent=65537, key_size=2048
                    )
                else:
                    raise
        return self._private_key

    def create_token(
        self,
        subject: str,
        email: str | None = None,
        internal_user_id: str | None = None,
        expires_in_seconds: int | None = None,
    ) -> str:
        """建立 JWT Token.

        Args:
            subject: Subject (通常是 provider_sub)
            email: Email
            internal_user_id: 內部使用者 ID
            expires_in_seconds: 過期時間（秒），預設使用設定值

        Returns:
            JWT Token 字串
        """
        now = datetime.now(UTC)
        exp = now + timedelta(
            seconds=expires_in_seconds or self._settings.jwt_expiration_seconds
        )

        payload = {
            "iss": self._settings.jwt_issuer,
            "sub": subject,
            "aud": self._settings.jwt_audience,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
        }

        if email:
            payload["email"] = email

        if internal_user_id:
            payload["internal_user_id"] = internal_user_id

        private_key = self._get_private_key()
        public_key = private_key.public_key()
        kid = self._calculate_kid(public_key)
        
        # 添加 kid 到 header
        headers = {"kid": kid}
        
        return jwt.encode(
            payload,
            private_key,
            algorithm=self._settings.jwt_algorithm,
            headers=headers,
        )

    def _get_public_key(self) -> rsa.RSAPublicKey:
        """取得公鑰."""
        private_key = self._get_private_key()
        return private_key.public_key()

    def _calculate_kid(self, public_key: rsa.RSAPublicKey) -> str:
        """計算 Key ID (kid).

        Args:
            public_key: RSA 公鑰

        Returns:
            Key ID（使用公鑰 DER 編碼的 SHA-256 哈希前 8 字節的 base64url 編碼）
        """
        # 將公鑰序列化為 DER 格式
        public_key_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # 計算 SHA-256 哈希
        hash_bytes = hashlib.sha256(public_key_der).digest()
        # 取前 8 字節並進行 base64url 編碼
        kid_bytes = hash_bytes[:8]
        kid = base64.urlsafe_b64encode(kid_bytes).decode("utf-8").rstrip("=")
        return kid

    def _int_to_base64url(self, value: int) -> str:
        """將整數轉換為 base64url 編碼的字串.

        Args:
            value: 要編碼的整數

        Returns:
            base64url 編碼的字串（無填充）
        """
        # 計算需要的字節數
        byte_length = (value.bit_length() + 7) // 8
        # 轉換為字節
        value_bytes = value.to_bytes(byte_length, byteorder="big")
        # base64url 編碼並移除填充
        return base64.urlsafe_b64encode(value_bytes).decode("utf-8").rstrip("=")

    def get_jwks(self) -> dict[str, list[dict[str, str]]]:
        """取得 JWKS (JSON Web Key Set).

        Returns:
            JWKS 格式的字典，包含 keys 數組
        """
        public_key = self._get_public_key()
        public_numbers = public_key.public_numbers()

        # 計算 Key ID
        kid = self._calculate_kid(public_key)

        # 構建 JWK
        jwk = {
            "kty": "RSA",
            "use": "sig",
            "kid": kid,
            "n": self._int_to_base64url(public_numbers.n),  # 模數
            "e": self._int_to_base64url(public_numbers.e),  # 指數
            "alg": self._settings.jwt_algorithm,
        }

        return {"keys": [jwk]}
