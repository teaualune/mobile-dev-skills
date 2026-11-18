#!/usr/bin/env python3
"""Deterministic subset of CLAUDE.md's cross-file contracts (maintainer skill, `contracts` mode).

Usage: check_contracts.py [--root DIR] [--anchors FILE] [--state FILE]
       check_contracts.py --pins FILE [--heading HEADING] [--min-len N] [--root DIR]
  --root     repo checkout to check (default: the checkout holding this script)
  --anchors  required wording and structure (default: <root>/maintenance/anchors.json)
  --state    known warnings (default: <root>/maintenance/state.json; a missing file means none)
  --pins     print an exact check for FILE (repo-relative), or for its HEADING section, as JSON to paste into anchors.json;
             --min-len defaults to the existing check's, else 12

Prints one line per finding — `FAIL|WARN|KNOWN|INFO  <check>  <where>  <message>` — then
`PASS  <check>` for each clean check and `SUMMARY  fail=N warn=N known=N info=N`.
A WARN whose `<check>  <where>  <message>` is listed in state.json `contracts.known_warnings`
prints as KNOWN and doesn't count as a warning.
Exit codes: 0 no FAIL; 1 at least one FAIL; 3 internal error; 4 usage/config error. Never writes files.
"""
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True  # keep __pycache__ out of the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintlib  # noqa: E402

NUMBER_WORDS = ("zero one two three four five six seven eight nine ten eleven twelve "
                "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty").split()
TEXT_EXT = {".md", ".json", ".sh", ".dart", ".yaml", ".yml", ".plist", ".py", ".txt", ".env"}
SKIP_DIRS = {".git", "node_modules", "build", ".dart_tool", "__pycache__"}
DESCRIPTION_CAP = 1536  # skill-listing truncation, code.claude.com/docs/en/skills.md
NEGATIVE_CLAUSE = re.compile(r"\b(do not|don't|never|not for|instead)\b", re.I)
FLAG = r"-{1,2}[a-z][a-z-]*"
CELL_SPLIT = re.compile(r"(?<!\\)\|")


class ConfigError(Exception):
    pass


class Out:
    def __init__(self, known):
        self.rows, self.order, self.bad = [], [], set()
        self.known = {k["warning"]: k.get("status", "known") for k in known}
        self.seen_known = set()

    def start(self, check):
        if check not in self.order:
            self.order.append(check)

    def add(self, level, check, where, msg):
        self.start(check)
        key = f"{check}  {where or '-'}  {msg}"
        if level == "WARN" and key in self.known:
            self.seen_known.add(key)
            level, msg = "KNOWN", f"{msg} [{self.known[key]}]"
        self.rows.append((level, check, where, msg))
        if level in ("FAIL", "WARN"):
            self.bad.add(check)

    def emit(self):
        for key in sorted(set(self.known) - self.seen_known):
            self.add("INFO", "known-warnings", "maintenance/state.json", f"listed warning no longer occurs: {key}")
        for level, check, where, msg in self.rows:
            print(f"{level}  {check}  {where or '-'}  {msg}")
        for check in self.order:
            if check not in self.bad:
                print(f"PASS  {check}")
        n = {lv: sum(1 for r in self.rows if r[0] == lv) for lv in ("FAIL", "WARN", "KNOWN", "INFO")}
        print(f"SUMMARY  fail={n['FAIL']} warn={n['WARN']} known={n['KNOWN']} info={n['INFO']}")
        return 1 if n["FAIL"] else 0


