"""T-620: the reconciled-quantities statement V11 = the T-609 statement V10 (rebuilt read only and checked equal to its
committed JSON and markdown, sha256 pinned as T-613 reads it; every V10 key carried byte-equal, lists extended as a
prefix) + restated sections and beside blocks for the work MERGED after V10:

  T-600 r2 (column / beam pair residual: capacity terms as BOUNDS, SHORT UNRESOLVED per mark, proposals only),
  T-614 r2 (beam-end fix rows, unwired), T-619 (manifest V14 B10 range, unwired), T-608 (lift landing doors by trade),
  T-617 (landing head bounds), T-616 (lintel-implied -6 nr split), T-618 (finishes small residuals: FR-T618-1 ranges),
  T-621 (B3 floor tile row evidence), T-615 (Q-80 0.15 m black-block module; his m2 only),

and the F-T613-5 fix: a section's engine HELD-blank line count is ONE number with its cause (799 = 798 in the six
compared rebar groups + 1 tank line in the NOT_COMPARABLE block). No private input; no quantity moves; nothing released
(ARCH_TAKEOFF_V3.0.58 NOT RELEASED; V2.9 + route G unchanged).

R-T620-1 (proposed, every villa: the statement fold method):
  (a) FOLD ONLY MERGED WORK: a fold names its task and merge commit, and its source file must be in the tree; a task not
      in the merged register (READY, TODO, REJECTED) is refused, never folded;
  (b) A RESTATED SECTION KEEPS ITS ROWS: reference / engine / difference equal to its section of record; every row keeps
      every key byte-equal (name, class, delta, evidence ...) and may only ADD annotation keys from a named set, except
      where the fold itself is an evidence or class split and says so (T-621 evidence, T-616 split, apart);
  (c) A BOUND IS NOT A CLASS: a capacity term, a SHORT (balancing) term or a range end from a merged task is carried as
      an annotation or a beside bound, never as a statement row or class; a residual against a HELD range is a range
      (low OPEN where the HELD high is open), never a point quantity;
  (d) ONE HELD-BLANK COUNT: the section's engine_held.held_blank_lines must equal the rows' count plus the count of the
      NOT_COMPARABLE blocks of the same report, the cause named; otherwise refused;
  (e) EXACT RE-ADD: rows re-add to each class and the classes to the difference in every V11 section.

  python3 -I research/agents_t620/t620_build.py --write   # write out/
  python3 -I research/agents_t620/t620_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T609 = ROOT / "research/agents_t609"
if str(T609) not in sys.path:
    sys.path.insert(0, str(T609))
import t609_build as B609  # noqa: E402  (T-609, read only)

A = B609.A
Z = A.Z
D = Decimal
StatementError = Z.StatementError

OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T620.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T620.md"
V10_SHA256 = "dc2b25d65003e383d9aee2d73da609891e35d28d780744b65702638bf8d665b7"   # = T-613's pin of statement V10

SRC = {
    "T-600": ROOT / "research/agents_t600/out/T600_PAIR_RESIDUAL.json",
    "T-608": ROOT / "research/agents_t608/out/T608_SCOPE_TABLE.json",
    "T-614": ROOT / "research/agents_t614/out/T614_BEAM_END_CENSUS.json",
    "T-615": ROOT / "research/agents_t615/out/SUMMARY_T615.json",
    "T-616": ROOT / "research/agents_t616/out/T616_RESIDUAL.json",
    "T-617": ROOT / "research/agents_t617/out/T617_HEAD_BOUNDS.json",
    "T-618": ROOT / "research/agents_t618/out/T618_RESIDUALS.json",
    "T-619": ROOT / "research/agents_t619/out/WIRING_MANIFEST_V14.json",
    "T-621": ROOT / "research/agents_t621/out/T621_ROW_EVIDENCE.json",
}
# (a) the merged register: task -> engine merge / push commit and the Checker Gate A time (BOARD.md, agents/control)
MERGED = {
    "T-600": ("61fef828", "Verifier 2026-11-08T01:54Z, MERGED r2"),
    "T-608": ("3c3aa2f8", "Verifier 2026-11-07T23:57Z, MERGED"),
    "T-614": ("a7f1f3af", "Verifier 2026-11-08T05:59Z, MERGED r2"),
    "T-615": ("b8265219", "Verifier 2026-11-08T08:21Z, MERGED"),
    "T-616": ("17559e1b", "Verifier 2026-11-08T01:00Z, MERGED"),
    "T-617": ("44ee93d5", "Verifier 2026-11-08T04:58Z, MERGED"),
    "T-618": ("85a473ce", "Verifier 2026-11-08T06:02Z, MERGED"),
    "T-619": ("e8709e09", "Verifier 2026-11-08T08:01Z, MERGED"),
    "T-621": ("e8709e09", "Verifier 2026-11-08T08:01Z, MERGED"),
}

# Checker verdict texts quoted in part from BOARD.md (agents/control); nothing else is read.
V600 = ("Checker 2026-11-08T01:54Z (T-600 r2 Gate A, engine push 61fef828): closure re-added GF terms sum 0.740916, 1F "
        "1.208362 = T - J (3.022166 - 2.28125; 1.593362 - 0.385); B27 node 0.2433 vs 0.243784 AGREE; 'Statement keeps "
        "2.248826 m3 UNRESOLVED; capacity terms are bounds, not verified quantities'; WHO IS RIGHT: GF B2 / CB5 / CB7 at "
        "REC columns RULE_DIFFERENCE, at HELD columns HELD; every other mark UNRESOLVED")
V614 = ("Checker 2026-11-08T05:59Z (T-614 r2 Gate A, engine push a7f1f3af): own re-measure FR-T614-3 +0.002308, FR-T614-4 "
        "+0.037500, FR-T614-5 +0.000878 m3 AGREE; FR-T614-1 / -2 cited (03:55 AGREE); total +0.061576 m3 ENGINE_WRONG "
        "OMISSION (research, unwired); col 2 west 0.00454 m2 HELD (bound 0.003405 m3); FR-T610-3 withdrawal AGREE; GF CB4 "
        "BAND0021.1.r2 +0.01355 m3 possible double billing named")
V616 = ("Checker 2026-11-08T01:00Z (T-616 Gate A, merge 17559e1b): own recount of his 54 deducted openings AGREE; P-1F-01, "
        "D-GF-05 own reads AGREE; W17 sagitta 0.711 m > 0.20 band: no straight stock piece, ENGINE_RIGHT AGREE; counts "
        "carry ENGINE_RIGHT bound 3 .. 5 / UNRESOLVED 2 .. 4 named; established basis ENGINE_RIGHT -2 .. -4 / UNRESOLVED "
        "-4 .. -2 (designer heads D-45 / DCR-3); note: the statement should carry P-GF-01 in one group only")
V618 = ("Checker 2026-11-08T06:02Z (T-618 Gate A, engine push 85a473ce): stair skirting UNRESOLVED as a range by stair "
        "(the 0.710951 point refused, R-T618-1 (a)); rails (-inf, 0.226] with RL-09 HELD inside the scope; door steps "
        "CANDIDATE RULE_DIFFERENCE, UNRESOLVED (no ids on his rows); curved room and corridor: every uniform offset "
        "refuted, UNRESOLVED (his sides needed); ST-02 landing 1.25 lm ENGINE_RIGHT (own read); FR-T618-1 / -2 accepted")
V621 = ("Checker 2026-11-08T08:01Z (T-621 Gate A, engine push e8709e09): OWN RE-MEASURE (own ezdxf + shapely polygonization "
        "of layer-1 wall faces, worker handles not used)")
V621_ROWS = {
    6: V621 + ": GF DEWANEYA 4.000 x 6.300 - (1.10^2 - pi x 1.10^2 / 4) = 24.940332 m2 AGREE row 6",
    17: V621 + ": 1F west bed own closed face 19.050000 m2 (4.25 x 4.50 box, two column notches 0.075) AGREE row 17",
    19: V621 + ": 2F MAID R. 3.000 x 6.450 = 19.350 m2 AGREE row 19",
}
V621_LINE = ("Checker 2026-11-08T08:01Z (T-621 Gate A) PARTIALLY VERIFIED 3 / 5 of the Checker set: rows 6 / 17 / 19 VERIFIED "
             "by own re-measure; GF-OPEN.full 147.657717 and 1F-LIV.floor_printed 38.5855 NOT re-measured (rows 2-5, 9, "
             "11-13 stay DRAWING-CONFIRMED, worker); row 0 NOT_REMEASURED, never 0; floor tile line stays PARTIALLY VERIFIED")
V608 = ("Checker 2026-11-07T23:57Z (T-608 Gate A, merge 3c3aa2f8): own P7757 read LIFT_LANDING_DOOR x 3 AGREE "
        "(DRAWING-CONFIRMED); ARCH.PASSAGE 9 - 3 = 6 pcs AGREE; landing-door supply ENGINE_OMISSION HELD-blank x 3; his "
        "2.40 m UNRESOLVED (his side), ours HELD correct")
V617 = ("Checker 2026-11-08T04:58Z (T-617 Gate A, merge 44ee93d5): own ST7757 read: heads bounded above GF 3.70 / 1F 3.40 "
        "/ 2F 3.75 (r est.); low end HELD; 0.000 m2 change on 1F-13 / 2F-01 / GF-08; FR-T617-1 band 0.59 / 0.59 / 0.24 m2 "
        "AGREE; his 2.40 UNRESOLVED")
V615 = ("Checker 2026-11-08T08:21Z (T-615 Gate A, engine push b8265219): module 1 / (0.40 x 0.20) = 12.5 / m2; 15 walls "
        "175.871 m2 -> units 2,198.3875 (low 2,194.1375) AGREE; no drawing prints a 15 cm face (nothing to report against "
        "Q-80); freelancer m2 only: UNRESOLVED")

T600_TERMS = ("BESIDE", "BEYOND", "CARRIER_NODE", "OUTSIDE_SET_HELD", "OUTSIDE_SET_OPEN", "OVERLAP_CROSSING",
              "OVERLAP_REPEAT", "UNCOVERED", "UNRESOLVED_SHORT")
# (b) annotation keys a restated row may add; every other key stays byte-equal
ANNOTATIONS = ("t600_v11", "t618_v11", "range_v11", "range_basis_v11", "evidence_source_v11", "evidence_v11")
EVIDENCE_KEYS = ("evidence_status", "evidence_verdict")   # T-621 only (an evidence fold)
NEW_REPORTS = ["T-600 r2", "T-608", "T-614 r2", "T-615", "T-616", "T-617", "T-618", "T-619", "T-621"]
PENDING = [
    "T-622 (B4 wall tile 47 UNKNOWN rows to evidence: READY, not merged at the T-620 claim 2026-11-08T09:01Z)",
    "T-623 / T-624 / T-625 / T-626 / T-627 / T-628 (TODO at the claim: B10 rows, beam-end open items, B3 carry-forward, "
    "B8, B12 m2, B10 footing / lift walls)",
    "fix rows not wired in the candidate (beside only): FR-T606-1, FR-T608-1 / -2, FR-T610-1 / -2 / -4, FR-T614-1 .. -5 "
    "(+ H1 HELD), FR-T615-1 .. -7, FR-T616-1 .. -3, FR-T617-1, FR-T618-2",
    "T-180 P02 GF (not read) and the B10 per-row re-measure (T-623)",
]
LESSONS_ADOPTED = [
    "T-600 r2 (Checker ADOPTED as written s.9): a carrier node is counted once across marks; a balancing SHORT term "
    "is never a cause and never a class",
    "T-614 r2 (Checker ADOPT): billing of a piece is read from the line's own measured extent and named adds, never "
    "from a plan model inside a tolerance larger than the piece",
    "T-618 (Checker ADOPT): a residual against a HELD range is a range by group; read a reference's row structure before "
    "choosing the compared element",
    "T-616 (Checker PROPOSED): never pick an identity among equal widths",
    "T-613 F-T613-5 (this task): one HELD-blank count per section, the NOT_COMPARABLE part named",
]


# ================================================================================ inputs ===========================
def require_merged(task: str, merged: dict = MERGED) -> tuple[str, str]:
    """(a) a fold from a task that is not MERGED is refused."""
    if task not in merged:
        raise StatementError(f"{task}: not in the merged register: a fold from an unmerged task is refused (R-T620-1 (a))")
    p = SRC.get(task)
    if p is None or not p.exists():
        raise StatementError(f"{task}: merged source file absent from the tree: refused")
    return merged[task]


def load_sources(merged: dict = MERGED) -> dict:
    out = {}
    for t in SRC:
        require_merged(t, merged)
        out[t] = json.loads(SRC[t].read_text(encoding="utf-8"))
    return out


def v10_statement() -> dict:
    raw = B609.JSON_OUT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V10_SHA256:
        raise StatementError("statement V10 sha256 differs from the pin (T-613 reads the same pin)")
    st10 = B609.build()
    if st10 != json.loads(raw) or B609.to_markdown(st10) != B609.MD_OUT.read_text(encoding="utf-8"):
        raise StatementError("T-609 statement V10 does not reproduce: rebuild it before T-620")
    return st10


LEVELS10 = ("sections", "sections_v5", "sections_v6", "sections_v7", "sections_v8", "sections_v9", "sections_v10")
SUP10 = ("supersedes_v7", "supersedes_v8", "supersedes_v9", "supersedes_v10")


def all_sections(st: dict, levels: tuple = LEVELS10) -> dict:
    out = {}
    for lv in levels:
        for c in st.get(lv, []):
            if c["section_id"] in out:
                raise StatementError(f"{c['section_id']}: twice")
            out[c["section_id"]] = c
    return out


def supersession(st: dict, keys: tuple = SUP10) -> dict:
    sup = {}
    for k in keys:
        sup.update({a: b for a, b in st.get(k, {}).items() if not a.startswith("beside")})
    return sup


def of_record(st: dict, sid: str) -> dict:
    secs, sup = all_sections(st), supersession(st)
    if sid in sup:
        raise StatementError(f"{sid}: superseded by {sup[sid]}, not a section of record")
    return secs[sid]


# ================================================================================ (b) (e) guards ===================
def check_rows_kept(old: dict, new: dict, extra: tuple = ()) -> None:
    """(b) every row keeps every key byte-equal; only annotation keys (and `extra`) may be added."""
    if len(old["rows"]) != len(new["rows"]):
        raise StatementError(f"{new['section_id']}: row count changed in a restatement")
    allowed = set(ANNOTATIONS) | set(extra)
    for o, n in zip(old["rows"], new["rows"]):
        for k, v in o.items():
            if k in extra:
                continue
            if json.dumps(n.get(k), sort_keys=True) != json.dumps(v, sort_keys=True):
                raise StatementError(f"{new['section_id']}: row '{o['name'][:50]}' key {k} changed (R-T620-1 (b))")
        added = set(n) - set(o)
        if added - allowed:
            raise StatementError(f"{new['section_id']}: row '{o['name'][:50]}' adds {sorted(added - allowed)}")


def check_totals(old: dict, new: dict) -> None:
    for k in ("reference_total", "engine_valued", "difference", "unit"):
        if str(old.get(k)) != str(new.get(k)):
            raise StatementError(f"{new['section_id']}: {k} {new.get(k)} != section of record {old.get(k)}")
    readd(new)


def readd(sec: dict) -> None:
    """(e) rows re-add to each class and the classes to the difference."""
    by = {c: D(0) for c in sec["by_class"]}
    for r in sec["rows"]:
        if r["class"] not in by:
            raise StatementError(f"{sec['section_id']}: row class {r['class']!r} is not a statement class (R-T620-1 (c))")
        by[r["class"]] += D(r["delta"])
    for c, v in by.items():
        if v != D(sec["by_class"][c]):
            raise StatementError(f"{sec['section_id']}: rows re-add to {c} {v} != {sec['by_class'][c]}")
    if sum(by.values()) != D(sec["difference"]):
        raise StatementError(f"{sec['section_id']}: classes do not re-add to the difference")


def refuse_bound_as_row(sec: dict) -> None:
    """(c) a T-600 capacity / SHORT term or a range end never enters as a row or a class."""
    for r in sec["rows"]:
        if r["class"] in T600_TERMS or r.get("t600_term") or str(r.get("source", "")).startswith("T-600 term"):
            raise StatementError(f"{sec['section_id']}: T-600 term '{r['name'][:50]}' entered as a row / class (R-T620-1 (c))")
        rg = r.get("range_v11")
        if rg is not None and D(rg[1]) != D(r["delta"]):
            raise StatementError(f"{sec['section_id']}: row delta is not the range end it annotates")


def _restate(old: dict, sid_new: str, task: str) -> dict:
    require_merged(task)
    new = copy.deepcopy(old)
    new["section_id"] = sid_new
    new["restates"] = old["section_id"]
    new["fold_v11"] = f"{task} ({MERGED[task][0]})"
    return new


def _row(sec: dict, prefix: str, exact: bool = False) -> tuple[int, dict]:
    hit = [(i, r) for i, r in enumerate(sec["rows"]) if (r["name"] == prefix if exact else r["name"].startswith(prefix))]
    if len(hit) != 1:
        raise StatementError(f"{sec['section_id']}: {len(hit)} rows start with {prefix!r}")
    return hit[0]


# ================================================================================ restated sections ================
def t621_floor_tile(st10: dict, d621: dict) -> tuple[dict, list]:
    """T-621 evidence fold: classes and deltas unchanged; evidence per row from the merged ledger + Checker re-measure."""
    if d621["statement"]["sha256"] != V10_SHA256 or d621["section"] != "T-553/floor-tile":
        raise StatementError("T-621 was built on another statement / section")
    old = of_record(st10, "T-553/floor-tile")
    new = _restate(old, "T-553/floor-tile@V11", "T-621")
    moves = []
    if len(d621["rows"]) != len(new["rows"]):
        raise StatementError("T-621 row count differs from the section of record")
    for i, (r, e) in enumerate(zip(new["rows"], d621["rows"])):
        if e["row"] != i or e["name"] != r["name"] or e["class"] != r["class"] or D(e["delta"]) != D(r["delta"]):
            raise StatementError(f"T-621 row {i} does not match the section row (name / class / delta)")
        was = r.get("evidence_status") or r.get("verification")
        if i in V621_ROWS:
            if e["evidence_status"] != "DRAWING_CONFIRMED":
                raise StatementError(f"T-621 row {i}: Checker re-measure on a row the worker did not confirm")
            r["evidence_status"], r["evidence_verdict"] = "CHECKER_VERIFIED", V621_ROWS[i]
        elif e["evidence_status"] == "DRAWING_CONFIRMED":
            hd = [h for m in e["measures"] for h in m.get("handles", [])]
            r["evidence_status"] = "DRAWING_CONFIRMED"
            r["evidence_verdict"] = (f"T-621 worker handle chain ({len(hd)} handles, T621_DRAWN.json; kind {e['kind']}); "
                                     "status accepted at Checker Gate A 2026-11-08T08:01Z, quantity not re-measured by "
                                     "the Checker")
        elif e["evidence_status"] == "NOT_REMEASURED":
            r["evidence_v11"] = ("NOT_REMEASURED (T-621 row 0: round-stair footprint 6.124412 m2; closure 6.124432 "
                                 "beside, never a measure): evidence unchanged, never 0; carried forward (T-625)")
        else:
            raise StatementError(f"T-621 row {i}: unknown evidence {e['evidence_status']!r}")
        r["evidence_source_v11"] = f"T-621 ({MERGED['T-621'][0]})"
        now = r.get("evidence_status") or r.get("verification")
        if now != was:
            moves.append({"section_id": new["section_id"], "row": i, "name": r["name"][:80], "from": was[:40],
                          "to": now, "class": r["class"], "delta": r["delta"], "unit": new["unit"]})
    new["verification"] = V621_LINE
    new["change_note_v11"] = ("evidence only (classes and deltas unchanged): rows 6 / 17 / 19 VERIFIED by the Checker's own "
                              "re-measure, 37 rows DRAWING-CONFIRMED by the worker's handle chains, row 0 NOT_REMEASURED")
    check_rows_kept(old, new, extra=EVIDENCE_KEYS)
    check_totals(old, new)
    return new, moves


def t618_stairs(st10: dict, d618: dict) -> dict:
    """FR-T618-1: the three stair UNRESOLVED rows are upper ends of ranges (a residual against a HELD range)."""
    old = of_record(st10, "T-574/skirting-stairs@V8")
    new = _restate(old, "T-574/skirting-stairs@V11", "T-618")
    ps = {p["stair"]: p for p in [r for r in d618["rows"] if r["row"] == "stair skirting"][0]["per_stair"]}
    _, wind = _row(new, "ST-01 main: winder corner")
    w_lo = D(wind["bound"][0])
    spec = [("ST-03 entrance (E1): his entrance row", "ST-03 entrance (E1)", D(0)),
            ("ST-01 main: his main-stair row", "ST-01 main", w_lo),
            ("ST-02 round (inner): his inner-stair row", "ST-02 round (inner)", D(0))]
    highs = D(0)
    by_stair = {}
    for prefix, stair, held_apart in spec:
        _, r = _row(new, prefix)
        lo, hi = ps[stair]["range_his_minus_ours"]
        if D(hi) - held_apart != D(r["delta"]):
            raise StatementError(f"{stair}: T-618 range end {hi} - {held_apart} != row delta {r['delta']}")
        lo_v = None if lo is None else Z.s(D(lo) - held_apart)
        r["range_v11"] = [lo_v, r["delta"]]
        r["range_basis_v11"] = (f"FR-T618-1 (T-618 {MERGED['T-618'][0]}): his - ours over the HELD flight-form bounds "
                                f"{ps[stair]['held_bounds'][0]} is ({'OPEN' if lo is None else lo} .. {hi}]"
                                + (f"; the winder corner (HELD row, low {wind['bound'][0]}) is apart in this section since "
                                   f"V8, so this row's end is {hi} - {wind['bound'][0]} = {r['delta']}" if held_apart else "")
                                + "; the point is the range's upper end, never a quantity (R-T618-1 (a))")
        highs += D(r["delta"])
        by_stair[stair] = [lo_v, r["delta"]]
    if highs != D(old["by_class"]["UNRESOLVED"]):
        raise StatementError("stair UNRESOLVED rows do not re-add to the section UNRESOLVED")
    t618_pt = D([r for r in d618["rows"] if r["row"] == "stair skirting"][0]["range_his_minus_ours"][1])
    if highs + w_lo != t618_pt:
        raise StatementError("T-618 0.710951 does not reconcile with the V8 rows + the winder low bound")
    new["residual_range_v11"] = {
        "UNRESOLVED": ["OPEN", Z.s(highs)], "by_stair": by_stair,
        "t618_statement_row": Z.s(t618_pt),
        "reconciles": f"{Z.s(highs)} (V8 rows) + {wind['bound'][0]} (winder corner HELD at its low end since V8) = "
                      f"{Z.s(t618_pt)} (the V6 figure T-618 names); the point is refused as a quantity",
        "landing_st02": "ST-02 landing walled 1.25 lm = engine RS-LD: ENGINE_RIGHT (Checker own read, T-618)",
        "verdict": V618}
    refuse_bound_as_row(new)
    check_rows_kept(old, new)
    check_totals(old, new)
    return new


def t618_rails(st10: dict, d618: dict) -> dict:
    old = of_record(st10, "T-578/rails")
    new = _restate(old, "T-578/rails@V11", "T-618")
    src = [r for r in d618["rows"] if r["row"] == "rails"][0]
    _, r = _row(new, "unexplained: his 18.95 - (RL-05 16.324 + RL-06 2.400)")
    lo, hi = src["range_his_minus_ours"]
    if lo is not None or D(hi) != D(r["delta"]):
        raise StatementError("rails: T-618 range does not end at the row delta")
    r["range_v11"] = [None, r["delta"]]
    r["range_basis_v11"] = (f"FR-T618-1 (T-618 {MERGED['T-618'][0]}): under {src['hypothesis']}, RL-09 "
                            f"{src['held_in_scope']['RAIL:RL-09']} HELD inside the scope: his - ours is (OPEN .. {hi}]; "
                            "0.226 is the upper end, never a quantity; closes it: " + src["closes_it"][:160])
    new["residual_range_v11"] = {"UNRESOLVED": ["OPEN", r["delta"]], "verdict": V618}
    refuse_bound_as_row(new)
    check_rows_kept(old, new)
    check_totals(old, new)
    return new


def _t618_cause(src: dict) -> dict:
    return {"task": f"T-618 ({MERGED['T-618'][0]})", "verdict": src["verdict"],
            "readings": {t["reading"][:70]: t["status"] for t in src["readings_tested"]},
            "cause": (src.get("cause") or src.get("candidate_cause") or "")[:300],
            "closes_it": src["closes_it"][:240], "class_unchanged": "UNRESOLVED (no reading reproduces his row)"}


def t618_room(st10: dict, d618: dict) -> dict:
    old = of_record(st10, "T-574/skirting-room@V10")
    new = _restate(old, "T-574/skirting-room@V11", "T-618")
    rows = {r["row"]: r for r in d618["rows"]}
    for prefix, key in (("1F curved east bed room with its lobby (his 'bed room 1'): drawn outline", "1F curved"),
                        ("2F corridor = stair-room lobby + arrival (T-443 children; parent NOT_APPLICABLE): his outline",
                         "2F corridor")):
        _, r = _row(new, prefix)
        if D(rows[key]["dP"]) != D(r["delta"]):
            raise StatementError(f"{key}: T-618 dP {rows[key]['dP']} != row delta {r['delta']}")
        r["t618_v11"] = _t618_cause(rows[key])
    check_rows_kept(old, new)
    check_totals(old, new)
    return new


def t618_door_steps(st10: dict, d618: dict) -> dict:
    old = of_record(st10, "T-577/marble-lm@V10")
    new = _restate(old, "T-577/marble-lm@V11", "T-618")
    src = [r for r in d618["rows"] if r["row"] == "door steps"][0]
    _, r = _row(new, "EXT: his 6 door-step pieces 7.7 lm")
    if D(src["residual"]) != D(r["delta"]):
        raise StatementError("door steps: T-618 residual != row delta")
    c = _t618_cause(src)
    c.update({"candidate_parts_lm": src["candidate_parts"], "candidate_class": "RULE_DIFFERENCE (proposal, not applied)",
              "why_not_established": src["why_not_established"][:200]})
    r["t618_v11"] = c
    check_rows_kept(old, new)
    check_totals(old, new)
    return new


def t616_lintel(st10: dict, d616: dict) -> tuple[dict, list]:
    """T-616 split of the APART implied count -6 nr: ENGINE_RIGHT at its firm magnitude 2 + UNRESOLVED 4 (of which up
    to 2 more ENGINE_RIGHT); the class range is carried, never a point beyond the firm part."""
    old = of_record(st10, "T-571/lintel-count-implied@V8")
    sm = d616["summary"]["statement_sign_his_minus_ours"]
    er, un, tot = [D(x) for x in sm["ENGINE_RIGHT"]], [D(x) for x in sm["UNRESOLVED"]], D(sm["total"])
    if tot != D(old["difference"]) or D(d616["theirs_nr"]) != D(old["reference_total"]) or \
            D(d616["ours_nr"]) != D(old["engine_valued"]):
        raise StatementError("T-616 totals differ from the section of record")
    if er[0] + un[1] != tot or er[1] + un[0] != tot:
        raise StatementError("T-616 class ranges do not pair to the total")
    firm = max(er)            # -2: ENGINE_RIGHT in every admissible set
    rest = tot - firm         # -4
    new = _restate(old, "T-571/lintel-count-implied@V11", "T-616")
    req = d616["requirement"]
    unres = sorted(k for k, v in req.items() if v["decision"] == "UNRESOLVED")
    new["rows"] = [
        {"name": ("ENGINE_RIGHT at its firm magnitude: ours-only openings that need a lintel in every admissible "
                  f"pairing ({', '.join(d616['ours_only_firm'])} firm; REQUIRED where the head is below the soffit) net "
                  "of W17 (+1: his 1F EXT 3.15 piece, no straight stock piece over the curved band, sagitta 0.711 m)"),
         "class": "ENGINE_RIGHT", "delta": Z.s(firm), "unit": "nr", "evidence_status": "PARTIALLY_VERIFIED",
         "evidence_verdict": V616, "source": f"T-616 R-T616-1 summary ({MERGED['T-616'][0]})",
         "range_of_class": [Z.s(er[0]), Z.s(er[1])]},
        {"name": ("UNRESOLVED: ours-only openings whose member over the head is not established (designer heads D-45 / "
                  f"DCR-3: {', '.join(unres)}) and the 1F 3-of-8 set membership (T-571 list, not re-measured); of "
                  f"which 0 .. {Z.s(abs(er[0] - firm))} more may be ENGINE_RIGHT"),
         "class": "UNRESOLVED", "delta": Z.s(rest), "unit": "nr", "evidence_status": "PARTIALLY_VERIFIED",
         "evidence_verdict": V616, "source": f"T-616 R-T616-1 summary ({MERGED['T-616'][0]})",
         "range_split": {"ENGINE_RIGHT": [Z.s(er[0] - firm), "0"], "UNRESOLVED": [Z.s(un[0]), Z.s(un[1])]}},
    ]
    new["by_class"] = {c: "0" for c in old["by_class"]}
    new["by_class"]["ENGINE_RIGHT"], new["by_class"]["UNRESOLVED"] = Z.s(firm), Z.s(rest)
    new["by_class_gross_abs"] = {c: Z.s(abs(D(v))) for c, v in new["by_class"].items()}
    new["class_range_v11"] = {"ENGINE_RIGHT": [Z.s(er[0]), Z.s(er[1])], "UNRESOLVED": [Z.s(un[0]), Z.s(un[1])],
                              "pairs": f"ENGINE_RIGHT {Z.s(er[0])} with UNRESOLVED {Z.s(un[1])}, or {Z.s(er[1])} with "
                                       f"{Z.s(un[0])}: every pairing re-adds to {Z.s(tot)}"}
    new["rows_v8_by_opening"] = ("the V8 per-opening pairing (T-571) is not carried: T-616 shows L-GF-01 is his shaft "
                                 "1.00 and P-GF-01 is ours-only; identities among equal widths are never picked; "
                                 "P-GF-01 is carried in ONE group only (GF 15 cm / 0.20 GF-W14 give the same bound, Checker "
                                 "note)")
    new["verification"] = V616
    new["change_note_v11"] = ("the V8 rows were stamped on the T-571 per-opening pairing, which T-616 (Checker AGREE, own "
                              "recount of his 54) shows wrong (L-GF-01 is his shaft 1.00; P-GF-01 ours-only): restated "
                              "by group, ENGINE_RIGHT -2 firm + UNRESOLVED -4 (ranges carried), both PARTIALLY VERIFIED "
                              "(counts and W17 re-measured; the member over 2 .. 4 heads not established)")
    check_totals(old, new)
    moves = [{"section_id": new["section_id"], "from": "UNRESOLVED", "to": "ENGINE_RIGHT", "delta": Z.s(firm),
              "unit": "nr", "apart": True, "why": "T-616 firm magnitude (every admissible pairing)"}]
    return new, moves


def _t600_block(d600: dict, storey: str) -> dict:
    s = d600["storeys"][storey]
    terms = s["by_class_m3"]
    if sum(D(v) for v in terms.values()) != D(s["residual_m3"]) or \
            D(s["through_support_T_m3"]) - D(s["joint_head_J_m3"]) != D(s["residual_m3"]):
        raise StatementError(f"T-600 {storey}: terms / T - J do not re-add to R")
    props = []
    for m, v in s["beam_marks"].items():
        if v["proposal"].startswith(("PER-MARK", "CONDITIONAL")):
            props.append({"mark": m, "basis": v["proposal"].split(":")[0], "short_m3": v["short_bounds_m3"],
                          "T_m3": v["T_m3"], "per_column": [{"column": c["column"], "kind": c["kind"],
                                                             "proposal": c["proposal"].split(":")[0]}
                                                            for c in v.get("per_column", [])]})
    return {"task": f"T-600 r2 ({MERGED['T-600'][0]})", "storey": storey,
            "through_support_T_m3": s["through_support_T_m3"], "joint_head_J_m3": s["joint_head_J_m3"],
            "residual_R_m3": s["residual_m3"], "statement_pair_residual_m3": s["statement_pair_residual_m3"],
            "b7_folded_m3": s["b7_untraced_folded_m3"],
            "capacity_terms_m3_bounds_not_classes": {k: v for k, v in terms.items() if k != "UNRESOLVED_SHORT"},
            "unresolved_short_m3": terms["UNRESOLVED_SHORT"],
            "short_bounds_by_mark_m3": {m: v["short_bounds_m3"] for m, v in sorted(s["beam_marks"].items())},
            "proposals_only": props,
            "class_of_record": "UNRESOLVED unchanged: capacity terms are bounds, SHORT is not a cause (R-T600-1 .. 3 "
                               "r2); proposals are per mark, never moved into a class here",
            "verdict": V600}


def t600_beams(st10: dict, d600: dict) -> dict:
    old = of_record(st10, "T-545/beams@V10")
    new = _restate(old, "T-545/beams@V11", "T-600")
    gf, f1 = _t600_block(d600, "GF"), _t600_block(d600, "1F")
    _, r_gf = _row(new, "GF: THROUGH_SUPPORT residual")
    _, r_b7 = _row(new, "GF: UNTRACED -> GF B7")
    _, r_1f = _row(new, "1F: THROUGH_SUPPORT residual")
    _, r_2f = _row(new, "2F: THROUGH_SUPPORT", exact=True)
    if D(r_gf["delta"]) != D(gf["statement_pair_residual_m3"]) or D(r_b7["delta"]) != D(gf["b7_folded_m3"]) or \
            D(r_gf["delta"]) + D(r_b7["delta"]) != D(gf["residual_R_m3"]):
        raise StatementError("T-600 GF: pair 0.620464 + B7 0.120452 != R")
    if D(r_1f["delta"]) != D(f1["residual_R_m3"]):
        raise StatementError("T-600 1F: R != row")
    if D(r_2f["delta"]) != D(d600["storey_2F"]["residual_m3"]):
        raise StatementError("T-600 2F: residual != row")
    r_gf["t600_v11"] = gf
    r_b7["t600_v11"] = {"task": gf["task"], "traced": "folded into the GF pair residual R 0.740916 = 0.620464 + "
                        "0.120452 (B7 group: capacity 0.532430, T 0.354452, SHORT 0.177978 by mark); class UNRESOLVED "
                        "unchanged", "verdict": V600}
    r_1f["t600_v11"] = f1
    r_2f["t600_v11"] = {"task": gf["task"], "storey": "2F", "column_partner": d600["storey_2F"]["column_partner"],
                        "source": d600["storey_2F"]["source"][:300],
                        "class_of_record": "UNRESOLVED unchanged (statement keeps 2.248826 m3 UNRESOLVED)"}
    unres3 = D(r_gf["delta"]) + D(r_1f["delta"]) + D(r_2f["delta"])
    if unres3 != D("2.248826"):
        raise StatementError(f"the three THROUGH_SUPPORT residuals {unres3} != 2.248826 m3 (T-600 verdict)")
    new["pair_residual_v11"] = {"through_support_unresolved_m3": Z.s(unres3), "plus_b7_traced_m3": r_b7["delta"],
                                "section_unresolved_m3": old["by_class"]["UNRESOLVED"],
                                "note": "2.248826 (GF 0.620464 + 1F 1.208362 + 2F 0.42) stays UNRESOLVED; with B7 "
                                        "0.120452 = the section's UNRESOLVED 2.369278"}
    new["change_note_v11"] = ("annotations only: T-600 r2 bounds and proposals on the GF / 1F / 2F THROUGH_SUPPORT "
                              "residual rows and the B7 row; classes, deltas and evidence unchanged; T-614 / T-619 beside")
    refuse_bound_as_row(new)
    check_rows_kept(old, new)
    check_totals(old, new)
    return new


# ================================================================================ beside blocks ====================
def t614_beside(d614: dict) -> dict:
    fr = [{"id": f["id"], "storey": f["storey"], "mark": f["mark"], "change_m3": Z.s(D(str(f["change_m3"])))}
          for f in d614["fix_rows"]]
    tot = sum((D(x["change_m3"]) for x in fr), D(0))
    if tot != D("0.061576"):
        raise StatementError(f"T-614 fix rows {tot} != 0.061576 m3 (Checker)")
    return {"block": "T-614 r2 beam-end pieces (beside T-545/beams@V11; unwired)", "task": f"T-614 r2 ({MERGED['T-614'][0]})",
            "fix_rows": fr, "total_m3": Z.s(tot), "class_proposed": "ENGINE_WRONG OMISSION (Checker own hand calc)",
            "held": [{"id": h["id"], "storey": h["storey"], "bound_m3": ["0", Z.s(D(str(h["bound_m3"])))],
                      "state": h["state"][:120]} for h in d614["held_rows"]],
            "withdrawn": "FR-T610-3 (CB8 bills no B27 zone; 0.000 instead of -0.000692 m3)",
            "open": "GF CB4 BAND0021.1.r2 +0.01355 m3 possible double billing (T-624)",
            "statement_effect": "none: the candidate is unchanged (V3.0.58 NOT RELEASED); engine valued 66.321054 stays",
            "verdict": V614}


def t619_beside(d619: dict) -> dict:
    b = d619["beam_b10"]
    v14 = b["STR.CONC.BEAM|m3"]["v14"]
    lo, hi = D(v14["released"]), D(v14["released"]) + D(b["fix_rows"][0]["range"]["high"]) - \
        D(b["fix_rows"][0]["range"]["low"])
    if Z.s(lo) != "66.392081" or Z.s(hi) != "66.393376":
        raise StatementError(f"T-619 B10 range {lo} .. {hi} != 66.392081 .. 66.393376")
    return {"block": "T-619 manifest V14 (beside; not wired, no class moves)", "task": f"T-619 ({MERGED['T-619'][0]})",
            "STR.CONC.BEAM_m3": {"v13_released": b["STR.CONC.BEAM|m3"]["v13"]["released"],
                                 "v14_released_if_wired": [Z.s(lo), Z.s(hi)],
                                 "v14_held": [v14["held_low"], v14["held_high"]], "hand": b["hand"]},
            "ARCH.PASSAGE_pcs": {"v13": d619["passage"]["ARCH.PASSAGE|pcs"]["v13"]["released"],
                                 "v14": d619["passage"]["ARCH.PASSAGE|pcs"]["v14"]["released"]},
            "DOOR.LIFT_LANDING": d619["lift_landing_door"]["note"],
            "held_not_wired": [h["id"] + " " + h["bound_m3"] + " m3" for h in d619["held_not_wired"]],
            "findings": d619["findings"],
            "statement_effect": "none: the reference lines compare the candidate as built (V3.0.58); the V14 figures "
                                "are what Gate B would wire, a range, never a point"}


def t608_beside(d608: dict) -> dict:
    tab = {}
    for r in d608["rows"]:
        e = r.get("expected") or {}
        tab.setdefault(r["family"], {})[r["storey"]] = f"{e.get('status')} / {r['verdict']}"
    return {"block": "T-608 lift landing doors by trade (beside the NOT_COMPARABLE T-568/lift-landings block)",
            "task": f"T-608 ({MERGED['T-608'][0]})", "by_family_storey": tab,
            "label_restated": "F-T608-1: the 3 lift landing openings are 'trade HELD (no printed note)', not 'excluded: "
                              "lift supply' (label only, no quantity)",
            "findings": [f["id"] + ": " + f["what"][:200] for f in d608["findings"]],
            "summary": d608["summary"], "verdict": V608}


def t617_beside(d617: dict) -> dict:
    heads = {r["storey"]: {"opening": r["opening"], "high_at_drawn_buildup_m": r["head"]["high_at_drawn_buildup"],
                           "low": "HELD (printed nowhere; never a default)",
                           "always_plastered_above_head_m2": r["q72_plaster_for_T558"]["always_plastered_above_head_m2"]}
             for r in d617["rows"]}
    return {"block": "T-617 lift landing head bounds (beside; 0.000 m2 change on 1F-13 / 2F-01 / GF-08)",
            "task": f"T-617 ({MERGED['T-617'][0]})", "heads": heads, "summary": d617["summary"],
            "his_2_40": "UNRESOLVED (admissible: below every drawn bound, printed nowhere)", "verdict": V617}


def t615_beside(d615: dict) -> dict:
    return {"block": "T-615 Q-80 0.15 m black-block module (beside T-543/blockwork; his m2 only: NOT_COMPARABLE in "
                     "units / mortar / ties)", "task": f"T-615 ({MERGED['T-615'][0]})", "rule": d615["rule"],
            "walls": d615["walls"], "area_m2": d615["area_m2"],
            "units_nr": [Z.s(D(str(d615["units_nr"]["low"]))), Z.s(D(str(d615["units_nr"]["theoretical"])))],
            "panel_mortar_m3": [Z.s(D(str(d615["panel_mortar_m3"]["low"]))),
                                Z.s(D(str(d615["panel_mortar_m3"]["material_base"])))],
            "perimeter_mortar_m3": [d615["perimeter_mortar_m3"]["low"], d615["perimeter_mortar_m3"]["high"]],
            "cement_bags_50kg": [d615["cement_bags_50kg"]["low"], d615["cement_bags_50kg"]["high"]],
            "status": "ASSUMED - OWNER-APPROVED (Q-80 + Q-75 / Q-77 / Q-78); waste and procurement HELD, never 0",
            "statement_effect": "none: T-543/blockwork compares m2 (unchanged); his rows carry no units / mortar",
            "freelancer": d615["freelancer"], "verdict": V615}


def t618_porch_beside(d618: dict) -> dict:
    fr2 = [f for f in d618["fix_rows"] if f.startswith("FR-T618-2")][0]
    return {"block": "FR-T618-2 E1 porch landing skirting (beside T-574/skirting-outdoor@V8; no candidate line)",
            "task": f"T-618 ({MERGED['T-618'][0]})", "lm_walled": "3.50", "status": "ENGINE_OMISSION CANDIDATE, scope "
            "HELD (never 0) for the Lead", "fix_row": fr2}


def t621_carry_beside(d621: dict) -> dict:
    return {"block": "T-621 carry-forward (beside T-553/floor-tile@V11)", "task": f"T-621 ({MERGED['T-621'][0]})",
            "split_by_evidence_worker": d621["split"]["by_evidence"],
            "not_remeasured": "row 0 round-stair footprint 6.124412 m2 (T-625)",
            "open_plan_not_checker_remeasured": ["GF-OPEN.full 147.657717 m2 (rows 2-5, 9)",
                                                 "1F-LIV.floor_printed 38.5855 m2 (rows 11-13)"]}


# ================================================================================ (d) F-T613-5 =====================
def held_blank_reconciliation(st: dict, record: dict) -> list[dict]:
    """(d) one HELD-blank count per section: rows + NOT_COMPARABLE blocks of the same report = the section's count."""
    out = []
    for sid, sec in record.items():
        eh = sec.get("engine_held")
        if not isinstance(eh, dict) or "held_blank_lines" not in eh:
            continue
        rows = sum(int(r.get("engine_held_blank_lines") or 0) for r in sec.get("rows", []))
        nc = {n.get("block_id"): int(n["engine_held_blank_lines"]) for n in st.get("not_comparable", [])
              if n.get("report") == sec.get("report") and n.get("engine_held_blank_lines") is not None
              and str(n.get("unit")) == str(sec.get("unit"))}
        tot = rows + sum(nc.values())
        if tot != int(eh["held_blank_lines"]):
            raise StatementError(f"{sid}: HELD-blank lines {eh['held_blank_lines']} != rows {rows} + NOT_COMPARABLE "
                                 f"{sum(nc.values())} (R-T620-1 (d))")
        out.append({"section_id": sid, "held_blank_lines": int(eh["held_blank_lines"]), "in_compared_rows": rows,
                    "in_not_comparable_blocks": nc,
                    "cause": (f"{eh['held_blank_lines']} = {rows} in the compared rows + "
                              + " + ".join(f"{v} in {k} (NOT_COMPARABLE: his NO_ROW, never 0)" for k, v in nc.items())
                              if nc else f"{rows} in the compared rows"),
                    "fixes": "F-T613-5 (statement 799 vs scorecard 798): one count, the tank line named"})
    return out


