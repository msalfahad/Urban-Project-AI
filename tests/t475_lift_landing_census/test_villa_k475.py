"""T-475 hand villa K475 (not Alsenan): a lift with landings GF / 1F / 2F and a closed roof. GF and 2F have a printed
surround detail (bands + door height), 1F has none -> HELD. 2F landing is only 0.40 deep -> the 0.50 owner threshold
depth does not fit -> HELD. Hand figures (metres):

  GF  W 0.90, detail L = T = R = 0.30, h 2.10: 2.10 x 0.60 + 0.30 x 1.50 = 1.710 m2; threshold 0.90 x 0.50 = 0.450
  1F  W 0.90, no detail, faces 0.80 / 0.60, storey 3.60: HELD 0.50 x 1.90 = 0.950 .. 3.10 x 1.00 + 0.950 = 4.050;
      threshold 0.450 (landing 1.20 deep)
  2F  W 0.90, detail 0.25 bands, h 2.10: 2.10 x 0.50 + 0.25 x 1.40 = 1.400; threshold HELD 0 .. 0.90 x 0.40 = 0.360
  surround valued 3.110, family bound 4.060 .. 7.160; threshold valued 0.900, bound 0.900 .. 1.260; edges 2.700 lm
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t475"))
import lift_landing_census_v1 as C  # noqa: E402

LM = C.LM
DET = "landing door elevation, sheet K475-A12"


def _floors():
    return [
        {"floor": "GF", "state": C.LANDING, "evidence": "jamb pair 0.90", "openings": [{"w": 0.90}]},
        {"floor": "1F", "state": C.LANDING, "evidence": "jamb pair 0.90", "openings": [{"w": 0.90}]},
        {"floor": "2F", "state": C.LANDING, "evidence": "jamb pair 0.90", "openings": [{"w": 0.90}]},
        {"floor": "ROOF", "state": C.NO_LANDING, "evidence": "roof slab closes the shaft", "openings": []},
    ]


SPEC = {
    "GF": dict(detail={"left": 0.30, "top": 0.30, "right": 0.30, "clear_height_m": 2.10, "source": DET},
               faces={"left": 0.80, "right": 0.60}, storey=4.00, depth=None, ffl="+0.60"),
    "1F": dict(detail=None, faces={"left": 0.80, "right": 0.60}, storey=3.60, depth=1.20, ffl="+4.60"),
    "2F": dict(detail={"left": 0.25, "top": 0.25, "right": 0.25, "clear_height_m": 2.10, "source": DET},
               faces={"left": 0.80, "right": 0.60}, storey=3.60, depth=0.40, ffl="+8.20"),
}


def _station(floor, w=0.90, spec=None):
    sp = spec or SPEC[floor]
    sid = f"ELV-01-{floor}"
    sur = C.surround_from_detail(sid, clear_width_m=w, detail=sp["detail"], faces=sp["faces"],
                                 storey_height_m=sp["storey"])
    thr = LM.threshold(sid, clear_width_m=w, default_depth_m=0.50, depth_source=LM.THRESHOLD_SOURCE, wall_band_m=0.20)
    thr = C.threshold_fit(sid, thr, sp["depth"], "printed" if sp["depth"] else None)
    return {"station_id": sid, "surround": sur, "threshold": thr, "level": C.level_relation(sp["ffl"])}


def _all():
    return [_station(f) for f in ("GF", "1F", "2F")]


def test_census_three_landings_roof_closed():
    cen = C.census(_floors())
    assert cen["stations"] == ["ELV-01-GF", "ELV-01-1F", "ELV-01-2F"]
    assert cen["station_count"] == 3 and cen["status"] == LM.DRAWING
    assert cen["floors"][-1]["state"] == C.NO_LANDING


def test_hand_figures_per_station():
    gf, f1, f2 = _all()
    assert gf["surround"]["area_m2"] == pytest.approx(1.710, abs=5e-4)
    assert gf["surround"]["status"] == LM.DRAWING
    assert f1["surround"]["area_m2"] is None and f1["surround"]["status"] == LM.HELD
    assert f1["surround"]["bound_m2"] == pytest.approx([0.950, 4.050], abs=5e-4)
    assert f2["surround"]["area_m2"] == pytest.approx(1.400, abs=5e-4)
    assert gf["threshold"]["area_m2"] == pytest.approx(0.450) and f1["threshold"]["area_m2"] == pytest.approx(0.450)
    assert f2["threshold"]["area_m2"] is None and f2["threshold"]["status"] == LM.HELD
    assert f2["threshold"]["bound_m2"] == pytest.approx([0.0, 0.360])
    assert "INFEASIBLE_DEPTH" in f2["threshold"]["missing"][0]
    assert gf["threshold"]["landing_depth"]["status"] == "NOT_LIMITING"


def test_family_totals_held_never_zero():
    t = C.family_totals(_all())
    assert t["surround"]["value"] is None
    assert t["surround"]["bound"] == pytest.approx([4.060, 7.160], abs=5e-4)
    assert t["surround_valued_part_m2"] == pytest.approx(3.110, abs=5e-4)
    assert t["threshold"]["value"] is None
    assert t["threshold"]["bound"] == pytest.approx([0.900, 1.260], abs=5e-4)
    assert t["threshold_valued_part_m2"] == pytest.approx(0.900)
    assert t["front_edge_lm"] == pytest.approx(2.700)


def test_mirror_swaps_faces_same_quantities():
    for f in ("GF", "1F", "2F"):
        sp = dict(SPEC[f])
        sp["faces"] = {"left": SPEC[f]["faces"]["right"], "right": SPEC[f]["faces"]["left"]}
        a, b = _station(f), _station(f, spec=sp)
        assert a["surround"]["area_m2"] == b["surround"]["area_m2"]
        assert a["surround"]["bound_m2"] == b["surround"]["bound_m2"]
        assert a["threshold"]["area_m2"] == b["threshold"]["area_m2"]


def _faces_from_points(j_left, j_right, c_left, c_right):
    d = lambda p, q: math.hypot(p[0] - q[0], p[1] - q[1])  # noqa: E731
    return {"left": round(d(j_left, c_left), 6), "right": round(d(j_right, c_right), 6), "w": round(d(j_left, j_right), 6)}


@pytest.mark.parametrize("deg", [0, 90, 37, 180])
def test_rotation_invariant(deg):
    a = math.radians(deg)
    rot = lambda p: (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))  # noqa: E731
    pts = [(-0.45, 0.0), (0.45, 0.0), (-1.25, 0.0), (1.05, 0.0)]  # jambs, then the face ends (0.80 / 0.60)
    f = _faces_from_points(*[rot(p) for p in pts])
    assert f == {"left": 0.8, "right": 0.6, "w": 0.9}
    sp = dict(SPEC["1F"], faces={"left": f["left"], "right": f["right"]})
    assert _station("1F", w=f["w"], spec=sp)["surround"]["bound_m2"] == pytest.approx([0.950, 4.050], abs=5e-4)


def test_millimetres_refused():
    with pytest.raises(C.Refused):
        C.surround_from_detail("X", clear_width_m=900, detail=None, faces={"left": 0.8, "right": 0.6})
    with pytest.raises(C.Refused):
        C.threshold_fit("X", LM.threshold("X", clear_width_m=0.9, default_depth_m=0.5,
                                          depth_source=LM.THRESHOLD_SOURCE), 1200)


def test_unknown_floor_held_never_copied():
    fl = _floors()
    fl[1] = {"floor": "1F", "state": C.UNKNOWN, "evidence": "", "openings": []}
    cen = C.census(fl)
    assert cen["status"] == LM.HELD and cen["unknown_floors"] == ["1F"] and cen["station_count"] == 2
    fl[1] = {"floor": "1F", "state": C.UNKNOWN, "evidence": "", "openings": [], "copied_from": "GF"}
    with pytest.raises(C.Refused):
        C.census(fl)


def test_landing_claims_need_evidence():
    fl = _floors()
    fl[3] = {"floor": "ROOF", "state": C.LANDING, "evidence": "", "openings": []}
    with pytest.raises(C.Refused):
        C.census(fl)
    fl[3] = {"floor": "ROOF", "state": C.NO_LANDING, "evidence": "closed", "openings": [{"w": 0.9}]}
    with pytest.raises(C.Refused):
        C.census(fl)
    fl[3] = {"floor": "ROOF", "state": C.NO_LANDING, "evidence": "", "openings": []}
    with pytest.raises(C.Refused):
        C.census(fl)


def test_through_car_two_stations_on_one_floor():
    fl = _floors()
    fl[0]["openings"] = [{"w": 0.9}, {"w": 0.9}]
    cen = C.census(fl)
    assert cen["station_count"] == 4 and cen["stations"][:2] == ["ELV-01-GF-1", "ELV-01-GF-2"]


def test_catalogue_height_refused():
    with pytest.raises(C.Refused):
        C.surround_from_detail("X", clear_width_m=0.9, detail={"left": 0.3, "top": 0.3, "right": 0.3,
                                                               "clear_height_m": 2.10, "source": "typical lift door"},
                               faces={"left": 0.8, "right": 0.6})
    with pytest.raises(C.Refused):
        C.clear_height(2.10, "catalogue value")
    assert C.clear_height(2.10, "supplier shop drawing LD-01") == 2.10


def test_detail_band_wider_than_face_refused():
    with pytest.raises(C.Refused):
        C.surround_from_detail("X", clear_width_m=0.9, detail={"left": 0.3, "top": 0.3, "right": 0.7,
                                                               "clear_height_m": 2.1, "source": DET},
                               faces={"left": 0.8, "right": 0.6})


def test_level_relation():
    assert C.level_relation("+4.60")["relation"] == C.FLUSH
    assert C.level_relation(None)["relation"] == C.UNKNOWN and C.level_relation(None)["status"] == LM.HELD
    assert C.level_relation("+4.60", step_drawn=True)["status"] == LM.HELD


def test_deduction_matrix_lift_opening():
    s = _station("1F")
    m = C.deduction_matrix("ELV-01-1F", clear_width_m=0.90, surround=s["surround"], thr=s["threshold"])
    sk, wf, fl, none = m["rows"]
    assert sk["deduct_lm"] == 0.9 and sk["jamb_skirting_lm"] == 0.0
    assert wf["opening_m2"] is None and wf["opening_status"] == LM.HELD
    assert wf["surround_status"] == LM.HELD and wf["surround_bound_m2"] == pytest.approx([0.950, 4.050], abs=5e-4)
    assert fl["threshold_floor_part_bound_m2"] == pytest.approx([0.270, 0.450])
    assert none["status"] == "NOT_APPLICABLE"


def test_equivalence():
    assert C.equivalent(_all()) is False
    assert C.equivalent([_station("1F"), _station("1F")]) is True
