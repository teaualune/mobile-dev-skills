# Reading a feature's code — `feature-workflow`

How a `feature-workflow` subagent reads a feature's code when its procedure sends it here: `baseline.md`, to record what the feature does, and `diagnose.md`, to find a bug's cause. The procedure says where reading starts and when it stops; this file says how much may be read, and how.

## Budget

**15 source files and 5 test files** opened, unless the prompt gives other numbers. A search (`grep`, a folder listing) doesn't count, but one that prints a file's contents counts as opening it. Never open a generated file (the adapter's "Project layout") or a package's code. The procedure's own files, the adapter, `feature-spec`, the spec and the style references don't count.

## Sample, then expand

1. **Sample.** Start where the procedure says, finding the files through the adapter's "Code entry points".
2. **Expand** along the adapter's **Links**, one level at a time, from what the files read so far show: the state primitive behind a screen, then what it calls, then the entities. A chain stops at the boundary the adapter names. Open an **App-wide** file only when the feature is reached from outside the app or sits behind a guard.
3. **Stop** where the procedure says, and at the budget in any case. Whatever you didn't open is not read: your report names it.
4. **Tests.** List the tests of the files you read (the adapter's **Tests**), then open the test files that may check the behaviors in question. A test counts for a scenario only when its body checks the scenario's THEN lines; its description alone never settles that.

## Only what the code shows

A behavior is established only where the code shows it: a condition, a handler, a call, or the widget or view a state renders. Whatever an unread file, the server or a remote config decides, and code that contradicts itself, is a gap, not behavior.
