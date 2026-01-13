"""In-Memory Repository 實作（開發/測試用）."""

from datetime import UTC, datetime

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


class InMemoryIdentityLinkRepository(IdentityLinkRepository):
    """In-Memory 身份對應 Repository."""

    def __init__(self) -> None:
        """初始化."""
        self._links: dict[str, IdentityLink] = {}

    async def find_by_provider(self, provider_iss: str, provider_sub: str) -> IdentityLink | None:
        """透過 IdP 身份查詢."""
        for link in self._links.values():
            if link.provider_iss == provider_iss and link.provider_sub == provider_sub:
                return link
        return None

    async def create(
        self, provider_iss: str, provider_sub: str, internal_user_id: str
    ) -> IdentityLink:
        """建立身份對應."""
        link_id = generate_ulid()
        link = IdentityLink(
            link_id=link_id,
            provider_iss=provider_iss,
            provider_sub=provider_sub,
            internal_user_id=internal_user_id,
            created_at=datetime.now(UTC),
        )
        self._links[link_id] = link
        return link


class InMemoryUserRepository(UserRepository):
    """In-Memory 使用者 Repository."""

    def __init__(self) -> None:
        """初始化."""
        self._users: dict[str, User] = {}

    async def get(self, internal_user_id: str) -> User | None:
        """取得使用者."""
        return self._users.get(internal_user_id)

    async def create(self, internal_user_id: str, data: UserCreate) -> User:
        """建立使用者."""
        user = User(
            internal_user_id=internal_user_id,
            display_name=data.display_name,
            email=data.email,
            created_at=datetime.now(UTC),
        )
        self._users[internal_user_id] = user
        return user


class InMemoryBabyRepository(BabyRepository):
    """In-Memory 嬰兒 Repository."""

    def __init__(self, membership_repo: "InMemoryMembershipRepository") -> None:
        """初始化."""
        self._babies: dict[str, Baby] = {}
        self._membership_repo = membership_repo

    async def get(self, baby_id: str) -> Baby | None:
        """取得嬰兒."""
        return self._babies.get(baby_id)

    async def create(self, data: BabyCreate) -> Baby:
        """建立嬰兒."""
        baby_id = generate_ulid()
        baby = Baby(
            baby_id=baby_id,
            name=data.name,
            birth_date=data.birth_date,
            gender=data.gender,
            created_at=datetime.now(UTC),
        )
        self._babies[baby_id] = baby
        return baby

    async def update(self, baby_id: str, data: BabyUpdate) -> Baby | None:
        """更新嬰兒."""
        baby = self._babies.get(baby_id)
        if not baby:
            return None

        update_data = data.model_dump(exclude_unset=True)
        updated_baby = baby.model_copy(update=update_data)
        self._babies[baby_id] = updated_baby
        return updated_baby

    async def delete(self, baby_id: str) -> bool:
        """刪除嬰兒."""
        if baby_id in self._babies:
            del self._babies[baby_id]
            return True
        return False

    async def list_by_user(self, internal_user_id: str) -> list[Baby]:
        """取得使用者可存取的嬰兒列表."""
        memberships = await self._membership_repo.list_by_user(internal_user_id)
        baby_ids = [m.baby_id for m in memberships]
        return [b for b in self._babies.values() if b.baby_id in baby_ids]


class InMemoryMembershipRepository(MembershipRepository):
    """In-Memory 成員 Repository."""

    def __init__(self) -> None:
        """初始化."""
        self._memberships: dict[tuple[str, str], Membership] = {}

    async def get(self, baby_id: str, internal_user_id: str) -> Membership | None:
        """取得成員資格."""
        return self._memberships.get((baby_id, internal_user_id))

    async def create(self, baby_id: str, internal_user_id: str, role: MemberRole) -> Membership:
        """建立成員資格."""
        membership = Membership(
            baby_id=baby_id,
            internal_user_id=internal_user_id,
            role=role,
            joined_at=datetime.now(UTC),
        )
        self._memberships[(baby_id, internal_user_id)] = membership
        return membership

    async def list_by_baby(self, baby_id: str) -> list[Membership]:
        """取得嬰兒的所有成員."""
        return [m for m in self._memberships.values() if m.baby_id == baby_id]

    async def list_by_user(self, internal_user_id: str) -> list[Membership]:
        """取得使用者的所有成員資格."""
        return [m for m in self._memberships.values() if m.internal_user_id == internal_user_id]

    async def delete(self, baby_id: str, internal_user_id: str) -> bool:
        """刪除成員資格."""
        key = (baby_id, internal_user_id)
        if key in self._memberships:
            del self._memberships[key]
            return True
        return False


