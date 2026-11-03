"""T-486 balcony / terrace waterproofing census (research/agents_t486). Synthetic villa (not the training villa) with
hand calculations, the adverse cases (a roof terrace already in the roof WP line is not added again; held is never 0;
mirror / rotation / mm units), and the development villa's census against the candidate roof WP lines."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t486"))
import t486_terrace_wp as T  # noqa: E402
import t486_alsenan as A  # noqa: E402

# ---- synthetic villa "Q" (hand-drawn, metres) ------------------------------------------------------------------------
# 1F terrace 6.00 x 3.00 over a habitable room, walls on three sides, the long north side an open slab edge;
# a 0.30 x 0.30 column in the south-west corner; a 1.00 x 1.00 light well through the slab.
TERRACE = [(0, 0), (6, 0), (6, 3), (0, 3)]
COLUMN = [(0, 0), (0.3, 0), (0.3, 0.3), (0, 0.3)]
WELL = [(3, 1), (4, 1), (4, 2), (3, 2)]
OPEN_N = [[(6, 3), (0, 3)]]


def test_terrace_geometry_by_hand():
    g = T.zone_geometry(TERRACE, footprints=[COLUMN], openings=[WELL], open_edges=OPEN_N)
    # area: 18.00 - 0.09 column - 1.00 well = 16.91
    assert g["gross_m2"] == pytest.approx(18.0)
    assert g["footprints_m2"] == pytest.approx(0.09)
    assert g["openings_m2"] == pytest.approx(1.0)
    assert g["net_m2"] == pytest.approx(16.91)
    # upturn: walls W 3 + S 6 + E 3 = 12, less 0.60 under the column, plus its two faces 0.60 = 12.00
    assert g["upturn_lm"] == pytest.approx(12.0)
    assert g["open_edge_lm"] == pytest.approx(6.0)
    assert g["opening_edge_lm"] == pytest.approx(4.0)
    assert g["perimeter_lm"] == pytest.approx(22.0)
    assert T.upturn_m2(g["upturn_lm"]) == pytest.approx(2.40)


@pytest.mark.parametrize("angle,mirror", [(0, True), (37, False), (37, True), (180, False)])
def test_rotation_and_mirror_do_not_change_the_quantities(angle, mirror):
    tr = lambda r: T.transformed(r, angle_deg=angle, mirror=mirror)  # noqa: E731
    g = T.zone_geometry(tr(TERRACE), footprints=[tr(COLUMN)], openings=[tr(WELL)],
                        open_edges=[tr(OPEN_N[0])])
    # the 1 micrometre snap grid moves an area by at most perimeter x 1e-6
    assert g["net_m2"] == pytest.approx(16.91, abs=5e-5)
    assert g["upturn_lm"] == pytest.approx(12.0, abs=5e-5)
    assert g["open_edge_lm"] == pytest.approx(6.0, abs=5e-5)


def test_millimetre_input():
    mm = lambda r: [(x * 1000, y * 1000) for x, y in r]  # noqa: E731
    g = T.zone_geometry(mm(TERRACE), footprints=[mm(COLUMN)], openings=[mm(WELL)], open_edges=[mm(OPEN_N[0])],
                        unit_m=0.001)
    assert g["net_m2"] == pytest.approx(16.91)
    assert g["upturn_lm"] == pytest.approx(12.0)


def test_a_cut_part_has_a_continuation_edge_not_an_upturn():
    # the west 2.00 m under an overhang, the rest open to the sky: the cut line 3.00 m is CONTINUATION
    west = T.zone_geometry(TERRACE, footprints=[COLUMN], open_edges=OPEN_N, clip=[(-1, -1), (2, -1), (2, 4), (-1, 4)])
    east = T.zone_geometry(TERRACE, footprints=[COLUMN], open_edges=OPEN_N, clip=[(2, -1), (7, -1), (7, 4), (2, 4)])
    assert west["net_m2"] == pytest.approx(6.0 - 0.09)
    assert east["net_m2"] == pytest.approx(12.0)
    assert west["continuation_lm"] == pytest.approx(3.0) and east["continuation_lm"] == pytest.approx(3.0)
    # west: W 3 + S 2 (less 0.6 under the column, + its 0.6 faces) = 5; east: S 4 + E 3 = 7; together the whole 12
    assert west["upturn_lm"] == pytest.approx(5.0) and east["upturn_lm"] == pytest.approx(7.0)
    assert west["open_edge_lm"] + east["open_edge_lm"] == pytest.approx(6.0)


def _villa_q():
    g = T.zone_geometry(TERRACE, footprints=[COLUMN], openings=[WELL], open_edges=OPEN_N)
    return [
        # accessible 1F terrace, no roof line over it: a B8-07 line is MISSING
        {"zone_id": "Q-1F-TERRACE", "label": None, "exposed": True, "below": "HABITABLE", "doors": 1,
         "membrane_m2": g["net_m2"], "upturn_lm": g["upturn_lm"], "carried": []},
        # 2F roof terrace (door from the stair), its membrane ALREADY in the roof WP line: carried, never added again
        {"zone_id": "Q-2F-ROOF-TERRACE", "label": "ROOF", "exposed": True, "below": "HABITABLE", "doors": 1,
         "membrane_m2": 40.0, "carried": [{"line_id": "L-roof-2f", "item_code": "FIN.WP.ROOF", "m2": 40.0}]},
        # cantilever balcony 4.00 x 1.50 drawn with a BALCONY label
        {"zone_id": "Q-BALCONY", "label": "BALCONY", "exposed": True, "below": "EXTERIOR", "doors": 1,
         "membrane_m2": 6.0, "carried": []},
        # a loggia under the floor above: not an exterior membrane
        {"zone_id": "Q-LOGGIA", "label": "BALCONY", "exposed": False, "doors": 1, "membrane_m2": 5.0},
        # a balcony whose outline is not closed: area unknown
        {"zone_id": "Q-BALCONY-2", "label": "BALCONY", "exposed": True, "doors": 1, "membrane_m2": None},
        # a non-accessible exposed slab (roof function) with no line
        {"zone_id": "Q-CANOPY", "label": None, "exposed": True, "below": "EXTERIOR", "doors": 0,
         "membrane_m2": 3.25, "carried": []},
    ]


def test_villa_census_normal():
    c = T.census(_villa_q())
    rows = {r["zone_id"]: r for r in c["rows"]}
    assert rows["Q-1F-TERRACE"]["status"] == T.MISSING and rows["Q-1F-TERRACE"]["family"] == "B8-07"
    assert rows["Q-1F-TERRACE"]["add_m2"] == pytest.approx(16.91)
    assert rows["Q-BALCONY"]["status"] == T.MISSING and rows["Q-BALCONY"]["add_m2"] == pytest.approx(6.0)
    assert rows["Q-LOGGIA"]["status"] == T.NOT_APPLICABLE
    assert rows["Q-CANOPY"]["family"] == "B8-06" and rows["Q-CANOPY"]["status"] == T.MISSING
    f = c["families"]
    assert f["B8-07"]["new_m2"] == pytest.approx(16.91 + 6.0)       # the roof terrace's 40.0 is NOT in it
    assert f["B8-07"]["carried_m2"] == pytest.approx(40.0)
    assert f["B8-06"]["new_m2"] == pytest.approx(3.25)


def test_adverse_a_roof_terrace_already_in_roof_wp_is_not_added_again():
    rows = {r["zone_id"]: r for r in T.census(_villa_q())["rows"]}
    r = rows["Q-2F-ROOF-TERRACE"]
    assert r["status"] == T.CARRIED and r["add_m2"] == 0.0 and r["carried_m2"] == pytest.approx(40.0)
    assert r["residual_m2"] == pytest.approx(0.0) and not r["flags"]


def test_adverse_held_is_never_zero():
    rows = {r["zone_id"]: r for r in T.census(_villa_q())["rows"]}
    r = rows["Q-BALCONY-2"]
    assert r["status"] == T.HELD and r["add_m2"] is None and "AREA_NOT_MEASURED" in r["flags"]
    u = T.classify({"zone_id": "U", "exposed": None, "doors": 1, "membrane_m2": 4.0})
    assert u["status"] == T.HELD and u["add_m2"] is None and "EXPOSURE_UNKNOWN" in u["flags"]
    h = T.classify({"zone_id": "H", "exposed": True, "doors": 0, "membrane_m2": 49.0,
                    "carried": [{"line_id": "L-top", "item_code": "FIN.WP.ROOF", "m2": None}]})
    assert h["status"] == T.HELD and h["add_m2"] is None and h["carried_m2"] is None
    assert T.upturn_m2(None) is None


def test_adverse_unexplained_carried_residual_is_flagged_and_mixed_lines_refused():
    r = T.classify({"zone_id": "R", "exposed": True, "doors": 1, "membrane_m2": 42.0,
                    "carried": [{"line_id": "L", "item_code": "FIN.WP.ROOF", "m2": 40.0}]})
    assert r["status"] == T.CARRIED and r["add_m2"] == 0.0 and "CARRIED_RESIDUAL_UNEXPLAINED" in r["flags"]
    with pytest.raises(ValueError):
        T.classify({"zone_id": "M", "exposed": True, "doors": 0, "membrane_m2": 10.0,
                    "carried": [{"line_id": "a", "item_code": "FIN.WP.ROOF", "m2": 5.0},
                                {"line_id": "b", "item_code": "FIN.WP.ROOF", "m2": None}]})
    with pytest.raises(ValueError):
        T.census(_villa_q() + [_villa_q()[0]])


def test_adverse_unknown_access_is_not_forced_into_a_family():
    r = T.classify({"zone_id": "A", "exposed": True, "doors": None, "membrane_m2": 7.0})
    assert r["family"] is None and "ACCESS_UNKNOWN" in r["flags"] and r["status"] == T.MISSING


# ---- development villa (the measured zone needs the private drawing; without it the zone must be HELD) -------------
HAVE_DXF = A.default_dxf() is not None


@pytest.fixture(scope="module")
def res():
    return A.build()


@pytest.mark.skipif(not HAVE_DXF, reason="private drawing not decoded in this checkout")
def test_dev_villa_poolcourt_slab(res):
    pc = res["poolcourt"]
    o, oh = pc["open_sky"], pc["overhang"]
    # T-062's independent trace (gross less the void, piers not deducted, merged): 6.130 m2, void 3.825 m2 / 7.139 lm
    assert pc["t062_basis_m2"] == pytest.approx(6.130, abs=0.001)
    assert pc["void_m2"] == pytest.approx(3.825, abs=0.001) and pc["void_perimeter_lm"] == pytest.approx(7.139, abs=1e-3)
    # the piers are the whole difference to T-062: 6.130 - piers = own net
    assert pc["t062_basis_m2"] - pc["footprints_m2"] == pytest.approx(pc["net_m2"], abs=1e-5)
    # the two parts re-add to the whole, nothing lost or doubled at the cut
    assert o["net_m2"] + oh["net_m2"] == pytest.approx(pc["net_m2"], abs=1e-5)
    assert o["upturn_lm"] + oh["upturn_lm"] == pytest.approx(pc["upturn_lm"], abs=1e-4)
    assert o["continuation_lm"] == pytest.approx(oh["continuation_lm"], abs=1e-6)
    # every boundary piece typed once
    assert pc["upturn_lm"] + pc["open_edge_lm"] + pc["opening_edge_lm"] == pytest.approx(pc["perimeter_lm"], abs=1e-5)
    # the overhang part's only upturn is the bay's outer face (its length read from the drawing on its own)
    assert oh["upturn_lm"] == pytest.approx(pc["bay_face_lm"], abs=1e-4)
    # the whole upturn = pier free faces + bay face + the straight wall / parapet pieces (at least the pier faces)
    assert pc["upturn_lm"] > sum(pc["footprint_free_faces_lm"].values()) + pc["bay_face_lm"]
    assert o["net_m2"] == pytest.approx(4.907, abs=1e-3) and oh["net_m2"] == pytest.approx(0.640, abs=1e-3)


@pytest.mark.skipif(not HAVE_DXF, reason="private drawing not decoded in this checkout")
def test_dev_villa_census(res):
    rows = {r["zone_id"]: r for r in res["census"]["rows"]}
    pc = rows["POOLCOURT-550"]
    assert pc["status"] == T.MISSING and pc["family"] == "B8-06" and pc["add_m2"] == pytest.approx(4.907, abs=1e-3)
    ov = rows["POOLCOURT-550-OVERHANG"]
    assert ov["status"] == T.HELD and ov["add_m2"] is None and ov["membrane_m2"] == pytest.approx(0.640, abs=1e-3)
    f = res["census"]["families"]
    assert f["B8-06"]["new_m2"] == pytest.approx(4.907, abs=1e-3)


def test_dev_villa_carried_zones_and_b8_07(res):
    rows = {r["zone_id"]: r for r in res["census"]["rows"]}
    assert res["candidate_version"] == "ARCH_TAKEOFF_V3.0.46"
    for z, m2 in (("ROOF-430", 55.559), ("TERRACE-550", 32.721), ("ROOF-970", 115.832)):
        assert rows[z]["status"] == T.CARRIED and rows[z]["add_m2"] == 0.0
        assert rows[z]["carried_m2"] == pytest.approx(m2) and not rows[z]["flags"]
    assert rows["ROOF-970"]["family"] == "B8-07"           # the only accessible roof terrace, already in FIN.WP.ROOF
    assert rows["ROOF-1390"]["status"] == T.HELD and rows["ROOF-1390"]["add_m2"] is None
    f = res["census"]["families"]
    assert f["B8-07"]["new_m2"] == 0.0 and f["B8-07"]["carried_m2"] == pytest.approx(115.832)


def test_without_the_drawing_the_measured_zone_is_held_not_zero(monkeypatch):
    monkeypatch.setattr(A, "default_dxf", lambda: None)
    rows = {r["zone_id"]: r for r in A.build()["census"]["rows"]}
    for z in ("POOLCOURT-550", "POOLCOURT-550-OVERHANG"):
        assert rows[z]["status"] == T.HELD and rows[z]["add_m2"] is None and rows[z]["membrane_m2"] is None


def test_no_candidate_line_carries_a_balcony_code(res):
    assert not [k for k, v in res["candidate_lines"].items() if v["item_code"] == "FIN.WP.BALCONY"]
