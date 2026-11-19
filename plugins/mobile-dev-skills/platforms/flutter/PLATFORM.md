# Flutter adapter

Everything the feature workflow needs to know about Flutter. The process skills (`feature-workflow`, `feature-spec`, `feature-scaffold`, `feature-verify`) read this file instead of carrying Flutter knowledge themselves.

## Applies when

A `pubspec.yaml` whose `dependencies` include the Flutter SDK (`flutter:` with `sdk: flutter`), in the working directory or a folder below it. If several qualify (a workspace with several apps), ask which one the feature is for.

## Project layout

- **Root:** the folder holding that `pubspec.yaml`. `.mobile-dev-skills/` sits here, and the skills resolve their paths and run their commands here; in a monorepo, it is the app's folder, not the repository's root.
- **Manifest:** `pubspec.yaml`, the source of truth for the stack; its `dev_dependencies` list the test packages.
- **Source:** `lib/`. **Host tests:** `test/`, which the verification run executes, and the native unit tests of `ios/` and `android/` ("Native interop"). `integration_test/` holds tests that need a device.
- **Generated files**, never edited by hand and never anchored: `*.g.dart`, `*.freezed.dart`, `*.mapper.dart`, `*.gr.dart`, the generated l10n output, and Pigeon's output (the Dart, Swift and Kotlin files each input's `@ConfigurePigeon` names).
- **Fingerprint** for `.mobile-dev-skills/stack.md`: the output of `grep -v -e '^version:' -e '^# android:' pubspec.yaml | cat - .fvmrc 2>/dev/null | git hash-object --stdin`, run at the root. It leaves out the version lines a release bumps.

## Stack layer

`pubspec.yaml` is the source of truth for the stack. Identify:

- **State management**: `flutter_riverpod`, `riverpod_annotation`, `hooks_riverpod`, `flutter_bloc`, `bloc`, `provider`, `get`, `mobx`, `signals`, `stacked`, etc.
- **Routing**: `go_router`, `auto_route`, `beamer`, `routemaster`, or none (Navigator 1.0).
- **HTTP**: `dio`, `http`, `chopper`, `retrofit`.
- **Serialization / codegen**: `freezed`, `json_serializable`, `built_value`, `dart_mappable`, `riverpod_generator`, `auto_route_generator`, `build_runner`.
- **DI**: `get_it`, `injectable`, `kiwi`.
- **Other relevant**: `flutter_hooks`, `equatable`, `fpdart`/`dartz`; for native work, `pigeon` (dev), `permission_handler`, and plugins that already wrap a platform API (`camera`, `image_picker`, `geolocator`, etc.).
- **Test packages** (dev dependencies): `mocktail`, `mockito`, `bloc_test`, golden tooling (`golden_toolkit`, `alchemist`), `integration_test`, `patrol`. `flutter_test` is the base.

**Fallback — only when detection fails.** Label every fallback choice in the report as the Detection report shows, e.g. `State management: FALLBACK: Riverpod (riverpod_annotation)`, and ask the user to confirm it.

- State management → Riverpod (`flutter_riverpod` if no codegen detected, `riverpod_annotation` if `build_runner` is present)
- Routing → `go_router`
- HTTP → `dio`
- Serialization → `freezed` + `json_serializable` if codegen is present, manual otherwise
- Tests → `flutter_test` with hand-written fakes, when the project has no mocking library and no tests to mirror

**Mixed or ambiguous:**
- Multiple state libraries in `pubspec.yaml` (e.g. both `flutter_bloc` and `provider`) → ask which one is canonical for new features. Don't pick.
- Stack present but feature folders use a different one (legacy migration) → ask. Don't assume.
- An obscure package you don't recognize → say so, ask the user to confirm its role, and read one sample file before depending on it.

## Convention probes

Read in this order; each step informs the next.

