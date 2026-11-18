# Standards — SwiftUI

Swift and SwiftUI rules, on top of the common `../standards.md`. They apply to all hand-written Swift code, on top of the detected conventions. In a Flutter project, where this adapter is the native adapter for `ios/`, only the rules under "Every Swift file" apply, to the Swift files a run writes there, and **Form**, **Unescaped titles**, **Fakes**, **Persistence** and **Host tests** to its native unit tests (the Flutter adapter's "Native interop"), so their descriptions are `@Test("<id> <Scenario title>")` strings this adapter's test-name search finds. That project's other scenario tests follow its own adapter, and Objective-C files are out of scope.

## Code

Every Swift file:

- **No force unwrap, `try!` or `as!` in hand-written code.** Use `guard let`, `if let`, `??`, `do`/`catch` or `as?`:

  ```swift
  // Bad:  let url = URL(string: path)!
  // Good:
  guard let url = URL(string: path) else { throw APIError.invalidURL(path) }
  ```

  Exempt: generated files (the "Project layout" list of the adapter that owns the project, e.g. SwiftGen output here or Pigeon's Swift output in a Flutter project) and the `@IBOutlet`s a project already declares implicitly unwrapped.
- **No swallowed errors.** No empty `catch {}`, and no `try?` that drops an error the spec gives a behavior for; such an error reaches the state the view shows.
- **Swift concurrency in new code**: `async`/`await` instead of completion handlers, except where an API you implement takes a callback (a Flutter `FlutterResult`, a delegate method). Never silence a concurrency error with `@unchecked Sendable`, `nonisolated(unsafe)` or a lower language mode.
- **UI work on the main actor.** Whatever updates what the user sees runs on `@MainActor`, and so does every Flutter channel call: a `FlutterResult` reply and each message sent to Dart.
- **Newer APIs behind `#available`.** An API newer than the deployment target goes behind `if #available` (or `@available`) with a fallback that keeps the feature working on the older systems; a fallback that drops the feature only where the spec says so.

In a SwiftUI app:

- **View models on the main actor.** Each view model or store class is `@MainActor` (implied where the target's default isolation is `MainActor`), and `@Observable` from iOS 17 unless the project's view models are `ObservableObject`.
- **Load in `.task`**, not in `onAppear` with a `Task {}`: `.task` is cancelled when the view goes away. Pull to refresh goes through `.refreshable`, calling the same async load. With TCA:
  - screen-scoped work starts from `.task { await store.send(.task).finish() }`, so its effect ends with the view;
  - an effect that must keep running while another screen is pushed on top, such as a subscription to app-wide events, never starts from `.task`, which is cancelled when the view disappears. It starts from an action the view sends in `onAppear`, its effect is `.cancellable(id:cancelInFlight: true)` so a second appearance restarts it rather than adding a second one, and it lives with the store: TCA cancels a child feature's effects when its state leaves the navigation stack or its presentation.
- **Unbounded lists in `List` or a `LazyVStack`**, never a `VStack` inside a `ScrollView`.
- **Strings in the String Catalog.** When the project has a `Localizable.xcstrings`, each new user-visible string is a key there with a value in every language the catalog holds. Write keys the way the convention probes found them: `Text("key")` for a `LocalizedStringKey` and `String(localized: "key")` where a `String` is needed; the symbols Xcode 26 generates from the catalog, `Text(.keyName)` and `String(localized: .keyName)`; or SwiftGen's `L10n`. With `.strings` files, the key goes into each `.lproj`.
- **A provisional stub's delay** is `try await Task.sleep(for: .milliseconds(400))` (below iOS 16, `try await Task.sleep(nanoseconds: 400_000_000)`).
- **The stub's file** is named after its type, `StubExampleRepository.swift`, next to `ExampleRepository.swift`.
- **Shipped models migrate.** A change to a persisted model that has shipped adds a schema version and a migration stage (SwiftData: a new `VersionedSchema` in the `SchemaMigrationPlan`), never an edit of the shipped schema in place.

## Tests

- **Form.** Swift Testing: `@Test("saved-articles.1 Empty")` on a function of a suite type, even where the project's older tests are XCTest (both run in one target), since an XCTest method name can't hold the description. Expectations are `#expect` and `#require`; a suite that tests a `@MainActor` view model is `@MainActor` too. For the fallback stack with nothing to mirror, start from `templates/observable-urlsession/ExampleListViewModelTests.swift`.
- **Screens.** A SwiftUI view has no host-test harness in Xcode alone, so a screen's state and action scenarios are tested on the state holder the view renders, its view model or its TCA reducer: the WHEN is the call or action the view's control makes (`viewModel.load()`, `.retryTapped`), and each THEN is an expectation on the state the view shows for it, the copy the state holder provides, and the calls the faked dependency received. A THEN about which view or control shows (an error view with Retry) is met by the view's one `switch` over that state, which the review reads, and by a snapshot test of each state where the project has swift-snapshot-testing. With ViewInspector in the project, the test may inspect the view instead.
- **TCA.** A reducer's scenario is a `TestStore` test: the WHEN is `await store.send(.action)`, and each THEN is a state change in its trailing closure or an `await store.receive(\.action)`. Keep the store exhaustive unless the project's tests turn exhaustivity off.
- **Unescaped titles.** A raw string, `#"…"#`, when the title holds `"` or a backslash.
- **Fakes** are hand-written types that conform to the dependency's protocol, unless the project uses a mocking library; a fake records each call a THEN line names, and a provisional repository's fake conforms to the protocol its stub implements. With TCA, a test overrides the dependency client in `withDependencies` instead.
- **Persistence.** A test that touches stored data uses an in-memory store (SwiftData: `ModelConfiguration(isStoredInMemoryOnly: true)`), reached the way the code reaches its store, or fakes that dependency; never the app's store on disk.
- **Platform scenarios.** A SwiftUI app has one platform, `ios`, so a tag changes nothing about the test.
- **Host tests** are the unit-test target's, run on a simulator. Tests in a UI-test target need the app running. A project without a unit-test target gets one first ("Project layout" in `PLATFORM.md`).
