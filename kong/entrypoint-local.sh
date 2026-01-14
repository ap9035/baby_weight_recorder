#!/bin/sh
# Kong 本地開發啟動腳本（Docker Compose 適用）
set -e

# 替換環境變數到 kong.yml
sed -e "s|AUTH_SERVICE_URL_PLACEHOLDER|${AUTH_SERVICE_URL}|g" \
    -e "s|API_SERVICE_URL_PLACEHOLDER|${API_SERVICE_URL}|g" \
    /kong/kong.yml.template > /kong/kong.yml

# 啟動 Kong
exec /docker-entrypoint.sh kong docker-start
