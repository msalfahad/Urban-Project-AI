"""CAD LIMIT CENSUS (T-025a) - every layer that a frozen CAD search skips for size, as a LIMIT record (generic; read only).

    census(ents, unit_m=None, *, sheet=None) -> [LIMIT record]      one per (layer, cap) over the cap, sorted
    summary(records)                         -> counts by cap and reason

The frozen searches below skip a whole layer when it carries more entities than a fixed cap. The skip leaves no HELD
record, so whatever that layer draws (rectangles, rings, beam faces, strap faces, door / window rectangles) can vanish
silently (T-018 P-18; UP-QTY-STATUS-001: every drawn element is released, held or a named exclusion). This module does
not change any search: it re-applies each cap's own counting rule (same roles, same filters, same comparison) to the
same entity set the search receives (one sheet's `drawing_model.sheet_entities`, or an intake record) and lists every
layer over a cap. Wiring the records into a method version is a later task.

Each record: record "LIMIT", state "HELD", reason_code "CAD_LAYER_OVER_CAP", cap_id, layer, count (entities counted
the way the search counts them), cap, module, line (the frozen comparison), function, counted (what is counted),
effect (what the search does not do on that layer), condition (when the search runs at all, or None), sheet.
A count that cannot be made exactly (the drawing unit is unknown and the cap counts only lines longer than a length)
is given as count None with count_upper_bound and reason_code "CAD_LAYER_OVER_CAP_UNIT_UNKNOWN"; it is listed only
when the upper bound is over the cap (never assumed under it). An empty or missing entity set gives [].
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.source import member_detection as MD

POLICY_ID = "CAD_LIMIT_CENSUS_V1"

# cap_id -> the frozen comparison it mirrors. The line numbers point at the comparison in the frozen source
# (tests check that the cap literal is on that line).
CAPS = (
    {"cap_id": "MD_CANDIDATE_RECTS_SEGMENTS", "cap": 4000, "module": "engine/source/member_detection.py", "line": 152,
     "function": "candidate_rects", "counted": "segments on the layer (layer role not an annotation role)",
     "effect": "closed rectangles from drawn lines not searched on this layer", "condition": None},
    {"cap_id": "MD_LINE_RINGS_LINES", "cap": 20000, "module": "engine/source/member_detection.py", "line": 249,
     "function": "line_rings", "counted": "LINE segments longer than 1 mm on the layer (layer role not an annotation "
     "role)", "effect": "closed non-rectangular outlines drawn as separate lines not searched on this layer",
     "condition": "options.polygons_from_lines"},
    {"cap_id": "MD_EDGE_LAYER_FACES", "cap": 6000, "module": "engine/source/member_detection.py", "line": 649,
     "function": "score_edge_layers", "counted": "segments (faces) on the layer (role not annotation, COLUMN or "
     "FOOTING; outline share <= 0.5)", "effect": "beam edge faces not scored on this layer",
     "condition": "slab / ground beam plan with scheduled widths"},
    {"cap_id": "MD_STRAP_LAYER_FACES", "cap": 6000, "module": "engine/source/member_detection.py", "line": 952,
     "function": "strap_layers", "counted": "segments (faces) on the layer (role not annotation or COLUMN)",
     "effect": "strap faces not searched on this layer", "condition": "foundation plan with strap marks"},
    {"cap_id": "GR_UNMARKED_NETWORK_FACES", "cap": 6000, "module": "engine/source/generic_route.py", "line": 340,
     "function": "run (unmarked beam network)", "counted": "segments (faces) on the layer (role not annotation, "
     "COLUMN or FOOTING; outline share <= 0.5)", "effect": "unmarked beam network (densest pair layer) not "
     "searched on this layer", "condition": "slab / ground beam plan where no edge layer scored"},
    {"cap_id": "ARCH_V27_RECT_SEGMENTS", "cap": 20000, "module": "engine/source/arch_v27.py", "line": 231,
     "function": "layer_roles (MAX_RECT_SEGMENTS, arch_v27.py:49)", "counted": "segments on the layer (any role)",
     "effect": "column / door / window rectangles not searched on this layer (evidence says NOT_SEARCHED)",
     "condition": None},
)
LINE_RINGS_EPS_M = 0.5e-3             # member_detection.py:293 passes eps = 0.5e-3 / unit_m; line_rings keeps > 2 eps
EDGE_EXCLUDED = MD.ANNOTATION_ROLES + ("COLUMN", "FOOTING")
STRAP_EXCLUDED = MD.ANNOTATION_ROLES + ("COLUMN",)
OUTLINE_SHARE_MAX = 0.5               # member_detection.py:646 and generic_route.py:337 skip layers above this first


def _role(layer):
    return MD._layer_role(layer)


def _record(cap, layer, count, sheet, upper=None):
    rec = {"record": "LIMIT", "state": "HELD", "policy": POLICY_ID,
           "reason_code": "CAD_LAYER_OVER_CAP" if count is not None else "CAD_LAYER_OVER_CAP_UNIT_UNKNOWN",
           "cap_id": cap["cap_id"], "layer": layer, "count": count, "cap": cap["cap"], "module": cap["module"],
           "line": cap["line"], "function": cap["function"], "counted": cap["counted"], "effect": cap["effect"],
           "condition": cap["condition"], "sheet": sheet}
    if count is None:
        rec["count_upper_bound"] = upper
    return rec


def census(ents, unit_m=None, *, sheet=None):
    """LIMIT records for every layer over a frozen size cap in one entity set (see the module docstring)."""
    if not ents:
        return []
    segs = list(ents.get("segments") or [])
    if not segs:
        return []
    caps = {c["cap_id"]: c for c in CAPS}
    by_layer = defaultdict(list)
    for s in segs:
        by_layer[s["layer"]].append(s)
    share_ents = {"segments": segs, "rects": list(ents.get("rects") or [])}
    unit_ok = isinstance(unit_m, (int, float)) and not isinstance(unit_m, bool) and math.isfinite(unit_m) \
        and unit_m > 0
    out = []
    for lay in sorted(by_layer):
        ss = by_layer[lay]
        n = len(ss)
        role = _role(lay)
        annotation = role in MD.ANNOTATION_ROLES
        if not annotation and n > caps["MD_CANDIDATE_RECTS_SEGMENTS"]["cap"]:
            out.append(_record(caps["MD_CANDIDATE_RECTS_SEGMENTS"], lay, n, sheet))
        if not annotation:
            lines = [s for s in ss if s.get("kind", "LINE") == "LINE"]
            cap = caps["MD_LINE_RINGS_LINES"]
            if unit_ok:
                eps = LINE_RINGS_EPS_M / unit_m
                k = sum(1 for s in lines if math.dist(s["a"], s["b"]) > 2 * eps)
                if k > cap["cap"]:
                    out.append(_record(cap, lay, k, sheet))
            elif len(lines) > cap["cap"]:
                out.append(_record(cap, lay, None, sheet, upper=len(lines)))
        over_6000 = n > caps["MD_EDGE_LAYER_FACES"]["cap"]
        if over_6000 and role not in EDGE_EXCLUDED and MD.outline_share(share_ents, lay) <= OUTLINE_SHARE_MAX:
            out.append(_record(caps["MD_EDGE_LAYER_FACES"], lay, n, sheet))
            out.append(_record(caps["GR_UNMARKED_NETWORK_FACES"], lay, n, sheet))
        if n > caps["MD_STRAP_LAYER_FACES"]["cap"] and role not in STRAP_EXCLUDED:
            out.append(_record(caps["MD_STRAP_LAYER_FACES"], lay, n, sheet))
        if n > caps["ARCH_V27_RECT_SEGMENTS"]["cap"]:
            out.append(_record(caps["ARCH_V27_RECT_SEGMENTS"], lay, n, sheet))
    order = {c["cap_id"]: i for i, c in enumerate(CAPS)}
    return sorted(out, key=lambda r: (str(r["sheet"]), r["layer"], order[r["cap_id"]]))


def summary(records):
    """Counts of LIMIT records by cap and by reason, and the layers they hold."""
    recs = list(records or [])
    return {"policy": POLICY_ID, "limit_records": len(recs),
            "by_cap": dict(sorted(Counter(r["cap_id"] for r in recs).items())),
            "by_reason": dict(sorted(Counter(r["reason_code"] for r in recs).items())),
            "layers": sorted({r["layer"] for r in recs})}
