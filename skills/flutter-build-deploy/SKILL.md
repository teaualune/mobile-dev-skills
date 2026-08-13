---
name: flutter-build-deploy
description: Build a new app version and deploy it to the stores in one flow — bumps version/build numbers and builds artifacts via scripts/build-version.sh (iOS .xcarchive and/or Android .aab), then hands the exact artifact paths to the flutter-store-deploy skill for upload to TestFlight / Play internal testing. Use when asked to "build and deploy", "build a new version and upload it", "release <version> to TestFlight/Play/both stores", "bump to X.Y.Z and ship it", or any request combining building a new version with store deployment. For deploy-only of an existing artifact use flutter-store-deploy instead; for build-only run scripts/build-version.sh directly.
---

# flutter-build-deploy

Thin wrapper that chains two existing pieces, in order:

1. **Build** — the project's `scripts/build-version.sh` (bumps `pubspec.yaml`, builds the `.xcarchive` and/or `.aab`, prints the artifact paths, and writes them to a machine-readable manifest)
2. **Deploy** — the `flutter-store-deploy` skill, invoked with the **exact artifact paths** captured from the build and verified on disk, so it never scans archives or guesses AAB locations

`$SKILL_DIR` below means the directory containing this file. Run everything from the project root.

## Project setup — `scripts/build-version.sh`

The build script lives **in the target project**, not in this skill: it edits the adjacent `pubspec.yaml` and is meant to be runnable by humans directly. If `scripts/build-version.sh` does not exist in the project:

1. Copy the template: `mkdir -p scripts && cp "$SKILL_DIR/templates/build-version.sh" scripts/build-version.sh && chmod +x scripts/build-version.sh`
2. Walk the user through the `Project config — ADAPT` block at the top of the copy: app name (used in the `.xcarchive` filename), flutter command (auto-detects `fvm`; override only if detection is wrong), the project's flavors, scheme/configuration naming if it deviates from `scheme == flavor` / `Release-<flavor>`, the fallback iOS deployment target, and the required `NS*UsageDescription` keys (list what the app's plugins need; empty skips the check). Fill values from the project's own files (`pubspec.yaml`, `ios/Runner.xcodeproj`, existing schemes) — ask, never guess.
3. Ensure `pubspec.yaml` carries the script's version-bookkeeping convention: a `version: <name>+<iosBuild>` line and a `# android: <androidBuild> = <name> (<iosBuild>)` comment line tracking the Android versionCode. Add the comment line (with the current versionCode, confirmed by the user) if missing.
4. Offer to commit the new script — it belongs to the project.

## Inputs

| Input | Maps to build flag | Notes |
|---|---|---|
| version name (optional) | `-v X.Y.Z` | unchanged if omitted |
| iOS build number | `-i N` | presence ⇒ build **and deploy** iOS |
| Android build number | `-a M` | presence ⇒ build **and deploy** Android |
| flavor | `--flavor <flavor>` | one of the project's flavors (e.g. staging \| production). **Ask if not stated** — the build script defaults to its first configured flavor, but store releases are usually production; never assume |

Deriving missing build numbers: current values live in `pubspec.yaml` (`version: X.Y.Z+N` → iOS build `N`; the `# android: M = …` comment → Android versionCode `M`). If the user wants a platform deployed but gave no new build number, propose current+1 and confirm before building — store uploads are permanent per build number, so never pick one silently.

Single-platform releases are first-class: only `-i` ⇒ iOS-only build **and** deploy; only `-a` ⇒ Android-only. Never add the other platform for symmetry. If the user's wording implies both stores but only one build number was given, ask for the missing one instead of assuming.

## Procedure

1. **Resolve inputs** (table above). Platforms to deploy = platforms being built.
2. **Preview when vague:** if the request left version/build numbers implicit, run `./scripts/build-version.sh … --dry-run` and confirm the pubspec change with the user before the real build.
3. **Build:**

   ```bash
   ./scripts/build-version.sh [-v X.Y.Z] [-i N] [-a M] --flavor <flavor>
   ```

   Stream the output. Any failure ⇒ STOP, report, and do not deploy. Known flake (Swift Package Manager projects): the iOS config-sync step can die with `Could not resolve package dependencies: … Package.swift was modified during the build` — fix with `rm -rf ios/Flutter/ephemeral` (generated, gitignored) and re-run the same command; the bump step is idempotent, so a retry after a partial run is safe.
4. **Capture the artifact paths** — the script writes `build/build-version-artifacts.env` (shell-quoted `IOS_ARCHIVE_PATH` / `ANDROID_AAB_PATH` for the latest run) and prints the same paths in its output; read the manifest, fall back to the printed `iOS archive: <path>` / `Output: <path>` lines if it is missing. Verify before deploying: each file exists on disk, and the iOS archive's app Info.plist matches this run (bundle id carries any flavor suffix the project uses — e.g. `.stg` for staging — and `CFBundleShortVersionString`/`CFBundleVersion` equal the requested version/build). Any mismatch ⇒ STOP and report (a stale path means the wrong artifact would ship).
5. **Deploy** — invoke the `flutter-store-deploy` skill (Skill tool), passing the platform(s) and the explicit artifact paths so it skips discovery entirely:
   - iOS: archive = the verified archive path from step 4 (no bundle-ID archive scan needed — the archive is already selected)
   - Android: AAB = the verified AAB path from step 4; package name = `applicationId` from `android/app/build.gradle` plus any flavor application-id suffix the project defines (e.g. `.stg` for staging)
   - All of that skill's rules apply unchanged: phase selection, the Phase 2 rollout pause, fail-loud, its summary block.
   - Missing `.flutter-store-deploy/` config (e.g. first release from this repo): flutter-store-deploy enters its **Setup mode** — interactive config creation + validation — and then continues the deploy. Let it run; don't work around it.
6. **Combined summary:** the build result (old → new version, flavor, artifact paths) followed by flutter-store-deploy's summary block per platform.

## Rules

- Build failure, an artifact path that cannot be captured from the build output, or a missing artifact file ⇒ never proceed to deploy.
- A deploy failure is reported as-is — do not rebuild or bump numbers to "fix" it (flutter-store-deploy's idempotency rule).
- The version bump edits `pubspec.yaml` by design and stays uncommitted; after a successful release, offer to commit — never commit unasked.
