---
name: flutter-feature
description: Two-phase workflow for adding a new feature to an existing Flutter app, or for editing a feature that already exists. Phase 1 gathers requirements interactively and produces a spec document aligned with the project's existing docs; Phase 2 implements the approved spec. Orchestrates the feature-intake, flutter-feature-spec, and flutter-feature-scaffold skills and may delegate steps to subagents. The tech stack (state management, routing, HTTP, codegen) is detected from project code rather than assumed; if detection fails, falls back to Riverpod + go_router + Dio + freezed and asks for confirmation. Manually invoked by the user — do not auto-trigger.
disable-model-invocation: true
argument-hint: "[new-feature or existing-feature-change description, or path to a requirements dump]"
---

# Flutter Feature Workflow

Act as a senior Flutter engineer who turns a fuzzy feature idea into (1) a complete, approved spec document, then (2) production-ready Flutter code. This happens through structured conversation, not one-shot generation. The idea may be a **brand-new feature** or a **change to a feature that already exists** in the app — both go through the same two phases.

The app's tech stack — state management, routing, HTTP client, code generation tools, UI/design system — must be **detected from the existing project code**, not assumed. If detection is impossible, fall back to **Riverpod + go_router + Dio** (with `freezed` + `json_serializable` if codegen is in play), state the fallback openly, and ask the user to confirm or correct.

## The hard gate

The workflow has two phases. **Never enter Phase 2 without explicit approval of the spec** (e.g. "looks good", "approved", "let's build it"). A vague "ok" or "thanks" is not approval — confirm: "Just to confirm, you'd like me to proceed with implementation based on this spec?" Do not write any Dart code in Phase 1.

---

## Phase 1 — Requirements & Spec

### Step 1.1 — Determine the mode: new feature or edit to an existing one

The user may invoke this skill in either mode. Establish which one applies before intake starts; if the request doesn't make it obvious, ask.

- **New feature** — nothing exists yet. Run the full Intake Sheet from scratch and produce a new spec document.
- **Existing feature edit** — the feature is already in the app and the user wants to change it. The deliverable is a **delta**, so Phase 1 shifts shape:
  1. **Locate ground truth first.** Find the feature's current spec document (if one exists) and its code — screens, state primitives, entities, routes. An `Explore` subagent works well for this sweep. Read the existing spec before asking the user anything; don't re-ask what's already documented.
  2. **Run intake against the delta.** The "Affected existing screens" section becomes central; "New routes" and "New entities" may legitimately be empty. For every change, capture what changes, what stays, and the regression risk to current behavior.
  3. **The spec deliverable is an update to the existing spec document** (see Step 1.5) rather than a new file — unless the feature was never spec'd, in which case write a new doc that records current behavior plus the change, and say that's what it is.

### Step 1.2 — Detect the tech stack

Do this early; it shapes the questions you ask.

**Pre-check — existing spec docs first.** Tech stacks rarely change over a project's lifetime, and previously written feature specs usually already name the detected stack (e.g. "Routing wiring (go_router)", "State management (Riverpod)"). Before sweeping code, read 1–2 recent spec docs (wherever the project keeps them, e.g. `docs/specs/`); if they state the stack, take it as a strong prior and only spot-verify against `pubspec.yaml` instead of running a full detection sweep. Docs can lag reality, so a quick `pubspec.yaml` confirmation is still required — if the two disagree, trust the code and flag the stale doc to the user.

When the pre-check comes up empty, run full detection: read `pubspec.yaml` (usually decisive) and skim 1–3 existing feature folders, or delegate the sweep to an `Explore` subagent (see Delegation below). Detection is two layers:

- **Stack layer** — what packages are in use: state management, routing, HTTP, codegen, serialization, DI.
- **Convention layer** — folder layout, naming style, theming, common widgets, error handling patterns, and how the chosen state/HTTP libraries are wired.

Produce a **Detected Stack** statement to the user:

```
Detected stack (from pubspec.yaml + sample files):
- State management: <e.g. flutter_riverpod + riverpod_annotation, or "not detected">
- Routing: <e.g. go_router 17.x, or "Navigator 1.0 — no routing package">
- HTTP client: <e.g. dio 5.x, or http 1.x>
- Serialization: <e.g. freezed + json_serializable, or manual fromJson/toJson>
- Codegen: <yes (build_runner) / no>
- Other relevant packages: <get_it, flutter_hooks, equatable, etc.>
- Flutter/Dart command: <`fvm flutter` / `fvm dart` (.fvmrc + fvm installed), or plain `flutter` / `dart`>

Proceeding with this stack. Confirm or correct?
```

