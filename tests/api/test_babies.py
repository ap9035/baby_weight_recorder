"""Baby CRUD API tests."""

import pytest
from fastapi.testclient import TestClient

from api.app.repositories import InMemoryRepositories


@pytest.mark.unit
class TestCreateBaby:
    """POST /v1/babies tests."""

    async def test_create_baby_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功建立嬰兒."""
        # Setup dev user
        await repos.init_dev_data()

        response = api_client.post(
            "/v1/babies",
            headers=dev_headers,
            json={
                "name": "Test Baby",
                "birth_date": "2026-01-01",
                "gender": "male",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "baby_id" in data
        assert len(data["baby_id"]) == 26  # ULID length

    async def test_create_baby_without_auth(
        self,
        api_client: TestClient,
        repos: InMemoryRepositories,
    ) -> None:
        """未認證時建立嬰兒失敗."""
        await repos.init_dev_data()

        response = api_client.post(
            "/v1/babies",
            json={
                "name": "Test Baby",
                "birth_date": "2026-01-01",
                "gender": "male",
            },
        )

        assert response.status_code == 401

    async def test_create_baby_invalid_gender(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """無效性別時建立失敗."""
        await repos.init_dev_data()

        response = api_client.post(
            "/v1/babies",
            headers=dev_headers,
            json={
                "name": "Test Baby",
                "birth_date": "2026-01-01",
                "gender": "unknown",  # Invalid
            },
        )

        assert response.status_code == 422  # Validation error

    async def test_create_baby_missing_fields(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """缺少必要欄位時建立失敗."""
        await repos.init_dev_data()

        response = api_client.post(
            "/v1/babies",
            headers=dev_headers,
            json={"name": "Test Baby"},  # Missing birth_date and gender
        )

        assert response.status_code == 422


@pytest.mark.unit
class TestListBabies:
    """GET /v1/babies tests."""

    async def test_list_babies_empty(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """沒有嬰兒時回傳空列表."""
        # 只建立 user，不建立 demo baby
        await repos.identity_links.create(
            provider_iss="http://localhost",
            provider_sub="dev-user",
            internal_user_id="01DEV000000000000000000000",
        )

        response = api_client.get("/v1/babies", headers=dev_headers)

        assert response.status_code == 200
        assert response.json() == []

    async def test_list_babies_with_data(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """有嬰兒時回傳列表."""
        await repos.init_dev_data()

        response = api_client.get("/v1/babies", headers=dev_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Demo Baby"
        assert data[0]["role"] == "owner"


@pytest.mark.unit
class TestGetBaby:
    """GET /v1/babies/{baby_id} tests."""

    async def test_get_baby_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功取得嬰兒."""
        await repos.init_dev_data()

        # 先取得 baby_id
        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(f"/v1/babies/{baby_id}", headers=dev_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["baby_id"] == baby_id
        assert data["name"] == "Demo Baby"
        assert data["gender"] == "male"
        assert data["role"] == "owner"

    async def test_get_baby_not_found(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """嬰兒不存在時回傳 403."""
        await repos.init_dev_data()

        response = api_client.get("/v1/babies/nonexistent", headers=dev_headers)

        assert response.status_code == 403  # No membership = forbidden

    async def test_get_baby_no_permission(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """沒有權限時回傳 403."""
        await repos.init_dev_data()

        # 建立另一個嬰兒（沒有 membership）
        from datetime import date

        from api.app.models import BabyCreate, Gender

        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date=date(2026, 1, 1), gender=Gender.FEMALE)
        )

        response = api_client.get(f"/v1/babies/{other_baby.baby_id}", headers=dev_headers)

        assert response.status_code == 403


@pytest.mark.unit
class TestUpdateBaby:
    """PUT /v1/babies/{baby_id} tests."""

    async def test_update_baby_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功更新嬰兒."""
        await repos.init_dev_data()

        # 取得 baby_id
        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.put(
            f"/v1/babies/{baby_id}",
            headers=dev_headers,
            json={"name": "Updated Baby Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Baby Name"
        assert data["gender"] == "male"  # Unchanged

    async def test_update_baby_partial(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """部分更新嬰兒."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.put(
            f"/v1/babies/{baby_id}",
            headers=dev_headers,
            json={"gender": "female"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Demo Baby"  # Unchanged
        assert data["gender"] == "female"  # Updated


@pytest.mark.unit
class TestDeleteBaby:
    """DELETE /v1/babies/{baby_id} tests."""

    async def test_delete_baby_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功刪除嬰兒（owner）."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.delete(f"/v1/babies/{baby_id}", headers=dev_headers)

        assert response.status_code == 204

        # 確認已刪除
        list_response2 = api_client.get("/v1/babies", headers=dev_headers)
        assert len(list_response2.json()) == 0

    async def test_delete_baby_no_permission(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """沒有權限時回傳 403."""
        await repos.init_dev_data()

        # 建立另一個嬰兒（沒有 membership）
        from datetime import date

        from api.app.models import BabyCreate, Gender

        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date=date(2026, 1, 1), gender=Gender.FEMALE)
        )

        response = api_client.delete(f"/v1/babies/{other_baby.baby_id}", headers=dev_headers)

        assert response.status_code == 403


# ==================== 成員管理測試 ====================


@pytest.mark.unit
class TestListMembers:
    """GET /v1/babies/{baby_id}/members tests."""

    async def test_list_members_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功列出成員."""
        await repos.init_dev_data()

        # 取得 baby_id
        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(f"/v1/babies/{baby_id}/members", headers=dev_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["role"] == "owner"

    async def test_list_members_no_permission(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """沒有權限時回傳 403."""
        await repos.init_dev_data()

        from datetime import date

        from api.app.models import BabyCreate, Gender

        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date=date(2026, 1, 1), gender=Gender.FEMALE)
        )

        response = api_client.get(
            f"/v1/babies/{other_baby.baby_id}/members", headers=dev_headers
        )

        assert response.status_code == 403


@pytest.mark.unit
class TestAddMember:
    """POST /v1/babies/{baby_id}/members tests."""

    async def test_add_member_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功新增成員."""
        await repos.init_dev_data()

        # 建立另一個使用者
        from api.app.models import UserCreate

        await repos.users.create(
            internal_user_id="01OTHER0000000000000000000",
            data=UserCreate(display_name="Other User", email="other@example.com"),
        )

        # 取得 baby_id
        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.post(
            f"/v1/babies/{baby_id}/members",
            headers=dev_headers,
            json={"email": "other@example.com", "role": "editor"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "other@example.com"
        assert data["role"] == "editor"
        assert data["display_name"] == "Other User"

    async def test_add_member_as_viewer(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功新增 viewer 成員."""
        await repos.init_dev_data()

        from api.app.models import UserCreate

        await repos.users.create(
            internal_user_id="01OTHER0000000000000000000",
            data=UserCreate(display_name="Viewer User", email="viewer@example.com"),
        )

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.post(
            f"/v1/babies/{baby_id}/members",
            headers=dev_headers,
            json={"email": "viewer@example.com", "role": "viewer"},
        )

        assert response.status_code == 201
        assert response.json()["role"] == "viewer"

    async def test_add_member_invalid_role(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """無效角色時回傳 400."""
        await repos.init_dev_data()

        from api.app.models import UserCreate

        await repos.users.create(
            internal_user_id="01OTHER0000000000000000000",
            data=UserCreate(display_name="Other User", email="other@example.com"),
        )

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.post(
            f"/v1/babies/{baby_id}/members",
            headers=dev_headers,
            json={"email": "other@example.com", "role": "owner"},  # 不能新增 owner
        )

        assert response.status_code == 400

    async def test_add_member_user_not_found(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """使用者不存在時回傳 404."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.post(
            f"/v1/babies/{baby_id}/members",
            headers=dev_headers,
            json={"email": "nonexistent@example.com", "role": "editor"},
        )

        assert response.status_code == 404

    async def test_add_member_already_exists(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """使用者已是成員時回傳 409."""
        await repos.init_dev_data()

        from api.app.models import UserCreate

        await repos.users.create(
            internal_user_id="01OTHER0000000000000000000",
            data=UserCreate(display_name="Other User", email="other@example.com"),
        )

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        # 第一次新增
        api_client.post(
            f"/v1/babies/{baby_id}/members",
            headers=dev_headers,
            json={"email": "other@example.com", "role": "editor"},
        )

        # 第二次新增
        response = api_client.post(
            f"/v1/babies/{baby_id}/members",
            headers=dev_headers,
            json={"email": "other@example.com", "role": "viewer"},
        )

        assert response.status_code == 409

    async def test_add_member_not_owner(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """非 owner 新增成員時回傳 403."""
        await repos.init_dev_data()

        from datetime import date

        from api.app.models import BabyCreate, Gender, MemberRole, UserCreate

        # 建立另一個嬰兒
        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date=date(2026, 1, 1), gender=Gender.FEMALE)
        )

        # 讓 dev user 成為 editor（不是 owner）
        from api.app.config import get_settings

        settings = get_settings()
        await repos.memberships.create(
            baby_id=other_baby.baby_id,
            internal_user_id=settings.dev_internal_user_id,
            role=MemberRole.EDITOR,
        )

        # 建立要新增的使用者
        await repos.users.create(
            internal_user_id="01NEWUSER000000000000000000",
            data=UserCreate(display_name="New User", email="new@example.com"),
        )

        response = api_client.post(
            f"/v1/babies/{other_baby.baby_id}/members",
            headers=dev_headers,
            json={"email": "new@example.com", "role": "viewer"},
        )

        assert response.status_code == 403


@pytest.mark.unit
class TestRemoveMember:
    """DELETE /v1/babies/{baby_id}/members/{user_id} tests."""

    async def test_remove_member_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功移除成員."""
        await repos.init_dev_data()

        from api.app.models import MemberRole, UserCreate

        # 建立並新增另一個使用者
        await repos.users.create(
            internal_user_id="01OTHER0000000000000000000",
            data=UserCreate(display_name="Other User", email="other@example.com"),
        )

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        await repos.memberships.create(
            baby_id=baby_id,
            internal_user_id="01OTHER0000000000000000000",
            role=MemberRole.EDITOR,
        )

        # 移除成員
        response = api_client.delete(
            f"/v1/babies/{baby_id}/members/01OTHER0000000000000000000",
            headers=dev_headers,
        )

        assert response.status_code == 204

        # 確認已移除
        members_response = api_client.get(
            f"/v1/babies/{baby_id}/members", headers=dev_headers
        )
        members = members_response.json()
        assert len(members) == 1  # 只剩 owner

    async def test_remove_self_forbidden(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """不能移除自己."""
        await repos.init_dev_data()

        from api.app.config import get_settings

        settings = get_settings()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.delete(
            f"/v1/babies/{baby_id}/members/{settings.dev_internal_user_id}",
            headers=dev_headers,
        )

        assert response.status_code == 400

    async def test_remove_member_not_owner(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """非 owner 移除成員時回傳 403."""
        await repos.init_dev_data()

        from datetime import date

        from api.app.models import BabyCreate, Gender, MemberRole, UserCreate

        from api.app.config import get_settings

        settings = get_settings()

        # 建立另一個嬰兒
        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date=date(2026, 1, 1), gender=Gender.FEMALE)
        )

        # 讓 dev user 成為 editor（不是 owner）
        await repos.memberships.create(
            baby_id=other_baby.baby_id,
            internal_user_id=settings.dev_internal_user_id,
            role=MemberRole.EDITOR,
        )

        # 建立並新增另一個使用者
        await repos.users.create(
            internal_user_id="01OTHER0000000000000000000",
            data=UserCreate(display_name="Other User", email="other@example.com"),
        )
        await repos.memberships.create(
            baby_id=other_baby.baby_id,
            internal_user_id="01OTHER0000000000000000000",
            role=MemberRole.VIEWER,
        )

        response = api_client.delete(
            f"/v1/babies/{other_baby.baby_id}/members/01OTHER0000000000000000000",
            headers=dev_headers,
        )

        assert response.status_code == 403
