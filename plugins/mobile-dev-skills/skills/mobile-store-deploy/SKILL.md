---
name: mobile-store-deploy
description: Upload already-built app artifacts to the stores — an iOS .xcarchive to TestFlight, an Android .aab to Google Play internal testing — from any framework, or set up deploy config ("set up store deployment"). For a review submission, names a plugin. Never builds; for build plus deploy use mobile-build-deploy.
---

# mobile-store-deploy

Ships **already-built** iOS/Android artifacts, whatever produced them — Flutter, native Xcode/Gradle, React Native. Building is the caller's job (e.g. the `mobile-build-deploy` skill or the project's own build script); this skill only uploads a `.xcarchive` and/or `.aab`. The store submission (What's New, the listing, privacy labels, app review) isn't an upload either: see "Store submission" under the Output contract.

- **iOS** → TestFlight (App Store Connect) via `xcodebuild -exportArchive`. Native Apple CLI only.
- **Android** → Play Console "Internal testing" track:
  - **Phase 1 (primary):** Google Play Developer API v3 (plain `curl` + JWT signing). Streams the `.aab` from disk with no size ceiling — the only path that can complete an Android deploy unattended.
  - **Phase 2 (assisted fallback):** Claude in Chrome automation of the Play Console website. **Cannot complete the upload on its own** — see the size limit below.

> **Phase 2 cannot upload a real release bundle unaided.** The `file_upload` browser tool caps a call at **10 MB combined** and only accepts paths the user has shared with the session; a release `.aab` is typically 50–200 MB. Phase 2 therefore drives navigation and the surrounding steps, then **hands the file drop to the user** and resumes. Treat Phase 1 setup as the default recommendation for any project that will release more than once.

Run all scripts from the project root so relative config paths resolve: the app's own folder, which in a monorepo isn't the repository's root.

## Inputs (per invocation)

Extract from the user's request; ask when unclear — never guess:

| Input | Values | Default |
|---|---|---|
| platform | `ios` \| `android` \| `both` — the caller decides; single-platform deploys are fully supported | — (required) |
| app identifier | iOS bundle ID / Android package name; a project alias is OK if resolvable | — (required) |
| version selector | `latest`, or explicit version (+ optional build number) | `latest` |
| artifact path | explicit `.xcarchive` / `.aab` path | discovered (below) |

Alias resolution: an app or flavor name may be resolved to the concrete ID via project sources — the `<config>/` files (`provisioningProfiles` keys, `appNames`), Xcode project settings, the Android `applicationId` (+ flavor suffix) in the Gradle build file, or the archive listing from `ios_find_archive.sh`. If more than one plausible ID remains, list them and ask.

Default artifact locations:

- `.xcarchive`: `~/Library/Developer/Xcode/Archives/{yyyy-MM-dd}/{name} {yyyy-MM-dd} {HH.mm.ss}.xcarchive` (scanned by `ios_find_archive.sh`)
- `.aab`: the `AAB_PATH_TEMPLATE` printed by `android_phase_select.sh` — `android.json`'s `aabPathTemplate`, else the Flutter default `build/app/outputs/bundle/{flavor}Release/app-{flavor}-release.aab`

When the caller already provides exact artifact paths — e.g. the `mobile-build-deploy` skill, which captures them from `scripts/build-version.sh` build output and verifies them on disk, with their ID and version where it can read them — use those paths directly and skip discovery entirely.

## Per-project configuration (`.mobile-store-deploy/`)

Optional directory at the project root. When a deploy needs a file that is missing, **Setup mode** (below) creates it interactively. See `${CLAUDE_SKILL_DIR}/templates/project-config.example.json` for the file shapes. Safe to commit, apart from `ios-api-key.json` — it contains paths and names, never secrets (the service-account key and the API key themselves must live **outside** the repo).

**Resolve the config directory once per run**, and use it as `<config>` in every path below:

- `.mobile-store-deploy/` exists → use it.
- Only `.flutter-store-deploy/` exists → use it as is. It is this skill's pre-rename config name (v0.2.0's) and stays supported. Mention it once and offer to rename it to `.mobile-store-deploy/` — `git mv` when the folder is tracked, plain `mv` when it isn't; never move it unasked. If the user accepts, `<config>` is `.mobile-store-deploy` for the rest of the run.
- Both exist → stop and ask which one is current; never merge them.
- Neither, but another folder at the project root holds an `ios.json` or `android.json` (`ls -d .*deploy*/`, or the folder the project's CLAUDE.md names for deploy config): show it and ask whether to use it as `<config>`, after reading its files against the keys below, or to create `.mobile-store-deploy/`. Never create a second config beside it unasked.
- Neither, and no such folder → `<config>` is `.mobile-store-deploy`; Setup mode creates files there.

Files:

- `ios.json` — **verbatim ExportOptions.plist keys** (e.g. `signingStyle`, `provisioningProfiles`, `teamID`, `signingCertificate`), deep-merged over `${CLAUDE_SKILL_DIR}/templates/ExportOptions.default.plist`; project value wins. A minimal automatic-signing project needs only `{"signingStyle": "automatic"}`.
- `android.json` —
  - `serviceAccountKeyPath` (optional, but **strongly recommended**): path to a Play service-account JSON key. Absent ⇒ Phase 2, which cannot upload a >10 MB bundle without the user dropping the file in by hand.
  - `aabPathTemplate` (optional): where the build writes the `.aab`, relative to the project root, with `{flavor}` standing for the flavor name. Default: `build/app/outputs/bundle/{flavor}Release/app-{flavor}-release.aab` (Flutter with flavors). Other common shapes: native Gradle `app/build/outputs/bundle/{flavor}Release/app-{flavor}-release.aab`; React Native `android/app/build/outputs/bundle/release/app-release.aab`; a flavorless Flutter app `build/app/outputs/bundle/release/app-release.aab`.
  - Phase 2 hints: `developerId` (number-only string used in the Console URL), `teamName`, `appNames` (map of flavor → Play app display name).
- `ios-api-key.json` (optional) — an App Store Connect API key for unattended iOS uploads: `keyPath` (the `.p8` file, best kept outside the repo), `keyID`, `issuerID`. It is per developer or per CI machine and **never committed**: `ios_upload.sh` refuses it (exit 4) unless git ignores it, and refuses a key file inside the project that git doesn't ignore. The two IDs are identifiers, not secrets; the script prints them. The environment's `ASC_API_KEY_PATH`, `ASC_API_KEY_ID` and `ASC_API_ISSUER_ID`, all three set, take its place, as on a CI machine. Without either, uploads use the Apple ID session saved in Xcode.

## Setup mode

Entered two ways:

- **Explicitly:** the user asks to set up / configure store deployment for the repo ("set up mobile-store-deploy", "configure store deploy config").
- **Implicitly:** a deploy needs a config file that does not exist — iOS with no `<config>/ios.json`, or Android with no `<config>/android.json`.

Setup covers only the platform(s) in scope — an iOS-only deploy never asks Android questions. After an implicit entry, continue straight into the deploy that was interrupted; after an explicit setup-only request, end with the validation report and offer to deploy (don't start one unasked).

### iOS walkthrough → `ios.json`

`ios.json` is effectively required: the template deliberately carries no `signingStyle`, so an iOS deploy cannot proceed without the file. Ask the user:

1. Signing style — `automatic` or `manual` (the same choice as in the Organizer wizard)?
2. If `manual`: `teamID`, `signingCertificate` (usually `Apple Distribution`), and the `provisioningProfiles` map (bundle ID → profile name) for every target — taken verbatim from the user, never guessed.
3. Any other ExportOptions overrides (rare; the template already sets `uploadSymbols=true`, `manageAppVersionAndBuildNumber=false`).
4. Uploads without Xcode's saved Apple ID session (unattended, or on a CI machine)? Only then: a team API key from App Store Connect (Users and Access ▸ Integrations), with the App Manager role (automatic signing that has to create a distribution certificate may need Admin). Ask for the `.p8` path (best outside the repo), the key ID and the issuer ID, and whether they come from the environment (above) or `<config>/ios-api-key.json`. For the file, `git check-ignore -q <config>/ios-api-key.json` must succeed first: if it fails, offer to add that path to `.gitignore`, and write the file only once it is ignored.

Write the answers to `<config>/ios.json` (verbatim ExportOptions keys only) and, when chosen, `<config>/ios-api-key.json`, and show the user the files — the API key file with its path values only.

**Validate** with the upload dry-run, using the archive already selected for this deploy (or, for standalone setup, any archive located by `ios_find_archive.sh`):

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/ios_upload.sh" --archive "<archive>" --project-config "<config>/ios.json" [--api-key-config "<config>/ios-api-key.json"] --dry-run
```

Exit 0 with the expected merged plist and `-- auth --` line ⇒ valid. Exit 4 ⇒ fix the file with the user and re-validate. If no archive exists yet (standalone setup on a fresh machine), at minimum confirm the JSON parses and the signing keys are present, and say that full validation happens on the first deploy.

### Android walkthrough → `android.json`

Ask the user:

1. Is there a Play service-account key (enables Phase 1)? Yes → its path (must live **outside** the repo). No → **recommend the one-time setup rather than presenting it as optional**: point them at the "One-time Google Play API setup" section and explain that without a key every Android release needs a manual file drop, because Phase 2 cannot upload a bundle over 10 MB. They may still decline and rely on assisted Phase 2.
2. Where the build writes the `.aab` — only when it differs from the Flutter default (native Gradle, React Native, a flavorless app): infer the shape from the project layout, confirm it with the user, and set `aabPathTemplate`.
3. Phase 2 hints — worth filling in even when a key exists, as fallback data: `developerId` (the number-only string from the Play Console URL), `teamName`, `appNames` (flavor → Play app display name).

Write `<config>/android.json` and show the user the file.

**Validate:**

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/android_phase_select.sh" --config "<config>/android.json"
```

Exit 4 ⇒ invalid config: fix and re-validate. `SERVICE_ACCOUNT_KEY_ERROR` ⇒ wrong key path: fix and re-validate. Otherwise confirm the resolved `PHASE`, `AAB_PATH_TEMPLATE` and hints with the user.

`android.json` is optional by design — if the user declines setup, proceed with assisted Phase 2, the default `.aab` location and no hints, but say so, and state that the file drop will be theirs to perform.

## Hard rules

1. **Fail loud.** Any ambiguity — multiple matching archives/AABs, missing signing config, unexpected wizard/API/page state — means STOP, show the findings, and ask. Never guess a signing identity, team, or version.
2. **Secrets:** never print key file contents or tokens; reference key files by path only. The scripts already behave this way — do not `cat` key files yourself. Never commit `ios-api-key.json` or a key file, and never pass `--api-key-config` for a file git doesn't ignore.
3. **Idempotency:** re-running with an already-uploaded build ⇒ surface the store's duplicate error verbatim (ASC: redundant binary / "bundle version must be higher"; Play: "Version code … has already been used"). Never auto-bump versions or rebuild.
4. **Phase 2 rollout pause:** the final rollout click in Play Console is an irreversible publish — pause and get explicit user confirmation in chat before clicking, **every run**. That one confirmation also covers the Console's publish dialog the click opens (Phase 2 step 9). Phase 1 needs no such pause.
5. **No fastlane. No Xcode GUI scripting.** Browser automation only as Android Phase 2.
6. **Platform scope is exactly what the caller chose** — `ios`, `android`, or `both`. A single-platform run never touches the other platform's config, artifacts, or setup questions. `both` runs the two platforms in parallel (see below).
7. Every run ends with the summary block from the Output contract section.

## iOS procedure

1. **Find the archive** (skip if the caller supplied an explicit path):

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/ios_find_archive.sh" --bundle-id <id> [--version X.Y.Z] [--build N] [--archives-dir DIR]
   ```

   - exit 0 → parse the `ARCHIVE_PATH` / `VERSION` / `BUILD` / `CREATION_DATE` lines
   - exit 2 (ambiguous) or 3 (no match) → relay the candidate list from stderr to the user, stop, ask.

2. **Upload:**

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/ios_upload.sh" --archive "<path>" [--project-config "<config>/ios.json"] [--api-key-config "<config>/ios-api-key.json"]
   ```

   If `<config>/ios.json` does not exist, enter **Setup mode** first — the upload cannot proceed without `signingStyle`. Pass `--project-config` whenever the file exists, and `--api-key-config` whenever `<config>/ios-api-key.json` does. The script deep-merges it over the template, validates the result (`method=app-store-connect`, `destination=upload`, `signingStyle` present; `manual` ⇒ `provisioningProfiles` present), prints the effective ExportOptions, then runs `xcodebuild -exportArchive`, streaming output.

   - `-allowProvisioningUpdates` is added only when `signingStyle=automatic` — never for `manual`.
   - `--dry-run` merges, validates, and prints the exact `xcodebuild` command without uploading.
   - exit 4 = config problem (e.g. missing `signingStyle`): relay the message and ask the user for the values. Never guess.

3. **Auth**, which the script's `-- auth --` line names: the App Store Connect API key when the environment or `ios-api-key.json` configures one (passed as `-authenticationKeyPath`, `-authenticationKeyID` and `-authenticationKeyIssuerID`), else the Apple ID session saved in Xcode (Settings ▸ Accounts) — the same session the Organizer wizard uses. Sign-in errors ("No accounts", session expired) with the session: ask the user to sign into Xcode and re-run. With a key, an authentication or permission error: report it and check the key's role with the user; never fall back to the other method silently. Never script the login.

4. Duplicate build → rule 3 above (report verbatim, don't bump).

## Android procedure

1. **Phase selection:**

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/android_phase_select.sh" --config "<config>/android.json"
   ```

   Prints `PHASE=1` (+ `SERVICE_ACCOUNT_KEY=…`) or `PHASE=2` (+ hints `DEVELOPER_ID`, `TEAM_NAME`, `APP_NAME_<flavor>`), and always `AAB_PATH_TEMPLATE`. Exit 4 ⇒ invalid config: relay the message, fix the file with the user, re-run; any other non-zero exit ⇒ stop and report. If `SERVICE_ACCOUNT_KEY_ERROR` appears (key configured but missing/unreadable — likely a bad path), surface it and confirm with the user before continuing to Phase 2. If the file is missing entirely for an Android deploy (`CONFIG_PRESENT=0`), enter **Setup mode** first; the user may decline it and continue hint-less with Phase 2.

2. **Locate the `.aab`** (skip if the caller supplied a path): `AAB_PATH_TEMPLATE` with `{flavor}` replaced by the flavor from the request/config (ask when the template needs a flavor and none is known). Missing file or multiple candidates → list findings, ask. If an explicit version was requested, verify the file really is that version (`bundletool dump manifest --bundle <aab>` if bundletool is available; otherwise report the file's mtime/size and confirm with the user).

3. **Phase 1:**

   ```bash
   bash "${CLAUDE_SKILL_DIR}/scripts/android_phase1_upload.sh" --package <pkg> --aab <path> --key <key.json>
   ```

   Internally: service-account JWT → OAuth token → `edits.insert` → `edits.bundles.upload` → `edits.tracks.update` (track `internal`, `status: completed`, **no releaseNotes**) → `edits.commit`.

   - exit 0 → released; no confirmation pause for Phase 1
   - exit 42 → auth/permission failure (HTTP 401/403): read the response the script printed above it. A 403 whose message names a Console declaration or policy form (e.g. "You must let us know whether your app includes any health features", or a Data safety, ads or app-content question) is a Console blocker, not a credential problem, and the browser route would stop at the same place: stop, quote the message and name the form the account owner completes in the Play Console (Policy and programs ▸ App content), then run again once it is done. Any other 401/403 (a key Google refuses, a missing permission, an app the account can't see): announce the fallback and run Phase 2
   - any other non-zero exit → **STOP and report. Do not fall back to Phase 2.**

4. **Phase 2 — Claude in Chrome** (only when the key is missing or Phase 1 exited 42):

   Preconditions to check and announce **before driving any pages**:
   - The Claude-in-Chrome extension is connected — verify with `list_connected_browsers`. An empty list means the extension is not reachable even if the `mcp__claude-in-chrome__*` tools loaded; `claude --chrome` exposes the tools but does not connect the extension. Stop and have the user install it from `claude.ai/chrome`, sign into claude.ai with the same account as Claude Code, restart Chrome, and grant site permission for `play.google.com`.
   - The user is already signed into the correct Google account in Chrome. The skill **never** performs Google login or handles credentials — if signed out, stop and ask the user to sign in first.
   - **Check the `.aab` size up front.** Over ~10 MB (i.e. essentially always) the file drop in step 6 must be done by the user. Say so *before* starting, so they can choose Phase 1 setup or a fully manual upload instead of being surprised mid-flow.

   Click path:
   1. Navigate to `https://play.google.com/console` — or directly to `https://play.google.com/console/u/0/developers/{DEVELOPER_ID}` when the developer ID is configured
   2. If an account/team chooser appears, select the team matching `TEAM_NAME`
   3. Open the app matching the package name / `APP_NAME_<flavor>`
   4. Sidebar: Testing ▸ Internal testing
   5. Click "Create new release"
   6. **Upload the `.aab` — user-assisted whenever it exceeds 10 MB.** `file_upload` is capped at 10 MB per call, so for a normal release bundle the agent cannot attach the file. Stop on the upload screen, give the user the absolute artifact path, and ask them to drag it into the drop zone themselves. Resume once the Console shows the bundle attached. Only attempt `file_upload` directly when the artifact is genuinely under 10 MB **and** its path was shared with the session; never present the hand-off as a failure — it is the documented Phase 2 behavior.
   7. Wait for upload and processing to finish
   8. Skip release notes (leave empty)
   9. Next → review → **STOP before the final rollout/confirm button. Ask the user in chat to confirm the rollout, and only click after explicit confirmation. Every run, no exceptions.** That button (e.g. "Save and publish") opens the Console's own confirmation dialog (e.g. "Publish changes on Google Play?"), which is part of the same rollout: ask once, before the button, then confirm the dialog without asking again. When the dialog lists more than this release (another track, store listing changes, other pending changes), stop, describe them and ask, since confirming would publish those too.

   Any other unexpected page state (error banners, extra dialogs beyond step 9's, changed UI) → pause, describe what is on screen, ask.

5. Duplicate version code (HTTP 400 "Version code … has already been used", or the equivalent Console error) → rule 3 (report verbatim, don't bump).

## `both` platforms — run in parallel

The iOS upload and Android Phase 1 are non-interactive: launch them concurrently (e.g. two background Bash invocations), collect both results, and emit one combined summary. If Android falls back to Phase 2 (interactive browser), start the iOS branch in the background first, then drive Chrome.

## GUI ↔ CLI validation table (iOS)

Every step of the manual Organizer flow maps to a script/CLI equivalent. Steps with **no** CLI mapping are flagged explicitly — never silently approximated.

| # | GUI step (manual Organizer flow) | CLI/script equivalent |
|---|---|---|
| 1 | Quit & relaunch Xcode | **N/A — intentionally unmapped.** Relaunching only forces the Organizer UI to re-scan the archives folder; the CLI reads `~/Library/Developer/Xcode/Archives/` directly from disk on every run, so there is nothing to refresh. |
| 2 | Open Window ▸ Organizer ▸ Archives | `ios_find_archive.sh` scans the archives directory |
| 3 | Pick the app in the left-hand app list | `--bundle-id` filter against each archive's `Info.plist` → `ApplicationProperties.CFBundleIdentifier` |
| 4 | Select the fresh (or requested) archive row | `latest` → newest `CreationDate`; explicit → `CFBundleShortVersionString` (+ `CFBundleVersion`) match; ambiguity/no match → stop and list candidates |
| 5 | Distribute App → Custom → App Store Connect → Upload → distribution options (upload symbols; manage version & build; signing style; if manual: distribution certificate + provisioning profile per target) | Merged ExportOptions plist consumed by `xcodebuild -exportArchive` in `ios_upload.sh`: `method=app-store-connect`, `destination=upload`, `uploadSymbols=true`, `manageAppVersionAndBuildNumber=false`, `signingStyle`, and (when manual) `signingCertificate` + `provisioningProfiles` + `teamID` |
| 6 | Apple ID sign-in + final "Upload" click | The App Store Connect API key's `-authenticationKey…` flags when configured, else Xcode's saved account session; `-allowProvisioningUpdates` added only when `signingStyle=automatic`; success = exit 0 with `EXPORT SUCCEEDED` in the streamed output, and ASC processing warnings from the output are surfaced |

## GUI ↔ API ↔ Chrome mapping table (Android)

| # | Play Console GUI step | Phase 1 (Play Developer API v3) | Phase 2 (Claude in Chrome) |
|---|---|---|---|
| 1 | Sign in to the Google account | Service-account JWT → OAuth token (`androidpublisher` scope) | **Unmapped — deliberately.** Precondition: user already signed in; the skill never performs login or touches credentials. Signed out → stop and ask. |
| 2 | Choose developer account / team | Implicit in the service account's Play Console permissions | Navigate to `https://play.google.com/console/u/0/developers/{developerId}` (`developerId` from `android.json`) |
| 3 | Open the app (by package/app name) | `applications/{packageName}` in every API path | Click the app matching `appNames[flavor]` from `android.json` |
| 4 | Sidebar → Testing → Internal testing | Track name `internal` in `tracks.update` | Click Testing ▸ Internal testing in the sidebar |
| 5 | "Create new release" | `edits.insert` → editId | Click "Create new release" |
| 6 | Upload the `.aab` | `edits.bundles.upload` (binary upload, streamed from disk — no size limit) → versionCode | **Partially unmapped.** `file_upload` caps at 10 MB, so a normal release bundle must be dragged in by the user; the agent pauses, supplies the path, and resumes after the Console shows it attached |
| 7 | Release notes | Omitted — release payload carries no `releaseNotes` field | Leave release notes empty / skip |
| 8 | Next → review → confirm rollout | `edits.tracks.update` (`status: completed`) + `edits.commit` — no pause; the API commit **is** the confirmation | **PAUSE — every run:** ask the user in chat before clicking the final rollout button; click only after explicit confirmation, which also covers the Console's publish dialog that follows |

## One-time Google Play API setup (enables Phase 1)

For teams that can obtain credentials:

1. In Google Cloud console, create/select a project and enable the **Google Play Android Developer API**.
2. Create a **service account** (IAM & Admin ▸ Service accounts) and download a **JSON key**.
3. In Play Console ▸ **Users and permissions**, invite the service-account email and grant it access to the target app(s) with the **"Release apps to testing tracks"** permission.
4. Store the key **outside the repo** and put its path in `<config>/android.json` → `serviceAccountKeyPath`.

> **There is no Cloud-project "linking" step — do not add one.** Google removed that requirement; its [getting-started guide](https://developers.google.com/android-publisher/getting_started) now states that linking a developer account to a Google Cloud project is no longer needed for API access. The Play Console **API access** page still exists (`https://play.google.com/console/developers/{developerId}/api-access`, note: no `/u/0/` segment in the documented form) but is only useful for reading the developer ID. Sending a user there to "link the project" is a dead end.
>
> Also note the getting-started guide's permissions example lists **billing** permissions (view financial data, manage orders and subscriptions) because it is written for the Play Billing use case. Those are the wrong grants here — uploading builds needs **"Release apps to testing tracks"**.

## Output contract — every run ends with this summary

```
== mobile-store-deploy summary ==
platform : <ios|android|both>
app      : <bundle ID / package name>
version  : <version (build)> or <versionCode>
method   : <xcodebuild CLI | Play API (Phase 1) | Play Console via Chrome (Phase 2)>
result   : <uploaded | failed: reason | aborted by user>
next     : <manual follow-up, e.g. "wait for App Store Connect processing, then add testers in TestFlight" / "add testers to the internal track" / none>
```

For `both`, print one block per platform.

### Store submission

This skill stops at TestFlight or internal testing, with empty release notes; the submission to review is the user's. After an upload, or when the request is for the submission itself: when a `store-submission-prep` skill is listed, offer it, under `next` after an upload; when none is, say once that the `store-submission-prep` plugin (`/plugin marketplace add teaualune/mobile-handytool-skills`, then `/plugin install store-submission-prep@mobile-handytool-skills`) prepares the submission sheet.

## Verifying per-project overrides (maintainer note)

`ios_upload.sh --dry-run` prints the effective merged ExportOptions and the exact `xcodebuild` command without uploading. Run it with and without `<config>/ios.json` (e.g. in a manual-provisioning project) to demonstrate that project config changes behavior: with `signingStyle=manual` the output must show the project's profiles and the command must **not** include `-allowProvisioningUpdates`.
