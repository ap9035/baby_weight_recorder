"""Repository 抽象介面."""

from abc import ABC, abstractmethod

from auth.app.models import User, UserCreate, UserInDB


class UserRepository(ABC):
    """使用者 Repository 介面."""

    @abstractmethod
    async def get_by_id(self, user_id: str) -> UserInDB | None:
        """根據 ID 取得使用者."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> UserInDB | None:
        """根據 Email 取得使用者."""
        pass

    @abstractmethod
    async def get_by_internal_id(self, internal_user_id: str) -> UserInDB | None:
        """根據內部使用者 ID 取得使用者."""
        pass

    @abstractmethod
    async def create(self, user_create: UserCreate, hashed_password: str) -> UserInDB:
        """建立使用者."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """關閉 Repository（清理資源）."""
        pass
