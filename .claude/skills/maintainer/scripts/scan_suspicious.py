#!/usr/bin/env python3
"""Flag risky content in a proposed diff, fetched upstream text, or the working tree (maintainer skill).

Usage:
  scan_suspicious.py [--diff | --plain] [FILE ...]   (no FILE: read stdin)
  scan_suspicious.py --worktree [--root DIR]         (`git diff HEAD` plus every untracked file)
Input is read as a unified diff when it starts like one (`diff --git`, or `---` then `+++`) or with
--diff; then only added lines inside hunks are scanned. --plain scans every line.
Prints `SUSPICIOUS  <kind>  <where>  <excerpt>` per hit, then `SCAN  hits=N`.
Kinds: network, url-not-allowlisted, credential, piped-shell, encoded-blob, hidden-unicode.
Hits are for the owner to judge, not automatic rejections. The URL allowlist comes from this
script's own checkout (maintenance/sources.json).
Exit codes: 0 clean; 1 hits; 3 internal error; 4 usage error.
"""
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maintlib  # noqa: E402

PATTERNS = [
    ("network", re.compile(r"(?<![\w./-])(curl|wget|nc|ncat|telnet|scp|rsync|ssh|sftp|ftp)\s+(-|https?://|[\"'$]|[\w.-]+@)|"
                           r"urllib|requests\.(get|post)|http\.client|\bfetch\(|XMLHttpRequest|Invoke-WebRequest|\bsocket\.|"
                           r"\bgit\s+(?:-C\s+\S+\s+)?(clone|fetch|pull|ls-remote|submodule)\b")),
    ("credential", re.compile(r"~/\.ssh|\bid_(rsa|ed25519|ecdsa)\b|\.(p8|p12|pem|keystore|jks|mobileprovision)\b|"
                              r"service[-_ ]?account|keychain|security\s+find-|\.netrc|\.aws/|\.npmrc|\.pypirc|"
                              r"BEGIN [A-Z ]*PRIVATE KEY", re.I)),
    ("credential", re.compile(r"\b[A-Z0-9_]*(TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY)\b")),
    ("piped-shell", re.compile(r"(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b|(curl|wget)\b[^\n|]*\|\s*(python3?|perl|ruby|node)\b|"
                               r"\b(ba|z)?sh\s+<\(\s*(curl|wget)|\beval\s+\"?\$\(|\bsource\s+<\(")),
    ("encoded-blob", re.compile(r"[A-Za-z0-9+/]{120,}={0,2}|(\\x[0-9a-fA-F]{2}){8,}|\bbase64\s+(-d|--decode|-D)\b|"
                                r"\bfromCharCode\b|\batob\(|b64decode")),
]
URL = re.compile(r"https?://[^\s\"'`<>)\]]+")


def allowlist():
    try:
        with open(os.path.join(maintlib.SCRIPT_ROOT, "maintenance", "sources.json"), encoding="utf-8") as fh:
            return [e["prefix"] for e in json.load(fh)["allowlist"]]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def looks_like_diff(lines):
    body = [ln for ln in lines if ln.strip()][:2]
    return bool(body) and (body[0].startswith("diff --git") or
                           (len(body) == 2 and body[0].startswith("--- ") and body[1].startswith("+++ ")))


def added_lines(lines):
    """(input line number, content) for each line a unified diff adds; hunk lengths are tracked."""
    out, old, new = [], 0, 0
    for n, line in enumerate(lines, 1):
        if old > 0 or new > 0:
            if line.startswith("+"):
                out.append((n, line[1:]))
                new -= 1
            elif line.startswith("-"):
                old -= 1
            elif not line.startswith("\\"):
                old, new = old - 1, new - 1
            continue
        m = re.match(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", line)
        if m:
            old = int(m.group(1)) if m.group(1) is not None else 1
            new = int(m.group(2)) if m.group(2) is not None else 1
    return out


def scan(name, text, prefixes, mode=None):
    lines = text.split("\n")
    diff = mode == "diff" or (mode is None and looks_like_diff(lines))
    hits = 0
    for n, line in (added_lines(lines) if diff else enumerate(lines, 1)):
        found = [kind for kind, rx in PATTERNS if rx.search(line)]
        if any(True for _ in maintlib.hidden_chars(line)):
            found.append("hidden-unicode")
        if prefixes is not None and any(not maintlib.allowed(u, prefixes) for u in URL.findall(line)):
            found.append("url-not-allowlisted")
        for kind in dict.fromkeys(found):
            hits += 1
            shown = maintlib.HIDDEN.sub(lambda m: f"<U+{ord(m.group()):04X}>", line.strip())
            print(f"SUSPICIOUS  {kind}  {name}:{n}  {maintlib.one_line(shown, 140)}")
    return hits


def git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, errors="replace")


def scan_worktree(root, prefixes):
    has_head = git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0
    d = git(root, "diff", "HEAD") if has_head else git(root, "diff", "--cached")
    if d.returncode:
        raise OSError(d.stderr.strip() or "git diff failed")
    total = scan("git-diff", d.stdout, prefixes, mode="diff")
    u = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if u.returncode:
        raise OSError(u.stderr.strip() or "git ls-files failed")
    for rel in filter(None, u.stdout.split("\0")):
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            total += scan(rel, fh.read(), prefixes, mode="plain")
    return total


def main():
    ap = maintlib.ArgParser()
    ap.add_argument("files", nargs="*")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--diff", action="store_const", const="diff", dest="mode")
    g.add_argument("--plain", action="store_const", const="plain", dest="mode")
    g.add_argument("--worktree", action="store_true")
    ap.add_argument("--root", default=maintlib.SCRIPT_ROOT)
    a = ap.parse_args()
    if a.worktree and a.files:
        ap.error("--worktree takes no FILE")
    prefixes = allowlist()
    if prefixes is None:
        print("note: maintenance/sources.json not readable; URL allowlist check skipped", file=sys.stderr)
    total = 0
    try:
        if a.worktree:
            total = scan_worktree(os.path.abspath(a.root), prefixes)
        elif a.files:
            for f in a.files:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    total += scan(f, fh.read(), prefixes, a.mode)
        else:
            total = scan("<stdin>", sys.stdin.read(), prefixes, a.mode)
    except OSError as e:
        print(f"cannot read: {e}", file=sys.stderr)
        return 4
    except Exception as e:  # a bug must not look like "hits found" or "clean"
        print(f"internal error: {type(e).__name__}: {e}", file=sys.stderr)
        return 3
    print(f"SCAN  hits={total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
