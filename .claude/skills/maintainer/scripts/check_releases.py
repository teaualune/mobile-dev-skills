#!/usr/bin/env python3
"""Compare upstream release metadata with maintenance/state.json (maintainer skill).

Usage:
  check_releases.py [--mode MODE] [--root DIR] [--state FILE] [--sources FILE]
  check_releases.py excerpt FEED_ID [--since VERSION] [--all] [--root DIR] [--state FILE] [--sources FILE]

Status run prints one line per feed, page and pending dry run, then a summary:
  FEED  <id>  mode=<m>  last=<v|->  latest=<v>  change=<first|same|patch|minor|major|older|changed|retagged|behind|error>  [key=value …]
  PAGE  <id>  mode=<m>  reviewed=<date|->  due=<yes|no>  [why=<reason>]  url=<url>
  PENDING  <finding>  since=<date>  files=<paths>
  SUMMARY  feeds=N changed=N pages_due=N errors=N pending=N
  NO_CHANGES                      (only when nothing changed, nothing is due and nothing failed)
`change=older` and feeds marked `inactive=` are reported but not counted as changed.
`excerpt` prints the changelog sections after VERSION (default: the feed's state value),
keeping only bullet lines that match the feed's keywords unless --all is given.

The URL allowlist always comes from this script's own checkout (maintenance/sources.json),
whatever --root/--sources say, and every redirect hop is checked against it. Never writes files.
Exit codes: 0 done; 2 done, but at least one fetch failed; 3 internal error; 4 usage/config error.
"""
import datetime
import email.utils
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True  # keep __pycache__ out of the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintlib  # noqa: E402

UA = "maintenance-check/1.0"
TRIGGERING = {"first", "major", "minor", "changed", "retagged"}
NOT_COUNTED = {"same", "older"}


class ConfigError(Exception):
    pass


class AllowlistRedirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, prefixes):
        super().__init__()
        self.prefixes = prefixes

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not maintlib.allowed(newurl, self.prefixes):
            raise urllib.error.URLError(f"redirect to a URL outside the allowlist: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    def __init__(self, prefixes):
        self.prefixes = prefixes
        self.opener = urllib.request.build_opener(AllowlistRedirects(prefixes))

    def check(self, url):
        if not maintlib.allowed(url, self.prefixes):
            raise ConfigError(f"URL not on the allowlist: {url}")

    def get(self, url):
        self.check(url)
        with self.opener.open(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
            return r.read()


def vkey(v):
    s = str(v).lstrip("vV")
    m = re.fullmatch(r"(\d+(?:\.\d+)*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?", s)
    if not m:
        core, pre, build = [int(x) for x in re.findall(r"\d+", s)], None, None
    else:
        core, pre, build = [int(x) for x in m.group(1).split(".")], m.group(2), m.group(3)
    core = tuple((core + [0] * 6)[:6])
    parts = lambda x: tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in x.split(".")) if x else ()
    return core, 0 if pre else 1, parts(pre), parts(build)  # a release sorts after its pre-releases


def classify(last, latest):
    if last is None:
        return "first"
    a, b = vkey(last), vkey(latest)
    if last == latest or a == b:
        return "same"
    if b < a:
        return "older"
    ca, cb = a[0], b[0]
    if cb[0] > ca[0] or (ca[0] == 0 and cb[0] == 0 and cb[1] > ca[1]):
        return "major"
    return "minor" if cb[1] > ca[1] else "patch"


def kind_flutter_releases(feed, F):
    d = json.loads(F.get(feed["url"]))
    h = d["current_release"]["stable"]
    rel = next(r for r in d["releases"] if r["hash"] == h)
    return rel["version"], {"dart": rel.get("dart_sdk_version", "?"), "date": str(rel.get("release_date", ""))[:10]}


def kind_pub_package(feed, F):
    d = json.loads(F.get(f"https://pub.dev/api/packages/{feed['package']}"))
    return d["latest"]["version"], {"date": str(d["latest"].get("published", ""))[:10],
                                    "changelog": f"https://pub.dev/packages/{feed['package']}/changelog"}


def kind_maven_metadata(feed, F):
    x = F.get(feed["url"]).decode()
    # Some libraries ship two-part versions (Robolectric 4.18).
    stable = [v for v in re.findall(r"<version>([^<]+)</version>", x) if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", v)]
    if not stable:
        raise ValueError("no stable versions in maven-metadata")
    return max(stable, key=vkey), {}


def kind_apple_rss(feed, F):
    root = ET.fromstring(F.get(feed["url"]))
    best = None
    for item in root.iter("item"):
        title = item.findtext("title") or ""
        m = re.search(feed["match"], title)
        if m and not re.search(feed.get("exclude", r"$^"), title, re.I):
            if best is None or vkey(m.group(1)) > vkey(best[0]):
                best = (m.group(1), item.findtext("pubDate") or "")
    if not best:
        raise ValueError("no matching release in the feed window")
    try:
        date = email.utils.parsedate_to_datetime(best[1]).date().isoformat()
    except (TypeError, ValueError):
        date = "?"
    return best[0], {"date": date}


def changelog_sections(text):
    sections, cur = [], None
    for line in text.split("\n"):
        m = re.match(r"^## \[?v?(\d+\.\d+\.\d+)", line)
        if m:
            cur = [m.group(1), []]
            sections.append(cur)
        elif cur is not None:
            cur[1].append(line)
    return sections


def kind_changelog_md(feed, F):
    sections = changelog_sections(F.get(feed["url"]).decode())
    if not sections:
        raise ValueError("no '## x.y.z' headings")
    return sections[0][0], {}


def kind_google_discovery(feed, F):
    d = json.loads(F.get(feed["url"]))
    picked, missing = {}, []
    for path in feed.get("methods", []):
        node, parts = d, path.split(".")
        try:
            for part in parts[:-1]:
                node = node["resources"][part]
            picked[path] = node["methods"][parts[-1]]
        except KeyError:
            missing.append(path)
    for name in feed.get("schemas", []):
        if name in d.get("schemas", {}):
            picked["schema:" + name] = d["schemas"][name]
        else:
            missing.append("schema:" + name)
    fp = hashlib.sha256(json.dumps(picked, sort_keys=True).encode()).hexdigest()[:16]
    extra = {"revision": d.get("revision", "?")}
    if missing:
        extra["missing"] = ",".join(missing)
    return fp, extra


def kind_git_tags(feed, F):
    F.check(feed["url"])
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    r = subprocess.run(["git", "ls-remote", "--tags", feed["url"]], capture_output=True, text=True, timeout=120, env=env)
    if r.returncode:
        raise ValueError(r.stderr.strip() or "git ls-remote failed")
    tags = {}
    for line in r.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        name = ref.removeprefix("refs/tags/")
        peeled = name.endswith("^{}")
        name = name.removesuffix("^{}")
        if re.fullmatch(r"v?\d+\.\d+\.\d+", name) and (peeled or name not in tags):
            tags[name] = sha
    if not tags:
        raise ValueError("no release tags")
    best = max(tags, key=vkey)
    return best, {"commit": tags[best]}


KINDS = {
    "flutter-releases": kind_flutter_releases,
    "pub-package": kind_pub_package,
    "maven-metadata": kind_maven_metadata,
    "apple-rss": kind_apple_rss,
    "changelog-md": kind_changelog_md,
    "google-discovery": kind_google_discovery,
    "git-tags": kind_git_tags,
}
FINGERPRINT_KINDS = {"google-discovery"}


def read_json(path, what):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        raise ConfigError(f"{what} {path}: {e}")


def validate(sources, state, prefixes):
    def need(cond, what):
        if not cond:
            raise ConfigError(what)

    need(isinstance(sources, dict) and isinstance(sources.get("feeds"), list) and isinstance(sources.get("pages"), list),
         "sources: needs feeds[] and pages[]")
    for f in sources["feeds"]:
        need(isinstance(f, dict) and all(isinstance(f.get(k), str) for k in ("id", "mode", "kind")), "sources: each feed needs id, mode, kind")
        need(f["kind"] in KINDS, f"sources: unknown kind {f['kind']!r} for feed {f['id']}")
        need(isinstance(f.get("url"), str) or (f["kind"] == "pub-package" and isinstance(f.get("package"), str)),
             f"sources: feed {f['id']} needs url (or package)")
        url = f.get("url") or f"https://pub.dev/api/packages/{f['package']}"
        need(maintlib.allowed(url, prefixes), f"feed {f['id']} URL not on the allowlist: {url}")
    feed_ids = {f["id"] for f in sources["feeds"]}
    for p in sources["pages"]:
        need(isinstance(p, dict) and all(isinstance(p.get(k), str) for k in ("id", "mode", "url")), "sources: each page needs id, mode, url")
        need(maintlib.allowed(p["url"], prefixes), f"page {p['id']} URL not on the allowlist: {p['url']}")
        need(isinstance(p.get("review_days", 0), int), f"page {p['id']}: review_days must be an integer")
        need(isinstance(p.get("trigger_feeds", []), list) and set(p.get("trigger_feeds", [])) <= feed_ids,
             f"page {p['id']}: trigger_feeds must list known feed ids")
    ids = [f["id"] for f in sources["feeds"]] + [p["id"] for p in sources["pages"]]
    need(len(ids) == len(set(ids)), "sources: duplicate feed/page id")
    need(isinstance(state, dict), "state: top level must be an object")
    for k in ("feeds", "pages"):
        need(isinstance(state.get(k, {}), dict) and all(isinstance(v, dict) for v in state.get(k, {}).values()),
             f"state: {k} must map ids to objects")
    need(isinstance(state.get("pending_dry_runs", []), list) and all(isinstance(x, dict) for x in state.get("pending_dry_runs", [])),
         "state: pending_dry_runs must be a list of objects")


def load(a):
    root = os.path.abspath(a.root)
    own = read_json(os.path.join(maintlib.SCRIPT_ROOT, "maintenance", "sources.json"), "allowlist source")
    try:
        prefixes = [e["prefix"] for e in own["allowlist"] if isinstance(e["prefix"], str)]
    except (KeyError, TypeError) as e:
        raise ConfigError(f"allowlist in {maintlib.SCRIPT_ROOT}/maintenance/sources.json: {e!r}")
    sources = read_json(a.sources or os.path.join(root, "maintenance", "sources.json"), "sources")
    state = read_json(a.state or os.path.join(root, "maintenance", "state.json"), "state")
    validate(sources, state, prefixes)
    return root, sources, state, Fetcher(prefixes)


def ecc_manifest(root, feed):
    path = os.path.join(root, feed["requires"])
    if not os.path.isfile(path):
        return None
    m = read_json(path, "manifest")
    files = m.get("files") if isinstance(m, dict) else None
    if not isinstance(files, list) or not all(isinstance(e, dict) for e in files):
        raise ConfigError(f"manifest {path}: files must be a list of objects")
    return files


def status(root, sources, state, F, mode):
    today = datetime.date.today()
    errors, changed, due_n, results = 0, 0, 0, {}
    feeds = [f for f in sources["feeds"] if mode in (None, f["mode"])]
    for f in feeds:
        last_entry = state.get("feeds", {}).get(f["id"], {})
        last = last_entry.get("value")
        try:
            latest, extra = KINDS[f["kind"]](f, F)
        except ConfigError:
            raise
        except Exception as e:  # network/parse failures are reported per feed
            errors += 1
            results[f["id"]] = "error"
            print(f"FEED  {f['id']}  mode={f['mode']}  last={maintlib.safe(last or '-')}  change=error  error={maintlib.one_line(e)}")
            continue
        if not maintlib.SAFE_VALUE.fullmatch(str(latest)):
            errors += 1
            results[f["id"]] = "error"
            print(f"FEED  {f['id']}  mode={f['mode']}  last={maintlib.safe(last or '-')}  change=error  error=unexpected-value-format")
            continue
        if f["kind"] in FINGERPRINT_KINDS:
            change = "first" if last is None else ("same" if latest == last else "changed")
        else:
            change = classify(last, latest)
            if change == "same" and "commit" in extra and last_entry.get("commit") not in (None, extra["commit"]):
                change = "retagged"
        inactive = None
        if f.get("requires"):
            entries = ecc_manifest(root, f)
            if entries is None:
                inactive = "no-manifest"
            else:
                behind = sum(1 for e in entries if e.get("upstream_commit") != extra.get("commit"))
                extra["behind"] = behind
                if change == "same" and behind:
                    change = "behind"
        results[f["id"]] = change
        if change not in NOT_COUNTED and not inactive:
            changed += 1
        if change == "same":
            extra.pop("changelog", None)
        elif f.get("notes"):
            extra["notes"] = ",".join(f["notes"])
        if inactive:
            extra["inactive"] = inactive
        tail = "  ".join(f"{k}={maintlib.safe(v)}" for k, v in extra.items())
        print(f"FEED  {f['id']}  mode={f['mode']}  last={maintlib.safe(last or '-')}  latest={latest}  change={change}  {tail}".rstrip())
    for p in sources["pages"]:
        if mode not in (None, p["mode"]):
            continue
        reviewed = state.get("pages", {}).get(p["id"], {}).get("reviewed")
        why = None
        if not reviewed:
            why = "never-reviewed"
        else:
            try:
                age = (today - datetime.date.fromisoformat(reviewed)).days
            except (TypeError, ValueError):
                raise ConfigError(f"state.json pages.{p['id']}.reviewed is not YYYY-MM-DD: {reviewed!r}")
            if p.get("review_days") and age > p["review_days"]:
                why = f"older-than-{p['review_days']}d"
        hit = [t for t in p.get("trigger_feeds", []) if results.get(t) in TRIGGERING]
        if hit:
            why = (why + "," if why else "") + "feed-" + "+".join(hit)
        due_n += bool(why)
        why_s = f"  why={why}" if why else ""
        print(f"PAGE  {p['id']}  mode={p['mode']}  reviewed={reviewed or '-'}  due={'yes' if why else 'no'}{why_s}  url={p['url']}")
    pending = state.get("pending_dry_runs", [])
    for d in pending:
        print(f"PENDING  {maintlib.one_line(d.get('finding', '?'), 80)}  since={maintlib.one_line(d.get('since', '?'), 20)}  "
              f"files={maintlib.one_line(','.join(d.get('files', [])), 200)}")
    print(f"SUMMARY  feeds={len(feeds)} changed={changed} pages_due={due_n} errors={errors} pending={len(pending)}")
    if not (changed or due_n or errors):
        print("NO_CHANGES")
    return 2 if errors else 0


def excerpt(sources, state, F, feed_id, since, show_all):
    feed = next((f for f in sources["feeds"] if f["id"] == feed_id), None)
    if not feed or feed["kind"] != "changelog-md":
        raise ConfigError(f"{feed_id!r} is not a changelog-md feed")
    since = since or state.get("feeds", {}).get(feed_id, {}).get("value")
    if not since:
        raise ConfigError(f"no baseline for {feed_id}: pass --since VERSION (first run: see the skill's claude-code mode)")
    kws = [k.lower() for k in feed.get("keywords", [])]
    versions = matched = total = 0
    for version, lines in changelog_sections(F.get(feed["url"]).decode()):
        if vkey(version) <= vkey(since):
            continue
        versions += 1
        bullets = [ln for ln in lines if re.match(r"^\s*[-*] ", ln)]
        total += len(bullets)
        keep = bullets if show_all else [ln for ln in bullets if any(k in ln.lower() for k in kws)]
        matched += len(keep)
        if keep:
            print(f"## {version}")
            print("\n".join(maintlib.one_line(ln, 2000) for ln in keep))
    print(f"EXCERPT  feed={feed_id} since={maintlib.safe(since)} versions={versions} matched={matched} total={total}")
    return 0


def main():
    ap = maintlib.ArgParser()
    ap.add_argument("command", nargs="?", choices=["status", "excerpt"], default="status")
    ap.add_argument("feed", nargs="?")
    ap.add_argument("--mode", choices=["toolchain", "packages", "claude-code", "ecc"])
    ap.add_argument("--since")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--root", default=maintlib.SCRIPT_ROOT)
    ap.add_argument("--state")
    ap.add_argument("--sources")
    a = ap.parse_args()
    try:
        root, sources, state, F = load(a)
        if a.command == "excerpt":
            if not a.feed:
                raise ConfigError("excerpt needs FEED_ID")
            return excerpt(sources, state, F, a.feed, a.since, a.all)
        return status(root, sources, state, F, a.mode)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 4
    except (OSError, urllib.error.URLError) as e:
        print(f"fetch failed: {maintlib.one_line(e)}", file=sys.stderr)
        return 2
    except Exception as e:  # a bug must not look like a clean run
        print(f"internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
