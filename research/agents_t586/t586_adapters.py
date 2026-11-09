"""T-586: reconciled-quantities statement V6 adapters for the merged T-571 (precast lintel count, nr; lm beside),
T-574 (skirting, lm and nr apart; outline vs deduction terms), T-575 (dome / ring / lift-wall rebar HELD ranges, t) and
T-577 (marble / thresholds / sills / steps by unit: m2, lm, nr apart). Research, unwired: computes no new quantity;
reads the committed, sha256-pinned research outputs only (no drawing, workbook or client data). T-576 (not merged) and
T-578 (READY, not merged) at claim time: pending.

Statement sign (as V4 / V5): reference - engine; + = in the reference only. The source reports print ours - his: every
amount is negated once here, and every section re-adds to reference - engine with residual 0 (t579 close_section).

R-T586-1 (proposed, every villa). A statement that takes in a later report:
  (a) NO ROW, NO %: a reference with no row of its own for the element (lintels) is a NOT_COMPARABLE block (NO_ROW);
      a figure BUILT from his other rows through an owner rule (an "implied" count) is its own section labelled
      FREELANCER_IMPLIED, compared in nr only, never with a %, and never read as his figure;
  (b) LENGTH IN AN AREA COLUMN: a reference cell whose own dimension cells are count x length is a length, whatever the
      column label; it never enters an m2 reference total; it closes his printed total as a UNIT block and is compared
      in lm from his own count x length cells;
  (c) HELD_RANGE IS NOT A POINT: a held range is printed low .. high (or HELD_BLANK with the blank named), valued 0;
      a range with no low / no high, or one carried as a value, is refused; a range keyed to a wiring-manifest row
      (not a candidate line) stays beside (R-T579-1 (c)) and never enters a group's held column;
  (d) UNITS: t once at the boundary; a row in kg inside a t section is refused; nr / lm / m2 each their own section;
  (e) NOT A CLASS, MAPPED BY NAME: AGREE terms (netting to 0 inside their group) are listed beside, never a class row; ENGINE_OMISSION that the
      Checker holds PLAUSIBLE only is UNRESOLVED with its F-T586 tag; a source verdict outside the map is refused;
  (f) OUTLINE vs DEDUCTION: a perimeter-type reference that makes no deduction is compared gross vs gross (outline
      terms) beside the deduction terms; the net % is printed NOT a verdict.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T579 = ROOT / "research/agents_t579"
if str(T579) not in sys.path:
    sys.path.insert(0, str(T579))
import t579_adapters as Z  # noqa: E402  (T-579, read only)

D = Decimal
StatementError = Z.StatementError
s, row, close_section, pct_of = Z.s, Z.row, Z.close_section, Z.pct_of

T571_JSON = ROOT / "research/agents_t571/out/T571_LINTEL_COUNT.json"
T574_JSON = ROOT / "research/agents_t574/out/T574_SKIRTING_RECONCILE.json"
T575_JSON = ROOT / "research/agents_t575/out/T575_DOME_LIFT_REBAR.json"
T577_JSON = ROOT / "research/agents_t577/out/T577_MARBLE_RECONCILE.json"
PINS = {
    T571_JSON: "ede7c1fd982e42f90ace54a2f3ccd2dcc0274506d37277cf5975b054d26cbc84",
    T574_JSON: "7b1e01bf83c20702bad3ed58689915c57bac5e3a179bf33195816c67435abab8",
    T575_JSON: "8a0d3f6771109347b97ba2340ae44a61feabf3f725e0aaec374ff4b450c0b24c",
    T577_JSON: "b1b684a3478982b7c80d6f25a6acf0c8dea4dfaa80449f0866e373cee2ddb320",
}

# Checker verdicts (board, verifier 2026-11-06), quoted as classes only
V571 = ("Checker 2026-11-06 21:57 (T-571 Gate A): his workbooks have NO lintel row (CONFIRMED); his 54 deducted "
        "openings through the owner rule 27 / 17 / 8 / 1 / 1 nr, 84.9 lm and the engine 60 AT_MOST re-derived by hand: "
        "counts AGREE both sides; lintel vs freelancer NOT_COMPARABLE as a figure; implied +6 nr RULE_DIFFERENCE / "
        "UNRESOLVED as named; F-C-T571-1 D-GF-09 width basis (attribution only, no count moves)")
V574 = ("Checker 2026-11-06 21:58 (T-574 Gate A) PARTIALLY VERIFIED 1 / 11 room outlines (GF dewaneya 20.127876 lm "
        "DRAWING-CONFIRMED); arithmetic re-added; deductions worker-proposed, not re-measured; his room perimeters not "
        "re-read (register reused as data); stair flights HELD >= 17.009049, 96 nr pieces not converted, yard UNRESOLVED")
V575 = ("Checker 2026-11-06 23:56 (T-575 Gate A): shell / ring / lift-wall classes re-derived AGREE; every row HELD_RANGE "
        "or HELD_BLANK, valued 0; freelancer TYPED_LUMP NOT_COMPARABLE, no %; dome shells + rings ENGINE_OMISSION now "
        "bounded HELD (CONFIRMED); DOME-3 and lift walls UNRESOLVED; F-C-T575-1 the lift-wall A low is not a strict "
        "lower bound (row HELD_BLANK, nothing moves)")
V577 = ("Checker 2026-11-06 23:58 (T-577 Gate A) PARTIALLY VERIFIED: freelancer side 3 / 3 units re-read (AGREE), "
        "engine side 0 / 8 groups re-measured; LENGTH_IN_AREA_COLUMN never compared; E1 step-lm ENGINE_OMISSION "
        "PLAUSIBLE, not confirmed; external door steps UNRESOLVED element")

# (e) source verdicts that are not statement classes, mapped once by name
NOT_A_CLASS = {
    "ENGINE_OMISSION": ("UNRESOLVED", "F-T586-1", "ENGINE_OMISSION PLAUSIBLE, not confirmed by the Checker (F-T577-1: "
                                                  "E1 carries no step-lm line, printed 4 x 2.80 = 11.20 lm)"),
}
AGREE = "AGREE"


def load(p: Path) -> dict:
    pin = PINS.get(p)
    if pin and Z.sha(p) != pin:
        raise StatementError(f"{p.relative_to(ROOT)}: sha256 differs from its pin")
    return json.loads(p.read_text(encoding="utf-8"))


def cls_of(verdict: str, where: str) -> tuple[str, str | None, str | None]:
    if verdict in Z.CLASSES:
        return verdict, None, None
    if verdict in NOT_A_CLASS:
        c, tag, why = NOT_A_CLASS[verdict]
        return c, tag, why
    raise StatementError(f"{where}: source verdict '{verdict}' is neither a class nor mapped by name (R-T586-1 (e))")


def cause_rows(groups: list[dict], unit: str, src: str, ver: str) -> tuple[list[dict], list[dict], list[dict]]:
    """ours - his causes -> reference - engine rows; AGREE (0) beside; non-classes mapped by name."""
    rows, agree, moves = [], [], []
    for g in groups:
        if g["unit"] != unit if "unit" in g else False:
            raise StatementError(f"{g['id']}: group unit {g['unit']} in a {unit} section (R-T586-1 (d))")
        gsum, asum = D(0), D(0)
        for c in g["causes"]:
            gsum += D(c["amount"])
            if c["verdict"] == AGREE:
                asum += D(c["amount"])
                agree.append({"group": g["id"], "label": c["label"], "kind": c["kind"], "amount": Z.neg(c["amount"])})
                continue
            k, tag, why = cls_of(c["verdict"], g["id"])
            kw = {"source_verdict": c["verdict"], "kind_of_cause": c["kind"]}
            if c.get("bound") is not None:
                kw["bound"] = c["bound"]
            if tag:
                kw.update(tag=tag, mapped_because=why)
                moves.append({"tag": tag, "section_id": src, "row": f"{g['id']}: {c['label']}", "from": c["verdict"],
                              "to": k, "delta": Z.neg(c["amount"])})
            rows.append(row(f"{g['id']}: {c['label']}", -D(c["amount"]), k, unit, f"{src} {g['id']}", ver, **kw))
        if asum != 0:
            raise StatementError(f"{g['id']}: AGREE terms net {asum}, not 0 (they must cancel inside the group)")
        if gsum != D(g["gap"]):
            raise StatementError(f"{g['id']}: causes {gsum} != group gap {g['gap']}")
    return rows, agree, moves


def refuse_pct_without_row(sec: dict) -> None:
    """(a) no % on a NO_ROW reference or an implied figure."""
    if sec.get("reference_kind") in ("NO_ROW", "FREELANCER_IMPLIED") and sec.get("difference_pct_of_reference"):
        raise StatementError(f"{sec['section_id']}: % on a {sec['reference_kind']} reference (R-T586-1 (a))")
    if sec.get("reference_total") in (None, "NO_ROW") and sec.get("difference_pct_of_reference"):
        raise StatementError(f"{sec['section_id']}: % with no reference row (R-T586-1 (a))")


def refuse_length_in_area(cells: list[dict], unit: str, where: str) -> None:
    """(b) a count x length cell never enters an m2 reference total."""
    for c in cells:
        if unit == "m2" and c.get("cell_class") == "LENGTH_IN_AREA_COLUMN":
            raise StatementError(f"{where}: cell {c['cell']} is count x length booked in an area column; never m2 "
                                 f"(R-T586-1 (b))")


def check_held_range(r: dict, unit: str) -> None:
    """(c) / (d) a HELD_RANGE is low .. high, valued 0; HELD_BLANK carries none and names its blank; t only."""
    if r.get("unit") != unit:
        raise StatementError(f"{r.get('row_id')}: row in {r.get('unit')} inside a {unit} block (R-T586-1 (d))")
    st = r.get("status")
    if st == "HELD_RANGE":
        lo, hi = r.get("t_low"), r.get("t_high")
        if lo is None or hi is None or D(str(lo)) <= 0 or D(str(hi)) < D(str(lo)):
            raise StatementError(f"{r.get('row_id')}: HELD_RANGE needs 0 < low <= high")
        if r.get("value") is not None or r.get("valued") not in (None, 0, "0"):
            raise StatementError(f"{r.get('row_id')}: HELD_RANGE carried as a point / value (R-T586-1 (c))")
    elif st == "HELD_BLANK":
        if r.get("t_low") is not None or r.get("t_high") is not None or not r.get("missing"):
            raise StatementError(f"{r.get('row_id')}: HELD_BLANK with a figure or no named blank")
    else:
        raise StatementError(f"{r.get('row_id')}: status {st} is not HELD_RANGE / HELD_BLANK")


# ================================================================================ T-571 lintels (nr) ==============
LENGTHS = ("1.2", "1.5", "2.5", "3.0", "4.0")
T571_CLASS = {  # per pair cause / opening, Checker (f) statuses
    ("WIDTH_READ", "D-GF-03"): "RULE_DIFFERENCE", ("WIDTH_READ", "D-GF-09"): "RULE_DIFFERENCE",
    ("WIDTH_READ", "P-GF-01"): "UNRESOLVED", ("NOT_IN_MASONRY", "W17"): "UNRESOLVED",
    ("ENGINE_ONLY", None): "UNRESOLVED",
}


def _nr(table: dict) -> dict:
    return {L: sum(table[L].values()) for L in LENGTHS}


def t571_sections(d: dict) -> tuple[list[dict], list[dict]]:
    eng, his = d["engine_owner_0.15"], d["freelancer_owner_0.15"]
    e_by, h_by = _nr(eng["at_most"]), _nr(his["at_most"])
    if sum(e_by.values()) != eng["total_at_most_nr"] or sum(h_by.values()) != his["total_at_most_nr"]:
        raise StatementError("T-571: count tables do not re-add to their totals")
    rows, by_len = [], {L: 0 for L in LENGTHS}
    for p in d["pairs_owner_0.15"]:
        if p["cause"] == "SAME_PIECE":
            if p["piece_ours"] != p["piece_theirs"]:
                raise StatementError(f"T-571 {p['ours']}: SAME_PIECE with two pieces")
            continue
        delta = {L: 0 for L in LENGTHS}
        if p.get("piece_theirs") is not None:
            delta[s(D(str(p["piece_theirs"])).quantize(D("0.1")))] += 1
        if p.get("piece_ours") is not None and p["state_ours"] != "NO_LINTEL":
            delta[s(D(str(p["piece_ours"])).quantize(D("0.1")))] -= 1
        if not any(delta.values()) and p["cause"] == "NOT_IN_MASONRY":
            continue                                  # NO_LINTEL on both sides: in neither count
        key = (p["cause"], p["ours"]) if (p["cause"], p["ours"]) in T571_CLASS else (p["cause"], None)
        if key not in T571_CLASS:
            raise StatementError(f"T-571 {p['ours']}: cause {p['cause']} has no Checker class")
        for L in LENGTHS:
            by_len[L] += delta[L]
        rows.append(row(f"{p['ours']} vs {p.get('theirs') or 'no row of his'}: {p['cause']}", sum(delta.values()),
                        T571_CLASS[key], "nr", "T-571 s.3 pairs (owner rule b = 0.15)", V571,
                        by_length_nr={L: v for L, v in delta.items() if v}, state_ours=p["state_ours"]))
    for L in LENGTHS:
        if by_len[L] != h_by[L] - e_by[L]:
            raise StatementError(f"T-571 @{L}: causes {by_len[L]} != implied - engine {h_by[L] - e_by[L]}")
    sec = Z.section("T-571/lintel-count-implied", "T-571", "B9-02 precast lintels, count by stock length (owner "
                    "manual method, BESIDE: the printed RC schedule governs, precast NOT_APPLICABLE)", "nr",
                    his["total_at_most_nr"], eng["total_at_most_nr"], rows,
                    basis="his 54 deducted openings of the blockwork workbook put through the owner rule (implied; "
                          "not his figure: he has no lintel row)",
                    kind="IMPLIED_COUNT", verification=V571, reference_kind_override=True)
    sec["reference_kind"] = "FREELANCER_IMPLIED"
    sec["engine_basis"] = "AT_MOST: every masonry opening of the V3.0.58 lintel lines built (60); ESTABLISHED 16"
    sec["by_length"] = {L: {"implied": h_by[L], "engine_at_most": e_by[L], "difference": h_by[L] - e_by[L]}
                        for L in LENGTHS}
    sec["engine_established_nr"] = eng["total_established_nr"]
    sec["pct_refused_because"] = "the reference has no lintel row: an implied count carries no % (R-T586-1 (a))"
    sec["beside_lm"] = {"unit": "lm", "implied": s(sum(D(str(v)) for v in his["lm_beside_at_most"].values())),
                        "engine_at_most": s(sum(D(str(v)) for v in eng["lm_beside_at_most"].values())),
                        "note": "count x stock length, beside the nr section, never summed with it"}
    refuse_pct_without_row(sec)
    nc = {"block_id": "T-571/lintel-figure", "report": "T-571", "trade": "B9-02 lintels (concrete / pieces)",
          "unit": "nr", "status": "NOT_COMPARABLE", "reference_total": "NO_ROW", "difference": None,
          "difference_pct_of_reference": None, "engine_valued": None,
          "information": "no lintel row in any of his workbooks; his cost-sheet lintel line is money (a lump), not a "
                         "quantity", "verification": V571}
    return [sec], [nc]


# ================================================================================ T-574 skirting (lm, nr) ========
def t574_sections(d: dict, candidate_lm: str) -> tuple[list[dict], list[dict], list[dict]]:
    secs, nc, allmoves, allagree = [], [], [], []
    room = d["room"]
    rrows, ragree, mv = cause_rows(room["groups"], "lm", "T-574/skirting-room", V574)
    allmoves += mv
    rt = room["totals"]["lm"]
    sec = Z.section("T-574/skirting-room", "T-574", "B6 skirting, dry rooms", "lm", rt["his"], rt["ours"], rrows,
                    basis="his tiles-sheet room perimeters (12 dry rooms, gross, no deduction; register "
                          "FREELANCER_RAW_ROWS, not re-read by the Checker)", verification=V574)
    out_t = {k: D(0) for k in ("OUTLINE", "DEDUCTION")}
    for g in room["groups"]:
        for c in g["causes"]:
            if c["kind"] in out_t:
                out_t[c["kind"]] += D(c["amount"])
    gg = room["gross_vs_gross"]
    if out_t["OUTLINE"] != D(gg["outline_gap"]) or out_t["OUTLINE"] + out_t["DEDUCTION"] != D(rt["gap"]):
        raise StatementError("T-574: outline + deduction terms do not close the room gap")
    sec["beside"] = {"gross_vs_gross_outline_terms": {"reference_lm": gg["his"], "engine_outline_lm":
                                                      gg["ours_outline"], "difference": Z.neg(gg["outline_gap"]),
                                                      "difference_pct_of_reference":
                                                          pct_of(gg["his"], gg["ours_outline"])},
                     "deduction_terms_lm": Z.neg(out_t["DEDUCTION"]),
                     "net_pct_NOT_a_verdict": pct_of(rt["his"], rt["ours"]),
                     "agree_rows": ragree}
    secs.append(sec)
    st = d["stairs"]
    lm_g = [g for g in st["groups"] if g["unit"] == "lm"]
    nr_g = [g for g in st["groups"] if g["unit"] == "nr"]
    srows, sagree, mv = cause_rows(lm_g, "lm", "T-574/skirting-stairs", V574)
    allmoves += mv
    t = st["totals"]["lm"]
    sec = Z.section("T-574/skirting-stairs", "T-574", "B7 stair skirting (flights, landings)", "lm", t["his"],
                    t["ours"], srows, basis="his marble-sheet level skirting rows (entrance / main / inner round)",
                    verification=V574)
    sec["beside"] = {"agree_rows": sagree,
                     "flight_lower_bounds_lm": s(sum(D(c["bound"][0]) for g in lm_g for c in g["causes"]
                                                     if c["verdict"] == "HELD" and c.get("bound")
                                                     and D(c["amount"]) != 0))}
    secs.append(sec)
    if D(rt["ours"]) + D(t["ours"]) != D(candidate_lm):
        raise StatementError("T-574: room + stair valued != the candidate FIN.SKIRTING released")
    prow, pagree, mv = cause_rows(nr_g, "nr", "T-574/skirting-pieces", V574)
    t = st["totals"]["nr"]
    sec = Z.section("T-574/skirting-pieces", "T-574", "B7 stair-side skirting pieces per step", "nr", t["his"],
                    t["ours"], prow, basis="his pieces per step (count, never converted to lm)", verification=V574)
    sec["pct_refused_because"] = "UNIT cause (his pieces vs our lm lines): no % (R-T574-1 (e))"
    secs.append(sec)
    od = d["outdoor"]
    orow, oagree, mv = cause_rows(od["groups"], "lm", "T-574/skirting-outdoor", V574)
    t = od["totals"]["lm"]
    secs.append(Z.section("T-574/skirting-outdoor", "T-574", "outdoor court / yard skirting", "lm", t["his"],
                          t["ours"], orow, basis="his yard skirting row", verification=V574))
    return secs, nc, allmoves


# ================================================================================ T-575 rebar ranges (t) ==========
def t575_beside(d: dict, v5: dict, v8: dict) -> dict:
    v8ids = {r["expected_after"]["element_id"]: r for r in v8["rebar_omission"]["rows"]}
    rows, lo, hi = [], D(0), D(0)
    for r in d["rows"]:
        check_held_range(r, "t")
        if r["row_id"] not in v8ids:
            raise StatementError(f"T-575 {r['row_id']}: not a V8 REBAR_OMISSION row")
        if v8ids[r["row_id"]]["concrete_line"] != r["concrete_line"]:
            raise StatementError(f"T-575 {r['row_id']}: concrete line differs from V8")
        x = {"row_id": r["row_id"], "status": r["status"], "concrete_line": r["concrete_line"],
             "concrete_class": r["concrete_class"], "unit": "t"}
        if r["status"] == "HELD_RANGE":
            x["range_t"] = [s(D(str(r["t_low"]))), s(D(str(r["t_high"])))]
            lo += D(str(r["t_low"]))
            hi += D(str(r["t_high"]))
        else:
            x["blank_named"] = r["missing"]
        x["t560_group"] = "G2_COLUMNS_NECKS_WALLS" if r["row_id"].startswith("LIFT_PIT") else "G5_STAIRS_DOME"
        rows.append(x)
    tt = d["totals"]
    if (s(lo), s(hi)) != (s(D(str(tt["t_low"]))), s(D(str(tt["t_high"])))) or tt["valued_t"] != 0.0:
        raise StatementError("T-575: rows do not re-add to its totals, or something is valued")
    r560 = [c for c in v5["sections_v5"] if c["section_id"] == "T-560/rebar"][0]
    g5 = [x for x in r560["rows"] if x["name"].startswith("G5_")][0]
    g5lo, g5hi = (D(v) for v in g5["engine_held_range_t"])
    dome_lo = sum((D(x["range_t"][0]) for x in rows if x["t560_group"] == "G5_STAIRS_DOME" and "range_t" in x), D(0))
    dome_hi = sum((D(x["range_t"][1]) for x in rows if x["t560_group"] == "G5_STAIRS_DOME" and "range_t" in x), D(0))
    his, val = D(g5["his_t"]), D(g5["engine_valued_t"])
    return {
        "block_id": "T-575/dome-lift-rebar", "kind": "HELD_RANGE_BESIDE", "report": "T-575", "unit": "t",
        "candidate_line": False, "valued_t": "0", "range_t": [s(lo), s(hi)],
        "held_blank_rows": sum(1 for x in rows if x["status"] == "HELD_BLANK"), "rows": rows,
        "reference": "his 44.19 t TYPED_LUMP (T-560): NOT_COMPARABLE, no %",
        "statement_effect": "none on any V5 column: the six rows are WIRING MANIFEST V8 REBAR_OMISSION rows, not "
                            "candidate lines (R-T579-1 (c)); the T-560/rebar G5 omission is now BOUNDED beside",
        "expected_after_v8_rebar_rows": {
            "group": "G5_STAIRS_DOME", "v5_held_range_t": g5["engine_held_range_t"],
            "plus_t575_t": [s(dome_lo), s(dome_hi)],
            "held_range_t": [s(g5lo + dome_lo), s(g5hi + dome_hi)],
            "residual_after_bounded_held_t": [s(his - val - g5hi - dome_hi), s(his - val - g5lo - dome_lo)],
            "note": "EXPECTED only, never valued; the west ring's B4 tag may put it in his BEAMS family (T-575 "
                    "text G5 / G3): group attribution of that ring UNRESOLVED, no split of the lump"},
        "g2_lift_walls": "HELD_BLANK: kg(h) = A h + B beside in T-575 (h not printed); F-C-T575-1: A low not strict",
        "verification": V575,
    }


# ================================================================================ T-577 marble by unit ===========
def _cells(groups: list[dict]) -> list[dict]:
    out = []
    for g in groups:
        unit_cause = any(c["kind"] == "UNIT" for c in g["causes"])
        for c in g.get("cells", []):
            out.append({"group": g["id"], "cell": c,
                        "cell_class": "LENGTH_IN_AREA_COLUMN" if unit_cause else "AREA"})
    return out


def t577_sections(d: dict) -> tuple[list[dict], list[dict], list[dict]]:
    secs, nc, moves = [], [], []
    tm = d["tables"]
    # m2: his length-in-area cells leave the reference total (b); his area cells stay
    m2g = tm["m2"]["groups"]
    cells = _cells(m2g)
    unit_cells = [c for c in cells if c["cell_class"] == "LENGTH_IN_AREA_COLUMN"]
    area_cells = [c for c in cells if c["cell_class"] == "AREA"]
    refuse_length_in_area(area_cells, "m2", "T-577/marble-m2")
    unit_amt = D(0)
    groups2 = []
    for g in m2g:
        u = [c for c in g["causes"] if c["kind"] == "UNIT"]
        unit_amt += sum((D(c["amount"]) for c in u), D(0))
        g2 = dict(g, causes=[c for c in g["causes"] if c["kind"] != "UNIT"])
        g2["gap"] = s(D(g["gap"]) - sum((D(c["amount"]) for c in u), D(0)))
        groups2.append(g2)
    his_area = D(tm["m2"]["totals"]["his"]) + unit_amt          # unit causes are -his length cells
    rows, agree, mv = cause_rows([dict(g, unit="m2") for g in groups2], "m2", "T-577/marble-m2", V577)
    moves += mv
    sec = Z.section("T-577/marble-m2", "T-577", "marble / stone thresholds, sills, lift and E1 stone (m2)", "m2",
                    his_area, tm["m2"]["totals"]["ours"], rows,
                    basis="his marble-sheet AREA cells of these elements only (E1 landing); his count x length cells "
                          "booked in the area column are lengths and leave this total (R-T586-1 (b))",
                    verification=V577)
    sec["pct_refused_because"] = "HELD / SCOPE causes (R-T577-1 (e))"
    sec["beside"] = {"agree_rows": agree, "area_cells": [c["cell"] for c in area_cells]}
    secs.append(sec)
    nc.append({"block_id": "T-577/length-in-area-column", "report": "T-577", "trade": "his door steps and entrance "
               "steps booked in his area column", "unit": "lm (in his m2 column)", "status": "NOT_COMPARABLE",
               "reference_total": s(-unit_amt), "difference": None, "difference_pct_of_reference": None,
               "engine_valued": None, "cells": [c["cell"] for c in unit_cells],
               "information": "count x length booked in his area column (UNIT, F-T577-3): never compared as m2; the "
                              "same elements are compared in T-577/marble-lm from his own count x length cells",
               "verification": V577})
    for unit in ("lm", "nr"):
        rows, agree, mv = cause_rows([dict(g, unit=unit) for g in tm[unit]["groups"]], unit, f"T-577/marble-{unit}",
                                     V577)
        moves += mv
        t = tm[unit]["totals"]
        sec = Z.section(f"T-577/marble-{unit}", "T-577", f"marble / stone thresholds, sills, lift and E1 stone "
                        f"({unit})", unit, t["his"], t["ours"], rows,
                        basis="his own count x length cells (lm) / count cells (nr) of these elements",
                        verification=V577)
        sec["pct_refused_because"] = "HELD / SCOPE / UNIT causes (R-T577-1 (e))"
        sec["beside"] = {"agree_rows": agree}
        secs.append(sec)
    return secs, nc, moves
