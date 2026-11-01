"""T-418 pins on the development villa (room-local dimensions only; no drawing content): the two stair-room faces
partition and re-add, their floor parts are SILENT_OMISSION findings in V3.0.35 (no floor-finish line), the committed
table and summary reproduce, and the adverse readings are refused."""
import copy
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t418"
sys.path.insert(0, str(HERE))
import stair_room_floor_v1 as SR  # noqa: E402
import t418_alsenan as A  # noqa: E402


def test_gf_stair_room_hand_values():
    res = SR.partition(A.gf_room())
    a = {r["part"]: r for r in res["rows"]}
    assert res["face_m2"] == pytest.approx(12.475)                     # 2.500 x 5.000 - 0.050 x 0.500
    assert a["GF-ST-HALL"]["area_m2"] == pytest.approx(2.5 * 0.45 + 1.15 * 0.70 + 1.15 * 2.50)   # 4.805
    assert a["GF-ST-LOBBY030"]["area_m2"] == pytest.approx(1.15 * 1.15)                          # 1.3225
    assert a["GF-ST-LOBBY030"]["sub_level"] is True and a["GF-ST-HALL"]["sub_level"] is False
    assert a["GF-ST-MS1L"]["area_m2"] == pytest.approx(1.15 * 2.70 - 0.05 * 0.50)                # 3.080
    assert a["GF-ST-D1"]["area_m2"] == pytest.approx(3 * 0.30 * 1.15)                            # 1.035
    assert res["held_bound"] == pytest.approx([0.0, 0.23])
    assert res["floor_m2"] == pytest.approx(6.1275) and res["closure_m2"] == pytest.approx(0.0, abs=1e-9)


def test_2f_stair_hall_hand_values():
    res = SR.partition(A.f2_room())
    a = {r["part"]: r for r in res["rows"]}
    assert res["face_m2"] == pytest.approx(18.600)                     # T-129 face
    assert a["2F-ST-LOBBY"]["area_m2"] == pytest.approx(2.0 * 1.25)    # printed (450 - 250) x 125
    assert a["2F-ST-ARRIVAL"]["family"] == "B7" and a["2F-ST-ARRIVAL"]["area_m2"] == pytest.approx(4.875)
    assert a["2F-ST-OPEN"]["area_m2"] == pytest.approx(10.8225)        # T-129 O-2F
    assert res["floor_m2"] == pytest.approx(2.5)


def test_committed_outputs_reproduce():
    assert A.main(["--check"]) == 0
    s = json.loads(A.SUMMARY.read_text(encoding="utf-8"))
    assert s["candidate_json_sha256"] == A.CANDIDATE_JSON_SHA256
    b = s["candidate_binding"]["floor_finish_lines_on_stair_rooms"]
    assert b == {"GF-R31F8AE": [], "2F-R4D1B62": []}                   # the silent omission this task names
    assert [c["state"] for c in s["census"]] == ["SILENT_OMISSION"] * 3
    fd = s["freelancer_dry"]
    assert fd["diff_m2"] == pytest.approx(fd["components_sum_m2"], abs=1e-4)
    assert fd["was_diff_m2"] == pytest.approx(-49.4242)


def test_adverse_tread_as_floor_refused():
    r = A.gf_room()
    others = [{"id": "D1", "class": "B7", "poly": A.R(1.35, 2.80, 2.5, 3.85)}]   # D1 read 0.15 m too long
    with pytest.raises(SR.Refused, match="stair element counted as floor"):
        SR.partition(r, others=others)


def test_adverse_arrival_counted_as_lobby_floor_refused():
    r = A.f2_room()
    r["parts"][0]["poly"] = A.R(0, 0, 4.5, 1.25)                       # the printed 450 read across the arrival
    with pytest.raises(SR.Refused, match="overlaps"):
        SR.partition(r)


def test_adverse_unread_strip_never_zero_and_missing_part_refused():
    r = A.gf_room()
    cn = [p for p in r["parts"] if p["id"] == "GF-ST-CN"][0]
    assert cn["kind"] == "UNREAD"
    r2 = copy.deepcopy(r)
    r2["parts"] = [p for p in r2["parts"] if p["id"] != "GF-ST-CN"]
    with pytest.raises(SR.Refused, match="do not re-add"):
        SR.partition(r2)
