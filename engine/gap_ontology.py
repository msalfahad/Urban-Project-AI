"""E1.3 §5, §6 — a gap is a question. "Door" is one of its answers.

E1.2 let any collinear gap wider than the junction tolerance and no wider
than a double leaf become a portal, on the strength of the two wall ends
facing each other. Driver showed the cost: a 150 mm break inside one
polyline, with no door entity anywhere near it, was established as a
doorway and a released room was built through it.

Two wall ends facing each other across a gap is what a doorway looks
like. It is also what a T-junction looks like where a cross wall lands,
what a column pocket looks like, and what a polyline broken for drafting
convenience looks like. The geometry alone cannot tell them apart, so it
is not allowed to.

A gap is therefore classified, and only a class carrying positive
evidence of an opening may become a portal. Everything else is recorded
as what it is - a junction, a place where material continues across, an
open edge, or a question nobody has answered.
"""

from __future__ import annotations

import hashlib

MODEL = "A_GAP_IS_CLASSIFIED_NEVER_ASSUMED_TO_BE_A_DOOR_V1"

# ------------------------------------------------------------------ classes
CONFIRMED_DOOR_PORTAL = "CONFIRMED_DOOR_PORTAL"
PROBABLE_DOOR_PORTAL = "PROBABLE_DOOR_PORTAL"
CAD_JUNCTION_GAP = "CAD_JUNCTION_GAP"
MATERIAL_CONTINUITY_GAP = "MATERIAL_CONTINUITY_GAP"
OPEN_PHYSICAL_EDGE = "OPEN_PHYSICAL_EDGE"
UNRESOLVED_GAP = "UNRESOLVED_GAP"

GAP_CLASSES = (CONFIRMED_DOOR_PORTAL, PROBABLE_DOOR_PORTAL, CAD_JUNCTION_GAP,
               MATERIAL_CONTINUITY_GAP, OPEN_PHYSICAL_EDGE, UNRESOLVED_GAP)

# Only these two are doorways. A boundary may be closed across them,
# topologically, with no material.
IS_A_PORTAL = (CONFIRMED_DOOR_PORTAL, PROBABLE_DOOR_PORTAL)

# A junction gap is repaired: the material was meant to be continuous and
# the pen stopped short. A continuity gap is likewise crossed by material
# that exists - the cross wall, the column - so the boundary continues.
MATERIAL_CONTINUES_ACROSS = (CAD_JUNCTION_GAP, MATERIAL_CONTINUITY_GAP)

# Neither a portal nor material. The boundary stops here and says so.
NOTHING_MAY_BE_CLOSED_ACROSS = (OPEN_PHYSICAL_EDGE, UNRESOLVED_GAP)

# ----------------------------------------------------------- door evidence
# Positive evidence that an OPENING was drawn. Any one of these is enough
# to confirm, because each is the author saying "a door is here".
EV_DOOR_LEAF_OR_SWING = "A_DOOR_LEAF_OR_SWING_ARC_STANDS_IN_THE_GAP"
EV_DOOR_BLOCK = "A_BLOCK_USED_FOR_DOORS_IS_PLACED_IN_THE_GAP"
EV_EXPLICIT_OPENING_ENTITY = "AN_EXPLICIT_OPENING_ENTITY_OCCUPIES_THE_GAP"
EV_DOOR_SCHEDULE_LINK = "A_DOOR_SCHEDULE_OR_MARK_REFERENCES_THIS_OPENING"
EV_THRESHOLD_WITH_DOOR = (
    "THRESHOLD_OR_JAMB_GEOMETRY_TOGETHER_WITH_ESTABLISHED_DOOR_EVIDENCE")

CONFIRMING_EVIDENCE = (EV_DOOR_LEAF_OR_SWING, EV_DOOR_BLOCK,
                       EV_EXPLICIT_OPENING_ENTITY, EV_DOOR_SCHEDULE_LINK,
                       EV_THRESHOLD_WITH_DOOR)

# Circumstantial evidence. No one of these is an opening; a combination
# of independent ones makes an opening probable, and the combination is
# recorded so a reader can disagree with it.
EV_JAMB_GEOMETRY = "JAMB_GEOMETRY_RETURNS_INTO_THE_WALL_AT_BOTH_ENDS"
EV_WIDTH_FAMILY = (
    "ITS_WIDTH_MATCHES_A_FAMILY_ESTABLISHED_BY_CONFIRMED_DOORS_IN_THIS_"
    "DRAWING")
EV_VISUAL_DOORWAY = "THE_COLD_SOURCE_ONLY_PASS_READ_A_DOORWAY_HERE"
EV_WALL_INTERRUPTION = (
    "THE_WALL_BAND_IS_INTERRUPTED_ACROSS_ITS_FULL_THICKNESS_HERE")

