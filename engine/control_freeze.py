"""E62 — accept the geometry, hash it, THEN open the benchmark.

A control measured after the reference was opened is not a control, and a
control chosen because it measured well is not one either. The selector in
`engine.controls` already refuses to see a measurement. This module closes the
other half: the polygon and its provenance are hashed and FROZEN before any
reference is read, so a later comparison cannot have influenced it.

    accept  ->  freeze (hash)  ->  compare  ->  report

The acceptance gate is about PROVENANCE as much as geometry. A polygon with a
bounding-box edge, or one whose boundary came from a raster outline, is refused
however well it measures — because the number would be right for the wrong
reason, and the next drawing would expose it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

# Why a candidate was refused as a control's physical space.
NOT_VALID = "GEOMETRY_NOT_VALID"
ZERO_AREA = "ZERO_OR_NEGATIVE_AREA"
OVERLAPS_ANOTHER = "OVERLAPS_AN_ACCEPTED_PHYSICAL_SPACE"
OUTSIDE_ENVELOPE = "NOT_INSIDE_THE_BUILDING_ENVELOPE"
UNSUPPORTED_BOUNDARY = "BOUNDARY_NOT_SUPPORTED_BY_WALL_OR_PORTAL_GEOMETRY"
BBOX_EDGE = "A_BOUNDING_BOX_DERIVED_EDGE_IS_PRESENT"
RASTER_EDGE = "A_RASTER_DERIVED_MILLIMETRE_EDGE_IS_PRESENT"
WRONG_BASIS = "MEASUREMENT_BASIS_IS_NOT_CLEAR_INTERNAL_FINISH_FACE"
MULTI_LABEL = "MORE_THAN_ONE_LABELLED_ROOM_INSIDE"
NO_CANDIDATE = "NO_SPACE_GEOMETRY_ENCLOSES_THIS_CONTROL"

ACCEPTED = "GEOMETRY_ACCEPTED_AND_FROZEN"
REFUSED = "GEOMETRY_REFUSED"

CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"

# A closed shape's perimeter can never be less than that of the circle with
# the same area, and a real room is not far above the square's. A raster
# region's boundary is a PIXEL STAIRCASE around a possibly ragged mask, and
# its length can run several times the room's true perimeter — so it is not a
# comparable perimeter measure, and saying "80% error" against it would be
# reporting the reference's raggedness as the engine's mistake.
MAX_PLAUSIBLE_SHAPE_FACTOR = 2.0


class FreezeError(RuntimeError):
    """A comparison was attempted against geometry that was never frozen."""


@dataclass(frozen=True)
class FrozenControl:
    """One control's accepted polygon, hashed before any reference was read."""

    space_id: str
    room_type: str
    space_geometry_id: str
    status: str
    polygon_mm: tuple = ()
    area_m2: float | None = None
    perimeter_m: float | None = None
    measurement_basis: str = CLEAR_INTERNAL_FINISH_FACE
    geometry_hash: str = ""
    provenance: dict = field(default_factory=dict)
    refusals: tuple[str, ...] = ()
    why: str = ""

    @property
    def accepted(self) -> bool:
        return self.status == ACCEPTED

    def record(self) -> dict:
        return {"space_id": self.space_id, "room_type": self.room_type,
                "space_geometry_id": self.space_geometry_id,
                "status": self.status,
                "clear_internal_area_m2": (None if self.area_m2 is None
                                           else round(self.area_m2, 3)),
                "clear_internal_perimeter_m": (
                    None if self.perimeter_m is None
                    else round(self.perimeter_m, 3)),
                "measurement_basis": self.measurement_basis,
                "vertices": len(self.polygon_mm),
                "geometry_hash": self.geometry_hash,
                "provenance": dict(self.provenance),
                "refusals": list(self.refusals),
                "frozen_before_any_reference_was_read": bool(
                    self.geometry_hash),
                "why": self.why}


def geometry_hash(space_id: str, polygon_mm, provenance: dict) -> str:
    """A stable hash of the polygon AND how it was made.

    Provenance is inside the hash on purpose: the same coordinates reached by
    a different route are a different result, and a later claim that the
    polygon was built the accepted way has to be checkable.
    """
    blob = json.dumps({
        "space_id": space_id,
        "polygon_mm": [[round(x, 4), round(y, 4)] for x, y in polygon_mm],
        "provenance": provenance,
    }, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:24]


