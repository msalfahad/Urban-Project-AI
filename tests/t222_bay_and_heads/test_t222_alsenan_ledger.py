"""T-222 development-villa ledger (research/agents_t222/T222_RESULTS.csv, READINGS_T222.csv): internal consistency
only; the numbers are re-made from the private drawings by `alsenan_t222.py --check` outside the test run."""
import csv
import re
from pathlib import Path

import pytest

D = Path(__file__).resolve().parents[2] / "research" / "agents_t222"
HELD_BOUND_M = 0.4769          # T-108 r2: 1F bay basis 0 .. 0.4769 m on 1F-W25 (0 .. 1.645 m2), never added
HELD_BOUND_M2 = 1.645


def rows():
    with open(D / "T222_RESULTS.csv", newline="") as f:
        return {(r["item"], r["quantity"]): r["value"] for r in csv.DictReader(f)}


def v(r, item, q):
    return float(r[(item, q)])


def test_bay_closed_inside_the_held_bound_and_nothing_unassigned():
    r = rows()
    assert v(r, "bay", "unassigned masonry (m2)") == 0.0
    group_m = v(r, "bay", "1F-W25 change (m)") + v(r, "bay", "1F-W00/W01 change (m)")
    assert 0 < group_m <= HELD_BOUND_M                      # a held bound closed, not new length beyond it
    # the m2 may exceed the 3.45 m bound only by the slab-height part (4.04 under the slab, not 3.45 under CB12)
    assert v(r, "bay", "1F-W25 change (m2)") + v(r, "bay", "1F-W00/W01 change (m2)") <= group_m * 4.04 + 1e-3
    # stub already established stays established (counted once)
    assert v(r, "bay", "1F-W25 physical length incl. stub (m)") == pytest.approx(
        v(r, "bay", "1F-W25 stub already established (m)") + v(r, "bay", "1F-W25 change (m)"), abs=2e-4)


def test_glazing_basis_is_the_drawn_arc_not_the_centreline_meeting():
    r = rows()
    # the hand row's drawn glazing arc 3.136 m; V2's 3.579 m (mid circle carried to the centrelines) is not it
    assert v(r, "bay", "glazing on the band mid circle between the caps (m)") == pytest.approx(3.136, abs=0.005)


def test_heights_from_members_drawn():
    r = rows()
    assert v(r, "bay", "CB12 band width (m)") == 0.25
    assert v(r, "bay", "ST translation votes (1F columns)") == 20
    assert v(r, "P-GF-05", "ST translation votes (GF columns)") == 30


def test_pgf05_value_from_b1_and_structural_top():
    r = rows()
    assert v(r, "P-GF-05", "B1 soffit (m)") == pytest.approx(5.45 - 0.40)
    assert v(r, "P-GF-05", "masonry above the lintel (m2)") == pytest.approx(1.20 * (5.05 - 2.65 - 0.20))
    assert v(r, "P-GF-05", "opening centre offset from the B1 band axis (m)") <= 0.01
    # the elevation's +4.70 line is an occluding band in front: never the top (it would give 2.220 m2)
    assert v(r, "P-GF-05", "masonry above the lintel (m2)") != pytest.approx(1.20 * (4.70 - 2.85))


def test_p1f01_occluded_not_conflict_and_held_never_zero():
    r = rows()
    assert r[("P-1F-01", "B-B evidence for P-1F-01")] == "OCCLUDED"
    assert "OP-006" in r[("P-1F-01", "B-B elements in front")]
    assert r[("P-1F-01", "masonry above the lintel")].startswith("HELD 0.0 .. ")
    assert float(r[("P-1F-01", "masonry above the lintel")].split()[-1]) == pytest.approx(4.992)


def test_no_coordinates_or_client_data_in_the_files():
    for name in ("T222_RESULTS.csv", "READINGS_T222.csv"):
        txt = (D / name).read_text()
        assert not re.search(r"-?\d{5,}\.\d+|-?\d{6,}", txt), name   # no drawing coordinates
        assert "IBRAHIM" not in txt.upper() and "FATEMAH" not in txt.upper()
