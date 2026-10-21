"""FOOTING_REBAR_POPULATION_V1 on a hand-calculated synthetic villa (NOT Alsenan: other marks, sizes, units, notations).

Hand values below were worked on paper from the fixture's own printed numbers: length = side - 2 x 75 mm cover,
kg/m = d^2 / 162 (12 -> 0.888889, 16 -> 1.580247). Spacing / per-metre counts are never released (owner Q-71):
readings A = ceil(inside / s), B = A + 1, C = rate x full side.
"""

from __future__ import annotations

import pytest

from engine.source import footing_rebar_population_v1 as P

COVER = {"value_mm": 75, "wording": "EXACT", "source": "synthetic general note 7"}
ENDS = {"BOTTOM": {"state": "STRAIGHT", "source": "synthetic typical footing detail"}, "TOP": None}
UMASS = {"method": "D2_OVER_162"}


def occ(cid, mark=None, **kw):
    """a route G FOOTINGS concrete item as data"""
    it = {"trade": "CONCRETE", "family": "FOOTINGS", "category": "PROVISIONAL", "base": 1.0,
          "component_id": cid if mark is None else f"FTG:S1:{mark}@{cid}", "blocker": "NOT_REVIEWED",
          "formula": "L x W x D (schedule; drawn outline confirms L x W)", "dimensions": {}}
    it.update(kw)
    return it


def rows():
    k1 = P.schedule_row("K1", (1500, 2000, 450), "mm", {"BOTTOM_SHORT": "10 T 16", "BOTTOM_LONG": "8Ø16"})
    k2 = P.schedule_row("K2", (300, 250, 60), "cm", {"BOTTOM_SHORT": "T12 @ 15cm", "BOTTOM_LONG": "T12@15"},
                        spacing_unit="cm")
    k3 = P.rows_from_block_attributes({"FO-TY": "K3", "W": "400", "H": "320", "DEPHT": "60", "SH-B-B": "8",
                                       "SH-B-D": "16/m", "LO-B-B": "8", "LO-B-D": "16/m", "SH-T-B": "5",
                                       "SH-T-D": "12/m", "LO-T-B": "", "LO-T-D": ""}, "cm")
    k4 = P.schedule_row("K4", (1200, 1200, 400), "mm", {"BOTTOM_SHORT": P.parse_cell(merged=True),
                                                         "BOTTOM_LONG": "9 T 12"})
    k9 = P.schedule_row("K9", (900, 900, 300), "mm", {"BOTTOM_SHORT": "6 T 12", "BOTTOM_LONG": "6 T 12"})
    return [k1, k2, k3, k4, k9]


def footings():
    return P.footings_from_route_items([
        occ("1,1", "K1"), occ("5,5", "K1"),                      # two occurrences of K1
        occ("9,1", "K2"), occ("9,9", "K3"), occ("3,3", "K4"),
        occ("FTG:S1:T7:AB"),                                       # one footing with two marks
        occ("4,4", "K1", formula="drawn polygon area x D; the outline is clipped where it meets a neighbour"),
        occ("8,8", "K5"),                                          # mark with no schedule row
        {"trade": "REINFORCEMENT", "family": "FOOTINGS", "component_id": "x"}])  # steel rows are ignored


def comp(res, cid_part, name):
    return next(c for c in res["components"] if cid_part in c["occurrence_id"] and c["component"] == name)


@pytest.fixture(scope="module")
def res():
    return P.run(footings(), rows(), cover=COVER, end_treatment=ENDS, unit_mass=UMASS)


def test_parse_notations_and_units():
    assert P.parse_cell("10 T 16") == {"mode": P.EXPLICIT, "count": 10, "dia_mm": 16.0, "raw": "10 T 16"}
    assert P.parse_cell("%%c12@200")["mode"] == P.UNREADABLE          # no unit printed, none in the header
    assert P.parse_cell("%%c12@200", spacing_unit="mm")["spacing_mm"] == 200.0
    assert P.parse_cell("T12@0.2m")["spacing_mm"] == pytest.approx(200.0)
    assert P.parse_cell("9 ø 14/m")["rate_per_m"] == 9.0
    assert P.parse_cell(count="9", dia="14/m")["mode"] == P.PER_METRE
    assert P.parse_cell(count="8", dia="12")["count"] == 8
    assert P.parse_cell(count="", dia="")["mode"] == P.EMPTY
    assert P.parse_cell("see detail 3")["mode"] == P.UNREADABLE


