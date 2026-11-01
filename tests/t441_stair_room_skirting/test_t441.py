"""T-441 / STAIR_ROOM_SKIRTING_V1 (R-T441-1 .. 4): floor-level wall-face length of the floor parts of a stair room.

Hand villa K441 (not Alsenan). Stair room 3.00 m wide; a hall floor part at +0.50 and a 2nd-floor lift lobby at +7.00.
By hand:
  hall south   3.00 = wall 0.80 + door D-K1 0.90 (deducted, no jambs) + wall 1.30            -> 2.10
  hall east    2.40 = wall 1.00 + passage P-K1 1.00 (deducted)          + wall 0.40            -> 1.40
               passage jambs 2 x 0.25 = 0.50, listed apart (not in the confirmed net)
  hall west    2.40 = 0.06 under the first nosing (owned by stair stretch F-K1 from its station) + wall 2.34 -> 2.34
  hall north   1.40 open to the flight; guard band 1.00 HELD (blank, candidate 1.00)
  hall confirmed 2.10 + 1.40 + 2.34 = 5.84 lm; deducted 1.90; held 1 stretch
  lobby south  2.00 wall; north 2.00 = wall 0.45 + lift opening L-K1 1.10 + wall 0.45; west open -> 2.90 lm
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research" / "agents_t441"
sys.path.insert(0, str(RES))
import stair_room_skirting_v1 as S  # noqa: E402


def hall():
    return {"id": "K-HALL", "room": "K-ST", "level": 0.50, "sides": [
        {"id": "S", "line": "K:y=0", "t0": 0.0, "dir": 1, "length": 3.0, "stretches": [
            {"s0": 0.0, "s1": 0.8, "kind": "WALL", "handles": "w1"},
            {"s0": 0.8, "s1": 1.7, "kind": "DOOR", "opening_id": "D-K1"},
            {"s0": 1.7, "s1": 3.0, "kind": "WALL", "handles": "w2"}]},
        {"id": "E", "line": "K:x=3", "t0": 0.0, "dir": 1, "length": 2.4, "stretches": [
            {"s0": 0.0, "s1": 1.0, "kind": "WALL", "handles": "w3"},
            {"s0": 1.0, "s1": 2.0, "kind": "PASSAGE", "opening_id": "P-K1"},
            {"s0": 2.0, "s1": 2.4, "kind": "WALL", "handles": "w4"}]},
        {"id": "N", "line": "K:y=2.4", "t0": 3.0, "dir": -1, "length": 1.4, "stretches": [
            {"s0": 0.0, "s1": 1.4, "kind": "OPEN", "note": "flight"}]},
        {"id": "G", "line": "K:x=1.6", "t0": 2.4, "dir": -1, "length": 1.0, "stretches": [
            {"s0": 0.0, "s1": 1.0, "kind": "GUARD_HELD", "cause": "stair band: wall or guard not established"}]},
        {"id": "W", "line": "K:x=0", "t0": 2.4, "dir": -1, "length": 2.4, "stretches": [
            {"s0": 0.0, "s1": 0.06, "kind": "STAIR_SIDE", "flight": "F-K1"},
            {"s0": 0.06, "s1": 2.4, "kind": "WALL", "handles": "w5"}]}],
        "jambs": [{"id": "J1", "opening_id": "P-K1", "depth": 0.25, "status": S.PROVISIONAL},
                  {"id": "J2", "opening_id": "P-K1", "depth": 0.25, "status": S.PROVISIONAL}]}


FLIGHTS = [{"id": "F-K1", "line": "K:x=0", "t0": 2.34, "t1": 4.50, "lo": 0.50, "hi": 2.00},
           {"id": "LD-K1", "line": "K:x=3", "t0": 0.00, "t1": 2.40, "lo": 2.00, "hi": 2.00}]   # landing above


def lobby():
    return {"id": "K-LOBBY", "room": "K-ST2", "level": 7.00, "sides": [
        {"id": "S", "line": "K2:y=0", "t0": 0.0, "dir": 1, "length": 2.0, "stretches": [
            {"s0": 0.0, "s1": 2.0, "kind": "WALL", "handles": "w6"}]},
        {"id": "N", "line": "K2:y=1.2", "t0": 2.0, "dir": -1, "length": 2.0, "stretches": [
            {"s0": 0.0, "s1": 0.45, "kind": "WALL", "handles": "w7"},
            {"s0": 0.45, "s1": 1.55, "kind": "LIFT_OPENING", "opening_id": "L-K1"},
            {"s0": 1.55, "s1": 2.0, "kind": "WALL", "handles": "w8"}]},
        {"id": "W", "line": "K2:x=0", "t0": 1.2, "dir": -1, "length": 1.2, "stretches": [
            {"s0": 0.0, "s1": 1.2, "kind": "OPEN"}]}]}


BAND = {"opening_id": "L-K1", "edge_handles": ["j1", "j2", "b1"]}


# ------------------------------------------------------------------------------------------------- normal
def test_k441_hall_by_hand():
    r = S.measure(hall(), FLIGHTS)
    assert r["net_confirmed_lm"] == pytest.approx(5.84, abs=1e-9)
    assert r["deducted_m"] == pytest.approx(1.90, abs=1e-9)
    assert [d["opening_id"] for d in r["deductions"]] == ["D-K1", "P-K1"]
    assert r["jambs_lm"] == pytest.approx(0.50, abs=1e-9)
    assert r["held_count"] == 1 and r["held"][0]["candidate_lm"] == 1.0
    assert r["boundary_m"] == pytest.approx(3.0 + 2.4 + 1.4 + 1.0 + 2.4, abs=1e-9)


def test_k441_lobby_by_hand_and_band():
    r = S.measure(lobby())
    assert r["net_confirmed_lm"] == pytest.approx(2.90, abs=1e-9)
    assert r["deductions"] == [{"opening_id": "L-K1", "kind": "LIFT_OPENING", "width_m": 1.1}]
    assert S.lift_band_check(lobby(), BAND)


def test_held_stays_blank_never_zero():
    r = S.measure(hall(), FLIGHTS)
    g = [row for row in r["rows"] if row["kind"] == "GUARD_HELD"]
    assert g and all(row["skirting_lm"] is None for row in g)


def test_landing_above_is_not_an_overlap():
    # LD-K1 lies on the hall's east wall line in plan but at +2.00: no shared base with the +0.50 hall
    assert S.overlaps(hall(), FLIGHTS) == []


def test_mirror_invariance():
    m = hall()
    for sd in m["sides"]:
        L = sd["length"]
        sd["t0"] = sd["t0"] + sd["dir"] * L
        sd["dir"] = -sd["dir"]
        sd["stretches"] = [dict(st, s0=round(L - st["s1"], 9), s1=round(L - st["s0"], 9))
                           for st in reversed(sd["stretches"])]
    a, b = S.measure(hall(), FLIGHTS), S.measure(m, FLIGHTS)
    for k in ("net_confirmed_lm", "deducted_m", "jambs_lm", "held_count", "boundary_m"):
        assert a[k] == pytest.approx(b[k], abs=1e-9)


# ------------------------------------------------------------------------------------------------- adverse
def test_adverse_lift_threshold_band_counted_as_wall_face():
    bad = lobby()
    bad["sides"][1]["stretches"][1] = {"s0": 0.45, "s1": 1.55, "kind": "WALL", "handles": "b1"}
    with pytest.raises(S.Refused, match="lift threshold band"):
        S.lift_band_check(bad, BAND)
    jam = lobby()
    jam["jambs"] = [{"id": "LJ", "opening_id": "L-K1", "depth": 0.2}]
    with pytest.raises(S.Refused, match="lift-opening jamb"):
        S.measure(jam)


def test_adverse_face_shared_with_flight_stretch():
    bad = hall()
    bad["sides"][4]["stretches"] = [{"s0": 0.0, "s1": 2.4, "kind": "WALL", "handles": "w5"}]
    with pytest.raises(S.Refused, match="R-T441-2"):
        S.measure(bad, FLIGHTS)


def test_adverse_held_as_zero_and_without_cause():
    z = hall()
    z["sides"][3]["stretches"][0]["lm"] = 0
    with pytest.raises(S.Refused, match="never 0"):
        S.measure(z, FLIGHTS)
    c = hall()
    del c["sides"][3]["stretches"][0]["cause"]
    with pytest.raises(S.Refused, match="cause"):
        S.measure(c, FLIGHTS)


def test_adverse_units_gap_overlap_short_cover():
    mm = hall()
    mm["sides"][0]["length"] = 3000.0
    with pytest.raises(S.Refused, match="unit slip"):
        S.measure(mm, FLIGHTS)
    gap = hall()
    gap["sides"][0]["stretches"][1]["s0"] = 0.85
    with pytest.raises(S.Refused, match="gap"):
        S.measure(gap, FLIGHTS)
    ov = hall()
    ov["sides"][0]["stretches"][1]["s0"] = 0.75
    with pytest.raises(S.Refused, match="overlap"):
        S.measure(ov, FLIGHTS)
    short = hall()
    short["sides"][0]["stretches"].pop()
    with pytest.raises(S.Refused, match="short cover"):
        S.measure(short, FLIGHTS)


def test_adverse_opening_without_id_and_door_jamb_and_stair_side_without_owner():
    a = hall()
    a["sides"][0]["stretches"][1]["opening_id"] = ""
    with pytest.raises(S.Refused, match="R-T441-3"):
        S.measure(a, FLIGHTS)
    b = hall()
    b["jambs"].append({"id": "DJ", "opening_id": "D-K1", "depth": 0.2})
    with pytest.raises(S.Refused, match="door jamb"):
        S.measure(b, FLIGHTS)
    c = hall()
    del c["sides"][4]["stretches"][0]["flight"]
    with pytest.raises(S.Refused, match="owning stair stretch"):
        S.measure(c, FLIGHTS)


def test_adverse_face_without_handle():
    a = hall()
    a["sides"][0]["stretches"][0]["handles"] = ""
    with pytest.raises(S.Refused, match="handle"):
        S.measure(a, FLIGHTS)


# ------------------------------------------------------------------------------------------------- Alsenan pins
def _summary():
    return json.loads((RES / "summary.json").read_text(encoding="utf-8"))


def test_alsenan_reproduces_from_committed_extract():
    out = subprocess.run([sys.executable, "-I", str(RES / "t441_alsenan.py"), "--check"], capture_output=True,
                         text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stderr
    assert "check OK" in out.stdout


def test_alsenan_totals_hand_checked():
    s = _summary()
    p = {x["part"]: x for x in s["parts"]}
    # hall: south 1.400 + 0.100, east 2.000 + 0.050, west 1.100 (0.050 under the first nosing stays with T-410)
    assert p["GF-ST-HALL"]["net_confirmed_lm"] == pytest.approx(1.4 + 0.1 + 2.0 + 0.05 + 1.1, abs=1e-6)
    assert p["GF-ST-LOBBY030"]["net_confirmed_lm"] == pytest.approx(1.15 + 0.147 + 0.103, abs=1e-6)
    assert p["2F-ST-LOBBY"]["net_confirmed_lm"] == pytest.approx(2.0 + 0.1016 + 0.2484 + 0.4 + 0.6, abs=1e-6)
    assert s["task_confirmed_lm"] == pytest.approx(4.65 + 1.4 + 3.35, abs=1e-6)
    assert p["GF-ST-HALL"]["held_face_length_lm"] == [pytest.approx(2.2), pytest.approx(3.4)]
    assert p["GF-ST-LOBBY030"]["held_face_length_lm"] == [0.0, pytest.approx(1.15)]
    assert [d["opening_id"] for d in p["2F-ST-LOBBY"]["deductions"]] == ["OP-007", "OP-002"]


def test_alsenan_closures_and_parents():
    s = _summary()
    assert s["closure"]["GF-R31F8AE"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert s["closure"]["2F-R4D1B62"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert s["handle_checks"]["agree"] == s["handle_checks"]["stretches"] > 0
    par = s["parents"]
    for lid in ("L-47fa825d197d32754240", "L-b8d4a7f04277deb1b0b0"):
        assert par[lid]["evidence_state"] == "BLOCKED_RFI" and par[lid]["measured_net"] is None


def test_alsenan_held_items_are_blank():
    s = _summary()
    for x in s["parts"]:
        for h in x["held"]:
            assert h["cause"] and h["candidate_lm"] > 0
    rows = (RES / "FACES_T441.csv").read_text(encoding="utf-8").splitlines()
    held = [r for r in rows if ",HELD," in r]
    assert held and all(",,HELD," in r for r in held)     # skirting cell empty, never 0
