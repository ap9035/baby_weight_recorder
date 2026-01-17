#!/bin/sh
# 從 Auth Service 的 JWKS 同步 keys 到 Kong 配置
# 在 Kong 啟動前執行，動態生成包含 JWKS keys 的 kong.yml

set -e

if [ -z "$AUTH_SERVICE_URL" ]; then
    echo "ERROR: AUTH_SERVICE_URL is not set!"
    exit 1
fi

JWKS_URL="${AUTH_SERVICE_URL}/.well-known/jwks.json"
echo "Fetching JWKS from ${JWKS_URL}..."

# 獲取 JWKS
JWKS_JSON=$(curl -s "${JWKS_URL}")

if [ -z "$JWKS_JSON" ] || [ "$JWKS_JSON" = "null" ]; then
    echo "WARNING: Failed to fetch JWKS from ${JWKS_URL}"
    exit 0  # 不阻止 Kong 啟動
fi

echo "JWKS fetched successfully"

# 檢查是否有 Python 可用於處理 JSON
if command -v python3 >/dev/null 2>&1; then
    # 使用 Python 解析 JWKS 並生成 Kong consumers 和 keys 配置
    python3 <<EOF
import json
import sys

try:
    jwks = json.loads('${JWKS_JSON}')
    keys = jwks.get('keys', [])
    
    if not keys:
        print("WARNING: No keys found in JWKS")
        sys.exit(0)
    
    # 生成 Kong consumers 和 keys 配置（YAML 格式）
    consumers_config = []
    keys_config = []
    
    for idx, key in enumerate(keys):
        kid = key.get('kid', f'key-{idx}')
        consumer_name = f'jwt-consumer-{kid}'
        
        consumers_config.append({
            'username': consumer_name,
        })
        
        # 提取 RSA 公鑰參數
        if key.get('kty') == 'RSA':
            n = key.get('n')
            e = key.get('e')
            
            if n and e:
                # Kong JWT 插件需要完整的 PEM 格式公鑰
                # 但我們只有 JWK 格式（n, e），需要轉換
                # 這裡先記錄，後續需要轉換為 PEM
                keys_config.append({
                    'consumer': consumer_name,
                    'rsa_public_key': f'-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----',  # 需要從 n, e 生成
                    'algorithm': 'RS256',
                    'key': kid
                })
    
    print("Consumers and keys configuration would be generated here")
    print(f"Found {len(keys)} keys in JWKS")
    
except Exception as e:
    print(f"ERROR parsing JWKS: {e}")
    sys.exit(1)
EOF
else
    echo "WARNING: python3 not available, skipping JWKS key synchronization"
fi

echo "Note: Kong JWT plugin requires pre-configured consumers and keys"
echo "This script can be extended to dynamically generate kong.yml with keys"
