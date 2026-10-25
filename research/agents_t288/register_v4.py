"""R-T288-1: a wall height piece under a SUNKEN (lowered) slab panel (research rule, any villa; T-288).

Provenance: Verifier 2026-10-25 02:00 (GF-W16 / GF-W12 findings, own register-wide scan) + T-213 (MERGED d5df7d1f,
Checker-verified 2026-10-24 09:59: a sunken panel is the same slab lowered at FULL thickness, its soffit lower by the
drop d; d printed nowhere = designer item D-41) + Q-60 A (a block wall rises to the underside of the member over it) +
R-T274-1 (height pieces are an exact cut of the census length) + R-T285-1 (register revision rules). Nothing here edits
an engine module, a rule or knowledge file.

Physical element: a block wall rises from its floor to the underside of whatever is over it. Over a normal slab panel
that is storey - t; over a sunken panel the same slab sits d lower, so its underside is storey - t - d. A beam bounding
the panel keeps its own soffit (the panel steps down between the beams; T-213 'step = side of the bounding beams').

1. CLIP: a piece is under a sunken panel when the wall axis lies inside the panel region; the region is the sunken
   hatch with its annotation islands united back (T-213 rule (a): a tag / text island does not end the panel) and a
   gap between the hatch and a member face with nothing drawn in it closed (the panel is bounded by member faces).
   A face lying ON the panel edge is outside (presence is tested on the region shrunk SHRINK_M).
2. HEIGHT: such a piece takes storey - t - d with d HELD by name until printed; never storey - t, never 0. Only a drawing
   that shows a THINNED slab with a flush soffit gives storey - t (then the thickness printed for the panel is used).
3. CARRIED VALUE: a wall with such pieces carries 'U - L x d' where U = its net with d = 0 (an UPPER BOUND, not a
   quantity) and L = the summed length of its sunken pieces (m); state HELD on the drop; its d-free part is never
   presented as the wall's net. A register that books storey - t on a sunken piece is refused.
4. CLOSURE: the pieces of the wall still close its census length exactly (R-T274-1), the sunken pieces included.
5. A ruling on a level re-cuts every element whose top or bottom is that level (lessons register row, T-288).
"""
from __future__ import annotations

RULE_ID = "R-T288-1"
SHRINK_M = 0.020
CLOSE_TOL_M = 0.0005
HELD_ON_DROP = "HELD ON DROP"


class SunkenError(ValueError):
    """a piece or register row the rule refuses (the code is the first word of the message)."""


def clip_length(axis, region, shrink=SHRINK_M):
    """rule 1: (present, length_m) of a wall axis (shapely LineString, metres) under a sunken region (Polygon, metres).
    present uses the region shrunk by `shrink` (a face or axis ON the edge is not under the panel); length is the clip
    by the full region."""
    core = region.buffer(-shrink)
    present = axis.intersection(core).length > 0.0005
    return present, (round(axis.intersection(region).length, 6) if present else 0.0)


def panel_region(hatch_exterior, annotation_islands=(), member_gaps=()):
    """rule 1: the sunken region = hatch exterior U annotation islands U member gaps (all shapely polygons)."""
    from shapely.ops import unary_union
    u = unary_union([hatch_exterior, *annotation_islands, *member_gaps])
    if u.geom_type != "Polygon":
        raise SunkenError("REGION_SPLIT: an island or gap that does not touch the panel is not part of it")
    return u


def piece_height(storey_m, slab_t_m, sunken, thinned_flush_soffit=False):
    """rule 2: (height_m or None, held_name or None). A sunken piece is HELD on the drop d, never storey - t."""
    for v in (storey_m, slab_t_m):
        if v is None or v <= 0 or v > 20:
            raise SunkenError("BAD_LEVEL: storey and slab thickness are positive metres")
    if not sunken:
        return round(storey_m - slab_t_m, 6), None
    if thinned_flush_soffit:
        return round(storey_m - slab_t_m, 6), None
    return None, "drop d of the sunken panel (D-41)"


def wall_with_drop(census_m, pieces, deductions_m2=0.0):
    """rule 3 / 4: pieces [{length_m, height_m, sunken(bool)}] with the sunken pieces' height_m = storey - t (the d = 0
    bound). Returns {upper_m2, drop_length_m, state, expression}. Refuses pieces that do not close the census."""
    if census_m <= 0 or census_m > 200:
        raise SunkenError("BAD_UNITS: census length in metres")
    s = sum(p["length_m"] for p in pieces)
    if abs(s - census_m) > CLOSE_TOL_M:
        raise SunkenError(f"NOT_CLOSED: pieces {s:.4f} m vs census {census_m:.4f} m")
    for p in pieces:
        if p["length_m"] <= 0 or p.get("height_m") is None:
            raise SunkenError("BAD_PIECE: every piece has a positive length and a height (the d = 0 bound if sunken)")
    upper = sum(p["length_m"] * p["height_m"] for p in pieces) - deductions_m2
    L = sum(p["length_m"] for p in pieces if p.get("sunken"))
    if upper <= 0:
        raise SunkenError("NON_POSITIVE: the d = 0 bound of a wall is positive")
    state = HELD_ON_DROP if L > 0 else "ESTABLISHED"
    return {"upper_m2": round(upper, 6), "drop_length_m": round(L, 6), "state": state,
            "expression": (f"{upper:.4f} - {L:.4f} x d m2 (d HELD, D-41)" if L > 0 else f"{upper:.4f} m2")}


def check_register_row(row, sunken_length_m):
    """rule 3: a register row {wall_id, state, net_m2, drop_length_m} for a wall whose clip found `sunken_length_m` of
    axis under sunken panels. Refuses a row that carries a plain net (storey - t booked), a 0, or a wrong length."""
    row = {k[:-3] if k.endswith("_v4") else k: v for k, v in row.items()}   # register columns carry a _v4 suffix
    w = row.get("wall_id", "?")
    if sunken_length_m <= CLOSE_TOL_M:
        if row.get("drop_length_m"):
            raise SunkenError(f"DROP_WITHOUT_PANEL: {w} carries a drop term but no piece lies under a sunken panel")
        return True
    if row.get("state") != HELD_ON_DROP:
        raise SunkenError(f"NORMAL_SOFFIT_BOOKED: {w} has {sunken_length_m:.4f} m under a sunken panel but is carried "
                          f"as {row.get('state')!r} at the normal soffit (storey - t)")
    if row.get("net_m2") not in (None, ""):
        raise SunkenError(f"PLAIN_NET: {w} under a sunken panel carries no plain net (only U - L x d)")
    if row.get("upper_m2") in (None, "") or float(row["upper_m2"]) <= 0:
        raise SunkenError(f"HELD_AS_ZERO: {w} keeps its d = 0 bound (never 0, never blank)")
    if abs(float(row.get("drop_length_m") or 0) - sunken_length_m) > CLOSE_TOL_M:
        raise SunkenError(f"DROP_LENGTH: {w} drop length {row.get('drop_length_m')} vs clipped {sunken_length_m:.4f} m")
    return True
