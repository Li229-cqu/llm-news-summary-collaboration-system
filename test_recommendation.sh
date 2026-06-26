#!/bin/bash

# 个性化推荐系统集成测试脚本
# 用于验证后端推荐接口是否正常工作

API_URL="http://localhost:8000"
PROFILE_API="$API_URL/api/profile"

echo "=========================================="
echo "个性化推荐系统测试"
echo "=========================================="
echo ""

# 测试 1：登录获取 token
echo "📝 测试 1：用户登录"
echo "POST $API_URL/api/auth/login"
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"123456"}')

echo "响应："
echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

# 提取 token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.token' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "❌ 登录失败，无法获取 token"
  exit 1
fi

echo "✅ 获取 token 成功: $TOKEN"
echo ""

# 测试 2：获取推荐接口 Swagger 定义
echo "📝 测试 2：检查推荐接口 Swagger 文档"
echo "GET $API_URL/openapi.json"
echo ""

SWAGGER=$(curl -s "$API_URL/openapi.json" | jq '.paths | keys[] | select(contains("recommendations"))' 2>/dev/null)

if [ -n "$SWAGGER" ]; then
  echo "✅ 推荐接口在 Swagger 中找到"
else
  echo "⚠️  推荐接口可能未在 Swagger 中注册"
fi
echo ""

# 测试 3：请求推荐接口 (limit=5)
echo "📝 测试 3：请求推荐接口"
echo "GET $PROFILE_API/recommendations?limit=5"
echo ""

RECOMMENDATIONS=$(curl -s -X GET "$PROFILE_API/recommendations?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo "响应："
echo "$RECOMMENDATIONS" | jq . 2>/dev/null || echo "$RECOMMENDATIONS"
echo ""

# 验证响应格式
CODE=$(echo "$RECOMMENDATIONS" | jq -r '.code' 2>/dev/null)
LIST_LEN=$(echo "$RECOMMENDATIONS" | jq '.data.list | length' 2>/dev/null)

if [ "$CODE" == "200" ]; then
  echo "✅ 接口返回成功（code=200）"
else
  echo "❌ 接口返回失败（code=$CODE）"
  exit 1
fi

echo "✅ 推荐列表长度：$LIST_LEN"

# 检查推荐理由
HAS_REASON=$(echo "$RECOMMENDATIONS" | jq '.data.list[0].recommendation_reason' 2>/dev/null)

if [ "$HAS_REASON" != "null" ] && [ -n "$HAS_REASON" ]; then
  echo "✅ 推荐理由存在"
  echo "   理由：$HAS_REASON"
else
  echo "⚠️  第一条推荐没有理由"
fi

# 检查推荐分数
HAS_SCORE=$(echo "$RECOMMENDATIONS" | jq '.data.list[0].recommendation_score' 2>/dev/null)

if [ "$HAS_SCORE" != "null" ]; then
  echo "✅ 推荐分数存在：$HAS_SCORE"
else
  echo "⚠️  第一条推荐没有分数"
fi

echo ""

# 测试 4：limit 边界测试
echo "📝 测试 4：limit 参数边界测试"
echo ""

for limit in 1 10 50 100; do
  RESPONSE=$(curl -s -X GET "$PROFILE_API/recommendations?limit=$limit" \
    -H "Authorization: Bearer $TOKEN")

  CODE=$(echo "$RESPONSE" | jq -r '.code' 2>/dev/null)
  ACTUAL_LEN=$(echo "$RESPONSE" | jq '.data.list | length' 2>/dev/null)

  if [ "$CODE" == "200" ]; then
    if [ "$limit" -le 50 ]; then
      EXPECTED_LEN=$limit
    else
      EXPECTED_LEN=50
    fi

    if [ "$ACTUAL_LEN" -le "$EXPECTED_LEN" ]; then
      echo "✅ limit=$limit: 返回 $ACTUAL_LEN 条（符合预期 ≤ $EXPECTED_LEN）"
    else
      echo "❌ limit=$limit: 返回 $ACTUAL_LEN 条（超出预期 $EXPECTED_LEN）"
    fi
  else
    echo "❌ limit=$limit: 接口返回失败（code=$CODE）"
  fi
done

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
