---
name: feature-verify
description: Check a mobile app feature's code against its spec — each requirement's `enforced` anchor still exists and each scenario's test passes. For "does the code match the spec". Do NOT use it to fix code or write specs.
argument-hint: "[spec file path, or feature name]"
---

# Feature Verify

Check a feature's code against the section 6 blocks of its spec (`feature-spec`) and report where the two disagree. The check fixes nothing. Its one write is the spec's `Last verified` line, after a full pass.

**Platform adapter.** Platform knowledge lives in the plugin's adapters, one per platform: `${CLAUDE_SKILL_DIR}/../../platforms/<platform>/PLATFORM.md`. Find the one this project needs with `grep -H -A2 '^## Applies when' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`, and use the adapter whose condition the project meets; if several do, ask which one the feature is built with. If none does, or the `platforms/` folder is missing, say so and stop. To read only some of its sections, take their line ranges from `grep -n '^## ' <adapter>`.

When `feature-workflow` invoked this skill, use the adapter it loaded. This skill needs only the adapter's "Project layout" and "Commands". A `test` anchor in a native platform's folder (such as `ios/`) is a native unit test: for it, also read the adapter's "Native interop" **Platforms** and **Testing** lines, find that platform's native adapter, the one whose "Native interop" says `**Native adapter for:** <platform>` (`grep -H 'Native adapter for:' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`), and read its "Commands". "The adapter" below means the first file, and the adapter's sections are named in quotes.

## Inputs

Resolve paths from the project root, the adapter's Root, and run commands there; in a monorepo, it is the app's folder, not the working directory.

- **The spec:** a file path, or a feature name to look up in the spec index. Find the index with `grep -rlxF --include='*index.md' '| Feature | Spec | Screens and routes | Status | Last verified |' .` at the project root. With no match, or several, ask.
- **The command** for the test run: the one the caller passes; else the line under `## Command` in `.mobile-dev-skills/stack.md` (the pre-rename `.flutter-skills/stack.md` in a project that has only that folder) whose inputs (the adapter's "Commands" names them) match this machine, a file you read and never write; else the adapter's command rule, with the option below. A native adapter's command is decided the same way, from its own rule's `## Command` line or its rule, on the container the adapter's **Testing** line names.

A section 6 still in the bullet format has no anchors to check: say so, mention that `feature-spec` can convert it, and stop.

## The check

1. **List the blocks** from the spec file itself, not from memory of writing it. `grep -nE '^(### (Requirement|Invariant): |#### Scenario: |<!-- (id|enforced|test): |N/A — )' <spec>` gives every id, anchor, scenario title and `N/A` body without the prose.
2. **Requirements and invariants.** Each `enforced` anchor `<path>#<Symbol>` must name a file that exists and declares the symbol (for `Class.method`, the method inside that class). Generated files (the adapter's "Project layout" lists them) don't count, here or in the search below. Otherwise the block gets one of:
   - `not anchored` — the value is still `(filled in Phase 2)`;
   - `moved` — the symbol is gone from that file, and one search of the adapter's source folder (for an anchor in a native platform's folder, such as `ios/`, that folder) finds it elsewhere;
   - `unimplemented` — the symbol is nowhere, or its body is only a stub (empty, nothing but a `TODO`, or a not-implemented error such as Dart's `UnimplementedError`).
3. **Scenarios.** Every scenario has either a `test` comment or an `N/A` body; one with neither is `no test`. For each `test` value:
   - `<path>#<test description>` — the file must hold the description whole, as the adapter's **Test-name search** ("Commands") finds it (a native unit test's, the native adapter's); if it doesn't, `test missing`. Several anchors split only at a comma followed by a file path and `#`, since a description may hold a comma;
   - `manual — <reason>` — no finding; it goes on the manual list;
   - `none`, `none — <reason>` (a test the user skipped: quote the reason; only a test closes the finding) or `(filled in Phase 2)` — `no test`.
4. **Run the tests.** Always run the anchored test files yourself, in one command: the anchored-test command in the adapter's "Commands". Native unit tests run in one more command per platform: its native adapter's anchored-test command. Each anchored description must show in the output as a test of its own that passed. One that fails, is skipped, or sits in a file that doesn't load is `failing`. One missing from the output of a run of several files is run again with its file alone, by the same command; one that still never ran is `test missing`. Reading a test never shows that it passes: without this command's output there is no pass. When a native adapter's command rule stops on this machine (no Xcode, no JDK, say), its anchored tests aren't run: each goes on the report's `Not run:` line, not as a finding.
5. **Unspecified behavior.** Read only the files the `enforced` anchors name, and section 6 in full. List any user action, request, navigation or side effect in those files that no block's statement or THEN/AND line covers; when unsure, leave it out. These are not findings: the user decides whether each belongs in the spec or out of the code.

## The report

Reply with the result; never write it into the spec.

```
Conformance — <feature>: PASS | FAIL (<n> findings)
Tests: <the command as run> → <its last output line>, one line per command
Findings:
- <id> [<scenario title>] — <kind>: <the anchor, and what was found instead>
Not run: <id> [<scenario title>] — <why>, or none
Unspecified behavior: <path#Symbol — what it does>, or none
Manual scenarios: <id + title — reason>, or none
```

`PASS` means no finding. Give no other totals. For each finding, say what would close it (restore or implement the code, update a moved anchor, write or repair the test), but change nothing yourself: no code, test, anchor or spec text, however obvious the fix. A request to fix them is work for `feature-workflow`.

When the user asked for this check directly, not `feature-workflow` during one of its runs, and the findings include `no test` or `test missing`, end with one line saying that `feature-workflow` can write those tests as a missing-tests request, if the user wants them. Untested scenarios are the user's call, not a defect to press on them.

## `Last verified`

- **Full pass**, with the step 4 test run behind every anchored test, so with nothing on the `Not run:` line → set the line under the spec's H1 to `> Last verified: <YYYY-MM-DD> (commit <short sha>)`. Take both facts from `git rev-parse --short HEAD; git status --porcelain`, run before you edit anything: when the second command lists anything but the spec and its index, write `(commit <short sha> + uncommitted changes)`; outside a git repository, or in one with no commit yet, `(no commit)`. Then copy the value into the `Last verified` cell of the spec's index row, if it has one. Touch no other cell and add no row.
- **Any finding, or a test on the `Not run:` line** → leave the line as it is.
- **The index row says `draft`** → the spec is being changed and its change isn't built yet: report, and leave the line as it is.
- **Told to report only** (a subagent run for `feature-workflow`) → write nothing, and return the line for the caller to write.

## The command rule's option

The plugin options the adapters' command rules read:

fvm policy (plugin option `fvm_policy`): [${user_config.fvm_policy}] — `auto`, `always` or `never`. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use `auto`.
