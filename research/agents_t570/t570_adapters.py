"""T-570: reconciled-quantities statement adapters V4 for the merged T-561 (B6 wall paint, m2), T-564 (B3 floor tile
expected after the V7 fix row, m2), T-565 (B1 earthworks: NO_ROW, NOT_COMPARABLE), T-566 (B10 GF / 1F column marks:
2 positions CONFLICT; B10-07 beam UNTRACED residual by mark, m3) and T-567 (B5 external plaster, gross vs gross, net vs
net, m2). Research, unwired: computes no new quantity, reads committed research outputs and the V3.0.57 line index
only; no drawing, workbook or client data.

The T-548 builder (R-T548-1), the T-554 / T-557 / T-562 adapters are IMPORTED READ ONLY; every section is still closed
by the T-548 builder. This module adds R-T570-1 (proposed, every villa). A statement that takes in a later report:
  (a) ENGINE OMISSION: a component whose element has NO candidate line at all (T-561 door-return paint) is never
      printed HELD (a HELD row names a held line, and inventing one is refused) and never agreement: it is classed
      ENGINE_WRONG with the fix row that adds the line, the source cause ENGINE_OMISSION and the omission bound
      [0, upper] beside; its expected class after the fix (HELD) rides on the row (precedent F-T553-1, the missing
      dressing floor line);
  (b) NO_ROW IS NOT A REFERENCE: a family the reference prices nowhere (T-565 earthworks) is printed as a
      NOT_COMPARABLE block outside the closed sections: engine figures by basis (IN_SITU / COMPACTED m3 apart), his
      side NO_ROW, no difference and no % cell; a NO_ROW written as 0, a % or a difference on such a block is refused;
  (c) CONFLICT IS NEVER RESOLVED IN THE STATEMENT: where a drawing prints two marks for one position (T-566), the
      rows keep the reported split, labelled 'reading of record, CONFLICT not resolved', and beside it the class totals
      of EVERY reading with their [min, max] per class; a single reading printed as the resolution, a missing reading
      or a reading whose storey residual differs is refused;
  (d) GROSS WITH GROSS, NET WITH NET: a facade restatement (T-567) closes the reference gross against the engine
      gross; each side's net is printed beside with its own opening rule, and a pair of a net with a gross is refused;
      a report verdict that is not a class (ROUNDING) is mapped once by name (TOLERANCE);
  (e) EXPECTED IS NOT VALUED: a fix row's expected-after figure (T-564: floor tile + 2.970 m2) is printed beside the
      as-valued figure with both percentages, labelled EXPECTED (not wired) with the evidence status of every added
      part (dressing finish A08 ESTIMATED, F-C-T564-1); it never enters the engine valued or bounded columns.
"""
from __future__ import annotations

