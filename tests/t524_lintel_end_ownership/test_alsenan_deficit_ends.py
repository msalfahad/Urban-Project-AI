"""T-524 on the training villa: the 10 T-516 FLAGGED_DEFICIT lintels (merged T-453 0.514 m3), from committed records
only (no private file needed).

Hand checks (b_min 0.40; B x D 0.15 x 0.20 = 0.03 m2 on 0.15 walls, 0.20 x 0.20 = 0.04 m2 on 0.20 walls):
  COLUMN ends, columns re-derived in the structural frame (R9.1 crosswalk + S8.6 census), gap vs T-516 a:
    D-1F-04 START a 0.079: planted column PC X08-Y02 1F (70x20, 0.20 along the wall), gap 0.0797; r 0.321 = 0.200
            inside (0.006 m3) + 0.121 beyond its far face (0.00363 m3, not built).
    D-2F-03 START a 0.249: C2 X10-Y09 2F (20x50, 0.50 along), gap 0.2492; r 0.151 inside (0.00453 m3).
    D-GF-06 END a 0.140: C6 X08-Y04 GF (25x70, 0.25 along), gap 0.166 (+26 mm frame registration); r 0.260 = 0.25
            inside (0.0100 m3) + 0.010 beyond (0.0004 m3).
    W18 START a 0.000: C8 X15-Y06 1F (20x90, 0.90 along), jamb 32.7 mm inside the column (register, VERIFIED): span strip
            0.0327 (0.001308 m3) + r 0.40 inside (0.016 m3); w_net 0.4673, L 0.8673, 0.034692 m3 (T-453 0.052).
  END_OF_MASONRY ends (far face of a cross wall; r not built): D-1F-03 0.162 (0.00486), D-1F-07 0.141 (0.00423),
    D-1F-10 0.141 (0.00423), D-GF-10 0.147 (0.00441).
  PIER D-GF-11 / D-GF-12 (0.238, heads 2.20 both, L1 0.15 x 0.20): T-453 overlap 0.80 - 0.238 = 0.562 m (0.01686 m3);
    pair hi 0.80 + 0.40 + 0.80 + 0.40 + 0.238 = 2.638 m (0.07914 m3), lo 0.80 + 0.40 + 0.80 + 0 (D-GF-12 END HELD) = 2.00.
  Set: T-453 0.514; corrected hi 0.437542, lo 0.372692; removed 0.076458 = inside columns 0.037838 + lintel on lintel
    0.01686 + not built 0.02176.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t524"))

import t524_lintel_end_ownership as T  # noqa: E402


@pytest.fixture(scope="module")
def out():
    return T.build()


def test_the_ten_deficit_lintels(out):
    assert sorted(out["lintels"]) == ["D-1F-03", "D-1F-04", "D-1F-07", "D-1F-10", "D-2F-03", "D-GF-06", "D-GF-10",
                                      "D-GF-11", "D-GF-12", "W18"]
    assert all(r["state"] == "HELD_BY_NAME" and r["concrete_lo_m3"] > 0 for r in out["lintels"].values())
    assert [p["pair"] for p in out["pairs"]] == [["D-GF-11", "D-GF-12"]]


@pytest.mark.parametrize("oid, cid, along, inside, beyond", [
    ("D-1F-04", "COL-PC-X08-Y02-1F", 0.20, 0.200, 0.121),
    ("D-2F-03", "COL-C2-X10-Y09-2F", 0.50, 0.151, 0.0),
    ("D-GF-06", "COL-C6-X08-Y04-GF", 0.25, 0.250, 0.010),
    ("W18", "COL-C8-X15-Y06-1F", 0.90, 0.400, 0.0),
])
def test_column_ends_by_hand(out, oid, cid, along, inside, beyond):
    e = [e for e in out["lintels"][oid]["ends"] if e["stopper"] == T.COLUMN and e["state"] == T.DEFICIT][0]
    assert e["host"]["id"] == cid and e["host"]["along_m"] == pytest.approx(along)
    assert e["host"]["covers_wall_width"] is True
    assert abs(e["host"]["gap_struct_frame_m"] - e["host"]["expected_gap_m"]) <= T.FRAME_TOL_M
    assert e["inside_column_m"] == pytest.approx(inside, abs=1e-9)
    assert e["not_built_m"] == pytest.approx(beyond, abs=1e-9)


def test_w18_span_strip_and_length(out):
    r = out["lintels"]["W18"]
    assert r["w_net_m"] == pytest.approx(0.4673) and r["length_hi_m"] == pytest.approx(0.8673)
    assert r["concrete_hi_m3"] == pytest.approx(0.034692) and r["span_strip_inside_column_m3"] == pytest.approx(0.001308)


@pytest.mark.parametrize("oid, hi_m3, lo_m3", [
    ("D-1F-03", 0.04914, 0.042), ("D-1F-04", 0.03837, 0.036), ("D-1F-07", 0.04377, 0.036),
    ("D-1F-10", 0.04377, 0.036), ("D-2F-03", 0.04347, 0.036), ("D-GF-06", 0.0616, 0.056), ("D-GF-10", 0.04359, 0.036),
])
def test_single_lintels_by_hand(out, oid, hi_m3, lo_m3):
    r = out["lintels"][oid]
    assert r["concrete_hi_m3"] == pytest.approx(hi_m3, abs=1e-9) and r["concrete_lo_m3"] == pytest.approx(lo_m3, abs=1e-9)


def test_pier_pair_by_hand(out):
    p = out["pairs"][0]
    assert p["pier_m"] == 0.238 and p["head_m"] == 2.2
    assert p["t453_overlap_m"] == pytest.approx(0.562) and p["lintel_on_lintel_m3"] == pytest.approx(0.01686)
    assert (p["length_lo_m"], p["length_hi_m"]) == (2.0, 2.638)
    assert p["concrete_hi_m3"] == pytest.approx(0.07914)


def test_set_totals_and_conservation(out):
    s = out["summary"]
    assert s["t453_m3"] == pytest.approx(0.514)
    assert s["corrected_hi_m3"] == pytest.approx(0.437542) and s["corrected_lo_m3"] == pytest.approx(0.372692)
    assert s["removed_m3"] == pytest.approx(0.076458)
    assert s["inside_column_m3"] == {"COL-C2-X10-Y09-2F": 0.00453, "COL-C6-X08-Y04-GF": 0.01,
                                     "COL-C8-X15-Y06-1F": 0.017308, "COL-PC-X08-Y02-1F": 0.006}
    assert s["inside_column_total_m3"] == pytest.approx(0.037838)
    assert s["lintel_on_lintel_m3"] == pytest.approx(0.01686) and s["not_built_m3"] == pytest.approx(0.02176)
    assert s["split_held"] == []
    assert s["t453_formwork_m2"] == pytest.approx(7.73)


def test_formwork_and_material_lists(out):
    s = out["summary"]
    # hi: sides 2 L D on the corrected lengths + soffits w_net B; T-453 7.73 m2
    assert s["formwork_hi_m2"] == pytest.approx(6.79638, abs=1e-6)
    assert s["end_stop_faces_max_m2"] == pytest.approx(4 * 0.03)        # four cross-wall ends, listed for T-474 only
    # host face over-deducted by T-453 at least D r per column / cross-wall end + D x 0.562 for the pair
    assert s["host_face_overdeduct_min_m2"] == pytest.approx(
        0.2 * (0.321 + 0.151 + 0.260 + 0.40 + 0.162 + 0.141 + 0.141 + 0.147) + 0.2 * 0.562)
