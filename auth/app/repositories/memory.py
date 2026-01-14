"""In-Memory Repository 實作（開發/測試用）."""

from datetime import UTC, datetime

from ulid import ULID

from auth.app.models import UserCreate, UserInDB
from auth.app.repositories.base import UserRepository


class InMemoryUserRepository(UserRepository):
    """In-Memory 使用者 Repository."""

    def __init__(self) -> None:
        """初始化."""
        self._users: dict[str, UserInDB] = {}
        self._users_by_email: dict[str, str] = {}  # email -> user_id
        self._users_by_internal_id: dict[str, str] = {}  # internal_user_id -> user_id

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        """根據 ID 取得使用者."""
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> UserInDB | None:
        """根據 Email 取得使用者."""
        user_id = self._users_by_email.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None

    async def get_by_internal_id(self, internal_user_id: str) -> UserInDB | None:
        """根據內部使用者 ID 取得使用者."""
        user_id = self._users_by_internal_id.get(internal_user_id)
        if user_id:
            return self._users.get(user_id)
        return None

    async def create(self, user_create: UserCreate, hashed_password: str) -> UserInDB:
        """建立使用者."""
        # 檢查 email 是否已存在
        if await self.get_by_email(user_create.email):
            raise ValueError(f"Email {user_create.email} already exists")

        now = datetime.now(UTC)
        user_id = str(ULID())
        internal_user_id = str(ULID())

        user = UserInDB(
            id=user_id,
            internal_user_id=internal_user_id,
            display_name=user_create.display_name,
            email=user_create.email,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now,
        )

        self._users[user_id] = user
        self._users_by_email[user_create.email.lower()] = user_id
        self._users_by_internal_id[internal_user_id] = user_id

        return user

    async def close(self) -> None:
        """關閉 Repository（In-Memory 無需清理）."""
        pass
