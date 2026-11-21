---
name: feature-spec
description: Write the spec document for a mobile app feature once its requirements are gathered (a populated Intake Sheet). For "write the spec". Do NOT use to gather requirements (feature-intake) or write code (feature-scaffold).
---

# Feature Spec

Turn a populated Intake Sheet into a spec — a single markdown document detailed enough that another engineer or a coding agent can implement the feature without further questions.

**Platform adapter.** Platform knowledge lives in the plugin's adapters, one per platform: `${CLAUDE_SKILL_DIR}/../../platforms/<platform>/PLATFORM.md`. Find the one this project needs with `grep -H -A2 '^## Applies when' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`, and use the adapter whose condition the project meets; if several do, ask which one the feature is built with. If none does, or the `platforms/` folder is missing, say so and stop. To read only some of its sections, take their line ranges from `grep -n '^## ' <adapter>`.

When `feature-workflow` invoked this skill, use the adapter it loaded. This skill needs only the adapter's "Stack layer" and "Spec notation": the template's platform-dependent parts (sections 2 to 5, 7 and 10, and the platform ids of section 6) follow the adapter's "Spec notation". A spec whose `test` anchors name existing tests (a baseline, a conversion from bullets) also needs the **Test-name search** line of its "Commands".

## The output template

Always use this exact structure. Name a new spec's file `<feature-slug>-feature-spec.md`, with the slug of its requirement ids (section 6's `id`), so that features don't share a file, unless the caller names another or the project's existing specs share another naming (Handoff); an update keeps the file it changes.

The one addition the structure allows is an unnumbered `## Appendix — <title>` after section 10, for material kept word for word for another team, such as an edge-case table a converted doc held (`${CLAUDE_SKILL_DIR}/conversion.md`).

```markdown
# Feature: <Feature Name>
> Last verified: never (not implemented)

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
- Whether routes are typed or plain
- Deep links: <which routes open from outside the app (link, notification), the link shape, and what a missing target or a signed-out user sees; leave this line out when section 9 names deep links>

## 3. Affected existing screens
For each affected screen:
- **`<ScreenName>` (`<path to its file>`)**
  - Change: <what's added/modified>
  - Reason: <why>
  - Risk: <what could break>

## 4. Data layer

### Entities
<a sketch of each entity in the adapter's notation — actual code is generated in Phase 2>

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
- Which HTTP client / interceptors it uses (match what the project uses)

### Native interfaces
| Interface | Method | Arguments → result | Errors | Platforms |
|---|---|---|---|---|
| `ExampleScannerApi` | `scan()` | none → `ScannedCode?`, null when the user cancels | `cameraUnavailable` | ios, android |

For each interface: its mechanism in the adapter's notation, anything the native side sends back later (events, callbacks), the thread or queue each method runs on, and how each error reaches the caller. Leave this subsection out when section 9 names native code.

### Permissions & capabilities
| Platform | Key | Usage string | Requested when |
|---|---|---|---|
| ios | `NSCameraUsageDescription` | "Scan codes with the camera." | the user first taps Scan |
| android | `android.permission.CAMERA` | — | the user first taps Scan |

One row per platform and key, capabilities included (a background mode, an entitlement), with `—` where the system shows no usage string. What the user sees after a denial is a section 6 scenario. Leave this subsection out when section 9 names permissions.

## 5. State management

> Heading suffix should name the detected library, e.g. `## 5. State management (Riverpod)`. The table's columns follow the adapter's notation for that library.

| <State primitive> | <columns for the detected library> |
|---|---|

For each state primitive: what it exposes, what it depends on, its mutations or events, and its lifecycle / invalidation behavior.

**Offline and resume:** <what is cached and shown without a network, what refreshes when the app returns to the foreground, and what happens to work in flight; leave this note out when section 9 names both offline and background / resume>

## 6. UI behavior per screen

### Requirement: Saved list loads when SavedArticlesScreen opens
<!-- id: saved-articles.1 -->
<!-- screen: SavedArticlesScreen -->
<!-- entities: SavedArticle -->
<!-- enforced: (filled in Phase 2) -->

The screen SHALL request the user's saved articles when it opens.

