# Trigger suite — description trimming

A `claude plugin eval` suite that measures which plugin skill Claude invokes for a request. It has run in six states, each against the plugin of its time. The suite was unchanged between S0 and S1; for S2 it took the new skill names, scope and state folder, and nothing else; S3 added four monorepo cases, one case that names the workflow, and a grader:

| State | Plugin |
|---|---|
| S0 | Baseline (0.3.11) |
| S1 | Trimmed descriptions (0.3.12) |
| S2 | Renamed plugin and skills (0.3.15) |
| S3 | `feature-workflow` model-invocable for delegated runs, monorepo exclusions, four descriptions trimmed (0.3.21) |
| S4-android | The Compose adapter (0.3.26): only the two `android-*` cases, descriptions unchanged |
| S5 | `mobile-store-deploy` takes a request to submit for review (0.1.0-alpha.1): the `deploy-*` cases, the new `deploy-submit-review` among them, and the `neg-*` cases |

Versions `0.3.x` were pre-release builds on the development branch, before the version restarted at `0.1.0-alpha.1`; the results also name that branch's step numbers and plan item ids (`IMP-`, `ADD-`, `OPT-`).

## Cases

30 cases, each in its own folder with `prompt.md` (run limits, tags, expected outcome) and `case.yaml` (fixture and graders). The `android-*` cases scaffold a small Jetpack Compose app with a greeting spec and its index (`_fixture/compose-app.sh`). The others scaffold the same small Flutter app (`_fixture/flutter-app.sh`, copied into each case folder because a scaffold script must sit inside its case). The `mono-*` cases scaffold a monorepo: `backend/` and `web/` with their own specs, a root `FEATURES.md`, and the same app in `app/` (`_fixture/monorepo.sh`, which adds the project's own `cross-part-feature` skill, or `_fixture/monorepo-noparent.sh` without it; both generated from `flutter-app.sh`).

- **Positives** (`tags: positive`): `intake-*`, `spec-*`, `compact-*`, `verify-*`, `deploy-*`, `scaffold-*` and `workflow-named`. Grader `fired`: the expected skill was invoked. The first four groups also have `no-other-plugin-skill`: no other plugin skill was; `scaffold-*` has `no-workflow`: `feature-workflow` wasn't. `workflow-named` asks for the feature workflow by name, without its command (blocked by Claude Code before 0.3.21).
- **Android** (`tags: android`): `android-verify` (`fired` for `feature-verify`) and `android-intake` (`fired` for `feature-intake`), each with `no-other-plugin-skill`. S4-android: 6/6 runs passed every grader ($0.50).
- **Negatives** (`tags: negative`): `neg-*`. Grader `no-plugin-skill`.
- **Monorepo** (`tags: monorepo`): `mono-app-only`, an app-only request (`fired` for `feature-intake`, `no-other-plugin-skill`, which includes `feature-workflow`); `mono-delegate`, a delegation brief (`fired` for `feature-workflow`); `mono-cross-part` and `mono-cross-part-noparent`, a request that needs backend and web work (`no-plugin-intake-or-workflow`). The eval loads only the plugin's skills, never a fixture's `.claude/skills/`, so the parent skill in `monorepo.sh` is a file the model may find and read, not a listed skill.

All graders are free (`tool_used`); no judge model.

## Running it

Each state runs against a snapshot copy of the repo, so edits to the working tree don't race a running eval. The plugin sits in `plugins/mobile-dev-skills/`, and `claude plugin eval` reads cases only from below the plugin ("--eval-dir must stay inside the plugin root"), so the snapshot gets a copy of the suite there; the repo's plugin folder never holds it:

```bash
SNAP=<scratchpad>/snapshots/S<n>        # a copy of the repo without .git
cp -R "$SNAP/maintenance/evals" "$SNAP/plugins/mobile-dev-skills/evals"
cd "$SNAP/plugins/mobile-dev-skills" && claude plugin eval . --eval-dir evals --trust-plugin --scaffold \
  --ablation none --model claude-sonnet-5-5 --runs 3 -j 4 --threshold 0 --no-publish \
  --max-cost-usd 15 --json "$SNAP/eval-result.json"
```

Moving the plugin into that folder (0.3.16) changed no description, so no state was re-run; one `intake-describe` run against the snapshot's plugin folder showed the suite finds it there (fired, no other skill; $0.08).

- `--ablation none`: a no-plugin arm adds nothing to a trigger test, and in a two-arm run `tool_used: Skill` graders don't count toward the score.
- `--model` is pinned so states are comparable.
- `--case 'intake-*'` runs one group, e.g. to check a single skill's change.
- A run is about $0.07 and 20 s, so a full state is roughly 90 runs and $6.5.

Results per state are in `results/S<n>.md`.
