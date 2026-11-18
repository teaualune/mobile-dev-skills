# Migrating from `flutter-skills` v0.2.0

For projects set up with `flutter-skills` v0.2.0, the last release under the plugin's old name. The plugin is now `mobile-dev-skills`: it serves native SwiftUI and Jetpack Compose apps beside Flutter ones, writes tests with the code, and checks the code against its spec. Your specs and project files keep working as they are, and the skills upgrade each one the first time they change it. This guide says what to reinstall, what upgrades itself, and what you can convert yourself.

Paths in this guide are from the folder that holds it, the plugin's own folder, and paths in your project from its root.

## 1. Reinstall

The plugin, its marketplace and six of the seven skills have new names, so an update of the old install doesn't reach this release: once the marketplace is refreshed, `/plugin` lists the old plugin as failed to load, "Plugin flutter-skills not found in marketplace flutter-skills". Remove it, then install the new one.

The version starts again with the new name, at `0.1.0-alpha.1`: a newer release than v0.2.0, not an older one. It is an alpha (README, ["Alpha"](README.md#alpha)); to wait for a stable release, see "Staying on v0.2.0" below.

| | v0.2.0 | Now |
|---|---|---|
| Plugin and marketplace | `flutter-skills` | `mobile-dev-skills` |
| Feature orchestrator | `flutter-feature` | `feature-workflow` |
| Requirement gathering | `feature-intake` | `feature-intake` |
| Spec skill | `flutter-feature-spec` | `feature-spec` |
| Code generation skill | `flutter-feature-scaffold` | `feature-scaffold` |
| Spec compaction skill | `flutter-feature-spec-compact` | `feature-spec-compact` |
| Conformance check | — | `feature-verify` |
| Build skill | `flutter-build-deploy` | `mobile-build-deploy` |
| Store upload skill | `flutter-store-deploy` | `mobile-store-deploy` |
| Review and build-fix agents | — | seven, in `agents/` |

- **Plugin install** (Claude Code v2.1.271 or later):

  ```
  /plugin uninstall flutter-skills@flutter-skills
  /plugin marketplace remove flutter-skills
  /plugin marketplace add teaualune/mobile-dev-skills
  /plugin install mobile-dev-skills@mobile-dev-skills
  ```

  The install notes that two options aren't set yet; until you set them, their defaults apply (section 4). Commands change with the names: `/flutter-skills:flutter-feature` is now `/mobile-dev-skills:feature-workflow`, and so on. The orchestrator also starts when a request names it ("use the feature workflow to add …"), where v0.2.0's ran only from its command.
- **Installed for the team** (project scope: the old plugin is enabled in a committed `.claude/settings.json`): the uninstall above refuses it. Run these from the project root instead, then commit the changed `.claude/settings.json`, which now names only the new IDs:

  ```
  claude plugin uninstall flutter-skills@flutter-skills --scope project
  claude plugin marketplace remove flutter-skills
  claude plugin marketplace add teaualune/mobile-dev-skills --scope project
  claude plugin install mobile-dev-skills@mobile-dev-skills --scope project
  ```

- **Other settings that name the old IDs.** An `enabledPlugins` or `extraKnownMarketplaces` entry that the commands above didn't rewrite, such as one in `.claude/settings.local.json`, needs `mobile-dev-skills@mobile-dev-skills` and the `mobile-dev-skills` marketplace instead of `flutter-skills@flutter-skills` and `flutter-skills`. A `Read(~/.claude/plugins/cache/flutter-skills/**)` allow rule becomes `Read(~/.claude/plugins/cache/mobile-dev-skills/**)`. Otherwise the plugin doesn't load for that project, or the read prompt comes back.
- **Manual copy.** Delete the seven v0.2.0 skill folders, the table's v0.2.0 column below its first row, from the project's `.claude/skills/`, or from `~/.claude/skills/` for a personal copy. Then copy as the README's ["Manual copy"](README.md#manual-copy-no-plugin) says. It now takes `platforms/`, the agents, `third_party/`, `LICENSE` and `THIRD_PARTY_NOTICES.md` besides the skills. An old folder left behind answers the same requests as its new copy. Later updates go the same way: delete what the copy put in `.claude/`, then copy again.
- **Staying on v0.2.0.** Pin the old marketplace to its `v0.2.0` tag, so a refresh can't move it to this release:

  ```
  /plugin marketplace remove flutter-skills
  /plugin marketplace add teaualune/mobile-dev-skills#v0.2.0
  /plugin install flutter-skills@flutter-skills
  ```

  Removing the marketplace also removes the plugin installed from it, so install it again after the pinned add. For a team install (project scope, as above), run from the project root and commit the changed `.claude/settings.json`, whose marketplace entry now carries `"ref": "v0.2.0"`:

  ```
  claude plugin marketplace remove flutter-skills
  claude plugin marketplace add teaualune/mobile-dev-skills#v0.2.0 --scope project
  claude plugin install flutter-skills@flutter-skills --scope project
  ```

  A manual copy of v0.2.0 needs nothing: it changes only when you copy again.

## 2. Specs

A v0.2.0 spec keeps its ten sections and works as it is. What the current format adds arrives with the spec's first edit that isn't trivial; a trivial change plan edits the spec in the format it has, and compaction keeps a section 6 of bullets as bullets.

| A v0.2.0 spec has | The current format has | Added by |
|---|---|---|
| Section 6 as bullets per screen | Requirement and Scenario blocks with ids, each anchored to its code and its test (`feature-spec`'s "Section 6 — Requirement and Scenario blocks") | `feature-spec`, on the spec's first non-trivial edit, after asking whether to convert: `feature-spec`'s "When updating an existing spec". Decline, and the spec keeps its bullets, and its verification runs skip the conformance check |
| No `Last verified` line | `> Last verified:` under the title, dated by the conformance check | The same conversion; `feature-verify` dates it after a full pass (`feature-verify`'s "`Last verified`") |
| No spec index | An `index.md` beside the specs, with a row and a status per spec | `feature-workflow`, the first time a lookup reads the spec (`feature-workflow`'s "Spec index") |
| No `### Test plan` in section 10 | How each layer of the feature is tested | The first change that adds or alters a scenario (`feature-spec`'s "When updating an existing spec") |
| No `### Native interfaces` or `### Permissions & capabilities` in section 4 | The feature's native code and permissions, per platform | The first change that needs one (`feature-spec`'s "When updating an existing spec") |
| A `<spec-basename>-changelog.md` beside the spec, from compaction | `changelogs/<feature-slug>/<YYYY-MM-DD>.md`, one file per compaction | `feature-spec-compact` leaves the old file where it is and names it in the spec's pointer line (`feature-spec-compact`'s "Step 4 — Write the changelog file") |
| No spec for a feature | A spec for each feature a change touches | `feature-workflow` records what the feature's code does today as a baseline spec, before its first change that isn't trivial (`feature-workflow`'s "Step 1.1") |

- A bug fix or a refactor on a spec in bullets asks the same conversion question before its spec change.
- `feature-verify` has nothing to check in a section 6 of bullets: it says so and stops.

## 3. Converting a spec by hand

The recommended path is the one above: the skills convert a spec on its first non-trivial edit. To convert one sooner, without a change to go with it, do what that conversion does:

1. **The line under the title**, directly below it and above any other line there, such as compaction's revision-history pointer: `> Last verified: never (implemented, not yet verified)`, or `> Last verified: never (not implemented)` for a feature that isn't built yet.
2. **The slug** of the ids: the feature's name in lowercase kebab-case (the `id` key in `feature-spec`'s "Section 6 — Requirement and Scenario blocks"). It is usually the spec file's name without `.md` and any `-feature-spec` suffix (`articles` for `articles-feature-spec.md`), the name compaction also gives the feature's changelog folder, but not for a file named only `feature-spec.md` or `spec.md`. If a feature run already saved a folder for the feature under `.mobile-dev-skills/`, use that folder's name.
3. **Section 6 as blocks**, with nothing added and nothing dropped: every bullet becomes a requirement, a scenario or a line of one, and the rest of the spec stays as it is. Ids run from `<slug>.1`. The cited section gives the syntax (the comment keys, a SHALL sentence per requirement, one fact per line), and the template's own section 6 is a worked example (`feature-spec`'s "6. UI behavior per screen"). For each screen:

   | v0.2.0 bullet | Becomes |
   |---|---|
   | Initial state | The statement of the screen's first requirement: what it requests or shows when it opens |
   | Loading, Error, Empty and Success state | That requirement's `Loading`, `Error`, `Empty` and `Success` scenarios. A state the bullets say can't occur gets `N/A — <reason>` |
   | User actions | A requirement per action, with its result as the THEN line. An action whose result differs when a request fails gets a second scenario for the failure, as the template's `Error — unsave fails` |
   | Navigation triggers | A THEN or AND line naming the route, in the scenario of the action that opens it; one with no action bullet (a toolbar icon, back) becomes a requirement of its own |
   | Side effects | AND lines in the scenario that causes them |

   Don't fill gaps while you convert: a state or a result the bullets don't give, or a rule another section states, is a question for the feature's next change.
4. **Anchors.** Point each `enforced` at the code that carries the behavior, `<path>#<Symbol>`, and leave `(filled in Phase 2)` only where you can't name it. A scenario's `test` names an existing test only when its body checks what the scenario's THEN and AND lines say: `<path>#<description>`, the description exactly as the test's own string literal, without a `group` name. Otherwise it is `none` for behavior the app already has, `(filled in Phase 2)` in a spec of a feature not built yet, or `manual — <reason>` when no test in the project can reach it, such as a system sheet.
5. **Check it:** `/mobile-dev-skills:feature-verify <spec path>` (`/feature-verify` in a manual copy). It runs the anchored tests and lists each `enforced` placeholder as `not anchored` and each scenario without a test as `no test`, and it dates the `Last verified` line only after a run with no finding.

A refactor doesn't start while a block is `not anchored`, so anchor every `enforced` before asking for one.

## 4. Project files

- **`.flutter-store-deploy/`** keeps working: `mobile-store-deploy` reads it when it is the only config folder, and offers once per run to rename it to `.mobile-store-deploy/` (`git mv` when it is tracked). Its files keep their format. Don't keep both: with two folders the skill stops and asks which one is current.
- **`scripts/build-version.sh`** from v0.2.0 predates two changes to its template, now `platforms/flutter/build-version.sh`. Before a build, `mobile-build-deploy` checks it for both (the Flutter adapter's "Build adapter", its "Older scripts"):
  - **The command.** Its `FLUTTER_CMD=""` line ignores the skill's command decision and takes a `.fvm/` folder for an fvm pin, where the skills look only at `.fvmrc`. The skill offers to update that line and the fvm block. Declined, the script runs as it is only when its own pick matches the skill's decision.
  - **Flavors.** It always passes `--flavor` and builds `lib/main.dart` with no defines. For an app without flavors, with several flavor dimensions, or with an entry point or defines per flavor, the skill offers to update the whole script from the template, carrying your `Project config — ADAPT` values over. Declined, it stops, unless you already changed the script to build this app. An app with flavors in one dimension whose release builds `lib/main.dart` keeps this part of its script.

  The `pubspec.yaml` version lines stay as they are. A project pinned only by fvm 2's `.fvm/fvm_config.json` gets a question about fvm, plain `flutter` by default; `fvm use <version>` with fvm 3 writes the `.fvmrc` that pins it.
- **`.mobile-dev-skills/`** is new: the feature workflow keeps its state there, at the project root (the saved tech stack, and each feature's Intake Sheet, task list and run reports), so a run resumes where it stopped. Commit it, or ignore it with the two `.gitignore` lines `.mobile-dev-skills/*` and `!.mobile-dev-skills/standards.md`. Your own code and test rules go in `.mobile-dev-skills/standards.md` (README, ["Feature workflow"](README.md#feature-workflow)).
- **`.flutter-skills/`** exists only in a project that ran a pre-release build of this plugin. The skills keep reading and writing it in place of `.mobile-dev-skills/`, so its saved stack, your standards file and unfinished features carry over. To switch to the new name, run `git mv .flutter-skills .mobile-dev-skills` (or `mv` when it isn't tracked) while no feature run is in progress, and update the `.gitignore` lines above. With those lines git moves only the standards file for your teammates; on each other machine, move the rest of the old folder into `.mobile-dev-skills/` by hand. Until then, a skill that finds unfinished work in the old folder beside `.mobile-dev-skills/` asks which folder to use. The skills never move or delete either folder.
- **The spec index** sits with the specs; commit it with them.
- **Plugin options.** The two rules v0.2.0 built in are options now, and their defaults keep v0.2.0's behavior: `spec_language_rule` (Chinese in specs is Traditional Chinese only) and `fvm_policy` (`auto`: `fvm` when the project has `.fvmrc` and fvm is installed, a question when only one of the two holds). Change them in `/config` (README, ["Plugin options"](README.md#plugin-options)). A manual copy always uses the defaults.

## 5. What a feature run does now

The README describes each skill; in short, against v0.2.0:

- **Sized to the request.** A trivial tweak gets a one-paragraph change plan to approve instead of intake and a spec, and a large feature is split into sub-features with a spec each.
- **Tests and checks before "done".** Phase 2 writes a test for every scenario with the code, then runs codegen, l10n, analyze, format, the tests and the conformance check; a failing check blocks "done". A review in fresh subagents follows, against your conventions, your standards and the spec, with the Flutter agent and, when the change touches requests, auth or storage, the security agent as second opinions.
- **Bug fixes and refactors.** A bug report is traced to its cause and reproduced as a failing test before the fix. A refactor is pinned by the tests and the conformance check before any code moves.
- **Resumable.** Invoking `feature-workflow` again on a feature picks up where it stopped, from `.mobile-dev-skills/`.
- **Native apps and native code.** Native iOS (SwiftUI) and Android (Jetpack Compose) apps get the same workflow, and a Flutter feature's Swift or Kotlin code, permissions and usage strings go into its spec.
- **Monorepos.** In a repository with a backend or a web part beside the app, the skills keep to the app's folder, and a project's own workflow can hand them the app's part of a feature (README, ["Monorepos"](README.md#monorepos)).
