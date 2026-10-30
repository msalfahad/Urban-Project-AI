"""T-355 generic rules on a NON-Alsenan hand fixture (normal and adverse cases).

Fixture (hand calculation): one black-block wall run 6.00 m between two 0.30 m columns (COLUMN 0.30 | BLOCK 5.40 |
COLUMN 0.30), block top 3.00 m above the structural floor (a 0.60 m beam under a 3.60 m storey). Course: 0.190 block +
0.010 joint = 0.200 module. Levels = joints over courses 3, 6, 9, 12: 0.60, 1.20, 1.80, 2.40 (2.40 + 0.01 < 3.00);
3.00 is the block top itself (no course above): not a level. One door 0.90 wide, hole 0.00 .. 2.20, lintel 0.25 deep
(2.20 .. 2.45), bearing 0.40 each end.
  level 0.60 / 1.20 / 1.80: 5.40 - 0.90 = 4.50 m each       = 13.50
  level 2.40: lintel span cut 0.90, bearings 2 x 0.40 HELD  = 3.70 net, 0.80 held
  net strip 17.20 m.l, held 0.80 m.l; junctions 2 (one each column), ties 2 x 4 = 8 pcs.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t355"))
import t355_masonry_accessories as X  # noqa: E402

C = X.course_spec(0.190, 0.010, "fixture: block 190 + joint 10", "ASSUMED — OWNER-APPROVED")


def wall(pieces=None, openings=None, course=C, held=""):
    if pieces is None:
        pieces = [X.make_piece("COLUMN", 0.30, None, "R1@0.000"), X.make_piece("BLOCK", 5.40, 3.00, "R1@b1"),
                  X.make_piece("COLUMN", 0.30, None, "R1@5.700")]
    if openings is None:
        openings = [X.make_opening("D1", 0.90, 0.0, 2.20, 0.25, 0.40)]
    return X.Panel("FX-W1", "FX", tuple(pieces), tuple(openings), course, held)


def net(p):
    recs, st = X.mesh_levels(p)
    return round(sum(r["net_m"] for r in recs), 6), round(sum(r["held_m"] for r in recs), 6), recs, st


def test_levels_are_integer_courses():
    assert [z for _, z, _ in X.levels(C, 3.00)] == [0.6, 1.2, 1.8, 2.4]
    assert X.levels(C, 3.00)[-1][2] == 0.19                      # full course above the last level


def test_hand_fixture_strip_and_ties():
    n, h, recs, st = net(wall())
    assert st == "MEASURED"
    assert [r["net_m"] for r in recs] == [4.5, 4.5, 4.5, 3.7]
    assert (n, h) == (17.2, 0.8)
    assert recs[3]["cut_lintel_m"] == 0.9 and recs[3]["held"][0][0] == "LINTEL_BEARING"
    t = X.ties(wall())
    assert len(t) == 2 and sum(x["ties"] for x in t) == 8
    assert {x["face"] for x in t} == {"column_start", "column_end"}


def test_mirror_and_mm_identical():
    p = wall()
    m = X.Panel(p.wall_id, p.floor, tuple(reversed(p.pieces)), p.openings, C)
    assert net(m)[:2] == net(p)[:2]
    assert sum(x["ties"] for x in X.ties(m)) == 8
    mm = wall(pieces=[X.make_piece("COLUMN", 300, None, "R1@0", units="mm"),
                      X.make_piece("BLOCK", 5400, 3000, "R1@b1", units="mm"),
                      X.make_piece("COLUMN", 300, None, "R1@5700", units="mm")],
              openings=[X.make_opening("D1", 900, 0, 2200, 250, 400, units="mm")],
              course=X.course_spec(190, 10, "fixture", "ASSUMED — OWNER-APPROVED", units="mm"))
    assert net(mm)[:2] == (17.2, 0.8)


def test_units_guard():
    with pytest.raises(X.AccessoryError):
        X.course_spec(190, 10, "mm read as m", "x")              # 190 m block refused
    with pytest.raises(X.AccessoryError):
        X.make_piece("BLOCK", 5.4, 3000)                         # a 3000 m block top refused
    with pytest.raises(X.AccessoryError):
        X.course_spec(0.19, 0.01, "", "x")                       # no source, no default


def test_wall_lower_than_three_courses_has_no_level():
    p = wall(pieces=[X.make_piece("BLOCK", 2.0, 0.60, "R1@b0")], openings=[])
    n, h, recs, st = net(p)
    assert recs == [] and st.startswith("NO LEVEL")


def test_wall_between_two_columns_two_ends():
    assert len(X.junctions(wall())) == 2


def test_wall_through_a_column_two_junctions_there():
    p = wall(pieces=[X.make_piece("BLOCK", 2.0, 3.0, "R1@b0"), X.make_piece("COLUMN", 0.3, None, "R1@2.000"),
                     X.make_piece("BLOCK", 2.0, 3.0, "R1@b2")], openings=[])
    j = X.junctions(p)
    assert len(j) == 2 and {x["column_at"] for x in j} == {"R1@2.000"}


def test_duplicate_junction_refused():
    c = X.make_piece("COLUMN", 0.3, None, "R1@2.000")
    p = wall(pieces=[X.make_piece("BLOCK", 1.0, 3.0, "R1@b0"), c, X.make_piece("BLOCK", 1.0, 3.0, "R1@b2"), c,
                     X.make_piece("BLOCK", 1.0, 3.0, "R1@b4")], openings=[])
    with pytest.raises(X.AccessoryError):
        X.junctions(p)


def test_unknown_height_held_never_zero():
    p = wall(pieces=[X.make_piece("COLUMN", 0.3, None, "R1@0"), X.make_piece("BLOCK", 5.4, None, "R1@b1")],
             openings=[])
    recs, st = X.mesh_levels(p)
    assert recs == [] and st.startswith("HELD")
    t = X.ties(p)
    assert t[0]["state"] == "HELD" and t[0]["ties"] is None
    X.no_zero_held(t)
    with pytest.raises(X.AccessoryError):
        X.no_zero_held([{"wall_id": "x", "state": "HELD", "ties": 0}])


def test_no_course_spec_held_by_name():
    p = wall(course=None)
    recs, st = X.mesh_levels(p)
    assert recs == [] and "course height not established" in st
    assert all(x["ties"] is None and x["state"] == "HELD" for x in X.ties(p))


def test_mesh_into_block_m2_refused():
    with pytest.raises(X.AccessoryError):
        X.check_separate(32.4, {"m": 17.2, "added_to": "block_m2"}, 8, None)
    assert X.check_separate(32.4, 17.2, 8, None) == 32.4


def test_window_below_sill_runs_through_and_cut_above():
    p = wall(openings=[X.make_opening("W1", 1.20, 1.00, 2.20, 0.20, 0.40)])
    n, h, recs, st = net(p)
    # 0.60 under the sill: 5.40; 1.20 / 1.80: 4.20; 2.40: over the lintel (2.20 .. 2.40 ends at the joint): 5.40
    assert [r["net_m"] for r in recs] == [5.4, 4.2, 4.2, 5.4] and h == 0.0


def test_opening_extent_unknown_holds_only_its_segment():
    p = wall(openings=[X.make_opening("W9", 1.00, None, None, None, 0.40)])
    n, h, recs, st = net(p)
    assert all(r["held_m"] == 1.8 and r["net_m"] == 3.6 for r in recs)   # 1.00 + 2 x 0.40 held, never cut, never 0


def test_lintel_unknown_holds_span_and_bearings_above_head():
    p = wall(openings=[X.make_opening("D2", 0.90, 0.0, 2.20, None, 0.40)])
    n, h, recs, st = net(p)
    assert recs[3]["held"][0][0] == "LINTEL_UNKNOWN" and recs[3]["net_m"] == 3.7


def test_opening_beside_unknown_piece_is_held_not_cut():
    p = wall(pieces=[X.make_piece("BLOCK", 3.0, 3.0, "R1@b0"), X.make_piece("BLOCK", 2.0, None, "R1@b1")])
    recs, st = X.mesh_levels(p)
    r = recs[0]
    assert r["cut_opening_m"] == 0.0 and r["net_m"] == 2.1 and r["held_m"] == 2.9    # 2.0 unknown + 0.9 position


def test_cut_wider_than_block_refused():
    p = wall(pieces=[X.make_piece("BLOCK", 0.5, 3.0, "R1@b0")], openings=[X.make_opening("D1", 0.9, 0.0, 2.2, 0.25, 0.4)])
    with pytest.raises(X.AccessoryError):
        X.mesh_levels(p)


def test_partial_top_course_reported():
    p = wall(pieces=[X.make_piece("BLOCK", 2.0, 3.10, "R1@b0")], openings=[])
    recs, _ = X.mesh_levels(p)
    assert recs[-1]["level_m"] == 3.0 and recs[-1]["partial_above"] and recs[-1]["course_above_h_m"] == 0.09


def test_module_changes_level_count():
    alt = X.course_spec(0.200, 0.010, "fixture 210", "x")
    assert X.n_levels(C, 3.75) == 6 and X.n_levels(alt, 3.75) == 5


def test_face_classes():
    assert X.face_class({"PLASTER"}) == "A" and X.face_class({"TILE"}) == "B"
    assert X.face_class({"SIGMA"}) == "C" and X.face_class({"NONE"}) == "D"
    assert X.face_class({"PLASTER", "TILE"}) == "MIXED" and X.face_class(set()) == "UNKNOWN"
    with pytest.raises(X.AccessoryError):
        X.face_class({"PAINT?"})


def test_lintel_schedule_bands():
    sch = [(0, 100, 0.20), (101, 200, 0.20), (201, 300, 0.30), (301, 500, 0.40), (501, 750, 0.55)]
    assert X.lintel_depth(1.00, sch) == 0.20 and X.lintel_depth(2.45, sch) == 0.30
    assert X.lintel_depth(1.005, sch) is None and X.lintel_depth(8.0, sch) is None


# r2 (Checker D-T355-1, 2026-10-30): a known lintel top below the level never holds the opening width (R-T355-6).
# Hand fixture: two block pieces of different tops, 3.00 x 3.00 m (under a beam) and 2.40 x 4.40 m (under the slab);
# door 0.90, head 2.20, lintel 0.25 (top 2.45), bearings 0.40. Levels from the highest top 4.40: 0.6 .. 4.2 (7).
#   0.60 / 1.20 / 1.80: the door's station is not tied to a piece, but below the lowest top 3.00 both pieces stand:
#                       5.40 - 0.90 = 4.50 each; 2.40: span cut 0.90, bearings 0.80 held, 3.70 net
#   3.00 / 3.60 / 4.20: only the 2.40 piece stands (3.01 > 3.00); above the lintel (2.45 < 3.00) the masonry is
#                       continuous wherever it exists: net 2.40 each, 0 held (r1 held 0.90 each, wrongly)
TWO_TOP = [X.make_piece("BLOCK", 3.0, 3.00, "R1@b0"), X.make_piece("BLOCK", 2.4, 4.40, "R1@b1")]


def test_r2_level_above_known_lintel_is_full_gross_on_a_two_top_wall():
    p = wall(pieces=TWO_TOP, openings=[X.make_opening("D1", 0.90, 0.0, 2.20, 0.25, 0.40)])
    n, h, recs, st = net(p)
    assert [r["level_m"] for r in recs] == [0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2]
    assert [r["net_m"] for r in recs] == [4.5, 4.5, 4.5, 3.7, 2.4, 2.4, 2.4]
    assert all(r["held_m"] == 0.0 and r["held"] == [] for r in recs[4:])
    assert (n, h) == (24.4, 0.8)


def test_r2_adverse_lintel_depth_unknown_still_holds_on_a_two_top_wall():
    p = wall(pieces=TWO_TOP, openings=[X.make_opening("D1", 0.90, 0.0, 2.20, None, 0.40)])
    recs, st = X.mesh_levels(p)
    r = {x["level_m"]: x for x in recs}
    assert r[3.0]["held_m"] == 0.9 and r[3.0]["net_m"] == 1.5 and r[3.0]["held"][0][0] == "POSITION_UNKNOWN"
    assert r[2.4]["held"][0][0] == "LINTEL_UNKNOWN"


def test_r2_partial_course_judged_per_piece():
    # GF-W01-like: tops 3.75 (beam) and 4.10 (slab); level 3.60: 0.14 above the 3.75 piece (partial), 0.49 -> 0.19
    # above the 4.10 piece (full). r1 reported 0.19, not partial.
    p = wall(pieces=[X.make_piece("BLOCK", 1.1, 3.75, "R1@b0"), X.make_piece("BLOCK", 0.5, 4.10, "R1@b1")],
             openings=[])
    recs, _ = X.mesh_levels(p)
    top = recs[-1]
    assert top["level_m"] == 3.6 and top["partial_above"] and top["course_above_h_m"] == 0.14
    assert top["partial_above_m"] == 1.1 and top["net_m"] == 1.6           # flag only: the strip is not reduced
    assert not recs[-2]["partial_above"] and recs[-2]["partial_above_m"] == 0.0
