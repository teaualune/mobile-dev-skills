# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A portable Claude Code **skills bundle** implementing a two-phase Flutter feature workflow (requirements → spec → approval → implementation). It contains no buildable app: the content is five `SKILL.md` prompt files plus Dart template files that are copied as reference material, never compiled here. There are no build, lint, or test commands. Deployment is copying the five skill folders into a target project's `.claude/skills/` directory.

## Architecture — how the skills chain

`flutter-feature/` is the orchestrator. It is user-invoked only (`disable-model-invocation: true` in its frontmatter) and drives the other three, which are model-invocable sub-skills:

1. **`feature-intake/`** — interactive requirement gathering. Its output contract is the six-section **Intake Sheet** (Summary, Routes, Affected screens, Entities & APIs, Binding logic, Figma references).
2. **`flutter-feature-spec/`** — turns the populated Intake Sheet into a ten-section spec document (`feature-spec.md` by default; the orchestrator overrides location/naming to match the target project's docs conventions).
3. **`flutter-feature-scaffold/`** — generates Dart code from the approved spec, in a fixed dependency order (entities → repository → state primitives → widgets → screens → routing → edits to existing screens). Its `templates/` cover the Riverpod + go_router + Dio stack only; other stacks are generated from the target project's own files as pattern source.

A fifth skill sits **outside the orchestrated chain**:

- **`flutter-feature-spec-compact/`** — standalone maintenance for existing spec files: folds accumulated change records (changelog sections, addenda, phased deltas, inline update notes) back into the base sections so only the current state remains. Its one hard gate is the mandatory Step 2 question — the caller decides whether removed history is discarded or extracted verbatim to a sibling `<spec-basename>-changelog.md` — and it must never alter the spec's meaning or section structure.

The `Explore` and `Plan` subagents referenced by the orchestrator are built-in Claude Code agent types — nothing to install.

## Cross-file contracts (keep in sync when editing)

Several rules are deliberately restated in multiple skills; changing one copy without the others breaks the workflow:

- **The hard gate**: no Dart code before explicit spec approval ("ok" alone doesn't count). Stated in `flutter-feature` and `flutter-feature-spec`'s handoff section.
- **Stack detection + fallback**: detect state management/routing/HTTP/codegen from `pubspec.yaml` and sample files; fall back to Riverpod + go_router + Dio + freezed only when detection fails, and label every fallback explicitly. Specified in both `flutter-feature` (Step 1.2) and `flutter-feature-scaffold` (Step 1).
- **Provisional API shapes**: the one exception to "never invent endpoints/fields" — applies only when the user says the backend isn't ready. Each skill defines its stage's handling (intake proposes and marks `PROVISIONAL`, spec marks sections and adds a confirm-with-backend checklist, scaffold generates stub repositories with `// TODO(api)` comments).
- **Intake Sheet section names/order**: `feature-intake` defines them; `flutter-feature` Step 1.3 and the spec template's sections map onto them.
- **Spec template structure**: `flutter-feature-spec` defines the ten-section layout; `flutter-feature-spec-compact` promises to preserve whatever structure a spec file uses (its fold rules reference the template's "N/A — don't delete sections silently" convention), so template restructures should be sanity-checked against the compact skill's Step 3.

## Conventions

- The bundle must stay **project-agnostic**. Concrete paths, commands, and doc conventions in `flutter-feature/SKILL.md` (e.g. `docs/specs/`, `fvm` prefixes) are illustrative examples users may replace per README's "Per-project adjustments" — never hardcode a specific project's names or rules.
- Skill `description:` frontmatter doubles as the auto-trigger condition; each one also states what the skill must NOT be used for. Preserve that pattern when editing.
- `flutter-feature-scaffold/templates/*.dart` are starting points that get adapted to detected conventions, not literal copy-paste output. Template pairs exist for with/without codegen (`entity_freezed`/`entity_manual`, `provider_codegen`/`provider_manual`).
