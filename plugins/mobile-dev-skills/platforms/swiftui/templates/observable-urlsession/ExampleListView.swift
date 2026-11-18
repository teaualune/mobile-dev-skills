// Template: a screen with its four states, loading in `.task`.
// Adjust to match project conventions:
//   - Shared loading, error and empty views? Use them instead of the system ones.
//   - Strings are String Catalog keys; add each one in every language the catalog holds.

import SwiftUI

struct ExampleListView: View {
    @State var viewModel: ExampleListViewModel

    var body: some View {
        // The List stays in every state, so pull to refresh works on Empty and Error too.
        List(items) { item in
            Text(item.name)
        }
        .overlay { stateView }
        .refreshable { await viewModel.load() }
        .navigationTitle("Examples")
        .task { await viewModel.load() }
    }

    private var items: [Example] {
        if case .loaded(let items) = viewModel.state {
            return items
        }
        return []
    }

    @ViewBuilder
    private var stateView: some View {
        switch viewModel.state {
        case .loading:
            ProgressView()
        case .failed:
            ContentUnavailableView {
                Label("Something went wrong", systemImage: "exclamationmark.triangle")
            } actions: {
                Button("Retry") {
                    Task { await viewModel.retry() }
                }
            }
        case .empty:
            ContentUnavailableView("Nothing here yet", systemImage: "tray")
        case .loaded:
            EmptyView()
        }
    }
}

#Preview {
    NavigationStack {
        ExampleListView(viewModel: ExampleListViewModel(repository: StubExampleRepository()))
    }
}
