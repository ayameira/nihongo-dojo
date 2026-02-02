import SwiftUI

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var backendURL: String = APIClient.shared.baseURL
    @State private var speakers: [Speaker] = []
    @State private var selectedSpeakerId: Int = TTSService.shared.speakerId
    @State private var isLoadingSpeakers: Bool = false

    var body: some View {
        NavigationView {
            Form {
                Section {
                    TextField("Backend URL", text: $backendURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                } header: {
                    Text("Server")
                } footer: {
                    Text("The URL of your Nihongo Dojo backend server (e.g., http://100.107.147.109:8000)")
                }

                Section {
                    Button("Test Connection") {
                        Task { await testConnection() }
                    }
                }

                Section {
                    if isLoadingSpeakers {
                        HStack {
                            ProgressView()
                            Text("Loading voices...")
                        }
                    } else if speakers.isEmpty {
                        Text("No voices available")
                            .foregroundColor(.secondary)
                    } else {
                        Picker("Voice", selection: $selectedSpeakerId) {
                            ForEach(speakers) { speaker in
                                Text(speaker.displayName).tag(speaker.id)
                            }
                        }
                    }
                } header: {
                    Text("Text-to-Speech")
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Save") {
                        APIClient.shared.baseURL = backendURL
                        TTSService.shared.speakerId = selectedSpeakerId
                        dismiss()
                    }
                }
            }
            .task {
                await loadSpeakers()
            }
        }
    }

    private func loadSpeakers() async {
        isLoadingSpeakers = true
        do {
            speakers = try await TTSService.shared.loadSpeakers()
        } catch {
            print("Failed to load speakers: \(error)")
        }
        isLoadingSpeakers = false
    }

    @State private var connectionStatus: String? = nil

    private func testConnection() async {
        do {
            // Temporarily set the URL
            let oldURL = APIClient.shared.baseURL
            APIClient.shared.baseURL = backendURL

            struct HealthResponse: Codable {
                let status: String
                let version: String
            }

            let _: HealthResponse = try await APIClient.shared.request("/api/health")
            connectionStatus = "Connected!"

            // Restore if test only
            APIClient.shared.baseURL = oldURL
        } catch {
            connectionStatus = "Failed: \(error.localizedDescription)"
        }
    }
}