#### Scenario: Loading
<!-- test: (filled in Phase 2) -->
- **WHEN** the request is in flight
- **THEN** the existing `SkeletonList` is shown

#### Scenario: Error
<!-- test: (filled in Phase 2) -->
- **WHEN** the request fails
- **THEN** `ErrorView` (existing) is shown with a retry button that repeats the request

#### Scenario: Empty
<!-- test: (filled in Phase 2) -->
- **WHEN** the request succeeds with zero items
- **THEN** `EmptyView` shows the empty copy with a "Browse" button that opens `/articles`

#### Scenario: Success
<!-- test: (filled in Phase 2) -->
- **WHEN** the request returns items
- **THEN** they are listed newest `savedAt` first

### Requirement: Swiping an item unsaves it
<!-- id: saved-articles.2 -->
<!-- screen: SavedArticlesScreen -->
<!-- entities: SavedArticle -->
<!-- enforced: (filled in Phase 2) -->

Swiping a list item SHALL remove that article from the saved list.

#### Scenario: Unsaved
<!-- test: (filled in Phase 2) -->
- **WHEN** the user swipes an item and `DELETE /saved-articles/{id}` succeeds
- **THEN** the item leaves the list
- **AND** a "Removed" snackbar is shown
- **AND** the analytics event `saved_article_removed` is logged with `article_id`

#### Scenario: Error — unsave fails
<!-- test: (filled in Phase 2) -->
- **WHEN** the delete request fails
- **THEN** the item returns to its place and a snackbar shows the error

### Invariant: An article is saved at most once
<!-- id: saved-articles.3 -->
<!-- entities: SavedArticle -->
<!-- enforced: (filled in Phase 2) -->

The saved list SHALL never hold two entries with the same `articleId`.

#### Scenario: Already saved
<!-- test: (filled in Phase 2) -->
- **WHEN** the user saves an article that is already in the list
- **THEN** the list still holds one entry for it

## 7. Design references
- Figma frames: <links>
- Reused components: <list from existing design system>
- New components: <list, with one-line description each>
- Specific tokens: <spacing, color, typography callouts>
- Motion / animation: <any specified>
- Accessibility: <screen-reader labels, tap targets, text scaling — or the existing practice it follows; leave this line out when section 9 names accessibility>
- Localization: <languages, where new strings go (e.g. ARB keys), date and number formats; leave this line out when section 9 names localization>

## 8. Open questions / TBDs
- [ ] <unresolved item, e.g. "`SavedArticle.savedAt` timezone">
- [ ] <section 6 item: id + scenario, e.g. "saved-articles.1 Empty: empty-state copy">

## 9. Out of scope
Explicit list of things this spec does NOT cover, to prevent scope creep during implementation.
- Not affected: <non-functional topics that don't apply> — <reason>

## 10. Implementation order (suggested)
<numbered steps in the adapter's generation order, each layer's tests right after it, ending with a manual pass against the design; for Flutter:>
1. Entities + JSON mapping
2. Repository + HTTP client wiring, then its tests
3. Native interfaces, when section 4 has them — the Dart interface, each platform's side, then the Dart side's tests
4. State primitives (providers / blocs / notifiers — match the detected stack), then their tests
5. New screen(s) — skeleton first, then states, then their widget tests
6. Wire routing (go_router / auto_route / etc.)
7. Platform declarations, when section 4 lists permissions or capabilities
8. Modify affected existing screens, with the tests that cover the change
9. Manual QA pass against Figma, and on a device for native work

