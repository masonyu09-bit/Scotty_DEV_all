"""
AI EchoDrive 백엔드 테스트 클라이언트

이 스크립트는 FastAPI 서버의 엔드포인트를 테스트합니다.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class EchoDriveClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def test_health(self) -> Dict[str, Any]:
        """헬스 체크"""
        print("\n=== Health Check ===")
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    def test_root(self) -> Dict[str, Any]:
        """루트 엔드포인트"""
        print("\n=== Root Endpoint ===")
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    def test_save_weakness(self, user_id: str, phrase: str, timestamp: float = 0.0) -> Dict[str, Any]:
        """약점 저장 테스트"""
        print("\n=== Save Weakness ===")
        payload = {
            "user_id": user_id,
            "phrase": phrase,
            "timestamp": timestamp
        }
        try:
            response = self.session.post(
                f"{self.base_url}/save-weakness",
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    def test_get_weaknesses(self, user_id: str) -> Dict[str, Any]:
        """약점 조회 테스트"""
        print("\n=== Get Weaknesses ===")
        try:
            response = self.session.get(f"{self.base_url}/weaknesses/{user_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, default=str)}")
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    def test_explain_phrase(self, phrase: str) -> Dict[str, Any]:
        """문장 설명 테스트"""
        print("\n=== Explain Phrase ===")
        try:
            response = self.session.get(
                f"{self.base_url}/explain",
                params={"phrase": phrase}
            )
            print(f"Status: {response.status_code}")
            print(f"Phrase: {phrase}")
            result = response.json()
            print(f"Status: {result.get('status')}")
            print(f"Explanation: {result.get('explanation', 'N/A')[:200]}...")
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    def test_analyze_video(self, youtube_url: str) -> Dict[str, Any]:
        """비디오 분석 테스트"""
        print("\n=== Analyze Video ===")
        payload = {"url": youtube_url}
        try:
            response = self.session.post(
                f"{self.base_url}/analyze",
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"URL: {youtube_url}")
            result = response.json()
            if response.status_code == 200:
                print(f"Video ID: {result.get('video_id')}")
                print(f"Transcript Length: {result.get('transcript_length')} chars")
                schedule = result.get('schedule', '')
                print(f"Schedule: {schedule[:200]}...")
            else:
                print(f"Error: {result}")
            return result
        except Exception as e:
            print(f"Error: {e}")
            return {"error": str(e)}

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("=" * 60)
        print("AI EchoDrive Backend - Test Suite")
        print("=" * 60)

        # 기본 엔드포인트 테스트
        self.test_health()
        self.test_root()

        # 약점 저장 및 조회 테스트
        test_user_id = "test_user_1"
        self.test_save_weakness(test_user_id, "How are you?", 10.5)
        self.test_save_weakness(test_user_id, "Nice to meet you", 25.0)
        self.test_save_weakness(test_user_id, "What's your name?", 40.3)
        self.test_get_weaknesses(test_user_id)

        # 문장 설명 테스트
        self.test_explain_phrase("The quick brown fox jumps over the lazy dog")

        # 비디오 분석 테스트 (선택사항 - YouTube 자막이 있는 비디오 필요)
        # self.test_analyze_video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        print("\n" + "=" * 60)
        print("Test Suite Complete!")
        print("=" * 60)


if __name__ == "__main__":
    client = EchoDriveClient()
    client.run_all_tests()
