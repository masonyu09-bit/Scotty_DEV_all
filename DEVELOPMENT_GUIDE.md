# 🚀 AI EchoDrive 개발 확인 가이드

개발한 백엔드를 확인하고 테스트하는 방법들을 설명합니다.

## 📋 목차
1. [빠른 확인 (30초)](#빠른-확인-30초)
2. [상세 테스트 (5분)](#상세-테스트-5분)
3. [데이터베이스 확인 (2분)](#데이터베이스-확인-2분)
4. [Swagger UI로 테스트 (브라우저)](#swagger-ui로-테스트-브라우저)
5. [로그 확인 (트러블슈팅)](#로그-확인-트러블슈팅)

---

## 빠른 확인 (30초)

### 1. 서버 실행 중인지 확인
```bash
ps aux | grep "python main.py" | grep -v grep
```

**예상 출력:**
```
root  7610  0.9  0.3  74344 65164 ?  S  02:11  0:00  python main.py
✅ 프로세스 보이면 실행 중
```

### 2. 헬스 체크 (가장 빠른 확인)
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

**예상 출력:**
```json
{
    "status": "healthy",
    "service": "AI EchoDrive Backend v2.0.0"
}
```

✅ **200 상태코드 + "healthy" 응답 = 정상 작동**

---

## 상세 테스트 (5분)

### 방법 1: 자동 테스트 스크립트 (권장)
```bash
bash test_api.sh
```

**테스트 항목:**
- ✅ 헬스 체크
- ✅ API 엔드포인트 목록
- ✅ 회원가입/로그인
- ✅ 사용자 프로필
- ✅ 약점 저장/조회
- ✅ 문장 설명
- ✅ 학습 진행도

**예상 시간:** 5-10초

### 방법 2: 포괄적 테스트
```bash
python test_client_v2.py
```

**테스트 항목:** 26개 모든 엔드포인트

**예상 출력:**
```
🚀 AI EchoDrive v2 - Full Test Suite
✅ Health Check: OK
✅ Sign Up: successful
✅ User Profile: retrieved
✅ Save Weakness: 5개 저장
✅ Get Weaknesses: 5개 조회
...
✅ Test Suite Complete!
```

### 방법 3: 기본 테스트
```bash
python test_client.py
```

---

## 데이터베이스 확인 (2분)

### 데이터베이스 상태 확인
```bash
python check_database.py
```

**확인 항목:**
- ✅ 파일 위치 및 크기
- ✅ 테이블 목록
- ✅ 데이터 샘플
- ✅ 통계 정보
- ✅ 사용자별 상세 통계

**예상 출력:**
```
======================================================================
🔍 AI EchoDrive 데이터베이스 상태 확인
======================================================================
✅ 데이터베이스 위치: /home/user/Scotty_DEV_all/echodrive.db
✅ 파일 크기: 48.00 KB
✅ 마지막 수정: 2026-06-23 03:01:10

📑 테이블 목록 (5개):
   - users
   - weaknesses
   - learning_progress
   - user_settings

📊 통계
👥 전체 사용자: 2명
📝 저장된 약점: 8개
🎓 학습한 영상: 2개

👤 사용자별 상세 통계
demo_user: 약점 3개, 학습 1개 영상
test_user_2024: 약점 5개, 학습 1개 영상
```

### SQLite CLI로 직접 확인
```bash
sqlite3 echodrive.db

# 데이터베이스 내에서:
> SELECT * FROM users;
> SELECT * FROM weaknesses LIMIT 5;
> SELECT COUNT(*) FROM learning_progress;
> .quit
```

---

## Swagger UI로 테스트 (브라우저)

### 방법: 브라우저에서 열기

**URL:**
```
http://localhost:8000/docs
```

또는
```
http://localhost:8000/redoc
```

### 장점:
- 🎨 보기 좋은 인터페이스
- 🧪 브라우저에서 직접 테스트 가능
- 📚 자동 생성 API 문서
- 🔒 인증 토큰 입력 가능

### 사용 방법:

1. **`/auth/signup` 엔드포인트 클릭**
   ```json
   {
     "user_id": "test_user",
     "password": "TestPassword123",
     "email": "test@example.com"
   }
   ```
   → "Try it out" → Execute

2. **응답에서 토큰 복사**
   ```json
   {
     "access_token": "lS2V-1ER1-DK8...",
     "token_type": "bearer",
     "expires_in": 1800
   }
   ```

3. **상단 "Authorize" 버튼 클릭**
   - Value에 `Bearer <token>` 입력
   - Authorize 클릭

4. **다른 엔드포인트 테스트**
   - GET `/user/profile`
   - POST `/weaknesses`
   - 등등...

---

## curl 명령어로 테스트

### 1. 회원가입
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"user_id": "myuser", "password": "Pass123", "email": "test@example.com"}' \
  | python -m json.tool
```

### 2. 로그인
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "myuser", "password": "Pass123"}' \
  | python -m json.tool
```

### 3. 인증된 요청 (프로필 조회)
```bash
TOKEN="YOUR_TOKEN_HERE"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/user/profile | python -m json.tool
```

### 4. 약점 저장
```bash
TOKEN="YOUR_TOKEN_HERE"
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "myuser", "phrase": "Hello world", "timestamp": 10.5}' \
  http://localhost:8000/weaknesses | python -m json.tool
```

---

## 로그 확인 (트러블슈팅)

### 전체 로그 보기
```bash
tail -f /tmp/echodrive.log
```

### 특정 로그 레벨 필터링
```bash
# ERROR 로그만
grep "ERROR" /tmp/echodrive.log

# INFO 로그만
grep "INFO" /tmp/echodrive.log

# 특정 시간 로그
tail -100 /tmp/echodrive.log
```

### 모듈별 로그
```bash
# 인증 로그
tail logs/echodrive.auth.log

# 데이터베이스 로그
tail logs/echodrive.db.log

# API 로그
tail logs/echodrive.api.log
```

---

## 🔄 서버 시작/중지

### 서버 시작
```bash
python main.py &
```

또는 백그라운드에서 실행
```bash
python main.py > /tmp/echodrive.log 2>&1 &
```

### 서버 중지
```bash
pkill -f "python main.py"
```

### 서버 재시작
```bash
pkill -f "python main.py"
sleep 2
python main.py &
```

---

## 📊 성능 확인

### 응답 시간 측정
```bash
time curl -s http://localhost:8000/health | python -m json.tool
```

**예상 응답 시간:** < 100ms

### 동시 요청 테스트
```bash
for i in {1..10}; do
  curl -s http://localhost:8000/health &
done
wait
```

### 데이터베이스 쿼리 성능
```bash
# check_database.py가 최근 통계를 표시
python check_database.py
```

---

## 🐛 일반적인 문제 해결

### 문제 1: "Connection refused"
```bash
# 해결: 서버 실행
python main.py &
sleep 3
```

### 문제 2: "User already exists"
```bash
# 해결: 다른 사용자 ID로 테스트
# 또는 데이터베이스 초기화
rm echodrive.db
python main.py &  # 테이블 자동 생성
```

### 문제 3: "Invalid token"
```bash
# 해결: 새로운 토큰 획득
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user", "password": "DemoPass123"}'
```

### 문제 4: 포트 이미 사용 중
```bash
# 기존 프로세스 종료
pkill -f "python main.py"
sleep 2

# 다른 포트에서 실행
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## ✅ 확인 체크리스트

완전한 개발 확인을 위해 다음 항목들을 확인하세요:

- [ ] 서버 실행 확인 (`ps aux`)
- [ ] 헬스 체크 성공 (`curl /health`)
- [ ] 회원가입/로그인 가능
- [ ] 약점 저장/조회 동작
- [ ] 문장 설명 동작
- [ ] 학습 진행도 저장/조회
- [ ] 데이터베이스에 데이터 저장됨
- [ ] Swagger UI 접근 가능
- [ ] 로그 파일 생성됨
- [ ] 테스트 스크립트 통과

**모든 항목이 ✅이면 개발 완료!**

---

## 📚 추가 자료

### API 문서
- **자동 생성 문서**: http://localhost:8000/docs
- **코드 주석**: main.py, database.py, auth.py
- **README.md**: 프로젝트 설명

### 테스트 파일
- **test_api.sh**: curl 기반 테스트
- **test_client_v2.py**: Python 클라이언트
- **check_database.py**: 데이터베이스 상태 확인

### 설정 파일
- **.env**: 환경 변수
- **requirements.txt**: 의존성

---

## 🚀 다음 단계

개발이 확인되었으면 다음을 고려하세요:

1. **프로덕션 배포**
   - Docker 컨테이너화
   - 환경 변수 설정
   - SSL/HTTPS 설정

2. **데이터베이스 마이그레이션**
   - PostgreSQL로 변경
   - 백업 설정

3. **모니터링**
   - 로그 분석 도구
   - 성능 모니터링
   - 알림 설정

4. **iOS 앱 완성**
   - 음성인식 구현
   - 로컬 데이터베이스
   - 데이터 동기화

---

**작성일**: 2026-06-23
**백엔드 버전**: 2.0.0
**상태**: ✅ 개발 완료
