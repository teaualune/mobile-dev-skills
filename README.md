# flutter-feature skill bundle

Portable copy of the two-phase Flutter feature workflow. Drop these four folders into a target project's `.claude/skills/` directory.

- `flutter-feature/` — the orchestrator (user-invoked via `/flutter-feature`); runs Phase 1 (requirements → spec → TBD-resolution loop → approval) and Phase 2 (implementation)
- `feature-intake/` — interactive requirement gathering (Intake Sheet)
- `flutter-feature-spec/` — spec document production
- `flutter-feature-scaffold/` — code generation rules + Riverpod/go_router/Dio templates

The `Explore` and `Plan` subagents referenced by `flutter-feature` are built-in Claude Code agent types — nothing extra to install.

## Installation

Prerequisite: [Claude Code](https://claude.com/claude-code) installed and working.

### Into an existing Flutter project

Copy the four skill folders into the project's `.claude/skills/` directory (create it if it doesn't exist):

```bash
cd /path/to/this/bundle
mkdir -p /path/to/your-flutter-app/.claude/skills
cp -R flutter-feature feature-intake flutter-feature-spec flutter-feature-scaffold \
  /path/to/your-flutter-app/.claude/skills/
```

Commit `.claude/skills/` so the whole team gets the workflow.

### Into a new Flutter project

Create the project first, then install the same way:

```bash
flutter create my_app
mkdir -p my_app/.claude/skills
cp -R flutter-feature feature-intake flutter-feature-spec flutter-feature-scaffold \
  my_app/.claude/skills/
```

Note for brand-new projects: the workflow detects the tech stack from existing code, and a fresh `flutter create` app has none of it yet. Either add your chosen packages (state management, routing, HTTP) to `pubspec.yaml` before the first feature, or accept the announced fallback stack (Riverpod + go_router + Dio + freezed) when the skill asks.

### Alternative: install once for all projects

Copy the folders into `~/.claude/skills/` instead — personal skills are available in every project. Project-level installation is preferred for teams, since it ships with the repository.

### Verify and use

1. Run `claude` in the project root.
2. Type `/flutter-feature` — it should autocomplete. Invoke it with a feature description, e.g. `/flutter-feature add a saved-articles screen with bookmarking`.
3. Only `/flutter-feature` is invoked directly; it orchestrates the other three skills (intake → spec → scaffold) automatically.

## Per-project adjustments

`flutter-feature/SKILL.md` contains a few example defaults that can be replaced with the target project's own conventions:

- Spec doc location/naming (e.g. `docs/specs/<feature-name>-feature-spec.md`, `docs/specs/artifacts/`) and API reference (e.g. `docs/api-reference.md`)
- Any language conventions the project enforces for spec documents
- Post-generation commands (e.g. `dart run build_runner build --delete-conflicting-outputs`, `flutter gen-l10n`, `flutter analyze`, with an `fvm` prefix if the project uses it)

The skill discovers these conventions dynamically when they differ, so the bundle works as-is; hardcoding the target project's values just gives it better defaults.
