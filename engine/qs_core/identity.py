"""Identity that survives a redrawn drawing.

Scan-order identity is the defect this replaces: number the components in the order a grid happens to be walked
and a five-millimetre wall move renumbers everything after it, so an owner's decision about a room lands on a
different room in the next revision.

Three separate ideas do the work here.  A FINGERPRINT is a hash of the geometry itself, so an identical rerun
produces identical identity.  A UID is the immutable handle a store keeps.  A PERSISTENT ID is what an owner
decision attaches to, and it is carried forward across revisions by matching geometry rather than by position in
a list.  Where a match is not clear, the engine says so instead of guessing, because a wrongly carried decision
is worse than a decision that has to be made again.
"""

from __future__ import annotations

import hashlib
import math
import uuid

from engine.qs_core import geom
from engine.qs_core.entities import (LINEAGE_MERGED, LINEAGE_MODIFIED, LINEAGE_NEW, LINEAGE_REMOVED,
                                     LINEAGE_REVIEW, LINEAGE_SPLIT, LINEAGE_UNCHANGED, NAMESPACE)

# Why these values: a match needs more than half the area in common, because two rooms that share less than half
# their area are not the same room moved - they are two rooms.  The ambiguity band is the margin within which two
# rivals are indistinguishable, and a split share is the smallest piece worth calling a child rather than noise.
MIN_IOU_MATCH = 0.50
AMBIGUITY_BAND = 0.05
SPLIT_SHARE = 0.20


def fingerprint(entity, places=4):
    """A hash of the geometry and its kind.  Identical input, identical fingerprint, on any machine."""
    rects = getattr(entity, "rects", None)
    if rects is None:
        rects = [entity.rect] if getattr(entity, "rect", None) is not None else []
    parts = [str(getattr(entity, "kind", getattr(entity, "opening_type", ""))),
             str(entity.floor),
             str(round(entity.thickness, places)) if getattr(entity, "thickness", None) is not None else "-",
             str(getattr(entity, "axis", "-") or "-")]
    parts += [",".join(str(v) for v in t) for t in sorted(r.as_tuple(places) for r in rects)]
    if not rects:
        # an opening whose host is unresolved has no footprint yet.  Its identity is the source features it
        # was admitted from, so it can still be matched across revisions - an object with no geometry is not
        # an object with no identity.
        c = getattr(entity, "candidate", None)
        if c is not None:
            parts += ["FEATURES", ",".join(str(round(v, places)) for v in c.centre),
                      str(round(c.span, places))]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _ref(e):
    """Whatever this kind of entity calls its human-readable reference."""
    return (getattr(e, "component_ref", None) or getattr(e, "opening_ref", None)
            or getattr(e, "room_id", None) or "")


def _sorted_by_geometry(entities):
    """A deterministic order that owes nothing to how the caller happened to collect the entities."""
    return sorted(entities, key=lambda e: (fingerprint(e), _ref(e)))


def assign_identity(entities, revision):
    """Give every entity a fingerprint-derived uid.  Identical geometry twice is reported, never hidden."""
    seen, duplicates = {}, []
    for e in _sorted_by_geometry(entities):
        fp = fingerprint(e)
        n = seen.get(fp, 0)
        seen[fp] = n + 1
        if n:
            duplicates.append(fp)
        e.uid = str(uuid.uuid5(NAMESPACE, f"{revision}|{fp}|{n}"))
        if e.persistent_id is None:
            e.persistent_id = str(uuid.uuid5(NAMESPACE, f"persistent|{fp}|{n}"))
    return {"ENTITIES": len(entities), "REVISION": revision,
            "DUPLICATE_GEOMETRY_FINGERPRINTS": sorted(set(duplicates)),
            "NOTE": "a duplicate fingerprint means two entities are geometrically identical; the engine reports "
                    "it rather than silently merging or silently keeping both"}


def _rects_of(e):
    return getattr(e, "rects", None) or [e.rect]


def _dimension_similarity(a, b):
    ba, bb = geom.bbox(_rects_of(a)), geom.bbox(_rects_of(b))
    dw = min(ba.width, bb.width) / max(ba.width, bb.width) if max(ba.width, bb.width) > 0 else 1.0
    dh = min(ba.height, bb.height) / max(ba.height, bb.height) if max(ba.height, bb.height) > 0 else 1.0
    return (dw + dh) / 2.0


