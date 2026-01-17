#!/bin/sh
# Kong 啟動腳本（Cloud Run 適用）
# 注意：不設置 set -e，避免腳本執行失敗導致容器無法啟動

# Cloud Run 使用 PORT 環境變數
if [ -n "$PORT" ]; then
    export KONG_PROXY_LISTEN="0.0.0.0:$PORT"
fi

# 檢查環境變數
echo "Configuring Kong with:"
echo "  AUTH_SERVICE_URL: ${AUTH_SERVICE_URL:-not set}"
echo "  API_SERVICE_URL: ${API_SERVICE_URL:-not set}"

# 檢查環境變數是否設置
if [ -z "$AUTH_SERVICE_URL" ] || [ -z "$API_SERVICE_URL" ]; then
    echo "ERROR: AUTH_SERVICE_URL or API_SERVICE_URL is not set!"
    exit 1
fi

# 檢查模板文件是否存在
if [ ! -f /kong/kong.template.yml ]; then
    echo "ERROR: /kong/kong.template.yml not found!"
    exit 1
fi

# 替換環境變數到 kong.yml
sed -e "s|AUTH_SERVICE_URL_PLACEHOLDER|${AUTH_SERVICE_URL}|g" \
    -e "s|API_SERVICE_URL_PLACEHOLDER|${API_SERVICE_URL}|g" \
    /kong/kong.template.yml > /kong/kong.yml

# 從 JWKS 同步 keys 並添加到 Kong 配置
if command -v python3 >/dev/null 2>&1 && [ -f /kong/scripts/sync-jwks.sh ]; then
    echo "Fetching JWKS and generating Kong consumers/jwt_secrets..."
    JWKS_URL="${AUTH_SERVICE_URL}/.well-known/jwks.json"
    /kong/scripts/sync-jwks.sh /kong/kong.yml "$JWKS_URL"
    if [ $? -eq 0 ]; then
        echo "✅ Successfully synced JWT keys from JWKS"
    else
        echo "⚠️  Failed to sync JWT keys, Kong JWT plugin may not work"
    fi
else
    echo "⚠️  Python3 or sync-jwks.sh not available, skipping JWT keys sync"
    echo "⚠️  JWT plugin will not work without keys!"
fi

# 檢查替換是否成功
if [ ! -f /kong/kong.yml ]; then
    echo "ERROR: Failed to create /kong/kong.yml!"
    exit 1
fi

# 驗證替換結果
if grep -q "AUTH_SERVICE_URL_PLACEHOLDER\|API_SERVICE_URL_PLACEHOLDER" /kong/kong.yml; then
    echo "WARNING: Some placeholders were not replaced!"
    echo "Remaining placeholders:"
    grep "AUTH_SERVICE_URL_PLACEHOLDER\|API_SERVICE_URL_PLACEHOLDER" /kong/kong.yml || true
fi

echo "Kong configuration (first 50 lines):"
head -50 /kong/kong.yml

# 啟動 Kong
exec /docker-entrypoint.sh kong docker-start
