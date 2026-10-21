"""T-137: MEMBRANE_COVERAGE_PROOF_V1, an independent proof that a strip layout covers the membrane surface or declares
every piece it leaves as a patch. Synthetic, hand-calculated outlines only (none is the development villa). Roll
1.00 x 10.00 m, lap 0.10 m, upturn h 0.20 m (UP-WP-001 / 002 / 003).

Hand values used below (m, m2):
  R  rectangle 3.00 x 4.00: surface = floor 12.00 + flaps 2 x (3 + 4) x 0.20 = 2.80 + 4 mitred corner squares 0.04
     = 14.96; strips along the 4.00 m wall: across extent 3.00 + 0.40 = 3.40 -> ceil((3.40 - 0.10) / 0.90) = 4 bands.
  L  L shape (0,0) (4,0) (4,2) (2,2) (2,3.5) (0,3.5): one internal corner -> the two flaps share 0.20 x 0.20 = 0.04
     (ADJACENT double need).
  S  3.00 x 3.00 with a slot 0.10 wide, 1.50 deep (a wall stub 0.10 thick): the two slot faces' flaps share 1.50 x 0.10
     = 0.15 and each runs 0.10 over the floor beyond the stub: 2 x 1.50 x 0.10 = 0.30 -> OPPOSED 0.45; the slot end
     edge's flap meets each face flap in 0.10 x 0.20 = 0.02 -> ADJACENT 0.04.
  H  5.00 x 4.00 with a 0.60 x 0.60 opening: body 5.40 x 4.40 - 0.36 = 23.40; the opening's four 0.60 x 0.20 flaps
     inside it cover 0.36 - 0.20 x 0.20 = 0.32 -> surface 23.72; the flaps meet at the 4 opening corners: ADJACENT
     4 x 0.04 = 0.16.
  T  step parallel to the strips (R-07's miss): (0,0) (6,0) (6,1.70) (2,1.70) (2,2.00) (0,2.00). V2 strips only
     (MEMBRANE_FOLD_V2.strips): 3 bands (D = 2.40); band 1's sheet ends at y 1.70, band 2 holds floor only at x 0..2
     (its strip -0.20 .. 2.20); the step edge's upturn y 1.70 .. 1.90 is bare for x 2.20 .. 6.20 (mitred corner to
     6.20): residue 4.00 x 0.20 = 0.80, undeclared. V3 adds an upturn-only strip there: proven.
  N  T-096 fixture N: (0,0) (12,0) (12,4.6) (4,4.6) (4,2.5) (0,2.5): V2 strips leave x -0.20 .. 3.80 x 0.10 = 0.40.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from shapely import affinity  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

from engine.source import membrane_coverage_proof_v1 as P  # noqa: E402
from engine.source import membrane_fold_v2 as F2  # noqa: E402
from engine.source import membrane_fold_v3 as F3  # noqa: E402

SP = dict(F3.DEFAULT)
RECT = [(0, 0), (3, 0), (3, 4), (0, 4)]
L_SHAPE = [(0, 0), (4, 0), (4, 2), (2, 2), (2, 3.5), (0, 3.5)]
SLOT = [(0, 0), (3, 0), (3, 3), (1.55, 3), (1.55, 1.5), (1.45, 1.5), (1.45, 3), (0, 3)]
HOLE = ([(0, 0), (5, 0), (5, 4), (0, 4)], [[(2, 1.5), (2.6, 1.5), (2.6, 2.1), (2, 2.1)]])
STEP = [(0, 0), (6, 0), (6, 1.7), (2, 1.7), (2, 2.0), (0, 2.0)]
NOTCH = [(0, 0), (12, 0), (12, 4.6), (4, 4.6), (4, 2.5), (0, 2.5)]


def _v2_only(poly):
    """MEMBRANE_FOLD_V2's strips alone (no V3 upturn-only strips, no patches) as a layout to prove."""
    p = Polygon(poly)
    ss = F2.strips(p, SP["upturn_h_m"], SP["roll_width_m"], SP["roll_length_m"], SP["lap_m"])
    return p, [(s["x0"], s["s0"], s["x1"], s["s1"], "MAIN") for s in ss], [dict(s, kind="MAIN") for s in ss]


