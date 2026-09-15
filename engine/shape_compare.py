"""E57 — two shapes can have the same area and not be the same shape.

Area agreement is a weak test and it is the one everybody reaches for. A
3.0 x 4.0 room and a 2.0 x 6.0 room both measure 12 m2; so does a polygon
offset two metres from where the room actually is. If the engine ever places a
boundary on the wrong side of a wall, or recovers the room next door, an
area-only comparison will report success.

So a room is compared as a SHAPE:

    intersection area     how much of the two actually coincide
    union area            how much either covers
    IoU                   intersection / union — 1.0 only for the same shape
    boundary deviation    the worst distance from one outline to the other
    area variance         the traditional number, kept but never alone
    perimeter variance    catches a shape that is right in area and wrong in
                          outline

BOTH SIDES MUST BE ON THE SAME BASIS. Comparing a centreline polygon against a
clear-internal region is comparing two different measurements that happen to
share a unit, and this module refuses it rather than returning a number.

The polygons here are rectilinear, so the intersection is computed by exact
cell decomposition over the combined coordinate grid: no clipping library, no
tolerance, and no approximation to explain away later.
"""

from __future__ import annotations

from dataclasses import dataclass


class ShapeCompareError(RuntimeError):
    """Two shapes were compared across bases, or without being shapes."""


def _point_in(poly, x: float, y: float) -> bool:
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y):
            xt = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < xt:
                inside = not inside
    return inside


def _area(poly) -> float:
    s = 0.0
    p = list(poly)
    for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s / 2)


def _cells(a, b):
    """The combined coordinate grid of two rectilinear polygons."""
    xs = sorted({p[0] for p in a} | {p[0] for p in b})
    ys = sorted({p[1] for p in a} | {p[1] for p in b})
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            yield x0, y0, x1, y1


def intersection_area(a, b) -> float:
    """Exact for rectilinear polygons: every cell is wholly in or wholly out."""
    la, lb = list(a), list(b)
    total = 0.0
    for x0, y0, x1, y1 in _cells(la, lb):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if _point_in(la, cx, cy) and _point_in(lb, cx, cy):
            total += (x1 - x0) * (y1 - y0)
    return total


