"""E31B — what the faces mean, checked against the raster without being led by it.

E31A walks the vector graph alone. This module is where the two
representations are finally allowed to meet, and the direction matters:

    faces are generated FIRST, from vector topology only
    then compared with the raster regions
    neither side is forced to match the other

The most valuable relationship class is VECTOR_SPLITS_RASTER: a vector face
that divides a region the raster kept whole may be the bathroom inside BED-04.
It may equally be a false split, and only the false-split control below can
tell them apart.

    A RECOVERY ENGINE THAT FINDS BED-04'S BATHROOM AND SPLITS TEN NORMAL
    BEDROOMS IS NOT SUCCESSFUL.

Micro-faces are classified before anything is done with them. There is no
`area < X -> delete` rule, for the same reason there is no such rule for
micro-edges: a 0.3 m² face may be a wall cavity, a shaft, a sliver, a
duplicate — or a real narrow space, and the four are told apart by topology,
not by size.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# How a vector face and a raster region relate. Six classes, and every face
# gets one — including the two that mean "these two representations disagree".
ONE_TO_ONE = "ONE_TO_ONE"
VECTOR_SPLITS_RASTER = "VECTOR_SPLITS_RASTER"
RASTER_SPLITS_VECTOR = "RASTER_SPLITS_VECTOR"
MANY_TO_MANY = "MANY_TO_MANY"
VECTOR_ONLY = "VECTOR_ONLY"
RASTER_ONLY = "RASTER_ONLY"

RELATIONSHIPS = (ONE_TO_ONE, VECTOR_SPLITS_RASTER, RASTER_SPLITS_VECTOR,
                 MANY_TO_MANY, VECTOR_ONLY, RASTER_ONLY)

# What a small face turns out to be. Classify, then decide — never the reverse.
REAL_NARROW_SPACE = "REAL_NARROW_SPACE"
WALL_CAVITY = "WALL_CAVITY"
SHAFT = "SHAFT"
GEOMETRIC_SLIVER = "GEOMETRIC_SLIVER"
DUPLICATE_ARTIFACT = "DUPLICATE_ARTIFACT"
MICRO_UNRESOLVED = "UNRESOLVED"

MICRO_CLASSES = (REAL_NARROW_SPACE, WALL_CAVITY, SHAFT, GEOMETRIC_SLIVER,
                 DUPLICATE_ARTIFACT, MICRO_UNRESOLVED)

# A face this small needs classifying before use. NOT a deletion threshold.
MICRO_AREA_M2 = 0.5
# A face longer than this multiple of its width is a sliver rather than a room.
SLIVER_ASPECT = 8.0
# A face narrower than this cannot be occupied floor at any scale a house uses.
MIN_HABITABLE_MM = 400.0
# Two faces overlapping by more than this share of the smaller are the same
# face found twice.
DUPLICATE_OVERLAP = 0.9


class FaceQaError(RuntimeError):
    """A face was compared to a region in a way that would force a match."""


@dataclass(frozen=True)
class Correspondence:
    face_id: str
    relationship: str
    raster_region_ids: tuple[int, ...]
    raster_space_ids: tuple[str, ...]
    vector_area_m2: float
    raster_area_m2: float | None
    overlap_ratio: float | None
    area_difference_m2: float | None
    why: str

    def record(self) -> dict:
        return {"face_id": self.face_id, "relationship": self.relationship,
                "raster_region_ids": list(self.raster_region_ids),
                "raster_space_ids": list(self.raster_space_ids),
                "vector_area_m2": round(self.vector_area_m2, 3),
                "raster_area_m2": (None if self.raster_area_m2 is None
                                   else round(self.raster_area_m2, 3)),
                "overlap_ratio": (None if self.overlap_ratio is None
                                  else round(self.overlap_ratio, 3)),
                "area_difference_m2": (None if self.area_difference_m2 is None
                                       else round(self.area_difference_m2, 3)),
                "why": self.why}


def _bbox_overlap(a, b) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    w = min(ax1, bx1) - max(ax0, bx0)
    h = min(ay1, by1) - max(ay0, by0)
    return max(0.0, w) * max(0.0, h)


def _bbox_area(b) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def correspond(faces, regions, *, min_overlap: float = 0.15
               ) -> list[Correspondence]:
    """Relate each vector face to the raster regions it overlaps.

    Bounding-box overlap, stated as such. It is a coarse measure and it is the
    honest one available without rasterising the faces: a precise polygon
    intersection would imply a precision the comparison does not have, and the
    classes below are about WHICH regions a face touches rather than by how
    much.

    `regions` maps region_id -> {"bbox_mm", "area_m2", "space_id"}.
    """
    out: list[Correspondence] = []
    face_hits: dict[str, list] = {}
    region_hits: dict[int, list] = {}

    for f in faces:
        fb = f.bbox_mm
        fa = _bbox_area(fb)
        for rid, r in regions.items():
            ov = _bbox_overlap(fb, r["bbox_mm"])
            if fa <= 0:
                continue
            share = ov / min(fa, _bbox_area(r["bbox_mm"]) or fa)
            if share >= min_overlap:
                face_hits.setdefault(f.face_id, []).append((rid, share))
                region_hits.setdefault(rid, []).append((f.face_id, share))

    for f in faces:
        hits = sorted(face_hits.get(f.face_id, ()), key=lambda h: -h[1])
        if not hits:
            out.append(Correspondence(
                f.face_id, VECTOR_ONLY, (), (), f.area_m2, None, None, None,
                "no raster region overlaps this face: the vector graph found a "
                "boundary the segmentation did not"))
            continue
        rids = tuple(r for r, _ in hits)
        spaces = tuple(sorted(
            regions[r].get("space_id", "") for r in rids
            if regions[r].get("space_id")))
        raster_area = sum(regions[r]["area_m2"] for r in rids)
        share = hits[0][1]

        # How many faces share this face's principal region?
        principal = rids[0]
        siblings = [h for h in region_hits.get(principal, ())
                    if h[0] != f.face_id]
        if len(rids) == 1 and not siblings:
            rel = ONE_TO_ONE
            why = "one face, one region, nothing else in either"
        elif len(rids) == 1 and siblings:
            rel = VECTOR_SPLITS_RASTER
            why = (f"{len(siblings) + 1} vector faces divide raster region "
                   f"{principal}, which the segmentation kept whole. This is "
                   "the class that may expose an under-segmented space — and "
                   "equally the class a false split hides in")
        elif len(rids) > 1 and not siblings:
            rel = RASTER_SPLITS_VECTOR
            why = (f"one vector face spans {len(rids)} raster regions: the "
                   "segmentation divided something the wall graph did not")
        else:
            rel = MANY_TO_MANY
            why = ("several faces and several regions overlap each other; "
                   "neither representation is a refinement of the other")
        out.append(Correspondence(
            f.face_id, rel, rids, spaces, f.area_m2, raster_area, share,
            f.area_m2 - raster_area, why))

    matched = {r for c in out for r in c.raster_region_ids}
    for rid, r in sorted(regions.items()):
        if rid in matched:
            continue
        out.append(Correspondence(
            f"(region {rid})", RASTER_ONLY, (rid,),
            (r.get("space_id", ""),) if r.get("space_id") else (),
            0.0, r["area_m2"], None, None,
            "the segmentation found this region and the vector graph produced "
            "no face over it"))
    return out


def classify_micro_faces(faces) -> list[dict]:
    """What each small face actually is. No size rule deletes anything.

    The categories are distinguished by geometry and topology:

      a face narrower than a person          cannot be occupied floor
      a long thin face between two walls     is a cavity or a sliver
      a small face wholly inside another     is a shaft or a hole
      two faces on the same footprint        are one face found twice
    """
    out: list[dict] = []
    by_box = {f.face_id: f.bbox_mm for f in faces}
    for f in faces:
        if f.area_m2 >= MICRO_AREA_M2:
            continue
        x0, y0, x1, y1 = f.bbox_mm
        w, h = x1 - x0, y1 - y0
        short, long_ = min(w, h), max(w, h)
        aspect = (long_ / short) if short else 1e9

        dup = None
        for g in faces:
            if g.face_id == f.face_id or g.area_m2 >= MICRO_AREA_M2:
                continue
            ov = _bbox_overlap(f.bbox_mm, by_box[g.face_id])
            if ov and ov / (_bbox_area(f.bbox_mm) or 1) >= DUPLICATE_OVERLAP:
                dup = g.face_id
                break

        inside = any(_bbox_overlap(f.bbox_mm, g.bbox_mm)
                     >= _bbox_area(f.bbox_mm) * 0.99
                     for g in faces
                     if g.face_id != f.face_id and g.area_m2 > f.area_m2)

        if dup:
            cls, why = DUPLICATE_ARTIFACT, (
                f"shares its footprint with {dup}: one face found twice")
        elif short < MIN_HABITABLE_MM and aspect >= SLIVER_ASPECT:
            cls, why = WALL_CAVITY, (
                f"{short:.0f} mm across and {aspect:.0f} times longer than "
                "wide: this is the space between two wall faces, not a room")
        elif aspect >= SLIVER_ASPECT:
            cls, why = GEOMETRIC_SLIVER, (
                f"aspect ratio {aspect:.0f}: a numerical sliver between nearly "
                "coincident boundaries")
        elif inside:
            cls, why = SHAFT, (
                "wholly inside a larger face: a shaft or a void, not a "
                "separate room")
        elif short >= MIN_HABITABLE_MM:
            cls, why = REAL_NARROW_SPACE, (
                f"{short:.0f} mm across: narrow, but wide enough to be real "
                "floor. It is NOT removed for being small")
        else:
            cls, why = MICRO_UNRESOLVED, (
                "too small to be floor and not explained by a cavity, shaft, "
                "sliver or duplicate. Held for review, not deleted")
        out.append({"face_id": f.face_id, "area_m2": round(f.area_m2, 4),
                    "short_side_mm": round(short, 1),
                    "aspect_ratio": round(aspect, 1),
                    "micro_class": cls, "why": why, "deleted": False})
    return out


def false_split_control(correspondences, *, stable_space_ids=()) -> dict:
    """Did recovery cost more than it found?

    A vector face that divides a raster space previously considered STABLE is
    the dangerous outcome, whatever else the run achieved. It is counted
    separately from a split of a space already known to be broken, because
    those are the splits we are hoping for.
    """
    stable = set(stable_space_ids)
    splits = [c for c in correspondences
              if c.relationship == VECTOR_SPLITS_RASTER]
    split_stable = [c for c in splits
                    if any(s in stable for s in c.raster_space_ids)]
    split_known_bad = [c for c in splits if c not in split_stable]
    return {
        "faces": len(correspondences),
        "by_relationship": dict(Counter(c.relationship
                                        for c in correspondences)),
        "raster_spaces_reproduced_one_to_one": sorted({
            s for c in correspondences if c.relationship == ONE_TO_ONE
            for s in c.raster_space_ids}),
        "vector_splits_of_a_STABLE_raster_space": [
            {"face_id": c.face_id, "spaces": list(c.raster_space_ids)}
            for c in split_stable],
        "vector_splits_of_a_KNOWN_BROKEN_space": [
            {"face_id": c.face_id, "spaces": list(c.raster_space_ids)}
            for c in split_known_bad],
        "raster_only": [c.raster_space_ids for c in correspondences
                        if c.relationship == RASTER_ONLY],
        "verdict": (
            "FALSE SPLITS PRESENT — recovery is splitting spaces that were "
            "already right, which costs more than it finds"
            if split_stable else
            "no stable raster space was split by a vector face"),
    }
