# Kong Gateway Dockerfile
# 用於 Cloud Run 部署

FROM kong:3.6-alpine

# 設定環境變數
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/kong/kong.yml
ENV KONG_PROXY_ACCESS_LOG=/dev/stdout
ENV KONG_ADMIN_ACCESS_LOG=/dev/stdout
ENV KONG_PROXY_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_ERROR_LOG=/dev/stderr
ENV KONG_PROXY_LISTEN=0.0.0.0:8000
ENV KONG_ADMIN_LISTEN=off

# 複製配置檔
COPY kong.yml /kong/kong.yml

# Cloud Run 使用 PORT 環境變數
# 需要在啟動時動態設定 KONG_PROXY_LISTEN
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
