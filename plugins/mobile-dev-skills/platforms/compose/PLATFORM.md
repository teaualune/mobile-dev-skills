# Jetpack Compose adapter

Everything the feature workflow needs to know about native Android apps built with Jetpack Compose. The process skills (`feature-workflow`, `feature-spec`, `feature-scaffold`, `feature-verify`) read this file instead of carrying Android knowledge themselves. In a Flutter project it is also the native adapter for the `android/` folder ("Native interop").

## Applies when

A Gradle build (`settings.gradle.kts` or `settings.gradle`) with an Android app module (the `com.android.application` plugin, applied directly, through a version-catalog alias or through a convention plugin) that uses Jetpack Compose (`buildFeatures { compose = true }` or the `org.jetbrains.kotlin.plugin.compose` plugin, in that module or a module it depends on), in the working directory or a folder below it — but not the `android/` folder of a Flutter project (a `pubspec.yaml` beside that folder) or a React Native one (a `package.json` listing `react-native`), which that platform's adapter owns, nor a Kotlin Multiplatform project (a module applying `org.jetbrains.kotlin.multiplatform`), which no adapter covers yet. If several qualify, ask which one the feature is for.

## Project layout

- **Root:** the folder holding `settings.gradle.kts` (or `settings.gradle`) and the Gradle wrapper. `.mobile-dev-skills/` sits here, and the skills resolve their paths and run their commands here; in a monorepo, it is the app's folder, not the repository's root.
- **Manifest:** the version catalog `gradle/libs.versions.toml` when the project has one, and each module's `build.gradle.kts` (or `build.gradle`): its plugins, its `android {}` block (`namespace`, `minSdk`, `compileSdk`, build types, product flavors, `buildFeatures`) and its dependencies. `settings.gradle(.kts)` lists the modules (`include(":app")`); convention plugins in `build-logic/` or `buildSrc/` may apply plugins and dependencies for them. The `testImplementation` and `androidTestImplementation` dependencies are the test packages.
- **Source:** each module's `src/main/kotlin/` (or `src/main/java/`, which may hold Kotlin too), with its resources in `src/main/res/` and its `src/main/AndroidManifest.xml`. **Host tests:** the module's `src/test/` folder, run on the JVM by the verification run; Compose screen tests run there under Robolectric. `src/androidTest/` holds instrumented tests, which need a device or an emulator.
- **Screen tests on the JVM** need Robolectric (`org.robolectric:robolectric`), `androidx.compose.ui:ui-test-junit4` with `ui-test-manifest` as a `debugImplementation`, and `testOptions { unitTests { isIncludeAndroidResources = true } }` in the module. With a `targetSdk` (or `@Config(sdk = …)`) of 37 or later, they also need `androidx.test.espresso:espresso-core` 3.7.0 or later as a `testImplementation`: the Espresso 3.5 that `ui-test-junit4` brings fails there (`NoSuchMethodException: InputManager.getInstance()`). A module without them gets them before Phase 2 writes its first screen test, as a new dependency the user approves. If the user declines, the screen's scenarios are tested on its ViewModel (`standards.md`, "Screens").
- **Generated files**, never edited by hand and never anchored: everything under a module's `build/` (KSP and kapt output, Hilt's components, Room's `_Impl` classes, the `R` and `BuildConfig` classes, protobuf or OpenAPI output), `.gradle/`, and Room's exported schemas in `schemas/`, which the build writes.
- **Fingerprint** for `.mobile-dev-skills/stack.md`: the output of `cat settings.gradle* gradle/libs.versions.toml 2>/dev/null | cat - $(find . \( -name 'build.gradle*' -o -path './build-logic/*.kt' -o -path './buildSrc/*.kt' \) -not -path '*/build/*' -not -path './.gradle/*' | sort) | grep -v -e versionCode -e versionName | git hash-object --stdin`, run at the root. It covers the convention plugins in `build-logic/` and `buildSrc/`, and leaves out the lines that change with every release.
- **File registration:** none. Each source set compiles every file in its folders, so a new file needs no project edit.

## Stack layer

The version catalog and the modules' build files are the source of truth for the stack. Identify:

