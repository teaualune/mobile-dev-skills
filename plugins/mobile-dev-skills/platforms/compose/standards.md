# Standards — Jetpack Compose

Rules for the Kotlin, Compose and Android code the feature workflow writes, on top of the common `../standards.md`. In a Flutter project's `android/` folder, only the rules under "Every Kotlin file" apply, to the Kotlin files a run writes there, and **Form**, **Unescaped titles**, **Fakes**, **Persistence** and **Host tests** to its native unit tests (the Flutter adapter's "Native interop"), so their names are this platform's backtick form, which this adapter's test-name search finds. That project's other scenario tests follow its own adapter.

## Code

**Every Kotlin file**
- **No `!!`.** Use `?.`, `?:`, `requireNotNull` or `checkNotNull` with a message, or change the code so the type isn't nullable. Pigeon's generated Kotlin is never edited.
- **No swallowed errors.** A `catch` handles the error or rethrows it, and never catches `CancellationException` without rethrowing it: a `catch (e: Exception)` around a `suspend` call rethrows it first, and `runCatching` isn't used around one.
- **Structured coroutines.** No `GlobalScope`, and no `runBlocking` outside tests. Work starts in the scope that owns it (`viewModelScope`, `lifecycleScope`, or a scope passed in), and blocking work runs on an injected dispatcher (`withContext(ioDispatcher)`), so tests can replace it.
- **Main thread for Flutter channels.** In a Flutter project, a `MethodChannel` result (`result.success`, `result.error`) and an `EventChannel` sink are called on the main thread: after background work, return to it with `withContext(Dispatchers.Main)` or the main looper's `Handler`.
- **Newer APIs behind a version check, with a fallback.** An API above the module's `minSdk` runs behind `if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.<LEVEL>)` (or in a function marked `@RequiresApi` that is only called behind one), and the feature keeps working below it. Lint's `NewApi` catches a missing check, but not a missing fallback.

**Compose apps**
- **One state per screen.** A screen's ViewModel exposes its UI state as one `StateFlow`: a private `MutableStateFlow` behind `asStateFlow()`, changed with `update { }`. Its type has a case for each section 6 state, a sealed interface with Loading, Error, Empty and Success, unless the project models screen state another way. A `when` over it names every case, with no `else`.
- **Collect with the lifecycle.** A screen reads its state with `collectAsStateWithLifecycle()`, not `collectAsState()`, so collection stops while the app is in the background.
- **Stateful route, stateless screen.** `FooRoute` obtains the ViewModel the project's way (`hiltViewModel()`, `viewModel()`, `koinViewModel()`), collects its state, and maps the screen's callbacks to the ViewModel's actions. `FooScreen(uiState, onRetry, …)` takes plain state and lambdas, so previews and tests can set any state. Navigation is a lambda the route receives (`onArticleClick: (String) -> Unit`), never a `NavController` passed down.
- **`modifier: Modifier = Modifier`** is the first optional parameter of every composable that emits UI, applied to its root.
- **Pull to refresh in every state.** A screen whose data the user can reload wraps each state's content in one `PullToRefreshBox` (Material 3). The content is scrollable in every state, so Error and Empty refresh too: a `LazyColumn`, or a `Column` with `verticalScroll` that fills the box.
- **Lazy lists.** An unbounded list is a `LazyColumn` with `items(list, key = { it.id })`, never a `Column` with `forEach`.
- **Strings through resources.** User-visible text is `stringResource(R.string.…)` (`pluralStringResource` for counts), never a literal in a composable, with each new key in every `values-<locale>/strings.xml` the module has. A ViewModel exposes a resource id or a typed error rather than a resolved string.
- **Previews.** Each new screen has a `@Preview` per state, of the stateless screen inside the app's theme.
- **The stub delay** of a provisional repository is `delay(400)`.
- **DTOs.**
  - With kotlinx.serialization, a DTO is `@Serializable`, with `@SerialName` on each key that differs from its property, and the `Json` instance (`ignoreUnknownKeys = true`) is configured once, where the project builds its Retrofit.
  - With Gson, every field has `@SerializedName`, every constructor parameter has a default, and an optional field is nullable: Gson bypasses Kotlin's constructor and its null checks.
  - With Moshi, a DTO is `@JsonClass(generateAdapter = true)`.
  - DTOs stay out of the UI layer.