def accept(control, candidate, *, envelope, labels_inside, others=(),
           run_id: str = "") -> FrozenControl:
    """Apply §14's gate, then hash. No reference is read anywhere in here."""
    common = dict(space_id=control.space_id, room_type=control.room_type,
                  space_geometry_id=(candidate.space_geometry_id
                                     if candidate is not None else ""))
    if candidate is None:
        return FrozenControl(
            status=REFUSED, refusals=(NO_CANDIDATE,),
            why=("no space geometry component encloses this control's "
                 "labelled position. There is nothing to accept, and the "
                 "raster outline may not stand in for one"),
            **common)

    refusals = []
    g = candidate.geometry
    if not g.is_valid:
        refusals.append(NOT_VALID)
    if g.area <= 0:
        refusals.append(ZERO_AREA)
    if candidate.measurement_basis != CLEAR_INTERNAL_FINISH_FACE:
        refusals.append(WRONG_BASIS)
    if not candidate.bounding_band_ids:
        refusals.append(UNSUPPORTED_BOUNDARY)
    prov = dict(candidate.provenance)
    if prov.get("bbox_derived_edges"):
        refusals.append(BBOX_EDGE)
    if prov.get("raster_derived_edges"):
        refusals.append(RASTER_EDGE)
    if len(labels_inside) > 1:
        refusals.append(MULTI_LABEL)
    if envelope is not None and envelope.geometry is not None:
        if not envelope.geometry.buffer(1.0).contains(g):
            refusals.append(OUTSIDE_ENVELOPE)
    for other in others:
        if other.space_geometry_id == candidate.space_geometry_id:
            continue
        if g.intersection(other.geometry).area > 1.0:
            refusals.append(OVERLAPS_ANOTHER)
            break

    if refusals:
        return FrozenControl(
            status=REFUSED, refusals=tuple(sorted(set(refusals))),
            area_m2=candidate.area_m2, perimeter_m=candidate.perimeter_m,
            why=("the gate refused this candidate. A number that is right for "
                 "the wrong reason is worse than no number: the next drawing "
                 "would expose it"),
            **common)

    poly = candidate.polygon_mm
    prov = {**prov, "run_id": run_id,
            "labels_inside": sorted(labels_inside),
            "bounding_band_ids": list(candidate.bounding_band_ids),
            "bounding_portal_ids": list(candidate.bounding_portal_ids),
            "geometry_role": candidate.geometry_role}
    return FrozenControl(
        status=ACCEPTED, polygon_mm=poly, area_m2=candidate.area_m2,
        perimeter_m=candidate.perimeter_m,
        geometry_hash=geometry_hash(control.space_id, poly, prov),
        provenance=prov,
        why=("valid, non-overlapping, inside the envelope, bounded by drawn "
             "wall faces and supported portal geometry, on the clear-internal "
             "basis, with no bbox and no raster millimetre edge"),
        **common)


def compare_after_freeze(frozen: FrozenControl, *, reference_area_m2=None,
                         reference_perimeter_m=None, reference_basis: str = "",
                         reference_name: str = "", overlap: dict | None = None
                         ) -> dict:
    """Open the reference — only now, and only against a hashed polygon."""
    if not frozen.accepted:
        return {"space_id": frozen.space_id, "comparable": False,
                "why": "this control's geometry was refused, so there is "
                       "nothing to compare"}
    if not frozen.geometry_hash:
        raise FreezeError(
            f"{frozen.space_id} was never frozen, so a comparison cannot "
            "prove the reference did not influence the geometry")
    if reference_area_m2 is None:
        return {"space_id": frozen.space_id, "comparable": False,
                "geometry_hash": frozen.geometry_hash,
                "why": f"no {reference_name or 'reference'} is available on "
                       "the clear-internal basis for this room"}
    if reference_basis and reference_basis != frozen.measurement_basis:
        return {"space_id": frozen.space_id, "comparable": False,
                "geometry_hash": frozen.geometry_hash,
                "why": (f"the reference is on {reference_basis} and the "
                        f"polygon is on {frozen.measurement_basis}. NEVER "
                        "COMPARE UNLIKE BASES")}
    d_area = frozen.area_m2 - reference_area_m2
    out = {
        "space_id": frozen.space_id, "comparable": True,
        "geometry_hash": frozen.geometry_hash,
        "frozen_before_comparison": True,
        "reference": reference_name,
        "reference_basis": reference_basis or frozen.measurement_basis,
        "vector_clear_area_m2": round(frozen.area_m2, 3),
        "reference_clear_area_m2": round(reference_area_m2, 3),
        "vector_clear_perimeter_m": (None if frozen.perimeter_m is None
                                     else round(frozen.perimeter_m, 3)),
        "reference_clear_perimeter_m": (None if reference_perimeter_m is None
                                        else round(reference_perimeter_m, 3)),
        "abs_area_diff_m2": round(abs(d_area), 3),
        "area_error_pct": (round(abs(d_area) / reference_area_m2 * 100, 2)
                           if reference_area_m2 else None),
        "acceptance_threshold": None,
        "note": ("no tuning is permitted after this point. A threshold is not "
                 "defined from one room on one project"),
    }
    if reference_perimeter_m:
        import math
        # Perimeter of the square with the reference's area — the practical
        # floor for a rectilinear room.
        square = 4 * math.sqrt(reference_area_m2) if reference_area_m2 else 0.0
        factor = (reference_perimeter_m / square) if square else 0.0
        if factor > MAX_PLAUSIBLE_SHAPE_FACTOR:
            out["perimeter_comparable"] = False
            out["reference_shape_factor"] = round(factor, 2)
            out["perimeter_why"] = (
                f"the reference perimeter is {factor:.1f}x that of the square "
                f"with its own area ({square:.1f} m). That is a pixel "
                "staircase around a ragged mask, not a room outline, so "
                "comparing perimeters against it would report the "
                "REFERENCE'S raggedness as this engine's error")
        else:
            out["perimeter_comparable"] = True
            out["reference_shape_factor"] = round(factor, 2)
            out["perimeter_error_pct"] = round(
                abs((frozen.perimeter_m or 0) - reference_perimeter_m)
                / reference_perimeter_m * 100, 2)
    if overlap:
        out.update({"intersection_m2": overlap.get("intersection_m2"),
                    "union_m2": overlap.get("union_m2"),
                    "iou": overlap.get("iou"),
                    "max_boundary_deviation_mm": overlap.get("hausdorff_mm")})
    return out


def summary(frozen_list) -> dict:
    ok = [f for f in frozen_list if f.accepted]
    return {
        "controls": len(frozen_list),
        "accepted_and_frozen": len(ok),
        "refused": len(frozen_list) - len(ok),
        "accepted_space_ids": [f.space_id for f in ok],
        "refusal_reasons": {f.space_id: list(f.refusals)
                            for f in frozen_list if not f.accepted},
        "exit_gate": ("PASS" if ok else "FAIL"),
        "exit_gate_rule": ("at least one frozen control has an independently "
                           "generated, valid, non-overlapping clear-internal "
                           "polygon with no bbox and no raster millimetre "
                           "edge"),
    }
