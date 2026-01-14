# 整合測試說明

## 測試類型

### 1. Auth → API 整合測試 (`test_auth_to_api.py`)
- **類型**: 單元級整合測試
- **需求**: 無需外部服務
- **運行**: `pytest tests/integration/test_auth_to_api.py`

### 2. Kong Gateway 路由測試 (`test_kong_gateway.py`)
- **類型**: 路由級整合測試
- **需求**: 無需外部服務（模擬路由）
- **運行**: `pytest tests/integration/test_kong_gateway.py`

### 3. Docker Compose E2E 測試 (`test_docker_compose.py`)
- **類型**: 端到端測試
- **需求**: Docker 或 Podman
- **運行**: `pytest tests/integration/test_docker_compose.py -m e2e`

## E2E 測試運行說明

### 前置需求

1. **Docker 或 Podman**
   - Docker: 需要 `docker-compose` 或 `docker compose`
   - Podman: 需要 `podman-compose`（推薦）

2. **端口可用性**
   - 8080: Firestore Emulator
   - 8081: API Service
   - 8082: Auth Service
   - 8000: Kong Gateway (Proxy)
   - 8001: Kong Gateway (Admin API)

### 運行測試

```bash
# 運行所有 E2E 測試
pytest tests/integration/test_docker_compose.py -m e2e -v

# 運行特定測試
pytest tests/integration/test_docker_compose.py::test_firestore_emulator_accessible -m e2e -v
```

### 手動啟動服務

如果需要手動啟動服務進行測試：

```bash
# 使用 Podman Compose
podman-compose -f docker-compose.yml up -d --build

# 或使用 Docker Compose
docker-compose -f docker-compose.yml up -d --build

# 檢查服務狀態
podman-compose -f docker-compose.yml ps

# 查看日誌
podman-compose -f docker-compose.yml logs -f

# 停止服務
podman-compose -f docker-compose.yml down -v
```

### 測試服務

```bash
# 測試 Firestore Emulator
curl http://localhost:8080

# 測試 Auth Service
curl http://localhost:8082/health

# 測試 API Service
curl http://localhost:8081/health

# 測試 Kong Gateway
curl http://localhost:8001/status
curl http://localhost:8000/health
```

### 已知問題

1. **Kong Gateway 啟動問題**
   - 如果 Kong 無法啟動，檢查 entrypoint 腳本權限
   - 確保 `kong/kong.yml` 中的環境變數已正確替換

2. **Podman 兼容性**
   - 測試會自動檢測並使用 `podman-compose`
   - 如果使用 Docker，確保 `DOCKER_HOST` 環境變數正確設置

3. **服務啟動時間**
   - 服務可能需要較長時間啟動（特別是首次構建）
   - 測試會等待最多 2 分鐘

### 故障排除

1. **服務無法啟動**
   ```bash
   # 檢查容器狀態
   podman ps -a
   
   # 查看特定服務日誌
   podman logs <container_name>
   ```

2. **端口衝突**
   ```bash
   # 檢查端口使用情況
   lsof -i :8080
   lsof -i :8081
   lsof -i :8082
   lsof -i :8000
   lsof -i :8001
   ```

3. **清理環境**
   ```bash
   # 停止並移除所有容器和卷
   podman-compose -f docker-compose.yml down -v
   
   # 清理未使用的資源
   podman system prune -a
   ```