- **UI**: Jetpack Compose, through the Compose BOM (`androidx.compose:compose-bom`) or per-artifact versions, or Views and Fragments with Compose in parts (`ComposeView`, `AndroidView`); Material 3 (`androidx.compose.material3`), Material 2 (`androidx.compose.material`) or the project's own design system. The `minSdk`, the Kotlin version and the AGP version decide which version a new library can take. The Compose compiler is the `org.jetbrains.kotlin.plugin.compose` plugin from Kotlin 2.0; before that, `composeOptions { kotlinCompilerExtensionVersion }`.
- **State**: Jetpack `ViewModel` (`lifecycle-viewmodel-compose`). It exposes `StateFlow`, collected with `collectAsStateWithLifecycle()` (`lifecycle-runtime-compose`) or `collectAsState()`; Compose state (`mutableStateOf`); or `LiveData` (`observeAsState()`). Other state holders: an MVI library (Orbit, Mavericks), Circuit presenters, Molecule, Decompose components, or Voyager's `ScreenModel`.
- **Navigation**: Navigation Compose (`androidx.navigation:navigation-compose`; type-safe `@Serializable` routes from 2.8, string routes before), Navigation 3 (`androidx.navigation3`), Voyager (`cafe.adriel.voyager`), Compose Destinations, Decompose, Circuit or Appyx, or Fragments with the Navigation component around Compose screens.
- **HTTP**: Retrofit on OkHttp, Ktor client, Apollo Kotlin (GraphQL), Ktorfit, or OkHttp alone. **Serialization**: kotlinx.serialization, Gson, Moshi (with KSP codegen or reflection), Jackson.
- **DI**: Hilt, Koin, Dagger (with Anvil), Metro, kotlin-inject, or manual (constructor injection, an `AppContainer`). **Persistence**: Room (`androidx.room`, or `androidx.room3`), DataStore (Preferences or Proto), SQLDelight, Realm, `SharedPreferences`.
- **Async**: coroutines and Flow, RxJava, `LiveData`. **Codegen**: KSP (`com.google.devtools.ksp`) or kapt.
- **Other relevant**: Coil, Glide or Landscapist for images; Paging 3 (`paging-compose`); `kotlinx-collections-immutable`. For native work, the AndroidX libraries that already wrap a platform API: CameraX, `biometric`, `work-runtime`, Play services location.
- **Test packages**:
  - frameworks: JUnit 4 (`junit:junit`), JUnit 5 or 6 (`org.junit.jupiter`, with the `de.mannodermaus.android-junit5` plugin), Kotest;
  - doubles: MockK, Mockito-Kotlin;
  - coroutines: `kotlinx-coroutines-test`, Turbine;
  - screens: Robolectric, Compose UI test (`ui-test-junit4`, `ui-test-manifest`);
  - HTTP: OkHttp's MockWebServer (`mockwebserver3`, or `mockwebserver` before OkHttp 5);
  - assertions: Truth, AssertK, Kotest assertions;
  - screenshots: Roborazzi, Paparazzi;
  - other: `hilt-android-testing`, and Espresso or Kaspresso on devices.

**Fallback — only when detection fails.** Label every fallback choice in the report as the Detection report shows, e.g. `Navigation: FALLBACK: Navigation Compose (type-safe routes)`, and ask the user to confirm it. A fallback library the project doesn't have yet is a new dependency, which the user approves (the common standards). Add it at the newest stable version that the project's `minSdk`, `compileSdk`, Kotlin and AGP allow, through the version catalog when the project has one.

- UI → Compose through the Compose BOM, with Material 3
- State → a `@HiltViewModel` ViewModel per screen, exposing one `StateFlow` of a sealed `UiState`, collected with `collectAsStateWithLifecycle()`
- Navigation → Navigation Compose with type-safe `@Serializable` routes (2.8 or later)
- HTTP → Retrofit + OkHttp with `suspend` functions, behind a repository interface
- Serialization → kotlinx.serialization, through Retrofit's `converter-kotlinx-serialization`
- DI → Hilt, through KSP, with `hiltViewModel()` from `androidx.hilt:hilt-lifecycle-viewmodel-compose` (the copy in `hilt-navigation-compose` is deprecated). The Hilt Gradle plugin of Dagger 2.59 and later needs AGP 9, so an AGP 8 project takes Dagger 2.58
- Persistence, only when a feature stores data → Room 2 (KSP) for records, Preferences DataStore for settings
- Images → Coil 3 (`coil-compose` with `coil-network-okhttp`); paging, only for a list the spec pages → Paging 3
- Tests → JUnit 4 with hand-written fakes, `kotlinx-coroutines-test` and Turbine for ViewModels, Robolectric with `createComposeRule()` for screens, and `mockwebserver3` for repositories, when the project has no tests to mirror

