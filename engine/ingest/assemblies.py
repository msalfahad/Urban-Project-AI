"""Hatch / block / structural object roles (PA06 WS9).

A HATCH is evidence about a region's material, never a wall face.  A BLOCK
instance keeps its INSERT (transform: scale, rotation, mirror) and its
transformed children; its role comes from geometry and context, with the
block name recorded as evidence only.  Columns exist independently of
their exposure; beams independently of wall ownership; stair treads
independently of the stairwell walls.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.ingest import ids

BLOCK_ROLES = ("DOOR_ASSEMBLY", "WINDOW_ASSEMBLY", "SANITARY_FIXTURE", "FURNITURE_OR_FITTING", "COLUMN_SYMBOL", "HATCH_PATTERN_BLOCK", "ANNOTATION_BLOCK",
               "STAIR_ASSEMBLY", "UNKNOWN_BLOCK")
NAME_HINTS = (("DOOR", "DOOR_ASSEMBLY"), ("WINDOW", "WINDOW_ASSEMBLY"), ("WC", "SANITARY_FIXTURE"), ("W.C", "SANITARY_FIXTURE"), ("WASH", "SANITARY_FIXTURE"),
              ("BASIN", "SANITARY_FIXTURE"), ("SINK", "SANITARY_FIXTURE"), ("TOILET", "SANITARY_FIXTURE"), ("BATH", "SANITARY_FIXTURE"), ("SHOWER", "SANITARY_FIXTURE"),
              ("BED", "FURNITURE_OR_FITTING"), ("SOFA", "FURNITURE_OR_FITTING"), ("TABLE", "FURNITURE_OR_FITTING"), ("CHAIR", "FURNITURE_OR_FITTING"),
              ("COL", "COLUMN_SYMBOL"), ("STAIR", "STAIR_ASSEMBLY"), ("OBLIQUE", "HATCH_PATTERN_BLOCK"), ("HATCH", "HATCH_PATTERN_BLOCK"))
COLUMN_SIDE = (150.0, 1200.0)


def block_objects(instances, prims, roles):
    """ASSEMBLY_OBJECT_REGISTER rows: one per block instance, with the roles of its transformed children."""
    children = defaultdict(list)
    for p in prims:
        ip = p.provenance.instance_path
        if ip:
            children[ip[0]].append(p)         # outermost placing INSERT handle
    rows = []
    for inst in instances:
        if inst.depth != 0:
            continue
        kids = children.get(inst.provenance.handle, [])
        kid_roles = defaultdict(int)
        for k in kids:
            r = roles.get(k.object_id)
            if r:
                kid_roles[r["ROLE"]] += 1
        n = len(kids)
        bbox = None
        if kids:
            xs = [v for k in kids for v in ((k.x1, k.x2) if k.kind == "SEGMENT" else (k.cx - k.radius, k.cx + k.radius))]
            ys = [v for k in kids for v in ((k.y1, k.y2) if k.kind == "SEGMENT" else (k.cy - k.radius, k.cy + k.radius))]
            bbox = [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]
        # geometry-first role
        role, ev, st = "UNKNOWN_BLOCK", [], "UNRESOLVED"
        if n and kid_roles.get("HATCH_STROKE", 0) >= 0.8 * n:
            role, ev, st = "HATCH_PATTERN_BLOCK", [f"{kid_roles['HATCH_STROKE']} of {n} children are hatch strokes"], "ESTABLISHED"
        elif kid_roles.get("DOOR_SWING", 0) >= 1:
            role, ev, st = "DOOR_ASSEMBLY", ["contains a door swing arc"], "ESTABLISHED"
        elif kid_roles.get("COLUMN_FACE", 0) >= 4:
            role, ev, st = "COLUMN_SYMBOL", ["contains a closed column loop"], "ESTABLISHED"
        elif n and (kid_roles.get("DIMENSION_LINE", 0) + kid_roles.get("DIMENSION_EXTENSION", 0)) >= 0.8 * n:
            role, ev, st = "ANNOTATION_BLOCK", ["dimension geometry"], "ESTABLISHED"
        elif bbox and (bbox[2] - bbox[0]) <= 1500 and (bbox[3] - bbox[1]) <= 1500 and n >= 3:
            role, ev, st = "FURNITURE_OR_FITTING", ["small closed symbol under 1.5 m"], "PROVISIONAL"
        name_hint = next((r for h, r in NAME_HINTS if h in inst.block_name.upper()), None)
        if name_hint:
            ev.append(f"block name suggests {name_hint} (evidence only)")
            if role == "UNKNOWN_BLOCK":
                role, st = name_hint, "PROVISIONAL"
            elif role == "FURNITURE_OR_FITTING" and name_hint == "SANITARY_FIXTURE":
                role = "SANITARY_FIXTURE"
        t = inst.transform
        rows.append({"ASSEMBLY_ID": ids.make_id("SPACE_SEED", "BLOCK", inst.block_name, [t.e, t.f], round(t.rotation, 4), tol=25.0).replace("SS-", "AS-"),
                     "BLOCK_NAME": inst.block_name, "INSERT_HANDLE": inst.provenance.handle, "INSERTION_MM": [round(t.e, 1), round(t.f, 1)],
                     "SCALE": [round(t.scale_x, 6), round(t.scale_y, 6)], "ROTATION_DEG": round(math.degrees(t.rotation), 3), "MIRRORED": bool(t.is_mirrored),
                     "CHILD_COUNT": n, "CHILD_ROLES": dict(kid_roles), "BBOX_MM": bbox, "ROLE": role, "ROLE_STATUS": st, "ROLE_EVIDENCE": ev,
                     "IS_BUILDING_FABRIC": role in ("COLUMN_SYMBOL",), "WALL_FACE_ELIGIBLE": False})
    return rows


def structural_objects(prims, roles, view_id):
    """STRUCTURAL_OBJECT_REGISTER: columns (closed loops), beams (hidden-layer parallel pairs), stair flights (tread families)."""
    out = []
    col_segs = [p for p in prims if roles.get(p.object_id, {}).get("ROLE") == "COLUMN_FACE"]
    # group column sides into loops by shared endpoints
    seen, groups = set(), []
    key = lambda x, y: (round(x / 5.0), round(y / 5.0))
    adj = defaultdict(list)
    for p in col_segs:
        adj[key(p.x1, p.y1)].append(p); adj[key(p.x2, p.y2)].append(p)
    for p in col_segs:
        if p.object_id in seen:
            continue
        stack, loop = [p], []
        while stack:
            q = stack.pop()
            if q.object_id in seen:
                continue
            seen.add(q.object_id); loop.append(q)
            for k in (key(q.x1, q.y1), key(q.x2, q.y2)):
                stack.extend(r for r in adj[k] if r.object_id not in seen)
        if len(loop) == 4:
            xs = [v for q in loop for v in (q.x1, q.x2)]; ys = [v for q in loop for v in (q.y1, q.y2)]
            cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            w, d = max(xs) - min(xs), max(ys) - min(ys)
            girth = sum(math.hypot(q.x2 - q.x1, q.y2 - q.y1) for q in loop)
            out.append({"OBJECT_ID": ids.column_id(view_id, (cx, cy), (w, d)), "TYPE": "COLUMN", "CENTRE_MM": [round(cx, 1), round(cy, 1)], "SIZE_MM": [round(w), round(d)],
                        "GIRTH_MM": round(girth, 1), "FACE_ENTITIES": [q.object_id for q in loop], "EXISTS_STATUS": "SOURCE_ESTABLISHED",
                        "EXPOSURE_STATUS": "NOT_ESTABLISHED", "NOTE": "existence from the plan loop; exposure per face is decided by the space boundary"})
    beams = [p for p in prims if roles.get(p.object_id, {}).get("ROLE") == "BEAM_EDGE" and p.kind == "SEGMENT"]
    for p in beams:
        out.append({"OBJECT_ID": ids.beam_id(view_id, "HIDDEN_EDGE", (p.x1, p.y1), (p.x2, p.y2)), "TYPE": "BEAM_EDGE_CANDIDATE", "LENGTH_MM": round(math.hypot(p.x2 - p.x1, p.y2 - p.y1), 1),
                    "ENTITY": p.object_id, "EXISTS_STATUS": "PROVISIONAL", "WALL_OWNERSHIP": "NONE", "NOTE": "hidden-line edge: overhead work; a beam schedule or section establishes it"})
    stairs = [p for p in prims if roles.get(p.object_id, {}).get("ROLE") == "STAIR_EDGE"]
    if stairs:
        xs = [v for q in stairs for v in (q.x1, q.x2)]; ys = [v for q in stairs for v in (q.y1, q.y2)]
        out.append({"OBJECT_ID": ids.make_id("SPACE_SEED", "STAIR", view_id, [min(xs), min(ys), max(xs), max(ys)], tol=100.0).replace("SS-", "ST-"), "TYPE": "STAIR_FLIGHT_CANDIDATE",
                    "TREAD_EDGES": len(stairs), "BBOX_MM": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))], "EXISTS_STATUS": "PROVISIONAL",
                    "NOTE": "tread geometry is separate from the stairwell walls; risers need a section"})
    return out
