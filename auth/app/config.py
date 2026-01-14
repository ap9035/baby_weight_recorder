"""Auth 服務設定."""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # JWT 設定
    jwt_issuer: str = "http://localhost:8082"
    jwt_audience: str = "baby-weight-api"
    jwt_algorithm: str = "RS256"
    jwt_expiration_seconds: int = 3600  # 1 小時

    # Secret Manager（JWT 私鑰）
    jwt_private_key_secret_id: str = "jwt-private-key-dev"
    jwt_private_key_secret_version: str = "latest"

    # 邀請碼設定
    invite_codes_secret_id: str = "invite-codes-dev"
    invite_codes_secret_version: str = "latest"

    # 密碼設定
    password_min_length: int = 8
    password_max_length: int = 128

    # CORS
    cors_origins: list[str] = ["*"]

    @property
    def use_firestore(self) -> bool:
        """是否使用 Firestore."""
        return self.repository_mode == RepositoryMode.FIRESTORE


@lru_cache
def get_settings() -> Settings:
    """取得設定（cached）."""
    return Settings()
