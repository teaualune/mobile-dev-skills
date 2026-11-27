---
name: feature-workflow
description: "Mobile feature workflow (spec, approval, code, tests, review). Invoke it only when the user names it, or when a project skill tells you to hand it an app's part with a delegation brief. Do NOT use for other requests (feature-intake)."
argument-hint: "[new feature, change, bug report or refactor, path to a requirements dump, or a delegation brief]"
---

# Feature Workflow

Act as a senior mobile engineer who turns a fuzzy feature idea into (1) a complete, approved spec document, then (2) production-ready code in the project's own stack. This happens through structured conversation, not one-shot generation. The idea may be a **brand-new feature** or a **change to a feature that already exists** in the app — both go through the same two phases, scaled to the request's size (Step 0). A bug report and a refactor are changes too, each with steps of its own ("Bug fix and refactor"), and so is a request that only adds the tests a spec's scenarios lack ("Missing tests").

The user starts this skill, with its command or by asking for it by name. A line in the project's CLAUDE.md that sends feature changes through this skill counts as asking: one that names it (`feature-workflow`, or its command), or one that says "the workflow" when no project skill is a workflow it could mean (a monorepo's parent workflow, say). The one other caller is a project's own workflow handing over an app's part of a feature that spans a monorepo, with a delegation brief ("Delegated runs"). Never start it yourself on a request that names neither, and never write a brief yourself to start it.

The app's tech stack — state management, routing, HTTP client, code generation tools, UI/design system — must be **detected from the existing project code**, not assumed. If detection is impossible, fall back to the platform adapter's fallback stack (for Flutter, **Riverpod + go_router + Dio**, with `freezed` + `json_serializable` if codegen is in play), state the fallback openly, and ask the user to confirm or correct.

## Platform adapter

**Platform adapter.** Platform knowledge lives in the plugin's adapters, one per platform: `${CLAUDE_SKILL_DIR}/../../platforms/<platform>/PLATFORM.md`. Find the one this project needs with `grep -H -A2 '^## Applies when' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`, and use the adapter whose condition the project meets; if several do, ask which one the feature is built with. If none does, or the `platforms/` folder is missing, say so and stop. To read only some of its sections, take their line ranges from `grep -n '^## ' <adapter>`.

Read it in full once per session, before the first step that uses it, except "Native interop", which you read only once a spec's section 4 lists native interfaces, permissions or capabilities; a trivial request (Step 0) reads only the adapter's "Project layout" and "Commands". The sub-skills and subagents use the same adapter. "The adapter" below means that file, and the adapter's sections are named in quotes.

**Native adapters.** Native code a feature writes for a platform the adapter's "Native interop" lists follows that section. When another adapter says `**Native adapter for:** <that platform>` (`grep -H 'Native adapter for:' ${CLAUDE_SKILL_DIR}/../../platforms/*/PLATFORM.md`), its "Standards" also apply to the native files in the language that line names, and its "Agents" review them and fix their native build. Native unit tests in that platform's folder, where the adapter's "Native interop" gives native logic tests of its own, also take its "Commands": its command rule, on the container that section names, settled once like the adapter's and saved as a `## Command` line of its own in `stack.md`, and its commands for a layer's tests, the Tests check, the test-name search and the anchored tests. Nothing else of it is read. Native files in another language (an older project's, e.g. Java) follow the project's own native files and the common standards, with no native review; a failing native build still goes to that build fixer. Without a native adapter, all of them do, with no native review, build fixer or native unit tests.

**Standards files:** `${CLAUDE_SKILL_DIR}/../../platforms/standards.md` (every platform), the adapter folder's `standards.md` when it has one, and the project's `.mobile-dev-skills/standards.md` when it exists. The scaffold applies them, the trivial path reads them, and Steps 2.3 and 2.4 pass their paths, adding a native adapter's `standards.md` when the run writes native code for its platform. The project's file may also have a `## Workflow` part: its `Skills:` line names the project's skills to load before writing code (the scaffold's Step 2, the trivial path and Step 2.2's implementation subagents load them, and the built-in review may, as reference), and `Pause after each task: yes` has Step 2.2 pause after each task.

## The hard gate

The workflow has two phases. **Never enter Phase 2 without explicit approval of the spec** (e.g. "looks good", "approved", "let's build it"). A vague "ok" or "thanks" is not approval — confirm: "Just to confirm, you'd like me to proceed with implementation based on this spec?" Do not write any code in Phase 1.

The gate holds at every size (Step 0). A trivial request's change plan is its spec: edit nothing, code or spec, until the plan is approved. A large request's sub-features are each approved, and built, on their own. A bug fix or refactor is a spec change like any edit: the approval covers its spec change, or, for a bug whose scenario the spec already states, the scenario the fix restores; no reproduction test or moved code comes before it. A missing-tests request's plan is approved before its first test is written. A delegated run's approval is the user's too: given here, or with the other parts' specs in a message that names this spec's file ("Delegated runs").

## State files

