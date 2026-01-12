"""Baby Weight Recorder - Auth Service.

認證服務, 提供使用者註冊, 登入和 JWT 簽發.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.app.routers import health


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """應用程式生命週期管理."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Baby Weight Recorder Auth",
    description="嬰兒體重紀錄系統 認證服務",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 生產環境應限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(health.router, tags=["Health"])


@app.get("/")
async def root() -> dict[str, str]:
    """Auth Service 根路徑。"""
    return {"message": "Baby Weight Recorder Auth Service", "version": "0.1.0"}
