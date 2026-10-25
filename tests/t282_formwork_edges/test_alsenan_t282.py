"""T-282 Alsenan ground-beam side forms re-traced per edge, as a delta against the merged formwork r4 (T-264), from
committed inputs only (ALSENAN_EDGE_INPUT.json derived from Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' sha
9f9d1179; FORMWORK_LINES_R4.csv). Development villa; not an accuracy claim; no BOQ line changed."""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t282"
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("formwork_t282", HERE / "formwork_t282.py")
FW = importlib.util.module_from_spec(spec)
spec.loader.exec_module(FW)
ROWS, RING, TEES, INP = FW.build()
BY = {(r["span_id"], r["side"]): r for r in ROWS}


def test_committed_outputs_equal_a_fresh_build(tmp_path):
    FW.write(str(tmp_path))
    for name in ("DELTA_T282_GROUND_BEAM_SIDES.csv", "summary_t282.json"):
        assert (tmp_path / name).read_text(encoding="utf-8") == (HERE / name).read_text(encoding="utf-8"), name


def test_ring_framing_band_closes_on_the_arc_on_each_edge():
    # the Verifier's T-276 case: band 177+7CD frames into ARC 158 at two stations; side A (LINE 177) is 0.219 m
    # longer than the square cut, the ring's outer face is the arc less the framing zone (Verifier own 5.9055 m)
    r = BY[("177+7CD#2", "A")]
    assert r["delta_m"] == pytest.approx(0.2191, abs=5e-4) and r["status"] == "DRAWING-CONFIRMED"
    assert BY[("177+7CD#2", "B")]["status"] == "AGREES"
    assert RING["outer_traced_m"] == pytest.approx(5.9055, abs=1e-3)
    assert RING["inner_traced_m"] == pytest.approx(6.5674, abs=1e-4)         # no tangent-point snap on the arc
    assert RING["cover_width_drawn_m"] == pytest.approx(0.3715, abs=5e-4)     # not 0.30
    assert not [r for r in ROWS if r["span_id"] == "177+7CD#2" and r["side"] == "END" and r["traced_m"] >= 0.001]


def test_sliver_column_is_a_column_face():
    sl = [s for s in INP["slivers"] if s["column"] == "COL:255"]
    assert sl and all(s["below_snap"] and abs(s["offset_mm"]) == pytest.approx(0.052, abs=1e-3) for s in sl)
    cols = {c["column"]: c["length_m"] for c in INP["traced"]["columns"]}
    assert cols["COL:255"] >= 0.7                                             # its 0.700 m face is the column's
    assert BY[("7D0+FC#3", "A")]["status"] == "AGREES"


def test_tee_on_carrier_and_verifier_agreements():
    # Verifier T-276 own: 7D0+FC#1 side B 2.975 less tee 0.300 = 2.675 m traced
    side = {(x["span_id"], x["side"]): x["length_m"] for x in INP["traced"]["sides"]}
    assert side[("7D0+FC#1", "B")] == pytest.approx(2.675, abs=1e-4)
    assert side[("7D0+FC#3", "B")] == pytest.approx(6.05, abs=1e-4)
    oblique = [t for t in TEES if t["gap_m"] == pytest.approx(0.4243, abs=1e-3)]
    assert len(oblique) == 3                                                  # 45-degree tees on 176+7E6 / 180D+180E


def test_no_square_cut_survives_and_held_never_zero():
    for r in ROWS:
        if r["status"] == "HELD":
            assert r["traced_m"] != 0.0 or r["side"] == "END"
        if r["side"] != "END" and r["status"] != "AGREES":
            assert r["cause"]
    assert not INP["traced"]["unattributed"]
    # every face piece of the boundary has one owner: sides + ends + columns + lift + arcs = the boundary
    t = INP["traced"]
    tot = sum(x["length_m"] for x in t["sides"]) + sum(x["length_m"] for x in t["ends"]) + \
        sum(x["length_m"] for x in t["columns"]) + sum(x["length_m"] for x in t["others"]) + \
        sum(x["length_m"] for x in t["arcs"])
    assert tot == pytest.approx(t["boundary_total_m"], abs=1e-3)


def test_no_client_text_or_coordinates_in_the_committed_input():
    raw = (HERE / "ALSENAN_EDGE_INPUT.json").read_text(encoding="utf-8")
    d = json.loads(raw)
    for sp in d["spans"]:
        for e in sp["edges"].values():
            assert -1.0 <= e["drawn_from_m"] <= 60.0 and e["drawn_to_m"] <= 60.0    # stations from the band start
    assert "Alsenan chalet project" in d["source"]["drive"]