1. **`lib/` folder structure**: the feature folder convention, e.g. `lib/features/<name>/{data,domain,presentation}/`, `lib/src/features/<name>/`, a flat `lib/<name>/`, or `lib/screens/`, `lib/models/`, `lib/blocs/`, `lib/providers/` split by type.
2. **One or two existing features** of similar shape, read end to end. They are the exemplars Phase 2 generates from.
   - An entity file → naming, freezed/manual/built_value, JSON mapping style
   - A repository file → HTTP client usage, error wrapping (throw / `Either` / `Result`), base URL handling
   - A state primitive file → for Riverpod: provider type and annotation style; for Bloc: event/state classes and Cubit vs Bloc; for Provider: ChangeNotifier patterns; etc.
   - A screen file → base widget type (`ConsumerWidget`, `BlocBuilder` + `StatelessWidget`, etc.), state-consumption pattern, error/loading/empty widgets used
   - Theme file → color/spacing/typography token names
   - A test file, if there is one → where tests sit relative to `lib/`, how a screen is pumped (a shared helper, provider or bloc overrides), fakes or mocks, golden setup
3. **Routing config**: the router file, how routes are declared (typed routes? plain `GoRoute`? `AutoRoute`? `MaterialPageRoute`?), where the route list lives, any guards or redirects.

**Without filesystem access**, ask the user to paste `pubspec.yaml` (or at least its `dependencies:` section), one existing feature folder's file tree, one representative screen file, the routing config file, the theme file (if there is one), and whether the project has `.fvmrc` and whether they run `fvm`. Don't proceed without `pubspec.yaml`.

## Detection report

```
Detected stack:
- State management: <detected value, or "FALLBACK: Riverpod (riverpod_annotation)">
- Routing: <detected value, or "FALLBACK: go_router">
- HTTP client: <detected value, or "FALLBACK: Dio">
- Serialization: <detected value, or "FALLBACK: freezed + json_serializable">
- Codegen tools: <build_runner targets in use, or "none">
- Other relevant packages: <get_it, flutter_hooks, etc.>
- Test packages: <e.g. flutter_test + mocktail, goldens with alchemist, integration_test — or "FALLBACK: flutter_test with hand-written fakes">
- Flutter/Dart command: <`fvm flutter` / `fvm dart`, or plain `flutter` / `dart`> (<policy + reason, e.g. "auto: .fvmrc + fvm installed">)

Detected conventions:
- Folder pattern: <e.g. lib/features/<name>/{data,domain,presentation}>
- Entities: <e.g. freezed + snake_case JSON keys>
- Repositories: <e.g. throw on error, no Result type; shared ApiClient wraps Dio>
- State primitives: <e.g. @riverpod functions + AsyncNotifier classes>
- Screens: <e.g. ConsumerWidget, AsyncValue.when() pattern with shared LoadingView/ErrorView/EmptyView>
- Routing: <e.g. typed routes via @TypedGoRoute, central router in lib/router/app_router.dart>
- Theme: <e.g. AppColors/AppSpacing/AppTextStyles classes>
- Imports: <package: vs relative>
- Tests: <e.g. test/ mirrors lib/, shared pump helper in test/helpers, fakes in test/fakes — or "no tests yet">
- Exemplar: <the feature folder(s) read end to end>
```

`feature-workflow` Step 1.2 shows the `Detected stack` part; the scaffold's Step 1 adds `Detected conventions` in Phase 2.

## Code entry points

Where reading a feature's existing code starts, and the links to follow from there. `feature-workflow` reads this section to find a feature's code when no spec anchors lead to it, and to record a baseline spec.

