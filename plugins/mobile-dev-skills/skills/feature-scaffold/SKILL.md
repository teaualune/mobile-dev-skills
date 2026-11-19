---
name: feature-scaffold
description: Generate the code and tests for a mobile app feature whose spec is approved, mirroring the project's detected stack and conventions. For "build it" or "scaffold the code" after approval. Do NOT use before the spec exists and is approved.
---

# Feature Scaffold

Generate the code and tests for an approved feature spec. **Detect the project's stack first**, then mirror its conventions.

**Platform adapter.** Platform knowledge lives in the plugin's adapters, one per platform: `${CLAUDE_SKILL_DIR}/../../platforms/<platform>/PLATFORM.md`. Find the one this project needs with `grep -H -A2 '^## Applies when' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`, and use the adapter whose condition the project meets; if several do, ask which one the feature is built with. If none does, or the `platforms/` folder is missing, say so and stop. To read only some of its sections, take their line ranges from `grep -n '^## ' <adapter>`.

When `feature-workflow` invoked this skill, use the adapter it loaded. Read the adapter in full, except when implementing one chunk (Step 1), and read its "Native interop" only when the spec's section 4 lists native interfaces, permissions or capabilities. "The adapter" below means that file, and the adapter's sections are named in quotes.

**Native adapters.** Native code a feature writes for a platform the adapter's "Native interop" lists follows that section. When another adapter says `**Native adapter for:** <that platform>` (`grep -H 'Native adapter for:' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`), its "Standards" also apply to the native files in the language that line names, and its "Agents" review them and fix their native build. Native unit tests in that platform's folder, where the adapter's "Native interop" gives native logic tests of its own, also take its "Commands": its command rule, on the container that section names, settled once like the adapter's and saved as a `## Command` line of its own in `stack.md`, and its commands for a layer's tests, the Tests check, the test-name search and the anchored tests. Nothing else of it is read. Native files in another language (an older project's, e.g. Java) follow the project's own native files and the common standards, with no native review; a failing native build still goes to that build fixer. Without a native adapter, all of them do, with no native review, build fixer or native unit tests.

## Step 1 — Detect tech stack + conventions BEFORE writing any code

Skipping this step is the most common failure mode. Detect before generating.

### Saved stack — `.mobile-dev-skills/stack.md`

Read it before anything else. It sits at the project root, as the adapter's "Project layout" defines it; in a monorepo, that is the app's folder, where this skill also runs its commands, not the working directory. A project that has only the pre-rename `.flutter-skills/` keeps its state there: use that folder wherever this skill says `.mobile-dev-skills/`. When both exist, use `.mobile-dev-skills/`, unless the old folder holds unfinished work (an `intake.md` without a `> Spec:` or `> Split:` first line, a `tasks.md` with unticked tasks, or a `request.md` or `brief.md` whose feature's spec has no index row yet): then name it and ask which folder to use.

- **Fingerprint:** the output of the adapter's fingerprint command ("Project layout"), run at the project root. It leaves out the version lines a release bumps.
- **Match, with conventions** → reuse the whole report with no detection and no confirmation. Say so in one line that names the file, its confirmed date and the command. Re-detect when the user asks.
- **Match, conventions `not yet confirmed`** → reuse the stack and the command decision, run the adapter's "Convention probes" for the conventions only, and add them once confirmed.
- **Mismatch** → re-read the manifest file only. If the stack it shows is unchanged, update the fingerprint and say so in one line; otherwise detect as below, showing what changed against the saved file.
- **No file, or a changed stack** → detect as below, and after the user confirms, write the result. A changed stack resets the conventions to `not yet confirmed`.
- **A file without a `Test packages` line** was saved before tests were detected → detect only what's missing, from the manifest's dev dependencies and one existing test, add it, and show the added lines so the user can correct them.
- **Command decision** → one line per set of the command rule's inputs (the adapter's "Commands" names them), with its command and the user's answer when the rule asked. The inputs vary per machine, so check them on every run: reuse the matching line, or decide by the rule and add a line.
- **Layout:** `# Saved stack`, then `> Confirmed <date> · fingerprint <hash>`, then the sections `## Detected stack`, `## Detected conventions` (`not yet confirmed` until Phase 2) and `## Command`, each holding what was confirmed.
- **Implementing one chunk for `feature-workflow`?** Use the Conventions Report it passes and leave `stack.md` alone; the orchestrator also keeps the task file and the run report. Read only the adapter's "Project layout", "Commands", "Generation order" and "Templates", plus "Native interop" when the chunk writes native code or declarations, then go on to Step 2.

