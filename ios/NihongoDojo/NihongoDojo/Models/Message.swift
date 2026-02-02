import Foundation

enum MessageRole: String, Codable {
    case user
    case assistant
}

enum MessageStatus {
    case sending
    case streaming
    case complete
    case error
}

struct Message: Identifiable {
    let id: String
    let role: MessageRole
    var content: String
    let timestamp: Date
    var status: MessageStatus

    init(id: String = UUID().uuidString, role: MessageRole, content: String, timestamp: Date = Date(), status: MessageStatus = .complete) {
        self.id = id
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.status = status
    }
}

// API response models
struct ChatHistoryResponse: Codable {
    let messages: [ChatMessageDTO]
}

struct ChatMessageDTO: Codable {
    let id: Int
    let role: String
    let content: String
    let createdAt: String

    enum CodingKeys: String, CodingKey {
        case id, role, content
        case createdAt = "created_at"
    }

    func toMessage() -> Message {
        let dateFormatter = ISO8601DateFormatter()
        dateFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let date = dateFormatter.date(from: createdAt) ?? Date()

        return Message(
            id: String(id),
            role: role == "user" ? .user : .assistant,
            content: content,
            timestamp: date,
            status: .complete
        )
    }
}
