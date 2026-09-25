"""Assembling rooms out of the fragments a drawing yields.

A drawing does not hand over rooms.  It hands over connected pieces of floor, and a room is often several of
them: a wardrobe recess that the flood fill cut off at a grid line, a lobby that continues past a column, a
pantry that a virtual closure sliced in two because the engine drew a door where the drawing only drew a gap.
The label sits in exactly one of those pieces, which is how a room label ends up describing a fragment.

So membership is decided at the SEAM between two pieces of floor.  For each seam the engine asks what is
physically there: wall material, an opening, or nothing at all.  Nothing at all means one room continues into the
next piece.  Wall material means two rooms.  An opening means two rooms with a door between them.  A seam that is
none of these clearly enough is REVIEW_REQUIRED - the engine does not pick.
"""

from __future__ import annotations

from engine.qs_core import geom
from engine.qs_core.entities import (ASSIGNED_TO_SPACE, CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG,
                                     CONFIDENCE_WEAK, EXTERNAL_OPEN_AREA, Evidence, KIND_COLUMN, KIND_EXTERNAL,
                                     KIND_FLOOR_REGION, KIND_SLIVER, KIND_WALL_BAND, NON_ROOM_GEOMETRY,
                                     NON_ROOM_KINDS, SPACE_LABEL_CONFLICT, SPACE_NAMED, SPACE_UNNAMED,
                                     SemanticSpace, UNRESOLVED)

# A seam is settled when one reading covers more than half of it; below that the evidence is mixed and the engine
# says so.  This is a property of the question, not of a project: half is the point at which "mostly" stops
# meaning anything.
MAJORITY = 0.5

SEAM_WALL = "SEPARATED_BY_WALL_MATERIAL"
SEAM_OPENING = "CONNECTED_BY_AN_OPENING"
SEAM_CONTINUOUS = "CONTINUOUS_FLOOR"
SEAM_CANDIDATE_OPENING = "CANDIDATE_OPENING_REVIEW_REQUIRED"
SEAM_MIXED = "REVIEW_REQUIRED"


class Barrier:
    """Something drawn between two pieces of floor, and what backs it.

    A wall band backs a barrier with material.  A virtual closure - the span an engine draws across a gap so a
    room stops at its doorway - backs nothing at all unless an opening sits in it.
    """

    def __init__(self, axis, position, lo, hi, kind, floor, component_ref=None, opening_ref=None):
        self.axis, self.position, self.lo, self.hi = axis, position, lo, hi
        self.kind, self.floor = kind, floor
        self.component_ref, self.opening_ref = component_ref, opening_ref

    BACKED_BY_MATERIAL = "WALL_MATERIAL"
    VIRTUAL_CLOSURE = "VIRTUAL_CLOSURE"

    def as_dict(self):
        return {"AXIS": self.axis, "POSITION": round(self.position, 6), "FROM": round(self.lo, 6),
                "TO": round(self.hi, 6), "KIND": self.kind, "FLOOR": self.floor,
                "COMPONENT_REF": self.component_ref, "OPENING_REF": self.opening_ref}


def _overlap(a_lo, a_hi, b_lo, b_hi):
    return max(0.0, min(a_hi, b_hi) - max(a_lo, b_lo))


def _covers_seam(seam, axis, position, lo, hi, tol):
    s_axis, s_pos, s_lo, s_hi = seam
    if axis != s_axis or abs(position - s_pos) > tol:
        return 0.0
    return _overlap(s_lo, s_hi, lo, hi)


def classify_seam(seam, barriers, openings, tol):
    """What is physically present along this seam, and therefore what the seam means."""
    _axis, _pos, lo, hi = seam
    length = hi - lo
    if length <= 0:
        return {"RELATION": SEAM_MIXED, "LENGTH_M": 0.0}
    material = opening = closure = 0.0
    refs = {"MATERIAL": [], "OPENINGS": [], "CLOSURES": []}
    for b in barriers:
        cov = _covers_seam(seam, b.axis, b.position, b.lo, b.hi, tol)
        if cov <= 0:
            continue
        if b.kind == Barrier.BACKED_BY_MATERIAL:
            material += cov
            refs["MATERIAL"].append(b.component_ref)
        else:
            # a break drawn in a wall line: the source says something is here, and does not say what
            closure += cov
            refs["CLOSURES"].append(b.opening_ref or b.component_ref)
    for o in openings:
        ob = o.rect
        if seam[0] == geom.AXIS_X:
            if abs(ob.centroid[1] - seam[1]) > max(tol, ob.height / 2 + tol):
                continue
            cov = _overlap(lo, hi, ob.x0, ob.x1)
        else:
            if abs(ob.centroid[0] - seam[1]) > max(tol, ob.width / 2 + tol):
                continue
            cov = _overlap(lo, hi, ob.y0, ob.y1)
        if cov > 0:
            opening += cov
            refs["OPENINGS"].append(o.opening_ref)
    material = min(material, length)
    opening = min(opening, max(0.0, length - material))
    closure = min(closure, max(0.0, length - material - opening))
    free = max(0.0, length - material - opening - closure)
    shares = {"MATERIAL": material / length, "OPENING": opening / length,
              "CANDIDATE_OPENING": closure / length, "FREE": free / length}
    if shares["MATERIAL"] > MAJORITY:
        rel = SEAM_WALL
    elif shares["OPENING"] > MAJORITY:
        rel = SEAM_OPENING
    elif shares["CANDIDATE_OPENING"] > MAJORITY:
        # the wall stops here and the source does not say whether anything fills the gap.  Two rooms with a
        # doorway and one room with an archway look identical at this point, so the engine asks.
        rel = SEAM_CANDIDATE_OPENING
    elif shares["FREE"] > MAJORITY:
        rel = SEAM_CONTINUOUS
    else:
        rel = SEAM_MIXED
    return {"RELATION": rel, "LENGTH_M": round(length, 6),
            "SHARES": {k: round(v, 6) for k, v in shares.items()}, "REFS": refs}