import copy
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T562 = ROOT / "research/agents_t562"
for p in (T562, ROOT / "research/agents_t557", ROOT / "research/agents_t554", ROOT / "research/agents_t548"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t562_adapters as Y  # noqa: E402  (T-562, read only)

X, SA, S, A, D = Y.X, Y.SA, Y.S, Y.A, Y.D
label, require_range, _held_entry, _index_lines = Y.label, Y.require_range, Y._held_entry, Y._index_lines
AdapterError = Y.AdapterError

T561_JSON = ROOT / "research/agents_t561/out/T561_PAINT_RECONCILE.json"
T564_JSON = ROOT / "research/agents_t564/WIRING_MANIFEST_V7.json"
T565_JSON = ROOT / "research/agents_t565/out/T565_EARTHWORKS_RECONCILE.json"
T566_JSON = ROOT / "research/agents_t566/out/T566_REGISTRATION.json"
T567_JSON = ROOT / "research/agents_t567/out/T567_EXT_RECONCILE.json"
T567_CSV = ROOT / "research/agents_t567/out/COMPONENTS_T567.csv"
T551_JSON = Y.T551_JSON


def _row(name, delta, cls, src, est, ids, source, note="") -> dict:
    return Y._row(name, delta, cls, src, est, ids, source, note)


def _move(row, to, est, ids, why, tag) -> dict:
    return Y._move(row, to, est, ids, why, tag)


def _q(x) -> Decimal:
    return D(x).normalize()


# ============================================================================================ T-561 paint (m2) ======
T561_VERDICT = ("Checker 2026-11-06 13:55 (T-561 Gate A) PARTIALLY VERIFIED: his side 26 / 26 rows (own read of his paint "
                "workbook), engine faces 2 / 4 released lines (2F-03 18.90 x 3.35, 1F-04 17.40 x 3.35 own re-measure); "
                "WHO IS RIGHT height G1 vs his flat RULE_DIFFERENCE (Q-48 A), soffits RULE_DIFFERENCE of class (CEILING), "
                "ENGINE_OMISSION paint return line CONFIRMED as a fact (HELD <= 23.07), UNRESOLVED 64.73 by name stands")
T561_WORKER = ("T-561 worker class (GF-15 face, the 7 HELD lines, the opening deductions, the shaft T-173 175.14 and the "
               "T-281 soffit rows not re-measured by the Checker)")
T561_TRADE = "B6 wall paint internal"
T561_SOFFIT_TRADE = "B6 stair soffit paint (CEILING class, in his wall-paint rows 18-19)"
T561_FIX = "T-569"                       # Lead 16:17: fix row (1) T-561 ENGINE_OMISSION paint returns
T561_FACES_CONFIRMED = ("1F-04", "2F-03")
WALL_PAIRS = ("DRY", "SHAFT", "RETURN")
SOFFIT_PAIR = "CEILING (stair soffits in his wall paint)"


def t561_sections(index: dict, json_path: Path = T561_JSON) -> list[dict]:
    return t561_from(json.loads(json_path.read_text(encoding="utf-8")), index)


def t561_from(d: dict, index: dict, fix_row: str = T561_FIX) -> list[dict]:
    """Two m2 sections from a T-561-format report + the index (any villa): wall paint (DRY + SHAFT + RETURN) against
    his wall rows, and the stair soffits he prices inside his wall paint against the CEILING-class soffit lines.
    Statement sign = his - engine (the report's own sign)."""
    it = d["internal"]
    pairs = it["pairs"]
    if set(pairs) != set(WALL_PAIRS) | {SOFFIT_PAIR}:
        raise AdapterError(f"T-561: pairs {sorted(pairs)} differ from the adapter table")
    for k, p in pairs.items():                       # each pair closes to its own gap (the report's own rule)
        acc = sum((D(r["delta"]) for r in p["rows"]), Decimal(0))
        if acc != D(p["gap"]) or D(p["freelancer_gross"]) - D(p["engine_valued"]) != D(p["gap"]):
            raise AdapterError(f"T-561 {k}: rows {acc} != gap {p['gap']}")
    if sum((D(p["gap"]) for p in pairs.values()), Decimal(0)) != D(it["gap_gross"]):
        raise AdapterError("T-561: pairs do not add to the internal gross gap")
    pl = _index_lines(index, {"FIN.PAINT"})
    valued = [{"line_id": x["line_id"], "qty": S.s(D(x["measured_net"])), "unit": "m2"} for x in pl["RELEASED"]]
    v_tot = sum((D(x["qty"]) for x in valued), Decimal(0))
    if v_tot != D(it["engine_valued"]) or D(pairs["DRY"]["engine_valued"]) != v_tot:
        raise AdapterError(f"T-561: index FIN.PAINT released {v_tot} != report {it['engine_valued']}")
    held_ids = {x["line_id"] for x in pl["HELD"]}
    room_line = {r["room"]: r.get("paint_line_id") for r in pairs["DRY"]["rooms"]}
    rows = []
    # ---------------- DRY ----------------
    for r in pairs["DRY"]["rows"]:
        room = r["name"].split()[0]
        lid = room_line.get(room, "?")
        if lid == "?":
            raise AdapterError(f"T-561 DRY {r['name'][:40]}: room {room} not in the report's room table")
        row = _row(f"DRY {r['name']}", r["delta"], r["cause"], r["cause"], "VALUED", [], f"T-561 s.2 DRY ({r['source']})",
                   r.get("note", ""))
        ln = index.get(lid) if lid else None
        if lid and (ln is None or ln["item_code"] != "FIN.PAINT"):
            raise AdapterError(f"T-561 {room}: {lid} is not a FIN.PAINT line")
        if ln is None:                                            # GF-02: a wet space he paints and tiles
            row["engine_status"] = "NONE"
            row["note"] = (row["note"] + "; " if row["note"] else "") + \
                "no paint line by the owner wet-area rule (one finish per face, UP-FIN-PAINT-001): his row 9"
            label(row, "CHECKER_CONFIRMED", T561_VERDICT + " (wash row 9 6.75 x 3.60 = RD 25.92 + ER -1.62 AGREE)")
        elif ln["class"] == "HELD":
            if r["cause"] == "HELD":
                row.update({"engine_status": "HELD", "held_line_ids": [lid]})
            else:
                _move(row, "HELD", "HELD", [lid], f"component on the HELD paint line {lid} (R-T548-1 (e), R-T562-1 "
                      "(b)): the engine values nothing of this room; source class kept", "F-T570-2")
            label(row, "WORKER_PROPOSED", T561_WORKER)
        elif ln["class"] == "RELEASED":
            conf = (" height:" in r["name"]) or (room in T561_FACES_CONFIRMED and " length:" in r["name"])
            label(row, "CHECKER_CONFIRMED" if conf else "WORKER_PROPOSED", T561_VERDICT if conf else T561_WORKER)
        else:
            raise AdapterError(f"T-561 {room}: paint line {lid} is {ln['class']}")
        rows.append(row)
    # ---------------- SHAFT ----------------
    sh = sorted(x["line_id"] for x in pl["HELD"] if x["line_id"] in
                {c["line_id"] for c in pairs["SHAFT"]["candidate_lines"]})
    if len(sh) != len(pairs["SHAFT"]["candidate_lines"]):
        raise AdapterError("T-561 SHAFT: a shaft candidate line is not a HELD FIN.PAINT line")
    for r in pairs["SHAFT"]["rows"]:
        row = _row(f"SHAFT: {r['name']}", r["delta"], r["cause"], r["cause"], "HELD", sh, "T-561 s.2 SHAFT (T-173)",
                   r.get("note", ""))
        if r["cause"] == "UNRESOLVED":
            row.update({"engine_status": "NONE", "held_line_ids": []})
            label(row, "CHECKER_CONFIRMED", T561_VERDICT + " (his rows 25 / 8 read: 13.50 + 40.50, no drawn face)")
        else:
            if r["cause"] != "HELD":
                _move(row, "HELD", "HELD", sh, "his shaft box vs the drawing (T-173) on the 3 HELD shaft paint lines: "
                      "the engine values no shaft face (R-T548-1 (e))", "F-T570-2")
            label(row, "WORKER_PROPOSED", T561_WORKER)
        rows.append(row)
    # ---------------- RETURN ----------------
    ret = pairs["RETURN"]
    if not ret.get("engine_omission"):
        raise AdapterError("T-561 RETURN: the report no longer names the engine omission: re-read before restating")
    if any(x["element_id"].endswith("RETURN_PAINT") for x in pl["HELD"] + pl["RELEASED"]):
        raise AdapterError("T-561 RETURN: a FIN.PAINT return line exists in the index: the omission is wired, use HELD")
    for r in ret["rows"]:
        if r["cause"] == "HELD":                                   # R-T570-1 (a)
            row = _row(f"RETURN: {r['name']}", r["delta"], "HELD", "ENGINE_OMISSION", "NONE", [],
                       "T-561 s.2 RETURN (ENGINE_OMISSION)", r.get("note", ""))
            row["fix_row"] = fix_row
            row["omission_bound_m2"] = ["0", S.s(D(r["delta"]))]
            row["expected_after_fix"] = {"class": "HELD", "fix_row": fix_row,
                                         "what": "one FIN.PAINT return line per plastered return, HELD on the frame "
                                                 "detail (painted part = return face - frame-covered depth)"}
            _move(row, "ENGINE_WRONG", "NONE", [], "no FIN.PAINT return line exists although every return is "
                  "plastered: a missing line is an engine error, never HELD without a line and never agreement "
                  f"(R-T570-1 (a)); the figure is the upper bound of the omission, fix row {fix_row}", "F-T570-1")
            label(row, "CHECKER_CONFIRMED", T561_VERDICT)
        else:
            row = _row(f"RETURN: {r['name']}", r["delta"], r["cause"], r["cause"], "NONE", [],
                       "T-561 s.2 RETURN", "his 14 doors x 0.20 x 5.70 not listed by id")
            label(row, "CHECKER_CONFIRMED", T561_VERDICT)
        rows.append(row)
    src = {}
    for k in WALL_PAIRS:
        for c, v in pairs[k]["by_cause"].items():
            src[c] = src.get(c, Decimal(0)) + D(v)
    his_wall = sum((D(pairs[k]["freelancer_gross"]) for k in WALL_PAIRS), Decimal(0))
    paint = {
        "section_id": "T-561/paint-internal", "report": "T-561", "trade": T561_TRADE, "item_codes": ["FIN.PAINT"],
        "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": S.s(his_wall), "unit": "m2",
                      "basis": f"freelancer paint workbook, wall statement rows 4-27 gross J28 {it['freelancer_gross']} "
                               f"less his stair-soffit rows 18-19 {pairs[SOFFIT_PAIR]['freelancer_gross']} (CEILING "
                               "class, own section) = dry 948.505 + shaft 244.92 + returns 15.96 (Checker own read "
                               "AGREE; equals his plaster gross row for row) (Drive 'Alsenan chalet project')"},
        "engine": {"valued_total": S.s(v_tot), "valued_lines": valued,
                   "held_lines": [_held_entry(x, f"{x['element_id']} HELD") for x in pl["HELD"]],
                   "excluded_lines": [{"line_id": x["line_id"]} for x in pl["EXCLUDED"]]},
        "rows": rows, "source_by_class": {k: S.s(v) for k, v in src.items()},
        "beside": {
            "his_net_m2": it["freelancer_net"], "his_half_deduction_m2": it["his_half_deduction"],
            "net_view_difference_m2_incl_soffits": it["gap_net"],
            "paint_height_basis": "finished ceiling (owner G1, Q-48 A; PROVISIONAL under Q-52 C, designer item): the "
                                  "4 released lines PROVISIONAL with the drawing-derived UPPER bound beside (Checker "
                                  "ACCEPTED); never the plaster height (T-556)",
            "two_methods_11_dry_lines_m2": {"owner_G1_gross": pairs["DRY"]["two_methods"]["owner_G1_gross_11_lines"],
                                            "drawing_derived_gross": pairs["DRY"]["two_methods"][
                                                "drawing_derived_gross_11_lines"],
                                            "released_lines": pairs["DRY"]["two_methods"]["released_lines"]},
            "return_omission": {"finding": "T-561 ENGINE_OMISSION", "fix_row": fix_row,
                                "bound_m2": ["0", S.s(D(ret["rows"][0]["delta"]))],
                                "outside_rows_plaster_returns_held": ret["outside"]},
            "external_paint": {"his_paint_workbook_external": "NO_ROW (his row 29 is an opening of his internal list)",
                               "engine_valued_m2": d["external"]["engine_valued_m2"],
                               "note": "his exterior coating is his exterior plaster area: reconciled once in "
                                       "T-552/plaster-external (T-567 restatement); never a 0 row here"},
            "ceiling_paint_not_here": d["ceiling_paint_beside"],
            "coats": d["coats"]}}
    # ---------------- stair soffits (CEILING class) ----------------
    sp = pairs[SOFFIT_PAIR]
    so = _index_lines(index, {"FIN.STAIR.SOFFIT"})
    so_ids = sorted(x["line_id"] for x in so["HELD"])
    if so["RELEASED"] or sorted(c["candidate_line"] for c in sp["candidate_lines"]) != so_ids:
        raise AdapterError("T-561 soffits: the soffit candidate lines differ from the index (2 HELD blank)")
    srows = []
    for r, c in zip(sp["rows"], sp["candidate_lines"] + [None]):
        if r["cause"] == "HELD":
            if c is None or c["candidate_line"][:10] not in r["source"]:
                raise AdapterError(f"T-561 soffit row {r['name'][:30]}: its candidate line is not named in its source")
            row = _row(f"SOFFIT {r['name']}", r["delta"], "HELD", "HELD", "HELD", [c["candidate_line"]],
                       "T-561 s.2 CEILING pair (T-281 method D)", "CEILING class (Q-57): never a wall-paint face")
            label(row, "WORKER_PROPOSED", T561_WORKER)
        else:
            row = _row(f"SOFFIT {r['name']}", r["delta"], r["cause"], r["cause"], "HELD", so_ids,
                       "T-561 s.2 CEILING pair (named residual)", "both soffit lines HELD blank")
            label(row, "CHECKER_CONFIRMED", T561_VERDICT)
        srows.append(row)
    soffit = {
        "section_id": "T-561/stair-soffit", "report": "T-561", "trade": T561_SOFFIT_TRADE,
        "item_codes": ["FIN.STAIR.SOFFIT"], "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": sp["freelancer_gross"], "unit": "m2",
                      "basis": "freelancer paint workbook, wall statement rows 18-19 'for the stair soffits' 1.20 x "
                               "20.20 + 2.10 x 7.50 = 39.99 (Checker own read AGREE; absent from his plaster sheet)"},
        "engine": {"valued_total": "0", "valued_lines": [],
                   "held_lines": [_held_entry(x, f"{x['element_id']} HELD blank") for x in so["HELD"]],
                   "excluded_lines": []},
        "rows": srows, "source_by_class": dict(sp["by_cause"]),
        "beside": {"why_own_section": sp["why_not_wall_paint"],
                   "note": "a soffit is a CEILING face (Q-57): its own trade, never in the wall-paint total "
                           "(Checker: RULE_DIFFERENCE of class)"}}
    return [paint, soffit]


