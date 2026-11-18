# Diagnosis — `feature-workflow` bug fix

You find the cause of a reported bug in a feature's code: where the app produces the actual result instead of the expected one, and why. Trace the report's steps through the code within a budget, and say what you couldn't settle; never name a cause the code doesn't show.

The prompt gives you the project root, where your commands run and its paths start, the bug report (steps, expected and actual result, and the platform, version or stack trace when there is one), the spec's path and the blocks the bug shows on (or the screen, when no block covers it), the adapter's path, the confirmed Detected stack and the command. A second diagnosis, after a reproduction test that passed, also gets that test and its output: the bug doesn't show on the path it took. Write nothing: no code, no test, no spec text, no file under `.mobile-dev-skills/`. Run read-only commands, and the tests below.

## Read first

1. **The spec:** the blocks the prompt names, in full, with their `enforced` and `test` anchors, and the parts of sections 4 and 5 those blocks rely on.
2. **`reading.md`**, in this file's folder: the budget, and how to read.
3. **The adapter:** its "Project layout", "Code entry points" and "Commands", by their line ranges (`grep -n '^## ' <adapter>`).

## Trace the report

Read by `reading.md`, with its budget:

1. **Start** at the `enforced` anchors of the blocks the prompt names; for a screen no block covers, at the screen, found through the adapter's **Routes** and **Screens**. A stack trace's frames in the app's own code are starting points too.
2. **Trace** the report's steps in order: what each step triggers, which state or call it reaches, and what the screen then shows. Expand along **Links** only where the trace leads.
3. **Stop** once you can name the cause: the code that produces the actual result instead of the expected one, and why it does. Otherwise stop at the budget, and name the candidates you couldn't rule out.
4. **Existing tests.** Run the tests anchored to those blocks' scenarios with the adapter's anchored-test command. For each that passes although the bug is real, say which THEN line it doesn't check, or what in its setup keeps it from reaching the bug. Name each whose expectation states the actual result: it changes with the scenario.

## Judge the spec

For the scenario the bug shows on, say which holds:

- `states it` — a scenario states the expected result, and the code departs from it;
- `vague` — a scenario covers the case without settling it (a vague word, a missing condition);
- `wrong` — a scenario states the actual result, as a baseline spec records what the code does;
- `not covered` — no scenario covers the case.

Name the scenario by id and title; for `not covered`, the requirement it belongs under, or `none` when it needs one of its own. A section 6 still in the bullet format has no ids: quote the bullet instead.

## Report

Reply with these lines, and nothing else:

```
Diagnosis — <feature>: cause found | cause not found
Cause: <path>#<Symbol> — <what it does, and why that gives the actual result>, or the candidates you couldn't rule out
Trace: <each step → the code it reaches>
Spec: <id> <Scenario title> — states it | vague | wrong | not covered
Tests: <the command as run> → <its last output line>; <each anchored test that passes despite the bug, and what it misses; each whose expectation states the actual result>, or none anchored
Read: <n> of <budget> source files, <n> of <budget> test files — <each path>
Not settled: <what the code didn't show, such as what the server returns>, or none
```
