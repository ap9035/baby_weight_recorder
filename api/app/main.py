"""Baby Weight Recorder - Weight API Service.

主要 API 服務, 提供嬰兒體重記錄的 CRUD 操作和成長曲線評估.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.config import get_settings
from api.app.repositories import FirestoreRepositories, InMemoryRepositories
from api.app.routers import babies, health, weights

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
    logger.info(f"Starting API service in {settings.environment} mode")
    logger.info(f"Auth mode: {settings.auth_mode.value}")
    logger.info(f"Repository mode: {settings.repository_mode.value}")

    # 檢查是否已經有設定好的 repos（測試用）
    existing_repos = getattr(app.state, "repos", None)
    if existing_repos is not None:
        logger.info("Using pre-configured repositories (test mode)")
        repos: InMemoryRepositories | FirestoreRepositories = existing_repos
    elif settings.use_firestore:
        logger.info(
            f"Using Firestore: project={settings.gcp_project_id}, "
            f"database={settings.firestore_database}"
        )
        repos = FirestoreRepositories(
            project_id=settings.gcp_project_id,
            database=settings.firestore_database,
        )
    else:
        logger.info("Using In-Memory repositories")
        repos = InMemoryRepositories()
        # In-Memory + Dev 模式：初始化測試資料
        if settings.is_dev_auth:
            logger.info("Initializing dev data...")
            await repos.init_dev_data()
            logger.info("Dev data initialized")

    app.state.repos = repos

    yield

    # Shutdown
    logger.info("Shutting down API service")
    if settings.use_firestore and isinstance(repos, FirestoreRepositories):
        await repos.close()


app = FastAPI(
    title="Baby Weight Recorder API",
    description="嬰兒體重紀錄系統 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(babies.router)
app.include_router(weights.router)


@app.get("/")
async def root() -> dict[str, str]:
    """API 根路徑。"""
    return {"message": "Baby Weight Recorder API", "version": "0.1.0"}
