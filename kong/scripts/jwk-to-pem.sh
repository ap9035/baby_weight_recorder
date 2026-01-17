#!/bin/sh
# 將 JWK (n, e) 轉換為 PEM 格式的公鑰
# 使用 Python 一行命令（Kong Ubuntu 鏡像應該有 Python）

if [ $# -lt 2 ]; then
    echo "Usage: jwk-to-pem.sh <n> <e>" >&2
    exit 1
fi

N="$1"
E="$2"

# 使用 Python 處理 base64url 並生成 PEM
python3 <<EOF
import base64
import sys
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

try:
    # 從 base64url 解碼
    n_bytes = base64.urlsafe_b64decode("${N}" + "==")
    e_bytes = base64.urlsafe_b64decode("${E}" + "==")
    
    n = int.from_bytes(n_bytes, "big")
    e = int.from_bytes(e_bytes, "big")
    
    # 構建 RSA 公鑰
    public_numbers = RSAPublicNumbers(e, n)
    public_key = public_numbers.public_key(default_backend())
    
    # 序列化為 PEM
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    print(pem.decode("utf-8"))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
