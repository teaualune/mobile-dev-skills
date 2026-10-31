# flutter-skills

A Claude Code **plugin** bundling seven Flutter skills in two families.

**Feature workflow** — the two-phase flow (requirements → spec → approval → implementation):

- `flutter-feature/` — the orchestrator (user-invoked); runs Phase 1 (requirements → spec → TBD-resolution loop → approval) and Phase 2 (implementation)
- `feature-intake/` — interactive requirement gathering (Intake Sheet)
- `flutter-feature-spec/` — spec document production
- `flutter-feature-scaffold/` — code generation rules + Riverpod/go_router/Dio templates
- `flutter-feature-spec-compact/` — standalone spec maintenance (not part of the orchestrated chain): folds a spec's accumulated change records (changelogs, addenda, phased deltas) back into its base sections so only the current state remains, asking first whether the removed history should be extracted to a sibling changelog file

**Build & deploy** — releasing to the stores:

- `flutter-build-deploy/` — build-and-deploy in one flow: bumps version/build numbers and builds artifacts via the project's `scripts/build-version.sh` (installed from this skill's `templates/` on first use and adapted to the project), then hands the exact artifact paths to `flutter-store-deploy`
- `flutter-store-deploy/` — uploads already-built artifacts: iOS `.xcarchive` → TestFlight via native Apple CLIs, Android `.aab` → Play "Internal testing" via the Play Developer API (with an assisted Play Console browser fallback); per-project config lives in the target project's `.flutter-store-deploy/`

All skills live under `skills/`. The `Explore` and `Plan` subagents referenced by `flutter-feature` are built-in Claude Code agent types — nothing extra to install.

## Installation

Prerequisite: [Claude Code](https://claude.com/claude-code) installed and working.

### As a plugin (recommended)

```
/plugin marketplace add teaualune/flutter-feature-skills
/plugin install flutter-skills@flutter-skills
```

Plugin skills are namespaced, e.g. `/flutter-skills:flutter-feature add a saved-articles screen`. Update later with `/plugin update flutter-skills`.

To try a local checkout without installing anything into `~/.claude`:

```bash
claude --plugin-dir /path/to/flutter-feature-skills
```

### Manual copy (no plugin)

Copy skill folders from `skills/` into the target project's `.claude/skills/` directory (create it if it doesn't exist):

```bash
cd /path/to/this/repo
mkdir -p /path/to/your-flutter-app/.claude/skills
cp -R skills/* /path/to/your-flutter-app/.claude/skills/
```

Copy only the family you need if you prefer — the feature workflow (five folders) and the deploy pair (two folders) are independent. Commit `.claude/skills/` so the whole team gets the workflow. Copying into `~/.claude/skills/` instead makes them personal skills available in every project; project-level installation is preferred for teams.

Note for brand-new projects: the feature workflow detects the tech stack from existing code, and a fresh `flutter create` app has none of it yet. Either add your chosen packages (state management, routing, HTTP) to `pubspec.yaml` before the first feature, or accept the announced fallback stack (Riverpod + go_router + Dio + freezed) when the skill asks.

### Verify and use

1. Run `claude` in the project root (with `--plugin-dir` if testing a local checkout).
2. Type `/flutter-skills:flutter-feature` (or `/flutter-feature` for a manual copy) — it should autocomplete. Invoke it with a feature description.
3. `flutter-feature` is the feature-workflow entry point; it orchestrates the intake → spec → scaffold skills automatically. `flutter-feature-spec-compact` sits outside that chain — invoke it (or let it auto-trigger on "compact the spec") when an existing spec has accumulated change history worth cleaning up.
4. For releases, ask to "build and deploy X.Y.Z to TestFlight/Play" (`flutter-build-deploy`) or, for an artifact that is already built, "upload the archive to TestFlight" (`flutter-store-deploy`).

## Per-project adjustments

### Feature workflow

`flutter-feature/SKILL.md` contains a few example defaults that can be replaced with the target project's own conventions:

- Spec doc location/naming (e.g. `docs/specs/<feature-name>-feature-spec.md`, `docs/specs/artifacts/`) and API reference (e.g. `docs/api-reference.md`)
- Any language conventions the project enforces for spec documents
- Post-generation commands (e.g. `dart run build_runner build --delete-conflicting-outputs`, `flutter gen-l10n`, `flutter analyze`)

The skill discovers these conventions dynamically when they differ, so the bundle works as-is; hardcoding the target project's values just gives it better defaults.

Two rules are built in rather than discovered: Chinese text in spec documents is always Traditional Chinese, and Flutter/Dart commands run through `fvm` (`fvm flutter …`, `fvm dart …`) when the project has `.fvmrc` and `fvm` is installed; otherwise it uses plain `flutter`/`dart`, asking first whether you want `fvm` only when exactly one of the two is present.

### Build & deploy

Project-specific values never live in the skills — they live in two places inside the target project, both created on first use:

- `scripts/build-version.sh` — copied from `flutter-build-deploy/templates/` and adapted via the `Project config — ADAPT` block at its top (app name, flutter command, flavors, scheme/configuration naming, iOS deployment-target fallback, required privacy usage keys). It also expects pubspec.yaml to carry the version-bookkeeping convention: `version: <name>+<iosBuild>` plus a `# android: <androidBuild> = …` comment line for the Android versionCode.
- `.flutter-store-deploy/` — deploy config (`ios.json` with ExportOptions overrides, `android.json` with the Play service-account key path and Play Console hints), created interactively by `flutter-store-deploy`'s setup mode. Safe to commit; the service-account key itself must live outside the repo.