def verify_t561(st: dict, d: dict) -> None:
    """Acceptance: the two paint sections close exactly to the T-561 internal gross gap; no FIN.PAINT HELD line is
    counted as agreement; the omission row is ENGINE_WRONG with its fix row and bound."""
    secs = {c["section_id"]: c for c in st["sections"]}
    p, so = secs["T-561/paint-internal"], secs["T-561/stair-soffit"]
    if D(p["difference"]) + D(so["difference"]) != D(d["internal"]["gap_gross"]):
        raise AdapterError("T-561: paint + soffit sections do not close to the report's gross gap")
    if D(p["reference_total"]) + D(so["reference_total"]) != D(d["internal"]["freelancer_gross"]):
        raise AdapterError("T-561: references do not add to his J28")
    if p["trade"] == so["trade"]:
        raise AdapterError("T-561: soffits share the wall-paint trade (a CEILING face in a wall total)")
    om = [r for r in p["rows"] if r["source_cause"] == "ENGINE_OMISSION"]
    if len(om) != 1 or om[0]["class"] != "ENGINE_WRONG" or not om[0].get("fix_row"):
        raise AdapterError("T-561: the return omission is not one ENGINE_WRONG row with a fix row")


# ============================================================================================ T-564 floor tile ======
T564_SOURCE = ("T-564 WIRING MANIFEST V7 FLOOR_FINISH_COMPLETENESS_WIRING (MERGED 8aba0d81; Checker 15:58 PARTIALLY "
               "VERIFIED: census 2 / 2 hits, 387.094 + 2.970 = 390.064, -5.490 % -> -4.765 % AGREE)")


def t564_expected(sec: dict, d: dict, index: dict) -> dict:
    """R-T570-1 (e): the T-553 floor-tile section gets the EXPECTED-after-fix block beside (never in the columns)."""
    sec = copy.deepcopy(sec)
    ew = sec["beside"]["engine_wrong_restated"]
    rows = [r for r in d["fix_rows"]["rows"] if r.get("closes") == ew["finding"]]
    if len(rows) != 1:
        raise AdapterError(f"T-564: {len(rows)} fix rows close {ew['finding']}")
    adds = [a for a in rows[0]["expected_after"]["add"] if a["item_code"] in Y.T553_CODES]
    if len(adds) != 1 or adds[0]["unit"] != "m2":
        raise AdapterError("T-564: the fix row does not add exactly one floor-tile m2 line")
    add = D(str(adds[0]["value"]))
    if add != D(ew["corrected_area_m2"]):
        raise AdapterError(f"T-564: added {add} != T-553 restated area {ew['corrected_area_m2']}")
    v, ref = D(sec["engine"]["valued_total"]), D(sec["reference"]["total"])
    exp = v + add
    if S.s(exp) != ew["engine_with_correction_m2"]:
        raise AdapterError("T-564: expected engine differs from the T-553 restatement")
    q = Decimal("0.001")
    recode = [r for r in d["fix_rows"]["rows"] if r.get("closes") == "F-T553-2"]
    sec["beside"]["expected_after_fix_T564"] = {
        "status": "EXPECTED (not wired; FLOOR_FINISH_COMPLETENESS_WIRING, Gate B after T-498 / T-423 r2 / T-563)",
        "source": T564_SOURCE,
        "engine_as_valued_m2": S.s(v), "engine_expected_m2": S.s(exp), "reference_m2": S.s(ref),
        "engine_vs_reference_pct_as_valued": S.s(((v - ref) / ref * 100).quantize(q)),
        "engine_vs_reference_pct_expected": S.s(((exp - ref) / ref * 100).quantize(q)),
        "added": [{"element_id": adds[0]["element_id"], "item_code": adds[0]["item_code"], "m2": S.s(add),
                   "area_status": "DRAWING-CONFIRMED (Checker T-553 12:01 own re-measure 1.65 x 1.80)",
                   "finish_status": "A08 ESTIMATED (adjacent master-bedroom finish; RFI RE-REVIEW 2026-11-02, "
                                    "F-C-T564-1): not tile-verified, never VERIFIED"}],
        "recode_zero_area": [r["closes"] for r in recode],
        "statement": f"{S.s(v)} + {S.s(add)} ESTIMATED = {S.s(exp)} m2 EXPECTED",
        "note": "beside only: the valued, bounded and difference columns stay the candidate's (387.09405)"}
    return sec