def _label_of(e):
    return getattr(e, "label", None)


def match_score(prev, cur, tol):
    """How much evidence says these are the same object.  Geometry dominates; a label only breaks a tie."""
    i = geom.iou(_rects_of(prev), _rects_of(cur))
    ca, cb = geom.centroid(_rects_of(prev)), geom.centroid(_rects_of(cur))
    d = math.dist(ca, cb)
    span = max(geom.bbox(_rects_of(prev)).width, geom.bbox(_rects_of(prev)).height, tol)
    proximity = max(0.0, 1.0 - d / max(span, tol))
    dims = _dimension_similarity(prev, cur)
    label = 1.0 if (_label_of(prev) and _label_of(prev) == _label_of(cur)) else 0.0
    return {"SCORE": 0.60 * i + 0.20 * proximity + 0.15 * dims + 0.05 * label,
            "IOU": i, "CENTROID_DISTANCE_M": d, "DIMENSION_SIMILARITY": dims, "LABEL_EQUAL": bool(label)}


def match_revisions(previous, current, tol):
    """Carry identity across a revision, and name what happened to everything that did not match one to one.

    Splits and merges are decided BEFORE one-to-one matching, because half of a room that split still overlaps
    its parent enough to look like the parent moved.  Calling that a move is how a decision about one room ends
    up attached to half of it.
    """
    prev_list, cur_list = _sorted_by_geometry(previous), _sorted_by_geometry(current)

    def inter(a, b):
        return geom.intersection_area(_rects_of(a), _rects_of(b))

    def kin(a, b):
        """Only like can descend from like: a column inside a room is not a piece the room split into."""
        ka, kb = getattr(a, "kind", None), getattr(b, "kind", None)
        return a.floor == b.floor and (ka is None or kb is None or ka == kb)

    def substantial(p, c):
        """A parent and child share enough of BOTH their areas; containment alone is not descent."""
        i = inter(p, c)
        return (i >= SPLIT_SHARE * geom.total_area(_rects_of(c))
                and i >= SPLIT_SHARE * geom.total_area(_rects_of(p)))

    children = {id(p): [c for c in cur_list if kin(p, c) and substantial(p, c)] for p in prev_list}
    parents = {id(c): [p for p in prev_list if kin(p, c) and substantial(p, c)] for c in cur_list}
    split_parents = {id(p) for p in prev_list if len(children[id(p)]) >= 2}
    merge_children = {id(c) for c in cur_list if len(parents[id(c)]) >= 2}

    pairs = []
    for p in prev_list:
        if id(p) in split_parents:
            continue
        for c in cur_list:
            if p.floor != c.floor or id(c) in merge_children:
                continue
            m = match_score(p, c, tol)
            if m["IOU"] > 0 or m["CENTROID_DISTANCE_M"] <= tol:
                pairs.append((m, p, c))
    pairs.sort(key=lambda t: (-t[0]["SCORE"], fingerprint(t[1]), fingerprint(t[2])))

    best_by_c = {}
    for m, _p, c in pairs:
        best_by_c.setdefault(id(c), []).append(m["SCORE"])

    taken_p, taken_c, chosen, ambiguous = set(), set(), [], {}
    for m, p, c in pairs:
        if m["IOU"] < MIN_IOU_MATCH or id(p) in taken_p or id(c) in taken_c:
            continue
        rivals = sorted(best_by_c[id(c)], reverse=True)
        if len(rivals) > 1 and rivals[0] - rivals[1] < AMBIGUITY_BAND:
            ambiguous[id(c)] = {"BEST": rivals[0], "RUNNER_UP": rivals[1], "BAND": AMBIGUITY_BAND}
            continue
        taken_p.add(id(p))
        taken_c.add(id(c))
        chosen.append((m, p, c))

    records, emitted_c, emitted_p = [], set(), set()
    for m, p, c in chosen:
        same = fingerprint(p) == fingerprint(c)
        c.persistent_id = p.persistent_id
        emitted_c.add(id(c))
        emitted_p.add(id(p))
        records.append({"STATE": LINEAGE_UNCHANGED if same else LINEAGE_MODIFIED,
                        "PREVIOUS_UID": p.uid, "CURRENT_UID": c.uid, "PERSISTENT_ID": c.persistent_id,
                        "PREVIOUS_REF": _ref(p), "CURRENT_REF": _ref(c),
                        "EVIDENCE": m, "DECISIONS_CARRY_FORWARD": True})

    for p in prev_list:
        if id(p) not in split_parents:
            continue
        emitted_p.add(id(p))
        kids = children[id(p)]
        records.append({"STATE": LINEAGE_SPLIT, "PREVIOUS_UID": p.uid, "CURRENT_UID": None,
                        "PERSISTENT_ID": p.persistent_id, "PREVIOUS_REF": _ref(p), "CURRENT_REF": None,
                        "EVIDENCE": {"CHILDREN": [_ref(c) for c in kids],
                                     "SHARES": [round(inter(p, c) / geom.total_area(_rects_of(c)), 6)
                                                for c in kids]},
                        "DECISIONS_CARRY_FORWARD": False,
                        "WHY_NOT": "this entity became several; a decision about it must be re-attached "
                                   "deliberately to whichever part it now belongs to"})
        for c in kids:
            if id(c) in emitted_c:
                continue
            emitted_c.add(id(c))
            records.append({"STATE": LINEAGE_SPLIT, "PREVIOUS_UID": None, "CURRENT_UID": c.uid,
                            "PERSISTENT_ID": c.persistent_id, "PREVIOUS_REF": None, "CURRENT_REF": _ref(c),
                            "EVIDENCE": {"PARENT": _ref(p), "PARENT_UID": p.uid},
                            "DECISIONS_CARRY_FORWARD": False,
                            "WHY_NOT": "this is part of an entity that split; its parent's decisions are not "
                                       "automatically its own"})

    for c in cur_list:
        if id(c) not in merge_children or id(c) in emitted_c:
            continue
        emitted_c.add(id(c))
        ps = parents[id(c)]
        for p in ps:
            emitted_p.add(id(p))
        records.append({"STATE": LINEAGE_MERGED, "PREVIOUS_UID": None, "CURRENT_UID": c.uid,
                        "PERSISTENT_ID": c.persistent_id, "PREVIOUS_REF": None, "CURRENT_REF": _ref(c),
                        "EVIDENCE": {"PARENTS": [_ref(p) for p in ps],
                                     "PARENT_UIDS": [p.uid for p in ps]},
                        "DECISIONS_CARRY_FORWARD": False,
                        "WHY_NOT": "several entities became one; which of their decisions survives is not a "
                                   "geometric question"})

    for c in cur_list:
        if id(c) in emitted_c:
            continue
        state = LINEAGE_REVIEW if id(c) in ambiguous else LINEAGE_NEW
        records.append({"STATE": state, "PREVIOUS_UID": None, "CURRENT_UID": c.uid,
                        "PERSISTENT_ID": c.persistent_id, "PREVIOUS_REF": None, "CURRENT_REF": _ref(c),
                        "EVIDENCE": ambiguous.get(id(c), {}),
                        "DECISIONS_CARRY_FORWARD": False,
                        "WHY_NOT": ("two previous entities match this one equally well; the engine does not "
                                    "choose between them" if state == LINEAGE_REVIEW
                                    else "there was nothing here before")})
    for p in prev_list:
        if id(p) in emitted_p:
            continue
        records.append({"STATE": LINEAGE_REMOVED, "PREVIOUS_UID": p.uid, "CURRENT_UID": None,
                        "PERSISTENT_ID": p.persistent_id, "PREVIOUS_REF": _ref(p), "CURRENT_REF": None,
                        "EVIDENCE": {}, "DECISIONS_CARRY_FORWARD": False,
                        "WHY_NOT": "nothing in the new revision occupies this geometry"})
    records.sort(key=lambda r: (r["STATE"], r["CURRENT_UID"] or "", r["PREVIOUS_UID"] or ""))
    return records


def lineage_summary(records):
    out = {}
    for r in records:
        out[r["STATE"]] = out.get(r["STATE"], 0) + 1
    return out
