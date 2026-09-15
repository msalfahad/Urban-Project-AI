"""E75 — close a junction with evidence, never with a tolerance.

Five passages of 50-300 mm merge rooms into blobs while accepted wall bands
run along their whole length. The walls are drawn; two wall polygons fail to
meet. Every cheap fix for that is a lie of a particular kind:

    a larger global snap      closes EVERY gap of that size in the drawing,
                              including the ones somebody drew open;
    a buffer or dilation      thickens every wall by the same amount and
                              changes every area;
    morphological closing     invents material wherever two things are
                              near, with no record of where or why;
    generic gap filling       has no evidence at all and no provenance.

So a gap is closed only by an explicit JUNCTION_PATCH, and only where local
vector geometry PROVES a physical junction. The patch is a named object with
its own polygon, evidence, validation status and a maximum extension it may
never exceed. It can be listed, reviewed, refused and removed.

A patch is physical material only if its evidence supports that. An
unvalidated patch may enter the diagnostic solid and may not enter the
established one.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# What kind of junction the evidence describes.
JUNCTION_L = "L_CORNER"
JUNCTION_T = "T_JUNCTION"
JUNCTION_X = "CROSSING"
JUNCTION_COLLINEAR = "COLLINEAR_CONTINUATION"
JUNCTION_UNRESOLVED = "JUNCTION_UNRESOLVED"

JUNCTION_TYPES = (JUNCTION_L, JUNCTION_T, JUNCTION_X, JUNCTION_COLLINEAR,
                  JUNCTION_UNRESOLVED)

# Evidence a junction is physical. Geometric items are ONE family however
# many of them there are; see the portal existence rule for why that matters.
EV_AXES_MEET = "WALL_BAND_AXES_MEET_WITHIN_A_WALL_THICKNESS"
EV_FACES_TERMINATE = "BOTH_BANDS_FACES_TERMINATE_AT_THE_MEETING_POINT"
EV_END_CAP = "AN_END_CAP_CLOSES_ONE_BAND_AT_THE_JUNCTION"
EV_COMPATIBLE_THICKNESS = "WALL_SEPARATIONS_ARE_COMPATIBLE"
EV_SHARED_SOURCE_PATH = "BOTH_BANDS_COME_FROM_ONE_SOURCE_PATH"
EV_RASTER_SOLID = "RASTER_SHOWS_SOLID_ACROSS_THE_JUNCTION"
EV_COLLINEAR = "THE_TWO_BANDS_ARE_COLLINEAR_AND_SAME_THICKNESS"

EVIDENCE_FAMILY = {
    EV_AXES_MEET: "GEOMETRY",
    EV_FACES_TERMINATE: "GEOMETRY",
    EV_COMPATIBLE_THICKNESS: "GEOMETRY",
    EV_COLLINEAR: "GEOMETRY",
    EV_END_CAP: "DRAWN_SYMBOL",
    EV_SHARED_SOURCE_PATH: "SOURCE_STRUCTURE",
    EV_RASTER_SOLID: "RASTER",
}

# WHERE A FAMILY'S EVIDENCE PHYSICALLY COMES FROM.
#
# The correction that prompted this: JP-0003 was VALIDATED on GEOMETRY +
# RASTER and reported as two independent families. It is not. This project's
# raster is RENDERED FROM THE SAME PDF as the vector geometry, so the two
# are one observation of one artefact in two encodings. A rendering cannot
# witness masonry the drawing does not contain — it can only redraw what is
# already there.
#
#     SAME_DRAWING     derived from this PDF and nothing else. However many
#                      such observations agree, they are ONE source.
#     SAME_DOCUMENT_SET  another sheet, schedule or table from the same
#                      issue: a different author's statement, still the
#                      same project record.
#     INDEPENDENT_OF_THE_DRAWING  a CAD entity from the originating model,
#                      a site measurement, a human inspection.
#
# Only families in different independence classes count as independent for
# establishing PHYSICAL MATERIAL.
SOURCE_INDEPENDENCE_CLASS = {
    "GEOMETRY": "SAME_DRAWING",
    "DRAWN_SYMBOL": "SAME_DRAWING",
    "SOURCE_STRUCTURE": "SAME_DRAWING",
    # Rendered from the same PDF. Corroborates and LOCALISES; never
    # independently establishes that material is present.
    "RASTER": "SAME_DRAWING",
    "DOCUMENT": "SAME_DOCUMENT_SET",
    "CAD": "INDEPENDENT_OF_THE_DRAWING",
    "SITE": "INDEPENDENT_OF_THE_DRAWING",
    "HUMAN": "INDEPENDENT_OF_THE_DRAWING",
}

MATERIAL_WITNESS_CLASSES = ("SAME_DOCUMENT_SET",
                            "INDEPENDENT_OF_THE_DRAWING")

# Where a gap turns out NOT to be a junction, the gap still has a cause and
# a repair, and they are not the same repair. Naming them stops the next
# round from reaching for a patch again.
REPAIR_JUNCTION = "REPAIR_IS_JUNCTION_ASSEMBLY"
REPAIR_PAIRING = "REPAIR_IS_IN_WALL_FACE_PAIRING"
REPAIR_NOT_ONE_WALL = "NOT_ONE_WALL_TWO_DIFFERENT_WALLS_MEET_HERE"
REPAIR_GENUINE_OPENING = "NOTHING_IS_DRAWN_HERE_THE_OPENING_IS_REAL"
REPAIR_UNRESOLVED = "REPAIR_UNRESOLVED"

REPAIR_CLASSES = (REPAIR_JUNCTION, REPAIR_PAIRING, REPAIR_NOT_ONE_WALL,
                  REPAIR_GENUINE_OPENING, REPAIR_UNRESOLVED)

PATCH_VALIDATED = "JUNCTION_PATCH_VALIDATED"
PATCH_PROBABLE = "JUNCTION_PATCH_PROBABLE"
PATCH_REFUSED = "JUNCTION_PATCH_REFUSED"

# A patch may never extend a wall further than this. It exists to close a
# junction, not to grow a wall, and the ceiling is taken from the drawing's
# own thickest accepted wall rather than from a constant: a junction gap
# wider than a wall is thick is not a junction.
MAX_EXTENSION_FACTOR = 1.0

# Two independent evidence families are required to VALIDATE a patch.
# Four geometric observations of one corner are one family, not four proofs.
MIN_FAMILIES_FOR_VALIDATED = 2


class JunctionPatchError(RuntimeError):
    """A patch was asked to do something a patch may not do."""


@dataclass(frozen=True)
class JunctionPatch:
    """One proven physical junction, as a named piece of material."""

    patch_id: str
    wall_band_ids: tuple[str, ...]
    source_face_ids: tuple[str, ...]
    polygon: object = None
    junction_type: str = JUNCTION_UNRESOLVED
    axis: str = ""
    evidence: tuple[str, ...] = ()
    conflicting_evidence: tuple[str, ...] = ()
    validation_status: str = PATCH_REFUSED
    gap_repair_class: str = REPAIR_UNRESOLVED
    strokes_at_the_gap: tuple[str, ...] = ()
    raster_support: float | None = None
    extension_mm: float = 0.0
    max_extension_mm: float = 0.0
    gap_closed_mm: float = 0.0
    drawing_id: str = ""
    drawing_revision: str = ""
    provenance: dict = field(default_factory=dict)
    why: str = ""

    @property
    def families(self) -> set:
        return {EVIDENCE_FAMILY[e] for e in self.evidence
                if e in EVIDENCE_FAMILY}

    @property
    def independence_classes(self) -> set:
        """How many genuinely separate SOURCES support this patch."""
        return {SOURCE_INDEPENDENCE_CLASS[f] for f in self.families
                if f in SOURCE_INDEPENDENCE_CLASS}

    @property
    def has_an_independent_material_witness(self) -> bool:
        """Does anything outside this drawing say material is here?"""
        return bool(self.independence_classes
                    & set(MATERIAL_WITNESS_CLASSES))

    @property
    def is_validated(self) -> bool:
        return self.validation_status == PATCH_VALIDATED

    @property
    def is_material(self) -> bool:
        """Physical material only where the evidence supports it."""
        return self.is_validated

    @property
    def area_m2(self) -> float:
        return 0.0 if self.polygon is None else self.polygon.area / 1e6

    def record(self) -> dict:
        return {
            "junction_patch_id": self.patch_id,
            "participating_wall_band_ids": list(self.wall_band_ids),
            "source_face_ids": list(self.source_face_ids),
            "junction_type": self.junction_type,
            "axis": self.axis,
            "patch_polygon_vertices": (
                0 if self.polygon is None
                else len(getattr(self.polygon, "exterior", ()).coords)
                if self.polygon.geom_type == "Polygon" else -1),
            "patch_area_m2": round(self.area_m2, 6),
            "gap_closed_mm": round(self.gap_closed_mm, 1),
            "extension_mm": round(self.extension_mm, 1),
            "maximum_extension_distance_mm": round(self.max_extension_mm, 1),
            "evidence": list(self.evidence),
            "evidence_families": sorted(self.families),
            "source_independence_classes": sorted(self.independence_classes),
            "has_an_independent_material_witness": (
                self.has_an_independent_material_witness),
            "why_raster_is_not_independent_here": (
                "this project's raster is rendered from the same PDF as the "
                "vector geometry. It corroborates and LOCALISES; it cannot "
                "independently establish that material is present, because "
                "a rendering only redraws what the drawing already "
                "contains"),
            "conflicting_evidence": list(self.conflicting_evidence),
            "validation_status": self.validation_status,
            "gap_repair_class": self.gap_repair_class,
            "unpaired_strokes_at_the_gap": list(self.strokes_at_the_gap),
            "raster_support_across_the_gap": self.raster_support,
            "is_physical_material": self.is_material,
            "drawing_id": self.drawing_id,
            "drawing_revision": self.drawing_revision,
            "provenance": dict(self.provenance),
            "why": self.why,
            "not_produced_by": (
                "no snap tolerance, no buffer, no morphological closing and "
                "no generic gap filling. A patch exists only where local "
                "vector geometry proves a physical junction, and it can be "
                "listed, reviewed and removed"),
        }


def _status(families: set, extension: float, ceiling: float,
            conflicts: tuple) -> tuple[str, str]:
    classes = {SOURCE_INDEPENDENCE_CLASS[f] for f in families
               if f in SOURCE_INDEPENDENCE_CLASS}
    if conflicts:
        return PATCH_REFUSED, (
            f"conflicting evidence: {', '.join(conflicts)}. A patch is not "
            "created where the drawing argues with itself")
    if extension > ceiling:
        return PATCH_REFUSED, (
            f"closing this would extend a band by {extension:.0f} mm, past "
            f"the {ceiling:.0f} mm ceiling taken from the drawing's own "
            "thickest accepted wall. A gap wider than a wall is thick is "
            "not a junction")
    if (len(families) >= MIN_FAMILIES_FOR_VALIDATED
            and len(classes) >= MIN_FAMILIES_FOR_VALIDATED):
        return PATCH_VALIDATED, (
            f"{len(families)} evidence families "
            f"({', '.join(sorted(families))}) from {len(classes)} "
            f"INDEPENDENT sources ({', '.join(sorted(classes))}) agree a "
            f"physical junction is here, and closing it extends a band by "
            f"{extension:.0f} mm against a ceiling of {ceiling:.0f} mm")
    if len(families) >= MIN_FAMILIES_FOR_VALIDATED:
        return PATCH_PROBABLE, (
            f"{len(families)} evidence families "
            f"({', '.join(sorted(families))}) support this junction, but "
            f"all of them are {', '.join(sorted(classes))}: this project's "
            "raster is RENDERED FROM THE SAME PDF as the vector geometry, "
            "so agreement between them is one observation of one artefact "
            "in two encodings. A rendering cannot witness masonry the "
            "drawing does not contain. Diagnostic solid only, until "
            "something outside this drawing says material is here")
    if families:
        return PATCH_PROBABLE, (
            f"only the {', '.join(sorted(families))} family supports this "
            "junction. Several observations within one family are one "
            "family, not several proofs — so this patch may enter the "
            "diagnostic solid and NOT the established one")
    return PATCH_REFUSED, "no evidence of a junction here at all"


def _repair_class(*, bands_reaching: int, conflicts: tuple,
                  wall_like_strokes: tuple, ratio, status: str
                  ) -> tuple[str, str]:
    """What would actually fix this gap, given what is at it."""
    if status in (PATCH_VALIDATED, PATCH_PROBABLE):
        # The repair class answers "what would fix this gap", which is a
        # different question from "may we build material here". A junction
        # supported only by this drawing is still a junction; what it lacks
        # is an independent witness, not a diagnosis.
        return REPAIR_JUNCTION, (
            "two walls meet here and the solid does not join them"
            + ("" if status == PATCH_VALIDATED else
               ". The reading is supported only by this drawing, so the "
               "patch is diagnostic until something outside it agrees"))
    if ratio is not None and ratio <= RASTER_EMPTY_SUPPORT:
        return REPAIR_GENUINE_OPENING, (
            f"raster support {ratio:.2f}: nothing solid is drawn across this "
            "gap. It is not a junction that failed to close — the drawing "
            "leaves it open, and closing it would invent a wall")
    if any("separations differ" in c for c in conflicts):
        return REPAIR_NOT_ONE_WALL, (
            "the bands meeting here are different walls, so there is no "
            "single junction to assemble. Whatever divides these spaces is "
            "not either of them")
    if wall_like_strokes:
        return REPAIR_PAIRING, (
            f"{len(wall_like_strokes)} wall-like unpaired stroke(s) lie at "
            "this gap with raster support, and only "
            f"{bands_reaching} accepted band reaches it. A wall IS drawn "
            "here and never became a band: the repair is in FACE PAIRING, "
            "not in junction assembly, and a patch here would paper over an "
            "extraction failure")
    return REPAIR_UNRESOLVED, (
        f"{bands_reaching} band(s) reach this gap, no wall-like stroke lies "
        "at it, and the raster is not decisive. Nothing available says what "
        "would fix it")


def propose(gap, bands, *, wall_polys=(), caps=(), raster_support=None,
            strokes=(), max_wall_thickness_mm: float = 0.0,
            drawing_id: str = "", revision: str = "",
            patch_id: str = "") -> JunctionPatch:
    """Examine one located gap and propose a patch, or refuse.

    `gap` carries the leak map's finding: axis, the fixed coordinate, the
    along extent, and the passage width. Everything else is read from the
    vector geometry at that place.
    """
    from shapely.geometry import box

    axis = gap["axis"]
    at = float(gap["fixed_mm"])
    lo, hi = (float(gap["along_mm"][0]), float(gap["along_mm"][1]))
    width = float(gap.get("passage_width_mm") or 0.0)
    ceiling = max_wall_thickness_mm * MAX_EXTENSION_FACTOR

    # Which accepted bands end at this gap, on either axis. A junction is
    # made of the bands that MEET there, so both orientations count.
    reach = max(ceiling, width) + MIN_EXTENSION_REACH_MM
    near = []
    for b in bands:
        t = getattr(b, "wall_face_separation_mm", None)
        if t is None:
            continue
        b_lo, b_hi = min(b.start_mm, b.end_mm), max(b.start_mm, b.end_mm)
        if b.axis == axis:
            if (abs(b.centreline_mm - at) <= reach
                    and b_hi >= lo - reach and b_lo <= hi + reach):
                near.append((b, min(abs(b_hi - lo), abs(b_lo - hi))))
        else:
            # A band on the other axis crosses this line: it participates if
            # its own run spans the gap's fixed coordinate.
            if (b_lo - reach <= at <= b_hi + reach
                    and lo - reach <= b.centreline_mm <= hi + reach):
                near.append((b, abs(b.centreline_mm - lo)))

    wall_like = _wall_like_at(strokes, axis, at, lo, hi, reach)
    ratio = (None if raster_support is None
             else raster_support(axis, at, lo, hi))

    if len(near) < 2:
        rclass, rwhy = _repair_class(
            bands_reaching=len(near), conflicts=(),
            wall_like_strokes=wall_like, ratio=ratio,
            status=PATCH_REFUSED)
        return JunctionPatch(
            patch_id=patch_id, wall_band_ids=tuple(
                b.wall_band_id for b, _ in near),
            source_face_ids=(), axis=axis, junction_type=JUNCTION_UNRESOLVED,
            validation_status=PATCH_REFUSED, gap_repair_class=rclass,
            strokes_at_the_gap=wall_like,
            raster_support=(None if ratio is None else round(ratio, 3)),
            max_extension_mm=ceiling,
            gap_closed_mm=width, drawing_id=drawing_id,
            drawing_revision=revision,
            why=(f"only {len(near)} accepted band(s) reach this gap. A "
                 "junction needs at least two walls to join, and inventing "
                 "the second is what this module exists to refuse. "
                 + rwhy))

    near.sort(key=lambda kv: kv[1])
    parts = [b for b, _ in near[:4]]
    ev, conflicts = [], []

    axes = {b.axis for b in parts}
    if len(axes) > 1:
        ev.append(EV_AXES_MEET)
        jtype = JUNCTION_T if len(parts) == 2 else JUNCTION_X
    else:
        jtype = JUNCTION_COLLINEAR
        seps = [b.wall_face_separation_mm for b in parts]
        if max(seps) - min(seps) <= COMPATIBLE_THICKNESS_MM:
            ev.append(EV_COLLINEAR)
        centres = [b.centreline_mm for b in parts]
        if max(centres) - min(centres) > COMPATIBLE_THICKNESS_MM:
            conflicts.append("collinear bands whose centrelines disagree by "
                             "more than a compatible tolerance")

    seps = [b.wall_face_separation_mm for b in parts]
    if max(seps) - min(seps) <= COMPATIBLE_THICKNESS_MM:
        if EV_COLLINEAR not in ev:
            ev.append(EV_COMPATIBLE_THICKNESS)
    else:
        conflicts.append(
            f"wall separations differ by {max(seps) - min(seps):.0f} mm, so "
            "these are not two stretches of one wall")

    band_ids = {b.wall_band_id for b in parts}
    cap_ids = tuple(sorted(
        str(getattr(c, "cap_id", "") or getattr(c, "segment_id", ""))
        for c in caps
        if getattr(c, "axis", "") in axes
        and abs(getattr(c, "fixed_mm", 1e12) - at) <= reach))
    if cap_ids:
        ev.append(EV_END_CAP)

    paths = [set(getattr(b, "source_object_ids", ())) for b in parts]
    if paths and set.intersection(*paths):
        ev.append(EV_SHARED_SOURCE_PATH)

    if raster_support is not None:
        if ratio is not None and ratio >= RASTER_SOLID_SUPPORT:
            ev.append(EV_RASTER_SOLID)
        elif ratio is not None and ratio <= RASTER_EMPTY_SUPPORT:
            conflicts.append(
                f"raster support {ratio:.2f} across this gap: nothing solid "
                "is drawn here, so a physical junction is contradicted")

    # The patch itself: the rectangle the gap leaves open, bounded by the
    # participating bands' own thickness. Never wider than the drawing's
    # thickest wall, and never longer than the gap.
    thickness = max(seps)
    if axis == "H":
        poly = box(lo, at - thickness / 2.0, hi, at + thickness / 2.0)
    else:
        poly = box(at - thickness / 2.0, lo, at + thickness / 2.0, hi)
    extension = hi - lo

    families = {EVIDENCE_FAMILY[e] for e in ev if e in EVIDENCE_FAMILY}
    status, why = _status(families, extension, ceiling, tuple(conflicts))
    rclass, rwhy = _repair_class(
        bands_reaching=len(near), conflicts=tuple(conflicts),
        wall_like_strokes=wall_like, ratio=ratio, status=status)
    return JunctionPatch(
        patch_id=patch_id, wall_band_ids=tuple(sorted(band_ids)),
        source_face_ids=tuple(sorted(
            f for b in parts for f in
            tuple(getattr(b, "face_a_ids", ())) +
            tuple(getattr(b, "face_b_ids", ())))),
        polygon=(poly if status != PATCH_REFUSED else None),
        junction_type=jtype, axis=axis, evidence=tuple(ev),
        conflicting_evidence=tuple(conflicts), validation_status=status,
        gap_repair_class=rclass, strokes_at_the_gap=wall_like,
        raster_support=(None if ratio is None else round(ratio, 3)),
        extension_mm=extension, max_extension_mm=ceiling,
        gap_closed_mm=width, drawing_id=drawing_id,
        drawing_revision=revision,
        provenance={"repair_class_why": rwhy,
                    "located_by": gap.get("located_by", "FREE_SPACE_NECK"),
                    "leak_id": gap.get("leak_id", ""),
                    "end_caps": list(cap_ids[:6])},
        why=why)


def _wall_like_at(strokes, axis, at, lo, hi, reach) -> tuple:
    """Unpaired strokes evidence says could be wall, lying at this gap."""
    from engine.unpaired_strokes import WALL_LIKE_CLASSES
    out = []
    for s in strokes:
        if s.stroke_class not in WALL_LIKE_CLASSES:
            continue
        if s.axis == axis:
            if (abs(s.fixed_mm - at) <= reach
                    and s.end_mm >= lo - reach and s.start_mm <= hi + reach):
                out.append(s.stroke_id)
        elif (s.start_mm - reach <= at <= s.end_mm + reach
              and lo - reach <= s.fixed_mm <= hi + reach):
            out.append(s.stroke_id)
    return tuple(sorted(out))


# How far past a gap's own extent to look for a band that ends there.
MIN_EXTENSION_REACH_MM = 50.0
# Two wall separations within this are the same wall.
COMPATIBLE_THICKNESS_MM = 25.0
RASTER_SOLID_SUPPORT = 0.5
RASTER_EMPTY_SUPPORT = 0.1


def summary(patches) -> dict:
    return {
        "patches_proposed": len(patches),
        "validated": sum(1 for p in patches if p.is_validated),
        "probable": sum(1 for p in patches
                        if p.validation_status == PATCH_PROBABLE),
        "refused": sum(1 for p in patches
                       if p.validation_status == PATCH_REFUSED),
        "by_junction_type": dict(Counter(p.junction_type for p in patches)),
        "by_gap_repair_class": dict(Counter(
            p.gap_repair_class for p in patches)),
        "validated_material_m2": round(sum(
            p.area_m2 for p in patches if p.is_material), 6),
        "patches": [p.record() for p in patches],
        "the_rule": (
            "a patch is physical material only where its evidence supports "
            "that: two families from two INDEPENDENT SOURCES. Two families "
            "that both derive from this drawing are one source, however "
            "much they agree"),
        "source_independence": {
            "classes": dict(SOURCE_INDEPENDENCE_CLASS),
            "material_witness_classes": list(MATERIAL_WITNESS_CLASSES),
            "why": ("the raster is rendered from the same PDF as the "
                    "vector geometry, so GEOMETRY + RASTER is one "
                    "observation in two encodings and not two witnesses"),
        },
        "patches_with_an_independent_material_witness": sum(
            1 for p in patches if p.has_an_independent_material_witness),
        "never_used": (
            "larger snap tolerance, buffer, morphological closing, generic "
            "gap filling"),
    }
