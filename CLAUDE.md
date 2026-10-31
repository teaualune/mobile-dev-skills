# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A Claude Code **plugin** (plugin name: `flutter-skills`, manifests in `.claude-plugin/`) bundling seven Flutter skills under `skills/`, in two independent families: a two-phase feature workflow (requirements → spec → approval → implementation) and a build & store-deploy pipeline. It contains no buildable app: the content is `SKILL.md` prompt files plus template files (Dart reference material and a shell-script template) that are copied into target projects, never compiled or executed here. There are no build, lint, or test commands. Deployment is `/plugin install` (via the repo's own marketplace manifest) or manually copying folders from `skills/` into a target project's `.claude/skills/`.

### Verifying a change

The only end-to-end check is loading the checkout as a plugin from a real Flutter project and invoking the skill:

```bash
cd /path/to/a-flutter-app && claude --plugin-dir /path/to/flutter-feature-skills
# then: /flutter-skills:flutter-feature …
```

Root `analysis_options.yaml` excludes `**/*` from the Dart analyzer **on purpose**: `skills/flutter-feature-scaffold/templates/*.dart` import packages this repo doesn't depend on (there is no `pubspec.yaml` here) and declare `part 'example.freezed.dart'` files that will never exist. They are prompt material, not compilable code — don't "fix" the templates to satisfy an analyzer, and don't narrow the exclude.

## Architecture — how the skills chain

### Feature workflow

`skills/flutter-feature/` is the orchestrator. It is user-invoked only (`disable-model-invocation: true` in its frontmatter) and drives the other three, which are model-invocable sub-skills:

