# mobile-dev-skills

A Claude Code marketplace with one plugin, `mobile-dev-skills`: a two-phase feature workflow for Flutter, native SwiftUI and native Jetpack Compose apps (requirements → spec → approval → tested code → verification → review), spec maintenance, and build & store deployment. Its specs are contracts with the code: each requirement is anchored to the code that carries it and each scenario to its test, and a conformance check confirms the anchors and runs those tests. The plugin is the [`plugins/mobile-dev-skills/`](plugins/mobile-dev-skills/) folder; [its README](plugins/mobile-dev-skills/README.md) describes what it does differently, the skills, manual copies, per-project adjustments and the plugin's options. Coming from `flutter-skills` v0.2.0? Its [migration guide](plugins/mobile-dev-skills/MIGRATION.md) says what to reinstall and how your specs carry over.

**Alpha.** The plugin is in alpha, in versions `0.1.0-alpha.N`: its skills are complete, but many of their paths have run only in test projects so far. [TESTING.md](TESTING.md) lists the end-to-end cases, which of them have passed, and what leaving alpha takes. Report problems as [issues](https://github.com/teaualune/flutter-feature-skills/issues).

## Install

Prerequisite: Claude Code v2.1.271 or later.

```
/plugin marketplace add teaualune/flutter-feature-skills
/plugin install mobile-dev-skills@mobile-dev-skills
```

Update later with `/plugin marketplace update mobile-dev-skills`, then `/plugin update mobile-dev-skills`. An install of `flutter-skills` doesn't update to this plugin; the migration guide says how to replace it, or how to keep v0.2.0 by adding its marketplace at the tag, `teaualune/flutter-feature-skills#v0.2.0`.

To try a local checkout without installing anything into `~/.claude`:

```bash
claude --plugin-dir /path/to/flutter-feature-skills/plugins/mobile-dev-skills
```

The same author's [mobile-handytool-skills](https://github.com/teaualune/mobile-handytool-skills) and [mobile-compat](https://github.com/teaualune/mobile-compat-skills) marketplaces hold four plugins the skills point to where this one stops; the plugin README's "Related plugins" lists them.

## Repository layout

- `plugins/mobile-dev-skills/` — the plugin, and all an install loads: its skills, agents, platform adapters, the record of the agents adapted from ECC, its README, the migration guide for v0.2.0 users, `LICENSE` and notices.
- `.claude-plugin/marketplace.json` — the marketplace, which lists the plugin.
- `CLAUDE.md` — how the repo is organized and the cross-file contracts to keep when editing it.
- `ROADMAP.md` — work that isn't scheduled yet.
- `TESTING.md` — the end-to-end cases, their evidence, and what leaving alpha takes.
- `.claude/skills/maintainer/` and `maintenance/` — the owner's maintenance skill and its state, the trigger evals (`maintenance/evals/`) and a chart of every use case (`maintenance/use-case-flows.md`).

## Maintaining this repo

A checkout of this repo includes an owner-only `/maintainer` skill in `.claude/skills/maintainer/`. It audits the cross-file contracts and checks toolchain, package and Claude Code releases. It loads only in sessions started inside the checkout. A plugin install loads and caches only `plugins/mobile-dev-skills/`; the marketplace's clone of the repo, in `~/.claude/plugins/marketplaces/`, still has these files, but nothing loads them there. CLAUDE.md's "Maintaining this repo" section describes it. After editing anything, run `python3 -I .claude/skills/maintainer/scripts/check_contracts.py`.

## License

[MIT](LICENSE). The plugin folder carries a copy, with ECC's MIT notice for the agents adapted from it in [THIRD_PARTY_NOTICES.md](plugins/mobile-dev-skills/THIRD_PARTY_NOTICES.md) and trademark disclaimers in [DISCLAIMERS.md](plugins/mobile-dev-skills/DISCLAIMERS.md).
