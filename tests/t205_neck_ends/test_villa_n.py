"""T-205 NECK_ENDS_V1 on the hand fixture Villa N (not Alsenan). Hand truth, worked here:

Villa N chain (printed): FFL +0.90, floor build-up 0.12 -> GF structural slab top +0.78; exterior ground-beam detail:
GB top = ground-floor slab level; ground beams billed NET of the column footprint (neck owns the junction); formation
-1.60 (printed), limit 'not less than 1.20 m below the plot' -> AT_MOST -1.20; under every footing 0.05 screed +
membrane and 0.10 blinding (stack 0.15 + H).

| neck | section | H | footing top = -1.60 + 0.15 + H | length = 0.78 - footing top | volume |
| N1 | 0.25 x 0.60 = 0.150 | 0.40 | -1.05 | 1.83 | 0.27450 |
| N2 | 0.30 x 0.30 = 0.090 | 0.60 | -0.85 | 1.63 | 0.14670 |
| N3 | 0.20 x 0.80 = 0.160 | 0.25 | -1.20 | 1.98 | 0.31680 |
total 0.73800 m3.  GB billed THROUGH the column, depth 0.40: N1 top +0.38, length 1.43, 0.21450 m3.
Formation not printed: N1 what-if length at b = d = 0: 0.90 + 1.20 - 0.55 = 1.55 m, 0.2325 m3, -0.150 per m of build-up.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t205"))
import neck_ends_v1 as N  # noqa: E402

UNDER = {"underlay": 0.05, "blinding": 0.10}
PROJECT = {
    "datums": {"FFL": 0.90, "FORMATION": -1.60},
    "layers": {"FLOOR_BUILD_UP": 0.12},
    "formation_limit": {"bound": "AT_MOST", "value": -1.20},
    "gb_top_relation": "SLAB_TOP",
    "gb_basis": "NET_OF_COLUMN",
}


def _n(i, W, D, H, units="m", **kw):
    return {"id": i, "type": i, "sections": [{"source": "schedule", "W": W, "D": D, "units": units}],
            "footing": dict(UNDER, H=H, **kw)}


NECKS = [_n("N1", 0.25, 0.60, 0.40), _n("N2", 0.30, 0.30, 0.60), _n("N3", 200, 800, 0.25, units="mm")]
HAND = {"N1": (1.83, 0.2745), "N2": (1.63, 0.1467), "N3": (1.98, 0.3168)}


def test_normal_three_necks_mixed_footing_depths():
    tot = 0.0
    for s in NECKS:
        r = N.neck(s, PROJECT)
        L, V = HAND[s["id"]]
        assert r["status"] == "DRAWING-CONFIRMED" and r["codes"] == []
        assert r["top"]["kind"] == "GB_TOP" and r["top"]["value_m"] == pytest.approx(0.78)
        assert r["length_m"] == pytest.approx(L) and r["volume_m3"] == pytest.approx(V)
        tot += r["volume_m3"]
    assert tot == pytest.approx(0.738)


def test_units_cm_and_mm_and_turned_section_agree():
    a = N.neck(_n("N1", 25, 60, 0.40, units="cm"), PROJECT)
    b = N.neck(_n("N1", 600, 250, 0.40, units="mm"), PROJECT)        # W / D swapped = the column turned 90 deg
    assert a["volume_m3"] == pytest.approx(0.2745) and b["volume_m3"] == pytest.approx(0.2745)
    with pytest.raises(ValueError, match="UNIT_UNKNOWN"):
        N.neck(_n("N1", 25, 60, 0.40, units="inch"), PROJECT)


def test_adverse_ffl_as_neck_top_is_refused():
    p = dict(PROJECT, neck_top_kind="FFL")
    r = N.neck(NECKS[0], p)
    assert r["status"] == "REFUSED" and "FINISHED_AS_STRUCTURAL" in r["codes"]
    assert r["volume_m3"] is None and r["length_m"] is None


def test_adverse_missing_founding_level_is_held_never_zero():
    p = copy.deepcopy(PROJECT)
    p["datums"].pop("FORMATION")
    r = N.neck(NECKS[0], p)
    assert r["status"] == "HELD" and "FORMATION_NOT_PRINTED" in r["codes"]
    assert r["volume_m3"] is None and r["length_m"] is None
    assert r["bottom"]["stack_m"] == pytest.approx(0.55) and r["bottom"]["limit_m"] == pytest.approx(-1.20)
    w = r["what_if"]
    assert w["label"].startswith("WHAT_IF") and w["length_at_b0_d0_m"] == pytest.approx(1.55)
    assert w["const_m3"][0] == pytest.approx(0.2325) and w["per_m_build_up_m3"][0] == pytest.approx(-0.15)
    assert w["per_m_below_limit_m3"][0] == pytest.approx(0.15)


def test_adverse_formation_above_the_printed_limit_is_violated_not_adjusted():
    p = copy.deepcopy(PROJECT)
    p["datums"]["FORMATION"] = -1.10
    r = N.neck(NECKS[0], p)
    assert r["status"] == "HELD" and "FORMATION_LIMIT_VIOLATED" in r["codes"] and r["volume_m3"] is None


def test_adverse_slab_top_not_printed_holds_the_top():
    p = copy.deepcopy(PROJECT)
    p["layers"]["FLOOR_BUILD_UP"] = None
    r = N.neck(NECKS[0], p)
    assert r["status"] == "HELD" and "LEVEL_NOT_PRINTED" in r["codes"] and r["top"]["value_m"] is None


def test_ground_beam_billed_through_the_column_moves_the_top_to_its_soffit():
    p = dict(PROJECT, gb_basis="THROUGH_COLUMN")
    s = dict(NECKS[0], gb_depth=0.40)
    r = N.neck(s, p)
    assert r["top"]["kind"] == "GB_BOTTOM" and r["top"]["value_m"] == pytest.approx(0.38)
    assert r["length_m"] == pytest.approx(1.43) and r["volume_m3"] == pytest.approx(0.2145)
    r2 = N.neck(NECKS[0], p)                                          # depth not printed at this neck
    assert r2["status"] == "HELD" and r2["volume_m3"] is None
    r3 = N.neck(NECKS[0], dict(PROJECT, gb_basis=None))
    assert "OWNER_UNDEFINED" in r3["codes"] and r3["volume_m3"] is None


def test_section_conflict_is_a_range_and_held_drawn_outline_is_only_a_note():
    s = copy.deepcopy(NECKS[0])
    s["sections"].append({"source": "column plan text", "W": 0.25, "D": 0.50})
    r = N.neck(s, PROJECT)
    assert r["status"] == "HELD" and "SECTION_CONFLICT" in r["codes"]
    assert r["section"]["range_m2"] == pytest.approx((0.125, 0.15))
    assert r["volume_range_m3"] == pytest.approx((0.22875, 0.2745))
    s2 = copy.deepcopy(NECKS[0])
    s2["sections"].append({"source": "drawn outline", "W": 0.25, "D": 0.40, "printed": False})
    r2 = N.neck(s2, PROJECT)
    assert r2["status"] == "DRAWING-CONFIRMED" and r2["volume_m3"] == pytest.approx(0.2745)
    assert r2["section"]["notes"] and r2["section"]["notes"][0]["source"] == "drawn outline"


def test_lift_pit_raft_and_footing_conflict_are_held():
    r = N.neck(_n("L1", 0.20, 0.50, 0.55, pit_raft=True, pit_depth=None), PROJECT)
    assert r["status"] == "HELD" and "PIT_DEPTH_NOT_PRINTED" in r["codes"]
    s = {"id": "X", "sections": [{"source": "schedule", "W": 0.3, "D": 0.7}],
         "footing": {"type": "F10|F", "H": None, "conflict": "one outline, two labels"}}
    r2 = N.neck(s, PROJECT)
    assert "FOOTING_CONFLICT" in r2["codes"] and r2["volume_m3"] is None


def test_neck_top_and_column_bottom_must_be_one_datum():
    assert N.stack_check("GB_TOP", 0.78, "GB_TOP", 0.78, 0.10)["code"] == "PASS"
    g = N.stack_check("GB_TOP", 0.78, "FFL", 0.90, 0.10)             # column line starts at the FFL
    assert g["code"] == "GAP" and g["volume_m3"] == pytest.approx(0.012)
    d = N.stack_check("GB_TOP", 0.78, "GB_BOTTOM", 0.38, 0.10)
    assert d["code"] == "DOUBLE" and d["volume_m3"] == pytest.approx(0.04)
    assert N.stack_check("GB_TOP", None, "FFL", 0.90, 0.10)["code"] == "HELD"


def test_reconcile_freelancer_to_engine_exactly_and_names_the_residual():
    fl = {"A": {"n": 3, "W": 0.3, "D": 0.5, "h": 1.2},                 # one more than released: engine holds it
          "B": {"n": 1, "W": 0.4, "D": 0.6, "h": 1.2},                 # wrong section, one omitted
          "Z": {"n": 1, "W": 0.3, "D": 0.3, "h": 1.2}}                 # not drawn at all
    census = {"A": {"area_m2": 0.15, "drawn": 3, "held": 1}, "B": {"area_m2": 0.18, "drawn": 2, "held": 0}}
    rel = [{"type": "A", "area_m2": 0.15, "length_m": 1.8}, {"type": "A", "area_m2": 0.15, "length_m": 1.6},
           {"type": "B", "area_m2": 0.18, "length_m": 1.7}, {"type": "B", "area_m2": 0.18, "length_m": 1.7}]
    r = N.reconcile(fl, census, rel)
    # hand: F = 3*.15*1.2 + .24*1.2 + .09*1.2 = 0.54 + 0.288 + 0.108 = 0.936; R = .27 + .24 + .612 = 1.122
    assert r["freelancer_m3"] == pytest.approx(0.936) and r["released_m3"] == pytest.approx(1.122)
    t = r["totals_m3"]
    assert t["scope_engine_held"] == pytest.approx(-0.18)             # 1 x 0.15 x 1.2
    assert t["section"] == pytest.approx(-0.072)                      # 1 x (0.18 - 0.24) x 1.2
    assert t["count"] == pytest.approx(0.216)                         # 1 x 0.18 x 1.2
    assert t["height"] == pytest.approx(0.33)                         # .15(.6+.4) + .18(.5+.5)
    assert t["scope_not_drawn"] == pytest.approx(-0.108)             # Z: priced, never drawn (census 0)
    assert r["residual_m3"] == pytest.approx(0.0, abs=1e-9)
    # adverse: the same priced Z with a census that does not list it is still caught as not drawn, never absorbed
    # into the height step; a census that wrongly lists Z as drawn and released-free leaves it as a named residual
    census2 = dict(census, Z={"area_m2": 0.09, "drawn": 1, "held": 0})
    r2 = N.reconcile(fl, census2, rel)
    assert r2["totals_m3"]["scope_not_drawn"] == 0 and r2["residual_m3"] == pytest.approx(-0.108)
