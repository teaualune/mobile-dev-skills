// Template: tests for a screen's section 6 scenarios, on the view model the view renders.
//
// Each description starts with the requirement id and the scenario title,
// exactly as the spec writes them. The spec's `test` anchors point at that text.
//
// Adjust to match project conventions:
//   - Where do fakes live, and does the project use a mocking library?
//   - `@testable import` the app target's module by its real name.

import Foundation
import Testing
@testable import App // <-- the app target's module

@MainActor
struct ExampleListViewModelTests {
    // The view shows `state` before its `.task` load finishes.
    @Test("example.1 Loading")
    func loading() {
        let viewModel = ExampleListViewModel(repository: FakeExampleRepository(result: .success([])))

        #expect(viewModel.state == .loading)
    }

    @Test("example.1 Error")
    func error() async {
        let repository = FakeExampleRepository(result: .failure(FakeError.offline))
        let viewModel = ExampleListViewModel(repository: repository)

        await viewModel.load()
        #expect(viewModel.state == .failed)

        repository.result = .success([.sample])
        await viewModel.retry()
        #expect(viewModel.state == .loaded([.sample]))
        #expect(repository.listCalls == 2)
    }

    @Test("example.1 Empty")
    func empty() async {
        let viewModel = ExampleListViewModel(repository: FakeExampleRepository(result: .success([])))

        await viewModel.load()

        #expect(viewModel.state == .empty)
    }

    @Test("example.1 Success")
    func success() async {
        let viewModel = ExampleListViewModel(repository: FakeExampleRepository(result: .success([.sample])))

        await viewModel.load()

        #expect(viewModel.state == .loaded([.sample]))
    }
}

@MainActor
final class FakeExampleRepository: ExampleRepository {
    var result: Result<[Example], any Error>
    private(set) var listCalls = 0

    init(result: Result<[Example], any Error>) {
        self.result = result
    }

    func list() async throws -> [Example] {
        listCalls += 1
        return try result.get()
    }
}

enum FakeError: Error {
    case offline
}

extension Example {
    static let sample = Example(id: "1", name: "First", createdAt: Date(timeIntervalSince1970: 0))
}
