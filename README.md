# AI EchoDrive - Backend

AI를 활용한 영어 발음 학습 앱 "AI EchoDrive"의 Python FastAPI 백엔드입니다.

## 프로젝트 개요

**AI EchoDrive**는 YouTube 영상의 자막을 활용하여 효율적인 영어 발음 학습을 돕는 앱입니다.

### 주요 기능

1. **YouTube 자막 분석** - 유튜브 영상의 자막 자동 추출
2. **AI 기반 학습 스케줄** - GPT를 활용한 맞춤형 5분 학습 단계 생성
3. **약점 추적** - 사용자가 못 들은 문장을 자동 저장
4. **발음 설명** - 각 문장의 구조, 발음, 연음 법칙 설명
5. **학습 모드**
   - **Shading Mode**: 자막을 보며 음성을 듣기
   - **Echoing Mode**: 자막 없이 소리만 듣고 따라 읽기

## 기술 스택

- **Framework**: FastAPI
- **Database**: SQLite3
- **AI Model**: OpenAI GPT-3.5-turbo
- **YouTube API**: youtube-transcript-api
- **Language**: Python 3.9+

## 설치 및 실행

### 1. 필수 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일을 열어 `OPENAI_API_KEY`를 설정합니다:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

> **참고**: OpenAI API 키가 없으면 기본값으로 작동하지만, GPT 기반 기능은 제한됩니다.

### 3. 백엔드 서버 시작

```bash
python main.py
```

또는:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

### 4. API 문서 확인

브라우저에서 다음 URL을 방문하세요:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 엔드포인트

### 1. 헬스 체크

```
GET /health
```

서버 상태 확인

**응답:**
```json
{
  "status": "healthy",
  "service": "AI EchoDrive Backend"
}
```

### 2. 루트 엔드포인트

```
GET /
```

사용 가능한 엔드포인트 목록 조회

### 3. YouTube 영상 분석

```
POST /analyze
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=..."
}
```

유튜브 영상에서 자막을 추출하고 AI가 학습 스케줄을 생성합니다.

**응답:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "transcript_length": 5234,
  "schedule": "[Day 1]\n...[Day 2]\n...",
  "status": "success"
}
```

### 4. 약점 저장

```
POST /save-weakness
Content-Type: application/json

{
  "user_id": "user_123",
  "phrase": "How are you?",
  "timestamp": 10.5
}
```

사용자가 못 들은 문장을 저장합니다.

**응답:**
```json
{
  "status": "success",
  "message": "약점이 저장되었습니다",
  "user_id": "user_123",
  "phrase": "How are you?"
}
```

### 5. 약점 목록 조회

```
GET /weaknesses/{user_id}
```

특정 사용자의 저장된 약점 목록을 조회합니다.

**응답:**
```json
{
  "user_id": "user_123",
  "weaknesses": [
    {
      "id": 1,
      "user_id": "user_123",
      "phrase": "How are you?",
      "timestamp": 10.5,
      "created_at": "2024-06-23 12:34:56",
      "reviewed": 0
    }
  ],
  "count": 1
}
```

### 6. 문장 설명

```
GET /explain?phrase=The%20quick%20brown%20fox%20jumps
```

영어 문장의 구조, 단어, 발음 설명을 제공합니다.

**응답:**
```json
{
  "phrase": "The quick brown fox jumps",
  "explanation": "1. 문법 구조\n...\n2. 주요 단어\n...\n3. 발음 팁\n...",
  "status": "success"
}
```

## 테스트

### 테스트 클라이언트 실행

```bash
python test_client.py
```

이 스크립트는 모든 API 엔드포인트를 테스트합니다:
- 헬스 체크
- 약점 저장 및 조회
- 문장 설명
- YouTube 영상 분석 (선택)

## 데이터베이스 스키마

### weaknesses 테이블
사용자가 못 들은 문장을 저장합니다.

```sql
CREATE TABLE weaknesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    phrase TEXT NOT NULL,
    timestamp REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed INTEGER DEFAULT 0
);
```

### learning_progress 테이블
사용자의 학습 진행도를 추적합니다.

```sql
CREATE TABLE learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    day INTEGER NOT NULL,
    completed INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### user_settings 테이블
사용자 맞춤 설정을 저장합니다.

```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    preferred_mode TEXT DEFAULT 'Echoing',
    daily_minutes INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## iOS 클라이언트

iOS 클라이언트 코드는 별도로 제공됩니다:
- SwiftUI 기반의 사용자 인터페이스
- 음성 인식 (Speech Recognition)
- SQLite 로컬 데이터베이스
- Shading/Echoing 학습 모드

iOS 개발은 macOS와 Xcode가 필요합니다.

## 프로젝트 구조

```
.
├── main.py                 # FastAPI 애플리케이션
├── database.py             # 데이터베이스 함수
├── test_client.py          # 테스트 클라이언트
├── requirements.txt        # 의존성
├── .env                    # 환경 변수 (로컬)
├── .env.example            # 환경 변수 템플릿
└── README.md              # 이 파일
```

## 주요 기능 설명

### 1. YouTube 자막 추출

`YouTubeTranscriptApi`를 사용하여 YouTube 영상의 자막을 자동으로 추출합니다.

```python
transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ko'])
```

### 2. AI 기반 학습 스케줄 생성

추출된 자막을 GPT-3.5-turbo에 전달하여 5분 단위로 학습 계획을 생성합니다.

```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[...],
    max_tokens=1000
)
```

### 3. 약점 추적 및 복습

사용자가 못 들은 문장을 SQLite에 저장하여 나중에 복습할 수 있습니다.

### 4. 발음 및 문법 설명

각 문장에 대해 GPT-3.5-turbo를 활용해 상세한 설명을 제공합니다:
- 문법 구조 분석
- 주요 단어 설명
- 원어민 발음 팁 및 연음 법칙

## 주의사항

1. **OpenAI API 비용**: YouTube 자막 분석 및 문장 설명에는 API 호출이 필요하므로 API 비용이 발생할 수 있습니다.

2. **YouTube 자막**: 자막이 없는 영상은 분석할 수 없습니다.

3. **CORS 설정**: 현재는 모든 오리진을 허용하고 있습니다. 프로덕션 환경에서는 제한해야 합니다.

4. **데이터베이스**: SQLite는 작은 프로젝트용입니다. 대규모 배포 시에는 PostgreSQL 등으로 마이그레이션을 권장합니다.

## 개발 계획

- [ ] 사용자 인증 (JWT)
- [ ] 학습 통계 및 분석 대시보드
- [ ] 더 많은 학습 모드 추가
- [ ] 실시간 음성 인식 피드백
- [ ] 발음 평가 기능 (문자-음성 일치도)

## 라이센스

MIT License

## 문의

문제가 발생하거나 기능을 추가하고 싶으면 이슈를 등록해주세요.
