#!/bin/sh
# 從 Auth Service 的 JWKS 同步 keys 到 Kong
# 這是一個輔助腳本，用於在 Kong 啟動時同步 JWKS keys

set -e

if [ -z "$AUTH_SERVICE_URL" ]; then
    echo "ERROR: AUTH_SERVICE_URL is not set!"
    exit 1
fi

JWKS_URL="${AUTH_SERVICE_URL}/.well-known/jwks.json"
echo "Fetching JWKS from ${JWKS_URL}..."

# 獲取 JWKS
JWKS=$(curl -s "${JWKS_URL}")

if [ -z "$JWKS" ] || [ "$JWKS" = "null" ]; then
    echo "WARNING: Failed to fetch JWKS from ${JWKS_URL}"
    exit 0  # 不阻止 Kong 啟動，讓它之後重試
fi

echo "JWKS fetched successfully"
# 注意：在 DB-less mode 下，需要在 kong.yml 中預先配置 keys
# 這個腳本只是用於驗證 JWKS 可用性
# 實際的 keys 需要通過 kong.yml 配置
