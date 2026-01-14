"""使用者相關資料模型."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """使用者基礎欄位."""

    display_name: str = Field(..., min_length=1, max_length=50, description="顯示名稱")
    email: EmailStr = Field(..., description="電子郵件")


class UserCreate(UserBase):
    """建立使用者的請求."""

    password: str = Field(..., min_length=8, max_length=128, description="密碼")
    invite_code: str = Field(..., description="邀請碼")


class UserInDB(UserBase):
    """資料庫中的使用者資料."""

    id: str = Field(..., description="使用者 ID (ULID)")
    internal_user_id: str = Field(..., description="內部使用者 ID (ULID)")
    hashed_password: str = Field(..., description="雜湊後的密碼")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    model_config = {"from_attributes": True}


class User(UserBase):
    """使用者公開資料（不含密碼）."""

    id: str = Field(..., description="使用者 ID")
    internal_user_id: str = Field(..., description="內部使用者 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """登入請求."""

    email: EmailStr = Field(..., description="電子郵件")
    password: str = Field(..., description="密碼")
