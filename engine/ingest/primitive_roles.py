"""Geometry role classifier (PA06 WS2).

A layer name alone never decides a role.  Roles come from combinations of
layer evidence (statistics + layer-table linetype), entity kind, block
membership, repetition families (hatch, stairs), paired-face geometry,
arc radius and hinge topology, dimension origins and closed loops.
Every row carries ROLE_STATUS, ROLE_EVIDENCE and a ROLE_CONFIDENCE_CLASS
(HIGH / MEDIUM / LOW); there is no numeric confidence.
"""

from __future__ import annotations

import math
from collections import defaultdict

ROLES = ("MATERIAL_WALL_FACE", "MATERIAL_WALL_CENTERLINE", "COLUMN_FACE", "BEAM_EDGE", "DOOR_LEAF", "DOOR_SWING", "WINDOW_FRAME", "GLAZING", "HATCH_STROKE",
         "DIMENSION_LINE", "DIMENSION_EXTENSION", "DIMENSION_TEXT", "TEXT_OR_LABEL", "GRID_OR_LEVEL", "STAIR_EDGE", "RAILING", "CASEWORK_OR_FITTING",
         "SITE_BOUNDARY", "DECORATIVE_GEOMETRY", "UNKNOWN_GEOMETRY")
MATERIAL_ROLES = ("MATERIAL_WALL_FACE", "MATERIAL_WALL_CENTERLINE", "COLUMN_FACE")
STATUSES = ("ESTABLISHED", "PROVISIONAL", "UNRESOLVED")
# parameters (millimetres; the source is scaled to mm before classification)
PAIR_OFFSET = (50.0, 600.0)
PAIR_OVERLAP_MIN = 0.3
HATCH_MAX_LEN = 3000.0
HATCH_FAMILY_MIN = 8
HATCH_SPACING_MAX = 200.0
STAIR_FAMILY_MIN = 5
STAIR_LEN = (700.0, 3500.0)
STAIR_SPACING = (220.0, 400.0)
DOOR_RADIUS = (500.0, 1400.0)
HINGE_TOL = 450.0
COLUMN_SIDE = (150.0, 1200.0)
MIN_WALL_LEN = 30.0          # below this a wall-layer piece is a CAD artefact, not material
SINGLE_LINE_MIN = 500.0      # an unpaired wall-layer line this long is a single-line wall; shorter unpaired pieces are face fragments / returns
SITE_BOUNDARY_MIN = 3.0e4
ANGLE_TOL = math.radians(1.0)


def _len(p):
    if p.kind == "SEGMENT":
        return math.hypot(p.x2 - p.x1, p.y2 - p.y1)
    if p.kind == "ARC":
        return p.radius * (((p.end_angle - p.start_angle) % (2 * math.pi)) or 2 * math.pi)
    if p.kind == "CIRCLE":
        return 2 * math.pi * p.radius
    return 0.0


def _angle(p):
    return math.atan2(p.y2 - p.y1, p.x2 - p.x1) % math.pi


def _line_key(p):
    """(direction bucket, offset bucket) so collinear / parallel segments group together."""
    ang = _angle(p)
    ux, uy = math.cos(ang), math.sin(ang)
    off = -uy * p.x1 + ux * p.y1
    return int(round(ang / ANGLE_TOL)), off, ux, uy


def _paired(segments):
    """Segments that have a parallel partner at a wall-thickness offset with real overlap -> {object_id: (partner_id, offset)}."""
    by_dir = defaultdict(list)
    for p in segments:
        k, off, ux, uy = _line_key(p)
        lo, hi = sorted((p.x1 * ux + p.y1 * uy, p.x2 * ux + p.y2 * uy))
        by_dir[k].append((off, lo, hi, p))
    out = {}
    for k, members in by_dir.items():
        members.sort(key=lambda m: m[0])
        for i, (off, lo, hi, p) in enumerate(members):
            best = None
            for j in range(i + 1, len(members)):
                off2, lo2, hi2, q = members[j]
                d = off2 - off
                if d > PAIR_OFFSET[1]:
                    break
                if d < PAIR_OFFSET[0]:
                    continue
                overlap = min(hi, hi2) - max(lo, lo2)
                if overlap > PAIR_OVERLAP_MIN * min(hi - lo, hi2 - lo2) and overlap > 0:
                    if best is None or d < best[1]:
                        best = (q.object_id, d)
            if best:
                out[p.object_id] = best
                out.setdefault(best[0], (p.object_id, best[1]))
    return out


