"""Phase A3 - schedule-driven structural QTO (engine/source/structural_schedule.py) on synthetic plans:
mark = type identity, schedule = nominal size, geometry = validation; conflict cases A-D; count first; derived
type summaries; reconciliation; columns per storey; strap / beam bands bound by containment; rebar definitions."""

from __future__ import annotations

import pytest

from engine.source import structural_qto as SQ
from engine.source import structural_schedule as SS

EPS = 1.0
LIB = {"F": {"L_cm": 90, "W_cm": 80, "H_cm": 30, "keys": ["S|F"]},
       "F10": {"L_cm": 280, "W_cm": 140, "H_cm": 50, "keys": ["S|F10"]},
       "FN": {"L_cm": 100, "W_cm": 100, "H_cm": 30, "keys": ["S|FN"]},
       "F9": {"L_cm": 340, "W_cm": 270, "H_cm": 55, "keys": ["S|F9"]},
       "FX": {"L_cm": 100, "W_cm": 100, "H_cm": None, "keys": ["S|FX"]}}


def poly(ent, pts, closed=True):
    n = len(pts) if closed else len(pts) - 1
    return [(f"R|{ent}||SEGMENT|{i}",) + tuple(pts[i]) + tuple(pts[(i + 1) % len(pts)]) for i in range(n)]


def line(ent, x1, y1, x2, y2):
    return (f"R|{ent}||SEGMENT|0", x1, y1, x2, y2)


def mark(key, value, x, y, typ):
    return {"key": key, "value": value, "x": x, "y": y, "type": typ}


def run(segs, marks, *, others=(), lib=LIB, carriers=(), overrides=None):
    rings = SS.entity_rings(segs, eps=EPS, others=others)
    rects = [SS.rect_candidate(r) for r in SQ.rectangles(segs, eps=EPS)]
    tmpl = {t: SQ.template_outlines(segs, v["L_cm"] * 10, v["W_cm"] * 10, 1.0, eps=EPS, support=())
            for t, v in lib.items() if v.get("L_cm") and v.get("W_cm")}
    cands = SS.merge_candidates(rings, rects, [SS.rect_candidate(c, "TEMPLATE") for v in tmpl.values() for c in v])
    res = SS.footing_occurrences(marks, lib, cands, umm=1.0, tol_mm=1.0, eps=EPS, templates_by_type=tmpl,
                                 carriers=carriers, overrides=overrides)
    return {r["mark_key"]: r for r in res["rows"]}, res, cands


def test_case_a_geometry_confirmed():
    rows, _, _ = run(poly("A", [(0, 0), (900, 0), (900, 800), (0, 800)]), [mark("m1", "C/F", 450, 400, "F")])
    r = rows["m1"]
    assert r["geometry_state"] == SS.CONFIRMED and r["status"] == SS.COMPLETE
    assert r["qty"] == pytest.approx(0.9 * 0.8 * 0.3) == pytest.approx(0.216)
    assert r["dims"]["H"]["m"] == 0.3 and r["dims"]["H"]["source"].startswith("SCHEDULE OF FOOTINGS")


def test_case_b_strap_entry_gap_is_schedule_authority():
    # outline open on its north side where a 300 mm strap enters; the strap lines pass through both gap ends
    segs = poly("B", [(400, 800), (0, 800), (0, 0), (900, 0), (900, 800), (700, 800)], closed=False)
    strap = [line("S1", 400, 300, 400, 5000), line("S2", 700, 300, 700, 5000)]
    rows, res, _ = run(segs + strap, [mark("m1", "F", 200, 400, "F")])
    r = rows["m1"]
    assert r["geometry_state"] == SS.INTERRUPTED and r["status"] == SS.COMPLETE and r["qty"] == pytest.approx(0.216)
    assert r["geometry"]["outline_state"] == SS.GAP_EXPLAINED and set(r["geometry"]["gap_keys"]) >= {strap[0][0]}


