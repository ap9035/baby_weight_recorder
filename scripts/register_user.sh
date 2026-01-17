#!/bin/bash
# 簡單的用戶註冊腳本

KONG_URL="https://kong-gateway-dev-ggofz32qfa-de.a.run.app"

# 參數
EMAIL="${1:-test@example.com}"
PASSWORD="${2:-Test123456!}"
DISPLAY_NAME="${3:-Test User}"
INVITE_CODE="${4:-BABY2026}"  # 可選參數，預設為 BABY2026

echo "註冊用戶..."
echo "Email: $EMAIL"
echo "Display Name: $DISPLAY_NAME"
echo ""

RESPONSE=$(curl -s -X POST "${KONG_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\",
    \"display_name\": \"${DISPLAY_NAME}\",
    \"invite_code\": \"${INVITE_CODE}\"
  }")

echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
