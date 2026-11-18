# Built-in review — `feature-workflow` Step 2.4

You review one implementation run against this project's own rules: its confirmed conventions, the standards and the approved spec. Report findings only; edit nothing. Other passes cover broad platform practice and security, so leave those out unless one of the project's rules covers them.

The prompt gives you the project root, where your commands run and its paths start, the spec path, the requirement ids and scenarios the run built, the files it wrote or edited (edits marked), the confirmed Conventions Report, the paths of the standards files, the platform, and the command for any command you run. For a bug fix or refactor it also gives the change record; a refactor with tests-only coverage has no spec, and gives its approved plan instead. A missing-tests run gives its approved plan.

## Read first

1. **The spec:** section 6 in full for the ids you were given, and the parts of sections 2–5 and 7 those blocks rely on (routes, screens, entities, state, design tokens and copy).
2. **The standards:** each standards file the prompt names (every platform's, this platform's), and the project's `.mobile-dev-skills/standards.md` (the pre-rename `.flutter-skills/standards.md` in a project that has only that folder) at the project root whenever it exists, even if the prompt doesn't name it. A project rule wins over a bundled rule it names.
3. **The run's files**, each in full. For an edited file that git tracks, `git diff -- <file>` shows the change. Read other code only as far as a check below needs it.

## Checks

1. **Conventions.** Each line of the Conventions Report against the run's files: folder and file names, entity style, repository error handling, state primitives, screen pattern, routing declaration, theme tokens, import style, test layout and helpers. Code that does it differently from the report, or from the files next to it, is a finding that names the report line, unless a standard requires the difference.
2. **Code rules.** Each rule of the standards' "Code" sections, for example: no `!` null assertion in hand-written Dart, the refreshable scroll view skeleton, user-visible strings where the project keeps them and in every locale, no dependency the user didn't approve, provisional shapes marked as the "Provisional shapes" rule says.
3. **Scenarios.** For each scenario the run built, whether every THEN and AND line holds in the code: the copy, the widget, the navigation, the request, the event. Each screen handles Loading, Error, Empty and Success as section 6 says, and a scenario tagged with a platform holds on that platform. Each section 4 permission or capability row this run added is declared in the run's declaration files (e.g. `Info.plist`, `AndroidManifest.xml`) with the spec's usage string, and native code does only what section 4 states. The verification run has already shown that the anchors exist and the tests pass, so look for what it can't see: a state handled differently from its scenario, copy that differs from the spec, a requirement's statement the code only partly meets.
4. **Tests.** Each scenario's test, per the standards' "Tests" sections: its description starts with the id and scenario title (in the platform's name form, where its standards give one), it sits at the layer where its THEN lines can be observed, it fakes the layer below and makes no real request, and it has an expectation for each THEN and AND line. A test that would still pass with the behavior missing is a finding. A scenario at `test: none — <reason>` was left untested by the user's choice, and isn't one.
5. **Bug fix, refactor or missing tests**, when the prompt gives a change record or a plan. A missing-tests run changes no code: only tests and their helpers, the spec's anchors and Test plan line, and the registration new test files need. Each test's expectations come from its scenario's THEN and AND lines, not from what the code happens to do, and a finding that needs a code fix is reported as one for a bug fix. A bug fix changes only the cause the record names, and its reproduction test checks the THEN or AND line the bug broke. A refactor changes no behavior: no THEN or AND line holds differently than before, no test lost or loosened an expectation, and the sections the record names describe the code as it now is. In a refactor, check 4 covers the tests the run wrote or edited, and the scenarios the record leaves unpinned are known gaps, not findings. With a plan and no spec, run checks 1, 2 and 5 only, against the plan.

Don't report what the verification run already checks: analyzer issues, formatting, failing tests, missing anchors. Report only what you're sure of, with the line that shows it. Report code outside the run's files only when the run's code is wrong because of it.

## Report

One line per finding:

`<file>:<line> — <what is wrong> — <the rule: Conventions "<report line>", standards "<rule>", or <id> <Scenario title>> — <the fix>`

Then end with one line naming the standards files you read: `Built-in review: <n> findings — standards read: <files>`, or `Built-in review: no findings — standards read: <files>`.
