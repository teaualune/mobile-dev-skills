# Roadmap

Future work for this plugin that isn't scheduled yet. Each top-level section is one area; each item says what it is, what it needs, and the decisions to take before starting. When an item is built, delete it here and describe the result in the plugin README and CLAUDE.md. Paths follow CLAUDE.md: `skills/`, `agents/`, `platforms/` and `third_party/` are in the plugin folder, `plugins/mobile-dev-skills/`; the rest are from the repo root.

## More platform adapters

The feature workflow reaches a platform through an adapter in `platforms/<name>/`, and the process skills never name a platform except as an example. Three adapters exist: Flutter; SwiftUI for native iOS apps; and Jetpack Compose for native Android apps. SwiftUI and Compose are also the native adapters for a Flutter project's `ios/` and `android/` folders. One candidate is left: **React Native**.

The test of the adapter contract: a new platform can be added by writing one `PLATFORM.md`, plus optional standards, templates and vendored agents, without touching the process skills (`skills/feature-*/`). "No process-skill edits" below means that. SwiftUI passed it. Compose needed one contract change first, now part of the contract: an adapter's own test-name form, with a **Test-name search** in its "Commands".

Kotlin Multiplatform / Compose Multiplatform is left out: it adds `expect`/`actual` source sets and Kotlin/Native to what the Compose adapter covers, and would start from that adapter.

### What every adapter needs

**Files**
- `platforms/<name>/PLATFORM.md` with the fourteen sections, in the order CLAUDE.md's "Platform adapters" contract lists them (Applies when … Native interop, Agents, Build adapter), carrying the labels in `maintenance/anchors.json`.
- `platforms/<name>/standards.md` with exactly `## Code` and `## Tests`. Optional, but the candidate below has rules that need it.
- A template set: optional. "Templates" may say `none`, leaving the project's own files as the only pattern source. A new project of that platform has no exemplar, though, so the scaffold would ask every time; SwiftUI and Compose shipped one for that reason.
- A build script, `platforms/<name>/build-version.sh`: optional. "Build adapter" names it or says `none`; the script keeps the build-adapter interface (CLAUDE.md, "build-version.sh interface"), and the checker's `build-interface` check finds it by its path.
- Two vendored ECC agents (reviewer, build fixer), pinned at `v2.2.3`: a manifest entry in `third_party/ecc/manifest.json` with `upstream_body_sha256` and `modifications`, the three notice comments, and an `## Inputs from feature-workflow` section. Read each upstream file first: some ECC agents target web or server code rather than mobile.

**Checker** (`maintenance/anchors.json`)
- `adapter-text` exact pins for the adapter, its standards, its templates and the agents' Inputs sections.
- `vendored.agents` entries with the exact descriptions and modification counts.
- `mentions` rules that keep the new platform's words (tool names, test APIs, file patterns) out of `skills/feature-*/`.

**Docs and counts**
- Agents go from seven to nine in the plugin README and CLAUDE.md (the `counts` anchors), and the plugin description in `plugin.json` and `marketplace.json` names the new platform.
- The agent descriptions are listed on every turn for every plugin user. The seven use 766 of the 800-character `agent_description_budget_chars`, so two more need another deliberate budget raise.

**Proof**
- A fixture project and live runs, as for SwiftUI and Compose: `feature-verify`, a trivial request, a Phase 2 run with a project standards file, and a hybrid run where the adapter is a native adapter.

**Decisions before starting**
- **Build adapter in scope or not.** `mobile-build-deploy` reads the adapter's "Build adapter" section (Template, Platforms, Version bookkeeping, Command, Setup, Artifacts), so a build needs no skill edit: write the script and fill the section. Without one, the section's Template says `none`, and the skill offers `mobile-store-deploy` alone for artifacts built another way. Either way the script keeps the build-adapter interface (CLAUDE.md, "build-version.sh interface"), so `mobile-store-deploy` needs no change.
- **Template set or none** (above).

