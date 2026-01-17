#!/bin/sh
# 從 JWKS 同步 keys 到 Kong 配置
# 使用 shell + curl + Python（一行命令）來處理
# 注意：不設置 set -e，避免錯誤導致容器無法啟動

if [ $# -lt 2 ]; then
    echo "Usage: sync-jwks.sh <kong_yml_path> <jwks_url>" >&2
    exit 1
fi

KONG_YML="$1"
JWKS_URL="$2"

echo "Fetching JWKS from ${JWKS_URL}..."

# 獲取 JWKS
JWKS_JSON=$(curl -s "${JWKS_URL}")

if [ -z "$JWKS_JSON" ] || [ "$JWKS_JSON" = "null" ]; then
    echo "ERROR: Failed to fetch JWKS from ${JWKS_URL}" >&2
    exit 1
fi

# 使用 Python 處理 JWKS 並生成 Kong consumers 和 jwt_secrets
python3 <<PYTHON_SCRIPT
import json
import sys
import base64
from pathlib import Path

try:
    # 從 shell 變數獲取路徑
    kong_yml_path = "${KONG_YML}"
    jwks_json_str = '''${JWKS_JSON}'''
    
    jwks = json.loads(jwks_json_str)
    keys = jwks.get("keys", [])
    
    if not keys:
        print("WARNING: No keys found in JWKS", file=sys.stderr)
        sys.exit(0)
    
    # 讀取現有配置
    with open(kong_yml_path, "r") as f:
        content = f.read()
    
    # 生成 consumers 和 jwt_secrets
    consumers = []
    jwt_secrets = []
    
    for key in keys:
        if key.get("kty") != "RSA":
            continue
        
        kid = key.get("kid", f"key-{len(consumers)}")
        # 使用 kid 作為 consumer key（JWT 中的 kid 會匹配這個）
        consumer_name = f"jwt-consumer-{kid}"
        
        consumers.append(f"  - username: {consumer_name}")
        
        # 轉換 JWK 為 PEM
        try:
            from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            
            n_bytes = base64.urlsafe_b64decode(key["n"] + "==")
            e_bytes = base64.urlsafe_b64decode(key["e"] + "==")
            
            n = int.from_bytes(n_bytes, "big")
            e = int.from_bytes(e_bytes, "big")
            
            public_numbers = RSAPublicNumbers(e, n)
            public_key = public_numbers.public_key(default_backend())
            
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")
            
            # 格式化 PEM（每行加上縮進）
            pem_lines = pem.strip().split("\n")
            pem_formatted = "\n".join(f"          {line}" for line in pem_lines)
            
            # 創建 JWT secret（使用 kid 作為 key，這樣 JWT 中的 kid 可以匹配）
            # YAML 格式：jwt_secrets 需要正確的縮進（2 個空格）
            jwt_secrets.append(f"""    jwt_secrets:
      - algorithm: RS256
        key: "{kid}"
        rsa_public_key: |
{pem_formatted}""")
            
        except Exception as e:
            print(f"WARNING: Failed to convert key {kid}: {e}", file=sys.stderr)
            continue
    
    if not consumers or not jwt_secrets:
        print("WARNING: No valid consumers/secrets generated", file=sys.stderr)
        sys.exit(0)
    
    # 合併 consumers 和 jwt_secrets
    consumers_block = "consumers:\n" + "\n".join(consumers)
    
    # 將 jwt_secrets 添加到對應的 consumer
    # 為每個 consumer 添加對應的 jwt_secret
    full_consumers = []
    for i, consumer_line in enumerate(consumers):
        username = consumer_line.split("username: ")[1].strip()
        jwt_secret = jwt_secrets[i] if i < len(jwt_secrets) else ""
        # 正確的 YAML 格式：每個 consumer 包含 username 和 jwt_secrets
        consumer_block = f"  - username: {username}\n{jwt_secret}"
        full_consumers.append(consumer_block)
    
    # 使用單個換行符連接（不是雙換行符），避免 YAML 格式錯誤
    consumers_block = "consumers:\n" + "\n".join(full_consumers)
    
    # 檢查是否已有 consumers 區塊
    import re
    if "consumers:" in content:
        # 替換現有的
        pattern = r"consumers:\s*\n(?:\s*-\s*username:.*\n(?:\s+jwt_secrets:.*\n(?:\s+-\s+algorithm:.*\n(?:\s+key:.*\n)?(?:\s+rsa_public_key:.*\n)*)*)*)*"
        content = re.sub(pattern, consumers_block + "\n", content, flags=re.MULTILINE | re.DOTALL)
    else:
        # 在 services 定義之前插入
        content = content.replace(
            "# ==============================================================================\n# Services 定義\n# ==============================================================================",
            f"# ==============================================================================\n# Consumers 定義（JWT 驗證用）\n# ==============================================================================\n{consumers_block}\n\n# ==============================================================================\n# Services 定義\n# ==============================================================================",
        )
    
    # 寫回配置
    with open(kong_yml_path, "w") as f:
        f.write(content)
    
    print(f"✅ Successfully added {len(consumers)} consumers and JWT secrets")
    
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT
