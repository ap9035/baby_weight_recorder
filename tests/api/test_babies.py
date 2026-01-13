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
        from api.app.models import BabyCreate, Gender

        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date="2026-01-01", gender=Gender.FEMALE)
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
        from api.app.models import BabyCreate, Gender

        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date="2026-01-01", gender=Gender.FEMALE)
        )

        response = api_client.delete(f"/v1/babies/{other_baby.baby_id}", headers=dev_headers)

        assert response.status_code == 403
