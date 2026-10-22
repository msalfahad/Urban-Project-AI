"""T-154: reconcile two measurements of one soffit (a hand set from printed dimensions and a CAD set) term by term.

Generic (nothing here names a project, a layer or a coordinate). A measurement is a shapely polygon in one local frame.

    decompose(hand, cad, zones, opened=None) -> terms
        hand    the hand-measured soffit (gross, before any void)
        cad     the CAD set as measured (after any morphological clean-up)
        zones   ordered {name: polygon}: where a CAD-only piece lies decides its term (first zone wins);
                CAD-only area outside every zone is the term "OTHER CAD-ONLY" (it must be named before use)
        opened  the CAD set before its clean-up (erosion / dilation); the difference is the term "CLEAN-UP ROUNDING"
        hand_only_zones  ordered {name: polygon} for hand-only pieces (e.g. a column face the CAD set dropped)
    Returns rows (term, m2, sign) whose signed sum turns the hand figure into the CAD figure; reconcile() asserts the
    re-add to `tol` and returns the residual.

    python3 -I t154_reconcile.py --check     synthetic, hand-calculated fixture (not any project): see check()
"""
from __future__ import annotations

import math
import sys

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

EPS = 1e-9


def decompose(hand, cad, zones, opened=None, hand_only_zones=None):
    rows = []
    base = opened if opened is not None else cad
    extra = base.difference(hand)
    used = None
    for name, z in zones.items():
        part = extra.intersection(z if used is None else z.difference(used))
        used = z if used is None else used.union(z)
        rows.append((name, part.area, +1))
    rest = extra.difference(used) if used is not None else extra
    rows.append(("OTHER CAD-ONLY", rest.area, +1))
    missing = hand.difference(base)
    used = None
    for name, z in (hand_only_zones or {}).items():
        part = missing.intersection(z if used is None else z.difference(used))
        used = z if used is None else used.union(z)
        rows.append((name, part.area, -1))
    rest = missing.difference(used) if used is not None else missing
    rows.append(("OTHER HAND-ONLY", rest.area, -1))
    if opened is not None:
        rows.append(("CLEAN-UP ROUNDING", opened.area - cad.area, -1))
    return rows


def reconcile(hand, cad, rows, tol=0.005):
    total = hand.area + sum(s * a for _, a, s in rows)
    resid = cad.area - total
    if abs(resid) > tol:
        raise AssertionError(f"terms do not re-add: hand {hand.area:.4f} + terms = {total:.4f} vs CAD {cad.area:.4f}")
    return resid


def opening(g, width):
    """the clean-up a CAD census applies: strips narrower than `width` are removed (erode then dilate by width / 2)."""
    return g.buffer(-width / 2).buffer(width / 2).intersection(g)


# ---------------------------------------------------------------- synthetic fixture (hand-calculated, not a project)
def _fixture(scale=1.0, mirror=False, quarter=0):
    """A court 3.000 x 4.000 m between wall faces, bounded east and north by 0.200 m walls (each with one opening
    under the slab), a 0.150 m recess between a straight frame line and the west court face, a column 0.250 x 0.300
    standing ABOVE the slab (its face drawn on the slab sheet, dropped by the CAD census), a void 1.000 x 1.200 inside.
    Hand by printed dimensions:
      hand gross            3.000 x 4.000                           = 12.0000
      void                  1.000 x 1.200                           =  1.2000  -> hand net 10.8000
    CAD set = slab plate outside the facade outline = hand gross + east wall top (0.200 x 4.200 incl. the NE corner)
      + north wall top (3.000 x 0.200) + frame recess (0.150 x 4.000, stopping at the north wall face) - the planted-column face (0.250 x 0.300),
      then cleaned by `opening(.., 0.10)`: every convex corner of the opened set loses (1 - pi / 4) x 0.05^2.
      east 0.8400, north 0.6000, recess 0.6000, column -0.0750 -> 12.0000 + 2.0400 - 0.0750 = 13.9650 before clean-up."""
    hand = box(0, 0, 3.0, 4.0)
    cad0 = unary_union([box(-0.15, 0, 0, 4.0), box(0, 0, 3.2, 4.2)]).difference(box(1.0, 0, 1.25, 0.3))
    void = box(1.0, 1.4, 2.0, 2.6)
    zones = {"EAST WALL TOP": box(3.0, -1, 3.2, 4.2), "NORTH WALL TOP": box(0, 4.0, 3.0, 4.2),
             "FRAME RECESS": box(-0.15, -1, 0, 4.2)}
    hz = {"PLANTED COLUMN FACE": box(1.0, 0, 1.25, 0.3)}

    def t(g):
        if mirror:
            g = affinity.scale(g, -1, 1, origin=(0, 0))
        if quarter:
            g = affinity.rotate(g, 90 * quarter, origin=(0, 0))
        return affinity.scale(g, scale, scale, origin=(0, 0))
    hand, cad0, void = t(hand), t(cad0), t(void)
    zones = {k: t(v) for k, v in zones.items()}
    hz = {k: t(v) for k, v in hz.items()}
    cad = opening(cad0, 0.10 * scale)
    return hand, cad0, cad, void, zones, hz


