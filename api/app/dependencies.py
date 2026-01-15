"""依賴注入."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose.exceptions import JWTError

from api.app.config import Settings, get_settings
from api.app.models import CurrentUser, Membership
from api.app.repositories import (
    BabyRepository,
    IdentityLinkRepository,
    MembershipRepository,
    UserRepository,
    WeightRepository,
)
from api.app.services.jwt import JWTVerificationService


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


def get_jwt_verification_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JWTVerificationService:
    """取得 JWT 驗證服務."""
    return JWTVerificationService(settings)


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    identity_repo: Annotated[IdentityLinkRepository, Depends(get_identity_link_repository)],
    jwt_service: Annotated[JWTVerificationService, Depends(get_jwt_verification_service)],
) -> CurrentUser:
    """取得當前使用者."""
    # 檢查 Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[7:]  # 移除 "Bearer "

    # Dev 模式：使用固定 token
    if settings.is_dev_auth:
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

    # OIDC 模式：驗證 JWT Token
    try:
        payload = await jwt_service.verify_token(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e!s}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # 從 JWT payload 取得身份信息
    provider_iss = payload.get("iss")
    provider_sub = payload.get("sub")
    email = payload.get("email")

    if not provider_iss or not provider_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims (iss, sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查詢 Identity Link 取得 internal_user_id
    link = await identity_repo.find_by_provider(
        provider_iss=provider_iss,
        provider_sub=provider_sub,
    )

    # 如果找不到 link，檢查是否有 internal_user_id 在 token 中（Auth Service 簽發的 token）
    internal_user_id = payload.get("internal_user_id")
    if not link and internal_user_id:
        # Token 中已經包含 internal_user_id（Auth Service 簽發的）
        # 這種情況下，我們可以直接使用，但理想情況下應該有 Identity Link
        pass
    elif link:
        internal_user_id = link.internal_user_id
    else:
        # 找不到 Identity Link 且 token 中沒有 internal_user_id
        # 這表示使用者尚未在系統中註冊
        internal_user_id = None

    return CurrentUser(
        provider_iss=provider_iss,
        provider_sub=provider_sub,
        internal_user_id=internal_user_id,
        email=email,
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
