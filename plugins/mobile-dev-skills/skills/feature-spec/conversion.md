# Converting a spec — `feature-spec`

A conversion brings an existing feature doc into `feature-spec`'s format: a section 6 of bullets per screen into Requirement and Scenario blocks, a layout other than the template's ten sections into them, or a project's freeform feature doc into the template. `feature-spec` converts a spec on its first non-trivial edit, once the user agrees (its "When updating an existing spec"), and `feature-workflow` Step 1.4 a freeform feature doc the same way; a spec can also be converted on its own, by hand or by a subagent given this file. The user sees the conversion as its own change, before any change to the feature goes in.

## What a conversion is

A reformat. Every statement of the original keeps its meaning and finds a place: each bullet becomes a requirement, a scenario or a line of one, other text moves where this file says, word for word, and the rest of the spec stays as it is. Nothing is added or dropped beyond what "What a conversion adds" allows. Gaps stay gaps: a state or a result the original doesn't give, or a rule another section states, is a question for the feature's next change.

Work in this order: the layout, the line under the title, the slug, section 6, the anchors. For a project's own feature doc, neither in the template's sections nor an older spec of them with section 6 in bullets, read "A project's own feature docs" first. Text you write follows the spec's language and the spec language rule, as `feature-spec` or your prompt states it; the fixed syntax stays in English (`feature-spec`'s "Section 6 — Requirement and Scenario blocks").

## The layout

