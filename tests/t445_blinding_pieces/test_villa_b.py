"""T-445 BLINDING_PIECE_LEDGER_V1 on a hand-calculated villa B (not the development villa): three pit footings and
a lift raft on a 20.00 x 12.00 plot, blinding t = 0.10 printed, typical projection p = 0.10 printed for the pits,
no projection printed on the raft's own detail.

Hand calculation (m2 / m3):
  P2 2.00 x 1.50, H 0.40 -> grown 2.20 x 1.70 = 3.74 -> 0.374
  P4 1.00 x 1.00, H 0.30, 0.10 clear of P2 -> grown 1.20 x 1.20 = 1.44; overlap with P2's grown 0.10 x 1.20 = 0.12
     belongs to the deeper P2 -> own 1.32 -> 0.132
  P3 1.50 x 1.00 on the plot line x = 0 -> grown 1.70 x 1.20 = 2.04; beyond the line 0.10 x 1.20 = 0.12 -> inside
     1.92 -> 0.192, beyond HELD 0 .. 0.012
  pits inside 3.74 + 1.32 + 1.92 = 6.98 m2 -> 0.698 m3 (= union 7.10 - 0.12 beyond)
  raft R 4.00 x 3.00: HELD, AT_LEAST 12.00 x 0.10 = 1.200; readings p 0.10 (inherited) 4.20 x 3.20 x 0.10 = 1.344,
     p 0.15 (scaled) 4.30 x 3.30 x 0.10 = 1.419
  candidate-like line: union 7.10 x 0.10 + raft at 0.10 = 0.710 + 1.344 = 2.054
  reference plate 20.00 x 12.00 x 0.10 = 24.000; residual (nothing valued) -24.000 = -0.374 - 0.132 - 0.192
     - [1.344 .. 1.419] + RULE_DIFFERENCE [-21.958 .. -21.883]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t445"))
import blinding_piece_ledger_v1 as B  # noqa: E402

PLOT = [(0, 0), (20, 0), (20, 12), (0, 12)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


PITS = [{"id": "P2", "outline": rect(5, 2, 7, 3.5), "depth_m": 0.40},
        {"id": "P4", "outline": rect(7.1, 2, 8.1, 3), "depth_m": 0.30},
        {"id": "P3", "outline": rect(0, 5, 1.5, 6), "depth_m": 0.30}]
LINE = "L-VB-FOOT"


def spec(pr, **over):
    s = {"thickness": {"value": 0.10, "basis": B.PRINTED, "source": "villa B detail 1"},
         "projection": {"value": 0.10, "basis": B.PRINTED, "source": "villa B typical footing detail"},
         "measured": [{"id": k, "element": f"pit {k}", "line": LINE, "inside_m2": pr[k]["inside_m2"],
                       "outside_m2": pr[k]["outside_m2"], "source": "plan", "verdict": "checker V-1"}
                      for k in ("P2", "P4", "P3")],
         "beyond_boundary": {"line": LINE, "blocker": "RFI plot-line projection"},
         "held_projection": [{"id": "R", "element": "raft", "line": LINE, "outline_m2": 12.0, "basis": B.INHERITED,
                              "readings": {"p10": 0.10, "p15": 0.15},
                              "plan_fn": lambda p: (4 + 2 * p) * (3 + 2 * p), "blocker": "RFI raft projection"}]}
    s.update(over)
    return s


@pytest.fixture
def pr():
    return B.plan_from_geometry(PITS, PLOT, "m", 0.10)


def test_hand_areas(pr):
    assert pr["P2"]["own_m2"] == pytest.approx(3.74)
    assert pr["P4"]["grown_m2"] == pytest.approx(1.44) and pr["P4"]["own_m2"] == pytest.approx(1.32)
    assert pr["P4"]["given_to"] == {"P2": pytest.approx(0.12)}
    assert pr["P3"]["inside_m2"] == pytest.approx(1.92) and pr["P3"]["outside_m2"] == pytest.approx(0.12)
    assert pr["_union"]["union_m2"] == pytest.approx(7.10) and pr["_union"]["inside_m2"] == pytest.approx(6.98)


def test_pieces_and_line(pr):
    ps = B.build(spec(pr))
    v = {p["id"]: p for p in ps}
    assert v["P2:IN"]["value"] == pytest.approx(0.374) and v["P2:IN"]["status"] == B.VERIFIED
    assert v["P4:IN"]["value"] == pytest.approx(0.132)
    assert v["P3:IN"]["value"] == pytest.approx(0.192)
    assert v["BEYOND_BOUNDARY"]["value"] is None and v["BEYOND_BOUNDARY"]["high"] == pytest.approx(0.012)
    assert v["R"]["status"] == B.AT_LEAST and v["R"]["value"] is None
    assert (v["R"]["low"], v["R"]["high"]) == (pytest.approx(1.344), pytest.approx(1.419))
    assert v["R"]["readings"]["at_least"] == pytest.approx(1.2)
    m = B.map_lines(ps, {LINE: {"value": 2.054, "reading": {"R": "p10"}, "at_high": ("BEYOND_BOUNDARY",)}})
    assert m[LINE]["proposal"] == B.SPLIT and m[LINE]["value_m3"] == pytest.approx(0.698)
    assert {h["id"] for h in m[LINE]["held"]} == {"BEYOND_BOUNDARY", "R"}


def test_reference_plate_split_closes_both_ends(pr):
    ps = B.build(spec(pr))
    r = B.reconcile_reference(ps, [], 24.0, "one layer over the plot")
    assert r["residual_m3"] == pytest.approx(-24.0)
    rd = r["rule_difference"]
    assert rd["term_low"] == pytest.approx(0.698 + 1.344 - 24.0) and rd["term_high"] == pytest.approx(0.698 + 1.419 - 24.0)
    assert [b["piece"] for b in r["beside"]] == ["BEYOND_BOUNDARY"]          # beyond the plate: never a term
    pieces_in_terms = [t["piece"] for t in r["terms"]]
    assert len(pieces_in_terms) == len(set(pieces_in_terms)) == 4            # no piece in two terms
    r2 = B.reconcile_reference(ps, ["P2:IN", "P4:IN", "P3:IN"], 24.0, "one layer over the plot")
    assert r2["residual_m3"] == pytest.approx(0.698 - 24.0)
    assert all(t["term_low"] == 0 for t in r2["terms"] if t["valued"])


def test_units_mirror_rotation_identical(pr):
    mm = [{"id": p["id"], "outline": [(x * 1000, y * 1000) for x, y in p["outline"]], "depth_m": p["depth_m"]}
          for p in PITS]
    a = B.plan_from_geometry(mm, [(x * 1000, y * 1000) for x, y in PLOT], "mm", 0.10)
    mir = [{"id": p["id"], "outline": [(-x, y) for x, y in p["outline"]], "depth_m": p["depth_m"]} for p in PITS]
    b = B.plan_from_geometry(mir, [(-x, y) for x, y in PLOT], "m", 0.10)
    rot = [{"id": p["id"], "outline": [(-y, x) for x, y in p["outline"]], "depth_m": p["depth_m"]} for p in PITS]
    c = B.plan_from_geometry(rot, [(-y, x) for x, y in PLOT], "m", 0.10)
    for k in ("P2", "P4", "P3"):
        for f in ("own_m2", "inside_m2", "outside_m2"):
            assert a[k][f] == pytest.approx(pr[k][f]) == pytest.approx(b[k][f]) == pytest.approx(c[k][f])


# ------------------------------------------------------------------ adverse
def test_adverse_one_rectangle_over_the_whole_footprint_counted_as_drawn():
    plate = {"id": "PLATE", "outline": rect(0, 0, 20, 12), "depth_m": 0.10}
    with pytest.raises(B.Refused) as e:
        B.plan_from_geometry(PITS + [plate], PLOT, "m", 0.10)
    assert e.value.code == "PLATE_COVERS_MEMBERS"
    with pytest.raises(B.Refused) as e:
        B.build({"thickness": {"value": 0.1, "basis": B.PRINTED, "source": "x"}, "plates": [plate]})
    assert e.value.code == "PLATE_NOT_DRAWN"


def test_adverse_thickness_or_projection_not_printed(pr):
    with pytest.raises(B.Refused) as e:
        B.build(spec(pr, thickness={"value": 0.10, "basis": B.INHERITED, "source": "other villa"}))
    assert e.value.code == "BLINDING_THICKNESS_NOT_PRINTED"
    with pytest.raises(B.Refused) as e:
        B.build(spec(pr, projection={"value": 0.10, "basis": B.INHERITED, "source": "typical of another type"}))
    assert e.value.code == "PROJECTION_NOT_PRINTED_FOR_MEASURED"


def test_adverse_equal_depth_overlap_is_not_guessed():
    a = [{"id": "A", "outline": rect(0, 0, 1, 1), "depth_m": 0.3}, {"id": "Z", "outline": rect(1.1, 0, 2.1, 1), "depth_m": 0.3}]
    with pytest.raises(B.Refused) as e:
        B.plan_from_geometry(a, None, "m", 0.10)
    assert e.value.code == "OVERLAP_OWNER_TIE"


def test_adverse_missing_data_never_zero(pr):
    with pytest.raises(B.Refused) as e:                                   # held piece with a value
        B._piece("x", "e", LINE, B.HELD, value=1.0, blocker="b")
    assert e.value.code == "HELD_WITH_VALUE"
    with pytest.raises(B.Refused) as e:                                   # a 0 piece
        B._piece("x", "e", LINE, B.DC, value=0.0)
    assert e.value.code == "ZERO_OR_NEGATIVE_PIECE"
    with pytest.raises(B.Refused) as e:                                   # held without its blocker
        B._piece("x", "e", LINE, B.HELD, low=0.0, high=1.0)
    assert e.value.code == "HELD_WITHOUT_BLOCKER"
    with pytest.raises(B.Refused) as e:                                   # VERIFIED without a verdict
        B._piece("x", "e", LINE, B.VERIFIED, value=1.0)
    assert e.value.code == "VERIFIED_WITHOUT_VERDICT"
    with pytest.raises(B.Refused) as e:                                   # beyond the plot line without a blocker
        B.build(spec(pr, beyond_boundary={"line": LINE}))
    assert e.value.code == "BEYOND_BOUNDARY_WITHOUT_BLOCKER"
    with pytest.raises(B.Refused) as e:                                   # one reading is not a conflict
        B.build(spec(pr, conflict=[{"id": "C", "element": "e", "line": LINE, "scenarios": {"a": 0.4}, "blocker": "q"}]))
    assert e.value.code == "CONFLICT_NEEDS_TWO_READINGS"
    u = B.build(spec(pr, unmeasured=[{"id": "U", "element": "wall base", "blocker": "count not printed"}]))
    assert next(p for p in u if p["id"] == "U")["low"] is None                # no figure, never 0
    with pytest.raises(B.Refused):
        B.reconcile_reference(u, ["U"], 24.0, "plate")                      # an unmeasured piece is never valued


def test_adverse_estimate_needs_label_and_reading(pr):
    h = dict(spec(pr)["held_projection"][0], estimate={"label": "", "reading": "p15"})
    with pytest.raises(B.Refused) as e:
        B.build(spec(pr, held_projection=[h]))
    assert e.value.code == "ESTIMATE_WITHOUT_LABEL_OR_READING"
    h = dict(spec(pr)["held_projection"][0], estimate={"label": "owner RFI label", "reading": "p15"})
    r = next(p for p in B.build(spec(pr, held_projection=[h])) if p["id"] == "R")
    assert r["status"] == B.ESTIMATED and r["value"] == pytest.approx(1.419) and r["status"] != B.VERIFIED


def test_adverse_line_must_re_add_and_pieces_map_once(pr):
    ps = B.build(spec(pr))
    with pytest.raises(B.Refused) as e:                                   # the plate figure as the line
        B.map_lines(ps, {LINE: {"value": 24.0, "reading": {"R": "p10"}, "at_high": ("BEYOND_BOUNDARY",)}})
    assert e.value.code == "LINE_DOES_NOT_RE_ADD"
    bad = [dict(p, line="L-UNKNOWN") if p["id"] == "R" else p for p in ps]
    with pytest.raises(B.Refused) as e:
        B.map_lines(bad, {LINE: {"value": 0.71, "at_high": ("BEYOND_BOUNDARY",)}})
    assert e.value.code == "PIECE_ON_UNKNOWN_LINE"
    with pytest.raises(B.Refused) as e:
        B.map_lines(ps, {LINE: {"value": 2.054, "reading": {"R": "p10"}, "at_high": ("BEYOND_BOUNDARY",)},
                         "L-EMPTY": {"value": 1.0}})
    assert e.value.code == "LINE_WITHOUT_PIECE"


def test_adverse_held_raft_reading_touching_a_neighbour():
    nb = {"P": [(x, y) for x, y in B.grow(B._poly(rect(14.2, 6, 15, 7), 1.0), 0.10).exterior.coords[:-1]]}
    B.clearance_ok(rect(10, 6, 14, 9), [0.0], nb, "m")                     # 0.20 clear at p = 0
    with pytest.raises(B.Refused) as e:
        B.clearance_ok(rect(10, 6, 14, 9), [0.0, 0.15], nb, "m")
    assert e.value.code == "HELD_PIECE_OVERLAP_UNRESOLVED"
