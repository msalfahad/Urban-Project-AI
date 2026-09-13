"""E25.2 — run the per-space wall model against a real drawing, and persist it.

E25 has had a per-space wall model for months: `SpaceWalls` holds segments and
openings, `WallSegment` records which space is on the other side, and
`gross_wall_perimeter_m` has been implemented and tested throughout. It had never
run on an actual drawing, because `VectorPdfSource.regions()` computed the label
map and ink mask inside one method and discarded them. Nothing else could reach
them, so every caller was a unit test on a synthetic array.

This module is the missing pipe, plus the three things a real run needs that a
unit test does not: it runs every space rather than one, it records where each
number came from, and it refuses to present an unclosed boundary as a
measurement.

On reconciliation. The prior E25 aggregate for project 23010 is 95.42 m. That
figure is NOT an authority: the notes stored with it record that it was traced
without door-gap bridging and that it carries two named defects — WSH-01 counted
4.193 m for what may be the shaft beside the wash room, and BED-04's printed
1600x3000 bathroom contributes roughly 9.2 m that was never measured at all.
Correcting both would overshoot it. So comparing against it is a CHANGE
DETECTOR: it says what moved and invites an explanation. A large difference may
mean the new model is more right, and this module never treats the old number as
a target to hit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from engine.walls import SpaceWalls, WallError, space_walls

# Why a space's wall model is or is not usable as a quantity input.
VALIDATED = "VALIDATED"
BOUNDED_ERROR = "BOUNDED_ERROR"
UNRESOLVED = "UNRESOLVED"

# How a difference against a prior aggregate is explained. Never "close enough".
SAME = "SAME"
NEW_BOUNDARY_RESOLVED = "NEW_BOUNDARY_RESOLVED"
KNOWN_DEFECT = "KNOWN_DEFECT"
UNEXPLAINED = "UNEXPLAINED"


class WallModelError(RuntimeError):
    """The run could not produce a wall model for a space it was asked about."""


@dataclass(frozen=True)
class SpaceWallRecord:
    """One space's persisted wall model, with everything needed to trace it."""

    space_id: str
    region_id: int
    walls: SpaceWalls

    drawing_id: str
    revision: str
    source_path: str
    source_sha256: str
    px_mm: Decimal
    measurement_basis: str
    geometry_source: str

    status: str
    status_reason: str = ""

    # --- the numbers a trade asks for ------------------------------------
    @property
    def gross_room_perimeter_m(self) -> Decimal:
        """The closed outline, open transitions included."""
        return self.walls.gross_room_perimeter_m

    @property
    def gross_wall_perimeter_m(self) -> Decimal:
        """Wall plus doorway closures, undeducted — a MEASURER row's basis."""
        return self.walls.gross_wall_perimeter_m

    @property
    def physical_wall_m(self) -> Decimal:
        """Masonry only. What blockwork is allowed to see."""
        return self.walls.physical_wall_m

    @property
    def open_length_m(self) -> Decimal:
        return self.walls.open_length_m

    @property
    def opening_count(self) -> int:
        return len(self.walls.openings)

    @property
    def segment_count(self) -> int:
        return len(self.walls.segments)

    @property
    def releasable(self) -> bool:
        """Only a closed, validated boundary may feed a quantity unreviewed."""
        return self.status == VALIDATED

    def row(self) -> dict:
        """One line of the per-space report."""
        return {
            "space_id": self.space_id,
            "region_id": self.region_id,
            "gross_room_perimeter_m": f"{self.gross_room_perimeter_m:.2f}",
            "gross_wall_perimeter_m": f"{self.gross_wall_perimeter_m:.2f}",
            "physical_wall_m": f"{self.physical_wall_m:.2f}",
            "open_length_m": f"{self.open_length_m:.2f}",
            "openings": self.opening_count,
            "segments": self.segment_count,
            "status": self.status,
            "status_reason": self.status_reason,
            "geometry_source": self.geometry_source,
            "measurement_basis": self.measurement_basis,
            "drawing_id": self.drawing_id,
            "revision": self.revision,
        }

    def segments_json(self) -> list[dict]:
        """Every segment, for persistence. Coordinates in mm as well as pixels:
        pixels are a rendering artefact that changes with dpi."""
        return [{
            "wall_segment_id": s.wall_id,
            "space_id": s.space_id,
            "side": s.side,
            "boundary_type": s.segment_type,
            "classification": s.classification,
            "start_px": list(s.start_px), "end_px": list(s.end_px),
            "start_mm": [int(Decimal(s.start_px[0]) * self.px_mm),
                         int(Decimal(s.start_px[1]) * self.px_mm)],
            "end_mm": [int(Decimal(s.end_px[0]) * self.px_mm),
                       int(Decimal(s.end_px[1]) * self.px_mm)],
            "length_mm": s.length_mm,
            "length_m": f"{s.length_m:.3f}",
            "adjacent_space_id": s.adjoining_space,
            "opening_ids": list(s.opening_ids),
            "wall_thickness_mm": None,
            "wall_thickness_source": "NOT_MEASURED",
            "wall_thickness_validation": UNRESOLVED,
            "measurement_basis": self.measurement_basis,
            "source_file": self.source_path,
            "source_sha256": self.source_sha256,
            "drawing_id": s.source_drawing or self.drawing_id,
            "revision": s.source_revision or self.revision,
            "validation_status": s.validation,
            "provenance": (f"E25 boundary trace of region {self.region_id} on "
                           f"{self.drawing_id} rev {self.revision}"),
            "note": s.note,
        } for s in self.walls.segments]

    def openings_json(self) -> list[dict]:
        return [{
            "opening_id": o.id,
            "space_id": self.space_id,
            "width_mm": o.width_mm,
            "axis": o.axis,
            "at_px": list(o.at_px),
            "provenance": o.provenance,
            "height_mm": None,          # E34's job, not a guess here
            "type": "UNCLASSIFIED",
        } for o in self.walls.openings]


