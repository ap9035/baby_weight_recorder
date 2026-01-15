"""Firestore Repository 實作."""

from datetime import UTC, datetime
from typing import Any

from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient
from ulid import ULID

from auth.app.models import UserCreate, UserInDB
from auth.app.repositories.base import UserRepository


def _convert_timestamp_to_datetime(value: Any) -> datetime:
    """將 Firestore Timestamp 轉換為 datetime."""
    if isinstance(value, firestore.SERVER_TIMESTAMP):
        return datetime.now(UTC)
    if isinstance(value, datetime):
        return value
    # Firestore Timestamp 對象
    if hasattr(value, "timestamp"):
        # 如果有 timestamp() 方法，轉換為 datetime
        return datetime.fromtimestamp(value.timestamp(), tz=UTC)
    if hasattr(value, "astimezone"):
        return value.astimezone(UTC)
    raise TypeError(f"Cannot convert {type(value)} to datetime")


class FirestoreUserRepository(UserRepository):
    """Firestore 使用者 Repository."""

    def __init__(self, db: AsyncClient, collection_name: str = "users"):
        """初始化."""
        self._db = db
        self._collection = db.collection(collection_name)

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        """根據 ID 取得使用者."""
        doc = await self._collection.document(user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data:
            return UserInDB(
                id=doc.id,
                internal_user_id=data["internal_user_id"],
                display_name=data["display_name"],
                email=data["email"],
                hashed_password=data["hashed_password"],
                created_at=_convert_timestamp_to_datetime(data["created_at"]),
                updated_at=_convert_timestamp_to_datetime(data["updated_at"]),
            )
        return None

    async def get_by_email(self, email: str) -> UserInDB | None:
        """根據 Email 取得使用者."""
        query = self._collection.where("email", "==", email.lower()).limit(1)
        docs = [doc async for doc in query.stream()]
        if not docs:
            return None
        doc = docs[0]
        data = doc.to_dict()
        if data:
            return UserInDB(
                id=doc.id,
                internal_user_id=data["internal_user_id"],
                display_name=data["display_name"],
                email=data["email"],
                hashed_password=data["hashed_password"],
                created_at=_convert_timestamp_to_datetime(data["created_at"]),
                updated_at=_convert_timestamp_to_datetime(data["updated_at"]),
            )
        return None

    async def get_by_internal_id(self, internal_user_id: str) -> UserInDB | None:
        """根據內部使用者 ID 取得使用者."""
        query = self._collection.where("internal_user_id", "==", internal_user_id).limit(1)
        docs = [doc async for doc in query.stream()]
        if not docs:
            return None
        doc = docs[0]
        data = doc.to_dict()
        if data:
            return UserInDB(
                id=doc.id,
                internal_user_id=data["internal_user_id"],
                display_name=data["display_name"],
                email=data["email"],
                hashed_password=data["hashed_password"],
                created_at=_convert_timestamp_to_datetime(data["created_at"]),
                updated_at=_convert_timestamp_to_datetime(data["updated_at"]),
            )
        return None

    async def create(self, user_create: UserCreate, hashed_password: str) -> UserInDB:
        """建立使用者."""
        # 檢查 email 是否已存在
        existing = await self.get_by_email(user_create.email)
        if existing:
            raise ValueError(f"Email {user_create.email} already exists")

        now = datetime.now(UTC)
        user_id = str(ULID())
        internal_user_id = str(ULID())

        user_data = {
            "internal_user_id": internal_user_id,
            "display_name": user_create.display_name,
            "email": user_create.email.lower(),  # 統一轉為小寫
            "hashed_password": hashed_password,
            "created_at": now,
            "updated_at": now,
        }

        await self._collection.document(user_id).set(user_data)

        return UserInDB(
            id=user_id,
            internal_user_id=internal_user_id,
            display_name=user_create.display_name,
            email=user_create.email,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now,
        )

    async def close(self) -> None:
        """關閉 Repository（Firestore AsyncClient 無需手動關閉）."""
        pass
