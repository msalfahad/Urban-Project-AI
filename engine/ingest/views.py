"""Views inside one CAD model space and the layer profile (PA05 §1, §4).

A DWG model space often holds several drawings side by side (plan copies,
elevations).  Views are found by gap clustering of entity bounding boxes
(deterministic, parameterised), plan copies by the translation that maps
one cluster's long segments onto another's.  Layer roles come from
evidence statistics (engine.cad_profile) plus explicit overrides in the
project configuration; nothing is assumed from a layer's name.
"""

from __future__ import annotations

import math
from collections import Counter

from engine import cad_profile as CP
from engine.ingest import ids

GAP_MM = 3000.0          # a gap wider than this between entity clouds separates two drawings
LONG_MM = 2000.0
COPY_SEG_MM = 500.0      # segments at least this long vote for a copy translation
COPY_MATCH_MIN = 40      # endpoint votes needed to call two views copies of one plan family


def _bbox(p):
    if p.kind == "SEGMENT":
        return min(p.x1, p.x2), min(p.y1, p.y2), max(p.x1, p.x2), max(p.y1, p.y2)
    if p.kind in ("ARC", "CIRCLE"):
        return p.cx - p.radius, p.cy - p.radius, p.cx + p.radius, p.cy + p.radius
    return None


def _split(items, lo_key, hi_key, gap):
    """Interval merging along one axis: an entity joins the open group when its extent starts within `gap` of the
    group's running extent (extents, not centres, so a long wall stays with the plan it bounds)."""
    if not items:
        return []
    items = sorted(items, key=lo_key)
    groups, cur, cur_hi = [], [items[0]], hi_key(items[0])
    for it in items[1:]:
        if lo_key(it) - cur_hi > gap:
            groups.append(cur)
            cur, cur_hi = [it], hi_key(it)
        else:
            cur.append(it); cur_hi = max(cur_hi, hi_key(it))
    groups.append(cur)
    return groups


def find_views(primitives, sheet, gap_mm=GAP_MM, min_entities=50):
    """Cluster primitives into views by x then y gaps between entity extents."""
    boxed = [(p, _bbox(p)) for p in primitives if _bbox(p) is not None]
    boxed = [(p, b) for p, b in boxed if (b[2] - b[0]) < 200000 and (b[3] - b[1]) < 200000]     # drop sheet frames / giant lines
    views = []
    for gx in _split(boxed, lambda t: t[1][0], lambda t: t[1][2], gap_mm):
        for gy in _split(gx, lambda t: t[1][1], lambda t: t[1][3], gap_mm):
            if len(gy) < min_entities:
                continue
            x0 = min(b[0] for _, b in gy); y0 = min(b[1] for _, b in gy); x1 = max(b[2] for _, b in gy); y1 = max(b[3] for _, b in gy)
            views.append({"BBOX_MM": [round(x0), round(y0), round(x1), round(y1)], "ENTITY_COUNT": len(gy), "PRIMITIVES": [p for p, _ in gy]})
    views.sort(key=lambda v: (v["BBOX_MM"][0], v["BBOX_MM"][1]))
    for v in views:
        v["VIEW_ID"] = ids.view_id(sheet, "UNCLASSIFIED", v["BBOX_MM"])
    return views


def _long_segments(prims, layer_filter=None, min_len=COPY_SEG_MM):
    out = []
    for p in prims:
        if p.kind == "SEGMENT" and (layer_filter is None or p.provenance.layer in layer_filter):
            L = math.hypot(p.x2 - p.x1, p.y2 - p.y1)
            if L >= min_len:
                ang = round(math.degrees(math.atan2(p.y2 - p.y1, p.x2 - p.x1)) % 180.0)
                out.append((p.provenance.layer, ang, (p.x1, p.y1), (p.x2, p.y2)))
    return out


