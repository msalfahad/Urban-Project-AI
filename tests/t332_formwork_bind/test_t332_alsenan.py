"""T-332 on the development villa, pinned from the committed inputs (no private file is read here)."""

import csv
import io
import json
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t332"
sys.path.insert(0, str(HERE))
import t332_alsenan as A  # noqa: E402
import t332_rules as R  # noqa: E402


@pytest.fixture(scope="module")
def B():
    return A.build()


@pytest.fixture(scope="module")
def OUT(B):
    return A.outputs(B)


def _faces(B):
    return {r["face_id"]: r for r in B["after"]}


def test_committed_outputs_are_a_fresh_build(OUT):
    for name, text in OUT.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_every_r5_face_once(B):
    src = [f["face_id"] for f in B["source"]]
    assert len(src) == len(set(src))
    after = [r["face_id"] for r in B["after"]]
    assert len(after) == len(set(after))
    assert set(src) <= set(after)


def test_closure_residual_zero(B):
    for k, v in B["closure"].items():
        assert v["residual_m2"] == 0.0, k


def test_no_scenario_row_in_any_total(B):
    assert not any(r.get("status") == "S1_NOT_RELEASED" and r.get("tie") in ("SAME", "REBOUND") for r in B["after"])


def test_held_faces_are_blank(B):
    for r in B["after"]:
        if r.get("status") == "HELD":
            assert r.get("m2") is None, r["face_id"]


def test_pool_faces_by_hand(B):
    f = _faces(B)
    po = 3.50 + 2 * 1.75 + math.pi * 1.75          # 7C6 outer D
    pw = 3.10 + 2 * 1.55 + math.pi * 1.55          # 7C5 water D
    deck = po - 3.50
    assert f["T332-POOL-WATER"]["m2"] == pytest.approx(pw * 1.20, abs=1e-6)                 # 13.283363
    assert f["T332-POOL-OUT-ABOVE-EG"]["m2"] == pytest.approx(deck * 0.30, abs=1e-6)          # 2.699336
    assert f["T332-POOL-OUT-BURIED-F"]["m2"] == pytest.approx(deck * 0.90, abs=1e-6)          # 8.098008
    assert f["T332-POOL-BASE-EDGE-F"]["m2"] == pytest.approx(deck * 0.40, abs=1e-6)           # 3.599115
    assert f["T332-POOL-BACK-WALL"]["hi"] == pytest.approx(3.50 * 1.20)
    total = sum(f[k]["m2"] for k in ("T332-POOL-WATER", "T332-POOL-OUT-ABOVE-EG", "T332-POOL-OUT-BURIED-F",
                                     "T332-POOL-BASE-EDGE-F")) + f["T332-POOL-BACK-WALL"]["hi"] + f["T332-POOL-BACK-BASE"]["hi"]
    assert total == pytest.approx(33.280, abs=0.0005)    # = T-183 r2 G formwork 33.280 (outer 19.996 + water 13.283)
    assert f["T332-POOL-OUT-BURIED-E"]["m2"] == 0.0 and f["T332-POOL-BASE-EDGE-E"]["m2"] == 0.0
    assert f["R4-340.WALLS"]["status"] == "REMOVED" and f["R4-340.BASE"]["status"] == "REMOVED"


def test_f8_pool_conflict(B):
    f = _faces(B)
    inp = B["input"]["f8_vs_pool"]
    assert inp["overlap_f8_outer_m2"] == pytest.approx(1.296442, abs=0.0002)     # T-189 / T-320
    assert inp["overlap_f8_envelope_m2"] == pytest.approx(1.616, abs=0.0005)     # T-320
    inside = sum(x["inside_envelope"] for x in inp["faces"])
    assert f[A.F8_FORMED]["m2"] + f["T332-F8-POOL-CONFLICT"]["hi"] == pytest.approx(7.600, abs=1e-6)
    assert f["T332-F8-POOL-CONFLICT"]["hi"] == pytest.approx(inside * 0.50, abs=1e-6)
    s = {x["face"]: x["inside_envelope"] for x in inp["faces"]}
    assert s["S"] == 0.0     # the SB1 cover (-0.350) sits on the S face: no second deduction


def test_lift_pit_per_metre(B):
    ring = B["input"]["lift_ring"]
    assert ring["inner"]["not_on_a_column"] == pytest.approx(7.20 - (0.30 + 0.30 + 0.30 + 0.80), abs=1e-6)
    assert ring["outer"]["not_on_a_column"] == pytest.approx(8.80 - (0.70 + 0.70 + 0.70 + 1.20), abs=1e-6)
    assert ring["band_net_of_columns_m2"] == pytest.approx(1.100, abs=1e-6)      # T-204 / T-322
    f = _faces(B)
    assert f["T332-LIFT-PIT-INNER"]["status"] == "HELD" and f["T332-LIFT-PIT-INNER"]["tie"] == "NO_LINE"
    assert f["R4-342"]["status"] == "REMOVED"


def test_parapet_rows_are_no_line_and_close_on_t311(B):
    rows = [r for r in B["after"] if r["face_id"].startswith("T332-PARAPET-")]
    assert len(rows) == 24
    assert all(r["tie"] == "NO_LINE" and r["status"] == "HELD" for r in rows)
    assert sum(r["lo"] for r in rows) == pytest.approx(81.58869, abs=1e-5)
    assert sum(r["hi"] for r in rows) == pytest.approx(202.781594, abs=1e-5)


def test_chain_closes_on_r3(B):
    assert B["chain_totals"]["r3"] == pytest.approx(1078.274, abs=1e-6)
    for row in B["chain"]:
        for k, v in row.items():
            if k.startswith("residual"):
                assert abs(v) < 1e-6, (row["element"], k, v)


def test_fill_table_only_tied_rows(OUT):
    fill = list(csv.DictReader(io.StringIO(OUT["T199_FILL_T332.csv"])))
    ids = set()
    for r in fill:
        for fid in r["face_ids"].split():
            assert fid not in ids
            ids.add(fid)
    assert not any(i.startswith("T332-PARAPET-") or i.startswith("T332-LIFT") for i in ids)


def test_no_coordinates_in_outputs(OUT):
    for name, text in OUT.items():
        assert not re.search(r"\b1\d{5}\.\d", text), name     # no model-space coordinate of the client drawing
