# Baseline spec — `feature-workflow` Step 1.1

You record what an existing feature does today, read from its code, as the spec that a change to it will then update: its baseline spec. The feature has no spec yet. Read within a budget, write only what the code shows, and mark what you didn't read or couldn't settle; never fill a gap with a guess.

The prompt gives you the project root, where your commands run and its paths start, the feature and where its code starts (its routes and screen files), the change the user asked for and its size, the spec's path and the slug of its ids, the project's spec style references and language conventions if it has any, the adapter's path, the `feature-spec` skill's path, the confirmed Detected stack and the spec language rule. Write only the spec file: no code, no file under `.mobile-dev-skills/`, no spec index row. Run read-only commands only.

## Read first

1. **`feature-spec`:** its output template, "Section 6 — Requirement and Scenario blocks", "Section 10 — Test plan", "Non-functional topics", "Quality check" and "A baseline of existing code".
2. **`reading.md`**, in this file's folder: the budget, and how to read.
3. **The adapter:** its "Project layout", "Code entry points" and "Spec notation", by their line ranges (`grep -n '^## ' <adapter>`), and the **Test-name search** line of its "Commands".
4. **The style references** the prompt names, if any.

## Read the code

Read by `reading.md`, with its budget:

1. **Start** with the screens the change touches, found through the adapter's **Routes** and **Screens**; for a Standard or Large change, then the feature's other screens. Note each behavior they show: what each state renders (loading, error, empty, success), each user action and its result, the navigation, and the side effects (analytics events, snackbars, dialogs).
2. **Expand** for the behaviors noted so far.
3. **Stop** once three files in a row add no behavior. The screens the change touches and their chains come first; whatever is left of the feature is not read.
4. **Tests** that may check the behaviors you noted.

Record a behavior only where the code shows it (`reading.md`'s "Only what the code shows").

## Write the spec

Save it at the given path, in the project's spec layout when the prompt names style references, else in `feature-spec`'s template, following its "A baseline of existing code" and the project's language conventions:

- **Section 6:** one requirement per behavior, grouped by screen, with ids `<slug>.1`, `<slug>.2`, … in the order written, and every `enforced` anchor naming code you read. Each screen you read gets `Loading`, `Error`, `Empty` and `Success` scenarios as its code handles them: `N/A — <reason>` for a state that can't occur, and `TBD` with an `uncertain` item for one whose handling you couldn't settle.
- **`test`:** the existing test whose body checks the scenario, as `<path>#<description>` with the description's text as its file writes it, without the quotes or backticks around it, so that the adapter's **Test-name search** finds it. A description with an escape or an interpolation in it can't be anchored. Otherwise `none`. Never `(filled in Phase 2)`: nothing in a baseline waits for Phase 2.
- **Gaps** become the section 8 items `feature-spec` defines: `uncertain` for a fact you couldn't settle, `Unplaced:` for behavior you saw signs of but couldn't place in a block, and one `Not read:` item for the feature's files you didn't open.
- **The spec language rule** applies to the text you write, and the fixed syntax stays in English.

Then check the saved file with the script that decides `feature-spec`'s quality checks 1 and 6, in the folder of the `feature-spec` path the prompt gives: `bash <that folder>/scripts/check_spec.sh --adapter <the adapter's path> <spec path>`, adding `--own-layout` when you wrote the project's layout. Fix each `FINDING=` line it prints, a missing state as the Section 6 bullet above says, and run it again until it prints none. Its open count is expected: the gaps stay open until the user's review.

## Report

Reply with these lines, and none of the spec's text:

```
Baseline spec — <feature>: <spec path>
Read: <n> of <budget> source files, <n> of <budget> test files — <each path>
Not read: <each path or folder>, or none
Blocks: <n> requirements, <n> invariants, <n> scenarios — <n> with a test anchor, <n> at none
Gaps: <n> uncertain, <n> Unplaced:, <n> files not read
Check: <the script's last RESULT= line>
```

## Extending a baseline

When a later change relies on files that the spec's `Not read:` item names, read them the same way, with a fresh budget, starting from the blocks whose code reaches them. Their behavior goes into new blocks, each taking the highest id in the file plus one, or into THEN/AND lines of the blocks they complete; an `Unplaced:` item they settle becomes a block or is dropped. Take the files you read off the item, and delete it once none is left. Change nothing else in the spec, and report as above.
