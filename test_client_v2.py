"""
AI EchoDrive v2 백엔드 테스트 클라이언트

새로운 기능 테스트:
- 사용자 인증 (회원가입/로그인)
- JWT 토큰 관리
- 전체 API 엔드포인트
"""

import requests
import json
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"


class EchoDriveClientV2:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None

    def print_header(self, title: str):
        """제목 출력"""
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")

    def print_result(self, status: int, data: Dict[str, Any]):
        """결과 출력"""
        print(f"\n📊 Status: {status}")
        print(f"📦 Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    def set_auth_header(self):
        """인증 헤더 설정"""
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })

    # MARK: - 공개 엔드포인트

    def test_health(self) -> Dict[str, Any]:
        """헬스 체크"""
        self.print_header("Health Check")
        response = self.session.get(f"{self.base_url}/health")
        self.print_result(response.status_code, response.json())
        return response.json()

    def test_root(self) -> Dict[str, Any]:
        """루트 엔드포인트"""
        self.print_header("Root Endpoint")
        response = self.session.get(f"{self.base_url}/")
        self.print_result(response.status_code, response.json())
        return response.json()

    # MARK: - 인증 엔드포인트

    def signup(self, user_id: str, password: str, email: str = None) -> bool:
        """회원가입"""
        self.print_header(f"Sign Up: {user_id}")
        payload = {
            "user_id": user_id,
            "password": password,
            "email": email
        }
        response = self.session.post(
            f"{self.base_url}/auth/signup",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = user_id
            self.set_auth_header()
            print(f"✅ Signup successful")
            self.print_result(response.status_code, data)
            return True
        else:
            print(f"❌ Signup failed")
            self.print_result(response.status_code, response.json())
            return False

    def login(self, user_id: str, password: str) -> bool:
        """로그인"""
        self.print_header(f"Login: {user_id}")
        payload = {
            "user_id": user_id,
            "password": password
        }
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = user_id
            self.set_auth_header()
            print(f"✅ Login successful")
            self.print_result(response.status_code, data)
            return True
        else:
            print(f"❌ Login failed")
            self.print_result(response.status_code, response.json())
            return False

    # MARK: - 사용자 엔드포인트

    def get_profile(self) -> Dict[str, Any]:
        """프로필 조회"""
        self.print_header("User Profile")
        response = self.session.get(f"{self.base_url}/user/profile")
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    def get_settings(self) -> Dict[str, Any]:
        """설정 조회"""
        self.print_header("User Settings")
        response = self.session.get(f"{self.base_url}/user/settings")
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    def update_settings(self, mode: str = None, daily_minutes: int = None) -> Dict[str, Any]:
        """설정 업데이트"""
        self.print_header("Update Settings")
        payload = {}
        if mode:
            payload["preferred_mode"] = mode
        if daily_minutes:
            payload["daily_minutes"] = daily_minutes

        response = self.session.put(
            f"{self.base_url}/user/settings",
            json=payload
        )
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    # MARK: - 약점 관리 엔드포인트

    def save_weakness(self, phrase: str, timestamp: float = 0.0) -> Dict[str, Any]:
        """약점 저장"""
        self.print_header("Save Weakness")
        payload = {
            "user_id": self.user_id,
            "phrase": phrase,
            "timestamp": timestamp
        }
        response = self.session.post(
            f"{self.base_url}/weaknesses",
            json=payload
        )
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    def get_weaknesses(self) -> Dict[str, Any]:
        """약점 목록 조회"""
        self.print_header("Get Weaknesses")
        response = self.session.get(f"{self.base_url}/weaknesses")
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    def get_unreviewd_weaknesses(self) -> Dict[str, Any]:
        """검토 안 된 약점 조회"""
        self.print_header("Get Unreviewd Weaknesses")
        response = self.session.get(f"{self.base_url}/weaknesses/unreviewd")
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    def mark_weakness_reviewed(self, weakness_id: int) -> Dict[str, Any]:
        """약점 검토 완료"""
        self.print_header(f"Mark Weakness Reviewed: {weakness_id}")
        response = self.session.put(
            f"{self.base_url}/weaknesses/{weakness_id}/reviewed"
        )
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    # MARK: - 문장 설명 엔드포인트

    def explain_phrase(self, phrase: str) -> Dict[str, Any]:
        """문장 설명"""
        self.print_header("Explain Phrase")
        response = self.session.get(
            f"{self.base_url}/phrases/explain",
            params={"phrase": phrase}
        )
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    # MARK: - 영상 분석 엔드포인트

    def analyze_video(self, url: str) -> Dict[str, Any]:
        """영상 분석"""
        self.print_header("Analyze Video")
        payload = {"url": url}
        response = self.session.post(
            f"{self.base_url}/videos/analyze",
            json=payload
        )
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    # MARK: - 학습 진행도 엔드포인트

    def get_learning_progress(self, video_id: str) -> Dict[str, Any]:
        """학습 진행도 조회"""
        self.print_header(f"Get Learning Progress: {video_id}")
        response = self.session.get(f"{self.base_url}/learning/progress/{video_id}")
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    def save_learning_progress(self, video_id: str, day: int) -> Dict[str, Any]:
        """학습 진행도 저장"""
        self.print_header(f"Save Learning Progress: {video_id} day {day}")
        response = self.session.post(
            f"{self.base_url}/learning/progress",
            params={"video_id": video_id, "day": day}
        )
        self.print_result(response.status_code, response.json())
        return response.json() if response.status_code == 200 else {}

    # MARK: - 통합 테스트

    def run_full_test(self):
        """전체 테스트 실행"""
        print("\n" + "="*70)
        print("  🚀 AI EchoDrive v2 - Full Test Suite")
        print("="*70)

        # 1. 기본 엔드포인트
        self.test_health()
        self.test_root()

        # 2. 회원가입 및 로그인
        test_user = "test_user_2024"
        test_password = "TestPassword123"
        test_email = "test@example.com"

        if self.signup(test_user, test_password, test_email):
            # 3. 사용자 정보
            self.get_profile()
            self.get_settings()

            # 4. 설정 업데이트
            self.update_settings("Shading", 10)

            # 5. 약점 저장
            phrases = [
                "How are you?",
                "Nice to meet you",
                "What's your name?",
                "I'm fine, thank you",
                "See you later"
            ]

            for i, phrase in enumerate(phrases, 1):
                self.save_weakness(phrase, i * 5.0)

            # 6. 약점 조회
            weaknesses_data = self.get_weaknesses()

            # 7. 검토 안 된 약점
            unreviewd = self.get_unreviewd_weaknesses()

            # 8. 약점 검토 완료
            if "weaknesses" in weaknesses_data and weaknesses_data["weaknesses"]:
                first_weakness_id = weaknesses_data["weaknesses"][0].get("id")
                if first_weakness_id:
                    self.mark_weakness_reviewed(first_weakness_id)

            # 9. 문장 설명
            self.explain_phrase("The quick brown fox jumps over the lazy dog")

            # 10. 학습 진행도
            test_video_id = "dQw4w9WgXcQ"
            self.save_learning_progress(test_video_id, 1)
            self.save_learning_progress(test_video_id, 2)
            self.get_learning_progress(test_video_id)

        # 마무리
        print("\n" + "="*70)
        print("  ✅ Test Suite Complete!")
        print("="*70 + "\n")


if __name__ == "__main__":
    client = EchoDriveClientV2()
    client.run_full_test()