def _v3_layout(poly, holes=()):
    pf, _ = F3._frame(poly, holes, 1.0)
    p = F3._to_layout(pf, F3.ALONG_LONG, F3.LOWER)
    return p, F3.layout(p, SP)


# ------------------------------------------------------------------------------------------------ the surface
def test_surface_rectangle_by_hand():
    s = P.surface(RECT, (), 0.20)
    assert s["union"].area == pytest.approx(14.96, abs=1e-9)
    assert len(s["corners"]) == 4 and s["double_need"] == []


def test_surface_equals_v3_required_on_every_fixture():
    for poly, holes in [(RECT, ()), (L_SHAPE, ()), (SLOT, ()), HOLE, (STEP, ()), (NOTCH, ())]:
        p, _ = _v3_layout(poly, holes)
        outer, opening = F3.required(p, 0.20)
        v3 = unary_union([outer] + ([opening] if opening is not None else [])).area
        mine = P.surface(list(p.exterior.coords), [list(r.coords) for r in p.interiors], 0.20)["union"].area
        assert mine == pytest.approx(v3, abs=1e-6)


def test_surface_with_opening_by_hand():
    s = P.surface(*HOLE, 0.20)
    assert s["union"].area == pytest.approx(23.72, abs=1e-9)
    adj = sum(x["m2"] for x in s["double_need"] if x["kind"] == P.ADJACENT)
    assert adj == pytest.approx(0.16, abs=1e-9)


def test_double_need_internal_corner_and_thin_wall():
    s = P.surface(L_SHAPE, (), 0.20)
    assert [(x["kind"], x["m2"]) for x in s["double_need"]] == [(P.ADJACENT, 0.04)]
    s = P.surface(SLOT, (), 0.20)
    opp = sum(x["m2"] for x in s["double_need"] if x["kind"] == P.OPPOSED)
    adj = sum(x["m2"] for x in s["double_need"] if x["kind"] == P.ADJACENT)
    assert opp == pytest.approx(0.45, abs=1e-9) and adj == pytest.approx(0.04, abs=1e-9)


def test_surface_refuses_missing_or_broken_outline():
    with pytest.raises(ValueError):
        P.surface([(0, 0), (1, 0)], (), 0.2)
    with pytest.raises(ValueError):
        P.surface([(0, 0), (1, 1), (1, 0), (0, 1)], (), 0.2)   # a bow tie


# ------------------------------------------------------------------------------------------------ proofs by hand
def test_v2_strips_miss_the_step_upturn_and_v3_closes_it():
    p, sheets, strips = _v2_only(STEP)
    r = P.prove(p, sheets, strips, [], SP)
    assert r["verdict"] == P.FAILED
    assert [x["m2"] for x in r["residues"]] == [pytest.approx(0.80, abs=1e-9)]
    assert r["residues"][0]["box"] == (2.2, 1.7, 6.2, 1.9)
    assert any(f.startswith("UNDECLARED_RESIDUE") for f in r["failures"])
    pr = P.prove_fold(STEP)
    assert pr["verdict"] != P.FAILED
    assert pr["chosen_v213"]["verdict"] != P.FAILED and pr["chosen_v5"]["verdict"] != P.FAILED


def test_t096_fixture_n_v2_residue():
    p, sheets, strips = _v2_only(NOTCH)
    r = P.prove(p, sheets, strips, [], SP)
    assert r["residue_m2"] == pytest.approx(0.40, abs=1e-9)
    assert P.prove_fold(NOTCH)["verdict"] != P.FAILED


def test_rectangle_proven_and_band_bound():
    r = P.prove_fold(RECT)
    assert r["verdict"] == P.PROVEN
    first = r["v3"][0]
    assert first["bands_needed"] == 4 and first["bands"] >= 4
    assert first["residue_m2"] == 0 and first["surface_m2"] == pytest.approx(14.96)