def verify_expected_apart(st: dict) -> None:
    sec = [c for c in st["sections"] if c["section_id"] == "T-553/floor-tile"][0]
    e = sec["beside"].get("expected_after_fix_T564")
    if e is None or not e["status"].startswith("EXPECTED"):
        raise AdapterError("floor tile: the expected-after block is missing or not labelled EXPECTED")
    if sec["engine_valued"] != e["engine_as_valued_m2"] or sec["engine_valued"] == e["engine_expected_m2"]:
        raise AdapterError("floor tile: an EXPECTED figure sits in the engine valued column")
    if "ESTIMATED" not in e["added"][0]["finish_status"]:
        raise AdapterError("floor tile: the dressing finish is not labelled ESTIMATED (F-C-T564-1)")


# ============================================================================================ T-565 earthworks =====
T565_VERDICT = ("Checker 2026-11-06 15:58 (T-565 Gate A) PARTIALLY VERIFIED: NO_ROW in his concrete + rebar workbook "
                "(own search, 0 hits); 8 / 24 pit footprints re-measured (blinding plan = footing + 0.10, depth chain "
                "1.67 S01 ESTIMATED); WHO IS RIGHT: scope ENGINE_RIGHT, quantity UNRESOLVED / NOT_COMPARABLE (no row of "
                "his), B1-05 AGREE_ABSENT; the pits line stays S01 ESTIMATED, never VERIFIED")
T565_FAMILIES = {"STR.EARTH.EXCAVATION": ("B1-02", "IN_SITU"), "STR.EARTH.BACKFILL": ("B1-03", "COMPACTED"),
                 "STR.EARTH.DISPOSAL": ("B1-04", "IN_SITU")}


def t565_block(index: dict, json_path: Path = T565_JSON) -> dict:
    return t565_from(json.loads(json_path.read_text(encoding="utf-8")), index)


def refuse_no_row_as_number(blk: dict) -> None:
    """R-T570-1 (b): NO_ROW is never 0, never a difference and never a %."""
    for f in blk["families"] + blk["information"]:
        if f.get("his") != "NO_ROW" or f.get("difference") is not None or f.get("pct") is not None:
            raise AdapterError(f"{blk['block_id']} / {f.get('family', f.get('component'))}: his NO_ROW written as "
                               f"{f.get('his')!r}, difference {f.get('difference')!r}, % {f.get('pct')!r}")
    if blk.get("reference_total") is not None or blk.get("difference_pct_of_reference") is not None:
        raise AdapterError(f"{blk['block_id']}: a NOT_COMPARABLE block carries a reference total or a %")


def t565_from(d: dict, index: dict) -> dict:
    comps = [c for c in d["components"] if c.get("line_id")]
    info = [c for c in d["components"] if not c.get("line_id")]
    lines = {x["line_id"]: x for x in index.values() if x["item_code"] in T565_FAMILIES}
    if {c["line_id"] for c in comps} != set(lines):
        raise AdapterError("T-565: the report's zone lines differ from the index earthworks lines")
    fams = {}
    for c in comps:
        ln = lines[c["line_id"]]
        fam, basis = T565_FAMILIES[ln["item_code"]]
        if c["his"] != "NO_ROW" or c["class"] != "NOT_COMPARABLE" or c["engine"]["basis"] != basis:
            raise AdapterError(f"T-565 {c['component']}: not NO_ROW / NOT_COMPARABLE / {basis}")
        e = c["engine"]
        f = fams.setdefault(ln["item_code"], {"family": fam, "item_code": ln["item_code"], "basis": basis,
                                              "unit": ln["unit"], "lines": 0, "valued": Decimal(0), "n_valued": 0,
                                              "held_low": Decimal(0), "held_high": Decimal(0), "n_range": 0,
                                              "held_blank": 0, "line_ids": []})
        f["lines"] += 1
        f["line_ids"].append(c["line_id"])
        if e["state"] == "VALUED":
            if ln["class"] != "RELEASED" or D(ln["measured_net"]) != D(e["value"]):
                raise AdapterError(f"T-565 {c['component']}: valued {e['value']} != index {ln['measured_net']}")
            f["valued"] += D(e["value"])
            f["n_valued"] += 1
        elif e["state"] == "HELD_RANGE":
            lo, hi = require_range([e["low"], e["high"]], f"T-565 {c['component']}")
            if ln["class"] != "HELD" or (D(ln["held_low"]), D(ln["held_high"])) != (lo, hi):
                raise AdapterError(f"T-565 {c['component']}: range differs from the index")
            f["held_low"] += lo
            f["held_high"] += hi
            f["n_range"] += 1
        elif e["state"] == "HELD_BLANK":
            if ln["class"] != "HELD" or ln["measured_net"] is not None or ln["held_low"] is not None:
                raise AdapterError(f"T-565 {c['component']}: blank zone carries a figure in the index")
            f["held_blank"] += 1
        else:
            raise AdapterError(f"T-565 {c['component']}: state {e['state']!r}")
    out = []
    for code, f in sorted(fams.items(), key=lambda t: t[1]["family"]):
        ft = d["family_totals"][code]
        val = S.s(f["valued"]) if f["n_valued"] else None
        rng = [S.s(f["held_low"]), S.s(f["held_high"])] if f["n_range"] else None
        if (ft["valued"] is None) != (val is None) or (val is not None and D(ft["valued"]) != f["valued"]):
            raise AdapterError(f"T-565 {code}: valued {val} != report {ft['valued']}")
        if rng != (None if ft["held_low"] is None else [S.s(D(ft["held_low"])), S.s(D(ft["held_high"]))]):
            raise AdapterError(f"T-565 {code}: held range {rng} != report")
        if f["lines"] != ft["lines"] or f["held_blank"] != ft["held_blank_lines"]:
            raise AdapterError(f"T-565 {code}: line counts differ from the report")
        out.append({"family": f["family"], "item_code": code, "basis": f["basis"], "unit": f["unit"],
                    "lines": f["lines"], "engine_valued": val, "engine_held_range": rng,
                    "engine_held_blank_lines": f["held_blank"], "line_ids": sorted(f["line_ids"]),
                    "his": "NO_ROW", "difference": None, "pct": None, "class": "NOT_COMPARABLE"})
    inf = [{"component": c["component"], "basis": c["engine"]["basis"], "engine": c["engine"].get("value"),
            "state": c["engine"]["state"], "his": c["his"], "difference": None, "pct": None, "class": c["class"],
            "note": c.get("note", c["engine"].get("evidence", ""))} for c in info]
    blk = {"block_id": "T-565/earthworks", "report": "T-565", "trade": "B1 earthworks",
           "status": "NOT_COMPARABLE (his NO_ROW on every component: never 0, no difference, no %)",
           "reference_kind": "NO_ROW", "reference_total": None, "difference_pct_of_reference": None,
           "reference_basis": "his six workbooks, every sheet and cell searched with the earthworks keywords: 0 hits "
                              "(Checker own search of the concrete + rebar workbook AGREE)",
           "families": out, "information": inf, "verification": "CHECKER_CONFIRMED", "verification_basis": T565_VERDICT,
           "beside": {"level_basis": d["level_basis"], "pits_backfill_closure_m3": d["pits_backfill_closure"],
                      "sensitivity_S01_pits_excavation_m3": d["sensitivity_S01_pits_excavation_m3"],
                      "printed_minimum_bound_pits_m3": d["printed_minimum_bound_pits_m3"],
                      "note": "IN_SITU and COMPACTED m3 are never added or compared (R-T565-2); E - B is not a "
                              "disposal quantity; compaction nr and formation m2 are information, never in a m3 total"}}
    refuse_no_row_as_number(blk)
    return blk


