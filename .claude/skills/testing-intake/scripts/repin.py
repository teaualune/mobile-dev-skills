#!/usr/bin/env python3
"""Brings maintenance/anchors.json's pins in line with the files they pin, after an intended edit. Dry run unless --write.

Usage: repin.py [--root DIR] [--write]

For each check of anchors.json "contracts" that has a `contains` list:
  exact check (a whole file or one section): the list becomes the lines check_contracts.py's pinned_lines() gives, in order.
  other check: a pin that is no longer in its file is replaced by the file line it most resembles (same first 25
  characters, similarity of at least 0.75); a pin with no such line is reported as MANUAL and left alone.
Each changed `contains` array is found in the raw file by its own text and replaced in place, so the file's layout
stays as it was (anchors.json isn't json.dumps-round-trippable). The result is parsed as JSON before it is written, and
a second pass over it must plan nothing. Edits of `repeats`, `order`, `not_contains` and every other key stay manual.

Output lines:
  REPIN <contract> <file> [<heading>] -<n> +<n>      then "  - <old pin>" and "  + <new pin>" lines
  MANUAL <contract> <file> <why>
  RESULT=clean | RESULT=changes edits=<n> manual=<n> written=yes|no
Exit: 0 clean, or written with nothing manual left; 1 changes pending or something manual; 4 usage or config error.
"""
import argparse
import difflib
import importlib.util
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # importing check_contracts must leave no __pycache__ in the repo

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def load_cc(root):
    p = os.path.join(root, ".claude", "skills", "maintainer", "scripts", "check_contracts.py")
    spec = importlib.util.spec_from_file_location("check_contracts", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def best_line(stale, text, taken):
    head = stale[:25]
    best, score = None, 0.0
    for ln in (x.strip() for x in text.split("\n")):
        if len(ln) < 20 or not ln.startswith(head) or ln in taken:
            continue
        r = difflib.SequenceMatcher(None, stale, ln, autojunk=False).ratio()
        if r > score:
            best, score = ln, r
    return best if score >= 0.75 else None


def plan(root, cc, data):
    """[(contract id, check, old list, new list)], [manual messages]."""
    changes, manual = [], []
    for contract in data.get("contracts", []):
        cid = contract.get("id", "?")
        for chk in contract.get("checks", []):
            want = chk.get("contains")
            if not want:
                continue
            rel = chk.get("file", "?")
            text = read(os.path.join(root, rel))
            if text is None:
                manual.append(f"MANUAL {cid} {rel} file not found")
                continue
            if chk.get("exact"):
                heading = chk["exact"] if isinstance(chk["exact"], str) else None
                if heading is not None and cc.section(text, heading) is None:
                    manual.append(f"MANUAL {cid} {rel} heading {heading!r} not found")
                    continue
                min_len = chk.get("min_len", 12)
                new = cc.pinned_lines(text, heading, min_len)
                if cc.repeated_lines(text, heading, min_len) != chk.get("repeats", {}):
                    manual.append(f"MANUAL {cid} {rel} repeated-line counts differ: edit \"repeats\" by hand")
            else:
                new, taken = [], set(want)
                for s in want:
                    if s in text:
                        new.append(s)
                        continue
                    cand = best_line(s, text, taken)
                    if cand:
                        taken.add(cand)
                        new.append(cand)
                    else:
                        new.append(s)
                        manual.append(f"MANUAL {cid} {rel} stale pin with no matching line: {s[:90]!r}")
            if new != want:
                changes.append((cid, chk, want, new))
    return changes, manual


def encode(s, ascii_only):
    return json.dumps(s, ensure_ascii=ascii_only)


def array_pattern(want, ascii_only):
    pins = [re.escape(encode(s, ascii_only)) for s in want]
    pat = r'("contains"\s*:\s*\[\s*)' + pins[0]
    if len(pins) > 1:
        pat += r"(\s*,\s*)" + pins[1] + "".join(r"\s*,\s*" + p for p in pins[2:])
    return re.compile(pat + r"(\s*\])")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--write", action="store_true")
    try:
        a = ap.parse_args()
    except SystemExit as e:
        return 4 if e.code else 0
    root = os.path.abspath(a.root)
    path = os.path.join(root, "maintenance", "anchors.json")
    raw = read(path)
    if raw is None or not os.path.isfile(os.path.join(root, ".claude", "skills", "maintainer", "scripts", "check_contracts.py")):
        print(f"config error: not a mobile-dev-skills checkout: {root}", file=sys.stderr)
        return 4
    try:
        data = json.loads(raw)
        cc = load_cc(root)
    except (ValueError, OSError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 4
    changes, manual = plan(root, cc, data)
    if not changes and not manual:
        print("RESULT=clean")
        return 0
    # Which raw array belongs to which check: the n-th check with identical pins takes the n-th match.
    by_chk = {id(chk): (cid, old, new) for cid, chk, old, new in changes}
    seen, spans = {}, []
    for contract in data.get("contracts", []):
        for chk in contract.get("checks", []):
            want = chk.get("contains")
            if not want:
                continue
            key = tuple(want)
            seen[key] = seen.get(key, 0) + 1
            hit = by_chk.get(id(chk))
            if not hit:
                continue
            cid, old, new = hit
            matches = []
            for ascii_only in (False, True):
                matches = list(array_pattern(old, ascii_only).finditer(raw))
                if matches:
                    break
            if len(matches) < seen[key]:
                manual.append(f"MANUAL {cid} {chk['file']} the pins' array wasn't found in the raw file")
                continue
            m = matches[seen[key] - 1]
            g1, close = m.group(1), m.group(m.lastindex)
            if len(old) > 1:
                sep = m.group(2)
            else:
                nl = g1.rfind("\n")
                sep = "," + g1[nl:] if nl >= 0 else ", "
            body = sep.join(encode(s, False) for s in new)
            spans.append((m.start(), m.end(), g1 + body + close))
            print(f"REPIN {cid} {chk['file']}" + (f" [{chk['exact']}]" if isinstance(chk.get("exact"), str) else "") + f" -{len([s for s in old if s not in new])} +{len([s for s in new if s not in old])}")
            for s in old:
                if s not in new:
                    print(f"  - {s[:110]}")
            for s in new:
                if s not in old:
                    print(f"  + {s[:110]}")
    out = raw
    for start, end, text in sorted(spans, reverse=True):
        out = out[:start] + text + out[end:]
    written = "no"
    if spans:
        try:
            again, _ = plan(root, cc, json.loads(out))
        except ValueError as e:
            print(f"MANUAL anchors.json the edited file isn't valid JSON ({e}); nothing written")
            return 1
        if again:
            print(f"MANUAL anchors.json a second pass would still change {len(again)} check(s); nothing written")
            return 1
        if a.write and not manual:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(out)
            written = "yes"
        elif a.write:
            print("MANUAL a manual item is left; nothing written")
    for line in manual:
        print(line)
    print(f"RESULT=changes edits={len(spans)} manual={len(manual)} written={written}")
    return 0 if written == "yes" else 1


if __name__ == "__main__":
    sys.exit(main())