def _seg_distance(px, py, x0, y0, x1, y1) -> float:
    dx, dy = x1 - x0, y1 - y0
    if dx == 0 and dy == 0:
        return ((px - x0) ** 2 + (py - y0) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    qx, qy = x0 + t * dx, y0 + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _to_boundary(poly, px, py) -> float:
    p = list(poly)
    return min(_seg_distance(px, py, a[0], a[1], b[0], b[1])
               for a, b in zip(p, p[1:] + p[:1]))


def boundary_deviation_mm(a, b) -> dict:
    """How far the two outlines wander from each other, both ways.

    A one-directional maximum misses the case where one outline is a subset of
    the other's path, so both directions are reported and the Hausdorff figure
    is the larger of them.
    """
    la, lb = list(a), list(b)
    a_to_b = [_to_boundary(lb, x, y) for x, y in la]
    b_to_a = [_to_boundary(la, x, y) for x, y in lb]
    return {"max_a_to_b_mm": round(max(a_to_b), 1) if a_to_b else None,
            "max_b_to_a_mm": round(max(b_to_a), 1) if b_to_a else None,
            "hausdorff_mm": round(max(max(a_to_b), max(b_to_a)), 1)
            if a_to_b and b_to_a else None,
            "mean_a_to_b_mm": round(sum(a_to_b) / len(a_to_b), 1)
            if a_to_b else None,
            "note": ("vertex-to-boundary distance on both sides. It catches a "
                     "polygon of the right AREA in the wrong PLACE, which an "
                     "area comparison cannot")}


@dataclass(frozen=True)
class ShapeComparison:
    """One room's vector polygon against one reference polygon."""

    space_id: str
    basis: str
    vector_area_m2: float
    reference_area_m2: float
    intersection_m2: float
    union_m2: float
    vector_perimeter_m: float | None = None
    reference_perimeter_m: float | None = None
    deviation: dict = None
    why: str = ""

    @property
    def iou(self) -> float:
        return (self.intersection_m2 / self.union_m2) if self.union_m2 else 0.0

    @property
    def area_variance_pct(self) -> float | None:
        if not self.reference_area_m2:
            return None
        return abs(self.vector_area_m2 - self.reference_area_m2) \
            / self.reference_area_m2 * 100

    @property
    def perimeter_variance_pct(self) -> float | None:
        if not self.reference_perimeter_m or self.vector_perimeter_m is None:
            return None
        return abs(self.vector_perimeter_m - self.reference_perimeter_m) \
            / self.reference_perimeter_m * 100

    @property
    def area_agrees_but_shape_does_not(self) -> bool:
        """The failure an area-only comparison cannot see."""
        av = self.area_variance_pct
        return av is not None and av < 5.0 and self.iou < 0.9

    def record(self) -> dict:
        return {"space_id": self.space_id, "basis": self.basis,
                "vector_area_m2": round(self.vector_area_m2, 3),
                "reference_area_m2": round(self.reference_area_m2, 3),
                "vector_perimeter_m": (None if self.vector_perimeter_m is None
                                       else round(self.vector_perimeter_m, 3)),
                "reference_perimeter_m": (
                    None if self.reference_perimeter_m is None
                    else round(self.reference_perimeter_m, 3)),
                "intersection_m2": round(self.intersection_m2, 3),
                "union_m2": round(self.union_m2, 3),
                "iou": round(self.iou, 4),
                "area_variance_pct": (None if self.area_variance_pct is None
                                      else round(self.area_variance_pct, 2)),
                "perimeter_variance_pct": (
                    None if self.perimeter_variance_pct is None
                    else round(self.perimeter_variance_pct, 2)),
                "boundary_deviation": self.deviation,
                "area_agrees_but_shape_does_not":
                    self.area_agrees_but_shape_does_not,
                "why": self.why}


def compare(space_id: str, vector_poly, reference_poly, *, basis: str,
            reference_basis: str, vector_perimeter_m: float | None = None,
            reference_perimeter_m: float | None = None) -> ShapeComparison:
    """Compare two rectilinear polygons — only on a matching basis."""
    if basis != reference_basis:
        raise ShapeCompareError(
            f"{space_id}: refusing to compare a {basis} polygon against a "
            f"{reference_basis} one. NEVER COMPARE UNLIKE BASES — they are "
            "different measurements that happen to share a unit")
    if len(vector_poly) < 3 or len(reference_poly) < 3:
        raise ShapeCompareError(
            f"{space_id}: a shape needs at least three vertices")
    va, ra = _area(vector_poly), _area(reference_poly)
    inter = intersection_area(vector_poly, reference_poly)
    union = va + ra - inter
    return ShapeComparison(
        space_id=space_id, basis=basis,
        vector_area_m2=va / 1_000_000, reference_area_m2=ra / 1_000_000,
        intersection_m2=inter / 1_000_000, union_m2=union / 1_000_000,
        vector_perimeter_m=vector_perimeter_m,
        reference_perimeter_m=reference_perimeter_m,
        deviation=boundary_deviation_mm(vector_poly, reference_poly),
        why=("polygon intersection over union, plus boundary deviation. Area "
             "alone can agree while the shape is wrong"))


def summary(comparisons) -> dict:
    """The shape distribution. Still no acceptance threshold."""
    if not comparisons:
        return {"rooms_compared": 0,
                "note": "no room has both a vector polygon and a reference "
                        "polygon on the same basis"}
    ious = sorted(c.iou for c in comparisons)
    devs = [c.deviation["hausdorff_mm"] for c in comparisons
            if c.deviation and c.deviation.get("hausdorff_mm") is not None]
    mid = len(ious) // 2
    return {
        "rooms_compared": len(comparisons),
        "median_iou": round(ious[mid], 4),
        "worst_iou": round(ious[0], 4),
        "worst_room": min(comparisons, key=lambda c: c.iou).space_id,
        "median_hausdorff_mm": (round(sorted(devs)[len(devs) // 2], 1)
                                if devs else None),
        "max_hausdorff_mm": round(max(devs), 1) if devs else None,
        "rooms_where_area_agrees_but_shape_does_not": [
            c.space_id for c in comparisons if c.area_agrees_but_shape_does_not],
        "acceptance_threshold": None,
        "acceptance_note": ("no IoU threshold is set from one project. First "
                            "measure the distribution"),
    }
