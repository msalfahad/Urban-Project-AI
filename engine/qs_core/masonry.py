"""Is this measurable band actually billable masonry?

A thickness is a measurement, not an identity.  Every extractor produces bands that have a width and are not
walls: the little square where two walls cross, a line drawn twice on two layers, a column that happens to sit in
a wall line, a grid artefact one cell wide.  Measure all of them and a bill acquires thickness families that no
one ever built, each with a plausible area beside it.

So identity is decided before measurement, on evidence about the object: what the drawing calls it, how it
behaves in the drawing's own topology, and whether its thickness is one the building actually uses.  A band that
proves none of this is not quietly billed and is not quietly dropped - it is unresolved, and it is a question.

There is no list of accepted thicknesses here.  Which thicknesses a building uses is discovered from the drawing
it was drawn in, and a building that uses different ones is classified just as well.
"""

from __future__ import annotations

from engine.qs_core import geom
from engine.qs_core.entities import (CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG, CONFIDENCE_WEAK,
                                     Evidence, KIND_COLUMN)

CONFIRMED_MASONRY_WALL = "CONFIRMED_MASONRY_WALL"
COLUMN_OR_STRUCTURE = "COLUMN_OR_STRUCTURE"
JUNCTION_ARTEFACT = "JUNCTION_ARTEFACT"
DUPLICATED_LINE_ARTEFACT = "DUPLICATED_LINE_ARTEFACT"
WALL_IDENTITY_UNRESOLVED = "WALL_IDENTITY_UNRESOLVED"
IDENTITIES = (CONFIRMED_MASONRY_WALL, COLUMN_OR_STRUCTURE, JUNCTION_ARTEFACT, DUPLICATED_LINE_ARTEFACT,
              WALL_IDENTITY_UNRESOLVED)

BILLABLE = (CONFIRMED_MASONRY_WALL,)

# A wall is longer than it is thick.  An object as long as it is wide is a column, a junction or an artefact -
# whatever it is, its quantity is not wall area.  This is what the word means, not a threshold chosen to fit.
WALL_ASPECT_MIN = 2.0

# A thickness that occurs on exactly one line in a whole drawing is not a construction standard; it is a
# measurement of something else that happens to have a width.  Two independent occurrences make it a family.
FAMILY_MIN_MEMBERS = 2

# Two lines that occupy the same place are one object drawn twice.
DUPLICATE_SHARE = 0.80

# A junction is covered by the walls that cross there.
JUNCTION_COVERAGE = 0.80


def family_key(thickness, tolerance):
    """The thickness a band belongs to, quantised to the distance the drawing distinguishes.

    Without this, a band drawn at 199.9 mm and its neighbour at 200.1 mm are billed as two different walls -
    which is how a bill acquires thickness families nobody built out of one that everybody did.
    """
    if thickness is None:
        return None
    step = max(tolerance, 1e-9)
    return round(round(thickness / step) * step, 6)


def thickness_families(lines, tolerance):
    """Which thicknesses this drawing actually uses, discovered from the drawing itself."""
    fams = {}
    for ln in lines:
        if ln.thickness is None:
            continue
        key = family_key(ln.thickness, tolerance)
        f = fams.setdefault(key, {"THICKNESS_M": key, "MEMBERS": [], "TOTAL_MATERIAL_LENGTH_M": 0.0})
        f["MEMBERS"].append(ln.component_ref)
        f["TOTAL_MATERIAL_LENGTH_M"] = round(
            f["TOTAL_MATERIAL_LENGTH_M"] + (ln.material_length if ln.material_length is not None else ln.length),
            6)
    for f in fams.values():
        f["MEMBERS"].sort()
        f["MEMBER_COUNT"] = len(f["MEMBERS"])
        f["PROVED"] = f["MEMBER_COUNT"] >= FAMILY_MIN_MEMBERS
        f["WHY"] = ("this thickness is used by several independent wall lines, so the building uses it"
                    if f["PROVED"] else
                    "this thickness occurs once in the whole drawing; one occurrence does not make a "
                    "construction standard, and the object may be something other than a wall")
    return {"FAMILIES": dict(sorted(fams.items())), "MIN_MEMBERS_FOR_A_FAMILY": FAMILY_MIN_MEMBERS,
            "DISCOVERED_FROM": "the wall lines of this source alone"}


def _segment_note(line, annotations):
    """A wall line is assembled from segments; what the drawing says about those segments is about the line.

    The segments agreeing is part of the evidence: two segments annotated as different materials do not make an
    annotated wall, they make a question, so a disagreement returns nothing and the line falls through to the
    other evidence.
    """
    segs = []
    for e in line.evidence:
        segs += list(e.detail.get("SEGMENTS", []) or [])
    notes = [annotations[s] for s in segs if s in annotations]
    if not notes:
        return {}
    materials = {(n.get("MATERIAL") or "").upper() for n in notes}
    if len(materials) > 1:
        return {}
    merged = dict(notes[0])
    merged["FROM_SEGMENTS"] = sorted(s for s in segs if s in annotations)
    return merged


def _aspect(ln):
    t = ln.thickness
    if not t:
        return None
    length = ln.material_length if ln.material_length is not None else ln.length
    return length / t


def _material(ln):
    return ln.material_rects or ln.rects


def _covered_share(ln, others):
    area = geom.total_area(_material(ln))
    if area <= 0:
        return 0.0
    inter = sum(geom.intersection_area(_material(ln), _material(o)) for o in others)
    return min(1.0, inter / area)


