"""engine/source/lintel_qto.py - synthetic known answers only (no project data)."""

from __future__ import annotations

import math

import pytest

from engine.source import lintel_qto as LQ

ROWS = [{"row_id": "A", "lo": 0, "hi": 100}, {"row_id": "B", "lo": 101, "hi": 200},
        {"row_id": "C", "lo": 201, "hi": 300}]


def test_parse_printed_cells():
    assert LQ.parse_width_range("0 -100") == (0, 100) and LQ.parse_width_range("101 - 200") == (101, 200)
    assert LQ.parse_section("B x 20") == ("B", 20.0) and LQ.parse_section("B X 55") == ("B", 55.0)
    assert LQ.parse_bars("2Ø12") == (2, 12) and LQ.parse_bars("3Ø14") == (3, 14)
    assert LQ.parse_rate("5Ø8/M") == (5, 8)
    for bad, f in (("100-0", LQ.parse_width_range), ("Bx", LQ.parse_section), ("0Ø12", LQ.parse_bars),
                   ("5Ø8", LQ.parse_rate)):
        with pytest.raises(LQ.LintelQtoError):
            f(bad)


def test_schedule_gaps_and_overlap_refused():
    c = LQ.check_schedule(ROWS)
    assert c["gaps"] == [(100, 101, "A", "B"), (200, 201, "B", "C")] and c["above"] == 300
    with pytest.raises(LQ.LintelQtoError):
        LQ.check_schedule([{"row_id": "A", "lo": 0, "hi": 100}, {"row_id": "B", "lo": 100, "hi": 200}])


@pytest.mark.parametrize("w,exp", [(1000.0, "A"), (999.99, "A"), (1000.5, LQ.BOUNDARY_GAP), (1009.99, LQ.BOUNDARY_GAP),
                                   (1010.0, "B"), (2000.0, "B"), (2005.0, LQ.BOUNDARY_GAP), (3000.0, "C"),
                                   (3000.1, LQ.ABOVE_SCHEDULE), (0.0, LQ.NOT_POSITIVE), (-5.0, LQ.NOT_POSITIVE)])
def test_row_for_width_exact_boundaries(w, exp):
    st, r = LQ.row_for_width(ROWS, w)
    assert (r["row_id"] if st == LQ.IN_ROW else st) == exp
    if st == LQ.BOUNDARY_GAP:
        assert len(r) == 2


def test_no_width_meets_two_rows():
    for w10 in range(1, 3200):
        w = w10 / 1.0
        hits = [r for r in ROWS if r["lo"] <= w / 10 <= r["hi"]]
        assert len(hits) <= 1


def test_lintel_extent_bearing_frame_and_deficit():
    e = LQ.lintel_extent(1000, 1900, LQ.MASONRY, LQ.MASONRY, 400, 1000, 600)
    assert (e["t0"], e["t1"], e["length"], e["flags"]) == (600, 2300, 1700, [])
    e = LQ.lintel_extent(1000, 1900, LQ.MASONRY, LQ.FRAME, 400, 224, None)
    assert (e["bearing_start"], e["bearing_end"], e["length"]) == (224, 0, 1124)
    assert e["flags"] == ["BEARING_DEFICIT:start"]
    with pytest.raises(LQ.LintelQtoError):
        LQ.lintel_extent(1000, 1900, LQ.MASONRY, LQ.MASONRY, 400)
    with pytest.raises(LQ.LintelQtoError):
        LQ.lintel_extent(1900, 1000, LQ.FRAME, LQ.FRAME, 400)


def test_resolve_overlaps_cuts_at_pier_middle():
    ls = [{"id": "a", "line": "L", "s0": 0, "s1": 1000, "t0": -400, "t1": 1400},
          {"id": "b", "line": "L", "s0": 1500, "s1": 2500, "t0": 1100, "t1": 2900},
          {"id": "c", "line": "M", "s0": 0, "s1": 1000, "t0": -400, "t1": 1400}]
    new, cuts = LQ.resolve_overlaps(ls)
    assert new["a"]["t1"] == new["b"]["t0"] == 1250 and new["c"]["t1"] == 1400
    assert cuts == [{"line": "L", "a": "a", "b": "b", "pier": 500, "cut_at": 1250}]
    assert new["a"]["length"] + new["b"]["length"] == 2900 + 400 - 0


def test_strip_relation():
    s = {"s0": 0, "s1": 1000, "o0": 0, "o1": 200}
    assert LQ.strip_relation(s, {"s0": -100, "s1": 1100, "o0": 0, "o1": 200})["relation"] == LQ.FULL
    assert LQ.strip_relation(s, {"s0": 0, "s1": 400, "o0": 0, "o1": 200})["relation"] == LQ.PARTIAL
    assert LQ.strip_relation(s, {"s0": 0, "s1": 1000, "o0": 150, "o1": 400})["relation"] == LQ.PARTIAL
    assert LQ.strip_relation(s, {"s0": 2000, "s1": 3000, "o0": 0, "o1": 200})["relation"] == LQ.NONE


def test_bar_lengths_and_counts():
    assert LQ.straight_bar_mm(1600, 25) == 1550
    assert LQ.stirrup_core_path_mm(150, 200, 25, 8) == 2 * 92 + 2 * 142
    assert LQ.rate_count(5, 1600) == 8 and LQ.rate_count(5, 1601) == 9 and LQ.rate_count(5, 2000) == 10
    assert LQ.spacing_count(1600, 5) == 9
    with pytest.raises(LQ.LintelQtoError):
        LQ.stirrup_core_path_mm(50, 200, 25, 8)
    with pytest.raises(LQ.LintelQtoError):
        LQ.straight_bar_mm(40, 25)


def test_known_lintel_by_hand():
    """800 mm door in a 150 mm wall, row 0-100: B x 20, 2Ø12 / 2Ø10, 5Ø8/M, 400 mm bearing each side."""
    e = LQ.lintel_extent(0, 800, LQ.MASONRY, LQ.MASONRY, 400, 2000, 2000)
    L = e["length"]
    assert L == 1600 and 150 * 200 * L / 1e9 == pytest.approx(0.048)
    kg = (2 * LQ.straight_bar_mm(L, 25) * 144 + 2 * LQ.straight_bar_mm(L, 25) * 100 +
          LQ.rate_count(5, L) * LQ.stirrup_core_path_mm(150, 200, 25, 8) * 64) / 162 / 1000
    assert kg == pytest.approx(3.1 * 144 / 162 + 3.1 * 100 / 162 + 8 * 0.468 * 64 / 162)
    assert math.isclose(kg, 6.148, abs_tol=0.001)
