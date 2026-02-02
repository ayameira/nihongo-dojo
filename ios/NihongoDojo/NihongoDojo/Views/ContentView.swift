import SwiftUI

struct ContentView: View {
    @StateObject private var sessionsViewModel = SessionsViewModel()
    @StateObject private var chatViewModel = ChatViewModel()

    @State private var showingSessions = false
    @State private var showingSettings = false

    var body: some View {
        NavigationStack {
            ChatView(viewModel: chatViewModel, sessionId: sessionsViewModel.currentSessionId)
                .navigationTitle(currentSessionName)
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button {
                            showingSessions = true
                        } label: {
                            Image(systemName: "list.bullet")
                        }
                    }

                    ToolbarItem(placement: .navigationBarTrailing) {
                        Menu {
                            Button {
                                Task { await sessionsViewModel.createNewSession() }
                            } label: {
                                Label("New Chat", systemImage: "plus")
                            }

                            Button {
                                showingSettings = true
                            } label: {
                                Label("Settings", systemImage: "gear")
                            }
                        } label: {
                            Image(systemName: "ellipsis.circle")
                        }
                    }
                }
        }
        .sheet(isPresented: $showingSessions) {
            SessionListView(viewModel: sessionsViewModel)
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView()
        }
        .task {
            await sessionsViewModel.loadSessions()
        }
        .onChange(of: sessionsViewModel.currentSessionId) { _, newId in
            chatViewModel.clearSession()
        }
        .alert("Error", isPresented: .constant(sessionsViewModel.error != nil)) {
            Button("OK") { sessionsViewModel.error = nil }
        } message: {
            Text(sessionsViewModel.error ?? "")
        }
    }

    private var currentSessionName: String {
        if let sessionId = sessionsViewModel.currentSessionId,
           let session = sessionsViewModel.sessions.first(where: { $0.id == sessionId }) {
            return session.displayName
        }
        return "Nihongo Dojo"
    }
}

#Preview {
    ContentView()
}
