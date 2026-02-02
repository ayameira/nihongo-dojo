import SwiftUI

struct SessionListView: View {
    @ObservedObject var viewModel: SessionsViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationView {
            List {
                ForEach(viewModel.sessions) { session in
                    SessionRow(
                        session: session,
                        isSelected: session.id == viewModel.currentSessionId
                    )
                    .contentShape(Rectangle())
                    .onTapGesture {
                        viewModel.selectSession(session)
                        dismiss()
                    }
                }
                .onDelete { indexSet in
                    Task {
                        for index in indexSet {
                            await viewModel.deleteSession(viewModel.sessions[index])
                        }
                    }
                }
            }
            .listStyle(.plain)
            .navigationTitle("Sessions")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Done") { dismiss() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task {
                            await viewModel.createNewSession()
                            dismiss()
                        }
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
        }
    }
}

struct SessionRow: View {
    let session: Session
    let isSelected: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(session.displayName)
                    .font(.headline)
                    .foregroundColor(isSelected ? .blue : .primary)

                if let preview = session.preview {
                    Text(preview)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            if isSelected {
                Image(systemName: "checkmark")
                    .foregroundColor(.blue)
            }
        }
        .padding(.vertical, 4)
    }
}
