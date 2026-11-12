"""T-720 rules (research, unwired; every villa): GROSS / COVERED FLOOR AREA per storey, the denominator of every per-m2
check (concrete m3 / m2, finish m2 / m2), measured from the drawing, never from a convention.

Physical element (ERS 2.1). The gross floor area of a storey is the plan area enclosed by the OUTER FACE of that storey's
external envelope: the external walls, the columns standing in or proud of them, and, where glazing is the envelope (a
curved or full-height glazing with no wall face across it), the outermost drawn glazing line. It is a physical plan area:
no municipal / permit convention (balcony halves, exempt shafts, ...) is applied; a convention, if one is ever needed,
is a separate HELD figure with its rule gap named (no-assumptions rule).

R-T720-1 GROSS TO THE OUTER FACE. Each storey's outline is closed by named handles of outer faces. Across a STRAIGHT
         opening in a STRAIGHT wall the wall's outer face line continues (the reveal and the frame set back from the face
         are inside the gross). Where no wall face crosses the opening (curved glazing bay), the outermost drawn glazing
         line is the face. Voids, shafts and stair wells inside the outline are NOT deducted (gross); they are named.
R-T720-2 ONE ROW PER BUILDING COMPONENT. Each separately closed building part (house, annex, roof structures) is its own
         row; the storey gross is their sum. A closed figure that is a SYMBOL (north arrow, title block, legend) is never
         floor area, whatever layer its lines sit on.
R-T720-3 COVERED vs OPEN. Ground outside a storey's envelope is COVERED_BY_FLOOR where the next storey's gross outline lies
         over it (overlay on the common column grid), COVERED_BY_SLAB only where a slab projection has its own closed
         outline, HELD where a slab projection is named without an outline (never 0, never assumed), else OPEN_TO_SKY.
         Overlaps are counted once (union, L-T703-1).
R-T720-4 PASSAGE APART. A passage closed only by thresholds (no door, no glazing) is outside the envelope (Q-67 A,
         conditional on the drawings): it is listed beside the gross with its own cover state, never inside the gross.
R-T720-5 RECONCILE. own gross = engine plate - (named closures the engine adds) - (symbols the engine reads as walls) +
         (named face differences); the residual after the named causes is stated in m2 and %; |residual| <= TOL_M2 is
         BALANCED, else RESIDUAL_NAMED when every m2 has a cause, else RESIDUAL_UNNAMED (and > 0.5 % fails acceptance).

Statuses (WORKFLOW_CONTROLS s.5 / UP-QTY-STATUS-001): DRAWING-CONFIRMED (outline closed by handles, own read), CITED
(another task's measure, not re-read here), HELD (named, no outline), EXCLUDED (symbol / not a floor).
"""
from __future__ import annotations

TOL_M2 = 0.005           # half a 0.10 x 0.10 tile: below the drawing precision of an outline
ACCEPT_PCT = 0.5         # task acceptance: residual per floor < 0.5 % or named

COVER_STATES = ("COVERED_BY_FLOOR", "COVERED_BY_SLAB", "HELD", "OPEN_TO_SKY")


def _poly(ring):
    from shapely.geometry import Polygon
    if ring is None:
        return None
    p = ring if hasattr(ring, "area") else Polygon(ring)
    if not p.is_valid or p.area <= 0:
        raise ValueError("an outline must be a valid closed polygon")
    return p


def gross(components):
    """R-T720-1 / -2. components: [{'id', 'kind': 'BUILDING' | 'SYMBOL', 'ring': [(x, y), ...] in metres or None}].
    -> {'rows': [...], 'gross_m2': float | None, 'state'}; a building part without a closed outline is HELD and makes the
    storey total None (missing is never 0); a symbol is EXCLUDED."""
    rows, total, held = [], 0.0, False
    for c in components:
        if c.get("kind") == "SYMBOL":
            rows.append({"id": c["id"], "state": "EXCLUDED", "m2": None, "why": "symbol, not a floor (R-T720-2)"})
            continue
        if c.get("ring") is None:
            rows.append({"id": c["id"], "state": "HELD", "m2": None, "why": "no closed outline (R-T720-1)"})
            held = True
            continue
        a = _poly(c["ring"]).area
        rows.append({"id": c["id"], "state": "DRAWING-CONFIRMED", "m2": a})
        total += a
    return {"rows": rows, "gross_m2": None if held else total, "state": "HELD" if held else "DRAWING-CONFIRMED"}


def cover(outside_ring, upper_rings, slabs=(), lower_envelope_rings=()):
    """R-T720-3. Ground of one piece (outside_ring), minus the lower storey's envelope, split by what lies over it:
    upper_rings = gross outlines of the storey above; slabs = [{'id', 'ring' or None}] slab projections.
    -> {state: m2} (each m2 once) + 'held' (named slabs without outline)."""
    from shapely.ops import unary_union
    ground = _poly(outside_ring)
    if lower_envelope_rings:
        ground = ground.difference(unary_union([_poly(r) for r in lower_envelope_rings]))
    up = unary_union([_poly(r) for r in upper_rings]) if upper_rings else None
    by_floor = ground.intersection(up) if up is not None else ground.difference(ground)
    rest = ground.difference(up) if up is not None else ground
    outlined = [_poly(s["ring"]) for s in slabs if s.get("ring") is not None]
    held = [s["id"] for s in slabs if s.get("ring") is None]
    by_slab = rest.intersection(unary_union(outlined)) if outlined else rest.difference(rest)
    open_ = rest.difference(by_slab)
    out = {"COVERED_BY_FLOOR": by_floor.area, "COVERED_BY_SLAB": by_slab.area,
           "OPEN_TO_SKY": None if held else open_.area, "open_to_sky_upper_bound_m2": open_.area, "held": held}
    return out


def passage(thresholds, doors=0, glazing=0):
    """R-T720-4: a passage is outside the envelope only when closed by thresholds alone."""
    if doors or glazing:
        return "INSIDE_ENVELOPE"
    if thresholds < 1:
        raise ValueError("a passage is bounded by at least one threshold")
    return "OUTSIDE_ENVELOPE"


def reconcile(own_m2, engine_m2, causes, tol=TOL_M2):
    """R-T720-5. causes: [(name, m2)] with own = engine + sum(causes) expected. -> record."""
    if own_m2 is None or engine_m2 is None:
        return {"state": "HELD", "residual_m2": None, "residual_pct": None}
    named = sum(m for _, m in causes)
    resid = own_m2 - engine_m2 - named
    gap = abs(own_m2 - engine_m2) / own_m2 * 100.0 if own_m2 else None
    rpct = abs(resid) / own_m2 * 100.0 if own_m2 else None
    if abs(resid) <= tol:
        state = "BALANCED" if not causes else "RESIDUAL_NAMED"
    else:
        state = "RESIDUAL_UNNAMED"
    return {"state": state, "own_minus_engine_m2": own_m2 - engine_m2, "named_m2": named, "residual_m2": resid,
            "gap_pct": gap, "residual_pct": rpct,
            "accept": state != "RESIDUAL_UNNAMED" or (rpct is not None and rpct < ACCEPT_PCT),
            "causes": [{"cause": n, "m2": m} for n, m in causes]}