**Mixed or ambiguous:**
- Several state or navigation approaches in the app (Navigation Compose beside Voyager in a migration, ViewModels beside Circuit presenters) → ask which one new features use. Don't pick.
- A Views app whose Compose is only a few screens hosted in Fragments → ask whether the new screens are Compose hosted the same way.
- A multi-module project (`:feature:*`, `:core:*`) → new code goes in the modules the feature's existing code uses; a new module is the user's decision.
- No DI library → Hilt is the fallback, but it also needs an `@HiltAndroidApp` application class and `@AndroidEntryPoint` on the activity; say so when asking. Constructor injection through the project's own factories is the alternative to offer.
- A library you don't recognize → say so, ask the user to confirm its role, and read one file that uses it before depending on it.

## Convention probes

Read in this order; each step informs the next.

1. **Project shape**:
   - the modules in `settings.gradle(.kts)`, and the convention plugins in `build-logic/` or `buildSrc/`;
   - for the app module and the feature's module: `namespace`, `minSdk`, `compileSdk`, build types and product flavors;
   - the AGP, Kotlin and Compose BOM versions;
   - whether the module has `src/test/`, its test dependencies, and the Robolectric setup ("Project layout");
   - the formatter and linters: ktlint (its Gradle plugin, or rules in `.editorconfig`), Spotless, ktfmt, detekt (`detekt.yml`), and Android Lint's `lint {}` block or `lint.xml` with any baseline file.
2. **The source layout**: package by feature (`com.example.app.feature.<name>`) or by layer (`ui/`, `data/`, `domain/`), and whether features have modules of their own.
3. **One or two existing features** of similar shape, read end to end. They are the exemplars Phase 2 generates from.
   - A model → data classes, `@Serializable` / `@SerializedName` / `@Json`, DTOs mapped to domain models or used directly
   - An API interface and repository → a Retrofit interface with `suspend` functions, or `Response<T>` / `Call<T>`; the repository interface and implementation; the error handling (exceptions, `Result`, a sealed result type); where the dispatchers come from
   - A ViewModel → how it is created (`@HiltViewModel`, Koin, a factory), how it exposes state (one `StateFlow<UiState>`, several flows, Compose state), a sealed or data-class UI state, one-off events (a `Channel`, a `SharedFlow`, state fields), and how it gets route arguments (`SavedStateHandle`, `toRoute<T>()`, assisted injection)
   - A persisted model, if there is one → Room `@Entity` and DAO, the `@Database` version and its migrations, DataStore keys
   - A screen → a stateful `FooRoute` beside a stateless `FooScreen`, or one composable; how it collects state; the loading, error and empty composables it uses; pull to refresh; `@Preview`s
   - The theme → the `MaterialTheme` setup, color scheme, typography, and spacing or design-system objects
   - A test file, if there is one → its folder and runner (`@RunWith(AndroidJUnit4::class)` with Robolectric, JUnit 5), how tests are named, fakes or mocks, a `MainDispatcherRule`, `createComposeRule()` or `createAndroidComposeRule()`, Hilt testing
4. **Navigation**: the `NavHost` and its destinations (`composable<Route>`, `composable("route")`), where the graph is built (one file, or a `NavGraphBuilder` extension per feature), how screens navigate (lambdas passed down, or a `NavController`), and deep links (`navDeepLink`, and the `<intent-filter>`s in `AndroidManifest.xml`).
5. **Resources**: `res/values/strings.xml` and its `values-<locale>/` folders, plurals, how strings are read (`stringResource`, `context.getString`), and per-app languages (`generateLocaleConfig`, `locales_config.xml`).
6. **DI wiring**: Hilt modules (`@Module @InstallIn`, `@Binds` or `@Provides`) or Koin modules, and where the Retrofit and OkHttp instances, the database and the dispatchers are provided.

