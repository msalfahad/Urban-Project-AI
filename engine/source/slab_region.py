"""SLAB REGION ENGINE (V1) - slab plate, openings and thickness from the slab plan's own line work. Never fitted to
any target area.

regions()   element lines (beam band edges, slab edges, arcs) + column outlines are noded into a planar arrangement
            by the TS01 topology engine (engine.source.topology: exact noding, half-edge faces, nested components as
            holes). Every bounded face (site) is classified from source evidence only:
              OPENING_VOID    the face holds a VOID label, or is crossed corner to corner by opening-layer lines (X)
              OPENING_STAIR   the face holds >= MIN_TREAD_LINES stair-layer lines (a stair drawn in the slab hole)
              PLATE           every other face of a plate component
            A connected component that holds no bound beam band (and does not lie inside one that does) is a
            DETAIL_REGION (a detail drawn on the sheet) and is excluded. Thickness: a printed 'T / nn' tag inside the
            face; when every tag on the sheet prints the same value the sheet thickness applies to untagged faces
            (SHEET_UNIFORM_PRINTED); differing tags without a face of their own -> BLOCKED.
            Closure audit: dangling line ends inside the plate, beam bands outside the plate. Any band tag outside
            the plate -> SLAB_OUTLINE_NOT_ESTABLISHED.
            The rings of the outer outline, of the openings and of the plate faces are returned (private key
            "_rings") for consumers that need polygons.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter

from . import topology as T

POLICY_ID = "SLAB_REGION_V1"
MIN_TREAD_LINES = 3
ARC_STEP_RAD = math.radians(5.0)


def cycle_points(arr, cyc) -> list:
    """The ring of a face cycle (arcs discretised every ARC_STEP_RAD)."""
    pts = []
    for k, fw in cyc:
        e = arr.edges[k]
        if e["kind"] == "S":
            pts.append(tuple(arr.nodes[e["n0"] if fw else e["n1"]]))
        else:
            pr = e["prim"]
            n = max(int((e["t1"] - e["t0"]) / ARC_STEP_RAD), 2)
            ts = [e["t0"] + (e["t1"] - e["t0"]) * i / n for i in range(n)]
            if not fw:
                ts = [e["t1"] - (e["t1"] - e["t0"]) * i / n for i in range(n)]
            pts += [tuple(pr.point(t)) for t in ts]
    return pts


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def regions(*, segments, arcs=(), columns=(), void_labels=(), opening_segments=(), stair_segments=(),
            thickness_tags=(), band_points=(), umm=1.0, eps=1.0) -> dict:
    """segments [(key, x1, y1, x2, y2)] element lines; arcs [(key, cx, cy, r, a0, a1)] (radians, CCW); columns
    [{"id", "polygon"}]; void_labels [(x, y)]; opening_segments / stair_segments [(key, x1, y1, x2, y2)];
    thickness_tags [{"t_cm", "x", "y"}]; band_points [(id, x, y)] centre points of bound beam bands."""
    items = [T.BoundaryItem(k, "SEGMENT", (x1, y1, x2, y2), "SLAB_LINE")
             for k, x1, y1, x2, y2 in segments if math.hypot(x2 - x1, y2 - y1) > eps]
    items += [T.BoundaryItem(k, "ARC", (cx, cy, r, a0, a1), "SLAB_LINE") for k, cx, cy, r, a0, a1 in arcs]
    for c in columns:
        p = c["polygon"]
        items += [T.BoundaryItem(f"{c['id']}#{i}", "SEGMENT", (p[i][0], p[i][1], p[(i + 1) % len(p)][0], p[(i + 1) % len(p)][1]),
                                 "COLUMN_OUTLINE") for i in range(len(p))]
    arr = T.build(items, eps)
    sites = T.sites_of(arr, "SLAB", "PLATE")
    uf = T._components(arr)
    comp = lambda cyc: uf.find(arr.edges[cyc[0][0]]["n0"])
    inside = lambda s, pt: T._winding(arr, s["cycle"], pt) != 0 and not any(T._winding(arr, hc, pt) != 0 for hc in s["hole_cycles"])
    outer = {}
    for k, f in enumerate(arr.faces):
        if f["area"] <= 0:
            c = comp(f["cycle"])
            if c not in outer or f["area"] < arr.faces[outer[c]]["area"]:
                outer[c] = k
    keep = {comp(s["cycle"]) for s in sites for _, x, y in band_points if inside(s, (x, y))}
    for c, k in sorted(outer.items()):                         # islands inside a kept component stay with it
        if c in keep:
            continue
        p0 = arr.nodes[arr.edges[arr.faces[k]["cycle"][0][0]]["n0"]]
        if any(comp(s["cycle"]) in keep and T._winding(arr, s["cycle"], p0) != 0 for s in sites):
            keep.add(c)
    detail = sorted(c for c in outer if c not in keep)
    kept_sites = [s for s in sites if comp(s["cycle"]) in keep]
    out_faces = []
    for s in kept_sites:
        b = s["bbox"]
        diag = math.hypot(b[2] - b[0], b[3] - b[1])
        role, why = "PLATE", None
        if any(inside(s, (x, y)) for x, y in void_labels):
            role, why = "OPENING_VOID", "VOID label inside the face"
        else:
            cross = sum(math.hypot(x2 - x1, y2 - y1) for _, x1, y1, x2, y2 in opening_segments
                        if inside(s, ((x1 + x2) / 2.0, (y1 + y2) / 2.0)))
            if diag > 0 and cross >= 1.5 * diag:
                role, why = "OPENING_VOID", "opening-layer cross over the face"
            elif sum(1 for _, x1, y1, x2, y2 in stair_segments if inside(s, ((x1 + x2) / 2.0, (y1 + y2) / 2.0))) >= MIN_TREAD_LINES:
                role, why = "OPENING_STAIR", "stair line work inside the face"
        tags = [t for t in thickness_tags if inside(s, (t["x"], t["y"]))]
        out_faces.append({"face": s["site_id"], "role": role, "why": why, "area_m2": round(s["area"] * umm * umm / 1e6, 6),
                          "tags_cm": sorted({t["t_cm"] for t in tags}), "_site": s})
    out_faces.sort(key=lambda f: f["face"])
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
    outside = [i for i, x, y in band_points if not any(inside(s, (x, y)) for s in kept_sites)]
    # dangling ends: an element line end that touches no other element line / column outline within eps,
    # inside the kept plate - a gap the arrangement could not close
    ends = Counter()
    for _, x1, y1, x2, y2 in segments:
        ends[(round(x1, 3), round(y1, 3))] += 1
        ends[(round(x2, 3), round(y2, 3))] += 1
    lines = [((x1, y1), (x2, y2)) for _, x1, y1, x2, y2 in segments]
    for c in columns:
        p = c["polygon"]
        lines += [(p[i], p[(i + 1) % len(p)]) for i in range(len(p))]
    dangles = []
    for (ex, ey), k in sorted(ends.items()):
        if k != 1 or not any(inside(s, (ex, ey)) or T._dist_to_cycle(arr, s["cycle"], (ex, ey)) <= eps for s in kept_sites):
            continue
        if sum(1 for a, b in lines if _seg_dist((ex, ey), a, b) <= eps) <= 1:
            dangles.append([ex, ey])
    outer_kept = [arr.faces[outer[c]]["cycle"] for c in sorted(keep) if c in outer]
    gross = sum(f["area_m2"] for f in out_faces)
    openings = sum(f["area_m2"] for f in out_faces if f["role"] != "PLATE")
    per = sum(T._cycle_perimeter(arr, cyc) for cyc in outer_kept) * umm / 1000.0
    op_per = sum(T._cycle_perimeter(arr, f["_site"]["cycle"]) for f in out_faces if f["role"] != "PLATE") * umm / 1000.0
    vol_state = "COMPUTED" if plate_faces and all(f["t_cm"] for f in plate_faces) and not outside else "BLOCKED"
    vol = round(sum(f["area_m2"] * f["t_cm"] / 100.0 for f in plate_faces), 6) if vol_state == "COMPUTED" else None
    rings = {"outer": [cycle_points(arr, cyc) for cyc in outer_kept],
             "openings": [cycle_points(arr, f["_site"]["cycle"]) for f in out_faces if f["role"] != "PLATE"],
             "plate_faces": [cycle_points(arr, f["_site"]["cycle"]) for f in plate_faces]}
    for f in out_faces:
        f.pop("_site", None)
    return {"policy": POLICY_ID, "faces": out_faces,
            "counts": dict(Counter(f["role"] for f in out_faces)), "detail_regions_excluded": len(detail),
            "plate_components": len(keep),
            "gross_outline_area_m2": round(gross, 6) if out_faces else None,
            "openings_area_m2": round(openings, 6),
            "net_plate_area_m2": round(gross - openings, 6) if out_faces else None,
            "perimeter_m": round(per, 6) if out_faces else None,
            "plate_perimeter_m": round(per + op_per, 6) if out_faces else None,
            "sheet_thickness_tags_cm": sheet_vals,
            "thickness_states": dict(Counter(f.get("thickness_state") for f in plate_faces)),
            "bands_outside_plate": outside, "dangling_line_ends": len(dangles), "_dangles": dangles,
            "closure": "CLOSED" if keep and not outside else "SLAB_OUTLINE_NOT_ESTABLISHED",
            "volume_state": vol_state, "volume_m3": vol, "_rings": rings}


def strip_private(rec) -> dict:
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "min_tread_lines": MIN_TREAD_LINES, "arrangement": "engine.source.topology (TS01)",
           "roles": ["PLATE", "OPENING_VOID", "OPENING_STAIR", "DETAIL_REGION (excluded)"],
           "thickness": ["PRINTED_IN_FACE", "SHEET_UNIFORM_PRINTED", "CONFLICTING_TAGS_IN_FACE", "SHEET_TAGS_DIFFER",
                         "NOT_PRINTED"],
           "never": ["a target area", "a bounding box as an outline", "a thickness not printed on the sheet"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
