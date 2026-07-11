---
name: flutter-feature-scaffold
description: Use this skill to generate Flutter Dart code (entities, repositories, state primitives, screens, routes) for a feature that has already been spec'd and approved. The skill detects the project's tech stack (state management, routing, HTTP client, codegen) from pubspec.yaml and sample files, then mirrors those conventions in generated code. If detection fails, it falls back to Riverpod + go_router + Dio + freezed and announces the fallback openly. Triggers after the spec is approved and the user says "build it", "scaffold the code", "generate the files", or similar. Do NOT use this skill before the spec exists and is approved.
---

# Flutter Feature Scaffold

Generate the Dart files for an approved feature spec. **Detect the project's stack first**, then mirror its conventions.

## Step 1 — Detect tech stack + conventions BEFORE writing any code

Skipping this step is the most common failure mode. Detect before generating.

### Detection sequence (filesystem access)

Read in this order — each step informs the next:

1. **`pubspec.yaml`** — this is the source of truth for the tech stack. Identify:
   - **State management**: look for `flutter_riverpod`, `riverpod_annotation`, `hooks_riverpod`, `flutter_bloc`, `bloc`, `provider`, `get`, `mobx`, `signals`, `stacked`, etc.
   - **Routing**: look for `go_router`, `auto_route`, `beamer`, `routemaster`, or none (Navigator 1.0).
   - **HTTP**: look for `dio`, `http`, `chopper`, `retrofit`.
   - **Serialization / codegen**: look for `freezed`, `json_serializable`, `built_value`, `dart_mappable`, `riverpod_generator`, `auto_route_generator`, `build_runner`.
   - **DI**: look for `get_it`, `injectable`, `kiwi`.
   - **Other relevant**: `flutter_hooks`, `equatable`, `fpdart`/`dartz`.
2. **`lib/` folder structure** — figure out the feature folder convention. Common patterns:
   - `lib/features/<name>/{data,domain,presentation}/`
   - `lib/src/features/<name>/`
   - `lib/<name>/` flat
   - `lib/screens/`, `lib/models/`, `lib/blocs/`, `lib/providers/` split by type
3. **Pick one or two existing features** of similar shape and read end-to-end:
   - An entity file → naming, freezed/manual/built_value, JSON mapping style
   - A repository file → HTTP client usage, error wrapping (throw / `Either` / `Result`), base URL handling
   - A state primitive file → for Riverpod: provider type and annotation style; for Bloc: event/state classes and Cubit vs Bloc; for Provider: ChangeNotifier patterns; etc.
   - A screen file → base widget type (`ConsumerWidget`, `BlocBuilder` + `StatelessWidget`, etc.), state-consumption pattern, error/loading/empty widgets used
   - Theme file → color/spacing/typography token names
4. **Routing config** — find the router file, note how routes are declared (typed routes? plain `GoRoute`? `AutoRoute`? `MaterialPageRoute`?), where the route list lives, any guards/redirects.

### If you do NOT have filesystem access

Ask the user to paste:
- `pubspec.yaml` (or at least the `dependencies:` section)
- One existing feature folder's file tree
- One representative screen file
- The routing config file
- The theme file (if there is one)

Do not proceed without `pubspec.yaml` at minimum.

### Fallback when detection is impossible

If after asking, the user still can't provide enough to detect (or says "I don't know, just pick reasonable defaults"), use this fallback stack and announce it explicitly:

- State management: **Riverpod** — `flutter_riverpod` if no codegen detected, `riverpod_annotation` if `build_runner` is present.
- Routing: **go_router**.
- HTTP: **Dio**.
- Serialization: **freezed + json_serializable** if codegen is present, manual `fromJson`/`toJson` otherwise.

Label every fallback choice as `FALLBACK` in the Detected Stack output so the user knows what wasn't actually detected.

### Output: the Detected Stack + Conventions Report

Before writing any feature code, produce a report. Format:

