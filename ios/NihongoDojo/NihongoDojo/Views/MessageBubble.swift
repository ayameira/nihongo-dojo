import SwiftUI

struct MessageBubble: View {
    let message: Message
    @ObservedObject var ttsService = TTSService.shared

    var body: some View {
        HStack {
            if message.role == .user {
                Spacer(minLength: 60)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(bubbleColor)
                    .foregroundColor(textColor)
                    .clipShape(RoundedRectangle(cornerRadius: 18))

                if message.status == .streaming {
                    HStack(spacing: 4) {
                        ProgressView()
                            .scaleEffect(0.7)
                        Text("Streaming...")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }

                // TTS button for assistant messages
                if message.role == .assistant && message.status == .complete && !message.content.isEmpty {
                    Button {
                        if ttsService.currentPlayingId == message.id {
                            ttsService.stop()
                        } else {
                            Task {
                                await ttsService.speak(text: message.content, messageId: message.id)
                            }
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: ttsService.currentPlayingId == message.id ? "stop.fill" : "speaker.wave.2.fill")
                                .font(.caption)
                            Text(ttsService.currentPlayingId == message.id ? "Stop" : "Play")
                                .font(.caption)
                        }
                        .foregroundColor(.secondary)
                    }
                }
            }

            if message.role == .assistant {
                Spacer(minLength: 60)
            }
        }
        .padding(.horizontal)
    }

    private var bubbleColor: Color {
        switch message.role {
        case .user:
            return .blue
        case .assistant:
            return Color(.systemGray5)
        }
    }

    private var textColor: Color {
        switch message.role {
        case .user:
            return .white
        case .assistant:
            return .primary
        }
    }
}

#Preview {
    VStack {
        MessageBubble(message: Message(role: .user, content: "Hello!"))
        MessageBubble(message: Message(role: .assistant, content: "Hi there! How can I help you today?"))
    }
}
