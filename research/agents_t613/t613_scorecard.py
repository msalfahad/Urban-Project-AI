"""T-613: 12-13 Nov scorecard tables read from the reconciled-quantities statement V10 (T-609, of record).

Research, unwired, read only: reads the committed, sha256-pinned statement JSON only (no drawing, workbook, coordinate
or client data); computes no new quantity, moves no total, releases nothing (ARCH_TAKEOFF_V3.0.58 NOT RELEASED; V2.9 +
route G unchanged). Sign as the statement: reference - engine; + = in the reference only.

  python3 -I research/agents_t613/t613_scorecard.py           # build out/SCORECARD_T613.json and .md
  python3 -I research/agents_t613/t613_scorecard.py --check   # rebuild and compare with out/ (exit 1 on a difference)

R-T613-1 (proposed, every villa: the table method). A scorecard read from a reconciled statement:
  (a) OF RECORD ONLY: every section is resolved through the statement's supersession chain (V7 .. V10 maps) to its
      section of record; a superseded section is never read, never added, and a statement `totals` entry whose section
      was superseded is checked only for reference / engine / difference equality with its section of record (a
      reclass never moves those), its by-class split being reported as superseded;
  (b) ONE UNIT, ONE REFERENCE KIND PER TABLE: tables are keyed (trade code, unit, reference kind); a row whose unit
      differs from its section's unit, or a sum over two units or two reference kinds, is refused;
  (c) SCORED vs APART: only DIFFERENCE sections (kind DIFFERENCE or the V1-V4 unkinded form) enter a trade table; a
      nested measured set, a conflict reading, an implied count, a cross reference, a bounds or one-sided block is
      listed apart and never added (its rows are terms of a scored section or beside it); no % is read from a nested
      set (F-T609-5);
  (d) STATUS PER ROW (WORKFLOW_CONTROLS s.5): class HELD -> HELD (whatever its evidence); evidence CHECKER_VERIFIED
      with its Checker verdict cited -> VERIFIED; PARTIALLY_VERIFIED (or a Checker section verdict that says PARTIALLY
      VERIFIED) -> PARTIALLY VERIFIED; a V1-V5 'CHECKER_CONFIRMED' stamp is a WHO-IS-RIGHT class confirmation, not a
      quantity re-measure, so it is UNKNOWN (class confirmed, quantity not stamped) unless a pinned Checker Gate A
      verdict names the row's own re-measure (READINGS below, quoted with its board time); WORKER_PROPOSED, no stamp or
      evidence by reference -> UNKNOWN with that sub-status. DRAWING-CONFIRMED is counted only where a row's own
      evidence says so; none is invented. A VERIFIED row without a cited Checker verdict is refused;
  (e) A LINE (section) IS VERIFIED only when every residual row is VERIFIED and none is HELD; otherwise PARTIALLY
      VERIFIED n / m (n VERIFIED rows of m) when any row is VERIFIED or PARTIALLY VERIFIED, HELD m / m when every
      row is HELD, else UNKNOWN 0 / m;
  (f) HELD IS NEVER 0 AND NEVER CORRECT: a HELD row is counted HELD with its delta and, where the statement carries
      it, its bound (low .. high, OPEN when the high is open); a HELD row with delta 0 and no bound is refused (a
      HELD counted as 0); HELD and UNKNOWN never enter an agreement figure, and no agreement figure is computed;
  (g) % ONLY AS PRINTED: the % column is the statement's own printed % of reference, labelled NOT a verdict; none is
      computed here; a % printed beside a HELD row (a V1-V4 section, R-T579-1 (e)), on a non-FREELANCER reference or
      on a nested set is suppressed with its reason and the printed figure quoted; a scorecard line carrying a % beside
      a HELD row is refused; freelancer agreement is never proof and no product accuracy figure is printed;
  (h) EXACT RE-ADD: per section the rows re-add to each class and the classes to the difference, reference - engine =
      difference, and each trade table's sums are the exact Decimal sums of its sections; pending merged work that is
      not in the statement (merged after it, or open) is listed as 'pending, not in V10', never folded in.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATEMENT = ROOT / "research/agents_t609/out/RECONCILED_STATEMENT_T609.json"
STATEMENT_SHA256 = "dc2b25d65003e383d9aee2d73da609891e35d28d780744b65702638bf8d665b7"
OUT_JSON = HERE / "out/SCORECARD_T613.json"
OUT_MD = HERE / "out/SCORECARD_T613.md"
SCHEMA = "URBAN_T613_SCORECARD_V1"
RULE = "R-T613-1"

D = Decimal
CLASSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
STATUSES = ("VERIFIED", "PARTIALLY VERIFIED", "DRAWING-CONFIRMED", "HELD", "UNKNOWN")
LEVELS = ("sections", "sections_v5", "sections_v6", "sections_v7", "sections_v8", "sections_v9", "sections_v10")
SUPERSEDES = ("supersedes_v7", "supersedes_v8", "supersedes_v9", "supersedes_v10")
SCORED_KINDS = (None, "DIFFERENCE")
CITE_FIELDS = ("evidence_verdict", "verification_basis", "source_verdict", "class_basis")


class ScorecardError(Exception):
    pass


# Pinned Checker readings for V5 (pre-stamp) rows whose stamp the Checker's own Gate A verdict qualifies. Key: section
# id + row name prefix. The board text is quoted from BOARD.md (agents/control) verbatim in part; nothing else is read.
READINGS = {
    ("T-568/alu-doors-nr", "GF D-GF-05 (no unit of his)"): (
        "VERIFIED",
        "Checker 2026-11-06 17:57 UTC (T-568 Gate A, merge 540bc99c) (e) INDEPENDENT: own census of door block INSERTs "
        "in the architectural DXF: 27 door inserts ... the GF cluster holds the 5 external leaves named ... total 6 "
        "aluminium + 20 internal + 1 entrance = 27 AGREE; (f) door counts 3 / 3 storeys"),
    ("T-568/internal-doors-nr", "1F D-1F-02 (no unit of his)"): (
        "VERIFIED",
        "Checker 2026-11-06 17:57 UTC (T-568 Gate A, merge 540bc99c) (e) the 1F cluster holds 10 leaves ... exactly the "
        "worker's 1F list -> 1F 10 doors vs his 8 = +2 count ENGINE_RIGHT CONFIRMED; (f) door counts 3 / 3 storeys"),
    ("T-568/internal-doors-nr", "1F D-1F-10 (no unit of his)"): (
        "VERIFIED",
        "Checker 2026-11-06 17:57 UTC (T-568 Gate A, merge 540bc99c) (e) the 1F cluster holds 10 leaves ... exactly the "
        "worker's 1F list -> 1F 10 doors vs his 8 = +2 count ENGINE_RIGHT CONFIRMED; (f) door counts 3 / 3 storeys"),
    ("T-568/internal-doors-nr", "DOOR.INTERNAL.PVC nr"): (
        "VERIFIED",
        "Checker 2026-11-06 17:57 UTC (T-568 Gate A, merge 540bc99c) (e) own census: 6 aluminium + 20 internal + 1 "
        "entrance = 27 AGREE (count of drawn leaves); widths NOT re-measured"),
    ("T-573/ceiling-board", "GF reception + dining + entrance (incl. pantry, south dining piece): no ceiling under"): (
        "PARTIALLY VERIFIED",
        "Checker 2026-11-06 20:02 UTC (T-573 Gate A, merge 587e47f9) (e) light-well outline 5.820 x 2.750 = 16.005 m2 "
        "AGREE, no-ceiling 13.39 AGREE to 0.02 %; pocket 0.233 / 1.551 not re-measured; (f) no ceiling line VERIFIED"),
    ("T-573/ceiling-paint", "paint: his cove-light strips"): (
        "PARTIALLY VERIFIED",
        "Checker 2026-11-06 20:02 UTC (T-573 Gate A, merge 587e47f9) re-added: paint -42.688823 + 27.9345 - 42.745 = "
        "-57.499323 AGREE (arithmetic); cove strips RULE_DIFFERENCE; (f) no ceiling line VERIFIED"),
}

# Merged or open work that is not in statement V10 (R-T613-1 (h)); the statement's own pending list is appended.
PENDING_NOT_IN_V10 = (
    {"task": "T-600", "state": "open (TODO r2 at the claim 2026-11-08T01:02Z)",
     "effect": "column / beam per-storey residuals GF 0.620464 (+ B7 0.120452) / 1F 1.208362 / 2F 0.42 m3 stay "
               "UNRESOLVED in T-545/beams@V10; not folded in"},
    {"task": "T-608", "state": "MERGED 3c3aa2f8 (after V10)",
     "effect": "FR-T608-1 ARCH.PASSAGE 9 -> 6 pcs (3 lift lines RELEASED -> EXCLUDED), FR-T608-2 lift landing door "
               "supply ADD HELD-blank x 3: no V10 section carries these lines; fix rows not wired; not folded in"},
    {"task": "T-616", "state": "merged on the engine branch 17559e1b (board row READY at the claim)",
     "effect": "lintel-implied count his 54 vs 60 by opening (T-571/lintel-count-implied@V8, an APART section, "
               "UNRESOLVED -6 nr): split ENGINE_RIGHT 3..5 + W17 / UNRESOLVED 2..4 not in V10; not folded in"},
)


# ================================================================================ reading the statement ============
def load_statement(path: Path = STATEMENT, sha: str | None = STATEMENT_SHA256) -> dict:
    raw = path.read_bytes()
    if sha is not None and hashlib.sha256(raw).hexdigest() != sha:
        raise ScorecardError(f"{path.name}: sha256 differs from the pinned statement V10 (re-pin in a new version)")
    return json.loads(raw)


def all_sections(st: dict) -> dict:
    out = {}
    for lv in LEVELS:
        for c in st.get(lv, []):
            if c["section_id"] in out:
                raise ScorecardError(f"{c['section_id']}: section id twice in the statement")
            out[c["section_id"]] = dict(c, _level=lv)
    return out


def supersession(st: dict) -> dict:
    sup = {}
    for k in SUPERSEDES:
        sup.update({a: b for a, b in st.get(k, {}).items() if not a.startswith("beside")})
    return sup


def of_record(sid: str, sup: dict) -> str:
    seen = set()
    while sid in sup:
        if sid in seen:
            raise ScorecardError(f"{sid}: supersession loop")
        seen.add(sid)
        sid = sup[sid]
    return sid


def sections_of_record(st: dict) -> OrderedDict:
    secs, sup = all_sections(st), supersession(st)
    for a, b in sup.items():
        if b not in secs:
            raise ScorecardError(f"{a} -> {b}: superseding section absent")
    return OrderedDict((k, v) for k, v in secs.items() if k not in sup)


def trade_code(trade: str) -> str:
    m = re.match(r"\s*(B\d+)", trade or "")
    return m.group(1) if m else f"UNCODED: {trade}"


# ================================================================================ (d) row status ==================
def _cite(row: dict) -> str | None:
    for f in CITE_FIELDS:   # the first field that names a Checker verdict (a bare stamp is not a citation)
        if row.get(f) and "Checker" in row[f]:
            return row[f]
    v = row.get("verification") or ""
    return v if v.startswith("Checker ") else None


def _reading(sid: str, row: dict):
    for (s, prefix), val in READINGS.items():
        if s == sid and row["name"].startswith(prefix):
            return val
    return None


def row_status(sid: str, row: dict) -> tuple[str, str, str | None]:
    """(status, sub-status, Checker citation or None)."""
    ev = row.get("evidence_status")
    ver = row.get("verification") or ""
    rd = _reading(sid, row)
    if row["class"] == "HELD":
        return "HELD", f"evidence {ev or ver[:40] or 'none'}", _cite(row)
    if rd is not None:
        return rd[0], "pinned Checker Gate A reading (V5 stamp qualified)", rd[1]
    if ev == "CHECKER_VERIFIED":
        c = _cite(row)
        if not c or "Checker" not in c:
            raise ScorecardError(f"{sid}: '{row['name'][:60]}' VERIFIED without a cited Checker verdict")
        return "VERIFIED", "CHECKER_VERIFIED", c
    if ev == "PARTIALLY_VERIFIED":
        return "PARTIALLY VERIFIED", "PARTIALLY_VERIFIED", _cite(row)
    if ev == "DRAWING_CONFIRMED":
        return "DRAWING-CONFIRMED", "DRAWING_CONFIRMED", _cite(row)
    if ev == "WORKER_PROPOSED":
        return "UNKNOWN", "worker-proposed", _cite(row)
    if ev:
        raise ScorecardError(f"{sid}: '{row['name'][:60]}' unknown evidence stamp {ev!r}")
    if ver.startswith("Checker ") and "PARTIALLY VERIFIED" in ver:
        return "PARTIALLY VERIFIED", "Checker section verdict", ver
    if ver.startswith("CHECKER_CONFIRMED"):
        return "UNKNOWN", "class confirmed (pre-stamp), quantity not stamped", _cite(row)
    if ver == "CHECKER_VERIFIED":
        raise ScorecardError(f"{sid}: '{row['name'][:60]}' VERIFIED without a cited Checker verdict")
    if ver == "WORKER_PROPOSED":
        return "UNKNOWN", "worker-proposed", _cite(row)
    if ver.startswith("AS "):
        return "UNKNOWN", f"evidence by reference ({ver})", None
    if not ver:
        return "UNKNOWN", "no stamp (pre-stamp section)", None
    raise ScorecardError(f"{sid}: '{row['name'][:60]}' unknown verification {ver[:40]!r}")


def held_bound(sid: str, row: dict) -> tuple[Decimal, Decimal | None]:
    """(low, high or None = OPEN) added to the HELD delta; refuses a HELD counted as 0 (R-T613-1 (f))."""
    b = row.get("bound")
    if D(row["delta"]) == 0:
        if not b:
            raise ScorecardError(f"{sid}: HELD row '{row['name'][:60]}' with delta 0 and no bound (HELD counted as 0)")
        lo, hi = b[0], b[1]
        if hi is not None and D(hi) == 0:
            raise ScorecardError(f"{sid}: HELD row '{row['name'][:60]}' bounded at 0 .. 0 (HELD counted as 0)")
        return D(lo), (D(hi) if hi is not None else None)
    return D(0), D(0)


# ================================================================================ (e) (g) (h) one section =========
def section_card(sid: str, sec: dict) -> dict:
    unit, rows = sec["unit"], sec.get("rows", [])
    ref, eng, diff = D(sec["reference_total"]), D(sec["engine_valued"]), D(sec["difference"])
    if ref - eng != diff:
        raise ScorecardError(f"{sid}: reference - engine {ref - eng} != difference {diff}")
    by = {c: D(0) for c in CLASSES}
    st_count = {s: 0 for s in STATUSES}
    st_signed = {s: D(0) for s in STATUSES}
    st_gross = {s: D(0) for s in STATUSES}
    subs: dict = {}
    held_lo, held_hi_open, held_hi = D(0), False, D(0)
    out_rows = []
    for r in rows:
        if r.get("unit") not in (None, unit):
            raise ScorecardError(f"{sid}: row '{r['name'][:60]}' in {r['unit']} inside a {unit} section (two units)")
        if r["class"] not in CLASSES:
            raise ScorecardError(f"{sid}: class {r['class']!r} is not a statement class")
        dl = D(r["delta"])
        status, sub, cite = row_status(sid, r)
        by[r["class"]] += dl
        st_count[status] += 1
        st_signed[status] += dl
        st_gross[status] += abs(dl)
        subs[f"{status} / {sub}"] = subs.get(f"{status} / {sub}", 0) + 1
        b = None
        if status == "HELD":
            lo, hi = held_bound(sid, r)
            held_lo += lo
            if hi is None:
                held_hi_open = True
            else:
                held_hi += hi
            if D(r["delta"]) == 0:
                b = [str(lo), str(hi) if hi is not None else "OPEN"]
        out_rows.append({"name": r["name"][:160], "class": r["class"], "delta": r["delta"], "status": status,
                         "sub": sub, "checker_citation": (cite[:240] if cite else None), "held_bound": b})
    if rows:
        for c in CLASSES:
            if by[c] != D(sec["by_class"].get(c, "0")):
                raise ScorecardError(f"{sid}: rows re-add to {c} {by[c]} != statement {sec['by_class'].get(c)}")
        if sum(by.values()) != diff:
            raise ScorecardError(f"{sid}: classes re-add to {sum(by.values())} != difference {diff}")
    held_rows = st_count["HELD"]
    n, m = st_count["VERIFIED"], len(rows)
    pv = st_count["PARTIALLY VERIFIED"]
    if not m:
        line = "NO ROWS (set sums only)"
    elif n == m and held_rows == 0:
        line = "VERIFIED"
    elif held_rows == m:
        line = f"HELD {m} / {m}"
    elif n or pv:
        line = f"PARTIALLY VERIFIED {n} / {m}" + (f" (+{pv} rows PV)" if pv else "")
    else:
        line = f"UNKNOWN 0 / {m}"
    kind = sec.get("kind")
    pct = sec.get("difference_pct_of_reference")
    if kind not in SCORED_KINDS:
        pct_out, pct_why = None, f"none: {kind} set (apart, F-T609-5: no % from a nested set)"
    elif sec.get("reference_kind") != "FREELANCER":
        pct_out, pct_why = None, f"none: reference is {sec.get('reference_kind')}, not the freelancer"
    elif held_rows and pct is not None:
        pct_out, pct_why = None, (f"suppressed: the V1-V4 section prints {pct} beside {held_rows} HELD row(s) "
                                  "(R-T579-1 (e) NOT a verdict; F-T603-6 / R-T613-1 (g): no % beside HELD)")
    elif pct is None:
        why = sec.get("pct_refused_because") or ("HELD rows present (R-T579-1 (e))" if held_rows else
                                                  "not printed by the statement")
        pct_out, pct_why = None, f"none: {why}"
    else:
        pct_out, pct_why = pct, "as printed by the statement: NOT a verdict, not agreement"
    if pct_out is not None and held_rows:
        raise ScorecardError(f"{sid}: a % beside a HELD row (R-T613-1 (g))")
    return {"section_id": sid, "level": sec["_level"], "kind": kind or "DIFFERENCE (V1-V4 form)",
            "trade": sec.get("trade"), "trade_code": trade_code(sec.get("trade")), "unit": unit,
            "reference_kind": sec.get("reference_kind"), "report": sec.get("report"),
            "reference_total": sec["reference_total"], "engine_valued": sec["engine_valued"],
            "difference": sec["difference"], "pct_of_reference": pct_out, "pct_note": pct_why,
            "by_class": {c: str(by[c]) if rows else sec["by_class"].get(c, "0") for c in CLASSES},
            "status_count": st_count, "status_signed": {s: str(v) for s, v in st_signed.items()},
            "status_gross": {s: str(v) for s, v in st_gross.items()}, "sub_status": dict(sorted(subs.items())),
            "held_rows": held_rows, "held_bound_add": [str(held_lo), "OPEN" if held_hi_open else str(held_hi)],
            "line_status": line, "rows": out_rows}


# ================================================================================ (a) (b) trade tables ============
def trade_tables(cards: list[dict]) -> list[dict]:
    groups: OrderedDict = OrderedDict()
    for c in cards:
        groups.setdefault((c["trade_code"], c["unit"], c["reference_kind"]), []).append(c)
    out = []
    for (code, unit, rk), cs in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2]))):
        out.append(sum_group(code, unit, rk, cs))
    return out


def sum_group(code: str, unit: str, rk: str, cs: list[dict]) -> dict:
    if len({c["unit"] for c in cs}) != 1 or cs[0]["unit"] != unit:
        raise ScorecardError(f"{code}: sum over two units refused ({sorted({c['unit'] for c in cs})})")
    if len({c["reference_kind"] for c in cs}) != 1:
        raise ScorecardError(f"{code} {unit}: sum over two reference kinds refused")
    tot = {k: sum((D(c[k]) for c in cs), D(0)) for k in ("reference_total", "engine_valued", "difference")}
    by = {k: sum((D(c["by_class"][k]) for c in cs), D(0)) for k in CLASSES}
    if tot["reference_total"] - tot["engine_valued"] != tot["difference"] or sum(by.values()) != tot["difference"]:
        raise ScorecardError(f"{code} {unit}: group does not re-add")
    sc = {s: sum(c["status_count"][s] for c in cs) for s in STATUSES}
    ss = {s: str(sum((D(c["status_signed"][s]) for c in cs), D(0))) for s in STATUSES}
    sg = {s: str(sum((D(c["status_gross"][s]) for c in cs), D(0))) for s in STATUSES}
    lo = sum((D(c["held_bound_add"][0]) for c in cs), D(0))
    hi_open = any(c["held_bound_add"][1] == "OPEN" for c in cs)
    hi = "OPEN" if hi_open else str(sum((D(c["held_bound_add"][1]) for c in cs), D(0)))
    lines = {}
    for c in cs:
        k = ("PARTIALLY VERIFIED" if c["line_status"].startswith("PARTIALLY") else
             "NO ROWS" if c["line_status"].startswith("NO ROWS") else c["line_status"].split(" ")[0])
        lines[k] = lines.get(k, 0) + 1
    return {"trade_code": code, "unit": unit, "reference_kind": rk, "sections": [c["section_id"] for c in cs],
            "reference_total": str(tot["reference_total"]), "engine_valued": str(tot["engine_valued"]),
            "difference": str(tot["difference"]), "by_class": {k: str(v) for k, v in by.items()},
            "status_count": sc, "status_signed": ss, "status_gross": sg, "held_bound_add": [str(lo), hi],
            "lines_by_status": dict(sorted(lines.items())),
            "note": "sums of reference lines in one unit and one reference kind; not an agreement figure"}


def check_statement_totals(st: dict, record: dict) -> list[dict]:
    """Every statement `totals` entry against the section of record (R-T613-1 (a))."""
    sup = supersession(st)
    out = []
    for t in st["totals"]:
        if len(t["sections"]) != 1:
            raise ScorecardError(f"totals {t['trade']}: more than one section ({t['sections']})")
        sid = t["sections"][0]
        cur = of_record(sid, sup)
        sec = record[cur]
        for k in ("reference_total", "engine_valued", "difference"):
            if D(t[k]) != D(sec[k]):
                raise ScorecardError(f"totals {sid}: {k} {t[k]} != section of record {cur} {sec[k]}")
        if sec["unit"] != t["unit"]:
            raise ScorecardError(f"totals {sid}: unit {t['unit']} != {sec['unit']}")
        moved = {c: [t["by_class"][c], sec["by_class"].get(c, "0")] for c in CLASSES
                 if D(t["by_class"][c]) != D(sec["by_class"].get(c, "0"))}
        if cur == sid and moved:
            raise ScorecardError(f"totals {sid}: by class differs from its own section ({moved})")
        out.append({"totals_section": sid, "section_of_record": cur, "unit": t["unit"],
                    "reference_engine_difference": "EQUAL",
                    "by_class": "EQUAL" if not moved else "SUPERSEDED (statement totals entry predates the restatement)",
                    "by_class_moved": moved})
    return out


# ================================================================================ build ===========================
def build(st: dict, pending: tuple = PENDING_NOT_IN_V10) -> dict:
    record = sections_of_record(st)
    cards, apart = [], []
    for sid, sec in record.items():
        if sec.get("kind") in SCORED_KINDS:
            if "rows" not in sec or "reference_total" not in sec:
                raise ScorecardError(f"{sid}: scored section without rows / reference")
            cards.append(section_card(sid, sec))
        else:
            ap = {"section_id": sid, "kind": sec.get("kind"), "trade": sec.get("trade"), "unit": sec.get("unit"),
                  "why_apart": "nested / reading / implied / cross-reference / bounds: never added (R-T613-1 (c))"}
            if "rows" in sec and "reference_total" in sec:
                c = section_card(sid, sec)
                ap.update({k: c[k] for k in ("reference_total", "engine_valued", "difference", "line_status",
                                             "status_count", "pct_of_reference", "pct_note", "by_class")})
            apart.append(ap)
    tables = trade_tables(cards)
    for tb in tables:   # the trade table re-adds from its sections exactly
        mine = [c for c in cards if c["section_id"] in tb["sections"]]
        if str(sum((D(c["difference"]) for c in mine), D(0))) != tb["difference"]:
            raise ScorecardError(f"{tb['trade_code']}: table difference not the sum of its sections")
    totals = check_statement_totals(st, record)
    by_unit_class: dict = {}
    for c in cards:   # one unit and one reference kind per row (R-T613-1 (b))
        u = by_unit_class.setdefault(f"{c['unit']} / {c['reference_kind']}", {k: D(0) for k in CLASSES})
        for k in CLASSES:
            u[k] += D(c["by_class"][k])
    sup = supersession(st)
    return {
        "schema": SCHEMA, "rule": RULE,
        "statement": {"path": str(STATEMENT.relative_to(ROOT)), "sha256": STATEMENT_SHA256,
                      "schema": st.get("schema_v10"), "released_quantities_changed": st.get("released_quantities_changed")},
        "not_claimed": "development villa; not an accuracy claim; no product accuracy figure; freelancer agreement is "
                       "never proof; nothing released (V3.0.58 NOT RELEASED; V2.9 + route G unchanged)",
        "sections_in_statement": len(all_sections(st)), "sections_of_record": len(record),
        "superseded_not_read": sorted(sup), "scored_sections": len(cards), "apart_sections": len(apart),
        "trade_tables": tables, "reference_lines": cards, "apart": apart,
        "residual_by_unit_reference_kind_and_class": {u: {k: str(v) for k, v in m.items()} for u, m in sorted(by_unit_class.items())},
        "statement_totals_check": totals,
        "not_comparable": [{k: n.get(k) for k in ("report", "trade", "unit")} for n in st.get("not_comparable", [])],
        "pending_not_in_v10": list(pending) + [{"task": "statement V10 pending", "state": "as listed by T-609",
                                                "effect": p} for p in st.get("reports_pending", [])],
    }


# ================================================================================ markdown ========================
def _sc(c: dict) -> str:
    return " / ".join(f"{s} {c['status_count'][s]}" for s in STATUSES)


def _lines(t: dict) -> str:
    return ", ".join(f"{k} {v}" for k, v in t["lines_by_status"].items())


def markdown(sc: dict) -> str:
    L = ["# T-613 scorecard tables from statement V10 (generated; reference - engine, + = in the reference only)", "",
         f"Statement of record: `{sc['statement']['path']}` sha256 {sc['statement']['sha256'][:16]}... "
         f"({sc['statement']['schema']}). {sc['not_claimed']}.", "",
         f"Sections in the statement {sc['sections_in_statement']}; of record {sc['sections_of_record']} "
         f"(superseded, never read: {len(sc['superseded_not_read'])}); scored {sc['scored_sections']}, apart "
         f"{sc['apart_sections']}. Status per residual row (WORKFLOW_CONTROLS s.5, R-T613-1 (d)); a line is VERIFIED "
         "only when every row is VERIFIED and none HELD. HELD and UNKNOWN never count as 0 or as correct.", "",
         "## Trade tables (one unit and one reference kind each)", "",
         "| Trade | Unit | Ref. kind | Lines | Reference | Engine valued | Difference | ENGINE_RIGHT | ENGINE_WRONG | "
         "RULE_DIFFERENCE | HELD | TOLERANCE | UNRESOLVED | Lines by status | HELD rows at delta 0: bound |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in sc["trade_tables"]:
        b = t["by_class"]
        L.append(f"| {t['trade_code']} | {t['unit']} | {t['reference_kind']} | {len(t['sections'])} | "
                 f"{t['reference_total']} | {t['engine_valued']} | {t['difference']} | {b['ENGINE_RIGHT']} | "
                 f"{b['ENGINE_WRONG']} | {b['RULE_DIFFERENCE']} | {b['HELD']} | {b['TOLERANCE']} | {b['UNRESOLVED']} | "
                 f"{_lines(t)} | {t['held_bound_add'][0]} .. {t['held_bound_add'][1]} |")
    L += ["", "## Residual rows by evidence status per trade table: count / signed / gross |delta|", "",
          "| Trade | Unit | Ref. kind | " + " | ".join(STATUSES) + " |", "|---|---|---|" + "---|" * len(STATUSES)]
    for t in sc["trade_tables"]:
        L.append(f"| {t['trade_code']} | {t['unit']} | {t['reference_kind']} | " + " | ".join(
            f"{t['status_count'][s]} / {t['status_signed'][s]} / {t['status_gross'][s]}" for s in STATUSES) + " |")
    L += ["", "## Engine vs freelancer per reference line", "",
          "| Section | Trade | Unit | Reference | Engine valued | Difference | % of ref. | Line status | Rows by status |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in sc["reference_lines"]:
        pct = c["pct_of_reference"] if c["pct_of_reference"] is not None else "none"
        L.append(f"| {c['section_id']} | {c['trade_code']} | {c['unit']} | {c['reference_total']} | "
                 f"{c['engine_valued']} | {c['difference']} | {pct} ({c['pct_note']}) | {c['line_status']} | {_sc(c)} |")
    L += ["", "## Residual by unit, reference kind and class (scored lines; units and reference kinds never mixed)", "",
          "| Unit / ref. kind | " + " | ".join(CLASSES) + " |", "|---|" + "---|" * len(CLASSES)]
    for u, m in sc["residual_by_unit_reference_kind_and_class"].items():
        L.append(f"| {u} | " + " | ".join(m[k] for k in CLASSES) + " |")
    L += ["", "## Apart (never added)", "", "| Section | Kind | Unit | Difference | Line status |", "|---|---|---|---|---|"]
    for a in sc["apart"]:
        L.append(f"| {a['section_id']} | {a['kind']} | {a['unit']} | {a.get('difference', '-')} | "
                 f"{a.get('line_status', '-')} |")
    L += ["", "## Statement totals check", "", "| Totals entry | Section of record | Ref / engine / diff | By class |",
          "|---|---|---|---|"]
    for t in sc["statement_totals_check"]:
        L.append(f"| {t['totals_section']} | {t['section_of_record']} | {t['reference_engine_difference']} | "
                 f"{t['by_class']} |")
    L += ["", "## Not comparable (his NO_ROW or a different unit; no %, no delta)", ""]
    L += [f"- {n['report']}: {n['trade']} ({n['unit']})" for n in sc["not_comparable"]]
    L += ["", "## Pending, not in V10 (never folded in)", ""]
    L += [f"- {p['task']} ({p['state']}): {p['effect']}" for p in sc["pending_not_in_v10"]]
    return "\n".join(L) + "\n"


def dumps(sc: dict) -> str:
    return json.dumps(sc, indent=1, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    sc = build(load_statement())
    js, md = dumps(sc), markdown(sc)
    if "--check" in argv:
        ok = OUT_JSON.read_text() == js and OUT_MD.read_text() == md
        print("T-613 scorecard --check:", "IDENTICAL" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(js)
    OUT_MD.write_text(md)
    print(f"T-613 scorecard written: {len(sc['trade_tables'])} trade tables, {sc['scored_sections']} lines scored")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
