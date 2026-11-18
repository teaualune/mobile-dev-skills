// Template: a Codable model.
// Adjust to match project conventions:
//   - Does a shared JSONDecoder set the key and date strategies, or does each model declare CodingKeys?
//   - Does the project keep DTOs apart from its models?

import Foundation

struct Example: Codable, Identifiable, Hashable, Sendable {
    let id: String
    let name: String
    let createdAt: Date
}
