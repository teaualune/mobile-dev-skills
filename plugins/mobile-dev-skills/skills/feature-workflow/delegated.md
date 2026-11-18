# Delegated runs — `feature-workflow`

In a monorepo, one feature can span parts that each have their own folder and specs: a backend, a web app, this app. Such a feature belongs to the project's own workflow (the parent): its intake, its split into parts, the other parts and the repository's root directory of specs. The parent may hand the app's part to this skill with a **delegation brief**. That part then runs here from intake to review, in the same conversation and with the same user, as a direct request does, apart from the steps below. The steps and sections named below are the skill's.

**The brief** comes as this skill's arguments, or as the path of a file that holds it. It comes from a skill or command the project defines, whose steps call for it; a brief you wrote yourself for a request the user made directly isn't one, and that request goes by Step 0's "In a monorepo".

```markdown
# Delegation brief — Reading history
- Slug: reading-history
- From: the project's `cross-part-feature` skill
- Request: new feature
- App: app/
- Specs: app/docs/specs/
- API contract: backend/docs/specs/reading-history.md (draft)
- Approval: here

## App slice
<the app's part: as much of an Intake Sheet as the parent knows; for a bug fix or refactor, its report or plan>

## Other parts
- backend: records each opened article; `GET /history`, `DELETE /history/{id}`
- web: none
```

- **Request** is `new feature`, `change` (an edit to a feature the app has), `bug fix` or `refactor`. A missing-tests request isn't delegated: it adds this app's tests and nothing another part depends on, so the user asks it of this skill directly.
- **App** is the project root, and **Specs** the spec folder inside it, both from the repository root.
- **API contract** names each other part's spec the app's requests come from, with its status as the parent knows it (`approved` or `draft`), or says `none`.
- **Approval** is `here`, when the user approves the app's spec in this run, or `with the other parts`, when the parent asks for every part's approval at once.

1. **Check the brief.** The adapter's lookup must find the app at **App**, **Specs** must sit inside it, and **Request** must be one of its four values; otherwise say what doesn't match and stop, writing nothing. Ask once for a missing line.
2. **The state folder.** A new feature's is `.mobile-dev-skills/<Slug>/` in the project root; when that folder already holds another feature's state, ask. A change, bug fix or refactor keeps the slug of the app spec it changes (Step 1.1; for a feature with no spec yet, `feature-intake`'s rule), since its spec, sheet, tasks and reports belong to that feature; the brief's **Slug** then names only the closing block. A change that touches several specs, and a slice split into sub-features (step 4), has a folder per spec.
3. **Save the brief** as `brief.md` in each of those folders, as given, before any other file. A brief that comes back for the same **Slug**, the parent invoking this skill again, is found by that line (`grep -lxF -- '- Slug: <slug>' .mobile-dev-skills/*/brief.md`) and replaces the saved copies. The run's state is the app's own from then on: the parent or the user (`/mobile-dev-skills:feature-workflow continue <slug>`, with either slug; `/feature-workflow` in a manual copy) resumes it as any run ("Resuming"). A brief applies only to the run it started: once that run's specs are `implemented` with no unticked task, a request on the feature without a new brief is a direct one.
4. **The slice is the request.** Step 0 sizes it alone, never the whole feature, and its size line opens your first reply as Step 0 says. **Request** gives its type: a bug fix or refactor runs its mode, the slice as its report or plan. A delegated request is never trivial, since the parent needs its spec. For a new feature or a change, write the slice as the feature's `intake.md` (`feature-intake`'s "Saving the sheet"), with the other parts' work under Summary's out-of-scope field; intake then asks only what it leaves open. A Large slice is split as Step 1.3 says, each sub-feature taking the brief; with `Approval: with the other parts`, every sub-feature's spec is written before the hand-back.
5. **Phase 1** runs as written. Step 1.4 takes **Specs** as the spec folder. The requests the app makes to another part follow `feature-spec`'s "API contract from another part": section 4 states the shapes the app uses and cites the contract's spec, and shapes from a `draft` contract are provisional (the skill's "Provisional API shapes").
6. **Approval.** With `here`, Step 1.6 runs as written. With `with the other parts`, Step 1.6 runs up to the approval question, then the run ends with the closing block at `awaiting approval` instead of asking. When the parent hands it back, first **re-read each API contract's status**, from the new brief or the contract's spec. Shapes from a contract approved since are now confirmed (`feature-spec`'s "API contract from another part"): change the spec, run Step 1.6's quality check, and ask for the approval here. **Otherwise take the approval** from a message of the user's in this conversation that is explicit ("The hard gate"), names this spec's file, alone or in a list, and comes after the spec's last change; without one, ask for it here.
7. **Phase 2** runs as written; its verification run and review cover the app alone. A check that needs another part running, such as a device test against a local server or a flow through the web app, goes under the run report's Follow-ups as a manual check.
8. **Write nothing outside the project root.** The other parts' specs and the root directory are read only; the parent updates them from the closing block.
9. **Hand back.** End every reply that ends the run with the closing block: at `awaiting approval`, after the last spec's Step 2.4, after a FAIL that stops the run, or when the user stops it. Its heading takes the brief's **Slug**. Paths are from the repository root, and each value comes from the files the run wrote, before the parent changes anything:

   ```markdown
   ## Handoff — reading-history
   - Spec: app/docs/specs/reading-history-feature-spec.md (index: implemented)
   - Stage: implemented
   - Verification: Codegen SKIPPED · l10n SKIPPED · Analyze PASS · Format PASS · Tests PASS · Native build SKIPPED · Conformance PASS
   - Review: built-in — no findings · flutter-reviewer — 1 MEDIUM, fixed · security-reviewer — no findings
   - Report: app/.mobile-dev-skills/reading-history/report.md
   - Follow-ups:
     - backend: `GET /history` has no paging; the app shows the first 50 (reading-history.3)
     - manual: open History after reading an article, against a local backend
   ```

   - **Spec** has a line per spec the run wrote, with its index status, or says `none — tests-only coverage` for a refactor without a spec; **Report** has a line per run report, or says `none`. **Stage** is `awaiting approval`, `implemented` or `stopped at Step <n> — <why>`.
   - **Verification** gives each check by name with its result, and **Review** each pass with its findings and how they were settled (`NOT RUN` and `FAIL — no report` included), or each says `not run`. **Follow-ups** take section 8's open items, the provisional list and the run report's Follow-ups, each under the part it's for or `manual`, or say `none`.
