// Template: a stub repository for when the backend API isn't ready yet.
// Use it when the spec marks the entity provisional. When the real API is ready:
//   1. Delete this file.
//   2. Wire the real repository where the stub is provided.
//   3. Remove the TODO(api) comments from the model.

import Foundation

// TODO(api): delete this file when the real backend is ready.
struct StubExampleRepository: ExampleRepository {
    // TODO(api): replace with sample data matching the agreed shape
    private static let samples: [Example] = []

    func list() async throws -> [Example] {
        try await Task.sleep(for: .milliseconds(400))
        return Self.samples
    }
}
