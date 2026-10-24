"""T-262 part 2: the engine's room of each opening crosswalked by area to the reference rooms (engine_rooms_t262.py), on
a hand-built fixture that is NOT the development villa, plus the committed development-villa result. Hand calculation:

  Reference rooms R1 = [0, 4] x [0, 3] (12.00 m2), R2 = [4.15, 8] x [0, 3] (11.55 m2), R3 = [0, 4] x [3.15, 6] (11.40).
  Engine room E1 = R1 exactly (share 1.000 / 1.000) -> R1; E2 = [4.15, 8] x [0, 3] -> R2; E13 = R1 + R3 drawn as one
  open face [0, 4] x [0, 6] (24.00 m2: R1 12.00 / 24 = 0.500 of E13 and 1.000 of R1; R3 1.000 of R3) -> {R1, R3}
  (COARSER); EX = [8.2, 9] x [0, 2] (1.60 m2, outdoors pocket) overlaps no reference room (UNREFERENCED).
  Door D1 between R1 and R2: engine rooms {E1, E2} -> AGREE; named by E13 and E2 -> AGREE_COARSER.
  Window W1 in R2's outer wall, geometric side R2 | NO_ROOM: engine {E2, EX} -> AGREE_PLUS_UNREFERENCED.
  Adverse: engine gives W1 to E1 only (R1, not R2) -> ENGINE_WRONG_ROOM; a door whose engine room covers one side only
  -> ENGINE_SIDE_MISSING; an unreferenced engine space on a side where the geometry found a room -> ENGINE_WRONG_ROOM;
  no engine opening -> NO_ENGINE_OPENING (never AGREE); a sliver overlap (2 %) is not a crosswalk.
  Mirror (x -> -x) and a 37 degree rotation leave every share and verdict unchanged.
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t262"
sys.path.insert(0, str(HERE))
import engine_rooms_t262 as E  # noqa: E402


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def tf(pts, mirror=False, deg=0.0, dx=0.0, dy=0.0):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = []
    for x, y in pts:
        x = -x if mirror else x
        out.append((c * x - s * y + dx, s * x + c * y + dy))
    return out


def fixture(**t):
    ref = {"R1": [{"ext": tf(rect(0, 0, 4, 3), **t), "holes": []}],
           "R2": [{"ext": tf(rect(4.15, 0, 8, 3), **t), "holes": []}],
           "R3": [{"ext": tf(rect(0, 3.15, 4, 6), **t), "holes": []}]}
    floor = {k: "GF" for k in ref}
    eng = [{"room_id": "E1", "floor": "GF", "class": "ROOM", "polygon_m": tf(rect(0, 0, 4, 3), **t),
            "doors": ["OP-001"], "windows": []},
           {"room_id": "E2", "floor": "GF", "class": "ROOM", "polygon_m": tf(rect(4.15, 0, 8, 3), **t),
            "doors": ["OP-001"], "windows": ["OP-002"]},
           {"room_id": "E13", "floor": "GF", "class": "MIXED", "polygon_m": tf(rect(0, 0, 4, 6), **t),
            "doors": ["OP-003"], "windows": []},
           {"room_id": "EX", "floor": "GF", "class": "UNLABELLED", "polygon_m": tf(rect(8.2, 0, 9, 2), **t),
            "doors": [], "windows": ["OP-002"]},
           {"room_id": "E1F", "floor": "1F", "class": "ROOM", "polygon_m": tf(rect(0, 0, 4, 3), **t),
            "doors": ["OP-001"], "windows": []}]
    return ref, floor, eng


TRANSFORMS = [{}, {"mirror": True}, {"deg": 37.0, "dx": 1000.0, "dy": -500.0}, {"mirror": True, "deg": -90.0}]


@pytest.mark.parametrize("t", TRANSFORMS)
def test_crosswalk_shares_by_hand(t):
    ref, floor, eng = fixture(**t)
    xw = E.crosswalk(eng, ref, floor)
    assert xw["E1"]["mapped"] == ["R1"] and xw["E1"]["refs"]["R1"] == pytest.approx((1.0, 1.0), abs=1e-4)
    assert xw["E2"]["mapped"] == ["R2"]
    assert xw["E13"]["mapped"] == ["R1", "R3"]
    assert xw["E13"]["refs"]["R1"] == pytest.approx((1.0, 0.5), abs=1e-4)
    assert xw["E13"]["refs"]["R3"] == pytest.approx((1.0, 11.40 / 24.0), abs=1e-4)
    assert xw["E13"]["area_m2"] == pytest.approx(24.0, abs=1e-3)          # kept in memory, not written
    assert xw["EX"]["refs"] == {} and xw["EX"]["mapped"] == []
    assert xw["E1F"]["refs"] == {}                 # another floor never matches


@pytest.mark.parametrize("t", TRANSFORMS)
def test_verdicts_normal_cases(t):
    ref, floor, eng = fixture(**t)
    xw = E.crosswalk(eng, ref, floor)
    d1 = E.engine_rooms_of(eng, "GF", "OP-001")
    assert d1 == ["E1", "E2"]                      # the 1F room naming OP-001 is another floor's opening
    assert E.verdict({"R1", "R2"}, d1, xw) == "AGREE"
    assert E.verdict({"R1", "R2"}, ["E13", "E2"], xw) == "AGREE_COARSER"
    w1 = E.engine_rooms_of(eng, "GF", "OP-002")
    assert w1 == ["E2", "EX"]
    assert E.verdict({"R2"}, w1, xw, geo_has_no_room_side=True) == "AGREE_PLUS_UNREFERENCED"


def test_verdicts_adverse_cases():
    ref, floor, eng = fixture()
    xw = E.crosswalk(eng, ref, floor)
    assert E.verdict({"R2"}, ["E1"], xw, True) == "ENGINE_WRONG_ROOM"            # window given to the wrong room
    assert E.verdict({"R1", "R2"}, ["E1"], xw) == "ENGINE_SIDE_MISSING"          # a door with one side only
    assert E.verdict({"R2"}, ["E2", "EX"], xw, False) == "ENGINE_WRONG_ROOM"     # unreferenced where a room is
    assert E.verdict({"R1"}, [], xw) == "ENGINE_NO_ROOM"
    assert E.verdict({"R2"}, ["EX"], xw, True) == "ENGINE_WRONG_ROOM"            # only the outdoors pocket


def test_sliver_is_not_a_crosswalk():
    ref = {"R1": [{"ext": rect(0, 0, 4, 3), "holes": []}]}
    eng = [{"room_id": "S", "floor": "GF", "class": "ROOM", "polygon_m": rect(3.94, 0, 8, 3)}]   # 0.18 / 12 = 1.5 %
    xw = E.crosswalk(eng, ref, {"R1": "GF"})
    st, se = xw["S"]["refs"]["R1"]
    assert st == pytest.approx(0.015, abs=1e-4) and xw["S"]["mapped"] == []


def test_no_engine_opening_is_never_agree():
    ref, floor, eng = fixture()
    census = [{"ID": "X1", "KIND": "DOOR", "FLOOR": "GF", "ENGINE_REF": "DOOR-GF-abc (engine door schedule only)"}]
    geo = [{"ID": "X1", "ROOMS_GEO": "R1 R2", "SIDE_A_GEO": "R1", "SIDE_B_GEO": "R2"}]
    rows, _, _ = E.compute({"rooms": ref, "room_floor": floor}, eng, census, geo)
    assert rows[0]["VERDICT"] == "NO_ENGINE_OPENING" and rows[0]["ENGINE_ROOMS"] == ""


def test_candidate_room_ids_checked_against_the_run():
    ref, floor, eng = fixture()
    _, wr, _ = E.compute({"rooms": ref, "room_floor": floor}, eng, [], [],
                         {("GF", "OP-002"): "E2", ("GF", "OP-001"): "E13"})
    st = {r["ENGINE_OPENING"]: r["STATE"] for r in wr}
    assert st == {"OP-001": "DIFFERS", "OP-002": "SAME"}


# ---- the development villa (committed result; research only, nothing applied) ----------------------------------

def _rows(name):
    with open(HERE / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_villa_engine_rooms_agree_with_geometry():
    rows = {r["ID"]: r for r in _rows("ENGINE_ROOMS_T262.csv")}
    assert len(rows) == 59
    v = [r["VERDICT"] for r in rows.values()]
    assert not [x for x in v if x in ("ENGINE_WRONG_ROOM", "ENGINE_SIDE_MISSING", "ENGINE_NO_ROOM")]
    assert sum(x.startswith("AGREE") for x in v) == 51 and v.count("NO_ENGINE_OPENING") == 8
    no_eng = {k for k, r in rows.items() if r["VERDICT"] == "NO_ENGINE_OPENING"}
    assert no_eng == {"D-GF-02", "D-GF-10", "D-GF-14", "D-GF-15", "D-1F-03", "D-1F-04", "W03", "W18"}
    # the five census labels T-262 found wrong: the engine's own rooms are the geometric ones
    assert rows["W06"]["ENGINE_ROOMS_AS_T128"] == "GF-13" and rows["W06"]["VERDICT"] == "AGREE"
    assert rows["W19"]["ENGINE_ROOMS_AS_T128"] == "1F-03" and rows["W20"]["ENGINE_ROOMS_AS_T128"] == "1F-02"
    assert rows["D-1F-01"]["VERDICT"] == "AGREE" and set(rows["D-1F-01"]["ROOMS_GEO"].split()) == {"1F-01", "1F-03"}
    unref = {k for k, r in rows.items() if r["UNREFERENCED"]}
    assert unref == {"D-GF-05", "D-1F-07", "W09", "W10", "A-1F-01"}
    assert all(":UNLABELLED:" in rows[k]["UNREFERENCED"] for k in unref)


def test_villa_candidate_window_rooms_are_the_runs():
    wr = _rows("CANDIDATE_WINDOW_ROOM_T262.csv")
    assert len(wr) == 27 and {r["STATE"] for r in wr} == {"SAME"}


def test_villa_files_carry_no_coordinates():
    for n in ("ENGINE_ROOMS_T262.csv", "ENGINE_ROOM_XWALK_T262.csv", "CANDIDATE_WINDOW_ROOM_T262.csv"):
        text = (HERE / n).read_text(encoding="utf-8")
        assert not __import__("re").search(r"\d\.\d{6,}", text), n
