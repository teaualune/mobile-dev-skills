// Template: a destination in a value-based NavigationStack.
// Adjust to match project conventions:
//   - One app-wide Route enum, a router object, or a coordinator? Add the case there.
//   - A destination with parameters is a case with associated values: `case example(id: Example.ID)`.
//   - A deep link maps its URL to the same case in the root view's `onOpenURL`.

import SwiftUI

enum Route: Hashable {
    case examples
}

extension View {
    // Apply once, inside the root NavigationStack.
    func routeDestinations(repository: any ExampleRepository) -> some View {
        navigationDestination(for: Route.self) { route in
            switch route {
            case .examples:
                ExampleListView(viewModel: ExampleListViewModel(repository: repository))
            }
        }
    }
}