@pytest.mark.parametrize("span,need", [(0.60, 1), (1.50, 2), (1.51, 3), (3.00, 4)])
def test_band_bound_exact_form(span, need):
    """D = span + 0.40; bound ceil((D - 0.10) / 0.90): D = 1.00 -> 1 and D = 1.90 -> 2 (R-07's ceil(D / 0.90) says 2
    and 3), D = 1.91 -> 3, D = 3.40 -> 4."""
    p, sheets, strips = _v2_only([(0, 0), (5, 0), (5, span), (0, span)])
    r = P.prove(p, sheets, strips, [], SP)
    assert r["bands_needed"] == need and r["bands"] == need and r["verdict"] == P.PROVEN


def test_slot_reported_as_opposed_faces_never_assumed():
    r = P.prove_fold(SLOT)
    assert r["verdict"] == P.PROVEN_DETAIL
    for x in r["v4"]:
        assert x["double_need_m2"][P.OPPOSED] == pytest.approx(0.45, abs=1e-9)


def test_splay_patches_all_matched():
    r = P.prove_fold([(0, 0), (3, 0), (3, 2), (2.4, 2.6), (0, 2.6)])
    assert r["verdict"] == P.PROVEN
    patched = [x for x in r["v4"] if x["patches"]]
    assert patched, "a 45 degree splay leaves corner pieces in some layout"
    assert all(q["state"] in ("MATCHED", "NUMERICAL") for x in r["v4"] for q in x["patches"])


def test_outline_narrower_than_one_strip():
    r = P.prove_fold([(0, 0), (2, 0), (2, 0.5), (0, 0.5)])
    assert r["verdict"] == P.PROVEN and r["v3"][0]["bands"] == 1


# ------------------------------------------------------------------------------------------------ mutations: defects are caught
def _rect_layout():
    p, lay = _v3_layout(RECT)
    return p, list(lay["_sheets"]), [dict(s) for s in lay["strips"]], list(lay["patches"])


def test_mutation_sheet_removed():
    p, sh, st, pa = _rect_layout()
    r = P.prove(p, sh[:-1], st[:-1], pa, SP)
    assert r["verdict"] == P.FAILED and any(f.startswith("UNDECLARED_RESIDUE") for f in r["failures"])


def test_mutation_strip_shorter_than_recorded():
    p, sh, st, pa = _rect_layout()
    x0, s0, x1, s1, k = sh[0]
    sh[0] = (x0, s0, x1 - 0.05, s1, k)
    r = P.prove(p, sh, st, pa, SP)
    assert any(f.startswith("STRIP_LENGTH") for f in r["failures"])
    assert any(f.startswith("UNDECLARED_RESIDUE") for f in r["failures"])


def test_mutation_side_lap_short():
    p, sh, st, pa = _rect_layout()
    sh = [(a, b + 0.05, c, d + 0.05, k) if s["band"] >= 1 else (a, b, c, d, k)
          for (a, b, c, d, k), s in zip(sh, st)]
    r = P.prove(p, sh, st, pa, SP)
    assert any(f.startswith("SIDE_LAP") for f in r["failures"])


def test_mutation_end_lap_short():
    """one strip cut in two with no end lap across the floor: a wet seam."""
    p, sh, st, pa = _rect_layout()
    x0, s0, x1, s1, k = sh[0]
    m = (x0 + x1) / 2
    sh2 = [(x0, s0, m, s1, k), (m, s0, x1, s1, k)] + sh[1:]
    st2 = [dict(st[0], length_m=m - x0, piece_lengths_m=[m - x0]),
           dict(st[0], length_m=x1 - m, piece_lengths_m=[x1 - m])] + st[1:]
    r = P.prove(p, sh2, st2, pa, SP)
    assert any(f.startswith("END_LAP") for f in r["failures"])


