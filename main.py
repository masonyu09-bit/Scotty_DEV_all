from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import openai
import os
from dotenv import load_dotenv
from datetime import timedelta

# 로컬 모듈
from database import (
    init_db, save_weakness, get_weaknesses, get_unreviewd_weaknesses,
    mark_weakness_as_reviewed, save_learning_progress as db_save_learning_progress,
    get_learning_progress as db_get_learning_progress,
    get_user_settings, update_user_settings, create_user, get_user,
    verify_user_exists, get_user_stats, deactivate_user
)
from auth import (
    verify_password, get_password_hash, create_token_response,
    verify_token, Token
)
from schemas import (
    VideoRequest, WeaknessRequest, PhraseRequest,
    UserSignUpRequest, UserLoginRequest, UserSettingsRequest,
    VideoResponse, WeaknessResponse, WeaknessListResponse,
    ExplanationResponse, HealthResponse, LearningProgressResponse,
    UserSettingsResponse, UserProfileResponse, ErrorResponse,
    LearningProgressItem
)
from logging_config import logger, api_logger, auth_logger

load_dotenv()

# API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-test")

app = FastAPI(
    title="AI EchoDrive API",
    description="AI를 활용한 영어 발음 학습 API",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# MARK: - 의존성

def get_current_user(authorization: str = Header(None)) -> str:
    """현재 사용자 조회"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = authorization.replace("Bearer ", "")
    token_data = verify_token(token)

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = get_user(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.get('is_active'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    return token_data.user_id


# MARK: - 유틸리티 함수

def extract_video_id(url: str) -> str:
    """유튜브 URL에서 영상 ID 추출"""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        return url.split("be/")[1].split("?")[0]
    raise ValueError("Invalid YouTube URL")


def ai_split_transcript(transcript_text: str) -> str:
    """AI를 사용하여 스크립트를 학습용으로 분절"""
    prompt = f"""
    다음은 유튜브 영상의 스크립트입니다.
    학습자가 하루에 5분 정도 공부할 수 있도록 맥락에 맞게 내용을 분절해주세요.
    각 분절은 [Day 1], [Day 2] 식으로 나누고, 해당 부분의 시작과 끝 텍스트를 명시하세요.

    최대 3000자까지의 스크립트를 사용합니다:
    {transcript_text[:3000]}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 효율적인 어학 학습 스케줄러입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"AI scheduling failed: {e}")
        return f"스크립트 길이: {len(transcript_text)}자\n\n[Day 1]\n{transcript_text[:500]}\n\n[Day 2]\n{transcript_text[500:1000]}"