@dataclass
class WallModelResult:
    records: list[SpaceWallRecord] = field(default_factory=list)
    failures: dict[str, str] = field(default_factory=dict)
    segmentation_provenance: dict = field(default_factory=dict)

    def by_id(self) -> dict[str, SpaceWallRecord]:
        return {r.space_id: r for r in self.records}

    @property
    def validated(self) -> list[SpaceWallRecord]:
        return [r for r in self.records if r.status == VALIDATED]

    @property
    def unresolved(self) -> list[SpaceWallRecord]:
        return [r for r in self.records if r.status != VALIDATED]

    def total(self, attr: str, *, validated_only: bool = False) -> Decimal:
        rows = self.validated if validated_only else self.records
        return sum((getattr(r, attr) for r in rows), Decimal(0))


def run_wall_model(seg, space_regions: dict[str, int], *,
                   min_run_mm: int = 100, max_opening_mm: int = 0,
                   measurement_basis: str = "CLEAR_INTERNAL_FINISH_FACE",
                   geometry_source: str = "VECTOR_PDF_RASTER_REGION",
                   ) -> WallModelResult:
    """Trace every mapped space's boundary from one real segmentation.

    `max_opening_mm` defaults to 0 — no door-gap bridging. On AR-00 bridging
    either swallows small rooms, because printed fixtures act as false jambs on
    raw ink, or fails to seal at all. That is a property of this sheet and the
    caller may override it, but the default is the conservative one: an unbridged
    boundary that stays open is reported as open, rather than a bridged one that
    silently ate a bathroom.
    """
    import numpy as np

    id_to_space = {rid: sid for sid, rid in space_regions.items()}
    bridges = np.zeros_like(seg.wall_mask)
    result = WallModelResult(segmentation_provenance=seg.provenance())

    for space_id, region_id in sorted(space_regions.items()):
        try:
            sw = space_walls(
                space_id, seg.labels, int(region_id), seg.wall_mask, bridges,
                seg.px_mm, outside_id=seg.outside_id,
                drawing=seg.drawing_id, revision=seg.revision,
                id_to_space=id_to_space, min_run_mm=min_run_mm,
                max_opening_mm=max_opening_mm)
        except WallError as exc:
            result.failures[space_id] = str(exc)
            continue

        if sw.open_length_m > 0:
            status, reason = UNRESOLVED, (
                f"boundary does not close: {sw.open_length_m:.2f} m of open "
                "transition. A wall quantity from an open outline would be "
                "measuring a room that has no edge there.")
        elif not sw.segments:
            status, reason = UNRESOLVED, "no boundary segments were traced"
        else:
            status, reason = VALIDATED, ""

        result.records.append(SpaceWallRecord(
            space_id=space_id, region_id=int(region_id), walls=sw,
            drawing_id=seg.drawing_id, revision=seg.revision,
            source_path=seg.source_path, source_sha256=seg.source_sha256,
            px_mm=seg.px_mm, measurement_basis=measurement_basis,
            geometry_source=geometry_source, status=status, status_reason=reason))
    return result


@dataclass
class ReconciliationLine:
    label: str
    new_m: Decimal
    prior_m: Decimal | None
    classification: str
    note: str = ""

    @property
    def delta_m(self) -> Decimal | None:
        return None if self.prior_m is None else self.new_m - self.prior_m


def reconcile_against_prior(result: WallModelResult, *, prior_total_m: Decimal,
                            prior_basis: str, known_defects: dict[str, str],
                            ) -> list[ReconciliationLine]:
    """Compare the new per-space model against a PRIOR ENGINE OUTPUT.

    Not against the manual site figure, and not as a pass/fail. Both numbers are
    wall lengths in metres, which is the only reason they can be subtracted at
    all — and even then only if they share a measurement basis, a scope and a
    boundary definition. Where the prior figure is known to be wrong, the
    difference is classified KNOWN_DEFECT rather than counted against the new
    model.
    """
    lines: list[ReconciliationLine] = []
    new_total = result.total("gross_wall_perimeter_m")
    lines.append(ReconciliationLine(
        f"all mapped spaces, gross wall perimeter ({prior_basis})",
        new_total, prior_total_m,
        SAME if abs(new_total - prior_total_m) < Decimal("0.5") else UNEXPLAINED,
        "the prior aggregate is a previous engine output with recorded defects, "
        "not an authority and not a target"))
    lines.append(ReconciliationLine(
        "validated spaces only", result.total("gross_wall_perimeter_m",
                                              validated_only=True),
        None, NEW_BOUNDARY_RESOLVED,
        f"{len(result.validated)} of {len(result.records)} spaces close"))
    lines.append(ReconciliationLine(
        "physical wall only (masonry, doorway closures excluded)",
        result.total("physical_wall_m"), None, NEW_BOUNDARY_RESOLVED,
        "what blockwork is allowed to see"))
    for space_id, why in sorted(known_defects.items()):
        rec = result.by_id().get(space_id)
        if rec is not None:
            lines.append(ReconciliationLine(
                f"{space_id} (recorded defect)", rec.gross_wall_perimeter_m,
                None, KNOWN_DEFECT, why))
    return lines