- **With Hilt**, a ViewModel is `@HiltViewModel` with an `@Inject constructor`, obtained with `hiltViewModel()`. A typed route's arguments come from its `SavedStateHandle` (`savedStateHandle.toRoute<FooDestination>()`). Bindings go in a `@Module @InstallIn(SingletonComponent::class)` beside the feature, or where the project keeps its others.
- **Shipped entities migrate.** A change to a Room entity in a database version that has shipped raises `@Database(version = …)` and adds a `Migration` or an `@AutoMigration`. Never `fallbackToDestructiveMigration()` for data the user would lose.

## Tests

- **Form.** JUnit 4. A scenario's test is a function with a backtick name, ``fun `saved-articles_1 Empty`()``: the description with each character a JVM name can't hold (`.` `;` `[` `]` `/` `<` `>` `:` `\` and a backtick) written as `_`, and each one Kotlin warns about in a name (`"` `?` `*` `|` `%`, which break on Windows) too, since that warning would fail Analyze. That is this platform's name form (the common **Name** rule), so the `test` anchor is `…/SavedArticlesScreenTest.kt#saved-articles_1 Empty`. In a project whose tests run on JUnit 5 or Kotest, the string form fits instead: `@DisplayName("saved-articles.1 Empty")`, or `test("saved-articles.1 Empty")`. For the fallback stack with nothing to mirror, start from `templates/viewmodel-navigation-retrofit/ExampleListScreenTest.kt`.
- **Unescaped titles.** The backtick form keeps the title's spaces and apostrophes as they are; only the characters above become `_`. A string form uses a raw string, `"""…"""`, when the title holds `"` or a backslash.
- **Screens.** A screen's state and action scenarios are Compose tests on the JVM, under `@RunWith(AndroidJUnit4::class)` with Robolectric and `createComposeRule()` (from `androidx.compose.ui.test.junit4.v2` from Compose UI 1.11, where the older one is deprecated):
  - each test sets the stateless screen with the scenario's state, inside the app's theme;
  - it finds nodes by text from the string resources or by `testTag`;
  - it asserts on what shows and on the lambdas the screen calls.

  A THEN about a request, saved data or an event goes in the ViewModel's test. Without Robolectric (a new dependency the user declined), the ViewModel's tests carry the screen's scenarios, as the common **Where** allows: a THEN about what shows is met by the screen's one `when` over that state, which the review reads.
- **ViewModels** run in `runTest` with a `MainDispatcherRule` that sets `Dispatchers.Main` to a test dispatcher, the repository faked. A test reads `uiState.value` after `advanceUntilIdle()`, or a sequence of states with Turbine (`uiState.test { awaitItem() }`).
- **Repositories** run through the real Retrofit and converter against MockWebServer (`mockwebserver3`), serving the JSON the spec gives; or a fake of the API interface, where the project's tests do that.
- **Fakes** are hand-written classes that implement the dependency's interface, unless the project uses a mocking library (MockK, Mockito-Kotlin). A fake records each call a THEN line names, and a provisional repository's fake implements the interface its stub implements.
- **Persistence.** A test that touches stored data uses an in-memory Room database (`Room.inMemoryDatabaseBuilder`, under Robolectric) or a fake DAO, and DataStore over a file in a `TemporaryFolder`; never the app's own storage.
- **Platform scenarios.** A Compose app has one platform, `android`, so a tag changes nothing about the test. A scenario that depends on the API level runs under Robolectric's `@Config(sdk = [<level>])`.
- **Host tests** are the module's `src/test/` tests, run on the JVM. Instrumented tests in `src/androidTest/` need a device or an emulator, and use plain camelCase names, since D8 rejects a method name with a space below `minSdk` 30.
