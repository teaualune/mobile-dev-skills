# SwiftUI adapter

Everything the feature workflow needs to know about native iOS apps built with SwiftUI. The process skills (`feature-workflow`, `feature-spec`, `feature-scaffold`, `feature-verify`) read this file instead of carrying iOS knowledge themselves. In a Flutter project it is also the native adapter for the `ios/` folder ("Native interop").

## Applies when

An Xcode project (`*.xcodeproj`, alone or in a `*.xcworkspace`) with an iOS app target whose sources `import SwiftUI`, or a `project.yml` (XcodeGen) or `Project.swift` (Tuist) that generates one, in the working directory or a folder below it — but not the `ios/` or `macos/` folder of a Flutter project (a `pubspec.yaml` beside that folder) or a React Native one (a `package.json` listing `react-native`), which that platform's adapter owns. If several qualify, ask which one the feature is for.

## Project layout

- **Root:** the folder holding the `.xcodeproj` (or the `.xcworkspace`, or the generator's manifest). `.mobile-dev-skills/` sits here, and the skills resolve their paths and run their commands here; in a monorepo, it is the app's folder, not the repository's root.
- **Manifest:** the project file, `<App>.xcodeproj/project.pbxproj`: its targets, the deployment target (`IPHONEOS_DEPLOYMENT_TARGET`), the Swift version and the Swift packages it references (`XCRemoteSwiftPackageReference`), with their resolved versions in `Package.resolved` (under `<App>.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/`, or the workspace's `xcshareddata/swiftpm/`). With CocoaPods, also `Podfile` and `Podfile.lock`. A generated project's manifest is `project.yml` or `Project.swift`. The test targets' package dependencies are the test packages.
- **Source:** the app target's folder (e.g. `Greeter/`), plus any local Swift package the app links. **Host tests:** the unit-test target's folder (e.g. `GreeterTests/`), which the verification run executes on a simulator. A UI-test target (XCUITest) holds tests that need the app running.
- **No unit-test target** (a project that never had tests): before Phase 2 writes its first code file, ask the user to add one in Xcode (File › New › Target › Unit Testing Bundle, hosted by the app and added to the scheme's test action) with the app target's deployment target, since Xcode gives a new target the newest iOS of its SDK. Then detect it again, with both targets' `IPHONEOS_DEPLOYMENT_TARGET` (`xcodebuild -project <App>.xcodeproj -target <target> -showBuildSettings`): a test target above the app goes back to the user before the baseline. Never create a target by editing the project file. Until one exists, no scenario has a host test to anchor to, and marking one `manual` needs the user's agreement.
- **Generated files**, never edited by hand and never anchored: SwiftGen and R.swift output, Sourcery's `*.generated.swift`, Apollo's output, `Pods/`, a project file that XcodeGen or Tuist generates, and `build/` and DerivedData.
- **Fingerprint** for `.mobile-dev-skills/stack.md`: the output of `cat *.xcodeproj/project.pbxproj | grep -e IPHONEOS_DEPLOYMENT_TARGET -e SWIFT_VERSION -e SWIFT_DEFAULT_ACTOR_ISOLATION -e repositoryURL -e minimumVersion -e productName | sort -u | cat - Podfile 2>/dev/null | git hash-object --stdin`, run at the root; for a generated project, `git hash-object project.yml` (or `Project.swift`). It leaves out the lines that change with every added file and every version bump.
- **File registration:** how a new file joins its target, which the convention probes decide:
  - **synchronized folders** (`PBXFileSystemSynchronizedRootGroup` in the project file, Xcode 16's default): a file written under a synchronized folder joins that folder's target with no project edit;
  - **XcodeGen or Tuist:** run `xcodegen generate` or `tuist generate` after adding files (the Codegen check);
  - **group-based project** (no synchronized folders): every new file needs a `PBXFileReference`, a group entry, and a `PBXBuildFile` listed in its target's `PBXSourcesBuildPhase` (`PBXResourcesBuildPhase` for a resource) in the project file. Before the first new file, ask the user whether to add the files in Xcode themselves or to have the project file edited; edit it only after that answer, and never reformat it.

## Stack layer

The project file and the packages it resolves are the source of truth for the stack. Identify:

- **UI**: SwiftUI, or SwiftUI mixed with UIKit (`UIHostingController`, `UIViewRepresentable`). The deployment target decides what is available: `@Observable` and `NavigationStack`'s value-based destinations need iOS 17 and 16. The default actor isolation (`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`, Xcode 26's default for new projects, or none) decides which types need an explicit `@MainActor` or `nonisolated`.
- **State**: `@Observable` view models, `ObservableObject` with `@Published`, The Composable Architecture (`swift-composable-architecture`), or Combine / RxSwift view models. With TCA, report its resolved version from `Package.resolved`, since its APIs changed across 1.x (`@ObservableState` from 1.7, for one).
- **Navigation**: `NavigationStack` with `navigationDestination(for:)`, a router or coordinator object, TCA's stack navigation, `NavigationSplitView`, or UIKit navigation around hosted views.
- **HTTP**: URLSession with async/await, Alamofire, Moya, Apollo iOS (GraphQL), or OpenAPI Generator / swift-openapi-generator clients. **Serialization**: `Codable`.
- **Persistence**: SwiftData, Core Data, GRDB, Realm, `UserDefaults` / `@AppStorage`. **DI**: initializer injection, SwiftUI environment values, Factory, Swinject, TCA's `@Dependency`.
- **Other relevant**: SwiftGen or R.swift for assets and strings, Kingfisher or Nuke for images, KeychainAccess.
- **Test packages**: Swift Testing (`import Testing`, Xcode 16+), XCTest, swift-snapshot-testing, ViewInspector, Quick/Nimble.

**Fallback — only when detection fails.** Label every fallback choice in the report as the Detection report shows, e.g. `State: FALLBACK: @Observable view models`, and ask the user to confirm it.

- State → `@MainActor @Observable` view models (`ObservableObject` with `@Published` below iOS 17)
- Navigation → `NavigationStack` with a `Route` enum and `navigationDestination(for:)`
- HTTP → URLSession with async/await, behind a repository protocol
- Serialization → `Codable`
- Tests → Swift Testing with hand-written fakes that conform to the dependency's protocol, when the project has no mocking library and no tests to mirror

**Mixed or ambiguous:**
- Several state approaches in the app (e.g. TCA features beside plain view models) → ask which one new features use. Don't pick.
- A UIKit app whose SwiftUI is only a few hosted views → ask whether the new screens are SwiftUI views hosted the same way.
- A package you don't recognize → say so, ask the user to confirm its role, and read one file that uses it before depending on it.

## Convention probes

Read in this order; each step informs the next.

1. **Project shape**: `xcodebuild -list -json` for the targets and schemes; the deployment target, the Swift version and the default actor isolation; the local Swift packages; whether a unit-test target exists; and the file registration ("Project layout": `grep -c PBXFileSystemSynchronizedRootGroup <App>.xcodeproj/project.pbxproj`, or a generator manifest).
2. **The app target's folder structure**: by feature (`Features/<Name>/`), by type (`Views/`, `ViewModels/`, `Models/`, `Services/`), or one Swift package per feature.
3. **One or two existing features** of similar shape, read end to end. They are the exemplars Phase 2 generates from.
   - A model → `struct` + `Codable`, `CodingKeys` or a decoder's key strategy, `Identifiable` / `Hashable`
   - An API client or repository → a protocol or a concrete type, request building, decoding, the error type it throws
   - A view model or store → `@Observable` or `ObservableObject`, `@MainActor`, how it gets its dependencies, how it exposes loading and error state; with TCA, the `@Reducer`'s layout, its dependency clients, and how a parent scopes and presents it
   - A persisted model, if there is one → SwiftData `@Model` or Core Data, whether the schema is versioned, and how code reaches the store (a dependency, an environment `ModelContext`, `@Query`)
   - A view → how it owns its view model (`@State`, `@StateObject`, `@Environment`, `@Bindable`), `.task` or `onAppear` loading, the loading, error and empty views it uses, `#Preview`s
   - The design system → `Color` / `Font` extensions, asset catalog color names, spacing constants
   - A test file, if there is one → Swift Testing or XCTest, `@testable import`, where fakes live, snapshot setup; with TCA, `TestStore` and its exhaustivity
4. **Navigation**: the root view (`NavigationStack`, `TabView`), how destinations are declared (a `Route` enum, `NavigationLink(value:)`, a router or coordinator), and deep links (`onOpenURL`, universal links).
5. **Localization**: a String Catalog (`Localizable.xcstrings`) or `.strings` files per `.lproj`, how keys are written (`Text("key")`, `String(localized:)`, the catalog's generated symbols such as `Text(.keyName)`, SwiftGen's `L10n`), and the languages it holds.

**Without filesystem access**, ask the user to paste the output of `xcodebuild -list`, the deployment target, the package list (`Package.resolved` or `Podfile`), one existing feature folder's file tree, one representative view with its view model, the navigation root, and a test file. Don't proceed without the package list.

## Detection report

```
Detected stack:
- UI: <SwiftUI, or SwiftUI + UIKit> (deployment target iOS <n>, Swift <n>, default isolation <MainActor or nonisolated>)
- State: <detected value, e.g. "TCA 1.26.2 (@Reducer, @ObservableState)", or "FALLBACK: @Observable view models">
- Navigation: <detected value, or "FALLBACK: NavigationStack + Route enum">
- HTTP client: <detected value, or "FALLBACK: URLSession async/await">
- Persistence: <SwiftData, Core Data, GRDB, … or "none">
- DI: <e.g. initializer injection, environment values, Factory>
- Codegen tools: <SwiftGen, Sourcery, Apollo, XcodeGen, Tuist, or "none">
- Other relevant packages: <Kingfisher, KeychainAccess, etc.>
- Test packages: <e.g. Swift Testing, XCTest in older tests, swift-snapshot-testing — or "FALLBACK: Swift Testing with hand-written fakes", or "no unit-test target: the user adds one before Phase 2">
- File registration: <synchronized folders | XcodeGen | Tuist | group-based project: <the user's choice>>
- Xcode command: `xcodebuild -project <App>.xcodeproj -scheme <scheme> -destination '<destination>'` (<reason, e.g. "one app scheme; iPhone 17 simulator chosen by the user">)

Detected conventions:
- Folder pattern: <e.g. Greeter/Features/<Name>/>
- Models: <e.g. Codable structs, snake_case keys through a shared JSONDecoder>
- API client: <e.g. protocol + URLSession implementation, throws APIError>
- View models: <e.g. @MainActor @Observable final class, dependencies through init>
- Views: <e.g. @State var viewModel, .task loading, shared LoadingView / ErrorView, ContentUnavailableView for empty>
- Navigation: <e.g. Route enum, navigationDestination(for: Route.self) in RootView>
- Design system: <e.g. Color.brand*, Font.app* extensions>
- Localization: <e.g. Localizable.xcstrings with en and zh-Hant, Text("key"), or generated symbols, Text(.keyName)>
- Access control: <e.g. internal types, private members>
- Tests: <e.g. GreeterTests/ mirrors Greeter/, Swift Testing, fakes in GreeterTests/Fakes — or "no tests yet">
- Exemplar: <the feature folder(s) read end to end>
```

`feature-workflow` Step 1.2 shows the `Detected stack` part; the scaffold's Step 1 adds `Detected conventions` in Phase 2.

## Code entry points

Where reading a feature's existing code starts, and the links to follow from there. `feature-workflow` reads this section to find a feature's code when no spec anchors lead to it, and to record a baseline spec. `<Source>` is the app target's folder ("Project layout").

- **Routes:** the navigation: the `Route` enum and the `navigationDestination(for:)` that maps its cases to views, a router or coordinator, the root `NavigationStack`, `NavigationSplitView` or `TabView`, and `NavigationLink(destination:)` inside a `NavigationView` below iOS 16; with TCA, a parent reducer's `Path` (`StackState`) and its `@Presents` destinations (`@PresentationState` before TCA 1.7). Find them with `grep -rlE 'navigationDestination|NavigationStack|NavigationSplitView|NavigationView|TabView|StackState|@Presents|@PresentationState' <Source>`.
- **Screens:** the view a destination shows, or a type the user names (`grep -rnE '(struct|class) <Name>\b' <Source>`), with the views from its own feature folder that it uses.
- **Links**, followed one level at a time from a view:
  1. its view model or store, the one it owns or receives (`@State`, `@StateObject`, `@ObservedObject`, `@Environment`, `@EnvironmentObject`, `@Bindable`), or with TCA its `StoreOf<…>` and that reducer;
  2. the repositories, services and dependency clients that one calls (its initializer's arguments, `@Dependency`), the models they return, and the persisted models they read or write (`@Model`, Core Data entities);
  3. a system service behind a protocol ("Native interop"), then its implementation.

  A chain ends at URLSession or another HTTP client, the store (`ModelContext`, `NSManagedObjectContext`), a system framework, a package's code or a generated file.
- **App-wide:** the `@main` `App` type (`grep -rl '@main' <Source>`) with the root view, environment values and model container it sets up, an `@UIApplicationDelegateAdaptor` app delegate (push registration, `UNUserNotificationCenterDelegate`), and `onOpenURL` or `onContinueUserActivity`. Read them when the feature is reached from outside the app or depends on how the app starts.
- **Tests:** the files of the unit-test target that use a type you read (`grep -rl '<Type>' <unit-test folder>`). `grep -nE '@(Test|Suite)\(' <file>` lists their descriptions; an XCTest method has no description to anchor.

## Commands

### The command rule — xcodebuild

Decides the `xcodebuild` command. It needs Xcode 16 or later (`xcodebuild -version`), for Swift Testing and the result reader below; with an older Xcode, say so and stop. No plugin option applies.

- **Container:** `-workspace <App>.xcworkspace` when the root has a workspace (CocoaPods makes one), else `-project <App>.xcodeproj`.
- **Scheme:** the shared scheme that builds the app target and tests its unit-test target, from `xcodebuild -list -json`. Ask when several qualify (one per environment, say); a scheme the project's docs name for development is the default.
- **Destination:** an iOS simulator from `xcrun simctl list devices available`, written `platform=iOS Simulator,name=<device>`, with `,OS=<version>` when several runtimes have that device. Ask which one, defaulting to the newest iPhone; with no simulator installed, say so and stop.

The rule's inputs are the container, the scheme and the simulator; `stack.md` keeps one `## Command` line per set of them, since simulators differ per machine. A saved line matches this machine when its container and scheme still exist (`xcodebuild -list -json`) and `xcrun simctl list devices available` lists its simulator under one runtime, or under the `OS=` it names; otherwise decide again. Use the command for every `xcodebuild` command — the checks and subagent prompts — even where the project's docs show another destination. Below, `<xcodebuild>` stands for `xcodebuild <container> -scheme <scheme> -destination '<destination>'`, and `<unit-test target>` for each unit-test target in the scheme's test action.

### Checks

| Check | Command | Runs when |
|---|---|---|
| Codegen | the project's generator for what changed: `swiftgen` after assets or strings changed, `sourcery` after annotated sources changed, Apollo's codegen after `.graphql` files changed, `xcodegen generate` or `tuist generate` after files were added to a generated project; none of them when a build phase already runs it | the project uses one and its inputs changed |
| l10n | `none` | never |
| Analyze | `<xcodebuild> -quiet build-for-testing`, then `swiftlint lint --quiet <files>` on the run's Swift files when the project has a `.swiftlint.yml` and no SwiftLint build phase | always |
| Format | `xcrun swift-format lint --strict <files>` with a `.swift-format` file, or `swiftformat --lint <files>` with a `.swiftformat` file, on the hand-written Swift files this run wrote or edited | the project configures one of them and Swift files were written or edited |
| Tests | `<xcodebuild> -quiet test -only-testing:<unit-test target>` | the scheme's test action has a unit-test target |
| Native build | `none` | never |

String Catalogs and `.strings` files compile in the build, so l10n has no command of its own; Analyze catches a broken catalog.

**Analyze's issues** are its `<path>:<line>:<col>: error:` and `<path>:<line>:<col>: warning:` lines; `-quiet` repeats each one in an excerpt below it, which doesn't count again. An incremental build prints a file's warnings only when it compiles that file again, so before the baseline's Analyze, `touch` the existing Swift files this run will edit. Every later Analyze then compiles each file of the run too, and the comparison with the baseline is per file, over the files this run created or edited. An error fails Analyze wherever it shows.

The Tests output names a failing test by `<suite>/<function>()`, not by its description; the anchored-test reader below maps one to the other.

**A test runner that doesn't start** is the simulator failing, not a test: the output stops with `Failed to install or launch the test runner`, or another error, before any test has a result. Shut the destination's simulator down (`xcrun simctl shutdown <udid>`, with the id `xcrun simctl list devices available` gives that device under its runtime), run the same command once more, and record both runs; when the second fails the same way, the check is a `FAIL` with that output. This holds for the Tests check, a layer's tests and the anchored tests.

**Native build** is `none`: this is a native app, and Analyze already builds everything a run touches. In a Flutter project, the Flutter adapter's Native build compiles the `ios/` folder, and this adapter adds only its standards, its agents and its test commands there ("Native interop").

### Other commands

- **A layer's tests**, as they are written: `<xcodebuild> -quiet test -only-testing:<unit-test target>/<suite>`, where the suite is the type that holds the file's `@Test` functions (`-only-testing:<unit-test target>/<function>()` for a free function).
- **Test-name search** (`feature-verify`, a baseline): `grep -F '"<description>"' <file>`, which also finds a raw string `#"…"#`. Only a Swift Testing `@Test("…")` string is a description; an XCTest method's name never is.
- **Anchored tests** (`feature-verify`): the console names tests only by function, so read the descriptions from the result bundle: `R="$(mktemp -d)/tests.xcresult"; <xcodebuild> -quiet test -only-testing:<unit-test target>/<suite> -resultBundlePath "$R"; xcrun xcresulttool get test-results tests --path "$R" | jq -r '[.. | objects | select(.nodeType == "Test Case")] | (.[] | "\(.result)  \(.name)"), "\(length) tests: \(map(select(.result == "Passed")) | length) passed, \(map(select(.result != "Passed")) | length) not passed"'`, with one `-only-testing:` per suite of the anchored files. Each test prints on its own line: its result (`Passed`, `Failed`, `Skipped`, `Expected Failure`), two spaces, then its description; the last line counts them. Without `jq` (macOS 14), drop the pipe and read each `Test Case` node's `name` and `result` in the JSON.
- **A local Swift package's tests** (a `Package.swift` above the test file; in a Flutter project usually `ios/<Kit>/`): `swift test --package-path <dir>` on the Mac, in place of the `xcodebuild` commands above for a layer's tests, the Tests check and the anchored tests, since a package has no app scheme; `--filter <suite>` narrows it. The output has a line per Swift Testing test with its `@Test` description in quotes and `passed` or `failed`, and a count at the end, so an anchored description is read from it without a result bundle. A package that needs iOS (it imports UIKit, say) can't run this way: its tests belong in the app's unit-test target.
- **A new golden image:** with swift-snapshot-testing, a test whose reference image is missing records it and fails that run (the default record mode, `missing`); run it again to see it pass. To re-record an existing image, pass `TEST_RUNNER_SNAPSHOT_TESTING_RECORD=all` before the layer's test command (version 1.17 or later; older versions set `isRecording = true` in the test for one run).
- **Device tests:** `<xcodebuild> test -only-testing:<UI-test target>`, run by hand; on a device, `-destination 'platform=iOS,id=<device id>'` with signing set up.

## Generation order

Concrete type and file names depend on the detected stack. After each layer, register its new files when the project needs it ("Project layout": File registration).

1. **Models** (`Codable` structs; DTOs and their mapping if the project separates them), then **persisted models** (SwiftData `@Model`, Core Data entities) with, for a change to a model that has shipped, its new schema version and migration stage
2. **API client / repository**: the protocol, its implementation (whichever HTTP client is detected), and the stub when the spec marks the API provisional, then the implementation's tests (a `URLProtocol` stub or a fake transport). With TCA, it is a dependency client with its `liveValue`, `testValue` and `previewValue`, registered where the project registers its others
3. **System services**, when section 4 has native interfaces ("Native interop"): a protocol per service and its implementation over the system framework, then the tests of the code that uses it, with the protocol faked
4. **View models / stores**, then their tests, which carry each screen's state and action scenarios (`standards.md`) — depends on detected state:
   - `@Observable` → a `@MainActor @Observable final class` per screen
   - `ObservableObject` → a `@MainActor final class` with `@Published` properties
   - TCA → the `@Reducer` with its `State`, `Action` and dependencies, scoped into its parent, tested with `TestStore`
5. **Shared views** (only if the feature introduces new reusable components)
6. **Screens** — for each screen, in this order:
   1. The view, with its view model (with TCA, its `StoreOf<Feature>`) and its navigation destination's parameters
   2. Loading started in `.task`, with the view model's state driving the body
   3. Loading state
   4. Error state with retry
   5. Empty state
   6. Success state UI
   7. User actions / navigation
   8. Snapshot tests of the screen's states, where the Test plan has them; a scenario the screen's work changed gets its view-model test updated here
7. **Navigation wiring** — the destination's `Route` case and `navigationDestination`, the router or coordinator, and `onOpenURL` handling for a deep link; with TCA, the parent's `Path` case (`StackState`) or `@Presents` destination and the view that shows it
8. **Platform declarations**, when section 4 lists permissions or capabilities: each row in its declaration ("Native interop")
9. **Modifications to existing screens** — clearly marked as edits, not rewrites — with the tests that cover the change

## Spec notation

How a SwiftUI spec fills the platform-dependent parts of the `feature-spec` template.

- **Section 2 routes:** the routes table's Path is the deep-link URL path a destination answers to, or `—` with none, and Params are the `Route` case's associated values. The routing wiring heading names the navigation, e.g. `### Routing wiring (NavigationStack)`, `### Routing wiring (Coordinator)` or `### Routing wiring (TCA)`, and gives each destination's `Route` case; with TCA, the parent feature and whether the destination is a `Path` case (a push) or a `@Presents` destination (a sheet or alert).
- **Section 3:** each affected view with its file, e.g. `` `SavedArticlesView` (`Greeter/Features/SavedArticles/SavedArticlesView.swift`) ``.
- **Section 4 entities:** a Swift sketch.

  ```swift
  // Sketch only — actual code generated in Phase 2
  struct SavedArticle: Codable, Identifiable {
      let id: String
      let articleId: String
      let savedAt: Date
  }
  ```
- **Section 4 persisted entities:** for each stored entity, its store (SwiftData `@Model`, Core Data, GRDB), its relationships with their delete rules, and, when a model that has shipped changes, the migration and what happens to the data already on users' devices.
- **Section 4 repository:** the HTTP client (URLSession, Alamofire, Moya — whatever the project uses), the decoder's settings and the error type it throws.
- **Section 4 native interfaces:** a native app calls the system frameworks itself, so each "interface" is a protocol around one framework service the feature needs. Choose in this order, and name the one chosen:
  1. a SwiftUI control that needs no permission and no wrapper (`PhotosPicker`, `ShareLink`), which means no native interface at all;
  2. a protocol around the system framework (AVFoundation, CoreLocation, Photos, UserNotifications, LocalAuthentication…), with its implementation in the app;
  3. a Swift package the project already has for it;
  4. with neither, propose a package; it is a new dependency, which the user approves in the spec.

  Give methods in Swift terms (`func requestAccess() async -> CameraAccess`), with the errors each throws.
- **Section 4 permissions:** iOS keys as the target declares them: the `Info.plist` key (`NSCameraUsageDescription`, `NFCReaderUsageDescription`), a `UIBackgroundModes` value, or an entitlement (`com.apple.developer.healthkit`).
- **Platform tags:** `ios`, the id of "Native interop". A SwiftUI app has one platform, so its scenarios need no tag.
- **Section 5:** the heading names the approach, e.g. `## 5. State management (@Observable)` or `## 5. State management (TCA)`, and the table follows it:

  **`@Observable` / `ObservableObject`:**

  | View model | Owned by | Depends on | Exposes | Actions |
  |---|---|---|---|---|
  | `SavedArticlesViewModel` | `SavedArticlesView` (`@State`) | `SavedArticlesRepository` | `state: .loading / .failed(message) / .empty / .loaded([SavedArticle])` | `load()`, `remove(id:)` |

  For each view model: who creates and owns it, its dependencies, what it exposes, the actions that change it, and when it reloads.

  **TCA:**

  | Reducer | State | Actions | Dependencies |
  |---|---|---|---|
  | `SavedArticlesFeature` | `articles`, `isLoading`, `alert` | `onAppear`, `removeTapped(id)`, `articlesResponse` | `savedArticlesClient` |
- **Specific, per stack:** name the actual view and the actual call, e.g. "Show `ErrorView` (existing) with a Retry button that calls `viewModel.load()`", for TCA "… that sends `.retryTapped`".
- **Section 7 localization:** where new strings go, e.g. keys in `Localizable.xcstrings`, with a value per language the catalog holds.
- **Section 10 implementation order:** the "Generation order" as steps, e.g. 1. Models (`Codable`); 2. Repository + stub, then its tests; 3. View models, then their tests, which cover each screen's states and actions; 4. New views — skeleton first, then states; 5. Navigation wiring; 6. Edits to affected existing screens, with the tests that cover the change; 7. Manual QA pass against Figma. A feature with native work adds System services after the repository, Platform declarations after navigation, and a pass on a device to the manual QA.
- **Section 10 test kinds**, one Test plan line each, before Manual: **Unit** (Swift Testing: the repository, and the view models or TCA reducers (`TestStore`), which carry each screen's state and action scenarios), **Snapshot** (this platform's golden tests, with swift-snapshot-testing), **UI** (XCUITest flows, run by hand).

## Standards

`standards.md` in this folder: the Swift and SwiftUI rules, on top of the common `../standards.md`. In a Flutter project's `ios/` folder only its rules for every Swift file apply, and the test rules it names for native unit tests ("Native interop").

## Templates

Templates are the fallback pattern source, used when the project has no exemplar for a file kind (the scaffold's "Pattern sources").

`templates/observable-urlsession/` applies when the confirmed stack is `@Observable` view models + `NavigationStack` + URLSession, or when the fallback is in effect, in both cases with a deployment target of iOS 17 or later:

- `Example.swift` — `Codable` model
- `ExampleRepository.swift` — repository protocol and its URLSession implementation
- `StubExampleRepository.swift` — stub repository for when the API isn't ready yet
- `ExampleListViewModel.swift` — `@MainActor @Observable` view model with a `State` enum
- `ExampleListView.swift` — view with `.task`, `.refreshable` in every state, and the four states in one `switch`
- `Route.swift` — `Route` case and `navigationDestination` wiring
- `ExampleListViewModelTests.swift` — Swift Testing tests named after requirement ids and scenario titles

Other stacks (`ObservableObject`, TCA, Alamofire, coordinators, etc.) and targets below iOS 17 have no template set.

## Native interop

What a SwiftUI feature needs from iOS itself, and what this adapter adds to another framework's iOS folder.

- **Platforms:** `ios`, the app's own target, in Swift.
- **Native adapter for:** `ios`. In a Flutter project, this adapter's "Standards" and "Agents" also apply to the Swift files a run writes in the `ios/` folder, and its "Commands" run the native unit tests there: its command rule, on the container and scheme the Flutter adapter's "Native interop" names, and its commands for a layer's tests, the Tests check, the test-name search and the anchored tests. Nothing else of it applies there, since the Flutter adapter's "Native interop" says where that code goes and its Native build compiles it.
- **Mechanism:** the one the spec names, ranked in "Spec notation": a system framework behind a protocol, with no bridge between languages.
- **Native code** goes where the project keeps its services (a `Services/` folder, or the feature's folder), mirroring the existing ones. The view model gets the protocol through its initializer, the way it gets its repository. Native code does only what section 4 states: a method whose behavior the spec doesn't give is a gap to ask about, never a stub.
- **Declarations**, one per section 4 permission or capability row:
  - an `Info.plist` key, with the spec's usage string, goes in the file the app target's `INFOPLIST_FILE` names, in each build configuration that names one. A target that generates its `Info.plist` (`GENERATE_INFOPLIST_FILE = YES` without `INFOPLIST_FILE`) takes a string key as an `INFOPLIST_KEY_<key>` build setting in each of its configurations, a project file edit; a key that can't be a build setting (an array such as `UIBackgroundModes`) goes to the user, to add in Xcode's Info tab. A localized `InfoPlist.xcstrings` may translate a usage string, but never replaces it. Each new usage key (`…UsageDescription`) also goes in `REQUIRED_USAGE_KEYS` of the project's `scripts/build-version.sh`, when it has one ("Build adapter").
  - an entitlement goes in the file each configuration's `CODE_SIGN_ENTITLEMENTS` names; with none, ask the user to add the capability in Xcode's Signing & Capabilities tab, which creates the file. Enabling the capability in the Apple Developer account is a manual check.
- **Testing:** host tests reach native work through its protocol, faked like a repository (the standards' "Tests"), a denial included. The framework itself and the system prompt are checked on a device: the closing notes list each native method and permission prompt to try by hand.

## Agents

| Role | Agent | Closing line |
|---|---|---|
| Reviewer | `swift-reviewer` | `Verdict: …` |
| Build fixer | `swift-build-resolver` | — |

## Build adapter

`mobile-build-deploy` builds the release archive with the project's `scripts/build-version.sh` and hands it to `mobile-store-deploy`. It applies to a native app only: in a Flutter project the Flutter adapter's build covers `ios/`.

- **Template:** `build-version.sh` in this folder.
- **Platforms:** `-i` builds the iOS archive. `-a` doesn't apply: the script exits 1 on it.
- **Version bookkeeping:** `MARKETING_VERSION` is the version and `CURRENT_PROJECT_VERSION` the build number; the ADAPT block's `VERSION_SOURCE` says where the script edits them:
  - `project`: the project file's lines that hold the app target's current values, in every target and configuration, so extensions that track the app move with it and targets with versions of their own stay (one that happens to hold the same value moves too);
  - the path to an `.xcconfig`: that file's `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION` lines. A project XcodeGen or Tuist generates keeps them in one, since its project file is rewritten on every generate;
  - `agvtool`: `agvtool new-marketing-version` and `agvtool new-version -all`, for an older project whose app target has an `Info.plist` file of its own with literal `CFBundleShortVersionString` and `CFBundleVersion` values (`VERSIONING_SYSTEM = apple-generic`, no generated `Info.plist`). The current values come from that file; agvtool sets every target's `Info.plist`.

  Read the current values from the script's dry run, which takes no `-i`. The script stops before any edit when the flavor's build configuration doesn't exist, before archiving when the app target doesn't read the new values back, and after archiving when the archived `Info.plist` doesn't carry them.
- **Command:** none to decide. The script runs the Xcode that `xcode-select -p` points at (`DEVELOPER_DIR` overrides it) and exits 1 before any edit when `xcodebuild` can't run. The header's `Xcode:` line shows the version in use; it has no expected value to check.
- **Setup:** the ADAPT block's app name (the `.xcarchive` filename), `XCODE_PROJECT` and `XCODE_WORKSPACE` (when the app builds from a workspace, as with CocoaPods), the flavors with the scheme and build configuration each one archives (one flavor when the app has none), `VERSION_SOURCE`, `REQUIRED_USAGE_KEYS`, and `XCODEBUILD_EXTRA_ARGS` (e.g. `-allowProvisioningUpdates` when automatic signing has to fetch profiles). Read them from `xcodebuild -list -json`, the schemes' archive actions and the project file: `grep -n -e MARKETING_VERSION -e CURRENT_PROJECT_VERSION -e baseConfigurationReference <App>.xcodeproj/project.pbxproj` shows where the version lives. The script writes `build/build-version-artifacts.env`, and a native project often doesn't ignore `build/`: when `git check-ignore -q build/` fails, offer to add `build/` to `.gitignore`.
- **Artifacts:** the bundle ID is the app target's `PRODUCT_BUNDLE_IDENTIFIER` in the flavor's configuration, which the script's header prints (`Bundle:`).

The script's `REQUIRED_USAGE_KEYS` holds the usage keys the archived `Info.plist` must contain, whether a key comes from the target's `Info.plist` file or from an `INFOPLIST_KEY_` build setting. The specs' section 4 `ios` permission rows feed it: Phase 2 adds each new key ("Native interop"), and `mobile-build-deploy` compares the list with the keys of the implemented specs' `ios` rows before each iOS build.