# ================================================================================ build ============================
EXTENDED = ("not_comparable", "reclasses", "reports_covered", "reports_pending", "rule", "provenance")


def check_v10_unchanged(st: dict, st10: dict) -> None:
    for k in st10:
        if k in EXTENDED:
            continue
        if json.dumps(st[k], sort_keys=True) != json.dumps(st10[k], sort_keys=True):
            raise StatementError(f"V10 key {k} changed in V11")
    for k in ("not_comparable", "reclasses", "reports_covered"):
        if st[k][:len(st10[k])] != st10[k]:
            raise StatementError(f"V10 {k} not carried as its prefix")
    if not st["rule"].startswith(st10["rule"]):
        raise StatementError("V10 rule text not carried as its prefix")
    if {k: v for k, v in st["provenance"].items() if k in st10["provenance"]} != st10["provenance"]:
        raise StatementError("V10 provenance changed")


def _ev(r: dict) -> str:
    e = r.get("evidence_status")
    if e:
        return e
    v = r.get("verification") or ""
    return "CHECKER_CONFIRMED (class)" if v.startswith("CHECKER_CONFIRMED") else (v.split(" ")[0] or "none")


def headline(secs: list[dict]) -> list[dict]:
    out = []
    for c in secs:
        ev: dict = {}
        for r in c["rows"]:
            e = ev.setdefault(r["class"], {}).setdefault(_ev(r), D(0))
            ev[r["class"]][_ev(r)] = e + D(r["delta"])
        out.append({"section_id": c["section_id"], "restates": c["restates"], "kind": c.get("kind"),
                    "unit": c["unit"], "reference_total": c["reference_total"], "engine_valued": c["engine_valued"],
                    "difference": c["difference"], "by_class": c["by_class"],
                    "by_class_evidence": {k: {e: Z.s(v) for e, v in sorted(m.items())} for k, m in sorted(ev.items())}})
    return out


