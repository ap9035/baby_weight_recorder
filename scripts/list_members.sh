#!/bin/bash
# 列出嬰兒的所有照顧者
#
# 使用方式:
#   ./list_members.sh <baby_id> [email] [password]
#
# 範例:
#   ./list_members.sh 01JHRP7XYZ
#   ./list_members.sh 01JHRP7XYZ owner@example.com MyPass123!

KONG_URL="https://kong-gateway-dev-ggofz32qfa-de.a.run.app"

# 參數檢查
if [ -z "$1" ]; then
    echo "❌ 使用方式: $0 <baby_id> [email] [password]"
    echo ""
    echo "範例:"
    echo "  $0 01JHRP7XYZ"
    echo "  $0 01JHRP7XYZ owner@example.com MyPass123!"
    exit 1
fi

BABY_ID="$1"
EMAIL="${2:-test@example.com}"
PASSWORD="${3:-Test123456!}"

echo "🔐 登入中..."

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

echo "================================================"
echo "Baby ID: $BABY_ID 的所有照顧者"
echo "================================================"
echo ""

# 取得成員列表
MEMBERS_RESPONSE=$(curl -s -X GET "${KONG_URL}/v1/babies/${BABY_ID}/members" \
  -H "Authorization: Bearer $TOKEN")

# 檢查錯誤
ERROR_DETAIL=$(echo "$MEMBERS_RESPONSE" | jq -r '.detail' 2>/dev/null)

if [ "$ERROR_DETAIL" != "null" ] && [ -n "$ERROR_DETAIL" ]; then
    echo "❌ 取得失敗: $ERROR_DETAIL"
    exit 1
fi

# 格式化輸出
echo "$MEMBERS_RESPONSE" | jq -r '.[] | "角色: \(.role)\nEmail: \(.email // "N/A")\n名稱: \(.display_name // "N/A")\n加入時間: \(.joined_at)\n---"' 2>/dev/null

if [ $? -ne 0 ]; then
    echo "$MEMBERS_RESPONSE" | jq . 2>/dev/null || echo "$MEMBERS_RESPONSE"
fi
