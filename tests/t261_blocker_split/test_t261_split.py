"""T-261: blockwork register v2 blockers, wall by wall: piece split (rule R-T261-1).

Fixture villa N (NOT Alsenan), storey basis +0.00, slab top +4.00 above every piece; hand truth (m2):
  N1 0.20 white, 10.000 m between column faces:
     A 4.000 m under beam BA 20x50  -> h 4.00 - 0.50 = 3.50 -> 14.000
     B 3.500 m under beam BB 20x75  -> h 4.00 - 0.75 = 3.25 -> 11.375   (a wall under a beam of two depths)
     C 2.500 m with no member drawn above -> HELD (no figure from a default)
     window NW1 1.20 x 1.50 = 1.800, jambs 0.50 .. 1.70 m inside A; door ND1 0.90 x 2.20 = 1.980 inside C
     established part = 14.000 + 11.375 - 1.800 = 23.575; HELD increment = C with ND1
  N2 0.20 white, 6.000 m: S 2.000 m stair-foot piece on a printed +0.30 landing under a stair member (height 4.10 on
     the storey basis is NOT a quantity) + T 4.000 m under beam 20x50 (h 3.50 = 14.000); window 0.60 x 0.80 = 0.480
     in T -> established 13.520, S HELD.
  N3 straddle: a window whose jambs 3.80 .. 4.40 m cross the A / B face -> no split, wall wholly HELD.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t261"
sys.path.insert(0, str(HERE))

import piece_split as P  # noqa: E402
import build_t261 as B   # noqa: E402


def n1(order=1):
    ps = [P.Piece("A", 4.000, 3.50, "member"), P.Piece("B", 3.500, 3.25, "member"),
          P.Piece("C", 2.500, None, held_item="no member drawn above", held_figure_m2="2.500 m, height not drawn")]
    ops = [P.Opening("NW1", "A", 0.50, 1.70, 1.800), P.Opening("ND1", "C", 0.80, 1.70, 1.980)]
    if order < 0:   # mirrored plan: pieces listed from the other end, jambs measured from the other face
        ps = list(reversed(ps))
        ops = [P.Opening("NW1", "A", 4.000 - 1.70, 4.000 - 0.50, 1.800), P.Opening("ND1", "C", 2.500 - 1.70, 2.500 - 0.80, 1.980)]
    return ps, ops


@pytest.mark.parametrize("order", [1, -1])
def test_villa_n1_two_beam_depths_and_no_beam(order):
    ps, ops = n1(order)
    s = P.split_wall("N1", ps, ops, 10.000)
    assert s.status == "SPLIT"
    assert s.established_gross_m2 == pytest.approx(25.375, abs=1e-4)
    assert s.established_deductions_m2 == pytest.approx(1.800, abs=1e-4)
    assert s.established_m2 == pytest.approx(23.575, abs=1e-4)
    assert s.held_pieces == ["C"] and s.held_openings == ["ND1"]
    txt = P.wall_total_text(s, "2.500 m, height not drawn")
    assert txt.startswith("23.5750 established + HELD increment")


def test_villa_n2_stair_foot_on_raised_landing_held():
    ps = [P.Piece("S", 2.000, 4.10, "member", base_is_storey_basis=False, top_is_stair_member=True,
                  held_figure_m2="2.000 x 4.10 = 8.200 on the storey basis"),
          P.Piece("T", 4.000, 3.50, "member")]
    s = P.split_wall("N2", ps, [P.Opening("w", "T", 1.0, 1.6, 0.480)], 6.000)
    assert s.established_m2 == pytest.approx(13.520, abs=1e-4)
    assert s.held_pieces == ["S"]
    ok, why = P.piece_established(ps[0])
    assert not ok and "storey basis" in why


def test_stair_member_with_floor_member_printed_is_established():
    p = P.Piece("S", 2.0, 3.5, "member", top_is_stair_member=True, floor_member_with_stair=True)
    assert P.piece_established(p) == (True, "")
    q = P.Piece("S", 2.0, 3.5, "member", top_is_stair_member=True)
    assert P.piece_established(q)[0] is False


def test_straddling_opening_keeps_wall_held():
    ps, _ = n1()
    s = P.split_wall("N3", ps, [P.Opening("X", "A", 3.80, 4.40, 0.900)], 10.000)
    assert s.status == "STRADDLE" and s.established_m2 is None
    assert P.wall_total_text(s, "25.375 figure").startswith("HELD")


@pytest.mark.parametrize("src", ["finish", "freelancer", "default", "storey"])
def test_adverse_height_sources_refused(src):
    ps = [P.Piece("A", 4.0, 3.50, src), P.Piece("C", 1.0, None)]
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N4", ps, [], 5.0)
    assert e.value.code == "BAD_SOURCE"


def test_adverse_height_with_no_source_refused():
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N5", [P.Piece("A", 4.0, 3.5, "")], [], 4.0)
    assert e.value.code == "BAD_SOURCE"


def test_adverse_held_shown_as_zero_refused():
    ps, ops = n1()
    s = P.split_wall("N1", ps, ops, 10.000)
    for z in ("", "0", "0.000"):
        with pytest.raises(P.SplitError) as e:
            P.wall_total_text(s, z)
        assert e.value.code == "HELD_AS_ZERO"


def test_adverse_pieces_not_closed_and_millimetres():
    ps, ops = n1()
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N1", ps[:2], ops[:1], 10.000)      # the held piece dropped: never silently 0
    assert e.value.code == "NOT_CLOSED"
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N1", [P.Piece("A", 4000.0, 3.5, "member")], [], 4000.0)
    assert e.value.code == "UNITS"
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N1", [P.Piece("A", 2.0, 3.5, "member"), P.Piece("A", 2.0, 3.5, "member")], [], 4.0)
    assert e.value.code == "DUPLICATE_PIECE"
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N1", ps, [P.Opening("Z", "Q", 0, 1, 1.0)], 10.000)
    assert e.value.code == "UNKNOWN_PIECE"


def test_all_pieces_held_gives_no_established_part():
    s = P.split_wall("N6", [P.Piece("C", 3.0, None, held_figure_m2="3.0 m")], [], 3.0)
    assert s.status == "HELD" and s.established_m2 is None


# ---------------- Alsenan (development villa; the register v2 CSVs are in the repository) ----------------

def rows(name):
    with open(HERE / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_alsenan_outputs_reproduce():
    assert B.main(["--check"]) == 0


def test_alsenan_split_values_and_totals():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    bw = s["by_wall"]
    # GF-W10 = the Checker's own eastern pieces (09:59 / 11:59): 13.880 + 13.400 + 13.3125 - 1.440
    assert bw["GF-W10"] == pytest.approx(39.1525, abs=1e-4)
    # 1F-W10: CB9 pieces 38.369 (Checker arithmetic) - W21 / W22 / W23 3 x 0.480; W25 sits in the B3 shaft piece
    assert bw["1F-W10"] == pytest.approx(36.929, abs=1e-4)
    assert bw["2F-W02"] == pytest.approx(3.470 * 3.45 - 0.480 - 1.800, abs=1e-4)
    assert s["established_net_v2_m2"] == pytest.approx(449.260, abs=1e-3)
    assert s["established_net_proposed_m2"] == pytest.approx(449.260 + sum(bw.values()), abs=2e-3)
    assert s["applied_to_register"] is False
    assert s["blockers"] == 41 and s["split"] + s["still_held"] == 41


def test_alsenan_stair_line_pieces_stay_held_with_their_openings():
    sp = rows("T261_SPLIT.csv")
    held = {(r["wall_id"], r["piece"]): r for r in sp if r["piece_status"] == "HELD"}
    assert ("GF-W10", "SF B3 (With Stair) stair-foot") in held and "D-GF-09" in held[("GF-W10", "SF B3 (With Stair) stair-foot")]["openings"]
    assert "W25" in held[("1F-W10", "SF B3 (With Stair)")]["openings"]
    assert "W27" in held[("2F-W02", "SF B3")]["openings"]
    for r in held.values():
        assert r["gross_m2"] == "" and r["held_figure_not_a_quantity"] not in ("", "0", "0.000")


def test_alsenan_split_gross_matches_register_v2_within_rounding():
    v2 = {r["wall_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv",
                                                       newline="", encoding="utf-8"))}
    bl = {r["wall_id"]: r for r in rows("T261_BLOCKERS.csv")}
    for w in ("1F-W04", "2F-W03", "2F-W07", "1F-W18", "1F-W24"):
        assert float(bl[w]["established_gross_m2"]) == pytest.approx(float(v2[w]["gross_m2"]), abs=0.003)
        assert float(bl[w]["established_deductions_m2"]) == pytest.approx(float(v2[w]["deductions_m2"]), abs=1e-4)


def test_alsenan_every_still_held_blocker_names_its_item_and_no_coordinates():
    bl = rows("T261_BLOCKERS.csv")
    for r in bl:
        if r["t261_verdict"] == "STILL-HELD":
            assert r["still_held"] and r["established_net_m2"] == ""
    text = "".join((HERE / n).read_text(encoding="utf-8") for n in ("T261_BLOCKERS.csv", "T261_SPLIT.csv"))
    import re
    assert not re.search(r"-?\d{5,}\.\d", text), "no drawing coordinates in the outputs"
