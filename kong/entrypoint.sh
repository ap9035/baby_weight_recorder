#!/bin/sh
# Kong 啟動腳本（Cloud Run 適用）
set -e

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