A spec whose `##` sections aren't the template's ten, numbered 1 to 10 in order, is brought to them first (`feature-spec`'s "The output template"):

- **A section that matches a template section's topic** takes that section's number and place. Its heading keeps its words.
- **An extra section** becomes a `###` subsection of the template section that shares its topic: new screens and widgets go under section 7 (Design references), data and API under section 4 (Data layer); anything else under the template section before it, or under section 7 when that is section 6, which holds only blocks. Its heading keeps its words without the number, its own headings go one level down, and its text stays as it is. An eleven-section spec's `## 6. New screens / widgets` becomes `### New screens / widgets` at the end of section 7, and its `## 7. UI behavior per screen` becomes section 6.
- **A missing section** is added in its place, and an empty one filled, with `N/A — not covered by the original spec`.
- **An unnumbered `## Appendix — <title>`** after section 10 stays where it is ("A project's own feature docs").

## The line under the title

`> Last verified: never (implemented, not yet verified)`, directly below the H1 and above any other line there, such as compaction's revision-history pointer; `> Last verified: never (not implemented)` for a feature that isn't built yet.

## The slug

The ids' slug follows the `id` key's rule (`feature-spec`'s "Section 6 — Requirement and Scenario blocks"): the name of the feature's folder under `.mobile-dev-skills/` when a feature run already saved one, else the feature's name in lowercase ASCII kebab-case. That is usually the spec file's name without `.md` and any `-feature-spec` suffix (`articles` for `articles-feature-spec.md`), the name compaction also gives the feature's changelog folder, but not for a file named only `feature-spec.md` or `spec.md`.

## Section 6 as blocks

Ids run from `<slug>.1`, in the order the blocks are written: the requirements screen by screen, then the invariants. `feature-spec`'s "Section 6 — Requirement and Scenario blocks" gives the syntax (the comment keys, a SHALL sentence per requirement, one fact per line), and the template's own section 6 is a worked example (`feature-spec`'s "6. UI behavior per screen"). For each screen:

| Bullet | Becomes |
|---|---|
| Initial state | The statement of the screen's first requirement: what it requests or shows when it opens |
| Loading, Error, Empty and Success state | That requirement's `Loading`, `Error`, `Empty` and `Success` scenarios. A state the bullets say can't occur gets `N/A — <reason>` |
| User actions | A requirement per action, with its result as the THEN line. An action whose result differs when a request fails gets a second scenario for the failure, as the template's `Error — unsave fails` |
| Navigation triggers | A THEN or AND line naming the route, in the scenario of the action that opens it; one with no action bullet (a toolbar icon, back) becomes a requirement of its own |
| Side effects | AND lines in the scenario that causes them |

## Section 6 beyond the bullets

Text in section 6 that isn't one of those bullets moves out of the blocks' way, word for word:

- **Feature-level prose** before the first screen goes to section 1, after its bullets, or to section 5 when it describes the data flow (where the data comes from, what is cached, what refreshes it).
- **A screen's own prose** goes in its first requirement, as body lines after the statement.
- **`### <Screen>` headings** are dropped: each block's `screen` key names its screen, and a `###` heading in section 6 that isn't a block is a `syntax` finding.
- **Layout blueprints and per-widget styling** (a sketch of the screen, a widget tree, sizes, colors and fonts per element) go to section 7, under a `### <Screen> layout` subsection per screen.
- **A bare `N/A`** with no reason, such as `Empty: N/A.`, becomes that state's scenario with the body `N/A — no reason recorded`.
- **A recorded decision not to test** (a `Tests: none` line for a screen or the feature) becomes `test: none — <the recorded reason>` on each scenario it covers, or `none — no reason recorded` when it gives none. Never `manual`, which says no test can reach the behavior.
- **Any other line** goes with the block it describes, as a body line after its statement, or with the feature-level prose when it describes no single block.

## Anchors

- **`enforced`**: the code that carries the behavior, `<path>#<Symbol>` as the `enforced` key says, the screen's own widgets or views included; comma-separate several. `(filled in Phase 2)` only where no code can be named: behavior not built yet.
- **`test`**: an existing test only when its body checks every THEN and AND line of the scenario, named by its own description: `<path>#<description>`, the description's text exactly as the test file writes it, without the quotes or backticks around it or the name of a group or suite around the test, so that the adapter's **Test-name search** finds it. A description with an escape or an interpolation in it can't be anchored, and neither can a test that checks only some of the lines. Otherwise the `test` is:
  - `none` for behavior the app already has;
  - `none — <reason>` for a recorded decision not to test ("Section 6 beyond the bullets");
  - `(filled in Phase 2)` for behavior not built yet;
  - `manual — <reason>` only when no test in the project can reach the behavior, such as a system sheet.

## A project's own feature docs

Feature docs in neither the template's ten sections nor an older spec of them with section 6 in bullets:

- **Docs that share one layout of their own** (the same sections across the project's feature docs) keep it: it is the project's spec layout (`feature-workflow` Step 1.4). Their behavior converts by this file into blocks in the section that describes the screens' behavior, or in a section added for them (`feature-spec`'s "Section 6 — Requirement and Scenario blocks"), with the line under the title and the slug as in any spec. Their other sections stay as they are, and the check runs with `--own-layout`.
- **Freeform docs that share no layout** convert to the template:
  1. **Dated addenda** (`## Update <date>`, an `Addendum` section, revision notes) are change records: run `feature-spec-compact` on the doc first, which folds them in and asks whether their history is discarded or extracted.
  2. **Each part** goes where "The layout" sends a section of its topic, and the behavior it describes becomes section 6 blocks.
  3. **A Files list** feeds the `enforced` anchors, and stays as written in a `### Files` subsection of section 10.
  4. **Rationale** (why a behavior is as it is) becomes body lines after the statement of the requirement it explains; rationale for the whole feature goes to section 1.
  5. **Tables kept word for word for another team** (an edge-case table a backend or QA team reads) go unchanged to an unnumbered `## Appendix — <title>` after section 10, the one addition the template allows. Each behavior a row states is also a scenario in section 6.
  6. **QA checklists** go under the section 10 Test plan's Manual line, as written. A behavior an item states that no section 6 scenario states is a section 8 item, `- [ ] QA list: <the item> — no scenario states it`, never a new scenario.

## What a conversion adds

Only these, beside the moves above:

- **What the checker requires:** the `Last verified` line, the block headings, ids and comment keys, a statement per requirement, the `N/A — no reason recorded` reason, a missing or empty section's `N/A — not covered by the original spec`, and the id of a section 6 `TBD` in the section 8 item that asks it.
- **The anchors.**
- **A renamed name.** A class, file or widget name that the code shows was renamed may be corrected. List each in your report, never in the spec.

Nothing else. A behavior the code contradicts isn't corrected: it stays as written, with a section 8 item in the baseline form, `- [ ] <id> <Scenario>: uncertain — <what the code does instead>`. Lines the original doesn't have, such as accessibility, routing or entry points filled from the code, aren't part of a conversion: they wait for the feature's next change. A topic that section 9 names as not affected while its template part is there (a `layout` finding that names section 9) is settled as `feature-spec`'s "Quality check" says and named in your report.

## Before you hand back

- [ ] Every `enforced` names the code wherever it can be named, the screen's widgets included; `(filled in Phase 2)` stays only for behavior not built yet.
- [ ] Every anchored test's body checks each THEN and AND line of its scenario. A test that checks some of them is no anchor: that scenario's `test` is `none`.
- [ ] A recorded decision not to test is `none — <reason>`; `manual — <reason>` stays only where no test in the project can reach the behavior.
- [ ] Nothing is added beyond "What a conversion adds".
- [ ] Run the checker in this file's folder: `bash <this folder>/scripts/check_spec.sh --adapter <the adapter's PLATFORM.md> <spec path>`, adding `--own-layout` for a layout you kept, and quote its `RESULT=` line. No `syntax` or `layout` finding is left; a `states` or `items` finding stays only for a gap the original left.

Then report these lines; a subagent replies with them and none of the spec's text:

```
Converted — <spec path>: <n> requirements, <n> invariants, <n> scenarios — <n> with a test anchor, <n> at none, <n> manual
Layout: <the sections renumbered, moved or added>, or unchanged
Renamed: <old → new, as the code shows>, or none
Section 8: <n> uncertain, <n> QA list items, <the states or items findings left>, or none
Check: <the script's last RESULT= line>
```