# ============================================================================================ T-566 columns =========
T566_VERDICT = ("Checker 2026-11-06 13:55 (T-566 Gate A) PARTIALLY VERIFIED: own ezdxf read + min-total assignment, 34 / 36 "
                "REGISTERED with the worker's mark, 2 CONFLICT at the same positions (10AE C3 | C, 10E0 C8 | C7); GF C3 "
                "COUNT +0.469 m3 CONFLICT-BOUNDED 0 .. +0.469, both lines HELD, storey residuals GF -1.945 / 1F -3.444 "
                "unchanged; beam residual 1 / 5 marks (2F B2 COUNT -0.200 ENGINE_RIGHT ACCEPTED)")
T566_WORKER = ("T-566 worker class (GF B2 MARK_BOUNDARY -0.011, 1F CB12 extent -0.161, GF B7 -0.120 UNRESOLVED, precision "
               "+0.015 not re-measured by the Checker)")
COUNT_VERDICT = {"COUNT": "ENGINE_RIGHT", "HELD": "HELD", "JOINT_HEAD": "RULE_DIFFERENCE", "BASE": "ENGINE_RIGHT",
                 "GLOBAL_DEPTH": "ENGINE_RIGHT", "HEIGHT_OPEN": "UNRESOLVED"}   # TRACED_SPLIT_OPEN -> UNRESOLVED


def _reading_key(rd: dict) -> str:
    return " / ".join(f"{k} {v}" for k, v in sorted(rd.items()))


def column_classes(tables: dict, two_f: dict, on_held: set) -> dict:
    """Statement class totals (his - engine) of one reading's per-storey tables (T-566 t551_resplit format): COUNT by
    mark, a COUNT term on a HELD drawn member -> HELD (F-T562-2), TRACED_SPLIT_OPEN -> UNRESOLVED (F-T562-4)."""
    out = {c: Decimal(0) for c in S.CLASSES}
    for st, t in list(tables.items()) + [("2F", two_f)]:
        acc = Decimal(0)
        for comp, v in t["components"].items():
            v = D(v)
            acc += v
            if comp == "COUNT":
                by = {m: D(x["COUNT"]) for m, x in t.get("by_mark", {}).items() if "COUNT" in x}
                if sum(by.values(), Decimal(0)) != v:
                    raise AdapterError(f"T-566 {st}: COUNT by mark does not sum to {v}")
                for m, x in by.items():
                    out["HELD" if (st, m) in on_held else "ENGINE_RIGHT"] -= x
                continue
            if comp not in COUNT_VERDICT:
                raise AdapterError(f"T-566 {st}: component {comp!r} not in the class table")
            out[COUNT_VERDICT[comp]] -= v
        if acc != D(t["residual_m3"]):
            raise AdapterError(f"T-566 {st}: components {acc} != residual {t['residual_m3']}")
    return {c: S.s(v) for c, v in out.items()}


def on_held_for(reading: dict, tables: dict, base: set, conflicts: list[dict]) -> set:
    """R-T394-2 under one reading: the merged on-held marks that still carry a positive COUNT, plus the reading's mark
    at each CONFLICT position on every storey where that position's member is a HELD line (T-566 conflict_bounds)."""
    out = set()
    for st, t in tables.items():
        cnt = {m: D(x["COUNT"]) for m, x in t["by_mark"].items() if "COUNT" in x}
        for m, v in cnt.items():
            if v <= 0:
                continue
            if (st, m) in base or any(reading[c["position"]] == m and c["storey"] == st for c in conflicts):
                out.add((st, m))
    return out


