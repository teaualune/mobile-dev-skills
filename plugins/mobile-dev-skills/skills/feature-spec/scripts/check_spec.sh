#!/usr/bin/env bash
# feature-spec: check a spec file's structure, the part of the quality check a script can decide.
#
# Prints KEY=VALUE lines:
#   FINDING=<check> <line> <message>   one per finding; <check> is states, syntax, items or layout
#   SECTION6=blocks|bullets|none        section 6's format (bullets: only layout and items run)
#   SLUG=<feature-slug>                 the requirement ids' slug, when section 6 has blocks
#   PLATFORM_IDS=<id,...>|unknown       the platform ids a platform comment may name
#   RESULT=pass|fail findings=<n> blocks=<n> scenarios=<n> open=<n>   always the last line;
#                                       open counts section 8 items neither deliberately deferred nor declined
#
# Usage: check_spec.sh [--adapter <PLATFORM.md>] [--own-layout] <spec.md>
#   --adapter     takes the platform ids from that adapter's "Spec notation"; without it,
#                 from every adapter beside this skill
#   --own-layout  the project's own spec layout (feature-workflow Step 1.4): no ten-section or
#                 section 6 check, blocks found anywhere, every checkbox item read as a section 8 item
# Exit codes: 0 no findings; 1 findings; 4 usage (bad argument, unreadable file or adapter)
set -euo pipefail

ADAPTER=""
OWN=0
SPEC=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --adapter) [[ $# -ge 2 ]] || { echo "--adapter needs a path" >&2; exit 4; }; ADAPTER="$2"; shift 2 ;;
    --own-layout) OWN=1; shift ;;
    -*) echo "unknown argument: $1" >&2; exit 4 ;;
    *) [[ -z "$SPEC" ]] || { echo "one spec file only" >&2; exit 4; }; SPEC="$1"; shift ;;
  esac
done
[[ -n "$SPEC" ]] || { echo "usage: check_spec.sh [--adapter <PLATFORM.md>] [--own-layout] <spec.md>" >&2; exit 4; }
[[ -f "$SPEC" && -r "$SPEC" ]] || { echo "can't read $SPEC" >&2; exit 4; }

# Platform ids: the backticked words on an adapter's "Platform tags:" line.
tags_of() {
  sed -n 's/^- \*\*Platform tags:\*\*//p' "$1" | head -1 | grep -o '`[a-z0-9_-]*`' | tr -d '`' || true
}
if [[ -n "$ADAPTER" ]]; then
  [[ -f "$ADAPTER" && -r "$ADAPTER" ]] || { echo "can't read $ADAPTER" >&2; exit 4; }
  IDS=$(tags_of "$ADAPTER")
  [[ -n "$IDS" ]] || { echo "$ADAPTER has no 'Platform tags:' line" >&2; exit 4; }