def classify_wall_identity(lines, tolerance, annotations=None, masonry_materials=(), families=None):
    """Decide what each band IS before anything measures it.

    `annotations` maps a component reference to whatever the drawing says about it - its layer, its material
    note.  It is the strongest evidence available and it comes from the source, so it is an argument.

    `families` lets the caller supply the thickness families of the WHOLE source.  Which thicknesses a building
    uses is a property of the building, not of one storey: a 150 mm partition that appears once in a basement
    and thirty times upstairs is a wall, and a per-storey view would call it an unknown object.
    """
    annotations = annotations or {}
    masonry_materials = {m.upper() for m in masonry_materials}
    fams = families or thickness_families(lines, tolerance)
    by_ref = {}
    records = []
    for ln in sorted(lines, key=lambda c: c.component_ref):
        by_ref[ln.component_ref] = ln

    for ln in sorted(lines, key=lambda c: c.component_ref):
        note = annotations.get(ln.component_ref) or _segment_note(ln, annotations)
        material = (note.get("MATERIAL") or "").upper()
        aspect = _aspect(ln)
        key = family_key(ln.thickness, tolerance)
        fam = fams["FAMILIES"].get(key, {"PROVED": False, "MEMBER_COUNT": 0})

        same_axis = [o for o in lines if o is not ln and o.floor == ln.floor and o.axis == ln.axis]
        cross_axis = [o for o in lines if o is not ln and o.floor == ln.floor and o.axis != ln.axis]
        twin = next((o for o in sorted(same_axis, key=lambda c: c.component_ref)
                     if geom.intersection_area(_material(ln), _material(o))
                     >= DUPLICATE_SHARE * geom.total_area(_material(ln))
                     and (geom.total_area(_material(o)), o.component_ref)
                     > (geom.total_area(_material(ln)), ln.component_ref)), None)
        junction_share = _covered_share(ln, cross_axis)

        if ln.kind == KIND_COLUMN:
            ident, conf, why = (COLUMN_OR_STRUCTURE, CONFIDENCE_PROVEN,
                                "the source draws this as a column, which is structure and not wall area")
        elif material and material in masonry_materials:
            ident, conf, why = (CONFIRMED_MASONRY_WALL, CONFIDENCE_PROVEN,
                                f"the drawing annotates this band as {material}, which the source declares a "
                                "masonry material")
        elif aspect is not None and aspect < WALL_ASPECT_MIN and junction_share >= JUNCTION_COVERAGE:
            ident, conf, why = (JUNCTION_ARTEFACT, CONFIDENCE_STRONG,
                                "this band is as short as it is thick and lies inside the crossing of walls "
                                "running the other way; it is where two walls meet, and its area is already in "
                                "them")
        elif twin is not None:
            ident, conf, why = (DUPLICATED_LINE_ARTEFACT, CONFIDENCE_STRONG,
                                f"this band occupies the same place as {twin.component_ref}; one object drawn "
                                "twice is billed once")
        elif aspect is not None and aspect < WALL_ASPECT_MIN:
            ident, conf, why = (COLUMN_OR_STRUCTURE, CONFIDENCE_WEAK,
                                "this band is as short as it is thick, so whatever it is, it is not a run of "
                                "wall; it is measured as structure or not at all")
        elif fam["PROVED"] and aspect is not None and aspect >= WALL_ASPECT_MIN:
            ident, conf, why = (CONFIRMED_MASONRY_WALL, CONFIDENCE_STRONG,
                                "this band runs far enough to be a wall and its thickness is one this drawing "
                                "uses repeatedly")
        else:
            ident, conf, why = (WALL_IDENTITY_UNRESOLVED, CONFIDENCE_NONE,
                                "nothing establishes what this band is: its thickness occurs "
                                f"{fam['MEMBER_COUNT']} time(s) in the whole drawing, the source does not "
                                "annotate it, and its shape does not settle it")

        ln.evidence.append(Evidence("WALL_IDENTITY", {"IDENTITY": ident, "WHY": why}))
        records.append({
            "COMPONENT_REF": ln.component_ref, "FLOOR": ln.floor, "THICKNESS_M": ln.thickness,
            "THICKNESS_FAMILY_M": key, "IDENTITY": ident, "BILLABLE_AS_MASONRY": ident in BILLABLE, "CONFIDENCE": conf,
            "MATERIAL_LENGTH_M": round(ln.material_length if ln.material_length is not None else ln.length, 6),
            "ASPECT_LENGTH_OVER_THICKNESS": None if aspect is None else round(aspect, 4),
            "ASPECT_REQUIRED_FOR_A_WALL": WALL_ASPECT_MIN,
            "THICKNESS_FAMILY_MEMBERS": fam.get("MEMBER_COUNT"), "THICKNESS_FAMILY_PROVED": fam.get("PROVED"),
            "COVERED_BY_CROSSING_WALLS": round(junction_share, 6),
            "DUPLICATE_OF": twin.component_ref if twin is not None else None,
            "ANNOTATION": note or None,
            "EVIDENCE_USED": ["DRAWING_ANNOTATION", "DRAWING_TOPOLOGY", "THICKNESS_FAMILY", "SHAPE"],
            "WHY": why})
    return {"REGISTER": records, "THICKNESS_FAMILIES": fams,
            "FAMILIES_DISCOVERED_FROM": ("the whole source, supplied by the caller" if families
                                         else "the wall lines passed to this call"),
            "COUNTS": {k: sum(1 for r in records if r["IDENTITY"] == k) for k in IDENTITIES},
            "IDENTITIES": list(IDENTITIES), "BILLABLE_IDENTITIES": list(BILLABLE),
            "RULE": "only a band whose identity is established as masonry is billed as masonry; an unresolved "
                    "band is a question, never a quantity"}
