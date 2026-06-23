from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import openai
import os
from dotenv import load_dotenv
from database import init_db, save_weakness, get_weaknesses

load_dotenv()

# API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-test")

app = FastAPI(title="AI EchoDrive Backend", version="1.0.0")

# CORS 설정 (iOS 클라이언트와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 모델
class VideoRequest(BaseModel):
    url: str

class WeaknessRequest(BaseModel):
    user_id: str
    phrase: str
    timestamp: float

class PhraseRequest(BaseModel):
    phrase: str

# 유튜브 ID 추출 함수
def extract_video_id(url: str) -> str:
    """유튜브 URL에서 영상 ID 추출"""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "be/" in url:
        return url.split("be/")[1].split("?")[0]
    raise ValueError("Invalid YouTube URL")

# AI를 이용해 스크립트를 5분 단위로 분절
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
        # OpenAI API가 없는 경우 기본값 반환
        return f"스크립트 길이: {len(transcript_text)}자\n\n[Day 1]\n{transcript_text[:500]}\n\n[Day 2]\n{transcript_text[500:1000]}"

@app.on_event("startup")
async def startup():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    init_db()

@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "message": "AI EchoDrive Backend API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze - 유튜브 영상 분석",
            "save_weakness": "POST /save-weakness - 약점 저장",
            "explain": "GET /explain - 문장 설명",
            "get_weaknesses": "GET /weaknesses/{user_id} - 저장된 약점 조회"
        }
    }

@app.post("/analyze")
async def analyze_video(request: VideoRequest):
    """유튜브 영상에서 자막을 추출하고 학습 스케줄 생성"""
    try:
        video_id = extract_video_id(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # 자막 추출
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ko'])
        full_text = " ".join([t['text'] for t in transcript])

        # AI 스케줄링
        schedule = ai_split_transcript(full_text)

        return {
            "video_id": video_id,
            "transcript_length": len(full_text),
            "schedule": schedule,
            "status": "success"
        }
    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(
            status_code=400,
            detail="이 영상에는 자막이 없거나 자막 기능이 비활성화되어 있습니다."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"영상 분석 오류: {str(e)}")

@app.post("/save-weakness")
async def save_weakness_endpoint(request: WeaknessRequest):
    """사용자가 못 들은 문장을 약점 목록에 저장"""
    try:
        save_weakness(request.user_id, request.phrase, request.timestamp)
        return {
            "status": "success",
            "message": "약점이 저장되었습니다",
            "user_id": request.user_id,
            "phrase": request.phrase
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터베이스 오류: {str(e)}")

@app.get("/weaknesses/{user_id}")
async def get_user_weaknesses(user_id: str):
    """사용자의 저장된 약점 목록 조회"""
    try:
        weaknesses = get_weaknesses(user_id)
        return {
            "user_id": user_id,
            "weaknesses": weaknesses,
            "count": len(weaknesses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터베이스 오류: {str(e)}")

@app.get("/explain")
async def explain_phrase(phrase: str):
    """영어 문장의 구조, 발음 설명"""
    if not phrase:
        raise HTTPException(status_code=400, detail="phrase 파라미터가 필요합니다")

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
        return {
            "phrase": phrase,
            "explanation": response.choices[0].message.content,
            "status": "success"
        }
    except Exception as e:
        # OpenAI API가 없는 경우 기본 설명 반환
        return {
            "phrase": phrase,
            "explanation": f"'{phrase}' - 이 문장의 발음 및 문법 설명입니다. OpenAI API를 설정하면 더 자세한 설명을 받을 수 있습니다.",
            "status": "fallback"
        }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "AI EchoDrive Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
