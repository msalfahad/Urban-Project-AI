"""FLOOR FACE TYPING AND CURVED FACES V1 (T-223). Pure, stdlib only, NOT wired into any method.

Three checks for the floor-area line of any villa, each from a finding on the development villa:

1. face_area(boundary) - the floor of a room bounded by a curved wall is the area to the DRAWN curved face: the
   polygon of its vertices plus (or minus) the circular segment of every arc edge (DXF bulge convention: bulge =
   tan(sweep / 4), positive = counter-clockwise arc). An arc edge with no radius / bulge (only its chord or only its
   end points) is REFUSED, never replaced by the chord or by the straight wall line (T-197 curved-geometry check R4).
   An edge whose source role is GLAZING is accepted as the room face only when a wall-layer face lies on the same
   curve (the wall jambs on the same radius); otherwise refused (a glazing line is not a wall face by itself).

2. type_space(space) - an UNLABELLED face is typed from its own evidence, every villa (proposed rule
   UP-SPACE-FACE-TYPE-001, scope: unlabelled faces of the architectural plan; provenance: UP-SPACE-001 1.0.0
   interior / exterior from enclosure and connectivity, UP-WET-002 1.3.0 wet evidence, Q-67 A, URBAN-FINISH-QUANTITY-
   INDEPENDENT-OF-MATERIAL@v1, URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1):
   - an opening to outside air with no door or glazing (an open end), or a project decision that binds it exterior
     (UP-SPACE-002, e.g. Q-67 A): EXTERIOR, never the internal floor line; its floor goes to the outdoor key;
   - a vertical shaft (a stack / riser / lift drawn above or below, or the same outline on the floors above / below,
     with no floor drawn): SHAFT, no floor line;
   - otherwise enclosed by walls and reached only from interior spaces (doors or open passages): INTERIOR; its area
     ENTERS the internal floor line (URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1: geometry is released even when
     the finish material is not source-proven), never ARCH.SPACE only;
   - its wet / dry class: WET only by a wet rule (a sanitary fixture of UP-WET-002, a drain on the drainage plan, an
     owner wet code); DRY when the drawing shows none of them; the finish MATERIAL stays HELD (never borrowed from the
     room it opens into) unless a material rule binds the class;
   - a box drawn on an annotation / furniture layer with no wall line and no counterpart above or below is joinery
     (the floor continues under it), never a shaft.

3. pair_row(parts, reference_m2, reference_lm) - a typed reference row (the freelancer's) is paired by TWO
   independent quantities, area AND perimeter (T-218 lesson); a reading that closes the area but not the perimeter
   (or the reverse) is NOT a pairing; the residual of each key is returned, never hidden.

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED / ASSUMED - OWNER-APPROVED / HELD / UNKNOWN; a missing input makes
the value HELD (None), never 0. Project-agnostic: no layer name, coordinate, room id or project name in code.
"""

from __future__ import annotations

import math

SCHEMA = "URBAN_FLOOR_FACE_TYPING_V1"
DC, AOA, HELD, UNKNOWN = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN"
UNIT_TO_M = {"m": 1.0, "mm": 0.001, "cm": 0.01}


class Refused(ValueError):
    """An input the method will not turn into a quantity."""


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------- 1 curved faces
def _bulge_from_arc(p, q, radius, side):
    """bulge of an arc of `radius` from p to q; side +1 = counter-clockwise (DXF positive), -1 = clockwise;
    the minor arc (sweep <= 180 deg)."""
    c = math.dist(p, q)
    if radius is None or radius <= 0:
        raise Refused("arc edge without a radius")
    if c > 2 * radius + 1e-9:
        raise Refused(f"chord {c:.4f} longer than the diameter {2 * radius:.4f}")
    half = math.asin(min(1.0, c / (2 * radius)))          # half the sweep
    return side * math.tan(half / 2.0)


