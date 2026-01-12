"""Repository 基礎介面."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, TypeVar

from api.app.models import (
    Baby,
    BabyCreate,
    BabyUpdate,
    IdentityLink,
    Membership,
    MemberRole,
    User,
    UserCreate,
    Weight,
    WeightCreate,
    WeightUpdate,
)

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Repository 基礎類."""

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """取得單一資料."""
        pass

    @abstractmethod
    async def list(self, **filters: object) -> list[T]:
        """取得列表."""
        pass

    @abstractmethod
    async def create(self, data: object) -> T:
        """建立資料."""
        pass

    @abstractmethod
    async def update(self, id: str, data: object) -> T | None:
        """更新資料."""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """刪除資料."""
        pass


class IdentityLinkRepository(ABC):
    """身份對應 Repository."""

    @abstractmethod
    async def find_by_provider(
        self, provider_iss: str, provider_sub: str
    ) -> IdentityLink | None:
        """透過 IdP 身份查詢."""
        pass

    @abstractmethod
    async def create(
        self, provider_iss: str, provider_sub: str, internal_user_id: str
    ) -> IdentityLink:
        """建立身份對應."""
        pass


class UserRepository(ABC):
    """使用者 Repository."""

    @abstractmethod
    async def get(self, internal_user_id: str) -> User | None:
        """取得使用者."""
        pass

    @abstractmethod
    async def create(self, internal_user_id: str, data: UserCreate) -> User:
        """建立使用者."""
        pass


class BabyRepository(ABC):
    """嬰兒 Repository."""

    @abstractmethod
    async def get(self, baby_id: str) -> Baby | None:
        """取得嬰兒."""
        pass

    @abstractmethod
    async def create(self, data: BabyCreate) -> Baby:
        """建立嬰兒."""
        pass

    @abstractmethod
    async def update(self, baby_id: str, data: BabyUpdate) -> Baby | None:
        """更新嬰兒."""
        pass

    @abstractmethod
    async def delete(self, baby_id: str) -> bool:
        """刪除嬰兒."""
        pass

    @abstractmethod
    async def list_by_user(self, internal_user_id: str) -> list[Baby]:
        """取得使用者可存取的嬰兒列表."""
        pass


class MembershipRepository(ABC):
    """成員 Repository."""

    @abstractmethod
    async def get(self, baby_id: str, internal_user_id: str) -> Membership | None:
        """取得成員資格."""
        pass

    @abstractmethod
    async def create(
        self, baby_id: str, internal_user_id: str, role: MemberRole
    ) -> Membership:
        """建立成員資格."""
        pass

    @abstractmethod
    async def list_by_baby(self, baby_id: str) -> list[Membership]:
        """取得嬰兒的所有成員."""
        pass

    @abstractmethod
    async def list_by_user(self, internal_user_id: str) -> list[Membership]:
        """取得使用者的所有成員資格."""
        pass

    @abstractmethod
    async def delete(self, baby_id: str, internal_user_id: str) -> bool:
        """刪除成員資格."""
        pass


class WeightRepository(ABC):
    """體重 Repository."""

    @abstractmethod
    async def get(self, baby_id: str, weight_id: str) -> Weight | None:
        """取得體重紀錄."""
        pass

    @abstractmethod
    async def create(
        self, baby_id: str, data: WeightCreate, created_by: str
    ) -> Weight:
        """建立體重紀錄."""
        pass

    @abstractmethod
    async def update(
        self, baby_id: str, weight_id: str, data: WeightUpdate
    ) -> Weight | None:
        """更新體重紀錄."""
        pass

    @abstractmethod
    async def delete(self, baby_id: str, weight_id: str) -> bool:
        """刪除體重紀錄."""
        pass

    @abstractmethod
    async def list_by_baby(
        self,
        baby_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Weight]:
        """取得嬰兒的體重紀錄."""
        pass
