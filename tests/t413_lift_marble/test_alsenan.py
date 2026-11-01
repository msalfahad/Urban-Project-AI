"""T-413 pins on the development villa (station-local dimensions only; no drawing content): three landing stations,
the 2F right band infeasible at the owner default, surround HELD with its bound, threshold 1.500 m2 with its owner
source, the committed table and summary reproduce, and the candidate carries no lift-marble line."""
import csv
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t413"
sys.path.insert(0, str(HERE))
import lift_entrance_marble_v1 as LM  # noqa: E402
import t413_alsenan as A  # noqa: E402


def test_committed_outputs_reproduce():
    assert A.main(["--check"]) == 0


def test_three_stations_one_door_each():
    st, rows, surs, thrs = A.build()
    assert st == ["ELV-01-GF", "ELV-01-1F", "ELV-01-2F"]
    assert [r["ENGINE_OPENING"] for r in rows] == ["OP-011", "OP-007", "OP-002"]
    assert all(r["CLEAR_WIDTH_M"] == "1.000" and r["WIDTH_STATUS"] == LM.DRAWING for r in rows)


def test_surround_held_by_height_and_2f_right_band():
    st, rows, surs, thrs = A.build()
    by = {s["station_id"]: s for s in surs}
    assert all(s["area_m2"] is None and s["status"] == LM.HELD for s in surs)
    assert by["ELV-01-GF"]["bound_m2"] == pytest.approx([1.0, 4.00 + 1.0])        # h_max 4.50 - 0.50
    assert by["ELV-01-1F"]["bound_m2"] == pytest.approx([1.0, 3.70 + 1.0])
    assert by["ELV-01-2F"]["bound_m2"] == pytest.approx([0.5 * 1.5, 3.70 * 0.9 + 0.5 * 1.9])
    right2f = by["ELV-01-2F"]["bands"][2]
    assert right2f["width_m"] is None and right2f["bound"] == [0.0, 0.4]
    assert "INFEASIBLE_DEFAULT" in right2f["source"]
    s = json.loads(A.SUMMARY.read_text(encoding="utf-8"))
    assert s["surround_B6_06"]["value_m2"] is None
    assert s["surround_B6_06"]["bound_m2"] == pytest.approx([2.75, 13.98])


def test_threshold_owner_depth_drawn_width():
    s = json.loads(A.SUMMARY.read_text(encoding="utf-8"))
    t = s["threshold_B6_07"]
    assert t["value_m2"] == pytest.approx(3 * 1.0 * 0.5) and t["front_edge_lm"] == pytest.approx(3.0)
    assert t["floor_overlap_bound_m2"] == pytest.approx([0.9, 1.5])
    assert "UP-ELEV-005" in t["status"]


def test_candidate_binding():
    s = json.loads(A.SUMMARY.read_text(encoding="utf-8"))
    b = s["candidate_binding"]
    assert s["candidate_json_sha256"] == A.CANDIDATE_JSON_SHA256
    assert b["lift_marble_lines"] == []                                     # B6-06 / B6-07: NO LINE
    assert sorted(b["lift_landing_threshold_lines"]) == sorted(A.LIFT_BAND_LINES)
    rows = list(csv.DictReader(A.TABLE.read_text(encoding="utf-8").splitlines()))
    assert {r["CANDIDATE_LINE"] for r in rows} == {"NO LINE (B6-06 / B6-07)"}
    assert [r["BAND_LINE"] for r in rows] == A.LIFT_BAND_LINES                 # GF, 1F, 2F
    assert all(r["OPENING_LINE"].startswith("L-") for r in rows)
    assert [r["FLOOR_LINE"] for r in rows] == ["L-7625f35c503d9f8e6196", "L-b06400d46d252f242018", "NO LINE"]
    strips = {x["line_id"]: x for x in b["lift_opening_lines"] if x["item_code"] == "FIN.FLOOR.PORCELAIN"}
    assert sorted(strips) == sorted(A.LIFT_STRIP_LINES)
    assert {x["evidence_state"] for x in strips.values()} == {"NOT_APPLICABLE_WITH_EVIDENCE"}
    bands = [x for x in b["lift_opening_lines"] if x["item_code"] == "ARCH.THRESHOLD"]
    assert all(x["bound_m2"] == [0.2, 0.2] for x in bands)                       # 1.000 x 0.200 wall band each


def test_adverse_on_the_villa():
    with pytest.raises(LM.Refused):
        LM.check_count(1, [{"floor": f, "doors": [{}]} for f in ("GF", "1F", "2F")])   # the shaft as the count
    with pytest.raises(LM.Refused):
        LM.band_width("RIGHT", drawn_m=0.5, available_m=0.4)                           # wider than the 2F face
    with pytest.raises(LM.Refused):
        LM.bind("ELV-01-GF", ["ARCH.THRESHOLD"])
