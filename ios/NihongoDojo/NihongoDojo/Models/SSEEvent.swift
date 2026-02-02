import Foundation

enum SSEEventType: String {
    case text
    case toolCall = "tool_call"
    case toolResult = "tool_result"
    case usage
    case done
    case error
}

struct SSEEvent {
    let type: SSEEventType
    let content: String?
    let name: String?
    let error: String?

    init?(from line: String) {
        guard line.hasPrefix("data: ") else { return nil }

        let jsonString = String(line.dropFirst(6))
        guard let data = jsonString.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let typeString = json["type"] as? String,
              let type = SSEEventType(rawValue: typeString) else {
            return nil
        }

        self.type = type
        self.content = json["content"] as? String
        self.name = json["name"] as? String
        self.error = json["error"] as? String
    }
}
