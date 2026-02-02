import Foundation
import Combine

@MainActor
class SessionsViewModel: ObservableObject {
    @Published var sessions: [Session] = []
    @Published var currentSessionId: String?
    @Published var isLoading: Bool = false
    @Published var error: String? = nil

    private let sessionService = SessionService()
    private let defaults = UserDefaults.standard
    private let sessionIdKey = "nihongo_session_id"

    init() {
        currentSessionId = defaults.string(forKey: sessionIdKey)
    }

    func loadSessions() async {
        isLoading = true
        error = nil

        do {
            sessions = try await sessionService.loadSessions()

            // Auto-create session if none exist
            if sessions.isEmpty {
                await createNewSession()
            } else if currentSessionId == nil {
                currentSessionId = sessions.first?.id
                saveCurrentSessionId()
            }
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func createNewSession() async {
        let newId = SessionService.generateSessionId()

        do {
            let session = try await sessionService.createSession(id: newId)
            sessions.insert(session, at: 0)
            currentSessionId = session.id
            saveCurrentSessionId()
        } catch {
            self.error = error.localizedDescription
        }
    }

    func selectSession(_ session: Session) {
        currentSessionId = session.id
        saveCurrentSessionId()
    }

    func deleteSession(_ session: Session) async {
        do {
            try await sessionService.deleteSession(id: session.id)
            sessions.removeAll { $0.id == session.id }

            if currentSessionId == session.id {
                currentSessionId = sessions.first?.id
                saveCurrentSessionId()
            }
        } catch {
            self.error = error.localizedDescription
        }
    }

    private func saveCurrentSessionId() {
        defaults.set(currentSessionId, forKey: sessionIdKey)
    }
}
