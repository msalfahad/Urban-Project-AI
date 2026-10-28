"""T-316 hand fixture, villa V316 (invented, NOT Alsenan): a two-span suspended slab, clear spans S1 = 4.00 m and
S2 = 5.00 m (bar direction), on three beams B1 (edge, 0.25 m), B2 (internal, 0.20 m) and B3 (0.25 m) with a 1.20 m
cantilever C beyond B3; panel width 3.00 m across the bars; top bars 5 o 10/m (u = 100 / 162 kg/m).

Hand calculation (p.15 typical detail):
  count A = ceil(5 x 3.00) = 15 bars, B = 16.
  B1 group (edge beam, S1 side):  0.25 x 4.00 = 1.000 in span + across B1 [0.25 - 0.040, 0.25] = [1.210, 1.250] m/bar
  B2 group (continuous):          0.30 x max(4.00, 5.00) = 1.500 each side + 0.20 over the band = 3.200 m/bar
  B3 group (edge, S2 side):       0.25 x 5.00 = 1.250 + [0.210, 0.250] = [1.460, 1.500] m/bar; cantilever beyond:
                                  'EXTEND 50 % ... WHERE POSSIBLE' UNRESOLVED; the cantilever's own top steel HELD.
  kg: B1 15 x 1.210 x u = 11.203704 .. 16 x 1.250 x u = 12.345679; B2 15 x 3.2 x u = 29.629630 .. 16 x 3.2 x u =
      31.604938; B3 15 x 1.46 x u = 13.518519 .. 16 x 1.50 x u = 14.814815.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t316"))
import t316_top_bars as tb  # noqa: E402

U = 100.0 / 162.0
NA, NB = 15, 16


def ends_v316():
    return {
        "B1": [tb.end_record("EDGE_BEAM", 4.0, w=0.25, beyond="NONE")],
        "B2": [tb.end_record("CONTINUOUS", 4.0, w=0.20, l_other=5.0),
               tb.end_record("CONTINUOUS", 5.0, w=0.20, l_other=4.0)],
        "B3": [tb.end_record("EDGE_BEAM", 5.0, w=0.25, beyond="CANTILEVER")],
    }


def per_bar(recs):
    lo = sum(r["in_panel"] + r["over_band"] + r["across"][0] for r in recs)
    hi = sum(r["in_panel"] + r["over_band"] + r["across"][1] for r in recs)
    return lo, hi


def test_group_lengths_by_hand():
    e = ends_v316()
    assert per_bar(e["B1"]) == pytest.approx((1.21, 1.25))
    assert per_bar(e["B2"]) == pytest.approx((3.2, 3.2))
    assert per_bar(e["B3"]) == pytest.approx((1.46, 1.50))
    assert e["B1"][0]["held"] == ["HOOK_DOWN_LEG"] and e["B1"][0]["unresolved"] == []
    assert e["B3"][0]["unresolved"] == ["EXTEND_50PCT_INTO_ADJACENT_SLAB"]
    assert all(r["status"] == "DRAWING_DERIVED" for r in e["B2"])


def test_group_kg_by_hand():
    e = ends_v316()
    for g, (lo, hi) in {"B1": (11.203704, 12.345679), "B2": (29.629630, 31.604938),
                        "B3": (13.518519, 14.814815)}.items():
        a, b = per_bar(e[g])
        assert NA * a * U == pytest.approx(lo, abs=1e-6)
        assert NB * b * U == pytest.approx(hi, abs=1e-6)
    assert tb.tonnes(NB * 3.2 * U) == pytest.approx(0.031604938, abs=1e-9)


def test_note2_readings_kept_apart():
    r = tb.end_record("CONTINUOUS", 4.0, w=0.20, l_other=5.0)
    assert r["note2_i"] == pytest.approx(4.0 / 6) and r["note2_ii"] == pytest.approx(4.0 / 3)
    assert r["in_panel"] == pytest.approx(1.5)          # p.15, never the note value


def test_cantilever_root_held():
    r = tb.end_record("CANTILEVER_ROOT", 1.2)
    assert r["status"] == "HELD" and r["in_panel"] is None and r["held"] == ["CANTILEVER_ROOT"]


def test_held_classes_never_zero():
    for c in ("STEP_EDGE", "IRREGULAR_SUPPORT", "OPENING_EDGE"):
        r = tb.end_record(c, 4.0, w=0.2)
        assert r["status"] == "HELD" and r["in_panel"] is None


def test_mirror_invariant():
    a = tb.span_overlap(4.0, 1.0, 1.5)
    b = tb.span_overlap(4.0, 1.5, 1.0)
    assert a == b and not a["overlap"]


def test_short_span_overlap_bound():
    # a 1.20 m span between a continuous support (other span 5.00) and an edge beam: 1.50 + 0.30 > 1.20
    a = tb.p15_extent("CONTINUOUS", 1.2, 5.0)
    b = tb.p15_extent("EDGE_BEAM", 1.2)
    ov = tb.span_overlap(1.2, a, b)
    assert ov["overlap"]
    assert a + b - ov["cut_low"] == pytest.approx(1.2)      # one through bar
    assert a + b - ov["cut_high"] == pytest.approx(1.5)     # two bars, each within the span
    one = tb.span_overlap(1.2, a, None)                     # other side HELD: valued side limited to the span
    assert a - one["cut_low"] == pytest.approx(1.2)


# ------------------------------------------------------------------------------------------------ adverse
def test_shorter_span_refused():
    with pytest.raises(ValueError, match="SHORTER_SPAN_REFUSED"):
        tb.p15_extent("CONTINUOUS", 5.0, 4.0, l_used=4.0)
    assert tb.p15_extent("CONTINUOUS", 5.0, 4.0, l_used=5.0) == pytest.approx(1.5)


def test_own_span_substituted_refused():
    with pytest.raises(ValueError, match="OWN_SPAN_SUBSTITUTED_REFUSED"):
        tb.p15_extent("CONTINUOUS", 4.0, None, l_used=4.0)
    r = tb.end_record("CONTINUOUS", 4.0, w=0.2, l_other=None)
    assert r["status"] == "HELD" and "OTHER_SPAN_UNKNOWN" in r["held"]


def test_edge_span_must_be_own():
    with pytest.raises(ValueError, match="WRONG_SPAN_REFUSED"):
        tb.p15_extent("EDGE_BEAM", 4.0, l_used=5.0)


def test_note_length_on_drawn_bar_refused():
    with pytest.raises(ValueError, match="NOTE_LENGTH_ON_DRAWN_BAR_REFUSED"):
        tb.end_record("CONTINUOUS", 4.0, w=0.2, l_other=5.0, drawn_length_m=2.4, offered_basis="NOTE2")
    r = tb.end_record("CONTINUOUS", 4.0, w=0.2, l_other=5.0, drawn_length_m=2.4)
    assert r["status"] == "DRAWN_BAR" and r["in_panel"] == 2.4


def test_undimensioned_leg_value_refused():
    with pytest.raises(ValueError, match="HOOK_LEG_VALUE_REFUSED"):
        tb.end_record("EDGE_BEAM", 4.0, w=0.25, hook_leg_m=0.12)


def test_group_both_sides_refused():
    ok = [dict(group="x|S1+S2", panel="S1", side_key=("A", 0, 0, "hi")),
          dict(group="x|S1+S2", panel="S2", side_key=("A", 0, 0, "lo"))]
    assert tb.check_groups(ok) == {"x|S1+S2": ["S1", "S2"]}
    with pytest.raises(ValueError, match="GROUP_BOTH_SIDES_REFUSED"):
        tb.check_groups([dict(group="x|S1+S2", panel="S1", side_key=("A", 0, 0, "hi"), books="BOTH")])
    with pytest.raises(ValueError, match="GROUP_SIDE_TWICE_REFUSED"):
        tb.check_groups(ok + [dict(group="x|S1+S2", panel="S1", side_key=("A", 0, 0, "hi"))])
    with pytest.raises(ValueError, match="GROUP_MORE_THAN_TWO_SIDES_REFUSED"):
        tb.check_groups(ok + [dict(group="x|S1+S2", panel="S3", side_key=("A", 0, 0, "lo"))])


def test_mm_refused():
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        tb.end_record("EDGE_BEAM", 4000.0, w=250.0)
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        tb.p15_extent("CONTINUOUS", 4.0, 5000.0)


def test_unknown_class_refused():
    with pytest.raises(ValueError, match="SUPPORT_CLASS_REFUSED"):
        tb.end_record("WALL", 4.0)
    with pytest.raises(ValueError, match="HELD_CLASS_EXTENT_REFUSED"):
        tb.p15_extent("STEP_EDGE", 4.0, l_used=4.0)


def test_cause_split_closes_and_wrong_figure_refused():
    # one S1 x-line with the T-152 booking: 15 bars at A, 16 at B; lo end B1 edge, hi end B2 continuous
    def line(n):
        out = []
        for _ in range(n):
            out.append(("EDGE_BEAM", tb.t152_end(4.0, False, None, None)))
            out.append(("CONTINUOUS", tb.t152_end(4.0, True, 0.20, 5.0)))
        return out
    eA, eB = line(NA), line(NB)
    lo, hi, ct = tb.line_path(eA, eB)
    # per bar: i 2 x 4/6 = 1.333, ii 2 x 4/3 = 2.667, p15 0.25 x 4 + 0.30 x 5 = 2.500 -> low i, high ii
    assert (lo, hi, ct) == ("i", "ii", "B")
    sp = tb.split_causes(eA, eB, lo, hi, ct)
    # by hand: i -> ii at A: 15 x 2 x 4/6 = 20.0 m; count: 1 bar x 2.667 m; crossing 16 x 0.10 m
    fig = {"TOP_NOTE2_WORDING": 20.0 * U, "COUNT_CONVENTION": 8.0 / 3 * U, "TOP_CROSSING": 1.6 * U}
    res = tb.close_line("V316", fig, sp, U)
    assert all(abs(v) < 1e-9 for v in res.values())
    assert sp["TOP_NOTE2_WORDING"]["EDGE_BEAM"] == pytest.approx(10.0)
    assert sp["TOP_CROSSING"].get("EDGE_BEAM", 0.0) == 0.0
    bad = dict(fig, TOP_CROSSING=fig["TOP_CROSSING"] + 0.01)
    with pytest.raises(ValueError, match="unexplained"):
        tb.close_line("V316", bad, sp, U)
