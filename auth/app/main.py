"""Baby Weight Recorder - Auth Service.

認證服務, 提供使用者註冊, 登入和 JWT 簽發.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google.cloud.firestore_v1 import AsyncClient

from auth.app.config import get_settings
from auth.app.repositories import FirestoreUserRepository, InMemoryUserRepository, UserRepository
from auth.app.routers import auth, health, jwks

# 設定 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """應用程式生命週期管理."""
    settings = get_settings()
    logger.info(f"Starting Auth service in {settings.environment} mode")
    logger.info(f"Repository mode: {settings.repository_mode.value}")

    # 檢查是否已經有設定好的 repo（測試用）
    existing_repo = getattr(app.state, "user_repo", None)
    if existing_repo is not None:
        logger.info("Using pre-configured repository (test mode)")
        user_repo: UserRepository = existing_repo
    elif settings.use_firestore:
        logger.info(
            f"Using Firestore: project={settings.gcp_project_id}, "
            f"database={settings.firestore_database}"
        )
        db = AsyncClient(project=settings.gcp_project_id, database=settings.firestore_database)
        user_repo = FirestoreUserRepository(db)
    else:
        logger.info("Using In-Memory repository")
        user_repo = InMemoryUserRepository()

    app.state.user_repo = user_repo

    yield

    # Shutdown
    logger.info("Shutting down Auth service")
    await user_repo.close()


app = FastAPI(
    title="Baby Weight Recorder Auth",
    description="嬰兒體重紀錄系統 認證服務",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 設定
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router)
app.include_router(jwks.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Auth Service 根路徑。"""
    return {"message": "Baby Weight Recorder Auth Service", "version": "0.1.0"}