def test_mutation_patch_not_needed_and_wrong_area():
    p, sh, st, pa = _rect_layout()
    fake = {"kind": "OUTLINE_CORNER_PATCH", "m2": 0.25, "box": (1.0, 1.0, 1.5, 1.5), "along_m": 0.5, "across_m": 0.5}
    r = P.prove(p, sh, st, pa + [fake], SP)
    assert any(f.startswith("PATCH_WITHOUT_RESIDUE") for f in r["failures"])
    p, sh, st, pa = _rect_layout()
    x0, s0, x1, s1, k = sh[0]
    sh[0] = (x0 + 0.30, s0, x1, s1, k)                     # leaves 0.30 x width bare at the strip start
    st[0] = dict(st[0], length_m=x1 - x0 - 0.30, piece_lengths_m=[x1 - x0 - 0.30])
    hole = box(x0, s0, x0 + 0.30, s1).intersection(P.surface(list(p.exterior.coords), (), 0.2)["union"]).difference(
        unary_union([box(*s[:4]) for s in sh]))
    b = hole.bounds
    wrong = {"kind": "OUTLINE_CORNER_PATCH", "m2": round(hole.area / 2, 6), "box": b, "along_m": b[2] - b[0],
             "across_m": b[3] - b[1]}
    r = P.prove(p, sh, st, [wrong], SP)
    assert any(f.startswith("PATCH_AREA_MISMATCH") for f in r["failures"])
    right = dict(wrong, m2=round(hole.area, 6))
    assert P.prove(p, sh, st, [right], SP)["verdict"] == P.PROVEN


def test_mutation_surface_mismatch_reported():
    p, sh, st, pa = _rect_layout()
    r = P.prove(p, sh, st, pa, SP, v3_required_m2=14.90)
    assert any(f.startswith("SURFACE_MISMATCH") for f in r["failures"])


def test_frame_check_catches_a_wrong_frame():
    pf, td = F3._frame(L_SHAPE, (), 1.0)
    p = F3._to_layout(pf, F3.ALONG_LONG, F3.LOWER)
    ok, _ = P._frame_check(L_SHAPE, (), 1.0, p, F3._back(F3.ALONG_LONG, F3.LOWER), td)
    assert ok
    bad = affinity.translate(p, 0.01, 0.0)
    ok, info = P._frame_check(L_SHAPE, (), 1.0, bad, F3._back(F3.ALONG_LONG, F3.LOWER), td)
    assert not ok and info["max_corner_offset_m"] == pytest.approx(0.01, abs=1e-9)


# ------------------------------------------------------------------------------------------------ units, mirror, rotation
def _summary(r):
    return [(x["verdict"], round(x["surface_m2"], 3), round(x["residue_m2"], 4), round(x["declared_patch_m2"], 4),
             x["rolls_by_basis"]["Q58_B"]) for x in r["v3"]]


def test_mm_mirror_rotation_same_proof():
    base = P.prove_fold(L_SHAPE)
    mm = P.prove_fold([(x * 1000, y * 1000) for x, y in L_SHAPE], unit_m=0.001)
    assert _summary(mm) == _summary(base)
    mir = P.prove_fold([(-x, y) for x, y in L_SHAPE][::-1])
    assert sorted(_summary(mir)) == sorted(_summary(base))
    rot = P.prove_fold([(-y, x) for x, y in L_SHAPE])
    assert sorted(_summary(rot)) == sorted(_summary(base))
    t = math.radians(30)
    r30 = P.prove_fold([(x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)) for x, y in L_SHAPE])
    assert r30["verdict"] != P.FAILED
    assert [x["surface_m2"] for x in r30["v3"]] == pytest.approx([x["surface_m2"] for x in base["v3"]], abs=1e-3)


# ------------------------------------------------------------------------------------------------ generator
def _random_outline(rng):
    """a union of 1 - 3 axis-parallel rectangles on a 0.05 m grid that is one polygon without openings."""
    for _ in range(200):
        rs = []
        for _k in range(rng.randint(1, 3)):
            x0, y0 = rng.randint(0, 60) * 0.05, rng.randint(0, 60) * 0.05
            w, h = rng.randint(8, 70) * 0.05, rng.randint(8, 70) * 0.05
            rs.append(box(x0, y0, x0 + w, y0 + h))
        u = unary_union(rs)
        if isinstance(u, Polygon) and not u.interiors and u.is_valid:
            u = u.simplify(0)
            return [(round(x, 4), round(y, 4)) for x, y in list(u.exterior.coords)[:-1]]
    raise AssertionError("no outline generated")