def _classify_kinds(components, sliver_min_dimension):
    """A floor region too thin to stand in is drafting residue, not a space.  The threshold is the caller's."""
    for c in components:
        if c.kind != KIND_FLOOR_REGION:
            continue
        b = c.bbox
        if min(b.width, b.height) < sliver_min_dimension:
            c.kind = KIND_SLIVER
            c.evidence.append(Evidence("RECLASSIFIED_AS_SLIVER",
                                       {"MIN_DIMENSION_M": round(min(b.width, b.height), 6),
                                        "THRESHOLD_M": sliver_min_dimension,
                                        "WHY": "no usable space is narrower than the threshold the source "
                                               "declares; this is wall residue or a drafting artefact"}))


class _Union:
    def __init__(self, keys):
        self.parent = {k: k for k in keys}

    def find(self, k):
        while self.parent[k] != k:
            self.parent[k] = self.parent[self.parent[k]]
            k = self.parent[k]
        return k

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def assemble_semantic_spaces(components, barriers, openings, labels, tolerance, sliver_min_dimension,
                             source_revision=None):
    """Turn geometry components into semantic spaces, leaving every component in exactly one state."""
    _classify_kinds(components, sliver_min_dimension)
    floors = [c for c in components if c.kind == KIND_FLOOR_REGION]
    others = [c for c in components if c.kind != KIND_FLOOR_REGION]

    seams, review_pairs = [], set()
    union = _Union(sorted(c.component_ref for c in floors))
    by_ref = {c.component_ref: c for c in components}

    ordered = sorted(floors, key=lambda c: c.component_ref)
    for i, a in enumerate(ordered):
        for b in ordered[i + 1:]:
            if a.floor != b.floor or not a.bbox.expanded(tolerance).overlaps(b.bbox):
                continue          # components whose bounding boxes do not meet cannot share a seam
            for seam in geom.shared_edge(a.rects, b.rects, tolerance):
                cls = classify_seam(seam, [x for x in barriers if x.floor == a.floor],
                                    [o for o in openings if o.floor == a.floor], tolerance)
                rec = {"A": a.component_ref, "B": b.component_ref, "FLOOR": a.floor,
                       "AXIS": seam[0], "POSITION": round(seam[1], 6),
                       "FROM": round(seam[2], 6), "TO": round(seam[3], 6), **cls}
                seams.append(rec)
                if cls["RELATION"] == SEAM_CONTINUOUS:
                    union.union(a.component_ref, b.component_ref)
                elif cls["RELATION"] in (SEAM_MIXED, SEAM_CANDIDATE_OPENING):
                    review_pairs.add((a.component_ref, b.component_ref))

    # an internal space that continues into an external area with nothing between them is not something the
    # engine may settle: either the enclosure is missing from the source or the area is not external at all
    external_review = set()
    for a in ordered:
        for e in sorted([c for c in components if c.kind == KIND_EXTERNAL], key=lambda c: c.component_ref):
            if a.floor != e.floor or not a.bbox.expanded(tolerance).overlaps(e.bbox):
                continue
            for seam in geom.shared_edge(a.rects, e.rects, tolerance):
                cls = classify_seam(seam, [x for x in barriers if x.floor == a.floor],
                                    [o for o in openings if o.floor == a.floor], tolerance)
                seams.append({"A": a.component_ref, "B": e.component_ref, "FLOOR": a.floor,
                              "AXIS": seam[0], "POSITION": round(seam[1], 6),
                              "FROM": round(seam[2], 6), "TO": round(seam[3], 6), **cls})
                if cls["RELATION"] in (SEAM_CONTINUOUS, SEAM_MIXED):
                    external_review.add(a.component_ref)
                    external_review.add(e.component_ref)
                    review_pairs.add((a.component_ref, e.component_ref))

    groups = {}
    for c in ordered:
        groups.setdefault(union.find(c.component_ref), []).append(c)

    spaces, membership = [], []
    for root, members in sorted(groups.items()):
        refs = sorted(m.component_ref for m in members)
        room_id = f"ROOM::{members[0].floor}::{root}"
        seen = []
        for lb in labels:
            for m in members:
                if any(r.contains_point(lb.x, lb.y, tolerance) for r in m.rects):
                    seen.append(lb.text)
                    break
        distinct = sorted(set(seen))
        if len(distinct) == 1:
            label, lstat, conf = distinct[0], SPACE_NAMED, CONFIDENCE_PROVEN
            ev = [Evidence("LABEL_APPLIES_TO_THE_WHOLE_SPACE",
                           {"LABEL": distinct[0], "COMPONENTS": refs,
                            "WHY": "the label sits in one component, and the other components of this space "
                                   "continue into it with no physical boundary between them"})]
        elif not distinct:
            label, lstat, conf = None, SPACE_UNNAMED, CONFIDENCE_STRONG
            ev = [Evidence("NO_LABEL_IN_THIS_SPACE",
                           {"COMPONENTS": refs, "WHY": "the drawing names no space here; the area is measured "
                                                       "and the identity is left unresolved"})]
        else:
            label, lstat, conf = None, SPACE_LABEL_CONFLICT, CONFIDENCE_NONE
            ev = [Evidence("CONFLICTING_LABELS_IN_ONE_CONTINUOUS_SPACE",
                           {"LABELS": distinct, "COMPONENTS": refs,
                            "WHY": "two different names fall inside floor that continues without a boundary; "
                                   "either a boundary is missing from the source or one label is misplaced"})]
        in_review = any((a, b) in review_pairs or (b, a) in review_pairs
                        for a in refs for b in refs if a != b) or any(r in external_review for r in refs)
        status = UNRESOLVED if (lstat == SPACE_LABEL_CONFLICT or in_review) else ASSIGNED_TO_SPACE
        if in_review:
            ev.append(Evidence("SEAM_EVIDENCE_MIXED",
                               {"WHY": "a seam inside this space is part material and part open; the engine "
                                       "does not decide whether it is one space or two"}))
            conf = CONFIDENCE_WEAK
        sp = SemanticSpace(room_id=room_id, floor=members[0].floor, source_revision=source_revision,
                           component_refs=refs,
                           rects=[r for m in members for r in m.rects], label=label, label_status=lstat, labels_seen=distinct,
                           area=sum(m.area for m in members), status=status, confidence=conf, evidence=ev)
        spaces.append(sp)
        for m in members:
            m.room_id = room_id
            m.status = ASSIGNED_TO_SPACE if status == ASSIGNED_TO_SPACE else UNRESOLVED
            m.confidence = conf
            membership.append({"COMPONENT_REF": m.component_ref, "ROOM_ID": room_id, "FLOOR": m.floor,
                               "KIND": m.kind, "AREA_M2": round(m.area, 6), "STATUS": m.status,
                               "LABEL": label, "LABEL_STATUS": lstat,
                               "EVIDENCE": [e.as_dict() for e in ev]})

    for c in others:
        if c.kind in NON_ROOM_KINDS:
            c.status = NON_ROOM_GEOMETRY
            c.confidence = CONFIDENCE_PROVEN
            c.room_id = None
            why = {KIND_WALL_BAND: "wall material is never floor finish, however much floor it touches",
                   KIND_COLUMN: "a column stands inside or beside a space; it is not part of its floor",
                   KIND_SLIVER: "too thin to be a space"}[c.kind]
            c.evidence.append(Evidence("NON_ROOM_GEOMETRY", {"KIND": c.kind, "WHY": why}))
        elif c.kind == KIND_EXTERNAL:
            if c.component_ref in external_review:
                c.status = UNRESOLVED
                c.confidence = CONFIDENCE_WEAK
                c.evidence.append(Evidence("EXTERNAL_AREA_CONTINUES_INTO_A_SPACE",
                                           {"WHY": "this external area meets internal floor with no boundary "
                                                   "between them; the engine does not decide which it is"}))
            else:
                c.status = EXTERNAL_OPEN_AREA
                c.confidence = CONFIDENCE_PROVEN
            c.room_id = None
        else:
            c.status = UNRESOLVED
            c.confidence = CONFIDENCE_NONE
        membership.append({"COMPONENT_REF": c.component_ref, "ROOM_ID": None, "FLOOR": c.floor,
                           "KIND": c.kind, "AREA_M2": round(c.area, 6), "STATUS": c.status,
                           "LABEL": None, "LABEL_STATUS": None,
                           "EVIDENCE": [e.as_dict() for e in c.evidence]})

    return {"SPACES": spaces, "MEMBERSHIP": sorted(membership, key=lambda r: r["COMPONENT_REF"]),
            "SEAMS": sorted(seams, key=lambda r: (r["A"], r["B"], r["POSITION"])),
            "REVIEW_PAIRS": sorted(review_pairs),
            "RULE": "a component belongs to one space, or is non-room geometry, or is external, or is "
                    "unresolved; there is no fifth outcome and no component may hold two"}
