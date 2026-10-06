"""CAD / SOURCE GUARDS learnt from blind donor runs (generic).

    segment_intersects_region   a member crossing into a region counts even when its start point is outside
    closed_polygon_area         no area from an open polyline without closure proof
    text_readability            unreadable note -> TEXT_UNREADABLE, routed to SOURCE_REVIEW (never "no rule")
    evidence_state              release state from STRUCTURED evidence authority, never from free-text notes
    physical_occurrence_geometry one geometry authority per occurrence; every span (clear, centreline,
                                support-to-support, rebar design) derived from it with an explicit transformation
    join_occurrences            plan occurrence -> schedule definition; a schedule row never creates an occurrence;
                                the same mark may have different occurrences per floor
    classify_drawn_object       real plan occurrence vs schedule graphic / typical detail / legend / copied detail /
                                paper-space annotation - only the first is physical work
Stdlib only.
"""

from __future__ import annotations

import math

TEXT_UNREADABLE = "TEXT_UNREADABLE"
SOURCE_REVIEW = "SOURCE_REVIEW"


# ------------------------------------------------------------------------------------------------ region crossing
def _point_in_polygon(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def _orient(a, b, c):
    v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)


def _on_segment(a, b, p):
    return min(a[0], b[0]) - 1e-12 <= p[0] <= max(a[0], b[0]) + 1e-12 and \
        min(a[1], b[1]) - 1e-12 <= p[1] <= max(a[1], b[1]) + 1e-12


def segments_intersect(a, b, c, d):
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return (o1 == 0 and _on_segment(a, b, c)) or (o2 == 0 and _on_segment(a, b, d)) or \
        (o3 == 0 and _on_segment(c, d, a)) or (o4 == 0 and _on_segment(c, d, b))


def segment_intersects_region(seg, region):
    """True if the segment has ANY part inside / on the region polygon - not just its start point."""
    a, b = seg
    if _point_in_polygon(a, region) or _point_in_polygon(b, region):
        return True
    n = len(region)
    return any(segments_intersect(a, b, region[i], region[(i + 1) % n]) for i in range(n))


def start_point_inside_region(seg, region):
    """The defective donor test, kept only so a regression test can show it misses crossing members."""
    return _point_in_polygon(seg[0], region)


# ------------------------------------------------------------------------------------------------ polyline area
def closed_polygon_area(pts, *, closed_flag=False, tol=1e-6):
    """Shoelace area only with closure proof: the entity's closed flag, or first == last vertex within tol.
    Returns {area, state}: CLOSED -> area; OPEN -> area None (never trusted)."""
    if len(pts) < 3:
        return {"area": None, "state": "DEGENERATE"}
    closed = closed_flag or math.dist(pts[0], pts[-1]) <= tol
    if not closed:
        return {"area": None, "state": "OPEN_POLYLINE_NO_CLOSURE_PROOF"}
    ring = pts[:-1] if math.dist(pts[0], pts[-1]) <= tol else pts
    a = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        a += x1 * y2 - x2 * y1
    return {"area": abs(a) / 2.0, "state": "CLOSED"}


# ------------------------------------------------------------------------------------------------ text
def text_readability(raw, *, decoded=None):
    """A note the native extractor cannot read is TEXT_UNREADABLE and goes to SOURCE_REVIEW (PDF vector / raster /
    OCR / human) - it is never read as 'no rule exists'."""
    txt = decoded if decoded is not None else raw
    if txt is None or not str(txt).strip():
        return {"state": TEXT_UNREADABLE, "route": SOURCE_REVIEW, "rule_absent": None}
    s = str(txt)
    bad = sum(1 for ch in s if ch == "�" or (ord(ch) < 32 and ch not in "\t\n\r"))
    if bad / max(1, len(s)) > 0.2 or s.strip("?") == "":
        return {"state": TEXT_UNREADABLE, "route": SOURCE_REVIEW, "rule_absent": None}
    return {"state": "READABLE", "route": None, "text": s}


# ------------------------------------------------------------------------------------------------ evidence
EVIDENCE_TO_STATE = {"SOURCE_FACT": "VERIFIED", "DERIVED_GEOMETRY": "VERIFIED", "PROJECT_RULE": "VERIFIED",
                     "PROJECT_HUMAN_CLAIM": "VERIFIED", "ENGINEERING_METHOD": "PROVISIONAL",
                     "URBAN_OWNER_RULE": "PROVISIONAL", "URBAN_STANDARD_CANDIDATE": "PROVISIONAL",
                     "BOUND_ONLY": "LOWER_BOUND", "BLOCKED": "BLOCKED"}


