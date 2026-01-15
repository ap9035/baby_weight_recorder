"""Weight CRUD API tests."""

from datetime import UTC

import pytest
from fastapi.testclient import TestClient

from api.app.repositories import InMemoryRepositories


@pytest.mark.unit
class TestCreateWeight:
    """POST /v1/babies/{baby_id}/weights tests."""

    async def test_create_weight_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功新增體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.post(
            f"/v1/babies/{baby_id}/weights",
            headers=dev_headers,
            json={
                "timestamp": "2026-01-10T08:00:00Z",
                "weight_g": 4500,
                "note": "測試體重",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "weight_id" in data
        assert data["weight_g"] == 4500
        assert data["note"] == "測試體重"
        assert data["baby_id"] == baby_id

    async def test_create_weight_without_note(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """不帶備註新增體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.post(
            f"/v1/babies/{baby_id}/weights",
            headers=dev_headers,
            json={
                "timestamp": "2026-01-10T08:00:00Z",
                "weight_g": 4500,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["note"] is None

    async def test_create_weight_invalid_weight(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """無效體重值."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        # 體重為 0
        response = api_client.post(
            f"/v1/babies/{baby_id}/weights",
            headers=dev_headers,
            json={
                "timestamp": "2026-01-10T08:00:00Z",
                "weight_g": 0,
            },
        )

        assert response.status_code == 422

        # 體重為負數
        response = api_client.post(
            f"/v1/babies/{baby_id}/weights",
            headers=dev_headers,
            json={
                "timestamp": "2026-01-10T08:00:00Z",
                "weight_g": -100,
            },
        )

        assert response.status_code == 422

    async def test_create_weight_no_permission(
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

        response = api_client.post(
            f"/v1/babies/{other_baby.baby_id}/weights",
            headers=dev_headers,
            json={
                "timestamp": "2026-01-10T08:00:00Z",
                "weight_g": 4500,
            },
        )

        assert response.status_code == 403


@pytest.mark.unit
class TestListWeights:
    """GET /v1/babies/{baby_id}/weights tests."""

    async def test_list_weights_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功列出體重（init_dev_data 會建立 5 筆）."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # init_dev_data 建立的
        # 確認按時間排序
        assert data[0]["note"] == "出生體重"
        assert data[-1]["note"] == "第四週"

    async def test_list_weights_with_date_filter(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """時間範圍篩選."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        # 只取 2025-12-08 ~ 2025-12-22 的資料
        response = api_client.get(
            f"/v1/babies/{baby_id}/weights",
            headers=dev_headers,
            params={
                "from": "2025-12-08T00:00:00Z",
                "to": "2025-12-22T23:59:59Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # 第一週、第二週、第三週

    async def test_list_weights_empty(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """沒有體重紀錄."""
        await repos.init_dev_data()

        # 建立新嬰兒（沒有體重）
        create_response = api_client.post(
            "/v1/babies",
            headers=dev_headers,
            json={
                "name": "New Baby",
                "birth_date": "2026-01-01",
                "gender": "female",
            },
        )
        baby_id = create_response.json()["baby_id"]

        response = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)

        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.unit
class TestGetWeight:
    """GET /v1/babies/{baby_id}/weights/{weight_id} tests."""

    async def test_get_weight_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功取得單筆體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        weights_response = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)
        weight_id = weights_response.json()[0]["weight_id"]

        response = api_client.get(f"/v1/babies/{baby_id}/weights/{weight_id}", headers=dev_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["weight_id"] == weight_id
        assert data["weight_g"] == 3200  # 出生體重

    async def test_get_weight_not_found(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """體重不存在."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(f"/v1/babies/{baby_id}/weights/nonexistent", headers=dev_headers)

        assert response.status_code == 404


@pytest.mark.unit
class TestUpdateWeight:
    """PUT /v1/babies/{baby_id}/weights/{weight_id} tests."""

    async def test_update_weight_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功更新體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        weights_response = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)
        weight_id = weights_response.json()[0]["weight_id"]

        response = api_client.put(
            f"/v1/babies/{baby_id}/weights/{weight_id}",
            headers=dev_headers,
            json={"weight_g": 3250, "note": "更正後的出生體重"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weight_g"] == 3250
        assert data["note"] == "更正後的出生體重"
        assert data["updated_at"] is not None

    async def test_update_weight_partial(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """部分更新體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        weights_response = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)
        weight_id = weights_response.json()[0]["weight_id"]

        response = api_client.put(
            f"/v1/babies/{baby_id}/weights/{weight_id}",
            headers=dev_headers,
            json={"note": "只更新備註"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weight_g"] == 3200  # 原本的
        assert data["note"] == "只更新備註"


@pytest.mark.unit
class TestDeleteWeight:
    """DELETE /v1/babies/{baby_id}/weights/{weight_id} tests."""

    async def test_delete_weight_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功刪除體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        weights_response = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)
        weight_id = weights_response.json()[0]["weight_id"]
        original_count = len(weights_response.json())

        response = api_client.delete(
            f"/v1/babies/{baby_id}/weights/{weight_id}", headers=dev_headers
        )

        assert response.status_code == 204

        # 確認已刪除
        weights_response2 = api_client.get(f"/v1/babies/{baby_id}/weights", headers=dev_headers)
        assert len(weights_response2.json()) == original_count - 1

    async def test_delete_weight_not_found(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """刪除不存在的體重."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.delete(
            f"/v1/babies/{baby_id}/weights/nonexistent", headers=dev_headers
        )

        assert response.status_code == 404

    async def test_delete_weight_no_permission(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """沒有權限時回傳 403."""
        await repos.init_dev_data()

        # 建立另一個嬰兒（沒有 membership）
        from datetime import datetime

        from api.app.models import BabyCreate, Gender, WeightCreate

        other_baby = await repos.babies.create(
            BabyCreate(name="Other Baby", birth_date=date(2026, 1, 1), gender=Gender.FEMALE)
        )
        # 為這個嬰兒建立一筆體重（由其他人建立）
        weight = await repos.weights.create(
            baby_id=other_baby.baby_id,
            data=WeightCreate(
                timestamp=datetime(2026, 1, 1, 8, 0, tzinfo=UTC),
                weight_g=3000,
                note=None,
            ),
            created_by="other-user-id",
        )

        response = api_client.delete(
            f"/v1/babies/{other_baby.baby_id}/weights/{weight.weight_id}",
            headers=dev_headers,
        )

        assert response.status_code == 403
