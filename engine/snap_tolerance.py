"""E69 — the snap grid is a measurement of this drawing, not a constant.

Round 1 snapped wall-polygon vertices onto a 0.05 mm grid and justified it as
"one two-thousandth of the thinnest wall". That reasoning is sound enough to
choose a safe number and not sound enough to publish one: it is a ratio to a
wall, not a measurement of the coordinates being snapped, and the next
drawing has different coordinates.

So the tolerance is measured. Vertices that OUGHT to be the same node are
separated either by representation noise — floating-point and PDF precision,
which is orders of magnitude below a millimetre — or by a real gap between
two walls that do not meet. A histogram of near-coincidence distances shows
whether those two populations separate. If they do, the noise floor is where
the recommendation goes. If they do NOT, no tolerance is defensible and this
module says so rather than picking one.

    SNAPPING IS NOT GAP-CLOSING.

Two hard limits survive any measurement:

* a recommendation may never exceed MAX_DEFENSIBLE_SNAP_MM, because above
  that it manufactures material between walls that were drawn apart;
* a measurement that cannot separate the two populations returns NO
  recommendation. A tolerance chosen to make a report pass is not a
  tolerance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The absolute ceiling, whatever the measurement says. Mirrors
# engine.wall_solid.MAX_DEFENSIBLE_SNAP_MM and is asserted equal to it.
MAX_DEFENSIBLE_SNAP_MM = 1.0

# Only pairs closer than this are candidates for being the same node. Beyond
# it the question is not "are these one point" but "why is there a gap".
CANDIDATE_REACH_MM = MAX_DEFENSIBLE_SNAP_MM

# Decade bins from a picometre up to the ceiling. Representation noise and
# drawn gaps differ by orders of magnitude, so decades are the right
# resolution: a linear histogram would put both in one bucket.
DECADES = (1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1.0)

MEASURED = "MEASURED_NUMERICAL_SNAP_TOLERANCE"
NOT_SEPARABLE = "NOISE_AND_GAPS_NOT_SEPARABLE"
NO_COINCIDENCES = "NO_NEAR_COINCIDENT_VERTICES_TO_MEASURE"


class SnapToleranceError(RuntimeError):
    """A tolerance was asked for that the coordinates do not support."""


@dataclass(frozen=True)
class SnapEvidence:
    """What the coordinates say, and what may be concluded from it."""

    status: str
    pairs_examined: int = 0
    vertices: int = 0
    histogram: dict = field(default_factory=dict)
    noise_floor_mm: float | None = None
    first_empty_decade_mm: float | None = None
    recommended_grid_mm: float | None = None
    ceiling_mm: float = MAX_DEFENSIBLE_SNAP_MM
    largest_coincidence_mm: float | None = None
    why: str = ""

    @property
    def is_usable(self) -> bool:
        return self.status == MEASURED and self.recommended_grid_mm is not None

    def record(self) -> dict:
        return {
            "metric": MEASURED,
            "status": self.status,
            "vertices": self.vertices,
            "pairs_examined": self.pairs_examined,
            "near_coincidence_histogram_mm": dict(self.histogram),
            "noise_floor_mm": self.noise_floor_mm,
            "first_empty_decade_mm": self.first_empty_decade_mm,
            "recommended_grid_mm": self.recommended_grid_mm,
            "absolute_ceiling_mm": self.ceiling_mm,
            "largest_near_coincidence_mm": self.largest_coincidence_mm,
            "is_usable": self.is_usable,
            "why": self.why,
            "not_a_drawing_constant": (
                "this is a measurement of THIS drawing's coordinates. It is "
                "recorded per run and must not be promoted to a project or "
                "engine default: the next sheet is produced by different "
                "software with different precision"),
            "snapping_is_not_gap_closing": (
                "the recommendation sits at the representation-noise floor. "
                "A gap larger than that is two walls that do not meet, and "
                "closing it would invent material"),
        }


def measure(rings, *, reach_mm: float = CANDIDATE_REACH_MM) -> SnapEvidence:
    """Measure near-coincidence among vertices that ought to be one node.

    `rings` is an iterable of coordinate sequences. Only pairs from
    DIFFERENT rings are counted: two vertices of one ring are meant to be
    distinct corners, and including them would put real wall lengths into a
    histogram of noise.
    """
    import math

    pts: list = []
    for i, ring in enumerate(rings):
        for x, y in ring:
            pts.append((float(x), float(y), i))
    if len(pts) < 2:
        return SnapEvidence(NO_COINCIDENCES, vertices=len(pts), why=(
            "fewer than two vertices: nothing to measure"))

    # Bucket by a cell the size of the reach so only neighbours are compared.
    cells: dict = {}
    for p in pts:
        cells.setdefault((int(p[0] // reach_mm), int(p[1] // reach_mm)),
                         []).append(p)

    counts = {d: 0 for d in DECADES}
    pairs, largest = 0, None
    seen: set = set()
    for (cx, cy), bucket in cells.items():
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.extend(cells.get((cx + dx, cy + dy), ()))
        for a in bucket:
            for b in near:
                if a is b or a[2] == b[2]:
                    continue
                key = (id(a), id(b)) if id(a) < id(b) else (id(b), id(a))
                if key in seen:
                    continue
                seen.add(key)
                d = math.hypot(a[0] - b[0], a[1] - b[1])
                if d > reach_mm:
                    continue
                pairs += 1
                if largest is None or d > largest:
                    largest = d
                for cut in DECADES:
                    if d <= cut:
                        counts[cut] += 1
                        break

    if not pairs:
        return SnapEvidence(NO_COINCIDENCES, vertices=len(pts),
                            histogram={_k(d): 0 for d in DECADES}, why=(
            f"no two vertices from different rings lie within {reach_mm} mm "
            "of each other. Nothing needs snapping, and no tolerance is "
            "warranted"))

    hist = {_k(d): counts[d] for d in DECADES}

    # The noise floor is the top of the OCCUPIED decades, not the first gap
    # inside them. Exactly-coincident nodes sit many decades below
    # representation noise, so the histogram is expected to be bimodal, and
    # stopping at the first empty decade would recommend a grid too small to
    # merge the very nodes it exists to merge.
    occupied = [d for d in DECADES if counts[d]]
    if not occupied:
        return SnapEvidence(NOT_SEPARABLE, vertices=len(pts),
                            pairs_examined=pairs, histogram=hist,
                            largest_coincidence_mm=largest, why=(
            "every near-coincidence fell outside the measured decades"))

    floor = occupied[-1]
    # Separation is only proven by an EMPTY band between the top of the
    # near-coincidence population and the ceiling. Without one there is no
    # distance at which snapping is provably not gap-closing.
    above = [d for d in DECADES if d > floor]
    empty = next((d for d in above if not counts[d]), None)

    if empty is None:
        return SnapEvidence(
            NOT_SEPARABLE, vertices=len(pts), pairs_examined=pairs,
            histogram=hist, noise_floor_mm=None,
            largest_coincidence_mm=largest, why=(
                f"near-coincidence distances reach {_k(floor)} mm with no "
                f"empty decade between there and the {reach_mm} mm ceiling. "
                "Representation noise and real gaps cannot be told apart on "
                "this drawing, so there is no distance at which snapping is "
                "provably not gap-closing. Snap nothing and report the gaps "
                "instead"))

    rec = min(floor, MAX_DEFENSIBLE_SNAP_MM)
    return SnapEvidence(
        MEASURED, vertices=len(pts), pairs_examined=pairs, histogram=hist,
        noise_floor_mm=floor, first_empty_decade_mm=empty,
        recommended_grid_mm=rec, largest_coincidence_mm=largest, why=(
            f"{pairs} vertex pairs from different rings lie within "
            f"{reach_mm} mm of each other. The largest of them is "
            f"{largest:.6g} mm, the population reaches {_k(floor)} mm, and "
            f"every decade from {_k(empty)} mm up to the {reach_mm} mm "
            f"ceiling is EMPTY — a clear band with nothing in it. So "
            f"representation noise on this drawing ends at {_k(floor)} mm "
            f"and the nearest thing anybody drew is at least {empty:g} mm "
            f"away. The grid goes at {rec} mm: large enough to merge the "
            "coincident nodes, orders of magnitude too small to close "
            "anything drawn"))


def compare_to_the_grid_in_use(evidence, grid_in_use: float) -> dict:
    """Judge the grid the run actually used against the measurement.

    The point is not to discover that a chosen constant was wrong. It is
    that a constant chosen by ratio to a wall cannot be right or wrong,
    because nothing measured it. Once something has, the constant becomes
    auditable.
    """
    rec = evidence.recommended_grid_mm
    if not evidence.is_usable or not rec:
        return {"grid_in_use_mm": grid_in_use,
                "verdict": "NOT_MEASURABLE_ON_THIS_DRAWING",
                "why": evidence.why}
    ratio = grid_in_use / rec if rec else None
    if grid_in_use > MAX_DEFENSIBLE_SNAP_MM:
        verdict = "ABOVE_THE_ABSOLUTE_CEILING"
    elif grid_in_use < rec:
        verdict = "SMALLER_THAN_THE_MEASURED_NOISE_FLOOR"
    elif ratio is not None and ratio <= 10.0:
        verdict = "SAFE_AND_WITHIN_AN_ORDER_OF_THE_MEASUREMENT"
    else:
        verdict = "SAFE_BUT_LARGER_THAN_THE_MEASUREMENT_WARRANTS"
    return {
        "grid_in_use_mm": grid_in_use,
        "measured_recommendation_mm": rec,
        "ratio_to_the_measurement": (None if ratio is None
                                     else round(ratio, 2)),
        "largest_near_coincidence_mm": evidence.largest_coincidence_mm,
        "first_empty_decade_mm": evidence.first_empty_decade_mm,
        "verdict": verdict,
        "still_below_anything_drawn": bool(
            evidence.first_empty_decade_mm
            and grid_in_use < evidence.first_empty_decade_mm),
        "why": (
            "a grid smaller than the noise floor leaves coincident nodes "
            "unmerged, which shows up as spurious components in the wall "
            "solid. A grid larger than the noise floor is safe only while it "
            "stays below the nearest thing anybody drew, and the measured "
            "empty band is what establishes that"),
    }


def _k(d: float) -> str:
    return f"<={d:g}"


def gaps_this_cannot_close(evidence, gaps_mm) -> dict:
    """State plainly which reported gaps snapping could never have closed.

    This is the question a reader actually has when a leak map reports a
    50 mm hole in a wall solid: was that an artefact of the tolerance? The
    answer is arithmetic, and giving it stops the next person tuning the
    grid upwards to chase it.
    """
    grid = evidence.recommended_grid_mm
    out = []
    for g in gaps_mm:
        out.append({
            "gap_mm": round(float(g), 3),
            "multiples_of_the_grid": (None if not grid
                                      else round(float(g) / grid, 1)),
            "closable_by_snapping": bool(grid and float(g) <= grid)})
    return {
        "recommended_grid_mm": grid,
        "gaps": out,
        "none_are_snap_artefacts": all(not g["closable_by_snapping"]
                                       for g in out),
        "why_this_matters": (
            "a gap orders of magnitude larger than the noise floor is not a "
            "numerical artefact and will not yield to a bigger tolerance. "
            "Raising the grid to reach it would close every genuine gap of "
            "that size too, which is how a wall appears between two rooms "
            "that were drawn open"),
    }
