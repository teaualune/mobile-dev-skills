# Maintainer — `ecc` mode procedure

Read only when `third_party/ecc/manifest.json` exists. Every rule in SKILL.md still applies; the scripts are the same ones SKILL.md names.

1. **Target.** `check_releases.py --mode ecc` gives the newest release tag, its commit, and `behind=N` (manifest entries not yet at that commit). Prefer tags. Use the default branch only when the owner asks, pinned to the commit hash you fetched. `change=retagged` (same tag, different commit) is a high-severity finding: stop and report it.
2. **Fetch.** Make a scratchpad clone: `git init <scratch>/ecc`. Then, for each distinct base commit (each entry's `upstream_commit`) and the target commit, run `git -C <scratch>/ecc fetch --depth 1 https://github.com/affaan-m/ECC <commit>`.
3. **Renames and deletions first:** `git -C <scratch>/ecc diff --name-status -M <base> <target>`. An entry whose `upstream_path` was renamed or deleted becomes a keep/drop proposal; follow a rename before step 4.
4. **Per manifest entry:**
   - base = `git -C <scratch>/ecc show <base>:<upstream_path>`, theirs = the same at the target (renamed path if any), ours = `local_path` in the plugin folder (`plugins/mobile-dev-skills/`, which holds the manifest; `local_path` is relative to it);
   - if base and theirs are equal, the entry is unchanged — still move it to the target on acceptance;
   - otherwise write `git -C <scratch>/ecc diff <base> <target> -- <upstream_path>` to the scratchpad and run `scan_suspicious.py --diff` on it;
   - then `git merge-file -p <ours> <base> <theirs> > <merged>`. The exit code is the number of conflicts, and every conflict goes to the owner.
5. **Classify each upstream hunk:**
   - bug fixes and new checks → propose;
   - ECC infrastructure (hooks, session memory, rules that weren't vendored) → skip by default;
   - anything that undoes a recorded `modifications` entry (a `model` pin, "use proactively" wording, a rewritten description, removed inputs) → skip.
6. **Re-check every recorded modification** against the merged result. If one no longer holds, that's a finding.
7. **Propose** one diff per file, ours → merged. Include the notice header's updated `@ <short sha>`.
8. **On acceptance**, set that entry's `upstream_commit`, `upstream_tag`, `last_reviewed` and `upstream_body_sha256`: the sha256 of theirs from its first line after the frontmatter. `check_contracts.py` then confirms the merged body, minus the Inputs section, matches it. Set `state.json` → `feeds.ecc` to the target only once every entry is at the target (`behind=0` on the next status run). Until then, the feed keeps reporting `behind`.
9. **New candidate files** need a provenance and license check first — `pi/core/` and `skills/taste-application/scripts/` carry their own licenses — and are vendored only through ADD-9's rules.