def t566_columns(sec: dict, d566: dict, d551: dict, index: dict) -> dict:
    """R-T570-1 (c): annotate the CONFLICT rows; per-reading class totals beside; rows stay the reported split."""
    sec = copy.deepcopy(sec)
    confl = d566["conflict_bounds"]
    for c in confl:
        ln = index.get(c["line_id"])
        if ln is None or ln["class"] != "HELD" or c["line_class"] != "HELD":
            raise AdapterError(f"T-566 {c['position']} {c['storey']}: CONFLICT line {c['line_id']} is not HELD")
    pos = {c["position"]: c for c in d566["gf_counts"]["conflict_positions"]}
    if set(pos) != {c["position"] for c in confl}:
        raise AdapterError("T-566: conflict positions differ between the count and bound tables")
    readings = d566["t551_resplit"]
    want = 1
    for p in pos.values():
        want *= len(p["candidates"])
    keys = {_reading_key(r["reading"]) for r in readings}
    if len(keys) != want or len(readings) != want:
        raise AdapterError(f"T-566: {len(keys)} readings given, {want} needed (every reading, none resolved)")
    base = set(Y.T551_COUNT_ON_HELD)
    two_f = dict(d551["columns"]["2F"])
    two_f = {"residual_m3": two_f["residual_m3"], "components": {k: v["m3"] for k, v in two_f["components"].items()}}
    merged = {p: max(c["candidates"], key=lambda m: len(c["candidates"][m])) for p, c in pos.items()}
    per, rec = {}, None
    for r in readings:
        for st, t in r["tables"].items():
            if D(t["residual_m3"]) != D(d551["columns"][st]["residual_m3"]):
                raise AdapterError(f"T-566 reading {r['reading']}: {st} residual moved")
        oh = on_held_for(r["reading"], r["tables"], base, confl)
        k = _reading_key(r["reading"])
        per[k] = {"reading": r["reading"], "on_held_count_marks": sorted(f"{a} {b}" for a, b in oh),
                  "by_class": column_classes(r["tables"], two_f, oh)}
        if r["reading"] == merged:
            rec = k
    if rec is None:
        raise AdapterError("T-566: the merged T-551 reading is not among the readings")
    sec_cls = {c: Decimal(0) for c in S.CLASSES}
    for row in sec["rows"]:
        sec_cls[row["class"]] += D(row["delta"])
    if per[rec]["by_class"] != {c: S.s(v) for c, v in sec_cls.items()}:
        raise AdapterError(f"T-566: the reading of record {rec} does not reproduce the section classes")
    rng = {c: [S.s(min(D(p["by_class"][c]) for p in per.values())), S.s(max(D(p["by_class"][c]) for p in per.values()))]
           for c in S.CLASSES}
    notes = {("GF", "C3"): "10AE: FP / CAP print C3, GBP prints C",
             ("1F", "C8"): "10E0: FP / CAP print C8, GBP prints C7", ("1F", "C7"): "10E0: FP / CAP print C8, GBP C7"}
    for row in sec["rows"]:
        for (st, mk), why in notes.items():
            if row["name"] == f"columns {st}: COUNT {mk}":
                row["note"] = (row["note"] + "; " if row["note"] else "") + \
                    f"T-566 CONFLICT ({why}): this term is the reading of record (merged T-551), NOT a resolution; " \
                    "class totals of every reading beside"
                row["conflict"] = "T-566"
                label(row, "CHECKER_CONFIRMED", T566_VERDICT)
    sec["beside"]["conflict_t566"] = {
        "status": "CONFLICT (designer item, D-16 / D-63 RFI list; no owner question: ERS s.2.7 not met)",
        "positions": [{"position": p, "candidates": c["candidates"], "gf_line": c["gf_line"]} for p, c in pos.items()],
        "held_lines": [{"position": c["position"], "storey": c["storey"], "line_id": c["line_id"],
                        "section_m2": [c["low_m2"], c["high_m2"]]} for c in confl],
        "reading_of_record": rec, "readings": per, "by_class_range_over_readings": rng,
        "gf_c3_count_bound_m3": ["0", S.s(-D([r for r in sec["rows"] if r["name"] == "columns GF: COUNT C3"][0]["delta"]))],
        "storey_residuals_m3": {st: d551["columns"][st]["residual_m3"] for st in ("GF", "1F", "2F")},
        "registration": f"{d566['agreement_with_merged_T205']['registered_equal']} / "
                        f"{d566['agreement_with_merged_T205']['positions']} REGISTERED (Checker VERIFIED 36 / 36 "
                        "positions)",
        "note": "a CONFLICT moves m3 between COUNT (ENGINE_RIGHT) and HELD only: the residual and the RULE_DIFFERENCE / "
                "UNRESOLVED terms are the same in every reading; never resolved by majority, section match or the "
                "freelancer (R-T566-1)",
        "classing_note": "the per-reading class totals apply the statement's own rules to T-566's re-split tables "
                         "(a positive COUNT on a HELD drawn member -> HELD, R-T394-2 / F-T562-2; a negative COUNT -> "
                         "ENGINE_RIGHT): T-570 adapter arithmetic on Checker-verified tables, not a Checker class"}
    return sec


def verify_conflict(st: dict) -> None:
    """R-T570-1 (c): CONFLICT stays a set of readings with ranges; a single resolved value is refused."""
    sec = [c for c in st["sections"] if c["section_id"] == "T-551/columns"][0]
    cf = sec["beside"].get("conflict_t566")
    if cf is None or not cf["status"].startswith("CONFLICT"):
        raise AdapterError("columns: the T-566 CONFLICT block is missing")
    if "resolved_reading" in cf or len(cf["readings"]) < 2:
        raise AdapterError("columns: CONFLICT resolved to one reading (never resolved in the statement)")
    for c, (lo, hi) in cf["by_class_range_over_readings"].items():
        if not D(lo) <= D(sec["by_class"][c]) <= D(hi):
            raise AdapterError(f"columns: {c} {sec['by_class'][c]} outside its reading range")
    rows = [r for r in sec["rows"] if r.get("conflict") == "T-566"]
    if not rows or any("NOT a resolution" not in r["note"] for r in rows):
        raise AdapterError("columns: a CONFLICT row is printed as resolved")


# ============================================================================================ T-566 beams ===========
UNTRACED_ROWS = {"GF": "GF: UNTRACED", "1F": "1F: UNTRACED", "2F": "2F: UNTRACED"}
B2_TS_ROW = "2F: THROUGH_SUPPORT"
T566_CLASS = {"DRAWING_PRECISION": "ENGINE_RIGHT", "COUNT": "ENGINE_RIGHT", "MARK_BOUNDARY": "ENGINE_RIGHT",
              "BEYOND_EXTENT": "ENGINE_RIGHT", "UNRESOLVED": "UNRESOLVED"}
T566_CHECKED = ("2F B2",)


def t566_beams(sec: dict, d566: dict) -> dict:
    """Replace the three UNTRACED rows by T-566's named marks (statement sign = his - engine = -(m3)); move the 2F B2
    count share out of THROUGH_SUPPORT (Checker ACCEPTED, split change of the same mark)."""
    sec = copy.deepcopy(sec)
    old_sum = sum((D(r["delta"]) for r in sec["rows"]), Decimal(0))
    bu = d566["beam_untraced"]
    named = bu["named"]
    if sum((D(n["m3"]) for n in named), Decimal(0)) != D(bu["untraced_total_m3"]):
        raise AdapterError("T-566 beams: named marks do not re-add to the UNTRACED total")
    names = [r["name"] for r in sec["rows"]]
    for st, nm in UNTRACED_ROWS.items():
        if names.count(nm) != 1:
            raise AdapterError(f"T-566 beams: row {nm!r} not found once")
    new_rows = []
    for r in sec["rows"]:
        st = next((s_ for s_, nm in UNTRACED_ROWS.items() if r["name"] == nm), None)
        if st is None:
            new_rows.append(r)
            continue
        mine = [n for n in named if n["mark"].startswith(st + " ")]
        if sum((-D(n["m3"]) for n in mine), Decimal(0)) != D(r["delta"]) or r["class"] != "UNRESOLVED":
            raise AdapterError(f"T-566 beams {st}: named marks != the UNTRACED row {r['delta']}")
        for n in mine:
            cls = T566_CLASS[n["cause"]]
            row = _row(f"{st}: UNTRACED -> {n['mark']} {n['cause']}", -D(n["m3"]), "UNRESOLVED", n["cause"], "VALUED",
                       [], "T-566 s.4 beam UNTRACED by mark (R-T566-5)", n["evidence"])
            row["correction"] = "T-566"
            if cls != "UNRESOLVED":
                _move(row, cls, "VALUED", [], f"T-566 names the cause {n['cause']} from the drawn runs (verdict "
                      f"{n['verdict']})", "F-T570-3")
            ok = n["mark"] in T566_CHECKED
            new_rows.append(label(row, "CHECKER_CONFIRMED" if ok else "WORKER_PROPOSED",
                                  T566_VERDICT if ok else T566_WORKER))
    b2 = [n for n in named if n["mark"] == "2F B2"][0]
    share = -D(b2["reclassed_from_THROUGH_SUPPORT_m3"])          # statement sign
    ts = [r for r in new_rows if r["name"] == B2_TS_ROW]
    if len(ts) != 1 or ts[0]["class"] != "RULE_DIFFERENCE":
        raise AdapterError("T-566 beams: the 2F THROUGH_SUPPORT row is not one RULE_DIFFERENCE row")
    ts = ts[0]
    i = new_rows.index(ts)
    ts["delta"] = S.s(D(ts["delta"]) - share)
    ts["note"] = (ts.get("note") or "") + ("; " if ts.get("note") else "") + \
        f"T-566: {S.s(share)} of the T-545 figure is the 2F B2 count (his lengths face to face there), moved to its row"
    ts["correction"] = "T-566"
    row = _row("2F: THROUGH_SUPPORT -> 2F B2 COUNT share", share, "RULE_DIFFERENCE", "THROUGH_SUPPORT", "VALUED", [],
               "T-566 s.4 (2F B2 mark residual -0.200 = UNTRACED -0.08724 + THROUGH_SUPPORT -0.11276)")
    row["correction"] = "T-566"
    _move(row, "ENGINE_RIGHT", "VALUED", [], "his fifth 2.5 m B2 row has no drawn run (4 B2 labels on the 2F roof "
          "sheet): a count, not a through-support length", "F-T570-4")
    new_rows.insert(i + 1, label(row, "CHECKER_CONFIRMED", T566_VERDICT))
    if sum((D(r["delta"]) for r in new_rows), Decimal(0)) != old_sum:
        raise AdapterError("T-566 beams: the restated rows do not sum to the old rows")
    sec["rows"] = new_rows
    sec["t566"] = {"replaced_rows": [{"name": nm} for nm in UNTRACED_ROWS.values()],
                   "split_row": {"name": B2_TS_ROW, "moved_m3": S.s(share)}}
    return sec