**Fallback rules — apply only when detection fails:**
- State management → Riverpod (`flutter_riverpod` if no codegen detected, `riverpod_annotation` if `build_runner` is present)
- Routing → `go_router`
- HTTP → `dio`
- Serialization → `freezed` + `json_serializable` if codegen is present, manual otherwise

Label every fallback explicitly: `State management: Riverpod (FALLBACK — not detected, please confirm)`.

**Mixed/ambiguous cases:**
- Multiple state libraries in `pubspec.yaml` (e.g. both `flutter_bloc` and `provider`) → ask which one is canonical for new features. Don't pick.
- Stack present but feature folders use a different one (legacy migration) → ask. Don't assume.
- An obscure package you don't recognize → say so, ask the user to confirm its role, and read one sample file before depending on it.

### Step 1.3 — Gather requirements (`feature-intake`)

Invoke the `feature-intake` skill. It defines the six-section Intake Sheet (Summary, Routes, Affected screens, Entities & APIs, Binding logic, Figma references) and the conversation rules for filling it.

Information may arrive incrementally (back-and-forth) or as a single dump (text file or long message). Either is fine — extract what's present, then ask only about what's missing.

**Delegating the Q&A:** when the gap-hunt is large or requires cross-checking the codebase while questioning, you may spawn a subagent to run the interactive collection instead of doing it inline. Spawn it **synchronously** (`run_in_background: false`), give it the current Intake Sheet state plus the specific gaps, and require it to use `AskUserQuestion` for each gap (one question per turn, per the intake rules). It returns the completed sections; you remain the owner of the sheet.

### Step 1.4 — Align with existing documentation

Before writing the spec, find out how this project already documents features. Spawn an `Explore` subagent (or look yourself if the layout is already known) to answer:

- Where do feature specs live, and what naming convention do they follow? (e.g. `docs/specs/<feature-name>-feature-spec.md`, with supporting images in `docs/specs/artifacts/`.)
- What structure/sections/language do existing specs use? Read 1–2 recent ones as the style reference, and note any language conventions they enforce (e.g. a required language or script variant for spec text).
- Is there an API reference to check endpoints against? (e.g. `docs/api-reference.md`.) Cross-check every endpoint the user mentions; discrepancies become intake questions, never silent corrections.

If the project has no docs convention, default to the `flutter-feature-spec` skill's standard output and say so.

### Step 1.5 — Write the spec (`flutter-feature-spec`)

Invoke the `flutter-feature-spec` skill to turn the populated Intake Sheet into the spec document. Three overrides on top of that skill:

- **File location/naming follows the conventions discovered in Step 1.4** (e.g. `docs/specs/<feature-name>-feature-spec.md`), not the skill's default `feature-spec.md`, whenever the project has an established spec directory.
- **Chinese-language text in spec documents must be Traditional Chinese only** — never Simplified, in every project and in every later edit to the spec.
- You may delegate the writing to a subagent: point it at the Intake Sheet, 1–2 example spec docs as style references, and the API reference doc, and state the Traditional Chinese rule in its prompt. Review its output yourself before presenting it — you own the deliverable.

If the spec updates an existing document rather than creating a new one, preserve the existing document's structure and only change what the feature changes.

### Step 1.6 — Resolve open questions, then the approval gate

This step is an **iteration loop** that improves and finalizes the spec before Phase 2 — not a rubber stamp.

1. **Surface.** Present the spec, calling out the **Open Questions / TBDs** section explicitly: "Here are the TBDs that need resolving before code: ...".
2. **Resolve.** Don't just leave the TBDs on the table — actively ask the user about them, one at a time (or via `AskUserQuestion` when the options are enumerable), starting with the ones that block the most implementation work. The user may answer, defer ("leave as TBD, we'll resolve later"), or cut scope.
3. **Edit.** Fold each answer back into the spec file immediately: update the affected sections, remove the resolved checkbox from Open Questions (deferred items stay, marked as deliberately deferred). Show the user what changed.
4. **Repeat** steps 2–3 until every open question is resolved or explicitly deferred by the user.
5. **Approval gate.** Only then ask for approval, and wait for it as defined in "The hard gate" above. Any further revision requests stay in this loop — Phase 1 doesn't end until the approval is explicit.

---

## Phase 2 — Implementation (only after approval)

### Step 2.1 — Confirm stack and conventions

Invoke the `flutter-feature-scaffold` skill and run its Step 1 in full: produce the **Detected Stack + Conventions Report** (folder pattern, entity style, repository/error conventions, state primitive patterns, screen patterns, routing declaration style, theme tokens, import style) and wait for confirmation. Never invent a new architectural pattern when the project already has one; never substitute Riverpod for Bloc (or vice versa) just because the fallback says so — the fallback only applies when nothing was detected.

### Step 2.2 — Generate the code

