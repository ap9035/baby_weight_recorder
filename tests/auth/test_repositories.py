"""Repository 測試."""

import pytest

from auth.app.models import UserCreate
from auth.app.repositories.memory import InMemoryUserRepository
from auth.app.services.password import hash_password


@pytest.fixture
def user_repo():
    """建立 In-Memory User Repository."""
    return InMemoryUserRepository()


@pytest.fixture
def sample_user_create():
    """建立測試用的 UserCreate."""
    return UserCreate(
        display_name="Test User",
        email="test@example.com",
        password="test_password_123",
        invite_code="TEST_CODE",
    )


@pytest.mark.asyncio
async def test_create_user(user_repo, sample_user_create):
    """測試建立使用者."""
    hashed_password = hash_password(sample_user_create.password)
    user = await user_repo.create(sample_user_create, hashed_password)

    assert user.id is not None
    assert user.internal_user_id is not None
    assert user.email == sample_user_create.email
    assert user.display_name == sample_user_create.display_name
    assert user.hashed_password == hashed_password
    assert user.hashed_password != sample_user_create.password


@pytest.mark.asyncio
async def test_get_user_by_id(user_repo, sample_user_create):
    """測試根據 ID 取得使用者."""
    hashed_password = hash_password(sample_user_create.password)
    created_user = await user_repo.create(sample_user_create, hashed_password)

    retrieved_user = await user_repo.get_by_id(created_user.id)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo, sample_user_create):
    """測試根據 Email 取得使用者."""
    hashed_password = hash_password(sample_user_create.password)
    created_user = await user_repo.create(sample_user_create, hashed_password)

    retrieved_user = await user_repo.get_by_email(sample_user_create.email)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == created_user.email


@pytest.mark.asyncio
async def test_get_user_by_internal_id(user_repo, sample_user_create):
    """測試根據內部使用者 ID 取得使用者."""
    hashed_password = hash_password(sample_user_create.password)
    created_user = await user_repo.create(sample_user_create, hashed_password)

    retrieved_user = await user_repo.get_by_internal_id(created_user.internal_user_id)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.internal_user_id == created_user.internal_user_id


@pytest.mark.asyncio
async def test_create_duplicate_email(user_repo, sample_user_create):
    """測試建立重複 Email 的使用者應該失敗."""
    hashed_password = hash_password(sample_user_create.password)
    await user_repo.create(sample_user_create, hashed_password)

    # 嘗試建立相同 email 的使用者
    with pytest.raises(ValueError, match="already exists"):
        await user_repo.create(sample_user_create, hashed_password)


@pytest.mark.asyncio
async def test_get_nonexistent_user(user_repo):
    """測試取得不存在的使用者."""
    assert await user_repo.get_by_id("nonexistent") is None
    assert await user_repo.get_by_email("nonexistent@example.com") is None
    assert await user_repo.get_by_internal_id("nonexistent") is None