def beams_expected_by_class(prev_by_class: dict, sec: dict) -> dict:
    out = {c: D(prev_by_class[c]) for c in S.CLASSES}
    for r in sec["rows"]:
        m = r.get("reclass")
        if m and m["tag"] in ("F-T570-3", "F-T570-4"):
            out[m["from"]] -= D(m["delta"])
            out[m["to"]] += D(m["delta"])
    return {c: S.s(v) for c, v in out.items()}


# ============================================================================================ T-567 external =======
T567_VERDICT = ("Checker 2026-11-06 15:58 (T-567 Gate A) PARTIALLY VERIFIED: his side 8 / 8 subtotals + net (own read of "
                "his plaster + Sigma workbook, formulas), our side 1 new face (SW pier returns, length) of 120; WHO IS "
                "RIGHT: domes / soffit / plinths RULE_DIFFERENCE +163.12; frames / boundary / drip HELD (his scope of "
                "other families); rows 77 / 78 / 83-84 UNRESOLVED; candidate FIN.EXT.FINISH HELD blank (ENGINE_OMISSION, "
                "T-314)")
T567_WORKER = ("T-567 worker class (our gross 1,166.45 .. 1,185.41 not re-measured face by face; row 65 double count 9.000, "
               "row 74 no-face 52.770 and the soffit surplus 6.320 ENGINE_RIGHT worker-proposed)")
T567_SOURCE = "T-567 R-T567-3 exact bridge (MERGED 8aba0d81)"
CLASS_OF_CAUSE = {"ROUNDING": "TOLERANCE"}                     # R-T570-1 (d): mapped once by name


def _t567_components(csv_path: Path = T567_CSV) -> list[dict]:
    return list(csv.DictReader(csv_path.open(encoding="utf-8")))