**Without filesystem access**, ask the user to paste `settings.gradle(.kts)`, the version catalog (or the app module's `plugins {}` and `dependencies {}`), one existing feature's file tree, one representative screen with its ViewModel, the `NavHost`, and a test file. Don't proceed without the dependencies.

## Detection report

```
Detected stack:
- UI: <Compose (BOM <version>, Material 3), or Views + Compose> (minSdk <n>, compileSdk <n>, Kotlin <n>, AGP <n>)
- State: <detected value, e.g. "ViewModel + StateFlow<UiState>, collectAsStateWithLifecycle", or "FALLBACK: @HiltViewModel + StateFlow of a sealed UiState">
- Navigation: <detected value, or "FALLBACK: Navigation Compose (type-safe routes)">
- HTTP client: <detected value, or "FALLBACK: Retrofit + OkHttp">
- Serialization: <detected value, or "FALLBACK: kotlinx.serialization">
- DI: <detected value, or "FALLBACK: Hilt (KSP)">
- Persistence: <Room, DataStore, … or "none">
- Codegen: <KSP, kapt, or "none">
- Other relevant libraries: <Coil, Paging 3, etc.>
- Test packages: <e.g. JUnit 4, MockK, Turbine, Robolectric + ui-test-junit4 — or "FALLBACK: JUnit 4 with hand-written fakes", or "no Robolectric: the user adds it before Phase 2, or screen scenarios go on the ViewModel">
- Gradle command: `./gradlew`, module `<:app>`, variant `<debug>` (<reason, e.g. "one app module, no product flavors">)

Detected conventions:
- Modules: <e.g. single :app, or :app + :feature:* + :core:*>
- Folder pattern: <e.g. app/src/main/kotlin/com/example/app/feature/<name>/>
- Models: <e.g. @Serializable DTOs mapped to domain data classes in the repository>
- API client: <e.g. Retrofit interface + repository interface and Default implementation, throws>
- ViewModels: <e.g. @HiltViewModel, one StateFlow<FooUiState> sealed interface, load() in init>
- Screens: <e.g. FooRoute(viewModel) + stateless FooScreen(uiState, callbacks), shared LoadingIndicator / ErrorMessage, PullToRefreshBox>
- Navigation: <e.g. NavHost in AppNavHost.kt, a NavGraphBuilder.fooScreen() extension per feature>
- DI: <e.g. Hilt @Binds modules per feature, NetworkModule provides Retrofit>
- Theme: <e.g. AppTheme over MaterialTheme, Dimens object>
- Resources: <e.g. strings.xml with values-zh-rTW>
- Tests: <e.g. app/src/test/ mirrors the packages, Robolectric screen tests, fakes in test/…/fake/ — or "ExampleUnitTest only">
- Exemplar: <the feature package(s) read end to end>
```

`feature-workflow` Step 1.2 shows the `Detected stack` part; the scaffold's Step 1 adds `Detected conventions` in Phase 2.

## Code entry points

Where reading a feature's existing code starts, and the links to follow from there. `feature-workflow` reads this section to find a feature's code when no spec anchors lead to it, and to record a baseline spec. `<Source>` is the module's source folder ("Project layout").

- **Routes:** the navigation graph:
  - the `NavHost` and the destinations in it, found with `grep -rlE 'NavHost\(|composable<|composable\(|navigation<|navDeepLink' <Source>`;
  - the route types (`@Serializable` objects and classes) or route strings, and the `NavGraphBuilder` extensions features add;
  - the deep links: `navDeepLink` entries, and the `<intent-filter>`s of the activities in `AndroidManifest.xml`;
  - with Voyager, the `Screen` classes and the `Navigator` that starts them.
- **Screens:** the composable a destination shows, or one the user names (`grep -rnE 'fun <Name>(Route|Screen)?\(' <Source>`), with the composables from its feature package that it calls.
- **Links**, followed one level at a time from a screen:
  1. its state holder: the ViewModel it obtains (`hiltViewModel()`, `viewModel()`, `koinViewModel()`) or receives, or its presenter or `ScreenModel`;
  2. what that one calls (its constructor's parameters): repositories, use cases and data sources, the API interface, DAO or DataStore they use, and the models they return;
  3. a system service behind an interface ("Native interop"), then its implementation.

  A chain ends at Retrofit or another HTTP client, a Room DAO's generated implementation, an Android framework API, a library's code or a generated file.
- **App-wide:** read these when the feature is reached from outside the app or depends on how the app starts:
  - the `Application` class (`@HiltAndroidApp`);
  - the activity that calls `setContent` (`grep -rl 'setContent' <Source>`), with the theme and `NavHost` it sets up;
  - the DI modules that provide the HTTP client, the database and the dispatchers;
  - `AndroidManifest.xml`: its activities, intent filters and permissions.
- **Tests:** the files under the module's `src/test/` that use a class you read (`grep -rl '<Class>' <module>/src/test`). ``grep -nE '@Test|fun `' <file>`` lists their test functions. A test's description is its function's name: the backtick name (`` `saved-articles_1 Empty` ``), or a plain name in older tests.

## Commands

### The command rule — Gradle

Decides the Gradle command. No plugin option applies.

- **Wrapper:** `./gradlew` at the root, never a `gradle` on the PATH; without a `gradlew`, say so and stop. Before the first command, `./gradlew --version` must succeed, which needs a JDK. AGP 8 and 9 need JDK 17 or later, and Robolectric against SDK 36 or later needs 21. The Android SDK must be found too, through `sdk.dir` in `local.properties` or `ANDROID_HOME`. If either is missing, say which and stop. On a Mac with Android Studio, its bundled JDK (`/Applications/Android Studio.app/Contents/jbr/Contents/Home`) works as `JAVA_HOME`.
- **Module:** the app module, `:app` in a single-module project. In a multi-module project, the commands also run in each module whose code or tests a run touches, or whose tests a spec anchors; the probes find them, and you ask when they don't.
- **Variant:** the app module's build type `debug`, with the product flavor the project's docs use for development when it has flavors (`devDebug`), else ask. Another module takes the same variant when it has it, and otherwise the build type alone (a library module without flavors: `debug`).

The rule's inputs are the app module and its variant; `stack.md` keeps one `## Command` line per set of them. A saved line matches when `settings.gradle(.kts)` still includes its module and the module still has its variant; otherwise decide again. Below, `<module>` stands for a module's path (`:app`, `:feature:articles`), `<dir>` for its folder (`app`, `feature/articles`), `<Variant>` for its variant with a capital first letter (`Debug`, `DevDebug`) and `<variant>` for the variant as written (`debug`, `devDebug`). A command that names `<module>` repeats its tasks for each module it runs in, in one `./gradlew` call.

### Checks

| Check | Command | Runs when |
|---|---|---|
| Codegen | `none` | never |
| l10n | `none` | never |
| Analyze | `rm -f <dir>/build/reports/lint-results-<variant>.xml; ./gradlew --continue <module>:compile<Variant>Kotlin --rerun <module>:compile<Variant>UnitTestKotlin --rerun <module>:lint<Variant>`, then the project's detekt task when it configures detekt | always |
| Format | whichever the project configures, on the hand-written Kotlin files this run wrote or edited: `ktlint <files>` (the ktlint CLI, rules in `.editorconfig`), `ktfmt --dry-run --set-exit-if-changed <files>`, or the Gradle task that checks the project (`./gradlew ktlintCheck`, `./gradlew spotlessCheck`) | the project configures one and Kotlin files were written or edited |
| Tests | `./gradlew --continue <module>:test<Variant>UnitTest --rerun` | the module has a `src/test/` folder |
| Native build | `none` | never |

KSP, kapt and the other generators run inside the compile, so Codegen has no command of its own and Analyze catches their errors. Resources compile in the build too, so l10n has none either; lint's `MissingTranslation` reports a key missing from a locale.

**Analyze's issues** are the Kotlin compiler's `e:` and `w:` lines (`w: file:///<path>:<line>:<col> <message>`), and the `<issue>` entries of lint's XML report, `<dir>/build/reports/lint-results-<variant>.xml`, each with its `id`, its `severity` and a `<location file="…">`. Each attribute sits on a line of its own, and the root element is `<issues>`, which a search for `<issue` also finds. The Kotlin compile is incremental and prints a file's warnings only when it compiles that file again, which is why each compile task carries `--rerun`. `--continue` runs lint even when the test sources fail to compile. The command deletes the old report first, so a missing report means lint didn't run, and Analyze fails. The comparison with the baseline is per file, over the files this run created or edited. An `e:` line fails Analyze wherever it shows, and so does a lint issue of severity `Error` or `Fatal` in the run's files.

**Tests** run with `--rerun`, so a task Gradle thinks is up to date still runs. The console names each failing test as `<Class> > <name> FAILED`, with the class's simple name; the passing ones are only in the reports the anchored-test reader below reads.

**Native build** is `none`: this is a native app, and Analyze already compiles everything a run touches. In a Flutter project, the Flutter adapter's Native build compiles the `android/` folder, and this adapter adds only its standards, its agents and its test commands there ("Native interop").

### Other commands

- **A layer's tests**, as they are written: `./gradlew <module>:test<Variant>UnitTest --tests '<class>'`, where the class is the file's fully qualified test class (its `package` line and its class name).
- **Test-name search** (`feature-verify`, a baseline): ``grep -F -e '`<description>`' -e 'fun <description>(' -e '"<description>"' <file>``. A test's description is its function's name, in backticks or plain, or the string of a JUnit 5 `@DisplayName` or a Kotest test. Write a `'` in the description as `'\''`, since the backticks must stay inside single quotes.
- **Anchored tests** (`feature-verify`): the console doesn't list passing tests, so read the results from the JUnit XML reports: `rm -f <dir>/build/test-results/test<Variant>UnitTest/TEST-<class>.xml; ./gradlew --continue <module>:test<Variant>UnitTest --rerun --tests '<class>'; cat <dir>/build/test-results/test<Variant>UnitTest/TEST-<class>.xml | awk '/<testcase /{n=$0; sub(/^.*<testcase name="/,"",n); sub(/".*$/,"",n); gsub(/&quot;/,"\"",n); gsub(/&apos;/,"\047",n); gsub(/&lt;/,"<",n); gsub(/&gt;/,">",n); gsub(/&amp;/,"\\&",n); r="PASSED"; if ($0 ~ /\/>[[:space:]]*$/) {print r"  "n; t++; p++; n=""}} /<failure|<error/{r="FAILED"} /<skipped/{r="SKIPPED"} /<\/testcase>/{if (n!="") {print r"  "n; t++; if (r=="PASSED") p++; n=""}} END{print t+0" tests: "p+0" passed, "t-p" not passed"}'`. Give one `--tests` and one report file per class of the anchored files, each under its module's test task and folder. Each test prints on its own line: its result (`PASSED`, `FAILED`, `SKIPPED`), two spaces, then its description; the last line counts them. Each report is deleted before the run, because a test task that doesn't run (when its sources fail to compile, say) leaves the old one in place. A class whose report file is missing didn't run.
- **A new golden image:** with Roborazzi, `./gradlew <module>:recordRoborazzi<Variant> --tests '<class>'`; with Paparazzi, `./gradlew <module>:recordPaparazzi<Variant> --tests '<class>'`.
- **Device tests:** `./gradlew <module>:connected<Variant>AndroidTest`, run by hand with a device or an emulator attached.

## Generation order

Concrete type and file names depend on the detected stack. A new file needs no registration ("Project layout").

1. **Models**: domain data classes, and DTOs with their serialization annotations and their mapping to the domain model if the project separates them. Then **persisted models** (Room `@Entity` classes and their DAOs), with, for a change to an entity that has shipped, the database version bump and its migration
2. **API interface and repository**: the Retrofit (or Ktor) interface, the repository interface and its implementation, and the stub when the spec marks the API provisional, then the implementation's tests (MockWebServer, or a fake of the API interface)
3. **System services**, when section 4 has native interfaces ("Native interop"): an interface per service and its implementation over the Android API, then the tests of the code that uses it, with the interface faked
4. **ViewModels** with their `UiState`, then their tests (`runTest` with a `MainDispatcherRule`, Turbine for a sequence of states), which carry the scenarios about requests, saved data and events
5. **DI bindings**: the Hilt module (`@Binds` for the repository, `@Provides` for the API interface) or the Koin module, where the project keeps its others
6. **Shared composables** (only if the feature introduces new reusable components)
7. **Screens** — for each screen, in this order:
   1. The stateful `FooRoute`, which obtains the ViewModel and collects its state, and the stateless `FooScreen(uiState, …)` it calls
   2. Loading started where the project starts it (the ViewModel's `init`, or an event the route sends)
   3. Loading state
   4. Error state with retry
   5. Empty state
   6. Success state UI
   7. User actions / navigation callbacks
   8. A `@Preview` per state
   9. The screen's Compose tests on Robolectric, each setting the stateless screen with a state; without Robolectric, the ViewModel's tests carry these scenarios (`standards.md`)
8. **Navigation wiring** — the `@Serializable` route type (`FooDestination`, since `FooRoute` is the stateful composable), its `composable<FooDestination> { }` destination (in a `NavGraphBuilder` extension where the project uses them), the callbacks that navigate, and for a deep link its `navDeepLink` and the activity's `<intent-filter>`
9. **Platform declarations**, when section 4 lists permissions or capabilities: each row in its declaration ("Native interop")
10. **Modifications to existing screens** — clearly marked as edits, not rewrites — with the tests that cover the change

## Spec notation

How a Compose spec fills the platform-dependent parts of the `feature-spec` template.

- **Section 2 routes:** the routes table's Path is the deep-link URI pattern a destination answers to (`https://example.com/articles/{id}`), or `—` with none, and Params are the route type's properties. The routing wiring heading names the navigation, e.g. `### Routing wiring (Navigation Compose)` or `### Routing wiring (Voyager)`, and gives each destination's route type (`@Serializable data class ArticleDestination(val id: String)`) and the graph it joins.
- **Section 3:** each affected screen with its file, e.g. `` `SavedArticlesScreen` (`app/src/main/kotlin/com/example/app/savedarticles/SavedArticlesScreen.kt`) ``.
- **Section 4 entities:** a Kotlin sketch.

  ```kotlin
  // Sketch only — actual code generated in Phase 2
  @Serializable
  data class SavedArticleDto(
      val id: String,
      @SerialName("article_id") val articleId: String,
      @SerialName("saved_at") val savedAt: String,
  )
  ```
- **Section 4 persisted entities:** for each stored entity, its store (a Room table, DataStore keys), its relationships with their `onDelete` rules, and, when an entity that has shipped changes, the database version bump, its migration, and what happens to the data already on users' devices.
- **Section 4 repository:** the HTTP client (Retrofit, Ktor — whatever the project uses), the converter and its `Json` settings (`ignoreUnknownKeys`), the interceptors that apply (auth, logging), and the error type the repository throws or returns.
- **Section 4 native interfaces:** a native app calls the Android APIs itself, so each "interface" is a Kotlin interface around one service the feature needs. Choose in this order, and name the one chosen:
  1. an Activity Result contract that needs no permission and no wrapper (the photo picker's `PickVisualMedia`, a share `Intent`), which means no native interface at all;
  2. an interface around the AndroidX or framework API (CameraX, `BiometricPrompt`, fused location, `NotificationManagerCompat`, `WorkManager`…), with its implementation in the app;
  3. a library the project already has for it;
  4. with neither, propose a library; it is a new dependency, which the user approves in the spec.

  Give methods in Kotlin terms (`suspend fun requestAccess(): CameraAccess`), with the errors each throws.
- **Section 4 permissions:** Android declarations as the manifest holds them: a `<uses-permission>` name (`android.permission.CAMERA`, `android.permission.POST_NOTIFICATIONS`), with the API levels it applies to when it differs by level (notifications from 33, `READ_MEDIA_*` from 33, background location from 29), or a `<uses-feature>` with whether it is required. A runtime permission's "usage string" is the rationale the app itself shows, a string resource, since Android's dialog has no text of the app's.
- **Platform tags:** `android`, the id of "Native interop". A Compose app has one platform, so its scenarios need no tag.
- **Section 5:** the heading names the approach, e.g. `## 5. State management (ViewModel + StateFlow)`, and the table follows it:

  | ViewModel | Obtained by | Depends on | Exposes | Actions |
  |---|---|---|---|---|
  | `SavedArticlesViewModel` (`@HiltViewModel`) | `SavedArticlesRoute` (`hiltViewModel()`) | `SavedArticlesRepository` | `uiState: StateFlow<SavedArticlesUiState>` — `Loading / Error(message) / Empty / Success(articles)` | `load()`, `refresh()`, `remove(id)` |

  For each ViewModel: who obtains it and how long it lives (the destination's back-stack entry, by default), its dependencies and route arguments (`SavedStateHandle`), what it exposes, the actions that change it, and when it reloads.
- **Specific, per stack:** name the actual composable and the actual call, e.g. "Show `ErrorMessage` (existing) with a Retry button that calls `onRetry`, which `SavedArticlesRoute` maps to `viewModel.load()`".
- **Section 7 localization:** where new strings go: keys in `res/values/strings.xml`, with a translation in each `values-<locale>/strings.xml` the module holds, and counts as `<plurals>`.
- **Section 10 implementation order:** the "Generation order" as steps, e.g. 1. Models (`@Serializable`); 2. API interface, repository + stub, then its tests; 3. ViewModels, then their tests; 4. DI bindings; 5. New screens — route and stateless screen first, then states, previews and Compose tests; 6. Navigation wiring; 7. Edits to affected existing screens, with the tests that cover the change; 8. Manual QA pass against Figma. A feature with native work adds System services after the repository, Platform declarations after navigation, and a pass on a device to the manual QA.
- **Section 10 test kinds**, one Test plan line each, before Manual: **Unit** (JUnit on the JVM: the repository with MockWebServer or a fake API, and the ViewModels with `runTest`), **Compose UI** (Robolectric host tests of each screen's states and actions; without Robolectric, the ViewModel tests carry them), **Screenshot** (this platform's golden tests, with Roborazzi or Paparazzi where the project has one), **Instrumented** (`androidTest` on a device or an emulator, run by hand).

## Standards

`standards.md` in this folder: the Kotlin, Compose and Android rules, on top of the common `../standards.md`. In a Flutter project's `android/` folder only its rules for every Kotlin file apply, and the test rules it names for native unit tests ("Native interop").

## Templates

Templates are the fallback pattern source, used when the project has no exemplar for a file kind (the scaffold's "Pattern sources").

`templates/viewmodel-navigation-retrofit/` applies when the confirmed stack is a Hilt ViewModel with `StateFlow` + Navigation Compose with type-safe routes + Retrofit with kotlinx.serialization, or when the fallback is in effect:

- `Example.kt` — `@Serializable` DTO and the domain model it maps to
- `ExampleApi.kt` — Retrofit interface with `suspend` functions
- `ExampleRepository.kt` — repository interface and its Retrofit implementation
- `StubExampleRepository.kt` — stub repository for when the API isn't ready yet
- `ExampleModule.kt` — Hilt bindings for the API and the repository, and the app-wide Retrofit a project without one needs
- `ExampleListViewModel.kt` — `@HiltViewModel` with a sealed `UiState` in one `StateFlow`
- `ExampleListScreen.kt` — stateful route and stateless screen, the four states in one `when`, pull to refresh in every state, a preview per state
- `ExampleNavigation.kt` — `@Serializable` route and its `NavGraphBuilder` destination
- `MainDispatcherRule.kt` — the test rule that replaces `Dispatchers.Main`
- `ExampleListViewModelTest.kt` — JUnit 4 ViewModel tests named after requirement ids and scenario titles
- `ExampleListScreenTest.kt` — Robolectric Compose tests of the screen's states and actions, named the same way
- `ExampleRepositoryTest.kt` — repository tests against MockWebServer

Other stacks (Koin, Voyager, Ktor, Gson, Compose state in the ViewModel, Views, etc.) have no template set.

## Native interop

What a Compose feature needs from Android itself, and what this adapter adds to another framework's Android folder.

- **Platforms:** `android`, the app's own module, in Kotlin.
- **Native adapter for:** `android`. In a Flutter project, this adapter's "Standards" and "Agents" also apply to the Kotlin files a run writes in the `android/` folder, and its "Commands" run the native unit tests there: its command rule, on the Gradle root, module and variant the Flutter adapter's "Native interop" names, and its commands for a layer's tests, the Tests check, the test-name search and the anchored tests. Nothing else of it applies there, since the Flutter adapter's "Native interop" says where that code goes and its Native build compiles it.
- **Mechanism:** the one the spec names, ranked in "Spec notation": an Android API behind a Kotlin interface, with no bridge between languages.
- **Native code** goes where the project keeps its services (a `data/` or `platform/` package, or the feature's package), mirroring the existing ones, and is bound in DI the way the repositories are; the ViewModel gets the interface through its constructor. A runtime permission request needs an activity, so the composable launches it (`rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission())`) and passes the result to the ViewModel. Native code does only what section 4 states: a method whose behavior the spec doesn't give is a gap to ask about, never a stub.
- **Declarations**, one per section 4 permission or capability row:
  - a permission is a `<uses-permission>` in the app module's `src/main/AndroidManifest.xml`, with `android:maxSdkVersion` where the spec limits it, and a hardware need is a `<uses-feature>` with `android:required` as the spec says. A flavor or build type with a manifest of its own (`src/<flavor>/AndroidManifest.xml`) gets a row only when the spec says it differs there;
  - a runtime permission's rationale, when the row has one, is a string resource the screen shows;
  - a declaration Google Play reviews (background location, a foreground service type, `QUERY_ALL_PACKAGES`) also needs its Play Console form, which is a manual check.
- **Testing:** host tests reach native work through its interface, faked like a repository (the standards' "Tests"), a denial included. The Android API itself and the system's permission dialog are checked on a device: the closing notes list each native method and permission prompt to try by hand.

## Agents

| Role | Agent | Closing line |
|---|---|---|
| Reviewer | `kotlin-reviewer` | `Verdict: …` |
| Build fixer | `kotlin-build-resolver` | — |

## Build adapter

No build script yet: `mobile-build-deploy` can't build a native Android app, and offers `mobile-store-deploy` alone for a bundle built another way. In a Flutter project the Flutter adapter's build covers `android/`.

- **Template:** `none`.
- **Platforms:** none. No script takes `-i` or `-a`; the release bundle comes from `./gradlew <module>:bundle<Flavor>Release` or Android Studio's Generate Signed App Bundle, with the project's own signing.
- **Version bookkeeping:** `versionCode` and `versionName` in the app module's `defaultConfig` (or where the project keeps them: the version catalog, `gradle.properties`). The user raises them before building; `mobile-store-deploy` never changes them.
- **Command:** none to decide.
- **Setup:** none.
- **Artifacts:** the package name is the app module's `applicationId`, with the flavor's `applicationIdSuffix`; the bundle is under `<dir>/build/outputs/bundle/<variant>/`.