def test_explicit_count_released_by_hand(res):
    s, lg = comp(res, "1,1", "BOTTOM_SHORT"), comp(res, "1,1", "BOTTOM_LONG")
    # SHORT: 10 bars x (1500 - 150) = 1.35 m x 1.580247 = 21.3333 kg; LONG: 8 x 1.85 x 1.580247 = 23.3877 kg
    assert (s["status"], s["count"], s["bar_length_m"]) == (P.RELEASED, 10, pytest.approx(1.35))
    assert s["net_kg"] == pytest.approx(21.33333, abs=1e-4)
    assert (lg["status"], lg["count"], lg["bar_length_m"]) == (P.RELEASED, 8, pytest.approx(1.85))
    assert lg["net_kg"] == pytest.approx(23.38765, abs=1e-4)
    assert s["procurement_kg"] == s["net_kg"]                    # bar under 12 m: no splice, procurement = net
    assert comp(res, "1,1", "TOP_SHORT")["status"] == P.NOT_APPLICABLE


def test_spacing_notation_held_with_three_readings(res):
    s = comp(res, "9,1", "BOTTOM_SHORT")
    assert s["status"] == P.HELD and s["net_kg"] is None and any("Q-71" in r for r in s["reasons"])
    # run 2500 - 150 = 2.35 m; spread over 3000, inside 2850 / 150 = 19 -> A 19, B 20; C 3000 / 150 = 20
    r = s["readings"]
    assert (r["A_ceil_inside_cover"]["count"], r["B_A_plus_edge_bar"]["count"]) == (19, 20)
    assert r["A_ceil_inside_cover"]["kg"] == pytest.approx(39.68889, abs=1e-4)
    assert r["B_A_plus_edge_bar"]["kg"] == pytest.approx(41.77778, abs=1e-4)
    assert r["C_rate_x_full_side"]["kg"] == pytest.approx(41.77778, abs=1e-4)
    lg = comp(res, "9,1", "BOTTOM_LONG")                         # unit from the header (cm): same 150 mm
    # run 2.85 m; inside 2350 / 150 = 15.67 -> A 16, B 17; C 2500 / 150 = 16.667
    assert lg["count_range"] == (16, 17)
    assert lg["readings"]["A_ceil_inside_cover"]["kg"] == pytest.approx(40.53333, abs=1e-4)
    assert lg["readings"]["C_rate_x_full_side"]["kg"] == pytest.approx(42.22222, abs=1e-4)


def test_two_layer_per_metre_block_row(res):
    b = comp(res, "9,9", "BOTTOM_SHORT")
    # 8 / m of T16: s = 125; run 3200 - 150 = 3.05 m; inside 3850 / 125 = 30.8 -> A 31; C = 8 x 4.0 = 32
    assert b["count_range"] == (31, 32) and b["bar_length_m"] == pytest.approx(3.05)
    assert b["readings"]["A_ceil_inside_cover"]["kg"] == pytest.approx(31 * 3.05 * 256 / 162)
    assert b["readings"]["C_rate_x_full_side"]["count"] == pytest.approx(32.0)
    t = comp(res, "9,9", "TOP_SHORT")
    assert t["status"] == P.HELD and any(r.startswith("END_TREATMENT_NOT_DRAWN") for r in t["reasons"])
    assert comp(res, "9,9", "TOP_LONG")["status"] == P.HELD       # empty printed cell
    assert comp(res, "9,9", "TOP_LONG")["net_kg_range"] is None


def test_mirror_and_rotation_do_not_change_steel():
    """the same footing printed with its sides swapped (a mirrored / rotated schedule row) gives the same steel"""
    a = P.schedule_row("M", (2000, 1500, 450), "mm", {"BOTTOM_SHORT": "10 T 16", "BOTTOM_LONG": "8 T 16"})
    b = P.schedule_row("M", (1500, 2000, 450), "mm", {"BOTTOM_SHORT": "10 T 16", "BOTTOM_LONG": "8 T 16"})
    f = P.footings_from_route_items([occ("1,1", "M", dimensions={"drawn_m": [1.5, 2.0]})])
    g = P.footings_from_route_items([occ("1,1", "M", dimensions={"drawn_m": [2.0, 1.5]})])
    ra = P.run(f, [a], cover=COVER, end_treatment=ENDS, unit_mass=UMASS)
    rb = P.run(g, [b], cover=COVER, end_treatment=ENDS, unit_mass=UMASS)
    assert ra["totals"]["released_kg"] == pytest.approx(rb["totals"]["released_kg"]) == pytest.approx(44.72099,
                                                                                                         abs=1e-4)


def test_units_mm_cm_m_agree():
    kw = {"BOTTOM_SHORT": "10 T 16", "BOTTOM_LONG": "8 T 16"}
    vals = [P.run(P.footings_from_route_items([occ("1,1", "U")]), [P.schedule_row("U", s, u, kw)], cover=COVER,
                  end_treatment=ENDS, unit_mass=UMASS)["totals"]["released_kg"]
            for s, u in (((1500, 2000, 450), "mm"), ((150, 200, 45), "cm"), ((1.5, 2.0, 0.45), "m"))]
    assert vals[0] == pytest.approx(vals[1]) == pytest.approx(vals[2])
    held = P.run(P.footings_from_route_items([occ("1,1", "U")]), [P.schedule_row("U", (150, 200, 45), None, kw)],
                 cover=COVER, end_treatment=ENDS, unit_mass=UMASS)
    assert held["totals"]["released_kg"] == 0 and held["occurrences"][0]["status"] == P.HELD
    assert any("UNIT_NOT_PRINTED" in r for c in held["components"] for r in c["reasons"])


