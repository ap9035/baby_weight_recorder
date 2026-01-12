"""使用者相關資料模型."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """使用者基礎欄位."""

    display_name: str = Field(..., min_length=1, max_length=50, description="顯示名稱")
    email: EmailStr = Field(..., description="電子郵件")


class UserCreate(UserBase):
    """建立使用者的請求."""

    pass


class User(UserBase):
    """使用者完整資料."""

    internal_user_id: str = Field(..., description="內部使用者 ID (ULID)")
    created_at: datetime = Field(..., description="建立時間")

    class Config:
        """Pydantic 設定."""

        from_attributes = True


class IdentityLink(BaseModel):
    """身份對應資料."""

    link_id: str = Field(..., description="對應 ID")
    provider_iss: str = Field(..., description="IdP Issuer")
    provider_sub: str = Field(..., description="IdP Subject")
    internal_user_id: str = Field(..., description="內部使用者 ID")
    created_at: datetime = Field(..., description="建立時間")

    class Config:
        """Pydantic 設定."""

        from_attributes = True


class MemberRole(str, Enum):
    """成員角色."""

    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class Membership(BaseModel):
    """嬰兒成員資料."""

    baby_id: str = Field(..., description="嬰兒 ID")
    internal_user_id: str = Field(..., description="內部使用者 ID")
    role: MemberRole = Field(..., description="角色")
    joined_at: datetime = Field(..., description="加入時間")

    class Config:
        """Pydantic 設定."""

        from_attributes = True

    def can_read(self) -> bool:
        """是否有讀取權限."""
        return True  # 所有角色都可讀

    def can_write(self) -> bool:
        """是否有寫入權限."""
        return self.role in (MemberRole.OWNER, MemberRole.EDITOR)

    def can_manage(self) -> bool:
        """是否有管理權限."""
        return self.role == MemberRole.OWNER


class CurrentUser(BaseModel):
    """當前使用者上下文（從 JWT 解析）."""

    provider_iss: str = Field(..., description="IdP Issuer (from JWT iss)")
    provider_sub: str = Field(..., description="IdP Subject (from JWT sub)")
    internal_user_id: str | None = Field(None, description="內部使用者 ID（可能尚未建立）")
    email: str | None = Field(None, description="Email (from JWT)")
