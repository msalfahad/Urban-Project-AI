"""T-269 floor-area blockers on hand-calculated fixtures that are NOT the Alsenan villa (any villa), plus the Alsenan
summary guard (and its rebuild when the private drawings are given).

Hand calculations (m, m2):
ARRIVING FLIGHT (upper floor of a dog-leg; flight 1.00 wide along y, arriving toward smaller y at a landing whose printed
edge is y = 3.76; the plan draws 8 risers y 6.00, 5.72, ..., 4.04 (going 0.28) and their nosings 0.04 beyond each
riser toward the flight's start (6.04 ... 4.08); the section counts 9 risers):
    top riser = 6.00 - (9 - 1) x 0.28 = 3.76 (on the printed landing edge)
    undrawn strip = 4.08 - 3.76 = 0.32 x 1.00 = 0.32
    9th riser's tread seen between nosings 4.08 and 3.80 ......................... 0.28  (stair, not floor)
    landing nosing band 3.80 .. 3.76 ............................................. 0.04  (floor of the landing)
    adverse: no section count -> HELD; 10 risers -> top riser 3.48, 0.28 beyond the landing edge -> HELD (conflict);
    unequal drawn goings -> HELD; no drawn nosings -> band HELD (tread 0.28 shown)
L-SHAPED HALL with a stair opening (0..8 x 0..6 less 5..8 x 3..6 = 39.00): an arriving flight x 1.00 .. 2.20,
y 0 .. 2.00 with a 0.05 band x 2.20 .. 2.25, y 0 .. 2.00 (0.10):
    structural slab edge along x = 2.20 (the flight side) -> the band stands on the slab: floor 0.10
    slab edge along x = 2.25 (its outer face) -> the band is in the opening: 0.00
    no structural edge, edges on both faces, or an upstand printed -> HELD
LOWEST STOREY, same L-shaped hall: flight A below the cut 1.00 x 2.00 (x 0 .. 1, y 0 .. 2) = 2.00; flight B overhead
1.00 x 1.50 (x 1 .. 2, y 0 .. 1.5) = 1.50; flight C overhead 1.00 x 1.00 (x 3 .. 4, y 0 .. 1) = 1.00 with a wall line
drawn under it; flight D overhead over B's last 0.50 (x 1 .. 2, y 1 .. 2) = 1.00 of which 0.50 is new:
    floor under overhead treads = B 1.50 + D 0.50 = 2.00; HELD = A 2.00 + C 1.00 = 3.00; tread union 5.00
PANTRY PIECE x 5 .. 8, y 0 .. 3 (9.00) next to the flights: treads inside 0.000 (no tread rule applies)
Every geometric fixture also mirrored, rotated 37 deg and translated."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t269"))

import floor_blockers as FB  # noqa: E402

TOL = 1e-6
R = [6.00 - 0.28 * i for i in range(8)]
N = [r + 0.04 for r in R]


def _foot(**kw):
    args = dict(first_riser=6.00, drawn_risers=R, drawn_nosings=N, governing_risers=9, landing_edge=3.76, width=1.0)
    args.update(kw)
    return FB.arriving_flight_foot(**args)


# ------------------------------------------------------------------------------------------- arriving flight foot
def test_foot_normal_split():
    r = _foot()
    assert r["status"] == "DERIVED"
    assert abs(r["strip_m2"] - 0.32) < TOL and abs(r["tread_m2"] - 0.28) < TOL and abs(r["landing_band_m2"] - 0.04) < TOL
    assert r["missing_risers"] == 1 and abs(r["nosing_m"] - 0.04) < TOL


def test_foot_mirrored_direction_same_areas():
    r = _foot(first_riser=-6.00, drawn_risers=[-x for x in R], drawn_nosings=[-x for x in N], landing_edge=-3.76)
    assert r["status"] == "DERIVED"
    assert abs(r["tread_m2"] - 0.28) < TOL and abs(r["landing_band_m2"] - 0.04) < TOL


def test_foot_translated_and_wider():
    d = 123.45
    r = _foot(first_riser=6.00 + d, drawn_risers=[x + d for x in R], drawn_nosings=[x + d for x in N],
              landing_edge=3.76 + d, width=1.20)
    assert abs(r["tread_m2"] - 0.336) < 1e-5 and abs(r["landing_band_m2"] - 0.048) < 1e-5


def test_foot_no_section_count_held_never_zero():
    r = _foot(governing_risers=None)
    assert r["status"] == "HELD" and "tread_m2" not in r and "landing_band_m2" not in r


def test_foot_top_riser_beyond_landing_edge_refused():
    r = _foot(governing_risers=10)
    assert r["status"] == "HELD" and "design conflict" in r["reason"] and abs(r["overshoot_m"] - 0.28) < 1e-4


def test_foot_unequal_goings_held():
    rs = list(R)
    rs[3] += 0.02
    assert _foot(drawn_risers=rs)["status"] == "HELD"


def test_foot_no_nosings_band_held_tread_shown():
    r = _foot(drawn_nosings=[])
    assert r["status"] == "HELD" and abs(r["tread_m2"] - 0.28) < TOL and "landing_band_m2" not in r


def test_foot_plan_count_is_not_the_governing_count():
    # the plan's own 8 risers: everything beyond the last drawn nosing would read as landing (the D-13 error)
    r = _foot(governing_risers=8)
    assert r["status"] == "DERIVED" and r["tread_m2"] == 0.0 and abs(r["landing_band_m2"] - 0.32) < TOL
    assert abs(_foot()["landing_band_m2"] - r["landing_band_m2"]) > 0.25  # the count decides, never the plan lines


# ------------------------------------------------------------------------------------------- side band
HALL = Polygon([(0, 0), (8, 0), (8, 3), (5, 3), (5, 6), (0, 6)])
FLIGHT = FB.rect(1.00, 0.0, 2.20, 2.00)
BAND = FB.rect(2.20, 0.0, 2.25, 2.00)
EDGE_IN = LineString([(2.20, 0.0), (2.20, 2.00)])
EDGE_OUT = LineString([(2.25, 0.0), (2.25, 2.00)])


def _frames():
    yield lambda g: g
    yield lambda g: affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))
    yield lambda g: affinity.translate(affinity.rotate(g, 37, origin=(0, 0)), 1000.0, -250.0)
    yield lambda g: affinity.rotate(affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0)), -90, origin=(0, 0))


@pytest.mark.parametrize("k", range(4))
def test_band_on_slab_is_floor(k):
    t = list(_frames())[k]
    r = FB.side_band_floor(t(BAND), t(FLIGHT), [t(EDGE_IN)])
    assert r["status"] == "ON_SLAB" and abs(r["floor_m2"] - 0.10) < 1e-9


@pytest.mark.parametrize("k", range(4))
def test_band_in_opening_is_not_floor(k):
    t = list(_frames())[k]
    r = FB.side_band_floor(t(BAND), t(FLIGHT), [t(EDGE_OUT)])
    assert r["status"] == "IN_OPENING" and r["floor_m2"] == 0.0


def test_band_adverse_held():
    assert FB.side_band_floor(BAND, FLIGHT, [])["status"] == "HELD"
    assert FB.side_band_floor(BAND, FLIGHT, [EDGE_IN, EDGE_OUT])["status"] == "HELD"
    assert FB.side_band_floor(BAND, FLIGHT, [EDGE_IN], upstand_printed=True)["status"] == "HELD"
    away = FB.rect(3.0, 0.0, 3.05, 2.0)  # a band not beside the flight
    assert FB.side_band_floor(away, FLIGHT, [EDGE_IN])["status"] == "HELD"
    for r in (FB.side_band_floor(BAND, FLIGHT, []),):
        assert "floor_m2" not in r  # held never becomes 0


# ------------------------------------------------------------------------------------------- lowest storey
def _flights(t):
    return [
        {"id": "A", "quads": [t(FB.rect(0, 0, 1, 1)), t(FB.rect(0, 1, 1, 2))], "drawn_overhead": False},
        {"id": "B", "quads": [t(FB.rect(1, 0, 2, 1.5))], "drawn_overhead": True},
        {"id": "C", "quads": [t(FB.rect(3, 0, 4, 1))], "drawn_overhead": True},
        {"id": "D", "quads": [t(FB.rect(1, 1, 2, 2))], "drawn_overhead": True},
    ]


@pytest.mark.parametrize("k", range(4))
def test_lowest_storey_overhead_floor_below_cut_held(k):
    t = list(_frames())[k]
    wall = t(LineString([(3.2, 0.2), (3.8, 0.2)]).buffer(0.002))
    r = FB.floor_under_rising_stair(t(HALL), _flights(t), closed_under=[wall])
    assert abs(r["treads_m2"] - 5.00) < 1e-6
    assert abs(r["floor_m2"] - 2.00) < 1e-6 and abs(r["held_m2"] - 3.00) < 1e-6
    st = {x["flight"]: x["status"] for x in r["rows"]}
    assert st == {"A": "HELD", "B": "FLOOR_UNDER_OVERHEAD", "C": "HELD", "D": "FLOOR_UNDER_OVERHEAD"}


def test_lowest_storey_adverse():
    t = lambda g: g  # noqa: E731
    fl = _flights(t) + [{"id": "E", "quads": [], "drawn_overhead": True},
                        {"id": "F", "quads": [FB.rect(6, 0, 7, 1)], "drawn_overhead": None}]
    r = FB.floor_under_rising_stair(HALL, fl)
    st = {x["flight"]: x["status"] for x in r["rows"]}
    assert st["E"] == "HELD" and st["F"] == "HELD"  # no outline / no cut drawn: held, never floor, never 0
    assert "floor_m2" not in [x for x in r["rows"] if x["flight"] == "E"][0]
    # with no closed element drawn under C, it is floor (nothing occupies the floor under an overhead flight)
    assert abs(r["floor_m2"] - 3.00) < 1e-6


def test_treads_in_pantry_piece():
    quads = [q for f in _flights(lambda g: g) for q in f["quads"]]
    assert FB.treads_in_piece(FB.rect(5, 0, 8, 3), quads) == 0.0
    assert abs(FB.treads_in_piece(FB.rect(0, 0, 1.5, 1), quads) - 1.5) < 1e-9
    assert FB.treads_in_piece(None, quads) is None


# ------------------------------------------------------------------------------------------- Alsenan summary
SUMMARY = ROOT / "research" / "agents_t269" / "summary_t269.json"


def _numbers(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _numbers(v)
    elif isinstance(o, list):
        for v in o:
            yield from _numbers(v)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        yield o


def test_alsenan_summary_values_and_no_coordinates():
    d = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert all(abs(x) < 1000 for x in _numbers(d))  # areas / lengths only: no drawing coordinate is stored
    f = d["d13_foot_strip_1f"]
    assert f["status"] == "DERIVED" and f["tread_m2"] == 0.345 and f["landing_band_m2"] == 0.0575
    assert f["landing_edge_to_top_riser_m"] == 0.0 and f["drawn_risers"] == 11
    assert d["st_corroboration"]["st_east_riser_lines"] == 12 and d["st_corroboration"]["st_east_goings_m"] == [0.3]
    assert d["d23_side_band_1f"]["status"] == "ON_SLAB" and d["d23_side_band_1f"]["floor_m2"] == 0.1175
    g = d["gf_pantry_and_round_stair"]
    assert g["RC99C2A"]["treads_in_pantry_part_m2"] == 0.0 and g["RC06FED"]["treads_in_piece_m2"] == 0.0
    assert abs(g["RC99C2A"]["treads_in_face_m2"] - 8.194412) < 1e-6
    assert abs(g["RC99C2A"]["floor_under_overhead_m2"] - 2.07) < 1e-6
    assert abs(g["RC99C2A"]["held_below_cut_m2"] - 6.124412) < 1e-6


@pytest.mark.skipif(not all(os.environ.get(k) for k in ("URBAN_P7757_DXF", "URBAN_ST7757_DXF", "URBAN_V29_PKL")),
                    reason="private drawings not given (URBAN_P7757_DXF, URBAN_ST7757_DXF, URBAN_V29_PKL)")
def test_alsenan_rebuild_equals_summary(tmp_path):
    subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t269" / "alsenan_t269.py"),
                    "--arch", os.environ["URBAN_P7757_DXF"], "--st", os.environ["URBAN_ST7757_DXF"],
                    "--v29", os.environ["URBAN_V29_PKL"], "--out", str(tmp_path)], check=True, capture_output=True)
    a = json.loads((tmp_path / "summary_t269.json").read_text(encoding="utf-8"))
    b = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert a == b
