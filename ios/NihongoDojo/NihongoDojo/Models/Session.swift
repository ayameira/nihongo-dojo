import Foundation

struct Session: Identifiable, Codable {
    let id: String
    var name: String?
    let preview: String?
    let messageCount: Int
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id, name, preview
        case messageCount = "message_count"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    var displayName: String {
        name ?? "New Chat"
    }
}

struct CreateSessionRequest: Codable {
    let id: String
    let name: String?
}

struct SessionsResponse: Codable {
    let sessions: [Session]
}