def explain_phrase_with_ai(phrase: str) -> str:
    """AI를 사용하여 문장 설명"""
    prompt = f"""
    다음 영어 문장의 구조, 주요 단어, 그리고 원어민이 발음할 때 주의해야 할 연음 법칙을 상세히 설명해줘:
    '{phrase}'

    형식:
    1. 문법 구조
    2. 주요 단어 설명
    3. 발음 팁 (연음, 강세 등)
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 친절한 전문 영어 강사입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"Phrase explanation failed: {e}")
        return f"'{phrase}' - 이 문장의 발음 및 문법 설명입니다."


# MARK: - 앱 이벤트

@app.on_event("startup")
async def startup():
    """애플리케이션 시작"""
    logger.info("Starting AI EchoDrive Backend")
    init_db()


@app.on_event("shutdown")
async def shutdown():
    """애플리케이션 종료"""
    logger.info("Shutting down AI EchoDrive Backend")


# MARK: - 공개 엔드포인트

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "AI EchoDrive Backend API",
        "version": "2.0.0",
        "endpoints": {
            "auth": {
                "signup": "POST /auth/signup - 회원가입",
                "login": "POST /auth/login - 로그인",
            },
            "video": {
                "analyze": "POST /videos/analyze - YouTube 영상 분석",
            },
            "weaknesses": {
                "save": "POST /weaknesses - 약점 저장",
                "list": "GET /weaknesses - 약점 목록",
                "explain": "GET /phrases/explain - 문장 설명",
            },
            "learning": {
                "progress": "GET /learning/progress/{video_id} - 학습 진행도",
                "save": "POST /learning/progress - 학습 진행도 저장",
            },
            "user": {
                "profile": "GET /user/profile - 사용자 프로필",
                "settings": "GET /user/settings - 사용자 설정",
                "update_settings": "PUT /user/settings - 설정 업데이트",
            }
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(status="healthy", service="AI EchoDrive Backend v2.0.0")


# MARK: - 인증 엔드포인트

@app.post("/auth/signup", response_model=Token)
async def signup(request: UserSignUpRequest):
    """사용자 가입"""
    try:
        if verify_user_exists(request.user_id):
            auth_logger.warning(f"Signup failed: user {request.user_id} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )

        hashed_password = get_password_hash(request.password)
        create_user(request.user_id, hashed_password, request.email)

        auth_logger.info(f"User signed up: {request.user_id}")
        return create_token_response(request.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        auth_logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/auth/login", response_model=Token)
async def login(request: UserLoginRequest):
    """사용자 로그인"""
    try:
        user = get_user(request.user_id)

        if not user or not verify_password(request.password, user.get('hashed_password', '')):
            auth_logger.warning(f"Login failed for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        auth_logger.info(f"User logged in: {request.user_id}")
        return create_token_response(request.user_id)
    except HTTPException:
        raise
    except Exception as e:
        auth_logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# MARK: - 영상 분석 엔드포인트

@app.post("/videos/analyze", response_model=VideoResponse)
async def analyze_video(request: VideoRequest, user_id: str = Depends(get_current_user)):
    """YouTube 영상 분석"""
    try:
        video_id = extract_video_id(request.url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ko'])
        full_text = " ".join([t['text'] for t in transcript])

        schedule = ai_split_transcript(full_text)

        api_logger.info(f"Video analyzed: {video_id} by user {user_id}")
        return VideoResponse(
            video_id=video_id,
            transcript_length=len(full_text),
            schedule=schedule,
            status="success"
        )
    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This video has no subtitles or subtitles are disabled"
        )
    except Exception as e:
        api_logger.error(f"Video analysis error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# MARK: - 약점 관리 엔드포인트

@app.post("/weaknesses", response_model=WeaknessResponse)
async def save_weakness_endpoint(
    request: WeaknessRequest,
    user_id: str = Depends(get_current_user)
):
    """약점 저장"""
    try:
        save_weakness(user_id, request.phrase, request.timestamp)
        api_logger.info(f"Weakness saved: {user_id} - {request.phrase}")
        return WeaknessResponse(
            status="success",
            message="약점이 저장되었습니다",
            user_id=user_id,
            phrase=request.phrase
        )
    except Exception as e:
        api_logger.error(f"Save weakness error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/weaknesses", response_model=WeaknessListResponse)
async def get_weaknesses_endpoint(user_id: str = Depends(get_current_user)):
    """약점 목록 조회"""
    try:
        weaknesses = get_weaknesses(user_id)
        return WeaknessListResponse(
            user_id=user_id,
            weaknesses=weaknesses,
            count=len(weaknesses)
        )
    except Exception as e:
        api_logger.error(f"Get weaknesses error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/weaknesses/unreviewd")
async def get_unreviewd(user_id: str = Depends(get_current_user)):
    """검토 안 된 약점 조회"""
    try:
        weaknesses = get_unreviewd_weaknesses(user_id)
        return WeaknessListResponse(
            user_id=user_id,
            weaknesses=weaknesses,
            count=len(weaknesses)
        )
    except Exception as e:
        api_logger.error(f"Get unreviewd weaknesses error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/weaknesses/{weakness_id}/reviewed")
async def mark_reviewed(weakness_id: int, user_id: str = Depends(get_current_user)):
    """약점을 검토 완료로 표시"""
    try:
        result = mark_weakness_as_reviewed(weakness_id)
        api_logger.info(f"Weakness marked reviewed: {weakness_id}")
        return result
    except Exception as e:
        api_logger.error(f"Mark reviewed error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# MARK: - 문장 설명 엔드포인트

@app.get("/phrases/explain", response_model=ExplanationResponse)
async def explain_phrase(phrase: str, user_id: str = Depends(get_current_user)):
    """영어 문장 설명"""
    if not phrase or len(phrase) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phrase")

    try:
        explanation = explain_phrase_with_ai(phrase)
        api_logger.info(f"Phrase explained: {phrase}")
        return ExplanationResponse(
            phrase=phrase,
            explanation=explanation,
            status="success"
        )
    except Exception as e:
        api_logger.error(f"Explain phrase error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# MARK: - 학습 진행도 엔드포인트

@app.get("/learning/progress/{video_id}")
async def get_learning_progress_endpoint(video_id: str, user_id: str = Depends(get_current_user)):
    """학습 진행도 조회"""
    try:
        progress = db_get_learning_progress(user_id, video_id)
        completed_days = sum(1 for p in progress if p['completed'] == 1)
        return LearningProgressResponse(
            user_id=user_id,
            video_id=video_id,
            progress=progress,
            completed_days=completed_days,
            total_days=len(progress)
        )
    except Exception as e:
        api_logger.error(f"Get learning progress error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/learning/progress")
async def save_learning_progress_endpoint(
    video_id: str,
    day: int,
    user_id: str = Depends(get_current_user)
):
    """학습 진행도 저장"""
    try:
        result = db_save_learning_progress(user_id, video_id, day)
        api_logger.info(f"Learning progress saved: {user_id} - {video_id} day {day}")
        return result
    except Exception as e:
        api_logger.error(f"Save learning progress error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# MARK: - 사용자 프로필 엔드포인트

@app.get("/user/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str = Depends(get_current_user)):
    """사용자 프로필 조회"""
    try:
        user = get_user(user_id)
        stats = get_user_stats(user_id)

        return UserProfileResponse(
            user_id=user_id,
            email=user.get('email'),
            is_active=bool(user.get('is_active')),
            created_at=user.get('created_at'),
            weakness_count=stats['weakness_count'],
            total_study_days=stats['total_study_days']
        )
    except Exception as e:
        api_logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/user/settings", response_model=UserSettingsResponse)
async def get_user_settings_endpoint(user_id: str = Depends(get_current_user)):
    """사용자 설정 조회"""
    try:
        settings = get_user_settings(user_id)
        return UserSettingsResponse(**settings)
    except Exception as e:
        api_logger.error(f"Get settings error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.put("/user/settings", response_model=UserSettingsResponse)
async def update_user_settings_endpoint(
    request: UserSettingsRequest,
    user_id: str = Depends(get_current_user)
):
    """사용자 설정 업데이트"""
    try:
        settings = update_user_settings(
            user_id,
            request.preferred_mode,
            request.daily_minutes
        )
        api_logger.info(f"User settings updated: {user_id}")
        return UserSettingsResponse(**settings)
    except Exception as e:
        api_logger.error(f"Update settings error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/user/account")
async def deactivate_account(user_id: str = Depends(get_current_user)):
    """계정 비활성화"""
    try:
        result = deactivate_user(user_id)
        auth_logger.info(f"User account deactivated: {user_id}")
        return result
    except Exception as e:
        api_logger.error(f"Deactivate account error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# MARK: - 에러 핸들러

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """값 오류 핸들러"""
    logger.error(f"Value error: {exc}")
    return {
        "status": "error",
        "code": "INVALID_VALUE",
        "message": str(exc)
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 핸들러"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "status": "error",
        "code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