def _families(segments, max_len, min_members, spacing_max, len_band=None):
    """Repetition families: parallel segments with regular perpendicular spacing inside a local window."""
    by_dir = defaultdict(list)
    for p in segments:
        L = _len(p)
        if L > max_len or (len_band and not (len_band[0] <= L <= len_band[1])):
            continue
        k, off, ux, uy = _line_key(p)
        mid = ((p.x1 + p.x2) / 2 * ux + (p.y1 + p.y2) / 2 * uy)
        by_dir[k].append((off, mid, p))
    members = set()
    for k, items in by_dir.items():
        items.sort(key=lambda t: t[0])
        # sliding window on offsets: a run of >= min_members with consecutive spacing <= spacing_max and mids within 4 m
        run = []
        for off, mid, p in items:
            if run and (off - run[-1][0] > spacing_max or abs(mid - run[-1][1]) > 4000):
                if len(run) >= min_members:
                    members.update(x[2].object_id for x in run)
                run = []
            run.append((off, mid, p))
        if len(run) >= min_members:
            members.update(x[2].object_id for x in run)
    return members


def _rectangles(segments):
    """Closed 4-segment loops with both sides inside the column band -> set of object ids."""
    pts = defaultdict(list)
    def key(x, y):
        return (round(x / 5.0), round(y / 5.0))
    segs = [p for p in segments if COLUMN_SIDE[0] <= _len(p) <= COLUMN_SIDE[1]]
    for p in segs:
        pts[key(p.x1, p.y1)].append(p); pts[key(p.x2, p.y2)].append(p)
    out = set()
    for p in segs:
        # walk: p -> q (sharing endpoint, perpendicular) -> r (parallel to p) -> s (back to start)
        a, b = key(p.x1, p.y1), key(p.x2, p.y2)
        ang = _angle(p)
        for q in pts[b]:
            if q is p or abs(((_angle(q) - ang) % math.pi) - math.pi / 2) > ANGLE_TOL * 5:
                continue
            c = key(q.x2, q.y2) if key(q.x1, q.y1) == b else key(q.x1, q.y1)
            for r in pts[c]:
                if r in (p, q) or abs((_angle(r) - ang) % math.pi) > ANGLE_TOL * 5:
                    continue
                d = key(r.x2, r.y2) if key(r.x1, r.y1) == c else key(r.x1, r.y1)
                for s in pts[d]:
                    if s in (p, q, r):
                        continue
                    e = key(s.x2, s.y2) if key(s.x1, s.y1) == d else key(s.x1, s.y1)
                    if e == a:
                        out.update(x.object_id for x in (p, q, r, s))
    return out


