"""T-178 lessons into rules and tests (ENGINEERING_REASONING_STANDARD section 4 B / C), research only.

Pure helper functions for the seven lessons of discrepancies already resolved by merged, checker-verified pieces.
Nothing here is wired, no engine module is edited or imported at module level, no quantity of any BOQ changes.
Each helper states one general rule (any villa); the regression tests are in tests/t178_lessons. Where a merged module
already implements the rule (dome ring T-160, facade composer T-159, release baseline T-165, masonry V2 T-169) the
tests call that module and this file holds only what the merged code does not expose as a function.

Metres in, metres out. A value the evidence does not establish is None (HELD / NOT_ESTABLISHED), never 0.
"""
from __future__ import annotations

import math

# ---------------------------------------------------------------------------------------------- lesson 2 (T-119 r2)
POSITIONS = ("DOWNSTAND", "UPSTAND")


def column_height(interval_m, members, slab_t_m):
    """URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 as a function (T-119 r2, merged 0f32ff8).

    Column concrete height = structural storey interval - the depth hanging below the slab top of the DEEPEST member
    framing into THIS column (slab t when none; never one global depth for every column).
    members: [{"id", "depth_m", "position": DOWNSTAND | UPSTAND | None}]. A DOWNSTAND hangs its full depth; an UPSTAND
    stands on the slab and hangs only the slab t; position None = the section does not show which side of the slab the
    member is on: the height is HELD as the range between both readings (never a guess, never 0).
    -> {"status": DRAWING-CONFIRMED | HELD, "height_m" or None, "range_m": (lo, hi) | None, "controlling": id | None}"""
    if interval_m is None or slab_t_m is None:
        return {"status": "HELD", "height_m": None, "range_m": None, "controlling": None,
                "why": "storey interval or slab thickness not established"}
    known, unknown = [], []
    for m in members:
        if m.get("depth_m") is None:
            return {"status": "HELD", "height_m": None, "range_m": None, "controlling": None,
                    "why": f"member {m.get('id')} has no printed depth"}
        if m.get("position") is None:
            unknown.append(m)
        elif m["position"] in POSITIONS:
            known.append(m)
        else:
            raise ValueError(f"unknown member position {m['position']!r}")

    def hang(m, pos):
        return m["depth_m"] if pos == "DOWNSTAND" else slab_t_m

    base = max([(slab_t_m, None)] + [(hang(m, m["position"]), m["id"]) for m in known], key=lambda x: x[0])
    if not unknown:
        return {"status": "DRAWING-CONFIRMED", "height_m": interval_m - base[0], "range_m": None,
                "controlling": base[1], "hang_m": base[0]}
    deep = max([base] + [(hang(m, "DOWNSTAND"), m["id"]) for m in unknown], key=lambda x: x[0])
    shallow = max([base] + [(hang(m, "UPSTAND"), m["id"]) for m in unknown], key=lambda x: x[0])
    return {"status": "HELD", "height_m": None, "range_m": (interval_m - deep[0], interval_m - shallow[0]),
            "controlling": None, "why": "member position (upstand / downstand) not shown: "
            + ", ".join(m["id"] for m in unknown)}


def joint_m3(column_area_m2, hang_m, slab_t_m):
    """URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1: the column-beam joint = column area x (D_ctrl - t)."""
    return column_area_m2 * (hang_m - slab_t_m)


# ---------------------------------------------------------------------------------------------- lesson 4 (T-142 D3)
def strip_blinding_range(centre_to_centre_m, a_half_m, b_half_true_m, b_half_max_m, width_m, t_m):
    """Blinding under a ground beam / strap that runs from footing A (outline drawn, half extent a_half along the
    strip) to footing B. The strip's own blinding stops at both footing faces (the footing blinding is counted with the
    footing: no double count).

    b_half_true_m: B's half extent when B has an outline on the plan; None when the reader bound no outline to B.
    b_half_max_m:  the largest half extent B can have where its outline may lie (the search window around its label,
                   member_detection / route_g_scope_v1 REACH); None when not even that is known.
    -> {"status": DRAWING-CONFIRMED | HELD, "m3", "low_m3", "high_m3"}:
       outline drawn -> one value; no outline -> HELD range: high = strip to B's centre (nothing merged), low = B at its
       largest possible extent; no window -> low NOT_ESTABLISHED (None), never the high value and never 0.
    General rule (T-142 D3): a HELD range must CONTAIN the physical value; its lower bound comes from the largest
    footing the evidence allows, never from the unmerged strip."""
    k = width_m * t_m
    if b_half_true_m is not None:
        L = centre_to_centre_m - a_half_m - b_half_true_m
        if L < 0:
            raise ValueError("footings overlap along the strip")
        return {"status": "DRAWING-CONFIRMED", "m3": L * k, "low_m3": None, "high_m3": None}
    high = (centre_to_centre_m - a_half_m) * k
    low = None if b_half_max_m is None else max(0.0, centre_to_centre_m - a_half_m - b_half_max_m) * k
    return {"status": "HELD", "m3": None, "low_m3": low, "high_m3": high,
            "why": "footing B has no outline: strip end not established"}


def range_contains(low, high, value, tol=1e-9):
    """a HELD range is valid evidence only if it contains the physical value; an open low end (None) is not a bound."""
    if high is None or value is None:
        return False
    return (low is None or low <= value + tol) and value <= high + tol


# ---------------------------------------------------------------------------------------------- lesson 7 (T-157)
def porch_surfaces(floor_poly, floor_holds, soffit_poly, soffit_holds=()):
    """The floor and the soffit of a covered outdoor space are TWO surfaces of different scope (T-157 / T-121):
    floor  = the space's ground-plan boundary (walls, steps, landing) minus what stands on it (a wall stub, a planter);
    soffit = the outline of the plate over it (slab edge, beam faces) minus what hangs in it (downstand beam soffits,
             a void).
    Neither is copied from the other; the difference is named by component:
    floor_only = floor - soffit (e.g. a step or landing outside the slab edge), soffit_only = soffit - floor (e.g. the
    slab over a wall stub or over a planter), so floor - floor_only + soffit_only = soffit (re-add check).
    Polygons as [(x, y), ...] in metres."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    def net(poly, holds):
        p = Polygon(poly)
        if holds:
            p = p.difference(unary_union([Polygon(h) for h in holds]))
        return p

    f = net(floor_poly, floor_holds)
    s = net(soffit_poly, soffit_holds)
    fo, so = f.difference(s).area, s.difference(f).area
    return {"floor_m2": f.area, "soffit_m2": s.area, "floor_only_m2": fo, "soffit_only_m2": so,
            "readd_m2": f.area - fo + so}