def check():
    want = {"EAST WALL TOP": 0.84, "NORTH WALL TOP": 0.60, "FRAME RECESS": 0.60, "OTHER CAD-ONLY": 0.0,
            "PLANTED COLUMN FACE": 0.075, "OTHER HAND-ONLY": 0.0}
    corner = (1 - math.pi / 4) * 0.05 ** 2
    n_convex = 7          # 5 outer corners (the recess stops at the north wall face) + the 2 mouth corners of the column notch
    fails = 0
    for scale, mirror, quarter, label in [(1.0, False, 0, "metres"), (1.0, True, 0, "mirror"), (1.0, False, 1, "quarter turn"),
                                          (1000.0, False, 0, "millimetres"), (1000.0, True, 3, "mm mirror 3/4 turn")]:
        hand, cad0, cad, void, zones, hz = _fixture(scale, mirror, quarter)
        u2 = scale * scale
        rows = decompose(hand, cad, zones, opened=cad0, hand_only_zones=hz)
        got = {k: a / u2 for k, a, _ in rows}
        ok = all(abs(got[k] - v) < 1e-6 for k, v in want.items())
        round_got = got["CLEAN-UP ROUNDING"]
        ok &= abs(round_got - n_convex * corner) < 2e-4          # polygonised quarter circles
        resid = reconcile(hand, cad, rows, tol=0.005 * u2) / u2
        ok &= abs(resid) < 1e-9
        ok &= abs(hand.difference(void).area / u2 - 10.8) < 1e-9
        ok &= abs(cad0.area / u2 - 13.965) < 1e-9
        print(f"{label:22s} terms {[(k, round(v, 4)) for k, v in got.items()]} residual {resid:+.2e} -> {'PASS' if ok else 'FAIL'}")
        fails += not ok
    # missing data: an unnamed CAD-only piece must surface as OTHER CAD-ONLY, never vanish
    hand, cad0, cad, void, zones, hz = _fixture()
    rows = decompose(hand, cad0, {"EAST WALL TOP": zones["EAST WALL TOP"]}, hand_only_zones=hz)
    other = dict((k, a) for k, a, _ in rows)["OTHER CAD-ONLY"]
    ok = abs(other - 1.2) < 1e-9
    print(f"{'unnamed zones':22s} OTHER CAD-ONLY {other:.4f} (north 0.6000 + recess 0.6000) -> {'PASS' if ok else 'FAIL'}")
    fails += not ok
    # a wrong term must fail the re-add
    try:
        bad = [(k, a + (0.01 if k == 'FRAME RECESS' else 0), s) for k, a, s in decompose(hand, cad, zones, cad0, hz)]
        reconcile(hand, cad, bad, tol=0.005)
        print(f"{'wrong term':22s} not caught -> FAIL"); fails += 1
    except AssertionError:
        print(f"{'wrong term':22s} 0.010 m2 error caught by the re-add -> PASS")
    print("CHECK", "PASS" if not fails else f"FAIL ({fails})")
    return fails


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    print(__doc__)
