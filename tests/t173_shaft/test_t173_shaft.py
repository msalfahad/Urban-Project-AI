"""T-173: stair-shaft wall faces from the actual exposed geometry (ERS s.2-4; any villa).

Synthetic 'Villa R' (not the development villa), metres unless stated. One shaft face 4.00 m long, storeys
0.00 / 3.00 / 6.00, roof slab top +9.00, slab 0.15, so the face runs 0.00 -> 8.85 (roof soffit) when nothing
crosses the shaft. Hand calculations:
  gross 4.00 x 8.85 = 35.400 m2
  landing band u 0..1.00 at +1.50, t 0.15: 1.00 x 0.15 = 0.150 m2
  window u 1.50..2.50, +4.00..+5.50: 1.00 x 1.50 = 1.500 m2           -> net 35.400 - 0.150 - 1.500 = 33.750 m2
  flight 3 risers 0.50, goings 0.50 (45 deg), waist 0.20, on grade, profile to the last riser:
    top: 0.5 on (0, 0.5), 1.0 on (0.5, 1.0) -> 0.750; soffit s - 0.2 x sqrt(2) = s - 0.282843, above 0 from s = 0.282843:
    integral (1 - 0.282843)^2 / 2 = 0.257157 -> profile 0.750 - 0.257157 = 0.492843 m2
  ADVERSE (shaft closed by a slab at +3.00 over the whole section): the face is NOT continuous; correct
    35.400 - 4.00 x 0.15 = 34.800 m2; the continuous shortcut 35.400 overstates by 0.600 m2 and continuity_check names
    the slab.
  ADVERSE (open side): a void side with no wall is not a face: a 2 x (2.00 + 4.00) box x 8.85 = 106.20 m2 against
    the drawn three walls (2.00 + 4.00 + 4.00) x 8.85 = 88.50 m2 (the box adds 17.70 m2 of wall that does not exist).
  Owner manual (room formula as written, 3.00 - 0.85 = 2.15 per storey): 4.00 x 2.15 x 3 = 25.80 m2, kept beside.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_P = ROOT / "research" / "agents_t173"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _P / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return sys.modules[name]


S = _load("t173_shaft")
A = _load("t173_alsenan")

TOP = 9.00 - 0.15
FLIGHT = dict(u_first=2.0, direction=1, z0=0.0, risers=3, riser=0.5, going=0.5, waist=0.2, t_start=0.0, t_end=0.15,
              extend_end=False)


def face(**kw):
    f = {"id": "R", "region": [[0.0, 4.0, 0.0, TOP]], "contacts": [], "openings": []}
    f.update(kw)
    return f


def test_gross_band_and_window_normal():
    f = face(contacts=[{"id": "landing", "band": {"u": [0.0, 1.0], "level": 1.50, "t": 0.15}}],
             openings=[{"id": "win", "status": "PRINTED", "rect": [1.5, 2.5, 4.0, 5.5]}])
    r = S.measure_face(f, storeys=[3.0, 6.0])
    assert r["gross"] == pytest.approx(35.40, abs=1e-9)
    assert r["contacts_known"] == pytest.approx(0.15, abs=1e-9)
    assert r["openings_known"] == pytest.approx(1.50, abs=1e-9)
    assert r["net_hi"] == pytest.approx(33.75, abs=1e-9) == r["net_lo"]
    assert [round(s["gross"], 6) for s in r["storeys"]] == [12.0, 12.0, 11.4]


def test_flight_profile_hand_value_and_mirror():
    p = S.flight_profile(**FLIGHT)
    assert p.area == pytest.approx(0.492843, abs=1e-6)
    m = S.flight_profile(**(FLIGHT | {"direction": -1}))
    assert m.area == pytest.approx(p.area, abs=1e-12)
    assert m.bounds[2] == pytest.approx(2.0) and p.bounds[0] == pytest.approx(2.0)   # mirrored about the first riser


def test_rotation_invariance_by_face_frame():
    # the same face measured from the other end (u -> L - u) gives the same areas
    f1 = face(contacts=[{"id": "fl", "flight": FLIGHT}])
    f2 = face(contacts=[{"id": "fl", "flight": FLIGHT | {"u_first": 2.0, "direction": -1}}])
    assert S.measure_face(f1)["net_hi"] == pytest.approx(S.measure_face(f2)["net_hi"], abs=1e-12)


def test_window_crossing_a_flight_is_deducted_once():
    win = {"id": "win", "status": "PRINTED", "rect": [2.0, 3.0, 0.5, 1.5]}
    fl = {"id": "fl", "flight": FLIGHT}
    r = S.measure_face(face(contacts=[fl], openings=[win]))
    both = S.flight_profile(**FLIGHT).union(S.rect(2.0, 3.0, 0.5, 1.5)).area
    assert r["gross"] - r["net_hi"] == pytest.approx(both, abs=1e-9)
    # the naive sum would deduct the overlap twice
    assert r["contacts_known"] + r["openings_known"] < 1.0 + S.flight_profile(**FLIGHT).area


def test_adverse_shaft_closed_by_a_slab():
    slab = {"id": "slab +3.00", "band": {"u": [0.0, 4.0], "level": 3.0, "t": 0.15}, "spans_full_section": True, "level": 3.0}
    continuous_wrong = S.measure_face(face())["net_hi"]
    right = S.measure_face(face(contacts=[slab]))["net_hi"]
    assert continuous_wrong == pytest.approx(35.40)
    assert right == pytest.approx(34.80, abs=1e-9)
    assert S.continuity_check([slab], 0.0, TOP) == [slab]
    assert S.continuity_check([slab | {"spans_full_section": False}], 0.0, TOP) == []


def test_adverse_open_side_is_not_a_wall():
    three = [face(id="N", region=[[0, 2.0, 0, TOP]]), face(id="W"), face(id="E")]
    assert S.measure_shaft(three)["total"]["gross"] == pytest.approx(88.50, abs=1e-9)
    box_perimeter = 2 * (2.0 + 4.0) * TOP
    assert box_perimeter - 88.50 == pytest.approx(17.70, abs=1e-9)


def test_held_opening_and_held_contact_are_ranges_never_zero():
    f = face(contacts=[{"id": "winders", "status": "HELD", "rect": [0.0, 1.0, 1.0, 2.0]}],
             openings=[{"id": "w?", "status": "HELD", "rect": [1.5, 2.5, 3.0, 6.0]}])
    r = S.measure_face(f)
    assert r["net_hi"] == pytest.approx(35.40)
    assert r["net_lo"] == pytest.approx(35.40 - 1.0 - 3.0)
    with pytest.raises(S.ShaftInputError):
        S.flight_profile(**(FLIGHT | {"riser": None}))
    with pytest.raises(S.ShaftInputError):
        S.measure_face(face(openings=[{"id": "x", "rect": [0, 1, 0, 1]}]))      # no status: refused
    with pytest.raises(S.ShaftInputError):
        S.owner_manual_gross({"GF": 4.0}, {"GF": None})


def test_units_mm_and_refused_unit():
    assert S.to_m(4000, "mm") == pytest.approx(4.0)
    assert S.to_m(885, "cm") == pytest.approx(8.85)
    with pytest.raises(S.ShaftInputError):
        S.to_m(13, "ft")
    with pytest.raises(S.ShaftInputError):
        S.to_m(None, "m")


def test_owner_manual_column_kept_beside():
    o = S.owner_manual_gross({"GF": 4.0, "1F": 4.0, "2F": 4.0}, {"GF": 2.15, "1F": 2.15, "2F": 2.15})
    assert o["total"] == pytest.approx(25.80)


def test_pier_return_uses_exposed_height():
    f = face(returns=[{"u": 0.5, "depth": 0.05}],
             contacts=[{"id": "landing", "band": {"u": [0.0, 1.0], "level": 1.50, "t": 0.15}}])
    r = S.measure_face(f)
    assert r["returns_hi"] == pytest.approx(0.05 * (TOP - 0.15), abs=1e-9)


# ---------------------------------------------------------------- development-villa run (input JSON in the repo)

def test_alsenan_reconciles_to_owner_and_storey_interval():
    res = A.run()
    hi = res["cases"]["HI"]["plaster"]["total"]
    gf, f1, f2 = (s["gross"] for s in hi["storeys"])
    # owner -> drawing-derived, storey by storey (gross; pier returns are added to the net, 0.10 m of face)
    assert gf - 55.115 == pytest.approx(15.10 * 0.85 - 0.40 + 3.675 - 0.10 * 4.50, abs=0.005)
    assert f1 - 43.55 == pytest.approx(13.00 * 0.85 - 0.10 * 4.20, abs=0.005)
    assert f2 - 43.55 == pytest.approx(13.00 * (4.04 - 3.35) - 0.10 * 4.04, abs=0.005)
    assert res["owner_manual"]["total"] == pytest.approx(142.22, abs=0.005)
    # GF storey interval shortcut of T-128 r2 is 15.10 x 4.50
    assert res["storey_interval_gf_1f"]["per_storey"]["GF"] == pytest.approx(67.95)


def test_alsenan_freelancer_box_closes():
    res = A.run()
    faces = {f["id"][0]: f for f in res["cases"]["HI"]["plaster"]["faces"]}
    mine = sum(f["gross"] for f in faces.values())
    his = 14.80 * 12.90 + 2.50 * 5.40
    n = 2.40 * 12.90 - faces["N"]["gross"]
    we = 2 * 5.00 * 12.90 - (faces["W"]["gross"] + faces["E"]["gross"])
    s = 2.40 * 12.90 - faces["S"]["gross"]           # above the GF there is no south wall: open arrival landings
    assert his - mine == pytest.approx(n + we + s + 13.50, abs=1e-9)
    assert s == pytest.approx(30.96 - 10.85, abs=0.005)


def test_alsenan_held_items_are_ranges_and_known_values():
    res = A.run()
    hi, lo = res["cases"]["HI"]["paint"]["total"], res["cases"]["LO"]["paint"]["total"]
    assert lo["net_lo"] < lo["net_hi"] <= hi["net_hi"]
    assert hi["net_lo"] > 0
    assert round(hi["net_hi"], 2) == 159.03 and round(lo["net_lo"], 2) == 135.26
