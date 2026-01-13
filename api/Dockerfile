# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

# 安裝 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 設定工作目錄
WORKDIR /app

# 複製依賴檔案
COPY pyproject.toml uv.lock ./

# 建立虛擬環境並安裝依賴
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv sync --frozen --no-dev

# ============================================
# Runtime stage
# ============================================
FROM python:3.12-slim AS runtime

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH"

# 建立非 root 使用者
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# 設定工作目錄
WORKDIR /app

# 從 builder 複製虛擬環境
COPY --from=builder /opt/venv /opt/venv

# 複製應用程式碼
COPY api/ ./api/

# 設定使用者
USER appuser

# 暴露埠號
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# 啟動應用
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
