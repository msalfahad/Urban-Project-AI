"""T-267: the main chat's adversarial acceptance A1 - A23 + A12b (OWNER_RULE_STAIRS_2026-10-24.md section 5 / 6). Each
test names the wrong logic it must catch; expected values are hand calculations or shapely (an independent library)."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union

from engine.source import stair_finish_levels_v1 as M

from .fixtures import MARBLE, dog_leg, rect, straight

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "engine/source/stair_finish_levels_v1.py"
VERIFIED_2100 = {"value": 2100.0, "source": "synthetic verified clause", "verified": True}


def line(res, comp, part):
    (ln,) = [x for x in res["lines"] if x["component"] == comp and x["part"] == part]
    return ln


def codes(res):
    return [f["code"] for f in res["findings"]]


def flight(res, f):
    return {g["flight"]: g for g in res["goings"]}[f]


# A1 / A2: goings from the drawn treads (catches a hard-coded N - 1, and its converse)
def test_a1_top_tread_drawn_before_the_landing_gives_n_goings():
    g = flight(M.check_stair(dog_leg(8, 6, 160.0, top_tread_drawn=True)), "A")
    assert (g["risers"], g["goings"], g["configuration"]) == (8, 8, "LAST_TREAD_AT_LANDING_LEVEL")


def test_a2_landing_is_the_top_tread_gives_n_minus_1_with_evidence():
    g = flight(M.check_stair(dog_leg(8, 6, 160.0, top_tread_drawn=False)), "A")
    assert (g["risers"], g["goings"], g["configuration"]) == (8, 7, "LAST_RISER_ONTO_NEXT_LEVEL")


# A3: a split-level landing: two landing surfaces, one extra riser between them, levels from the record
def test_a3_split_level_landing():
    rec = dog_leg(6, 6, 160.0)
    i = [s["id"] for s in rec["surfaces"]].index("L")
    rec["surfaces"][i]["polygon"] = rect(0, 0, 1300, 1150)
    rec["surfaces"].insert(i + 1, {"id": "L2", "kind": "LANDING", "finish_mm": 50.0, "polygon": rect(1300, 0, 2500, 1200),
                                   "thickness_mm": 160.0})
    rec["ffl_top_mm"] = 13 * 160.0                         # one riser more: 13
    res = M.check_stair(rec)
    lv = res["levels"]
    assert lv["n_risers"] == 13
    r7 = lv["risers"][6]
    assert (r7["from"], r7["onto"]) == ("L", "L2")
    assert r7["structural_riser_mm"] == pytest.approx(160.0)            # 160 + 50 - 50
    assert 7 in res["flights"]["transition_risers"]
    lands = {x["landing"]: x["area_m2"] for x in res["landings"]}
    assert lands == pytest.approx({"L": 1.495, "L2": 1.44})              # 1.30 x 1.15, 1.20 x 1.20
    assert "SURFACE_OVERLAP" not in codes(res)


# A4: quarter landings are their drawn polygons (catches width x width)
@pytest.mark.parametrize("poly,hand", [
    ([(0, 0), (1200, 0), (1200, 900), (900, 1200), (0, 1200)], 1.44 - 0.5 * 0.3 * 0.3),           # chamfer 300
    ([(200, 0), (1200, 0), (1200, 1200), (0, 1200), (0, 200), (200, 200)], 1.44 - 0.2 * 0.2),     # column notch
])
def test_a4_quarter_landing_polygon(poly, hand):
    rec = dog_leg(6, 6, 160.0, landing_poly=poly)
    a = {x["landing"]: x["area_m2"] for x in M.check_stair(rec)["landings"]}["L"]
    assert a == pytest.approx(hand) and a == pytest.approx(Polygon(poly).area / 1e6)
    assert a != pytest.approx(1.44)
    assert line(M.check_stair(rec), "MARBLE_LANDING", "L")["quantity"] == pytest.approx(hand)


# A5: a half landing with a curved edge (sagitta 300 on a 2600 chord), exact by its arc
def test_a5_half_landing_curved_edge():
    c, s = 2600.0, 300.0
    b = 2 * s / c                                                        # bulge = tan(theta / 4) = 2 s / c
    poly = [(0.0, 0.0), (2600.0, 0.0), (2600.0, 1200.0, b), (0.0, 1200.0)]
    r = (c * c / 4 + s * s) / (2 * s)                                    # 2966.67
    th = 4 * math.atan(b)
    hand = (2600.0 * 1200.0 + r * r / 2 * (th - math.sin(th))) / 1e6
    got = {x["landing"]: x["area_m2"] for x in M.check_stair(dog_leg(6, 6, 160.0, landing_poly=poly))["landings"]}["L"]
    assert got == pytest.approx(hand, rel=1e-12)
    # independent: the arc as 2000 shapely points about its centre (cy = 1200 - (r - s))
    cy = 1200.0 - (r - s)
    a0, a1 = math.atan2(1200.0 - cy, 1300.0), math.atan2(1200.0 - cy, -1300.0)
    arc = [(1300.0 + r * math.cos(a0 + (a1 - a0) * k / 2000), cy + r * math.sin(a0 + (a1 - a0) * k / 2000))
           for k in range(2001)]
    assert got == pytest.approx(Polygon([(0, 0), (2600, 0)] + arc).area / 1e6, rel=1e-5)
    assert got > 3.12                                                   # never the 2.60 x 1.20 rectangle


# A6: landing and treads touch, no overlap; a floor-level landing is floor finish (catches double counting)
def _touching():
    rec = straight(3, 160.0, polygons=True)                              # T1 0..300, T2 300..600
    rec["floor_landings"] = [{"id": "FLB", "floor": "BOTTOM", "polygon": rect(-1000, 0, 0, 1200)},
                             {"id": "FLT", "floor": "TOP", "polygon": rect(600, 0, 1800, 1200)}]
    return rec


def test_a6_touching_surfaces_no_overlap_and_floor_landing_to_the_floor():
    rec = _touching()
    res = M.check_stair(rec)
    assert "SURFACE_OVERLAP" not in codes(res)
    polys = [Polygon(s["polygon"]) for s in rec["surfaces"]] + [Polygon(x["polygon"]) for x in rec["floor_landings"]]
    assert unary_union(polys).area == pytest.approx(sum(p.area for p in polys))
    assert {x["part"] for x in res["lines"] if x["component"] == "FLOOR_FINISH_NOT_STAIR"} == {"FLB", "FLT"}
    assert not [x for x in res["lines"] if x["component"] == "MARBLE_LANDING"]
    stair_m2 = sum(x["quantity"] for x in res["lines"] if x["component"] == "MARBLE_TREAD")
    assert stair_m2 == pytest.approx(2 * 0.3 * 1.2)


def test_a6_adverse_overlap_is_reported():
    rec = _touching()
    rec["floor_landings"][1]["polygon"] = rect(500, 0, 1800, 1200)        # 100 x 1200 over T2
    (f,) = [x for x in M.check_stair(rec)["findings"] if x["code"] == "SURFACE_OVERLAP"]
    assert f["values"]["overlap_mm2"] == pytest.approx(100.0 * 1200.0)
    assert M.overlap_area(rect(0, 0, 10, 10), rect(5, 5, 15, 15)) == pytest.approx(25.0)
    assert M.overlap_area(rect(0, 0, 10, 10), rect(10, 0, 20, 10)) == pytest.approx(0.0, abs=1e-9)


# A7 / A8: drawn winders measured from their polygons; a missing winder outline holds that winder only
W1 = [(0, 0), (1200, 0), (1200, 700)]
W2 = [(0, 0), (1200, 700), (1200, 1200), (700, 1200)]
W3 = [(0, 0), (700, 1200), (0, 1200)]


def _winders(w2=W2):
    rec = straight(4, 160.0)                                             # A: T1..T3
    rec["surfaces"] += [{"id": "W1", "kind": "WINDER", "flight": "W", "finish_mm": 30.0, "polygon": W1},
                        {"id": "W2", "kind": "WINDER", "flight": "W", "finish_mm": 30.0, "polygon": w2},
                        {"id": "W3", "kind": "WINDER", "flight": "W", "finish_mm": 30.0, "polygon": W3}]
    rec["ffl_top_mm"] = 7 * 160.0
    rec["flights"]["W"] = {"rail_sides": ["LEFT"]}
    return rec


def test_a7_winders_from_drawn_polygons():
    res = M.check_stair(_winders())
    got = [line(res, "MARBLE_TREAD", w)["quantity"] for w in ("W1", "W2", "W3")]
    assert got == pytest.approx([0.42, 0.60, 0.42])                     # 0.5 x 1.2 x 0.7; 1.44 - 0.84; 0.5 x 0.7 x 1.2
    assert line(res, "CONCRETE", "flight W")["status"] == M.HELD
    assert line(res, "HANDRAIL", "flight W")["status"] == M.UNSUPPORTED
    assert flight(res, "W")["alternatives"] is None                     # no going is computed for a winder


def test_a8_winder_dimension_missing_holds_that_winder_only():
    res = M.check_stair(_winders(w2=None))
    assert line(res, "MARBLE_TREAD", "W2")["status"] == M.HELD and line(res, "MARBLE_TREAD", "W2")["quantity"] is None
    assert line(res, "MARBLE_TREAD", "W1")["status"] == M.MEASURED
    assert line(res, "CONCRETE", "flight A")["status"] == M.MEASURED
    assert line(res, "MARBLE_TREAD", "T1")["status"] == M.MEASURED


# A9 / A10: no winder generation, no hidden off-axis default
def test_a9_undrawn_stair_needing_winders_is_unsupported():
    rep = M.alternatives(3000.0, 2000.0, M.FIXED, configuration="WINDERS")
    assert rep["status"] == M.UNSUPPORTED and rep["alternatives"] == []
    assert M.alternatives(3000.0, 2000.0, M.FIXED, configuration="U_WITH_LANDING")["status"] == M.UNSUPPORTED


def test_a10_static_no_offset_default_and_no_winder_generator():
    src = MOD.read_text(encoding="utf-8")
    assert "walk" not in src.lower()
    assert not re.search(r"def \w*winder\w*\(", src, re.I)
    assert "annular_flight" not in src and "winder_plane_volume" not in src and "winder_bounds" not in src


# A11 / A12 / A12b: maximum vs fixed run, unknown run type (4.48 m)
def _feasible(rep):
    return {a["risers"]: a["going_interval_mm"] for a in rep["alternatives"] if a["feasible"]}


def test_a11_maximum_run_longer_never_removes():
    short, long_ = _feasible(M.alternatives(4480.0, 7560.0, M.MAXIMUM)), _feasible(M.alternatives(4480.0, 8400.0, M.MAXIMUM))
    assert set(short) <= set(long_)
    assert short == pytest.approx({27: [280.0, 7560.0 / 26], 28: [280.0, 280.0]})      # 29: 7560 / 28 = 270 < 280
    for n, (lo, hi) in short.items():
        assert long_[n][0] <= lo and long_[n][1] >= hi


def test_a12_fixed_run_is_not_monotone():
    a = _feasible(M.alternatives(4480.0, 7560.0, M.FIXED))
    b = _feasible(M.alternatives(4480.0, 8400.0, M.FIXED))
    assert a[28] == pytest.approx([280.0, 280.0])                        # 7560 / 27
    assert 28 not in b                                                  # 8400 / 27 = 311.1
    assert b[29] == pytest.approx([300.0, 300.0])                        # 8400 / 28


def test_a12b_run_type_unknown_gives_scenarios_only():
    rep = M.alternatives(4480.0, 7560.0, M.UNKNOWN)
    assert rep["status"] == M.UNKNOWN and rep["selected"] is None
    assert all(a["feasible"] is None and a["going_interval_mm"] is None for a in rep["alternatives"])
    rec = straight(28, 160.0, run_type=M.UNKNOWN)
    (f,) = M.check_stair(rec)["fit"]
    assert f["status"] == M.UNKNOWN and f["result"] is None


# A13: 4.48 m, 28 x 160, straight vs U: fit, goings, landing, headroom as four separate results
def test_a13_four_separate_results():
    st = M.check_stair(straight(28, 160.0, going=280.0))
    u = dog_leg(14, 14, 160.0, going=280.0)
    u["overhead"] = [{"id": "BM", "flight": "B", "s_from_mm": 0.0, "s_to_mm": 250.0, "soffit_mm": 4480.0}]
    uu = M.check_stair(u)
    for res in (st, uu):
        assert {"fit", "goings", "landings", "headroom"} <= set(res)
    assert st["fit"][0]["result"] == "FITS" and st["fit"][0]["first_to_last_riser_mm"] == pytest.approx(27 * 280.0)
    assert [g["goings"] for g in st["goings"]] == [27] and st["landings"] == [] and st["headroom"] == []
    assert [(g["risers"], g["goings"]) for g in uu["goings"]] == [(14, 13), (14, 13)]
    assert uu["landings"][0]["area_m2"] == pytest.approx(3.0)
    assert uu["headroom"][0]["clear_mm"] == pytest.approx(4480.0 - 15 * 160.0)          # B1 at level 15
    assert uu["headroom"][0]["check"] == "NO_LIMIT_GIVEN"
    assert all(f["status"] == M.UNKNOWN for f in uu["fit"])                             # no run given


# A14: a slab edge over the stair: headroom meets the limit for one going and not for another
def test_a14_headroom_per_going():
    # a member over the lower part of the flight, ending at the edge 3200 from the first riser line, soffit +3860.
    # The highest tread under it governs: k = ceil(3200 / g) (tread k spans (k - 1) g .. k g).
    oh = [{"id": "EDGE", "s_from_mm": 0.0, "s_to_mm": 3200.0, "soffit_mm": 3860.0}]
    rep = M.alternatives(4480.0, 8400.0, M.MAXIMUM, overhead=oh, headroom_limit=VERIFIED_2100)
    alt = {a["risers"]: a for a in rep["alternatives"]}
    # n 28 (160): g > 3200 / 11 = 290.91 -> tread 11 (1760) clear 2100 meets; g < 290.91 -> tread 12 (1920) 1940 fails
    (iv,) = alt[28]["headroom"]["going_intervals_meeting_limit"]
    assert iv["from_mm"] == pytest.approx(3200.0 / 11) and iv["to_mm"] == pytest.approx(300.0) and iv["to_closed"]
    assert alt[28]["feasible"] is True
    probe = {round(p["piece_mm"][0], 3): p for p in alt[28]["headroom"]["probes"]}
    assert probe[280.0]["min_clear_mm"] == pytest.approx(3860.0 - 12 * 160.0) and not probe[280.0]["meets_limit"]
    # n 27 (165.93): tread 11 clear 3860 - 11 x 165.93 = 2034.8 < 2100 for every going -> eliminated (VERIFIED limit)
    assert alt[27]["feasible"] is False and alt[27]["headroom"]["going_intervals_meeting_limit"] == []
    unv = M.alternatives(4480.0, 8400.0, M.MAXIMUM, overhead=oh, headroom_limit=dict(VERIFIED_2100, verified=False))
    u27 = {a["risers"]: a for a in unv["alternatives"]}[27]
    assert u27["feasible"] is True and u27["headroom"]["status"] == M.CODE_NOT_VERIFIED          # not enforced


# A15 / A16: each component released on its own evidence
def test_a15_concrete_released_marble_rail_bars_held():
    res = M.check_stair(straight(10, 160.0, finish=None, sides=None))
    c = res["components"]
    assert c["CONCRETE"]["status"] == M.MEASURED
    assert c["MARBLE_TREAD"]["status"] == M.HELD and "stair finish material (drawing / specification)" in c["MARBLE_TREAD"]["missing"]
    assert c["MARBLE_RISER"]["status"] == M.HELD
    assert c["HANDRAIL"]["status"] == M.HELD and "rail sides (drawing)" in c["HANDRAIL"]["missing"]
    assert c["BARS"]["status"] == M.HELD and "printed bar detail of the stair" in c["BARS"]["missing"]


def test_a16_marble_released_concrete_held():
    res = M.check_stair(straight(10, 160.0, waist=None))
    c = res["components"]
    assert c["MARBLE_TREAD"]["status"] == M.MEASURED and c["MARBLE_RISER"]["status"] == M.MEASURED
    assert c["CONCRETE"]["status"] == M.HELD and "waist thickness" in c["CONCRETE"]["missing"]


# A17 / A18: scenario report separate from the measured export; HELD blank, never 0 or a range
def test_a17_scenario_never_leaks_into_the_measured_export():
    rec = straight(10, 160.0, waist=None)
    before = M.export_csv(M.measured_rows(M.check_stair(rec))).encode()
    rep = M.alternatives(1600.0, 2700.0, M.FIXED, width_mm=1200.0, show_illustrative=True)
    after = M.export_csv(M.measured_rows(M.check_stair(rec))).encode()
    assert before == after
    assert json.loads(M.scenario_json(rep))["schema"] == M.SCENARIO_SCHEMA
    assert rep["illustrative"]["riser_mm"] == 160.0 and "ILLUSTRATIVE" in rep["illustrative"]["label"]
    with pytest.raises(M.StairFinishError):
        M.load_measured_rows([{"row_kind": "SCENARIO", "schema": M.SCENARIO_SCHEMA}])
    with pytest.raises(M.StairFinishError):
        M.load_measured_rows(rep)
    with pytest.raises(M.StairFinishError):
        M.export_csv([dict(rep["alternatives"][0], row_kind="SCENARIO")])
    assert len(M.load_measured_rows(M.measured_rows(M.check_stair(rec)))) > 0


def test_a18_held_is_blank_never_zero_or_range():
    rows = M.measured_rows(M.check_stair(straight(10, 160.0, waist=None)))
    held = [r for r in rows if r["status"] != M.MEASURED]
    assert held and all(r["quantity"] is None for r in held)
    with pytest.raises(M.StairFinishError):
        M.load_measured_rows([dict(held[0], quantity=0)])
    with pytest.raises(M.StairFinishError):
        M.load_measured_rows([dict(held[0], quantity=[0.8, 0.9])])


# A19 - A22: code applicability by building type; never a conformity claim
def test_a19_private_villa_no_udc_check():
    c = M.code_applicability("PRIVATE_HOUSE")
    udc = [s for s in c["sources"] if "Universal Design Code" in s["source"]][0]
    assert udc["status"] == "NOT_APPLICABLE" and udc["checks_emitted"] is False and "section 4" in udc["source"]
    assert c["regulatory_status"] == M.CODE_NOT_VERIFIED


def test_a20_dwelling_development_public_areas_only():
    udc = [s for s in M.code_applicability("DWELLING_DEVELOPMENT")["sources"] if "Universal" in s["source"]][0]
    assert udc["status"] == M.CODE_NOT_VERIFIED and udc["applies_to"].startswith("public areas only")
    assert udc["private_units"] == "NOT_APPLICABLE" and udc["enforced"] is False


def test_a21_building_type_missing():
    c = M.code_applicability(None)
    assert c["applicability_decided"] is False
    assert all(s["status"] == M.CODE_NOT_VERIFIED for s in c["sources"])


def test_a22_never_the_word_compliant():
    outs = [M.check_stair(dog_leg(6, 6, 160.0)), M.check_stair(straight(10, 180.0, going=260.0)),
            M.alternatives(4480.0, 8400.0, M.MAXIMUM), M.code_applicability(None)]
    for o in outs:
        assert "COMPLIANT" not in json.dumps(o, default=str).upper()
    assert M.check_stair(dog_leg(6, 6, 160.0))["code"]["statement"].startswith("no conflict found against verified clauses")


# A23: frozen stair modules and the 1.6.0 rule file unchanged; the new module is imported by no engine / tools code
PINNED = {
    "engine/source/stair_riser_schedule.py": "d2a5d0dd584354d9c6d4d4b403808dd1384b61cad35ce717e02dfaa215eea7f0",
    "engine/source/stair_fit_checks.py": "371e2f6b16b441b7df61b2de0ae354fea1b2d1df2e6ccd4484ffdd031ecbff19",
    "engine/source/stair_scenario_checks.py": "aec8209d2617c916a960319a52710fd0a07ced071ff0e081491d73dc9645d82c",
    "engine/source/stair_geometry.py": "d9bc4eaf96ae4eb966c6c0141d7a041ae24ec8ecd385e36afaa958c728e897ed",
    "engine/source/stair_measure.py": "6b762f3e9bf8f5351f55fd59674ac15d6849cbf49f9ab7edab50d6d66f003162",
    "engine/source/stair_rule_calculator.py": "50f7ce7bc9d0490eb73a08a3eb1f0b5db584bd97d8eafd963eb4493fe406f278",
    "rules/owner_decisions/URBAN_RULES_1.6.0.json": "a9a04c63044685041d90c06b715b99c2da859aeb997a36f672876fbf57008cd8",
}


@pytest.mark.parametrize("rel,sha", sorted(PINNED.items()))
def test_a23_frozen_files_byte_identical(rel, sha):
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha


def test_a23_new_module_wired_nowhere():
    users = [p.relative_to(ROOT).as_posix() for d in ("engine", "tools") for p in (ROOT / d).rglob("*.py")
             if "stair_finish_levels_v1" in p.read_text(encoding="utf-8", errors="ignore") and p != MOD]
    assert users == []
    assert M.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"


def test_rule_record_new_version_only():
    d = json.loads((ROOT / "rules/owner_decisions/URBAN_RULES_1.7.0.json").read_text(encoding="utf-8"))
    assert d["version"] == "1.7.0" and d["base"]["version"] == "1.6.0"
    (r,) = d["records"]
    assert r["rule_id"] == M.RULE_ID and r["status"] == "OWNER_APPROVED"
    assert {p["id"] for p in r["open_points"]} == {"S-4", "S-5", "S-6", "S-7", "S-8", "S-9"}
    assert MARBLE["material"] == "MARBLE"
