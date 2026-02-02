import Foundation

struct Speaker: Identifiable, Codable {
    let id: Int
    let name: String
    let style: String
    let displayName: String

    enum CodingKeys: String, CodingKey {
        case id, name, style
        case displayName = "display_name"
    }
}

struct SpeakersResponse: Codable {
    let speakers: [Speaker]
    let defaultSpeakerId: Int

    enum CodingKeys: String, CodingKey {
        case speakers
        case defaultSpeakerId = "default_speaker_id"
    }
}
