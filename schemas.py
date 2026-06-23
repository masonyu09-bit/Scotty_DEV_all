"""
Pydantic 스키마 정의
"""

from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List
from datetime import datetime


# MARK: - 요청 스키마

class VideoRequest(BaseModel):
    """YouTube 영상 분석 요청"""
    url: str = Field(..., description="YouTube URL", examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v or len(v) < 10:
            raise ValueError("유효한 URL을 입력하세요")
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("YouTube URL이어야 합니다")
        return v


class WeaknessRequest(BaseModel):
    """약점 저장 요청"""
    user_id: str = Field(..., description="사용자 ID", min_length=1, max_length=100)
    phrase: str = Field(..., description="문장", min_length=1, max_length=500)
    timestamp: float = Field(default=0.0, description="영상 시간(초)", ge=0)

    @field_validator('phrase')
    @classmethod
    def validate_phrase(cls, v):
        if not v.strip():
            raise ValueError("문장은 공백이 아니어야 합니다")
        return v.strip()


class PhraseRequest(BaseModel):
    """문장 설명 요청"""
    phrase: str = Field(..., description="설명할 문장", min_length=1, max_length=500)


class UserSignUpRequest(BaseModel):
    """사용자 가입 요청"""
    user_id: str = Field(..., description="사용자 ID", min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, description="이메일")
    password: str = Field(..., description="비밀번호", min_length=6)

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("사용자 ID는 영문, 숫자, -, _만 사용 가능합니다")
        return v


class UserLoginRequest(BaseModel):
    """사용자 로그인 요청"""
    user_id: str = Field(..., description="사용자 ID")
    password: str = Field(..., description="비밀번호")


class UserSettingsRequest(BaseModel):
    """사용자 설정 업데이트 요청"""
    preferred_mode: Optional[str] = Field(default=None, description="선호 모드 (Echoing/Shading)")
    daily_minutes: Optional[int] = Field(default=None, description="하루 학습시간", ge=5, le=120)


# MARK: - 응답 스키마

class VideoResponse(BaseModel):
    """YouTube 영상 분석 응답"""
    video_id: str
    transcript_length: int
    schedule: str
    status: str


class WeaknessResponse(BaseModel):
    """약점 저장 응답"""
    status: str
    message: str
    user_id: str
    phrase: str


class WeaknessItem(BaseModel):
    """약점 항목"""
    id: int
    user_id: str
    phrase: str
    timestamp: float
    created_at: str
    reviewed: int

    class Config:
        from_attributes = True


class WeaknessListResponse(BaseModel):
    """약점 목록 응답"""
    user_id: str
    weaknesses: List[WeaknessItem]
    count: int


class ExplanationResponse(BaseModel):
    """문장 설명 응답"""
    phrase: str
    explanation: str
    status: str


class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    service: str


class LearningProgressItem(BaseModel):
    """학습 진행도 항목"""
    id: int
    user_id: str
    video_id: str
    day: int
    completed: int
    completed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class LearningProgressResponse(BaseModel):
    """학습 진행도 응답"""
    user_id: str
    video_id: str
    progress: List[LearningProgressItem]
    completed_days: int
    total_days: int


class UserSettingsResponse(BaseModel):
    """사용자 설정 응답"""
    user_id: str
    preferred_mode: str
    daily_minutes: int
    created_at: str
    updated_at: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str
    expires_in: int


class UserProfileResponse(BaseModel):
    """사용자 프로필 응답"""
    user_id: str
    email: Optional[str] = None
    is_active: bool
    created_at: str
    weakness_count: int
    total_study_days: int


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: str = "error"
    code: str
    message: str
    detail: Optional[str] = None
    timestamp: str


class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)