def walk_files(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            yield os.path.relpath(os.path.join(d, f), root)


def lineno(text, idx):
    return text.count("\n", 0, idx) + 1


def lines_of(text):
    return text.split("\n")  # not splitlines(): it also splits on U+2028 etc., which breaks line numbers


def cells(row):
    return [c.strip() for c in CELL_SPLIT.split(row.strip().strip("|"))]


def table_keys(text, after):
    """First-column cells of the first table after `after`, header and separator excluded; None if there's none."""
    start = text.find(after)
    if start < 0:
        return None
    rows = []
    for ln in lines_of(text[start:])[1:]:
        s = ln.strip()
        if s.startswith("|"):
            rows.append(cells(s))
        elif rows or s.startswith("#"):
            break
    if len(rows) < 3 or not all(re.fullmatch(r":?-+:?", x) for x in rows[1]):
        return None
    return [r[0] for r in rows[2:]]


class Repo:
    def __init__(self, root, out, plugin):
        self.root, self.out, self.cache, self.plugin = root, out, {}, plugin

    def p(self, *parts):
        """Root-relative path of a file inside the plugin folder."""
        return "/".join((self.plugin,) + parts)

    def pabs(self, *parts):
        return os.path.join(self.root, self.plugin, *parts)

    def read(self, rel, check):
        if rel not in self.cache:
            try:
                with open(os.path.join(self.root, rel), encoding="utf-8") as fh:
                    self.cache[rel] = fh.read()
            except (OSError, UnicodeDecodeError):
                self.cache[rel] = None
        if self.cache[rel] is None:
            self.out.add("FAIL", check, rel, "file missing or unreadable")
        return self.cache[rel]

    def skill_dirs(self):
        return sorted(os.path.basename(os.path.dirname(p))
                      for p in glob.glob(self.pabs("skills", "*", "SKILL.md")))

    def json(self, rel, check):
        text = self.read(rel, check)
        try:
            return json.loads(text) if text is not None else None
        except ValueError:
            return None  # reported by the syntax check


def frontmatter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fields, key = {}, None
    for line in lines_of(text[4:end]):
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            fields[key] = "" if val in (">", "|", ">-", "|-") else val.strip("\"'")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def truthy(v):
    return str(v).strip().lower() in ("true", "yes", "on", "1")


def validate_anchors(a):
    def need(cond, what):
        if not cond:
            raise ConfigError(f"anchors.json: {what}")

    def strs(x):
        return isinstance(x, list) and all(isinstance(s, str) for s in x)

    need(isinstance(a, dict), "top level must be an object")
    pf = a.get("plugin_folder")
    need(isinstance(pf, dict) and isinstance(pf.get("path"), str) and re.fullmatch(r"plugins/[\w.-]+", pf["path"])
         and all(strs(pf.get(k)) and pf.get(k) for k in ("layout", "files", "manual_copy", "repo_only"))
         and strs(pf.get("root_copies", [])) and strs(pf.get("target_project_names", [])),
         "plugin_folder needs path (plugins/<name>), layout, files, manual_copy and repo_only; root_copies and target_project_names are lists of strings")
    i = a.get("intake")
    need(isinstance(i, dict) and isinstance(i.get("file"), str) and isinstance(i.get("after"), str) and strs(i.get("lists")),
         "intake needs file, after and lists")
    need(isinstance(a.get("spec_template"), str), "spec_template must be a path")
    for k, keys in (("build_interface", ("scripts", "skill")), ("deploy_scripts", ("dir", "skill"))):
        need(isinstance(a.get(k), dict) and all(isinstance(a[k].get(x), str) for x in keys), f"{k} needs {', '.join(keys)}")
    bi = a["build_interface"]
    need(strs(bi.get("flags")) and bi.get("flags") and isinstance(bi.get("platforms"), dict)
         and all(isinstance(v, dict) and isinstance(v.get("line"), str) and isinstance(v.get("key"), str) for v in bi["platforms"].values()),
         "build_interface needs flags, and platforms mapping a flag to its printed line and manifest key")
    need(isinstance(a["deploy_scripts"].get("required_args", {}), dict), "deploy_scripts.required_args must be an object")
    sc = a.get("spec_checker")
    need(isinstance(sc, dict) and isinstance(sc.get("script"), str) and isinstance(sc.get("template"), str)
         and isinstance(sc.get("callers"), dict) and sc["callers"]
         and all(isinstance(v, dict) and strs(v.get("flags", [])) for v in sc["callers"].values()),
         "spec_checker needs script, template, and callers mapping a file to {flags, kinds}")
    for c in a.get("counts", []):
        need(isinstance(c, dict) and isinstance(c.get("file"), str) and isinstance(c.get("text"), str), "counts[] needs file and text")
    pl = a.get("platforms")
    if pl is not None:
        need(isinstance(pl, dict) and isinstance(pl.get("common_standards"), str) and isinstance(pl.get("checks_after"), str)
             and strs(pl.get("sections")) and strs(pl.get("checks")) and strs(pl.get("agent_roles")) and strs(pl.get("citing", []))
             and isinstance(pl.get("labels", {}), dict) and all(strs(v) for v in pl.get("labels", {}).values()),
             "platforms needs common_standards, checks_after, sections, checks and agent_roles; citing is a list and labels maps a section to strings")
    need(isinstance(a.get("count_facts", {}), dict), "count_facts must be an object")
    for fact, spec in a.get("count_facts", {}).items():
        need(isinstance(spec, dict) and strs(spec.get("exclude")), f"count_facts.{fact} needs an exclude list")
    need(isinstance(a.get("user_config", {}), dict), "user_config must be an object")
    for key, uc in a.get("user_config", {}).items():
        need(isinstance(uc, dict) and strs(uc.get("files")) and isinstance(uc.get("fallback"), str), f"user_config.{key} needs files and fallback")
        for r in uc.get("restated", []):
            need(isinstance(r, dict) and isinstance(r.get("file"), str) and isinstance(r.get("text"), str), f"user_config.{key}.restated[] needs file and text")
    for m in a.get("mentions", []):
        need(isinstance(m, dict) and (isinstance(m.get("glob"), str) or (strs(m.get("glob")) and m.get("glob")))
             and isinstance(m.get("word"), str) and strs(m.get("allowed")) and strs(m.get("exclude", [])),
             "mentions[] needs glob (a string or a list), word and allowed; exclude, when present, is a list of path prefixes")
    sib = a.get("siblings")
    if sib is not None:
        need(isinstance(sib, dict) and strs(sib.get("allowed_files")) and isinstance(sib.get("plugins"), list)
             and all(isinstance(p, dict) and all(isinstance(p.get(k), str) for k in ("plugin", "marketplace", "repo", "skill"))
                     and strs(p.get("mentioned_in")) and isinstance(p.get("listed_only", False), bool) for p in sib.get("plugins", [])),
             "siblings needs allowed_files and plugins[] of {plugin, marketplace, repo, skill, mentioned_in: [...], listed_only?}")
    for k in ("user_invoked_only", "path_docs", "path_prefixes", "plugin_forbidden_keys", "allowed_substitutions"):
        need(strs(a.get(k, [])), f"{k} must be a list of strings")
    v = a.get("vendored")
    if v is not None:
        need(isinstance(v, dict) and all(isinstance(v.get(k), str) for k in ("manifest", "notices", "inputs_heading", "description_suffix", "license_sha256"))
             and strs(v.get("allowed_keys")) and strs(v.get("forbidden_description_words", [])) and strs(v.get("required_modifications", []))
             and isinstance(v.get("agent_description_budget_chars", 0), int),
             "vendored needs manifest, notices, inputs_heading, description_suffix, license_sha256 and allowed_keys; forbidden_description_words is a list of strings")
        need(isinstance(v.get("agents", {}), dict) and all(isinstance(s, dict) and strs(s.get("tools")) and isinstance(s.get("description", ""), str)
                                                           and isinstance(s.get("modifications", 0), int) for s in v.get("agents", {}).values()),
             "vendored.agents maps an agent name to {tools: [...], description?, modifications?: <count>}")
    for c in a.get("contracts", []):
        need(isinstance(c, dict) and isinstance(c.get("id"), str), "contracts[] needs id")
        cid = c["id"]
        for chk in c.get("checks", []):
            need(isinstance(chk, dict) and isinstance(chk.get("file"), str), f"contract {cid}: checks[] needs file")
            for k in ("contains", "not_contains", "line_prefixes"):
                need(strs(chk.get(k, [])), f"contract {cid}: {k} must be a list of strings")
            need(all(strs(p) and len(p) == 2 for p in chk.get("order", [])), f"contract {cid}: order entries are [before, after]")
            need(chk.get("exact") in (None, True) or isinstance(chk.get("exact"), str), f"contract {cid}: exact is true or a `## ` heading")
            need(isinstance(chk.get("min_len", 12), int), f"contract {cid}: min_len is an integer")
            need(isinstance(chk.get("row_contains", {}), dict) and all(strs(v) for v in chk.get("row_contains", {}).values()),
                 f"contract {cid}: row_contains maps a row prefix to strings")
        for g in c.get("identical_lines", []):
            need(isinstance(g, dict) and isinstance(g.get("prefix"), str) and strs(g.get("files")), f"contract {cid}: identical_lines needs prefix and files")
        for g in c.get("identical_rows", []):
            need(isinstance(g, dict) and strs(g.get("rows")) and strs(g.get("files")) and strs(g.get("normalize", [])),
                 f"contract {cid}: identical_rows needs rows and files")
        for g in c.get("same_value", []):
            need(isinstance(g, list) and len(g) > 1 and all(isinstance(p, dict) and isinstance(p.get("file"), str) and isinstance(p.get("regex"), str) for p in g),
                 f"contract {cid}: same_value groups are lists of {{file, regex}}")
        for g in c.get("same_table_keys", []):
            need(isinstance(g, list) and len(g) > 1 and all(isinstance(p, dict) and isinstance(p.get("file"), str) and isinstance(p.get("after"), str) for p in g),
                 f"contract {cid}: same_table_keys groups are lists of {{file, after}}")


def check_syntax(repo):
    c = "syntax"
    repo.out.start(c)
    plutil = shutil.which("plutil")
    for rel in walk_files(repo.root):
        p = os.path.join(repo.root, rel)
        ext = os.path.splitext(rel)[1]
        if ext == ".sh":
            r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
            if r.returncode:
                repo.out.add("FAIL", c, rel, "bash -n: " + maintlib.one_line(r.stderr.replace(p, rel), 200))
        elif ext == ".json":
            try:
                with open(p, encoding="utf-8") as fh:
                    json.load(fh)
            except (OSError, ValueError) as e:
                repo.out.add("FAIL", c, rel, f"invalid JSON: {e}")
        elif ext == ".py":
            try:
                with open(p, encoding="utf-8") as fh:
                    compile(fh.read(), rel, "exec")
            except (OSError, SyntaxError, ValueError) as e:
                repo.out.add("FAIL", c, rel, f"python syntax: {e}")
        elif ext == ".plist":
            if not plutil:
                repo.out.add("WARN", c, rel, "plutil not found; plist not linted")
                continue
            r = subprocess.run([plutil, "-lint", p], capture_output=True, text=True)
            if r.returncode:
                repo.out.add("FAIL", c, rel, "plutil -lint: " + maintlib.one_line(r.stdout.replace(p, rel)))


def check_hidden_unicode(repo):
    c = "hidden-unicode"
    repo.out.start(c)
    for rel in walk_files(repo.root):
        if os.path.splitext(rel)[1] not in TEXT_EXT:
            continue
        try:
            with open(os.path.join(repo.root, rel), encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        for i, cp in maintlib.hidden_chars(text):
            repo.out.add("FAIL", c, f"{rel}:{lineno(text, i)}", f"hidden/bidi character U+{cp:04X}")


def check_frontmatter(repo, anchors, facts):
    c = "skill-frontmatter"
    repo.out.start(c)
    user_only = set(anchors.get("user_invoked_only", []))
    found_user_only, total = set(), 0
    for name in repo.skill_dirs():
        rel = repo.p("skills", name, "SKILL.md")
        text = repo.read(rel, c)
        if text is None:
            continue
        fm = frontmatter(text)
        if fm is None:
            repo.out.add("FAIL", c, rel, "no frontmatter starting on line 1")
            continue
        if fm.get("name") != name:
            repo.out.add("FAIL", c, rel, f"name {fm.get('name')!r} != folder {name!r}")
        desc = (fm.get("description", "") + " " + fm.get("when_to_use", "")).strip()
        if not desc:
            repo.out.add("FAIL", c, rel, "description missing")
        if len(desc) > DESCRIPTION_CAP:
            repo.out.add("FAIL", c, rel, f"description {len(desc)} chars > {DESCRIPTION_CAP} (truncated in listing)")
        if "<" in desc or ">" in desc:
            repo.out.add("WARN", c, rel, "description contains < or > (listed as &lt; / &gt;; use [x])")
        if desc and not NEGATIVE_CLAUSE.search(desc):
            repo.out.add("WARN", c, rel, "description states no 'do NOT use for' clause")
        if truthy(fm.get("disable-model-invocation", "")):
            found_user_only.add(name)
        else:
            total += len(desc)
        n = len(lines_of(text))
        if n > 500:
            repo.out.add("WARN", c, rel, f"{n} lines > 500 (docs: keep SKILL.md under 500)")
    if found_user_only != user_only:
        repo.out.add("FAIL", c, repo.p("skills", "*", "SKILL.md"),
                     f"disable-model-invocation set on {sorted(found_user_only)}, expected {sorted(user_only)}")
    budget = anchors.get("description_budget_chars")
    repo.out.add("INFO", c, "-", f"model-invocable descriptions total {total} chars (budget {budget})")
    if budget and total > budget:
        repo.out.add("WARN", c, "-", f"always-listed descriptions grew past budget: {total} > {budget}")
    dirs = set(repo.skill_dirs())
    facts["skills"] = len(dirs)
    facts["model_invocable"] = facts["skills"] - len(found_user_only)
    for fact, spec in anchors.get("count_facts", {}).items():
        for gone in sorted(set(spec["exclude"]) - dirs):
            repo.out.add("FAIL", c, "maintenance/anchors.json", f"count_facts.{fact} excludes {gone!r}, which isn't a skill")
        facts[fact] = len(dirs - set(spec["exclude"]))


def frontmatter_lines(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    return None if end < 0 else [ln.strip() for ln in lines_of(text[4:end])]


def body_without(text, heading):
    """Text after the frontmatter, minus the section that starts at `heading` (up to the next `## `)."""
    end = text.find("\n---\n", 4) if text.startswith("---\n") else -1
    body = text[end + 5:] if end >= 0 else text
    i = body.find("\n" + heading + "\n")
    if i >= 0:
        j = body.find("\n## ", i + 1)
        body = body[:i + 1] + (body[j + 1:] if j >= 0 else "")
    return body


def check_vendored(repo, anchors, facts):
    c = "vendored"
    repo.out.start(c)
    agent_files = sorted(os.path.relpath(p, repo.root) for p in glob.glob(repo.pabs("agents", "*.md")))
    facts["agents"] = len(agent_files)
    v = anchors.get("vendored")
    if not v:
        return
    mrel = v["manifest"]
    # local_path and the agents' notice name paths from the plugin folder, which ships the manifest.
    mrel_in_plugin = os.path.relpath(mrel, repo.plugin)
    listed = {}
    m = repo.json(mrel, c) if os.path.isfile(os.path.join(repo.root, mrel)) else None
    up = m.get("upstream") if isinstance(m, dict) else None
    if m is None:
        repo.out.add("FAIL", c, mrel, "missing or not JSON")
    elif not isinstance(up, dict) or not all(isinstance(up.get(k), str) and up[k] for k in ("repo", "license", "copyright")):
        repo.out.add("FAIL", c, mrel, "upstream needs repo, license and copyright")
        up = None
    elif not isinstance(m.get("files"), list):
        repo.out.add("FAIL", c, mrel, "files must be a list")
    if up:
        sources = repo.json("maintenance/sources.json", c)
        feeds = [f for f in sources.get("feeds", []) if isinstance(f, dict) and f.get("requires") == mrel] if isinstance(sources, dict) else []
        if len(feeds) != 1 or feeds[0].get("url") != up["repo"]:
            repo.out.add("FAIL", c, "maintenance/sources.json", f"needs one feed that requires {mrel}, with url {up['repo']}")
        lm = re.search(r"^Copyright \(c\) .+$", repo.read("LICENSE", c) or "", re.M)
        slug = up["repo"].rstrip("/").split("github.com/")[-1]
        state = repo.json("maintenance/state.json", c)
        seen = (state.get("feeds", {}).get(feeds[0]["id"], {}) if feeds and isinstance(state, dict) else {}) or {}
        for i, e in enumerate(m.get("files") if isinstance(m.get("files"), list) else []):
            where = f"{mrel} files[{i}]"
            keys = ("local_path", "upstream_path", "upstream_commit", "upstream_tag", "last_reviewed", "upstream_body_sha256")
            if not isinstance(e, dict) or not all(isinstance(e.get(k), str) and e[k] for k in keys):
                repo.out.add("FAIL", c, where, f"needs {', '.join(keys)}")
                continue
            if not re.fullmatch(r"[0-9a-f]{40}", e["upstream_commit"]):
                repo.out.add("FAIL", c, where, "upstream_commit must be a full 40-character hash")
            try:
                datetime.date.fromisoformat(e["last_reviewed"])
            except ValueError:
                repo.out.add("FAIL", c, where, "last_reviewed must be a real YYYY-MM-DD date")
            if (e["upstream_tag"] == seen.get("value")) != (e["upstream_commit"] == seen.get("commit")):
                repo.out.add("FAIL", c, where, f"tag {e['upstream_tag']} and commit disagree with state.json feeds.{feeds[0]['id']}")
            mods = e.get("modifications")
            if not isinstance(mods, list) or not mods or not all(
                    isinstance(x, dict) and all(isinstance(x.get(k), str) and x[k].strip() for k in ("what", "why")) for x in mods):
                repo.out.add("FAIL", c, where, "modifications must be a non-empty list of {what, why}")
            count = v.get("agents", {}).get(os.path.splitext(os.path.basename(e["local_path"]))[0], {}).get("modifications")
            if count is not None and isinstance(mods, list) and len(mods) != count:
                repo.out.add("FAIL", c, where, f"{len(mods)} modifications; maintenance/anchors.json vendored.agents expects {count}")
            whats = " ".join(x.get("what", "") for x in mods if isinstance(x, dict)) if isinstance(mods, list) else ""
            for w in v.get("required_modifications", []):
                if w not in whats:
                    repo.out.add("FAIL", c, where, f"no modification record mentions {w!r}")
            lp = repo.p(e["local_path"])
            if lp in listed:
                repo.out.add("FAIL", c, where, f"{e['local_path']} listed twice")
            listed[lp] = e
            text = repo.read(lp, c)
            if text is None:
                continue
            fm = frontmatter_lines(text)
            notice = [f"# SPDX-License-Identifier: {up['license']}",
                      f"# {up['copyright']} (ECC); modifications {lm.group(0) if lm else '<LICENSE copyright line>'}",
                      f"# Derived from {slug} {e['upstream_path']} @ {e['upstream_commit'][:7]} (see {mrel_in_plugin})"]
            for line in notice:
                if fm is None or line not in fm:
                    repo.out.add("FAIL", c, lp, f"frontmatter lacks the notice line {line!r}")
            got = hashlib.sha256(body_without(text, v["inputs_heading"]).encode("utf-8")).hexdigest()
            if got != e["upstream_body_sha256"]:
                repo.out.add("FAIL", c, lp, f"body outside {v['inputs_heading']!r} differs from upstream (sha256 {got[:12]}…, manifest {e['upstream_body_sha256'][:12]}…)")
        for rel in walk_files(repo.root):
            if rel.startswith(tuple(repo.p(d, "") for d in ("agents", "skills", "platforms"))) and rel.endswith(".md") and rel not in listed \
                    and f"Derived from {slug} " in (repo.read(rel, c) or ""):
                repo.out.add("FAIL", c, rel, f"says it is derived from {slug} but isn't in {mrel}")
        nt = repo.read(v["notices"], c)
        for s in [up["copyright"], up["repo"], mrel_in_plugin]:
            if nt is not None and s not in nt:
                repo.out.add("FAIL", c, v["notices"], f"missing: {s!r}")
        blocks = re.findall(r"^```\n(.*?)^```$", nt or "", re.M | re.S)
        if v.get("license_sha256") and not any(hashlib.sha256(b.encode("utf-8")).hexdigest() == v["license_sha256"] for b in blocks):
            repo.out.add("FAIL", c, v["notices"], "no fenced block matches the upstream license text (vendored.license_sha256)")
        plugin = repo.json(repo.p(".claude-plugin", "plugin.json"), c)
        if isinstance(plugin, dict) and "ecc" in json.dumps(plugin.get("dependencies", [])).lower():
            repo.out.add("FAIL", c, repo.p(".claude-plugin", "plugin.json"), "depends on ECC; vendored copies replace it")
    spec = v.get("agents", {})
    names = sorted(os.path.splitext(os.path.basename(p))[0] for p in agent_files)
    if names != sorted(spec):
        repo.out.add("FAIL", c, repo.p("agents", ""), f"holds {names}; maintenance/anchors.json vendored.agents lists {sorted(spec)}")
    total = 0
    for rel in agent_files:
        name = os.path.splitext(os.path.basename(rel))[0]
        text = repo.read(rel, c) or ""
        fm = frontmatter(text)
        if fm is None:
            repo.out.add("FAIL", c, rel, "no frontmatter starting on line 1")
            continue
        if fm.get("name") != name:
            repo.out.add("FAIL", c, rel, f"name {fm.get('name')!r} != file {name!r}")
        for k in sorted(set(fm) - set(v.get("allowed_keys", fm))):
            repo.out.add("FAIL", c, rel, f"declares {k!r}; agents here set only {v['allowed_keys']}")
        desc = fm.get("description", "")
        total += len(desc)
        if not desc.endswith(v.get("description_suffix", "")) or not NEGATIVE_CLAUSE.search(desc):
            repo.out.add("FAIL", c, rel, f"description must end with {v.get('description_suffix')!r}")
        for w in v.get("forbidden_description_words", []):
            if w.lower() in desc.lower():
                repo.out.add("FAIL", c, rel, f"description contains {w!r}")
        tools = sorted(t.strip() for t in fm.get("tools", "").split(",") if t.strip())
        if name in spec and tools != sorted(spec[name]["tools"]):
            repo.out.add("FAIL", c, rel, f"tools {tools} != {sorted(spec[name]['tools'])}")
        if name in spec and "description" in spec[name] and desc != spec[name]["description"]:
            repo.out.add("FAIL", c, rel, f"description differs from maintenance/anchors.json vendored.agents: {desc!r}")
        if rel in listed and text.count(v["inputs_heading"]) != 1:
            repo.out.add("FAIL", c, rel, f"needs exactly one {v['inputs_heading']!r} section")
        if "${" in text:
            repo.out.add("FAIL", c, f"{rel}:{lineno(text, text.find('${'))}", "'${' in an agent file")
    for rel in agent_files:
        if rel not in listed and os.path.isfile(os.path.join(repo.root, mrel)):
            repo.out.add("WARN", c, rel, f"not in {mrel}; fine for an agent of this repo's own, but its notice rules don't apply")
    budget = v.get("agent_description_budget_chars")
    repo.out.add("INFO", c, "-", f"agent descriptions total {total} chars (budget {budget})")
    if budget and total > budget:
        repo.out.add("WARN", c, "-", f"always-listed agent descriptions grew past budget: {total} > {budget}")


def section(text, heading):
    """Body of the `## heading` section (up to the next `## `), or None."""
    m = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else None


def check_platforms(repo, anchors, facts):
    c = "platforms"
    repo.out.start(c)
    p = anchors.get("platforms")
    adapters = sorted(glob.glob(repo.pabs("platforms", "*", "PLATFORM.md")))
    facts["platforms"] = len(adapters)
    if not p:
        if adapters:
            repo.out.add("FAIL", c, "maintenance/anchors.json", "platforms/ holds adapters but there is no platforms object to check them against")
        return
    facts["adapter_sections"] = len(p["sections"])
    common = p["common_standards"]
    if not os.path.isfile(os.path.join(repo.root, common)):
        repo.out.add("FAIL", c, common, "common standards file missing")
    # Projects add or replace rules under these headings ("Standards" contract), so every standards file keeps them.
    for std in [common] + sorted(os.path.relpath(x, repo.root) for x in glob.glob(repo.pabs("platforms", "*", "standards.md"))):
        heads = re.findall(r"^## (.+)$", repo.read(std, c) or "", re.M)
        if os.path.isfile(os.path.join(repo.root, std)) and heads != ["Code", "Tests"]:
            repo.out.add("FAIL", c, std, f"headings {heads} != ['Code', 'Tests']")
    if not adapters:
        repo.out.add("FAIL", c, repo.p("platforms", ""), "no platforms/<name>/PLATFORM.md")
    for path in sorted(glob.glob(repo.pabs("platforms", "**", "*"), recursive=True)):
        rel = os.path.relpath(path, repo.root)
        if os.path.isfile(path) and rel.endswith(".md") and "${" in (repo.read(rel, c) or ""):
            text = repo.read(rel, c)
            repo.out.add("FAIL", c, f"{rel}:{lineno(text, text.find('${'))}",
                         "'${' in an adapter file, which gets no substitution; the loading skill states the value")
    agent_names = {os.path.splitext(os.path.basename(x))[0] for x in glob.glob(repo.pabs("agents", "*.md"))}
    seen, claimed, plats = {}, {}, {}
    for path in adapters:
        rel = os.path.relpath(path, repo.root)
        base = os.path.dirname(path)
        text = repo.read(rel, c) or ""
        heads = re.findall(r"^## (.+)$", text, re.M)
        if heads != p["sections"]:
            repo.out.add("FAIL", c, rel, f"sections {heads} != {p['sections']}")
        h1 = re.search(r"^# (.+)$", text, re.M)
        applies = " ".join((section(text, "## Applies when") or "").split())
        if not h1 or not applies:
            repo.out.add("FAIL", c, rel, "needs an H1 and an 'Applies when' condition")
        for key, val in (("H1", h1.group(1) if h1 else ""), ("Applies when", applies)):
            if val and (key, val) in seen:
                repo.out.add("FAIL", c, rel, f"{key} is the same as in {seen[(key, val)]}")
            seen[(key, val)] = rel
        for sec, labels in p.get("labels", {}).items():
            body = section(text, "## " + sec) or ""
            for lab in labels:
                if lab not in body:
                    repo.out.add("FAIL", c, rel, f"section {sec!r} lacks {lab!r}")
        keys = table_keys(text, p["checks_after"])
        if keys != p["checks"]:
            repo.out.add("FAIL", c, rel, f"check table after {p['checks_after']!r} has {keys}, expected {p['checks']}")
        start = text.find(p["checks_after"])
        for ln in (lines_of(text[start:])[3:] if start >= 0 else []):
            if not ln.startswith("|"):
                break
            row = cells(ln)
            if len(row) > 2 and row[1].strip("`") == "none" and row[2] != "never":
                repo.out.add("FAIL", c, rel, f"check {row[0]} has command none but runs when {row[2]!r}; expected 'never'")
        agents_body = section(text, "## Agents") or ""
        rows = [cells(ln) for ln in lines_of(agents_body) if ln.lstrip().startswith("|")][2:]
        if [r[0] for r in rows] != p["agent_roles"]:
            repo.out.add("FAIL", c, rel, f"Agents roles {[r[0] for r in rows]} != {p['agent_roles']}")
        for r in rows:
            name = r[1].strip("`") if len(r) > 1 else ""
            if name != "none" and name not in agent_names:
                repo.out.add("FAIL", c, rel, f"Agents names {name!r}, which isn't in agents/")
        native = section(text, "## Native interop") or ""
        plat_lines = re.findall(r"^- \*\*Platforms:\*\*(.*)$", native, re.M)
        tag_lines = re.findall(r"^- \*\*Platform tags:\*\*([^.\n]*)", section(text, "## Spec notation") or "", re.M)
        if len(plat_lines) != 1 or len(tag_lines) != 1:
            repo.out.add("FAIL", c, rel, f"needs exactly one 'Platforms' line in Native interop ({len(plat_lines)}) and one 'Platform tags' line in Spec notation ({len(tag_lines)})")
        # Platform ids are the backticked words without a slash; folders like `ios/` are skipped.
        ids = lambda s: set(re.findall(r"`([a-z0-9_-]+)`", s)) - {"none"}
        plats[rel] = ids(plat_lines[0]) if plat_lines else set()
        tags = ids(tag_lines[0]) if tag_lines else set()
        if tags != plats[rel]:
            repo.out.add("FAIL", c, rel, f"Spec notation's platform tags {sorted(tags)} != Native interop's platforms {sorted(plats[rel])}")
        claim = re.search(r"^- \*\*Native adapter for:\*\* `([a-z0-9_-]+)`", native, re.M)
        if claim and claim.group(1) != "none":
            pid = claim.group(1)
            if pid in claimed:
                repo.out.add("FAIL", c, rel, f"Native adapter for {pid!r}, which {claimed[pid]} claims too")
            if pid not in plats[rel]:
                repo.out.add("FAIL", c, rel, f"Native adapter for {pid!r}, which its own Platforms line doesn't list")
            claimed[pid] = rel
        elif not claim:
            repo.out.add("FAIL", c, rel, "Native interop's 'Native adapter for' needs a backticked platform id or `none`")
        std = (section(text, "## Standards") or "").strip()
        if not std.startswith("none") and not os.path.isfile(os.path.join(base, "standards.md")):
            repo.out.add("FAIL", c, rel, "Standards names a file, but the adapter folder has no standards.md")
        tmpl = section(text, "## Templates") or ""
        sets = [t.rstrip("/") for t in re.findall(r"`(templates/[\w.-]+/)`", tmpl)]
        listed = set(re.findall(r"^- `([\w.-]+)` — ", tmpl, re.M))
        shipped = set()
        for s in sets:
            d = os.path.join(base, s)
            if not os.path.isdir(d):
                repo.out.add("FAIL", c, rel, f"template set {s}/ doesn't exist")
                continue
            shipped |= {f for f in os.listdir(d) if not f.startswith(".")}
        for f in sorted(listed - shipped):
            repo.out.add("FAIL", c, rel, f"lists template {f}, which no template set holds")
        for f in sorted(shipped - listed):
            repo.out.add("FAIL", c, rel, f"template {f} ships but Templates doesn't list it")
        for doc in (rel, os.path.relpath(os.path.join(base, "standards.md"), repo.root)):
            body = repo.read(doc, c) if os.path.isfile(os.path.join(repo.root, doc)) else ""
            for m in re.finditer(r"`(templates/[\w./-]+)`", body or ""):
                if not glob.glob(os.path.join(base, m.group(1))):
                    repo.out.add("FAIL", c, f"{doc}:{lineno(body, m.start())}", f"refers to {m.group(1)}, which doesn't exist")
    for pid, rel in sorted(claimed.items()):
        if not any(pid in ids_ for other, ids_ in plats.items() if other != rel):
            repo.out.add("FAIL", c, rel, f"Native adapter for {pid!r}, which no other adapter lists as a platform")
    for rel in p.get("citing", []):
        text = repo.read(rel, c) or ""
        for m in re.finditer(r"adapter's (?:[^\"()\n]{1,60}\()?\"([^\"]+)\"", text):
            if m.group(1) not in p["sections"]:
                repo.out.add("FAIL", c, f"{rel}:{lineno(text, m.start())}", f"cites the adapter's {m.group(1)!r}, which isn't an adapter section")


def check_counts(repo, anchors, facts):
    c = "counts"
    repo.out.start(c)
    intake = anchors["intake"]
    text = repo.read(intake["file"], c) or ""
    start = text.find(intake["after"])
    block = re.search(r"```\n(.*?)```", text[start:], re.S) if start >= 0 else None
    names = [n.strip() for n in re.findall(r"^\d+\. ([A-Z][A-Z &/]*?)(?: \(.*\))?$", block.group(1), re.M)] if block else []
    facts["intake_sections"], facts["intake_names"] = len(names), names
    if not names:
        repo.out.add("FAIL", c, intake["file"], "Intake Sheet sections not found")
    nums = [int(n) for n in re.findall(r"^## (\d+)\. ", repo.read(anchors["spec_template"], c) or "", re.M)]
    facts["spec_sections"] = len(nums)
    if nums != list(range(1, len(nums) + 1)):
        repo.out.add("FAIL", c, anchors["spec_template"], f"template sections not numbered 1..N: {nums}")
    words = {k: NUMBER_WORDS[v] if isinstance(v, int) and v < len(NUMBER_WORDS) else v for k, v in facts.items()}
    for claim in anchors.get("counts", []):
        try:
            want = claim["text"].format(**words)
        except (KeyError, IndexError, ValueError) as e:
            raise ConfigError(f"anchors.json counts: bad placeholder in {claim['text']!r}: {e}")
        text = repo.read(claim["file"], c)
        if text is not None and want not in text:
            repo.out.add("FAIL", c, claim["file"], f"count claim not found: {want!r}")


def check_intake_lists(repo, anchors, facts):
    c = "intake-sheet"
    repo.out.start(c)
    heads = [set(n.lower().split()) for n in facts.get("intake_names", [])]
    for rel in anchors["intake"]["lists"]:
        text = repo.read(rel, c)
        if text is None:
            continue
        m = re.search(r"Intake Sheet\**\s*\(([^)]+)\)", text)
        if not m:
            repo.out.add("FAIL", c, rel, "no '(…)' section list after 'Intake Sheet'")
            continue
        items = [i.strip() for i in m.group(1).split(",")]
        where = f"{rel}:{lineno(text, m.start())}"
        if len(items) != len(heads):
            repo.out.add("FAIL", c, where, f"{len(items)} sections listed, feature-intake defines {len(heads)}")
            continue
        for i, (item, head) in enumerate(zip(items, heads), 1):
            if not set(item.lower().split()) <= head:
                repo.out.add("FAIL", c, where, f"section {i} {item!r} doesn't match {facts['intake_names'][i - 1]!r}")


def check_user_config(repo, anchors):
    c = "plugin-options"
    repo.out.start(c)
    manifest = repo.json(repo.p(".claude-plugin", "plugin.json"), c)
    if not isinstance(manifest, dict):
        return
    declared = manifest.get("userConfig", {})
    spec = anchors.get("user_config", {})
    refs = {}
    for rel in walk_files(repo.root):
        if not rel.startswith(repo.p("skills", "")) or os.path.splitext(rel)[1] not in TEXT_EXT:
            continue
        text = repo.read(rel, c) or ""
        lines = lines_of(text)
        for m in re.finditer(r"\$\{user_config\.([A-Za-z0-9_]+)\}", text):
            n = lineno(text, m.start())
            refs.setdefault(m.group(1), []).append((rel, n, lines[n - 1].strip()))
    for key in sorted(set(refs) - set(declared)):
        for rel, n, _ in refs[key]:
            repo.out.add("FAIL", c, f"{rel}:{n}", f"option {key!r} not declared in plugin.json userConfig")
    for key in sorted(set(declared) - set(spec)):
        repo.out.add("FAIL", c, "maintenance/anchors.json", f"declared option {key!r} has no user_config anchor")
    for key, want in sorted(spec.items()):
        if key not in declared:
            repo.out.add("FAIL", c, repo.p(".claude-plugin", "plugin.json"), f"option {key!r} expected but not declared")
            continue
        default = str(declared[key].get("default", ""))
        got = refs.get(key, [])
        files = {r for r, _, _ in got}
        for rel in sorted(set(want["files"]) - files):
            repo.out.add("FAIL", c, rel, f"no reference to option {key!r} (expected in this file)")
        for rel in sorted(files - set(want["files"])):
            repo.out.add("FAIL", c, rel, f"unexpected reference to option {key!r}")
        for rel in sorted(files):
            if sum(1 for r, _, _ in got if r == rel) > 1:
                repo.out.add("WARN", c, rel, f"option {key!r} referenced more than once")
        if len({line for _, _, line in got}) > 1:
            for rel, n, _ in got:
                repo.out.add("FAIL", c, f"{rel}:{n}", f"{key} line differs from its other copies")
        fallback = want["fallback"].format(default=default)
        for rel, n, line in got:
            if fallback not in line:
                repo.out.add("FAIL", c, f"{rel}:{n}", f"fallback missing or stale; expected {fallback!r}")
            for opt in declared[key].get("options", []):
                if f"`{opt}`" not in line:
                    repo.out.add("FAIL", c, f"{rel}:{n}", f"option value `{opt}` from plugin.json not listed")
        for r in want.get("restated", []):
            text = repo.read(r["file"], c)
            phrase = r["text"].format(default=default)
            if text is not None and phrase not in text:
                repo.out.add("FAIL", c, r["file"], f"default of {key!r} not restated as {phrase!r}")


def check_substitutions(repo, anchors):
    c = "substitutions"
    repo.out.start(c)
    manifest = repo.json(repo.p(".claude-plugin", "plugin.json"), c)
    declared = set(manifest.get("userConfig", {})) if isinstance(manifest, dict) else set()
    allowed = set(anchors.get("allowed_substitutions", ["CLAUDE_SKILL_DIR"]))
    for name in repo.skill_dirs():
        rel = repo.p("skills", name, "SKILL.md")
        text = repo.read(rel, c) or ""
        for m in re.finditer(r"\$\{([^}]*)\}", text):
            var = m.group(1)
            if not (var in allowed or (var.startswith("user_config.") and var.split(".", 1)[1] in declared)):
                repo.out.add("FAIL", c, f"{rel}:{lineno(text, m.start())}",
                             f"'${{{var}}}' would be substituted or is shell syntax in prose")
        for m in re.finditer(r"\$SKILL_DIR\b", text):
            repo.out.add("FAIL", c, f"{rel}:{lineno(text, m.start())}", "$SKILL_DIR — use the CLAUDE_SKILL_DIR substitution")
        for m in re.finditer(r"(?<!\\)\$(ARGUMENTS\b|\d)", text):
            repo.out.add("WARN", c, f"{rel}:{lineno(text, m.start())}",
                         f"'${m.group(1)}' is an argument placeholder and expands when args are passed")
    for p in sorted(glob.glob(repo.pabs("skills", "*", "**", "*.md"), recursive=True)):
        rel = os.path.relpath(p, repo.root)
        text = repo.read(rel, c) or ""
        if os.path.basename(p) != "SKILL.md" and "${" in text:
            repo.out.add("FAIL", c, f"{rel}:{lineno(text, text.find('${'))}",
                         "'${' in a supporting file, which gets no substitution; pass the value from SKILL.md")


def check_skill_refs(repo):
    c = "skill-file-refs"
    repo.out.start(c)
    for name in repo.skill_dirs():
        base = repo.pabs("skills", name)
        rel = repo.p("skills", name, "SKILL.md")
        text = repo.read(rel, c) or ""
        refs = [m.group(1) for m in re.finditer(r"\$\{CLAUDE_SKILL_DIR\}/([\w./*-]+)", text)]
        if os.path.isdir(os.path.join(base, "templates")):
            refs += [m.group(1) for m in re.finditer(r"`(templates/[\w./*-]+)`", text)]
        if os.path.isdir(os.path.join(base, "scripts")):
            for m in re.finditer(r"`([\w-]+\.sh)`", text):
                if not (glob.glob(os.path.join(base, "scripts", m.group(1))) or glob.glob(os.path.join(base, "templates", m.group(1)))):
                    repo.out.add("FAIL", c, f"{rel}:{lineno(text, m.start())}", f"names {m.group(1)}, which this skill doesn't ship")
        for ref in sorted(set(refs)):
            if not glob.glob(os.path.join(base, ref.rstrip("."))):
                repo.out.add("FAIL", c, rel, f"refers to {ref}, which doesn't exist in the skill folder")
    # `<skill>`'s "<Heading>" or `<file>.md`'s "<Heading>": the cited heading must exist there.
    sources = [(repo.p("skills", name, os.path.basename(path)), repo.pabs("skills", name))
               for name in repo.skill_dirs() for path in sorted(glob.glob(os.path.join(repo.pabs("skills", name), "*.md")))]
    sources += [(repo.p(doc), None) for doc in ("README.md", "MIGRATION.md") if os.path.isfile(repo.pabs(doc))]
    for src, base in sources:
        body = repo.read(src, c) or ""
        for m in re.finditer(r"`([a-z0-9-]+(?:\.md)?)`'s \"([^\"]+)\"", body):
            target, head = m.group(1), m.group(2)
            if target.endswith(".md"):
                hits = [os.path.join(base, target)] if base and os.path.isfile(os.path.join(base, target)) else sorted(glob.glob(repo.pabs("skills", "*", target)))
            elif os.path.isfile(repo.pabs("skills", target, "SKILL.md")):
                hits = [repo.pabs("skills", target, "SKILL.md")]
            else:
                continue
            if not hits or not any(re.search(rf"^#{{1,6}} {re.escape(head)}(?=\s|$)", open(h, encoding="utf-8").read(), re.M) for h in hits):
                repo.out.add("FAIL", c, f"{src}:{lineno(body, m.start())}", f"cites {target}'s {head!r}, which has no such heading")


def check_manifests(repo, anchors):
    c = "manifests"
    repo.out.start(c)
    plugin = repo.json(repo.p(".claude-plugin", "plugin.json"), c)
    market = repo.json(".claude-plugin/marketplace.json", c)
    if not isinstance(plugin, dict) or not isinstance(market, dict):
        return
    for k in anchors.get("plugin_forbidden_keys", []):
        if k in plugin:
            repo.out.add("FAIL", c, repo.p(".claude-plugin", "plugin.json"), f"declares {k!r}; components are auto-discovered from their folders")
    entries = [p for p in market.get("plugins", []) if isinstance(p, dict) and p.get("name") == plugin.get("name")]
    if not entries:
        repo.out.add("FAIL", c, ".claude-plugin/marketplace.json", f"lists no plugin named {plugin.get('name')!r}")
    for e in entries:
        if e.get("description") != plugin.get("description"):
            repo.out.add("FAIL", c, ".claude-plugin/marketplace.json", "plugin description differs from plugin.json")
        if e.get("source") != "./" + repo.plugin:
            repo.out.add("FAIL", c, ".claude-plugin/marketplace.json", f"plugin source {e.get('source')!r} isn't './{repo.plugin}'")
    if os.path.basename(repo.plugin) != plugin.get("name"):
        repo.out.add("FAIL", c, repo.p(".claude-plugin", "plugin.json"), f"plugin {plugin.get('name')!r} lives in {repo.plugin}/; folder and name must match")
    # Every entry is a folder of its own under plugins/, so none can ship the repo root again.
    parent = os.path.dirname(repo.plugin)
    listed = set()
    for e in market.get("plugins", []):
        name = e.get("name") if isinstance(e, dict) else None
        listed.add(name)
        if not isinstance(name, str) or e.get("source") != f"./{parent}/{name}":
            repo.out.add("FAIL", c, ".claude-plugin/marketplace.json", f"entry {name!r} has source {e.get('source') if isinstance(e, dict) else e!r}; expected './{parent}/<name>'")
        elif (repo.json(f"{parent}/{name}/.claude-plugin/plugin.json", c) or {}).get("name") != name:
            repo.out.add("FAIL", c, f"{parent}/{name}/.claude-plugin/plugin.json", f"doesn't declare plugin {name!r}")
    for n in sorted(set(os.listdir(os.path.join(repo.root, parent))) - listed - {".DS_Store"}):
        repo.out.add("FAIL", c, f"{parent}/{n}", "not a plugin the marketplace lists (a stray write?)")
    ident = f"{plugin.get('name')}@{market.get('name')}"
    siblings = {f"{s['plugin']}@{s['marketplace']}" for s in anchors.get("siblings", {}).get("plugins", [])}
    legacy = anchors.get("legacy_install") or {}
    readmes = {rel: repo.read(rel, c) or "" for rel in ("README.md", repo.p("README.md"), repo.p("MIGRATION.md")) if os.path.isfile(os.path.join(repo.root, rel))}
    for cmd in ("/plugin install", "claude plugin configure"):
        found = False
        for rel, readme in readmes.items():
            for i in re.findall(re.escape(cmd) + r" ([\w.-]+@[\w.-]+)", readme):
                if cmd == "/plugin install" and i in siblings:
                    continue  # checked by check_siblings
                if cmd == "/plugin install" and i == legacy.get("ident") and rel in legacy.get("files", []):
                    continue  # v0.2.0, pinned in the migration guide
                found = True
                if i != ident:
                    repo.out.add("FAIL", c, rel, f"`{cmd} {i}` doesn't match the manifests' {ident}")
        if not found:
            repo.out.add("FAIL", c, "README.md", f"no `{cmd} {ident}` line in the READMEs or the migration guide")


def check_mentions(repo, anchors):
    c = "mentions"
    repo.out.start(c)
    for rule in anchors.get("mentions", []):
        word = rule["word"].lower()
        globs = rule["glob"] if isinstance(rule["glob"], list) else [rule["glob"]]
        exclude = tuple(rule.get("exclude", []))
        paths = set()
        for g in globs:
            found = glob.glob(os.path.join(repo.root, g), recursive=True)
            if not found:
                repo.out.add("FAIL", c, g, f"{rule.get('id', rule['word'])}: glob matches no file")
            paths.update(found)
        for p in sorted(paths):
            if not os.path.isfile(p):
                continue
            rel = os.path.relpath(p, repo.root)
            if rel.startswith(exclude):
                continue
            text = repo.read(rel, c) or ""
            for n, line in enumerate(lines_of(text), 1):
                if word not in line.lower():
                    continue
                rest = line
                for a in rule["allowed"]:
                    rest = rest.replace(a, "")
                if word in rest.lower():
                    repo.out.add("FAIL", c, f"{rel}:{n}", f"{rule.get('id', rule['word'])}: {rule['word']!r} outside the allowed phrases")


def check_release(repo, anchors):
    c = "release"
    repo.out.start(c)
    rel = anchors.get("release")
    if not rel:
        repo.out.add("FAIL", c, "maintenance/anchors.json", "no `release` block, so nothing checks the version, the alpha notices or TESTING.md")
        return
    prel = repo.p(".claude-plugin", "plugin.json")
    plugin = repo.json(prel, c) or {}
    market = repo.json(".claude-plugin/marketplace.json", c) or {}
    version = str(plugin.get("version", ""))
    if not re.fullmatch(r"\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?", version):
        repo.out.add("FAIL", c, prel, f"version {version!r} isn't MAJOR.MINOR.PATCH[-alpha.N]")
    alpha = "-alpha." in version
    base = version.split("-", 1)[0]
    descs = [(prel, plugin.get("description", ""))] + [(".claude-plugin/marketplace.json", e.get("description", "")) for e in market.get("plugins", []) if isinstance(e, dict)]
    for where, d in descs:
        if str(d).startswith(rel["alpha_prefix"]) != alpha:
            repo.out.add("FAIL", c, where, f"description {'must' if alpha else 'must not'} start with {rel['alpha_prefix']!r} at version {version}")
    for f, phrase in rel["alpha_notice"].items():
        text = repo.read(f, c) or ""
        if alpha and phrase.replace("{base}", base) not in text:
            repo.out.add("FAIL", c, f, f"no alpha notice ({phrase.replace('{base}', base)!r}) at version {version}")
        if not alpha and phrase.split("{base}")[0] in text:
            repo.out.add("FAIL", c, f, f"a leftover alpha notice ({phrase.split('{base}')[0]!r}) at version {version}")
    url = rel.get("repo_url")
    for doc in [repo.p("README.md")] + list(anchors.get("path_docs", [])):
        for m in re.finditer(re.escape(url) + r"([^)\s#>`]+)", repo.read(doc, c) or "") if url else []:
            if not os.path.exists(os.path.join(repo.root, m.group(1))):
                repo.out.add("FAIL", c, doc, f"links {m.group(0)}, but the repo has no {m.group(1)}")
    text = repo.read(rel["testing"], c)
    if text is None:
        return
    cases = section(text, "## Cases") or ""
    seen = set()
    evidence = re.compile(rel["evidence"])
    for ln in lines_of(cases):
        if not ln.startswith("|") or re.match(r"^\|\s*(ID\s*\||-)", ln):
            continue
        m = re.match(r"^\| ([A-Z]\d+) \|", ln)
        where = f"{rel['testing']}:{m.group(1) if m else lineno(cases, cases.find(ln))}"
        cl = cells(ln)
        if not m or len(cl) != 5:
            repo.out.add("FAIL", c, where, "not a case row: | <ID like B7> | Case | Pass when | Kind | Status |")
            continue
        if m.group(1) in seen:
            repo.out.add("FAIL", c, where, "duplicate case id")
        seen.add(m.group(1))
        if cl[3] not in rel["kinds"]:
            repo.out.add("FAIL", c, where, f"Kind {cl[3]!r} isn't one of {rel['kinds']}")
        status = re.split(r" — | \(", cl[4], maxsplit=1)[0]
        if status not in rel["statuses"]:
            repo.out.add("FAIL", c, where, f"Status {cl[4][:40]!r} doesn't start with one of {rel['statuses']}")
        elif status in ("partly", "passed", "failed", "fixed"):
            ev = evidence.match(cl[4])
            day = None
            if ev:
                try:
                    day = datetime.date.fromisoformat(ev.group(2))
                except ValueError:
                    pass
            if not ev or day is None or day > datetime.date.today():
                repo.out.add("FAIL", c, where, f"{status} needs its evidence: ' — <date>, <version>, <where>[, <cost>]', a real date no later than today")
    if not seen:
        repo.out.add("FAIL", c, rel["testing"], "no case rows under '## Cases'")
    leaving = section(text, rel["leaving_heading"])
    if alpha and not (leaving or "").strip():
        repo.out.add("FAIL", c, rel["testing"], f"no or an empty {rel['leaving_heading']!r} section while the plugin is in alpha")
    for cid in re.findall(r"\b([A-Z]\d+)\b", leaving or ""):
        if cid not in seen:
            repo.out.add("FAIL", c, rel["testing"], f"{rel['leaving_heading']!r} names {cid}, which isn't a case")


def check_siblings(repo, anchors):
    c = "siblings"
    sib = anchors.get("siblings")
    if not sib:
        return
    repo.out.start(c)
    plugins = sib["plugins"]
    readme_rel = repo.p("README.md")
    readme = repo.read(readme_rel, c) or ""
    related = section(readme, "## Related plugins")
    if related is None:
        repo.out.add("FAIL", c, readme_rel, "no `## Related plugins` section")
        related = ""
    for rel in walk_files(repo.root):
        if rel.startswith(".claude/settings"):  # local settings may name an installed sibling
            continue
        text = repo.read(rel, c) if rel.endswith((".md", ".json", ".py", ".sh", ".txt", ".yaml", ".yml", ".toml", ".html", ".js", ".ts", ".dart", ".swift", ".kt")) else None
        if not text:
            continue
        low = text.lower()
        for s in plugins:
            if s["plugin"].lower() in low and rel not in sib["allowed_files"] and rel not in s["mentioned_in"]:
                repo.out.add("FAIL", c, rel, f"names {s['plugin']!r}, which only its mention files and {', '.join(sib['allowed_files'])} may")
        if rel.endswith(".md") and rel.startswith((repo.p("skills") + "/", repo.p("agents") + "/")):
            desc = (frontmatter(text) or {}).get("description", "")
            for s in plugins:
                if s["plugin"].lower() in desc.lower() or s["skill"].lower() in desc.lower():
                    repo.out.add("FAIL", c, rel, f"description names {s['skill']!r}; mentions stay in the body")
    related_lines = {ln.strip() for ln in lines_of(related)}
    installs = {f"{s['plugin']}@{s['marketplace']}" for s in plugins}
    for i in re.findall(r"^/plugin install (\S+)\s*$", related, re.M):
        if i not in installs:
            repo.out.add("FAIL", c, readme_rel, f"'Related plugins' installs {i!r}, which isn't a sibling's <plugin>@<marketplace>")
    root_readme = repo.read("README.md", c) or ""
    if '"Related plugins"' not in root_readme:
        repo.out.add("FAIL", c, "README.md", "no pointer to the plugin README's \"Related plugins\"")
    for s in plugins:
        for rel in s["mentioned_in"]:
            text = repo.read(rel, c) or ""
            if f"a `{s['skill']}` skill is listed" not in text:
                repo.out.add("FAIL", c, rel, f"no offer conditioned on the skill: 'a `{s['skill']}` skill is listed'")
            hint = f"the `{s['plugin']}` plugin (`/plugin marketplace add {s['repo']}`, then `/plugin install {s['plugin']}@{s['marketplace']}`)"
            if not s.get("listed_only") and hint not in text:
                repo.out.add("FAIL", c, rel, f"no not-listed hint: {hint!r}")
            if s.get("listed_only") and "/plugin marketplace add" in text:
                repo.out.add("FAIL", c, rel, f"{s['plugin']} is offered only when listed, but the file has an install hint")
        if not any(ln.startswith(f"| `{s['plugin']}` | `{s['repo']}` |") for ln in lines_of(related)):
            repo.out.add("FAIL", c, readme_rel, f"'Related plugins' has no row for {s['plugin']} from {s['repo']}")
        if f"/plugin install {s['plugin']}@{s['marketplace']}" not in related_lines:
            repo.out.add("FAIL", c, readme_rel, f"'Related plugins' has no `/plugin install {s['plugin']}@{s['marketplace']}` line")
        if f"/plugin marketplace add {s['repo']}" not in related_lines:
            repo.out.add("FAIL", c, readme_rel, f"'Related plugins' has no `/plugin marketplace add {s['repo']}` line")
        if f"github.com/{s['repo']})" not in root_readme:
            repo.out.add("FAIL", c, "README.md", f"no link to {s['repo']}")


def pinned_lines(text, heading=None, min_len=12):
    """Lines an exact pin list must equal, in order: stripped, at least min_len long, not a table rule, a whole line only once in the file."""
    body = text if heading is None else heading + "\n" + (section(text, heading) or "")
    whole = {}
    for ln in lines_of(text):
        whole[ln.strip()] = whole.get(ln.strip(), 0) + 1
    # A line that is also a substring of a longer line still counts: whole-line matches only.
    return [s for s in (ln.strip() for ln in lines_of(body))
            if len(s) >= min_len and not s.startswith("|---") and whole.get(s) == 1]


def repeated_lines(text, heading=None, min_len=12):
    """Counts, in the pinned text, of the lines pinned_lines leaves out for repeating in the file."""
    body = text if heading is None else heading + "\n" + (section(text, heading) or "")
    whole, counts = {}, {}
    for ln in lines_of(text):
        whole[ln.strip()] = whole.get(ln.strip(), 0) + 1
    for s in (ln.strip() for ln in lines_of(body)):
        if len(s) >= min_len and not s.startswith("|---") and whole.get(s, 0) > 1:
            counts[s] = counts.get(s, 0) + 1
    return counts


def print_pins(root, rel, heading, min_len):
    """Print an exact check for anchors.json, generated from the file so no pin is retyped."""
    path = os.path.join(root, rel)
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as e:
        print(f"cannot read {rel}: {e}", file=sys.stderr)
        return 4
    if heading is not None and section(text, heading) is None:
        print(f"{rel}: no line {heading!r}", file=sys.stderr)
        return 4
    if min_len is None:
        # Default to the existing check's min_len, so regenerating never drops short pins.
        min_len = 12
        try:
            with open(os.path.join(root, "maintenance", "anchors.json"), encoding="utf-8") as fh:
                for contract in json.load(fh).get("contracts", []):
                    for old in contract.get("checks", []):
                        if old.get("file") == rel and old.get("exact") == (heading if heading is not None else True):
                            min_len = old.get("min_len", 12)
        except (OSError, ValueError):
            pass
    chk = {"file": rel, "exact": heading if heading is not None else True}
    if min_len != 12:
        chk["min_len"] = min_len
    reps = repeated_lines(text, heading, min_len)
    if reps:
        chk["repeats"] = reps
    chk["contains"] = pinned_lines(text, heading, min_len)
    print(json.dumps(chk, ensure_ascii=False, indent=2))
    return 0


def check_anchor_contracts(repo, anchors):
    for contract in anchors.get("contracts", []):
        c = "contract:" + contract["id"]
        repo.out.start(c)
        for chk in contract.get("checks", []):
            rel = chk["file"]
            text = repo.read(rel, c)
            if text is None:
                continue
            for s in chk.get("contains", []):
                if s not in text:
                    repo.out.add("FAIL", c, rel, f"missing: {s!r}")
            if chk.get("exact"):
                # Whole-file (or whole-section) pins: no unpinned line, no pin sharing a line, same order.
                want = chk.get("contains", [])
                got = pinned_lines(text, chk["exact"] if isinstance(chk["exact"], str) else None, chk.get("min_len", 12))
                for s in got:
                    if s not in want:
                        repo.out.add("FAIL", c, f"{rel}:{lineno(text, text.find(s))}", f"line not pinned (exact check): {s!r}")
                for s in want:
                    if s in text and s not in got:
                        repo.out.add("FAIL", c, rel, f"pin is no longer a line of its own (exact check): {s[:80]!r}")
                if [s for s in got if s in want] != [s for s in want if s in got]:
                    repo.out.add("FAIL", c, rel, "pinned lines are out of order (exact check)")
                # Lines that repeat can't be pinned by text, so their counts are.
                got_rep = repeated_lines(text, chk["exact"] if isinstance(chk["exact"], str) else None, chk.get("min_len", 12))
                want_rep = chk.get("repeats", {})
                for s in sorted(set(got_rep) | set(want_rep)):
                    if got_rep.get(s, 0) != want_rep.get(s, 0):
                        repo.out.add("FAIL", c, rel, f"repeated line count {got_rep.get(s, 0)}, expected {want_rep.get(s, 0)} (exact check): {s[:80]!r}")
            for s in chk.get("not_contains", []):
                if s in text:
                    repo.out.add("FAIL", c, f"{rel}:{lineno(text, text.find(s))}", f"must not contain: {s!r}")
            stripped = [ln.lstrip() for ln in lines_of(text)]
            for p in chk.get("line_prefixes", []):
                if not any(ln.startswith(p) for ln in stripped):
                    repo.out.add("FAIL", c, rel, f"no line starting with {p!r}")
            for p, subs in chk.get("row_contains", {}).items():
                rows = [ln for ln in stripped if ln.startswith(p)]
                for s in subs:
                    if not any(s in r for r in rows):
                        repo.out.add("FAIL", c, rel, f"row {p!r} lacks {s!r}")
            for before, after in chk.get("order", []):
                a, b = text.find(before), text.find(after)
                if a < 0 or b < 0:
                    repo.out.add("FAIL", c, rel, f"order check: {(before if a < 0 else after)!r} not found")
                elif a > b:
                    repo.out.add("FAIL", c, f"{rel}:{lineno(text, a)}", f"{before!r} must come before {after!r}")
        for grp in contract.get("identical_lines", []):
            variants = set()
            for rel in grp["files"]:
                hits = [ln.strip() for ln in lines_of(repo.read(rel, c) or "") if ln.strip().startswith(grp["prefix"])]
                if not hits:
                    repo.out.add("FAIL", c, rel, f"no line starting with {grp['prefix']!r}")
                variants.update(hits)
            if len(variants) > 1:
                repo.out.add("FAIL", c, ", ".join(grp["files"]), f"lines starting with {grp['prefix']!r} differ")
        for grp in contract.get("identical_rows", []):
            for prefix in grp["rows"]:
                seen = {}
                for rel in grp["files"]:
                    rows = [ln.strip() for ln in lines_of(repo.read(rel, c) or "") if ln.lstrip().startswith(prefix)]
                    if len(rows) != 1:
                        repo.out.add("FAIL", c, rel, f"expected one row starting with {prefix!r}, found {len(rows)}")
                        continue
                    val = cells(rows[0])[: grp.get("cells")] if grp.get("cells") else cells(rows[0])
                    val = " | ".join(val)
                    for s in grp.get("normalize", []):
                        val = val.replace(s, "")
                    seen[rel] = val
                if len(set(seen.values())) > 1:
                    detail = "; ".join(f"{os.path.basename(os.path.dirname(r)) or r}: {v[:60]!r}" for r, v in seen.items())
                    repo.out.add("FAIL", c, ", ".join(seen), f"row {prefix!r} differs — {detail}")
        for grp in contract.get("same_value", []):
            values = {}
            for p in grp:
                m = re.search(p["regex"], repo.read(p["file"], c) or "")
                if not m:
                    repo.out.add("FAIL", c, p["file"], f"pattern not found: {p['regex']!r}")
                else:
                    values[f"{p['file']} /{p['regex']}/"] = m.group(1)
            if len(set(values.values())) > 1:
                repo.out.add("FAIL", c, "-", "values differ: " + "; ".join(f"{k} → {v!r}" for k, v in values.items()))
        for grp in contract.get("same_table_keys", []):
            keys = {}
            for p in grp:
                text = repo.read(p["file"], c)
                if text is None:
                    continue
                k = table_keys(text, p["after"])
                if k is None:
                    repo.out.add("FAIL", c, p["file"], f"no table after {p['after']!r}")
                else:
                    keys[f"{p['file']} after {p['after']!r}"] = k
            if len({tuple(k) for k in keys.values()}) > 1:
                detail = "; ".join(f"{r}: {', '.join(k)}" for r, k in keys.items())
                repo.out.add("FAIL", c, ", ".join(dict.fromkeys(p["file"] for p in grp)), f"table first columns differ — {detail}")


def find_flag_table(skill):
    """Flags in the Inputs table's flag column (the column holding the most flags)."""
    m = re.search(r"^#{2,4} [^\n]*Inputs[^\n]*\n(.*?)(?=^#{1,4} |\Z)", skill, re.M | re.S)
    if not m:
        return None
    rows = [cells(ln) for ln in lines_of(m.group(1)) if ln.lstrip().startswith("|")][2:]
    if not rows:
        return None
    width = max(len(r) for r in rows)
    col = max(range(width), key=lambda i: sum(bool(re.search(FLAG, r[i])) for r in rows if i < len(r)))
    return [f for r in rows if col < len(r) for f in re.findall(rf"(?<![\w-])({FLAG})", r[col])]


def check_build_interface(repo, anchors):
    c = "build-interface"
    repo.out.start(c)
    spec = anchors["build_interface"]
    skill = repo.read(spec["skill"], c)
    if skill is None:
        return
    ignore = set(spec.get("ignore_flags", []))
    want = {frozenset(g.split("|")) for g in spec["flags"]}
    flags = {f for g in want for f in g}
    has = lambda text, f: re.search(rf"(?<![\w-]){re.escape(f)}(?![\w-])", text)
    for g in sorted(want, key=sorted):
        if not any(has(skill, f) for f in g):
            repo.out.add("FAIL", c, spec["skill"], f"build flag {'|'.join(sorted(g))} not documented")
    used = find_flag_table(skill)
    if used is None:
        repo.out.add("FAIL", c, spec["skill"], "no table with build flags under an Inputs heading")
        used = []
    used += [f for ln in lines_of(skill) if "./scripts/build-version.sh" in ln
             for f in re.findall(rf"(?<![\w-])({FLAG})", ln.split("./scripts/build-version.sh", 1)[1])]
    for f in sorted(set(used) - flags - ignore):
        repo.out.add("FAIL", c, spec["skill"], f"documents flag {f} that the build-adapter interface doesn't have")
    for v in spec["platforms"].values():
        if v["key"] not in skill:
            repo.out.add("FAIL", c, spec["skill"], f"manifest key {v['key']} not documented")
    scripts = sorted(glob.glob(os.path.join(repo.root, spec["scripts"])))
    if not scripts:
        repo.out.add("FAIL", c, spec["scripts"], "no build script matches")
    manifests = set()
    for path in scripts:
        rel = os.path.relpath(path, repo.root)
        script = repo.read(rel, c)
        if script is None:
            continue
        groups = {frozenset(g.split("|")) for g in re.findall(rf"^\s*({FLAG}(?:\|{FLAG})*)\)", script, re.M)}
        groups = {g for g in groups if not g & ignore}
        for g in sorted(want - groups, key=sorted):
            repo.out.add("FAIL", c, rel, f"doesn't accept {'|'.join(sorted(g))}")
        for g in sorted(groups - want, key=sorted):
            repo.out.add("FAIL", c, rel, f"accepts {'|'.join(sorted(g))}, which the build-adapter interface doesn't have")
        m = re.search(r'^MANIFEST="\$PROJECT_DIR/([^"]+)"\n(.*?)^\}\s*>\s*"\$MANIFEST"', script, re.M | re.S)
        if not m:
            repo.out.add("FAIL", c, rel, "artifact manifest block not found")
            continue
        manifests.add(m.group(1))
        keys = set(re.findall(r'echo\s+"([A-Z][A-Z0-9_]*)=', m.group(2)))
        for k in spec.get("required_manifest_keys", []):
            if k not in keys:
                repo.out.add("FAIL", c, rel, f"manifest doesn't write {k}")
        adapter_rel = os.path.join(os.path.dirname(rel), "PLATFORM.md")
        build = section(repo.read(adapter_rel, c) or "", "## Build adapter") or ""
        plat = [ln for ln in lines_of(build) if ln.startswith("- **Platforms:**")]
        tmpl = [ln for ln in lines_of(build) if ln.startswith("- **Template:**")]
        if len(plat) != 1 or len(tmpl) != 1:
            repo.out.add("FAIL", c, adapter_rel, "Build adapter needs one '- **Platforms:**' and one '- **Template:**' line")
            continue
        if f"`{os.path.basename(rel)}`" not in tmpl[0]:
            repo.out.add("FAIL", c, adapter_rel, f"Build adapter's Template doesn't name {os.path.basename(rel)}")
        built = 0
        for flag, v in spec["platforms"].items():
            builds = v["line"] in script
            built += builds
            if builds != (v["key"] in keys):
                printed, written = ("prints", "doesn't write") if builds else ("doesn't print", "writes")
                repo.out.add("FAIL", c, rel, f"{printed} {v['line']!r} but {written} {v['key']}")
            var = re.search(r"\$\w+", v["line"])
            want_line = f'echo "{v["key"]}=\\"{var.group(0)}\\""' if var else None
            if builds and want_line and want_line not in m.group(2):
                repo.out.add("FAIL", c, rel, f"manifest doesn't write {want_line!r}, the path its {v['line']!r} line prints")
            if builds and f"`{flag}`" not in plat[0]:
                repo.out.add("FAIL", c, adapter_rel, f"Build adapter's Platforms doesn't name {flag}, which the script builds")
            if not builds and f"`{flag}` doesn't apply" not in plat[0]:
                repo.out.add("FAIL", c, adapter_rel, f"Build adapter's Platforms doesn't say `{flag}` doesn't apply")
        if not built:
            repo.out.add("FAIL", c, rel, "builds no platform: prints none of the interface's artifact lines")
    for adapter in sorted(glob.glob(os.path.join(repo.root, os.path.dirname(spec["scripts"]), "PLATFORM.md"))):
        arel = os.path.relpath(adapter, repo.root)
        if os.path.join(os.path.dirname(adapter), "build-version.sh") in scripts:
            continue
        tmpl = [ln for ln in lines_of(section(repo.read(arel, c) or "", "## Build adapter") or "") if ln.startswith("- **Template:**")]
        if len(tmpl) != 1 or "`none`" not in tmpl[0]:
            repo.out.add("FAIL", c, arel, "no build-version.sh beside it, so Build adapter's Template must say `none`")
    for path in sorted(manifests):
        if path not in skill:
            repo.out.add("FAIL", c, spec["skill"], f"manifest path {path!r} not documented")
    if len(manifests) > 1:
        repo.out.add("FAIL", c, spec["scripts"], f"build scripts write different manifests: {sorted(manifests)}")


def header_and_body(text):
    lines = lines_of(text)
    i = 1 if lines and lines[0].startswith("#!") else 0
    head = []
    while i < len(lines) and lines[i].startswith("#"):
        head.append(lines[i])
        i += 1
    body = [ln for ln in lines[i:] if not ln.lstrip().startswith("#")]
    return "\n".join(head), "\n".join(body)


KEY_PRINT = re.compile(r"""(?:\becho|\bprintf|\bprint\(f?)\s*["']([A-Z][A-Z0-9_]*)(?:\{[^}]*\})?=""")


def printed_keys(body):
    keys = set(KEY_PRINT.findall(body))
    for m in re.finditer(r"\bcat\s*<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)^\s*\1\s*$", body, re.M | re.S):
        keys |= set(re.findall(r"^\s*([A-Z][A-Z0-9_]*)=", m.group(2), re.M))
    return keys


def skill_refs(skill, script):
    """Exit codes and KEY names the SKILL.md uses in the step that invokes `script`."""
    segs, cur = [], None
    for ln in lines_of(skill):
        inv = re.search(r"^\s*bash\s.*scripts/([A-Za-z0-9_]+\.sh)", ln)
        if inv:
            cur = inv.group(1)
        elif re.match(r"^(#{1,4} |\d+\. )", ln):
            cur = None
        if cur == script:
            segs.append(ln)
    text, codes = "\n".join(segs), set()
    for m in re.finditer(r"\bexit(?:s|ed)?\s+(\d+)\b", text, re.I):
        found, pos = {int(m.group(1))}, m.end()
        while True:
            more = re.match(r"\s*(?:\([^)]*\))?\s*(?:or|and|,|/)\s*(\d+)\b", text[pos:])
            if not more:
                break
            found.add(int(more.group(1)))
            pos += more.end()
        # Only branch statements ("exit 2 (…) → …", "exit 4 = …", "Exit 4 ⇒ …") count; prose mentions don't.
        if re.match(r"\s*(?:\([^)]*\))?\s*(→|⇒|->|=|:)", text[pos:]):
            codes |= found
    # Backticked names with `=` or `_` only, so words like `VERSION` alone aren't taken for keys.
    keys = {m.group(1) for m in re.finditer(r"`([A-Z][A-Z0-9_]{2,})(=[^`]*|<[a-z]+>)?`", text)
            if m.group(2) or "_" in m.group(1)}
    return codes, keys, bool(segs)


def check_deploy_scripts(repo, anchors):
    c = "deploy-scripts"
    repo.out.start(c)
    spec = anchors["deploy_scripts"]
    skill = repo.read(spec["skill"], c)
    if skill is None:
        return
    printed, read = set(), set()
    for path in sorted(glob.glob(os.path.join(repo.root, spec["dir"], "*.sh"))):
        name, rel = os.path.basename(path), os.path.relpath(path, repo.root)
        text = repo.read(rel, c) or ""
        head, body = header_and_body(text)
        for n, ln in enumerate(lines_of(text), 1):
            if ln.lstrip().startswith("#"):
                continue
            if (re.match(r"^\s*read\b", ln) and "<" not in ln) or re.search(r"\bselect\s+\w+\s+in\b|/dev/tty", ln):
                repo.out.add("FAIL", c, f"{rel}:{n}", "interactive input; deploy scripts must stay non-interactive")
        ex = head.find("Exit codes:")
        if ex < 0:
            repo.out.add("FAIL", c, rel, "header declares no 'Exit codes:'")
            continue
        declared = {int(n) for n in re.findall(r"(?:^|[;:]|#)\s*(\d+)\s+[A-Za-z(]", head[ex + len("Exit codes:"):], re.M)}
        used = {int(n) for n in re.findall(r"\bexit\s+(\d+)\b", body)} | {int(n) for n in re.findall(r"sys\.exit\((\d+)\)", body)}
        for n in sorted(used - declared - {0}):
            repo.out.add("FAIL", c, rel, f"exits {n} but the header doesn't declare it")
        for n in sorted(declared - used - {0, 1}):
            repo.out.add("WARN", c, rel, f"header declares exit {n} that the body never uses")
        head_keys = set(re.findall(r"\b([A-Z][A-Z0-9_]*)(?:<[a-z]+>)?=", head)) - {"KEY"}
        body_keys = printed_keys(body)
        for k in sorted(body_keys - head_keys):
            repo.out.add("FAIL", c, rel, f"prints {k}= but the header doesn't declare it")
        for k in sorted(head_keys - body_keys):
            repo.out.add("FAIL", c, rel, f"header declares {k}= but the body never prints it")
        refs, skill_keys, invoked = skill_refs(skill, name)
        if not invoked:
            repo.out.add("FAIL", c, spec["skill"], f"{name} is never invoked")
            continue
        for ln in lines_of(skill):
            if re.search(rf"^\s*bash\s.*scripts/{re.escape(name)}", ln):
                for arg in spec.get("required_args", {}).get(name, []):
                    if not re.search(rf"(?<![\w-]){re.escape(arg)}(?![\w-])", ln):
                        repo.out.add("FAIL", c, spec["skill"], f"invokes {name} without {arg}")
        for k in sorted(body_keys):
            if k not in skill:
                repo.out.add("INFO", c, spec["skill"], f"{name} prints {k}= that the skill doesn't use")
        printed |= body_keys
        read |= skill_keys
        for n in sorted(refs - declared):
            repo.out.add("FAIL", c, spec["skill"], f"branches on exit {n} of {name}, which the script doesn't declare")
        for n in sorted(declared - refs - {0}):
            repo.out.add("INFO", c, spec["skill"], f"{name} exit {n} handled only generically")
    # Later steps reuse earlier output, so a key read anywhere may come from any deploy script.
    for k in sorted(read):
        if not any(k == b or (b.endswith("_") and k.startswith(b)) for b in printed):
            repo.out.add("FAIL", c, spec["skill"], f"reads {k}, which no deploy script prints")


def check_spec_checker(repo, anchors):
    """The spec checker's header against its body, its callers against its interface, and the template against it."""
    c = "spec-checker"
    repo.out.start(c)
    spec = anchors["spec_checker"]
    text = repo.read(spec["script"], c)
    if text is None:
        return
    head, body = header_and_body(text)
    ex = head.find("Exit codes:")
    if ex < 0:
        repo.out.add("FAIL", c, spec["script"], "header declares no 'Exit codes:'")
        return
    declared = {int(n) for n in re.findall(r"(?:^|[;:]|#)\s*(\d+)\s+[A-Za-z(]", head[ex + len("Exit codes:"):], re.M)}
    used = {int(n) for n in re.findall(r"\bexit\s+(\d+)\b", body)}
    for m in re.finditer(r"\bexit\s*\(\s*\w+\s*\?\s*(\d+)\s*:\s*(\d+)\s*\)", body):
        used |= {int(m.group(1)), int(m.group(2))}
    for n in sorted(used ^ declared):
        repo.out.add("FAIL", c, spec["script"], f"exit {n} is {'used but not declared' if n in used else 'declared but never used'}")
    head_keys = set(re.findall(r"\b([A-Z][A-Z0-9_]*)(?:<[a-z]+>)?=", head)) - {"KEY"}
    body_keys = set(re.findall(r"\bprint\s+\"([A-Z][A-Z0-9_]*)=", body)) | printed_keys(body)
    for k in sorted(head_keys ^ body_keys):
        repo.out.add("FAIL", c, spec["script"], f"{k}= is {'printed but not declared' if k in body_keys else 'declared but never printed'}")
    km = re.search(r"<check> is ([a-z, ]+?) or ([a-z]+)\s*$", head, re.M)
    kinds = set(re.split(r",\s*", km.group(1))) | {km.group(2)} if km else set()
    if not kinds:
        repo.out.add("FAIL", c, spec["script"], "header doesn't list the finding kinds ('<check> is a, b or c')")
    for k in sorted(set(re.findall(r'\bfinding\("(\w+)"', body)) ^ kinds):
        repo.out.add("FAIL", c, spec["script"], f"finding kind {k} is {'declared but never reported' if k in kinds else 'reported but not declared'}")
    um = re.search(r"^#\s*Usage:.*$", head, re.M)
    flags = set(re.findall(r"--[a-z][a-z-]*", um.group(0))) if um else set()
    for f in sorted(set(re.findall(r"^\s*(--[a-z][a-z-]*)\)", body, re.M)) ^ flags):
        repo.out.add("FAIL", c, spec["script"], f"flag {f} is {'in the Usage line but not parsed' if f in flags else 'parsed but not in the Usage line'}")
    name = os.path.basename(spec["script"])
    for caller, need in spec["callers"].items():
        t = repo.read(caller, c)
        if t is None:
            continue
        lines = [ln for ln in lines_of(t) if f"scripts/{name}" in ln]
        if not lines:
            repo.out.add("FAIL", c, caller, f"never runs {name}")
            continue
        if "RESULT=" not in t:
            repo.out.add("FAIL", c, caller, "doesn't quote the RESULT= line")
        for f in sorted(set(re.findall(r"(?<![\w-])--[a-z][a-z-]*", "\n".join(lines))) - flags):
            repo.out.add("FAIL", c, caller, f"passes {f}, which {name} doesn't take")
        for f in need.get("flags", []):
            if not any(f in ln for ln in lines):
                repo.out.add("FAIL", c, caller, f"runs {name} without {f}")
        for k in sorted(kinds) if need.get("kinds") else ():
            if f"`{k}`" not in t:
                repo.out.add("FAIL", c, caller, f"doesn't say what a `{k}` finding is")
    # The template's own example must pass: it is what every new spec starts from.
    tpl = repo.read(spec["template"], c) or ""
    fm = re.search(r"^## The output template\n.*?^```markdown\n(.*?)^```\s*$", tpl, re.M | re.S)
    if not fm:
        repo.out.add("FAIL", c, spec["template"], "no ```markdown template under '## The output template'")
        return
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "feature-spec.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(fm.group(1))
        try:
            r = subprocess.run(["bash", os.path.join(repo.root, spec["script"]), p], capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            repo.out.add("FAIL", c, spec["script"], "timed out on the template")
            return
    last = (r.stdout.strip().splitlines() or [""])[-1]
    if r.returncode != 0 or not last.startswith("RESULT=pass"):
        found = [ln[8:] for ln in r.stdout.splitlines() if ln.startswith("FINDING=")][:3]
        repo.out.add("FAIL", c, spec["template"], f"the template fails {name} (exit {r.returncode}): {'; '.join(found) or maintlib.one_line(r.stderr, 160)}")


def strip_fences(text):
    """Text with fenced code blocks blanked out, line count unchanged (examples there name target-project files)."""
    return re.sub(r"^```.*?^```[^\n]*$", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.M | re.S)


# Inline links (a title allowed) and reference-style link definitions.
MD_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'(][^)]*)?\)|^ {0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?", re.M)
URL_SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:")
UP_RUN = re.compile(r"(?:\.\./)+")
PATH_LEFT, PATH_RIGHT = set("_$}{./-"), set("_./*-")


def link_targets(body):
    for m in MD_LINK.finditer(body):
        t = (m.group(1) or m.group(2) or "").split("#")[0]
        if t and not URL_SCHEME.match(t):
            yield m.start(), t


def heading_slugs(text):
    """GitHub's anchors for a markdown file's headings: lowercased, punctuation dropped, spaces to hyphens, repeats numbered."""
    seen, out = {}, set()
    for m in re.finditer(r"^#{1,6}[ \t]+(.+?)[ \t#]*$", strip_fences(text), re.M):
        base = re.sub(r"[^\w\- ]", "", m.group(1).lower()).replace(" ", "-")
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.add(base if n == 0 else f"{base}-{n}")
    return out


def glob_regex(pattern):
    """`**` spans folders; `*` and `?` stay inside one."""
    parts = re.findall(r"\*\*|\*|\?|[^*?]+", pattern)
    return re.compile("".join({"**": ".*", "*": "[^/]*", "?": "[^/]"}.get(p, re.escape(p)) for p in parts) + r"\Z")


def up_paths(text):
    """(index, token, base, rest) for each path with a `../` run. base: 'skill', 'plugin', 'file', or None for an absolute path."""
    seen = set()
    for m in UP_RUN.finditer(text):
        lo, hi = m.start(), m.end()
        while lo > 0 and (text[lo - 1].isalnum() or text[lo - 1] in PATH_LEFT):
            lo -= 1
        while hi < len(text) and (text[hi].isalnum() or text[hi] in PATH_RIGHT):
            hi += 1
        if lo in seen:
            continue
        seen.add(lo)
        tok = text[lo:hi]
        var = re.match(r"\$\{?(\w+)\}?/", tok)
        if var:
            yield lo, tok, {"CLAUDE_SKILL_DIR": "skill", "CLAUDE_PLUGIN_ROOT": "plugin"}.get(var.group(1), "file"), tok[var.end():]
        elif tok.startswith("/"):
            # `$(dirname "$0")/../x` is the script's folder; other absolute paths fall to the root-path rule.
            yield lo, tok, ("file" if text[lo - 1:lo] == ")" else None), tok.lstrip("/")
        else:
            yield lo, tok, "file", tok


def vendored_mask(text, inputs_heading):
    """Blank the upstream body of a vendored agent (its own `../` examples aren't this plugin's paths); keep frontmatter and Inputs."""
    lines, keep, in_fm, in_inputs = lines_of(text), [], text.startswith("---\n"), False
    for i, ln in enumerate(lines):
        if in_fm and i > 0 and ln == "---":
            in_fm = None
            keep.append(ln)
            continue
        if ln.startswith("## "):
            in_inputs = ln == inputs_heading
        keep.append(ln if in_fm or in_inputs else "")
    return "\n".join(keep)


def check_plugin_folder(repo, anchors):
    c = "plugin-folder"
    repo.out.start(c)
    pf = anchors["plugin_folder"]
    base = repo.pabs()
    if not os.path.isdir(base):
        repo.out.add("FAIL", c, repo.plugin, "plugin folder missing")
        return
    layout, copies, manual = set(pf["layout"]), set(pf.get("root_copies", [])), set(pf["manual_copy"])
    present = {n for n in os.listdir(base) if n != ".DS_Store"}
    for n in sorted(layout - present):
        repo.out.add("FAIL", c, repo.p(n), "missing from the plugin folder")
    for n in sorted(present - layout):
        repo.out.add("FAIL", c, repo.p(n), "not in plugin_folder.layout; every install would ship it")
    for n in sorted(layout):
        at_root = os.path.join(repo.root, n)
        if n in copies:
            same = os.path.isfile(at_root) and os.path.isfile(repo.pabs(n))
            if same:
                with open(at_root, "rb") as a, open(repo.pabs(n), "rb") as b:
                    same = a.read() == b.read()
            if not same:
                repo.out.add("FAIL", c, repo.p(n), f"must be a byte-identical copy of the root {n}")
        elif n == ".claude-plugin":
            extra = sorted(set(os.listdir(at_root)) - {"marketplace.json", ".DS_Store"}) if os.path.isdir(at_root) else []
            for x in extra:
                repo.out.add("FAIL", c, f".claude-plugin/{x}", "the root .claude-plugin/ holds only marketplace.json")
        elif n not in pf.get("target_project_names", []) and os.path.exists(at_root):
            repo.out.add("FAIL", c, n, f"at the repo root; it belongs in {repo.plugin}/ only")
    # Every root entry is classified, so a new one is a decision: repo only, or a name skills use for the target project.
    known = set(pf.get("target_project_names", [])) | copies | {".claude-plugin"} | {e.rstrip("/").split("/")[0] for e in pf["repo_only"]}
    for n in sorted(os.listdir(repo.root)):
        if not n.startswith(".") and n not in known:
            repo.out.add("FAIL", c, n, "root entry not in plugin_folder.repo_only or target_project_names")
    named = [re.compile(r"(?<![\w./~-])" + re.escape(e) + ("" if e.endswith("/") else r"(?![\w-])(?!\.\w)")) for e in pf["repo_only"]]
    named += [re.compile(re.escape(repo.plugin)), re.compile(re.escape(os.path.abspath(repo.root)))]
    allowed = [glob_regex(g) for g in pf["files"]]
    vendored = anchors.get("vendored") or {}
    mpath = vendored.get("manifest")
    mdata = repo.json(mpath, c) if mpath and os.path.isfile(os.path.join(repo.root, mpath)) else None
    upstream = {e.get("local_path") for e in (mdata or {}).get("files", []) if isinstance(e, dict)}
    for d, dirs, files in os.walk(base):
        for x in sorted(dirs + files):
            if os.path.islink(os.path.join(d, x)):
                repo.out.add("FAIL", c, repo.p(os.path.relpath(os.path.join(d, x), base)), "symlink; an install copies what it points at")
        dirs[:] = sorted(x for x in dirs if not os.path.islink(os.path.join(d, x)))
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(d, f), base).replace(os.sep, "/")
            if f == ".DS_Store" or os.path.islink(os.path.join(d, f)):
                continue
            prel, parts = repo.p(rel), rel.split("/")[:-1]
            if not any(r.match(rel) for r in allowed):
                repo.out.add("FAIL", c, prel, "matches no plugin_folder.files pattern; every install would ship it")
            try:
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            for pat in named:
                for m in pat.finditer(text):
                    repo.out.add("FAIL", c, f"{prel}:{lineno(text, m.start())}", f"names {m.group(0)!r}, which an install doesn't have (repo only)")
            if "templates" in parts:
                continue  # template paths are the target project's
            runtime = bool(parts and parts[0] in manual) or rel in manual
            scan = vendored_mask(text, vendored.get("inputs_heading", "")) if rel in upstream else text
            refs = [(scan, i, tok, b, rest) for i, tok, b, rest in up_paths(scan) if b]
            if f.endswith(".md"):
                body = strip_fences(scan)
                refs += [(body, i, t, "file", t) for i, t in link_targets(body)]
            for src, i, tok, b, rest in refs:
                start = {"skill": parts[:2], "plugin": [], "file": parts}[b]
                target = os.path.normpath("/".join(start + [rest]))
                where = f"{prel}:{lineno(src, i)}"
                if target == ".." or target.startswith("../"):
                    repo.out.add("FAIL", c, where, f"{tok!r} leaves the plugin folder")
                elif runtime and target.split("/")[0] not in manual | {"."}:
                    repo.out.add("FAIL", c, where, f"{tok!r} reaches {target}, which a manual copy doesn't have (plugin_folder.manual_copy)")
                elif os.path.splitext(f)[1] in (".md", ".sh", ".py") and rest.strip("./") and not glob.glob(os.path.join(base, target)):
                    repo.out.add("FAIL", c, where, f"{tok!r} doesn't exist in the plugin folder")
    # The README's manual copy has to bring every manual_copy entry along.
    readme = repo.read(repo.p("README.md"), c) or ""
    cp = "\n".join(ln for ln in lines_of(readme) if ln.strip().startswith("cp "))
    for n in sorted(manual):
        if not re.search(r"(?<![\w./-])" + re.escape(n) + r"(?=[/\s]|$)", cp, re.M):
            repo.out.add("FAIL", c, repo.p("README.md"), f"its manual-copy commands don't copy {n}")


def check_paths(repo, anchors):
    c = "doc-paths"
    repo.out.start(c)
    skills = set(repo.skill_dirs())
    prefixes = tuple(anchors.get("path_prefixes", ["skills/", ".claude-plugin/", "maintenance/"]))
    for rel in anchors.get("path_docs", ["CLAUDE.md", "README.md"]):
        text = repo.read(rel, c)
        if text is None:
            continue
        for m in re.finditer(r"`([^`\s]+)`", text):
            tok = m.group(1).rstrip(".,:;)")
            if any(ch in tok for ch in "<>{}…$"):
                continue
            if tok.split("/")[0] in skills and "/" in tok:
                tok = "skills/" + tok
            elif not tok.startswith(prefixes):
                continue
            # The docs name plugin files from the plugin folder (CLAUDE.md says so once), the rest from the root.
            if not glob.glob(os.path.join(repo.root, tok)) and not glob.glob(repo.pabs(tok)):
                repo.out.add("FAIL", c, f"{rel}:{lineno(text, m.start())}", f"path doesn't exist: {tok}")
        body = strip_fences(text)
        for i, t in link_targets(body):
            if not os.path.exists(os.path.join(repo.root, os.path.dirname(rel), t)):
                repo.out.add("FAIL", c, f"{rel}:{lineno(body, i)}", f"link target doesn't exist: {t}")
        for m in MD_LINK.finditer(body):
            t, _, frag = (m.group(1) or m.group(2) or "").partition("#")
            if not frag or URL_SCHEME.match(t) or (t and not t.endswith(".md")):
                continue
            target = os.path.join(repo.root, os.path.dirname(rel), t) if t else os.path.join(repo.root, rel)
            if os.path.isfile(target) and frag not in heading_slugs(open(target, encoding="utf-8").read()):
                repo.out.add("FAIL", c, f"{rel}:{lineno(body, m.start())}", f"link fragment #{frag} matches no heading in {t or rel}")
    sources = repo.json("maintenance/sources.json", c)
    for feed in (sources.get("feeds", []) if isinstance(sources, dict) else []):
        for a in (feed.get("affects", []) if isinstance(feed, dict) else []):
            tok = a.split()[0] if a.split() else ""
            if "/" in tok and not glob.glob(os.path.join(repo.root, tok)):
                repo.out.add("FAIL", c, "maintenance/sources.json", f"feed {feed.get('id')!r} affects {tok}, which doesn't exist")


def load_known(path):
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        known = state.get("contracts", {}).get("known_warnings", []) if isinstance(state, dict) else None
        if not isinstance(known, list) or not all(isinstance(k, dict) and isinstance(k.get("warning"), str) for k in known):
            raise ConfigError(f"{path}: contracts.known_warnings must be a list of {{warning, status}}")
        return known
    except (OSError, ValueError, AttributeError) as e:
        raise ConfigError(f"bad state file {path}: {e}")


def main():
    ap = maintlib.ArgParser()
    ap.add_argument("--root", default=maintlib.SCRIPT_ROOT)
    ap.add_argument("--anchors")
    ap.add_argument("--state")
    ap.add_argument("--pins")
    ap.add_argument("--heading")
    ap.add_argument("--min-len", type=int)
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if not os.path.isfile(os.path.join(root, "CLAUDE.md")) or not os.path.isfile(os.path.join(root, ".claude-plugin", "marketplace.json")):
        print(f"not a mobile-dev-skills checkout: {root}", file=sys.stderr)
        return 4
    if a.pins:
        return print_pins(root, a.pins, a.heading, a.min_len)
    if a.heading is not None or a.min_len is not None:
        print("--heading and --min-len need --pins", file=sys.stderr)
        return 4
    anchors_path = a.anchors or os.path.join(root, "maintenance", "anchors.json")
    try:
        with open(anchors_path, encoding="utf-8") as fh:
            anchors = json.load(fh)
        validate_anchors(anchors)
        known = load_known(a.state or os.path.join(root, "maintenance", "state.json"))
    except (OSError, ValueError, ConfigError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 4
    out, facts = Out(known), {}
    repo = Repo(root, out, anchors["plugin_folder"]["path"])
    try:
        check_plugin_folder(repo, anchors)
        check_syntax(repo)
        check_hidden_unicode(repo)
        check_frontmatter(repo, anchors, facts)
        check_vendored(repo, anchors, facts)
        check_platforms(repo, anchors, facts)
        check_counts(repo, anchors, facts)
        check_intake_lists(repo, anchors, facts)
        check_user_config(repo, anchors)
        check_substitutions(repo, anchors)
        check_skill_refs(repo)
        check_manifests(repo, anchors)
        check_mentions(repo, anchors)
        check_siblings(repo, anchors)
        check_release(repo, anchors)
        check_build_interface(repo, anchors)
        check_deploy_scripts(repo, anchors)
        check_spec_checker(repo, anchors)
        check_anchor_contracts(repo, anchors)
        check_paths(repo, anchors)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 4
    except Exception as e:  # a bug here must not read as exit 1 (= contract FAIL)
        print(f"internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    return out.emit()


if __name__ == "__main__":
    sys.exit(main())