### Detection

Run the adapter's detection in order, each step informing the next: the adapter's "Stack layer" (the manifest is the source of truth), the adapter's "Convention probes", then the command below. The probes' exemplar features are the pattern source for Step 3. Without filesystem access, ask for what the probes list, and don't proceed without the manifest.

**Fallback when detection is impossible.** If the user still can't provide enough to detect, or says "I don't know, just pick reasonable defaults", use the adapter's fallback stack ("Stack layer") and label every fallback choice `FALLBACK` in the report, so the user knows what wasn't actually detected.

### The command

Decide it once by the adapter's command rule ("Commands"), report it in the Step 1 output, and use it for every command the adapter names. When `feature-workflow` invoked this skill, reuse the command it settled in its Step 1.2 instead of deciding again.

fvm policy (plugin option `fvm_policy`): [${user_config.fvm_policy}] — `auto`, `always` or `never`. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use `auto`.

### Output: the Detected Stack + Conventions Report

Before writing any feature code, produce the adapter's "Detection report", stack and conventions, and end it with "Going to generate the feature using these. Confirm or correct?"

Wait for confirmation, save the confirmed report to `stack.md`, then generate.

## Step 2 — Load the standards

Run this in every session that writes code, before its first file: also when Step 1 reused a saved stack, and when `feature-workflow` handed you one chunk. Read `${CLAUDE_SKILL_DIR}/../../platforms/standards.md` (every platform), the adapter folder's `standards.md` when it has one, and the project's `.mobile-dev-skills/standards.md` when it exists. When the spec has native code for a platform that has a native adapter (above), read its `standards.md` too, now, for those files. Then say in one line which files you read, as `Standards: <file>, <file>, no project file`, naming a native adapter's file with the files it covers: `platforms/<native adapter>/standards.md (<platform folder>/ files)`.

**The project's skills.** When the project's file has a `## Workflow` part with a `Skills: <skill>, …` line, load each skill it names with the Skill tool, after reading the standards and before the first file, and end the `Standards:` line with them: `…, skills: <a>, <b>`. A skill that isn't listed in this session is named there as missing, `<b> (not listed)`, never skipped silently. Use them as reference for the code they cover; where a skill's advice differs from a standard, the standard wins. The part's `Pause after each task:` line applies only in `feature-workflow`'s Step 2.2.

Apply the standards to every file you write, tests included, on top of the confirmed conventions. A project rule wins over a bundled rule it names, and a standard wins over an exemplar. When the user corrects generated code for a reason that holds for every feature, offer the rule as a line for the project's file, and add it only if they accept.

## Step 3 — Generate file-by-file

Running outside `feature-workflow`? Take Step 5's baseline before the first file.

For each file:
1. State the path.
2. State whether it's new or modifies an existing file.
3. If modifying, show the diff (or the inserted block + surrounding context).
4. Write the code.
5. Move to the next file.

Do NOT dump 12 files in one message. Group naturally — e.g. "entities + JSON mapping" as one group, "repository + provider" as the next, then "screen + states", then "router wiring", then "modifications to existing screens". A group's tests come right after it (see "Tests").

## Step 4 — Generation order

Always follow the adapter's "Generation order", each layer's tests right after it. Concrete class and file names depend on the detected stack. For each screen, take each state and action from the screen's section 6 entries.

## Pattern sources

1. **An exemplar first.** For each file kind, mirror the project's own files: the exemplar features the convention probes read, or the existing file of that kind closest to the one you're writing. Copy their structure, class shapes and wiring, except where a standard says otherwise.
2. **Templates** only for a file kind with nothing to mirror, when the confirmed stack matches one of the adapter's template sets (the adapter's "Templates") or the fallback is in effect. Use them as **starting points only**, adapted to the confirmed conventions.
3. **Neither** (a stack with no template set, and no file of that kind to mirror): tell the user what was detected, and ask whether to (a) write it from scratch, following the stack's own documented patterns, (b) switch the project's stack for this feature (rare, usually a bad idea — flag it), or (c) hold off until a template set exists. Proceed only after the user picks. Never fake one stack with another stack's templates.

The generation order holds whatever the source — only the specific class shapes change.

**Native work** follows the adapter's "Native interop": the mechanism it ranks, native code where it says, mirrored from the project's own native files. Write each section 4 permission and capability row into its declaration file, with the spec's usage string, in the same run as the code that requests it, plus any build-check list the section names (e.g. the build script's usage keys).

