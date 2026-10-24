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
