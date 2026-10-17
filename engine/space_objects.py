"""E86 — three objects, three questions, three statuses that never merge.

The deterministic vector path tried to answer one question: WHAT IS THE ROOM.
It could not, because that question is really three, and they have different
evidence, different failure modes and different release rules:

    TOPOLOGY_REGION           is there one connected physical space here?
    MEASURED_SPACE_CANDIDATE  can its boundary be measured from source
                              geometry, interval by interval?
    RELEASED_PHYSICAL_SPACE   may a quantity be built on it?

Collapsing them is how a raster blob became an area. A region found by
segmentation is a topology claim carrying NO released millimetre; a candidate
whose boundary is matched to vector faces is a measurement; only the third is
a quantity. Each object states what it is NOT, because every previous round's
failures were a status being read as the next one up.

The objects are deliberately separate TYPES, not three values of one status
field, so that passing a topology region where a released space is required
is a type error rather than an optimistic read.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# ---------------------------------------------------------------- sources

# Where a boundary interval's MEASUREMENT comes from. The order is the
# production priority for a vector PDF such as AR-00.
SRC_VECTOR_WALL_FACE = "VECTOR_WALL_FACE"
SRC_VECTOR_OPENING_JAMB = "VECTOR_OPENING_JAMB"
SRC_VECTOR_EXTERNAL_BOUNDARY = "VECTOR_EXTERNAL_BOUNDARY"
SRC_RECOVERED_FRAGMENT = "RECOVERED_FRAGMENTED_VECTOR_GEOMETRY"
SRC_DOCUMENT_DIMENSION = "DOCUMENT_SUPPORTED_DIMENSION"
SRC_DIAGNOSTIC_VECTOR = "DIAGNOSTIC_VECTOR_GEOMETRY"
SRC_RASTER_ONLY = "RASTER_ONLY"
SRC_UNRESOLVED = "UNRESOLVED"

BOUNDARY_SOURCES = (
    SRC_VECTOR_WALL_FACE, SRC_VECTOR_OPENING_JAMB,
    SRC_VECTOR_EXTERNAL_BOUNDARY, SRC_RECOVERED_FRAGMENT,
    SRC_DOCUMENT_DIMENSION, SRC_DIAGNOSTIC_VECTOR, SRC_RASTER_ONLY,
    SRC_UNRESOLVED)

# Search priority: lower is preferred. Not a confidence and not a score —
# a stated order of authority, so a boundary's source can be argued with.
SOURCE_PRIORITY = {s: i for i, s in enumerate(BOUNDARY_SOURCES)}

# Which sources may carry a released millimetre. RASTER_ONLY is absent by
# construction: a pixel may localise a wall and may never measure one.
PRODUCTION_ELIGIBLE_SOURCES = frozenset({
    SRC_VECTOR_WALL_FACE, SRC_VECTOR_OPENING_JAMB,
    SRC_VECTOR_EXTERNAL_BOUNDARY, SRC_RECOVERED_FRAGMENT})

# Sources that measure something real but are not licensed for release.
DIAGNOSTIC_SOURCES = frozenset({SRC_DOCUMENT_DIMENSION,
                                SRC_DIAGNOSTIC_VECTOR})

UNMEASURED_SOURCES = frozenset({SRC_RASTER_ONLY, SRC_UNRESOLVED})

# ---------------------------------------------------------------- statuses

# A. topology
TOPOLOGY_PROPOSED = "TOPOLOGY_REGION_PROPOSED"
TOPOLOGY_RESOLVED = "TOPOLOGY_RESOLVED"
TOPOLOGY_REJECTED = "TOPOLOGY_REGION_REJECTED"

# B. measurement
MEASUREMENT_NONE = "MEASUREMENT_NOT_ATTEMPTED"
MEASUREMENT_PARTIAL = "MEASUREMENT_PARTIAL"
MEASUREMENT_COMPLETE_DIAGNOSTIC = "MEASUREMENT_COMPLETE_DIAGNOSTIC"
MEASUREMENT_COMPLETE_PRODUCTION = "MEASUREMENT_COMPLETE_PRODUCTION_ELIGIBLE"

# C. release
RELEASE_BLOCKED = "RELEASE_BLOCKED"
RELEASE_ELIGIBLE = "RELEASE_ELIGIBLE"

# What each object refuses to be read as.
NOT_A = {
    "TOPOLOGY_REGION": (
        "a measured space. It carries NO released millimetre: its extent is "
        "a pixel mask, its area is approximate, and neither may reach a "
        "quantity"),
    "MEASURED_SPACE_CANDIDATE": (
        "a released space. Its polygon is built from source geometry, and "
        "whether every interval of that boundary is production-eligible is "
        "a separate question answered by the release object"),
    "RELEASED_PHYSICAL_SPACE": (
        "an identity claim. It says a polygon may carry a quantity; which "
        "room it is remains identity evidence's problem"),
}


# ------------------------------------------------- A. the topology region

@dataclass(frozen=True)
class TopologyRegion:
    """The drawing's evidence suggests one connected physical space here.

    May come from raster segmentation, vision, vector barriers or semantic
    evidence. Carries no released geometry — `approximate_area_m2` is named
    approximate because a pixel count is not a measurement, and the name is
    the safety device.
    """

    region_id: str
    source: str                          # which instrument proposed it
    approximate_area_m2: float
    centroid_mm: tuple
    bbox_mm: tuple
    pixel_count: int = 0
    adjacent_region_ids: tuple[str, ...] = ()
    candidate_opening_ids: tuple[str, ...] = ()
    candidate_barrier_ids: tuple[str, ...] = ()
    confidence: float | None = None
    status: str = TOPOLOGY_PROPOSED
    provenance: dict = field(default_factory=dict)
    why: str = ""

    @property
    def is_resolved(self) -> bool:
        return self.status == TOPOLOGY_RESOLVED

    def record(self) -> dict:
        return {
            "region_id": self.region_id,
            "source": self.source,
            "APPROXIMATE_area_m2": round(self.approximate_area_m2, 3),
            "centroid_mm": [round(v, 1) for v in self.centroid_mm],
            "bbox_mm": [round(v, 1) for v in self.bbox_mm],
            "pixel_count": self.pixel_count,
            "adjacent_region_ids": list(self.adjacent_region_ids),
            "candidate_opening_ids": list(self.candidate_opening_ids),
            "candidate_barrier_ids": list(self.candidate_barrier_ids),
            "confidence": self.confidence,
            "topology_status": self.status,
            "carries_no_released_geometry": True,
            "what_this_is_not": NOT_A["TOPOLOGY_REGION"],
            "provenance": dict(self.provenance),
            "why": self.why,
        }


# --------------------------------------- B. the measured space candidate

@dataclass(frozen=True)
class BoundaryInterval:
    """One run of a region's boundary, and what measured it.

    The decision record is the point (§10): a QS quantity must be traceable
    to the exact drawn geometry, so every interval names the candidates it
    saw, the one it chose, why, and what it rejected.
    """

    interval_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    source_type: str = SRC_UNRESOLVED
    chosen_object_id: str = ""
    candidate_object_ids: tuple[str, ...] = ()
    rejected: tuple = ()                 # ((object_id, reason), ...)
    distance_mm: float | None = None
    orientation_difference_deg: float | None = None
    support_length_mm: float = 0.0
    validation_class: str = ""
    reason_chosen: str = ""

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def is_production_eligible(self) -> bool:
        return self.source_type in PRODUCTION_ELIGIBLE_SOURCES

    @property
    def is_measured(self) -> bool:
        return self.source_type not in UNMEASURED_SOURCES

    def record(self) -> dict:
        return {
            "region_boundary_interval_id": self.interval_id,
            "axis": self.axis,
            "fixed_mm": round(self.fixed_mm, 2),
            "interval_mm": [round(self.start_mm, 2), round(self.end_mm, 2)],
            "length_mm": round(self.length_mm, 1),
            "source_type": self.source_type,
            "chosen_vector_object_id": self.chosen_object_id,
            "candidate_vector_object_ids": list(self.candidate_object_ids),
            "alternatives_rejected": [
                {"object_id": o, "reason": r} for o, r in self.rejected],
            "distance_mm": (None if self.distance_mm is None
                            else round(self.distance_mm, 3)),
            "orientation_difference_deg": self.orientation_difference_deg,
            "support_length_mm": round(self.support_length_mm, 1),
            "validation_class": self.validation_class,
            "production_eligible": self.is_production_eligible,
            "reason_chosen": self.reason_chosen,
        }


@dataclass(frozen=True)
class MeasuredSpaceCandidate:
    """A topology region whose boundary has been matched to source geometry.

    Partial measurement is a first-class outcome (§12): one unmeasurable
    boundary does not throw away useful topology. It does, however, stop
    the area and perimeter from being released.
    """

    candidate_id: str
    region_id: str
    intervals: tuple = ()
    polygon_wkt: str = ""
    area_m2: float | None = None
    perimeter_m: float | None = None
    measurement_basis: str = ""
    geometry_hash: str = ""
    polygon_closed: bool = False
    why: str = ""

    # --- measured extent -------------------------------------------------
    @property
    def boundary_length_mm(self) -> float:
        return sum(i.length_mm for i in self.intervals)

    @property
    def measured_length_mm(self) -> float:
        return sum(i.length_mm for i in self.intervals if i.is_measured)

    @property
    def production_length_mm(self) -> float:
        return sum(i.length_mm for i in self.intervals
                   if i.is_production_eligible)

    @property
    def unresolved_intervals(self) -> tuple:
        return tuple(i for i in self.intervals if not i.is_measured)

    def _pct(self, part: float) -> float:
        total = self.boundary_length_mm
        return 0.0 if total <= 0 else round(100.0 * part / total, 2)

    @property
    def measured_pct(self) -> float:
        return self._pct(self.measured_length_mm)

    @property
    def production_pct(self) -> float:
        return self._pct(self.production_length_mm)

    @property
    def unresolved_pct(self) -> float:
        return round(100.0 - self.measured_pct, 2)

    # --- status ----------------------------------------------------------
    @property
    def measurement_status(self) -> str:
        if not self.intervals:
            return MEASUREMENT_NONE
        if self.unresolved_intervals or not self.polygon_closed:
            return MEASUREMENT_PARTIAL
        if all(i.is_production_eligible for i in self.intervals):
            return MEASUREMENT_COMPLETE_PRODUCTION
        return MEASUREMENT_COMPLETE_DIAGNOSTIC

    @property
    def is_complete(self) -> bool:
        return self.measurement_status in (
            MEASUREMENT_COMPLETE_DIAGNOSTIC,
            MEASUREMENT_COMPLETE_PRODUCTION)

    def record(self) -> dict:
        by_source = Counter(i.source_type for i in self.intervals)
        return {
            "candidate_id": self.candidate_id,
            "region_id": self.region_id,
            "measurement_status": self.measurement_status,
            "boundary_source_coverage": {
                "measured_pct": self.measured_pct,
                "production_eligible_pct": self.production_pct,
                "unresolved_pct": self.unresolved_pct,
                "unresolved_intervals": len(self.unresolved_intervals),
                "boundary_length_m": round(
                    self.boundary_length_mm / 1000, 3),
            },
            "by_boundary_source": dict(by_source),
            "length_by_boundary_source_m": {
                s: round(sum(i.length_mm for i in self.intervals
                             if i.source_type == s) / 1000, 3)
                for s in sorted(by_source)},
            "area_m2": (None if self.area_m2 is None
                        else round(self.area_m2, 3)),
            "perimeter_m": (None if self.perimeter_m is None
                            else round(self.perimeter_m, 3)),
            "measurement_basis": self.measurement_basis,
            "geometry_hash": self.geometry_hash,
            "polygon_closed": self.polygon_closed,
            "polygon_built_from": (
                "the chosen vector sources only. The raster polygon was "
                "never scaled, warped, offset or smoothed into place: "
                "raster identifies topology, vector reconstructs "
                "measurement"),
            "intervals": [i.record() for i in self.intervals],
            "what_this_is_not": NOT_A["MEASURED_SPACE_CANDIDATE"],
            "why": self.why,
        }


# ----------------------------------------- C. the released physical space

# Every requirement, named, so a refusal can say which one failed.
REQ_POLYGON = "A_VALID_MEASURED_POLYGON"
REQ_IDENTITY = "A_VALID_SPACE_IDENTITY"
REQ_SOURCES = "EVERY_BOUNDARY_INTERVAL_PRODUCTION_ELIGIBLE"
REQ_NO_UNRESOLVED = "NO_UNRESOLVED_BOUNDARY_INTERVAL"
REQ_PORTALS = "APPROVED_PORTAL_EVIDENCE_WHERE_RELEVANT"
REQ_BASIS = "A_DECLARED_MEASUREMENT_BASIS"

REQUIREMENTS = (REQ_POLYGON, REQ_IDENTITY, REQ_SOURCES, REQ_NO_UNRESOLVED,
                REQ_PORTALS, REQ_BASIS)


@dataclass(frozen=True)
class ReleasedPhysicalSpace:
    """May a quantity be built on this polygon. Nothing else."""

    space_id: str
    candidate_id: str
    requirements_met: tuple[str, ...] = ()
    requirements_failed: tuple[str, ...] = ()
    area_m2: float | None = None
    measurement_basis: str = ""
    geometry_hash: str = ""
    why: str = ""

    @property
    def status(self) -> str:
        return (RELEASE_ELIGIBLE if not self.requirements_failed
                else RELEASE_BLOCKED)

    def record(self) -> dict:
        return {
            "space_id": self.space_id,
            "candidate_id": self.candidate_id,
            "release_status": self.status,
            "requirements": list(REQUIREMENTS),
            "requirements_met": list(self.requirements_met),
            "requirements_failed": list(self.requirements_failed),
            "area_m2": (None if self.area_m2 is None
                        else round(self.area_m2, 3)),
            "measurement_basis": self.measurement_basis,
            "geometry_hash": self.geometry_hash,
            "what_this_is_not": NOT_A["RELEASED_PHYSICAL_SPACE"],
            "why": self.why,
        }


def assess_release(candidate: MeasuredSpaceCandidate, *, space_id: str = "",
                   identity_valid: bool = False,
                   portal_evidence_approved: bool = True,
                   portal_note: str = "") -> ReleasedPhysicalSpace:
    """Apply §2C's requirements. Every failure is named, not summarised."""
    met, failed = [], []

    def check(ok: bool, req: str) -> None:
        (met if ok else failed).append(req)

    check(candidate.polygon_closed and candidate.area_m2 is not None,
          REQ_POLYGON)
    check(bool(identity_valid), REQ_IDENTITY)
    check(bool(candidate.intervals)
          and all(i.is_production_eligible for i in candidate.intervals),
          REQ_SOURCES)
    check(not candidate.unresolved_intervals, REQ_NO_UNRESOLVED)
    check(bool(portal_evidence_approved), REQ_PORTALS)
    check(bool(candidate.measurement_basis), REQ_BASIS)

    if failed:
        why = ("release refused: " + ", ".join(failed)
               + (f". {portal_note}" if portal_note
                  and REQ_PORTALS in failed else ""))
    else:
        why = ("every boundary interval is production-eligible, the polygon "
               "closes, the identity is valid and the basis is declared")

    return ReleasedPhysicalSpace(
        space_id=space_id or candidate.region_id,
        candidate_id=candidate.candidate_id,
        requirements_met=tuple(met), requirements_failed=tuple(failed),
        area_m2=candidate.area_m2,
        measurement_basis=candidate.measurement_basis,
        geometry_hash=candidate.geometry_hash, why=why)


