import Foundation

class APIService: NSObject, ObservableObject {
    static let shared = APIService()

    // 백엔드 서버 주소 (실제 환경에 맞게 수정 필요)
    private let baseURL: String

    override init() {
        #if targetEnvironment(simulator)
        self.baseURL = "http://127.0.0.1:8000"
        #else
        // 실제 기기의 경우 로컬 네트워크의 서버 주소 사용
        self.baseURL = "http://192.168.1.100:8000"
        #endif

        super.init()
    }

    init(baseURL: String) {
        self.baseURL = baseURL
        super.init()
    }

    // MARK: - Public Methods

    /// 서버 헬스 체크
    func checkHealth() async throws -> HealthResponse {
        let url = try createURL(path: "/health")
        return try await performRequest(url: url, method: "GET", responseType: HealthResponse.self)
    }

    /// YouTube 영상 분석
    func analyzeVideo(url: String) async throws -> AnalysisResponse {
        let endpoint = try createURL(path: "/analyze")
        let request = VideoRequest(url: url)
        return try await performRequest(
            url: endpoint,
            method: "POST",
            body: request,
            responseType: AnalysisResponse.self
        )
    }

    /// 약점 저장
    func saveWeakness(userId: String, phrase: String, timestamp: Double = 0.0) async throws -> WeaknessResponse {
        let endpoint = try createURL(path: "/save-weakness")
        let request = WeaknessRequest(user_id: userId, phrase: phrase, timestamp: timestamp)
        return try await performRequest(
            url: endpoint,
            method: "POST",
            body: request,
            responseType: WeaknessResponse.self
        )
    }

    /// 약점 목록 조회
    func getWeaknesses(userId: String) async throws -> WeaknessListResponse {
        let endpoint = try createURL(path: "/weaknesses/\(userId)")
        return try await performRequest(url: endpoint, method: "GET", responseType: WeaknessListResponse.self)
    }

    /// 문장 설명 조회
    func explainPhrase(_ phrase: String) async throws -> ExplanationResponse {
        let endpoint = try createURL(path: "/explain", queryParams: ["phrase": phrase])
        return try await performRequest(url: endpoint, method: "GET", responseType: ExplanationResponse.self)
    }

    // MARK: - Private Methods

    /// URL 생성
    private func createURL(path: String, queryParams: [String: String] = [:]) throws -> URL {
        var components = URLComponents(string: baseURL + path)
        components?.queryItems = queryParams.map { URLQueryItem(name: $0.key, value: $0.value) }

        guard let url = components?.url else {
            throw APIError.invalidURL
        }
        return url
    }

    /// HTTP 요청 수행
    private func performRequest<T: Decodable>(
        url: URL,
        method: String,
        body: Encodable? = nil,
        responseType: T.Type
    ) async throws -> T {
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = method
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // 바디 인코딩
        if let body = body {
            urlRequest.httpBody = try JSONEncoder().encode(body)
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: urlRequest)

            // 응답 상태 확인
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            if httpResponse.statusCode != 200 {
                if let errorMessage = try? JSONDecoder().decode([String: String].self, from: data),
                   let detail = errorMessage["detail"] {
                    throw APIError.serverError(detail)
                }
                throw APIError.serverError("HTTP \(httpResponse.statusCode)")
            }

            // 응답 디코딩
            let decoder = JSONDecoder()
            let decodedResponse = try decoder.decode(responseType, from: data)
            return decodedResponse
        } catch let error as APIError {
            throw error
        } catch let error as DecodingError {
            throw APIError.decodingError
        } catch {
            throw APIError.networkError(error.localizedDescription)
        }
    }
}

// MARK: - URL Session Extension

extension URLSession {
    func data(for request: URLRequest) async throws -> (Data, URLResponse) {
        var task: URLSessionDataTask?
        let onCancel = { task?.cancel() }

        return try await withTaskCancellationHandler(
            operation: {
                try await withCheckedThrowingContinuation { continuation in
                    task = dataTask(with: request) { data, response, error in
                        if let error = error {
                            continuation.resume(throwing: error)
                        } else if let data = data, let response = response {
                            continuation.resume(returning: (data, response))
                        } else {
                            continuation.resume(throwing: APIError.invalidResponse)
                        }
                    }
                    task?.resume()
                }
            },
            onCancel: onCancel
        )
    }
}
