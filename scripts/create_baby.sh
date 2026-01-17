#!/bin/bash
# 創建嬰兒腳本（需要先註冊用戶）

KONG_URL="https://kong-gateway-dev-ggofz32qfa-de.a.run.app"

# 參數
EMAIL="${1:-test@example.com}"
PASSWORD="${2:-Test123456!}"
BABY_NAME="${3:-測試嬰兒}"
BIRTH_DATE="${4:-2024-01-01}"
GENDER="${5:-male}"

echo "登入獲取 JWT token..."
echo "Email: $EMAIL"
echo ""

# 登入
LOGIN_RESPONSE=$(curl -s -X POST "${KONG_URL}/auth/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "❌ 登入失敗"
  echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✅ 登入成功"
echo ""

echo "創建嬰兒..."
echo "名稱: $BABY_NAME"
echo "出生日期: $BIRTH_DATE"
echo "性別: $GENDER"
echo ""

# 創建嬰兒
CREATE_RESPONSE=$(curl -s -X POST "${KONG_URL}/v1/babies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${BABY_NAME}\",
    \"birth_date\": \"${BIRTH_DATE}\",
    \"gender\": \"${GENDER}\"
  }")

echo "$CREATE_RESPONSE" | jq . 2>/dev/null || echo "$CREATE_RESPONSE"

BABY_ID=$(echo "$CREATE_RESPONSE" | jq -r '.baby_id' 2>/dev/null)

if [ -n "$BABY_ID" ] && [ "$BABY_ID" != "null" ]; then
  echo ""
  echo "✅ 創建嬰兒成功！"
  echo "Baby ID: $BABY_ID"
else
  echo ""
  echo "❌ 創建嬰兒失敗"
  exit 1
fi
