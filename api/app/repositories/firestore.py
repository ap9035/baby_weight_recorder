"""Firestore Repository 實作."""

from datetime import UTC, datetime
from typing import Any

from google.cloud.firestore_v1 import AsyncClient
from ulid import ULID

from api.app.models import (
    Baby,
    BabyCreate,
    BabyUpdate,
    Gender,
    IdentityLink,
    MemberRole,
    Membership,
    User,
    UserCreate,
    Weight,
    WeightCreate,
    WeightUpdate,
)
from api.app.repositories.base import (
    BabyRepository,
    IdentityLinkRepository,
    MembershipRepository,
    UserRepository,
    WeightRepository,
)


def generate_ulid() -> str:
    """產生 ULID."""
    return str(ULID())


def _to_datetime(value: Any) -> datetime:
    """將 Firestore timestamp 轉換為 datetime."""
    if value is None:
        return datetime.now(UTC)
    if isinstance(value, datetime):
        return value
    # Firestore DatetimeWithNanoseconds
    return value


class FirestoreIdentityLinkRepository(IdentityLinkRepository):
    """Firestore 身份對應 Repository."""

    def __init__(self, db: AsyncClient) -> None:
        """初始化."""
        self._db = db
        self._collection = "identity_links"

    async def find_by_provider(self, provider_iss: str, provider_sub: str) -> IdentityLink | None:
        """透過 IdP 身份查詢."""
        query = (
            self._db.collection(self._collection)
            .where("provider_iss", "==", provider_iss)
            .where("provider_sub", "==", provider_sub)
            .limit(1)
        )
        docs = query.stream()
        async for doc in docs:
            data = doc.to_dict()
            if data:
                return IdentityLink(
                    link_id=doc.id,
                    provider_iss=data["provider_iss"],
                    provider_sub=data["provider_sub"],
                    internal_user_id=data["internal_user_id"],
                    created_at=_to_datetime(data.get("created_at")),
                )
        return None

    async def create(
        self, provider_iss: str, provider_sub: str, internal_user_id: str
    ) -> IdentityLink:
        """建立身份對應."""
        link_id = generate_ulid()
        now = datetime.now(UTC)
        data = {
            "provider_iss": provider_iss,
            "provider_sub": provider_sub,
            "internal_user_id": internal_user_id,
            "created_at": now,
        }
        await self._db.collection(self._collection).document(link_id).set(data)
        return IdentityLink(
            link_id=link_id,
            provider_iss=provider_iss,
            provider_sub=provider_sub,
            internal_user_id=internal_user_id,
            created_at=now,
        )


