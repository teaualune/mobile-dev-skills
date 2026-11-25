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
