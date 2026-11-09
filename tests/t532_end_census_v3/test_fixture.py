"""T-532 (R-T532-1, COLUMN_END_CENSUS_V3) on a hand-calculated villa that is not the development villa (villa P532).

Villa P532, one storey 3.50 m (structural floor 0.00, finished floor 0.10), black blocks 0.20 m, course 0.19 + 10 mm
joint (module 0.40 x 0.20), owner joint 10 mm. Run R1 axis (0, 0) -> (3.30, 0), t 0.20, pieces as a T-274 ledger cuts
them (kinds by what lies over each stretch):
  P0 COLUMN 0.00 .. 0.30  architectural column C0 crossed by the run (concrete in plan)
  P1 FACE   0.30 .. 1.50  under slab S1 t 0.20  -> masonry, block top 3.50 - 0.20 = 3.30
  P2 BEAM   1.50 .. 3.30  under beam BM1 h 0.60 -> masonry, block top 3.50 - 0.60 = 2.90
  K1 a column drawn ONLY on the structural sheet, 3.30 .. 3.60 x -0.20 .. 0.20: the run ENDS on its face.
V2 on these kinds raises at end 1 ('the end piece is BEAM') and lists no interior junction (no BLOCK kind): F-C-T526-1.
V3: interior COLUMN-FACE at P0/P1 (face column_end of C0) + end BEAM-END_COLUMN at end 1 (K1), nothing else.
Hand effects (merged rule code, pieces mapped by the V3 kind table: FACE / BEAM -> BLOCK with their tops):
  sharmat ties (R-T355-1, levels z = 0.60 k while z + 0.01 < top): C0 beside top 3.30 -> 0.6 .. 3.0 = 5 nr;
    K1 beside top 2.90 -> 0.6 .. 2.4 = 4 nr;
  V-joint mesh (T-317 drawing band, to the block top less the finished floor 0.10): C0 3.20 m, K1 2.80 m per side, 2 sides;
  perimeter mortar (R-T520-1, kappa 0.92625 for this module, P526): end 1 F -> C adds
    0.92625 x 0.20 x 0.010 x (2.90 - 0.010) = 0.005353725 m3;
  run length / blockwork / blocks: 0 (the end face is the column face).
Adverse: unknown kind -> HELD by name (interior and end), never skipped; masonry-masonry and concrete-concrete boundaries
are no junction; ST_COLUMN is concrete; run reversed / rotated / mirrored gives the same junctions; inconsistent end
data raises; units in mm refused.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t532", "agents_t526", "agents_t520", "agents_t355", "agents_t317"):
    sys.path.insert(0, str(ROOT / "research" / p))
import end_census_v3 as V3  # noqa: E402
import perimeter_joint_v1 as PJ  # noqa: E402
import t317_spatter_mesh as M  # noqa: E402
import t355_masonry_accessories as X  # noqa: E402

A, B, T, J = (0.0, 0.0), (3.30, 0.0), 0.20, 0.010
C0 = box(0.00, -0.20, 0.30, 0.20)          # architectural column, a piece of the run (start)
K1 = box(3.30, -0.20, 3.60, 0.20)          # structural-only column beyond end 1
KINDS = ["COLUMN", "FACE", "BEAM"]
TOPS = [None, 3.30, 2.90]
LENS = [0.30, 1.20, 1.80]


def ends(a=A, b=B, cols=(K1,), own_start=True):
    return [V3.classify_end(a, b, T, 0, list(cols), J, own_piece_is_column=own_start),
            V3.classify_end(a, b, T, 1, list(cols), J)]


def test_v2_raises_on_raw_kinds_v3_lists_both_junctions():
    E = ends()
    assert [e.cls for e in E] == ["COLUMN_PIECE_IN_RUN", "COLUMN"]
    v2, err = V3.v2_on_kinds("P532-R1", KINDS, E)
    assert v2 is None and "end piece is BEAM" in err
    js = V3.end_junctions_v3("P532-R1", KINDS, E)
    assert [(j["source"], j["at"], j["class"], j["state"]) for j in js] == [
        ("V3_INTERIOR", "piece 0/1", "COLUMN-FACE", "LISTED"), ("V3_END", "end 1", "BEAM-END_COLUMN", "LISTED")]
    assert js[0]["column_piece"] == 0 and js[0]["face"] == "column_end"


def _block_pieces():
    """the V3 kind table applied: masonry kinds -> BLOCK with the top read from their member (hand values)."""
    out = []
    for k, L, top in zip(KINDS, LENS, TOPS):
        r = V3.role(k)[0]
        assert r in (V3.MASONRY, V3.CONCRETE)
        out.append(("COLUMN" if r == V3.CONCRETE else "BLOCK", L, top, k))
    return out


def test_hand_ties_mesh_and_perimeter_at_both_junctions():
    ps = _block_pieces()
    course = X.course_spec(0.190, 0.010, "P532 fixture", "FIXTURE")
    pcs = [X.make_piece(kd, L, top, "R1@0.000" if kd == "COLUMN" else f"R1@b{i}") for i, (kd, L, top, _k) in enumerate(ps)]
    old = X.Panel("P532-R1", "GF", tuple(pcs), (), course)
    new = X.Panel("P532-R1", "GF", tuple(pcs) + (X.make_piece("COLUMN", 0.30, None, "R1@END1"),), (), course)
    assert [(t["column_at"], t["ties"]) for t in X.ties(old)] == [("R1@0.000", 5)]
    assert [(t["column_at"], t["face"], t["ties"]) for t in X.ties(new)] == [
        ("R1@0.000", "column_end", 5), ("R1@END1", "column_start", 4)]
    sides = (M.Side("INT-A", "PLASTER", 0.10, 3.40), M.Side("INT-B", "PLASTER", 0.10, 3.40))
    under = {"FACE": "SLAB", "BEAM": "BEAM"}
    mp = [M.Piece("COLUMN", L, None, "C0") if kd == "COLUMN" else M.Piece("BLOCK", L, top, k, (), under[k])
          for kd, L, top, k in ps]
    w0 = M.make_wall("P532-R1", 3.50, mp, sides)
    w1 = M.make_wall("P532-R1", 3.50, mp + [M.Piece("COLUMN", 0.30, None, "K1")], sides)
    v = lambda w: sorted((j["at"], j["length_m"]) for j in M.joints_to_soffit(w, 0.10) if j["dir"] == "V")
    assert v(w0) == [("C0", 3.20), ("C0", 3.20)]
    assert v(w1) == [("C0", 3.20), ("C0", 3.20), ("K1", 2.80), ("K1", 2.80)]
    mod = (0.39, 0.19, 0.40, 0.20)
    assert PJ.kappa(mod) == pytest.approx(0.92625, abs=1e-12)
    pj = [PJ.Piece("COLUMN" if kd == "COLUMN" else "BLOCK", L, top, k) for kd, L, top, k in ps]
    before = PJ.measure(PJ.Wall("P532-R1", T, J, mod, pj, "C", "F"))["m3"]
    after = PJ.measure(PJ.Wall("P532-R1", T, J, mod, pj, "C", "C"))["m3"]
    assert after - before == pytest.approx(0.92625 * 0.20 * 0.010 * (2.90 - 0.010), abs=1e-12)
    assert after - before == pytest.approx(0.005353725, abs=1e-10)


def test_kind_table_roles_and_provenance():
    assert {k: V3.role(k)[0] for k in ("BLOCK", "BEAM", "FACE", "NONE", "COLUMN", "ST_COLUMN")} == {
        "BLOCK": "MASONRY", "BEAM": "MASONRY", "FACE": "MASONRY", "NONE": "MASONRY",
        "COLUMN": "CONCRETE", "ST_COLUMN": "CONCRETE"}
    for k, (_r, _h, src) in V3.KIND_MAP.items():
        assert src, k                                   # every mapping names its source
    assert V3.role("LINTEL")[0] == "UNKNOWN"            # never guessed
    with pytest.raises(V3.EndCensusError):
        V3.role("")


def test_unknown_kind_is_held_by_name_never_skipped():
    js = V3.end_junctions_v3("P532-R1", ["COLUMN", "GLAZING", "BEAM"], ends())
    held = [j for j in js if j["state"] == "HELD"]
    assert [(j["at"], j["class"]) for j in held] == [("piece 0/1", "COLUMN-GLAZING"), ("piece 1/2", "GLAZING-BEAM")]
    assert all("'GLAZING'" in j["held"] for j in held)
    js = V3.end_junctions_v3("P532-R1", ["COLUMN", "FACE", "XYZ"], ends())
    end = [j for j in js if j["source"] == "V3_END"]
    assert end[0]["state"] == "HELD" and "'XYZ'" in end[0]["held"]


def test_masonry_masonry_and_concrete_concrete_are_not_junctions():
    js = V3.end_junctions_v3("R", ["BEAM", "FACE", "NONE", "BEAM"], ends(own_start=False, cols=()))
    assert js == []
    js = V3.end_junctions_v3("R", ["COLUMN", "ST_COLUMN", "BEAM"], ends(cols=()))
    assert [(j["class"], j["face"]) for j in js] == [("ST_COLUMN-BEAM", "column_end")]


def test_st_column_interior_is_listed():
    js = V3.end_junctions_v3("R", ["BEAM", "ST_COLUMN", "FACE"], ends(own_start=False, cols=()))
    assert [(j["class"], j["column_piece"], j["face"]) for j in js] == [
        ("BEAM-ST_COLUMN", 1, "column_start"), ("ST_COLUMN-FACE", 1, "column_end")]


@pytest.mark.parametrize("deg", [0.0, 37.0, 90.0, 213.5])
@pytest.mark.parametrize("mirror", [False, True])
def test_rotation_mirror_and_reversal_invariant(deg, mirror):
    def tf(g):
        g = affinity.scale(g, -1.0, 1.0, origin=(0, 0)) if mirror else g
        return affinity.rotate(g, deg, origin=(0, 0))

    def pt(p):
        return tuple(tf(Polygon([p, (p[0] + 1e-9, p[1]), (p[0], p[1] + 1e-9)])).exterior.coords[0])
    a, b = pt(A), pt(B)
    base = V3.end_junctions_v3("R", KINDS, ends(a, b, (tf(K1),)))
    assert [(j["class"], j["state"]) for j in base] == [("COLUMN-FACE", "LISTED"), ("BEAM-END_COLUMN", "LISTED")]
    rev_ends = [V3.classify_end(b, a, T, 0, [tf(K1)], J), V3.classify_end(b, a, T, 1, [tf(K1)], J, own_piece_is_column=True)]
    rev = V3.end_junctions_v3("R", KINDS[::-1], rev_ends)
    assert sorted((j["source"], j["state"]) for j in rev) == sorted((j["source"], j["state"]) for j in base)
    assert [(j["class"], j.get("face")) for j in rev] == [("FACE-COLUMN", "column_start"), ("BEAM-END_COLUMN", None)]


def test_inconsistent_inputs_raise_and_units_refused():
    with pytest.raises(V3.EndCensusError):          # column beyond the end of a column piece
        V3.end_junctions_v3("R", ["BEAM", "COLUMN"], [ends()[1], ends()[1]][::-1])
    with pytest.raises(V3.EndCensusError):          # COLUMN_PIECE_IN_RUN but the end piece is masonry
        V3.end_junctions_v3("R", ["BEAM", "FACE"], ends())
    with pytest.raises(V3.EndCensusError):
        V3.end_junctions_v3("R", [], ends())
    with pytest.raises(V3.EndCensusError):
        V3.end_junctions_v3("R", KINDS, ends()[:1])
    with pytest.raises(V3.EndCensusError):          # a held end needs its reason
        V3.end_junctions_v3("R", ["BEAM"], [V3.EndResult("NO_COLUMN", None, 0, None, None, False),
                                            V3.EndResult("GAP_HELD", 0.02, 1.0, T, 0, None, "")])
    with pytest.raises(V3.EndCensusError):
        V3.classify_end(A, B, 200, 1, [K1], J)       # thickness in mm
    with pytest.raises(V3.EndCensusError):
        V3.classify_end(A, B, T, 1, [K1], 10)        # joint in mm


def test_partial_and_gapped_ends_stay_held():
    half = box(3.30, 0.0, 3.60, 0.40)
    E = [V3.classify_end(A, B, T, 0, [C0], J, own_piece_is_column=True), V3.classify_end(A, B, T, 1, [half], J)]
    js = V3.end_junctions_v3("R", KINDS, E)
    assert js[-1]["class"] == "BEAM-PARTIAL_COLUMN" and js[-1]["state"] == "HELD" and "0.0995" in js[-1]["held"]
    gap = box(3.315, -0.20, 3.615, 0.20)
    E = [E[0], V3.classify_end(A, B, T, 1, [gap], J)]
    js = V3.end_junctions_v3("R", KINDS, E)
    assert js[-1]["class"] == "BEAM-GAP_HELD" and "15.0 mm" in js[-1]["held"]
