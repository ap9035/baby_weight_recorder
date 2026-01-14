"""依賴注入."""

from typing import Annotated

from fastapi import Depends, Request

from auth.app.config import Settings, get_settings
from auth.app.repositories import UserRepository
from auth.app.services.invite import InviteCodeService
from auth.app.services.jwt import JWTService
from auth.app.services.secrets import SecretService


def get_user_repository(request: Request) -> UserRepository:
    """取得 UserRepository."""
    return request.app.state.user_repo  # type: ignore[no-any-return]


def get_secret_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> SecretService:
    """取得 SecretService."""
    return SecretService(project_id=settings.gcp_project_id)


def get_invite_service(
    secret_service: Annotated[SecretService, Depends(get_secret_service)]
) -> InviteCodeService:
    """取得 InviteCodeService."""
    return InviteCodeService(secret_service)


def get_jwt_service(
    settings: Annotated[Settings, Depends(get_settings)],
    secret_service: Annotated[SecretService, Depends(get_secret_service)],
) -> JWTService:
    """取得 JWTService."""
    return JWTService(settings, secret_service)