def evidence_state(evidence):
    """State from structured evidence: {authority_class, ...}. Free text (`note`) is ignored on purpose - a note
    saying 'verified' or 'assumed' changes nothing. Missing authority -> BLOCKED."""
    cls = (evidence or {}).get("authority_class")
    return EVIDENCE_TO_STATE.get(cls, "BLOCKED")


# ------------------------------------------------------------------------------------------------ geometry authority
def physical_occurrence_geometry(occurrence_id, *, axis_start, axis_end, support_widths=(0.0, 0.0), source_ref=None):
    """ONE geometry authority per member occurrence. Every span is derived from it:
        centreline span      = |axis_end - axis_start|          (support centre to support centre)
        clear span           = centreline - (w_start + w_end) / 2
        support-to-support   = centreline
        rebar design span    = clear span (the transformation is named, so concrete and rebar cannot drift)."""
    cl = math.dist(axis_start, axis_end)
    clear = cl - (support_widths[0] + support_widths[1]) / 2.0
    return {"occurrence_id": occurrence_id, "axis": [list(axis_start), list(axis_end)], "source_ref": source_ref,
            "centreline_span": cl, "clear_span": clear, "support_to_support": cl,
            "rebar_design_span": clear,
            "transformations": {"clear_span": "centreline - (w_start + w_end)/2",
                                "rebar_design_span": "= clear_span"}}


def check_geometry_consistency(geometry, *, concrete_span, rebar_span, concrete_basis, rebar_basis, tol=1e-6):
    """A member's concrete and rebar spans must come from the same occurrence geometry through named bases."""
    problems = []
    for name, val, basis in (("concrete", concrete_span, concrete_basis), ("rebar", rebar_span, rebar_basis)):
        if basis not in geometry:
            problems.append(f"{name} span basis {basis} is not derived from the occurrence geometry")
        elif abs(geometry[basis] - val) > tol:
            problems.append(f"{name} span {val} differs from occurrence {basis} {geometry[basis]}")
    return problems


# ------------------------------------------------------------------------------------------------ occurrences
def join_occurrences(plan_occurrences, schedule_rows):
    """Plan decides occurrence; schedule only defines. Returns (joined, unbound_occurrences, rows_without_occurrence).
    A schedule row with no plan occurrence creates NOTHING. The same mark may occur on several floors, each a separate
    occurrence, and is joined per (mark, storey band) when the schedule is banded."""
    by_key = {}
    for r in schedule_rows:
        by_key.setdefault((r["mark"], r.get("storey_band")), []).append(r)
    joined, unbound, used = [], [], set()
    for o in plan_occurrences:
        rows = by_key.get((o["mark"], o.get("storey_band"))) or by_key.get((o["mark"], None))
        if not rows or len(rows) != 1:
            unbound.append(dict(o, join_state="NO_ROW" if not rows else "DUPLICATE_ROW"))
            continue
        used.add(id(rows[0]))
        joined.append(dict(o, definition=rows[0], join_state="DEFINED"))
    orphans = [r for r in schedule_rows if id(r) not in used]
    return joined, unbound, [dict(r, occurrences_created=0) for r in orphans]


DRAWN_ROLES = ("PLAN_OCCURRENCE", "SCHEDULE_GRAPHIC", "TYPICAL_DETAIL", "LEGEND", "DUPLICATE_COPIED_DETAIL",
               "PAPER_SPACE_ANNOTATION")


def classify_drawn_object(obj):
    """Only PLAN_OCCURRENCE is physical work. Role from structured context (space, region role, copy family)."""
    if obj.get("space") == "PAPER":
        return "PAPER_SPACE_ANNOTATION"
    role = obj.get("region_role")
    if role in ("SCHEDULE", "SCHEDULE_TABLE"):
        return "SCHEDULE_GRAPHIC"
    if role in ("TYPICAL_DETAIL", "DETAIL"):
        return "TYPICAL_DETAIL"
    if role == "LEGEND":
        return "LEGEND"
    if obj.get("copy_of"):
        return "DUPLICATE_COPIED_DETAIL"
    if role == "PLAN":
        return "PLAN_OCCURRENCE"
    return "UNCLASSIFIED"


def counts_as_physical(obj):
    return classify_drawn_object(obj) == "PLAN_OCCURRENCE"
