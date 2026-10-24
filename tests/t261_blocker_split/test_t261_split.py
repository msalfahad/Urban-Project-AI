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
  N7 (rule 7, r2): 0.20 wall, census 5.300 m = column face -> centreline of a perpendicular wall at the far end:
     D 5.000 m under beam BD 20x50 drawn 5.000 m between the column faces -> h 3.50 -> 17.500
     E 0.300 m corner overlap inside a perpendicular band 0.60 m wide, beam BE 60x75 printed -> h 3.25 -> 0.975
     window 1.00 x 1.20 = 1.200 in D -> established 17.500 + 0.975 - 1.200 = 17.275
     adverse: D stretched to 5.300 'closed to census' under BD drawn 5.000 -> OVER_MEMBER; D with no drawn extent ->
     EXTENT_UNNAMED; E under an unlabelled band (depth not printed) -> E HELD, established 16.300, never 0.
  N8 (rule 8, r3): 0.15 partition, census 3.000 m = band face -> wall face, slab 0.16 at +4.00:
     F 1.200 m under a slab panel drawn 1.200 m on the centreline -> h 4.00 - 0.16 = 3.84 -> 4.608
     G 0.300 m across a 30x50 band -> h 3.50 -> 1.050
     K 0.500 m under a slab corner outside a dome ring (drawn 0.800 m to the ring) -> 3.84 -> 1.920
     L 1.000 m inside the dome opening -> HELD (top not drawn), never 0
     established 4.608 + 1.050 + 1.920 = 7.578; without L (opening drawn elsewhere) the wall is whole 7.578 on 2.000
     adverse: F carried from an earlier register as gross / weighted height ('register v2 ... not re-derived', the
     rejected r2 pattern) -> EXTENT_UNNAMED; a census-remainder extent -> EXTENT_UNNAMED; K at the storey height 4.00
     ('storey') -> BAD_SOURCE.
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
    ps = [P.Piece("A", 4.000, 3.50, "member", drawn_extent_m=4.000, extent_source="N faces"),
          P.Piece("B", 3.500, 3.25, "member", drawn_extent_m=3.500, extent_source="N faces"),
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
          P.Piece("T", 4.000, 3.50, "member", drawn_extent_m=4.000, extent_source="N faces")]
    s = P.split_wall("N2", ps, [P.Opening("w", "T", 1.0, 1.6, 0.480)], 6.000)
    assert s.established_m2 == pytest.approx(13.520, abs=1e-4)
    assert s.held_pieces == ["S"]
    ok, why = P.piece_established(ps[0])
    assert not ok and "storey basis" in why


def test_stair_member_with_floor_member_printed_is_established():
    p = P.Piece("S", 2.0, 3.5, "member", top_is_stair_member=True, floor_member_with_stair=True, drawn_extent_m=2.0,
                extent_source="N faces")
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


def n7(e_height=3.25, d_len=5.000, d_extent=5.000, d_src="N7 column faces"):
    return [P.Piece("D", d_len, 3.50, "member", drawn_extent_m=d_extent, extent_source=d_src),
            P.Piece("E", 0.300, e_height, "member" if e_height else "", drawn_extent_m=0.600,
                    extent_source="N7 perpendicular band faces", held_item="band depth not printed",
                    held_figure_m2="0.300 x 3.25 .. 3.50, not a quantity")]


@pytest.mark.parametrize("mirror", [False, True])
def test_villa_n7_corner_overlap_is_its_own_piece(mirror):
    ps = n7()
    op = P.Opening("NW7", "D", 1.00, 2.00, 1.200) if not mirror else P.Opening("NW7", "D", 5.000 - 2.00, 5.000 - 1.00, 1.200)
    s = P.split_wall("N7", list(reversed(ps)) if mirror else ps, [op], 5.300)
    assert s.status == "ESTABLISHED" and s.established_m2 == pytest.approx(17.275, abs=1e-4)
    assert s.established_gross_m2 == pytest.approx(17.500 + 0.975, abs=1e-4)


def test_adverse_closed_to_census_over_the_member_refused():
    with pytest.raises(P.SplitError) as e:     # the rejected r1 pattern: census length put under a shorter member
        P.split_wall("N7", [P.Piece("D", 5.300, 3.50, "member", drawn_extent_m=5.000, extent_source="N7 faces")], [], 5.300)
    assert e.value.code == "OVER_MEMBER"
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N7", n7(d_extent=None), [], 5.300)
    assert e.value.code == "EXTENT_UNNAMED"
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N7", n7(d_src=""), [], 5.300)
    assert e.value.code == "EXTENT_UNNAMED"
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N7", n7(d_extent=5000.0), [], 5.300)
    assert e.value.code == "UNITS"