**Where the process skills may still be touched.** Each one is a finding about the adapter contract, not a failure of the adapter.
- **Command options.** `fvm_policy` is Flutter's. An adapter whose command rule needs a user setting adds a `userConfig` key and a line in each skill that runs commands. React Native shouldn't need one.
- **Test naming.** The common **Name** rule needs a description starting with `<id> <Scenario title>`, as one plain string literal or in the name form an adapter's standards give where its test names can't hold the description's characters (Compose's backtick names). `feature-verify` finds tests with the adapter's **Test-name search**. Jest fits as a literal.
- **Applies when.** Flutter and React Native projects contain `ios/` and `android/` native projects. A native adapter's "Applies when" must exclude those folders, or every Flutter run would ask which adapter to use; SwiftUI's and Compose's already exclude both frameworks' folders. A native adapter reaches those folders through `**Native adapter for:** <platform>` in its "Native interop", and a hybrid run adds its "Standards" and "Agents" to the native files it writes there.

### React Native (TypeScript)

**Applies when** — a `package.json` whose `dependencies` include `react-native`, in the working directory or a folder below it. Expo projects also list `expo`. Ask when several qualify (a monorepo with several apps). It doesn't overlap Flutter's `pubspec.yaml`, and SwiftUI's and Compose's "Applies when" already leave this project's `ios/` and `android/` alone.

**Why it is the cleanest test of the contract** — Jest names fit the **Name** rule as literals, the command rule is deterministic, its "Applies when" overlaps no existing adapter, and its native folders can reuse SwiftUI and Compose as native adapters after a wording change in those adapters and their agents. Effort M. Toolchain on the maintainer's machine (2026-11-16): Node 22, npm, pnpm, yarn.

**Project layout**
- Root: the folder holding that `package.json`.
- Manifest: `package.json`; the lockfile decides the package manager; `app.json` / `app.config.*` for Expo.
- Source: `src/`, or `app/` for Expo Router routes; found by the probes.
- Host tests: wherever Jest's `testMatch` finds them (`__tests__/` or co-located `*.test.tsx`); Jest runs in Node. Device tests: `e2e/` (Detox) or `.maestro/`.
- Generated files: `ios/` and `android/` when Expo prebuild generates them (gitignored), GraphQL or OpenAPI codegen output, `.expo/`.
- Fingerprint: `package.json` and `app.json` without their `"version":`, `"buildNumber":` and `"versionCode":` lines, through `git hash-object --stdin`.

**Stack layer**
- Language: TypeScript (`tsconfig.json`) or JavaScript.
- Client state: Redux Toolkit, Zustand, Jotai, MobX, React Context.
- Server state: TanStack Query, RTK Query, SWR, Apollo.
- Navigation: Expo Router, React Navigation, react-native-navigation.
- HTTP: fetch, axios, ky. Validation: zod, valibot.
- Styling: StyleSheet, NativeWind, Tamagui, Restyle, styled-components.
- i18n: i18next, lingui, react-intl.
- Test packages: Jest (`jest-expo` preset), `@testing-library/react-native`, MSW; Detox or Maestro on devices.
- Fallback: TypeScript; Expo Router with Expo, otherwise React Navigation's native stack; TanStack Query + fetch; Zustand for client state; Jest + React Native Testing Library with hand-written fakes.

