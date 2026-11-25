#!/usr/bin/env python3
"""Reads a TESTING.md side-check report (the tables a real-app session ends its reply with) and checks it against TESTING.md. Read-only.

Usage:
  intake_rows.py parse REPORT                       the report's rows, normalized, with the ids they will get; says
                                                    whether state.json already lists the report (seen=NEW | SEEN <date>)
  intake_rows.py verify REPORT [--drop ID,...] [--map OLD=NEW,...]
                                                    TESTING.md after the rows were fed in (and some dropped or renumbered)
Options: --testing FILE (default <repo>/TESTING.md), --state FILE (default <repo>/maintenance/state.json)

Output lines:
  REPORT <path> sha256=<hex> date=<d> version=<v> cost=<c> seen=NEW|SEEN <date>
  MATCH <id> result=<r> current=<status word> line=<n>           then CURRENT / EVIDENCE / CELL lines for that id
  PROBLEM <id> group=<g> kind=<k> -> <id to use> insert_after=<line>   then CASE / PASS_WHEN lines
  FINDING=<kind> <where> <message>
  RESULT=pass|fail findings=<n> matches=<n> problems=<n>
Finding kinds: tables, id, cell, row, group, kind, status, dup, drop.
Exit: 0 no finding; 1 findings; 4 usage or config error.
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
RESULTS = ("passed", "partly", "failed")
CELL_RE = re.compile(r"^(passed|partly|failed)\s+—\s+(\d{4}-\d{2}-\d{2}),\s*([^,]+?),\s*a real (Flutter|SwiftUI|Compose) app")
ID_RE = re.compile(r"^[A-Z]\d+$")


class Parser(argparse.ArgumentParser):
    def error(self, message):
        print(f"usage error: {message}", file=sys.stderr)
        sys.exit(4)


def split_row(line):
    """Cells of a markdown table row; a `|` inside backticks stays in its cell."""
    s = line.strip()
    if not s.startswith("|"):
        return None
    cells, cur, tick = [], [], False
    for ch in s[1:]:
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        cells.append("".join(cur).strip())
    return cells


def norm(cell):
    """One plain line: HTML lists become '; '-joined items, backtick spans stay as written."""
    parts = re.split(r"(`[^`]*`)", cell)
    out = []
    for p in parts:
        if p.startswith("`"):
            out.append(p)
            continue
        items = re.findall(r"<li>(.*?)</li>", p, re.S)
        if items:
            head = re.split(r"<[uo]l>", p, maxsplit=1)[0]
            tail = re.split(r"</[uo]l>", p, maxsplit=1)[-1] if re.search(r"</[uo]l>", p) else ""
            p = head + " " + "; ".join(i.strip().rstrip(".") for i in items) + tail
        p = re.sub(r"</?(ul|ol|li|br|p)\s*/?>", " ", p)
        out.append(p)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def strip_ticks(s):
    s = s.strip()
    return s[1:-1].strip() if len(s) > 1 and s.startswith("`") and s.endswith("`") else s


def load_testing(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    group, rows, last, groups = None, {}, {}, {}
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^### ([A-Z])\. (.+)$", ln)
        if m:
            group = m.group(1)
            groups[group] = m.group(2)
            continue
        if ln.startswith("## "):
            group = None
        cells = split_row(ln)
        if group and cells and ID_RE.match(cells[0]):
            rows.setdefault(cells[0], []).append({"line": i, "cells": cells, "group": group})
            last[group] = i
    return lines, rows, last, groups


def load_report(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    info = {"sha256": hashlib.sha256(raw).hexdigest(), "path": path, "matches": [], "problems": [], "findings": []}
    m = re.search(r"side check\W+(\d{4}-\d{2}-\d{2})", text)
    info["date"] = m.group(1) if m else "?"
    m = re.search(r"Plugin version:\s*`?([0-9][^\s`(),]*)", text)
    info["version"] = m.group(1).rstrip(".") if m else "?"
    m = re.search(r"Cost:\s*([^\n]*)", text)
    info["cost"] = re.split(r"\.(?:\s|$)", m.group(1).strip())[0] if m else "?"
    mode, cols = None, {}
    for ln in text.split("\n"):
        cells = split_row(ln)
        if cells is None:
            mode = None
            continue
        low = [c.lower() for c in cells]
        if cells and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c):
            continue
        if "id" in low and "result" in low:
            mode, cols = "matches", {k: next((i for i, c in enumerate(low) if c.startswith(k)), None) for k in ("id", "result", "evidence", "status")}
            continue
        if "group" in low and "id" in low and "case" in low:
            mode, cols = "problems", {k: next((i for i, c in enumerate(low) if c.startswith(k)), None) for k in ("group", "id", "case", "pass", "kind", "status")}
            continue
        if mode and len(cells) >= 2:
            def cell(k):
                i = cols.get(k)
                return cells[i] if i is not None and i < len(cells) else ""
            if mode == "matches":
                info["matches"].append({k: cell(k) for k in ("id", "result", "evidence", "status")})
            else:
                info["problems"].append({k: cell(k) for k in ("group", "id", "case", "pass", "kind", "status")})
    return info


def emit(kind, where, message):
    print(f"FINDING={kind} {where} {message}")


def plan_ids(report, rows, last):
    """The id each problem gets: its own when free, else the next in its group."""
    taken = {g: [int(i[1:]) for i in rows if i[0] == g] for g in set(i[0] for i in rows)}
    plan = []
    for p in report["problems"]:
        g = p["group"].strip()[:1] or p["id"][:1]
        want = p["id"].strip()
        used = taken.setdefault(g, [])
        if ID_RE.match(want) and want not in rows and int(want[1:]) not in used:
            use = want
        else:
            use = f"{g}{(max(used) if used else 0) + 1}"
        used.append(int(use[1:]))
        plan.append((p, g, use))
    return plan


def cmd_parse(args, state):
    lines, rows, last, groups = load_testing(args.testing)
    r = load_report(args.report)
    seen = {e.get("sha256"): e for e in state.get("testing_intakes", []) if isinstance(e, dict)}
    mark = f"SEEN {seen[r['sha256']].get('intaken', '?')}" if r["sha256"] in seen else "NEW"
    print(f"REPORT {r['path']} sha256={r['sha256']} date={r['date']} version={r['version']} cost={r['cost']} seen={mark}")
    n = 0
    if not r["matches"] and not r["problems"]:
        emit("tables", args.report, "no 'Matching cases' or 'New problems' table found; read the report by hand")
        n += 1
    for m in r["matches"]:
        cid = strip_ticks(m["id"])
        res = m["result"].strip().lower()
        row = (rows.get(cid) or [None])[0]
        cell = strip_ticks(m["status"])
        cm = CELL_RE.match(cell)
        if not ID_RE.match(cid) or row is None:
            emit("id", cid, "is not a case in TESTING.md")
            n += 1
        if res not in RESULTS:
            emit("cell", cid, f"result {res!r} is not passed, partly or failed")
            n += 1
        if not cm:
            emit("cell", cid, "status cell isn't '<status> — <date>, <version>, a real Flutter|SwiftUI|Compose app'")
            n += 1
        else:
            if cm.group(1) != res:
                emit("cell", cid, f"status cell says {cm.group(1)}, result says {res}")
                n += 1
            if r["version"] != "?" and cm.group(3) != r["version"]:
                emit("cell", cid, f"cell version {cm.group(3)} differs from the report's {r['version']}")
                n += 1
        cur = row["cells"][-1] if row else ""
        cw = re.match(r"(\w+)", cur)
        print(f"MATCH {cid} result={res} current={cw.group(1) if cw else '?'} line={row['line'] if row else '?'}")
        print(f"CURRENT {cid}: {cur}")
        print(f"EVIDENCE {cid}: {norm(m['evidence'])}")
        print(f"CELL {cid}: {cell}")
    for p, g, use in plan_ids(r, rows, last):
        kind = strip_ticks(p["kind"]).lower()
        status = strip_ticks(p["status"]).lower()
        if g not in groups:
            emit("group", p["id"], f"group {g} has no heading in TESTING.md")
            n += 1
        if kind not in ("use", "synthetic"):
            emit("kind", p["id"], f"kind {kind!r} is not use or synthetic")
            n += 1
        if status != "open":
            emit("status", p["id"], f"a new problem starts as open, not {status!r}")
            n += 1
        if not (p["case"] and p["pass"]):
            emit("row", p["id"], "case or pass-when is empty")
            n += 1
        where = last.get(g, "?")
        note = "" if use == p["id"].strip() else f" (the report's {p['id'].strip()} is taken)"
        print(f"PROBLEM {p['id'].strip()} group={g} kind={kind} -> {use}{note} insert_after={where}")
        print(f"CASE {use}: {norm(p['case'])}")
        print(f"PASS_WHEN {use}: {norm(p['pass'])}")
    print(f"RESULT={'pass' if n == 0 else 'fail'} findings={n} matches={len(r['matches'])} problems={len(r['problems'])}")
    return 0 if n == 0 else 1


def cmd_verify(args, state):
    lines, rows, last, groups = load_testing(args.testing)
    r = load_report(args.report)
    drop = {x for x in (args.drop or "").split(",") if x}
    remap = dict(x.split("=", 1) for x in (args.map or "").split(",") if "=" in x)
    n = 0
    for cid, found in rows.items():
        if len(found) > 1:
            emit("dup", cid, f"appears {len(found)} times (lines {', '.join(str(f['line']) for f in found)})")
            n += 1
        for f in found:
            if len(f["cells"]) != 5:
                emit("row", f"{cid} line {f['line']}", f"has {len(f['cells'])} cells, expected 5")
                n += 1
    for m in r["matches"]:
        cid = strip_ticks(m["id"])
        res = m["result"].strip().lower()
        row = (rows.get(cid) or [None])[0]
        if row is None:
            emit("id", cid, "is missing from TESTING.md")
            n += 1
            continue
        cell = row["cells"][-1]
        cm = CELL_RE.match(strip_ticks(m["status"]))
        date, ver = (cm.group(2), cm.group(3)) if cm else (r["date"], r["version"])
        ok = cell.startswith(f"{res} — {date}, {ver}") or re.match(r"fixed — \d{4}-\d{2}-\d{2}, \S+", cell)
        if not ok:
            emit("cell", cid, f"status cell doesn't start with '{res} — {date}, {ver}' or 'fixed — …': {cell[:90]!r}")
            n += 1
    for p in r["problems"]:
        pid = p["id"].strip()
        use = remap.get(pid, pid)
        if pid in drop or use in drop:
            if use in rows:
                emit("drop", use, "was dropped but is still in TESTING.md")
                n += 1
            continue
        row = (rows.get(use) or [None])[0]
        if row is None:
            emit("id", use, "is missing from TESTING.md")
            n += 1
            continue
        if not re.match(r"(open|fixed|partly|passed|failed|owner)\b", row["cells"][-1]):
            emit("status", use, f"status cell starts oddly: {row['cells'][-1][:60]!r}")
            n += 1
        if row["cells"][3].strip("` ") not in ("use", "synthetic"):
            emit("kind", use, f"kind cell is {row['cells'][3]!r}")
            n += 1
    print(f"RESULT={'pass' if n == 0 else 'fail'} findings={n} matches={len(r['matches'])} problems={len(r['problems'])}")
    return 0 if n == 0 else 1


def main():
    ap = Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--testing", default=os.path.join(ROOT, "TESTING.md"))
    ap.add_argument("--state", default=os.path.join(ROOT, "maintenance", "state.json"))
    sub = ap.add_subparsers(dest="cmd")
    sub.required = True
    s = sub.add_parser("parse")
    s.add_argument("report")
    s = sub.add_parser("verify")
    s.add_argument("report")
    s.add_argument("--drop")
    s.add_argument("--map")
    for sp in sub.choices.values():
        sp.add_argument("--testing", default=argparse.SUPPRESS)
        sp.add_argument("--state", default=argparse.SUPPRESS)
    a = ap.parse_args()
    try:
        state = {}
        if os.path.isfile(a.state):
            with open(a.state, encoding="utf-8") as fh:
                state = json.load(fh)
        if not os.path.isfile(a.testing):
            print(f"config error: {a.testing} not found", file=sys.stderr)
            return 4
        if not os.path.isfile(a.report):
            print(f"usage error: {a.report} is not a file", file=sys.stderr)
            return 4
    except (OSError, ValueError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 4
    return {"parse": cmd_parse, "verify": cmd_verify}[a.cmd](a, state)


if __name__ == "__main__":
    sys.exit(main())
