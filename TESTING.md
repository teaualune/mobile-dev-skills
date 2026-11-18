# Testing

The end-to-end cases of the `mobile-dev-skills` plugin: what a live session has to show for each part of the skills to count as working, and what has shown it so far. Trigger tests (which skill a request fires) are a separate layer, in [`maintenance/evals/`](maintenance/evals/README.md); `python3 -I .claude/skills/maintainer/scripts/check_contracts.py` checks the files' contracts, not their behavior.

The plugin is in **alpha** until "Leaving alpha" below holds. Real projects are its end-to-end tests: the owner uses it in their own apps, and a session that covers a case adds its evidence here. The cases real use rarely reaches are marked `synthetic` and are run on purpose, in fixtures, before the plugin leaves alpha ("Leaving alpha").

## Reading the tables

- **Kind**: `use` for a case that real use in an app reaches, even when the app needs a particular stack or setup (codegen, flavors, several modules); `synthetic` for one that needs a staged failure, a missing or old tool, or a request or project shape real use rarely brings, so it is run on purpose in a fixture.
- **Status**: `open` (never run), `partly` (a run covered part of it), `owner` (needs the owner's account, app or machine), `passed`, `failed` (the last run broke it), or `fixed` (a change answers what a run found, and no run has checked it since). After `partly`, `passed` or `failed` the cell holds the evidence: the date, the plugin version, where it ran (a fixture below, or "a real Flutter app", "a real SwiftUI app", "a real Compose app", never the app's name), and the cost when known. A `fixed` cell holds the date, the version that has the change and what it changed, then the earlier status and its evidence, if there was any. Versions `0.3.x` were pre-release builds on the development branch, before the version restarted at `0.1.0-alpha.1`. A `failed` cell also says what broke; once fixed, it becomes `fixed`, and the next run that passes replaces it.
- **A new problem** found in real use that no case covers becomes a new row in its group: the next free id, the case and what passing looks like, Kind, and `open`.

## How to run