**Convention probes** — folder layout (`src/features/<name>/`, or by type: `screens/`, `components/`, `hooks/`, or Expo's `app/`); one exemplar feature end to end (type, API module, query hooks or slice, screen, test); the navigation setup (root navigator, `RootStackParamList`, linking config for deep links); theme tokens; i18n setup; import style (`@/` aliases from `tsconfig` `paths` vs relative); test setup (`jest.config`, `jest.setup`, a render helper that wraps providers).

**Detection report** — Language, Client state, Server state, Navigation, HTTP client, Validation, Styling, i18n, Test packages, and `Package manager: <pm> (<reason, e.g. "pnpm-lock.yaml">)` as the command line.

**Code entry points** — Routes: Expo Router's `app/` files, or React Navigation's navigators (`createNativeStackNavigator`, `<Stack.Screen>`) and the linking config. Links: the hooks and stores a screen uses (query hooks, Redux slices, Zustand stores), then the API module, then the types. App-wide: `App.tsx` or `app/_layout.tsx` with its providers. A native module chain ends in `ios/` or `android/`. Tests: `__tests__/` folders or `*.test.tsx` beside the file.

**Commands**
- Command rule: the `packageManager` field in `package.json` wins; otherwise the lockfile (`package-lock.json` → npm, `yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm, `bun.lock` / `bun.lockb` → bun); several lockfiles → ask; none → npm. Binaries run through `<pm> exec` (`npx` for npm). Deterministic, so no plugin option.
- Checks:

  | Check | Command | Runs when |
  |---|---|---|
  | Codegen | the project's codegen script (e.g. `graphql-codegen`) | the project defines one and its inputs changed |
  | l10n | the project's i18n compile script (e.g. `lingui compile`) | the project defines one and message files changed |
  | Analyze | `tsc --noEmit`, then `eslint <files>` when ESLint is configured | always |
  | Format | `prettier --check <files>` (or `biome check` with Biome) | the project configures a formatter and files were written |
  | Tests | `jest` (or the `test` script) | the project has Jest configured |
  | Native build | `xcodebuild` on `ios/` after `pod install`, and `./gradlew assembleDebug` in `android/` | a run touches `ios/` or `android/`, or adds a package with native code |

- Test-name search: `grep -F -e "'<description>'" -e '"<description>"' <file>`. Anchored tests: `jest --verbose <files>`, one line per test with its description and result. Snapshot update: `jest -u -t '<description>' <file>`. Device tests: `detox test` or `maestro test`, run by hand.

**Generation order** — 1. types (and zod schemas); 2. API module / repository, then its tests; 3. server-state hooks and client stores, then their tests; 4. shared components; 5. screens: skeleton with route params, data hook, Loading, Error with retry, Empty, Success, actions, then the screen's RNTL tests; 6. navigation: register the screen and its param type (React Navigation) or add the route file under `app/` (Expo Router, where the file is the route, so this merges with step 5) plus the linking config for deep links; 7. native modules and platform declarations, when the spec's section 4 lists them; 8. edits to existing screens, with their tests.

**Spec notation** — §2 `### Routing wiring (Expo Router)` or `(React Navigation)`, with typed params; §3 each screen with its file; §4 a TypeScript type sketch, the HTTP client and query library, and native interfaces ranked: an existing package, an Expo Module or Turbo Module, else a new dependency the user approves; §5 heading names the library, with a TanStack Query table (Query key | Hook | Fetches | Invalidated by) or a store table (Store/slice | State | Actions | Notes); §7 i18n keys and locale files; §10 test kinds: Unit (Jest: API, hooks, stores), Component (RNTL: screen states and actions), Snapshot (only where the project uses them), E2E (Detox / Maestro, on a device). Platform tags: `ios`, `android`.

**Native interop** — Platforms: `ios` and `android`. Native adapter for: `none`. Mechanism: Expo Modules API in Expo projects, Turbo Modules (with Codegen specs) in bare ones. Declarations: `app.json` config plugins and `infoPlist` / `android.permissions` in Expo; `Info.plist` and `AndroidManifest.xml` in bare projects. The SwiftUI adapter is the native adapter for `ios` and the Compose adapter for `android`, but their native-adapter text assumes a Flutter host:
- in each `PLATFORM.md`, the Native build note under "Commands", the "Standards" section and `Native adapter for:`;
- the scope line of each `standards.md`, and their Flutter channel rules;
- the Inputs sections of `swift-reviewer`, `swift-build-resolver`, `kotlin-reviewer` and `kotlin-build-resolver`, whose build fixers are given "its Flutter command".

Generalizing them to "a Flutter or React Native project", with React Native's native build commands for the build fixers, is part of this adapter's work: new `adapter-text` pins and ECC manifest modification records.

**Standards**
- Code: no `any` (`unknown` and narrowing) and no non-null `!`; no `@ts-ignore`; unbounded lists through `FlatList` / `FlashList`, not `ScrollView` + `map`; pull to refresh through `RefreshControl`; styles through the project's system and theme tokens, no literals; user-visible strings through i18n, in every locale file; `testID` or accessibility labels on interactive elements; a provisional stub's delay is `await new Promise((r) => setTimeout(r, 400))`.
- Tests: Form: `it('saved-articles.1 Empty', …)` or `test(…)`; a `describe` may group tests, but the `it` string carries the whole `<id> <title>`. Unescaped titles: single quotes, double quotes when the title holds an apostrophe, never a template literal. Host tests: the Jest suites; Detox and Maestro need a device. Native modules are faked behind their TypeScript interface.

**Templates** — optional: `expo-router-tanstack-query/` with `types.ts`, `api.ts`, `api_stub.ts`, `queries.ts`, `screen.tsx`, a route file and `screen.test.tsx`.

**Agents** — reviewer: read `react-reviewer` and `typescript-reviewer` at `v2.2.3` and take the one that covers React Native, not only web React. Build fixer: `react-build-resolver`, if it covers Metro, CocoaPods and Gradle errors rather than only web bundlers. ECC reference material: `rules/react-native/` and the `react-native-patterns` skill.

**Build adapter** — none in the first cut (Template `none`). Later: a `build-version.sh` for bare React Native or Expo prebuild that bumps `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` and `versionName` / `versionCode` (or `app.json` before prebuild), archives `ios/*.xcworkspace` after `pod install` and runs `./gradlew bundleRelease`, with the build-adapter interface's flags, printed lines and manifest keys. The SwiftUI script's version modes and its read-back and archive checks are the iOS half to start from. EAS cloud builds produce an `.ipa`, which `mobile-store-deploy` doesn't take: out of scope.

**Risks and open questions** — `tsc` time on large projects; monorepo workspaces ("Applies when" asks); Jest presets differ between Expo and bare; an Expo project with generated (gitignored) native folders edits config plugins rather than `ios/`, so its Native build needs a prebuild first.

**Fixture** — `create-expo-app` (TypeScript) with one small feature; a bare `@react-native-community/cli init` project for the native interop and, if in scope, the build adapter.

## Build adapters

`mobile-build-deploy` builds through an adapter's `build-version.sh` (CLAUDE.md, "build-version.sh interface"). Flutter and SwiftUI have one; Compose doesn't yet.

### Jetpack Compose (native Android)

The Compose adapter's "Build adapter" says `none`, so a native Android release is built in Android Studio or with Gradle and handed to `mobile-store-deploy` alone.

**The script** — an Android-only `build-version.sh` in `platforms/compose/` that:
- bumps `versionCode` / `versionName` where the project keeps them: the module build file, the version catalog or `gradle.properties`;
- runs `./gradlew :<module>:bundle<Flavor>Release`, and writes `ANDROID_AAB_PATH` to the artifact manifest;
- exits as not applicable on `-i`, as the SwiftUI script does on `-a`. "Platforms" names `-a` and says "`-i` doesn't apply", as the checker requires.

**Decide when it is taken up** — where the version lives (the ADAPT block's equivalent of SwiftUI's `VERSION_SOURCE`), reading the version back from the built bundle (`bundletool dump manifest`), and the signing config the release build expects (the project's own, never one the script writes).

**Fixture** — the Compose adapter's fixture app with a release signing config and one product flavor.
