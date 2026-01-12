"""體重紀錄相關資料模型."""

from datetime import datetime

from pydantic import BaseModel, Field


class WeightBase(BaseModel):
    """體重基礎欄位."""

    timestamp: datetime = Field(..., description="量測時間")
    weight_g: int = Field(..., gt=0, lt=100000, description="體重（公克）")
    note: str | None = Field(None, max_length=500, description="備註")


class WeightCreate(WeightBase):
    """新增體重的請求."""

    pass


class WeightUpdate(BaseModel):
    """修改體重的請求."""

    timestamp: datetime | None = Field(None, description="量測時間")
    weight_g: int | None = Field(None, gt=0, lt=100000, description="體重（公克）")
    note: str | None = Field(None, max_length=500, description="備註")


class Weight(WeightBase):
    """體重完整資料."""

    weight_id: str = Field(..., description="體重紀錄 ID")
    baby_id: str = Field(..., description="嬰兒 ID")
    created_by: str = Field(..., description="建立者內部 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime | None = Field(None, description="更新時間")

    class Config:
        """Pydantic 設定."""

        from_attributes = True


class WeightResponse(Weight):
    """體重回應（可選含評估）."""

    assessment: "WeightAssessmentBrief | None" = Field(None, description="成長評估")


class WeightAssessmentBrief(BaseModel):
    """簡易成長評估（用於列表）."""

    percentile: float = Field(..., description="百分位數")
    assessment: str = Field(..., description="評估結果")
    message: str = Field(..., description="評估訊息")


class WeightAssessment(BaseModel):
    """完整成長評估."""

    weight_id: str = Field(..., description="體重紀錄 ID")
    weight_g: int = Field(..., description="體重（公克）")
    age_in_days: int = Field(..., description="年齡（天）")
    gender: str = Field(..., description="性別")
    percentile: float = Field(..., description="百分位數")
    z_score: float = Field(..., description="Z 分數")
    assessment: str = Field(..., description="評估結果")
    message: str = Field(..., description="評估訊息")
    reference_range: "ReferenceRange" = Field(..., description="參考範圍")


class ReferenceRange(BaseModel):
    """參考體重範圍."""

    p3: int = Field(..., description="第 3 百分位")
    p15: int = Field(..., description="第 15 百分位")
    p50: int = Field(..., description="第 50 百分位")
    p85: int = Field(..., description="第 85 百分位")
    p97: int = Field(..., description="第 97 百分位")


# Update forward references
WeightResponse.model_rebuild()
WeightAssessment.model_rebuild()