- **Nested sessions.** From a fixture copy outside the repo:

  ```bash
  env -u CLAUDE_CODE_PLUGIN_DIRS claude -p --model claude-sonnet-5-5 \
    --plugin-dir <repo>/plugins/mobile-dev-skills \
    --permission-mode acceptEdits --allowedTools "Bash" "Read" "Write" "Edit" "Glob" "Grep" "Skill" "Agent" \
    --output-format stream-json --verbose "<prompt>" > <case>.jsonl
  ```

  Continue a conversation with `--resume <session id>` (the id is in the log's `result` line). `Read` must be in the allowlist, since the adapters sit outside the fixture. A narrow Bash allowlist makes `-p` hang on the first compound command; `bypassPermissions` is refused in auto mode.
- **Judge from the tool calls, not the reply.** Models have reported checks done that never ran. A case passes only on the log's tool calls and the files it left.
- **One assertion on every Phase 1 run:** no Write or Edit to the project's source or test folders before the user's approval message. A run that fails it is recorded as a new case: a hook-enforced gate waits for that evidence.
- **Never edit the plugin's files while a nested run reads them.** A run has followed a mid-run change before.
- **Fixtures are git repos.** Work on a `git clone` of one, commit the state a case starts from, and judge by `git status` and `git diff` afterwards.
- **Plugin CLI cases** run with `HOME=<scratch>/home` (`CLAUDE_CONFIG_DIR` doesn't isolate installs), against a git marketplace served over local smart HTTP (a WSGI wrapper around `git http-backend`; `marketplace add` refuses `file://` and dumb HTTP), or against GitHub for a published version.
- **Deploy cases** run with a PATH shim in front that refuses `xcodebuild -exportArchive`, unless the case is a real upload the owner runs. A SwiftUI fixture archives unsigned with `XCODEBUILD_EXTRA_ARGS=(CODE_SIGNING_ALLOWED=NO)` in its build script's ADAPT block. Never pass `-allowProvisioningUpdates` without the owner. Afterwards delete the run's archives under `~/Library/Developer/Xcode/Archives/<date>/` and the fixture's DerivedData folder (find it by its `info.plist` `WorkspacePath`).
- **Plugin options** under `--plugin-dir`: the plugin's ID is `mobile-dev-skills@inline`, so pass `--settings <file>` with `{"pluginConfigs":{"mobile-dev-skills@inline":{"options":{…}}}}`.
- **Copies from the plugin cache** (`cp` of a template) ask for permission, since the cache sits under `~/.claude/`; a model then falls back to Read and Write, which is fine.
- **Cost.** Record each run's `total_cost_usd`. A Phase 1 conversation costs about $0.5–1.5, a full Phase 2 run with review $3–9.

## Fixtures

Fixtures are throwaway projects, rebuilt when needed. A Flutter one is made with `fvm spawn <version> create …` and an `.fvmrc` when the system Flutter can't build for the installed Xcode's simulator.

| Fixture | What it is | How to make one |
|---|---|---|
| Articles app | Flutter (Riverpod, go_router, Dio): an articles feature with a spec, its index row and tests, and a settings feature without a spec; no `ios/` or `android/` | `flutter create`, two features by hand, the articles spec written by the plugin; for an unspecced feature, remove its spec and index row |
| v0.2.0 project | The articles app with a v0.2.0 bullet spec and an old `-changelog.md`, no index and no state folder | The articles app with its spec rewritten in v0.2.0's format |
| Camera app | Flutter with `.fvmrc`, `ios/` and `android/`, a camera spec whose section 4 has permissions and a native interface | `fvm spawn <version> create`, a camera Intake Sheet run through Phase 1 |
| Greeter | SwiftUI, an Xcode 16-format project with synchronized folders and a shared scheme, an `@Observable` greeting screen, a Swift Testing test, a spec and its index | A hand-written or Xcode-created project |
| Compose Greeter | Compose (Navigation Compose, `viewModel()`, Robolectric), a greeting spec and its index; and a project with the adapter's whole fallback stack, for the templates | Android Studio's empty Compose template plus the libraries |
| Monorepo | The articles app in `app/` beside `backend/` and `web/` parts with their own manifests and specs, a root `FEATURES.md`, and the plugin README's sample parent skill | `maintenance/evals/_fixture/monorepo.sh` makes a smaller one |
| Eval fixtures | `maintenance/evals/_fixture/flutter-app.sh`, `compose-app.sh`, `monorepo.sh`, `monorepo-noparent.sh` | Run the script in an empty folder |

Still to build for open cases: a Flutter app with codegen (freezed, `riverpod_generator`), ARB files and goldens; a Flutter app with flavors and `permission_handler` or Pigeon; a SwiftUI app with TCA and SwiftData; a group-based or XcodeGen SwiftUI project; a SwiftUI project with SwiftLint or swift-format and snapshot tests; a CocoaPods workspace Flutter app; a monorepo with two apps, one of them SwiftUI.

## Leaving alpha

The plugin leaves alpha when every `synthetic` case has passed, A1, A2 and K1 (the owner's real Flutter, SwiftUI and Compose apps) have passed, and no case is `failed`. That is the minimum: the owner may require more `use` cases then, never fewer.

## Cases

### A. Real projects

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| A1 | A new feature and an edit to it, start to finish, in one of the owner's real Flutter apps | Every step's evidence present: size line, detection report, intake sheet, spec and quality check, approval, `tasks.md` baseline, verification report, review, index `implemented`; the app builds | use | owner |
| A2 | The same in one of the owner's real SwiftUI apps | As A1, with the SwiftUI adapter's commands; where the app uses TCA or SwiftData, the standards' rules for them followed; where the app had a workflow of its own before, a list of what that did and this one doesn't | use | partly — 2026-11-18, 0.1.0-alpha.2, a real SwiftUI app (TCA + SwiftData, no unit-test target): the migration only, no feature run yet. The app's own workflow (local skills) did, and this one doesn't: a confirmation pause after each implementation increment; each increment handed to a project subagent with the project's skills preloaded; the project's SwiftUI, SwiftData and TCA reference skills loaded explicitly; the TCA version restated at the start of TCA work. Its project rules moved to `.mobile-dev-skills/standards.md`, which had to replace two bundled rules (H6, H7). Since 0.1.0-alpha.3, not yet run: the project's standards file takes a `## Workflow` part (`Skills:` loaded before code, by implementation subagents and by the trivial path; `Pause after each task: yes`), the TCA version is already in the Detection report's State line, and H6 and H7 are fixed |
| A3 | The fvm matrix: an fvm project, an unpinned one, and `build-version.sh --dry-run` with `.fvmrc` but fvm off the PATH | The skills' `Flutter/Dart command` line matches the fvm rule's table in each case; the script exits 1 before touching `pubspec.yaml` in the last | synthetic | open |

### B. Intake and spec

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| B1 | A Large request, intake to split | One question per turn; the split proposed after intake; a sheet per sub-feature and `> Split:` on the parent; each sub-feature specced and approved on its own | use | open |
| B2 | A Standard intake from scratch with gaps, through the Step 1.6 loop | Intake asks the non-functional topics that apply; the quality check runs on the saved file before every approval question, again after each spec change, and its findings become §8 TBDs | use | fixed — 2026-11-18, 0.1.0-alpha.3, `feature-spec`'s quality check counts copying a sibling scenario's copy or behavior as a guess: the §8 item offers it as a proposal the user confirms in one word. Before it: partly — 2026-11-18, pre-release 0.3.24, articles fixture: the Step 1.6 loop on a baseline spec's open items (B5); intake's topic questions from scratch not yet run. Also 2026-11-18, 0.1.0-alpha.2, a real Flutter app: standalone `feature-intake` → `feature-spec`, so no Step 1.6 loop; intake asked the applicable topics one per turn (permissions with usage strings and denial; notifications and analytics as one side-effects question; accessibility and localization with the design question), recorded deep links and push as out of scope from the notification answer, and took offline from the existing sync's practice; `check_spec.sh` ran on the saved file before the approval question and after each change (findings 62 → 0 → 0). Not met: quality-check-2 gaps (failure scenarios for a pull-to-refresh, an enable flow and a first estimate) were added as scenarios with copy reused from sibling scenarios instead of becoming §8 TBDs |
| B3 | A project with its own spec layout (Step 1.4) | The spec follows the project's layout and language; the §6 blocks sit in its behavior section; the index is found and written | use | open |
| B4 | A localized app (ARB) | §7 lists the string keys per locale; Phase 2 adds them to every ARB file and runs l10n | use | open |
| B5 | The spec checker in Step 1.6, on a spec with open baseline items | `check_spec.sh` run on the saved file before the first approval question and after each change, its `RESULT=` line quoted; approval asked only at `open=0`; deferred items marked `deliberately deferred` | use | passed — 2026-11-18, pre-release 0.3.24, articles fixture with 9 open baseline items, $2.67 over three turns |
| B6 | The spec checker on a project's own layout | `--own-layout` passed; no ten-section or §6 findings on the layout's own headings and text; blocks and checkbox items checked wherever they sit; a provisional list at any heading level left out of `open`. Also a layout with a checklist that isn't questions (acceptance criteria): every unticked box counts as open, so see whether the gate gets stuck | use | partly — 2026-11-18, 0.1.0-alpha.1, a real Flutter app: `--own-layout` on 25 specs in the app's own layout gave no ten-section or §6 findings, counted blocks wherever they sit (§1, §3, §6.x, §7, §8, §8A, §12), caught a `####` heading inside a block, and left `### Provisional shapes` lists out of `open`; a checklist of owner console tasks counted as open=3, so the gate would hold until each is ticked or marked `— deliberately deferred`; not run: a provisional list at another heading level, the Step 1.6 gate itself |
| B7 | The spec checker under a Linux awk (mawk, gawk, busybox) | The same results on fixture specs as macOS awk, CRLF and `—` markers included | synthetic | open |
| B8 | A declined quality-check finding in Step 1.6 | The item stays with `— declined` after its text; `open` drops by one; an open question that merely mentions something declined (a card) still counts | use | open |
| B9 | `feature-spec` on its own, for two features | Each spec saved as `<slug>-feature-spec.md`, no shared file; an update keeps its file's name | use | partly — 2026-11-18, 0.1.0-alpha.2, a real Flutter app: one feature saved as `<slug>-feature-spec.md` (the intake sheet's slug) beside the project's existing specs; a second feature and an update not run |
| B10 | `feature-intake` inside a `feature-workflow` run | The finished sheet returns to the orchestrator's Step 1.4, never straight to `feature-spec` | use | open |
| B11 | A feature with no screen of its own (a background service, a shared FAB) | The spec gives the host that isn't a screen a `screen` value `feature-spec` defines; quality check 1 and `check_spec.sh` treat it alike: skipped (the script already skips `none` and `N/A — …`, which the skill never mentions) or settled by one `N/A — <reason>` scenario titled `Loading, Error, Empty, Success` | use | fixed — 2026-11-18, 0.1.0-alpha.3, `feature-spec` defines `screen: none` for behavior with no screen of its own (after the screens' requirements, before the invariants), says behavior with a trigger is a requirement, not an invariant, and quality check 1 and `check_spec.sh` both skip it. Before it: partly — 2026-11-18, 0.1.0-alpha.2, a real Flutter app: converting a bullet spec, a subagent gave a weekly notification's blocks (no screen of their own) `screen: none`, and `check_spec.sh` skipped them with no `states` finding; `feature-spec` still doesn't define the value, and quality check 1 wasn't run. Also 2026-11-18, 0.1.0-alpha.2, a real SwiftUI app: converting freeform docs (G12), subagents gave 12 screenless blocks in 6 specs (analytics, push registration, ATT sync, watch-progress reporting, sign-out purge, progress broadcast) `screen: none`, and others used `### Invariant:` blocks with no `screen` key; `check_spec.sh` skipped both with no `states` finding. Also 2026-11-18, 0.1.0-alpha.2, a real Flutter app: a new spec gave its native background logic (estimator, write policy, background triggers) 15 `### Invariant:` blocks with no `screen` key; `check_spec.sh` gave no `states` finding |
| B12 | A non-functional topic answered in its template part and also named in §9, e.g. §2's `- Deep links: none.` beside §9's `Not affected: deep links` (in a real SwiftUI app, a hand-converted spec did this and nine of eleven specs converted from it copied it; `check_spec.sh` passed all of them, and one converter caught it by quality check 5) | `check_spec.sh` reports the double answer, at least for deep links, or the template's deep-links bullet says to leave it out when §9 names the topic | use | fixed — 2026-11-18, 0.1.0-alpha.3, the template's optional parts carry their condition (leave the deep-links line out when section 9 names deep links), and `check_spec.sh` reports a `layout` finding when a §9 `Not affected:` line names a topic whose template part is still there (deep links, accessibility, localization, permissions, native code, offline with background); no false finding on 79 real specs. Before it: failed — 2026-11-18, 0.1.0-alpha.2, a real Flutter app: `feature-spec` writing a new spec put §2's `- Deep links: none — …` beside §9's `Not affected: … deep links`; `check_spec.sh` gave `RESULT=pass findings=0`, and only quality check 5 by hand caught it |
| B13 | `feature-intake` → `feature-spec` outside `feature-workflow`, in a project whose specs live in a folder with an index (`docs/specs/` + `index.md`) (in a real Flutter app, `feature-spec`'s Handoff step 1 fell back to "the project root", since `feature-intake`'s handoff names no folder; the model picked `docs/specs/` itself and wrote no index row) | The spec is saved beside the existing specs, not at the project root, and gets an index row (`draft`), or the handoff names the missing row | use | fixed — 2026-11-18, 0.1.0-alpha.3, `feature-spec`'s Handoff saves beside the spec index or the existing specs, in their naming, before falling back to the project root, and says the index has no row for it yet, which `feature-workflow` adds on its next lookup |
| B14 | A provisional field on an existing endpoint: an optional object added to an existing request model the backend doesn't accept yet (in a real Flutter app, "When the API is explicitly not ready yet" spoke only of whole new endpoints, `PROVISIONAL` in the Path column and a stub repository, so the model marked only the entity heading and the §8 list) | The skill says how to mark it: the existing path stays, the field's entity is marked provisional, it sits in §8's `### Provisional shapes` list, and no stub repository is asked for | use | fixed — 2026-11-18, 0.1.0-alpha.3, `feature-spec`'s "When the API is explicitly not ready yet" has the field case (the real path, the field marked `PROVISIONAL` with a note under its entity, the `### Provisional shapes` list, no stub, what is sent meanwhile asked or a TBD), restated in `feature-intake`, `feature-workflow`, the common standards and the scaffold |

### C. Phase 2, verification and review

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| C1 | A run whose verification ends on a FAIL, then a resume in a new session | The report is written with the FAIL and later checks `NOT RUN`; the index stays `approved`; the resume starts at Step 2.3 and runs every check from the first | synthetic | open |
| C2 | A review whose fix loop ends on a FAIL, then a resume | The fix goes back through Step 2.3 and `feature-verify` (not a grep); the report's `### Review` holds the first round; the resume continues with the second round | synthetic | open |
| C3 | An app with codegen, ARB and goldens | Codegen runs before tests on annotated files; l10n runs; goldens are created with the golden command and listed under Manual checks | use | open |
| C4 | A stale `stack.md` with no `Test packages` line | Detection re-runs for the test layer and rewrites the saved stack | use | open |
| C5 | `feature-scaffold` invoked on its own, outside the orchestrator | Its own Step 1 detection and Step 5 verification run, in the adapter's order, with the closing notes | use | open |
| C6 | A manual copy without `agents/` | Step 2.4 runs the built-in pass and records the second opinions as `NOT RUN` | synthetic | open |
| C7 | Phase 2 on a Flutter app with flavors and `permission_handler` or Pigeon | Native files and declarations per platform; the Native build row runs each touched platform; the denial scenario's test | use | open |
| C8 | The trivial path on an `Info.plist` usage-string edit | A change plan, no spec conversion, the edit and the checks it needs, no report | use | open |
| C9 | `swift-build-resolver` on a failing `flutter build ios` | Called once after two failed fixes of Native build; the check re-run by the orchestrator | synthetic | open |
| C10 | A machine without Xcode | Native build for iOS becomes a manual check, not a FAIL or a PASS | synthetic | open |
| C11 | The trivial path with a check that fails twice | No build fixer called; it stops and shows the command, its output and what it tried | synthetic | open |
| C12 | A Flutter run that writes native code in a language its native adapter doesn't cover (Objective-C in `ios/`, Java in `android/`) | No native review of those files: a Native row of their own records `NOT RUN — no reviewer for <language> files`; files in the adapter's language still get the Native pass | synthetic | open |
| C13 | `feature-verify`'s anchored-test command on several files (in a real Flutter app, `--reporter expanded` on three files printed only 11 of one file's 26 passing tests; `-j 1`, or the file alone, printed them all) | Every anchored description shows in the output as a test of its own (e.g. the adapter's command runs with `-j 1`), so none is reported `test missing` when it passed | use | fixed — 2026-11-18, 0.1.0-alpha.3, the Flutter adapter's anchored-test command runs with `--concurrency=1`, and `feature-verify` reruns a description missing from a multi-file run with its file alone before reporting `test missing` |
| C14 | A Flutter feature whose core logic runs in native code with native unit tests (in a real Flutter app, an estimator that must run in iOS HealthKit background wakes, where the Flutter engine never starts, was specced with Swift Testing and JUnit tests on shared JSON fixtures; the Flutter adapter's "Native interop" says native code is checked only by the native build and on a device, the Test-name search looks for a Dart string literal, and anchored tests run with `flutter test`, so the spec had to note that `feature-verify` can't run them) | The Flutter adapter's Test plan has a native-unit line with its commands (`swift test` / `xcodebuild test`, `./gradlew :app:test<Variant>UnitTest`); Phase 2 runs them in Step 2.3; `feature-verify` runs anchored native tests, or lists them on its report's `Not run:` line when this machine can't run them, never `test missing` | use | fixed — 2026-11-18, 0.1.0-alpha.3, the Flutter adapter has a Native unit test kind run through the SwiftUI and Compose adapters' commands (`RunnerTests` in `ios/Runner.xcworkspace`, `android/` `:app:test<Variant>UnitTest`), in the Tests check and its baseline, and `feature-verify` runs anchored native tests or lists them under `Not run:`; the commands are composed from the adapters and haven't run on a real app |
| C15 | A Flutter run that adds a Swift file under `ios/Runner/` that isn't a test (Flutter's iOS project is group-based, so a new file isn't compiled until the Runner target lists it; found while adding native unit tests in 0.1.0-alpha.3, whose test files join their target through the SwiftUI adapter's File registration, while the Flutter adapter's "Native interop" gives no such rule for other new Swift files) | The Flutter adapter says how a new `ios/Runner/` file joins the Runner target (e.g. the SwiftUI adapter's File registration for a group-based project, or asking first); the Native build compiles it | use | open |