else
  IDS=""
  for a in "$(dirname "$0")"/../../../platforms/*/PLATFORM.md; do
    [[ -f "$a" ]] && IDS="$IDS $(tags_of "$a")"
  done
fi
IDS=$(printf '%s\n' $IDS | sort -u | paste -sd, - || true)

# read, not $(cat <<…): bash 3.2 misparses quotes inside a heredoc in a command substitution.
PROG=""
IFS= read -r -d '' PROG <<'AWK' || true
function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
function finding(check, line, msg) { nf++; F[nf] = check " " line " " msg }
function level(s,   n) { n = 0; while (substr(s, n + 1, 1) == "#") n++; return (substr(s, n + 1, 1) == " " && n > 0) ? n : 0 }
function reasoned(s, word) { return s ~ ("^" word " +(\342\200\224|\342\200\223|-) *[^ ]") }
function is_state(part, w) { return part ~ ("^" w "([^A-Za-z0-9]|$)") }
# declined settles an item only as a marker after a dash or in parentheses, so a question about a declined card stays open.
function settled(s) {
  s = tolower(trim(s))
  if (s ~ /deliberately deferred/) return 1
  return s ~ /(\342\200\224|\342\200\223| -|\() *declined\)?\.?$/ || s ~ /(\342\200\224|\342\200\223| -) *declined *(\342\200\224|\342\200\223|- )/
}
{ sub(/\r$/, ""); if (NR == 1) sub(/^\357\273\277/, ""); L[NR] = $0 }
END {
  n = NR
  # Code fences hold sample code, never structure.
  fence = 0
  for (i = 1; i <= n; i++) {
    if (L[i] ~ /^ *(```|~~~)/) { fence = !fence; H[i] = 0; continue }
    H[i] = fence ? -1 : level(L[i])
  }

  # H1, H2 sections and the template numbering.
  h1 = 0; ns = 0
  for (i = 1; i <= n; i++) {
    if (H[i] == 1 && !h1) h1 = i
    if (H[i] == 2) { ns++; SL[ns] = i; t = L[i]; sub(/^## +/, "", t); SN[ns] = (t ~ /^[0-9]+\./) ? t + 0 : 0 }
  }
  sec6s = sec6e = sec8s = sec8e = 0
  # A project's own layout has no section 6 or 8 the script can find.
  if (!own) for (k = 1; k <= ns; k++) {
    e = (k < ns) ? SL[k + 1] - 1 : n
    if (SN[k] == 6 && !sec6s) { sec6s = SL[k]; sec6e = e }
    if (SN[k] == 8 && !sec8s) { sec8s = SL[k]; sec8e = e }
  }
  if (!h1) finding("layout", 1, "no H1 title")
  if (!own) {
    last = 0
    for (k = 1; k <= ns; k++) {
      if (!SN[k]) continue
      if (SN[k] < 1 || SN[k] > 10) { finding("layout", SL[k], "section " SN[k] " isn't one of the ten"); continue }
      if (SEEN[SN[k]]) { finding("layout", SL[k], "section " SN[k] " appears twice"); continue }
      SEEN[SN[k]] = SL[k]
      if (SN[k] < last) finding("layout", SL[k], "section " SN[k] " comes after section " last)
      last = SN[k] > last ? SN[k] : last
      e = (k < ns) ? SL[k + 1] - 1 : n; body = 0
      for (i = SL[k] + 1; i <= e; i++) if (trim(L[i]) != "") { body = 1; break }
      if (!body) finding("layout", SL[k], "section " SN[k] " is empty; write its content or N/A with a reason")
    }
    for (s = 1; s <= 10; s++) if (!SEEN[s]) finding("layout", h1 ? h1 : 1, "section " s " is missing; keep it, with N/A and a reason if it doesn't apply")
  }

  # Blocks: ### Requirement: / ### Invariant: and their #### Scenario: children.
  nb = 0
  for (i = 1; i <= n; i++) {
    if (H[i] == 3 && L[i] ~ /^### +(Requirement|Invariant):/) { nb++; B[nb] = i }
    else if (H[i] > 0 && L[i] ~ /^#+ +(Requirement|Invariant|Scenario)[: ]/ && !(H[i] == 4 && L[i] ~ /^#### +Scenario:/))
      finding("syntax", i, "malformed heading; blocks are ### Requirement: / ### Invariant: <title>, scenarios #### Scenario: <title>")
  }
  sec6 = nb ? "blocks" : "none"
  if (!nb && sec6s) for (i = sec6s + 1; i <= sec6e; i++) {
    t = trim(L[i]); if (t == "" || H[i] < 0) continue
    if (t !~ /^N\/A/) { sec6 = "bullets" }; break
  }

  if (nb) {
    # The Last verified line, directly under the H1.
    j = h1 + 1; while (j <= n && trim(L[j]) == "") j++
    if (!h1 || j > n || L[j] !~ /^> Last verified: /)
      finding("syntax", h1 ? h1 : 1, "no > Last verified: line directly under the H1")
    else if (L[j] !~ /^> Last verified: (never \(not implemented\)|never \(implemented, not yet verified\)|[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] \((commit [0-9a-f]+( \+ uncommitted changes)?|no commit)\))$/)
      finding("syntax", j, "Last verified isn't never (not implemented), never (implemented, not yet verified) or <date> (commit <sha>)")
    # Section 6 holds only blocks.
    if (sec6s) for (i = sec6s + 1; i < B[1] && i <= sec6e; i++) {
      t = trim(L[i]); if (t == "" || H[i] < 0) continue
      finding("syntax", i, "text in section 6 before its first block"); break
    }
  }

  slug = ""; nsc = 0
  for (b = 1; b <= nb; b++) {
    s0 = B[b]; kind = (L[s0] ~ /^### +Requirement:/) ? "R" : "I"
    t = L[s0]; sub(/^### +(Requirement|Invariant): */, "", t)
    if (trim(t) == "") finding("syntax", s0, "block has no title")
    if (!own && sec6s && (s0 < sec6s || s0 > sec6e)) finding("syntax", s0, "block outside section 6")
    e = n; for (i = s0 + 1; i <= n; i++) if (H[i] >= 1 && H[i] <= 3) { e = i - 1; break }
    BE[b] = e
    # Comment keys, directly under the heading.
    keys = ""; id = ""; scr = ""; i = s0 + 1
    delete V
    while (i <= e) {
      t = trim(L[i])
      if (t == "") { i++; continue }
      if (t !~ /^<!-- *[a-z_]+:.*-->$/) break
      k = t; sub(/^<!-- */, "", k); v = k; sub(/:.*/, "", k); sub(/^[a-z_]+: */, "", v); sub(/ *-->$/, "", v)
      keys = keys (keys == "" ? "" : ",") k; V[k] = trim(v)
      if (V[k] == "") finding("syntax", i, k " comment has no value")
      i++
    }
    want = (kind == "R") ? "id,screen,entities,enforced" : "id,entities,enforced"
    if (keys != want && !(kind == "I" && keys == "id,screen,entities,enforced"))
      finding("syntax", s0, "comment keys are " (keys == "" ? "none" : keys) "; expected " (kind == "R" ? "id, screen, entities, enforced" : "id, entities, enforced (screen after id when screen-bound)"))
    id = V["id"]; BID[b] = id
    if (id != "") {
      if (id !~ /^[a-z0-9]+(-[a-z0-9]+)*\.[1-9][0-9]*$/) finding("syntax", s0, "id " id " isn't <feature-slug>.<n>")
      else {
        sl = id; sub(/\.[0-9]+$/, "", sl)
        if (slug == "") slug = sl
        else if (sl != slug) finding("syntax", s0, "id " id " doesn't use the file's slug " slug)
        if (ID[id]) finding("syntax", s0, "id " id " is already an earlier block's id")
        else ID[id] = s0
      }
    }
    if ("enforced" in V && V["enforced"] != "" && V["enforced"] != "(filled in Phase 2)") {
      m = split(V["enforced"], parts, ",")
      for (q = 1; q <= m; q++) { p = trim(parts[q]); if (p !~ /^[^#]+#[^#]+$/ || p ~ /:[0-9]+#/ || p ~ /#L?[0-9]+$/) { finding("syntax", s0, "enforced " p " isn't <path>#<Symbol>"); break } }
    }
    scr = V["screen"]
    if (kind == "R" && scr != "") {
      m = split(scr, parts, ",")
      for (q = 1; q <= m; q++) { p = trim(parts[q]); gsub(/`/, "", p); if (p == "" || p == "none" || p ~ /^N\/A/) continue
        if (!(p in SCR)) { SCR[p] = s0; nscr++; SCRN[nscr] = p } }
    }
    BSCR[b] = scr
    # Statement: a line of its own before the first scenario.
    stmt = 0
    for (j = i; j <= e; j++) {
      if (H[j] > 0) break
      t = trim(L[j]); if (t == "" || H[j] < 0 || t ~ /^>/ || t ~ /^<!--/) continue
      stmt = 1; break
    }
    if (!stmt) finding("syntax", s0, "no statement after the comment keys")
    # TBDs inside the block need a section 8 item naming the id.
    for (j = s0; j <= e; j++) if (H[j] >= 0 && L[j] ~ /(^|[^A-Za-z])TBD([^A-Za-z]|$)/ && L[j] !~ /^<!--/) { BTBD[b] = j; break }
    # Change records, joined across the > lines of their blockquote.
    for (j = s0 + 1; j <= e; j++) {
      if (L[j] !~ /^> \*\*Bug fix/) continue
      rec = L[j]
      for (y = j + 1; y <= e && L[y] ~ /^>/ && L[y] !~ /^> \*\*/; y++) { u = L[y]; sub(/^> */, "", u); rec = rec " " u }
      if (rec !~ /^> \*\*Bug fix [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] \342\200\224 [^*]+:\*\* .*: (corrected|added|restored)\.?/)
        finding("syntax", j, "bug-fix record isn't > **Bug fix <date> \342\200\224 <title>:** ... <id> <Scenario>: corrected | added | restored.")
    }
    # Scenarios.
    nsb = 0
    for (j = s0 + 1; j <= e; j++) {
      if (H[j] == 4 && L[j] ~ /^#### +Scenario:/) { nsb++; nsc++
        t = L[j]; sub(/^#### +Scenario: */, "", t); t = trim(t)
        if (t == "") finding("syntax", j, "scenario has no title")
        se = e; for (x = j + 1; x <= e; x++) if (H[x] >= 1 && H[x] <= 4) { se = x - 1; break }
        # The titles that name states count for every screen the block names.
        STITLE[b, nsb] = t
        x = j + 1; while (x <= se && trim(L[x]) == "") x++
        if (x <= se && trim(L[x]) ~ /^<!-- *platform:/) {
          v = trim(L[x]); sub(/^<!-- *platform: */, "", v); sub(/ *-->$/, "", v)
          if (ids != "") { m = split(v, parts, ","); for (q = 1; q <= m; q++) { p = trim(parts[q]); if (!index("," ids ",", "," p ",")) finding("syntax", x, "platform " p " isn't one of " ids) } }
          x++; while (x <= se && trim(L[x]) == "") x++
        }
        first = (x <= se) ? trim(L[x]) : ""
        if (first ~ /^(- )?N\/A/) { sub(/^- /, "", first)
          if (!reasoned(first, "N/A")) finding("syntax", x, "N/A scenario gives no reason (N/A \342\200\224 <reason>)")
          for (y = x + 1; y <= se; y++) { u = trim(L[y])
            if (u ~ /^<!-- *test:/) finding("syntax", y, "N/A scenario has a test comment")
            if (u ~ /^- \*\*(GIVEN|WHEN|THEN|AND)\*\*/) { finding("syntax", y, "N/A scenario has GIVEN/WHEN/THEN lines"); break } }
          continue
        }
        if (first !~ /^<!-- *test:.*-->$/) {
          finding("syntax", j, "scenario doesn't start with its test comment (after its platform comment)")
        } else {
          v = first; sub(/^<!-- *test: */, "", v); sub(/ *-->$/, "", v); v = trim(v)
          # manual or none as a word, not a path that starts with it.
          if (v ~ /^manual( |\342\200\224|\342\200\223|$)/) { if (!reasoned(v, "manual")) finding("syntax", x, "manual test comment gives no reason (manual \342\200\224 <reason>)") }
          else if (v ~ /^none( |\342\200\224|\342\200\223)/) { if (!reasoned(v, "none")) finding("syntax", x, "test none gives no reason after its dash") }
          else if (v != "(filled in Phase 2)" && v != "none" && v !~ /^[^#]+#.+$/)
            finding("syntax", x, "test " v " isn't <path>#<description>, (filled in Phase 2), manual \342\200\224 <reason> or none")
          x++
        }
        wh = th = gv = 0
        for (y = x; y <= se; y++) {
          u = trim(L[y]); if (u == "" || H[y] < 0) continue
          if (u ~ /^<!-- *(test|platform):/) { finding("syntax", y, "test or platform comment out of place"); continue }
          if (u ~ /^- \*\*GIVEN\*\*/) { if (wh) finding("syntax", y, "GIVEN after WHEN"); gv = 1 }
          else if (u ~ /^- \*\*WHEN\*\*/) { if (th) finding("syntax", y, "WHEN after THEN"); wh = 1 }
          else if (u ~ /^- \*\*THEN\*\*/) { if (!wh) finding("syntax", y, "THEN before any WHEN"); th = 1 }
          else if (u ~ /^- \*\*AND\*\*/) { if (!th) finding("syntax", y, "AND before THEN") }
        }
        if (!wh) finding("syntax", j, "scenario has no WHEN line")
        if (!th) finding("syntax", j, "scenario has no THEN line")
      } else if (H[j] == 4) finding("syntax", j, "a heading inside a block that isn't #### Scenario:")
    }
    BNS[b] = nsb
    if (kind == "R" && nsb == 0) finding("syntax", s0, "requirement has no scenario")
  }
  # Section 6 headings that aren't blocks.
  if (nb && sec6s) for (i = sec6s + 1; i <= sec6e; i++)
    if (H[i] == 3 && L[i] !~ /^### +(Requirement|Invariant):/) finding("syntax", i, "a ### heading in section 6 that isn't a block")

  # States: across the blocks naming a screen, Loading, Error, Empty and Success.
  for (q = 1; q <= nscr; q++) {
    p = SCRN[q]; delete ST
    for (b = 1; b <= nb; b++) {
      m = split(BSCR[b], parts, ","); hit = 0
      for (r = 1; r <= m; r++) { w = trim(parts[r]); gsub(/`/, "", w); if (w == p) hit = 1 }
      if (!hit) continue
      for (k = 1; k <= BNS[b]; k++) {
        c = split(STITLE[b, k], tp, ",")
        for (r = 1; r <= c; r++) { w = trim(tp[r])
          if (is_state(w, "Loading")) ST["Loading"] = 1; if (is_state(w, "Error")) ST["Error"] = 1
          if (is_state(w, "Empty")) ST["Empty"] = 1;     if (is_state(w, "Success")) ST["Success"] = 1 }
      }
    }
    miss = ""
    if (!ST["Loading"]) miss = miss ", Loading"; if (!ST["Error"]) miss = miss ", Error"
    if (!ST["Empty"]) miss = miss ", Empty";     if (!ST["Success"]) miss = miss ", Success"
    if (miss != "") finding("states", SCR[p], p " has no " substr(miss, 3) " scenario (N/A \342\200\224 <reason> when it can't occur)")
  }

  # Section 8 items: the ids they name, the baseline forms, and what is still open.
  is8 = own ? 1 : (sec8s > 0); lo = own ? 1 : sec8s; hi = own ? n : sec8e
  open = 0; prov = 0
  if (is8) for (i = lo; i <= hi; i++) {
    if (H[i] < 0) continue
    if (H[i] == 3 || (own && H[i] > 0)) prov = (L[i] ~ /^#+ +Provisional/)
    if (L[i] !~ /^ *- \[[ xX]\] /) continue
    t = L[i]; sub(/^ *- \[[ xX]\] +/, "", t)
    if (L[i] ~ /^ *- \[ \]/ && !prov && !settled(t)) open++
    if (slug != "") {
      rest = t
      while (match(rest, slug "\\.[0-9]+")) {
        tok = substr(rest, RSTART, RLENGTH); pre = (RSTART > 1) ? substr(rest, RSTART - 1, 1) : ""
        post = substr(rest, RSTART + RLENGTH, 1); rest = substr(rest, RSTART + RLENGTH)
        if (pre ~ /[a-z0-9-]/ || post ~ /[0-9]/) continue
        NAMED[tok] = 1
        if (!(tok in ID)) finding("items", i, "names " tok ", which no block has")
      }
    }
    if (t ~ /Unplaced:/ && t !~ /^Unplaced: [^ ]+#[^ ]+ \342\200\224 [^ ]/) finding("items", i, "baseline item isn't Unplaced: <path>#<Symbol> \342\200\224 <what it seems to do>")
    if (t ~ /Not read:/ && t !~ /^Not read: [^ ].* \342\200\224 [^ ]/) finding("items", i, "baseline item isn't Not read: <path>, ... \342\200\224 <what they seem to hold>")
    if (t ~ /: uncertain([^a-z]|$)/ && t !~ /^[^:]+: uncertain \342\200\224 [^ ]/) finding("items", i, "baseline item isn't <id> <Scenario>: uncertain \342\200\224 <what the code didn't settle>")
  }
  for (b = 1; b <= nb; b++) if (BTBD[b] && BID[b] != "" && !(BID[b] in NAMED))
    finding("items", BTBD[b], BID[b] " holds a TBD that no section 8 item names")

  for (k = 1; k <= nf; k++) print "FINDING=" F[k]
  print "SECTION6=" sec6
  if (slug != "") print "SLUG=" slug
  print "PLATFORM_IDS=" (ids != "" ? ids : "unknown")
  print "RESULT=" (nf ? "fail" : "pass") " findings=" (nf + 0) " blocks=" nb " scenarios=" nsc " open=" open
  exit (nf ? 1 : 0)
}
AWK
LC_ALL=C awk -v own="$OWN" -v ids="$IDS" "$PROG" "$SPEC"