## Tests — written with each layer

Every section 6 scenario gets an automated test unless it is `N/A` or `manual`, or the user skipped its test (`none — <reason>`, `feature-workflow`'s Step 2.2); one with a `platform` comment runs with that platform set. Follow the spec's `### Test plan` (section 10) for the kind of test per layer and for fakes or mocks. A spec without one uses the detected test conventions, and the closing notes say so. In a bullet-format section 6, each state or action bullet this run adds or changes gets a test described `<Screen> <state or action>`, and nothing is anchored.

How tests are placed, named, asserted and faked is in the standards' "Tests" sections.

- **Native unit tests**, where the adapter's "Native interop" tests native logic natively (for Flutter, logic that must run without the engine): each goes in the unit-test target or folder that section names for its platform, follows the native adapter's test rules (its `standards.md` names them), and runs with its commands, as "Native adapters" above says.
- **Goldens**, when the Test plan has them: create each new image with the adapter's golden command, and list it under Manual checks. Regenerate an existing image only when the approved change alters how that screen looks, and list it too.
- **Run** each layer's tests when they're written, with the adapter's command for a layer's tests, after the Codegen command when the layer added annotated files. A test that fails because the code departs from its scenario means the code is wrong: fix the code, not the expectation. If the scenario itself is wrong, stop and tell the user; that is a spec change.
- **Test-first, on request.** When the user asks for it, write a scenario's test before its code and run it to see it fail for the expected reason.
- **In an edit**, rewrite the tests of changed scenarios and delete the tests of removed blocks. Leave the scenarios the change doesn't touch as they are, tested or not.
- **A bug fix** (`feature-workflow`'s "Bug fix and refactor") writes its reproduction test first, and it must fail before the fix. **A refactor** edits a test only where the code it calls moved or was renamed, never an expectation. **A missing-tests run** (`feature-workflow`'s "Missing tests") writes only tests, each passing on the code as it is; one that fails on a THEN or AND line goes to the user, never into a code fix.

## Spec anchors — filled before verification

When the spec's section 6 uses Requirement/Scenario blocks (`feature-spec`), record where each behavior lives once every file has landed, in one pass over the spec's anchor comments. These edits need no overwrite confirmation.

- **`enforced`** on each Requirement and Invariant → `<path>#<Symbol>`: the project-relative file plus the class, method (`Class.method`) or provider that carries the behavior, e.g. `lib/features/saved_articles/presentation/saved_articles_screen.dart#SavedArticlesScreen`. Comma-separate several when the behavior spans layers, such as a notifier method and the screen. Never a line number, and never a name that exists only in generated code: anchor the annotated function or class.
- **`test`** on each of their Scenarios → `<path>#<test description>` for the test that covers it, e.g. `test/features/saved_articles/saved_articles_screen_test.dart#saved-articles.1 Empty`, with the description's text as the test file writes it, in the platform's name form where its standards give one, without the quotes or backticks around it. Comma-separate several, each with its path.
  - `manual — <reason>` stays as approved. Set it yourself only when the user agrees that no test here can reach the scenario, and list it under the defaults confirmed during generation.
  - `none` alone is only for behavior this run didn't write and that has no test. `none — <reason>` is a test the user skipped; it stays until a test covers the scenario.
  - `N/A` scenarios have no `test` comment; don't add one.
- **Fill every anchor still at `(filled in Phase 2)` whose code exists**, including behavior this run didn't touch (edit mode, a spec converted from the bullet format). Any left at the placeholder go in the closing notes with the reason.
- **In an edit, also update the anchors the change moves:** a renamed or moved symbol (in a refactor, every one the move changes), a rewritten or renamed test, a `none` scenario that now has a test.
- **Then the H1 line:** if it still reads `> Last verified: never (not implemented)`, change it to `> Last verified: never (implemented, not yet verified)`. Leave any other value alone.
- **Change nothing else in the spec.** Ids, titles, statements and scenario text stay as approved.
- **Implementing one chunk for `feature-workflow`?** Report the anchors instead of editing the spec; the orchestrator writes them. A scenario you can't test goes back as a question, never as `manual`.
- A spec whose section 6 is still a bullet list has nothing to anchor; say so in the closing notes.

## Step 5 — Verify, then the closing notes

**Implementing for `feature-workflow`?** Skip the checks: its Step 2.3 runs them and records the results. Hand it the closing notes.

Otherwise, once the spec anchors are filled, run the checks of the adapter's "Commands" table in its order (Codegen, l10n, Analyze, Format, Tests, Native build), then Conformance: the `feature-verify` skill on the spec, when section 6 has blocks. Write each command with the command from the Step 1 report (e.g. `fvm flutter analyze`). Where the project's CLAUDE.md or README documents its own form of a command, use that form, still with that command.

- **Results.** Each check ends as `PASS`, `FAIL` or `SKIPPED — <why>`, taken from the command's output in this run, never from reading the code or from an earlier run. `SKIPPED` is only for a check that doesn't apply: its "Runs when" is false, or the user has said the project doesn't use it. A check that applies and couldn't run is a `FAIL`.
- **Against the baseline.** Before the first file of Step 3, run Analyze and Tests on the untouched code (Tests with the native unit tests of each platform whose native tests you will write or the spec anchors), and Native build for each platform whose folder you will write in, and keep the result. A check fails on anything that wasn't there before, wherever it shows up. What was already there is reported, not fixed. Native build passes only when its builds succeed; one that fails at the baseline goes to the user before any native file is written.
- **Conformance** fails only on what this run wrote or changed. `feature-verify`'s findings on older behavior (a scenario the run didn't touch, left at `test: none`, say; a scenario with a deferred `TBD`) and on tests the user skipped (`test: none — <reason>`) are listed, not failed.
- **On a FAIL**, fix the cause in the files this run wrote and run again from the earliest check the fix can affect. Never make a check pass by weakening it: no loosened or deleted expectation, no `skip`, no suppression comment (`// ignore`). While a check fails, don't call the feature done.