def classify(prims, layers, dims=(), texts=(), level_layers=()):
    """prims: primitives of one view (millimetres); layers: the layer profile; dims: DimensionObservation list of the view.
    Returns PRIMITIVE_ROLE_REGISTER rows keyed by object id."""
    wall_layers = set(layers.get("WALL_LAYERS") or [])
    hidden = set(layers.get("HIDDEN_LAYERS") or [])
    dim_layers = set(layers.get("DIMENSION_LAYERS") or [])
    door_layer = layers.get("DOOR_LAYER")
    glazing_layers = set(layers.get("GLAZING_LAYERS") or [])
    segs = [p for p in prims if p.kind == "SEGMENT"]
    dim_origins = set()
    for d in dims:
        dim_origins.add((round(d.x1 / 10), round(d.y1 / 10))); dim_origins.add((round(d.x2 / 10), round(d.y2 / 10)))
    # families and structures (computed over all segments, not only wall layers: a hatch is a hatch on any layer)
    hatch_members = _families(segs, HATCH_MAX_LEN, HATCH_FAMILY_MIN, HATCH_SPACING_MAX)
    stair_members = _families([p for p in segs if p.provenance.layer not in wall_layers], STAIR_LEN[1], STAIR_FAMILY_MIN, STAIR_SPACING[1], len_band=STAIR_LEN) - hatch_members
    wall_segs = [p for p in segs if p.provenance.layer in wall_layers and p.object_id not in hatch_members and _len(p) >= MIN_WALL_LEN]
    pairs = _paired(wall_segs)
    rect_members = _rectangles([p for p in segs if p.object_id not in hatch_members])
    # door swings: arcs of door radius with a hinge at a wall segment endpoint; leaves: segments from the hinge of leaf length
    wall_ends = [(p.x1, p.y1) for p in wall_segs] + [(p.x2, p.y2) for p in wall_segs]
    def near_wall_end(x, y):
        return any(math.hypot(x - ex, y - ey) <= HINGE_TOL for ex, ey in wall_ends)
    swings = {}
    for p in prims:
        if p.kind == "ARC" and DOOR_RADIUS[0] <= p.radius <= DOOR_RADIUS[1]:
            sweep = (p.end_angle - p.start_angle) % (2 * math.pi)
            quarter = abs(sweep - math.pi / 2) < 0.35 or abs(sweep - math.pi) < 0.35
            on_door_layer = door_layer is not None and p.provenance.layer == door_layer
            hinge = near_wall_end(p.cx, p.cy)
            concentric = any(q is not p and q.kind == "ARC" and math.hypot(q.cx - p.cx, q.cy - p.cy) <= 30 and 50 <= abs(q.radius - p.radius) <= 600 for q in prims)
            if quarter and not concentric:
                swings[p.object_id] = {"HINGE_AT_WALL_END": hinge, "ON_DOOR_LAYER": on_door_layer, "RADIUS_MM": round(p.radius, 1)}
    leaf_ids = {}
    centres = [(p.cx, p.cy, p.radius, p.object_id) for p in prims if p.object_id in swings]
    for p in segs:
        L = _len(p)
        for cx, cy, r, sid in centres:
            if abs(L - r) <= 0.15 * r and (math.hypot(p.x1 - cx, p.y1 - cy) <= 60 or math.hypot(p.x2 - cx, p.y2 - cy) <= 60):
                leaf_ids[p.object_id] = sid
    rows = {}
    for p in prims:
        oid, layer, kind, L = p.object_id, p.provenance.layer, p.kind, _len(p)
        blk = list(p.provenance.block_path)
        ev, role, st, conf = [], None, "ESTABLISHED", "HIGH"
        in_dim_block = any(str(b).startswith("*D") for b in blk)
        if kind == "HATCH":
            role, ev = "HATCH_STROKE", ["HATCH entity"]
        elif oid in swings:
            role, ev = "DOOR_SWING", [f"arc radius {swings[oid]['RADIUS_MM']} in the door band, quarter / half sweep", "hinge at a wall end" if swings[oid]["HINGE_AT_WALL_END"] else "on the door layer"]
            conf = "HIGH" if swings[oid]["HINGE_AT_WALL_END"] else ("MEDIUM" if swings[oid]["ON_DOOR_LAYER"] else "LOW")
            st = "ESTABLISHED" if (swings[oid]["HINGE_AT_WALL_END"] or swings[oid]["ON_DOOR_LAYER"]) else "PROVISIONAL"
        elif oid in leaf_ids:
            role, ev = "DOOR_LEAF", [f"segment from the hinge of swing {leaf_ids[oid]} with leaf length"]
        elif layer in dim_layers or in_dim_block:
            near = kind == "SEGMENT" and ((round(p.x1 / 10), round(p.y1 / 10)) in dim_origins or (round(p.x2 / 10), round(p.y2 / 10)) in dim_origins)
            role, ev = ("DIMENSION_EXTENSION" if near else "DIMENSION_LINE"), ["dimension layer / dimension block" + (" and ends at a dimension origin" if near else "")]
        elif oid in hatch_members:
            role, ev = "HATCH_STROKE", [f"member of a family of >= {HATCH_FAMILY_MIN} short parallel strokes at regular spacing"]
        elif layer in hidden:
            role, ev, st, conf = "BEAM_EDGE", ["hidden / dashed layer by the layer table: overhead work, not a wall"], "PROVISIONAL", "LOW"
        elif oid in rect_members:
            role, ev = "COLUMN_FACE", ["side of a closed 4-segment loop with both sides in the column band"]
        elif oid in stair_members:
            role, ev, conf = "STAIR_EDGE", [f"member of a family of >= {STAIR_FAMILY_MIN} parallel edges at tread spacing"], "MEDIUM"
        elif layer in glazing_layers:
            role, ev = "GLAZING", ["glazing layer (project configuration)"]
        elif layer in level_layers:
            role, ev, conf = "GRID_OR_LEVEL", ["layer carrying level / grid text"], "MEDIUM"
        elif layer in wall_layers and kind == "SEGMENT":
            if L < MIN_WALL_LEN:
                role, ev, st, conf = "UNKNOWN_GEOMETRY", [f"wall-layer stub shorter than {MIN_WALL_LEN} mm"], "UNRESOLVED", "LOW"
            elif oid in pairs:
                role, ev = "MATERIAL_WALL_FACE", [f"paired with parallel face {pairs[oid][0]} at {round(pairs[oid][1])} mm (wall thickness band)"]
            elif L >= SINGLE_LINE_MIN:
                role, ev, st, conf = "MATERIAL_WALL_FACE", ["wall-like layer, no paired face: single-line wall"], "PROVISIONAL", "MEDIUM"
            else:
                role, ev, st, conf = "MATERIAL_WALL_FACE", ["short unpaired wall-layer piece: face fragment or jamb return (material by layer evidence, geometry unpaired)"], "PROVISIONAL", "LOW"
        elif layer in wall_layers and kind in ("ARC", "CIRCLE"):
            partner = [q for q in prims if q is not p and q.kind == p.kind and q.provenance.layer in wall_layers and math.hypot(q.cx - p.cx, q.cy - p.cy) <= 30
                       and PAIR_OFFSET[0] <= abs(q.radius - p.radius) <= PAIR_OFFSET[1]]
            if partner:
                role, ev = "MATERIAL_WALL_FACE", [f"curved face with a concentric partner at {round(abs(partner[0].radius - p.radius))} mm"]
            elif L >= SINGLE_LINE_MIN:
                role, ev, st, conf = "MATERIAL_WALL_FACE", ["curved wall-layer entity without a concentric partner"], "PROVISIONAL", "MEDIUM"
            else:
                role, ev, st, conf = "DECORATIVE_GEOMETRY", ["short curve on a wall layer"], "UNRESOLVED", "LOW"
        elif kind == "SEGMENT" and L >= SITE_BOUNDARY_MIN:
            role, ev, st, conf = "SITE_BOUNDARY", ["very long line outside the wall layers"], "PROVISIONAL", "LOW"
        else:
            role, ev, st, conf = "UNKNOWN_GEOMETRY", ["no rule applies"], "UNRESOLVED", "LOW"
        rows[oid] = {"OBJECT_ID": oid, "KIND": kind, "LAYER": layer, "BLOCK_PATH": blk, "LENGTH_MM": round(L, 1), "ROLE": role, "ROLE_STATUS": st,
                     "ROLE_CONFIDENCE_CLASS": conf, "ROLE_EVIDENCE": ev, "MATERIAL": role in MATERIAL_ROLES}
    return rows


def summarise(rows):
    by = defaultdict(lambda: {"COUNT": 0, "LENGTH_M": 0.0})
    for r in rows.values():
        by[r["ROLE"]]["COUNT"] += 1
        by[r["ROLE"]]["LENGTH_M"] = round(by[r["ROLE"]]["LENGTH_M"] + r["LENGTH_MM"] / 1000, 3)
    return dict(by)