def copy_offsets(views, wall_layers=None, bucket_mm=100.0, min_matches=COPY_MATCH_MIN):
    """Translation vectors between views that repeat the same drawn pattern (plan copies of one building).
    Endpoints of segments with the same layer and orientation vote for a translation (all layers: two
    storeys of one building share the envelope, columns and grid even when the partitions differ); the
    winning bucket is refined to the median exact delta so the offset is a source fact, not a grid value."""
    sigs = {v["VIEW_ID"]: _long_segments(v["PRIMITIVES"], None) for v in views}
    out = []
    for i, a in enumerate(views):
        for b in views[i + 1:]:
            sa, sb = sigs[a["VIEW_ID"]], sigs[b["VIEW_ID"]]
            if len(sa) < min_matches // 2 or len(sb) < min_matches // 2:
                continue
            by = {}
            for l, ang, p1, p2 in sb:
                by.setdefault((l, ang), []).extend([p1, p2])
            votes, exact = Counter(), {}
            for l, ang, p1, p2 in sa:
                for (x, y) in (p1, p2):
                    for (bx, by_) in by.get((l, ang), []):
                        key = (round((bx - x) / bucket_mm), round((by_ - y) / bucket_mm))
                        votes[key] += 1
                        exact.setdefault(key, []).append((bx - x, by_ - y))
            if votes:
                key, n = votes.most_common(1)[0]
                if n >= min_matches:
                    dxs = sorted(d[0] for d in exact[key]); dys = sorted(d[1] for d in exact[key])
                    dx, dy = dxs[len(dxs) // 2], dys[len(dys) // 2]
                    out.append({"FROM_VIEW": a["VIEW_ID"], "TO_VIEW": b["VIEW_ID"], "DX_MM": round(dx, 2), "DY_MM": round(dy, 2), "MATCHES": n, "STATUS": "SOURCE_ESTABLISHED"})
    return out


NON_CONTINUOUS = ("HIDDEN", "DASHED", "DASH", "DOT", "CENTER", "PHANTOM", "DIVIDE", "BORDER")


def linetypes_from_decode(decoded):
    """Layer name -> linetype name from a DWG decode's LAYER / LTYPE tables (a document fact: a layer whose table
    linetype is HIDDEN / DASHED draws hidden work, not walls).  Returns {} when the tables are absent."""
    objs = decoded.get("OBJECTS") if isinstance(decoded, dict) else None
    if not objs:
        return {}
    def hnum(h):
        return h[-1] if isinstance(h, (list, tuple)) and h else h
    lt = {hnum(o.get("handle")): o.get("name") for o in objs if o.get("object") == "LTYPE"}
    return {o.get("name"): lt.get(hnum(o.get("ltype")), "UNKNOWN") for o in objs if o.get("object") == "LAYER" and o.get("name") is not None}


def layer_profile(normalized, overrides=None, linetypes=None):
    """Layer roles from evidence statistics plus the layer table's linetypes; explicit overrides win and are recorded as such."""
    prof = CP.build(normalized, source_file=normalized.source_file)
    walls = list(prof.wall_like_layers())
    linetypes = linetypes or {}
    hidden = sorted(l for l, lt in linetypes.items() if lt and any(t in str(lt).upper() for t in NON_CONTINUOUS))
    walls = [l for l in walls if l not in hidden]
    arcs = Counter(p.provenance.layer for p in normalized.primitives if p.kind == "ARC" and 600 <= p.radius <= 1300 and 1.2 <= ((p.end_angle - p.start_angle) % (2 * math.pi)) <= 1.9)
    door = arcs.most_common(1)[0][0] if arcs else None
    dims = Counter(d.provenance.layer for d in normalized.dimensions)
    texts = Counter(t.provenance.layer for t in normalized.texts)
    total_dims = sum(dims.values()) or 1
    roles = {"WALL_LAYERS": walls, "DOOR_LAYER": door, "DIMENSION_LAYERS": [l for l, c in dims.most_common(3) if c >= 0.2 * total_dims], "TEXT_LAYERS": [l for l, _ in texts.most_common(3)],
             "HIDDEN_LAYERS": hidden, "GLAZING_LAYERS": [], "LINETYPES": linetypes,
             "EVIDENCE": {"wall_like_from_profile": list(prof.wall_like_layers()), "hidden_by_layer_table_linetype": hidden, "door_arc_votes": dict(arcs), "profile_hash": prof.profile_hash()}, "OVERRIDES": {}}
    for k, v in (overrides or {}).items():
        roles["OVERRIDES"][k] = {"FROM": roles.get(k), "TO": v}
        roles[k] = v
    return roles
