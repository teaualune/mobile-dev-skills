# Missing tests — `feature-workflow`

A missing-tests request (the skill's Step 0) adds automated tests for scenarios the spec already states, including tests the user skipped (`test: none — <reason>`). It changes no code and no spec text but the anchors and a section 10 Test plan line, and writes no change record. The tests stay optional throughout: the user takes any part of the plan, or none, and a scenario left untested blocks no later run (Step 2.3). The steps and sections named below are the skill's.

## Phase 1

1. **The scope.** The feature, and its scenarios when the user names them. When the feature's `tasks.md` still has another run's unticked tasks, that run is finished first (the skill's "Resuming"), since this run's tasks replace the file.
2. **The spec.** Find it by Step 1.1's step 1. A feature with no spec gets its baseline spec first (Step 1.1's step 2, with Step 1.2 before it). Then run Step 1.2, if it hasn't run. A section 6 still in the bullet format has nothing to anchor a test to: offer `feature-spec`'s conversion, and stop if the user declines.
3. **Baseline run**, before any test is written: Conformance (`feature-verify` on the spec, run as in Step 2.3) and the Tests check of the adapter's "Commands", each taken from its output in this run. Show both results.
   - The candidates are the `no test` and `test missing` findings, of the scenarios the user named or of all. A `moved` anchor is updated with this run's anchors.
   - Other findings belong to other requests: `failing` to a bug fix, `unimplemented` to an edit, `not anchored` to the unfinished run that left it (resume it). Name them and leave them.
4. **The plan**, in one message, as a trivial change plan is: the type line; the scenarios to test, grouped by test file, each with its layer (section 10's Test plan, else the detected test conventions); the `moved` anchors to update; any section 10 Test plan line the tests make untrue, old → new; the commands; and the scenarios left untested. List the scenarios by what a regression would cost, errors and writes before copy, so that the user can take the top of the list when time is short. A scenario no test can reach without changing the code (nothing to fake the layer below with) is left out and named, since that change is a refactor. Then ask for approval (the hard gate). The spec and its index row stay as they are. When the spec is a baseline written for this request, say that the approval also accepts it as the feature's spec, with its open section 8 items.

## Phase 2

1. **Tasks**, written at the approval, before Step 2.1: `tasks.md` gets `> Change: Missing tests <date> — <title>` under its `> Spec:` line, one task per test file (`Tests — <test file> — <id> (<Scenario>, …)`), then Spec anchors, Verification and Review.
2. **Baseline.** Step 2.2's `> Baseline:` line adds `conformance — <each finding as id and kind, or none>`: Phase 1's, or a fresh `feature-verify` run when Phase 1 ran in another session or the code changed since.
3. **Write each test** by the standards' "Tests", with an expectation for each THEN and AND line of its scenario, taken from the spec, never from what the code does. Run it with the adapter's command for a layer's tests; it must pass on the code as it is.
   - It fails another way (it doesn't compile, a finder or a fake is wrong): fix the test without changing what it checks.
   - It fails on what a THEN or AND line states: the code or the scenario is wrong, and this run changes neither. Show the user the test and its output; the scenario leaves the plan (Step 2.3), its test removed, and can go to a bug fix, where this test can be the reproduction test.
   - Tick the task once its tests pass, adding the result to its line (`— 6 passed`).
   - The user may drop or skip any planned scenario during the run; it leaves the plan the same way.
4. **No code changes.** Write tests, fakes and test helpers in the adapter's host-test folder, the spec's anchors and section 10 line (step 5), and the registration a new test file needs by the adapter's "Project layout" (a project file without synchronized folders, say), asked as that section says. Change no other file. A test that turns out to need a change to the code leaves the plan, named as the change a refactor would make.
5. **Anchors.** Each tested scenario's `test` anchor names its test (`feature-scaffold`'s "Spec anchors"), the `moved` anchors are updated, and the plan's section 10 line is changed. Nothing else in the spec changes.

Then Steps 2.3 and 2.4 as written; Step 2.3's Conformance passes as its "In a refactor or a missing-tests run" says. In Step 2.4, a finding whose fix would change the code rather than a test is a follow-up, never fixed here. Step 2.4's last step keeps the index row's status, since an `approved` or `draft` row stands for a change not built yet, and copies only the spec's `Last verified` line into it; a baseline spec that has no row gets one at `implemented`.
