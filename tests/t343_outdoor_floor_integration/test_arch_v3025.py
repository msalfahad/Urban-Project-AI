"""T-343: ARCH_TAKEOFF_V3.0.25 (the outdoor floor surfaces of an open court, one line per drawn piece, finish from
the owner rule or HELD with the area kept, and the pool water-face finish HELD BLANK with its bound) on a
hand-calculated NON-Alsenan villa (P343), normal and adverse.

Villa P343, by hand (a villa court: front and side strips ceramic by the owner sides rule; the open court interlock as
on a chalet court; porch and pool deck finish undecided):
  court face (filled, inside the boundary-wall inner faces) 124.400 m2 with ONE hole: the pool outer D, r 1.50, two
  straight sides 2.00, back 3.00 = 2 r: exact pi 1.5^2 / 2 + 3.00 x 2.00 = 3.534292 + 6.000 = 9.534292 m2 (perimeter
  pi 1.5 + 2 x 2.00 + 3.00 = 11.712389 m); a tessellated reading 9.530 m2 (residual -0.004292).
  plan pieces:   open court interlock 80.000 | front + side strip ceramic 15.000 (owner manual 2.00 x 8.00 = 16.000
                 beside) | covered porch 6.000 (finish HELD) | steps E1 treads 4 x 0.30 x 2.00 = 2.400 marble |
                 landing 1.50 x 2.00 = 3.000 marble | pool deck = deck face 18.000 - outer D 9.534292 = 8.465708
                 (finish HELD)
                 sum 114.865708 = face 124.400 - 9.534292 = 114.865708 (difference 0.000000)
  vertical:      E1 visible risers 5 x 0.140 x 2.00 = 1.400 marble (outside the plan closure)
  pool water D r 1.30, straight 2.00, back 2.60: floor pi 1.3^2 / 2 + 2.60 x 2.00 = 2.654646 + 5.200 = 7.854646 m2,
  perimeter pi 1.3 + 4.00 + 2.60 = 10.684070 m; finished depth (finished floor -> rim) 1.20, structural 1.25 beside:
  surface bound 7.854646 + 10.684070 x 1.20 = 7.854646 + 12.820885 = 20.675531 m2 (BLANK, never 0).
  released (finish stated): 80.000 + 15.000 + 2.400 + 3.000 + 1.400 = 101.800 m2; held finish 6.000 + 8.465708 =
  14.465708 m2 (kept as ranges [a, a]); 8 lines.
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3025 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402
from tools import t334_line_state_check as LS  # noqa: E402

PID, REV = "villa-p343", "f" * 64
DOCS = [{"file": "p343_arch.dxf", "sha256": "d" * 64}]
OUTER = math.pi * 1.5 ** 2 / 2 + 3.0 * 2.0              # 9.534292
DECK = 18.0 - OUTER                                       # 8.465708
WATER_A = math.pi * 1.3 ** 2 / 2 + 2.6 * 2.0              # 7.854646
WATER_P = math.pi * 1.3 + 2 * 2.0 + 2.6                   # 10.684070
BOUND = WATER_A + WATER_P * 1.20                          # 20.675531


def _ln(code, eid, ev, net=None, floor="GF", unit="m2", formula="p343 candidate"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element="member", formula=formula,
                        documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "not read"} if ev == "BLOCKED_RFI" else None, notes="p343")


def lines_3024():
    return [_ln("FIN.FLOOR.PORCELAIN", "GF-HALL", "SOURCE_DERIVED", 30.0, formula="6 x 5 = 30.0 m2"),
            _ln("STR.CONC.POOL", "POOL-1#WALLS", "SOURCE_DERIVED", 2.5, unit="m3", formula="ring x 1.25 = 2.5 m3"),
            _ln("ARCH.SPACE", "HL:FLOOR_SCOPE:OUTDOOR:GF:PASSAGE", "SOURCE_DERIVED", 4.0, formula="2 x 2 = 4.0 m2")]


def _p(piece, code, a, kind="PLAN", ms=A.OA, mat="interlock", src="owner outdoor rule (court)", item=None, **kw):
    d = {"piece": piece, "element_id": f"GF-COURT#{piece}", "floor": "GF", "item_code": code, "unit": "m2",
         "kind": kind, "area_m2": a, "area_status": A.DC, "area_basis": f"{piece} drawn polygon",
         "edges": "boundary-wall inner faces + drawn cut lines", "material": mat, "material_status": ms,
         "source_task": "T-P1"}
    if ms == "HELD":
        d["material_item"] = item or "owner: finish undecided"
    else:
        d["material_source"] = src
    d.update(kw)
    return d


def doc():
    pieces = [
        _p("OPEN", "EXT.PAVING.INTERLOCK", 80.0),
        _p("SIDE", "EXT.FLOOR.PORCELAIN", 15.0, mat="porcelain / ceramic", src="owner sides rule",
           owner_manual={"formula": "2.00 x 8.00 (to the plot line)", "m2": 16.0},
           freelancer={"row": "yard", "m2": 99.0, "note": "one row"}),
        _p("PORCH", "EXT.FLOOR.OUTDOOR", 6.0, ms="HELD", mat="undecided"),
        _p("E1-TREADS", "FIN.MARBLE.TREAD", 2.4, mat="marble", src="UP-STAIR-001"),
        _p("E1-RISERS", "FIN.MARBLE.RISER", 1.4, kind="VERTICAL", mat="marble", src="UP-STAIR-001",
           flags=["drawn riser 0.170 > 0.16 (check only)"]),
        _p("E1-LANDING", "FIN.MARBLE.LANDING", 3.0, mat="marble", src="UP-STAIR-001"),
        _p("DECK", "EXT.FLOOR.OUTDOOR", round(DECK, 6), ms="HELD", mat="undecided",
           derived={"face_m2": 18.0, "face_source": "deck face polygon",
                    "less": [{"what": "pool outer D", "r_m": 1.5, "straight_m": 2.0, "width_m": 3.0,
                              "edges": "ARC r 1500 + 2 LINEs", "tessellated_m2": 9.53}]}),
    ]
    pool = {"element_id": "GF-POOL#WATER_FACE_FINISH", "floor": "GF",
            "water_outline": {"r_m": 1.3, "straight_m": 2.0, "width_m": 2.6, "edges": "ARC r 1300 + 2 LINEs"},
            "rim_height_m": 1.20, "structural_height_m": 1.25, "rim_basis": "FINISHED_FLOOR_TO_RIM",
            "rim_height_source": "section S1: dimension 1200 finished floor -> rim", "rim_status": A.DC,
            "material_status": "HELD", "material_item": "owner / designer: pool finish", "source_task": "T-P1"}
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "sources": [{"file": "p343_areas.csv", "sha256": "c" * 64, "task": "T-P1", "merge_commit": "m" * 40,
                         "checker_run": "checker p343"}],
            "face": {"face_id": "GF-COURT", "floor": "GF", "filled_m2": 124.4, "filled_source": "court polygon",
                     "holes": [{"what": "pool outer D", "r_m": 1.5, "straight_m": 2.0, "width_m": 3.0,
                                "edges": "ARC r 1500 + 2 LINEs", "tessellated_m2": 9.53}],
                     "closure_tol_m2": 0.005, "reference_total_m2": 114.87, "reference_source": "earlier ledger"},
            "pieces": pieces, "pool_finish": pool,
            "cross_check": [{"line_id": lines_3024()[0]["line_id"], "item_code": "FIN.FLOOR.PORCELAIN",
                             "element_id": "GF-HALL", "why": "interior hall, another face", "shared_m2": 0.0},
                            {"line_id": lines_3024()[2]["line_id"], "item_code": "ARCH.SPACE",
                             "element_id": "passage", "why": "side passage, another face", "shared_m2": 0.0}],
            "declared": {"lines": 8, "plan_m2": round(80 + 15 + 6 + 2.4 + 3 + DECK, 6), "vertical_m2": 1.4,
                         "held_material_m2": round(6 + DECK, 6), "pool_bound_m2": round(BOUND, 6)}}


def _run(d=None, base=None):
    d = A.load_inputs(copy.deepcopy(d or doc()), PID)
    base = base or lines_3024()
    ch, logs, clo = A.changes_for(d, base)
    out, ident = A.integrate(base, ch)
    return d, base, ch, logs, clo, out, ident


# ================================================================================================ normal
def test_hand_values_of_the_d_outline():
    a, p = A.d_outline(1.5, 2.0, 3.0)
    assert round(a, 6) == 9.534292 and round(p, 6) == 11.712389
    a, p = A.d_outline(1.3, 2.0, 2.6)
    assert round(a, 6) == 7.854646 and round(p, 6) == 10.68407


def test_villa_lines_closure_and_states():
    d, base, ch, logs, clo, out, ident = _run()
    assert ident["added"] == 8 and ident["outside_rows_identical_to_v3_0_24"] == 3
    assert [A30.line_sha(x) for x in out[:3]] == [A30.line_sha(x) for x in base]
    assert clo["face_net_exact_m2"] == round(124.4 - OUTER, 6) and abs(clo["difference_m2"]) < 1e-6
    assert clo["holes"][0]["tessellation_residual_m2"] == round(9.53 - OUTER, 6)       # -0.004292 named
    assert clo["vertical_pieces_m2"] == 1.4
    fam = ident["outdoor_family"]
    assert fam == {"lines": 8, "released_m2": 101.8, "held_material_m2": round(6 + DECK, 6), "pool_blank": 1}
    by = {ln["location"]["element_id"]: ln for ln in out[3:]}
    assert by["GF-COURT#OPEN"]["evidence_state"] == "SOURCE_DERIVED" and by["GF-COURT#OPEN"]["measured_net"] == 80.0
    assert by["GF-COURT#OPEN"]["material_state"] == "PROJECT_OWNER_FACT"
    deck = by["GF-COURT#DECK"]
    assert deck["evidence_state"] == "BOUNDED_EXPOSURE" and deck["measured_net"] is None
    assert deck["bounded_range"]["low"] == deck["bounded_range"]["high"] == round(DECK, 6) > 0
    assert deck["item_code"] == "EXT.FLOOR.OUTDOOR" and deck["rfi"]["items"] == ["owner: finish undecided"]
    pool = by["GF-POOL#WATER_FACE_FINISH"]
    rec = pool["calculation"]["inputs"]["outdoor_floor_v3025"]
    assert pool["evidence_state"] == "BLOCKED_RFI" and pool["measured_net"] is None and pool["bounded_range"] is None
    assert rec["bound"]["surface_m2"] == round(BOUND, 6) and rec["bound"]["walls_m2"] == round(WATER_P * 1.2, 6)
    side = by["GF-COURT#SIDE"]["calculation"]["inputs"]["outdoor_floor_v3025"]
    assert side["owner_manual"]["m2"] == 16.0          # owner manual method beside, never used
    assert by["GF-COURT#SIDE"]["measured_net"] == 15.0


def test_every_added_line_states_one_state_for_the_export_check():
    *_, out, _ident = _run()
    for ln in out[3:]:
        res = LS.check_line(ln)
        assert res["category"] == LS.OK, res
    pool = [ln for ln in out if ln["item_code"] == A.POOL_FINISH_ITEM][0]
    assert LS.formula_figure(pool["calculation"]["formula"], "m2") == (None, None)       # no concluding figure


def test_write_files_diff_added_only_and_totals_in_family(tmp_path):
    d, base, ch, logs, clo, out, ident = _run()
    names, ident2, led = A.write(tmp_path, base, ch, logs, clo, d, released_lines=base[:1])
    assert "V3_0_25_CLOSURE.csv" in names and (tmp_path / "V3_0_25_DIFF.csv").exists()
    assert ident2["diff"]["vs_v3_0_24"] == {"SAME": 3, "ADDED": 8}
    assert len(led["rows"]) == 8 and all(r["release_status"] == "NOT RELEASED" for r in led["rows"])
    assert "-0.004292" in (tmp_path / "V3_0_25_CLOSURE.csv").read_text(encoding="utf-8")


def test_no_input_no_change():
    ch, logs, clo = A.changes_for(None, lines_3024())
    assert ch == [] and logs[0]["state"] == "NO_PROJECT_INPUT" and clo is None


# ================================================================================================ adverse
def _refused(mut, match=None, base=None):
    d = doc()
    mut(d)
    with pytest.raises((A.InputsError, ValueError), match=match):
        dd = A.load_inputs(d, PID)
        A.changes_for(dd, base or lines_3024())


def test_adverse_circle_for_a_d_is_refused():
    def m(d):
        d["face"]["holes"][0]["width_m"] = 2.0          # not 2 r: a circle-like reading
    _refused(m, "not a D")


def test_adverse_deck_from_a_circle_area_is_refused():
    def m(d):
        d["pieces"][6]["area_m2"] = round(18.0 - math.pi * 1.5 ** 2, 6)   # face less a full circle
        d["declared"]["plan_m2"] = 0
    _refused(m, "exact outline")


def test_adverse_court_on_an_interior_tile_line_is_refused():
    def m(d):
        d["pieces"][0]["item_code"] = "FIN.FLOOR.PORCELAIN"
    _refused(m, "not an outdoor floor item")


def test_adverse_held_material_as_zero_is_refused():
    def m(d):
        d["pieces"][2]["area_m2"] = 0.0
    _refused(m, "never 0")


def test_adverse_held_material_on_a_priced_item_is_refused():
    def m(d):
        d["pieces"][2]["item_code"] = "EXT.FLOOR.PORCELAIN"
    _refused(m, "HELD finish is not priced")


def test_adverse_assumed_material_without_source_and_on_the_blank_item():
    def m(d):
        d["pieces"][0].pop("material_source")
    _refused(m, "names its source")

    def m2(d):
        d["pieces"][0]["item_code"] = "EXT.FLOOR.OUTDOOR"
    _refused(m2, "its own item")


def test_adverse_a_missing_piece_fails_the_closure():
    def m(d):
        d["pieces"] = [p for p in d["pieces"] if p["piece"] != "PORCH"]
        d["declared"].update(lines=7, plan_m2=round(80 + 15 + 2.4 + 3 + DECK, 6), held_material_m2=round(DECK, 6))
    _refused(m, "missing or counted twice")


def test_adverse_mm2_areas_fail_the_closure():
    def m(d):
        d["pieces"][0]["area_m2"] = 80.0 * 1e6
        d["declared"]["plan_m2"] = round(80e6 + 15 + 6 + 2.4 + 3 + DECK, 6)
    _refused(m, "missing or counted twice")


def test_adverse_piece_twice_and_element_already_carried():
    def m(d):
        d["pieces"].append(copy.deepcopy(d["pieces"][0]))
    _refused(m, "named twice")
    base = lines_3024() + [_ln("FIN.FLOOR.PORCELAIN", "GF-COURT#OPEN", "SOURCE_DERIVED", 80.0)]
    _refused(lambda d: None, "counted once", base=base)
    fam = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="EXT.PAVING.INTERLOCK", unit="m2",
                       evidence_state="SOURCE_DERIVED", measured_net=1.0, element_id="X", floor="GF", formula="1 m2",
                       documents=DOCS, rule_id="R", rule_version="1", item_en="paving", item_ar="paving",
                       trade="EXTERNAL_WORKS")
    _refused(lambda d: None, "added once", base=lines_3024() + [fam])


def test_adverse_cross_check_shared_area_or_stale_line():
    def m(d):
        d["cross_check"][0]["shared_m2"] = 1.2
    _refused(m, "counted once")

    def m2(d):
        d["cross_check"][0]["line_id"] = "L-not-in-the-run"
    _refused(m2, "stale inputs")


def test_adverse_pool_rim_from_the_structure_or_in_mm():
    def m(d):
        d["pool_finish"]["rim_basis"] = "BASE_TOP_TO_RIM"
    _refused(m, "finished pool floor")

    def m2(d):
        d["pool_finish"]["rim_height_m"] = 1200
    _refused(m2, "outside")

    def m3(d):
        d["pool_finish"]["rim_height_m"] = 1.30           # above the structural 1.25
        d["declared"]["pool_bound_m2"] = round(WATER_A + WATER_P * 1.3, 6)
    _refused(m3, "structural height")


def test_adverse_pool_water_as_a_floor_piece():
    def m(d):
        d["pool_finish"]["element_id"] = "GF-COURT#OPEN"
    _refused(m, "never a floor")


def test_adverse_declared_total_not_the_records_sum():
    def m(d):
        d["declared"]["plan_m2"] += 0.01
    _refused(m, "declared plan_m2")


def test_adverse_a_held_line_with_a_figure_is_refused_on_integrate():
    d, base, ch, logs, clo, out, ident = _run()
    bad = copy.deepcopy(ch)
    for c in bad:
        if c["after"]["location"]["element_id"] == "GF-COURT#DECK":
            c["after"]["evidence_state"] = "SOURCE_DERIVED"
            c["after"]["measured_net"] = 0.0
            c["after"]["bounded_range"] = None
    with pytest.raises(ValueError, match="two states"):           # the V3.0.24 line-state check runs first
        A.integrate(base, bad)
    with pytest.raises(ValueError, match="held range"):           # the family check on its own
        A.check_outdoor_family([c["after"] for c in bad])


def test_adverse_a_changed_v3024_line_is_refused():
    d, base, ch, logs, clo, out, ident = _run()
    bad = ch + [{"piece": "DEFAULT_GUARD", "action": "REPLACE", "before": base[0], "after": base[0]}]
    with pytest.raises(ValueError, match="byte-identical"):
        A.integrate(base, bad)


def test_order_reversed_gives_the_same_lines():
    d1 = doc()
    d2 = doc()
    d2["pieces"] = list(reversed(d2["pieces"]))
    o1 = _run(d1)[5]
    o2 = _run(d2)[5]
    assert sorted(A30.line_sha(x) for x in o1) == sorted(A30.line_sha(x) for x in o2)


# ================================================================================================ r2: R-T343-1
# Villa P343-B (a villa with a curved glazed band on the pool court; hand-calculated, not Alsenan):
#   deck face to the band's COURT face: rectangle 3.00 x 4.00 = 12.000 + band segment r 2.00 beyond the chord at 0.50
#   = 4 acos(0.25) - 0.5 sqrt(3.75) = 5.272464 - 0.968246 = 4.304218 - column 0.30 x 0.30 = 0.090 -> 16.214218 m2;
#   deck = 16.214218 - outer D 9.534292 = 6.679926 m2 (finish HELD).
#   the window frame inside the band: r 2.08 at 0.58 (segment 4.414736) + straights 0.08 x 3.60 = 0.288; the recess
#   in front of the frame = 4.414736 + 0.288 - 4.304218 = 0.398518 m2 (the opening's reveal strip, never deck);
#   the court polygon walked the frame: frame face 16.612736 read 16.608736 (tessellation -0.004 named);
#   filled = 80 + 15 + 6 + 2.4 + 3 + 16.612736 - 0.004 = 123.008736 m2;
#   closure: 123.008736 + 0.004 - 9.534292 - 0.398518 = 113.079926 = plan pieces 106.4 + 6.679926 (difference 0).
SEG = lambda r, d: r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)  # noqa: E731
BAND_FACE = 12.0 + SEG(2.0, 0.5) - 0.09                    # 16.214218
STRIP = SEG(2.08, 0.58) + 0.08 * 3.6 - SEG(2.0, 0.5)       # 0.398518
DECK_B = round(BAND_FACE, 6) - OUTER                       # 6.679926
BAND_TERMS = [
    {"what": "rect 3.00 x 4.00", "kind": "RECT", "a_m": 3.0, "b_m": 4.0, "sign": 1, "edge_kind": "DRAWN_LINE",
     "edges": "house face + boundary wall + cut lines"},
    {"what": "band segment r 2.00 at 0.50", "kind": "SEGMENT", "r_m": 2.0, "d_m": 0.5, "sign": 1,
     "edge_kind": "BAND_COURT_FACE", "edges": "band court face ARC r 2000 (printed dimension line)"},
    {"what": "column 0.30 x 0.30", "kind": "RECT", "a_m": 0.3, "b_m": 0.3, "sign": -1, "edge_kind": "DRAWN_LINE",
     "edges": "column outline"}]
STRIP_TERMS = [
    {"what": "frame segment r 2.08 at 0.58", "kind": "SEGMENT", "r_m": 2.08, "d_m": 0.58, "sign": 1,
     "edge_kind": "FRAME_LINE", "edges": "frame polyline bulge r 2080"},
    {"what": "frame straights 0.08 x 3.60", "kind": "RECT", "a_m": 0.08, "b_m": 3.6, "sign": 1, "edge_kind": "FRAME_LINE",
     "edges": "frame polyline straights"},
    {"what": "band segment r 2.00 at 0.50", "kind": "SEGMENT", "r_m": 2.0, "d_m": 0.5, "sign": -1,
     "edge_kind": "BAND_COURT_FACE", "edges": "band court face ARC r 2000"}]


def doc_band():
    d = doc()
    deck = d["pieces"][6]
    deck["area_m2"] = round(DECK_B, 6)
    deck["derived"] = {"face_m2": round(BAND_FACE, 6), "face_edge_kind": "BAND_COURT_FACE",
                       "face_source": "drawn construction", "construction": {"terms": copy.deepcopy(BAND_TERMS)},
                       "polygon_reading": {"m2": 16.608736, "edge_kind": "FRAME_LINE", "source": "court polygon"},
                       "less": copy.deepcopy(deck["derived"]["less"])}
    d["face"]["filled_m2"] = round(106.4 + BAND_FACE + STRIP - 0.004, 6)               # 123.008736
    d["face"]["reveal_strips"] = [{"what": "recess in front of the frame", "scope": "glazing reveal strip",
                                   "held_with": "the opening's reveal strip line", "edges": "band face to frame line",
                                   "construction": {"terms": copy.deepcopy(STRIP_TERMS)}, "m2": round(STRIP, 6)}]
    d["face"]["reading_residuals"] = [{"what": "court polygon along the frame", "tessellated_m2": 16.608736,
                                       "exact_m2": round(BAND_FACE + STRIP, 6), "basis": "frame face exact"}]
    d["face"]["reference_total_m2"] = 113.08
    d["declared"].update(plan_m2=round(106.4 + DECK_B, 6), held_material_m2=round(6 + DECK_B, 6))
    return d


def test_hand_values_of_the_band_fixture():
    assert round(SEG(2.0, 0.5), 6) == 4.304218 and round(BAND_FACE, 6) == 16.214218
    assert round(STRIP, 6) == 0.398518 and round(DECK_B, 6) == 6.679926
    assert round(A.terms_area(BAND_TERMS, "t", floor_face=True)[0], 6) == 16.214218
    assert round(A.circular_segment(2.25, 0.25), 6) == 6.829476          # the T-127 hand 6.8295 (band segment)


def test_r2_deck_to_the_band_court_face_with_the_reveal_strip_named():
    d, base, ch, logs, clo, out, ident = _run(doc_band())
    assert abs(clo["difference_m2"]) < 1e-6 and clo["face_net_exact_m2"] == round(106.4 + DECK_B, 6)
    assert clo["reveal_strips"][0]["m2"] == round(STRIP, 6) > 0
    assert clo["reading_residuals"][0]["residual_m2"] == -0.004
    by = {ln["location"]["element_id"]: ln for ln in out[3:]}
    deck = by["GF-COURT#DECK"]
    assert deck["bounded_range"]["low"] == deck["bounded_range"]["high"] == round(DECK_B, 6)
    rec = deck["calculation"]["inputs"]["outdoor_floor_v3025"]
    assert rec["face_edge_kind"] == "BAND_COURT_FACE" and "R-T343-1" in rec["rules_applied"]
    assert [t["m2"] for t in rec["face_construction"]] == [12.0, 4.304218, 0.09]
    assert not any(ln["location"]["element_id"].endswith("recess in front of the frame") for ln in out)  # not a line
    assert ident["added"] == 8


def test_r2_closure_csv_names_the_strip_and_the_residual(tmp_path):
    d, base, ch, logs, clo, out, ident = _run(doc_band())
    A.write(tmp_path, base, ch, logs, clo, d, released_lines=base[:1])
    t = (tmp_path / "V3_0_25_CLOSURE.csv").read_text(encoding="utf-8")
    assert "REVEAL_STRIP" in t and str(round(STRIP, 6)) in t and "READING_RESIDUAL" in t and "-0.004" in t


def test_adverse_r2_deck_walked_along_the_frame_line_is_refused():
    def m(d):                                         # the deck face built with the frame segment instead of the band
        dv = d["pieces"][6]["derived"]
        dv["construction"]["terms"][1].update(r_m=2.08, d_m=0.58, edge_kind="FRAME_LINE")
    _refused(lambda d: (d.update(doc_band()), m(d)), "window-frame line")

    def m2(d):                                        # the frame-walked polygon taken as the deck face
        dv = d["pieces"][6]["derived"]
        dv.pop("construction")
        dv.update(face_m2=16.608736, face_edge_kind="FRAME_LINE")
        d["pieces"][6]["area_m2"] = round(16.608736 - OUTER, 6)
    _refused(lambda d: (d.update(doc_band()), m2(d)), "window-frame line")


def test_adverse_r2_frame_face_without_the_flag_fails_the_closure():
    def m(d):                                         # deck = frame face - D, strip still named: counted twice
        dv = d["pieces"][6]["derived"]
        dv.pop("construction")
        dv.update(face_m2=round(BAND_FACE + STRIP, 6), face_edge_kind="DRAWN_LINE")
        a = round(BAND_FACE + STRIP - OUTER, 6)
        d["pieces"][6]["area_m2"] = a
        d["declared"].update(plan_m2=round(106.4 + a, 6), held_material_m2=round(6 + a, 6))
    _refused(lambda d: (d.update(doc_band()), m(d)), "missing or counted twice")


def test_adverse_r2_strip_as_zero_without_scope_or_off_its_construction():
    for mut, msg in ((lambda s: s.update(m2=0.0), "must be > 0"), (lambda s: s.pop("scope"), "scope required"),
                     (lambda s: s.update(m2=0.5), "construction")):
        def m(d, mut=mut):
            d.update(doc_band())
            mut(d["face"]["reveal_strips"][0])
        _refused(m, msg)


def test_adverse_r2_face_off_its_construction_and_a_large_residual():
    def m(d):
        d.update(doc_band())
        d["pieces"][6]["derived"]["construction"]["terms"][0]["a_m"] = 3.10
    _refused(m, "drawn construction")

    def m2(d):
        d.update(doc_band())
        d["face"]["reading_residuals"][0]["tessellated_m2"] = 16.0
    _refused(m2, "not a tessellation residual")
