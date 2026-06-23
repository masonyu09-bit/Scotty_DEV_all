import Foundation

// MARK: - API Request Models

struct VideoRequest: Codable {
    let url: String
}

struct WeaknessRequest: Codable {
    let user_id: String
    let phrase: String
    let timestamp: Double
}

struct PhraseRequest: Codable {
    let phrase: String
}

// MARK: - API Response Models

struct AnalysisResponse: Codable {
    let video_id: String
    let transcript_length: Int
    let schedule: String
    let status: String
}

struct WeaknessResponse: Codable {
    let status: String
    let message: String
    let user_id: String
    let phrase: String
}

struct WeaknessListResponse: Codable {
    let user_id: String
    let weaknesses: [Weakness]
    let count: Int
}

struct Weakness: Codable, Identifiable {
    let id: Int
    let user_id: String
    let phrase: String
    let timestamp: Double
    let created_at: String
    let reviewed: Int

    var isReviewed: Bool {
        reviewed == 1
    }
}

struct ExplanationResponse: Codable {
    let phrase: String
    let explanation: String
    let status: String
}

struct HealthResponse: Codable {
    let status: String
    let service: String
}

// MARK: - App Models

struct LearningSession: Identifiable {
    let id = UUID()
    let videoId: String
    let day: Int
    let phrase: String
    let startTime: Double
    let duration: Double
}

struct UserSettings: Codable {
    var userId: String
    var preferredMode: String = "Echoing"
    var dailyMinutes: Int = 5
}

struct LearningProgress: Codable, Identifiable {
    let id: Int
    let user_id: String
    let video_id: String
    let day: Int
    let completed: Int
    let completed_at: String?
    let created_at: String

    var isCompleted: Bool {
        completed == 1
    }
}

// MARK: - Error Models

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case decodingError
    case serverError(String)
    case networkError(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL format"
        case .invalidResponse:
            return "Invalid server response"
        case .decodingError:
            return "Failed to decode response"
        case .serverError(let message):
            return "Server error: \(message)"
        case .networkError(let message):
            return "Network error: \(message)"
        }
    }
}

// MARK: - View Models

enum LearningMode: String, CaseIterable {
    case echoing = "Echoing"
    case shading = "Shading"

    var description: String {
        switch self {
        case .echoing:
            return "자막 없이 소리만 듣고 따라 읽기"
        case .shading:
            return "자막을 보며 음성 듣기"
        }
    }
}

struct AppState {
    var userId: String = "user_\(UUID().uuidString.prefix(8))"
    var currentMode: LearningMode = .echoing
    var isLoggedIn: Bool = false
    var currentVideo: AnalysisResponse?
    var weaknesses: [Weakness] = []
}