The workflow keeps its state in the target project. It lives in `.mobile-dev-skills/` at the project root (the adapter's "Project layout"), apart from the spec index, which sits with the specs. The project decides whether to commit the folder; never edit `.gitignore` for it.

**Project root.** The project root is the adapter's **Root**, the app's own folder, which need not be the session's working directory: resolve every path these skills name from it, and run every command in it (`cd <root> && …`), the spec index search, the fingerprint and the checks included. Paths written into the state files, the specs and the index are from it too, except where a path must reach outside it: a spec's `Contract:` line, a saved brief and a delegated run's closing block give paths from the repository's root. **Monorepo:** the app is one part of a monorepo when the project root isn't the repository's root (`git rev-parse --show-toplevel`) and another folder of the repository, outside the project root, holds a part of its own: its own manifest (`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`, `build.gradle`, `Cargo.toml` and the like) or its own specs. A repository with one app in a subfolder beside docs, design or CI files isn't one. In a monorepo, and in every delegated run, nothing outside the project root is written.

**Pre-rename folder.** A project that has only the pre-rename `.flutter-skills/` (the name pre-release builds used) keeps using it: read and write there, and take every `.mobile-dev-skills/` path in this skill, the sub-skills and the subagent prompts as that folder. When both exist, look in the old folder for unfinished work: an `intake.md` without a `> Spec:` or `> Split:` first line, a `tasks.md` with unticked tasks, or a `request.md` or `brief.md` whose feature's spec has no index row yet. If there is any, name it and ask which folder to use before reading either; otherwise use `.mobile-dev-skills/` and say once that the other is ignored. Never move, copy or delete either folder; renaming it is the user's choice.

| File | Holds | Written |
|---|---|---|
| `.mobile-dev-skills/stack.md` | Detected Stack, Conventions Report, command decision | Step 1.2; Step 2.1 adds the conventions; a refactor's approval may change them |
| `.mobile-dev-skills/<feature-slug>/brief.md` | A delegation brief, as given | At the start of a delegated run ("Delegated runs") |
| `.mobile-dev-skills/<feature-slug>/request.md` | The request a baseline spec is written for, in the user's words, with its type | Step 1.1, before the baseline subagent starts |
| `.mobile-dev-skills/<feature-slug>/intake.md` | The Intake Sheet | By `feature-intake`, as answers arrive; a sub-feature's at the split (Step 1.3) |
| `.mobile-dev-skills/<feature-slug>/figma/` | Figma frame exports the Intake Sheet's references name | By the export `feature-intake` offers (its Figma rule), after the user agrees |
| `.mobile-dev-skills/<feature-slug>/tasks.md` | Phase 2 tasks, ticked as they land, the run's baseline, and a bug fix's reproduction or a refactor's pinning run | Step 2.2 |
| `.mobile-dev-skills/<feature-slug>/report.md` | One report per Phase 2 run, newest first | Steps 2.3 and 2.4 |
| `index.md` in the spec folder | One row per spec | Steps 1.5, 1.6 and 2.4 |

`<feature-slug>` is the slug of the spec's requirement ids, chosen once at intake, or by intake's rule for a baseline spec (Step 1.1). Subagents never write these files; they report, and you write. A trivial request (Step 0) writes none of them, apart from a `## Command` line in an existing `stack.md`. The project's own `.mobile-dev-skills/standards.md` isn't state: the user writes it, and you add a rule only when they accept one.

### Spec index

`index.md` sits in the folder that holds the project's specs (Step 1.4), or next to the spec when the project has none. If that folder already has an `index.md` that isn't a spec index, use `spec-index.md`. Create it with the first row you write.

```markdown
| Feature | Spec | Screens and routes | Status | Last verified |
|---|---|---|---|---|
| Saved articles | [saved-articles-feature-spec.md](saved-articles-feature-spec.md) | `SavedArticlesScreen` (`/saved`), `ArticleDetailScreen` | implemented | 2026-11-02 (commit 3f2a9c1) |
```

- **Status is the index's own record:** `draft` whenever Phase 1 saves the spec (Steps 1.5 and 1.6), including an update to an approved or implemented one; `approved` at the approval (Step 1.6); `implemented` once a run's verification and review have passed (Step 2.4), except in a missing-tests run, which keeps the status it found.
- **A run's specs** are its own spec and the existing specs it edits (Step 1.1). In Phase 1 they are the specs with a `draft` row whose blocks point to its spec's file (`grep -rlF '<spec file name>' <spec folder>`); in Phase 2, the specs that the ids in its tasks belong to (`grep -rlF '<!-- id: <slug>.' <spec folder>`, for each slug). Their rows move together: `draft` at Step 1.5, `approved` at the approval, `implemented` at Step 2.4.
- **The other cells copy the spec:** its H1 name, the screens of sections 2 and 3 with their section 2 paths, and its `Last verified` line. Refresh them whenever you write the row. The spec wins: when a spec you open disagrees with its row, rewrite the row.
- **Finding it:** `grep -rlxF --include='*index.md' '| Feature | Spec | Screens and routes | Status | Last verified |' .` at the project root. Lookups read it first (Steps 0, 1.1, 1.2 and 1.4, and resuming).
- **A miss**, no index, or a row whose file is gone falls back to the sweep; add rows only for the specs this run reads. A spec that never had a row is `implemented` when its `Last verified` line says so or its section 2 screen classes exist in the adapter's source folder, otherwise `draft`. A baseline spec with no row yet gets none: Step 1.5 adds it when the change is saved, or, in a missing-tests run (a `request.md` whose `- Type:` is `missing tests`, or a `tasks.md` whose `> Change:` line starts `Missing tests`), Step 2.4.

### Resuming

Before Step 0, look up the state of the feature the request names: its `.mobile-dev-skills/<feature-slug>/` folder, index row and spec. A bare "continue" or "resume" means the feature with unfinished work, counting the sub-features of one split as one feature; if several have some, ask which. Take the first row that matches, without repeating intake or detection, and say where you're resuming and why. Before resuming at any row but the last, apply Step 1.2's saved-stack rules (fingerprint and command-rule inputs).

| On disk | Resume at |
|---|---|
| `intake.md` with a `> Split:` first line | The first sub-feature it lists that matches a row other than the last, at that row; if none does, the last row |
| `intake.md` without a `> Spec:` first line | Step 1.3: reflect back the saved sheet, then ask about its first empty field |
| Spec with status `draft`, whatever `tasks.md` holds | Step 1.6 |
| `intake.md` with a `> Spec:` first line, whose spec file has no index row (a session that ended after the save, before Step 1.5 wrote the row) | Step 1.6, after adding the row as `draft` |
| A block still at `enforced: (filled in Phase 2)` that no task names, in a spec with status `implemented`, or `approved` with unticked tasks | Step 1.6 for those blocks, as an edit; after approval, add their tasks |
| Status `approved`, no unfinished `tasks.md` | Step 2.1 |
| Status `approved`, `tasks.md` with unticked tasks | Step 2.2, at the first unticked task |
| A spec with no index row, whose section 8 holds baseline items (`feature-spec`'s "A baseline of existing code"), and whose `.mobile-dev-skills/<feature-slug>/` folder for its ids' slug is missing or holds only `request.md` (and, in a delegated run, `brief.md`) | Step 1.1, at its baseline review, or past it when `request.md` has a `Reviewed:` line; then the saved request, in its type. Without a `request.md`, ask what the change is |
| None of these | Step 0 |

- **The first unticked task's work already exists** (a session that ended mid-task): a new file it names exists, or its `(edit)` file already shows the change. Show it and ask whether to keep it or finish it.
- **A new change to a feature with unfinished work:** ask whether to finish that work first.
- **An "approved" given before the check ran** (a status question answered "approved as written", or a message from an earlier session) isn't the approval when a resume lands at Step 1.6: run the check first, then ask step 6's question, which quotes its `RESULT=` line and names every `test: manual` scenario.
- **A delegated run** (a `brief.md` in the feature's folder, while the run it started is unfinished) resumes the same way, whether the parent or the user invokes it, after reading `delegated.md`, and ends with the closing block ("Delegated runs").
- **A bug fix, refactor or missing-tests run** resumes in its mode ("Bug fix and refactor", "Missing tests"), at the step its row gives, when the spec's index row is `draft` or `approved` and its newest change record (`feature-spec`'s "Change records") is a `Bug fix` or `Refactor` one that no heading in `report.md` names yet, or when `tasks.md` has unticked tasks and a `> Change:` line. A refactor with tests-only coverage, which has no spec or index row, and a missing-tests run, which leaves the row as it is: take the `tasks.md` as an `approved` spec's. A missing-tests run's blocks still at `enforced: (filled in Phase 2)` belong to a change not built yet, not to its tasks, so the row for blocks no task names doesn't apply to it. Read `missing-tests.md` first for a missing-tests run, found by that `> Change:` line or, before its tasks exist, by a `request.md` whose `- Type:` is `missing tests`. Name the mode and the record or `> Change:` line when you say where you're resuming.
- **Only Verification, or Verification and Review, are unticked** (a run that ended on a FAIL, or stopped during a review fix): resume at Step 2.3 and run its checks again from the first. **Only the Review task is unticked:** resume at Step 2.4. In both cases, when the newest report's `### Review` already holds a first round, Step 2.4 continues with its second round, taking the passes and files from that section; otherwise it starts with every pass.
- **Resuming at Step 1.3** sizes the saved sheet as Step 0 sizes a request, never below Small, and says so in the same way. A sub-feature's sheet (its Summary names the feature it was split from) stays Standard, and with no empty field left it goes straight to Step 1.5. A `TBD` field was deferred, not left empty: don't ask about it again.

---

## Step 0 — Size the request

Size each new request before Step 1.1, from what it says and what the spec index shows; don't sweep the code for it. Take the largest size any part of the request reaches, and the larger of two when unsure, except Standard over Large: Step 1.3 can still split after intake.

**In a monorepo** ("State files"), check the request first. One that comes with a delegation brief runs as "Delegated runs" says, sized by its app slice alone. A direct request that also needs work another part owns, such as an endpoint that doesn't exist yet or a web page, isn't taken: name the parts it touches, from the request and the repository's top-level folders, and point to the project's own workflow for such features when one is listed. Without one, offer to take the app's part alone, the other parts out of scope and their API shapes asked for, or provisional, as for any API. A request that only uses what another part already provides is the app's own.

| Size | The request… | Intake | Spec | Approval | Phase 2 |
|---|---|---|---|---|---|
| Trivial | changes only copy, a color or spacing token, or one UI element's look: no state, data, request, route or user action changes | none | none; an existing spec that states what changes is edited to match | the change plan (below) | the edit, then verification |
| Small | changes or adds one behavior on one screen | only what the change needs (Step 1.3) | the lighter spec, or an update of the existing one | explicit | full |
| Standard | adds a screen or a flow, or changes behavior on several screens | full | full | explicit | full |
| Large | adds several flows or a new module | full, then split into sub-features (Step 1.3) | one per sub-feature | per sub-feature | per sub-feature |

- **Announce the size** and why in one line at the top of your first reply — with the change plan for a trivial request, otherwise with whatever Phase 1 asks first — never in a reply of its own. The user can override it at any time; an override down still moves up when the work needs what that size excludes.
- **Move up a size** as soon as the work outgrows its own (a trivial edit needs state or a request; a small change reaches a second screen): say why, and continue in that size's flow with what's already gathered. Move down only when the user asks, and to trivial only before this request has written an Intake Sheet. An approval covers only the plan or spec it was given for.
- **Standard runs Phase 1 and Phase 2 as written.** Small and Large differ only where Steps 1.3 and 1.5 say.

### Request types beside the sizes

Three request types sit beside the sizes, each about a feature the app already has, with steps of its own ("Bug fix and refactor" and "Missing tests", after Phase 2):

- **Bug fix:** the feature does something other than what it should, and the request says, or can say, what happens and what should. Behavior the app never had is an edit, even when the user calls it a bug, and wrong copy, a wrong color or token is trivial.
- **Refactor:** the code changes how it's built and nothing the user sees: code moved or split, a layer added, another library for the same job. A refactor that would also change behavior is an edit, or a refactor first and an edit after.
- **Missing tests:** the request only adds tests for scenarios the spec already states and no test checks (`feature-verify`'s `no test` and `test missing` findings). No code or behavior changes. Its steps are in `missing-tests.md` ("Missing tests").

Announce the type where the size line goes, at the top of your first reply, as `**Bug fix** — <why>`, `**Refactor** — <why>` or `**Missing tests** — <why>`; a reply that opens with the diagnosis or a baseline run still starts with that line. None is ever trivial or split. A baseline spec it needs (Step 1.1) reads as for a Small change in a bug fix, and a Standard one in a refactor or a missing-tests request. When a bug fix turns out to need behavior the app never had, or a refactor to change behavior, say so and continue as an edit, sized by the table above. A request with several bugs runs once per spec it touches, one run after another, each through its own approval; the bugs of one spec share the run ("Bug fix"), and behavior that spec needs and the app never had is an edit inside it.

### Trivial: the change plan

A trivial request skips Phase 1's steps and Phase 2's. Instead:

1. **Locate the code.** Use the feature's index row and `enforced` anchors when it has them, otherwise a targeted search for the string, widget or token; sweep with `Explore` only when those find nothing. Read what you'll change, and the tests that check the old value (the scenarios' `test` anchors, or a search of the adapter's host-test folder).
2. **Settle the command** by the adapter's command rule (see "Platform commands" below). When `stack.md` exists, reuse its matching `## Command` line, or add one when the rule asked. Don't detect the stack, and don't create `stack.md`. Take the commands that will verify the edit from the adapter's "Commands", read by its line range.
3. **Read the standards files** ("Platform adapter" above); the edit follows them. Knowing the rules from memory doesn't count: the plan names the files you read in a `Standards:` line. Load the skills on the project file's `Skills:` line too, as `feature-scaffold`'s Step 2 says, and end that line with them.
4. **Check the spec.** If the feature's spec states what changes (copy quoted in a scenario, a token in section 7), the plan edits that text to match, in its current format: no block conversion and no quality check. Ids, anchors and the `Last verified` line stay as they are, and the spec language rule applies.
5. **Present the plan** in one message: the size line, then one paragraph naming what changes, in which files, the spec and test edits if any (old → new) and the commands that will verify it, then the `Standards:` line, then the approval question. A plan holds no TBDs: when a value is missing (the new copy, which token), ask for it first. In a localized app, the plan names each locale's file with its new text, proposing any translation the user didn't give. When the command rule asks a question, ask it in this message.

   > **Size: trivial** — copy only; no state, request or route changes. Say "treat it as small" to get a spec update instead.
   >
   > **Plan:** change `SavedArticlesScreen`'s empty-state title from "Nothing here" to "No saved articles yet" in `lib/l10n/app_en.arb` (`savedArticlesEmptyTitle`, the app's only locale), then run `fvm flutter gen-l10n` and `fvm flutter analyze`. The spec's `saved-articles.1` Empty scenario quotes the old title, so its THEN line changes to match.
   >
   > Standards: `platforms/standards.md`, `platforms/flutter/standards.md`, no project file. Approve this plan?

6. **After approval**, run the analyzer once as a baseline, along with Format's command on the source files the plan edits and Native build when the plan edits a native platform's folder. Make the edits, then run Step 2.3's checks under its rules: the ones the edit needs (always Analyze), Tests on the tests the plan names, and no Conformance or build fixer: after two failed fixes of a check, stop and show the user its command, its output and what you tried. There's no review (Step 2.4). Fix only new issues in the plan's files, and report the rest without fixing them; when a fix needs more than the plan covers, move up a size. Reply with the files changed, each check's command and result, and any check left to do by hand (e.g. "open Saved and look at the empty state"). While a check fails, the change isn't done. Write no other state files: no intake, tasks or report, and the index stays as it is, even where its rules would add or refresh a row.

---

## Phase 1 — Requirements & Spec

### Step 1.1 — Determine the mode: new feature or edit to an existing one

The user may invoke this skill in either mode. Establish which one applies before intake starts; if the request doesn't make it obvious, ask.

- **New feature** — nothing exists yet. Run the full Intake Sheet from scratch and produce a new spec document.
- **Existing feature edit** — the feature is already in the app and the user wants to change it. The deliverable is a **delta**, so Phase 1 shifts shape:
  1. **Locate ground truth first.** Find the feature's current spec document (if one exists) through the spec index, and its code — screens, state primitives, entities, routes — through the spec's `enforced` anchors. Sweep with an `Explore` subagent only for what those don't give: no row, no anchors, or anchors that no longer match the code; point it at the adapter's "Code entry points" to start from. Read the existing spec, and the deviations and follow-ups of its newest run report, before asking the user anything; don't re-ask what's already documented. When its section 8 has a `Not read:` item naming files the change relies on, extend the baseline spec first: step 2's subagent, told to follow `baseline.md`'s "Extending a baseline". Then, before intake or the diagnosis goes on, show the user what it added: the report's `Added:` and `Settled:` lines, spot-checked against the spec as step 2's review does, and the `Not read:` files that are left. Show it and go on; a correction the user gives goes in as step 2 says. The `Check:` line alone is not what it added.
  2. **No spec: record a baseline spec first.** A feature that was never specced gets its spec now: a baseline of what its code does today (`feature-spec`'s "A baseline of existing code"), which the change then updates like any spec. The feature is the one the touched screens belong to, as the project groups features (a feature folder or module); the spec and its slug are named after it. Run Step 1.2 and Step 1.4's first two questions (where specs go, their style and language) first; Step 1.2 doesn't run again, and the rest of Step 1.4 runs in its place. Don't read the feature's code yourself: a search for its routes and screen files gives the subagent its starting points. **Save the request** before the subagent starts, so a session that ends during the baseline keeps it: `.mobile-dev-skills/<slug>/request.md` holds a `# Request — <feature>` heading, a `- Type:` line (`edit (<size>)`, `bug fix`, `refactor` or `missing tests`), and an `- Asked:` line quoting the user's words whole, with each later answer about the request (a bug report's steps, say) quoted on an `- Asked:` line of its own. A delegated run writes one too, beside its `brief.md`, with `- Asked: see brief.md`. Then have a `general-purpose` subagent read `${CLAUDE_SKILL_DIR}/baseline.md` and follow it. Pass it the project root, the feature and those files, the change as the user put it and its size (Step 0), the spec's path and the slug (`feature-intake`'s rule), the style references and language conventions Step 1.4 found, the adapter's path, `${CLAUDE_SKILL_DIR}/../feature-spec/SKILL.md`, the confirmed Detected stack, and the spec language rule's resolved text with its quoted-wording exception. It writes the spec and reports. How much it reads is `baseline.md`'s to decide: the prompt neither widens nor narrows it.
     - **Review the file** yourself, spot-checking a few of its anchors against the code rather than reading again every file it read, then show the user its screens and requirements, the report's `Read:` and `Not read:` lines, and the section 8 items. Ask once whether the app does anything differently, and whether to read the not-read files now or leave them for later.
     - **Fold the answers in** before intake. A correction goes into the spec once the code confirms it; one the code contradicts is a bug, which joins the change. Not-read files to read now go through "Extending a baseline", and items left for later are marked `deliberately deferred`, as in Step 1.6. Then add `- Reviewed: <date>` to `request.md`.
     - **No index row yet:** Step 1.5 adds it when it saves the change, or, after a Large change's split, the spec index's miss rule (a missing-tests run: Step 2.4). Until then, a resumed session finds the spec by its baseline items and the saved request ("Resuming").
  3. **Run intake against the delta.** The "Affected existing screens" section becomes central; "New routes" and "New entities" may legitimately be `N/A`. For every change, capture what changes, what stays, and the regression risk to current behavior.
  4. **The spec deliverable is an update to the existing spec document** (see Step 1.5), a baseline spec included, rather than a new file. A change to a split feature updates the sub-feature specs it touches, with one sheet per spec. A Large change is split as Step 1.3 says, into sub-features with specs of their own; what they change on the existing spec's screens goes in their section 3, as for any screen outside a feature, and each existing spec whose blocks they change is edited too (`feature-spec`'s "When updating an existing spec"). Either way, section 6 records behavior as Requirement/Scenario blocks (unless the user keeps an older spec's bullet format), and the code you found here supplies the `enforced` anchors of behavior that already exists.
- **Bug fix or refactor** (Step 0) — an existing-feature edit whose Phase 1 follows "Bug fix and refactor" below: it uses steps 1 and 2 above for the spec, and its own steps in place of steps 3 and 4, Step 1.3 and Step 1.4, apart from the two Step 1.4 questions a baseline spec needs. **Missing tests** (Step 0) does the same, by "Missing tests" below, and skips Steps 1.5 and 1.6 as well: the approval of its plan takes Step 1.6's place.

### Step 1.2 — Detect the tech stack

Do this early; it shapes the questions you ask.

**Saved stack — `.mobile-dev-skills/stack.md`.** Read it before anything else:

- **Fingerprint:** the output of the adapter's fingerprint command ("Project layout"), run at the project root. It leaves out the version lines a release bumps.
- **Match** → reuse the saved stack, and its conventions once Phase 2 has added them, with no sweep and no confirmation. Say so in one line that names the file, its confirmed date and the command. Re-detect when the user asks.
- **Mismatch** → re-read the manifest file only. If the stack it shows is unchanged, update the fingerprint and say so in one line; otherwise detect as below, showing what changed against the saved file.
- **No file, or a changed stack** → detect as below, and after the user confirms, write the result. A changed stack resets the conventions to `not yet confirmed`.
- **A file without a `Test packages` line** was saved before tests were detected → detect only what's missing, from the manifest's dev dependencies and one existing test, add it, and show the added lines so the user can correct them.
- **Command decision** → one line per set of the command rule's inputs (the adapter's "Commands" names them), with its command and the user's answer when the rule asked. The inputs vary per machine, so check them on every run: reuse the matching line, or decide by the rule and add a line.
- **Layout:** `# Saved stack`, then `> Confirmed <date> · fingerprint <hash>`, then the sections `## Detected stack`, `## Detected conventions` (`not yet confirmed` until Phase 2) and `## Command`, each holding what was confirmed.

**Pre-check — existing spec docs first.** Tech stacks rarely change over a project's lifetime, and previously written feature specs usually already name the detected stack (e.g. "Routing wiring (go_router)", "State management (Riverpod)"). Before sweeping code, read 1–2 recent spec docs (rows of the spec index, preferring `implemented` ones; without an index, wherever the project keeps them, e.g. `docs/specs/`); if they state the stack, take it as a strong prior and only spot-verify against the manifest file instead of running a full detection sweep. Docs can lag reality, so a quick manifest confirmation is still required — if the two disagree, trust the code and flag the stale doc to the user.

When the pre-check comes up empty, run full detection: read the manifest file (usually decisive) and skim 1–3 existing feature folders, or delegate the sweep to an `Explore` subagent (see Delegation below). Detection is two layers:

- **Stack layer** — what packages are in use: state management, routing, HTTP, codegen, serialization, DI, tests. The adapter's "Stack layer" lists them, with its rules for mixed or ambiguous cases.
- **Convention layer** — folder layout, naming style, theming, common widgets, error handling patterns, how the chosen state/HTTP libraries are wired, and how tests are laid out and set up. The adapter's "Convention probes" say what to read.

Produce the `Detected stack` part of the adapter's "Detection report", ending with "Proceeding with this stack. Confirm or correct?"

**Fallback — only when detection fails:** the adapter's fallback stack ("Stack layer"). Label every fallback explicitly, as the adapter's "Detection report" shows, and ask the user to confirm it.

### Step 1.3 — Gather requirements (`feature-intake`)

Invoke the `feature-intake` skill. It defines the six-section Intake Sheet (Summary, Routes, Affected screens, Entities & APIs, Binding logic, Figma references), the non-functional topics to cover, and the conversation rules for filling it. When the sheet is done, it returns here instead of handing off to `feature-spec`: Step 1.4 comes first.

Information may arrive incrementally (back-and-forth) or as a single dump (text file or long message). Either is fine — extract what's present, then ask only about what's missing.

**By size (Step 0):**
- **Small:** after the Summary, ask only what the one behavior needs: its trigger and result, the request and data it uses, the states it changes, that request's errors, and the non-functional topics it touches. Fields it doesn't touch say `N/A`.
- **Large:** run the full intake under the whole feature's slug, then split it before Step 1.4:
  1. **Propose the split.** Sub-features that can each be specced, approved and built on their own, each the size of a Standard feature. For each: its name and slug (e.g. `messaging-inbox`), its screens and routes, and the entities and endpoints it introduces. Order them so that each builds only on earlier ones; shared data goes in the first one that needs it. Wait for the user to confirm or change the split.
  2. **Write the sheets.** Each sub-feature's sheet goes to `.mobile-dev-skills/<sub-slug>/intake.md`: its part of the full sheet, with a Summary that names the whole feature and an out-of-scope field that names what the other sub-features cover. Fields only other sub-features need say `N/A`. Then add `> Split: <sub-slug>, …`, in the confirmed order, as the full sheet's first line.
  3. **One at a time.** Take the sub-features in that order, each as a Standard feature from Step 1.5 through Step 2.4, unless the user asks to write every spec first. Step 1.4 runs once, for all of them.

**Delegating the Q&A:** when the gap-hunt is large or requires cross-checking the codebase while questioning, you may spawn a subagent to run the interactive collection instead of doing it inline. Spawn it **synchronously** (`run_in_background: false`), give it the project root, the current Intake Sheet state plus the specific gaps, and require it to use `AskUserQuestion` for each gap (one question per turn, per the intake rules) and to leave `intake.md` alone. It returns the completed sections; you remain the owner of the sheet and write them to `intake.md`.

### Step 1.4 — Align with existing documentation

Before writing the spec, find out how this project already documents features. A spec index answers the first question below and lists the specs to take style references from. Spawn an `Explore` subagent for what is still unknown (or look yourself if the layout is already known):

- Where do feature specs live, and what naming convention do they follow? (e.g. `docs/specs/<feature-name>-feature-spec.md`, with supporting images in `docs/specs/artifacts/`.)
- What structure/sections/language do existing specs use? Read 1–2 recent ones as the style reference, and note any language conventions they enforce (e.g. a required language or script variant for spec text).
- Is there an API reference to check endpoints against? (e.g. `docs/api-reference.md`.) Cross-check every endpoint the user mentions; discrepancies become intake questions, never silent corrections.

If the project has no docs convention, default to the `feature-spec` skill's standard output and file name (`<feature-slug>-feature-spec.md`), and say so.

Feature docs in neither `feature-spec`'s ten sections nor an older spec of them with section 6 in bullets go one of two ways:
- **Docs that share one layout of their own** keep it: it is the project's spec layout, `feature-spec`'s blocks go in its screen-behavior section, and its check runs with `--own-layout`.
- **Freeform docs that share none**: when the change's feature has one, ask once whether to convert it to the template before the change, and recommend converting. The conversion follows `${CLAUDE_SKILL_DIR}/../feature-spec/conversion.md`, and the user sees it as its own change. Declined, the change edits the doc in its own form, as a layout of its own.

In a monorepo, and in a delegated run, the spec folder sits inside the project root: a docs folder outside it belongs to the repository or another part, so the app's specs go in the app's own. A delegated run takes the brief's **Specs**.

### Step 1.5 — Write the spec (`feature-spec`)

Invoke the `feature-spec` skill to turn the populated Intake Sheet into the spec document. On top of that skill:

- **Stop its Handoff after step 1 (save the file).** Step 1.6 runs the quality check, the TBD loop and the approval question.
- **A Small new feature** (Step 0) gets the skill's lighter spec.
- **File location/naming follows the conventions discovered in Step 1.4** (e.g. `docs/specs/<feature-name>-feature-spec.md`, with the feature slug as `<feature-name>`), not the skill's default, whenever the project has an established spec directory.
- **After every save, set the spec's index row to `draft`**, adding the row if it has none, and likewise the row of each existing spec the save edited.
- **A sub-feature that edits existing specs** (Step 1.1) asks once, before the writing starts, whether each edited spec gets a changelog entry, as a one-word proposal that recommends one only where the project already keeps changelogs for its specs. Tell the writer the answer; without a yes, no entry is written.
- **The spec language rule holds for this spec and every later edit to it** (Step 1.6, edit mode), in every project.
  Spec language rule (plugin option `spec_language_rule`): [${user_config.spec_language_rule}] — apply it to all spec text you write or rewrite, except quoted user wording, which stays exactly as the user wrote it. Empty brackets mean no rule. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use the default, "Chinese text must be Traditional Chinese (zh-Hant) only, never Simplified."
- You may delegate the writing to a subagent: point it at the project root, the saved `intake.md`, the `feature-spec` skill (its section 6 block format applies even where the examples use bullets), the adapter's path, 1–2 example spec docs as style references, and the API reference doc, and state the spec language rule's resolved text, with its quoted-wording exception, in its prompt. Tell it to leave `intake.md` alone; you add its `> Spec:` line. Review its output yourself before presenting it — you own the deliverable.

If the spec updates an existing document rather than creating a new one, preserve the existing document's structure and only change what the feature changes, following `feature-spec`'s "When updating an existing spec".

### Step 1.6 — Resolve open questions, then the approval gate

This step is an **iteration loop** that improves and finalizes the spec before Phase 2 — not a rubber stamp.

1. **Check.** Run `feature-spec`'s "Quality check" on the saved spec, its script first: `bash ${CLAUDE_SKILL_DIR}/../feature-spec/scripts/check_spec.sh --adapter <the adapter's path> <spec path>`, with `--own-layout` when Step 1.4 kept the project's own layout. Quote its `RESULT=` line in the reply. Its findings join the Open Questions. A change that also edited existing specs ("A run's specs" in "Spec index") runs the script on each of them too, with the same flags: each must have no finding in a block this change edited or added, while a finding elsewhere in it is older and goes under Follow-ups. Their `open` counts aren't part of the gate, since older items sit there, but a TBD this change added to one is surfaced with the rest.
   Also read the spec's design sections (section 5, and section 4's native interfaces and permissions) and its Test plan against the standards files the run will load: the adapter's "Standards", a native adapter's for native code, and the project's `.mobile-dev-skills/standards.md`. A line that prescribes what a rule there forbids (a permission request made outside the interface class the standards require, say) is a finding that joins the Open Questions: the user changes the spec or, with a yes, replaces the rule in the project's standards file, as the scaffold's Step 2 says. The code never departs from a standard in silence.
2. **Surface.** Present the spec, calling out the **Open Questions / TBDs** section explicitly: "Here are the TBDs that need resolving before code: ...". Section 6 TBDs are named by requirement id and scenario.
3. **Resolve.** Don't just leave the TBDs on the table — actively ask the user about them, one at a time (or via `AskUserQuestion` when the options are enumerable), starting with the ones that block the most implementation work. The user may answer, defer ("leave as TBD, we'll resolve later"), cut scope (a cut non-functional topic goes in section 9), or decline a quality-check finding.
4. **Edit.** Fold each answer back into the spec file immediately: update the affected sections, remove the resolved checkbox from Open Questions (deferred and declined items stay, their text followed by `— deliberately deferred` or `— declined` in English, whatever the spec's language, which the script reads as settled). Show the user what changed. In section 6, edit blocks per `feature-spec`'s "When updating an existing spec".
5. **Repeat** steps 3–4 until every open question is resolved, or explicitly deferred or declined by the user.
6. **Approval gate.** If the spec changed since the last quality check, run it again, script included; new findings go back to step 3. Only when the latest check finds nothing new and its `RESULT=` line says `open=0`, ask for approval, quoting that line in the question, naming each existing spec the change edited by its file, any scenario marked `test: manual` since approval accepts it as checked by hand, and any whose test the user skipped (Step 2.2's "Skipped tests"), and wait for it as defined in "The hard gate" above. Any further revision requests stay in this loop — Phase 1 doesn't end until the approval is explicit. On approval, set the index row to `approved`, and likewise the row of each existing spec the change edited. In a delegated run whose brief says `Approval: with the other parts`, end with the closing block instead of asking ("Delegated runs").

---

## Phase 2 — Implementation (only after approval)

### Step 2.1 — Confirm stack and conventions

Invoke the `feature-scaffold` skill, in every session that does Phase 2 work, including one that resumes at Step 2.2, 2.3 or 2.4 or reuses a saved stack. Then run its Step 1: produce the **Detected Stack + Conventions Report** (folder pattern, entity style, repository/error conventions, state primitive patterns, screen patterns, routing declaration style, theme tokens, import style, test layout and helpers) and wait for confirmation, unless `stack.md` already holds conventions under a matching fingerprint. Its Step 2, loading the standards, runs in every session that writes code, whatever Step 1 reused. Never invent a new architectural pattern when the project already has one; never substitute Riverpod for Bloc (or vice versa) just because the fallback says so — the fallback only applies when nothing was detected.

### Step 2.2 — Generate the code

Follow `feature-scaffold` for the standards, generation order, pattern sources, tests, spec anchors and hard rules. Additionally:

- **Write the task file before the first code file:** `.mobile-dev-skills/<feature-slug>/tasks.md`, from the spec's section 10 and the Conventions Report's folder pattern.

  ```markdown
  # Tasks — Saved articles
  > Spec: `docs/specs/saved-articles-feature-spec.md`
  > Baseline: analyze — 0 errors, 4 infos · tests — 212 passed, 0 failed · format — clean
  > Standards: `platforms/standards.md`, `platforms/flutter/standards.md`, `.mobile-dev-skills/standards.md`

  - [x] Entity `SavedArticle` — `lib/features/saved_articles/domain/saved_article.dart` — saved-articles.1, saved-articles.3
  - [ ] Repository — `lib/features/saved_articles/data/saved_articles_repository.dart`, `test/features/saved_articles/data/saved_articles_repository_test.dart` — saved-articles.1, saved-articles.2
  - [ ] Bookmark icon — `lib/features/articles/presentation/article_detail_screen.dart` (edit) — saved-articles.4
  - [ ] Spec anchors
  - [ ] Verification (Step 2.3)
  - [ ] Review (Step 2.4)
  ```

  - One task per file, or per group of files that only work together, in the generation order below; a layer's tests belong to its task. Each names its files, marking edits with `(edit)`, and the requirement ids it serves (the screen, for a section 6 without ids).
  - Every block still at `enforced: (filled in Phase 2)` appears in at least one task, so a new feature's tasks name every id. A block whose code already exists (a spec converted from bullets) goes on the Spec anchors task.
  - Each native interface and each permission or capability row that section 4 adds also appears in a task, its native files and declaration files named per platform (the adapter's "Native interop").
  - A scenario tested natively has its logic in the target its native tests run in: a local package, or a module with a unit-test target. When the design puts that logic in a target with none (the app target of a hybrid project, say), move it in the task split or add the test target as a task of its own, before any chunk starts; a chunk never writes logic it can't test.
  - Tick a task as soon as its files are written (for a delegated chunk, once the subagent reports), never before. When a task changes as you work (a file split, a path the user corrects), rewrite its line to match what was built.
  - A bug fix or refactor adds the `> Change:` line, its first tasks and its own steps ("Bug fix and refactor"); a missing-tests run writes its own tasks ("Missing tests").
  - In edit mode the tasks cover only the change, and each names, after its id, the scenarios the change adds or alters, as in `saved-articles.2 (Unsaved, Error — unsave fails)`. A new task file replaces one whose tasks are all ticked; a change approved while tasks are still unticked adds its tasks to the same file at approval, and unticks Spec anchors, Verification and Review.
- **Take the baseline next, still before the first code file.** On the untouched code, run Step 2.3's Analyze and Tests commands (Tests with the native unit tests of each platform whose native tests the tasks write or the spec anchors), its Format command on the existing files the tasks will edit, and its Native build for each platform whose folder the tasks name; run Codegen first when generated files are missing. Record the result as the task file's `> Baseline:` line: the issue counts, each failing test by file and description, each unformatted file and each native build's result (`tests — none` in a project with no host-test folder). A native build that fails here goes to the user before any native file is written. Mention what it shows and don't fix it. If it shows the edited files unformatted, ask once how the project formats its code, and use that form of the Format command, or none. A verification run that passed earlier in this session, with no source file changed since, serves as the baseline.
- **Record the standards** next: the `Standards:` line of the scaffold's Step 2 becomes the task file's `> Standards:` line, before the first code file, with each native adapter's file when the tasks write native code, and the project's skills it loaded. A session that resumes code work reads the standards and loads the skills again, and rewrites the line.
- **Generate file-by-file** with clear file paths, in the adapter's "Generation order", each layer's tests right after it (`feature-scaffold`'s "Tests"). Ask before overwriting anything that exists.
- **Delegation:** you may hand implementation chunks to subagents or platform-specific skills. When spawning an implementation subagent, have it load `feature-scaffold`, point it at the project root and the **on-disk spec file path** (not conversation history) plus the adapter's path (and a native adapter's, for a chunk with native code), the confirmed Conventions Report, the settled command and the skills on the project file's `Skills:` line, to load before its first file, and scope it to a coherent chunk (e.g. "data layer", "screens + states") named by its tasks and the requirement ids they cover. It writes and runs the chunk's tests by that skill's rules; a scenario it can't test comes back as a question, never as `manual`. Have it leave the spec and the state files alone and report the files it wrote, each requirement's `enforced` and each scenario's `test` in the format of `feature-scaffold`'s "Spec anchors"; you write them into the spec and tick its tasks. For a large feature, a `Plan` subagent can draft the task list from the on-disk spec.
- **A chunk's prompt points to its sources, never restates them.** It names the spec's path with the requirement ids, and the adapter section a path or command comes from, or quotes the line whole; a rule or a path written from memory is how a brief comes to contradict its source. A chunk whose brief disagrees with the spec or the adapter follows them and reports the conflict.
- **Pause after each task** when the project file's `## Workflow` part says `Pause after each task: yes`, or the user asks for it in this run. Each time you tick a task, a bug fix's, refactor's or missing-tests run's included, name its files and the tests you ran with their results (or none), and wait for the user's go-ahead before the next task. A delegated chunk pauses once its tasks are ticked. The Spec anchors task and Steps 2.3 and 2.4 go on without a pause, and resuming is unchanged: the next session starts at the first unticked task.
- **Skipped tests.** Tests can wait when delivery comes first. When the user asks to skip the tests of some scenarios, in Phase 1 or here, set each one's `test` to `none — <reason>` in the spec right away, the reason in the user's words (`none — skipped for the December release`), and rewrite the task lines that named those tests. Only a new test can be skipped: an existing test of a scenario the change alters is still rewritten to match, since it would fail otherwise, and a scenario that already has an anchored test keeps its anchor, the skip showing only on its task line (a bug fix's `Reproduction — manual`). A refactor's pin tests aren't skipped this way: declining one leaves its scenario unpinned ("Refactor"). Step 2.3 lists the skipped tests under Follow-ups, and a later missing-tests request can add them ("Missing tests"). Until it does, each skipped test is a `no test` finding, so `feature-verify` leaves the spec's `Last verified` line undated.
- Never skip error/loading/empty states. If the spec doesn't give a screen's Loading, Error, Empty or Success behavior (a scenario, a bullet in an older section 6, or `N/A — <reason>`), ask before generating that screen.

### Step 2.3 — Verification run

Once the spec anchors are filled, run the checks of the adapter's "Commands" table in its order (Codegen, l10n, Analyze, Format, Tests, Native build), then Conformance: the `feature-verify` skill on each of the run's specs ("Spec index") whose section 6 has blocks, passing it the ids of that spec's blocks this run's tasks name and this run's files. Write each command with the command settled by the command rule ("Platform commands" below); where the project's CLAUDE.md or README documents its own form of a command, use that form, still with the settled command.

- **Results.** Each check ends as `PASS`, `FAIL` or `SKIPPED — <why>`, taken from the command's output in this run, never from reading the code or from an earlier run. `SKIPPED` is only for a check that doesn't apply: its "Runs when" is false, or the user has said the project doesn't use it. A check that applies and couldn't run is a `FAIL`.
- **Against the baseline.** Analyze, Format and Tests pass when nothing is new against the baseline (Step 2.2): no issue in a file this run created, no issue count above the baseline's, and no failing test or unformatted file it doesn't list. With no `> Baseline:` line (an older task file), nothing counts as already there until the user confirms it: show each issue outside this run's files and ask. Native build passes only when its builds succeed.
- **Conformance** passes when `feature-verify` reports no finding on what this run built: the `enforced` anchors of the blocks its code tasks name, and those blocks' scenarios (in an edit, only the scenarios the tasks list). In an edit, a listed scenario whose test isn't in a file this run wrote or edited is a finding too, since its old test still passing says nothing about the change. Everything else is older behavior and doesn't fail the run: a scenario the change didn't touch (left at `test: none`, say), a block that is only on the Spec anchors task, a scenario that still holds a deferred `TBD`. Neither does a scenario whose test the user skipped (`test: none — <reason>`). Those findings go under Follow-ups, with an offer to add the missing tests as further tasks or by a later missing-tests request, which the user is free to decline. Anchored tests on its `Not run:` line (native unit tests this machine can't run) aren't findings: they go on the manual checks, with their command. A run with several specs gets a Conformance row for each in `### Verification`.
- **In a refactor or a missing-tests run**, this rule replaces the Conformance bullet above: Conformance passes only when `feature-verify` reports the findings of the run's baseline and no other, less those this run closed: a `no test` or `test missing` scenario it pinned or tested, a `moved` anchor it updated. A new finding anywhere in the spec fails it, since neither changes behavior, and a test it left untouched is what shows that. A missing-tests run also fails while a scenario still on its plan is a finding. A scenario that leaves the plan during the run (the user drops or skips it, its test fails on a THEN line, or it needs a change to the code) comes off it: its task line is rewritten, and it goes under Follow-ups.
- **Unspecified behavior** that `feature-verify` lists in this run's files goes to the user. Removing it is a fix, so run again from the earliest check it can affect; keeping it is a deviation the user agrees to. Until the user answers, it stays under Follow-ups.
- **A contradicted line** that `feature-verify` lists in a scenario this run built goes to the user with its proposed spec change: the code is fixed to the line, and the checks run again from the earliest one the fix can affect, or the spec is changed as Step 2.4's "A spec change in Phase 2" says. Until the user answers, it stays under Follow-ups, and so does one in any other scenario.
- **On a FAIL**, fix the cause in this run's files, update any anchor the fix moves, and run again from the earliest check the fix can affect. Never make a check pass by weakening it: no loosened or deleted expectation, no `skip`, no suppression comment (`// ignore`). A scenario that turns out to be wrong is a spec change for Step 1.6. After two failed fixes of a Codegen, l10n, Analyze or Native build check, call the build fixer (below) once, when there is one. When the check still fails after that, or after two failed fixes of any other check, stop fixing: mark the checks after it `NOT RUN`, record the run as below, then show the user the command, its output and what you tried.
- **The build fixer** is the adapter's build-fixer agent ("Agents"; "Plugin agents" below); for Native build, the build fixer of the native adapter ("Native adapters" above), and none without one. Pass it the project root, the check, its exact command as run, the command's output, the fixes you tried, this run's files, the spec path, the settled command, the confirmed Conventions Report and the standards files' paths. Review its edits as your own and update any anchor its renames move; anything it proposes outside this run's files, such as a dependency change, goes to the user. Then run the check again yourself: that output decides, not the agent's report.
- **A FAIL blocks "done".** Until every check is `PASS` or `SKIPPED`, open your reply with the failing check, and don't call the feature done or implemented, even when the user chooses to stop there.

Then record the run:

1. **Write the run report** to `.mobile-dev-skills/<feature-slug>/report.md`, above any earlier runs, whether or not the run passed: a `## <date> — <initial implementation, or the change>` heading (for a bug fix, refactor or missing-tests run, the label of its `> Change:` line, every label when the run has several bugs, as in `## 2026-11-17 — Bug fix 2026-11-16 — unlike below zero`) and a `Spec: <path>` line, then these sections:
   - `### Files` — each file, new or edited, with what changed in an edited one;
   - `### Verification` — the baseline line, then a table with one row per check, skipped ones included: the command as run and its result, with its counts and what any fix changed;
   - `### Review` — added by Step 2.4;
   - `### Deviations from the spec` — each default confirmed during generation and any other departure the user agreed to, with its requirement id or screen and why, or `none`. A deviation means the spec no longer states what was built, so its follow-up is an edit to the spec;
   - `### Follow-ups` — unresolved TBDs, the provisional list, anchors left at the placeholder, conformance findings outside this run, the tests the user skipped, and the manual checks.

   A run that comes back to Step 2.3, resumed after a FAIL or for a review fix, updates its own report (the newest one, when its heading names this change) instead of adding one.
2. **Once every check is `PASS` or `SKIPPED`, tick the Verification task and go on to Step 2.4** (after a review fix, to its second round). After a FAIL that stops the run, output `feature-scaffold`'s closing notes; the index row stays `approved` and the task unticked, so the next session resumes here.

### Step 2.4 — Review

Once Step 2.3 has passed, have the run reviewed in fresh subagents, never in this context, which wrote the code. Start the passes in one message so they run in parallel. Each reports and edits nothing.

| Pass | Agent | Runs when |
|---|---|---|
| Built-in | a `general-purpose` subagent told to read `${CLAUDE_SKILL_DIR}/review.md` and follow it | always |
| Platform | the adapter's reviewer agent ("Agents"), e.g. `mobile-dev-skills:flutter-reviewer` | always |
| Native | per platform, the reviewer of its native adapter ("Native adapters" above), given only that platform's native files in the adapter's language | this run wrote native code in that language for that platform |
| Security | `mobile-dev-skills:security-reviewer` | this run's files handle auth or tokens, add or change a request, read or write secrets or local storage, request a permission or add a platform declaration, or handle a deep link |

- **Prompt.** Give every pass the project root, the spec path, the requirement ids with the scenarios this run built (in an edit, the ones its tasks list), this run's files with edits marked, the confirmed Conventions Report, the standards files' paths, the platform and the settled command. The security pass also gets the areas its files touch. For a bug fix or refactor, every pass also gets its change record, each one when the run has several (with tests-only coverage, its approved plan), a missing-tests run gives its approved plan, and in a refactor the ids are the blocks whose code moved, with all their scenarios. Don't pass `model` unless the user asked for one.
- **Pass results.** Each pass ends with its findings or `no findings`, taken from its report in this run. Quote each pass's closing line in `### Review`, whole, as the pass wrote it: the built-in pass's `Built-in review: …` line, the platform or native reviewer's closing line (its adapter's "Agents" names it), security-reviewer's count per severity. A pass that returns without it didn't finish: start it once more, then record `FAIL — no report`, which blocks "done". `SKIPPED — <why>` is only for the security pass, when its "Runs when" is false, and names the triggers checked. When the platform pass names `security-reviewer` and the security pass was skipped, run it on the files that finding names. `NOT RUN — <agent> not installed` is only for a second-opinion pass whose agent can't be found ("Plugin agents" below), `NOT RUN — no reviewer for <platform>` for a platform or native pass whose adapter names `none`, or a native pass with no native adapter, and `NOT RUN — no reviewer for <language> files`, on a Native row of its own, for a platform's native files in a language its native adapter doesn't cover: none of these blocks "done", and your reply names it. A run without native code has no native row. The built-in pass always runs.
- **Settle each finding** as one of these. The spec, the Conventions Report and the standards take precedence over a second opinion.
  - **fixed** — the default, for every finding not settled otherwise;
  - **deviation** — a built-in finding the user agrees to keep. One that departs from the spec also goes under Deviations from the spec; one that departs from a convention or code rule stays in `### Review`;
  - **question** — a platform, native or security reviewer finding that contradicts the spec, the Conventions Report or the standards. Ask the user instead of editing; a change they want is a spec change ("A spec change in Phase 2" below), or a conventions change. A CRITICAL or HIGH question stays open until the user answers it;
  - **declined** — a finding that the code or the spec shows is wrong, quoting the line that shows it. A CRITICAL or HIGH finding is declined only when the user agrees;
  - **follow-up** — a second-opinion finding whose fix would touch files outside this run, or add behavior the spec doesn't state. A CRITICAL or HIGH one becomes a follow-up only when the user agrees. In a missing-tests run, any finding whose fix would change the code rather than a test is a follow-up, a bug fix to propose, whatever pass found it.
- **A fix that adds behavior the spec doesn't state** (a change to what the user sees, or to when something runs or stops, such as a request, a poll, a retry or a resume, that no scenario covers, from a review or a diagnosis) is checked against the spec before it lands. Each `fixed` finding's line in `### Review` (step 1 below) names the scenario the fix keeps true, as `<id> <title>`, or says `no behavior change`; a fix that adds a guard, a stop or a trigger has to name one. A scenario that already says it, or the user's yes, is the ground; without either, the finding is a question for the user, and the fix waits. When it lands, its tests are anchored, or the spec changes first.
- **A spec change in Phase 2** is one the user chooses in answer to a question of this step, or to a contradicted line (Step 2.3). When it only brings the spec to what the code does, and the question quoted the lines it changes, the user's answer is the approval: edit those lines at once, show the edit, run `check_spec.sh` on each edited spec, quote its `RESULT=` line, and leave the index rows as they are. A change that needs other code, or new behavior, goes through Step 1.6 like any spec change, and its code is written after the approval. Either way, run Step 2.3 again, from the earliest check the change can affect (for a spec-only edit, Conformance), on every spec it touched, before the run closes.
- **Fix, then verify again**, in this order:
  1. Write `### Review` with this round's findings and settlements, and untick the Verification task, before you edit any file.
  2. Fix by Step 2.3's rules: in this run's files, no weakened check, anchors updated.
  3. Run Step 2.3 again from the earliest check the fixes can affect, through Conformance. Every fix, to code or to tests, affects Conformance, and a search for the anchors is not a `feature-verify` run. The re-run replaces the results in `### Verification`.
  4. Review once more: only the files the fixes changed, and only with the passes whose findings you fixed. Settle that round's findings the same way, then take steps 1, 2 and 3 again for its fixes, recording the round before any edit. There is no third review.
- **The second round's passes** are new subagents of the same kinds, each given its round-1 findings and how they were settled, from `### Review`, so a resumed session works the same way; a session that still holds a round-1 reviewer may continue it by message instead. The round's rows in `### Review` say `fresh` or `continued`.
- **An open finding blocks "done"** as a failing check does: a finding not yet settled, or a fix whose verification fails.

Then record the review and end the run:

1. **Complete `### Review` in the run report**, after `### Verification`: a row per pass with its agent, its counts by severity (for a second opinion) and its closing line quoted whole, then one line per finding with its settlement: what the fix changed, the question and its answer, why it was declined, or why it is a follow-up. A question still unanswered also goes under Follow-ups.
2. **Output `feature-scaffold`'s closing notes.**
3. **Once no finding is open, set the index row of each of the run's specs to `implemented`**, copying each spec's `Last verified` line, then tick the Review task (adding it to a task file written before this step existed). A missing-tests run keeps the row's status and copies only that line (`missing-tests.md`).

---

## Bug fix and refactor

A bug fix or refactor (Step 0) runs Phase 1 and Phase 2 as an edit to an existing feature does, apart from the steps below. Each writes its reason into the spec as a change record (`feature-spec`'s "Change records") and writes no file of its own: no diagnosis or plan document.

### Bug fix

**Bug fix, Phase 1:**

1. **The report.** Get the steps that show the bug, what happens and what should, and, when it matters, the platform, the app version or a crash's stack trace. Ask for what's missing, one question per turn, and quote the user's words. For a crash:
   - **Without steps** (a Crashlytics issue, a stack trace alone, or whether a crash still happens), it needs crash triage, which this workflow doesn't do. Outside a delegated run, when a `crash-issue-fixer` skill is listed, offer to hand the report to it, and stop here when the user agrees; when none is listed, say once that the `crash-issue-fixer` plugin (`/plugin marketplace add teaualune/mobile-handytool-skills`, then `/plugin install crash-issue-fixer@mobile-handytool-skills`) does that triage. Then, or when the user declines, ask for the steps.
   - **With steps, or handed over by `crash-issue-fixer`** with the verdict and cause it found, it stays here and no hand-off is offered: the stack trace, or that cause, is where the diagnosis starts. Ask for steps only when the cause alone can't place the reproduction test.
2. **The spec.** Find the spec and the blocks the bug shows on by Step 1.1's step 1, without reading the code: the diagnosis does that. A feature with no spec gets its baseline spec first (Step 1.1's step 2, with Step 1.2 before it). Then run Step 1.2, if it hasn't run.
3. **Diagnose** in a `general-purpose` subagent told to read `${CLAUDE_SKILL_DIR}/diagnose.md` and follow it. Pass it the project root, the report, the spec's path and the blocks the bug shows on (or the screen, when no block covers it), the adapter's path, the confirmed Detected stack and the settled command.
4. **Show the diagnosis**, after checking its cause in the code yourself, there and nowhere else: the cause, the trace, the scenario with what the spec says about it, any anchored test that missed the bug, and any whose expectation states the actual result. With `cause not found`, ask the user for more (a log, exact steps, the data involved) and diagnose once more; when that finds no cause either, stop there: show both diagnoses and change nothing. Nothing is fixed on a guess.
5. **The spec change** (Step 1.5, by `feature-spec`'s "When updating an existing spec"): correct a `vague` or `wrong` scenario, or add one for `not covered`; with `states it`, the scenario's text stays as it is. A section 10 Test plan line that says nothing tests the reproduction test's layer changes too. Add the change record in every case.
6. **Approval** (Step 1.6). The quality check covers the scenario the fix corrects, adds or restores. The approval question names that scenario, the cause and each anchored test whose expectation states the actual result, which changes with the scenario, and says so when the scenario's text didn't change. A scenario at `test: manual` still gets a reproduction test at the layer of the cause when a host test there can reach it; when none can, say so, since its reproduction and its check after the fix are then manual.

**Several bugs in one spec** share one run: steps 1, 3 and 4 run per bug (the diagnoses may run in parallel, each shown before the spec change), step 5 writes a change record per bug, each next to its own requirement, and step 6 asks once, naming every bug's scenario, cause and anchored tests. Behavior the spec needs that the app never had is an edit in the same change: the same update writes its scenarios with no record, and the approval question names them apart from the bugs.

**Bug fix, Phase 2:**

1. **Tasks.** `tasks.md` gets `> Change: <the change record's label>` under its `> Spec:` line, and two tasks before Spec anchors: `Reproduction test — <test file> — <id> (<Scenario>)`, then `Fix — <files> (edit) — <id> (<Scenario>)`. When no host test can reach the bug, or the user skips its test (Step 2.2's "Skipped tests"), the first is `Reproduction — manual — <id> (<Scenario>)`. With several bugs, the `> Change:` line names every record's label, joined by ` + `, and each bug gets that pair of tasks, its reproduction test before its own fix.
2. **Reproduce**, after Step 2.2's baseline and before any fix. Write the scenario's test (the standards' "Tests"); an anchored test whose expectation states the actual result is rewritten to the approved THEN line instead, and is the reproduction test. Run it with the adapter's command for a layer's tests. It must fail on an expectation from the THEN or AND line the bug breaks. Record `> Reproduction: <command> → <the failing expectation, as the output prints it>` in `tasks.md` (for a manual one, `> Reproduction: manual — <what the user saw>`), then tick the task.
   - It passes: it didn't reproduce the bug. Fix nothing and leave the task unticked, so a resume starts here again. Show the user the test, its output and the diagnosis, and settle with them which one is wrong:
     - **The test**, when it doesn't take the report's path (other data, a fake that hides the cause, the wrong layer): rewrite it to that path, its expectations still the approved THEN line's, and run it again.
     - **The diagnosis:** diagnose again by Phase 1's steps 3 and 4, also passing the test and its output. A new cause is a spec change, since the change record and the approval named the old one: correct the record, and the scenario when the new cause changes it, for Step 1.6 before any further test or fix. The same cause leaves the test or neither.
     - **Neither**, when no host test shows the bug: if the user still sees it in the app, the task becomes `Reproduction — manual — …` (step 1) and the test that passed stays as the scenario's test; if they no longer do, stop the run there.
   - It fails another way (it doesn't compile, its setup throws): fix the test, not the code, and run it again.
3. **Fix** only the cause the diagnosis named; other problems found on the way go under Follow-ups. The reproduction test then passes, its expectations as they were when it failed.
4. **Anchors.** The scenario's `test` anchor names the reproduction test, beside any other it names that checks the corrected scenario. Rewriting an expectation to the approved THEN line follows the spec change; it doesn't weaken a check (Step 2.3).

Then Steps 2.3 and 2.4 as written.

### Refactor

**Refactor, Phase 1:**

1. **The refactor.** Get what moves where, the design it moves to, why, and any dependency it adds or removes. Ask for what's missing, one question per turn.
2. **The spec.** Find the spec, and the blocks whose `enforced` anchors name the code that moves or code that calls it (a search for its callers), by Step 1.1's step 1. A feature with no spec gets its baseline spec first (Step 1.1's step 2, with Step 1.2 before it), unless the user accepts tests-only coverage (below). Then run Step 1.2, if it hasn't run.
   - A section 6 still in the bullet format: offer `feature-spec`'s conversion first, a reformat that changes no behavior. If the user declines, nothing can be anchored or checked: the baseline is the Tests check only, and Step 2.3's Conformance is `SKIPPED — section 6 in bullets`.
3. **Baseline run**, before any change: the Tests check of the adapter's "Commands", and Conformance (`feature-verify` on the spec, run as in Step 2.3), each taken from its output in this run. Show both results.
   - A failing test that covers the code that moves (an anchored test of those blocks, or a test of a file that moves), or a finding other than `no test` and `moved`, isn't refactored over: report it, and the refactor waits until it's fixed, as a bug fix or an edit. Other failing tests are reported and kept in the baseline, as Step 2.2 does.
   - A `moved` anchor is updated with the refactor's other anchors.
4. **Unpinned behavior.** A scenario of those blocks at `test: none` has nothing to show the refactor broke it. Propose a pin test for each, written and passing before any code moves; the user may decline, and the approval then names what stays unpinned.
5. **The spec change** (Step 1.5, by `feature-spec`'s "When updating an existing spec"): only the sections that describe the code that moves, such as section 4's repository or native interfaces, section 5's state primitives or section 2's routing wiring, and section 10's Test plan where the pin tests make it untrue; nothing in section 6. Add the change record, which names the scenarios to pin and those left unpinned.
6. **Approval** (Step 1.6). The quality check covers the changed sections. The approval question names the blocks whose code moves, the tests that pin them, what stays unpinned, any dependency added or removed, and each line of the Conventions Report the new design departs from, asking whether the project now works that way. If it does, update those lines in `stack.md` once approved; if not, the departure is a deviation for the run report.

**Refactor, Phase 2:**

1. **Tasks.** `tasks.md` gets `> Change: <the change record's label>` under its `> Spec:` line. The pin tests come first, in one task, then one task per refactor step, each small enough to leave the code building and its tests passing, and each naming the ids whose code it moves.
2. **Baseline.** Step 2.2's `> Baseline:` line adds `conformance — <each finding as id and kind, or none>`: Phase 1's, or a fresh `feature-verify` run when Phase 1 ran in another session or the code changed since. A fresh run stops the refactor on whatever would have stopped Phase 1's.
3. **Pin tests** run on the untouched code and must pass. One that fails another way (it doesn't compile, a finder or a fake is wrong) is fixed in the test, without changing what it checks. One that fails on what a THEN or AND line states shows a bug: stop, and report it. Record `> Pinned: <command> → <its last output line>` in `tasks.md`, then tick the task.
4. **After each step**, run Analyze, and the tests that pin the blocks the step touches (their anchored tests and the pin tests) with the adapter's anchored-test command. Go on only when nothing is new against the baseline; a failure is fixed within the step. Tick the step's task only after those runs, adding their results to its line (`— analyze: no issues · 10 passed`).
5. **Tests keep their expectations.** A refactor edits a test only where the code it calls moved or was renamed (an import, a constructor, a fake), never an expectation: that would weaken it (Step 2.3).
6. **Anchors.** Update every `enforced` and `test` anchor the move changes (`feature-scaffold`'s "Spec anchors").

Then Steps 2.3 and 2.4 as written; Step 2.3's Conformance passes as its "In a refactor" says.

**Tests-only coverage.** A feature with no spec whose user declines the baseline spec has no spec to change, and gets no change record. Phase 1 is steps 1 and 3, with the Tests check only, then a refactor plan given in one message, as a trivial change plan is: what moves where, why, and the existing tests that cover that code (a search of the adapter's host-test folder), approved as the hard gate says. Phase 2 runs the steps above without anchors, Conformance or an index row. Its task file and run report go under a slug named after the code that moves (`feature-intake`'s rule), with `> Change: Refactor <date> — <title>` in place of the `> Spec:` and `Spec:` lines. Step 2.4's built-in pass reviews against the conventions and the standards only.

---

## Missing tests

A missing-tests request (Step 0) adds automated tests for scenarios the spec already states, and changes nothing else. Its steps for both phases are in `${CLAUDE_SKILL_DIR}/missing-tests.md`: read it as soon as Step 0 names the type, and in every session that resumes such a run (a `tasks.md` whose `> Change:` line starts `Missing tests`, or a `request.md` whose `- Type:` is `missing tests`), before its next step. The tests stay optional: the user takes any part of its plan, or none.

---

## Delegated runs

In a monorepo, a project's own workflow (the parent) may hand this skill the app's part of a feature that spans several parts, with a **delegation brief**: a `# Delegation brief — <feature>` block in this skill's arguments, or the path of a file that holds one. A brief you wrote yourself, for a request the user made directly, isn't one; that request goes by Step 0's "In a monorepo".

A delegated run's steps are in `${CLAUDE_SKILL_DIR}/delegated.md`: the brief's lines, saving it as `brief.md`, the app slice as the request, the approval, and the closing block that ends every reply that ends the run. Read it before Step 0 when a request comes with a brief, and in every session that resumes a feature whose folder holds a `brief.md` ("Resuming"). Your first reply in the run still opens with Step 0's size line for the app slice.

---

## Provisional API shapes — the one exception to "never invent"

Never invent endpoints, field names, or response shapes. **Exception:** the user explicitly says the API isn't ready yet ("backend isn't built yet", "API comes later") but wants to proceed with UI work, or a delegation brief's API contract is a spec still in `draft` ("Delegated runs"). Then:

1. State clearly that the shape is a provisional guess to unblock UI work, or, from a draft contract, a shape that may still change.
2. Show the proposed shape (from a draft contract, the shape its spec states) and get a sanity check before locking it into the spec.
3. In generated code, every provisional field, and a provisional entity's class itself, carries a `// TODO(api): provisional — confirm with backend` comment.
4. For a provisional endpoint that doesn't exist yet, the repository must be a clearly-labeled stub/mock implementation, never a call to a fabricated endpoint. A provisional field on an endpoint that exists keeps the real repository, and so does an endpoint the backend has built but not deployed, tested with fakes (`feature-spec`'s "When the API is explicitly not ready yet").
5. The spec's Open Questions section gets a dedicated "Provisional shapes — confirm with backend" list so nothing is forgotten.

The `feature-intake`, `feature-spec`, and `feature-scaffold` skills each describe how to handle provisional shapes at their stage — follow them.

## Platform commands

Settle the command once by the adapter's command rule ("Commands"), in Step 1.2 (for a trivial request, step 2 of its change plan), report it in the Detected Stack, and use it for every command the adapter names — including commands in subagent prompts and the verification run — even where the project's docs show the command without it (plain `flutter` for `fvm flutter`, say). For native unit tests ("Native adapters" above), a native adapter's command rule is settled the same way, before the first of them is written or run.

The plugin options the adapters' rules read:

fvm policy (plugin option `fvm_policy`): [${user_config.fvm_policy}] — `auto`, `always` or `never`. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use `auto`.

## Delegation guide

| Need | How |
|---|---|
| Sweep the codebase for stack/conventions or existing docs | `Explore` subagent (read-only), specific questions in the prompt |
| Record a never-specced feature's current behavior (Step 1.1) | `general-purpose` subagent told to read `baseline.md` and follow it; you review the spec it writes |
| Find a bug's cause ("Bug fix") | `general-purpose` subagent told to read `diagnose.md` and follow it; you check the cause it names |
| Interactive Q&A to fill Intake Sheet gaps | Synchronous subagent with `AskUserQuestion`, one question per turn |
| Draft the spec doc against existing style references | Subagent pointed at Intake Sheet + example specs; review before presenting |
| Task list for a big feature | `Plan` subagent, fed the on-disk spec; you write `tasks.md` |
| Implement a scoped chunk of the approved spec | Subagent pointed at the on-disk spec path + Conventions Report |
| Conformance check (Step 2.3) | `feature-verify` skill, inline or in a subagent given the adapter's path and told to report only; you write the `Last verified` line it returns |
| A Codegen, l10n, Analyze or Native build failure after two failed fixes (Step 2.3) | The adapter's build fixer, or for Native build the native adapter's; you re-run the check |
| Review (Step 2.4) | Built-in pass in a `general-purpose` subagent with `review.md`; the adapter's reviewer; a native adapter's reviewer for native code; `mobile-dev-skills:security-reviewer` when the run touches its areas |
| Requirements conversation (inline) | `feature-intake` skill |
| Spec document production | `feature-spec` skill |
| Code and test generation rules | `feature-scaffold` skill, with the adapter and the standards files |

Subagents start cold: always pass the project root, where their commands run and their paths start, and file paths (spec, examples, report, adapter) rather than assuming they can see this conversation.

**Plugin agents.** This plugin ships its agents in its `agents/` folder: each adapter's reviewer and build fixer ("Agents"), and `security-reviewer` for every platform. Call them by the scoped name, `mobile-dev-skills:<name>`. A manual copy installs them under the bare `<name>`, so when the Agent tool rejects the scoped name, use the bare one. When it rejects both, quote its error and tell the user to install the plugin's agents.

## Operating principles

- **One question per turn, ideally.** Don't dump a 12-question form on the user. Group tightly related questions only when splitting would feel unnatural.
- **Reflect back before asking more.** When the user gives a chunk of info, briefly restate your understanding ("So screen A navigates to B after a successful POST to /foo — right?") before asking the next thing.
- **Detect, don't assume.** For anything project-specific (folder structure, theme tokens, error widgets, base API client), look at existing code or ask.
- **Run platform commands per the adapter's command rule** (see "Platform commands" above) — settled once in Step 1.2 or a trivial change plan, never re-decided per command.
- **Be concrete about gaps.** If the user hasn't mentioned error, loading, or empty states for a new screen, ask. These get forgotten and bite later.
- **Treat Figma as visual ground truth.** When a Figma reference is provided, capture specific details (spacing, color tokens, component variants) in the spec so the implementer doesn't drift.

## What you do NOT do

- Don't write code in Phase 1.
- Don't proceed to Phase 2 without explicit approval of the spec.
- Don't guess at the project's folder structure or conventions.
- Don't fabricate API endpoints, field names, or model shapes — unless the provisional-shape exception applies, handled exactly as described above.
- Don't skip error/loading/empty state handling.
- Don't call a feature done while a verification check fails or a review finding is open, and don't weaken a check to make it pass.
- Don't let a subagent's output reach the user unreviewed — you own every deliverable.
