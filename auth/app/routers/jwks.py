"""JWKS 端點."""

from typing import Annotated

from fastapi import APIRouter, Depends

from auth.app.dependencies import get_jwt_service
from auth.app.services.jwt import JWTService

router = APIRouter()


@router.get("/.well-known/jwks.json")
async def get_jwks(
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> dict[str, list[dict[str, str]]]:
    """取得 JWKS (JSON Web Key Set).

    這個端點提供用於驗證 JWT 的公鑰信息，符合 OIDC 標準。

    Returns:
        JWKS 格式的 JSON，包含公鑰信息
    """
    return jwt_service.get_jwks()
