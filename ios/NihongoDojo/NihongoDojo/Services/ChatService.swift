import Foundation

class ChatService {
    private let api = APIClient.shared

    func loadHistory(sessionId: String) async throws -> [Message] {
        let dtos: [ChatMessageDTO] = try await api.request("/api/chat/history/\(sessionId)")
        return dtos.map { $0.toMessage() }
    }

    func streamMessage(sessionId: String, content: String) -> AsyncThrowingStream<SSEEvent, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    guard let url = URL(string: "\(api.baseURL)/api/chat/stream") else {
                        continuation.finish(throwing: APIError.invalidURL)
                        return
                    }

                    var request = URLRequest(url: url)
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    request.setValue("text/event-stream", forHTTPHeaderField: "Accept")

                    let body: [String: Any] = [
                        "session_id": sessionId,
                        "message": content
                    ]
                    request.httpBody = try JSONSerialization.data(withJSONObject: body)

                    let (bytes, response) = try await URLSession.shared.bytes(for: request)

                    guard let httpResponse = response as? HTTPURLResponse,
                          (200...299).contains(httpResponse.statusCode) else {
                        continuation.finish(throwing: APIError.invalidResponse)
                        return
                    }

                    for try await line in bytes.lines {
                        if let event = SSEEvent(from: line) {
                            continuation.yield(event)
                            if event.type == .done || event.type == .error {
                                break
                            }
                        }
                    }

                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
}