def face_area(boundary, unit="m"):
    """boundary: list of edges {"p": (x, y), "kind": "LINE" | "ARC", "role": "WALL" | "GLAZING" | "COLUMN" | "CLOSE",
    "bulge": b (ARC, DXF convention) or "radius": R + "side": +1/-1 (ARC), "wall_on_same_curve": bool (GLAZING arcs)}.
    The edge runs from its p to the next edge's p (closed ring). Returns {"area_m2", "perimeter_m", "arcs": [...]}.
    Refused: an ARC with neither bulge nor radius (chord only), a GLAZING arc with no wall face on the same curve,
    fewer than 3 vertices, an unknown unit."""
    if unit not in UNIT_TO_M:
        raise Refused(f"unit {unit!r} not established")
    k = UNIT_TO_M[unit]
    if not boundary or len(boundary) < 3:
        raise Refused("a face needs at least three vertices")
    pts = [(e["p"][0] * k, e["p"][1] * k) for e in boundary]
    n = len(pts)
    shoe = 0.0
    seg_total = 0.0
    per = 0.0
    arcs = []
    for i, e in enumerate(boundary):
        p, q = pts[i], pts[(i + 1) % n]
        shoe += p[0] * q[1] - q[0] * p[1]
        c = math.dist(p, q)
        if e.get("kind", "LINE") == "LINE":
            per += c
            continue
        if e.get("role") == "GLAZING" and not e.get("wall_on_same_curve"):
            raise Refused("a glazing line is the room face only with a wall face on the same curve")
        b = e.get("bulge")
        if b is None:
            if e.get("radius") is None or e.get("side") not in (1, -1):
                raise Refused("curved face given by its chord only: radius / bulge required, the chord is refused")
            b = _bulge_from_arc(p, q, e["radius"] * k, e["side"])
        if b == 0:
            raise Refused("an ARC edge with zero bulge is a chord")
        sweep = 4.0 * math.atan(abs(b))
        R = c / (2.0 * math.sin(sweep / 2.0))
        seg = 0.5 * R * R * (sweep - math.sin(sweep))
        seg_total += math.copysign(seg, b)
        L = R * sweep
        per += L
        arcs.append({"radius_m": _r(R, 4), "sweep_deg": _r(math.degrees(sweep), 3), "chord_m": _r(c, 4),
                     "arc_m": _r(L, 4), "segment_m2": _r(seg, 4), "sense": "outward" if b > 0 else "inward"})
    signed = 0.5 * shoe
    # Green's theorem: each arc adds its segment with the sign of its own sense (CCW +), whichever way the ring runs
    area = abs(signed + seg_total)
    return {"area_m2": _r(area, 6), "perimeter_m": _r(per, 6), "polygon_m2": _r(abs(signed), 6), "arcs": arcs}


def chord_reading_refused(boundary):
    """The chord / straight-line substitute of a curved face is never a quantity: returns what it would give, so the
    report can name the difference, flagged REFUSED."""
    straight = [dict(e, kind="LINE") for e in boundary]
    v = face_area(straight)
    return {"area_m2": v["area_m2"], "perimeter_m": v["perimeter_m"], "status": "REFUSED",
            "why": "chord / straight wall line instead of the drawn arc (T-197 R4)"}


# --------------------------------------------------------------------------------------------------- 2 space typing
WET_EVIDENCE = ("WC", "SHOWER", "BATH_TUB", "FLOOR_DRAIN", "OWNER_WET_CODE")   # UP-WET-002: a basin alone is not wet
BASIN_ONLY = "BASIN"