### D. Baseline specs

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| D1 | Intake and Step 1.5 on top of a baseline spec | Intake asks only the delta; the update keeps the baseline's ids and anchors; the index row appears at Step 1.5 | use | open |
| D2 | "Extending a baseline": a change that relies on a `Not read:` file | The subagent extends the baseline first, and the user sees what it added | use | partly — 2026-11-17, pre-release 0.3.23, articles fixture: one file read at the baseline review, not from a later change |
| D3 | A SwiftUI baseline | Entry points from the SwiftUI adapter; view-model anchors | use | open |
| D4 | Phase 2 against a baseline spec | Untouched blocks keep their anchors; the change's scenarios get tests | use | open |
| D5 | A session that ends at the baseline review, then `continue` in a new session | `request.md` written before the subagent; the resume returns to the review and continues with the saved request without asking for it; `Reviewed:` added after the answers | use | passed — 2026-11-17, pre-release 0.3.23, articles fixture, $2.50 over three sessions |
| D6 | A delegated run's baseline, resumed in a new session | The baseline row matches a folder with `brief.md` and `request.md`; `delegated.md` read; the size line first; back at the review | use | passed — 2026-11-17, pre-release 0.3.23, articles fixture, $0.56 |
| D7 | The spec checker in the baseline subagent | The subagent finds `check_spec.sh` from the `feature-spec` path its prompt gives, runs it with `--adapter` on the saved spec, fixes its findings and reports `Check: RESULT=…` | use | passed — 2026-11-18, pre-release 0.3.24, articles fixture without the articles spec, $1.22 |
| D8 | A baseline of a Flutter feature with native unit tests (the Flutter adapter's "Code entry points" look for tests only under `test/`, so a baseline can't anchor an existing `ios/` or `android/` unit test; found while adding native unit tests in 0.1.0-alpha.3) | When the feature has native code, the baseline reads its native unit-test folders and anchors a native test whose body checks the scenario, found by the native adapter's Test-name search, or names those folders in a `Not read:` item | use | open |

