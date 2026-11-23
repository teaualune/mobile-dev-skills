---
name: mobile-build-deploy
description: Bump the app version, build the iOS archive and/or Android AAB with the project's scripts/build-version.sh (Flutter or SwiftUI), then upload them through mobile-store-deploy. For "bump to 2.4.0 and ship it to TestFlight/Play". Not for deploy-only (mobile-store-deploy) or build-only.
---

# mobile-build-deploy

Thin wrapper that chains two pieces, in order:

1. **Build** — the project's `scripts/build-version.sh`: it bumps the version, builds the `.xcarchive` and/or `.aab`, prints the artifact paths, and writes them to a machine-readable manifest
2. **Deploy** — the `mobile-store-deploy` skill, invoked with the **exact artifact paths** captured from the build and verified on disk, so it never scans archives or guesses AAB locations

What depends on the platform — the script template, where the version lives, the command the script runs — comes from the platform adapter's "Build adapter" section. Run everything from the project root, the folder the adapter's "Project layout" names as Root; in a monorepo, it is the app's folder, not the repository's root.

## Platform adapter

**Platform adapter.** Platform knowledge lives in the plugin's adapters, one per platform: `${CLAUDE_SKILL_DIR}/../../platforms/<platform>/PLATFORM.md`. Find the one this project needs with `grep -H -A2 '^## Applies when' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`, and use the adapter whose condition the project meets; if several do, ask which app to build. If none does, or the `platforms/` folder is missing, say so and stop. Read only its "Project layout" and "Build adapter" sections, with their line ranges from `grep -n '^## ' <adapter>`, plus "Commands" when "Build adapter" sends you there. "The adapter" below means that file.

"Build adapter" gives, under these labels:

- **Template** — the build script to install, a file in the adapter's folder, or `none`: then this skill can't build the app. Say so, and offer `mobile-store-deploy` for an archive or AAB built another way.
- **Platforms** — which build flags the script takes: `-i` (iOS archive), `-a` (Android AAB), or both.
- **Version bookkeeping** — where the version and build numbers live, and how the script changes them.
- **Command** — how the command the script runs is decided and passed in, and the header line that shows it.
- **Setup** — the values the script's ADAPT block needs, and where to read each one.
- **Artifacts** — how to tell the right artifact before deploying: the iOS bundle ID, the Android package name.

Plus, when it has them, **Older scripts** (earlier versions of its template) and **Known issues** (failures with a safe retry).

The plugin options the adapters' command rules read:

fvm policy (plugin option `fvm_policy`): [${user_config.fvm_policy}] — `auto`, `always` or `never`. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use `auto`.

## Project setup — `scripts/build-version.sh`

The build script lives **in the target project**, not in this skill: it edits the project's own version files and is meant to be runnable by humans directly. If `scripts/build-version.sh` does not exist in the project:

1. Copy the adapter's template: `mkdir -p scripts && cp "${CLAUDE_SKILL_DIR}/../../platforms/<platform>/<template>" scripts/build-version.sh && chmod +x scripts/build-version.sh`
2. Walk the user through the `Project config — ADAPT` block at the top of the copy, value by value, as the adapter's "Setup" lists them, including the required usage keys, such as `NSCameraUsageDescription` (the keys the specs declare, below, plus any the app's libraries need; empty skips the check). Fill values from the project's own files — ask, never guess.
3. Make sure the project keeps its version the way the adapter's "Version bookkeeping" says, before the first run.
4. Offer to commit the new script — it belongs to the project.

An existing script: check it against the adapter's "Older scripts", when it has them, before relying on the next sections.

A script that is neither the template nor a copy "Older scripts" lists (one the project wrote before this plugin) isn't passed this skill's flags as they are. Read its usage (`--help`, its top comment or its argument parsing), map the inputs below to the flags it takes and the artifact manifest to the keys it writes, and say the mapping in one line; never pass a flag its usage doesn't list, since an `Unknown argument` exit means this step was skipped. When an input has no flag or the manifest has no path key, ask: run the script as the user directs, or replace it with the template, carrying its values into the ADAPT block. A script that hardcodes the command the adapter's "Command" decides runs as it is when that command equals the decided one, with the header check skipped, as "Older scripts" allows; when they differ, stop. Offer the template's update either way, and never edit a script the user declined to update.

## Usage keys the specs declare

The feature workflow's specs list each iOS permission in section 4's `### Permissions & capabilities` table, and its Phase 2 adds each new usage key (`…UsageDescription`) to the script's `REQUIRED_USAGE_KEYS`. Before every iOS build, check that nothing slipped past it:

1. Find the spec index: `grep -rlxF --include='*index.md' '| Feature | Spec | Screens and routes | Status | Last verified |' .`. No index → skip the check and say so.
2. For each `implemented` row, take the keys of its spec's iOS permission rows, `grep -E '^\| ios \|' <its spec> | grep -oE '[A-Za-z]+UsageDescription'`, and compare them with the ADAPT block's `REQUIRED_USAGE_KEYS`.
3. A key the specs declare that the list lacks: show it with its spec, and offer to add it to the ADAPT block before the build. Never add one unasked, and never remove one the specs don't name.