- **Routes:** the router configuration: `GoRouter(` or the `@TypedGoRoute` classes (go_router); the `@AutoRouterConfig` class, or `@MaterialAutoRouter` and its siblings before auto_route 6; `BeamerDelegate` and its `BeamLocation`s (beamer); `RouteMap` (routemaster); `MaterialApp`'s `routes` or `onGenerateRoute` (Navigator 1.0). Find it with `grep -rlE 'GoRouter\(|@TypedGoRoute|AutoRouter|BeamerDelegate|RouteMap\(|onGenerateRoute|routes:' lib/`. A route names its screen in its builder, or, with auto_route, as its `page`: the `@RoutePage()` widget whose generated route that is. A screen without a route is pushed directly (`grep -rn 'MaterialPageRoute' lib/`).
- **Screens:** the widget a route builds, or a class the user names (`grep -rnE 'class <Name>\b' lib/`), with the widgets from its own feature folder that it uses.
- **Links**, followed one level at a time from a screen:
  1. the state primitives it reads: providers (`ref.watch`, `ref.read`), blocs and cubits (`BlocBuilder`, `BlocProvider`, `context.read`), `ChangeNotifier`s (`Consumer`, `context.watch`), GetX controllers;
  2. the repositories and services those call, and the entities they return;
  3. a native interface they call (a Pigeon API, a channel wrapper), then its native side: the handler registered in `ios/Runner/AppDelegate.swift` and in `MainActivity` under `android/app/src/main/kotlin/` (`java/` in older projects).

  A chain ends at the HTTP client, the local database, a package's code or a generated file.
- **App-wide:** `lib/main.dart` (`runApp`, and DI setup such as `get_it` registrations), the router's `redirect` and guards, and the deep-link and push handlers (`app_links`, `FirebaseMessaging.onMessageOpenedApp`). Read them when the feature is reached from outside the app or sits behind a guard.
- **Tests:** the files under `test/` that import a file you read (`grep -rl '<file name>' test/`), usually at its mirrored path. `grep -nE -A1 "(test|testWidgets|blocTest|testGoldens|goldenTest|patrolTest|group)(<[^>]*>)?\(" <file>` lists their descriptions, with the next line for one that `dart format` wrapped.

## Commands

### The command rule — fvm

Decides the Flutter/Dart command. The policy is the plugin option `fvm_policy`; the skill that sends you here states its value.

- `never` → plain `flutter`/`dart`. `always` → `fvm flutter`/`fvm dart`; if `fvm` isn't installed, stop and say so.
- `auto` → decide from two facts: the project root has `.fvmrc` (a `.fvm/` directory alone doesn't count), and `fvm` is installed (`command -v fvm` succeeds):

  | `.fvmrc` | fvm installed | Command |
  |---|---|---|
  | yes | yes | `fvm flutter` / `fvm dart` |
  | yes | no | ask first, naming the mismatch ("`.fvmrc` present but `fvm` not installed"); default plain |
  | no | yes | ask first whether to use fvm ("`fvm` installed but no `.fvmrc`"); default plain |
  | no | no | plain `flutter` / `dart`, no question |

The rule's inputs are the policy, whether `.fvmrc` exists and whether `fvm` is installed; `stack.md` keeps one `## Command` line per set of them. Use the command for every Flutter/Dart command — the checks, subagent prompts, and generated comments that name a command (e.g. the `build_runner` line in `entity_freezed.dart`) — even where the project's docs show plain `flutter`/`dart`. Below, `<flutter>` and `<dart>` stand for it.

### Checks

| Check | Command | Runs when |
|---|---|---|
| Codegen | `<dart> run build_runner build --delete-conflicting-outputs` when the project uses `build_runner` and annotated files changed; `<dart> run pigeon --input <file>` for each Pigeon input that changed | either of those holds |
| l10n | `<flutter> gen-l10n` | ARB files changed |
| Analyze | `<flutter> analyze` | always |
| Format | `<dart> format --output=none --set-exit-if-changed <files>`, on the hand-written Dart files this run wrote or edited | Dart files were written or edited |
| Tests | `<flutter> test`, then each platform's native unit tests with its native adapter's Tests command ("Native interop") | the project has a `test/` folder; native unit tests, for each platform whose native unit tests the tasks write or the spec anchors |
| Native build | for `ios/`, `<flutter> build ios --simulator --debug`; for `android/`, `<flutter> build apk --debug` | this run wrote or edited files in that folder, or changed the manifest's dependencies; `ios/` only where `xcodebuild -version` succeeds |

ARB→Dart is Flutter's `gen-l10n` (configured in `l10n.yaml`), not a `build_runner` target.

**Native build** compiles the Swift and Kotlin code a run touches, which no other check sees. In a project with flavors (Android `productFlavors`, iOS schemes besides `Runner`), add `--flavor <name>`, the flavor its docs use for development, else ask. When the build's entry point isn't `lib/main.dart`, add it as `-t <file>`, from the run configurations or the build script's `BUILD_ARGS`. It passes only when every build it runs succeeds: there is no count to compare. The baseline runs it for each platform whose folder the run will write in, and a build that already fails there is shown to the user before any native file is written. A platform this machine can't build goes on the manual checks ("build for iOS on a Mac"); with neither platform left, the check is `SKIPPED`. Once it has passed, a fix reruns it only when the fix changed that platform's folder, the manifest or a Pigeon input.

**Native unit tests** ("Native interop") run in the Tests check after `<flutter> test`, and count like the host tests against the baseline, which runs them too. A platform whose native command rule stops on this machine (no Xcode for `ios`, no JDK or Android SDK for `android`) goes on the manual checks ("run the `ios` native unit tests on a Mac"), and `feature-verify` lists its anchored tests as not run; the other tests still decide the check.

### Other commands

- **A layer's tests**, as they are written: `<flutter> test <file>`. A native unit test runs with its native adapter's command ("Native interop").
- **Test-name search** (`feature-verify`, a baseline): `grep -F -e "'<description>'" -e '"<description>"' <file>`. A description is one whole string literal. An anchor under `ios/` or `android/` is a native unit test: search it with its native adapter's command.
- **Anchored tests** (`feature-verify`): `<flutter> test --reporter expanded --concurrency=1 <files>`, all the anchored files in one command: `--concurrency=1` keeps every test of every file in the expanded output, where files run in parallel can leave some out. Each test prints on its own line with its description and its result; a test run with a `variant` prints ` (variant: …)` after its description. Anchored native unit tests run with their native adapter's command ("Native interop").
- **A new golden image:** `<flutter> test --update-goldens --plain-name '<description>' <file>`.
- **Device tests:** `<flutter> test integration_test/<file>`, run by hand.

## Generation order

Concrete class and file names depend on the detected stack.

1. **Entities** (and `.g.dart` / `.freezed.dart` / `.mapper.dart` reminders if codegen)
2. **API client / repository** (uses whichever HTTP client is detected — Dio, http, chopper, retrofit), then its tests
3. **Native interfaces**, when section 4 has them ("Native interop"): the Dart interface (a Pigeon input, or a class wrapping the channel), Codegen, each platform's implementation and its registration, with its native unit tests when the Test plan has them, then the tests of the Dart side, with the native side faked
4. **State primitives**, then their tests — depends on detected state management:
   - Riverpod → providers (`Provider`, `FutureProvider`, `AsyncNotifier`, or `@riverpod` functions)
   - Bloc → events + states + the Bloc/Cubit class
   - Provider → ChangeNotifier subclass(es)
   - GetX → controllers
   - MobX → stores
5. **Shared widgets** (only if the feature introduces new reusable components)
6. **Screens** — for each screen, in this internal order (for complicated refreshable scroll views, use the skeleton in `standards.md`):
   1. Skeleton with route + Scaffold
   2. State consumption wired to the state primitive (`AsyncValue.when` for Riverpod, `BlocBuilder` for Bloc, `Consumer`/`Selector` for Provider package, `Obx` for GetX, etc.)
   3. Loading state
   4. Error state with retry
   5. Empty state
   6. Success state UI
   7. User actions / navigation
   8. The screen's widget tests
7. **Routing wiring** — add the new routes to whichever router is in use
8. **Platform declarations**, when section 4 lists permissions or capabilities: each row in its declaration file ("Native interop")
9. **Modifications to existing screens** — clearly marked as edits, not rewrites — with the tests that cover the change

## Spec notation

How a Flutter spec fills the platform-dependent parts of the `feature-spec` template.

- **Section 2 routing wiring:** the heading names the router, e.g. `### Routing wiring (go_router)` or `### Routing wiring (auto_route)`, and says whether routes are typed (`@TypedGoRoute`, `@RoutePage`) or plain.
- **Section 3:** each affected screen with its file, e.g. `` `ArticleDetailScreen` (`lib/features/articles/presentation/article_detail_screen.dart`) ``.
- **Section 4 entities:** a Dart sketch.

  ```dart
  // Sketch only — actual code generated in Phase 2
  class SavedArticle {
    final String id;
    final String articleId;
    final DateTime savedAt;
  }
  ```
- **Section 4 repository:** the HTTP client and interceptors it uses (Dio, http, retrofit, chopper — whatever the project uses).
- **Section 4 native interfaces:** choose the mechanism in this order, and name the one chosen:
  1. a package the project already has that covers the need, which means no native interface at all;
  2. Pigeon, when the project uses it (the `pigeon` dev dependency), as a `@HostApi` for calls into native code and a `@FlutterApi` for calls back;
  3. a `MethodChannel('<app id>/<feature>')`, or an `EventChannel` for a stream, written like the project's existing channels;
  4. with neither, propose Pigeon or a plugin package; either is a new dependency, which the user approves in the spec.

  Give argument and result types in Dart terms. Logic that must run without the Flutter engine (a background wake, an app extension, a home-screen widget) is native code: say where it runs, and whether it is tested natively ("Native interop").
- **Section 4 permissions:** keys as each platform declares them. iOS: the `Info.plist` key (`NSCameraUsageDescription`, `NFCReaderUsageDescription`), a `UIBackgroundModes` value, or an entitlement (`com.apple.developer.healthkit`). Android: the manifest permission (`android.permission.CAMERA`), with `maxSdkVersion` when it applies only up to an API level; runtime or install-time.
- **Platform tags:** `ios` and `android`, the ids of "Native interop".
- **Section 5:** the heading names the library, e.g. `## 5. State management (Riverpod)` or `## 5. State management (Bloc)`, and the table follows it:

  **Riverpod:**

  | Provider | Type | Watches | Exposes |
  |---|---|---|---|
  | `savedArticlesProvider` | `AsyncNotifierProvider` | `repo` | `AsyncValue<List<SavedArticle>>` |

  For each provider: type (Provider / FutureProvider / StreamProvider / NotifierProvider / AsyncNotifierProvider), dependencies, mutation methods (if Notifier), caching / invalidation behavior.

  **Bloc:**

  | Bloc/Cubit | Events | States | Notes |
  |---|---|---|---|
  | `SavedArticlesCubit` | `load`, `refresh`, `remove(id)` | `Initial`, `Loading`, `Loaded(items)`, `Error(msg)` | Depends on `SavedArticlesRepository` |

  For each Bloc/Cubit: events handled, states emitted, dependencies, side effects, when it's provided in the widget tree.

  **Provider package / ChangeNotifier:**

  | Notifier | Methods | Properties | Notes |
  |---|---|---|---|
  | `SavedArticlesModel` | `load()`, `remove(id)` | `items`, `isLoading`, `error` | Provided in `MaterialApp` scope |

  For another library, follow the same idea: name the state primitive, what it exposes, what it depends on, and its lifecycle / invalidation behavior.
- **Specific, per stack:** name the actual widget and the actual call, e.g. for Riverpod "Show `ErrorView` (existing) with retry button that re-invokes `savedArticlesProvider.future`", for Bloc "… that dispatches `SavedArticlesEvent.refresh()`".
- **Section 7 localization:** where new strings go, e.g. ARB keys.
- **Section 10 implementation order:** the "Generation order" as steps, e.g. 1. Entities + JSON mapping; 2. Repository + HTTP client wiring, then its tests; 3. State primitives (providers / blocs / notifiers), then their tests; 4. New screens — skeleton first, then states, then their widget tests; 5. Routing wiring (go_router / auto_route); 6. Edits to affected existing screens, with the tests that cover the change; 7. Manual QA pass against Figma. A feature with native work adds Native interfaces after the repository, Platform declarations after routing, and a pass on a device to the manual QA.
- **Section 10 test kinds**, one Test plan line each, before Manual: **Unit** (repository and state primitives), **Widget** (`testWidgets`: each screen's states and actions), **Golden** (golden-file tests), **Integration** (flows on a device, under `integration_test/`), and **Native unit** only when section 4 places logic in native code that is tested natively ("Native interop"): Swift Testing in the `ios` unit-test target, run with `xcodebuild test`, and JUnit under `android/app/src/test/`, run with `./gradlew :app:test<Variant>UnitTest`.

## Standards

`standards.md` in this folder: the Flutter rules, on top of the common `../standards.md`.

## Templates

Templates are the fallback pattern source, used when the project has no exemplar for a file kind (the scaffold's "Pattern sources").

`templates/riverpod-gorouter-dio/` applies when the confirmed stack is Riverpod + go_router + Dio, with or without codegen, or when the fallback is in effect:

- `entity_freezed.dart` — entity with freezed + json_serializable
- `entity_manual.dart` — entity without codegen
- `repository.dart` — Dio-using repository
- `repository_stub.dart` — stub repository for when the API isn't ready yet
- `provider_codegen.dart` — Riverpod with annotation
- `provider_manual.dart` — Riverpod without annotation
- `screen_async.dart` — ConsumerWidget with AsyncValue.when
- `router_route.dart` — go_router route entry
- `screen_test.dart` — widget tests named after requirement ids and scenario titles

Other stacks (Bloc, Provider, GetX, MobX, auto_route, chopper, etc.) have no template set.

## Native interop

What a Flutter feature needs when it reaches into the iOS or Android projects.

- **Platforms:** `ios` (`ios/`, Swift, or Objective-C in older projects) and `android` (`android/`, Kotlin, or Java in older projects). Other platform folders (`macos/`, `web/`, `windows/`, `linux/`) aren't covered: ask before writing native code there.
- **Native adapter for:** `none`. Flutter isn't a native platform; a native adapter for `ios` or `android` adds its standards and agents to that platform's files, and its test commands to the native unit tests there (Testing).
- **Mechanism:** the one the spec names, ranked in "Spec notation". Pigeon inputs go where the project's existing ones sit, else `pigeons/`.
- **Native code** goes beside the project's existing native files, mirroring them and its existing channels:
  - `ios`: in `ios/Runner/`, registered where `AppDelegate.swift` registers plugins. With the UIScene lifecycle (Flutter ≥ 3.41; the delegate adopts `FlutterImplicitEngineDelegate`), that is `didInitializeImplicitFlutterEngine(_:)`, with `engineBridge.applicationRegistrar.messenger()`, which the engine's header names for app-level channels (`engineBridge.pluginRegistry.registrar(forPlugin:)` where a Flutter version lacks it); in an older `AppDelegate`, `application(_:didFinishLaunchingWithOptions:)`. Never through `window?.rootViewController`, which UIScene leaves nil.
  - `android`: beside `MainActivity` under `android/app/src/main/kotlin/` (`java/` in older projects), registered in `configureFlutterEngine`.
  - Native code does only what section 4 states: a method whose behavior the spec doesn't give is a gap to ask about, never a stub.
- **Declarations**, one per section 4 permission or capability row:
  - `ios`: an `Info.plist` key goes in each `Info.plist` the target's build configurations name in `INFOPLIST_FILE` (usually only `ios/Runner/Info.plist`), with the spec's usage string. A localized `InfoPlist.xcstrings` or `.strings` may translate it, but never replaces it, since App Store validation reads `Info.plist`. Each new usage key (`…UsageDescription`) also goes in `REQUIRED_USAGE_KEYS` of the project's `scripts/build-version.sh`, when it has one ("Build adapter"). An entitlement goes in the file each configuration's `CODE_SIGN_ENTITLEMENTS` names; with none, ask before adding one to the Xcode project. Enabling the capability in the Apple Developer account is a manual check.
  - `android`: `<uses-permission>` (or `<uses-feature>`) in `android/app/src/main/AndroidManifest.xml`, with `android:maxSdkVersion` where the spec gives one.
  - With `permission_handler`, each iOS permission also needs the setup its README lists (with CocoaPods, a `PERMISSION_…=1` macro in the `ios/Podfile` `post_install` block); without it the request returns denied without a prompt.
- **Testing:** host tests reach native work through the Dart interface, faked like a repository (the standards' "Tests"). Native logic that section 4 places in native code because it must run without the Flutter engine, or that the spec says is tested natively, also gets native unit tests in its platform's unit-test target. They follow the native adapter's standards, and run through its "Commands" (its command rule, a layer's tests, the Tests check, the test-name search, the anchored tests) with this project's container:
  - `ios`: `ios/Runner.xcworkspace`, the scheme Native build builds (`Runner`, or the flavor's), and the unit-test target in that scheme's test action: Flutter's template creates `RunnerTests` from Flutter 3.10, and a project may have another, or none (the SwiftUI standards' **Host tests**). Before the first `xcodebuild` in a checkout, run `<flutter> build ios --config-only --simulator --debug`, with Native build's `--flavor` and `-t`: it writes `ios/Flutter/Generated.xcconfig` and, with CocoaPods, runs `pod install`, which a build of Runner needs. A new test file joins the target as the SwiftUI adapter's File registration says; Flutter's template project is group-based.
  - `android`: `android/app/src/test/kotlin/`, with `android/` as the Gradle root, module `:app` and the variant `debug`, or `<flavor>Debug` with Native build's flavor. `gradlew` and `local.properties` are gitignored there; `<flutter> build apk --config-only` writes them. Flutter's template moves the module's build folder to `build/app/` at the project root (in `android/build.gradle` or `build.gradle.kts`), so the reports the Compose adapter reads under `<dir>/build/` are there. The template has no test dependencies: JUnit 4 (`junit:junit`) as a `testImplementation` is a new dependency the user approves.

  The native code is also checked by the native build ("Commands"), and on a device: the closing notes list each native method and permission prompt to try by hand.

## Agents

| Role | Agent | Closing line |
|---|---|---|
| Reviewer | `flutter-reviewer` | `Verdict: …` |
| Build fixer | `dart-build-resolver` | — |

## Build adapter

`mobile-build-deploy` builds release artifacts with the project's `scripts/build-version.sh` and hands them to `mobile-store-deploy`.

- **Template:** `build-version.sh` in this folder.
- **Platforms:** `-i` builds the iOS archive, `-a` the Android AAB.
- **Version bookkeeping:** `pubspec.yaml` holds `version: <name>+<iosBuild>` and a `# android: <androidBuild> = <name> (<iosBuild>)` comment line that tracks the Android versionCode; the script rewrites both. Read the current values there. Before the first run, add the comment line if it's missing, with the current versionCode the user confirms.
- **Command:** the fvm rule ("Commands"), decided once before the first script run, unless the ADAPT block sets `FLUTTER_CMD` to a literal value: that pins the project's command, used as is. Otherwise pass the decision on every run, dry runs included: `FLUTTER_CMD="<cmd>" ./scripts/build-version.sh …`. The script keeps its own copy of the rule, because it can't ask questions: without `FLUTTER_CMD` it runs `fvm flutter` when the root has `.fvmrc` and fvm is installed, exits 1 before touching `pubspec.yaml` when `.fvmrc` is there without fvm, and runs `flutter` otherwise. Whatever the command, it exits 1 before touching `pubspec.yaml` when that command isn't installed. The header's `Flutter:` line shows the command in use.
- **Setup:** the ADAPT block's app name (the `.xcarchive` filename), `FLUTTER_CMD` (keep the default line, which takes the environment and otherwise follows the rule; a literal value pins one command for the project), the flavors with each one's `BUILD_ARGS`, scheme and configuration naming when it isn't `scheme == flavor` / `Release-<flavor>` (`Runner` / `Release` without flavors), the fallback iOS deployment target, and `REQUIRED_USAGE_KEYS`. Read them from `pubspec.yaml`, `ios/Runner.xcodeproj` and its schemes, and `android/app/build.gradle` (or `build.gradle.kts`).
  - **Flavors** are the Android `productFlavors` and the iOS schemes besides `Runner`. One `--flavor` goes to both builds, so the names must match; with several flavor dimensions it is the combined name (`stagingPlay` for `staging` × `play`). An app with neither leaves `FLAVORS` empty: the script then builds without `--flavor` and rejects one. Flavors on one platform only (e.g. Android `productFlavors` without iOS schemes) aren't covered: say so, and don't build.
  - **`BUILD_ARGS`** holds what a flavor's release build needs besides `--flavor`: its entry point when that isn't `lib/main.dart` (e.g. `-t lib/main_production.dart`), and the defines it passes (`--dart-define`, `--dart-define-from-file`). Take them from the project's run configurations (`.vscode/launch.json`, `.idea/runConfigurations/`), its docs or its CI, and ask when they disagree or say nothing. Without them the script builds `lib/main.dart` with no defines, which can ship the wrong configuration without any error. Both platforms' builds get every flag, and the header prints them, so a secret goes in a define file, never in a `--dart-define`.
- **Older scripts:** a script copied from v0.2.0 has an empty `FLUTTER_CMD=""` line in its ADAPT block. It ignores `FLUTTER_CMD` from the environment, picks `fvm flutter` when the root has `.fvmrc` **or** a `.fvm/` directory and `flutter` otherwise, and prints no `Flutter:` line. Offer to update its `FLUTTER_CMD` line and fvm block from the template. If the user declines, run it as is only when its pick equals the decided command, and skip the header line check; when they differ, stop and explain, since it would bump `pubspec.yaml` and build with the wrong command. Never edit a script the user declined to update.
  A script copied from v0.2.0 or a pre-release build has no `BUILD_ARGS` line. It always passes `--flavor`, builds `lib/main.dart` with no defines and expects `app-<flavor>-release.aab`, so it fails on an app without flavors or with several flavor dimensions, and builds the wrong entry point for one whose flavors have their own (`lib/main_<flavor>.dart`) or define files. For such a project, offer to update it from the template, carrying its ADAPT values over. If the user declines, stop, since a build would fail or ship the wrong configuration, unless the script was already changed to build this app (e.g. its `--flavor` removed for an app without flavors). Otherwise it runs as is.
- **Artifacts:** the iOS bundle ID carries the flavor's suffix, if the project uses one. The Android package name is `applicationId` in `android/app/build.gradle` (or `build.gradle.kts`), plus the flavor's `applicationIdSuffix`.
- **Known issues:** in a Swift Package Manager project, the iOS config sync can die with `Could not resolve package dependencies: … Package.swift was modified during the build`. Remove `ios/Flutter/ephemeral` (generated, gitignored) and run the same command again.

The script's `REQUIRED_USAGE_KEYS` holds the iOS usage keys the archived `Info.plist` must contain. The specs' section 4 `ios` permission rows feed it: Phase 2 adds each new key ("Native interop"), and `mobile-build-deploy` compares the list with the keys of the implemented specs' `ios` rows before each iOS build.