Then output the closing notes:

```
## Manual checks

- [ ] Each new screen against its Figma reference
- [ ] <each scenario marked `test: manual`: id, title and reason>
- [ ] <native work, on a device per platform: each native interface method, each permission prompt with its usage string, and the denial path>
- [ ] <each native build or native unit test run this machine couldn't do, with its command>
- [ ] <capabilities to enable outside the code, e.g. in the Apple Developer account>
- [ ] <permission or capability rows not declared in code, with why>
- [ ] Affected existing screens, on a device
- [ ] <new golden images to look at; the command for tests that need a device>

## TBDs still unresolved from the spec

<list any items still marked TBD>

## Spec anchors

<n of m requirements anchored; each `enforced` or `test` still `(filled in Phase 2)`, with its id and why; number of scenarios with `test: manual` and with `test: none`, and each test the user skipped>

## Defaults confirmed during generation that the spec doesn't state

<each with its requirement id or screen, or "none">
```

## Hard rules

- **Never overwrite existing files without asking.** Show the user the existing file content (or path) and confirm.
- **Never invent API endpoints, field names, or response shapes — except for documented provisional shapes.** If something is TBD in the spec, write a `// TODO(spec): <thing>` and surface it in the closing notes. If something is marked **provisional** in the spec (the API isn't ready yet, but the UI is proceeding), generate it as the standards' "Provisional shapes" rule says, with its `// TODO(api)` markers, and with a stub repository only for a provisional endpoint that doesn't exist yet: a provisional field on an existing endpoint, and an endpoint built but not deployed, keep the real one. Add every provisional file to the closing notes under a dedicated "Provisional — must replace before launch" heading.
- **Never skip error/loading/empty states.** If the spec doesn't give a screen's Loading, Error, Empty or Success behavior (a scenario, a bullet in an older section 6, or `N/A — <reason>`), ask before generating that screen — don't guess and don't omit.
- **Never anchor a test to a line it contradicts.** Before a scenario's `test` anchor is written, check the test's assertions against the scenario's THEN and AND lines and the sibling lines of its screen. A test that asserts the opposite of a line stays unanchored, and the contradiction goes to the closing notes as a spec question.
- **Don't introduce new dependencies** without flagging. If the spec implies you need a package the manifest doesn't list, ask before adding it, e.g. "This will require adding `cached_network_image` to pubspec.yaml — proceed?"

## When the spec has gaps

If the user says "just build it, fill in the gaps with your best guess" — don't. Instead:
1. List the gaps in one message.
2. Offer a sensible default for each ("for empty state, I'd put 'No saved articles yet' with a 'Browse articles' button — ok?").
3. Wait for the user to confirm each default before generating that part.

This keeps the user in the loop without making them write every detail upfront.