1. **`feature-intake/`** — interactive requirement gathering. Its output contract is the six-section **Intake Sheet** (Summary, Routes, Affected screens, Entities & APIs, Binding logic, Figma references).
2. **`flutter-feature-spec/`** — turns the populated Intake Sheet into a ten-section spec document (`feature-spec.md` by default; the orchestrator overrides location/naming to match the target project's docs conventions).
3. **`flutter-feature-scaffold/`** — generates Dart code from the approved spec, in a fixed dependency order (entities → repository → state primitives → widgets → screens → routing → edits to existing screens). Its `templates/` cover the Riverpod + go_router + Dio stack only; other stacks are generated from the target project's own files as pattern source.

A fifth skill sits **outside the orchestrated chain**:

- **`flutter-feature-spec-compact/`** — standalone maintenance for existing spec files: folds accumulated change records (changelog sections, addenda, phased deltas, inline update notes) back into the base sections so only the current state remains. Its one hard gate is the mandatory Step 2 question — the caller decides whether removed history is discarded or extracted verbatim to a sibling `<spec-basename>-changelog.md` — and it must never alter the spec's meaning or section structure.

The `Explore` and `Plan` subagents referenced by the orchestrator are built-in Claude Code agent types — nothing to install.

### Build & deploy

- **`flutter-build-deploy/`** — orchestrates a release: runs the target project's `scripts/build-version.sh` (version bump + iOS archive and/or Android AAB), captures the artifact paths, then invokes `flutter-store-deploy` with them. The build script itself lives **in the target project** — `templates/build-version.sh` here is the installable template, adapted per project via the `Project config — ADAPT` block at its top (app name, flutter command with fvm auto-detect, flavors, scheme/configuration naming, iOS target fallback, required privacy usage keys).
- **`flutter-store-deploy/`** — uploads already-built artifacts (iOS `.xcarchive` → TestFlight via `xcodebuild -exportArchive`; Android `.aab` → Play internal testing via the Play Developer API, with an assisted Claude-in-Chrome fallback). Unlike the build script, its `scripts/` are executed **in place** from the skill directory (`$SKILL_DIR`); per-project values live in the target project's `.flutter-store-deploy/` config, created by the skill's setup mode. Model-invocable on its own for deploy-only requests.

## Cross-file contracts (keep in sync when editing)

Several rules are deliberately restated in multiple skills; changing one copy without the others breaks the workflow:

- **The hard gate**: no Dart code before explicit spec approval ("ok" alone doesn't count). Stated in `flutter-feature` and `flutter-feature-spec`'s handoff section.
- **Stack detection + fallback**: detect state management/routing/HTTP/codegen from `pubspec.yaml` and sample files; fall back to Riverpod + go_router + Dio + freezed only when detection fails, and label every fallback explicitly. Specified in both `flutter-feature` (Step 1.2) and `flutter-feature-scaffold` (Step 1).
- **Provisional API shapes**: the one exception to "never invent endpoints/fields" — applies only when the user says the backend isn't ready. Each skill defines its stage's handling (intake proposes and marks `PROVISIONAL`, spec marks sections and adds a confirm-with-backend checklist, scaffold generates stub repositories with `// TODO(api)` comments).
- **Intake Sheet section names/order**: `feature-intake` defines them; `flutter-feature` Step 1.3 and the spec template's sections map onto them.
- **Spec template structure**: `flutter-feature-spec` defines the ten-section layout; `flutter-feature-spec-compact` promises to preserve whatever structure a spec file uses (its fold rules reference the template's "N/A — don't delete sections silently" convention), so template restructures should be sanity-checked against the compact skill's Step 3.
- **build-version.sh interface**: `flutter-build-deploy`'s SKILL.md restates the template's contract — the CLI flags (`-v`/`-i`/`-a`/`--flavor`/`--dry-run`), the pubspec version-bookkeeping convention (`version: <name>+<iosBuild>` plus the `# android: <androidBuild> = …` comment line), the printed `iOS archive:` / `Output:` lines, and the `build/build-version-artifacts.env` manifest (keys `IOS_ARCHIVE_PATH`, `ANDROID_AAB_PATH`, …). Changing any of these in `templates/build-version.sh` requires the same change in that SKILL.md, and vice versa.
- **store-deploy script exit codes + stdout keys**: `flutter-store-deploy`'s SKILL.md branches on values its `scripts/` define in their header comments — `ios_find_archive.sh` (0 selected / 2 ambiguous / 3 no match / 4 usage, printing `ARCHIVE_PATH=`/`VERSION=`/`BUILD=`/`CREATION_DATE=`), `ios_upload.sh` (4 = config problem, `--dry-run` prints the merged plist), `android_phase_select.sh` (`CONFIG_PRESENT=`/`PHASE=`/`SERVICE_ACCOUNT_KEY=`/`SERVICE_ACCOUNT_KEY_ERROR=`/hints; 4 = invalid config), and `android_phase1_upload.sh` (**42 = auth/permission failure, the only code that permits the Phase 2 fallback**; any other non-zero must stop the deploy). Renumbering an exit code or renaming a `KEY=VALUE` line silently changes control flow in the SKILL.md — change both together.
- **Build → deploy handoff**: `flutter-build-deploy` Step 5 passes explicit artifact paths; `flutter-store-deploy`'s Inputs section promises to skip discovery when paths are supplied. Both files state the deal — keep them aligned. `flutter-build-deploy` also defers to `flutter-store-deploy`'s rules (setup mode, Phase 2 rollout pause, idempotency/no-auto-bump) rather than restating them; don't duplicate those rules into the build skill.

## Conventions

- The bundle must stay **project-agnostic**. Concrete paths, commands, and doc conventions (e.g. `docs/specs/`, `.stg` flavor suffixes) are illustrative examples users may replace per README's "Per-project adjustments" — never hardcode a specific project's names or rules. **Deliberate exceptions in `flutter-feature`** (keep them): Chinese text in spec documents is always Traditional Chinese, and Flutter/Dart commands go through `fvm` when the project has `.fvmrc` and `fvm` is installed (plain commands otherwise; the caller is asked first only when exactly one of the two is present). For the deploy family, project-specific values belong in the target project (`scripts/build-version.sh`'s ADAPT block, `.flutter-store-deploy/`), never in the skills.
- Skill `description:` frontmatter doubles as the auto-trigger condition; each one also states what the skill must NOT be used for. Preserve that pattern when editing.
- Neither `.claude-plugin/plugin.json` nor `marketplace.json` enumerates skills — `skills/` is auto-discovered, so adding a skill means adding a folder with a `SKILL.md` and nothing else. What the manifests *do* carry (plugin `description`, `version`, keywords) duplicates README's framing; keep the skill count and family split in sync across README, plugin.json, marketplace.json, and this file when a skill is added or removed. Only `flutter-feature` sets `disable-model-invocation: true`; the other six are model-invocable by design.
- `templates/` folders hold files copied into target projects and adapted, not literal copy-paste output: `flutter-feature-scaffold/templates/*.dart` (pairs for with/without codegen: `entity_freezed`/`entity_manual`, `provider_codegen`/`provider_manual`), `flutter-build-deploy/templates/build-version.sh` (ADAPT block), `flutter-store-deploy/templates/` (ExportOptions default + example project config). By contrast, `flutter-store-deploy/scripts/` are executables run from the installed skill directory — keep them project-agnostic and non-interactive.