def test_r2_no_end_face_on_a_hull_diagonal():
    # Verifier 2026-10-25 00:04: 170+7C3#4 END 0.2318 and 1811+1812#1 END 0.0972 were hull diagonals: withdrawn
    ends = {(e["span_id"], e["end_kind"]): e["length_m"] for e in INP["traced"]["ends"]}
    assert ("170+7C3#4", "COLUMN") not in ends and ("1811+1812#1", "COLUMN") not in ends
    # r3: 15E+15F#1's 0.100 beside COL:1F5 and 1811+1812#1's 0.300 lie on drawn concrete faces (R-FACE-END-3)
    assert ("15E+15F#1", "COLUMN") not in ends and ("1811+1812#1", "FREE_END") not in ends
    cols = {c["column"]: c["length_m"] for c in INP["traced"]["columns"]}
    assert cols["COL:17C0"] == pytest.approx(0.2475, abs=1e-4) and cols["COL:1E8"] == pytest.approx(0.5, abs=1e-4)
    # side B of 170+7C3#4 is unchanged (Verifier own +0.300 m, CALC +0.285 m2)
    assert BY[("170+7C3#4", "B")]["delta_m"] == pytest.approx(0.300, abs=1e-4)
    assert BY[("170+7C3#4", "B")]["delta_m2_lo"] == pytest.approx(0.285, abs=1e-4)
    formed = FW.totals(ROWS)["delta_m2"]["DRAWING-CONFIRMED FORMED"]
    assert formed[0] == pytest.approx(0.0, abs=1e-4)      # r1 0.340, r2 0.120 (17C+7E3#1 on the lift ring: r3 contact)


def test_r3_ends_on_concrete_outlines_are_contacts():
    # Verifier 2026-10-25 01:31 + own re-measure: the lift pit ring S-BW 7C2 (T-204 / T-230) and the boundary G.B
    # bands S-BOUN 7FE / 7FC / 810 (T-253) are owners; r1 / r2 passed only the pool outline 7C6 (labelled 'LIFT')
    t = INP["traced"]
    assert sorted(o["owner"] for o in t["others"]) == ["BOUNDARY_GB:7FC", "BOUNDARY_GB:7FE", "BOUNDARY_GB:810",
                                                       "RC_WALL:7C2", "RC_WALL:7C6"]
    con = {(c["span_id"], c["owner"]): c for c in t["end_contacts"] if c["status"] == "CONTACT"}
    for sid, owner, kind in (("1811+1812#1", "BOUNDARY_GB:7FE", "FREE_END"),
                             ("15D+7C8#1", "RC_WALL:7C2", "FOOTING_FACE"),
                             ("17C+7E3#1", "RC_WALL:7C2", "FOOTING_FACE"),
                             ("177+7CD#1", "RC_WALL:7C2", "GAP_TO_COLUMN"),
                             ("15E+15F#1", "RC_WALL:7C2", "COLUMN")):
        c = con[(sid, owner)]
        assert c["kind"] == kind and c["covered_m"] == pytest.approx(0.3, abs=1e-4), sid
        r = [x for x in ROWS if x["span_id"] == sid and x["side"] == "END"]
        assert len(r) == 1 and r[0]["traced_m"] == 0.0 and r[0]["status"] == "DRAWING-CONFIRMED", sid
    ends = {(e["span_id"], e["end_kind"]) for e in t["ends"]}
    assert ends == {("13E+7D6#2", "BEAM_JUNCTION"), ("ARC:139+13A/1", "ARC_END"), ("ARC:157+158/2", "ARC_END")}
    assert not t["open_outline_ends"] and not [c for c in t["end_contacts"] if c["status"] in ("NONE", "PARTIAL")]
    # every end whose two edges stop at different stations is accounted for (none left silent)
    res = {(u["span_id"], u["end"]): u["resolution"] for u in t["unequal_station_ends"]}
    assert len(res) == 18 and set(res.values()) == {"COVERED_BY_OUTLINES", "CLOSED_AS_BEAM"}
    assert res[("177+7CD#2", "end")] == "CLOSED_AS_BEAM"                       # the ring end (T-276 +0.2191 m)
    # 10B+7D1#1 side A: boundary band 810 frames into the annex beam face over 0.200 m (plan; annex CONFLICT, m only)
    assert BY[("10B+7D1#1", "A")]["traced_m"] == pytest.approx(1.3, abs=1e-4)
    tot = FW.totals(ROWS)
    assert tot["delta_m_by_status"]["DRAWING-CONFIRMED_END"] == pytest.approx(0.0, abs=1e-4)
    assert tot["delta_m2"]["DRAWING-CONFIRMED HELD"] == pytest.approx((0.6567, 0.8556), abs=1e-4)