def test_merged_cell_and_held_footings_never_zero(res):
    m = comp(res, "3,3", "BOTTOM_SHORT")
    assert m["status"] == P.HELD and m["net_kg"] is None and m["reasons"][0].startswith("MERGED")
    assert comp(res, "3,3", "BOTTOM_LONG")["status"] == P.RELEASED  # its own printed cell stays released
    two = [o for o in res["occurrences"] if o["mark"] is None][0]
    assert two["status"] == P.HELD and "TWO_MARKS" in two["held"] and two["released_kg"] == 0
    clip = [c for c in res["components"] if "4,4" in c["occurrence_id"] and c["component"] == "BOTTOM_SHORT"][0]
    assert clip["status"] == P.HELD and clip["reasons"][0].startswith("OUTLINE_CLIPPED") and clip["net_kg"] is None
    k5 = [o for o in res["occurrences"] if o["mark"] == "K5"][0]
    assert k5["status"] == P.HELD and k5["held"].startswith("NO_SCHEDULE_ROW")
    assert res["schedule_rows_without_footing"] == ["K9"]          # listed, no steel created from a row alone
    assert res["check"]["all_pass"]


def test_project_totals_by_hand(res):
    # released: K1 x 2 (44.72099 each) + K4 long 9 x (1.2 - 0.15) x 0.888889 = 8.4 kg
    assert res["totals"]["released_kg"] == pytest.approx(2 * 44.72099 + 8.4, abs=1e-3)
    assert res["totals"]["occurrences"] == 8 and res["totals"]["occurrences_released"] == 2
    assert res["totals"]["held_kg_low"] > 0 and res["totals"]["held_kg_high"] >= res["totals"]["held_kg_low"]


def test_no_cover_holds_every_length():
    r = P.run(P.footings_from_route_items([occ("1,1", "K1")]), rows()[:1], cover=None, end_treatment=ENDS,
              unit_mass=UMASS)
    assert r["totals"]["released_kg"] == 0
    assert all(c["status"] in (P.HELD, P.NOT_APPLICABLE) and c["net_kg"] is None for c in r["components"])
    assert any("COVER_NOT_PRINTED" in x for c in r["components"] for x in c["reasons"])


def test_bar_over_stock_length_holds_procurement():
    big = P.schedule_row("G", (13000, 2000, 900), "mm", {"BOTTOM_LONG": "10 T 16"})
    r = P.run(P.footings_from_route_items([occ("1,1", "G")]), [big], cover=COVER, end_treatment=ENDS,
              unit_mass=UMASS)
    c = comp(r, "1,1", "BOTTOM_LONG")
    assert c["status"] == P.HELD and any("PROCUREMENT_LAP_NOT_PRINTED" in x for x in c["reasons"])
    assert r["stock_length_m"] == 12.0


def test_module_is_project_agnostic():
    src = open(P.__file__, encoding="utf-8").read()
    for bad in ("Alsenan", "ST7757", "SH10", "F12", "FF@", "kg/m3 ratio"):
        assert bad not in src, bad


def test_boxed_cell_is_held_unquantified():
    r = P.rows_from_block_attributes({"FO-TY": "B1", "W": "150", "H": "150", "DEPHT": "40", "SH-B": "10",
                                      "SH-D": "12", "LO-B": "10", "LO-D": "12", "BOXED": "2+3"}, "cm")
    e = P.rows_from_block_attributes({"FO-TY": "B2", "W": "150", "H": "150", "DEPHT": "40", "SH-B": "10",
                                      "SH-D": "12", "LO-B": "10", "LO-D": "12", "BOXED": ""}, "cm")
    res = P.run(P.footings_from_route_items([occ("1,1", "B1"), occ("2,2", "B2")]), [r, e], cover=COVER,
                end_treatment=ENDS, unit_mass=UMASS)
    o1, o2 = sorted(res["occurrences"], key=lambda o: o["mark"])
    assert o1["held_unquantified"] == ["BOXED(printed '2+3')"] and o2["held_unquantified"] == ["BOXED(printed '')"]
    # mesh: 10 x (1.50 - 0.15) x 0.888889 = 12.0 kg each way, released; the boxed bars are not in it
    assert o1["released_kg"] == pytest.approx(24.0, abs=1e-6)
    assert res["totals"]["held_unquantified_components"] == 2
