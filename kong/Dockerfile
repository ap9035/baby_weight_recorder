# Kong Gateway Dockerfile
# 用於 Cloud Run 部署

FROM kong:3.9

# 以 root 身份設定檔案
USER root

# 設定環境變數
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/kong/kong.yml
ENV KONG_PROXY_ACCESS_LOG=/dev/stdout
ENV KONG_ADMIN_ACCESS_LOG=/dev/stdout
ENV KONG_PROXY_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_ERROR_LOG=/dev/stderr
ENV KONG_PROXY_LISTEN=0.0.0.0:8000
ENV KONG_ADMIN_LISTEN=off

# 創建腳本目錄
USER root
RUN mkdir -p /kong/scripts && \
    chown -R kong:kong /kong

# 複製配置檔模板
COPY --chown=kong:kong kong/kong.yml /kong/kong.template.yml

# 不需要 Python 腳本，移除相關配置

# 複製啟動腳本
COPY --chown=root:root kong/entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

# 切換回 kong 用戶
USER kong

EXPOSE 8000

ENTRYPOINT ["/custom-entrypoint.sh"]
