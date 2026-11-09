"""T-579: reconciled-quantities statement adapters V5 for the merged T-560 (B11 reinforcement, t), T-568 (doors /
windows, nr and m2 apart), T-569 (wiring manifest V8 rows: beside, never candidate lines), T-572 (B10 / B1 structural
HELD bounds and the like-for-like measured set, m3) and T-573 (ceilings by face class, m2 and lm apart). Research,
unwired: computes no new quantity; reads committed research outputs (sha256-pinned) and the pinned V3.0.57 line index
only; no drawing, workbook or client data. T-571 and T-574 were not merged at claim time: pending.

Statement sign (as V4): reference - engine; + = in the reference only.

R-T579-1 (proposed, every villa). A statement that takes in a later report:
  (a) BENCHMARK BASIS FIRST: a reference figure classed TYPED_LUMP (a typed constant with no measured row, R-T560-1) is
      compared only on the smallest common scope group, as RULE_DIFFERENCE with the quantity UNRESOLVED; it never
      carries a %, never reads as agreement, and an ENGINE_OMISSION of a line inside such a group (no bound: bar detail
      not read) rides on the group as a named omission with its fix row, never as a split of the lump;
  (b) ONE-SIDED IS NOT A POINT: a held component with a drawn lower end only is printed AT_LEAST x with the upper end
      OPEN; a family total is stated only when every held component carries that end; a low of one subset is never
      printed beside a high of another as a range; no % on a held family; % only on the like-for-like measured set;
  (c) A MANIFEST ROW IS NOT A CANDIDATE LINE: a wiring-manifest row (T-569 V8) is printed beside with its evidence
      status and the statement row it will switch, and the switch condition (the line exists in the candidate); its
      planned element ids must be absent from the pinned line index and its expected figure never enters a valued or
      bounded column;
  (d) UNITS: kg inside, t once at the boundary (6 dp); one unit per section; nr and m2 never in one section; lm never
      with m2; a row whose unit is not the section's unit is refused;
  (e) A HEADLINE % WITH HELD OR SCOPE CAUSES IS NOT A VERDICT: printed beside labelled so, with the like-for-like % on
      the set with no HELD and no scope cause;
  (f) ONE REFERENCE ROW, ONE TOTAL: a reference row that is already a term of another section (his pool-court soffit
      row in T-552/plaster-external; his door-opening deduction rows in T-543/blockwork; the stair soffits in
      T-561/stair-soffit) is shown in the face-class view as a CROSS_REFERENCE whose figures are checked equal to that
      section's, never added to a second trade total;
  (g) RECLASS BY NAME: a report verdict that is not a statement class (NOT_IN_HIS_ROWS, a cove with no candidate line)
      is mapped once by name with an F-T579 tag (no line is never HELD, R-T554-1 (d)); a later report that settles a
      V4 UNRESOLVED row (T-568 on the T-559 opening rows) restates the row's class only, the delta stays.
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
T570 = ROOT / "research/agents_t570"
if str(T570) not in sys.path:
    sys.path.insert(0, str(T570))

D = Decimal
CLASSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
SIGN = "reference - engine (+ = in the reference only)"

T560_JSON = ROOT / "research/agents_t560/out/T560_REBAR_RECONCILE.json"
T568_JSON = ROOT / "research/agents_t568/out/T568_TYPE_TABLE.json"
T569_JSON = ROOT / "research/agents_t569/WIRING_MANIFEST_V8.json"
T572_JSON = ROOT / "research/agents_t572/out/T572_HELD_BOUNDS.json"
T573_JSON = ROOT / "research/agents_t573/out/T573_CEILING_RECONCILE.json"
V4_JSON = T570 / "out/RECONCILED_STATEMENT_T570.json"
INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
PINS = {
    T560_JSON: "bc57247be19e8a72e86e9d6aa3b3cc7fcc581794eb67391694942c1baed4a96b",
    T568_JSON: "75e25fe8239fcb08361869a0d5c4e4483f3b6c859b8a74912ec42aae326be045",
    T569_JSON: "c71ecdc0eb11cba4e593ce31e3ec2d3bbad89d55fbc86a596f5b5890a474cf6b",
    T572_JSON: "a39e7b4b838e3590d6b456327823618e66b023617cb49be39821ad93ccb264f5",
    T573_JSON: "447804a48e21142e5d0eeffda8517300ab595791a11b599a7b1af74dbf3dcdbf",
    V4_JSON: "5dac67ff1cff604747b2563d3f10cbd71e1614fb712940d9ebb0ba8372483222",
    INDEX: "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738",
}

# Checker verdicts (board, verifier 2026-11-06), quoted as classes only
V560 = ("Checker 2026-11-06 17:57 (T-560 Gate A) PARTIALLY VERIFIED: his side 7 / 7 typed family cells (TYPED_LUMP "
        "CONFIRMED, own read of his workbook); engine totals and part counts 4 / 4 (own sum of the pinned index); one "
        "valued bar group R043 2 / 3 components (11.500 kg); every group RULE_DIFFERENCE -> quantity UNRESOLVED "
        "CONFIRMED; dome + lift-pit-wall rebar ENGINE_OMISSION of a line CONFIRMED; tank NO_ROW NOT_COMPARABLE")
V568 = ("Checker 2026-11-06 17:57 (T-568 Gate A) PARTIALLY VERIFIED: door counts 3 / 3 storeys CONFIRMED from the drawn "
        "leaves (own census of 27 door inserts in P7757.dxf); window counts, door widths and every m2 term "
        "worker-proposed (ACCEPTED as worker-proposed); W02 HELD (D-53)")
V572 = ("Checker 2026-11-06 19:58 (T-572 Gate A) PARTIALLY VERIFIED 2 / 8 families (necks lower end 9.7239 m3 own "
        "recompute 36 / 36, pit backfill lower end 99.645011 re-added); every other component HELD / LOWER_ONLY / "
        "UNBOUNDED with basis or item, nothing VERIFIED; measured-set splits worker-proposed (his workbook not opened "
        "by the Checker); NOTE1_ON_LIFT_RAFT ACCEPTED")
V573 = ("Checker 2026-11-06 20:02 (T-573 Gate A) PARTIALLY VERIFIED: light-well outline 16.005 m2 and round flight "
        "re-measured (no-ceiling 13.39 AGREE 0.02 %); causes re-added; no ceiling line VERIFIED; light well ENGINE_RIGHT "
        "CONFIRMED; cove strips RULE_DIFFERENCE; UNRESOLVED 6.161 m2 named; the -10.42 % is not a verdict")
V569 = ("Checker 2026-11-06 20:00 (T-569 Gate A) PARTIALLY VERIFIED: return sum 23.070 (26 faces), pier storey "
        "2.2533924 and W17 9.870 re-checked; nothing wired; a Gate B package must carry these rows")


class StatementError(ValueError):
    """A V5 adapter or verification refused its input."""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path, pin: bool = True) -> dict:
    if pin and p in PINS and sha(p) != PINS[p]:
        raise StatementError(f"{p.relative_to(ROOT)}: sha256 differs from its pin (re-pin after review)")
    return json.loads(p.read_text(encoding="utf-8"))


def load_index(p: Path = INDEX) -> dict:
    return {ln["line_id"]: ln for ln in load(p)["lines"]}


def s(x) -> str:
    """Decimal to its canonical text (no exponent, trailing zeros kept as computed)."""
    v = D(str(x))
    return format(v, "f")


def neg(x) -> str:
    return s(-D(str(x)))


def zero_classes() -> dict:
    return {c: D(0) for c in CLASSES}


def row(name: str, delta, cls: str, unit: str, source: str, verification: str, **kw) -> dict:
    if cls not in CLASSES:
        raise StatementError(f"{name}: '{cls}' is not a statement class (map it by name, R-T579-1 (g))")
    r = {"name": name, "delta": s(delta), "class": cls, "unit": unit, "source": source, "verification": verification}
    r.update(kw)
    return r


def close_section(sec: dict) -> dict:
    """Residual 0: the rows re-add to reference - engine valued; class totals from the rows; one unit (R-T579-1 (d))."""
    for r in sec["rows"]:
        if r["unit"] != sec["unit"]:
            raise StatementError(f"{sec['section_id']}: row '{r['name']}' in {r['unit']}, section in {sec['unit']}")
        if r["class"] == "HELD" and D(r["delta"]) == 0 and not r.get("bound") and not r.get("item"):
            raise StatementError(f"{sec['section_id']}: HELD row '{r['name']}' printed as 0 with no bound or item")
    diff = D(sec["reference_total"]) - D(sec["engine_valued"])
    tot = sum((D(r["delta"]) for r in sec["rows"]), D(0))
    if sec["rows"] and tot != diff:
        raise StatementError(f"{sec['section_id']}: rows {tot} != reference - engine {diff}")
    bc, bg = zero_classes(), zero_classes()
    for r in sec["rows"]:
        bc[r["class"]] += D(r["delta"])
        bg[r["class"]] += abs(D(r["delta"]))
    sec["difference"] = s(diff)
    sec["by_class"] = {k: s(v) for k, v in bc.items()}
    sec["by_class_gross_abs"] = {k: s(v) for k, v in bg.items()}
    sec["closure_residual"] = s(diff - tot) if sec["rows"] else None
    refuse_pct(sec)
    return sec


def refuse_pct(sec: dict) -> None:
    """(a) / (b) / (e): no % on a TYPED_LUMP, on a section with a HELD row or on a one-sided comparison."""
    pct = sec.get("difference_pct_of_reference")
    if pct is None:
        return
    if sec.get("benchmark_basis") == "TYPED_LUMP":
        raise StatementError(f"{sec['section_id']}: a TYPED_LUMP reference carries no % (R-T560-1, R-T579-1 (a))")
    if any(r["class"] == "HELD" for r in sec["rows"]) or sec.get("engine_held"):
        raise StatementError(f"{sec['section_id']}: % on a section with HELD parts (R-T579-1 (e))")
    want = (D(sec["reference_total"]) - D(sec["engine_valued"])) / D(sec["reference_total"]) * 100
    if D(pct) != want.quantize(D("0.01")):
        raise StatementError(f"{sec['section_id']}: % {pct} != {want.quantize(D('0.01'))}")


def pct_of(ref, eng) -> str:
    return s(((D(str(ref)) - D(str(eng))) / D(str(ref)) * 100).quantize(D("0.01")))


def section(sid: str, report: str, trade: str, unit: str, ref, eng, rows: list[dict], *, basis: str,
            kind: str = "DIFFERENCE", verification: str, pct: bool = False, **kw) -> dict:
    sec = {"section_id": sid, "report": report, "trade": trade, "unit": unit, "kind": kind, "sign": SIGN,
           "reference_kind": "FREELANCER", "reference_basis": basis, "reference_total": s(ref),
           "engine_valued": s(eng), "rows": rows, "verification": verification}
    sec.update(kw)
    sec["difference_pct_of_reference"] = pct_of(ref, eng) if pct else None
    return close_section(sec)


# ================================================================================ T-560 reinforcement (t) ========
def kg_to_t(kg) -> str:
    """R-T579-1 (d): kg inside, t once at the boundary, 6 dp."""
    return s((D(str(kg)) / 1000).quantize(D("0.000001")))


def t560_sections(d: dict) -> tuple[list[dict], dict]:
    if d["bench"]["basis"] != "TYPED_LUMP" or d["bench"]["bar_rows_in_workbook"] != 0:
        raise StatementError("T-560: benchmark basis must be TYPED_LUMP with 0 bar rows to use this adapter")
    fam_t = {k: D(v["t"]) for k, v in d["bench"]["families"].items()}
    if sum(fam_t.values(), D(0)) != D(d["bench"]["total_t"]):
        raise StatementError("T-560: his families do not re-add to his typed total")
    rows, ref, eng_kg, lo_kg, hi_kg, blank, excl, nc = [], D(0), D(0), D(0), D(0), 0, 0, None
    for gid, g in d["groups"].items():
        k = g["engine_kg"]
        if g["cls"] == "NO_ROW":
            nc = {"block_id": "T-560/rebar-tank", "report": "T-560", "trade": "B11 reinforcement (tank)", "unit": "t",
                  "status": "NOT_COMPARABLE", "reference_total": "NO_ROW", "difference": None,
                  "difference_pct_of_reference": None, "engine_valued": None,
                  "engine_held_blank_lines": k["held_blank"], "information": g["scope_items"],
                  "verification": V560}
            blank += k["held_blank"]
            continue
        his = sum((fam_t[f] for f in g["bench_families"]), D(0))
        if his != D(g["his_t"]):
            raise StatementError(f"T-560 {gid}: his families {his} != group {g['his_t']}")
        v_t = D(kg_to_t(k["valued_kg"])) if k["valued_kg"] is not None else D(0)
        h = (kg_to_t(k["held_low_kg"]), kg_to_t(k["held_high_kg"])) if k["held_low_kg"] is not None else None
        if s(his - v_t) != s(D(g["gap_valued_t"])):
            raise StatementError(f"T-560 {gid}: gap {his - v_t} != report {g['gap_valued_t']}")
        omission = [x for x in g["scope_items"]]
        short = {"LIFT_PIT": "lift-pit walls", "DOME": "dome shells + rings"}
        rows.append(row(f"{gid}: his {', '.join(g['bench_families'])} vs engine {', '.join(g['engine_families'])}",
                        his - v_t, "RULE_DIFFERENCE", "t", f"T-560 s.4 group {gid}", "CHECKER_CONFIRMED",
                        source_class="RULE_DIFF (TYPED_LUMP vs counted bars): quantity UNRESOLVED",
                        his_t=s(his), engine_valued_t=s(v_t),
                        engine_held_range_t=list(h) if h else None,
                        engine_held_blank_lines=k["held_blank"],
                        residual_after_bounded_held_t=[g["residual_low_t"], g["residual_high_t"]],
                        residual_carried_by=g["residual_carried_by"],
                        engine_omission_of_a_line=[{"what": x, "element": [v for k, v in short.items() if k in x][0],
                                                    "class": "ENGINE_OMISSION (CONFIRMED)",
                                                    "bound": None, "fix_row": "T-569 WIRING MANIFEST V8 REBAR_OMISSION"
                                                    " (HELD blank STR.REBAR rows, never 0)",
                                                    "inside_this_row": True} for x in omission if "TANK" not in x]))
        ref += his
        eng_kg += D(k["valued_kg"] or 0)
        lo_kg += D(k["held_low_kg"] or 0)
        hi_kg += D(k["held_high_kg"] or 0)
        blank += k["held_blank"]
        excl += k["excluded"]
    tk = d["engine_totals_kg"]
    if (eng_kg, lo_kg, hi_kg, blank, excl) != (D(tk["valued_kg"]), D(tk["held_low_kg"]), D(tk["held_high_kg"]),
                                               tk["held_blank"], tk["excluded"]):
        raise StatementError("T-560: engine groups do not re-add to the candidate totals in every part")
    sec = section("T-560/rebar", "T-560", "B11 reinforcement (installed, net)", "t", ref, kg_to_t(eng_kg), rows,
                  basis="freelancer concrete + rebar workbook, summary sheet: seven typed family constants (no "
                        "formula) and a typed total 44.19 t; no bar row on any of 8 sheets (T-560 s.2; Drive 'Alsenan "
                        "chalet project')",
                  benchmark_basis="TYPED_LUMP", verification=V560,
                  engine_held={"held_range_t": [kg_to_t(lo_kg), kg_to_t(hi_kg)], "held_blank_lines": blank,
                               "excluded_lines": excl, "lines": d["engine_lines"]},
                  pct_refused_because="TYPED_LUMP reference (R-T560-1): no %, no agreement",
                  procurement="B11-04 procurement tonnage (waste, offcuts, laps) is a separate account, no line yet")
    return [sec], nc


# ================================================================================ T-568 doors / windows ==========
def _t568_rows(rows: list[dict], cls: str, unit: str, ver: dict) -> list[dict]:
    out = []
    for r in rows:
        if r["cls"] != cls or r["unit"] != unit:
            continue
        out.append(row(f"{r['name']} / {r['term']}", neg(r["delta"]), r["cause"], unit,
                       "T-568 s.1 type table (ours - his restated as his - ours)", ver.get(r["term"], ver["*"]),
                       note=r.get("note", "")))
    return out


def _cand(d: dict, cls: str, unit: str) -> tuple[D, D, D, int]:
    """Candidate lines of one class / unit: settled sum, held low, held high, held lines with no figure."""
    val = lo = hi = D(0)
    nofig = 0
    for c in d["candidate_closure"]:
        k, _st, u, status = c["line"].split("|")
        if k != cls or u != unit:
            continue
        v, l, h = (None if x is None else (D(str(x)).quantize(D(1)) if unit == "pcs" else D(str(x)))
                   for x in c["candidate"])
        if v is not None and unit == "pcs" and v != D(str(c["candidate"][0])):
            raise StatementError(f"{c['line']}: a count that is not a whole number")
        if status.startswith("SETTLED"):
            val += v
        elif l is None:
            nofig += 1
        else:
            lo += l
            hi += h
    return val, lo, hi, nofig


def t568_sections(d: dict, v4: dict) -> tuple[list[dict], list[dict]]:
    """nr and m2 apart; engine valued = SETTLED candidate lines; HELD lines beside with their bounds."""
    count_ok = {"ours only": "CHECKER_CONFIRMED", "*": "WORKER_PROPOSED"}
    m2_ver = {"*": "WORKER_PROPOSED"}
    out = []
    unit_of = {"nr": "pcs", "m2": "m2"}
    specs = [("DOOR.EXTERNAL.ALUMINIUM", "supply_aluminium", "T-568/alu-doors",
              "B12 aluminium external doors (supply)", "freelancer aluminium workbook, supply rows"),
             ("WINDOW.ALUMINIUM", "supply_aluminium", "T-568/windows", "B12 aluminium windows (supply)",
              "freelancer aluminium workbook, supply rows"),
             ("DOOR.INTERNAL.PVC", "masonry_deduction_doors", "T-568/internal-doors",
              "B12 internal doors: COUNT CROSS-CHECK ONLY (his only door rows are masonry opening deductions, no supply "
              "row)", "freelancer masonry workbook, opening deduction rows (CROSS_REFERENCE: the same rows are terms "
              "of T-543/blockwork; never added to a second total, R-T579-1 (f))")]
    for cls, blk, sid, trade, basis in specs:
        src = d[blk][cls]
        for unit in ("nr", "m2"):
            t = src[unit]
            val, lo, hi, nofig = _cand(d, cls, unit_of[unit])
            ours = D(str(t["ours_settled"]))
            held_count = lo if unit == "nr" else None
            if unit == "nr" and ours != val + lo and ours != val:
                raise StatementError(f"{sid}-nr: report count {ours} != candidate settled {val} + held {lo}")
            if unit == "m2" and ours != val:
                raise StatementError(f"{sid}-m2: report settled {ours} != candidate settled {val}")
            his = D(str(t["his"]))
            rows = _t568_rows(src["rows"], cls, unit, count_ok if unit == "nr" else m2_ver)
            his_minus_ours = sum((D(r["delta"]) for r in rows), D(0))
            if s(his_minus_ours) != s(-D(str(t["ours_minus_his"]))):
                raise StatementError(f"{sid}-{unit}: causes {his_minus_ours} != report {t['ours_minus_his']}")
            for r in rows:
                if r["class"] == "HELD" and unit == "nr" and not r.get("bound"):
                    r["bound"] = [s(lo), s(hi)]
                    r["item"] = "count HELD on the candidate (D-53)"
            if unit == "nr" and held_count and ours == val + lo:
                # the count is drawn (Checker: door leaves) but the candidate line is HELD (its width is held)
                rows.append(row(f"{cls} {unit}: candidate count lines HELD (width held), count drawn {lo}", lo,
                                "HELD", unit, "T-568 candidate closure", "CHECKER_CONFIRMED (count of drawn leaves)",
                                bound=[s(lo), s(hi)]))
            held = {}
            if lo or hi or nofig:
                held = {"held_range": [s(lo), s(hi)], "held_lines_no_figure": nofig,
                        "held_items": t.get("ours_held") or t.get("ours_count_held") or [],
                        "held_bounds": t.get("ours_held_bounds") or {}}
            ver = V568 + ("; counts CONFIRMED" if unit == "nr" and cls.startswith("DOOR") else "")
            sec = section(f"{sid}-{unit}", "T-568", trade, unit, his, val, rows, basis=basis, verification=ver,
                          pct=not held and not any(r["class"] == "HELD" for r in rows) and his != 0,
                          engine_held=held or None)
            if blk == "masonry_deduction_doors":
                sec["kind"] = "CROSS_REFERENCE_COUNT_CHECK"
                sec["reference_counted_in"] = "T-543/blockwork"
            out.append(sec)
    w = d["windows_like_for_like"]
    win = [x for x in out if x["section_id"] == "T-568/windows-m2"][0]
    a, b = w["settled_both_sides"], w["with_Q76A_W17"]
    win["beside"] = {
        "like_for_like_settled_both_sides": {"openings": a["nr"], "reference_m2": a["his"], "engine_m2": a["ours"],
                                             "difference": neg(a["diff"]), "difference_pct_of_reference":
                                             pct_of(a["his"], a["ours"]), "engine_vs_reference_pct": a["pct"]},
        "expected_after_V8_W17_row": {"status": "EXPECTED (not wired; T-569 V8 row W17_Q76A, ASSUMED - "
                                                "OWNER-APPROVED Q-76 A)", "openings": b["nr"], "reference_m2": b["his"],
                                      "engine_m2": b["ours"], "difference": neg(b["diff"]),
                                      "difference_pct_of_reference": pct_of(b["his"], b["ours"]),
                                      "engine_vs_reference_pct": b["pct"]}}
    nc = [{"block_id": "T-568/main-entrance", "report": "T-568", "trade": "B12 main entrance door", "unit": "nr / m2",
           "status": "NOT_COMPARABLE", "reference_total": "NO_ROW", "difference": None,
           "difference_pct_of_reference": None, "engine_valued": None,
           "engine_held": "1 pcs / 5.000 m2 HELD (D-53)", "verification": V568},
          {"block_id": "T-568/internal-doors-supply", "report": "T-568", "trade": "B12 internal doors (supply)",
           "unit": "nr / m2", "status": "NOT_COMPARABLE", "reference_total": "NO_ROW (no supply row in his supply "
                                                                              "workbooks)", "difference": None,
           "difference_pct_of_reference": None, "engine_valued": None,
           "engine_held": "see T-568/internal-doors-nr / -m2 (count cross-check only)", "verification": V568}]
    ll = d["masonry_deduction_doors"]["LIFT.LANDING_OPENING"]
    nc.append({"block_id": "T-568/lift-landings", "report": "T-568", "trade": "B12 lift landing openings (lift supply "
               "excluded; no candidate line)", "unit": "nr / m2", "status": "NOT_COMPARABLE",
               "reference_total": f"his masonry deduction rows {ll['nr']['his']} nr / {ll['m2']['his']} m2 (terms of "
                                  "T-543/blockwork, R-T579-1 (f))", "difference": None,
               "difference_pct_of_reference": None, "engine_valued": None,
               "engine_held": f"census {ll['nr']['ours_settled']} openings, heights HELD "
                              f"({', '.join(ll['m2']['ours_held'])})", "verification": V568})
    return out, nc


T559_ROWS = {   # V4 T-543/blockwork rows of T-559 s.1 (+6.30 m2 UNRESOLVED) -> T-568 s.2 classes
    "openings GF: GF D-GF-03 vs his 1.00 x 2.40 / width": ("ENGINE_RIGHT", "width: masonry ends 0.900 both faces, "
                                                           "his 1.00 = the frame", "WORKER_PROPOSED"),
    "openings GF: GF D-GF-09 (engine deducts; no unit of his) / count": ("ENGINE_RIGHT", "count: 5 GF external leaves "
                                                                        "drawn vs his 4", "CHECKER_CONFIRMED"),
    "openings 20CM: 20CM D-GF-08 vs his 1.10 x 2.40 / width": ("RULE_DIFFERENCE", "width: drawn 1.000, his 1.10 = the "
                                                              "Q-04 wall-opening minimum (UP-DOOR-OPEN-003)",
                                                              "WORKER_PROPOSED"),
    "openings 1F: 1F D-1F-03 vs his 0.90 x 2.40 / width": ("ENGINE_RIGHT", "width: D115 1.000 between masonry ends",
                                                           "WORKER_PROPOSED"),
    "openings 1F: 1F W18 (engine deducts; no unit of his) / count": ("ENGINE_RIGHT", "size, not count: his sixth bath "
                                                                    "window is W18 (0.50 x 2.16)", "WORKER_PROPOSED"),
    "openings 1F: 1F his 0.60 x 0.80 (no engine opening) / count": ("ENGINE_RIGHT", "size, not count: the same W18",
                                                                   "WORKER_PROPOSED"),
    "openings 1F: 1F D-1F-10 (engine deducts; no unit of his) / count": ("ENGINE_RIGHT", "count: 10 1F leaves drawn "
                                                                        "vs his 8", "CHECKER_CONFIRMED"),
    "openings 1F: 1F D-1F-02 (engine deducts; no unit of his) / count": ("ENGINE_RIGHT", "count: 10 1F leaves drawn "
                                                                        "vs his 8", "CHECKER_CONFIRMED"),
}


def restate_blockwork_t568(sec: dict) -> tuple[dict, list[dict]]:
    """R-T579-1 (g): the 8 T-559 opening rows (UNRESOLVED +6.30 m2) take the T-568 classes; deltas unchanged."""
    sec = copy.deepcopy(sec)
    moves, seen = [], set()
    for r in sec["rows"]:
        if r["name"] not in T559_ROWS:
            continue
        if r["class"] != "UNRESOLVED":
            raise StatementError(f"T-543/blockwork '{r['name']}': expected UNRESOLVED, found {r['class']}")
        cls, why, ver = T559_ROWS[r["name"]]
        seen.add(r["name"])
        m = {"tag": "F-T579-1", "from": "UNRESOLVED", "to": cls, "delta": r["delta"],
             "why": f"T-568 s.2 (MERGED 540bc99c): {why}"}
        r["class"] = cls
        r["correction"] = "T-568"
        r["verification_t568"] = ver + (" (Checker T-568: count terms CONFIRMED)" if ver == "CHECKER_CONFIRMED" else
                                        " (Checker T-568: ACCEPTED as worker-proposed)")
        r["reclass_t579"] = m
        moves.append({"section_id": sec["section_id"], "row": r["name"], **m})
    if seen != set(T559_ROWS):
        raise StatementError(f"T-543/blockwork: T-559 rows missing {sorted(set(T559_ROWS) - seen)}")
    tot = sum((D(m["delta"]) for m in moves), D(0))
    if tot != D("6.30"):
        raise StatementError(f"T-543/blockwork: the T-559 rows add to {tot}, not +6.30 m2")
    bc, bg = zero_classes(), zero_classes()
    for r in sec["rows"]:
        bc[r["class"]] += D(r["delta"])
        bg[r["class"]] += abs(D(r["delta"]))
    for key, new in (("by_class", bc), ("by_class_gross_abs", bg)):       # V4 text kept where a class did not move
        old = sec[key]
        sec[key] = {k: (old[k] if D(old[k]) == new[k] else s(new[k])) for k in CLASSES}
    return sec, moves


# ================================================================================ T-572 structural bounds (m3) ===
V4_OF_FAMILY = {"B10 COLUMN": "T-551/columns", "B10 NECK": "T-551/necks", "B10 LIFT": "T-551/lift-walls",
                "B10 FOOTING LINE": "T-551/footing-line", "B10 BLINDING (plain)": "T-551/blinding",
                "B1-02 EXCAVATION": "not_comparable:T-565", "B1-03 BACKFILL": "not_comparable:T-565",
                "B1-04 DISPOSAL": "not_comparable:T-565"}
SPLIT_CLASS = {"COUNT": "ENGINE_RIGHT", "JOINT_HEAD": "RULE_DIFFERENCE", "BASE": "ENGINE_RIGHT",
               "GLOBAL_DEPTH": "ENGINE_RIGHT", "HEIGHT_OPEN": "UNRESOLVED"}     # = T-570 COUNT_VERDICT (T-566)


def at_least(x) -> dict:
    """R-T579-1 (b): a one-sided bound is never a point."""
    return {"at_least": s(x), "high": "OPEN"}


def t572_bounds(d: dict, v4: dict) -> dict:
    v4s = {c["section_id"]: c for c in v4["sections"]}
    ew = {f["family"]: f for f in v4["not_comparable"][0]["families"]}
    fams = []
    for name, f in d["families"].items():
        comps = [c for c in d["components"] if c["family"] == name]
        if any(c["unit"] != "m3" for c in comps):
            raise StatementError(f"T-572 {name}: a component not in m3")
        both = [c for c in comps if c["kind"] == "BOUNDED"]
        low1 = [c for c in comps if c["kind"] == "LOWER_ONLY"]
        unb = [c for c in comps if c["kind"] == "UNBOUNDED"]
        npp = [c for c in comps if c["kind"] == "NOT_PRESENT_PROPOSED"]
        for c in low1:
            if c["high"] is not None or c["low"] is None:
                raise StatementError(f"T-572 {c['element_id']}: LOWER_ONLY with a high or without a low")
        b_lo = sum((D(c["low"]) for c in both), D(0))
        b_hi = sum((D(c["high"]) for c in both), D(0))
        l_lo = sum((D(c["low"]) for c in low1), D(0))
        if len(both) + len(low1) + len(unb) != f["held_components"] or len(npp) != f["not_present_proposed"]:
            raise StatementError(f"T-572 {name}: component counts do not close")
        if f["bounded_part_low"] is not None and D(f["bounded_part_low"]) != b_lo + l_lo:
            raise StatementError(f"T-572 {name}: bounded low {f['bounded_part_low']} != {b_lo} + {l_lo}")
        if both and D(f["bounded_part_high"]) != b_hi:
            raise StatementError(f"T-572 {name}: bounded high {f['bounded_part_high']} != {b_hi}")
        held_all_low = not unb and (both or low1)
        if held_all_low and low1:
            fam_total = {"family_held": at_least(b_lo + l_lo), "stated": "LOWER END ONLY (every held component "
                                                                         "carries a drawn lower end)"}
        elif held_all_low:
            fam_total = {"family_held": [s(b_lo), s(b_hi)], "stated": "BOTH ENDS"}
        else:
            fam_total = {"family_held": None, "stated": "NOT STATEABLE: " + "; ".join(sorted(
                {c["low_item"] or c["high_item"] or "" for c in unb})) if unb else "NOT STATEABLE"}
        if f["family_low"] is not None and (not low1 or D(f["family_low"]) != b_lo + l_lo):
            raise StatementError(f"T-572 {name}: family low {f['family_low']} differs")
        rel = V4_OF_FAMILY[name]
        if rel.startswith("not_comparable"):
            code = name.split()[0]
            v4_val = ew[code]["engine_valued"] if code in ew else None
        else:
            v4_val = v4s[rel]["engine_valued"]
        if D(f["valued"]) != D(v4_val or 0):
            raise StatementError(f"T-572 {name}: valued {f['valued']} != V4 {rel} engine {v4_val}")
        fams.append({"family": name, "unit": "m3", "relates_to_v4": rel, "engine_valued": f["valued"],
                     "held_components": f["held_components"],
                     "both_ends_drawn": {"n": len(both), "range": [s(b_lo), s(b_hi)] if both else None},
                     "lower_end_only": {"n": len(low1), **(at_least(l_lo) if low1 else {"at_least": None})},
                     "no_drawn_bound": {"n": len(unb), "items": sorted({c["low_item"] or c["high_item"]
                                                                        for c in unb})},
                     "not_present_proposed": {"n": len(npp), "note": "carried apart; wiring is lane I (held lines "
                                                                     "-> no line), never 0 m3 of a held line"},
                     "family_total": fam_total, "difference_pct_of_reference": None})
    return {"section_id": "T-572/held-bounds", "report": "T-572", "trade": "B10 concrete / B1 earthworks HELD "
            "bounds (engine side only; beside the V4 T-551 sections and the T-565 block)", "unit": "m3",
            "kind": "BOUNDS", "families": fams, "verification": V572,
            "beside_candidate": {"necks_candidate_range_not_drawn_m3": d["beside_his"]["B10 NECK"]
                                 ["candidate_generic_range_m3"], "note": "generic 0.50 .. 2.50 m (T-167): beside, "
                                                                         "never the bound"}}


def t572_measured(d: dict) -> list[dict]:
    m = d["measured_set"]
    out = []
    for key, trade in (("columns_GF", "B10 GF columns, measured set (9 marks fully valued, a row of his)"),
                       ("columns_1F", "B10 1F columns, measured set (4 marks)"),
                       ("footing_pads_and_straps", "B10 footing pads + straps, measured set (18 marks)")):
        x = m[key]
        if s(D(x["engine"]) - D(x["his"])) != s(D(x["diff"])):
            raise StatementError(f"T-572 {key}: engine - his != diff")
        rows = [row(f"{key}: {k}", neg(v), SPLIT_CLASS[k], "m3", "T-572 s.3 measured set (engine - his restated)",
                    "WORKER_PROPOSED", class_basis="JOINT_HEAD RULE_DIFFERENCE (T-551, Checker T-572); the other "
                    "terms by the T-570 COUNT_VERDICT map of the same split vocabulary (T-566)")
                for k, v in x.get("split_m3", {}).items()]
        rd = sum((D(r["delta"]) for r in rows if r["class"] == "RULE_DIFFERENCE"), D(0))
        sec = section(f"T-572/measured-{key}", "T-572", trade, "m3", x["his"], x["engine"], rows,
                      basis="freelancer concrete + rebar workbook, his rows of the same marks (measured-set sums "
                            "only, T-572 s.3)", verification=V572, pct=True, kind="LIKE_FOR_LIKE_MEASURED_SET")
        if x.get("pct") is not None and neg(x["pct"]) != sec["difference_pct_of_reference"]:
            raise StatementError(f"T-572 {key}: % {x['pct']} does not restate")
        if rows:
            net = D(sec["difference"]) - rd
            sec["beside"] = {"net_of_RULE_DIFFERENCE": {"difference": s(net), "difference_pct_of_reference":
                                                        s((net / D(x["his"]) * 100).quantize(D("0.01")))}}
        else:
            sec["beside"] = {"split": "carried in V4 T-551/footing-line (T-551 classes); not repeated here"}
        out.append(sec)
    n = m["necks_on_his_count"]
    out.append({"section_id": "T-572/measured-necks", "report": "T-572", "trade": "B10 necks on his count (34 necks, "
                "13 marks): HELD, one-sided", "unit": "m3", "kind": "ONE_SIDED", "sign": SIGN,
                "reference_total": n["his_m3"], "engine": at_least(n["engine_drawn_lower_m3"]),
                "reference_minus_engine_lower": n["his_minus_engine_lower_m3"], "class": n["class"],
                "marks_reference_below_drawn_lower": n["marks_his_below_drawn_lower"], "marks": n["marks"],
                "difference": None, "difference_pct_of_reference": None,
                "verdict_proposal": "ENGINE_RIGHT (worker): his flat 1.50 m is at or below the drawn minimum; his "
                                    "total vs the drawn lower end on his count NOT re-measured by the Checker",
                "verification": V572})
    return out


def refuse_one_sided_as_point(sec: dict) -> None:
    for f in sec.get("families", []):
        lo = f["lower_end_only"]
        if lo["n"] and lo.get("high") != "OPEN":
            raise StatementError(f"{sec['section_id']} {f['family']}: LOWER_ONLY printed with a high")
        if f["lower_end_only"]["n"] and isinstance(f["family_total"]["family_held"], list):
            raise StatementError(f"{sec['section_id']} {f['family']}: a one-sided family printed as a range")
        if f["no_drawn_bound"]["n"] and f["family_total"]["family_held"] is not None:
            raise StatementError(f"{sec['section_id']} {f['family']}: family total stated with an unbounded part")
    if sec.get("kind") == "ONE_SIDED":
        if sec["engine"].get("high") != "OPEN" or sec.get("difference") is not None or \
                sec.get("difference_pct_of_reference") is not None:
            raise StatementError(f"{sec['section_id']}: a one-sided comparison printed as a point / %")


# ================================================================================ T-573 ceilings by face class ====
NOT_A_CLASS = {"NOT_IN_HIS_ROWS": ("UNRESOLVED", "F-T579-3", "scope in one list (engine face, no row of his): no "
                                                             "who-is-right verdict in the report; owner Q-57 A mod (6) "
                                                             "paints BOARD + BULKHEAD (RULE_DIFFERENCE proposal for "
                                                             "the Checker)")}


def t573_sections(d: dict, v4: dict) -> tuple[list[dict], list[dict], list[dict]]:
    v4s = {c["section_id"]: c for c in v4["sections"]}
    secs, nc, moves = [], [], []
    # BOARD
    rows = []
    for g in d["board"]["groups"]:
        gs = D(0)
        for c in g["causes"]:
            if c["verdict"] not in CLASSES:
                raise StatementError(f"T-573 board {g['id']}: verdict {c['verdict']}")
            kw = {"bound": c["bound"]} if c.get("bound") else {}
            if c["verdict"] == "HELD" and D(c["amount"]) == 0:
                kw["item"] = "location vs his row not established; bound beside"
            rows.append(row(f"{g['id']}: {c['label']}", neg(c["amount"]), c["verdict"], "m2", c.get("source", ""),
                            "CHECKER_CONFIRMED" if "light well" in c["label"] else "WORKER_PROPOSED", **kw))
            gs += D(c["amount"])
        if gs != D(g["gap"]):
            raise StatementError(f"T-573 board {g['id']}: causes {gs} != gap {g['gap']}")
    t = d["board"]["totals"]["m2"]
    board = section("T-573/ceiling-board", "T-573", "B7 ceilings: BOARD (horizontal decor ceiling)", "m2", t["his"],
                    t["ours"], rows, basis="freelancer decor sheet, halls / rooms + kitchens / baths rows (his "
                                           "H31 / H65)", verification=V573)
    bv = {k: neg(v) for k, v in d["board"]["by_verdict"].items()}
    if any(board["by_class"][k] != s(D(v)) and D(board["by_class"][k]) != D(v) for k, v in bv.items()):
        raise StatementError("T-573 board: class totals do not restate the report's by_verdict")
    ll = d["board"]["like_for_like_no_held"]
    board["beside"] = {"headline_pct_NOT_a_verdict": {"difference_pct_of_reference": pct_of(t["his"], t["ours"]),
                                                      "engine_vs_reference_pct": t["pct"],
                                                      "why": "HELD and scope causes inside (R-T579-1 (e))"},
                       "like_for_like_no_held": {"reference_m2": ll["his"], "engine_m2": ll["ours"],
                                                 "difference": neg(ll["gap"]),
                                                 "difference_pct_of_reference": pct_of(ll["his"], ll["ours"]),
                                                 "engine_vs_reference_pct": ll["pct"]}}
    secs.append(board)
    cl = {g["id"]: g for g in d["classes"]["groups"]}
    # BULKHEAD: his NO_ROW
    bh = cl["BULKHEAD vertical faces (all rooms)"]
    nc.append({"block_id": "T-573/ceiling-bulkhead", "report": "T-573", "trade": "B7 ceilings: BULKHEAD vertical faces",
               "unit": "m2", "status": "NOT_COMPARABLE", "reference_total": "NO_ROW (he lists no bulkhead)",
               "difference": None, "difference_pct_of_reference": None, "engine_valued": bh["ours"],
               "engine_basis": "13 lines ASSUMED - OWNER-APPROVED (Q-48 A + Q-43)",
               "engine_held": {"GF-RFD4E1D": bh["held_bound"]}, "verification": V573})
    # COVE (lm): no candidate line -> UNRESOLVED (R-T554-1 (d))
    cv = cl["COVE / cornice runs (lm)"]
    if cv["unit"] != "lm" or cv["lines"]:
        raise StatementError("T-573 cove: expected lm with no candidate line")
    m = {"tag": "F-T579-2", "from": "HELD", "to": "UNRESOLVED", "delta": cv["his"],
         "why": "cove / cornice: no candidate line (no cove detail drawn; T-283 ledger is research, not a line): no "
                "line is never HELD (R-T554-1 (d), as F-T570-5)"}
    cove = section("T-573/ceiling-cove", "T-573", "B7 ceilings: COVE / cornice runs", "lm", cv["his"], "0",
                   [row("his cornice runs (halls / rooms + kitchens / baths)", cv["his"], "UNRESOLVED", "lm",
                        "T-573 s.3", "WORKER_PROPOSED", reclass=m)],
                   basis="freelancer decor sheet, cornice runs 282.85 + 144.61 lm", verification=V573,
                   beside={"research_ledger_T283_m": d["cove_ledger_m"], "blank_faces": d["cove_ledger_blank_faces"],
                           "note": "a ledger beside, never valued"})
    moves.append({"section_id": cove["section_id"], "row": cove["rows"][0]["name"], **m})
    secs.append(cove)
    # STAIR soffits: carried once in V4 T-561/stair-soffit
    ss = [g for g in d["classes"]["groups"] if g["id"].startswith("STAIR soffits")][0]
    v4ss = v4s["T-561/stair-soffit"]
    if D(v4ss["reference_total"]) != D(ss["his"]) or D(v4ss["by_class"]["HELD"]) != -D(ss["causes"][0]["amount"]) \
            or D(v4ss["by_class"]["UNRESOLVED"]) != -D(ss["causes"][1]["amount"]):
        raise StatementError("T-573 stair soffits differ from V4 T-561/stair-soffit")
    secs.append({"section_id": "T-573/ceiling-stair-soffit", "report": "T-573", "kind": "CROSS_REFERENCE",
                 "unit": "m2", "trade": "B7 ceilings: STAIR soffits", "reference_counted_in": "T-561/stair-soffit",
                 "checked_equal": {"reference": ss["his"], "HELD": neg(ss["causes"][0]["amount"]),
                                   "UNRESOLVED": neg(ss["causes"][1]["amount"])},
                 "note": "counted once, in V4 T-561/stair-soffit; never added again (R-T579-1 (f))"})
    # DOME intrados: his NO_ROW
    nc.append({"block_id": "T-573/ceiling-dome", "report": "T-573", "trade": "B7 ceilings: DOME intrados", "unit": "m2",
               "status": "NOT_COMPARABLE", "reference_total": "NO_ROW", "difference": None,
               "difference_pct_of_reference": None, "engine_valued": None,
               "engine_held": "2 lines HELD, unbounded (DCR-4)", "verification": V573})
    # EXTERIOR soffits: his row 73 is a term of V4 T-552/plaster-external
    ex = [g for g in d["classes"]["groups"] if g["id"].startswith("EXTERIOR soffits")][0]
    v4x = [r for r in v4s["T-552/plaster-external"]["rows"] if r["name"].startswith("his row 73 ")]
    if sum((D(r["delta"]) for r in v4x), D(0)) != D(ex["his"]):
        raise StatementError("T-573 exterior soffit: his row 73 does not equal its V4 T-552/plaster-external rows")
    er = [c for c in ex["causes"] if c["verdict"] == "ENGINE_RIGHT"][0]
    only = [c for c in ex["causes"] if c["verdict"] == "NOT_IN_HIS_ROWS"][0]
    pool = D(ex["his"]) + D(er["amount"])
    secs.append({"section_id": "T-573/ceiling-exterior-soffit", "report": "T-573", "kind": "CROSS_REFERENCE",
                 "unit": "m2", "trade": "B7 ceilings: EXTERIOR soffits (over outside air)",
                 "reference_counted_in": "T-552/plaster-external (his row 73: " + "; ".join(
                     f"{r['class']} {r['delta']}" for r in v4x) + ")",
                 "face_class_view": {"pool_court_PL-03": {"reference": ex["his"], "engine": s(pool),
                                                         "difference": neg(er["amount"]), "class": "ENGINE_RIGHT"},
                                     "PL-01 / -02 / -04 / -05": {"reference": "NO_ROW", "engine": only["amount"],
                                                                 "status": "NOT_COMPARABLE"}},
                 "engine_total_5_lines": ex["ours"], "difference_pct_of_reference": None,
                 "note": "face-class view only; never added to a ceiling or plaster total (R-T579-1 (f))",
                 "verification": V573})
    # CEILING PAINT
    pg = d["paint"]["groups"][0]
    prow = []
    for c in pg["causes"]:
        if c["verdict"] == "BY_TABLE":
            for k in CLASSES:
                v = D(board["by_class"][k])
                if v:
                    prow.append(row(f"board gap by the BOARD table: {k}", v, k, "m2", "T-573 s.4 = s.2",
                                    "AS T-573/ceiling-board"))
            if sum((D(r["delta"]) for r in prow), D(0)) != -D(c["amount"]):
                raise StatementError("T-573 paint: BY_TABLE does not equal the board gap")
        elif c["verdict"] in NOT_A_CLASS:
            to, tag, why = NOT_A_CLASS[c["verdict"]]
            mv = {"tag": tag, "from": c["verdict"], "to": to, "delta": neg(c["amount"]), "why": why}
            prow.append(row(f"paint: {c['label']}", neg(c["amount"]), to, "m2", c.get("source", ""),
                            "WORKER_PROPOSED", source_class=c["verdict"], reclass=mv))
            moves.append({"section_id": "T-573/ceiling-paint", "row": prow[-1]["name"], **mv})
        else:
            kw = {"bound": c["bound"]} if c.get("bound") else {}
            if c["verdict"] == "HELD" and D(c["amount"]) == 0:
                kw["item"] = "GF-RFD4E1D bulkhead paint (depth not decided)"
            prow.append(row(f"paint: {c['label']}", neg(c["amount"]), c["verdict"], "m2", c.get("source", ""),
                            "CHECKER_CONFIRMED" if c["verdict"] == "RULE_DIFFERENCE" else "WORKER_PROPOSED", **kw))
    pt = d["paint"]["totals"]["m2"]
    paint = section("T-573/ceiling-paint", "T-573", "B6 ceiling paint (FIN.PAINT.CEILING, 31 lines)", "m2", pt["his"],
                    pt["ours"], prow, basis="freelancer decor paint rows 47-50 (board + cove-light strips 0.10 m)",
                    verification=V573,
                    beside={"headline_pct_NOT_a_verdict": {"difference_pct_of_reference": pct_of(pt["his"], pt["ours"]),
                                                           "engine_vs_reference_pct": pt["pct"]}})
    secs.append(paint)
    return secs, nc, moves


# ================================================================================ T-569 manifest rows (beside) ====
def t569_manifest(d: dict, index: dict, v4: dict) -> dict:
    """R-T579-1 (c): manifest rows beside; planned element ids absent from the pinned index; switch conditions."""
    elements = {ln.get("element_id") for ln in index.values()}
    planned = [f["paint_row"]["element_id"] for f in d["return_paint"]["valued"] + d["return_paint"]["held"]] + \
              [r["expected_after"]["element_id"] for r in d["rebar_omission"]["rows"]]
    present = [e for e in planned if e in elements]
    if present:
        raise StatementError(f"T-569 manifest rows already candidate lines: {present[:3]}")
    rp = d["return_paint"]
    vsum = sum((D(str(f["paint_row"]["bound_beside_m2"][1])) for f in rp["valued"]), D(0))
    v4p = [r for c in v4["sections"] if c["section_id"] == "T-561/paint-internal" for r in c["rows"]
           if r.get("source_cause") == "ENGINE_OMISSION"][0]
    if vsum != D(v4p["delta"]) or len(rp["valued"]) != 26:
        raise StatementError(f"T-569 return paint bound {vsum} != V4 ENGINE_WRONG row {v4p['delta']}")
    w = d["w17"]
    if D(str(w["before"]["settled_m2"])) + D(str(w["expected_after"]["m2_change"])) != D(str(w["expected_after"]
                                                                                       ["settled_m2"])):
        raise StatementError("T-569 W17: 23.285 + 9.870 != 33.155")
    rows = [
        {"id": "RETURN_PAINT_FACES", "candidate_line": False, "evidence_status": "HELD (frame-covered depth not "
         "printed)", "planned": f"{len(rp['valued'])} FIN.PAINT rows HELD blank, bound 0 .. {s(vsum)} m2 + "
         f"{len(rp['held'])} HELD by name", "statement_row": "V4 T-561/paint-internal 'RETURN: return faces' "
         f"(ENGINE_WRONG {v4p['delta']} m2, omission bound 0 .. {v4p['omission_bound_m2'][1]})",
         "switch_condition": "the 30 FIN.PAINT return lines exist in the candidate (Gate B RETURN_PAINT_FACES): then "
         "the row restates ENGINE_WRONG -> HELD <= 23.07 (F-C-T570-1); until then it stays ENGINE_WRONG at the face "
         "area with the bound beside", "valued_column_change": "0"},
        {"id": "FLOOR_CLASS_A08:1F-RFFE7AF", "candidate_line": False, "evidence_status": d["dressing_class"]
         ["evidence_status"], "planned": "label only (2.970 m2 unchanged)", "statement_row": "V4 T-553/floor-tile "
         "beside expected_after_fix_T564", "switch_condition": "label lands with the V7 package; EXPECTED stays "
         "beside, never valued", "valued_column_change": "0"},
        {"id": "PIER_RETURNS_EXT", "candidate_line": False, "evidence_status": d["pier_returns"]["evidence_status"],
         "planned": f"ledger of FIN.EXT.FINISH 1F {d['pier_returns']['owner_line']} (HELD blank, T-314)",
         "statement_row": "V4 T-552/plaster-external (engine 0, HELD)", "switch_condition": "none while the facade "
         "lines stay HELD (T-314)", "valued_column_change": "0"},
        {"id": "W17_Q76A", "candidate_line": False, "evidence_status": w["evidence_status"],
         "planned": f"HELD {w['before']['held_line']} retires; 1F settled {w['before']['settled_m2']} -> "
         f"{w['expected_after']['settled_m2']} m2", "statement_row": "T-568/windows-m2 beside "
         "expected_after_V8_W17_row", "switch_condition": "the 1F settled line reads 33.155 in the candidate",
         "valued_column_change": "0"},
        {"id": "REBAR_OMISSION", "candidate_line": False, "evidence_status": d["rebar_omission"]["evidence_status"],
         "planned": f"{d['rebar_omission']['lines']} STR.REBAR rows HELD blank (domes, rings, lift-pit walls)",
         "statement_row": "T-560/rebar G2 / G5 engine_omission_of_a_line", "switch_condition": "the rows exist: the "
         "omission note becomes 'HELD blank lines'; the group stays RULE_DIFFERENCE (TYPED_LUMP)",
         "valued_column_change": "0"}]
    return {"block_id": "T-569/manifest-v8", "kind": "MANIFEST_ROWS_BESIDE", "rows": rows,
            "planned_element_ids_checked_absent": len(planned), "verification": V569}


def refuse_manifest_as_line(st: dict) -> None:
    for blk in st.get("manifest_beside", []):
        for r in blk["rows"]:
            if r["candidate_line"] is not False or r["valued_column_change"] != "0":
                raise StatementError(f"manifest row {r['id']} shown as a candidate line (R-T579-1 (c))")
    for c in st.get("sections_v5", []):
        for r in c.get("rows", []):
            if "WIRING MANIFEST" in r.get("source", "") or r.get("manifest_row"):
                raise StatementError(f"{c['section_id']}: a manifest row inside the valued rows")
