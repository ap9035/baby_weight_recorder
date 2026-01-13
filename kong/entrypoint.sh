#!/bin/sh
# Kong 啟動腳本（Cloud Run 適用）
set -e

# Cloud Run 使用 PORT 環境變數
if [ -n "$PORT" ]; then
    export KONG_PROXY_LISTEN="0.0.0.0:$PORT"
fi

# 替換環境變數到 kong.yml
echo "Configuring Kong with:"
echo "  AUTH_SERVICE_URL: ${AUTH_SERVICE_URL:-not set}"
echo "  API_SERVICE_URL: ${API_SERVICE_URL:-not set}"

sed -e "s|AUTH_SERVICE_URL_PLACEHOLDER|${AUTH_SERVICE_URL}|g" \
    -e "s|API_SERVICE_URL_PLACEHOLDER|${API_SERVICE_URL}|g" \
    /kong/kong.template.yml > /kong/kong.yml

echo "Kong configuration:"
cat /kong/kong.yml

# 啟動 Kong
exec /docker-entrypoint.sh kong docker-start
