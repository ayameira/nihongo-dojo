import Foundation
import SwiftUI
import Combine

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var inputText: String = ""
    @Published var isLoading: Bool = false
    @Published var agentStatus: String? = nil
    @Published var error: String? = nil

    private let chatService = ChatService()
    private var currentSessionId: String?

    func loadHistory(sessionId: String) async {
        currentSessionId = sessionId
        isLoading = true
        error = nil

        do {
            messages = try await chatService.loadHistory(sessionId: sessionId)
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func sendMessage() async {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              let sessionId = currentSessionId else { return }

        let content = inputText
        inputText = ""

        // Add user message
        let userMessage = Message(role: .user, content: content, status: .complete)
        messages.append(userMessage)

        // Add placeholder assistant message
        let assistantMessage = Message(role: .assistant, content: "", status: .streaming)
        messages.append(assistantMessage)
        let assistantIndex = messages.count - 1

        isLoading = true
        agentStatus = "Thinking..."
        error = nil

        do {
            for try await event in chatService.streamMessage(sessionId: sessionId, content: content) {
                switch event.type {
                case .text:
                    if let text = event.content {
                        messages[assistantIndex].content += text
                    }
                case .toolCall:
                    if let name = event.name {
                        agentStatus = "Using \(name)..."
                    }
                case .toolResult:
                    agentStatus = "Thinking..."
                case .done:
                    messages[assistantIndex].status = .complete
                    agentStatus = nil
                case .error:
                    messages[assistantIndex].status = .error
                    self.error = event.error ?? "Unknown error"
                    agentStatus = nil
                case .usage:
                    break
                }
            }
        } catch {
            messages[assistantIndex].status = .error
            self.error = error.localizedDescription
            agentStatus = nil
        }

        isLoading = false
    }

    func clearSession() {
        messages = []
        currentSessionId = nil
        error = nil
    }
}