PROBABLE_EVIDENCE = (EV_JAMB_GEOMETRY, EV_WIDTH_FAMILY, EV_VISUAL_DOORWAY,
                     EV_WALL_INTERRUPTION)
PROBABLE_EVIDENCE_REQUIRED = 2

# ------------------------------------------------- occupancy of the gap
# §6: what is standing in the gap, if anything.
OCC_PERPENDICULAR_WALL = "A_PERPENDICULAR_WALL_LANDS_IN_THIS_GAP"
OCC_COLUMN_OR_PIER = "A_COLUMN_OR_PIER_OCCUPIES_THIS_GAP"
OCC_STRUCTURAL_OBJECT = "A_STRUCTURAL_OBJECT_OCCUPIES_THIS_GAP"
OCC_OTHER_MATERIAL_BAND = "ANOTHER_MATERIAL_BAND_CROSSES_THIS_GAP"
OCCUPANCY = (OCC_PERPENDICULAR_WALL, OCC_COLUMN_OR_PIER,
             OCC_STRUCTURAL_OBJECT, OCC_OTHER_MATERIAL_BAND)

# ------------------------------------------------------------------- prose
A_JUNCTION_AND_A_DOOR_ARE_DIFFERENT_ONTOLOGIES = (
    "repairing a junction says the author drew one thing in two strokes. "
    "Establishing a door says the author drew an opening. They license "
    "different downstream work - one contributes wall material at a "
    "corner, the other contributes a door - and a rule that cannot tell "
    "them apart will keep producing rooms with doorways nobody built")

TWO_ENDS_FACING_IS_NOT_A_DOOR = (
    "two wall ends facing each other across a gap is what a doorway looks "
    "like, and also what a T-junction, a column pocket and a polyline "
    "broken for drafting convenience look like. It is the shape of the "
    "question, not the answer")

WIDTH_FAMILIES_COME_FROM_THE_DRAWING = (
    "the widths that count as door-like are learned from the openings this "
    "drawing itself confirms, never from a number chosen for one project. "
    "A drawing with no confirmed door establishes no width family, and "
    "then width is not evidence of anything")


def model_hash() -> str:
    parts = ([MODEL] + list(GAP_CLASSES) + list(CONFIRMING_EVIDENCE)
             + list(PROBABLE_EVIDENCE) + list(OCCUPANCY)
             + [str(PROBABLE_EVIDENCE_REQUIRED)])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- inference
def thickness_families(band_offsets_mm, *, tol_mm=15.0) -> list:
    """The wall thicknesses this drawing actually uses.

    Built by clustering the offsets at which paired wall faces were found,
    so it is the drawing's own evidence rather than a project constant. A
    drawing that establishes no wall band establishes no family, and then
    §6 simply does not fire.
    """
    vals = sorted(float(v) for v in band_offsets_mm or () if float(v) > 0)
    families, cur = [], []
    for v in vals:
        if cur and v - cur[0] > tol_mm:
            families.append(cur)
            cur = []
        cur.append(v)
    if cur:
        families.append(cur)
    out = []
    for f in families:
        out.append({"thickness_mm": round(sum(f) / len(f), 2),
                    "members": len(f),
                    "min_mm": round(min(f), 2), "max_mm": round(max(f), 2)})
    out.sort(key=lambda r: -r["members"])
    return out


def width_families(confirmed_widths_mm, *, tol_mm=50.0) -> list:
    """The opening widths this drawing's CONFIRMED doors actually use."""
    return [{"width_mm": f["thickness_mm"], "members": f["members"],
             "min_mm": f["min_mm"], "max_mm": f["max_mm"]}
            for f in thickness_families(confirmed_widths_mm, tol_mm=tol_mm)]


def matches_a_thickness_family(gap_mm, families, *, tol_mm=25.0):
    """Is this gap the size of a wall this drawing uses?"""
    for f in families or ():
        if abs(float(gap_mm) - f["thickness_mm"]) <= tol_mm:
            return f
    return None


def matches_a_width_family(gap_mm, families, *, tol_mm=75.0):
    for f in families or ():
        if abs(float(gap_mm) - f["width_mm"]) <= tol_mm:
            return f
    return None


