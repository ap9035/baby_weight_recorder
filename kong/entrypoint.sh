#!/bin/sh
# Kong 啟動腳本（Cloud Run 適用）

# Cloud Run 使用 PORT 環境變數
if [ -n "$PORT" ]; then
    export KONG_PROXY_LISTEN="0.0.0.0:$PORT"
fi

# 替換環境變數到 kong.yml
envsubst < /kong/kong.yml > /tmp/kong.yml
cp /tmp/kong.yml /kong/kong.yml

# 啟動 Kong
exec /docker-entrypoint.sh kong docker-start
