"""T-272 r2: a run is counted per drawn clear span between supporting faces, a beam that frames into it or crosses it
being a supporting face (Checker 2026-10-24 17:04: no link continues through a crossing ground beam unless a print
shows it); a curved run is split at its supports and counted on radial sweeps. Villa G hand fixture (synthetic, not
Alsenan) and adverse cases.

Villa G, sheet S-3 (invented): ground beam GB-G2, 0.30 wide, 6.00 m between column faces, links 'ø8/15cm', no end
rule printed. Ground beam GB-G7 (0.30 wide) frames into its side with its faces at 2.00 and 2.30 m from the left face.
Hand count, each clear span on its own (low = faces as end ties ceil(p/s) - 1, high = a link at each face ceil(p/s) + 1):
  2.00 / 0.15 = 13.33 -> 13 .. 15 (reading 14); 3.70 / 0.15 = 24.67 -> 24 .. 26 (reading 25)  => 37 .. 41 (reading 39).
  Through-run reading (links through GB-G7, NOT admissible without a print): 6.00 / 0.15 = 40 -> 39 .. 41.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t272"))
import t272_stirrups as S  # noqa: E402

S_ = 0.15


def test_villa_g_tee_splits_the_run():
    p = S.clear_pieces(6.00, [(2.00, 2.30)])
    assert p == [2.0, 3.7]
    env = S.pieces_envelope(p, S_)
    assert (env["low"], env["half_spacing_reading"], env["high"]) == (37, 39, 41)
    assert env["status"] == S.HELD and env["count"] is None
    through = S.count_envelope([(6.00, S_)])
    assert (through["low"], through["high"]) == (39, 41)
    assert env["low"] < through["low"]            # the r1 fault: a through-run low end is not a lower bound


def test_mirrored_tee_same_count():
    a = S.pieces_envelope(S.clear_pieces(6.00, [(2.00, 2.30)]), S_)
    b = S.pieces_envelope(S.clear_pieces(6.00, [(6.00 - 2.30, 6.00 - 2.00)]), S_)
    assert (a["low"], a["high"]) == (b["low"], b["high"])


def test_offset_tees_from_both_sides_leave_a_short_span():
    # GB-G7 from one side at 2.00 .. 2.30, GB-G8 from the other at 2.60 .. 2.90: a 0.30 m span between them
    p = S.clear_pieces(6.00, [(2.60, 2.90), (2.00, 2.30)])
    assert p == [2.0, 0.3, 3.1]
    env = S.pieces_envelope(p, S_)
    assert (env["low"], env["high"]) == (13 + 1 + 20, 15 + 3 + 22)


def test_overlapping_footprints_merge_oblique_tee():
    # an oblique beam (45 deg, 0.30 wide) whose drawn faces meet this face from 2.25 to 2.72: 0.30 / sin 45 = 0.424
    p = S.clear_pieces(6.00, [(2.00, 2.30), (2.25, 2.72)])
    assert p == [2.0, 3.28]
    env = S.pieces_envelope(p, S_)
    assert (env["low"], env["high"]) == (13 + 21, 15 + 23)


def test_footprint_outside_the_run_or_inverted_refused():
    for fp in ([(5.90, 6.20)], [(-0.10, 0.20)], [(2.30, 2.00)]):
        with pytest.raises(S.StirrupInputError):
            S.clear_pieces(6.00, fp)
    with pytest.raises(S.StirrupInputError):
        S.clear_pieces(0.0, [])
    with pytest.raises(S.StirrupInputError):
        S.pieces_envelope([], S_)


def test_no_tee_is_the_single_span():
    env = S.pieces_envelope(S.clear_pieces(6.00, []), S_)
    one = S.count_envelope([(6.00, S_)])
    assert (env["low"], env["high"]) == (one["low"], one["high"])


def test_ring_split_at_columns_radial_sweeps():
    # Villa G curved beam split by a column into two sweeps: inner / outer face arcs 3.05 / 3.66 and 1.52 / 1.82 m
    env = S.ring_envelope([{"inner_arc_m": 3.05, "outer_arc_m": 3.66}, {"inner_arc_m": 1.52, "outer_arc_m": 1.82}],
                          S_, face_pieces={"inner": [3.05, 1.70], "outer": [3.66, 1.82]})
    assert (env["low"], env["high"]) == (20 + 10, 26 + 14)
    assert env["status"] == S.HELD and env["count"] is None
    # the face reading is reported beside, never the envelope
    assert env["face_reading"]["inner"] == [20 + 11, 22 + 13]
    one = S.curved_count_envelope(1.0, 2.0, 2.4, S_)        # unsplit reading differs: splitting is not optional
    assert "split" not in one["basis"]


def test_ring_bad_sweeps_refused():
    with pytest.raises(S.StirrupInputError):
        S.ring_envelope([], S_)
    with pytest.raises(S.StirrupInputError):
        S.ring_envelope([{"inner_arc_m": 2.0, "outer_arc_m": 1.9}], S_)


def test_units_cm_input_refused_as_metres():
    # a footprint typed in cm (200 .. 230) on a 6.00 m run is outside the run: refused, never silently scaled
    with pytest.raises(S.StirrupInputError):
        S.clear_pieces(6.00, [(200, 230)])