### E. Bug fix and refactor modes

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| E1 | A refactor | `> Pinned:` in `tasks.md`, each step's Analyze and pin-test results on its task line, the Conventions Report question when the design departs from it | use | open |
| E2 | A diagnosis that finds no cause | Asks for more, diagnoses once more, then stops with both diagnoses and changes nothing | synthetic | open |
| E3 | A reproduction test that passes | Nothing fixed and the task left unticked; the test, its output and the diagnosis shown; the user's pick followed: the test rewritten to the report's path, a second diagnosis given the test (a new cause corrects the change record and goes back to Step 1.6), or a manual reproduction that keeps the passing test as the scenario's, or a stop | synthetic | open |
| E4 | A bug fix on a never-specced feature | Baseline spec first, then the diagnosis | use | open |
| E5 | A refactor with tests-only coverage (baseline declined) | An approved plan instead of a spec; no Conformance; `tasks.md` as the record | use | open |
| E6 | A refactor whose baseline run fails on the moving code | It stops and points to a bug fix or an edit first | synthetic | open |
| E7 | A resume in each mode | The mode taken from the newest change record or the `> Change:` line, and named | use | open |
| E8 | Both modes in a SwiftUI project | The reproduction test with Swift Testing, on the view model | use | open |
| E9 | Either mode on a spec still in bullets | The conversion question before the spec change; a declined refactor runs with Conformance `SKIPPED` | use | open |
| E10 | A missing-tests request, both phases | The type line; `missing-tests.md` read; a baseline run; a plan by regression cost, approved before any test; `> Change: Missing tests …`; tests only in the host-test folder, passing on untouched code; Conformance as a refactor's; review; the index row as it was | use | passed — 2026-11-17, pre-release 0.3.23, articles fixture, $5.93 |
| E11 | Tests skipped in a Small edit | `test: none — <reason>` set before approval and named in the approval question; no new test; Conformance passes; the run report's Follow-ups list them | use | partly — 2026-11-17, pre-release 0.3.23, articles fixture, $2.85: passed up to Step 2.4, whose review the run didn't reach |
| E12 | A missing-tests test that fails on a THEN line | Nothing in the app's source changes; the scenario goes to a bug fix (the test as its reproduction test) or out of the plan | synthetic | open |
| E13 | A missing-tests run resumed in a new session | `missing-tests.md` read again; the run found by its `> Change:` line and resumed at the first unticked task | use | open |
| E14 | A missing-tests request on a never-specced feature | `request.md` with `Type: missing tests`, a baseline spec, then the plan | use | open |
| E15 | A planned scenario dropped during a missing-tests run | It leaves the plan: task line rewritten, under Follow-ups; Conformance passes; a review finding fixed in tests only | use | passed — 2026-11-17, pre-release 0.3.23, articles fixture, $2.03 |
| E16 | A missing-tests run on a spec whose row is `approved` (a change not built yet), and on a baseline spec with no row | The `approved` row keeps its status, only its `Last verified` cell copied; resumed mid-run, it goes to its first unticked task, not to Step 1.6 for the unbuilt change's blocks; the baseline spec gets a row at `implemented` | use | open |
| E17 | A test skipped in Phase 2, after approval | Its `test` becomes `none — <reason>`; Conformance doesn't fail on it; the run report's Follow-ups list it | use | open |
| E18 | A bug fix whose reproduction test the user skips | `> Reproduction: manual — …` in `tasks.md`; the fix still goes through Step 2.3; the scenario's `test` set as the skip says | use | open |