def test_corner_under_an_unprinted_member_stays_held_not_zero():
    ps = n7(e_height=None)
    s = P.split_wall("N7", ps, [P.Opening("NW7", "D", 1.00, 2.00, 1.200)], 5.300)
    assert s.status == "SPLIT" and s.held_pieces == ["E"]
    assert s.established_m2 == pytest.approx(16.300, abs=1e-4)
    assert "HELD increment" in P.wall_total_text(s, ps[1].held_figure_m2)


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
    assert s["blockers"] == 41 and s["split"] + s["settled_whole"] + s["still_held"] == 41


def test_alsenan_stair_line_pieces_stay_held_with_their_openings():
    sp = rows("T261_SPLIT.csv")
    held = {(r["wall_id"], r["piece"]): r for r in sp if r["piece_status"] == "HELD"}
    assert ("GF-W10", "SF B3 (With Stair) stair-foot") in held and "D-GF-09" in held[("GF-W10", "SF B3 (With Stair) stair-foot")]["openings"]
    assert "W25" in held[("1F-W10", "SF B3 (With Stair)")]["openings"]
    assert "W27" in held[("2F-W02", "SF B3")]["openings"]
    for r in held.values():
        assert r["gross_m2"] == "" and r["held_figure_not_a_quantity"] not in ("", "0", "0.000")


def test_alsenan_deductions_match_register_v2_and_no_inherited_gross():
    v2 = {r["wall_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv",
                                                       newline="", encoding="utf-8"))}
    bl = {r["wall_id"]: r for r in rows("T261_BLOCKERS.csv")}
    for w in B.WALLS:                     # r3: no established piece of any wall carries an inherited extent
        for pc in B.WALLS[w]["pieces"]:
            low = pc.extent_source.lower()
            assert not any(m in low for m in P.INHERITED_EXTENT_MARKERS), (w, pc.pid)
    for w in ("1F-W04", "2F-W03", "2F-W07"):
        assert float(bl[w]["established_deductions_m2"]) == pytest.approx(float(v2[w]["deductions_m2"]), abs=1e-4)


def test_alsenan_r2_pieces_are_drawn_member_extents_not_census_closures():
    """Checker 2026-10-24 15:10: B2 (1F-W04) and B15 (2F-W07) are drawn 2.700 m face to face; 2F-W03's band spans
    re-derived from the ST inner faces (2.500 / 1.800 / 3.000) with the 0.200 framing-in junctions and the census corner
    overlaps as their own pieces. Hand truth (m2): 1F-W04 2.700 x 3.80 + 0.100 x 3.45 (B23 45x75) - 2.760 = 7.845;
    2F-W03 7.300 x 3.80 + 0.100 x 3.45 (B7 20x75) - 2.200 = 25.885; 2F-W07 2.700 x 3.00 - 1.875 = 6.225."""
    sp = rows("T261_SPLIT.csv")
    assert not any("closed to census" in r["piece"] for r in sp)
    for w, census in (("1F-W04", 3.600), ("2F-W03", 7.900), ("2F-W07", 5.725), ("2F-W05", 2.250)):
        assert sum(float(r["length_m"]) for r in sp if r["wall_id"] == w) == pytest.approx(census, abs=1e-6)
    est = {(r["wall_id"], r["piece"]): float(r["length_m"]) for r in sp if r["piece_status"] != "HELD"}
    assert est[("1F-W04", "E B2 BM-1F-006")] == 2.700 and est[("2F-W07", "E B15 BM-2F-007")] == 2.700
    assert est[("2F-W03", "E B2 BM-2F-006")] == 3.000
    bw = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))["by_wall"]
    assert bw["1F-W04"] == pytest.approx(2.700 * 3.80 + 0.100 * 3.45 - 2.760, abs=1e-4)
    assert bw["2F-W03"] == pytest.approx(7.300 * 3.80 + 0.100 * 3.45 - 2.200, abs=1e-4)
    assert bw["2F-W07"] == pytest.approx(2.700 * 3.00 - 1.875, abs=1e-4)
    # 2F-W05 (r2): B1 1.000 between column faces x 3.80, no opening in it; D-2F-02 wholly in the held BM-2F-017 piece
    assert bw["2F-W05"] == pytest.approx(1.000 * 3.80, abs=1e-4)
    held = {(r["wall_id"], r["piece"]): r for r in sp if r["piece_status"] == "HELD"}
    assert "D-2F-02" in held[("2F-W05", "H BM-2F-017")]["openings"]
    for w in B.WALLS:                     # rule 7 on every established member piece of the run
        for pc in B.WALLS[w]["pieces"]:
            if P.piece_established(pc)[0] and pc.source in ("member", "slab"):
                assert pc.length_m <= pc.drawn_extent_m + P.TOL and pc.extent_source


