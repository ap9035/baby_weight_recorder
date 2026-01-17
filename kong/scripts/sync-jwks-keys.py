#!/usr/bin/env python3
"""從 JWKS 同步 keys 到 Kong 配置（靜態配置，非動態獲取）."""

import json
import sys
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
    pem = public_key.public_bytes(
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


def generate_kong_jwt_config(jwks_url: str) -> tuple[list[str], list[str]]:
    """從 JWKS 生成 Kong consumers 和 jwt_keys 配置."""
    # 獲取 JWKS
    jwks = fetch_jwks(jwks_url)
    keys = jwks.get("keys", [])

    if not keys:
        print("WARNING: No keys found in JWKS", file=sys.stderr)
        return [], []

    consumers = []
    jwt_keys = []

    for key in keys:
        if key.get("kty") != "RSA":
            print(f"WARNING: Skipping non-RSA key: {key.get('kty')}", file=sys.stderr)
            continue

        kid = key.get("kid", f"key-{len(consumers)}")
        consumer_name = f"jwt-consumer-{kid}"

        # 創建 consumer
        consumers.append(f"  - username: {consumer_name}")

        # 轉換 JWK 為 PEM
        try:
            pem_key = jwk_to_pem(key)
            
            # 格式化 PEM（每行加上適當的縮進）
            pem_lines = pem_key.strip().split("\n")
            pem_formatted = "\n".join(f"      {line}" for line in pem_lines)

            # 創建 JWT key（Kong DB-less mode 格式）
            jwt_keys.append(
                f"""  - consumer: {consumer_name}
    rsa_public_key: |
{pem_formatted}
    algorithm: RS256
    key: "{kid}\""""
            )
        except Exception as e:
            print(f"WARNING: Failed to convert key {kid} to PEM: {e}", file=sys.stderr)
            continue

    return consumers, jwt_keys


def update_kong_yml(kong_yml_path: str, jwks_url: str) -> None:
    """更新 kong.yml，添加從 JWKS 獲取的 consumers 和 jwt_keys."""
    # 讀取現有配置
    with open(kong_yml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 生成 consumers 和 jwt_keys
    consumers, jwt_keys = generate_kong_jwt_config(jwks_url)

    if not consumers or not jwt_keys:
        print("WARNING: No valid consumers/keys generated, keeping original config", file=sys.stderr)
        return

    # 構建 consumers 和 jwt_keys 區塊
    consumers_block = "consumers:\n" + "\n".join(consumers)
    jwt_keys_block = "jwt_keys:\n" + "\n".join(jwt_keys)

    # 檢查是否已有 consumers 區塊
    if "consumers:" in content:
        # 替換現有的 consumers 區塊
        import re
        # 匹配從 consumers: 開始到下一個頂級區塊（如 services: 或 plugins:）為止
        pattern = r"consumers:\s*\n(?:\s*-\s*username:.*\n)*"
        content = re.sub(pattern, consumers_block + "\n", content, flags=re.MULTILINE)
    else:
        # 在 services 定義之前插入 consumers
        content = content.replace(
            "# ==============================================================================\n# Services 定義\n# ==============================================================================",
            f"# ==============================================================================\n# Consumers 定義（JWT 驗證用）\n# ==============================================================================\n{consumers_block}\n\n# ==============================================================================\n# Services 定義\n# ==============================================================================",
        )

    # 檢查是否已有 jwt_keys 區塊
    if "jwt_keys:" in content:
        # 替換現有的 jwt_keys 區塊
        import re
        # 匹配從 jwt_keys: 開始到文件結尾或下一個頂級區塊
        pattern = r"jwt_keys:\s*\n(?:\s*-\s*consumer:.*\n(?:\s+\w+:.*\n)*)*"
        content = re.sub(pattern, jwt_keys_block + "\n", content, flags=re.MULTILINE | re.DOTALL)
    else:
        # 在 consumers 區塊後添加 jwt_keys
        content = content.replace(
            consumers_block,
            f"{consumers_block}\n\n# ==============================================================================\n# JWT Keys（從 JWKS 靜態配置）\n# ==============================================================================\n{jwt_keys_block}",
        )

    # 寫回配置
    with open(kong_yml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Successfully added {len(consumers)} consumers and {len(jwt_keys)} JWT keys to Kong config")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: sync-jwks-keys.py <kong_yml_path> <jwks_url>", file=sys.stderr)
        sys.exit(1)

    kong_yml_path = sys.argv[1]
    jwks_url = sys.argv[2]

    update_kong_yml(kong_yml_path, jwks_url)