### F. Monorepos and delegated runs

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| F1 | A `draft` API contract, approval `with the other parts` | Provisional shapes from the contract; the run stops at the closing block `awaiting approval`; after the contract is approved, the shapes are confirmed as a spec change the user approves | use | open |
| F2 | A delegated bug fix and a delegated refactor | The brief's Request reaches Step 0; the app spec's own slug holds the state | use | open |
| F3 | A Large delegated slice | Sub-features with the brief; a `Spec` and a `Report` line per spec in the closing block | use | open |
| F4 | A direct cross-part request in a live session (not an eval) | The parts named, the project's workflow pointed to, or the app's part offered alone; nothing written | use | open |
| F5 | A SwiftUI app in a monorepo | The SwiftUI adapter's Root is the app folder; nothing written outside it | use | open |
| F6 | A monorepo with two apps | The adapter lookup asks which app; state stays in each app | synthetic | open |
| F7 | `mobile-build-deploy` in a monorepo | It asks which app to build and runs from that app's Root | use | open |
| F8 | A delegated run | `delegated.md` read before Step 0; `brief.md` written first; the first reply opens with the size line | use | passed — 2026-11-17, pre-release 0.3.23, monorepo fixture, $1.72 |
| F9 | A brief with `Request: missing tests` | The run says the request isn't delegated and stops, writing nothing | synthetic | passed — 2026-11-18, pre-release 0.3.25, a monorepo copy of the articles fixture, $0.26 |

