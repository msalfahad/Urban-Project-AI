"""E56 — a closed cycle is not a room, and a sum of cycles is not an area.

The first space-graph run reported:

    bounded area = 1102.64 m2

That figure is meaningless. It adds a 989 m2 cycle to the cycles INSIDE it. The
building envelope and every room it contains were summed together, so the total
counts most of the floor at least twice. It is not a project metric and it is
not a bug in the arithmetic — it is a category error: a set of closed walks is
not a set of spaces.

    NOT EVERY COUNTERCLOCKWISE BOUNDED WALK IS ONE OCCUPIABLE ROOM.

A cycle can be the building envelope, a room, a shaft inside a room, a wall
cavity, a sliver, or a nested artefact of the walker. Those are told apart by
CONTAINMENT and by what they hold, not by size and not by orientation.

So this module builds the containment hierarchy first, classifies each cycle
from its position in it, and only then names a non-overlapping ATOMIC SPACE
set whose areas may legitimately be added.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# What a cycle turns out to be, once its position in the hierarchy is known.
BUILDING_ENVELOPE = "BUILDING_ENVELOPE"
ATOMIC_SPACE_FACE = "ATOMIC_SPACE_FACE"
ENCLOSURE_CYCLE = "ENCLOSURE_CYCLE"
HOLE = "HOLE"
WALL_CAVITY = "WALL_CAVITY"
MICRO_FACE = "MICRO_FACE"
UNRESOLVED_NESTED_FACE = "UNRESOLVED_NESTED_FACE"

CYCLE_CLASSES = (BUILDING_ENVELOPE, ATOMIC_SPACE_FACE, ENCLOSURE_CYCLE, HOLE,
                 WALL_CAVITY, MICRO_FACE, UNRESOLVED_NESTED_FACE)

# How two cycles sit relative to each other.
CONTAINS = "CONTAINS"
CONTAINED_BY = "CONTAINED_BY"
SIBLING = "SIBLING"
OVERLAPS_WITHOUT_CONTAINMENT = "OVERLAPS_WITHOUT_CONTAINMENT"
DISJOINT = "DISJOINT"

# A cycle smaller than this needs classifying before anything is done with it.
# NOT a deletion threshold — nothing here deletes a face.
MICRO_AREA_M2 = 0.5
# A cycle longer than this multiple of its width is a cavity or a sliver.
CAVITY_ASPECT = 8.0
# Narrower than this cannot be occupied floor at any scale a house uses.
MIN_HABITABLE_MM = 400.0
# An envelope candidate must hold at least this many labelled rooms. One room
# inside a bigger cycle is a nesting question, not a whole building.
ENVELOPE_MIN_LABELS = 3


class NestingError(RuntimeError):
    """A face set was summed or classified without resolving containment."""


@dataclass(frozen=True)
class NestedFace:
    """One cycle, its place in the hierarchy, and what that makes it."""

    space_face_id: str
    area_m2: float
    perimeter_m: float
    cycle_class: str
    depth: int = 0
    parent_id: str = ""
    child_ids: tuple[str, ...] = ()
    sibling_ids: tuple[str, ...] = ()
    overlapping_ids: tuple[str, ...] = ()
    labelled_space_ids: tuple[str, ...] = ()
    portal_edge_count: int = 0
    min_extent_mm: float = 0.0
    aspect: float = 0.0
    why: str = ""

    @property
    def is_atomic(self) -> bool:
        return self.cycle_class == ATOMIC_SPACE_FACE

    @property
    def net_area_m2(self) -> float:
        """This cycle's area with its own holes still in it.

        Reported as-is; `atomic_area_m2` below is the figure that subtracts
        holes, and it is the only one that may be added to anything.
        """
        return self.area_m2

    def record(self) -> dict:
        return {"space_face_id": self.space_face_id,
                "cycle_class": self.cycle_class,
                "area_m2": round(self.area_m2, 3),
                "perimeter_m": round(self.perimeter_m, 3),
                "depth": self.depth, "parent": self.parent_id,
                "children": list(self.child_ids),
                "siblings": list(self.sibling_ids),
                "overlaps_without_containment": list(self.overlapping_ids),
                "labelled_space_ids": list(self.labelled_space_ids),
                "labelled_rooms_inside": len(self.labelled_space_ids),
                "portal_edges": self.portal_edge_count,
                "min_extent_mm": round(self.min_extent_mm, 1),
                "aspect": round(self.aspect, 2),
                "is_atomic_space": self.is_atomic,
                "why": self.why}


def _point_in(poly, x: float, y: float) -> bool:
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y):
            xt = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xt:
                inside = not inside
    return inside


def _all_in(outer, inner) -> bool:
    """Is every vertex of `inner` inside `outer`?

    Every vertex, not the first one. A single-vertex test calls two cycles
    that cross each other "contained", and a containment tree built on that is
    a tree of the wrong shape.
    """
    op = list(outer)
    return all(_point_in(op, x, y) for x, y in inner)


def _any_in(outer, inner) -> bool:
    op = list(outer)
    return any(_point_in(op, x, y) for x, y in inner)


def _extent(poly) -> tuple[float, float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (max(xs) - min(xs), max(ys) - min(ys))


def hierarchy(faces, regions=None) -> list[NestedFace]:
    """The containment tree, then a class for every cycle in it.

    Depth decides most of it. A cycle at depth 0 holding three or more
    labelled rooms is the building envelope; a cycle inside a space is a hole
    or a cavity; a cycle whose parent chain is ambiguous says so rather than
    being promoted to a room.
    """
    labelled = [(r["space_id"], r["centroid_mm"]) for r in
                (regions or {}).values() if r.get("space_id")]
    polys = {f.space_face_id: list(f.polygon_mm) for f in faces}

    contains: dict[str, set] = {f.space_face_id: set() for f in faces}
    overlaps: dict[str, set] = {f.space_face_id: set() for f in faces}
    for a in faces:
        for b in faces:
            if a.space_face_id == b.space_face_id:
                continue
            if b.area_m2 > a.area_m2:
                continue
            if _all_in(polys[a.space_face_id], polys[b.space_face_id]):
                contains[a.space_face_id].add(b.space_face_id)
            elif _any_in(polys[a.space_face_id], polys[b.space_face_id]):
                overlaps[a.space_face_id].add(b.space_face_id)
                overlaps[b.space_face_id].add(a.space_face_id)

    # Immediate parent = the SMALLEST cycle that contains this one.
    by_id = {f.space_face_id: f for f in faces}
    parent: dict[str, str] = {}
    for fid in by_id:
        holders = [h for h, kids in contains.items() if fid in kids]
        if holders:
            parent[fid] = min(holders, key=lambda h: by_id[h].area_m2)

    children: dict[str, list] = {fid: [] for fid in by_id}
    for fid, pid in parent.items():
        children[pid].append(fid)

    def depth_of(fid: str, seen=()) -> int:
        if fid not in parent or fid in seen:
            return 0
        return 1 + depth_of(parent[fid], seen + (fid,))

    out: list[NestedFace] = []
    for f in faces:
        fid = f.space_face_id
        poly = polys[fid]
        inside = tuple(sorted(sid for sid, (cx, cy) in labelled
                              if _point_in(poly, cx, cy)))
        # Labels that belong to THIS cycle rather than to a child of it.
        own = tuple(sorted(set(inside) - {
            sid for kid in children[fid]
            for sid in _labels_in(polys[kid], labelled)}))
        w, h = _extent(poly)
        small, large = (min(w, h), max(w, h))
        aspect = (large / small) if small else 0.0
        d = depth_of(fid)
        sibs = tuple(sorted(
            s for s in children.get(parent.get(fid, ""), ()) if s != fid))
        cls, why = _classify(
            f, depth=d, labels=own, all_labels=inside, aspect=aspect,
            min_extent=small, has_parent=fid in parent,
            overlapping=bool(overlaps[fid]))
        out.append(NestedFace(
            space_face_id=fid, area_m2=f.area_m2, perimeter_m=f.perimeter_m,
            cycle_class=cls, depth=d, parent_id=parent.get(fid, ""),
            child_ids=tuple(sorted(children[fid])), sibling_ids=sibs,
            overlapping_ids=tuple(sorted(overlaps[fid])),
            labelled_space_ids=own,
            portal_edge_count=len(getattr(f, "portal_edge_ids", ())),
            min_extent_mm=small, aspect=aspect, why=why))
    return sorted(out, key=lambda n: (n.depth, -n.area_m2))


def _labels_in(poly, labelled) -> set:
    return {sid for sid, (cx, cy) in labelled if _point_in(list(poly), cx, cy)}


def _classify(face, *, depth: int, labels, all_labels, aspect: float,
              min_extent: float, has_parent: bool, overlapping: bool
              ) -> tuple[str, str]:
    """What this cycle is, from its position and its contents.

    Order matters. The envelope test comes first because a whole-floor cycle
    holding every room in the villa is not "a room whose dividing walls are
    missing" — calling it that sends the next round hunting for a wall that
    was never meant to exist.
    """
    if depth == 0 and len(all_labels) >= ENVELOPE_MIN_LABELS:
        return BUILDING_ENVELOPE, (
            f"a depth-0 cycle containing {len(all_labels)} labelled rooms. "
            "This is the external boundary of the floor, NOT a room whose "
            "dividing walls are missing")
    if min_extent < MIN_HABITABLE_MM:
        return WALL_CAVITY, (
            f"{min_extent:.0f} mm across at its narrowest: too narrow to be "
            "occupied floor at any scale a house uses")
    if face.area_m2 < MICRO_AREA_M2:
        return MICRO_FACE, (
            f"{face.area_m2:.3f} m2 needs classifying before use. NOTHING "
            "here deletes it")
    if aspect >= CAVITY_ASPECT:
        return WALL_CAVITY, (
            f"aspect {aspect:.1f}: a long thin cycle between two walls is a "
            "cavity or a sliver, not a room")
    if overlapping and not labels:
        return UNRESOLVED_NESTED_FACE, (
            "this cycle overlaps another without containing it or being "
            "contained by it, and holds no labelled room of its own")
    if has_parent and not labels:
        return HOLE, (
            "a cycle wholly inside another with no labelled room of its own: "
            "a shaft or a void. Its parent's floor area must exclude it")
    # Before the overlap test: a cycle holding several labelled rooms is the
    # most informative thing this module can say about it, and §13 asks for
    # exactly that diagnosis. Overlap keeps it out of the atomic set anyway,
    # so nothing can be double-counted by naming it properly.
    if len(labels) > 1:
        return ENCLOSURE_CYCLE, (
            f"{len(labels)} labelled rooms inside one cycle "
            f"({', '.join(labels)}): an enclosure of several spaces, so a "
            "dividing boundary is missing or a portal over-closed"
            + (". It also overlaps another cycle without containing it"
               if overlapping else ""))
    if overlapping:
        return UNRESOLVED_NESTED_FACE, (
            "this cycle overlaps another without containing it or being "
            "contained by it. Neither is a refinement of the other, so "
            "neither may be treated as an atomic space")
    if len(labels) == 1:
        return ATOMIC_SPACE_FACE, (
            f"one labelled room ({labels[0]}) and nothing nested that holds "
            "another. ATOMIC CANDIDATE — its identity is a separate question")
    return UNRESOLVED_NESTED_FACE, (
        "a plausible cycle with no labelled room inside it. It may be "
        "circulation nobody labelled, or an artefact; unresolved either way")


# §13 — why a cycle holds more than one room. NOT always a missing wall.
WALL_EXTRACTION_MISSING = "WALL_EXTRACTION_MISSING"
WALL_PAIRING_MISSING = "WALL_PAIRING_MISSING"
PORTAL_OVER_CLOSURE = "PORTAL_OVER_CLOSURE"
FACE_NESTING_ARTIFACT = "FACE_NESTING_ARTIFACT"
SEMANTIC_IDENTITY_ERROR = "SEMANTIC_IDENTITY_ERROR"
DIVIDER_UNRESOLVED = "UNRESOLVED"

DIVIDER_CAUSES = (WALL_EXTRACTION_MISSING, WALL_PAIRING_MISSING,
                  PORTAL_OVER_CLOSURE, FACE_NESTING_ARTIFACT,
                  SEMANTIC_IDENTITY_ERROR, DIVIDER_UNRESOLVED)


def diagnose_enclosures(nested, faces, regions=None, *, rejections=(),
                        portals=(), index=None) -> list[dict]:
    """For each cycle holding several rooms: where the divider should be, and
    which of five causes explains its absence.

    DO NOT ASSUME EVERY MULTI-ROOM FACE IS MISSING A WALL. A cycle can hold
    two labels because a portal closed something it should not have, because
    the walker nested two cycles wrongly, or because one of the two labels is
    not where the drawing says it is. Each is a different repair, and guessing
    "missing wall" sends the next round looking for geometry that is present.
    """
    by_face = {f.space_face_id: f for f in faces}
    labelled = {r["space_id"]: r["centroid_mm"] for r in
                (regions or {}).values() if r.get("space_id")}
    index = dict(index or {})
    out = []
    for n in nested:
        if n.cycle_class != ENCLOSURE_CYCLE:
            continue
        f = by_face.get(n.space_face_id)
        pts = [labelled[s] for s in n.labelled_space_ids if s in labelled]
        # The divider should run BETWEEN the labelled rooms: the perpendicular
        # bisector band of the two most separated centroids.
        where = None
        if len(pts) >= 2:
            (x0, y0), (x1, y1) = pts[0], pts[-1]
            horizontal = abs(x1 - x0) >= abs(y1 - y0)
            where = {
                "axis": "V" if horizontal else "H",
                "at_mm": round((x0 + x1) / 2 if horizontal
                               else (y0 + y1) / 2, 1),
                "between": [n.labelled_space_ids[0], n.labelled_space_ids[-1]],
                "separation_mm": round(
                    max(abs(x1 - x0), abs(y1 - y0)), 1)}

        near_rejections = []
        if where is not None:
            for r in rejections:
                ax = r.get("axis")
                at = r.get("centreline_mm", r.get("fixed_mm"))
                if ax == where["axis"] and at is not None and abs(
                        at - where["at_mm"]) <= 800:
                    near_rejections.append(r.get("rejection_id")
                                           or r.get("face_id") or "?")

        portal_ids = list(getattr(f, "portal_edge_ids", ()) or ())
        unhosted = [pid for pid in portal_ids
                    if pid in index and not index[pid].host_wall_band_id]
        cause, why = _divider_cause(
            n, near_rejections, portal_ids, unhosted)
        out.append({
            "space_face_id": n.space_face_id,
            "area_m2": round(n.area_m2, 3),
            "contained_semantic_observations": list(n.labelled_space_ids),
            "candidate_dividing_wall": where,
            "wall_band_evidence_near_divider": near_rejections,
            "unpaired_faces_near_divider": len(near_rejections),
            "portal_candidates_on_this_face": portal_ids,
            "portals_with_no_host": unhosted,
            "overlaps_without_containment": list(n.overlapping_ids),
            "divider_cause": cause,
            "why": why,
        })
    return out


def _divider_cause(n, near_rejections, portal_ids, unhosted) -> tuple[str, str]:
    """Which of the five, on the evidence actually present."""
    if n.overlapping_ids:
        return FACE_NESTING_ARTIFACT, (
            f"this cycle overlaps {len(n.overlapping_ids)} other cycle(s) "
            "without containing them. The walk itself is suspect before any "
            "wall is blamed")
    if unhosted:
        return PORTAL_OVER_CLOSURE, (
            f"{len(unhosted)} of {len(portal_ids)} portal closures on this "
            "face name no host wall band. A closure between two unrelated "
            "walls can merge two spaces into one cycle")
    if len(portal_ids) >= 3:
        return PORTAL_OVER_CLOSURE, (
            f"{len(portal_ids)} portal closures on one cycle. A false closure "
            "merges topology, and a cycle leaning on this many of them has "
            "not been tested by any of them")
    if near_rejections:
        return WALL_PAIRING_MISSING, (
            f"{len(near_rejections)} rejected wall face(s) lie on the divider "
            "line. The wall was DRAWN and did not pair into a band, so this "
            "is a pairing failure rather than a missing wall")
    return WALL_EXTRACTION_MISSING, (
        "no wall band and no rejected face on the divider line, and the "
        "portals on this cycle are hosted. On the evidence present the "
        "dividing wall was not extracted at all — the weakest of the five "
        "conclusions, so it is the one drawn last")


def atomic_set(nested) -> dict:
    """The non-overlapping subset whose areas may legitimately be added.

    Everything else is reported in its own bucket. There is no single "bounded
    area" figure, because the quantity a reader wants — occupiable floor — is
    not the sum of closed walks.
    """
    atoms = [n for n in nested if n.is_atomic]
    by_id = {n.space_face_id: n for n in nested}
    # An atom's own holes come out of its area. A shaft inside a bedroom is
    # not bedroom floor.
    net = {}
    for a in atoms:
        holes = sum(by_id[c].area_m2 for c in a.child_ids
                    if c in by_id and by_id[c].cycle_class in (HOLE,
                                                               WALL_CAVITY))
        net[a.space_face_id] = a.area_m2 - holes
    # Overlap check, on the atoms only: an atomic set that double-counts area
    # is not atomic.
    clashes = [a.space_face_id for a in atoms
               if set(a.overlapping_ids) & {b.space_face_id for b in atoms}]
    nesting = [a.space_face_id for a in atoms
               if a.parent_id in {b.space_face_id for b in atoms}]
    return {
        "atomic_space_candidates": len(atoms),
        "atomic_area_m2": round(sum(net.values()), 3),
        "atomic_net_area_by_face": {k: round(v, 3) for k, v in net.items()},
        "holes_deducted_m2": round(
            sum(a.area_m2 for a in atoms) - sum(net.values()), 3),
        "non_overlapping": not clashes and not nesting,
        "overlapping_atoms": clashes,
        "atoms_nested_inside_other_atoms": nesting,
        "by_cycle_class": dict(Counter(n.cycle_class for n in nested)),
        "building_envelope_candidates": [
            n.space_face_id for n in nested
            if n.cycle_class == BUILDING_ENVELOPE],
        "enclosure_cycles": [n.space_face_id for n in nested
                             if n.cycle_class == ENCLOSURE_CYCLE],
        "excluded_from_the_total": {
            c: round(sum(n.area_m2 for n in nested if n.cycle_class == c), 3)
            for c in (BUILDING_ENVELOPE, ENCLOSURE_CYCLE, HOLE, WALL_CAVITY,
                      MICRO_FACE, UNRESOLVED_NESTED_FACE)},
        "note": ("the sum of bounded cycles is NOT a project area: it adds "
                 "the building envelope to the rooms inside it. Only the "
                 "atomic set is additive, and it is additive only because it "
                 "was checked for overlap and nesting"),
    }


def assert_additive(nested) -> None:
    """Refuse to publish a total over a face set that is not atomic."""
    out = atomic_set(nested)
    if not out["non_overlapping"]:
        raise NestingError(
            "these faces may not be summed: "
            + (f"atoms overlap: {out['overlapping_atoms']}. "
               if out["overlapping_atoms"] else "")
            + (f"atoms nested inside atoms: "
               f"{out['atoms_nested_inside_other_atoms']}. "
               if out["atoms_nested_inside_other_atoms"] else "")
            + "A sum over overlapping cycles counts the same floor twice")