## Inputs

| Input | Maps to build flag | Notes |
|---|---|---|
| version name (optional) | `-v X.Y.Z` | unchanged if omitted |
| iOS build number | `-i N` | presence ⇒ build **and deploy** iOS |
| Android build number | `-a M` | presence ⇒ build **and deploy** Android; only when the adapter's "Platforms" lists it |
| flavor | `--flavor <flavor>` | one of the ADAPT block's flavors (e.g. staging \| production). With several, **ask if not stated** — the build script defaults to its first configured flavor, but store releases are usually production; never assume. None listed (an app without flavors) ⇒ leave the flag out |

Deriving missing build numbers: the adapter's "Version bookkeeping" says where the current values live, and the script's `--dry-run` header prints them. If the user wants a platform deployed but gave no new build number, propose current+1 and confirm before building — store uploads are permanent per build number, so never pick one silently.

Single-platform releases are first-class: only `-i` ⇒ iOS-only build **and** deploy; only `-a` ⇒ Android-only. Never add the other platform for symmetry. If the user's wording implies both stores but only one build number was given, ask for the missing one instead of assuming. A platform the adapter's "Platforms" doesn't list can't be built here: say so, and never pass its flag.

## Procedure

1. **Resolve inputs** (table above), the adapter (section above) and the command: decide it once, before the first script run, as the adapter's "Command" says, and report it. Platforms to deploy = platforms being built. Building iOS: run the usage-key check (section above).
2. **Preview when vague:** if the request left version/build numbers implicit, run the script with `--dry-run` and confirm the version change with the user before the real build.
3. **Build**, with the command passed in as the adapter's "Command" says (`<command>` below; Flutter: `FLUTTER_CMD="<cmd>"`, or nothing when the ADAPT block pins the command):

   ```bash
   <command> ./scripts/build-version.sh [-v X.Y.Z] [-i N] [-a M] [--flavor <flavor>]
   ```

   Stream the output whole: the header comes first, so never cut it with `head` or `tail`. After every run, dry runs included, check the header line the adapter's "Command" names against the expected command; a different or missing line ⇒ STOP and report — before the real build after a dry run, before deploying after a real one (the adapter's "Older scripts" may name an exception). Any failure ⇒ STOP, report, and do not deploy. Retry only what the adapter's "Known issues" names, as it says; the version bump is idempotent, so a retry after a partial run is safe.
4. **Capture the artifact paths** — the script writes `build/build-version-artifacts.env` (shell-quoted `IOS_ARCHIVE_PATH` / `ANDROID_AAB_PATH` for the latest run) and prints the same paths in its output; read the manifest, fall back to the printed `iOS archive: <path>` / `Output: <path>` lines if it is missing. Verify before deploying: each file exists on disk, and the iOS archive's app Info.plist matches this run (the bundle ID the adapter's "Artifacts" names, with any flavor suffix the project uses — e.g. `.stg` for staging — and `CFBundleShortVersionString`/`CFBundleVersion` equal to the requested version/build), and so does the AAB: with `bundletool` installed, `bundletool dump manifest --bundle <aab>` shows the package name the adapter's "Artifacts" names, `versionName` equal to the requested version and `versionCode` to the Android build; without it, the file must be newer than this build's start (note the time before step 3's real build), and the summary says its package and version weren't read. Any mismatch ⇒ STOP and report (a stale path means the wrong artifact would ship).
5. **Deploy** — invoke the `mobile-store-deploy` skill (Skill tool), passing the platform(s) and the explicit artifact paths so it skips discovery entirely:
   - iOS: archive = the verified archive path from step 4 (no bundle-ID archive scan needed — the archive is already selected)
   - Android: AAB = the verified AAB path from step 4; package name as the adapter's "Artifacts" says
   - All of that skill's rules apply unchanged: phase selection, the Phase 2 rollout pause, fail-loud, its summary block.
   - Missing deploy config (the `ios.json` / `android.json` a platform needs doesn't exist yet, e.g. first release from this repo): mobile-store-deploy enters its **Setup mode** — interactive config creation + validation — and then continues the deploy. Let it run; don't work around it.
6. **Combined summary:** the build result (old → new version, flavor, the command from the header line, artifact paths) followed by mobile-store-deploy's summary block per platform.

## Rules

- Build failure, an artifact path that cannot be captured from the build output, or a missing artifact file ⇒ never proceed to deploy.
- A deploy failure is reported as-is — do not rebuild or bump numbers to "fix" it (mobile-store-deploy's idempotency rule).
- The version bump edits the files the adapter's "Version bookkeeping" names, by design, and stays uncommitted; after a successful release, offer to commit them — never commit unasked, and never the manifest under `build/`, which holds this machine's paths.