def build_from(st10: dict, src: dict) -> dict:
    st = copy.deepcopy(st10)
    floor, ev_moves = t621_floor_tile(st10, src["T-621"])
    lintel, mv_apart = t616_lintel(st10, src["T-616"])
    secs = [t600_beams(st10, src["T-600"]), floor, t618_stairs(st10, src["T-618"]), t618_rails(st10, src["T-618"]),
            t618_room(st10, src["T-618"]), t618_door_steps(st10, src["T-618"]), lintel]
    old_all, sup10 = all_sections(st10), supersession(st10)
    for c in secs:
        if c["section_id"] in old_all:
            raise StatementError(f"{c['section_id']}: section id already in V10")
        if c["restates"] in sup10:
            raise StatementError(f"{c['section_id']}: restates a superseded section {c['restates']}")
        readd(c)
    sup11 = {c["restates"]: c["section_id"] for c in secs}
    st["sections_v11"] = secs
    st["supersedes_v11"] = sup11
    st["headline_v11"] = headline(secs)
    st["class_shift_v11"] = {"scored": "none: no class moves in a scored section (bounds, ranges and evidence only)",
                             "apart": mv_apart}
    st["evidence_shift_v11"] = ev_moves
    st["beside_v11"] = [t614_beside(src["T-614"]), t619_beside(src["T-619"]), t608_beside(src["T-608"]),
                        t617_beside(src["T-617"]), t615_beside(src["T-615"]), t618_porch_beside(src["T-618"]),
                        t621_carry_beside(src["T-621"])]
    rec = {k: v for k, v in dict(all_sections(st10), **{c["section_id"]: c for c in secs}).items()
           if k not in dict(sup10, **sup11)}
    st["held_blank_reconciliation_v11"] = held_blank_reconciliation(st10, rec)
    st["folds_v11"] = {t: {"merge": MERGED[t][0], "verdict": MERGED[t][1]} for t in SRC}
    st["reclasses"] = st10["reclasses"] + [{k: v for k, v in m.items() if k != "unit"} for m in mv_apart]
    st["reports_covered"] = st10["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st10["rule"] + " + R-T620-1"
    st["schema_v11"] = "URBAN_T620_RECONCILED_STATEMENT_V11"
    st["lessons_adopted_applied_v11"] = LESSONS_ADOPTED
    st["provenance"]["inputs_v11"] = {str(p.relative_to(ROOT)): Z.sha(p) for p in
                                      list(SRC.values()) + [B609.JSON_OUT, B609.MD_OUT, HERE / "t620_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v10_unchanged(out, st10)
    return out


def build() -> dict:
    return build_from(v10_statement(), load_sources())


# ================================================================================ markdown =========================
def _rg(r) -> str:
    return f"({'OPEN' if r[0] is None else r[0]} .. {r[1]}]"


def to_markdown(st: dict) -> str:
    md = ("# T-620 reconciled-quantities statement V11 (generated; reference - engine, + = in the reference only)\n\n"
          "V11 = statement V10 (T-609, rebuilt, equal to its committed output and its sha256 pin; every V10 key carried "
          "byte-equal) + the restated sections and blocks below. Development villa; not an accuracy claim; nothing "
          "released (ARCH_TAKEOFF_V3.0.58 NOT RELEASED; V2.9 + route G unchanged). No class moves in a scored section.\n\n")
    md += ("## V11 sections (restated; reference / engine / difference equal to the section of record)\n\n| Section | "
           "Restates | Unit | Reference | Engine valued | Difference | By class |\n|---|---|---|---|---|---|---|\n")
    for h in st["headline_v11"]:
        bc = "; ".join(f"{k} {v}" for k, v in h["by_class"].items() if D(v))
        md += (f"| {h['section_id']} | {h['restates']} | {h['unit']} | {h['reference_total']} | {h['engine_valued']} | "
               f"{h['difference']} | {bc} |\n")
    md += "\n## Evidence moves (T-621; class and delta unchanged)\n\n| Row | From | To | Class | Delta m2 |\n|---|---|---|---|---|\n"
    for m in st["evidence_shift_v11"]:
        md += f"| {m['row']} {m['name'][:60]} | {m['from']} | {m['to']} | {m['class']} | {m['delta']} |\n"
    md += "\n## Class moves\n\n- Scored sections: " + st["class_shift_v11"]["scored"] + ".\n"
    for m in st["class_shift_v11"]["apart"]:
        md += f"- APART {m['section_id']}: {m['from']} -> {m['to']} {m['delta']} {m['unit']} ({m['why']}; never added).\n"
    lin = [c for c in st["sections_v11"] if c["section_id"].startswith("T-571/")][0]
    md += (f"\n## Lintel-implied count (T-616; APART, never added)\n\nhis {lin['reference_total']} vs engine "
           f"{lin['engine_valued']} = {lin['difference']} nr: " + "; ".join(f"{r['class']} {r['delta']}" for r in lin["rows"])
           + f". Class ranges: ENGINE_RIGHT {' .. '.join(lin['class_range_v11']['ENGINE_RIGHT'])}, UNRESOLVED "
           f"{' .. '.join(lin['class_range_v11']['UNRESOLVED'])} ({lin['class_range_v11']['pairs']}). "
           f"{lin['rows_v8_by_opening']}.\n")
    bm = [c for c in st["sections_v11"] if c["section_id"] == "T-545/beams@V11"][0]
    md += "\n## B10 pair residual (T-600 r2; class UNRESOLVED unchanged, terms are bounds)\n\n"
    for r in bm["rows"]:
        t = r.get("t600_v11")
        if t and "residual_R_m3" in t:
            md += (f"- {t['storey']}: T {t['through_support_T_m3']} - J {t['joint_head_J_m3']} = R {t['residual_R_m3']} "
                   f"m3 (rows {t['statement_pair_residual_m3']} + B7 {t['b7_folded_m3']}); SHORT "
                   f"{t['unresolved_short_m3']} (not a cause); capacity bounds " +
                   ", ".join(f"{k} {v}" for k, v in t["capacity_terms_m3_bounds_not_classes"].items()) +
                   "; proposals only: " + ("; ".join(
                       f"{p['mark']} {p['basis']} (" + ", ".join(f"{c['column']} {c['kind']} {c['proposal']}"
                                                              for c in p["per_column"]) + ")"
                       for p in t["proposals_only"]) or "none") + ".\n")
    pr = bm["pair_residual_v11"]
    md += f"- {pr['note']}.\n"
    md += "\n## Ranges (FR-T618-1; the point is the upper end, never a quantity)\n\n"
    for c in st["sections_v11"]:
        for r in c["rows"]:
            if "range_v11" in r:
                md += f"- {c['section_id']}: {r['name'][:70]}: {_rg(r['range_v11'])} {c['unit']}\n"
    stairs = [c for c in st["sections_v11"] if c["section_id"] == "T-574/skirting-stairs@V11"][0]
    md += f"- Stairs: UNRESOLVED (OPEN .. {stairs['residual_range_v11']['UNRESOLVED'][1]}]: {stairs['residual_range_v11']['reconciles']}.\n"
    md += "\n## Causes named (T-618; class UNRESOLVED unchanged)\n\n"
    for c in st["sections_v11"]:
        for r in c["rows"]:
            if "t618_v11" in r:
                md += f"- {c['section_id']}: {r['name'][:70]} ({r['delta']} {c['unit']}): {r['t618_v11']['cause'][:160]}; closes it: {r['t618_v11']['closes_it'][:120]}\n"
    md += "\n## HELD-blank lines, one count per section (F-T613-5)\n\n"
    for h in st["held_blank_reconciliation_v11"]:
        md += f"- {h['section_id']}: {h['cause']}.\n"
    md += "\n## Beside (no statement quantity moves)\n\n"
    for b in st["beside_v11"]:
        md += f"- {b['block']} [{b['task']}]"
        if "total_m3" in b:
            md += f": fix rows {', '.join(f['id'] + ' ' + f['change_m3'] for f in b['fix_rows'])} = +{b['total_m3']} m3 ({b['class_proposed']}); held {b['held'][0]['id']} {' .. '.join(b['held'][0]['bound_m3'])} m3; {b['open']}"
        if "STR.CONC.BEAM_m3" in b:
            x = b["STR.CONC.BEAM_m3"]
            md += f": B10 released if wired {' .. '.join(x['v14_released_if_wired'])} m3 (V13 {x['v13_released']}); ARCH.PASSAGE {b['ARCH.PASSAGE_pcs']['v13']} -> {b['ARCH.PASSAGE_pcs']['v14']} pcs"
        if "heads" in b:
            md += ": heads at most " + ", ".join(f"{k} {v['high_at_drawn_buildup_m']} m" for k, v in b["heads"].items()) + "; low HELD"
        if "units_nr" in b:
            md += f": {b['walls']} walls, units {' .. '.join(b['units_nr'])} nr, panel mortar {' .. '.join(b['panel_mortar_m3'])} m3; {b['status']}"
        md += ".\n"
    md += ("\nSuperseded (kept byte-equal in their versions): " +
           "; ".join(f"{k} -> {v}" for k, v in st["supersedes_v11"].items()) + ".\n")
    md += f"\nReports covered (added): {', '.join(NEW_REPORTS)}; pending: {'; '.join(st['reports_pending'])}.\n"
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-620 statement differs from out/")
            return 1
        print("T-620 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