def test_case_b_bare_gap_does_not_close():
    segs = poly("B", [(400, 800), (0, 800), (0, 0), (900, 0), (900, 800), (700, 800)], closed=False)
    rows, _, _ = run(segs, [mark("m1", "F", 200, 400, "F")])
    assert rows["m1"]["status"] == SS.BLOCKED and rows["m1"]["geometry_state"] == SS.UNBOUND


def test_case_b_notch_at_adjacent_footing():
    f9 = poly("F9", [(-3400, -2700), (0, -2700), (0, 0), (-3400, 0)])
    fn = poly("FN", [(-400, 0), (0, 0), (0, -350), (600, -350), (600, 650), (-400, 650)])
    rows, _, _ = run(f9 + fn, [mark("n1", "CN/FN", 200, 300, "FN"), mark("f9", "F9", -1700, -1300, "F9")])
    r = rows["n1"]
    assert r["geometry_state"] == SS.INTERRUPTED and r["qty"] == pytest.approx(0.3)
    assert r["geometry"]["notch_m2"] == pytest.approx(0.14) and r["geometry"]["outline_state"] == SS.NOTCHED
    assert rows["f9"]["geometry_state"] == SS.CONFIRMED


def test_unexplained_notch_is_a_drawn_size_conflict():
    fn = poly("FN", [(-400, 0), (0, 0), (0, -350), (600, -350), (600, 650), (-400, 650)])
    rows, _, _ = run(fn, [mark("n1", "FN", 200, 300, "FN")])
    assert rows["n1"]["status"] == SS.BLOCKED and rows["n1"]["geometry_state"] == SS.DRAWN_SIZE


def test_case_c_own_outline_of_another_size_blocks_and_override_computes():
    segs = poly("C", [(0, 0), (1500, 0), (1500, 1400), (0, 1400)])
    rows, _, _ = run(segs, [mark("m1", "F", 700, 700, "F")])
    assert rows["m1"]["geometry_state"] == SS.DRAWN_SIZE and rows["m1"]["qty"] is None
    assert rows["m1"]["schedule_value_m3"] == pytest.approx(0.216)          # shown, never totalled
    ov = {"m1": {"L_m": 1.5, "W_m": 1.4, "H_m": 0.3, "source": "DIMENSION H99 bound to this outline"}}
    rows, _, _ = run(segs, [mark("m1", "F", 700, 700, "F")], overrides=ov)
    assert rows["m1"]["geometry_state"] == SS.OVERRIDE and rows["m1"]["qty"] == pytest.approx(1.5 * 1.4 * 0.3)


def test_case_d_combined_outline_blocks_both_and_never_overrides_the_schedule():
    # one polyline 3250 x 1400 holding F10 and F, a 700 mm strap entering its north side
    segs = poly("H6939", [(1050, 1400), (0, 1400), (0, 0), (3250, 0), (3250, 1400), (1750, 1400)], closed=False)
    strap = [line("S1", 1050, 250, 1050, 9000), line("S2", 1750, 250, 1750, 9000)]
    rows, _, cands = run(segs + strap, [mark("t10", "F10", 180, 1000, "F10"), mark("tf", "F", 2600, 500, "F")])
    for k in ("t10", "tf"):
        assert rows[k]["geometry_state"] == SS.COMBINED and rows[k]["status"] == SS.BLOCKED and rows[k]["qty"] is None
    assert rows["t10"]["geometry"]["drawn_mm"] == [3250.0, 1400.0]
    assert rows["t10"]["schedule_value_m3"] == pytest.approx(2.8 * 1.4 * 0.5)
    # the A2 clipped parts (1.05 x 1.40 / 1.50 x 1.40) are not candidates of any type
    assert not any(abs((c["bounds"][2] - c["bounds"][0]) - 1500) < 1 for c in cands)


