"""T-229 hand fixture, synthetic Villa Q (not Alsenan): a two-bay beam carrying a planted column at mid-span.

Hand values (m, m2, m3):
  TB 0.40 wide x 0.80 deep, supports C1 (0.30 x 0.30) at x = 0 and C2 (0.30 x 0.30) at x = 8.00, clear 0.15 .. 7.85.
  Planted column PC 0.30 (along the beam) x 0.20 centred at x = 4.00, starting ON the beam (it is carried).
  Continuous beam: 7.70 x 0.40 x 0.80 = 2.464.
  Billed as two pieces cut at the PC (0.15 .. 3.85 and 4.15 .. 7.85): 2 x 3.70 x 0.40 x 0.80 = 2.368.
  Gap 0.30 x 0.40 = 0.12 m2, PC covers 0.06 m2 (share 0.5), the rest beside it inside the beam width:
  the whole gap is beam -> short 0.12 x 0.80 = 0.096; 2.368 + 0.096 = 2.464.
  Adverse: 2.368 offered as the beam (cut at the carried member) -> refused; the joint under the PC owned by the
  beam AND by a column line -> refused; 0 for a missing quantity -> refused.
  Beside a support: beam 0.40 over C3 0.20 (across) x 0.30 (along) flush with one face, pieces cut 0.30 long at C3:
  gap 0.12 m2, C3 0.06 m2 -> beside 0.06 m2 x 0.80 = 0.048 (the beam keeps it).
  Oblique end: beam end face at x = 0 (width 0.40, y -0.20 .. +0.20) against a support face running from (0.2, -0.2)
  to (0.6, 0.2): unbilled trapezoid 0.40 x (0.2 + 0.6) / 2 = 0.16 m2 -> 0.128 m3 at D 0.80.
  Through column: C4 0.20 x 0.40 = 0.08 m2 under a beam piece billed through it, D 0.75, column line at the full
  storey interval -> DOUBLE 0.08 x 0.75 = 0.060 (owner column, beam over-billed 0.060); column built to the soffit of
  the member billed through it -> PASS.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t229"))
import beam_support as S  # noqa: E402

AP = pytest.approx


def _rot(p, ang, mirror=False):
    a = math.radians(ang)
    x, y = p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a)
    return (-x, y) if mirror else (x, y)


def _quad(x0, x1, w, ang=0.0, mirror=False, ox=3.0, oy=-2.0):
    pts = [(x0, -w / 2), (x1, -w / 2), (x1, w / 2), (x0, w / 2)]
    return [(_rot(p, ang, mirror)[0] + ox, _rot(p, ang, mirror)[1] + oy) for p in pts]


def _villa(ang=0.0, mirror=False, unit=1.0):
    """Pieces and members of Villa Q, turned by ang degrees and optionally mirrored, coordinates in metres / unit."""
    tr = lambda p: (_rot(p, ang, mirror)[0] + 3.0, _rot(p, ang, mirror)[1] - 2.0)
    a = S.piece_from_quad("TB.1", "TB", [(x / unit, y / unit) for x, y in _quad(0.15, 3.85, 0.40, ang, mirror)], 0.80)
    b = S.piece_from_quad("TB.2", "TB", [(x / unit, y / unit) for x, y in _quad(4.15, 7.85, 0.40, ang, mirror)], 0.80)
    pc = S.Member("PC", "CARRIED_COLUMN", [(x / unit, y / unit) for x, y in
                                            [tr(p) for p in [(3.85, -0.10), (4.15, -0.10), (4.15, 0.10), (3.85, 0.10)]]])
    return a, b, pc


@pytest.mark.parametrize("ang,mirror", [(0.0, False), (30.0, False), (-47.5, True), (90.0, False)])
def test_cut_at_planted_column_is_refused_and_the_gap_is_beam(ang, mirror):
    a, b, pc = _villa(ang, mirror)
    poly, L, w = S.gap(a, b)
    assert L == AP(0.30, abs=1e-9) and w == AP(0.40, abs=1e-9) and abs(S.area(poly)) == AP(0.12, abs=1e-9)
    sh = S.shares(poly, [pc])
    assert sh["CARRIED_COLUMN"] == AP(0.5, abs=1e-9) and "COLUMN_BELOW" not in sh
    g = S.classify_gap({"area_m2": 0.12, "support_share": 0.0, "carried_share": sh["CARRIED_COLUMN"],
                        "depth_m": 0.80, "edges_continuous": True})
    assert g["cls"] == "CUT_AT_CARRIED" and g["status"] == "BEAM_SHORT"
    assert g["short_m3"] == AP(0.096) and g["under_carried_m2"] == AP(0.06) and g["beside_m2"] == AP(0.06)
    run = S.beam_run([a.length * 0.40 * 0.80, b.length * 0.40 * 0.80], [g])
    assert run["billed_m3"] == AP(2.368) and run["drawing_m3"] == AP(2.464)
    assert S.check_claim(run, 2.464)
    with pytest.raises(S.Refused, match="CUT_AT_CARRIED_MEMBER"):
        S.check_claim(run, 2.368)                         # adverse: the cut kept
    with pytest.raises(S.Refused, match="MISSING_AS_ZERO"):
        S.check_claim(run, 0)


@pytest.mark.parametrize("unit", [1.0, 0.01, 0.001])          # m, cm, mm drawings: the same beam after to_m
def test_units(unit):
    a, b, pc = _villa(unit=unit)
    f = S.to_m(1, {1.0: "m", 0.01: "cm", 0.001: "mm"}[unit])
    a2 = S.Piece(a.id, a.mark, (a.p0[0] * f, a.p0[1] * f), (a.p1[0] * f, a.p1[1] * f), a.width * f, 0.80)
    b2 = S.Piece(b.id, b.mark, (b.p0[0] * f, b.p0[1] * f), (b.p1[0] * f, b.p1[1] * f), b.width * f, 0.80)
    poly, L, w = S.gap(a2, b2)
    assert L == AP(0.30) and abs(S.area(poly)) == AP(0.12)
    with pytest.raises(S.Refused, match="UNKNOWN_UNIT"):
        S.to_m(1, "ft")


def test_joint_owned_once():
    assert S.check_joint_claims([{"line": "TB", "contains_joint": True}, {"line": "PC", "contains_joint": False}]) == "TB"
    with pytest.raises(S.Refused, match="JOINT_OWNED_TWICE"):
        S.check_joint_claims([{"line": "TB", "contains_joint": True}, {"line": "PC ledger joint", "contains_joint": True}])
    with pytest.raises(S.Refused, match="JOINT_OWNED_BY_NONE"):
        S.check_joint_claims([{"line": "TB", "contains_joint": False}, {"line": "PC", "contains_joint": False}])


def test_support_cut_and_beside():
    pure = S.classify_gap({"area_m2": 0.12, "support_share": 1.0, "carried_share": 0.0, "depth_m": 0.8,
                           "edges_continuous": True})
    assert pure["cls"] == "SUPPORT_CUT" and pure["status"] == "PASS" and pure["short_m3"] == 0.0
    side = S.classify_gap({"area_m2": 0.12, "support_share": 0.5, "carried_share": 0.0, "depth_m": 0.8,
                           "edges_continuous": True})
    assert side["cls"] == "SUPPORT_CUT_BESIDE" and side["status"] == "BEAM_SHORT" and side["short_m3"] == AP(0.048)
    # a crossing beam that bills part of the beside zone is not counted again
    part = S.classify_gap({"area_m2": 0.12, "support_share": 0.5, "other_beam_share": 0.25, "depth_m": 0.8,
                           "edges_continuous": True})
    assert part["short_m3"] == AP(0.024)
    # adverse: beam edges not drawn past the support -> HELD bounded, never a number, never 0
    held = S.classify_gap({"area_m2": 0.12, "support_share": 0.5, "depth_m": 0.8, "edges_continuous": False})
    assert held["status"] == "HELD" and held["short_m3"] is None and held["bound_m3"] == AP(0.048)
    # adverse: the beam width is a printed / drawn conflict -> HELD
    wc = S.classify_gap({"area_m2": 0.12, "support_share": 0.5, "depth_m": 0.8, "edges_continuous": True,
                         "width_conflict": True})
    assert wc["status"] == "HELD" and wc["short_m3"] is None


def test_held_cases_never_zero():
    proj = S.classify_gap({"area_m2": 0.16, "support_share": 0.0, "depth_m": None, "projection": True})
    assert proj["status"] == "HELD" and proj["short_m3"] is None
    nodepth = S.classify_gap({"area_m2": 0.12, "carried_share": 0.5, "depth_m": None, "edges_continuous": True})
    assert nodepth["status"] == "HELD" and nodepth["short_m3"] is None
    noedge = S.classify_gap({"area_m2": 0.12, "carried_share": 0.5, "depth_m": 0.8, "edges_continuous": False})
    assert noedge["status"] == "HELD" and noedge["bound_m3"] == AP(0.096)
    nothing = S.classify_gap({"area_m2": 0.12, "depth_m": 0.8})
    assert nothing["cls"] == "CUT_NO_MEMBER" and nothing["status"] == "HELD" and nothing["bound_m3"] == AP(0.096)
    run = S.beam_run([1.0], [noedge])
    assert run["status"] == "HELD" and run["drawing_m3"] is None
    with pytest.raises(S.Refused, match="HELD_RUN"):
        S.check_claim(run, 1.096)
    with pytest.raises(S.Refused, match="SHARES_EXCEED_GAP"):
        S.classify_gap({"area_m2": 0.12, "support_share": 0.8, "carried_share": 0.5, "depth_m": 0.8})


def test_oblique_end_geometry_and_class():
    p = S.Piece("B", "B", (-3.0, 0.0), (0.0, 0.0), 0.40, 0.80)
    sup = S.Member("C", "COLUMN_BELOW", [(0.2, -0.2), (2.0, -0.2), (2.0, 2.0), (0.6, 0.2)])
    poly, t, sid, beam_area, t_far = S.extension(p, 1, [sup])
    assert sid == "C" and t == AP(0.2, abs=1e-3) and t_far == AP(0.6, abs=2e-3)
    assert beam_area == AP(0.16, abs=1e-3)                      # trapezoid 0.40 x (0.2 + 0.6) / 2
    e = {"touch": "SUPPORT", "beyond_area_m2": 0.16, "beyond_closed": True, "beyond_edge_cover": [1.0, 1.0],
         "depth_m": 0.80}
    c = S.classify_end(e)
    assert c["cls"] == "END_SHORT_OBLIQUE" and c["status"] == "BEAM_SHORT" and c["short_m3"] == AP(0.128)
    # square end (residual only) and an open strip (no member closes it): PASS
    assert S.classify_end({**e, "beyond_area_m2": 0.001})["status"] == "PASS"
    assert S.classify_end({**e, "beyond_closed": False})["cls"] == "END_AT_SUPPORT"
    # the drawn beam ends at the billed face (one side not drawn): PASS; drawn in part: HELD bounded
    assert S.classify_end({**e, "beyond_edge_cover": [0.2, 1.0]})["status"] == "PASS"
    h = S.classify_end({**e, "beyond_edge_cover": [0.7, 1.0]})
    assert h["status"] == "HELD" and h["bound_m3"] == AP(0.128) and h["short_m3"] is None
    # a piece that stops at a member it carries with no support behind it: HELD, never PASS
    assert S.classify_end({**e, "touch": "CARRIED", "beyond_closed": False})["status"] == "HELD"
    with pytest.raises(S.Refused, match="BEYOND_NOT_MEASURED"):
        S.classify_end({"touch": "SUPPORT", "depth_m": 0.8})


def test_end_short_at_carried_member():
    # turned / planted column at the end: the piece stops at its face, the support face is 0.30 further
    c = S.classify_end({"touch": "CARRIED", "beyond_area_m2": 0.12, "beyond_closed": True,
                        "beyond_edge_cover": [1.0, 1.0], "depth_m": 0.80})
    assert c["cls"] == "END_SHORT_AT_CARRIED" and c["short_m3"] == AP(0.096)


def test_through_column_ownership():
    d = S.joint_ownership(0.999, 0.08, 0.75, "FULL_INTERVAL")
    assert d["result"] == "DOUBLE" and d["double_m3"] == AP(0.08 * 0.999 * 0.75) and d["owner"].startswith("column")
    assert S.joint_ownership(1.0, 0.08, 0.75, "JOINT_LINE")["result"] == "DOUBLE"
    assert S.joint_ownership(1.0, 0.08, 0.75, "TO_THROUGH_SOFFIT") == {
        "result": "PASS", "owner": "beam (billed through; the column stops at its soffit)", "double_m3": 0.0}
    assert S.joint_ownership(1.0, 0.08, 0.75, "NONE")["result"] == "PASS"
    half = S.joint_ownership(0.5, 0.08, 0.75, "FULL_INTERVAL")
    assert half["result"] == "DOUBLE_PARTIAL" and half["double_m3"] == AP(0.03)
    assert S.joint_ownership(0.0, 0.08, 0.75, "FULL_INTERVAL")["result"] == "PASS"
    with pytest.raises(S.Refused, match="UNKNOWN_COLUMN_BASIS"):
        S.joint_ownership(1.0, 0.08, 0.75, "GUESS")


def test_not_one_beam():
    a = S.Piece("A", "B1", (0, 0), (3, 0), 0.2, 0.4)
    b = S.Piece("B", "B1", (3.3, 0.2), (6, 0.2), 0.2, 0.4)           # offset 0.20: another line
    with pytest.raises(S.Refused, match="NOT_COLLINEAR"):
        S.gap(a, b)
    c = S.Piece("C", "B1", (3.3, 0), (6, 3), 0.2, 0.4)               # turned 45 deg
    with pytest.raises(S.Refused, match="NOT_COLLINEAR"):
        S.gap(a, c)
    assert S.gap(a, S.Piece("D", "B1", (3.0, 0), (6, 0), 0.2, 0.4)) is None   # touching pieces: no gap
