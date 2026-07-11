---
name: flutter-feature-spec
description: Use this skill to produce a structured feature specification markdown document for a Flutter feature, after requirements have been gathered (typically via the feature-intake skill). Triggers when the user says "write the spec", "produce the spec doc", "summarize the requirements", or when the Intake Sheet is fully populated and ready to become a deliverable. The output is a single `feature-spec.md` file detailed enough that another engineer (or a coding agent) could implement the feature without further questions. Do NOT use this skill to gather requirements (use feature-intake) or to write Dart code (use flutter-feature-scaffold).
---

# Flutter Feature Spec

Turn a populated Intake Sheet into `feature-spec.md` — a single markdown document detailed enough that another engineer or a coding agent can implement the feature without further questions.

## The output template

Always use this exact structure. Use `feature-spec.md` as the filename.

```markdown
# Feature: <Feature Name>

## 1. Summary
- **Purpose**: <one sentence>
- **User outcome**: <what the user can now do>
- **Entry points**: <where in the app this feature is reached from>

## 2. Routes

### New routes
| Path | Screen | Purpose | Params |
|---|---|---|---|
| `/example` | `ExampleScreen` | ... | `id` (path) |

### Routing wiring
> Heading suffix should name the detected library, e.g. `### Routing wiring (go_router)` or `### Routing wiring (auto_route)`.

- Where in the existing route tree this attaches (parent shell, guards, etc.)
- Any new redirects or guards
- Whether routes are typed (`@TypedGoRoute`, `@RoutePage`) or plain

## 3. Affected existing screens
For each affected screen:
- **`<ScreenName>` (`lib/.../existing_screen.dart`)**
  - Change: <what's added/modified>
  - Reason: <why>
  - Risk: <what could break>

## 4. Data layer

### Entities
```dart
// Sketch only — actual code generated in Phase 2
class SavedArticle {
  final String id;
  final String articleId;
  final DateTime savedAt;
}
```
For each entity: fields, types, nullability, JSON mapping notes.

### API endpoints
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/saved-articles` | Bearer | List saved |

For each endpoint:
- Request shape (query, body)
- Response shape (success + each error)
- Error codes the UI must handle distinctly

### Repository
- Repository class name + responsibilities
- Which HTTP client / interceptors it uses (Dio, http, retrofit, chopper — match what the project uses)

## 5. State management

> Heading suffix should name the detected library, e.g. `## 5. State management (Riverpod)` or `## 5. State management (Bloc)`. Below table columns adapt to the stack — examples for the common cases follow.

**Riverpod example:**

| Provider | Type | Watches | Exposes |
|---|---|---|---|
| `savedArticlesProvider` | `AsyncNotifierProvider` | `repo` | `AsyncValue<List<SavedArticle>>` |

For each provider: type (Provider / FutureProvider / StreamProvider / NotifierProvider / AsyncNotifierProvider), dependencies, mutation methods (if Notifier), caching / invalidation behavior.

**Bloc example:**

| Bloc/Cubit | Events | States | Notes |
|---|---|---|---|
| `SavedArticlesCubit` | `load`, `refresh`, `remove(id)` | `Initial`, `Loading`, `Loaded(items)`, `Error(msg)` | Depends on `SavedArticlesRepository` |

For each Bloc/Cubit: events handled, states emitted, dependencies, side effects, when it's provided in the widget tree.

**Provider package / ChangeNotifier example:**

| Notifier | Methods | Properties | Notes |
|---|---|---|---|
| `SavedArticlesModel` | `load()`, `remove(id)` | `items`, `isLoading`, `error` | Provided in `MaterialApp` scope |

Use the format that matches the detected stack. If the stack is something not shown here, follow the same idea: name the state primitive, what it exposes, what it depends on, and its lifecycle / invalidation behavior.

## 6. UI behavior per screen

For each new or modified screen:
- **Initial state**: <what loads first>
- **Loading state**: <skeleton / spinner / shimmer>
- **Error state**: <retry? toast? full-screen?>
- **Empty state**: <copy + CTA if any>
- **Success state**: <what's shown>
- **User actions**: <list of taps/gestures and their results>
- **Navigation triggers**: <when does this screen push/pop/replace>
- **Side effects**: <analytics events, snackbars, dialogs>