# ------------------------------------------------------------- classify
def classify(*, gap_mm, junction_gap_mm, max_barrier_mm,
             confirming_evidence=(), probable_evidence=(),
             occupancy=(), thickness_family=None,
             collinear=True) -> dict:
    """Name what this gap is, and say what the naming rests on.

    The order matters. Material that demonstrably continues across the gap
    settles it before any door reasoning runs, because a cross wall
    landing in a gap is not an opening however door-shaped the gap is.
    """
    gap = float(gap_mm)
    conf = [e for e in confirming_evidence if e in CONFIRMING_EVIDENCE]
    prob = [e for e in probable_evidence if e in PROBABLE_EVIDENCE]
    occ = [o for o in occupancy if o in OCCUPANCY]
    notes = []

    if gap <= junction_gap_mm:
        cls = CAD_JUNCTION_GAP
        notes.append(f"at or below {junction_gap_mm} mm a line stops short "
                     "of its junction. That is drafting, not an opening")
    elif occ:
        cls = MATERIAL_CONTINUITY_GAP
        notes.append("material stands in this gap, so the boundary "
                     "continues across it: " + ", ".join(sorted(occ)))
        if thickness_family:
            notes.append(
                "its width matches a wall thickness this drawing uses "
                f"({thickness_family['thickness_mm']} mm, "
                f"{thickness_family['members']} paired faces), which is "
                "what a T-junction looks like in plan")
    elif conf:
        cls = CONFIRMED_DOOR_PORTAL
        notes.append("the author drew an opening here: " + ", ".join(conf))
    elif thickness_family and not conf:
        cls = UNRESOLVED_GAP
        notes.append(
            "its width matches a wall thickness this drawing uses "
            f"({thickness_family['thickness_mm']} mm) and nothing was found "
            "standing in it. A wall-thickness-scale gap with no door "
            "evidence is as likely a junction the cross wall did not reach "
            "as it is a doorway, and neither reading is established")
    elif len(prob) >= PROBABLE_EVIDENCE_REQUIRED:
        cls = PROBABLE_DOOR_PORTAL
        notes.append(
            f"{len(prob)} independent circumstantial evidences, at or above "
            f"the {PROBABLE_EVIDENCE_REQUIRED} this class requires: "
            + ", ".join(sorted(prob)))
    elif gap > max_barrier_mm:
        cls = OPEN_PHYSICAL_EDGE
        notes.append(f"wider than {max_barrier_mm} mm with no door "
                     "evidence. Nothing was built across it")
    elif not collinear:
        cls = UNRESOLVED_GAP
        notes.append("the two ends do not continue each other's line, so "
                     "this is not the shape of a doorway, and what it is "
                     "has not been established")
    else:
        cls = UNRESOLVED_GAP
        notes.append(
            f"{len(prob)} circumstantial evidence(s), below the "
            f"{PROBABLE_EVIDENCE_REQUIRED} this class requires, and no "
            "confirming evidence. Two wall ends facing each other is not "
            "on its own a door")

    return {
        "GAP_CLASS": cls,
        "gap_mm": round(gap, 2),
        "IS_A_PORTAL": cls in IS_A_PORTAL,
        "MATERIAL_CONTINUES_ACROSS": cls in MATERIAL_CONTINUES_ACROSS,
        "NOTHING_MAY_BE_CLOSED_ACROSS": cls in NOTHING_MAY_BE_CLOSED_ACROSS,
        "confirming_evidence": sorted(conf),
        "probable_evidence": sorted(prob),
        "probable_evidence_required": PROBABLE_EVIDENCE_REQUIRED,
        "occupancy": sorted(occ),
        "matched_wall_thickness_family": thickness_family,
        "collinear": bool(collinear),
        "notes": notes,
        "two_ends_facing_is_not_a_door": TWO_ENDS_FACING_IS_NOT_A_DOOR,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "GAP_CLASSES": list(GAP_CLASSES),
        "IS_A_PORTAL": list(IS_A_PORTAL),
        "MATERIAL_CONTINUES_ACROSS": list(MATERIAL_CONTINUES_ACROSS),
        "NOTHING_MAY_BE_CLOSED_ACROSS": list(NOTHING_MAY_BE_CLOSED_ACROSS),
        "CONFIRMING_EVIDENCE": list(CONFIRMING_EVIDENCE),
        "PROBABLE_EVIDENCE": list(PROBABLE_EVIDENCE),
        "PROBABLE_EVIDENCE_REQUIRED": PROBABLE_EVIDENCE_REQUIRED,
        "OCCUPANCY": list(OCCUPANCY),
        "scope": ("GENERAL. No project dimension appears here: the wall "
                  "thickness families and the opening width families are "
                  "inferred from the drawing under test"),
        "why": {
            "a_junction_and_a_door_are_different_ontologies":
                A_JUNCTION_AND_A_DOOR_ARE_DIFFERENT_ONTOLOGIES,
            "two_ends_facing_is_not_a_door": TWO_ENDS_FACING_IS_NOT_A_DOOR,
            "width_families_come_from_the_drawing":
                WIDTH_FAMILIES_COME_FROM_THE_DRAWING,
        },
    }