@pytest.mark.parametrize("seed", range(24))
def test_generated_rectilinear_outlines_proven(seed):
    rng = random.Random(1370 + seed)
    ring = _random_outline(rng)
    r = P.prove_fold(ring)
    bad = [(x["name"], x["failures"]) for x in r["v4"] if x["verdict"] == P.FAILED]
    assert not bad, (ring, bad)
    for x in r["v4"]:
        assert x["bands"] >= x["bands_needed"]
        assert x["residue_m2"] == pytest.approx(sum(q["residue_m2"] for q in x["patches"]) + x["numerical_m2"],
                                                abs=F2.COVER_TOL_M2)


def test_policy_record_names_no_new_tolerance():
    rec = P.policy_record()
    assert rec["grid_m"] == 0.001 and rec["numerical_m2"]["value"] == F2.COVER_TOL_M2


def test_seam_under_the_next_band_is_closed():
    """a 45 degree chamfered outline whose V4 135-degree frame puts an upturn-only piece 0.112 m long against a main
    strip with 0.029 m of end lap: the seam lies inside the next band's side lap (y within its sheet), so it is
    closed by a third sheet and is not an END_LAP failure (found while building this proof)."""
    ring = [(3.2, 0.4), (0.65, 0.4), (0.35, 0.7), (0.35, 3.1), (0.9, 3.1), (0.9, 3.75), (2.7, 3.75), (2.7, 3.1),
            (3.2, 3.1)]
    r = P.prove_fold(ring)
    assert r["verdict"] != P.FAILED
    assert not [f for x in r["v4"] for f in x["failures"] if f.startswith("END_LAP")]


def _chamfered(rng):
    ring = _random_outline(rng)
    poly = Polygon(ring)
    c = rng.randrange(len(ring))
    d = rng.randint(2, 10) * 0.05
    x, y = ring[c]
    q = poly.difference(Polygon([(x - d, y), (x, y + d), (x + d, y), (x, y - d)]))
    if not isinstance(q, Polygon) or q.interiors:
        return ring, ()
    return [(round(a, 4), round(b, 4)) for a, b in list(q.simplify(0).exterior.coords)[:-1]], ()


def _with_column(rng):
    ring = _random_outline(rng)
    poly = Polygon(ring)
    m = poly.representative_point()
    s = rng.randint(4, 12) * 0.05
    hb = box(m.x - s / 2, m.y - s / 2, m.x + s / 2, m.y + s / 2)
    if not poly.buffer(-0.05).contains(hb):
        return ring, ()
    return ring, [list(hb.exterior.coords)[:-1]]


def _rotated(rng):
    ring = _random_outline(rng)
    t = math.radians(rng.uniform(1, 89))
    return [(x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)) for x, y in ring], ()


@pytest.mark.parametrize("kind,seed", [(k, s) for k in ("chamfer", "column", "rotated") for s in range(8)])
def test_generated_chamfer_column_rotated_proven(kind, seed):
    rng = random.Random(13700 + seed)
    ring, holes = {"chamfer": _chamfered, "column": _with_column, "rotated": _rotated}[kind](rng)
    r = P.prove_fold(ring, holes=holes)
    bad = [(x["name"], x["failures"]) for x in r["v4"] if x["verdict"] == P.FAILED]
    assert not bad, (ring, holes, bad)


def test_rotation_noise_at_an_opening_touching_the_outline_is_repaired_area_kept():
    """an opening whose corner touches the outline (valid as drawn); turning it can leave a 1e-13 m crossing: the
    surface repairs it only because the area is kept (4.00 x 3.00 - 0.5 x 2.00 x 1.00 = 11.00 m2)."""
    outer = [(0, 0), (4, 0), (4, 3), (0, 3)]
    hole = [(1.5, -1e-13), (2.5, 1.0), (0.5, 1.0)]
    s = P.surface(outer, [hole], 0.20)
    assert s["repaired_after_turn"] and s["floor"].area == pytest.approx(11.00, abs=1e-9)
    assert not P.surface(outer, [[(1.5, 0.0), (2.5, 1.0), (0.5, 1.0)]], 0.20)["repaired_after_turn"]