## 7. Design references
- Figma frames: <links>
- Reused components: <list from existing design system>
- New components: <list, with one-line description each>
- Specific tokens: <spacing, color, typography callouts>
- Motion / animation: <any specified>

## 8. Open questions / TBDs
- [ ] <unresolved item 1>
- [ ] <unresolved item 2>

## 9. Out of scope
Explicit list of things this spec does NOT cover, to prevent scope creep during implementation.

## 10. Implementation order (suggested)
1. Entities + JSON mapping
2. Repository + HTTP client wiring
3. State primitives (providers / blocs / notifiers — match the detected stack)
4. New screen(s) — skeleton first, then states
5. Wire routing (go_router / auto_route / etc.)
6. Modify affected existing screens
7. Manual QA pass against Figma
```

## Writing the spec — guidelines

- **Be specific, not aspirational.** "Show a friendly error" → bad. A good version names the actual widget and the actual call — e.g. for a Riverpod project: "Show `ErrorView` (existing) with retry button that re-invokes `savedArticlesProvider.future`"; for a Bloc project: "Show `ErrorView` (existing) with retry button that dispatches `SavedArticlesEvent.refresh()`". Match the project's stack.
- **Quote the user's words for tricky business logic.** Don't paraphrase rules; the original phrasing is the contract.
- **Mark every unknown as a TBD checkbox in section 8.** Don't bury unknowns inside prose where they'll be missed.
- **Always include section 9 (Out of scope).** Even if it's just "no offline support in v1." This is where future scope arguments die before they start.
- **Implementation order matters.** Section 10 isn't decoration — it's the dependency order for the coding agent.

## When the user wants a lighter spec

If the feature is genuinely small (e.g. "add a toggle to settings that calls one API"), collapse sections that don't apply but **keep the structure**. Don't delete sections silently — write "N/A — single-screen toggle, no new routes" so the reader knows it was considered.

## When fields are still unknown

For each unknown, write the explicit string `TBD` in the cell or prose, and add a checkbox in section 8. Never invent values. Never write "probably something like `{id, name}`" — write `TBD` and ask.

## When the API is explicitly not ready yet

If the user has told you the backend isn't built yet and they want to proceed with provisional shapes (this should already have been flagged during intake), handle it differently from a TBD:

1. **In the Entities subsection (section 4),** write the provisional shape as a normal entity but prefix the section heading with `(Provisional — API not yet built)` and add a one-line note explaining the source: "Shape inferred from UI needs and confirmed with the user on <date>."
2. **In the API endpoints table,** write `PROVISIONAL` in the Path column and use a placeholder like `/articles (provisional)`. In the request/response shape descriptions, write "Mirrors entity shape above — to be confirmed once backend exists."
3. **In the Repository description,** explicitly say: "Implementation should be a stub returning hardcoded sample data (or `Future.delayed` to simulate latency) until the API is ready. Stub class name: `StubExampleRepository implements ExampleRepository`."
4. **In section 8 (Open Questions),** add a dedicated subsection:
   ```
   ### Provisional shapes — confirm with backend before launch
   - [ ] `Article` entity field set and JSON keys
   - [ ] `GET /articles` actual path, query params, pagination shape
   - [ ] Error response format
   ```
5. **Never mix provisional and confirmed entities silently.** Every provisional thing must be visually marked so a reviewer scanning the spec sees it immediately.

This distinction matters: a TBD blocks progress until resolved. A provisional shape unblocks UI work today but creates a debt that must be paid before launch. Both need to be tracked, but differently.

## Handoff

After producing `feature-spec.md`:
1. Save it to the working directory (or present it to the user if no filesystem).
2. Show the user the **Open Questions** section explicitly: "Here are the TBDs that need resolving before code: ..."
3. Ask: "Approve this spec? Once you approve, I'll move to scaffolding the Dart code."
4. **Wait for explicit approval.** "ok" alone is not enough — confirm: "Just to confirm, you'd like me to proceed with code generation based on this spec?"
