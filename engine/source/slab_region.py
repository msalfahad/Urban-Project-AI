"""SLAB REGION ENGINE (V1) - slab plate, openings and thickness from the slab plan's own line work. Never fitted to
any target area.

regions()   element lines (beam band edges, slab edges; arcs discretised) + column outlines are noded and polygonised
            into faces. Faces are classified from source evidence only:
              OPENING_VOID    the face holds a VOID label, or is crossed corner to corner by opening-layer lines (X)
              OPENING_STAIR   the face holds >= MIN_TREAD_LINES stair-layer lines (a stair drawn in the slab hole)
              PLATE           every other face of a plate component
            A connected plate component that holds no bound beam band is a DETAIL_REGION (a detail drawn on the
            sheet) and is excluded. Thickness: a printed 'T / nn' tag inside the face; when every tag on the sheet
            prints the same value the sheet thickness applies to untagged faces (SHEET_UNIFORM_PRINTED); differing
            tags without a face of their own -> BLOCKED.
            Closure audit: dangling line ends inside the plate, beam bands or tags outside the plate. Any band tag
            outside the plate -> SLAB_OUTLINE_NOT_ESTABLISHED.

Project-agnostic; uses shapely (already a dependency of engine.source.topology_crosscheck).
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

POLICY_ID = "SLAB_REGION_V1"
MIN_TREAD_LINES = 3
ARC_STEP_RAD = math.radians(5.0)


def _arc_points(cx, cy, r, a0, a1):
    if a1 < a0:
        a1 += 2 * math.pi
    n = max(int((a1 - a0) / ARC_STEP_RAD), 2)
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def regions(*, segments, arcs=(), columns=(), void_labels=(), opening_segments=(), stair_segments=(),
            thickness_tags=(), band_points=(), umm=1.0, eps=1.0) -> dict:
    """segments [(key, x1, y1, x2, y2)] element lines; arcs [(key, cx, cy, r, a0, a1)]; columns [{"id", "polygon"}];
    void_labels [(x, y)]; opening_segments / stair_segments [(key, x1, y1, x2, y2)]; thickness_tags [{"t_cm", "x",
    "y"}]; band_points [(id, x, y)] centre points of bound beam bands (plate membership + detail exclusion)."""
    geoms = [LineString([(x1, y1), (x2, y2)]) for _, x1, y1, x2, y2 in segments if math.hypot(x2 - x1, y2 - y1) > eps]
    geoms += [LineString(_arc_points(cx, cy, r, a0, a1)) for _, cx, cy, r, a0, a1 in arcs]
    for c in columns:
        p = c["polygon"]
        geoms.append(LineString(list(p) + [p[0]]))
    noded = unary_union(geoms)
    faces = [f for f in polygonize(noded) if f.area > (eps * eps)]
    faces.sort(key=lambda f: (round(f.representative_point().x, 3), round(f.representative_point().y, 3)))
    plate_all = unary_union(faces) if faces else None
    comps = list(getattr(plate_all, "geoms", [plate_all])) if plate_all is not None else []
    bpts = [(i, Point(x, y)) for i, x, y in band_points]
    keep = [c for c in comps if any(c.buffer(eps).contains(p) for _, p in bpts)]
    detail = [c for c in comps if c not in keep]
    op = [LineString([(x1, y1), (x2, y2)]) for _, x1, y1, x2, y2 in opening_segments]
    st = [LineString([(x1, y1), (x2, y2)]) for _, x1, y1, x2, y2 in stair_segments]
    out_faces = []
    for i, f in enumerate(faces):
        if not any(c.buffer(eps).contains(f.representative_point()) for c in keep):
            continue
        inner = f.buffer(-eps)
        role, why = "PLATE", None
        if any(f.contains(Point(x, y)) for x, y in void_labels):
            role, why = "OPENING_VOID", "VOID label inside the face"
        else:
            diag = math.hypot(f.bounds[2] - f.bounds[0], f.bounds[3] - f.bounds[1])
            crossing = sum(l.intersection(inner).length for l in op if l.intersects(inner))
            if crossing >= 1.5 * diag and diag > 0:
                role, why = "OPENING_VOID", "opening-layer cross over the face"
            elif sum(1 for l in st if l.within(f.buffer(eps))) >= MIN_TREAD_LINES:
                role, why = "OPENING_STAIR", "stair line work inside the face"
        tags = [t for t in thickness_tags if f.contains(Point(t["x"], t["y"]))]
        out_faces.append({"face": i, "role": role, "why": why, "area_m2": round(f.area * umm * umm / 1e6, 6),
                          "tags_cm": sorted({t["t_cm"] for t in tags}), "_poly": f})
    sheet_vals = sorted({t["t_cm"] for t in thickness_tags})
    plate_faces = [f for f in out_faces if f["role"] == "PLATE"]
    for f in plate_faces:
        if len(f["tags_cm"]) == 1:
            f["t_cm"], f["thickness_state"] = f["tags_cm"][0], "PRINTED_IN_FACE"
        elif len(f["tags_cm"]) > 1:
            f["t_cm"], f["thickness_state"] = None, "CONFLICTING_TAGS_IN_FACE"
        elif len(sheet_vals) == 1:
            f["t_cm"], f["thickness_state"] = sheet_vals[0], "SHEET_UNIFORM_PRINTED"
        else:
            f["t_cm"], f["thickness_state"] = None, "NOT_PRINTED" if not sheet_vals else "SHEET_TAGS_DIFFER"
    plate = unary_union([f["_poly"] for f in plate_faces]) if plate_faces else None
    gross = unary_union([f["_poly"] for f in out_faces]) if out_faces else None
    outside = [i for i, p in bpts if not any(c.buffer(eps).contains(p) for c in keep)]
    # dangling ends: an element line end that touches no other element line / column outline (within eps), inside
    # the kept plate - a gap the polygoniser could not close
    ends = Counter()
    for _, x1, y1, x2, y2 in segments:
        ends[(round(x1, 3), round(y1, 3))] += 1
        ends[(round(x2, 3), round(y2, 3))] += 1
    others = [LineString([(x1, y1), (x2, y2)]) for _, x1, y1, x2, y2 in segments] + \
             [LineString(list(c["polygon"]) + [c["polygon"][0]]) for c in columns] + \
             [LineString(_arc_points(cx, cy, r, a0, a1)) for _, cx, cy, r, a0, a1 in arcs]
    dangles = []
    kept = unary_union(keep) if keep else None
    for (ex, ey), k in sorted(ends.items()):
        if k != 1 or kept is None:
            continue
        P = Point(ex, ey)
        if not kept.buffer(eps).contains(P):
            continue
        touching = sum(1 for g in others if g.distance(P) <= eps)
        if touching <= 1:
            dangles.append([ex, ey])
    vol_state = "COMPUTED" if plate_faces and all(f["t_cm"] for f in plate_faces) and not outside else "BLOCKED"
    net = round(plate.area * umm * umm / 1e6, 6) if plate is not None else None
    vol = round(sum(f["area_m2"] * f["t_cm"] / 100.0 for f in plate_faces), 6) if vol_state == "COMPUTED" else None
    for f in out_faces:
        f.pop("_poly", None)
    return {"policy": POLICY_ID, "faces": out_faces,
            "counts": dict(Counter(f["role"] for f in out_faces)), "detail_regions_excluded": len(detail),
            "plate_components": len(keep),
            "gross_outline_area_m2": round(gross.area * umm * umm / 1e6, 6) if gross is not None else None,
            "openings_area_m2": round(sum(f["area_m2"] for f in out_faces if f["role"] != "PLATE"), 6),
            "net_plate_area_m2": net, "perimeter_m": round(gross.length * umm / 1000.0, 6) if gross is not None else None,
            "plate_perimeter_m": round(plate.boundary.length * umm / 1000.0, 6) if plate is not None else None,
            "sheet_thickness_tags_cm": sheet_vals,
            "thickness_states": dict(Counter(f.get("thickness_state") for f in plate_faces)),
            "bands_outside_plate": outside, "dangling_line_ends": len(dangles), "_dangles": dangles,
            "closure": "CLOSED" if keep and not outside else "SLAB_OUTLINE_NOT_ESTABLISHED",
            "volume_state": vol_state, "volume_m3": vol, "_plate": plate, "_gross": gross}


def strip_private(rec) -> dict:
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "min_tread_lines": MIN_TREAD_LINES,
           "roles": ["PLATE", "OPENING_VOID", "OPENING_STAIR", "DETAIL_REGION (excluded)"],
           "thickness": ["PRINTED_IN_FACE", "SHEET_UNIFORM_PRINTED", "CONFLICTING_TAGS_IN_FACE", "SHEET_TAGS_DIFFER",
                         "NOT_PRINTED"],
           "never": ["a target area", "a bounding box as an outline", "a thickness not printed on the sheet"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
