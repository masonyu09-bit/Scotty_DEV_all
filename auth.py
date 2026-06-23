"""
인증 시스템 (JWT 없이 간단한 토큰)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets
from pydantic import BaseModel
import os

# 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 토큰 저장소 (프로덕션에서는 Redis 등 사용)
TOKEN_STORE = {}


class Token(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """토큰 데이터"""
    user_id: Optional[str] = None


class User(BaseModel):
    """사용자 정보"""
    user_id: str
    email: Optional[str] = None
    is_active: bool = True


def hash_password(password: str) -> str:
    """비밀번호 해시"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return hash_password(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """비밀번호 해시"""
    return hash_password(password)


def create_access_token(user_id: str) -> str:
    """액세스 토큰 생성"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    TOKEN_STORE[token] = {
        "user_id": user_id,
        "expires_at": expires_at
    }

    return token


def verify_token(token: str) -> Optional[TokenData]:
    """토큰 검증"""
    if token not in TOKEN_STORE:
        return None

    token_data = TOKEN_STORE[token]
    expires_at = token_data.get("expires_at")

    # 만료 확인
    if datetime.now(timezone.utc) > expires_at:
        del TOKEN_STORE[token]
        return None

    user_id = token_data.get("user_id")
    return TokenData(user_id=user_id) if user_id else None


def create_token_response(user_id: str) -> Token:
    """토큰 응답 생성"""
    access_token = create_access_token(user_id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def revoke_token(token: str) -> bool:
    """토큰 폐기"""
    if token in TOKEN_STORE:
        del TOKEN_STORE[token]
        return True
    return False
