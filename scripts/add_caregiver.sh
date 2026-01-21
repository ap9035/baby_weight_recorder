#!/bin/bash
# 新增照顧者腳本（需要 owner 權限）
#
# 使用方式:
#   ./add_caregiver.sh <baby_id> <caregiver_email> [role] [owner_email] [owner_password]
#
# 參數:
#   baby_id          - 嬰兒 ID
#   caregiver_email  - 要新增的照顧者 Email
#   role             - 角色: editor（可編輯）或 viewer（只能查看），預設 editor
#   owner_email      - Owner 的 Email（預設 test@example.com）
#   owner_password   - Owner 的密碼（預設 Test123456!）
#
# 範例:
#   ./add_caregiver.sh 01JHRP7XYZ spouse@example.com editor
#   ./add_caregiver.sh 01JHRP7XYZ grandma@example.com viewer owner@example.com MyPass123!

KONG_URL="https://kong-gateway-dev-ggofz32qfa-de.a.run.app"

# 參數檢查
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "❌ 使用方式: $0 <baby_id> <caregiver_email> [role] [owner_email] [owner_password]"
    echo ""
    echo "範例:"
    echo "  $0 01JHRP7XYZ spouse@example.com editor"
    echo "  $0 01JHRP7XYZ grandma@example.com viewer owner@example.com MyPass123!"
    exit 1
fi

BABY_ID="$1"
CAREGIVER_EMAIL="$2"
ROLE="${3:-editor}"
OWNER_EMAIL="${4:-test@example.com}"
OWNER_PASSWORD="${5:-Test123456!}"

echo "================================================"
echo "新增照顧者"
echo "================================================"
echo "Baby ID:         $BABY_ID"
echo "照顧者 Email:    $CAREGIVER_EMAIL"
echo "角色:            $ROLE"
echo "Owner Email:     $OWNER_EMAIL"
echo "================================================"
echo ""

# 驗證角色
if [ "$ROLE" != "editor" ] && [ "$ROLE" != "viewer" ]; then
    echo "❌ 角色必須是 'editor' 或 'viewer'"
    exit 1
fi

echo "🔐 登入獲取 JWT token..."

# 登入
LOGIN_RESPONSE=$(curl -s -X POST "${KONG_URL}/auth/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${OWNER_EMAIL}\",
    \"password\": \"${OWNER_PASSWORD}\"
  }")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ 登入失敗"
    echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"
    exit 1
fi

echo "✅ 登入成功"
echo ""

echo "👤 新增照顧者..."

# 新增成員
ADD_RESPONSE=$(curl -s -X POST "${KONG_URL}/v1/babies/${BABY_ID}/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${CAREGIVER_EMAIL}\",
    \"role\": \"${ROLE}\"
  }")

# 檢查結果
ERROR_DETAIL=$(echo "$ADD_RESPONSE" | jq -r '.detail' 2>/dev/null)

if [ "$ERROR_DETAIL" != "null" ] && [ -n "$ERROR_DETAIL" ]; then
    echo ""
    echo "❌ 新增失敗: $ERROR_DETAIL"
    echo ""
    echo "完整回應:"
    echo "$ADD_RESPONSE" | jq . 2>/dev/null || echo "$ADD_RESPONSE"
    exit 1
fi

USER_ID=$(echo "$ADD_RESPONSE" | jq -r '.internal_user_id' 2>/dev/null)

if [ -n "$USER_ID" ] && [ "$USER_ID" != "null" ]; then
    echo ""
    echo "✅ 新增照顧者成功！"
    echo ""
    echo "照顧者資訊:"
    echo "$ADD_RESPONSE" | jq . 2>/dev/null || echo "$ADD_RESPONSE"
else
    echo ""
    echo "❌ 新增失敗"
    echo "$ADD_RESPONSE" | jq . 2>/dev/null || echo "$ADD_RESPONSE"
    exit 1
fi
