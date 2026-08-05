---
name: flutter-feature-spec-compact
description: Use this skill to compact an existing Flutter feature spec document (written by flutter-feature-spec) that has accumulated incremental change records — changelog sections, addenda, revision notes, phased updates, strikethroughs, superseded paragraphs — by folding every change into the base sections so the file records only the latest state. Triggers when the user says "compact the spec", "flatten the spec", "clean up the spec's changelog", "squash the spec revisions", "remove the addendums", or points at a spec file cluttered with change history. Before deleting anything, always asks the caller whether the removed change records should be preserved in a separate changelog file. Do NOT use this skill to write a new spec or add new requirements to one (use flutter-feature-spec), or to generate code (use flutter-feature-scaffold) — compaction never changes what the feature does.
argument-hint: "[path to the spec file to compact]"
---

# Flutter Feature Spec Compact

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
| Duplicated sections | Two versions of the same numbered section where the later supersedes the earlier |
| Resolved-TBD residue | Open Questions entries checked off with the answer appended next to them instead of folded into the section it belongs to |

Specs produced by `flutter-feature-spec` and then revised over several rounds — especially via the orchestrator's existing-feature-edit mode — typically contain several of these at once.

## Process

### Step 1 — Locate and inventory

If no spec path was given, ask which file to compact — when multiple spec documents exist, never guess.

Read the spec end to end and build an **inventory**: every change record found, with its location (heading or approximate line), its date/version if stated, and a one-line summary of what it changes. Present the inventory to the caller before touching the file. If nothing is found, say so and stop — there is nothing to compact.

While inventorying, classify each record:

- **Dev-time increment** — a small correction or refinement made while the feature was being built; the intermediate state has no lasting value once folded in.
- **Version-boundary change** — records what changed between shipped or planned versions of the feature; the history itself likely has lasting value.

The classification is a recommendation to inform Step 2, not a decision.

### Step 2 — The extraction question (mandatory gate)

Before rewriting anything, ask the caller what should happen to the change records. **Never skip this question** — deleting history without asking is the one unrecoverable mistake this skill can make. Use `AskUserQuestion` when available. The options:

1. **Discard** — the records were development churn; fold them in and delete them.
2. **Extract to a changelog file** — fold them in, and preserve every removed record in a sibling changelog file (format in Step 4).
3. **Selective** — walk through the inventory together; the caller marks which entries go to the changelog file and which are discarded.

Recommend a default from the Step 1 classification — all dev-time increments → suggest **Discard**; any version-boundary entries present → suggest **Extract** or **Selective** — but the caller decides.

### Step 3 — Fold

Rewrite the spec so every base section reflects the **latest** state:

- Apply each change record to the section it modifies. Where records touch the same thing, newest wins.
- Remove the change records themselves — history sections, delta sections, inline update notes, strikethroughs.
- Merge duplicated sections into a single current version.
- **Preserve the document's structure.** Keep the ten-section `flutter-feature-spec` layout — or whatever project-specific structure the file actually uses. Compaction never renumbers, reorders, adds, or removes sections; a section the changes emptied out gets an explicit "N/A" line rather than silent deletion, matching the spec skill's own rule.
- `TBD` values and `PROVISIONAL` markers survive as whatever the latest state says. If an addendum resolved a TBD, fold the answer into its section and remove the checkbox from Open Questions; if it is still open, leave it exactly as it stands.
- Keep quoted user phrasing intact — where the spec quotes the user's words for business logic, the quote is the contract; fold around it, don't paraphrase it.

If two records conflict and their order cannot be determined (no dates, no version numbers, no positional clue), **stop and ask the caller which is current** — never guess which is newer.

### Step 4 — Write the changelog file (when extraction was chosen)

Naming: `<spec-basename>-changelog.md` next to the spec — e.g. `docs/specs/saved-articles-feature-spec.md` → `docs/specs/saved-articles-feature-spec-changelog.md`. If the project has an established changelog or docs convention, follow that instead and say so.

Structure:

```markdown
# Changelog — <Feature Name>

> Extracted from `<spec filename>` on <date> by spec compaction. The spec file records only the current state; historical changes live here.

## <date or version of newest entry>
<the change record's original text, quoted verbatim — not paraphrased>

## <next entry, reverse-chronological>
...
```

Rules:
- **Reverse-chronological** (newest first). Undated entries go under a `## Date unknown` heading at the bottom, in the order they appeared in the spec.
- **Quote, don't summarize.** The extracted text is the historical record; paraphrasing it defeats the purpose of keeping it.
- If the changelog file already exists from a previous compaction, **prepend** the new entries above the old ones — never overwrite it.
- Leave a single pointer line in the compacted spec, right under the H1 title: `> Revision history: see <changelog filename>.` (Only when a changelog file exists — a Discard run leaves no pointer.)

### Step 5 — Verify, then report

Before presenting the result, check:

- [ ] Every requirement stated anywhere in the old file is either present in the new file or was explicitly superseded by a newer record — nothing dropped by accident.
- [ ] No change-record artifacts remain (search the result for `Update`, `Addendum`, `Changelog`, `~~`, `EDIT:`, dates in headings).
- [ ] Section structure and numbering are unchanged.
- [ ] Open TBDs and `PROVISIONAL` markers survived per the latest state.
- [ ] If extraction was chosen: every removed record appears in the changelog file verbatim.

Then report to the caller: how many records were folded, which sections changed, where the changelog file was written (if any), and a reminder that the spec now states current truth as of today — future changes should either be edited in place or deliberately recorded as new addenda until the next compaction.

## Hard rules

- **Never alter meaning.** Compaction must not add, remove, weaken, or strengthen any requirement. It is not the place to fix wording, resolve TBDs, or improve the spec — flag such urges to the caller as separate follow-ups.
- **Never delete history without the Step 2 question being answered.** Not even when the records look like obvious churn.
- **Never guess recency.** Ambiguous ordering between conflicting records is a question for the caller, not a judgment call.
- **Single-file scope.** Touch only the spec file and (optionally) its changelog file. Never edit code, other specs, or intake sheets.
