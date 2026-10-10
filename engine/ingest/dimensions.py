"""Dimension-chain walker (PA05 §5).

Reading the number and owning the number are different facts.  Ownership
comes from extension-line termination: the entity whose endpoint or line
passes within tolerance of the extension origin, never from proximity to
the nearest object.
"""

from __future__ import annotations

import math

from engine.ingest import ids

DIM_TYPES = {"21": "LINEAR", "22": "ALIGNED", "20": "ORDINATE", "23": "ANGULAR_3PT", "24": "ANGULAR_2LN", "25": "RADIAL", "26": "DIAMETER"}
OWN_TOL_MM = 60.0
CHAIN_TOL_MM = 60.0


def _dist_point_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _owner(point, prims, entity_ids, tol=OWN_TOL_MM):
    """Entities terminating the extension line at `point`: endpoint hits rank above line hits."""
    px, py = point
    end_hits, line_hits = [], []
    for p in prims:
        if p.kind == "SEGMENT":
            if math.hypot(px - p.x1, py - p.y1) <= tol or math.hypot(px - p.x2, py - p.y2) <= tol:
                end_hits.append(entity_ids[p.object_id])
            elif _dist_point_segment(px, py, p.x1, p.y1, p.x2, p.y2) <= tol:
                line_hits.append(entity_ids[p.object_id])
        elif p.kind in ("ARC", "CIRCLE"):
            if abs(math.hypot(px - p.cx, py - p.cy) - p.radius) <= tol:
                line_hits.append(entity_ids[p.object_id])
    if end_hits:
        return {"ENTITIES": sorted(set(end_hits)), "TERMINATION": "ENDPOINT"}
    if line_hits:
        return {"ENTITIES": sorted(set(line_hits)), "TERMINATION": "ON_LINE"}
    return {"ENTITIES": [], "TERMINATION": "NONE"}


def _display(v):
    """The displayed number as the drawing shows it (display value = geometry x DIMLFAC), without float noise."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    r = round(f, 2)
    return str(int(r)) if abs(r - round(r)) < 1e-9 else f"{r:g}"


def walk(view_id, dims, prims, entity_ids, unit="mm"):
    """dims: DimensionObservation list inside the view; prims: non-dimension primitives of the view;
    entity_ids: object_id -> canonical entity id.  Returns the DIMENSION_CHAIN_REGISTER rows for the view."""
    rows = []
    for d in dims:
        t = DIM_TYPES.get(str(d.provenance.entity_type), "UNSUPPORTED_TYPE")
        origins = ((d.x1, d.y1), (d.x2, d.y2))
        if t in ("LINEAR", "ALIGNED"):
            a, b = _owner(origins[0], prims, entity_ids), _owner(origins[1], prims, entity_ids)
            axis = "x" if abs(d.y1 - d.y2) < CHAIN_TOL_MM else ("y" if abs(d.x1 - d.x2) < CHAIN_TOL_MM else "oblique")
            line_coord = round(d.y1) if axis == "x" else (round(d.x1) if axis == "y" else None)
        else:
            a = b = {"ENTITIES": [], "TERMINATION": "NOT_SUPPORTED"}
            axis, line_coord = "n/a", None
        own = "BOTH_OWNED" if a["ENTITIES"] and b["ENTITIES"] else ("ONE_OWNED" if a["ENTITIES"] or b["ENTITIES"] else ("UNOWNED" if t in ("LINEAR", "ALIGNED") else "NOT_SUPPORTED"))
        rows.append({"DIMENSION_ID": ids.dimension_id(view_id, origins, d.geometry_mm), "TYPE": t, "DISPLAY_TEXT": _display(d.display_value), "DISPLAY_FACTOR": getattr(d, "dimlfac", None), "MEASURED_VALUE_MM": round(d.geometry_mm, 2),
                     "OVERRIDE_TEXT": d.user_text or None, "TEXT_OVERRIDDEN": bool(d.user_text), "START_EXTENSION_OWNER": a, "END_EXTENSION_OWNER": b,
                     "DIMENSION_LINE": {"AXIS": axis, "COORD_MM": line_coord, "ORIGINS_MM": [[round(d.x1, 1), round(d.y1, 1)], [round(d.x2, 1), round(d.y2, 1)]]},
                     "CHAIN_ID": None, "VIEW": view_id, "UNIT": unit, "SOURCE_ENTITY_ID": f"handle:{d.provenance.handle}", "LAYER": d.provenance.layer,
                     "OWNER_STATUS": own, "READ_STATUS": "SOURCE_ESTABLISHED" if not d.user_text else "HUMAN_REVIEW"})
    # chains: same axis, same line coordinate (within tol), origins contiguous
    by_line = {}
    for r in rows:
        dl = r["DIMENSION_LINE"]
        if dl["AXIS"] in ("x", "y"):
            key = (dl["AXIS"], int(round(dl["COORD_MM"] / CHAIN_TOL_MM)))
            by_line.setdefault(key, []).append(r)
    for (axis, _), members in by_line.items():
        k = 0 if axis == "x" else 1
        members.sort(key=lambda r: min(r["DIMENSION_LINE"]["ORIGINS_MM"][0][k], r["DIMENSION_LINE"]["ORIGINS_MM"][1][k]))
        chain, prev_end = [], None
        chains = []
        for r in members:
            lo = min(r["DIMENSION_LINE"]["ORIGINS_MM"][0][k], r["DIMENSION_LINE"]["ORIGINS_MM"][1][k])
            hi = max(r["DIMENSION_LINE"]["ORIGINS_MM"][0][k], r["DIMENSION_LINE"]["ORIGINS_MM"][1][k])
            if prev_end is not None and abs(lo - prev_end) > CHAIN_TOL_MM:
                chains.append(chain); chain = []
            chain.append(r); prev_end = hi
        chains.append(chain)
        for c in chains:
            cid = ids.chain_id(view_id, axis, c[0]["DIMENSION_LINE"]["COORD_MM"], [r["DIMENSION_ID"] for r in c])
            for r in c:
                r["CHAIN_ID"] = cid
                r["CHAIN_LENGTH"] = len(c)
    return rows


def register(view_rows):
    all_rows = [r for rows in view_rows for r in rows]
    return {"ARTIFACT": "DIMENSION_CHAIN_REGISTER", "ROWS": all_rows,
            "COUNTS": {"TOTAL": len(all_rows), "BY_OWNER_STATUS": {s: sum(1 for r in all_rows if r["OWNER_STATUS"] == s) for s in ("BOTH_OWNED", "ONE_OWNED", "UNOWNED", "NOT_SUPPORTED")},
                       "BY_TYPE": {t: sum(1 for r in all_rows if r["TYPE"] == t) for t in set(r["TYPE"] for r in all_rows)}, "OVERRIDDEN": sum(1 for r in all_rows if r["TEXT_OVERRIDDEN"])},
            "PRINCIPLE": "reading the number and owning the number are different facts; ownership by extension-line termination only"}
