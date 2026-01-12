"""API 服務設定."""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthMode(str, Enum):
    """認證模式."""

    DEV = "dev"  # 開發模式，使用固定 token
    LOCAL_OIDC = "local-oidc"  # 本地 Auth Service
    OIDC = "oidc"  # 生產模式，真實 OIDC


class RepositoryMode(str, Enum):
    """Repository 模式."""

    MEMORY = "memory"  # In-Memory（開發/測試）
    FIRESTORE = "firestore"  # Firestore（Emulator 或真實）


class Settings(BaseSettings):
    """應用程式設定."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # 基本設定
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    port: int = 8080

    # GCP 設定
    gcp_project_id: str = "local-dev"
    firestore_database: str = "(default)"

    # Repository 設定
    repository_mode: RepositoryMode = RepositoryMode.MEMORY

    # Auth 設定
    auth_mode: AuthMode = AuthMode.DEV
    auth_issuer: str = "http://localhost:8082"
    auth_audience: str = "baby-weight-api"
    auth_jwks_url: str = ""

    # Dev 模式設定（AUTH_MODE=dev 時使用）
    dev_user_id: str = "dev-user"
    dev_internal_user_id: str = "01DEV000000000000000000000"

    # CORS
    cors_origins: list[str] = ["*"]

    @property
    def is_dev_auth(self) -> bool:
        """是否為開發認證模式."""
        return self.auth_mode == AuthMode.DEV

    @property
    def use_firestore(self) -> bool:
        """是否使用 Firestore."""
        return self.repository_mode == RepositoryMode.FIRESTORE

    @property
    def effective_jwks_url(self) -> str:
        """取得有效的 JWKS URL."""
        if self.auth_jwks_url:
            return self.auth_jwks_url
        return f"{self.auth_issuer}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    """取得設定（cached）."""
    return Settings()
