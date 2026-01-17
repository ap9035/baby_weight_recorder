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

# 安裝 Python 和 cryptography（用於處理 JWKS）
# Kong 3.9 使用 Ubuntu 作為基礎鏡像
USER root

# 分步安裝，確保每個步驟成功
RUN apt-get update

# 安裝 Python3 和基本工具
RUN apt-get install -y --no-install-recommends python3 python3-pip python3-venv

# 安裝 cryptography 編譯依賴
RUN apt-get install -y --no-install-recommends python3-dev gcc libc6-dev libssl-dev libffi-dev

# 安裝 cryptography
RUN pip3 install --no-cache-dir --break-system-packages cryptography

# 清理編譯依賴
RUN apt-get purge -y python3-dev gcc libc6-dev libssl-dev libffi-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 創建腳本目錄
RUN mkdir -p /kong/scripts && \
    chown -R kong:kong /kong

# 複製配置檔模板
COPY --chown=kong:kong kong/kong.yml /kong/kong.template.yml

# 複製腳本
COPY --chown=kong:kong kong/scripts/sync-jwks.sh /kong/scripts/sync-jwks.sh
RUN chmod +x /kong/scripts/sync-jwks.sh

# 複製啟動腳本
COPY --chown=root:root kong/entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

# 切換回 kong 用戶
USER kong

EXPOSE 8000

ENTRYPOINT ["/custom-entrypoint.sh"]