class FirestoreUserRepository(UserRepository):
    """Firestore 使用者 Repository."""

    def __init__(self, db: AsyncClient) -> None:
        """初始化."""
        self._db = db
        self._collection = "users"

    async def get(self, internal_user_id: str) -> User | None:
        """取得使用者."""
        doc = await self._db.collection(self._collection).document(internal_user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if not data:
            return None
        return User(
            internal_user_id=doc.id,
            display_name=data["display_name"],
            email=data["email"],
            created_at=_to_datetime(data.get("created_at")),
        )

    async def get_by_email(self, email: str) -> User | None:
        """透過 Email 取得使用者."""
        query = self._db.collection(self._collection).where("email", "==", email).limit(1)
        docs = query.stream()
        async for doc in docs:
            data = doc.to_dict()
            if not data:
                continue
            return User(
                internal_user_id=doc.id,
                display_name=data["display_name"],
                email=data["email"],
                created_at=_to_datetime(data.get("created_at")),
            )
        return None

    async def create(self, internal_user_id: str, data: UserCreate) -> User:
        """建立使用者."""
        now = datetime.now(UTC)
        doc_data = {
            "display_name": data.display_name,
            "email": data.email,
            "created_at": now,
        }
        await self._db.collection(self._collection).document(internal_user_id).set(doc_data)
        return User(
            internal_user_id=internal_user_id,
            display_name=data.display_name,
            email=data.email,
            created_at=now,
        )


class FirestoreBabyRepository(BabyRepository):
    """Firestore 嬰兒 Repository."""

    def __init__(self, db: AsyncClient) -> None:
        """初始化."""
        self._db = db
        self._collection = "babies"

    async def get(self, baby_id: str) -> Baby | None:
        """取得嬰兒."""
        doc = await self._db.collection(self._collection).document(baby_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if not data:
            return None
        return Baby(
            baby_id=doc.id,
            name=data["name"],
            birth_date=data["birth_date"],
            gender=Gender(data["gender"]),
            created_at=_to_datetime(data.get("created_at")),
        )

    async def create(self, data: BabyCreate) -> Baby:
        """建立嬰兒."""
        baby_id = generate_ulid()
        now = datetime.now(UTC)
        doc_data = {
            "name": data.name,
            "birth_date": data.birth_date.isoformat(),
            "gender": data.gender.value,
            "created_at": now,
        }
        await self._db.collection(self._collection).document(baby_id).set(doc_data)
        return Baby(
            baby_id=baby_id,
            name=data.name,
            birth_date=data.birth_date,
            gender=data.gender,
            created_at=now,
        )

    async def update(self, baby_id: str, data: BabyUpdate) -> Baby | None:
        """更新嬰兒."""
        doc_ref = self._db.collection(self._collection).document(baby_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None

        update_data: dict[str, Any] = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.birth_date is not None:
            update_data["birth_date"] = data.birth_date.isoformat()
        if data.gender is not None:
            update_data["gender"] = data.gender.value

        if update_data:
            await doc_ref.update(update_data)

        return await self.get(baby_id)

    async def delete(self, baby_id: str) -> bool:
        """刪除嬰兒."""
        doc_ref = self._db.collection(self._collection).document(baby_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        await doc_ref.delete()
        return True

    async def list_by_user(self, internal_user_id: str) -> list[Baby]:
        """取得使用者可存取的嬰兒列表.

        透過查詢 memberships subcollection 來找到所有嬰兒.
        """
        # 使用 collection group query 查詢所有 members subcollection
        query = self._db.collection_group("members").where(
            "internal_user_id", "==", internal_user_id
        )

        babies: list[Baby] = []
        async for doc in query.stream():
            # doc.reference.parent.parent 是 baby document
            baby_ref = doc.reference.parent.parent
            if baby_ref:
                baby = await self.get(baby_ref.id)
                if baby:
                    babies.append(baby)

        return babies


class FirestoreMembershipRepository(MembershipRepository):
    """Firestore 成員 Repository.

    memberships 存放在 babies/{babyId}/members/{internalUserId}
    """

    def __init__(self, db: AsyncClient) -> None:
        """初始化."""
        self._db = db

    def _get_member_ref(self, baby_id: str, internal_user_id: str) -> Any:  # AsyncDocumentReference
        """取得成員 document reference."""
        return (
            self._db.collection("babies")
            .document(baby_id)
            .collection("members")
            .document(internal_user_id)
        )

    async def get(self, baby_id: str, internal_user_id: str) -> Membership | None:
        """取得成員資格."""
        doc = await self._get_member_ref(baby_id, internal_user_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if not data:
            return None
        return Membership(
            baby_id=baby_id,
            internal_user_id=internal_user_id,
            role=MemberRole(data["role"]),
            joined_at=_to_datetime(data.get("joined_at")),
        )

    async def create(self, baby_id: str, internal_user_id: str, role: MemberRole) -> Membership:
        """建立成員資格."""
        now = datetime.now(UTC)
        data = {
            "internal_user_id": internal_user_id,  # 冗餘存放，方便 collection group query
            "role": role.value,
            "joined_at": now,
        }
        await self._get_member_ref(baby_id, internal_user_id).set(data)
        return Membership(
            baby_id=baby_id,
            internal_user_id=internal_user_id,
            role=role,
            joined_at=now,
        )

    async def list_by_baby(self, baby_id: str) -> list[Membership]:
        """取得嬰兒的所有成員."""
        query = self._db.collection("babies").document(baby_id).collection("members")
        memberships: list[Membership] = []
        async for doc in query.stream():
            data = doc.to_dict()
            if data:
                memberships.append(
                    Membership(
                        baby_id=baby_id,
                        internal_user_id=doc.id,
                        role=MemberRole(data["role"]),
                        joined_at=_to_datetime(data.get("joined_at")),
                    )
                )
        return memberships

    async def list_by_user(self, internal_user_id: str) -> list[Membership]:
        """取得使用者的所有成員資格."""
        query = self._db.collection_group("members").where(
            "internal_user_id", "==", internal_user_id
        )
        memberships: list[Membership] = []
        async for doc in query.stream():
            data = doc.to_dict()
            if data:
                # 從 path 取得 baby_id: babies/{babyId}/members/{userId}
                baby_id = doc.reference.parent.parent.id if doc.reference.parent.parent else ""
                memberships.append(
                    Membership(
                        baby_id=baby_id,
                        internal_user_id=doc.id,
                        role=MemberRole(data["role"]),
                        joined_at=_to_datetime(data.get("joined_at")),
                    )
                )
        return memberships

    async def delete(self, baby_id: str, internal_user_id: str) -> bool:
        """刪除成員資格."""
        doc_ref = self._get_member_ref(baby_id, internal_user_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        await doc_ref.delete()
        return True


class FirestoreWeightRepository(WeightRepository):
    """Firestore 體重 Repository.

    weights 存放在 babies/{babyId}/weights/{weightId}
    """

    def __init__(self, db: AsyncClient) -> None:
        """初始化."""
        self._db = db

    def _get_weights_collection(self, baby_id: str) -> Any:  # AsyncCollectionReference
        """取得體重 collection reference."""
        return self._db.collection("babies").document(baby_id).collection("weights")

    async def get(self, baby_id: str, weight_id: str) -> Weight | None:
        """取得體重紀錄."""
        doc = await self._get_weights_collection(baby_id).document(weight_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if not data:
            return None
        return Weight(
            weight_id=doc.id,
            baby_id=baby_id,
            timestamp=_to_datetime(data["timestamp"]),
            weight_g=data["weight_g"],
            note=data.get("note"),
            created_by=data["created_by"],
            created_at=_to_datetime(data.get("created_at")),
            updated_at=_to_datetime(data.get("updated_at")) if data.get("updated_at") else None,
        )

    async def create(self, baby_id: str, data: WeightCreate, created_by: str) -> Weight:
        """建立體重紀錄."""
        weight_id = generate_ulid()
        now = datetime.now(UTC)
        doc_data: dict[str, Any] = {
            "timestamp": data.timestamp,
            "weight_g": data.weight_g,
            "created_by": created_by,
            "created_at": now,
        }
        if data.note:
            doc_data["note"] = data.note

        await self._get_weights_collection(baby_id).document(weight_id).set(doc_data)
        return Weight(
            weight_id=weight_id,
            baby_id=baby_id,
            timestamp=data.timestamp,
            weight_g=data.weight_g,
            note=data.note,
            created_by=created_by,
            created_at=now,
            updated_at=None,
        )

    async def update(self, baby_id: str, weight_id: str, data: WeightUpdate) -> Weight | None:
        """更新體重紀錄."""
        doc_ref = self._get_weights_collection(baby_id).document(weight_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None

        update_data: dict[str, Any] = {"updated_at": datetime.now(UTC)}
        if data.timestamp is not None:
            update_data["timestamp"] = data.timestamp
        if data.weight_g is not None:
            update_data["weight_g"] = data.weight_g
        if data.note is not None:
            update_data["note"] = data.note

        await doc_ref.update(update_data)
        return await self.get(baby_id, weight_id)

    async def delete(self, baby_id: str, weight_id: str) -> bool:
        """刪除體重紀錄."""
        doc_ref = self._get_weights_collection(baby_id).document(weight_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        await doc_ref.delete()
        return True

    async def list_by_baby(
        self,
        baby_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Weight]:
        """取得嬰兒的體重紀錄."""
        query: Any = self._get_weights_collection(baby_id)

        if from_date:
            query = query.where("timestamp", ">=", from_date)
        if to_date:
            query = query.where("timestamp", "<=", to_date)

        query = query.order_by("timestamp")

        weights: list[Weight] = []
        async for doc in query.stream():
            data = doc.to_dict()
            if data:
                weights.append(
                    Weight(
                        weight_id=doc.id,
                        baby_id=baby_id,
                        timestamp=_to_datetime(data["timestamp"]),
                        weight_g=data["weight_g"],
                        note=data.get("note"),
                        created_by=data["created_by"],
                        created_at=_to_datetime(data.get("created_at")),
                        updated_at=_to_datetime(data.get("updated_at"))
                        if data.get("updated_at")
                        else None,
                    )
                )
        return weights


class FirestoreRepositories:
    """統一管理所有 Firestore Repositories."""

    def __init__(self, project_id: str, database: str = "(default)") -> None:
        """初始化所有 repositories.

        Args:
            project_id: GCP Project ID
            database: Firestore database name（預設為 "(default)"）
        """
        self._db = AsyncClient(project=project_id, database=database)
        self.identity_links = FirestoreIdentityLinkRepository(self._db)
        self.users = FirestoreUserRepository(self._db)
        self.babies = FirestoreBabyRepository(self._db)
        self.memberships = FirestoreMembershipRepository(self._db)
        self.weights = FirestoreWeightRepository(self._db)

    async def close(self) -> None:
        """關閉 Firestore client."""
        self._db.close()
