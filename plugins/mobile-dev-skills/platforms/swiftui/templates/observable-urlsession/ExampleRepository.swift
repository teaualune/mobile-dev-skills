// Template: a repository protocol and its URLSession implementation.
// Adjust to match project conventions:
//   - Is there a shared API client that builds requests and maps errors? Use it.
//   - Does the project throw its own error type, or return a Result?

import Foundation

protocol ExampleRepository: Sendable {
    func list() async throws -> [Example]
}

enum ExampleRepositoryError: Error, Equatable {
    case invalidResponse
    case status(Int)
}

struct URLSessionExampleRepository: ExampleRepository {
    let baseURL: URL
    var session: URLSession = .shared

    func list() async throws -> [Example] {
        let (data, response) = try await session.data(from: baseURL.appending(path: "examples"))
        try Self.check(response)
        return try Self.decoder().decode(Page.self, from: data).items
    }

    private static func check(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { throw ExampleRepositoryError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else { throw ExampleRepositoryError.status(http.statusCode) }
    }

    private static func decoder() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }

    private struct Page: Decodable {
        let items: [Example]
    }
}