def test_alsenan_every_still_held_blocker_names_its_item_and_no_coordinates():
    bl = rows("T261_BLOCKERS.csv")
    for r in bl:
        if r["t261_verdict"] == "STILL-HELD":
            assert r["still_held"] and r["established_net_m2"] == ""
    text = "".join((HERE / n).read_text(encoding="utf-8") for n in ("T261_BLOCKERS.csv", "T261_SPLIT.csv"))
    import re
    assert not re.search(r"-?\d{5,}\.\d", text), "no drawing coordinates in the outputs"


# ---------------- r3 (Checker 2026-10-24 17:00): rule 8, every established piece from a drawn extent ----------------

def n8(f_src="N8 slab panel P1 on the centreline, band face -> band face", with_l=True):
    ps = [P.Piece("F", 1.200, 3.84, "slab", drawn_extent_m=1.200, extent_source=f_src),
          P.Piece("G", 0.300, 3.50, "member", drawn_extent_m=0.300, extent_source="N8 band faces, 30x50 printed"),
          P.Piece("K", 0.500, 3.84, "slab", drawn_extent_m=0.800,
                  extent_source="N8 slab corner outside the ring, band face -> ring outer arc")]
    if with_l:
        ps.append(P.Piece("L", 1.000, None, held_item="inside the dome opening: top of wall not drawn",
                          held_figure_m2="1.000 m, height not drawn"))
    return ps


@pytest.mark.parametrize("mirror", [False, True])
def test_villa_n8_slab_band_corner_and_dome_opening(mirror):
    ps = n8()
    s = P.split_wall("N8", list(reversed(ps)) if mirror else ps, [], 3.000)
    assert s.status == "SPLIT" and s.held_pieces == ["L"]
    assert s.established_m2 == pytest.approx(1.200 * 3.84 + 0.300 * 3.50 + 0.500 * 3.84, abs=1e-4)   # 7.578
    assert "HELD increment" in P.wall_total_text(s, "1.000 m, height not drawn")
    w = P.split_wall("N8b", n8(with_l=False), [], 2.000)
    assert w.status == "ESTABLISHED" and P.wall_total_text(w, "") == "7.5780"


@pytest.mark.parametrize("src", [B.V2_EXT, "register v2 gross 17.934 over 4.761 m",
                                 "census remainder after the held piece", "weighted height of the earlier pieces",
                                 "Closed To Census"])
def test_adverse_inherited_extent_refused(src):
    """The rejected r2 pattern: an earlier register's gross / weighted height carried onto a length that is not a drawn
    member extent (1F-W18 17.934 on 4.761 m, 1F-W24 5.651 on 1.426 m) is refused, whatever the length says."""
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N8", n8(f_src=src), [], 3.000)
    assert e.value.code == "EXTENT_UNNAMED"


def test_adverse_slab_corner_at_storey_height_refused():
    ps = n8()
    ps[2] = P.Piece("K", 0.500, 4.00, "storey")
    with pytest.raises(P.SplitError) as e:
        P.split_wall("N8", ps, [], 3.000)
    assert e.value.code == "BAD_SOURCE"


def test_alsenan_r3_1f_w18_and_1f_w24_from_drawn_extents():
    """Own re-measure on 'ST7757 dxf.dxf' (1F roof slab), wall centrelines from the arch faces (frame by the common
    column 2FDB = 667). Hand truth (m2):
    1F-W18: B5 3.475 x 3.70 (SBT B5 20x50) + B19 0.01515 x 3.45 (40x75) + slab 1F-057 0.99533 x 4.04
            + B6 0.250 x 3.70 (25x50) + slab corner 1F-076/c0 0.46452 x 4.04 = 19.7326 on 5.200, nothing held.
    1F-W24: slab 1F-094 1.14234 x 4.04 + B6 0.250 x 3.70 = 5.5401; dome opening 1.05766 HELD."""
    bw = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))["by_wall"]
    assert bw["1F-W18"] == pytest.approx(3.475 * 3.70 + 0.01515 * 3.45 + 0.99533 * 4.04 + 0.250 * 3.70
                                         + 0.46452 * 4.04, abs=1e-4)
    assert bw["1F-W24"] == pytest.approx(1.14234 * 4.04 + 0.250 * 3.70, abs=1e-4)
    sp = rows("T261_SPLIT.csv")
    for w, census in (("1F-W18", 5.200), ("1F-W24", 2.450)):
        assert sum(float(r["length_m"]) for r in sp if r["wall_id"] == w) == pytest.approx(census, abs=1e-3)
    assert not any(r["piece_status"] == "HELD" for r in sp if r["wall_id"] == "1F-W18")
    held = [r for r in sp if r["wall_id"] == "1F-W24" and r["piece_status"] == "HELD"]
    assert len(held) == 1 and held[0]["gross_m2"] == "" and held[0]["held_figure_not_a_quantity"]
    bl = {r["wall_id"]: r for r in rows("T261_BLOCKERS.csv")}
    assert bl["1F-W18"]["t261_verdict"].startswith("SETTLED") and bl["1F-W18"]["wall_net_text"] == "19.7326"