def t567_restate(sec: dict, d: dict, comps: list[dict], index: dict) -> dict:
    """R-T570-1 (d) + R-T562-1 (a): the T-552 external rows are SUPERSEDED by the T-567 bridge (gross vs gross)."""
    sec = copy.deepcopy(sec)
    if D(sec["reference"]["total"]) != D(d["his"]["gross_J93"]) or D(sec["engine"]["valued_total"]) != 0:
        raise AdapterError("T-567: the section's reference / engine differ from the report (his J93, engine 0)")
    el = _index_lines(index, {"FIN.EXT.FINISH", "ARCH.FACADE", "EXT.FENCE.PLASTER", "FIN.CEILING"})
    facade = sorted(x["line_id"] for x in el["HELD"] if x["item_code"] in ("FIN.EXT.FINISH", "ARCH.FACADE"))
    fence = sorted(x["line_id"] for x in el["HELD"] if x["item_code"] == "EXT.FENCE.PLASTER")
    if any(x["item_code"] in ("FIN.EXT.FINISH", "ARCH.FACADE", "EXT.FENCE.PLASTER") for x in el["RELEASED"]):
        raise AdapterError("T-567: an external finish line is valued: the bridge is against engine 0")
    for c, ln in d["candidate_lines"].items():
        if index[c]["class"] != "HELD" or c not in facade:
            raise AdapterError(f"T-567: candidate line {c} is not a HELD facade line")
    by = {"lo": [], "hi": []}
    for c in comps:
        by[c["pass"]].append(c)
    his_only = {p: [c for c in by[p] if c["kind"] == "HIS_ONLY"] for p in by}
    if [(c["row"], c["cause"], c["m2"]) for c in his_only["lo"]] != [(c["row"], c["cause"], c["m2"]) for c in his_only["hi"]]:
        raise AdapterError("T-567: his-only rows differ between the passes")
    plinth = {p: sum((D(c["m2"]) for c in by[p] if c["kind"] == "TERM" and c["cause"] == "RULE_DIFFERENCE"), Decimal(0))
              for p in by}
    if plinth["lo"] != plinth["hi"]:
        raise AdapterError("T-567: the plinth RULE_DIFFERENCE terms differ between the passes")
    rows = []
    for c in his_only["lo"]:
        nm = f"his row {c['row']} ({c['group']}): {c['name']}"
        v = D(c["m2"])
        if c["cause"] == "RULE_DIFFERENCE":
            row = _row(nm, v, "RULE_DIFFERENCE", c["cause"], "NONE", [], f"{T567_SOURCE}: his-only row",
                       "owned by FIN.CEILING (another family, released)" if "FIN.CEILING" in c["name"] else
                       "owner item 3: no domes in the render scope")
            label(row, "CHECKER_CONFIRMED", T567_VERDICT)
        elif c["cause"] == "ENGINE_RIGHT":
            row = _row(nm, v, "ENGINE_RIGHT", c["cause"], "NONE", [], f"{T567_SOURCE}: his-only row (no drawn face)")
            label(row, "WORKER_PROPOSED", T567_WORKER)
        elif c["cause"] == "HELD":
            row = _row(nm, v, "HELD", c["cause"], "HELD", [], f"{T567_SOURCE}: his-only row (other family)")
            if "EXT.FENCE.PLASTER" in c["name"]:
                row["held_line_ids"] = fence
            else:
                why = ("frame bands: FIN.EXT.FRAME has no candidate line" if "FIN.EXT.FRAME" in c["name"] else
                       "drip edge: nothing drawn, owner item unanswered, no candidate line")
                _move(row, "UNRESOLVED", "NONE", [], why + " (R-T554-1 (d): no line is never HELD; as F-T557-5)",
                      "F-T570-5")
            label(row, "CHECKER_CONFIRMED", T567_VERDICT)
        else:
            raise AdapterError(f"T-567 row {c['row']}: his-only cause {c['cause']!r}")
        rows.append(row)
    pl = _row("plinth below his +1.00 planes (rows 52 / 64 / 69; owner Q-07 B bands from the F.F.L.)", plinth["lo"],
              "RULE_DIFFERENCE", "RULE_DIFFERENCE", "HELD", facade, f"{T567_SOURCE}: terms",
              "our plinth faces are inside the HELD facade lines (T-314)")
    _move(pl, "HELD", "HELD", facade, "the plinth faces are on the HELD facade lines: the engine values none of them "
          "(R-T548-1 (e)); the owner Q-07 B difference stays the cause", "F-T570-6")
    rows.append(label(pl, "CHECKER_CONFIRMED", T567_VERDICT))
    # the pass-dependent remainder: our gross + ours-only + his terms on the drawn faces (one row, exact both passes)
    parts, tot = {}, {}
    for p in ("lo", "hi"):
        pp = d["passes"][p]
        if D(pp["residual"]) != 0 or D(pp["his_gross"]) != D(d["his"]["gross_J93"]):
            raise AdapterError(f"T-567 {p}: the bridge does not close")
        agg = {}
        for c in by[p]:
            if c["kind"] == "HIS_ONLY" or (c["kind"] == "TERM" and c["cause"] == "RULE_DIFFERENCE"):
                continue
            k = f"{c['kind']} {c['cause']}"
            agg[k] = agg.get(k, Decimal(0)) + D(c["m2"])
        for cause, v in pp["by_cause"].items():
            got = sum((D(c["m2"]) for c in by[p] if c["cause"] == cause), Decimal(0))
            if got != D(v):
                raise AdapterError(f"T-567 {p}: components {cause} {got} != report {v}")
        agg["OUR_GROSS HELD"] = D(pp["our_gross"])
        parts[p] = agg
        tot[p] = sum(agg.values(), Decimal(0))
    if tot["lo"] != tot["hi"]:
        raise AdapterError(f"T-567: the face row differs between the passes ({tot['lo']} vs {tot['hi']})")
    split = {k: [S.s(min(parts["lo"][k], parts["hi"][k])), S.s(max(parts["lo"][k], parts["hi"][k]))]
             for k in sorted(parts["lo"])}
    big = _row("drawn render faces on the HELD facade lines (T-314) with his rows matched to them: our gross + our "
               "faces in no row of his + his widths / heights / unprinted figures on those faces", tot["lo"], "HELD",
               "HELD + ENGINE_RIGHT + UNRESOLVED + ROUNDING", "HELD", facade, f"{T567_SOURCE}: lo / hi passes",
               "the split is a RANGE between the two passes (R-T562-1 (c)), the row total is exact in both: "
               + "; ".join(f"{k} {v[0]} .. {v[1]}" for k, v in split.items())
               + "; ROUNDING is mapped to TOLERANCE by name (R-T570-1 (d)) inside this HELD row")
    big["split_range_m2"] = split
    big["reclass"] = {"tag": "F-T570-7", "from": "ENGINE_RIGHT + UNRESOLVED + TOLERANCE", "to": "HELD",
                      "delta": S.s(tot["lo"] - parts["lo"]["OUR_GROSS HELD"]),
                      "delta_bridge_hi": S.s(tot["hi"] - parts["hi"]["OUR_GROSS HELD"]),
                      "why": "every term on our drawn faces sits on the HELD facade lines (engine valued 0): one row "
                             "classed by its engine side, the ENGINE_RIGHT / UNRESOLVED (rows 77 / 78 / 83-84) / "
                             "ROUNDING ends printed beside, never as agreement"}
    rows.append(label(big, "WORKER_PROPOSED", T567_WORKER))
    old = {"status": "SUPERSEDED", "superseded_by": "T-567 (MERGED 8aba0d81; Checker 15:58)",
           "why": "T-552 matched his rows to the T-337 faces row by row and left 93.15 m2 UNRESOLVED (rows 65 / 68 / "
                  "69); T-567 bridges gross to gross per face key on its own elevation (residual 0 both passes)",
           "rows": [{"name": r["name"], "delta": r["delta"], "class": r["class"]} for r in sec["rows"]]}
    if sum((D(r["delta"]) for r in rows), Decimal(0)) != D(sec["reference"]["total"]):
        raise AdapterError("T-567: the restated rows do not close to his gross")
    sec["rows"] = rows
    for r in sec["rows"]:
        r["correction"] = "T-567"
    nb = d["net_bound"]
    lf = d["like_for_like_gross"]
    sec["beside"]["rows_superseded_T552"] = old
    sec["beside"]["net_vs_net"] = {"basis": "NET", "his_net_m2": nb["his_net"],
                                   "his_rule": "his J93 - half of his opening list J97 65.745 (his own step)",
                                   "our_net_m2": [nb["our_net_lo"], nb["our_net_hi"]],
                                   "our_rule": "full holes Q-73: 97.788801 fixed + W02 0 .. 28.485 + D-GF-07 0 .. 5.000 "
                                               "HELD",
                                   "his_minus_ours_m2": [nb["his_minus_ours_lo"], nb["his_minus_ours_hi"]],
                                   "ours_vs_his_pct": nb["ours_vs_his_pct"],
                                   "note": "our net is drawn faces on HELD lines (T-314): a method figure, never an "
                                           "engine valued figure"}
    sec["beside"]["like_for_like"] = {
        "gross": {"basis": "GROSS", "his_comparable_m2": lf["his_comparable_gross"],
                  "ours_m2": [lf["our_gross_lo"], lf["our_gross_hi"]], "ours_vs_his_pct": lf["ours_vs_his_pct"]},
        "net": {"basis": "NET", "his_comparable_m2": lf["his_comparable_net"],
                "ours_m2": [lf["our_net_lo"], lf["our_net_hi"]], "ours_vs_his_pct": lf["net_ours_vs_his_pct"]},
        "his_excluded_m2": lf["his_excluded_m2"], "note": lf["note"]}
    sec["beside"]["note"] = ("no external finish line is valued in the candidate (T-314, ENGINE_OMISSION): the section "
                             "closes his gross J93 against engine 0; our drawn gross is HELD inside the face row; nets "
                             "are beside, each with its own opening rule, never paired with a gross (R-T570-1 (d))")
    return sec


def pair(a: dict, b: dict) -> tuple:
    """R-T570-1 (d): a comparison pairs two figures of one basis only (GROSS with GROSS, NET with NET)."""
    if a.get("basis") not in ("GROSS", "NET") or a.get("basis") != b.get("basis"):
        raise AdapterError(f"{a.get('basis')} paired with {b.get('basis')}: a net is never set against a gross")
    return a, b


def verify_gross_net(st: dict) -> None:
    sec = [c for c in st["sections"] if c["section_id"] == "T-552/plaster-external"][0]
    b = sec["beside"]
    if b.get("rows_superseded_T552", {}).get("status") != "SUPERSEDED":
        raise AdapterError("external plaster: the T-552 rows lost their SUPERSEDED label")
    pair(b["like_for_like"]["gross"], {"basis": "GROSS"})
    pair(b["like_for_like"]["net"], {"basis": "NET"})
    if b["net_vs_net"]["basis"] != "NET":
        raise AdapterError("external plaster: the net block is not NET")
    if any(r.get("correction") != "T-567" for r in sec["rows"]):
        raise AdapterError("external plaster: a row is not the T-567 restatement")