class InMemoryWeightRepository(WeightRepository):
    """In-Memory 體重 Repository."""

    def __init__(self) -> None:
        """初始化."""
        self._weights: dict[str, Weight] = {}

    async def get(self, baby_id: str, weight_id: str) -> Weight | None:
        """取得體重紀錄."""
        weight = self._weights.get(weight_id)
        if weight and weight.baby_id == baby_id:
            return weight
        return None

    async def create(self, baby_id: str, data: WeightCreate, created_by: str) -> Weight:
        """建立體重紀錄."""
        weight_id = generate_ulid()
        weight = Weight(
            weight_id=weight_id,
            baby_id=baby_id,
            timestamp=data.timestamp,
            weight_g=data.weight_g,
            note=data.note,
            created_by=created_by,
            created_at=datetime.now(UTC),
            updated_at=None,
        )
        self._weights[weight_id] = weight
        return weight

    async def update(self, baby_id: str, weight_id: str, data: WeightUpdate) -> Weight | None:
        """更新體重紀錄."""
        weight = await self.get(baby_id, weight_id)
        if not weight:
            return None

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.now(UTC)
        updated_weight = weight.model_copy(update=update_data)
        self._weights[weight_id] = updated_weight
        return updated_weight

    async def delete(self, baby_id: str, weight_id: str) -> bool:
        """刪除體重紀錄."""
        weight = await self.get(baby_id, weight_id)
        if weight:
            del self._weights[weight_id]
            return True
        return False

    async def list_by_baby(
        self,
        baby_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Weight]:
        """取得嬰兒的體重紀錄."""
        weights = [w for w in self._weights.values() if w.baby_id == baby_id]

        if from_date:
            weights = [w for w in weights if w.timestamp >= from_date]
        if to_date:
            weights = [w for w in weights if w.timestamp <= to_date]

        # 按時間排序
        return sorted(weights, key=lambda w: w.timestamp)


class InMemoryRepositories:
    """統一管理所有 In-Memory Repositories."""

    def __init__(self) -> None:
        """初始化所有 repositories."""
        self.identity_links = InMemoryIdentityLinkRepository()
        self.users = InMemoryUserRepository()
        self.memberships = InMemoryMembershipRepository()
        self.babies = InMemoryBabyRepository(self.memberships)
        self.weights = InMemoryWeightRepository()

    async def init_dev_data(self) -> None:
        """初始化開發模式測試資料."""
        from api.app.config import get_settings

        settings = get_settings()

        # 建立 dev 使用者的 identity link
        await self.identity_links.create(
            provider_iss="http://localhost",
            provider_sub=settings.dev_user_id,
            internal_user_id=settings.dev_internal_user_id,
        )

        # 建立 dev 使用者
        await self.users.create(
            internal_user_id=settings.dev_internal_user_id,
            data=UserCreate(
                display_name="Dev User",
                email="dev@example.com",
            ),
        )

        # 建立 demo baby
        from datetime import date

        demo_baby = await self.babies.create(
            BabyCreate(
                name="Demo Baby",
                birth_date=date(2025, 12, 1),
                gender=Gender.MALE,
            )
        )

        # 設定 dev user 為 owner
        await self.memberships.create(
            baby_id=demo_baby.baby_id,
            internal_user_id=settings.dev_internal_user_id,
            role=MemberRole.OWNER,
        )

        # 新增一些測試體重資料
        test_weights = [
            (datetime(2025, 12, 1, 8, 0, tzinfo=UTC), 3200, "出生體重"),
            (datetime(2025, 12, 8, 8, 0, tzinfo=UTC), 3350, "第一週"),
            (datetime(2025, 12, 15, 8, 0, tzinfo=UTC), 3600, "第二週"),
            (datetime(2025, 12, 22, 8, 0, tzinfo=UTC), 3900, "第三週"),
            (datetime(2025, 12, 29, 8, 0, tzinfo=UTC), 4200, "第四週"),
        ]

        for ts, weight_g, note in test_weights:
            await self.weights.create(
                baby_id=demo_baby.baby_id,
                data=WeightCreate(timestamp=ts, weight_g=weight_g, note=note),
                created_by=settings.dev_internal_user_id,
            )
