"""依賴注入."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from api.app.config import Settings, get_settings
from api.app.models import CurrentUser, Membership
from api.app.repositories import (
    BabyRepository,
    IdentityLinkRepository,
    MembershipRepository,
    UserRepository,
    WeightRepository,
)


def get_identity_link_repository(request: Request) -> IdentityLinkRepository:
    """取得 IdentityLinkRepository."""
    return request.app.state.repos.identity_links  # type: ignore[no-any-return]


def get_user_repository(request: Request) -> UserRepository:
    """取得 UserRepository."""
    return request.app.state.repos.users  # type: ignore[no-any-return]


def get_baby_repository(request: Request) -> BabyRepository:
    """取得 BabyRepository."""
    return request.app.state.repos.babies  # type: ignore[no-any-return]


def get_membership_repository(request: Request) -> MembershipRepository:
    """取得 MembershipRepository."""
    return request.app.state.repos.memberships  # type: ignore[no-any-return]


def get_weight_repository(request: Request) -> WeightRepository:
    """取得 WeightRepository."""
    return request.app.state.repos.weights  # type: ignore[no-any-return]


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    identity_repo: Annotated[IdentityLinkRepository, Depends(get_identity_link_repository)],
) -> CurrentUser:
    """取得當前使用者."""
    # Dev 模式：使用固定身份
    if settings.is_dev_auth:
        # 檢查 Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
            )

        token = auth_header[7:]  # 移除 "Bearer "
        if token != "dev":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid dev token (use 'dev')",
            )

        # 查詢 identity link 取得 internal_user_id
        link = await identity_repo.find_by_provider(
            provider_iss="http://localhost",
            provider_sub=settings.dev_user_id,
        )

        return CurrentUser(
            provider_iss="http://localhost",
            provider_sub=settings.dev_user_id,
            internal_user_id=link.internal_user_id if link else settings.dev_internal_user_id,
            email="dev@example.com",
        )

    # TODO: 實作真實 JWT 驗證
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="JWT validation not implemented yet",
    )


async def require_baby_membership(
    baby_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    membership_repo: Annotated[MembershipRepository, Depends(get_membership_repository)],
) -> Membership:
    """要求嬰兒成員資格（任意角色）."""
    if not current_user.internal_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not registered",
        )

    membership = await membership_repo.get(baby_id, current_user.internal_user_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this baby",
        )

    return membership


async def require_baby_write_access(
    baby_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    membership_repo: Annotated[MembershipRepository, Depends(get_membership_repository)],
) -> Membership:
    """要求嬰兒寫入權限（owner 或 editor）."""
    
    membership = await require_baby_membership(
        baby_id=baby_id,
        current_user=current_user,
        membership_repo=membership_repo,
    )

    if not membership.can_write():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write access required",
        )

    return membership


# Type aliases for DI
IdentityLinkRepoDep = Annotated[IdentityLinkRepository, Depends(get_identity_link_repository)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
BabyRepoDep = Annotated[BabyRepository, Depends(get_baby_repository)]
MembershipRepoDep = Annotated[MembershipRepository, Depends(get_membership_repository)]
WeightRepoDep = Annotated[WeightRepository, Depends(get_weight_repository)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
