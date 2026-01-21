"""嬰兒相關資料模型."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Gender(str, Enum):
    """性別."""

    MALE = "male"
    FEMALE = "female"


class BabyBase(BaseModel):
    """嬰兒基礎欄位."""

    name: str = Field(..., min_length=1, max_length=50, description="嬰兒名稱")
    birth_date: date = Field(..., description="出生日期")
    gender: Gender = Field(..., description="性別（成長曲線評估需要）")


class BabyCreate(BabyBase):
    """建立嬰兒的請求."""

    pass


class BabyUpdate(BaseModel):
    """更新嬰兒的請求."""

    name: str | None = Field(None, min_length=1, max_length=50, description="嬰兒名稱")
    birth_date: date | None = Field(None, description="出生日期")
    gender: Gender | None = Field(None, description="性別")


class Baby(BabyBase):
    """嬰兒完整資料."""

    baby_id: str = Field(..., description="嬰兒 ID")
    created_at: datetime = Field(..., description="建立時間")

    class Config:
        """Pydantic 設定."""

        from_attributes = True


class BabyResponse(Baby):
    """嬰兒回應（含角色）."""

    role: str | None = Field(None, description="當前使用者的角色")


class BabyCreateResponse(BaseModel):
    """建立嬰兒的回應."""

    baby_id: str = Field(..., description="嬰兒 ID")


class MemberAdd(BaseModel):
    """新增成員請求."""

    email: str = Field(..., description="成員的 Email")
    role: str = Field("editor", description="角色（editor 或 viewer）")


class MemberResponse(BaseModel):
    """成員回應."""

    internal_user_id: str = Field(..., description="內部使用者 ID")
    email: str | None = Field(None, description="Email")
    display_name: str | None = Field(None, description="顯示名稱")
    role: str = Field(..., description="角色")
    joined_at: datetime = Field(..., description="加入時間")
