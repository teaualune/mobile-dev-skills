---
name: feature-spec-compact
description: "Compact an existing feature spec: fold its change records (changelogs, addenda, revision notes, strikethroughs) into the base sections so only the current state remains. Do NOT use to write a spec, add requirements or generate code."
argument-hint: "[path to the spec file to compact]"
---

# Feature Spec Compact

Rewrite a feature spec that has accumulated incremental change records so that only the latest state of every requirement remains — the file reads as if it had been written fresh today. Change history is never destroyed silently: the caller always decides whether it is discarded or extracted to a separate changelog file.

Compaction is a **structural** operation, not an editorial one. The set of requirements the spec expresses must be identical before and after; the only thing that changes is how the history of arriving at those requirements is recorded. If applying this skill would change what an implementer builds, something has gone wrong — stop.

Why this exists: during development, a spec picks up small incremental edits (a renamed field here, a resolved TBD there) that are pure churn and safe to erase. But some accumulated changes mark a real version boundary of the feature — those deserve to be recorded somewhere, just not inside the spec, whose job is to state the current truth cleanly.

## What counts as an incremental change record

Scan the whole file, not just the obvious sections. Look for (non-exhaustive):

| Kind | Typical shapes |
|---|---|
| Dedicated history sections | `## Changelog`, `## Revision history`, `## Updates`, `## Addendum`, `## Amendments` |
| Phased / delta sections | `## Phase 2 changes`, `### Delta — 2026-07-14`, `## v2 additions`, any section whose heading carries a date or version |
| Inline update notes | `**Update 2026-07-20:** …`, `EDIT:`, `NEW:`, `(superseded by §5)`, "was `articleId`, now `id`" |
| Strikethrough revisions | `~~old value~~ new value` |
| Duplicated sections | Two versions of the same numbered section, or two section 6 blocks with the same `id`, where the later supersedes the earlier |
| Resolved-TBD residue | Open Questions entries checked off with the answer appended next to them instead of folded into the section it belongs to |
| Bug-fix and refactor records | `> **Bug fix 2026-11-17 — unlike below zero:** …`, `> **Refactor 2026-11-17 — repository on ApiClient:** …` (`feature-spec`'s "Change records") |

Specs produced by `feature-spec` and then revised over several rounds — especially via the orchestrator's existing-feature-edit mode — typically contain several of these at once.

Not change records, even when they hold a date: the `> Last verified:` line under the H1, the section 6 block comments (`id`, `screen`, `entities`, `enforced`, `test`), and an unnumbered `## Appendix — <title>` after section 10, which holds material kept word for word for another team (`feature-spec`'s "The output template"). Keep them.

## Process

### Step 1 — Locate and inventory

If no spec path was given, ask which file to compact — when multiple spec documents exist, never guess.

**Check the structure first.** Before anything else, run `bash ${CLAUDE_SKILL_DIR}/../feature-spec/scripts/check_spec.sh <spec path>`, adding `--own-layout` when the file doesn't use the template's ten numbered sections, and keep its output for Step 5. Its findings are older than this compaction: name them in the inventory as follow-ups, never fix them here.

Read the spec end to end and build an **inventory**: every change record found, with its location (heading or approximate line), its date/version if stated, and a one-line summary of what it changes. Present the inventory to the caller before touching the file. If nothing is found, or only a record kept below, say so and stop — there is nothing to compact.

While inventorying, classify each record:

- **Dev-time increment** — a small correction or refinement made while the feature was being built; the intermediate state has no lasting value once folded in.
- **Version-boundary change** — records what changed between shipped or planned versions of the feature; the history itself likely has lasting value.

The classification is a recommendation to inform Step 2, not a decision.

**A change still being built keeps its record.** Find the spec's row in the spec index (`feature-workflow`'s "Spec index" says how). While it says `draft` or `approved`, the newest bug-fix or refactor record belongs to a change not built yet, unless a heading in the feature's run reports quotes its label: `.mobile-dev-skills/<feature-slug>/report.md` (the pre-rename `.flutter-skills/` in a project that has only that folder), which you read and never write. `feature-workflow` resumes an unbuilt change in its mode by its record, and quotes it in the run's report and review. Keep that record exactly where it is, list it in the inventory as kept until the change is built, and compact everything else. Once the row says `implemented`, or the spec has no row, the record is removed or extracted like any other (Step 2).

### Step 2 — The extraction question (mandatory gate)

Before rewriting anything, ask the caller what should happen to the change records. **Never skip this question** — deleting history without asking is the one unrecoverable mistake this skill can make. Use `AskUserQuestion` when available. The options:

1. **Discard** — the records were development churn; fold them in and delete them.
2. **Extract to a changelog file** — fold them in, and preserve every removed record in this compaction's changelog file (Step 4).
3. **Selective** — walk through the inventory together; the caller marks which entries go to the changelog file and which are discarded.

Recommend a default from the Step 1 classification — all dev-time increments → suggest **Discard**; any version-boundary entries present → suggest **Extract** or **Selective** — but the caller decides.

### Step 3 — Fold

Rewrite the spec so every base section reflects the **latest** state:

- Apply each change record to the section it modifies. Where records touch the same thing, newest wins.
- Remove the change records themselves — history sections, delta sections, inline update notes, strikethroughs. A bug-fix or refactor record holds only the reason for a change that is already in its section, so it has nothing to fold: it is removed, or extracted, unless Step 1 kept it.
- Merge duplicated sections into a single current version.
- **Preserve the document's structure.** Keep the ten-section `feature-spec` layout — or whatever project-specific structure the file actually uses. Compaction never renumbers, reorders, adds, or removes sections; a section the changes emptied out gets an explicit "N/A" line rather than silent deletion, matching the spec skill's own rule. Section 10's `### Test plan` subsection stays where it is, with changes to it folded into its lines, and so do section 4's `### Native interfaces` and `### Permissions & capabilities` tables, with changes folded into their rows.
- **Requirement blocks keep their identity.** Fold each change into the block it modifies: a changed or added result becomes a THEN/AND line of its scenario, not part of the requirement's statement. Never change an `id`: no renumbering, and a renamed block keeps its id. A block that a change record removed is deleted, and its gap stays. Behavior a record adds with no block of its own gets a new block whose id is the highest the file held before compaction, plus one. Place it with its screen's requirements, before the invariants. New blocks and scenarios get `(filled in Phase 2)` anchors, never `none`. Blocks sharing an id merge only when one supersedes the other; if they state different behavior, stop and ask. Keep the `Last verified` line exactly as it is, and each scenario's `platform` comment; a record that limits a scenario to some platforms adds one, as the spec skill's "Per-platform behavior" says. A section 6 still in the older bullet format stays a bullet list.
- `TBD` values and `PROVISIONAL` markers survive as whatever the latest state says. If an addendum resolved a TBD, fold the answer into its section and remove the checkbox from Open Questions; if it is still open, leave it exactly as it stands.
- Keep quoted user phrasing intact — where the spec quotes the user's words for business logic, the quote is the contract; fold around it, don't paraphrase it.

If two records conflict and their order cannot be determined (no dates, no version numbers, no positional clue), **stop and ask the caller which is current** — never guess which is newer.

### Step 4 — Write the changelog file (when extraction was chosen)

Naming: one file per compaction date, `changelogs/<feature-slug>/<YYYY-MM-DD>.md` in the spec's folder — e.g. compacting `docs/specs/saved-articles-feature-spec.md` on 2026-11-17 writes `docs/specs/changelogs/saved-articles/2026-11-17.md`. The feature slug is the requirement-id slug when section 6 has blocks; otherwise the spec's file name without its extension and any `-feature-spec` suffix. If the project has an established changelog or docs convention, follow that instead and say so.

Structure:

```markdown
# Changelog — <Feature Name> — <compaction date>

> Extracted from `<spec filename>` on <date> by spec compaction. The spec file records only the current state; historical changes live in this folder, one file per compaction.

## <date or version of newest entry>
<the change record's original text, quoted verbatim — not paraphrased>

## <next entry, reverse-chronological>
...
```

Rules:
- **Reverse-chronological** (newest first). Undated entries go under a `## Date unknown` heading at the bottom, in the order they appeared in the spec.
- **Quote, don't summarize.** The extracted text is the historical record; paraphrasing it defeats the purpose of keeping it.
- Never rewrite an earlier compaction's file. If today's file already exists (a second compaction the same day), **prepend** the new entries above its old ones. A single `<spec-basename>-changelog.md` from a compaction made before this layout stays where it is, untouched.
- Leave a single pointer line in the compacted spec, right under the H1 title (below its `Last verified` line, if any): `> Revision history: see changelogs/<feature-slug>/ (one file per compaction date).`, naming the older single file too when one exists. (Only when a changelog file exists — a Discard run leaves no pointer.)

### Step 5 — Verify, then report

Before presenting the result, check:

- [ ] Every requirement stated anywhere in the old file is either present in the new file or was explicitly superseded by a newer record — nothing dropped by accident.
- [ ] No change-record artifacts remain (search the result for `Update`, `Addendum`, `Changelog`, `~~`, `EDIT:`, dates in headings), apart from a record Step 1 kept, which is unchanged.
- [ ] Section structure and numbering are unchanged.
- [ ] Every requirement id from the old file is still present, unless a change record removed that block; no id changed, and `Last verified` is untouched.
- [ ] Open TBDs and `PROVISIONAL` markers survived per the latest state.
- [ ] If extraction was chosen: every removed record appears in the changelog file verbatim.
- [ ] Text you wrote or rewrote follows the spec language rule (Hard rules).
- [ ] The Step 1 script, run again the same way on the result, reports no finding whose check and message the first run didn't (line numbers move), the same `SECTION6=` and `SLUG=`, and the same `blocks=` count unless a record removed or added a block. A new finding means the fold broke the structure: fix the fold, never the finding's other causes.

Then report to the caller: both runs' `RESULT=` lines, quoted whole, how many records were folded, which sections changed, any record kept until its change is built, where the changelog file was written (if any), and a reminder that the spec now states current truth as of today — future changes should either be edited in place or deliberately recorded as new addenda until the next compaction.

## Hard rules

- **Never alter meaning.** Compaction must not add, remove, weaken, or strengthen any requirement. It is not the place to fix wording, resolve TBDs, or improve the spec — flag such urges to the caller as separate follow-ups.
- **Never delete history without the Step 2 question being answered.** Not even when the records look like obvious churn.
- **Never guess recency.** Ambiguous ordering between conflicting records is a question for the caller, not a judgment call.
- **Single-file scope.** Touch only the spec file and (optionally) this compaction's changelog file. Never edit code, other specs, the spec index (`index.md`) or the workflow's `.mobile-dev-skills/` state files; `feature-workflow` refreshes the index row from the spec.
- **Follow the spec language rule in text you write.**
  Spec language rule (plugin option `spec_language_rule`): [${user_config.spec_language_rule}] — apply it to all spec text you write or rewrite, except quoted user wording, which stays exactly as the user wrote it. Empty brackets mean no rule. If the brackets hold an unsubstituted `user_config` placeholder, the option isn't set: use the default, "Chinese text must be Traditional Chinese (zh-Hant) only, never Simplified."
  Changelog extracts are verbatim material too and stay as they are. A passage you'd otherwise leave untouched that breaks the rule is a follow-up for the caller, not a silent fix.