def summary(regions=(), candidates=(), releases=()) -> dict:
    """The three counts, side by side and never added together."""
    regions, candidates = list(regions), list(candidates)
    releases = list(releases)
    by_meas = Counter(c.measurement_status for c in candidates)
    return {
        "A_TOPOLOGY_REGIONS": {
            "regions": len(regions),
            "resolved": sum(1 for r in regions if r.is_resolved),
            "by_source": dict(Counter(r.source for r in regions)),
            "answers": "is there one connected physical space here",
            "carries": "no released millimetre",
        },
        "B_MEASURED_SPACE_CANDIDATES": {
            "candidates": len(candidates),
            "by_measurement_status": dict(by_meas),
            "complete": sum(1 for c in candidates if c.is_complete),
            "partial": by_meas.get(MEASUREMENT_PARTIAL, 0),
            "answers": ("can this region's boundary be measured from "
                        "source geometry, interval by interval"),
        },
        "C_RELEASED_PHYSICAL_SPACES": {
            "assessed": len(releases),
            "release_eligible": sum(1 for r in releases
                                    if r.status == RELEASE_ELIGIBLE),
            "blocked": sum(1 for r in releases
                           if r.status == RELEASE_BLOCKED),
            "by_failed_requirement": dict(Counter(
                req for r in releases for req in r.requirements_failed)),
            "answers": "may a quantity be built on this polygon",
        },
        "why_three_objects": (
            "they have different evidence, different failure modes and "
            "different release rules. Collapsing them is how a raster blob "
            "became an area: a region is a topology claim, a candidate is a "
            "measurement, and only the third is a quantity"),
        "these_counts_are_not_comparable": (
            "a region is not a partly-released space. Reading the three "
            "numbers as one funnel of the same object is the error the "
            "separation exists to prevent"),
    }
