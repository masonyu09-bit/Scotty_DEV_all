# AI EchoDrive - iOS Client

iOS 기반 영어 발음 학습 앱의 SwiftUI 클라이언트입니다.

## 개발 환경

- **Xcode**: 14.0 이상
- **iOS**: 15.0 이상
- **Swift**: 5.7 이상

## 구조

```
ios-client/
├── Sources/
│   ├── Models/          # 데이터 모델
│   ├── Views/           # SwiftUI 뷰
│   ├── Services/        # API 및 데이터 서비스
│   └── App/             # 앱 진입점
├── Project.swift        # SPM 패키지 정의
└── README.md
```

## 주요 컴포넌트

### Models (데이터 모델)

```swift
// VideoRequest.swift
struct VideoRequest: Codable {
    let url: String
}

// WeaknessRequest.swift
struct WeaknessRequest: Codable {
    let user_id: String
    let phrase: String
    let timestamp: Double
}
```

### Views (사용자 인터페이스)

#### 1. **ModesView** - 학습 모드 선택
- Shading Mode (자막 보기)
- Echoing Mode (소리만 듣기)

#### 2. **EchoingView** - 메인 학습 화면
- YouTube URL 입력
- 학습 자료 표시
- Yes/No 버튼으로 이해도 표시

#### 3. **ShadingView** - 자막 보기 모드
- 영상 재생과 동시에 자막 표시
- 어려운 문장 표시 기능

### Services (API 통신)

```swift
// APIService.swift
class APIService {
    let baseURL = "http://localhost:8000"
    
    func analyzeVideo(url: String) async throws -> AnalysisResult
    func saveWeakness(userId: String, phrase: String) async throws
    func getWeaknesses(userId: String) async throws -> [Weakness]
    func explainPhrase(phrase: String) async throws -> Explanation
}
```

## 주요 기능

### 1. YouTube 영상 분석
- 사용자가 입력한 유튜브 URL로부터 자막 추출
- AI가 자동으로 5분 단위 학습 구간 생성

### 2. 발음 학습 모드

#### Shading Mode
```
┌──────────────────────────────────┐
│   AI EchoDrive - Shading Mode    │
├──────────────────────────────────┤
│   영상 플레이어                  │
│   ─────────────────              │
│                                  │
│   [자막]                         │
│   How are you?                   │
│   Nice to meet you!              │
│                                  │
└──────────────────────────────────┘
```

#### Echoing Mode
```
┌──────────────────────────────────┐
│   AI EchoDrive - Echoing Mode    │
├──────────────────────────────────┤
│                                  │
│   오늘의 학습 구간               │
│                                  │
│   How are you?                   │
│                                  │
│   ☑️ Yes    ✗ No                │
│                                  │
└──────────────────────────────────┘
```

### 3. 약점 추적
- "No" 클릭 시 해당 문장을 약점 목록에 자동 저장
- SQLite에 로컬 저장
- 백엔드 서버에도 동기화

### 4. 발음 설명
- 각 문장에 대한 상세 설명 조회
- 문법 구조 설명
- 원어민 발음 팁
- 연음 법칙 설명

## 설치 및 실행

### 1. Xcode에서 프로젝트 열기

```bash
open ios-client
```

### 2. 의존성 설치 (Cocoapods 사용 시)

```bash
cd ios-client
pod install
```

### 3. 백엔드 서버 연결 설정

`APIService.swift`에서 `baseURL` 설정:

```swift
let baseURL = "http://192.168.1.100:8000"  // 서버 IP 주소
```

### 4. 프로젝트 빌드 및 실행

Xcode에서 ▶️ Run 클릭 또는 Cmd+R

## API 통신

### 1. 영상 분석 요청

```swift
do {
    let result = try await apiService.analyzeVideo(url: "https://youtube.com/watch?v=...")
    print("Video ID: \(result.videoId)")
    print("Schedule: \(result.schedule)")
} catch {
    print("Error: \(error)")
}
```

### 2. 약점 저장

```swift
do {
    try await apiService.saveWeakness(userId: "user1", phrase: "How are you?")
} catch {
    print("Error: \(error)")
}
```

### 3. 약점 조회

```swift
do {
    let weaknesses = try await apiService.getWeaknesses(userId: "user1")
    for weakness in weaknesses {
        print("\(weakness.phrase) - \(weakness.timestamp)s")
    }
} catch {
    print("Error: \(error)")
}
```

### 4. 문장 설명 조회

```swift
do {
    let explanation = try await apiService.explainPhrase("The quick brown fox")
    print(explanation.text)
} catch {
    print("Error: \(error)")
}
```

## 데이터베이스 (로컬 SQLite)

SQLite를 사용하여 약점과 학습 진행도를 로컬에 저장합니다.

### 테이블 구조

```sql
-- 약점 저장
CREATE TABLE weaknesses (
    id INTEGER PRIMARY KEY,
    phrase TEXT NOT NULL,
    timestamp REAL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 학습 진행도
CREATE TABLE learning_progress (
    id INTEGER PRIMARY KEY,
    videoId TEXT,
    day INTEGER,
    completed BOOLEAN DEFAULT 0,
    completedAt TIMESTAMP
);

-- 사용자 설정
CREATE TABLE user_settings (
    userId TEXT PRIMARY KEY,
    preferredMode TEXT,
    dailyMinutes INTEGER
);
```

## 음성 인식 (Speech Recognition)

`SFSpeechRecognizer`를 사용하여 사용자의 음성을 인식합니다.

### 마이크 권한 설정

`Info.plist`에 다음 권한을 추가합니다:

```xml
<key>NSSpeechRecognitionUsageDescription</key>
<string>음성 학습을 위해 마이크 접근 권한이 필요합니다.</string>

<key>NSMicrophoneUsageDescription</key>
<string>발음 연습을 위해 마이크가 필요합니다.</string>
```

### 음성 인식 구현

```swift
import Speech

class SpeechRecognitionService {
    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let audioEngine = AVAudioEngine()
    
    func startListening(completion: @escaping (String) -> Void) {
        // 음성 인식 시작
    }
    
    func stopListening() {
        // 음성 인식 중지
    }
}
```

## 주의사항

1. **시뮬레이터**: 음성 인식은 실제 iOS 기기에서만 작동합니다.

2. **네트워크**: 백엔드 서버와 통신하기 위해 네트워크 연결이 필요합니다.

3. **API 설정**: `APIService.baseURL`을 백엔드 서버 주소로 설정해야 합니다.

4. **Info.plist**: 마이크 및 음성 인식 권한을 설정해야 합니다.

## 개발 계획

- [ ] 사용자 인증 (Sign In)
- [ ] 발음 평가 (음성-자막 일치도)
- [ ] 학습 통계 대시보드
- [ ] 오프라인 모드 지원
- [ ] 더 많은 언어 지원
- [ ] 커뮤니티 기능 (다른 사용자와 발음 비교)

## 참고 자료

- [SwiftUI Documentation](https://developer.apple.com/xcode/swiftui/)
- [Speech Framework](https://developer.apple.com/documentation/speech)
- [URLSession](https://developer.apple.com/documentation/foundation/urlsession)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

## 라이센스

MIT License