### Test plan
<one line per test kind the adapter's "Spec notation" lists, then Manual; for Flutter:>
- **Unit**: <repository and state primitives; what is faked and how, e.g. a hand-written `FakeSavedArticlesRepository`, or `mocktail`>
- **Widget**: <each screen's state and action scenarios; how the screen is pumped, e.g. with the list provider overridden>
- **Golden**: <which screens, or `N/A — the project has no golden tests`>
- **Integration**: <which flows, or `N/A — <reason>`>
- **Manual**: <what only a person can check: the section 6 scenarios marked `test: manual`, the Figma pass>
```

## Section 6 — Requirement and Scenario blocks

Section 6 consists only of blocks; a block may also hold a bug fix's change record ("Change records"). When a project's own spec layout replaces this template (`feature-workflow` Step 1.4), the blocks go in its screen-behavior section, or in a section added for them if it has none.

- **Requirements.** One `### Requirement: <title>` per behavior; the title says what happens and when. Group them by screen, in the order the screens appear in sections 2 and 3, then the requirements with `screen: none`, before the invariants. For an affected screen outside the feature (section 3), write only the behavior the change adds or alters. After the comments, one normative sentence states the behavior (SHALL, or its equivalent in the spec's language).
- **Comment keys**, directly under the heading, in this order:
  - `id` — `<feature-slug>.<n>`. The slug is the one the Intake Sheet was saved under (`.mobile-dev-skills/<feature-slug>/intake.md`), or else the feature name in lowercase ASCII kebab-case (for a non-Latin name, an English rendering that matches the spec file's name when it has one). It stays fixed for the life of the spec, even if the feature is renamed. A new block takes the highest `n` in the file plus one, counting any block the same edit removes. Ids are never renumbered: rewording or renaming a requirement keeps its id, and a deleted block's gap stays.
  - `screen` — the screen class from section 2 or 3, or several, comma-separated; `none` for a requirement with no screen of its own (a background task, a notification, a service).
  - `entities` — the section 4 entities involved, or `none`.
  - `enforced` — `(filled in Phase 2)`, or, for behavior already in the code, `<path>#<Symbol>`: the project-relative file plus the class, method (`Class.method`) or provider that carries it. Comma-separate several; never a line number, or a name that exists only in generated code.
- **Scenarios.** `#### Scenario: <title>` blocks under a requirement. Each one, unless it is `N/A` (below), starts with its `test` comment (after its `platform` comment, when it has one), `<!-- test: (filled in Phase 2) -->`, `<!-- test: manual — <reason> -->` or, for a test the user skipped, `<!-- test: none — <reason> -->` (in a baseline, below, or a conversion from the bullet format, an existing test or `none`), then `- **WHEN** <trigger>` and `- **THEN** <result>` lines, optionally `- **GIVEN** <precondition>` before WHEN and `- **AND** <further result>` after THEN. Each line states one observable fact.
- **Four states per screen.** Across its requirements, every new or modified screen has scenarios titled `Loading`, `Error`, `Empty` and `Success`; a variant adds a qualifier, as in `Error — session expired`. A state that can't occur, or that a modified screen's change doesn't touch, gets the body `N/A — <reason>` in place of WHEN/THEN and no `test` comment; several such states may share one scenario whose title lists them, as in `#### Scenario: Loading, Empty`. A requirement with `screen: none` has no screen, so no states to give.
- **Per-platform behavior.** A scenario that holds on some platforms only carries `<!-- platform: <id> -->` directly under its heading, with the ids of the adapter's "Spec notation" (comma-separated for several); an `N/A` scenario may carry one too. A scenario without it holds on every platform. When a state or action differs per platform, give each platform its own scenario, its title qualified to tell them apart, as in `#### Scenario: Error — permission denied (iOS)`.
- **Actions, navigation and side effects are scenarios too.** Each user action (tap, gesture, pull-to-refresh, pagination) has its result in a THEN/AND line, either in a scenario of its own or in the scenario it belongs to, like a retry button in `Error`. THEN/AND lines also name the route an action opens (from section 2) and any analytics event, snackbar or dialog.
- **Invariants.** Always-true rules from the Intake Sheet's Binding logic (limits, ordering, consistency across screens) become `### Invariant: <title>` blocks after the requirements. They carry `id`, `entities` and `enforced` (plus `screen` when screen-bound) and a SHALL sentence. Scenarios are optional, but tests anchor to scenarios, so a rule a test can exercise gets one. An invariant is a rule that always holds; behavior with a trigger (an event, a schedule, a background wake) is a requirement, with `screen: none` when no screen shows it.
- **Tests.** Phase 2 writes an automated test for every scenario that isn't `N/A` or `manual`, of the kind section 10's Test plan gives its layer. Mark a scenario `manual` only when no test in this project can reach it (the system permission dialog itself, though not what the app does with its answer; a push arriving; how something looks on a real device), and give the reason. The user approves each one with the spec.
- **Skipped tests.** When delivery matters more, the user may skip a scenario's test, before approval or during Phase 2: its `test` becomes `none — <reason>`, the reason in the user's words. It blocks no run, and a later missing-tests request (`feature-workflow`) can add the test. Until then it is a `no test` finding, so `feature-verify` leaves `Last verified` undated.
- **`TBD` and `PROVISIONAL`** keep their meaning inside WHEN/THEN text. Each TBD also gets its section 8 checkbox naming the id and scenario.
- **Fixed syntax.** The heading keywords, the state words that start state scenario titles, the bold GIVEN/WHEN/THEN/AND, the comment keys, the values `(filled in Phase 2)`, `none`, `manual` and `N/A`, the platform ids, the `Last verified` line, and the words `deliberately deferred` and `declined` that settle a section 8 item stay in English in every spec. Other title text, statements, WHEN/THEN text and a `manual` or `none` reason follow the spec language rule.
- **`Last verified`.** A new spec says `never (not implemented)`, or `never (implemented, not yet verified)` when it records behavior already in the app. From then on Phase 2 (`feature-scaffold`) and the conformance check (`feature-verify`) own the line; spec edits leave it alone.

## Section 10 — Test plan

The `### Test plan` subsection says how this feature is tested in this project, layer by layer. It doesn't list tests: section 6 already holds one `test` comment per scenario.

- **Source.** The Detected Stack's `Test packages` line and the test conventions (`.mobile-dev-skills/stack.md`, or the pre-rename `.flutter-skills/stack.md` in a project that has only that folder, or the conversation). Without them, read the manifest's dev dependencies and one existing test. A project with no tests to mirror gets the adapter's fallback test stack ("Stack layer"; for Flutter, `flutter_test` with hand-written fakes), stated as a default.
- **Lines.** One per test kind the adapter's "Spec notation" lists (for Flutter: Unit, Widget, Golden, Integration), then Manual. A kind the project doesn't use, or the feature doesn't need, says `N/A — <reason>`; a kind the adapter lists only under a condition is left out while the condition doesn't hold.
- **A project's own layout** (`feature-workflow` Step 1.4): put the plan in its testing section, or at the end of its implementation section.

## Non-functional topics

The Intake Sheet covers the same topics (`feature-intake`). Write each answered topic where this table says.

| Topic | Where the spec answers it |
|---|---|
| Offline / poor network | Section 5's offline-and-resume note, plus an `Error — offline` scenario wherever a screen behaves differently offline |
| Deep links | Section 2 routing wiring |
| Permissions | Section 4's permissions table, a row per platform and key with its usage string; section 6 scenarios for the request and for denial (`Error — permission denied`) |
| Native code & platform differences | Section 4's native interfaces table; section 6 scenarios tagged with their platform wherever behavior differs |
| Analytics events | Section 6 THEN/AND lines, each event with its parameters |
| Accessibility | Section 7 accessibility line |
| Localization | Section 7 localization line |
| Background / resume | Section 5's offline-and-resume note, plus a scenario wherever the user sees the effect |
| Push notifications | Section 1 entry points, section 2 routing wiring for the route a tap opens, and section 6 scenarios for a push arriving while the screen is open and for the tap |

- **Not applicable or cut.** Name a topic that doesn't apply, or that the user explicitly cut, in section 9 with its reason, e.g. `- Not affected: push notifications, deep links — settings toggle only`, and leave out its template part (section 2's deep links bullet, section 4's native interfaces or permissions subsection, section 5's offline-and-resume note, section 7's accessibility or localization line). A topic is answered or in section 9, never both.
- **Unanswered.** A topic that applies but that nobody answered or cut is a section 8 TBD, not an out-of-scope entry.
- **Updates** cover only the topics the change touches.
- **A project's own layout** (`feature-workflow` Step 1.4): answer each topic in the closest section, and name the ones that don't apply in its out-of-scope section, adding one if it has none.

## Quality check — before every approval question

Run it on the saved spec file, not from memory of writing it: in this skill's Handoff, in `feature-workflow` Step 1.6, and again whenever the spec changed since the last run, but never twice on an unchanged file. For an update to an existing spec, check what the change adds or alters.

**The script decides checks 1 and 6.** Run `bash ${CLAUDE_SKILL_DIR}/scripts/check_spec.sh --adapter <the adapter's PLATFORM.md> <spec path>` first, adding `--own-layout` when the spec follows a project's own layout (`feature-workflow` Step 1.4). Reading the spec never stands in for running it.
- Each `FINDING=<check> <line> <message>` line is a finding: `states` of check 1; `syntax`, `items` and `layout` of check 6. What the script passes is no finding of either.
- A `layout` finding that names section 9 is check 5's double answer: a topic section 9 names as not affected that still has its template part. The script finds it only in the template layout and only for English topic names on a `- Not affected:` line, so check 5 stays yours.
- It checks the whole file. In an update, a `states` finding on a screen the change doesn't touch is older: name it in your reply and leave that screen alone; it isn't new on later runs.
- The last line, `RESULT=pass|fail findings=<n> blocks=<n> scenarios=<n> open=<n>`, goes in your reply whole. `open` counts the unticked section 8 items not marked `— deliberately deferred` or `— declined` (`feature-workflow` Step 1.6), outside a `### Provisional shapes` list.
- Exit 4 is a usage error, never a result: fix the call and run it again.

1. **States.** Every new or modified screen has `Loading`, `Error`, `Empty` and `Success` scenarios, or `N/A — <reason>`. A requirement with `screen: none` has none to check.
2. **Endpoint errors.** Every request the feature makes has a scenario for its failure (a screen's `Error` scenario covers the request that loads it), and every error case that section 4 says the UI must handle distinctly has its own.
3. **Action results.** Every user action (tap, gesture, pull-to-refresh, pagination, submit) has a THEN/AND result.
4. **No vague words.** No untestable qualifier (fast, smooth, nice, user-friendly, intuitive, properly, as usual, or its equivalent in the spec's language) stands where a value, a widget, copy or a named existing behavior belongs. Quoted user wording is exempt.
5. **Non-functional topics.** Each topic is answered where the table above says or named in section 9, never both.
6. **Block syntax and layout.** Ids are unique and match `<feature-slug>.<n>`. Comment keys are present and in order. Every scenario that isn't `N/A` has a `test` comment, WHEN and THEN, and a `manual` test comment gives its reason. A `platform` comment names ids from the adapter's "Spec notation". Each section 8 item about section 6 names an id that exists, and each block that holds a `TBD` is named by one. The `Last verified` line, a bug-fix record's label and a baseline's section 8 items keep their forms, and the template layout keeps its ten sections.
7. **Platform work.** Each section 4 permission row names its platform, key, usage string (`—` where the system shows none) and when it is requested, and each permission the user can deny has a denial scenario. Each native interface method names its arguments, result, errors and platforms, and each of its errors that the UI handles has a scenario.

A section 6 kept in the bullet format (`SECTION6=bullets`): the script checks only the layout and section 8, so check 1 is yours. Wherever these checks or the topics table say scenario or THEN/AND line, the matching bullet counts (a state bullet, or a user-action or side-effect bullet with its result).

Handle each finding as follows:
- **Fix in place:**
  - a check 6 finding (the script's `syntax`, `items` and `layout`);
  - check 5's double answer: leave out the template part, or, when that part states something the feature does, take the topic out of section 9;
  - a slip that the Intake Sheet or the user's own words already answer;
  - a topic that clearly doesn't apply, named in section 9 with a reason the spec itself shows (e.g. "no new routes").
- **Everything else becomes a TBD for the loop.** A missing state, failure or action result becomes its scenario or THEN/AND line with `TBD` in it, under a new requirement whose statement is `TBD` if the screen has none. Each of these findings gets a section 8 checkbox, naming the id and scenario when it is in section 6. Never resolve a finding by guessing. Copying another scenario's behavior or copy is a guess too: when a sibling scenario suggests the answer, the section 8 item offers it as a proposal the user can confirm in one word, e.g. `` `<id> Error — refresh fails`: the same snackbar as `<id> Error`? ``.
- **Not new:** a finding already in section 8, whether open, deliberately deferred or marked declined by the user.

Report the result in your reply, never in the spec:
- a one-line count, e.g. `Quality check: 3 findings added to section 8, 1 fixed` or `Quality check: passed`, and the script's `RESULT=` line from its last run;
- each in-place fix;
- for an update, the topics judged untouched by the change.

## Writing the spec — guidelines

- **Follow the spec language rule**, in this document and every later edit to it.
  Spec language rule (plugin option `spec_language_rule`): [${user_config.spec_language_rule}] — apply it to all spec text you write or rewrite, except quoted user wording, which stays exactly as the user wrote it. Empty brackets mean no rule. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use the default, "Chinese text must be Traditional Chinese (zh-Hant) only, never Simplified."
- **Be specific, not aspirational.** "Show a friendly error" → bad. A good version names the actual widget and the actual call in the project's stack — the adapter's "Spec notation" gives examples.
- **Quote the user's words for tricky business logic.** Don't paraphrase rules; the original phrasing is the contract.
- **Mark every unknown as a TBD checkbox in section 8.** Don't bury unknowns inside prose where they'll be missed.
- **Always include section 9 (Out of scope).** Even if it's just "no offline support in v1." This is where future scope arguments die before they start. It also names the non-functional topics that don't apply.
- **Implementation order matters.** Section 10 isn't decoration — it's the dependency order for the coding agent.

## When the user wants a lighter spec

If the feature is genuinely small (e.g. "add a toggle to settings that calls one API"), collapse sections that don't apply but **keep the structure**. Don't delete sections silently — write "N/A — single-screen toggle, no new routes" so the reader knows it was considered. Section 6 still uses blocks whenever screen behavior changes, however small: the toggle is one requirement, and states that can't occur are `N/A — <reason>` scenarios. The non-functional topics that don't apply usually fit on one section 9 line.

## When updating an existing spec

- **Edit blocks in place.** Changed behavior stays in its block, under the same id. New behavior takes the next id. Removed behavior loses its block; the other ids stay as they are. A state scenario that is cut becomes `N/A — out of scope`. Anchors already filled stay as they are; Phase 2 updates them.
- **No `### Test plan` yet** (a spec from before tests were planned): add it with the first change that adds or alters a scenario.
- **No section 4 native interfaces or permissions subsection yet** (a spec from before they existed): add one with the first change that needs it, and move into it any permission the spec states elsewhere, such as a section 10 declaration step. Don't add either for a change that needs neither.
- **Section 6 from before the block format** (a bullet list per screen): before applying the change, ask once whether to convert it to blocks, and recommend converting. The conversion is a reformat that changes no behavior, and the user sees it as its own change before the delta goes in. When the user agrees, read `${CLAUDE_SKILL_DIR}/conversion.md` and convert by it, the layout first when the spec's sections aren't the ten. If the user declines, edit in the bullet format.
- **A bug fix** (`feature-workflow`) corrects the scenario the bug shows to be vague or wrong, in its block under the same id, or adds one for a case no scenario covered, under its requirement or a new one with the next id. When a scenario already states the right behavior, its text stays as it is. Either way it adds its change record (below).
- **A refactor** (`feature-workflow`) changes only the sections that describe the code it moves (section 4's repository or native interfaces, section 5's state primitives, section 2's routing wiring, and section 10's Test plan where its pin tests make it untrue) and nothing in section 6, then adds its change record.

- **A sub-feature of a Large change** (`feature-workflow` Step 1.1) changes the blocks of this spec that its own screens affect: those blocks are edited in place under the same ids, each with a pointer to the sub-feature's spec (a line, or inline as the project's specs point to each other), every changed scenario's anchors reset to `(filled in Phase 2)`, and the TBDs the block still holds kept in this spec. This spec's index row goes to `draft`. A changelog entry goes here only when the user said yes to it, which `feature-workflow` asks once per sub-feature before the writing starts.

## Change records

`feature-workflow`'s bug fixes and refactors record why the spec changed, next to the change, as one blockquote:

- **Bug fix**, directly under the statement of the requirement whose scenario it corrects, adds or restores: `> **Bug fix <YYYY-MM-DD> — <title>:** <steps> → expected <…>, actual <…>. Cause: <path>#<Symbol> — <why>. <id> <Scenario>: corrected | added | restored.`
- **Refactor**, directly under the heading of the first section it changes: `> **Refactor <YYYY-MM-DD> — <title>:** <why>. Sections <n, …> changed; section 6 unchanged. Pinned: <id> (<Scenario>, …), or none; left unpinned: <id> (<Scenario>, …), or none.`

The part before the colon is the record's label, which the workflow's task file and run report quote. A record isn't part of the current state: later edits leave it alone, and `feature-spec-compact` removes it, or extracts it to the changelog, once its change is built. Until then the workflow resumes, reports and reviews the change by it, so compaction keeps the newest one while the spec's index row says `draft` or `approved`. `Bug fix`, `Refactor`, the date, `corrected`, `added`, `restored`, `Pinned:` and `left unpinned:` stay in English; the rest follows the spec language rule, and quoted user wording stays as written.

## A baseline of existing code

`feature-workflow` (Step 1.1) writes one when a feature that was never specced is about to change: its current behavior, read from its code and saved as its spec, which the change then updates.

- **Only what the code shows.** Every block's `enforced` names the code that carries it; behavior whose code can't be named gets no block. A scenario's `test` is an existing test whose body checks it, by its description's text as its file writes it, without the quotes or backticks around it, so that the adapter's **Test-name search** finds it; a description with an escape or an interpolation in it can't be anchored. Otherwise `none`.
- **`Last verified`:** `never (implemented, not yet verified)`.
- **The other sections describe what exists:** section 1 what the feature does and where it's reached from, section 2 the routes of the screens it covers (new to the spec), section 3 `N/A — baseline`, sections 4 and 5 the code's entities, endpoints, repository and state, section 7 the components, tokens and strings it uses, and section 10 `N/A — the code exists` for the order, with a Test plan for the project's existing tests. Each non-functional topic the feature can meet is answered with what the code does, even when that is nothing (no screen-reader labels, no offline handling); section 9 names only the topics that can't arise here.
- **Gaps are section 8 items**, never guesses:
  - `- [ ] <id> <Scenario>: uncertain — <what the code didn't settle, and why>`, a fact the reading didn't settle, written `TBD` where it belongs; outside section 6, the item names its section and field in place of the id and scenario;
  - `- [ ] Unplaced: <path>#<Symbol> — <what it seems to do, and why that's unconfirmed>`, behavior with no block yet, which names code rather than an id;
  - `- [ ] Not read: <path>, … — <what they seem to hold>`, one item for the feature's files the reading left out (a folder stands for its files).
- **Later edits** settle them like other TBDs: an answer replaces the `TBD` and closes its item, an `Unplaced:` item becomes a block with the next id or is dropped, and a file read for a later change is taken off the `Not read:` item, which goes once it's empty.
- `uncertain`, `Unplaced:` and `Not read:` are fixed syntax, in English in every spec.

## When fields are still unknown

For each unknown, write the explicit string `TBD` in the cell or prose, and add a checkbox in section 8. Never invent values. Never write "probably something like `{id, name}`" — write `TBD` and ask.

## When the API is explicitly not ready yet

If the user has told you the backend isn't built yet and they want to proceed with provisional shapes (this should already have been flagged during intake), handle it differently from a TBD:

1. **In the Entities subsection (section 4),** write the provisional shape as a normal entity but prefix the section heading with `(Provisional — API not yet built)` and add a one-line note explaining the source: "Shape inferred from UI needs and confirmed with the user on <date>."
2. **In the API endpoints table,** write `PROVISIONAL` in the Path column and use a placeholder like `/articles (provisional)`. In the request/response shape descriptions, write "Mirrors entity shape above — to be confirmed once backend exists."
3. **In the Repository description,** explicitly say: "Implementation should be a stub returning hardcoded sample data after a simulated delay until the API is ready. Stub class name: `StubExampleRepository`, implementing `ExampleRepository`."
4. **In section 8 (Open Questions),** add a dedicated subsection, its heading in English so the quality check's open count leaves its items out:
   ```
   ### Provisional shapes — confirm with backend before launch
   - [ ] `Article` entity field set and JSON keys
   - [ ] `GET /articles` actual path, query params, pagination shape
   - [ ] Error response format
   ```
5. **Never mix provisional and confirmed entities silently.** Every provisional thing must be visually marked so a reviewer scanning the spec sees it immediately.

**A new field on an endpoint that exists**, which the backend doesn't accept or return yet, is marked on its own:
- The endpoint keeps its real path in the API endpoints table, without `PROVISIONAL`, and the entity's heading gets no prefix.
- The field is marked `PROVISIONAL` in its entity's sketch and in the request or response shape, and one line under that entity names its provisional fields and their source.
- The field goes in section 8's `### Provisional shapes` list.
- The repository stays the real one, with no stub. What it sends until the backend accepts the field (the field left out, or sent anyway) is the user's answer, or a section 8 TBD.

**An endpoint the backend has built but not deployed** (its branch or staging has it; the server the app calls doesn't yet) is provisional too, but keeps everything real: its path stays in the API endpoints table with `PROVISIONAL` beside it, its entity's note names the source, its repository is the real one tested with fakes (no stub), and section 8's `### Provisional shapes` list gets an item that gates the release on the deployment. The provisional state ends when an integration test runs against the deployed endpoint, or a live check is done by hand and recorded: the item is then ticked with that test's name or the check's date, and the path loses `PROVISIONAL`.

This distinction matters: a TBD blocks progress until resolved. A provisional shape unblocks UI work today but creates a debt that must be paid before launch. Both need to be tracked, but differently.

## API contract from another part

In a monorepo, the app's requests may come from another part's spec, such as the backend's (a delegation brief's `API contract:` line, `feature-workflow`'s "Delegated runs"). The app's spec still states each shape it uses, never only a link:

1. **Section 4's API endpoints** give each request the app makes, with its request and response shapes and the errors the UI handles, as for any API, taken from the contract's spec. Under the table, a `Contract:` line names that spec's path from the repository root and the section each endpoint comes from.
2. **What the contract doesn't settle** (a field the app needs, an error code) is a section 8 TBD that names the part, e.g. `- [ ] backend: does GET /history page its results?`.
3. **A contract that isn't approved yet** (`draft` in the brief): its shapes are provisional, marked as "When the API is explicitly not ready yet" says, except that each endpoint keeps the contract's path beside `PROVISIONAL`, the entity's note names the contract's spec as its source, and the section 8 list names that spec too. Once it is approved, confirming them is a spec change like any other.

## Handoff

After producing the spec:
1. Save it in the folder the caller names. Without one, use the spec index's folder, found with `grep -rlxF --include='*index.md' '| Feature | Spec | Screens and routes | Status | Last verified |' .` at the project root; else the folder of the project's existing specs; else the project root. The project root is the adapter's Root, which in a monorepo is the app's folder, not the working directory (present the spec to the user if there is no filesystem). Unless the caller names the file, follow the existing specs' file naming when they share one, with the feature slug in it. Only `feature-workflow` adds index rows: when the folder has a spec index and that skill didn't invoke this one, say that the new spec has no row yet and that `feature-workflow` adds it the next time it reads the spec. If the Intake Sheet was saved as `.mobile-dev-skills/<feature-slug>/intake.md` (or under the pre-rename `.flutter-skills/`, in a project that has only that folder), add `> Spec: <spec path>` as its first line.
2. Run the quality check (above), its script first, and report its result. After in-place fixes, run the script again before step 3.
3. Show the user the **Open Questions** section explicitly: "Here are the TBDs that need resolving before code: ..." Name any scenario marked `test: manual` too, since approval accepts it as checked by hand, and any whose test the user skipped (`test: none — <reason>`).
4. Ask: "Approve this spec? Once you approve, I'll move to scaffolding the code." If the spec changes before approval, run the quality check again before asking again.
5. **Wait for explicit approval.** "ok" alone is not enough — confirm: "Just to confirm, you'd like me to proceed with code generation based on this spec?"
