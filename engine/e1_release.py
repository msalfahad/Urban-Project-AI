"""E1.1 §F §G §J §K — what has to be true before a region is released.

E1 v1 validated each candidate on its own. The pool showed why that is not
enough: six wedges, each individually closed, each individually plausible,
all of them inside one circle. Nothing in a local check can see that.

This module holds the four gates that are NOT local:

    §F  every released region is compared with every other one
    §G  agreement with A18 must name WHAT agrees, not just the label
    §J  ten conditions, all of which must hold, or the region is WITHHELD
    §K  a picture of the candidate on the ORIGINAL SHEET is looked at
        before release, and only VISUALLY_CONSISTENT releases automatically

None of these can be satisfied by repairing geometry. They are reasons to
withhold, and withholding is the correct outcome when they are not met.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field

from engine import cad_entity_role as cer
from engine import cad_geometry as cg
from engine import raster_qa as rq

MODEL = "A_REGION_IS_RELEASED_ONLY_WHEN_NOTHING_CONTRADICTS_IT_V1"

# =======================================================================
# §F  global released-region overlap
# =======================================================================
DUPLICATE_REGION = "DUPLICATE_REGION"
NESTED_REGION = "NESTED_REGION"
OVERLAPPING_REGION = "OVERLAPPING_REGION"
SHARED_BOUNDARY_ONLY = "SHARED_BOUNDARY_ONLY"
SAME_PHYSICAL_REGION_DIFFERENT_LABEL = "SAME_PHYSICAL_REGION_DIFFERENT_LABEL"
BILINGUAL_DUPLICATE = "BILINGUAL_DUPLICATE"
LEGITIMATE_NESTED_ARCHITECTURAL_OBJECT = (
    "LEGITIMATE_NESTED_ARCHITECTURAL_OBJECT")
UNRESOLVED_OVERLAP = "UNRESOLVED_OVERLAP"
OVERLAP_RELATIONS = (DUPLICATE_REGION, NESTED_REGION, OVERLAPPING_REGION,
                     SHARED_BOUNDARY_ONLY,
                     SAME_PHYSICAL_REGION_DIFFERENT_LABEL,
                     BILINGUAL_DUPLICATE,
                     LEGITIMATE_NESTED_ARCHITECTURAL_OBJECT,
                     UNRESOLVED_OVERLAP)

# Which relations are compatible with BOTH regions being released.
OVERLAP_PERMITS_RELEASE = (SHARED_BOUNDARY_ONLY,
                           LEGITIMATE_NESTED_ARCHITECTURAL_OBJECT)

TWO_ROOMS_MAY_NOT_OCCUPY_ONE_PLACE = (
    "two independently released physical regions must not substantially "
    "overlap. Where one architectural object legitimately sits inside "
    "another - a column, a stair well, a pool in a terrace - the nesting "
    "is named as such and both may stand. Anything else is withheld")

DUPLICATE_IOU = 0.97
NESTED_SHARE = 0.90
OVERLAP_SHARE = 0.02
# Two rooms either side of one wall touch along it. The densified ring is
# a chord approximation, so "touching" comes back as a sliver of area
# rather than exactly zero, and a sliver is a shared boundary, not an
# overlap.
SLIVER_SHARE = 0.001

# Architectural objects that may legitimately sit inside another region.
NESTABLE_OBJECT_KINDS = ("ROUND_OBJECT", "STAIR_ASSEMBLY", "COLUMN",
                         "SHAFT", "LIFT")


# =======================================================================
# §G  alignment must name what it confirms
# =======================================================================
IDENTITY_CONFIRMED_GEOMETRY_UNRESOLVED = (
    "IDENTITY_CONFIRMED_GEOMETRY_UNRESOLVED")
IDENTITY_CONFIRMED_GEOMETRY_CONFLICT = "IDENTITY_CONFIRMED_GEOMETRY_CONFLICT"
TOPOLOGY_CONFIRMED = "TOPOLOGY_CONFIRMED"
TOPOLOGY_CHALLENGED = "TOPOLOGY_CHALLENGED"
BOUNDARY_CONFIRMED = "BOUNDARY_CONFIRMED"
BOUNDARY_RESHAPED = "BOUNDARY_RESHAPED"
BOUNDARY_CONFLICT = "BOUNDARY_CONFLICT"
NO_LIKE_FOR_LIKE_GEOMETRY = "NO_LIKE_FOR_LIKE_GEOMETRY"
ALIGNMENT_STATUSES = (IDENTITY_CONFIRMED_GEOMETRY_UNRESOLVED,
                      IDENTITY_CONFIRMED_GEOMETRY_CONFLICT,
                      TOPOLOGY_CONFIRMED, TOPOLOGY_CHALLENGED,
                      BOUNDARY_CONFIRMED, BOUNDARY_RESHAPED,
                      BOUNDARY_CONFLICT, NO_LIKE_FOR_LIKE_GEOMETRY)

CONFIRMED_MUST_NAME_ITS_SUBJECT = (
    "'CONFIRMED_BY_CAD' is not a status here. Every agreement names WHAT "
    "agrees - the identity, the topology, or the boundary - because a "
    "closed ring containing the same text stamp confirms none of the "
    "other two")

# General topology words, read from A18's own frozen prose. These are
# ordinary English about buildings, not a token map for this project.
_OPEN_WORDS = re.compile(
    r"\b(open[- ]sided|open[- ]plan|partly open|partially open|openly|"
    r"open on (the|its)|open edge|open boundary|open side|no wall|"
    r"without a wall|no second face|no partition|continuous with|"
    r"flows? into|wide opening|unbounded|not enclosed|open to)\b", re.I)
_CLOSED_WORDS = re.compile(
    r"\b(enclosed|fully bounded|closed room|four walls|sealed)\b", re.I)
_CURVE_WORDS = re.compile(r"\b(curv\w+|arc|radius|circular|round)\b", re.I)
_STEP_WORDS = re.compile(r"\b(step\w*|recess\w*|niche|jog|nib)\b", re.I)

OPEN = "A18_SAYS_OPEN"
CLOSED = "A18_SAYS_ENCLOSED"
NOT_STATED = "A18_STATES_NO_TOPOLOGY"


def a18_topology_claim(*statements) -> str:
    text = " ".join(s for s in statements if s)
    if _OPEN_WORDS.search(text):
        return OPEN
    if _CLOSED_WORDS.search(text):
        return CLOSED
    return NOT_STATED


def a18_shape_observations(*statements) -> tuple:
    text = " ".join(s for s in statements if s)
    out = []
    if _CURVE_WORDS.search(text):
        out.append("A18_OBSERVED_A_CURVE")
    if _STEP_WORDS.search(text):
        out.append("A18_OBSERVED_A_STEP_OR_RECESS")
    return tuple(out)


def alignment_status(*, has_a18_identity, a18_topology, a18_shape,
                     a18_geometry_source, released, outcome, boundary,
                     label_point_inside, a18_label_point_inside) -> dict:
    """Name every dimension of agreement separately, and never merge them."""
    statuses, notes = [], []
    if not has_a18_identity:
        statuses.append(NO_LIKE_FOR_LIKE_GEOMETRY)
        notes.append("no frozen A18 hypothesis carries this identity")
        return {"A18_ALIGNMENT_STATUS": statuses,
                "confirmed_what": [],
                "notes": notes,
                "confirmed_must_name_its_subject":
                    CONFIRMED_MUST_NAME_ITS_SUBJECT}

    confirmed = ["IDENTITY"]
    # --- topology ----------------------------------------------------
    # A DOORWAY IS NOT AN OPEN SIDE. An enclosed room has doors in it, so
    # a portal across a door confirms nothing either way; what contradicts
    # "enclosed" is a stretch of ring lying on NO drawn entity, and what
    # contradicts "open" is a ring of unbroken material.
    has_portal = bool(boundary is not None
                      and boundary.contains_artificial_topology)
    open_mm = 0.0 if boundary is None else sum(
        s.length_mm for s in boundary.segments if s.role == cg.OPEN_EDGE)
    has_open_edge = open_mm > cg.SNAP_MM
    # AND A DOOR IS NOT AN OPEN SIDE EITHER. When A18 reports a side with
    # no wall on it, a door-width portal does not confirm that reading -
    # it contradicts it, because a doorway is a hole in a wall and the
    # reading was that there is no wall.
    widest_portal = 0.0 if boundary is None else max(
        [s.length_mm for s in boundary.segments
         if s.role == cg.VIRTUAL_PORTAL_BOUNDARY] or [0.0])
    wide_opening = widest_portal > cg.MAX_DOUBLE_LEAF_MM
    if boundary is None:
        notes.append("no ring to compare A18's topology with")
    elif a18_topology == OPEN and (has_open_edge or wide_opening):
        statuses.append(TOPOLOGY_CONFIRMED)
        confirmed.append("TOPOLOGY_OPEN" if has_open_edge
                         else "TOPOLOGY_OPEN_ACROSS_A_WIDE_GAP")
    elif a18_topology == OPEN:
        statuses.append(TOPOLOGY_CHALLENGED)
        notes.append(
            "A18 read this space as open. The CAD ring that holds its "
            "stamp is drawn material"
            + (f", broken only by a {widest_portal:.0f} mm opening, which "
               "is a doorway rather than an open side" if has_portal
               else " with no portal and no open edge in it")
            + ". One of the two readings is wrong, and a closed ring "
              "containing the stamp does not settle which")
    elif a18_topology == CLOSED and has_open_edge:
        statuses.append(TOPOLOGY_CHALLENGED)
        notes.append("A18 read this space as enclosed, and part of the CAD "
                     "ring lies on no drawn entity at all")
    elif a18_topology == CLOSED:
        statuses.append(TOPOLOGY_CONFIRMED)
        confirmed.append("TOPOLOGY_ENCLOSED")
    else:
        notes.append("A18 states no topology for this space")

    # --- boundary -----------------------------------------------------
    if boundary is None or not released:
        statuses.append(IDENTITY_CONFIRMED_GEOMETRY_UNRESOLVED)
        notes.append(f"CAD outcome is {outcome} and no boundary is released")
    else:
        if a18_geometry_source in ("LABEL_POINT", "", None):
            statuses.append(NO_LIKE_FOR_LIKE_GEOMETRY)
            notes.append(
                "the A18 hypothesis carries a label point, not an extent, "
                "so there is nothing to compare this boundary with "
                "shape-for-shape")
        if a18_label_point_inside is False:
            statuses.append(BOUNDARY_CONFLICT)
            notes.append(
                "the place A18 read the label is outside the CAD region "
                "that claims it")
        elif label_point_inside:
            statuses.append(BOUNDARY_CONFIRMED)
            confirmed.append("BOUNDARY_HOLDS_THE_LABEL_A18_READ")
    if TOPOLOGY_CHALLENGED in statuses and released:
        statuses.append(IDENTITY_CONFIRMED_GEOMETRY_CONFLICT)
    if "A18_OBSERVED_A_CURVE" in a18_shape and boundary is not None \
            and not boundary.has_curves:
        statuses.append(BOUNDARY_RESHAPED)
        notes.append("A18 observed a curve here; the CAD ring has none")
    return {"A18_ALIGNMENT_STATUS": sorted(set(statuses)),
            "confirmed_what": confirmed,
            "a18_topology_claim": a18_topology,
            "a18_shape_observations": list(a18_shape),
            "notes": notes,
            "confirmed_must_name_its_subject": CONFIRMED_MUST_NAME_ITS_SUBJECT}


# =======================================================================
# §K  visual back-check on the ORIGINAL sheet
# =======================================================================
VISUALLY_CONSISTENT = "VISUALLY_CONSISTENT"
POSSIBLE_UNDER_CAPTURE = "POSSIBLE_UNDER_CAPTURE"
POSSIBLE_OVER_CAPTURE = "POSSIBLE_OVER_CAPTURE"
INTERNAL_FEATURE_USED_AS_BOUNDARY = "INTERNAL_FEATURE_USED_AS_BOUNDARY"
LABEL_OWNERSHIP_CONFLICT = "LABEL_OWNERSHIP_CONFLICT"
BOUNDARY_ROLE_CONFLICT = "BOUNDARY_ROLE_CONFLICT"
HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
VISUAL_QA_STATES = (VISUALLY_CONSISTENT, POSSIBLE_UNDER_CAPTURE,
                    POSSIBLE_OVER_CAPTURE, INTERNAL_FEATURE_USED_AS_BOUNDARY,
                    LABEL_OWNERSHIP_CONFLICT, BOUNDARY_ROLE_CONFLICT,
                    HUMAN_REVIEW_REQUIRED)

ONLY_VISUALLY_CONSISTENT_RELEASES = (
    "only VISUALLY_CONSISTENT releases automatically. Every other state "
    "is a reason to withhold and to put the overlay in front of a person")

# A dimension states the clear distance between two faces. Where the
# candidate's span across that same line is shorter by more than this, the
# boundary has stopped somewhere the drawing did not.
DIMENSION_DISAGREEMENT_MM = 100.0


def dimension_cross_check(boundary, dimensions, *,
                          wall_face_tol_mm=60.0) -> list:
    """What the sheet's own dimensions say about this candidate's span.

    Only dimensions whose BOTH extension-line origins land on established
    MATERIAL WALL FACES are used, and only where no other established wall
    face crosses the span - so the dimension is measuring a clear
    wall-to-wall distance. Then the candidate's span along that same line
    is measured and compared. A cabinet front 500 mm inside the room shows
    up here as a boundary 500 mm short of a dimension the architect drew.
    """
    from shapely.geometry import LineString, Point, Polygon
    out = []
    if boundary is None:
        return out
    try:
        poly = Polygon(boundary.points())
        if not poly.is_valid:
            poly = poly.buffer(0)
    except Exception:
        return out
    walls = [s for s in boundary.segments if s.role in cg.MATERIAL_ROLES]
    for d in dimensions:
        span = math.hypot(d.x2 - d.x1, d.y2 - d.y1)
        if span <= 0:
            continue
        mid = Point((d.x1 + d.x2) / 2.0, (d.y1 + d.y2) / 2.0)
        if not poly.contains(mid):
            continue
        # both origins must sit on an established wall face
        origins_on_wall = sum(
            1 for pt in ((d.x1, d.y1), (d.x2, d.y2))
            if _near_any_wall(pt, walls, wall_face_tol_mm))
        line = LineString([(d.x1, d.y1), (d.x2, d.y2)])
        crossed = sum(1 for s in walls
                      if _segment_crosses(s, line, wall_face_tol_mm))
        inter = poly.intersection(line)
        got = inter.length if not inter.is_empty else 0.0
        if got <= 0:
            continue
        short = span - got
        out.append({
            "dimension_mm": round(span, 2),
            "printed_value": d.display_value,
            "candidate_span_along_it_mm": round(got, 2),
            "difference_mm": round(short, 2),
            "origins_on_established_wall_faces": origins_on_wall,
            "established_wall_faces_crossing_it": crossed,
            "usable": bool(origins_on_wall == 2 and crossed <= 2),
            "verdict": (POSSIBLE_UNDER_CAPTURE
                        if short > DIMENSION_DISAGREEMENT_MM
                        else POSSIBLE_OVER_CAPTURE
                        if short < -DIMENSION_DISAGREEMENT_MM
                        else VISUALLY_CONSISTENT),
        })
    return out


def _near_any_wall(pt, walls, tol) -> bool:
    for s in walls:
        if s.kind == cg.LINE:
            if _dist_point_seg(pt, (s.x1, s.y1), (s.x2, s.y2)) <= tol:
                return True
        else:
            d = abs(math.hypot(pt[0] - s.cx, pt[1] - s.cy) - s.radius)
            if d <= tol:
                return True
    return False


def _dist_point_seg(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n2 = dx * dx + dy * dy
    if n2 <= 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n2))
    return math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1])


def _segment_crosses(seg, line, tol) -> bool:
    from shapely.geometry import LineString
    try:
        pts = seg.points(tol_mm=cg.DENSIFY_TOL_MM)
        if len(pts) < 2:
            return False
        return LineString(pts).distance(line) <= tol
    except Exception:
        return False


def visual_gate(*, boundary, entity_roles, distinct_label_groups,
                dimension_rows, sheet=None, registration=None) -> dict:
    """The §K states, from the candidate and the registered sheet."""
    states, notes = [], []
    if boundary is None:
        return {"VISUAL_QA_STATE": [HUMAN_REVIEW_REQUIRED],
                "notes": ["no boundary to look at"],
                "dimension_cross_check": list(dimension_rows or ()),
                "only_visually_consistent_releases":
                    ONLY_VISUALLY_CONSISTENT_RELEASES}

    bad = []
    for s in boundary.segments:
        if s.role not in cg.MATERIAL_ROLES:
            continue
        role = entity_roles.get(s.object_id)
        if role is None or not role.may_bound_material:
            bad.append((s.object_id,
                        role.established_role if role else "NOT_IN_REGISTER"))
    if bad:
        states.append(INTERNAL_FEATURE_USED_AS_BOUNDARY)
        notes.append(f"{len(bad)} ring segments come from entities whose "
                     f"established role may not bound material: "
                     f"{sorted({r for _o, r in bad})}")

    roles_on_ring = {s.role for s in boundary.segments}
    if cg.ROLE_UNRESOLVED in roles_on_ring or cg.DIMENSION_WITNESS in \
            roles_on_ring or cg.ANNOTATION_ONLY in roles_on_ring:
        states.append(BOUNDARY_ROLE_CONFLICT)
        notes.append(f"the ring carries {sorted(roles_on_ring)}")

    if len(distinct_label_groups) > 1:
        states.append(LABEL_OWNERSHIP_CONFLICT)
        notes.append("more than one functional label group is seen inside: "
                     f"{sorted(distinct_label_groups)}")

    usable = [r for r in dimension_rows if r["usable"]]
    under = [r for r in usable if r["verdict"] == POSSIBLE_UNDER_CAPTURE]
    over = [r for r in usable if r["verdict"] == POSSIBLE_OVER_CAPTURE]
    if under:
        states.append(POSSIBLE_UNDER_CAPTURE)
        worst = max(under, key=lambda r: r["difference_mm"])
        notes.append(
            f"a dimension between two established wall faces states "
            f"{worst['dimension_mm']:.0f} mm across this space and the "
            f"candidate spans {worst['candidate_span_along_it_mm']:.0f} mm "
            "along the same line")
    if over:
        states.append(POSSIBLE_OVER_CAPTURE)

    if registration is not None and not registration.established:
        states.append(HUMAN_REVIEW_REQUIRED)
        notes.append("the sheet could not be registered against the CAD, so "
                     "no visual back-check was possible")

    if not states:
        states.append(VISUALLY_CONSISTENT)
        notes.append("nothing on the sheet or in the drawing's own "
                     "dimensions contradicts this candidate")
    return {"VISUAL_QA_STATE": sorted(set(states)),
            "notes": notes,
            "dimension_cross_check": dimension_rows,
            "only_visually_consistent_releases":
                ONLY_VISUALLY_CONSISTENT_RELEASES}


# =======================================================================
# §J  the release invariant
# =======================================================================
C1 = "BOUNDARY_GEOMETRY_IS_COHERENT"
C2 = "EVERY_MATERIAL_SEGMENT_HAS_AN_ESTABLISHED_ENTITY_ROLE"
C3 = "NO_CASEWORK_FIXTURE_OR_ANNOTATION_IS_ACTING_AS_ROOM_WALL"
C4 = "PORTALS_ARE_TOPOLOGY_ONLY"
C5 = "CURVES_REMAIN_ANALYTICAL"
C6 = "LABEL_OWNERSHIP_IS_PLAUSIBLE"
C7 = "BILINGUAL_ALIASES_ARE_NOT_TREATED_AS_SEPARATE_FUNCTIONS"
C8 = "GLOBAL_OVERLAP_CHECK_PASSES"
C9 = "A18_CAD_TOPOLOGY_CONFLICT_RESOLVED_OR_ACCEPTED_ON_EVIDENCE"
C10 = "VISUAL_BACK_CHECK_SHOWS_NO_UNDER_OR_OVER_CAPTURE"
RELEASE_CONDITIONS = (C1, C2, C3, C4, C5, C6, C7, C8, C9, C10)

PASS = "PASS"
FAIL = "FAIL"
WITHHELD = "WITHHELD"
RELEASED = "RELEASED"

OTHERWISE_WITHHOLD = (
    "a region is RELEASED only when all ten conditions hold. Any one of "
    "them failing means WITHHOLD - never repair the geometry until it "
    "passes, because a boundary obtained that way is a quantity nobody "
    "drew")


def release_decision(*, boundary, outcome, closed_outcome, entity_roles,
                     label_groups_inside, alias_conflict, overlap_relations,
                     alignment, visual, curve_check_ok=True) -> dict:
    """Ten conditions. All of them, or WITHHOLD."""
    checks = {}

    def put(name, ok, note):
        checks[name] = {"result": PASS if ok else FAIL, "note": note}

    put(C1, bool(boundary is not None and boundary.closed
                 and boundary.segments and outcome == closed_outcome),
        f"outcome is {outcome}")
    if boundary is None:
        for name in RELEASE_CONDITIONS[1:]:
            checks.setdefault(name, {"result": FAIL,
                                     "note": "no boundary was built"})
        failed = [k for k, v in checks.items() if v["result"] == FAIL]
        return {"RELEASE_CONDITIONS": checks, "failed": failed,
                "decision": WITHHELD, "released": False,
                "otherwise_withhold": OTHERWISE_WITHHOLD}

    material = [s for s in boundary.segments if s.role in cg.MATERIAL_ROLES]
    unestablished = [s.object_id for s in material
                     if s.object_id not in entity_roles
                     or entity_roles[s.object_id].established_role
                     == cer.UNKNOWN]
    put(C2, not unestablished,
        f"{len(unestablished)} material segments have no established entity "
        "role" if unestablished else
        f"all {len(material)} material segments name an established role")
    wrong = sorted({entity_roles[s.object_id].established_role
                    for s in material
                    if s.object_id in entity_roles
                    and not entity_roles[s.object_id].may_bound_material})
    put(C3, not wrong,
        f"roles acting as room wall that may not: {wrong}" if wrong
        else "no casework, fixture, dimension or annotation is on this ring")
    put(C4, all(s.wall_length_contribution_mm == 0.0
                for s in boundary.segments
                if s.role in cg.TOPOLOGY_ONLY_ROLES),
        "every inserted segment contributes zero wall material")
    curved = [s for s in boundary.segments if s.kind in (cg.ARC, cg.CIRCLE)]
    put(C5, curve_check_ok and all(s.radius > 0 for s in curved),
        f"{len(curved)} curved segments keep centre, radius and angles")
    put(C6, len(label_groups_inside) <= 1,
        f"label groups inside: {sorted(label_groups_inside)}")
    put(C7, not alias_conflict,
        "an alternate-language stamp was counted as a second function"
        if alias_conflict else
        "bilingual stamps of one room are one functional identity")
    blocking = [r for r in overlap_relations
                if r["relation"] not in OVERLAP_PERMITS_RELEASE]
    put(C8, not blocking,
        f"{len(blocking)} overlap relations block release: "
        f"{sorted({r['relation'] for r in blocking})}" if blocking
        else "no released region overlaps this one impermissibly")
    st = set(alignment.get("A18_ALIGNMENT_STATUS", ()))
    put(C9, not (st & {TOPOLOGY_CHALLENGED,
                       IDENTITY_CONFIRMED_GEOMETRY_CONFLICT,
                       BOUNDARY_CONFLICT}),
        "; ".join(alignment.get("notes", ())) or "no A18 conflict")
    vs = set(visual.get("VISUAL_QA_STATE", ()))
    put(C10, vs == {VISUALLY_CONSISTENT},
        "; ".join(visual.get("notes", ())))

    failed = [k for k, v in checks.items() if v["result"] == FAIL]
    return {"RELEASE_CONDITIONS": checks, "failed": failed,
            "decision": RELEASED if not failed else WITHHELD,
            "released": not failed,
            "otherwise_withhold": OTHERWISE_WITHHOLD}


# ---------------------------------------------------------------- §F body

def overlap_relations(candidates) -> list:
    """Compare EVERY candidate with every other, before any release.

    `candidates` are dicts with keys: id, points, label_group, object_kind.
    """
    from shapely.geometry import Polygon
    polys = {}
    for c in candidates:
        try:
            p = Polygon(c["points"])
            if not p.is_valid:
                p = p.buffer(0)
            if p.area > 0:
                polys[c["id"]] = p
        except Exception:
            continue
    rows = []
    ids = [c["id"] for c in candidates if c["id"] in polys]
    by_id = {c["id"]: c for c in candidates}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            pa, pb = polys[a], polys[b]
            if not pa.intersects(pb):
                continue
            inter = pa.intersection(pb).area
            small = min(pa.area, pb.area)
            union = pa.union(pb).area or 1.0
            iou = inter / union
            share = inter / small if small else 0.0
            same_group = (by_id[a].get("label_group")
                          and by_id[a].get("label_group")
                          == by_id[b].get("label_group"))
            inner = a if pa.area <= pb.area else b
            kind = by_id[inner].get("object_kind")
            if iou >= DUPLICATE_IOU:
                rel = (BILINGUAL_DUPLICATE if same_group
                       else SAME_PHYSICAL_REGION_DIFFERENT_LABEL
                       if by_id[a].get("label_group")
                       != by_id[b].get("label_group")
                       else DUPLICATE_REGION)
            elif share >= NESTED_SHARE:
                rel = (LEGITIMATE_NESTED_ARCHITECTURAL_OBJECT
                       if kind in NESTABLE_OBJECT_KINDS else NESTED_REGION)
            elif share >= OVERLAP_SHARE:
                rel = OVERLAPPING_REGION
            elif share <= SLIVER_SHARE:
                rel = SHARED_BOUNDARY_ONLY
            else:
                rel = UNRESOLVED_OVERLAP
            rows.append({
                "a": a, "b": b, "relation": rel,
                "intersection_m2_rendering_only": round(inter / 1e6, 6),
                "share_of_smaller": round(share, 4),
                "iou": round(iou, 4),
                "inner_object_kind": kind,
                "same_label_group": bool(same_group),
                "two_rooms_may_not_occupy_one_place":
                    TWO_ROOMS_MAY_NOT_OCCUPY_ONE_PLACE,
            })
    return rows


def model_hash() -> str:
    parts = ([MODEL] + list(OVERLAP_RELATIONS) + list(ALIGNMENT_STATUSES)
             + list(VISUAL_QA_STATES) + list(RELEASE_CONDITIONS)
             + [f"{DUPLICATE_IOU}", f"{NESTED_SHARE}", f"{OVERLAP_SHARE}",
                f"{DIMENSION_DISAGREEMENT_MM}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "OVERLAP_RELATIONS": list(OVERLAP_RELATIONS),
        "OVERLAP_PERMITS_RELEASE": list(OVERLAP_PERMITS_RELEASE),
        "NESTABLE_OBJECT_KINDS": list(NESTABLE_OBJECT_KINDS),
        "ALIGNMENT_STATUSES": list(ALIGNMENT_STATUSES),
        "VISUAL_QA_STATES": list(VISUAL_QA_STATES),
        "RELEASE_CONDITIONS": list(RELEASE_CONDITIONS),
        "DUPLICATE_IOU": DUPLICATE_IOU,
        "NESTED_SHARE": NESTED_SHARE,
        "OVERLAP_SHARE": OVERLAP_SHARE,
        "SLIVER_SHARE": SLIVER_SHARE,
        "DIMENSION_DISAGREEMENT_MM": DIMENSION_DISAGREEMENT_MM,
        "why": {
            "two_rooms_may_not_occupy_one_place":
                TWO_ROOMS_MAY_NOT_OCCUPY_ONE_PLACE,
            "confirmed_must_name_its_subject":
                CONFIRMED_MUST_NAME_ITS_SUBJECT,
            "only_visually_consistent_releases":
                ONLY_VISUALLY_CONSISTENT_RELEASES,
            "otherwise_withhold": OTHERWISE_WITHHOLD,
        },
    }