```
Detected stack:
- State management: <detected value, or "FALLBACK: Riverpod (riverpod_annotation)">
- Routing: <detected value, or "FALLBACK: go_router">
- HTTP client: <detected value, or "FALLBACK: Dio">
- Serialization: <detected value, or "FALLBACK: freezed + json_serializable">
- Codegen tools: <build_runner targets in use, or "none">
- Other relevant packages: <get_it, flutter_hooks, etc.>

Detected conventions:
- Folder pattern: <e.g. lib/features/<name>/{data,domain,presentation}>
- Entities: <e.g. freezed + snake_case JSON keys>
- Repositories: <e.g. throw on error, no Result type; shared ApiClient wraps Dio>
- State primitives: <e.g. @riverpod functions + AsyncNotifier classes>
- Screens: <e.g. ConsumerWidget, AsyncValue.when() pattern with shared LoadingView/ErrorView/EmptyView>
- Routing: <e.g. typed routes via @TypedGoRoute, central router in lib/router/app_router.dart>
- Theme: <e.g. AppColors/AppSpacing/AppTextStyles classes>
- Imports: <package: vs relative>

Going to generate the feature using these. Confirm or correct?
```

Wait for confirmation. Then generate.

### Unsupported stacks

The bundled templates currently cover **Riverpod + go_router + Dio** (with and without codegen). If detection reveals a different stack (Bloc, Provider package, GetX, MobX, auto_route, chopper, etc.), **don't fake it with the Riverpod templates**. Instead:

1. Tell the user what was detected.
2. Ask if they want you to:
   - (a) Generate code from scratch matching the detected stack — you'll use the existing project files as the pattern source rather than the bundled templates. This usually works fine but you'll be writing more of the structure yourself.
   - (b) Switch the project's stack for this feature (rare, usually a bad idea — flag it).
   - (c) Hold off until templates for that stack are added.
3. Proceed only after the user picks.

## Step 2 — Generate file-by-file

For each file:
1. State the path.
2. State whether it's new or modifies an existing file.
3. If modifying, show the diff (or the inserted block + surrounding context).
4. Write the code.
5. Move to the next file.

Do NOT dump 12 files in one message. Group naturally — e.g. "entities + JSON mapping" as one group, "repository + provider" as the next, then "screen + states", then "router wiring", then "modifications to existing screens".

## Step 3 — Generation order

Always follow this dependency order. Concrete class/file names depend on the detected stack — adapt accordingly.

1. **Entities** (and `.g.dart` / `.freezed.dart` / `.mapper.dart` reminders if codegen)
2. **API client / repository** (uses whichever HTTP client is detected — Dio, http, chopper, retrofit)
3. **State primitives** — depends on detected state management:
   - Riverpod → providers (`Provider`, `FutureProvider`, `AsyncNotifier`, or `@riverpod` functions)
   - Bloc → events + states + the Bloc/Cubit class
   - Provider → ChangeNotifier subclass(es)
   - GetX → controllers
   - MobX → stores
4. **Shared widgets** (only if the feature introduces new reusable components)
5. **Screens** — for each screen, build in this internal order (for complicated refreshable scroll views, use the skeleton from "Code style & layout rules" below):
   1. Skeleton with route + Scaffold
   2. State consumption wired to the state primitive (`AsyncValue.when` for Riverpod, `BlocBuilder` for Bloc, `Consumer`/`Selector` for Provider package, `Obx` for GetX, etc.)
   3. Loading state
   4. Error state with retry
   5. Empty state
   6. Success state UI
   7. User actions / navigation
6. **Routing wiring** — add the new routes to whichever router is in use
7. **Modifications to existing screens** — clearly marked as edits, not rewrites

## Step 4 — Reminders that always go at the end

After all files are generated, output:

```
## Post-generation checklist

- [ ] Run `dart run build_runner build --delete-conflicting-outputs` (if using codegen)
- [ ] Run `flutter analyze` and resolve any issues
- [ ] Add any new strings to localization files (if the project uses .arb), then regenerate with `flutter gen-l10n` — ARB→Dart is Flutter's gen-l10n tool (configured via `l10n.yaml`), NOT a build_runner target; build_runner will not pick up ARB changes
- [ ] Manually QA each new screen against the Figma reference
- [ ] Verify error/loading/empty states by simulating network conditions
- [ ] Check that affected existing screens still behave correctly

## TBDs still unresolved from the spec

<list any items still marked TBD>
```

## Templates

Use templates as **starting points only**. Adapt them to match the detected stack and conventions. The bundled templates target the **Riverpod + go_router + Dio** stack — they apply when that's what's detected, or when the fallback is in effect.

