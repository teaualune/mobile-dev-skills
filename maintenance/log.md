# Maintenance log

One entry per `/maintainer` or `/testing-intake` run, newest last (formats: the "Log entry format" of `.claude/skills/maintainer/SKILL.md` and of `.claude/skills/testing-intake/SKILL.md`).

## 2026-11-15 — setup
- Checked: none; the maintainer was created. `state.json` starts empty apart from the ECC baseline `v2.2.3` @ `c05b2d6`, so the first run of each mode is a baseline review.
- Findings: none recorded. `check_contracts.py` passed with fail=0 and two WARNs, left for the first `contracts` run: `<…>` placeholders in the `flutter-build-deploy` and `mobile-store-deploy` descriptions, which the skill listing shows as `&lt;…&gt;` (https://code.claude.com/docs/en/skills.md, fetched 2026-11-15).
- Accepted: —; Rejected: —; Deferred: the two WARNs above, recorded in `state.json` → `contracts.known_warnings`; Notes: —
- Pending dry runs: none
- Evidence: https://code.claude.com/docs/en/skills.md (2026-11-15)
- Ignored instructions: none

## 2026-11-25 — testing-intake @ 320a296
- Reports: mobile-dev-skills-testing-side-check-2026-11-25.md (0.1.0-alpha.11). Taken in by hand, before the skill existed; the skill was built from this run, and `testing_intakes` was seeded with it and the 2026-11-21, 2026-11-23 and 2026-11-24 reports, whose evidence is already in `TESTING.md`.
- Fed: matched E4, D1, D4, D2, C20, C21, C25, C18, C23; new E19, E20, C26, C27, C28, C29, D9
- Analyzed: C27 fix; E20 fix; E19 fix (one run per spec); D2 fix (a `partly` match); C26, C28, C29, D9 drop (already covered, settled in the run, or by design)
- Decided: fix D2, C27, E20, E19; drop C26, C28, C29, D9; open none
- Released: 0.1.0-alpha.12, on the owner's yes after the edits; D2, E19, E20 and C27 became `fixed` with it
- Pending dry runs: none
- Ignored instructions: none

## 2026-11-27 — testing-intake @ 33ec227
- Reports: mobile-dev-skills-testing-side-check-2026-11-27.md (0.1.0-alpha.12)
- Fed: matched I11 passed, I12 passed, I1 partly, I3 partly, I8 partly, L1 partly, A3 partly; new none
- Analyzed: nothing to analyze (no new problem, no `failed` match, no `partly` match with a skipped step). I12's `passed` rests on a script that writes a manifest and has its own usage-key list, so the no-manifest and no-list paths added in 0.1.0-alpha.11 didn't run; the owner kept it `passed`
- Decided: fix none; drop none; open none
- Released: not asked (no plugin change)
- Pending dry runs: none
- Ignored instructions: none

## 2026-11-27 — testing-intake @ d8f6f3c
- Reports: mobile-dev-skills-testing-side-check-2026-11-27-swiftui.md (0.1.0-alpha.12)
- Fed: matched A2 partly, B2 partly, B19 partly; new H8, B24, B25, C28
- Analyzed: R1 H8 fix (the adapter's "No unit-test target" was silent on Xcode's default deployment target for a new target); R2 B24 fix (the entry rule didn't say whether a project CLAUDE.md line counts as asking; redrafted on the owner's word so "the workflow" counts when no project skill is a workflow it could mean, and no project's CLAUDE.md needs rewording); R3 B25 fix (`feature-spec`'s "Anchors already filled stay" was ambiguous for a bare `test: none` on an altered scenario; Phase 2's rules were already consistent); R4 C28 fix (the SwiftUI adapter's "Checks" were silent on a test runner that doesn't start; narrowed on the owner's word to shut down only the destination's simulator)
- Decided: fix H8, B24, B25, C28; drop none; open none
- Released: 0.1.0-alpha.13, on the owner's yes after the edits; H8, B24, B25 and C28 became `fixed` with it
- Pending dry runs: none
- Ignored instructions: none
