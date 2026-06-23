import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            // 학습 탭
            LearningView()
                .tabItem {
                    Label("학습", systemImage: "book.fill")
                }
                .tag(0)

            // 약점 탭
            WeaknessesView(viewModel: viewModel)
                .tabItem {
                    Label("약점", systemImage: "exclamationmark.circle.fill")
                }
                .tag(1)

            // 설정 탭
            SettingsView(viewModel: viewModel)
                .tabItem {
                    Label("설정", systemImage: "gear")
                }
                .tag(2)
        }
        .onAppear {
            viewModel.initializeApp()
        }
    }
}

// MARK: - Learning View

struct LearningView: View {
    @StateObject private var apiService = APIService.shared
    @State private var youtubeUrl = ""
    @State private var currentStep = 0
    @State private var learningText = "준비 중..."
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var schedule: [String] = []
    @State private var currentDay = 1

    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                if currentStep == 0 {
                    // URL 입력 화면
                    urlInputView
                } else if currentStep == 1 {
                    // 학습 화면
                    learningView
                }
            }
            .navigationTitle("AI EchoDrive")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private var urlInputView: some View {
        VStack(spacing: 20) {
            Text("AI EchoDrive")
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(.blue)

            VStack(alignment: .leading, spacing: 10) {
                Text("YouTube 링크")
                    .font(.headline)

                TextField("https://www.youtube.com/watch?v=...", text: $youtubeUrl)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.URL)
                    .autocapitalization(.none)
            }

            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding()
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(8)
            }

            Button(action: analyzeVideo) {
                if isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                } else {
                    Text("학습 스케줄 생성하기")
                }
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(isLoading ? Color.gray : Color.blue)
            .foregroundColor(.white)
            .cornerRadius(10)
            .disabled(isLoading || youtubeUrl.isEmpty)

            Spacer()
        }
        .padding()
    }

    private var learningView: some View {
        VStack(spacing: 20) {
            VStack(alignment: .leading) {
                Text("Day \(currentDay)")
                    .font(.headline)
                Text("오늘의 학습 구간")
                    .font(.caption)
                    .foregroundColor(.gray)
            }

            Text(learningText)
                .font(.title2)
                .padding()
                .frame(maxWidth: .infinity)
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)

            HStack(spacing: 40) {
                Button(action: nextPhrase) {
                    VStack(spacing: 8) {
                        Image(systemName: "checkmark.circle.fill")
                            .resizable()
                            .frame(width: 60, height: 60)
                        Text("들었음")
                            .font(.caption)
                    }
                    .foregroundColor(.green)
                }

                Button(action: markAsWeakness) {
                    VStack(spacing: 8) {
                        Image(systemName: "xmark.circle.fill")
                            .resizable()
                            .frame(width: 60, height: 60)
                        Text("못 들었음")
                            .font(.caption)
                    }
                    .foregroundColor(.red)
                }
            }

            Button(action: { currentStep = 0 }) {
                Text("새로운 영상 분석하기")
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.gray.opacity(0.2))
                    .cornerRadius(10)
            }
            .foregroundColor(.blue)

            Spacer()
        }
        .padding()
    }

    private func analyzeVideo() {
        isLoading = true
        errorMessage = nil

        Task {
            do {
                let response = try await apiService.analyzeVideo(url: youtubeUrl)
                schedule = parseSchedule(response.schedule)
                currentDay = 1
                learningText = schedule.first ?? "No content"
                currentStep = 1
            } catch let error as APIError {
                errorMessage = error.errorDescription ?? "알 수 없는 오류"
            } catch {
                errorMessage = "오류: \(error.localizedDescription)"
            }
            isLoading = false
        }
    }

    private func nextPhrase() {
        if currentDay < schedule.count {
            currentDay += 1
            learningText = schedule[currentDay - 1]
        } else {
            errorMessage = "모든 구간을 완료했습니다!"
        }
    }

    private func markAsWeakness() {
        Task {
            do {
                _ = try await apiService.saveWeakness(
                    userId: "user_1",
                    phrase: learningText,
                    timestamp: Double(currentDay) * 5.0
                )
                nextPhrase()
            } catch let error as APIError {
                errorMessage = error.errorDescription ?? "저장 실패"
            }
        }
    }

    private func parseSchedule(_ scheduleText: String) -> [String] {
        scheduleText
            .split(separator: "\n")
            .filter { !$0.isEmpty && !$0.contains("[Day") && !$0.contains("[Day") }
            .map(String.init)
    }
}

// MARK: - Weaknesses View

struct WeaknessesView: View {
    @StateObject private var apiService = APIService.shared
    @ObservedObject var viewModel: ContentViewModel
    @State private var weaknesses: [Weakness] = []
    @State private var isLoading = false

    var body: some View {
        NavigationView {
            VStack {
                if isLoading {
                    ProgressView()
                } else if weaknesses.isEmpty {
                    VStack(spacing: 20) {
                        Image(systemName: "checkmark.seal.fill")
                            .font(.system(size: 60))
                            .foregroundColor(.green)
                        Text("저장된 약점이 없습니다")
                            .font(.headline)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.gray.opacity(0.1))
                } else {
                    List {
                        ForEach(weaknesses) { weakness in
                            VStack(alignment: .leading, spacing: 8) {
                                Text(weakness.phrase)
                                    .font(.headline)
                                Text(weakness.created_at)
                                    .font(.caption)
                                    .foregroundColor(.gray)
                            }
                            .padding(.vertical, 8)
                        }
                    }
                }
            }
            .navigationTitle("약점 저장소")
            .onAppear(perform: loadWeaknesses)
            .refreshable {
                await loadWeaknessesAsync()
            }
        }
    }

    private func loadWeaknesses() {
        isLoading = true
        Task {
            await loadWeaknessesAsync()
        }
    }

    private func loadWeaknessesAsync() async {
        do {
            let response = try await apiService.getWeaknesses(userId: "user_1")
            weaknesses = response.weaknesses
        } catch {
            weaknesses = []
        }
        isLoading = false
    }
}

// MARK: - Settings View

struct SettingsView: View {
    @ObservedObject var viewModel: ContentViewModel
    @State private var selectedMode: LearningMode = .echoing
    @State private var dailyMinutes = 5

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("학습 모드")) {
                    Picker("선택", selection: $selectedMode) {
                        ForEach(LearningMode.allCases, id: \.self) { mode in
                            Text(mode.rawValue)
                                .tag(mode)
                        }
                    }
                    .onChange(of: selectedMode) { newValue in
                        viewModel.updateLearningMode(newValue)
                    }

                    Text(selectedMode.description)
                        .font(.caption)
                        .foregroundColor(.gray)
                }

                Section(header: Text("학습 시간")) {
                    HStack {
                        Text("하루 학습 시간")
                        Spacer()
                        Picker("분", selection: $dailyMinutes) {
                            ForEach([5, 10, 15, 20, 30], id: \.self) { minutes in
                                Text("\(minutes)분").tag(minutes)
                            }
                        }
                    }
                }

                Section(header: Text("정보")) {
                    HStack {
                        Text("앱 버전")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.gray)
                    }
                }
            }
            .navigationTitle("설정")
        }
    }
}

// MARK: - View Model

class ContentViewModel: ObservableObject {
    @Published var appState = AppState()
    @Published var weaknessCount = 0

    func initializeApp() {
        // 앱 초기화
    }

    func updateLearningMode(_ mode: LearningMode) {
        appState.currentMode = mode
    }

    func loadWeaknesses() {
        // 약점 로드
    }
}

#Preview {
    ContentView()
}
