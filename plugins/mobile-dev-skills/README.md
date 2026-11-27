# mobile-dev-skills

A Claude Code **plugin** that builds features in Flutter, native SwiftUI and native Jetpack Compose apps from a spec you approve, checks the code against that spec, and releases the apps to TestFlight and Google Play. It bundles eight skills in two families — six for the feature workflow in Flutter, native SwiftUI and native Jetpack Compose apps, two for builds and store uploads — and seven agents the feature workflow uses for review and build fixes. The build skill handles Flutter and native SwiftUI apps; the store uploader works for any iOS/Android build.

Coming from `flutter-skills` v0.2.0? [MIGRATION.md](MIGRATION.md) says what to reinstall and how your specs and project files carry over.

Paths in this README are from the folder that holds it, the plugin's own folder.

## Alpha

The plugin is in alpha, in versions `0.1.0-alpha.N`. Its skills are complete, but many of their paths have run only in test projects so far; its author's own apps are its end-to-end tests, and [the repository's test plan](https://github.com/teaualune/mobile-dev-skills/blob/main/TESTING.md) lists the cases and which have passed. Until it leaves alpha, read what a run wrote before you commit it, expect changes between versions, and report problems as [issues](https://github.com/teaualune/mobile-dev-skills/issues). To stay on v0.2.0 until a stable release, see [MIGRATION.md](MIGRATION.md)'s "Staying on v0.2.0".

## What it does differently

- **The spec is a contract with the code.** Each behavior is a requirement with an id and WHEN/THEN scenarios. Phase 2 anchors every requirement to the symbol that carries it and every scenario to the test that checks it, so `feature-verify` can check, at any time, that each requirement's code is still there and each scenario's test still passes.
- **No code before you approve the spec.** Open questions are settled first, and a quality check looks for missing states, failures, action results and vague words before every approval question. A script decides its mechanical part (the four states per screen, block syntax, the ten sections, open questions left), so that part never depends on a model's reading. "ok" alone isn't approval.
- **Code in your project's own style.** Before writing a line it detects the stack (state management, routing, HTTP, codegen, test packages) and the conventions (folders, naming, an existing feature to mirror). A fallback stack is used only when detection fails, and says so.
- **The backend doesn't have to be ready.** Say so, and the API shapes are proposed openly, marked provisional in the spec, built against a stub repository, and listed for the backend to confirm.
- **"Done" means checked.** Every layer comes with its tests, a verification run with the conformance check blocks "done" on any failure, and a review in fresh subagents checks the change against your conventions, your standards and the spec.
- **Tests when you have time for them.** When delivery comes first, say "skip the tests for …": those scenarios are marked `test: none — <reason>` in the spec, block nothing, and are listed as follow-ups. Until they exist, `feature-verify` reports them and leaves the spec's `Last verified` line undated. Later, `/mobile-dev-skills:feature-workflow add the missing tests for <feature>` plans tests for the scenarios you name, or for every untested one, the skipped ones included, and writes the ones you approve without touching the code.
- **Specs stay current.** A change edits the spec in place, and bug fixes and refactors also record why. `feature-spec-compact` later folds a spec's accumulated changes into its current state and removes those records, asking first whether to keep them in a changelog.
- **Releases with guard rails.** The build script lives in your project and names the artifacts it built. The build skill checks their bundle ID, version and build (an Android bundle's with `bundletool`, when it's installed); the uploader takes exactly those, pauses before an irreversible rollout and never bumps a build number on its own.

### A session, shortened

```text
> /mobile-dev-skills:feature-workflow add a screen listing the articles I saved
Size: Standard — a new screen and endpoint, plus a bookmark on the article screen.
Detected stack: Riverpod (codegen) · go_router · Dio · freezed · tests: flutter_test + mocktail
Q: When unsaving an article fails, what does the user see?
> The item comes back and a snackbar shows the error.
  …
Spec saved: docs/specs/saved-articles-feature-spec.md (index: draft)
Quality check: passed (RESULT=pass findings=0 blocks=4 scenarios=11 open=0). Approve the spec to start Phase 2?
> Approved, build it.
  …
Verification: Codegen PASS · l10n SKIPPED · Analyze PASS · Format PASS · Tests PASS · Native build SKIPPED · Conformance PASS
Review: built-in — no findings · flutter-reviewer — 1 MEDIUM, fixed · security-reviewer — no findings
```

The spec's section 6 after Phase 2: one requirement of three, with one of its two scenarios.

```markdown
### Requirement: Swiping an item unsaves it
<!-- id: saved-articles.2 -->
<!-- screen: SavedArticlesScreen -->
<!-- entities: SavedArticle -->
<!-- enforced: lib/features/saved_articles/presentation/saved_articles_screen.dart#SavedArticlesScreen, lib/features/saved_articles/providers/saved_articles.dart#SavedArticles.unsave -->

Swiping a list item SHALL remove that article from the saved list.

#### Scenario: Error — unsave fails
<!-- test: test/features/saved_articles/saved_articles_screen_test.dart#saved-articles.2 Error — unsave fails -->
- **WHEN** the delete request fails
- **THEN** the item returns to its place and a snackbar shows the error
```

### Next to Spec Kit, OpenSpec and ECC

| | What it is | This plugin |
|---|---|---|
| [Spec Kit](https://github.com/github/spec-kit/) | GitHub's toolkit for spec-driven development with many coding agents: a constitution, then specify, plan, tasks, implement and converge, plus bug-fixing and assessment extensions, presets and workflows | The same spec-before-code idea, for mobile apps in Claude Code only: it knows each platform's stack, commands and native code, and goes on from the feature to a review and a store release |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/) | Specs as the current truth, changed through a folder per change (proposal, spec deltas, design, tasks) that is archived into them, for 30+ AI assistants | Section 6 uses OpenSpec's Requirement and Scenario format. A change edits the spec itself, behind a hard approval gate, and anchors from each requirement to its code and each scenario to its test let `feature-verify` run those tests |
| [ECC](https://github.com/affaan-m/ECC) | A broad Claude Code harness: agents, skills, hooks and rules for many languages | Seven of its agents, copied in and refined for this workflow, are Phase 2's second-opinion reviewers and build fixers ("Agents" below). ECC itself isn't installed or needed |

## What's in it

**Feature workflow** — the two-phase flow (requirements → spec → approval → implementation):

- `feature-workflow/` — the orchestrator, started with its command or when you name it in a request, or by a project's own workflow that hands it the app's part of a monorepo feature ("Monorepos"); sizes each request, then runs Phase 1 (requirements → spec → TBD-resolution loop → approval) and Phase 2 (implementation with tests, then a verification run whose failing checks block "done", then a review in fresh subagents). A trivial tweak gets an approved one-paragraph change plan instead of intake and a spec, and a large feature is split into sub-features with a spec each. A change to a feature that was never specced first records what its code does today as a baseline spec, read within a file budget. A bug report is diagnosed in a subagent and reproduced as a failing test before the fix, and a refactor is pinned by the tests and the conformance check before any code moves; both are spec changes behind the same approval, and each records its reason in the spec for a later compaction. A request that only adds missing tests gets a plan of the untested scenarios, ordered by what a regression would cost, and writes only tests and the spec's anchors
- `feature-intake/` — interactive requirement gathering (Intake Sheet)
- `feature-spec/` — spec document production, with `scripts/check_spec.sh`, the structure check its quality check runs (bash and awk, nothing to install)
- `feature-scaffold/` — code and test generation rules: mirrors an existing feature of the project, with Riverpod/go_router/Dio templates as the fallback
- `feature-verify/` — conformance check: does the code still match the spec? It checks that each requirement's code anchor exists and each scenario's test passes, and dates the spec's `Last verified` line after a full pass. Runs at the end of Phase 2, or on its own ("verify the saved-articles spec")
- `feature-spec-compact/` — standalone spec maintenance (not part of the orchestrated chain): folds a spec's accumulated change records (changelogs, addenda, phased deltas, the workflow's bug-fix and refactor records, kept while their change isn't built yet) back into its base sections so only the current state remains, asking first whether the removed history should be extracted to `changelogs/<feature>/`, one file per compaction date, next to the spec

**Build & deploy** — releasing to the stores:

- `mobile-build-deploy/` — build-and-deploy in one flow, for Flutter and native SwiftUI apps: bumps version/build numbers and builds artifacts via the project's `scripts/build-version.sh` (installed on first use from the platform adapter, `platforms/<platform>/build-version.sh`, and adapted to the project), then hands the exact artifact paths to `mobile-store-deploy`
- `mobile-store-deploy/` — uploads already-built artifacts from any build (Flutter, native, React Native): iOS `.xcarchive` → TestFlight via native Apple CLIs, Android `.aab` → Play "Internal testing" via the Play Developer API (with an assisted Play Console browser fallback); iOS uploads sign in with Xcode's saved Apple ID, or with an App Store Connect API key for unattended runs; per-project config lives in the target project's `.mobile-store-deploy/`.

**Agents** — called only by `feature-workflow`, never on their own:

- `flutter-reviewer` and `security-reviewer` — second opinions in Phase 2's review, next to a built-in pass that checks the project's own conventions and the spec. The security pass runs when the change touches auth, requests, secrets, storage, permissions or deep links
- `dart-build-resolver` — fixes a codegen, l10n or analyzer failure the verification run couldn't fix in two attempts, using the same fvm-aware command
- `swift-reviewer` and `swift-build-resolver` — the same two roles for Swift: in a SwiftUI app, and for the Swift code a Flutter feature writes in `ios/`
- `kotlin-reviewer` and `kotlin-build-resolver` — the same two roles for Kotlin: in a Compose app, and for the Kotlin code a Flutter feature writes in `android/`

The seven are refined copies of agents from [ECC](https://github.com/affaan-m/ECC) (MIT), pinned to one upstream commit each; [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and `third_party/ecc/manifest.json` say what was taken and what changed. ECC itself isn't needed.

**Platform adapters** — what the feature workflow knows about Flutter sits in `platforms/flutter/`, apart from the skills: how the stack is detected, where reading a feature's code starts, the commands (through the fvm rule), the generation order, the code and test standards, the templates and the agents. The skills stay platform-neutral process, so another platform is a folder next to it. `platforms/swiftui/` is the second: native iOS apps with SwiftUI, built and tested with `xcodebuild` on a simulator (Xcode 16 or later), with Swift Testing tests. `platforms/compose/` is the third: native Android apps with Jetpack Compose, built with the project's Gradle wrapper and Android Lint (Kotlin 2.0.20, AGP 8.5.2 and JDK 17 or later), with JUnit 4 tests on the JVM and screen tests under Robolectric. Its tests are named like ``fun `saved-articles_1 Empty`()``, since a JVM method name can't hold the id's `.`. Compose has no build script yet, so `mobile-build-deploy` hands a bundle built in Android Studio or with Gradle to `mobile-store-deploy`. Invoke `/mobile-dev-skills:feature-workflow` the same way in any of these projects.

**Native code and permissions** — a feature that needs Swift or Kotlin code, a new permission or a capability gets it in the spec: section 4 lists each native interface (Pigeon or a platform channel) and each permission with its usage string, and section 6 tags behavior that differs per platform. Phase 2 writes the native side, the `Info.plist` and `AndroidManifest.xml` entries and the denial scenario's test, and builds each native project it touched. Each new iOS usage key also goes into `REQUIRED_USAGE_KEYS` of `scripts/build-version.sh`, in a Flutter or a SwiftUI app, which `mobile-build-deploy` checks against the specs before every iOS build. The SwiftUI adapter is the native adapter for iOS: it adds its Swift standards, `swift-reviewer` and `swift-build-resolver` for the Swift code. The Compose adapter does the same for Android's Kotlin code, with `kotlin-reviewer` and `kotlin-build-resolver`. Logic that must run without the Flutter engine, such as work in a background wake, gets native unit tests (Swift Testing in the Runner workspace's unit-test target, JUnit under `android/app/src/test/`), which the verification run and `feature-verify` run with the native adapter's commands; a platform this machine can't run is left as a manual check.

All skills live under `skills/`, the agents under `agents/` and the adapters under `platforms/`. The `Explore`, `Plan` and `general-purpose` subagents referenced by `feature-workflow` are built-in Claude Code agent types — nothing extra to install.

## Installation

Prerequisite: [Claude Code](https://claude.com/claude-code) v2.1.271 or later (the plugin's options use a fixed-choice picker, which older versions can't load).

### As a plugin (recommended)

```
/plugin marketplace add teaualune/mobile-dev-skills
/plugin install mobile-dev-skills@mobile-dev-skills
```

Plugin skills are namespaced, e.g. `/mobile-dev-skills:feature-workflow add a saved-articles screen`. Update later with `/plugin marketplace update mobile-dev-skills`, then `/plugin update mobile-dev-skills`. An install of `flutter-skills` doesn't update to this plugin: [MIGRATION.md](MIGRATION.md) says how to replace it.

To try this folder without installing anything into `~/.claude`:

```bash
claude --plugin-dir /path/to/this/folder
```

### Manual copy (no plugin)

Copy skill folders from `skills/` into the target project's `.claude/skills/` directory (create it if it doesn't exist), and `LICENSE` next to them. Run the commands from the folder that holds this README, in a checkout of the repository or in your plugin cache:

```bash
cd /path/to/this/folder
mkdir -p /path/to/your-app/.claude/skills
cp -R skills/* /path/to/your-app/.claude/skills/
cp LICENSE /path/to/your-app/.claude/
```

For the feature workflow and `mobile-build-deploy`, also copy the platform adapters next to `skills/`, and for the feature workflow the agents, which install under their bare names (`flutter-reviewer` rather than `mobile-dev-skills:flutter-reviewer`; `feature-workflow` accepts either):

```bash
cp -R platforms third_party /path/to/your-app/.claude/
mkdir -p /path/to/your-app/.claude/agents
cp agents/*.md /path/to/your-app/.claude/agents/
cp THIRD_PARTY_NOTICES.md /path/to/your-app/.claude/
```

The licenses travel with the copy, as both ask: `LICENSE` covers the skills, adapters and agents, and `THIRD_PARTY_NOTICES.md` reproduces ECC's license for the seven agents adapted from it. `third_party/` is the record of what was taken from ECC and changed, which the agents' notices cite.

The skills look for the adapters in the `platforms/` folder next to their own `skills/` folder, so a copy into `~/.claude/skills/` needs `platforms/` in `~/.claude/` too. Copy the folders rather than symlinking them, since that path is resolved from the link's location.

Copy only the family you need if you prefer — the feature workflow (six folders, plus the adapters and the agents) and the deploy pair (two folders, plus the adapters, which hold the build scripts) are independent, and `mobile-store-deploy` also works alone, e.g. in a React Native project. Commit `.claude/skills/`, `.claude/platforms/`, `.claude/agents/`, `.claude/third_party/`, `.claude/LICENSE` and `.claude/THIRD_PARTY_NOTICES.md` so the whole team gets the workflow. Copying into `~/.claude/skills/` instead makes them personal skills available in every project; project-level installation is preferred for teams.

To update a manual copy, delete what the earlier copy put in `.claude/` (the skill folders, `platforms/`, the agent files, `third_party/`, `LICENSE` and `THIRD_PARTY_NOTICES.md`), then copy again as above. A folder left behind from an older copy can answer the same requests as its new copy, or hold files that moved. A copy of `flutter-skills` has other folder names: [MIGRATION.md](MIGRATION.md) lists them.

Note for brand-new projects: the feature workflow detects the tech stack from existing code, and a fresh `flutter create` app has none of it yet. Either add your chosen packages (state management, routing, HTTP) to `pubspec.yaml` before the first feature, or accept the announced fallback stack (Riverpod + go_router + Dio + freezed) when the skill asks. A new Xcode app likewise gets the SwiftUI fallback (`@Observable` view models + `NavigationStack` + URLSession) and its templates. A new Android Studio app gets the Compose fallback: Hilt ViewModels with a `StateFlow` per screen, Navigation Compose with type-safe routes, and Retrofit + OkHttp + kotlinx.serialization. Each library the project doesn't have yet is added only after you approve it.

### Verify and use

1. Run `claude` in the project root (with `--plugin-dir` if testing a local checkout).
2. Type `/mobile-dev-skills:feature-workflow` (or `/feature-workflow` for a manual copy) — it should autocomplete. Invoke it with a feature description.
3. `feature-workflow` is the entry point; it orchestrates the intake → spec → scaffold → verify skills and the review agents automatically. `feature-spec-compact` sits outside that chain — invoke it (or let it auto-trigger on "compact the spec") when an existing spec has accumulated change history worth cleaning up.
4. For releases, ask to "build and deploy X.Y.Z to TestFlight/Play" (`mobile-build-deploy`) or, for an artifact that is already built, "upload the archive to TestFlight" (`mobile-store-deploy`).

## Per-project adjustments

### Feature workflow

`feature-workflow/SKILL.md` and the Flutter adapter contain a few example defaults that can be replaced with the target project's own conventions:

- Spec doc location/naming (e.g. `docs/specs/<feature-name>-feature-spec.md`, `docs/specs/artifacts/`) and API reference (e.g. `docs/api-reference.md`)
- Any language conventions the project enforces for spec documents
- Verification commands, in `platforms/flutter/PLATFORM.md` (e.g. `dart run build_runner build --delete-conflicting-outputs`, `flutter gen-l10n`, `flutter analyze`, `dart format`, `flutter test`); a form the project's CLAUDE.md or README documents wins

The skill discovers these conventions dynamically when they differ, so the bundle works as-is; hardcoding the target project's values just gives it better defaults.

A line in the project's CLAUDE.md that sends feature changes through the workflow starts it too, whether it names the skill (`/mobile-dev-skills:feature-workflow`) or says "the workflow" and the project has no workflow skill of its own.

Code and test rules come from `platforms/standards.md` and the adapter's own `standards.md` (e.g. no `!` null assertion in hand-written Dart, no force unwrap in Swift, no `!!` in Kotlin). A project adds its own, or replaces a bundled rule by naming it, in `.mobile-dev-skills/standards.md`; when you correct generated code for a reason that holds for every feature, the scaffold offers to add the rule there.

Beside its `## Code` and `## Tests` rules, that file may have a `## Workflow` part with two optional lines:

```markdown
## Workflow

Skills: tca-reference, swiftdata-reference
Pause after each task: yes
```

- `Skills:` names your project's own skills (a TCA or SwiftData reference, say). The scaffold, Phase 2's implementation subagents and a trivial change load them before writing code, and name them on their `Standards:` line, a skill that isn't installed included; the built-in review may load them as reference. Where a skill's advice differs from the standards, the standards win.
- `Pause after each task: yes` stops Phase 2 after each task: the workflow shows the task's files and test results, and waits for you to say go on. To pause for one run only, ask for it in the conversation. The verification run and the review don't pause.

The workflow keeps its state in the target project:
- `.mobile-dev-skills/` at the project root holds the confirmed tech stack, plus, per feature, the Intake Sheet, the Phase 2 task list and the run reports, which record each verification check as PASS, FAIL or SKIPPED;
- an `index.md` next to the specs lists each spec with its screens, its status and when it was last verified against the code.

Re-invoking `feature-workflow` on a feature resumes unfinished work where it stopped, and the saved stack skips re-detection until `pubspec.yaml` or `.fvmrc` changes (in a SwiftUI app, the project's deployment target, Swift version or packages; in a Compose app, the Gradle build files and the version catalog). Commit `.mobile-dev-skills/` to resume on another machine, or ignore it with the two `.gitignore` lines `.mobile-dev-skills/*` and `!.mobile-dev-skills/standards.md`, which keep your own standards file. The skills never edit `.gitignore` for it.

The skills read the plugin's own files (the adapters, the standards, the review checklist). In the default permission mode Claude Code asks before the first of those reads; allow it for the session, or add a `Read` allow rule for the plugin folder (e.g. `Read(~/.claude/plugins/cache/mobile-dev-skills/**)` for a marketplace install).

### Plugin options

Two rules are plugin options rather than discovered per project:

| Option | Default | Effect |
|---|---|---|
| `fvm_policy` | `auto` | How Flutter/Dart commands run, in the feature workflow and in `mobile-build-deploy`. `auto`: through `fvm` (`fvm flutter …`, `fvm dart …`) when the project has `.fvmrc` and `fvm` is installed, plain `flutter`/`dart` when neither, and ask first when only one of the two holds. `always`: always `fvm`. `never`: always plain. |
| `spec_language_rule` | `Chinese text must be Traditional Chinese (zh-Hant) only, never Simplified.` | Applied to all spec text the feature skills write or rewrite, including compaction; quoted user wording is kept as written. Empty = no rule. |

Change them in `/config` (one row per option) or with `claude plugin configure mobile-dev-skills@mobile-dev-skills`. Until a value is saved, the skills fall back to the defaults above. Manual copies get no option substitution and always use the defaults; to change one there, edit its fallback text in the copied `SKILL.md` files.

### Build & deploy

Project-specific values never live in the skills — they live in two places inside the target project, both created on first use:

- `scripts/build-version.sh` — copied from the platform adapter's `build-version.sh` and adapted via the `Project config — ADAPT` block at its top.
  - **Flutter** (`platforms/flutter/`): app name, flutter command — keep the default line unless the project needs one command pinned, flavors (an empty list for an app without them), each flavor's build arguments (its entry point and defines, when its release build needs them), scheme/configuration naming, iOS deployment-target fallback, required privacy usage keys. With the default line, `mobile-build-deploy` passes in the command its fvm rule decided, while a direct run always behaves like `fvm_policy` `auto` — the script can't read plugin options. It also expects pubspec.yaml to carry the version-bookkeeping convention: `version: <name>+<iosBuild>` plus a `# android: <androidBuild> = …` comment line for the Android versionCode.
  - **SwiftUI** (`platforms/swiftui/`): app name, the Xcode project (and workspace, if any), a scheme and a build configuration per flavor, where the version lives (`VERSION_SOURCE`: the project file, an `.xcconfig`, or `agvtool` for an older project with literal `Info.plist` versions), required privacy usage keys, and extra `xcodebuild` arguments (e.g. `-allowProvisioningUpdates`). It sets `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION`, reads them back before archiving, and checks the archived `Info.plist` after; it builds iOS only.
- `.mobile-store-deploy/` — deploy config (`ios.json` with ExportOptions overrides; `android.json` with the Play service-account key path, Play Console hints, and an optional `aabPathTemplate` for builds that don't write the `.aab` to Flutter's default location), created interactively by `mobile-store-deploy`'s setup mode. A `.flutter-store-deploy/` folder keeps working; it is read when it is the only one present. Safe to commit; the service-account key itself must live outside the repo. The one exception is the optional `ios-api-key.json` (an App Store Connect API key's `.p8` path, key ID and issuer ID, for uploads without Xcode's saved Apple ID): it is per machine and must be gitignored, which the upload script checks. On a CI machine, the `ASC_API_KEY_PATH`, `ASC_API_KEY_ID` and `ASC_API_ISSUER_ID` environment variables can replace it.

## Monorepos

A repository can hold an app beside other parts, each with its own folder and specs: say `backend/`, `web/` and a Flutter app in `app/`. The skills count it as a monorepo when another folder beside the app holds a part with its own manifest (`package.json`, `go.mod`, `pyproject.toml` and the like) or its own specs; one app in a subfolder beside docs or CI files isn't one. In a monorepo the skills treat the app's folder as the project root: its specs, its spec index and its `.mobile-dev-skills/` sit inside it, every command runs there, and nothing outside it is written, even in a session started at the repository's root.

A feature that spans the parts belongs to the project's own workflow, a skill you write for the repository: its intake, its split into parts, the other parts' specs and a root directory that links them. Asked directly for such a feature, `feature-intake` and `feature-workflow` name the parts it touches and point to that workflow, or offer to take the app's part alone. A request that only uses an existing endpoint is the app's own.

### Handing over the app's part

The parent workflow invokes `mobile-dev-skills:feature-workflow` (`feature-workflow` in a manual copy) with a **delegation brief**, which the user never types. The app's part then runs as a direct request does, from intake (asking only what the brief leaves open) through the approved spec, the code and its tests, the verification run and the review, with the user in the same conversation:

```markdown
# Delegation brief — Reading history
- Slug: reading-history
- From: the project's `cross-part-feature` skill
- Request: new feature
- App: app/
- Specs: app/docs/specs/
- API contract: backend/docs/specs/reading-history.md (draft)
- Approval: here

## App slice
A History tab lists the articles the user opened, newest first, by day; swiping one deletes it.

## Other parts
- backend: records each opened article; `GET /history`, `DELETE /history/{id}`
- web: none
```

- **Slug** is shared by every part, so the root directory can line their specs up. A new feature's app spec and state take it; a change, bug fix or refactor keeps the slug of the app feature it changes, and the brief's names the closing block. **Request** is `new feature`, `change`, `bug fix` or `refactor`; a request that only adds missing tests isn't delegated, so ask `feature-workflow` for it directly.
- **App** and **Specs** are paths from the repository's root; the spec folder must sit inside the app.
- **API contract** names the other parts' specs the app's requests come from, with their status. The app's spec states every shape it uses and cites the contract; shapes from a `draft` contract are marked provisional, with a list to confirm once that spec is approved.
- **Approval** is `here`, or `with the other parts`: the run then stops at the approval question, and the user approves every part's spec in one message that names each file, after which the parent invokes the skill again. A `draft` contract approved by then turns the app spec's provisional shapes into confirmed ones first, and the user approves that change.

The brief is saved beside the run's state, as `app/.mobile-dev-skills/<slug>/brief.md`, so the run resumes whether the parent invokes it again or the user types `/mobile-dev-skills:feature-workflow continue <slug>`. It applies until the run's spec is `implemented`; a later request on the feature without a new brief is a direct one. A large slice is split into sub-features, each with its own spec and state. Every reply that ends the run closes with a block the parent reads to update the root directory and the other parts:

```markdown
## Handoff — reading-history
- Spec: app/docs/specs/reading-history-feature-spec.md (index: implemented)
- Stage: implemented
- Verification: Codegen SKIPPED · l10n SKIPPED · Analyze PASS · Format PASS · Tests PASS · Native build SKIPPED · Conformance PASS
- Review: built-in — no findings · flutter-reviewer — 1 MEDIUM, fixed · security-reviewer — no findings
- Report: app/.mobile-dev-skills/reading-history/report.md
- Follow-ups:
  - backend: `GET /history` has no paging; the app shows the first 50 (reading-history.3)
  - manual: open History after reading an article, against a local backend
```

**Spec** and **Report** have a line per spec and run report the run wrote. **Stage** is `awaiting approval`, `implemented` or `stopped at Step <n> — <why>`. Checks that need another part running (device tests against a local server, end-to-end flows) come back as manual follow-ups.

### The root directory

A table at the repository's root, e.g. `FEATURES.md`, with a row per part of each feature. It links each part's spec and copies no status, since each part's own index and spec say where it stands:

```markdown
| Feature | Slug | Part | Spec |
|---|---|---|---|
| Reading history | reading-history | backend | [backend/docs/specs/reading-history.md](backend/docs/specs/reading-history.md) |
| Reading history | reading-history | app | [app/docs/specs/reading-history-feature-spec.md](app/docs/specs/reading-history-feature-spec.md) |
```

### A sample parent workflow

Not shipped as a skill: adapt it to the repository's parts and save it as `.claude/skills/cross-part-feature/SKILL.md` at the repository's root.

````markdown
---
name: cross-part-feature
description: Plan and build a feature that spans this repository's backend, web and app parts, with one spec per part. For "add X across the backend and the app". Do NOT use for a change that stays inside one part.
---

# Cross-part feature

Parts: `backend/` (specs in `backend/docs/specs/`), `web/` (`web/docs/specs/`) and `app/`, a mobile app built with the mobile-dev-skills plugin (`app/docs/specs/`). Root directory: `FEATURES.md`.

1. **Root intake.** Ask what the feature does for the user, then what each part does for it, one question per turn. Name the feature and choose its slug, lowercase kebab-case; every part's spec uses it.
2. **Split.** Show each part's slice, the requests between the parts, and the order: the backend first, since the others call it. Wait for the user to confirm.
3. **Backend.** Write `backend/docs/specs/<slug>.md`: each endpoint with its request and response shapes and its errors, and a `Status: draft` line under the title. Ask the user to approve it; on approval, the line says `approved`.
4. **Web.** <the web part's own steps>
5. **App.** Invoke the `mobile-dev-skills:feature-workflow` skill (`feature-workflow` in a manual copy) with this brief, and let it run with the user until its reply ends with `## Handoff — <slug>`:

   ```markdown
   # Delegation brief — <feature name>
   - Slug: <slug>
   - From: the project's `cross-part-feature` skill
   - Request: new feature
   - App: app/
   - Specs: app/docs/specs/
   - API contract: backend/docs/specs/<slug>.md (<its status>)
   - Approval: here

   ## App slice
   <the app's slice from step 2, under the Intake Sheet's headings where it fits>

   ## Other parts
   - backend: <its slice, one line>
   - web: <its slice, one line>
   ```

6. **Root directory.** Add a row per part to `FEATURES.md`, linking its spec, with no status.
7. **Follow-ups.** Show the handoff's follow-ups by the part they name, and list the manual checks for the user. Ask before changing another part's spec for one; an approved spec that changes goes back to `draft` until the user approves it again. To continue the app's part later, invoke the skill with the same brief.
````

## Related plugins

Four plugins by the same author, from two marketplaces of their own (`mobile-handytool-skills` and `mobile-compat`), cover what this one leaves out. A skill here offers its sibling only when that skill is listed in the session. When it isn't, the crash and submission mentions name the plugin once, with its install commands; the Figma mention tries its skill first and otherwise falls back as its intake rule says.

| Plugin | Repository | What it does | Where this plugin points to it |
|---|---|---|---|
| `crash-issue-fixer` | `teaualune/mobile-handytool-skills` | Crash, non-fatal and ANR reports from Crashlytics or any crash reporter: whether a crash still happens, its cause, and a fix after approval | `feature-workflow`'s bug fix, for a crash report without steps |
| `store-submission-prep` | `teaualune/mobile-handytool-skills` | A prefilled App Store Connect and Play Console submission sheet, with store copy for every listing language | `mobile-store-deploy`, after an upload or for the submission itself |
| `figma-design-to-artifact` | `teaualune/mobile-handytool-skills` | Figma frames exported through Chrome as reference code or a layer tree, with 2x screenshots | `feature-intake`, for Figma links, tried first when listed (on the user's yes) |
| `iphone-duo-ui-fix` | `teaualune/mobile-compat-skills` | An existing iOS or Flutter app's layout fixed for iPhone Duo's inner and outer displays | — |

```
/plugin marketplace add teaualune/mobile-handytool-skills
/plugin install crash-issue-fixer@mobile-handytool-skills
/plugin install store-submission-prep@mobile-handytool-skills
/plugin install figma-design-to-artifact@mobile-handytool-skills
/plugin marketplace add teaualune/mobile-compat-skills
/plugin install iphone-duo-ui-fix@mobile-compat
```

Two of them point back: `crash-issue-fixer` to `feature-workflow`'s bug fix, for a crash fix that changes what a spec states, and `store-submission-prep` to `mobile-build-deploy` or `mobile-store-deploy`, for a build that isn't uploaded yet.

## License

[MIT](LICENSE). The agents adapted from ECC keep ECC's MIT notice, in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Trademark and third-party disclaimers are in [DISCLAIMERS.md](DISCLAIMERS.md).