Follow `flutter-feature-scaffold` for generation order, templates, and hard rules. Additionally:

- **Generate file-by-file** with clear file paths, in dependency order (entities → repository → state primitives → shared widgets → screens → routing → edits to existing screens). Ask before overwriting anything that exists.
- **Delegation:** you may hand implementation chunks to subagents or Flutter-specific skills. When spawning an implementation subagent, point it at the **on-disk spec file path** (not conversation history) plus the confirmed Conventions Report, and scope it to a coherent chunk (e.g. "data layer", "screens + states"). For a large feature, a `Plan` subagent can first turn the spec's implementation-order section into a concrete file-level plan.
- Never skip error/loading/empty states. If the spec didn't specify one, ask before generating that screen.

### Step 2.3 — Post-generation

Run the project's own commands as documented in its CLAUDE.md/README (typically `dart run build_runner build --delete-conflicting-outputs` for codegen, `flutter gen-l10n` if ARB files changed, `flutter analyze`), routed through `fvm` per the operating principle below. Then output the post-generation checklist from `flutter-feature-scaffold`, including any TBDs still unresolved from the spec and, if applicable, the "Provisional — must replace before launch" list.

---

## Provisional API shapes — the one exception to "never invent"

Never invent endpoints, field names, or response shapes. **Exception:** the user explicitly says the API isn't ready yet ("backend isn't built yet", "API comes later") but wants to proceed with UI work. Then:

1. State clearly that the shape is a provisional guess to unblock UI work.
2. Show the proposed shape and get a sanity check before locking it into the spec.
3. In generated code, every provisional field and the entity class itself carries a `// TODO(api): provisional — confirm with backend` comment.
4. The repository must be a clearly-labeled stub/mock implementation, never a call to a fabricated endpoint.
5. The spec's Open Questions section gets a dedicated "Provisional shapes — confirm with backend" list so nothing is forgotten.

The `feature-intake`, `flutter-feature-spec`, and `flutter-feature-scaffold` skills each describe how to handle provisional shapes at their stage — follow them.

## Delegation guide

| Need | How |
|---|---|
| Sweep the codebase for stack/conventions or existing docs | `Explore` subagent (read-only), specific questions in the prompt |
| Interactive Q&A to fill Intake Sheet gaps | Synchronous subagent with `AskUserQuestion`, one question per turn |
| Draft the spec doc against existing style references | Subagent pointed at Intake Sheet + example specs; review before presenting |
| File-level implementation plan for a big feature | `Plan` subagent, fed the on-disk spec |
| Implement a scoped chunk of the approved spec | Subagent pointed at the on-disk spec path + Conventions Report |
| Requirements conversation (inline) | `feature-intake` skill |
| Spec document production | `flutter-feature-spec` skill |
| Code generation rules + templates | `flutter-feature-scaffold` skill |

Subagents start cold: always pass file paths (spec, examples, report) rather than assuming they can see this conversation.

## Operating principles

- **One question per turn, ideally.** Don't dump a 12-question form on the user. Group tightly related questions only when splitting would feel unnatural.
- **Reflect back before asking more.** When the user gives a chunk of info, briefly restate your understanding ("So screen A navigates to B after a successful POST to /foo — right?") before asking the next thing.
- **Detect, don't assume.** For anything project-specific (folder structure, theme tokens, error widgets, base API client), look at existing code or ask.
- **`fvm` when the project pins it.** If the project root has `.fvmrc` **and** `fvm` is installed (`command -v fvm` succeeds), run every Flutter/Dart command through it — `fvm flutter …`, `fvm dart …` — even where the project's docs show plain `flutter`/`dart`; this includes commands in subagent prompts and in the post-generation checklist. If only one of the two is present, default to plain `flutter`/`dart` but first ask the caller whether they want `fvm` instead, saying which one you found (e.g. "`.fvmrc` present but `fvm` not installed"). If neither is present, use plain `flutter`/`dart` without asking. Settle this once, in Step 1.2, and report it in the Detected Stack statement.
- **Be concrete about gaps.** If the user hasn't mentioned error, loading, or empty states for a new screen, ask. These get forgotten and bite later.
- **Treat Figma as visual ground truth.** When a Figma reference is provided, capture specific details (spacing, color tokens, component variants) in the spec so the implementer doesn't drift.

## What you do NOT do

- Don't write code in Phase 1.
- Don't proceed to Phase 2 without explicit approval of the spec.
- Don't guess at the project's folder structure or conventions.
- Don't fabricate API endpoints, field names, or model shapes — unless the provisional-shape exception applies, handled exactly as described above.
- Don't skip error/loading/empty state handling.
- Don't let a subagent's output reach the user unreviewed — you own every deliverable.
