"""成長曲線評估服務.

基於 WHO 兒童生長標準，評估嬰兒體重是否在正常範圍內。
"""

from datetime import date
from typing import Literal

from api.app.data import (
    get_percentile_weights,
    weight_to_percentile,
    weight_to_zscore,
)
from api.app.models.weight import (
    ReferenceRange,
    WeightAssessment,
    WeightAssessmentBrief,
)


class AssessmentService:
    """成長曲線評估服務."""

    # 評估等級定義
    ASSESSMENT_LEVELS = {
        "severely_underweight": {"min": 0, "max": 3, "message": "體重嚴重不足，建議儘速就醫諮詢"},
        "underweight": {"min": 3, "max": 15, "message": "體重偏低，建議諮詢小兒科醫師"},
        "normal": {"min": 15, "max": 85, "message": "體重在正常範圍內，持續保持"},
        "overweight": {"min": 85, "max": 97, "message": "體重偏高，建議注意飲食均衡"},
        "severely_overweight": {"min": 97, "max": 100, "message": "體重過重，建議諮詢小兒科醫師"},
    }

    @staticmethod
    def calculate_age_in_months(birth_date: date, measure_date: date) -> int:
        """計算月齡.
        
        Args:
            birth_date: 出生日期
            measure_date: 測量日期
        
        Returns:
            月齡（取整數）
        """
        days = (measure_date - birth_date).days
        # 以 30.44 天為一個月（365.25 / 12）
        return int(days / 30.44)

    @staticmethod
    def calculate_age_in_days(birth_date: date, measure_date: date) -> int:
        """計算日齡.
        
        Args:
            birth_date: 出生日期
            measure_date: 測量日期
        
        Returns:
            日齡
        """
        return (measure_date - birth_date).days

    @classmethod
    def get_assessment_level(cls, percentile: float) -> tuple[str, str]:
        """根據百分位取得評估等級和訊息.
        
        Args:
            percentile: 百分位數 (0-100)
        
        Returns:
            (assessment_key, message)
        """
        for key, level in cls.ASSESSMENT_LEVELS.items():
            if level["min"] <= percentile < level["max"]:
                return key, level["message"]
        
        # Edge case: percentile = 100
        return "severely_overweight", cls.ASSESSMENT_LEVELS["severely_overweight"]["message"]

    @classmethod
    def assess_weight(
        cls,
        weight_id: str,
        weight_g: int,
        gender: Literal["male", "female"],
        birth_date: date,
        measure_date: date,
    ) -> WeightAssessment | None:
        """評估體重.
        
        Args:
            weight_id: 體重紀錄 ID
            weight_g: 體重（公克）
            gender: 性別
            birth_date: 出生日期
            measure_date: 測量日期
        
        Returns:
            WeightAssessment 或 None（如果超出數據範圍）
        """
        age_months = cls.calculate_age_in_months(birth_date, measure_date)
        age_days = cls.calculate_age_in_days(birth_date, measure_date)
        
        # 檢查是否在數據範圍內 (0-24 個月)
        if age_months < 0 or age_months > 24:
            return None
        
        # 計算百分位和 Z-score
        weight_kg = weight_g / 1000
        percentile = weight_to_percentile(weight_kg, gender, age_months)
        z_score = weight_to_zscore(weight_kg, gender, age_months)
        
        if percentile is None or z_score is None:
            return None
        
        # 取得評估等級
        assessment_key, message = cls.get_assessment_level(percentile)
        
        # 取得參考範圍
        ref_weights = get_percentile_weights(gender, age_months)
        if ref_weights is None:
            return None
        
        reference_range = ReferenceRange(
            p3=int(ref_weights[3] * 1000),
            p15=int(ref_weights[15] * 1000),
            p50=int(ref_weights[50] * 1000),
            p85=int(ref_weights[85] * 1000),
            p97=int(ref_weights[97] * 1000),
        )
        
        return WeightAssessment(
            weight_id=weight_id,
            weight_g=weight_g,
            age_in_days=age_days,
            gender=gender,
            percentile=round(percentile, 1),
            z_score=round(z_score, 2),
            assessment=assessment_key,
            message=message,
            reference_range=reference_range,
        )

    @classmethod
    def assess_weight_brief(
        cls,
        weight_g: int,
        gender: Literal["male", "female"],
        birth_date: date,
        measure_date: date,
    ) -> WeightAssessmentBrief | None:
        """簡易評估體重（用於列表）.
        
        Args:
            weight_g: 體重（公克）
            gender: 性別
            birth_date: 出生日期
            measure_date: 測量日期
        
        Returns:
            WeightAssessmentBrief 或 None
        """
        age_months = cls.calculate_age_in_months(birth_date, measure_date)
        
        if age_months < 0 or age_months > 24:
            return None
        
        weight_kg = weight_g / 1000
        percentile = weight_to_percentile(weight_kg, gender, age_months)
        
        if percentile is None:
            return None
        
        assessment_key, message = cls.get_assessment_level(percentile)
        
        return WeightAssessmentBrief(
            percentile=round(percentile, 1),
            assessment=assessment_key,
            message=message,
        )