### G. Compaction and migration

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| G1 | Compaction of a spec with an older single `-changelog.md` | The old file untouched, a new `changelogs/<slug>/<date>.md`, and the pointer line naming both | use | open |
| G2 | A second compaction the same day | The new entries prepended to that day's file | synthetic | open |
| G3 | A manual copy replaced as `MIGRATION.md` says | Old folders gone, new ones answer, no duplicate skill fires | synthetic | open |
| G4 | The guide's `/plugin` commands in the interactive UI | The same result as their CLI forms | use | open |
| G5 | A skill-driven conversion of a bullet spec | Existing untested scenarios get `none`, tests that check them are anchored | use | partly — 2026-11-17, pre-release 0.3.22, v0.2.0 project fixture: a conversion before the `none` rule was written |
| G6 | Compaction of a spec with a bug-fix record, index row `draft` and then `implemented` | `draft`: the record kept and named, nothing compacted; `implemented`: Discard removes it, Extract moves it verbatim to `changelogs/<slug>/<date>.md` with the pointer line | use | passed — 2026-11-17, pre-release 0.3.23, articles fixture, $1.18 |
| G7 | Compaction with the spec checker | The script run in Step 1 and again in Step 5, both `RESULT=` lines quoted, no new finding after the fold, older findings named as follow-ups and left alone | use | open |
| G8 | A pre-release 0.3.x install updated to the 0.1.0-alpha line, whose version number is lower | The update reaches 0.1.0-alpha.x: the install's recorded version and the cached `.claude-plugin/plugin.json` both show it (`claude plugin list` gives the recorded version for a git marketplace; for a directory marketplace it reads the source folder live, so read `~/.claude/plugins/installed_plugins.json`) | use | passed — 2026-11-18, 0.1.0-alpha.1, the owner's install, local directory marketplace, `claude plugin marketplace update` + `claude plugin update`: `installed_plugins.json` and the cached `plugin.json` at 0.1.0-alpha.1, no model cost |
| G9 | Every bullet spec of a real app converted at once, as `MIGRATION.md`'s "Converting a spec by hand" says | Each spec: the `Last verified` line directly under its title; nothing added or dropped; each `enforced` a `<path>#<Symbol>` that exists, `(filled in Phase 2)` only where none can be named; `test` anchored only where the test's body checks the THEN and AND lines, else `none`, `manual — <reason>`, or `(filled in Phase 2)` for a feature not built yet. `check_spec.sh` (`--own-layout` for a project's own layout) reports no `syntax` or `layout` finding, and `states` or `items` findings only for gaps the bullets left. `feature-verify` on one spec runs its anchored tests and reports `not anchored` and `no test` as the guide's "Check it" step says | use | fixed — 2026-11-18, 0.1.0-alpha.3, the conversion rules moved to `skills/feature-spec/conversion.md`, which `feature-spec` and `MIGRATION.md` cite: what a conversion may add (only the checker's forms; a renamed name corrected and reported; behavior the code contradicts as an `uncertain` item; nothing filled from the code) and a converter's checklist for the three slips. Before it: partly — 2026-11-18, 0.1.0-alpha.2, a real Flutter app: 7 bullet specs converted (one by hand, six by parallel subagents given it as the worked example); each got the `Last verified` line; 271 `enforced` anchors all resolve, none left as a placeholder; 65 test anchors, each checking its scenario's THEN and AND lines, the rest `none`; `check_spec.sh` gave 0 `syntax` or `layout` findings and 6 `states` findings, all gaps the bullets left; `feature-verify` on one spec ran its 29 anchored tests (all passed) and reported 24 `no test`. Review fixed three subagent slips: a placeholder where widgets could be named, a test anchored that checks only part of a THEN line, and `manual` where the spec recorded a skipped-test reason (now `none — <reason>`). Not met: "nothing added", since the checker forced small additions (a reason for a bare `Empty: N/A.`, an 11-section spec renumbered, G10) and the converters had to place non-bullet prose themselves (G11). Also 2026-11-18, 0.1.0-alpha.2, a real SwiftUI app: 11 freeform design docs, not bullet specs (G12), converted, one by hand and ten by seven parallel subagents given it as the worked example; each got the `Last verified` line; 390 `enforced` anchors all resolve, one block left at `(filled in Phase 2)` for a part not built yet; no unit-test target, so every `test` is `none` except four `manual` system-sheet scenarios; `check_spec.sh` gave 0 findings on all 11 (146 blocks, 538 scenarios); `feature-verify` not run. The converters corrected over 40 stale implementation details from the code and left 17 open §8 items, 10 of them code/doc mismatches, which the owner then settled (8 by following the code, 1 by a code fix, 1 in CLAUDE.md). Not met: "nothing added", since converters filled accessibility, routing and entry-point lines from the code, and a topic answered twice passed the checker (B12) |
| G10 | A v0.2.0 bullet spec whose layout isn't the ten sections (an extra section, such as `New screens / widgets`, moves the UI section off §6) | `MIGRATION.md` names the fix: renumber to the ten and say where the extra section's text goes. After conversion, `check_spec.sh` gives no `layout` finding and no `block outside section 6` | use | fixed — 2026-11-18, 0.1.0-alpha.3, `conversion.md`'s "The layout" renumbers to the ten first, an extra section becoming a `###` subsection of the template section on its topic; `MIGRATION.md` §3 starts with it; an 11-section fixture converted by it gave no finding |
| G11 | Converting a §6 that holds more than state bullets: intro prose, `### <Screen>` headings, layout blueprints and per-widget styling, a bare `Empty: N/A.`, a recorded "Tests: none" decision | `MIGRATION.md` says where each goes (e.g. body lines after the requirement's statement) and how a reasonless `N/A` and a recorded test skip convert (`none — <reason>`); two converters place them alike, with no `syntax` finding | use | fixed — 2026-11-18, 0.1.0-alpha.3, `conversion.md`'s "Section 6 beyond the bullets" places intro prose, `### <Screen>` headings, layout blueprints and styling, a bare `N/A` (`N/A — no reason recorded`) and a recorded test skip (`none — <reason>`) |
| G12 | Converting a project's own freeform feature docs (design notes with Files lists, rationale, edge-case tables meant for another team, QA lists and dated addenda; neither the ten sections nor v0.2.0 bullets) to the template (in a real SwiftUI app, 11 such docs were converted with placement rules the guide doesn't give) | `MIGRATION.md` or Step 1.4 says whether such docs stay as the project's own layout (`--own-layout`) or convert, and, for a conversion, where a Files list, rationale, tables kept verbatim for another team, QA lists and dated addenda go; two converters place them alike | use | fixed — 2026-11-18, 0.1.0-alpha.3, `conversion.md`'s "A project's own feature docs" and `feature-workflow` Step 1.4: a shared layout is kept (`--own-layout`), freeform docs convert after one question, dated addenda go through `feature-spec-compact` first, and a Files list, rationale, tables kept for another team (an unnumbered `## Appendix — <title>` after section 10) and QA lists each have a place |

### H. SwiftUI variants

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| H1 | A group-based project, and one using XcodeGen or Tuist | New files registered the way the project does it | use | open |
| H2 | A project with SwiftLint or swift-format and snapshot tests | Format uses the project's tool; snapshots recorded and listed under Manual checks | use | open |
| H3 | TCA with SwiftData | Screen scenarios tested on the reducer with `TestStore`; in-memory stores in tests; migrations for shipped models | use | open |
| H4 | Xcode 16 (the declared minimum) | `xcresulttool get test-results`, Swift Testing and synchronized folders work as written | synthetic | owner |
| H5 | A manual copy in a SwiftUI project | The adapters found in `.claude/platforms/` | synthetic | open |
| H6 | A TCA app whose screens send `.onInit` from `onAppear` and start long-lived effects there, such as event-bridge subscriptions that must outlive a pushed screen (in a real SwiftUI app, the project's standards file had to replace **Load in `.task`**, since `.task` would cancel them) | The SwiftUI standards' **Load in `.task`** says how a TCA screen starts its effects (e.g. `.task { await store.send(.onInit).finish() }` for screen-scoped work, a store-lifetime effect for subscriptions), so a TCA project needs no replacement | use | fixed — 2026-11-18, 0.1.0-alpha.3, **Load in `.task`** gives the TCA form: screen-scoped work from `.task { await store.send(.task).finish() }`, an effect that outlives a pushed screen from an action sent in `onAppear`, cancellable by id and living with the store |
| H7 | An app that reads its String Catalog through Xcode's generated symbols (`Text(.keyName)`, `String(localized: .keyName)`) (in a real SwiftUI app, the project's standards file had to replace **Strings in the String Catalog**, which names only `Text("key")` and `String(localized: "key")`) | The rule accepts the generated-symbol form where the convention probes' localization step finds it | use | fixed — 2026-11-18, 0.1.0-alpha.3, **Strings in the String Catalog** takes the form the probes find, Xcode 26's generated symbols (`Text(.keyName)`, `String(localized: .keyName)`) included, and the localization probe and the Detection report name it |

### I. Build and deploy

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| I1 | A real signed TestFlight upload with Xcode's saved session, for a Flutter app and a native one | The build appears in App Store Connect; the summary block matches | use | owner |
| I2 | The same with an App Store Connect API key, from `ios-api-key.json` and from the environment | As I1; the key file refused when git would commit it | use | owner |
| I3 | A Play internal-testing upload through the API (Phase 1) | The release appears in Play Console; exit 42 alone allows the browser fallback | use | owner |
| I4 | Android with an old `android.json` in `.flutter-store-deploy/` | Phase select reads the legacy folder; the rename offered | use | open |
| I5 | A real archive of a CocoaPods workspace Flutter app | The workspace used; the archive checked | use | open |
| I6 | The old-script decline paths | Declined with a matching fvm pick, the script runs as it is; with a mismatch, the skill stops before `pubspec.yaml` changes | synthetic | open |
| I7 | Installs from the public GitHub marketplace | A v0.2.0 install follows the guide; a fresh install of the current version; the `#v0.2.0` pin installs v0.2.0 | use | passed — 2026-11-18, 0.1.0-alpha.1, isolated `HOME`, no model cost: a fresh install (eight skills, only the plugin folder cached); the `#v0.2.0` pin, which stayed on the tag after `main` moved and a `marketplace update`; a v0.2.0 project install that failed to load after a refresh ("Plugin flutter-skills not found in marketplace flutter-skills") and was replaced by the guide's project-scope commands |
| I8 | `mobile-build-deploy` for Android with and without `bundletool`, and with a stale AAB | With it: package, `versionName` and `versionCode` read and compared; without: the file's time checked and the summary says the version wasn't read; a stale AAB stops before deploying | synthetic | open |

### J. Maintainer

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| J1 | The first `contracts` audit | A proposal per finding, `last_audited_commit` recorded | use | owner |
| J2 | The first `toolchain` run | Minimums proposed for Flutter/Dart (3.41 for the UIScene text), AGP and the build scripts' Xcode, with evidence | use | owner |
| J3 | The first `claude-code` run | The `cc-*` and `readme-*` pages reviewed; the comparison table checked | use | owner |
| J4 | The first `packages` run | Feeds baselined | use | owner |
| J5 | `ecc` against a newer upstream tag | A three-way merge proposal per vendored file | use | open |

### K. Jetpack Compose

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| K1 | A real Compose app of the owner's, a new feature and an edit | As A1, with the Compose adapter's commands and the backtick test names | use | owner |
| K2 | The fallback stack in a fresh project: a Phase 2 run that adds Hilt, Retrofit and kotlinx.serialization | Each new dependency approved before it is added; `@HiltAndroidApp` and `@AndroidEntryPoint` added; files mirror the templates; Analyze and Tests pass | use | open |
| K3 | A detected non-fallback stack: Koin, Voyager or Gson | Detection names them; no template used; Gson DTOs follow the standards' Gson rules | use | open |
| K4 | A multi-module project (`:feature:*`, `:core:*`, convention plugins) | The module comes from the probes or a question; Analyze and Tests run for that module | use | open |
| K5 | A project with ktlint, Spotless or detekt, and a lint baseline file | Format uses the project's tool; Analyze compares per file against the baseline | use | open |
| K6 | An AGP 8.x project (the declared minimum) | The commands work as written; Hilt takes Dagger 2.58 or lower | synthetic | open |
| K7 | A Compose feature with a runtime permission (camera or notifications) | Manifest row, rationale string, interface faked with a denial scenario test, and the device check listed | use | open |
| K8 | `kotlin-build-resolver` called by Step 2.3 itself, after two failed fixes in a real run | The orchestrator passes the Inputs section's list, re-runs the check itself, and reviews the edit | synthetic | partly — 2026-11-18, pre-release 0.3.26, Compose Greeter, $0.22: the agent called by a stand-in for Step 2.3 |
| K9 | A Flutter run whose Android native build fails twice | `kotlin-build-resolver` is called for Native build with the Flutter command | synthetic | open |
| K10 | A missing-tests or bug-fix run in a Compose app | Backtick test names; the reproduction test fails first (bug fix) | use | open |
| K11 | A manual copy in a Compose project | The adapter found in `.claude/platforms/` | synthetic | open |

### L. Sibling plugins

| ID | Case | Pass when | Kind | Status |
|---|---|---|---|---|
| L1 | `mobile-store-deploy` after a real upload, with and without `store-submission-prep` installed | Listed: offered under `next`, invoked only on a yes. Not listed: the plugin named once with its install commands | use | open |
| L2 | `crash-issue-fixer` on a crash whose fix changes a scenario of a `mobile-dev-skills` spec, with `feature-workflow` listed | Step 1 records the feature specs; Step 5 offers "Through the feature workflow"; Step 6 skips the group; Step 7 hands it over last with no field data; bug-fix mode offers no hand-back, starts from the cause and writes the reproduction test first | use | partly — 2026-11-18, pre-release 0.3.27, articles fixture, $0.87: the receiving side only, with a typed hand-over |
| L3 | `store-submission-prep` when the developer says the build isn't uploaded yet | `mobile-build-deploy` or `mobile-store-deploy` offered when listed, else the plugin named once; the sheet is still written | use | open |
| L4 | A crash report with steps in `feature-workflow` | Stays in bug-fix mode; no hand-off offered | use | open |
| L5 | `feature-intake` with Figma links: Claude-in-Chrome loaded and no Figma MCP; then a Figma MCP loaded; then neither | First: the export offered into `.mobile-dev-skills/<feature-slug>/figma/`, and the references name the files. Second and third: no offer (a pre-release run with neither tool was offered the export, which the current rule forbids) | use | open |
| L6 | A crash report without steps, `crash-issue-fixer` listed, the user declines the hand-off | Bug-fix mode asks for the steps and goes on | synthetic | open |
| L7 | A request to submit a build for review, with no upload in the session: with `store-submission-prep` listed, and without | Listed: that skill fires, or `mobile-store-deploy` offers it and invokes it only on a yes. Not listed: `mobile-store-deploy` names the plugin once with its install commands and uploads nothing | use | partly — 2026-11-18, 0.1.0-alpha.1, eval Flutter fixture, $0.20: listed, two runs offered the installed skill and uploaded nothing; not listed, the trigger eval shows the skill fires, but its reply wasn't checked |

## Covered by earlier runs

Paths that pre-release runs covered before these tables existed, so they aren't cases:

- A full intake writing `intake.md` turn by turn, from a brief and for a Small edit (2026-11-17, 0.3.21 and 0.3.22).
- A complete Phase 2 run writing `report.md` and the index row (2026-11-16 to 17, 0.3.9 to 0.3.21), with `security-reviewer` (0.3.21).
- A second adapter and the hybrid path with Swift (2026-11-16, 0.3.14), and with Kotlin, including a `Native (android)` review pass (2026-11-18, 0.3.26).
- Phase 2 anchor filling (0.3.9), and the conversion of a bullet spec (0.3.22).
- The trivial path (0.3.11 for Flutter, 0.3.14 for SwiftUI, 0.3.26 for Compose).
- The Compose adapter's detection, Phase 2 with a project standards file, and `feature-verify` with the backtick test-name search (2026-11-18, 0.3.26).
- A manual copy with the renamed folders, and a marketplace-cache install (2026-11-17, 0.3.16).
- A marketplace reinstall under the new name, and a fresh project creating `.mobile-dev-skills/` (2026-11-17, 0.3.22).
- A session started at a monorepo's root (2026-11-17, 0.3.21).
- The crash-report mention with and without `crash-issue-fixer` listed (2026-11-18, 0.3.27).