- `templates/entity_freezed.dart` — entity with freezed + json_serializable
- `templates/entity_manual.dart` — entity without codegen
- `templates/repository.dart` — Dio-using repository
- `templates/repository_stub.dart` — stub repository for when the API isn't ready yet
- `templates/provider_codegen.dart` — Riverpod with annotation
- `templates/provider_manual.dart` — Riverpod without annotation
- `templates/screen_async.dart` — ConsumerWidget with AsyncValue.when
- `templates/router_route.dart` — go_router route entry

For other stacks (Bloc, Provider, GetX, MobX, auto_route, chopper, etc.) the templates don't apply. Generate from scratch using the existing project files as the structural reference, as described in the "Unsupported stacks" section of Step 1. The dependency order from Step 3 still holds — only the specific class shapes change.

## Code style & layout rules

Apply these to all generated Dart code, on top of the detected conventions:

- **No null-assertion operator (`!`) in hand-written code.** Extract the nullable expression into a local variable, null-check it, then use the promoted local — fields don't promote, so the local is required:

  ```dart
  // Bad:  if (card.foo != null) use(card.foo!);
  // Good:
  final foo = card.foo;
  if (foo != null) use(foo);
  ```

  For nullable-returning calls (e.g. `Color.lerp(...)`), prefer `?? <sensible fallback>` over `!`. Exempt: generated files (`*.g.dart`, `*.freezed.dart`, generated l10n output) and the `is!` type-test operator, which is not a null assertion.

- **Refreshable scroll view skeleton.** For complicated scroll views — heterogeneous blocks, especially with pull-to-refresh — use this structure instead of `ListView`:

  ```dart
  RefreshIndicator.adaptive(
    onRefresh: ...,
    child: SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: SafeArea( // SafeArea is the FIRST child of the scroll view — do not wrap RefreshIndicator with it
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [ /* blocks */ ],
        ),
      ),
    ),
  )
  ```

  Why this shape: `SingleChildScrollView` + `Column` handles heterogeneous blocks better than `ListView`; `AlwaysScrollableScrollPhysics` keeps pull-to-refresh firing when content is shorter than the viewport; `SafeArea` inside the scroll view keeps the refresh spinner positioned correctly while still insetting content; `stretch` makes blocks fill the width the way `ListView` children do. A homogeneous item list may still use `ListView.separated` — but prefer `RefreshIndicator.adaptive` over plain `RefreshIndicator` either way.

## Hard rules

- **Never overwrite existing files without asking.** Show the user the existing file content (or path) and confirm.
- **Never invent API endpoints, field names, or response shapes — except for documented provisional shapes.** If something is TBD in the spec, write a `// TODO(spec): <thing>` and surface it in the post-generation checklist. If something is marked **provisional** in the spec (the API isn't ready yet, but the UI is proceeding):
  - Every field on the provisional entity gets a `// TODO(api): provisional — confirm with backend` comment.
  - The entity class itself gets a class-level comment block stating it's provisional, when it was decided, and that JSON keys may need to change.
  - Generate a stub repository implementing the same interface, returning hardcoded sample data via `Future.delayed(const Duration(milliseconds: 400))` to simulate network latency. Name it `StubExampleRepository`. Place it next to the real repository file (`example_repository.dart` → `example_repository_stub.dart`) or under a `lib/.../stubs/` folder if the project has one.
  - Wire the provider to the stub repository **with a clearly-labeled `// TODO(api): swap to real repository when backend is ready` comment** above the provider definition.
  - Add every provisional file to the post-generation checklist under a dedicated "Provisional — must replace before launch" heading.
- **Never skip error/loading/empty states.** If the spec didn't specify behavior for one of them, ask before generating that screen — don't guess and don't omit.
- **Mirror the project's naming style.** If existing files are `saved_articles_repository.dart` (snake_case), don't generate `SavedArticlesRepository.dart` (PascalCase). If providers are suffixed `Provider`, don't switch to `Notifier`.
- **Match the project's import style.** Some projects use package imports (`package:app/...`), some use relative. Match.
- **Don't introduce new dependencies** without flagging. If the spec implies you need a package not in `pubspec.yaml`, surface it: "This will require adding `cached_network_image` to pubspec.yaml — proceed?"

## When the spec has gaps

If the user says "just build it, fill in the gaps with your best guess" — don't. Instead:
1. List the gaps in one message.
2. Offer a sensible default for each ("for empty state, I'd put 'No saved articles yet' with a 'Browse articles' button — ok?").
3. Wait for the user to confirm each default before generating that part.

This keeps the user in the loop without making them write every detail upfront.
