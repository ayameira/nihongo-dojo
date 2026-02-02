import Foundation
import AVFoundation
import Combine

class TTSService: ObservableObject {
    static let shared = TTSService()

    private let api = APIClient.shared
    private let defaults = UserDefaults.standard
    private let speakerIdKey = "nihongo_tts_speaker_id"

    private var audioPlayer: AVAudioPlayer?
    @Published var isPlaying: Bool = false
    @Published var currentPlayingId: String? = nil

    var speakerId: Int {
        get { defaults.integer(forKey: speakerIdKey) == 0 ? 2 : defaults.integer(forKey: speakerIdKey) }
        set { defaults.set(newValue, forKey: speakerIdKey) }
    }

    private init() {
        // Configure audio session for playback
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            print("Failed to configure audio session: \(error)")
        }
    }

    func loadSpeakers() async throws -> [Speaker] {
        let response: SpeakersResponse = try await api.request("/api/media/speakers")
        return response.speakers
    }

    func speak(text: String, messageId: String) async {
        // Stop any current playback
        stop()

        await MainActor.run {
            isPlaying = true
            currentPlayingId = messageId
        }

        do {
            guard let url = URL(string: "\(api.baseURL)/api/media/tts") else {
                throw APIError.invalidURL
            }

            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")

            let body: [String: Any] = [
                "text": text,
                "speaker_id": speakerId
            ]
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                throw APIError.invalidResponse
            }

            await MainActor.run {
                do {
                    audioPlayer = try AVAudioPlayer(data: data)
                    audioPlayer?.delegate = AudioPlayerDelegate.shared
                    AudioPlayerDelegate.shared.onFinish = { [weak self] in
                        self?.isPlaying = false
                        self?.currentPlayingId = nil
                    }
                    audioPlayer?.play()
                } catch {
                    print("Failed to play audio: \(error)")
                    isPlaying = false
                    currentPlayingId = nil
                }
            }
        } catch {
            await MainActor.run {
                isPlaying = false
                currentPlayingId = nil
            }
            print("TTS error: \(error)")
        }
    }

    func stop() {
        audioPlayer?.stop()
        audioPlayer = nil
        isPlaying = false
        currentPlayingId = nil
    }
}

class AudioPlayerDelegate: NSObject, AVAudioPlayerDelegate {
    static let shared = AudioPlayerDelegate()
    var onFinish: (() -> Void)?

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        DispatchQueue.main.async {
            self.onFinish?()
        }
    }
}
