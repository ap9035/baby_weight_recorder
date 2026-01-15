#!/bin/bash
# Dev 環境 Smoke Test 腳本
# 測試所有服務的健康狀態和完整認證流程

set -e

echo "=== Dev 環境 Smoke Test ==="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 服務 URL
AUTH_URL="https://auth-service-dev-ggofz32qfa-de.a.run.app"
API_URL="https://weight-api-dev-ggofz32qfa-de.a.run.app"
KONG_URL="https://kong-gateway-dev-ggofz32qfa-de.a.run.app"

# 1. Health Checks
echo "1. Health Checks"
echo "----------------"
echo -n "Auth Service: "
AUTH_HEALTH=$(curl -s "$AUTH_URL/health")
if echo "$AUTH_HEALTH" | grep -q "healthy"; then
  echo -e "${GREEN}✅ OK${NC} - $AUTH_HEALTH"
else
  echo -e "${RED}❌ FAILED${NC} - $AUTH_HEALTH"
  exit 1
fi

echo -n "Weight API (expect 403): "
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$API_CODE" = "403" ] || [ "$API_CODE" = "200" ]; then
  echo -e "${GREEN}✅ OK${NC} - HTTP $API_CODE"
else
  echo -e "${YELLOW}⚠️  WARNING${NC} - HTTP $API_CODE"
fi

echo ""

# 2. Kong Gateway 路由測試
echo "2. Kong Gateway 路由測試"
echo "----------------"
echo -n "Kong -> Auth /.well-known/jwks.json: "
KONG_JWKS=$(curl -s "$KONG_URL/.well-known/jwks.json")
KID=$(echo "$KONG_JWKS" | jq -r '.keys[0].kid // "no keys"' 2>/dev/null || echo "invalid json")
if [ "$KID" != "no keys" ] && [ "$KID" != "invalid json" ]; then
  echo -e "${GREEN}✅ OK${NC} - kid: $KID"
else
  echo -e "${RED}❌ FAILED${NC} - $KONG_JWKS"
  exit 1
fi

echo ""

# 3. 完整認證流程
echo "3. 完整認證流程測試"
echo "----------------"
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@example.com"

echo "註冊新用戶 ($TEST_EMAIL)..."
REGISTER_RESPONSE=$(curl -s -X POST "$KONG_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"Test123456!\",
    \"display_name\": \"Test User\",
    \"invite_code\": \"BABY2026\"
  }")

if echo "$REGISTER_RESPONSE" | jq -e '.email' > /dev/null 2>&1; then
  echo -e "${GREEN}✅ 註冊成功${NC}"
  REGISTERED_EMAIL=$(echo "$REGISTER_RESPONSE" | jq -r '.email')
  echo "   Email: $REGISTERED_EMAIL"
  
  echo ""
  echo "登入取得 Token..."
  TOKEN_RESPONSE=$(curl -s -X POST "$KONG_URL/auth/token" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\": \"$TEST_EMAIL\",
      \"password\": \"Test123456!\"
    }")
  
  TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null || echo "")
  
  if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
    echo -e "${GREEN}✅ 登入成功，取得 Token${NC}"
    
    echo ""
    echo "使用 Token 訪問 API..."
    API_RESPONSE=$(curl -s -X GET "$KONG_URL/v1/babies" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$API_RESPONSE" | jq -e '. // empty' > /dev/null 2>&1; then
      echo -e "${GREEN}✅ API 訪問成功${NC}"
      BABY_COUNT=$(echo "$API_RESPONSE" | jq 'length' 2>/dev/null || echo "0")
      echo "   目前有 $BABY_COUNT 個嬰兒記錄"
    else
      echo -e "${YELLOW}⚠️  API 回應: $API_RESPONSE${NC}"
    fi
  else
    echo -e "${RED}❌ 登入失敗${NC}"
    echo "   回應: $TOKEN_RESPONSE"
    exit 1
  fi
else
  ERROR_MSG=$(echo "$REGISTER_RESPONSE" | jq -r '.detail // .message // "Unknown error"' 2>/dev/null || echo "$REGISTER_RESPONSE")
  if echo "$ERROR_MSG" | grep -q "already registered"; then
    echo -e "${YELLOW}⚠️  用戶已存在，嘗試登入...${NC}"
    # 嘗試登入
    TOKEN_RESPONSE=$(curl -s -X POST "$KONG_URL/auth/token" \
      -H "Content-Type: application/json" \
      -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"Test123456!\"
      }")
    TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null || echo "")
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
      echo -e "${GREEN}✅ 登入成功${NC}"
    else
      echo -e "${RED}❌ 登入失敗: $TOKEN_RESPONSE${NC}"
      exit 1
    fi
  else
    echo -e "${RED}❌ 註冊失敗${NC}"
    echo "   錯誤: $ERROR_MSG"
    exit 1
  fi
fi

echo ""
echo -e "${GREEN}=== Smoke Test 完成 ✅ ===${NC}"
