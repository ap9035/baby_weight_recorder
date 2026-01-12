"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """健康檢查端點。"""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """就緒檢查端點。"""
    # TODO: 檢查 Firestore 連線
    return {"status": "ready"}