def test_count_first_and_count_unique_completion():
    # two F marks beside two free F-size outlines, each carrying a column; a third F inside its own outline
    a = poly("A", [(0, 0), (900, 0), (900, 800), (0, 800)])
    b = poly("B", [(5000, 0), (5900, 0), (5900, 800), (5000, 800)])
    c = poly("C", [(10000, 0), (10900, 0), (10900, 800), (10000, 800)])
    marks = [mark("m1", "C/F", 950, 900, "F"), mark("m2", "C/F", 5950, 900, "F"), mark("m3", "F", 10450, 400, "F")]
    rows, res, _ = run(a + b + c, marks, carriers=[(450, 400), (5450, 400), (10450, 300)])
    assert rows["m3"]["geometry_state"] == SS.CONFIRMED
    assert rows["m1"]["geometry_state"] == rows["m2"]["geometry_state"] == SS.COUNT_UNIQUE
    assert all(r["status"] == SS.COMPLETE for r in rows.values())
    # one more F mark with no third free outline -> the whole type's orphans stay blocked (never by distance)
    marks.append(mark("m4", "F", 20000, 20000, "F"))
    rows, _, _ = run(a + b + c, marks, carriers=[(450, 400), (5450, 400), (10450, 300)])
    assert {rows[k]["geometry_state"] for k in ("m1", "m2", "m4")} == {SS.UNBOUND}
    rec = SS.reconcile(marks, list(rows.values()), LIB)
    assert rec["state"] == "PASS" and rec["per_type"]["F"] == {"tags": 4, "computed": 1, "blocked": 3, "state": "PASS"}


