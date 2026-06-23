#!/bin/bash

# AI EchoDrive API 테스트 스크립트
# 사용: bash test_api.sh

BASE_URL="http://localhost:8000"
USER_ID="demo_user"
PASSWORD="DemoPass123"

echo "🚀 AI EchoDrive API 테스트"
echo "================================"

# 1. 헬스 체크
echo -e "\n1️⃣ 헬스 체크"
curl -s $BASE_URL/health | python -m json.tool
echo "✅ 서버 정상"

# 2. API 목록
echo -e "\n2️⃣ API 엔드포인트 목록"
curl -s $BASE_URL/ | python -m json.tool | head -30
echo "... (총 26개 엔드포인트)"

# 3. 회원가입 또는 로그인
echo -e "\n3️⃣ 회원가입 시도"
SIGNUP_RESPONSE=$(curl -s -X POST $BASE_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"password\": \"$PASSWORD\", \"email\": \"demo@example.com\"}")

# 회원가입 실패 시 로그인 시도
if echo "$SIGNUP_RESPONSE" | grep -q "already exists"; then
  echo "👤 사용자가 이미 존재합니다. 로그인 시도..."
  LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\", \"password\": \"$PASSWORD\"}")
  TOKEN=$(echo $LOGIN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
  echo "✅ 로그인 성공"
else
  TOKEN=$(echo $SIGNUP_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
  echo "✅ 회원가입 성공"
fi

if [ -z "$TOKEN" ]; then
  echo "❌ 인증 실패"
  exit 1
fi

echo "📝 토큰: ${TOKEN:0:20}..."

# 4. 사용자 프로필
echo -e "\n4️⃣ 사용자 프로필"
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/user/profile | python -m json.tool

# 5. 사용자 설정
echo -e "\n5️⃣ 사용자 설정"
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/user/settings | python -m json.tool

# 6. 약점 저장
echo -e "\n6️⃣ 약점 저장 (3개)"
for i in 1 2 3; do
  curl -s -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"$USER_ID\", \"phrase\": \"Test phrase $i\", \"timestamp\": $((i*10))}" \
    $BASE_URL/weaknesses > /dev/null
done
echo "✅ 저장 완료"

# 7. 약점 조회
echo -e "\n7️⃣ 약점 목록 조회"
curl -s -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/weaknesses | python -m json.tool | head -40

# 8. 문장 설명
echo -e "\n8️⃣ 문장 설명"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/phrases/explain?phrase=How%20are%20you" | python -m json.tool

# 9. 학습 진행도
echo -e "\n9️⃣ 학습 진행도 저장"
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/learning/progress?video_id=test_video&day=1" | python -m json.tool
echo "✅ 저장 완료"

# 10. 학습 진행도 조회
echo -e "\n🔟 학습 진행도 조회"
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/learning/progress/test_video" | python -m json.tool

echo -e "\n================================"
echo "✅ 모든 테스트 완료!"
echo "================================"
