"""認證相關路由."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from auth.app.dependencies import (
    get_invite_service,
    get_jwt_service,
    get_user_repository,
)
from auth.app.models import User, UserCreate, UserLogin
from auth.app.repositories import UserRepository
from auth.app.services.invite import InviteCodeService
from auth.app.services.jwt import JWTService
from auth.app.services.password import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    invite_service: Annotated[InviteCodeService, Depends(get_invite_service)],
) -> User:
    """註冊新使用者.

    Args:
        user_create: 註冊請求
        user_repo: User Repository
        invite_service: 邀請碼服務

    Returns:
        建立的使用者（不含密碼）

    Raises:
        HTTPException: 邀請碼無效或 Email 已存在
    """
    # 驗證邀請碼
    if not invite_service.validate(user_create.invite_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite code",
        )

    # 檢查 Email 是否已存在
    existing_user = await user_repo.get_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email {user_create.email} already registered",
        )

    # 雜湊密碼
    hashed_password = hash_password(user_create.password)

    # 建立使用者
    try:
        user_in_db = await user_repo.create(user_create, hashed_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    # 返回使用者（不含密碼）
    return User(
        id=user_in_db.id,
        internal_user_id=user_in_db.internal_user_id,
        display_name=user_in_db.display_name,
        email=user_in_db.email,
        created_at=user_in_db.created_at,
        updated_at=user_in_db.updated_at,
    )


@router.post("/token")
async def login(
    user_login: UserLogin,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> dict[str, str]:
    """登入取得 JWT Token.

    Args:
        user_login: 登入請求
        user_repo: User Repository
        jwt_service: JWT 服務

    Returns:
        JWT Token

    Raises:
        HTTPException: Email 或密碼錯誤
    """
    # 取得使用者
    user = await user_repo.get_by_email(user_login.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # 驗證密碼
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # 建立 JWT Token
    # 使用 internal_user_id 作為 subject（未來可改為 provider_sub）
    token = jwt_service.create_token(
        subject=user.internal_user_id,
        email=user.email,
        internal_user_id=user.internal_user_id,
    )

    return {
        "access_token": token,
        "token_type": "Bearer",
    }