def type_space(space):
    """space: {
        "id", "label": str|None,
        "decision": {"class": "EXTERIOR"|"INTERIOR", "source": "Q-.."} | None   (UP-SPACE-002 binding decision),
        "enclosed": bool | None            (every side a wall / door / glazing / open passage to an interior space),
        "open_end_to_outside": bool | None (an opening to outside air with no door, gate or glazing),
        "reached_from": [types of the spaces it opens into],
        "fixtures": [WET_EVIDENCE / BASIN codes inside],
        "drainage_checked": bool           (the drainage / sanitary plan was read for this face),
        "stack_above_or_below": bool | None, "floor_drawn_inside": bool | None,
        "boxes": [{"layer_role": "ANNOTATION"|"FURNITURE"|"WALL", "has_wall_line": bool,
                   "counterpart_above_or_below": bool}],
        "area_m2": float | None }
    -> {"class", "floor_line", "wet_dry", "material_status", "area_m2", "area_status", "joinery", "why": [...]}"""
    why = []
    area = space.get("area_m2")
    if area is not None and not (0 < area < 1000):
        raise Refused(f"face area {area} m2 out of range")
    dec = space.get("decision")
    out = {"id": space.get("id"), "area_m2": _r(area), "joinery": [], "why": why}
    if dec and dec.get("class") == "EXTERIOR":
        why.append(f"bound EXTERIOR by {dec.get('source')} (UP-SPACE-002)")
        out.update({"class": "EXTERIOR", "floor_line": "FLOOR.OUTDOOR", "wet_dry": None,
                    "material_status": "by the outdoor floor rule", "area_status": DC if area is not None else HELD})
        return out
    if space.get("open_end_to_outside"):
        why.append("an opening to outside air with no door or glazing (UP-SPACE-001 connectivity)")
        out.update({"class": "POSSIBLY_EXTERIOR", "floor_line": None, "wet_dry": None, "material_status": HELD,
                    "area_status": HELD})
        why.append("no binding decision: HELD until one binds it (UP-SPACE-002); never the internal floor line")
        return out
    if space.get("stack_above_or_below") and not space.get("floor_drawn_inside"):
        why.append("a stack / riser / lift drawn above or below and no floor inside: a shaft")
        out.update({"class": "SHAFT", "floor_line": None, "wet_dry": None, "material_status": None,
                    "area_status": DC if area is not None else HELD})
        return out
    if space.get("enclosed") is not True:
        why.append("enclosure not established")
        out.update({"class": UNKNOWN, "floor_line": None, "wet_dry": None, "material_status": HELD,
                    "area_status": HELD})
        return out
    reached = space.get("reached_from") or []
    if not reached or any(t not in ("INTERIOR", "DRY", "WET") for t in reached):
        why.append(f"reached from {reached}: not only interior spaces")
        out.update({"class": UNKNOWN, "floor_line": None, "wet_dry": None, "material_status": HELD,
                    "area_status": HELD})
        return out
    for b in space.get("boxes") or []:
        if b.get("layer_role") in ("ANNOTATION", "FURNITURE") and not b.get("has_wall_line") \
                and not b.get("counterpart_above_or_below"):
            out["joinery"].append(b)
        else:
            why.append("a box with a wall line or a counterpart above / below: possible shaft, HELD")
            out.update({"class": UNKNOWN, "floor_line": None, "wet_dry": None, "material_status": HELD,
                        "area_status": HELD})
            return out
    if out["joinery"]:
        why.append("box(es) on an annotation / furniture layer, no wall line, nothing above / below: joinery, the "
                   "floor continues under it (URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1)")
    fx = set(space.get("fixtures") or [])
    wet = sorted(fx & set(WET_EVIDENCE))
    if wet:
        cls = "WET"
        why.append(f"wet evidence {wet} (UP-WET-002)")
    elif fx == {BASIN_ONLY}:
        cls = None
        why.append("a basin alone does not make a space wet (UP-WET-002): class HELD")
    elif not space.get("drainage_checked"):
        cls = None
        why.append("no fixture drawn but the drainage plan was not read: class HELD")
    else:
        cls = "DRY"
        why.append("no sanitary fixture, no drain on the drainage plan: DRY")
    why.append("enclosed, reached only from interior spaces: INTERIOR (UP-SPACE-001); area enters the internal floor "
               "line (URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1), never ARCH.SPACE only")
    out.update({"class": "INTERIOR", "floor_line": "FLOOR.INTERNAL", "wet_dry": cls,
                "material_status": HELD, "area_status": DC if area is not None else HELD})
    if cls is None:
        out["floor_line"] = "FLOOR.INTERNAL (class HELD)"
    return out


# ------------------------------------------------------------------------------------------------ 3 row pairing
def pair_row(readings, reference_m2, reference_lm, tol_m2=0.005, tol_lm=0.01):
    """readings: [{"id", "m2", "lm", "physical": bool}] (each a complete reading of the engine-side element).
    -> every reading with its two residuals and whether it closes BOTH keys; "paired" names the readings that do
    (physical ones only); a reading closing one key only is listed with the key it fails."""
    rows = []
    for r in readings:
        da = None if r.get("m2") is None else _r(r["m2"] - reference_m2, 4)
        dl = None if r.get("lm") is None else _r(r["lm"] - reference_lm, 4)
        ca = da is not None and abs(da) <= tol_m2
        cl = dl is not None and abs(dl) <= tol_lm
        rows.append({"id": r["id"], "m2": _r(r.get("m2")), "lm": _r(r.get("lm")), "d_m2": da, "d_lm": dl,
                     "closes_area": ca, "closes_perimeter": cl, "physical": bool(r.get("physical")),
                     "verdict": "NOT A PAIRING" if not r.get("physical") else
                                ("PAIRED" if (ca and cl) else ("ONE KEY ONLY" if (ca or cl) else "NOT A PAIRING"))})
    paired = [x["id"] for x in rows if x["verdict"] == "PAIRED"]
    return {"reference_m2": reference_m2, "reference_lm": reference_lm, "readings": rows, "paired": paired,
            "closed": bool(paired)}
