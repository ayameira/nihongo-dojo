import Foundation

class SessionService {
    private let api = APIClient.shared

    func loadSessions() async throws -> [Session] {
        return try await api.request("/api/sessions")
    }

    func createSession(id: String, name: String? = nil) async throws -> Session {
        let request = CreateSessionRequest(id: id, name: name)
        return try await api.post("/api/sessions", body: request)
    }

    func deleteSession(id: String) async throws {
        try await api.delete("/api/sessions/\(id)")
    }

    static func generateSessionId() -> String {
        let timestamp = Int(Date().timeIntervalSince1970 * 1000)
        let random = String((0..<8).map { _ in "abcdefghijklmnopqrstuvwxyz0123456789".randomElement()! })
        return "session_\(timestamp)_\(random)"
    }
}
