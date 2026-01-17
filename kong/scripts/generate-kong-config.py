#!/usr/bin/env python3
"""從 JWKS 生成 Kong 配置（包含 consumers 和 keys）."""

import json
import sys
import os
import urllib.request
from base64 import urlsafe_b64decode
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def jwk_to_pem(jwk: dict) -> str:
    """將 JWK 轉換為 PEM 格式的公鑰."""
    # 從 base64url 解碼
    n_bytes = urlsafe_b64decode(jwk["n"] + "==")
    e_bytes = urlsafe_b64decode(jwk["e"] + "==")

    n = int.from_bytes(n_bytes, "big")
    e = int.from_bytes(e_bytes, "big")

    # 構建 RSA 公鑰
    public_numbers = RSAPublicNumbers(e, n)
    public_key = public_numbers.public_key(default_backend())

    # 序列化為 PEM
    pem = public_key.public_key_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem.decode("utf-8")


def fetch_jwks(jwks_url: str) -> dict:
    """從 URL 獲取 JWKS."""
    try:
        with urllib.request.urlopen(jwks_url, timeout=5) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"ERROR: Failed to fetch JWKS from {jwks_url}: {e}", file=sys.stderr)
        sys.exit(1)


def update_kong_config(config_path: str, jwks_url: str) -> None:
    """更新 Kong 配置，添加從 JWKS 獲取的 consumers 和 keys."""
    # 讀取現有配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = f.read()

    # 獲取 JWKS
    jwks = fetch_jwks(jwks_url)
    keys = jwks.get("keys", [])

    if not keys:
        print("WARNING: No keys found in JWKS", file=sys.stderr)
        return

    # 生成 consumers 和 jwt_keys
    consumers = []
    jwt_keys = []

    for key in keys:
        if key.get("kty") != "RSA":
            continue

        kid = key.get("kid", f"key-{len(consumers)}")
        consumer_name = f"jwt-consumer-{kid}"

        # 創建 consumer
        consumers.append(f"  - username: {consumer_name}")

        # 轉換 JWK 為 PEM
        try:
            pem_key = jwk_to_pem(key)

            # 創建 JWT key（Kong DB-less mode 格式）
            jwt_keys.append(
                f"""  - consumer: {consumer_name}
    rsa_public_key: |
{pem_key.split(chr(10))[0]}
{chr(10).join('      ' + line for line in pem_key.split(chr(10))[1:] if line.strip())}
    algorithm: RS256
    key: "{kid}\""""
            )
        except Exception as e:
            print(f"WARNING: Failed to convert key {kid} to PEM: {e}", file=sys.stderr)
            continue

    if not consumers:
        print("WARNING: No valid RSA keys found in JWKS", file=sys.stderr)
        return

    # 檢查是否已有 consumers 區塊
    if "consumers:" in config:
        # 替換現有的 consumers
        import re

        # 找到 consumers 區塊並替換
        pattern = r"consumers:\s*\n(?:\s*-\s*username:.*\n)*"
        replacement = "consumers:\n" + "\n".join(consumers) + "\n"
        config = re.sub(pattern, replacement, config, flags=re.MULTILINE)
    else:
        # 在 services 定義之前插入 consumers
        config = config.replace(
            "# ==============================================================================\n# Services 定義\n# ==============================================================================",
            f"# ==============================================================================\n# Consumers 定義（JWT 驗證用）\n# ==============================================================================\nconsumers:\n"
            + "\n".join(consumers)
            + "\n\n# ==============================================================================\n# Services 定義\n# ==============================================================================",
        )

    # 添加 jwt_keys（需要在 consumers 之後）
    if "jwt_keys:" not in config:
        # 在 consumers 區塊後添加 jwt_keys
        config = config.replace(
            "consumers:\n" + "\n".join(consumers),
            "consumers:\n"
            + "\n".join(consumers)
            + "\n\n# ==============================================================================\n# JWT Keys（從 JWKS 動態生成）\n# ==============================================================================\njwt_keys:\n"
            + "\n".join(jwt_keys),
        )

    # 寫回配置
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config)

    print(f"✅ Successfully added {len(consumers)} consumers and {len(jwt_keys)} JWT keys")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: generate-kong-config.py <kong_yml_path> <jwks_url>")
        sys.exit(1)

    config_path = sys.argv[1]
    jwks_url = sys.argv[2]

    update_kong_config(config_path, jwks_url)