def test_unscheduled_type_and_missing_height_block():
    segs = poly("A", [(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    rows, _, _ = run(segs, [mark("x", "FX", 500, 500, "FX"), mark("y", "FQ", 500, 500, "FQ")])
    assert rows["x"]["geometry_state"] == SS.NOT_SCHEDULED and rows["x"]["qty"] is None
    assert rows["y"]["geometry_state"] == SS.NOT_SCHEDULED


def test_type_summary_is_derived_from_occurrences():
    a = poly("A", [(0, 0), (900, 0), (900, 800), (0, 800)])
    b = poly("B", [(5000, 0), (5900, 0), (5900, 800), (5000, 800)])
    marks = [mark("m1", "F", 450, 400, "F"), mark("m2", "F", 5450, 400, "F")]
    rows, res, _ = run(a + b, marks)
    summ = {s["type"]: s for s in SS.type_summary(res["rows"], LIB)}
    assert summ["F"]["count_tagged"] == 2 and summ["F"]["count_geometry_confirmed"] == 2
    assert summ["F"]["m3_total_computed"] == pytest.approx(2 * 0.216) and summ["F"]["status"] == SS.COMPLETE
    assert summ["F10"]["count_tagged"] == 0 and summ["F10"]["status"] == "NOT_TAGGED_ON_PLAN"


def test_parse_mark_exact_tokens_only():
    ft = ["F", "F3", "F10", "FN"]
    assert SS.parse_mark("C3/F3", ft)["types"] == ["F3"]
    assert SS.parse_mark("CN/FN", ft)["types"] == ["FN"]
    assert SS.parse_mark("F12", ft)["types"] == []                          # never a prefix of F1 / F
    assert SS.parse_mark("FOUNDATION PLAN.", ft)["types"] == []
    p = SS.parse_mark("S.B1", ["SB1", "SB2"])
    assert p == {"types": ["SB1"], "normalised": True}
    assert SS.parse_mark("S.B1", ["SB1", "S.B1X"], normalise=False)["types"] == []


def test_columns_per_storey_and_printed_labels():
    lib = {"C1": {"FOUNDATION": {"B_cm": 30, "D_cm": 50, "reinf": "8 Ø 16"},
                  "GROUND FLOOR": {"B_cm": 20, "D_cm": 50, "reinf": "8 Ø 16"}},
           "CN": {"FOUNDATION": {"B_cm": 30, "D_cm": 30, "reinf": "4 Ø 14"}, "GROUND FLOOR": {}}}
    marks = [{"type": "C1", "key": f"c{i}"} for i in range(3)] + [{"type": "CN", "key": "n"}]
    out = SS.column_storeys(lib, marks, size_labels=["30X50", "30X50", "20X50", "30X30"],
                            per_sheet_outlines={"GROUND FLOOR": [(200, 500)] * 3})
    f, g = out["storeys"]["FOUNDATION"], out["storeys"]["GROUND FLOOR"]
    assert f["columns_with_section"] == 4 and f["plan_area_m2"] == pytest.approx(3 * 0.15 + 0.09)
    assert g["columns_with_section"] == 3 and g["plan_area_m2"] == pytest.approx(3 * 0.10)
    assert g["corroboration"]["state"] == "AGREES"
    assert {r["type"]: r["status"] for r in g["rows"]}["CN"] == "SECTION_NOT_SCHEDULED_FOR_STOREY"
    lab = out["printed_size_labels"]
    assert lab["closest_band"] == "FOUNDATION" and lab["by_band"]["FOUNDATION"]["deviation_count"] == 1


def test_strap_band_measured_between_footing_faces_only_when_the_mark_is_inside():
    f1 = SS.rect_candidate({"bounds": (0, 0, 1000, 1000)})
    f2 = SS.rect_candidate({"bounds": (0, 6000, 1000, 7000)})
    lines = [line("S1", 150, 500, 150, 6500), line("S2", 850, 500, 850, 6500)]
    lib = {"SB1": {"B_cm": 70, "D_cm": 50}}
    m_in = {"key": "s", "value": "S.B1", "type": "SB1", "x": 500, "y": 3000}
    r = SS.beam_bands([m_in], lib, lines, umm=1.0, tol_mm=2.0, eps=EPS, supports=[f1, f2])[0]
    assert r["state"] == "MEASURED" and r["length_m"] == pytest.approx(5.0, abs=0.01)
    assert r["volume_m3"] == pytest.approx(r["length_m"] * 0.7 * 0.5)
    m_out = dict(m_in, x=1200)
    assert SS.beam_bands([m_out], lib, lines, umm=1.0, tol_mm=2.0, eps=EPS, supports=[f1, f2])[0]["state"] == \
        "NO_BAND_HOLDS_THE_MARK"
    wrong = {"SB1": {"B_cm": 100, "D_cm": 50}}
    r_wrong = SS.beam_bands([m_in], wrong, lines, umm=1.0, tol_mm=2.0, eps=EPS, supports=[f1, f2])[0]
    assert r_wrong["state"] == "NO_BAND_HOLDS_THE_MARK" and r_wrong["pairs_between_mm"] == [700.0]
    near = {"SB1": {"B_cm": 72, "D_cm": 50}}                       # drawn 700 vs scheduled 720: 2.8 % -> flagged
    r_near = SS.beam_bands([m_in], near, lines, umm=1.0, tol_mm=2.0, eps=EPS, supports=[f1, f2])[0]
    assert r_near["state"] == "MEASURED_WITH_WIDTH_DEVIATION" and r_near["width_deviation_mm"] == -20.0
    assert r_near["volume_m3"] == pytest.approx(r_near["length_m"] * 0.72 * 0.5)     # schedule section governs
    free = SS.beam_bands([m_in], lib, lines, umm=1.0, tol_mm=2.0, eps=EPS, supports=[f1])[0]
    assert free["state"] == "SPAN_ENDS_NOT_AT_SUPPORTS" and free["volume_m3"] is None
    cb = SS.beam_bands([dict(m_in, type="CB3")], lib, lines, umm=1.0, tol_mm=2.0, eps=EPS, supports=[f1, f2])[0]
    assert cb["state"] == "SECTION_NOT_SCHEDULED"


def test_rebar_definitions_weight_blocked_and_ratio_refused():
    d = SS.rebar_definitions([{"element": "FOOTING", "type": "F", "fields": {"short": "8 Ø 12", "long": "7 Ø 12"}},
                              {"element": "FOOTING", "type": "F8", "fields": {"short": "6 Ø 14/m"}}])
    assert d[0]["bars"]["short"] == [{"count": 8, "dia_mm": 12, "per_m": False}] and d[0]["definition"] == SS.COMPLETE
    assert d[1]["bars"]["short"][0]["per_m"] is True
    assert all(x["weight_kg"] is None and x["weight_state"] == "BLOCKED" for x in d)
    with pytest.raises(ValueError):
        SS.rebar_definitions([{"element": "X", "type": "F", "fields": {"kg_per_m3": "90"}}])
