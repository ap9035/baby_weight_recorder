"""成長曲線評估 API tests."""

import pytest
from fastapi.testclient import TestClient

from api.app.repositories import InMemoryRepositories


@pytest.mark.unit
class TestWeightAssessment:
    """GET /v1/babies/{baby_id}/weights/{weight_id}/assessment tests."""

    async def test_get_assessment_success(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """成功取得體重評估."""
        await repos.init_dev_data()

        # 取得 baby 和 weight
        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        weights_response = api_client.get(
            f"/v1/babies/{baby_id}/weights", headers=dev_headers
        )
        weight_id = weights_response.json()[0]["weight_id"]

        # 取得評估
        response = api_client.get(
            f"/v1/babies/{baby_id}/weights/{weight_id}/assessment",
            headers=dev_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "percentile" in data
        assert "z_score" in data
        assert "assessment" in data
        assert "message" in data
        assert "reference_range" in data
        assert data["assessment"] in [
            "severely_underweight",
            "underweight",
            "normal",
            "overweight",
            "severely_overweight",
        ]

    async def test_assessment_reference_range(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """評估結果包含參考範圍."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        weights_response = api_client.get(
            f"/v1/babies/{baby_id}/weights", headers=dev_headers
        )
        weight_id = weights_response.json()[0]["weight_id"]

        response = api_client.get(
            f"/v1/babies/{baby_id}/weights/{weight_id}/assessment",
            headers=dev_headers,
        )

        data = response.json()
        ref = data["reference_range"]

        # 確認參考範圍正確（P3 < P15 < P50 < P85 < P97）
        assert ref["p3"] < ref["p15"] < ref["p50"] < ref["p85"] < ref["p97"]

    async def test_assessment_weight_not_found(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """體重不存在時回傳 404."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(
            f"/v1/babies/{baby_id}/weights/nonexistent/assessment",
            headers=dev_headers,
        )

        assert response.status_code == 404


@pytest.mark.unit
class TestListWeightsWithAssessment:
    """GET /v1/babies/{baby_id}/weights?include_assessment=true tests."""

    async def test_list_without_assessment(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """預設不包含評估."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(
            f"/v1/babies/{baby_id}/weights", headers=dev_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # 預設不包含評估
        assert data[0]["assessment"] is None

    async def test_list_with_assessment(
        self,
        api_client: TestClient,
        dev_headers: dict[str, str],
        repos: InMemoryRepositories,
    ) -> None:
        """include_assessment=true 時包含評估."""
        await repos.init_dev_data()

        list_response = api_client.get("/v1/babies", headers=dev_headers)
        baby_id = list_response.json()[0]["baby_id"]

        response = api_client.get(
            f"/v1/babies/{baby_id}/weights?include_assessment=true",
            headers=dev_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # 包含評估
        assert data[0]["assessment"] is not None
        assert "percentile" in data[0]["assessment"]
        assert "assessment" in data[0]["assessment"]
        assert "message" in data[0]["assessment"]


@pytest.mark.unit
class TestAssessmentService:
    """AssessmentService 單元測試."""

    def test_calculate_age_in_months(self) -> None:
        """計算月齡."""
        from datetime import date

        from api.app.services import AssessmentService

        # 剛出生
        assert AssessmentService.calculate_age_in_months(
            date(2025, 12, 1), date(2025, 12, 1)
        ) == 0

        # 1 個月
        assert AssessmentService.calculate_age_in_months(
            date(2025, 12, 1), date(2026, 1, 1)
        ) == 1

        # 6 個月
        assert AssessmentService.calculate_age_in_months(
            date(2025, 6, 1), date(2025, 12, 1)
        ) == 6

    def test_assessment_levels(self) -> None:
        """評估等級判定."""
        from api.app.services import AssessmentService

        # P1 = severely_underweight
        level, _ = AssessmentService.get_assessment_level(1.0)
        assert level == "severely_underweight"

        # P10 = underweight
        level, _ = AssessmentService.get_assessment_level(10.0)
        assert level == "underweight"

        # P50 = normal
        level, _ = AssessmentService.get_assessment_level(50.0)
        assert level == "normal"

        # P90 = overweight
        level, _ = AssessmentService.get_assessment_level(90.0)
        assert level == "overweight"

        # P99 = severely_overweight
        level, _ = AssessmentService.get_assessment_level(99.0)
        assert level == "severely_overweight"

    def test_weight_to_percentile(self) -> None:
        """體重轉百分位."""
        from api.app.data import weight_to_percentile

        # 0 個月男嬰 3.35kg = P50
        p = weight_to_percentile(3.35, "male", 0)
        assert p is not None
        assert 49 < p < 51  # 約 P50

        # 0 個月男嬰 2.5kg = 約 P3
        p = weight_to_percentile(2.5, "male", 0)
        assert p is not None
        assert p < 5  # 約 P3

        # 5 歲 (60 個月) 還在範圍內
        p = weight_to_percentile(18.0, "male", 60)
        assert p is not None
        assert 40 < p < 60  # 約 P50

        # 超出範圍 (61 個月)
        p = weight_to_percentile(18.0, "male", 61)
        assert p is None
