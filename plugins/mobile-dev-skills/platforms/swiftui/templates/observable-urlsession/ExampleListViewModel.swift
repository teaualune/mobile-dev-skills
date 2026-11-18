// Template: a screen's view model (@Observable, iOS 17+).
// Adjust to match project conventions:
//   - How do view models get their dependencies: initializer, environment, a DI container?
//   - Does the project model a screen's state as one enum, or as separate properties?

import Foundation
import Observation

@MainActor
@Observable
final class ExampleListViewModel {
    enum State: Equatable {
        case loading
        case failed
        case empty
        case loaded([Example])
    }

    private(set) var state: State = .loading
    private let repository: any ExampleRepository

    init(repository: some ExampleRepository) {
        self.repository = repository
    }

    // Keeps the current content on screen during a pull to refresh.
    func load() async {
        do {
            let items = try await repository.list()
            state = items.isEmpty ? .empty : .loaded(items)
        } catch {
            // A load cancelled because the view went away keeps the current state.
            if !Self.isCancellation(error) {
                state = .failed
            }
        }
    }

    func retry() async {
        state = .loading
        await load()
    }

    private static func isCancellation(_ error: any Error) -> Bool {
        error is CancellationError || (error as? URLError)?.code == .cancelled
    }
}
