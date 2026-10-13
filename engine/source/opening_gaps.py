"""OPENING GAPS WITH A UNIT-RELATIVE MERGE TOLERANCE (M9 S6, ARCH_TAKEOFF_V2) - opening_census.band_gaps merges the two
wall faces' covers across a break shorter than a literal 1.0 drawing unit: 1 mm in a millimetre drawing, but 1 m in a
metre drawing, where it closes every door gap. opening_census.py itself is not changed: its code digest is part of
the S8.6 lintel freeze (the S8.6 build script's CODE list; tests/lintels_s8_6 rebuild the package byte for byte).

    band_gaps(band, ..., merge_tol=1.0)

merge_tol == 1.0 calls opening_census.band_gaps itself (the frozen function, byte for byte); any other value runs the
same procedure with that merge tolerance, built from opening_census's own helpers. A caller measuring in unit_m passes
1e-3 / unit_m (1 mm in the drawing's unit), which is exactly 1.0 at millimetres. Project-agnostic; stdlib only.
"""

from __future__ import annotations

from engine.source import opening_census as OC

LEGACY_MERGE_TOL = 1.0


def band_gaps(band, min_gap=250.0, jamb_tol=30.0, obstacles=(), column_reach=60.0, closures=(), cover_ratio=0.9,
              merge_tol=LEGACY_MERGE_TOL):
    if merge_tol == LEGACY_MERGE_TOL:
        return OC.band_gaps(band, min_gap=min_gap, jamb_tol=jamb_tol, obstacles=obstacles, column_reach=column_reach,
                            closures=closures, cover_ratio=cover_ratio)
    lo, hi = band["lo"], band["hi"]
    A, B = OC._covers(band["A"]["cover"], lo, hi), OC._covers(band["B"]["cover"], lo, hi)
    both = OC._union([(a, b, ids) for a, b, ids in A + B], merge_tol)
    out = []
    for (_x0, e0, _ids0), (s1, _x1, _ids1) in zip(both, both[1:]):
        g = s1 - e0
        if g < min_gap:
            continue
        ends = {}
        for side, s in ((-1, e0), (1, s1)):
            fa = [t for t in A if (abs(t[1] - s) <= jamb_tol if side < 0 else abs(t[0] - s) <= jamb_tol)]
            fb = [t for t in B if (abs(t[1] - s) <= jamb_tol if side < 0 else abs(t[0] - s) <= jamb_tol)]
            col = OC._obstacle_at(band, s, side, obstacles, column_reach)
            if col is not None:
                ends[side] = (OC.COLUMN_JAMB, col)
            elif fa and fb:
                ends[side] = (OC.MASONRY_JAMB, None)
            else:
                cl = OC._closure_at(band, s, closures, jamb_tol, cover_ratio)
                ends[side] = (OC.CLOSURE_JAMB, cl) if cl is not None else (OC.UNBOUNDED, None)
        state = OC.OPENING if all(v[0] != OC.UNBOUNDED for v in ends.values()) else OC.REJECTED
        out.append({"band_id": band["band_id"], "s0": e0, "s1": s1, "width": g, "t": band["t"],
                    "start_jamb": ends[-1][0], "start_column": ends[-1][1],
                    "end_jamb": ends[1][0], "end_column": ends[1][1], "state": state})
    return out
