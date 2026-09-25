"""Two questions about a band, kept apart: is it wall geometry, and what is it made of?

Repeated thickness, an elongated shape and sensible topology establish that an object is a WALL.  They say
nothing whatever about what it is built from.  A 200 mm band could be blockwork, a concrete shear wall, a
stud partition or a service duct casing, and those are different bill items at different rates.  Answering both
questions with one classifier means the geometric evidence silently becomes material evidence, and a drawing
that annotates no material at all still produces confident blockwork quantities.

So there are two axes.  Geometry identity comes from the drawing's shapes and topology.  Material identity comes
only from something that states a material: an annotation, a legend, a specification, an owner-confirmed input,
or an active project standard.  A thickness family appearing twice is not material proof, and this module will
not pretend that it is.

A band may be measured as wall geometry with its material unknown.  What it may not do is appear in a masonry
quantity on that basis.
"""

from __future__ import annotations

from engine.qs_core import evidence as EV, geom
from engine.qs_core.entities import (CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG, CONFIDENCE_WEAK,
                                     Evidence, KIND_COLUMN)

# ---------------------------------------------------------------- axis one: is this wall geometry?
CONFIRMED_WALL_GEOMETRY = "CONFIRMED_WALL_GEOMETRY"
WALL_GEOMETRY_CANDIDATE = "WALL_GEOMETRY_CANDIDATE"
NON_WALL_ARTEFACT = "NON_WALL_ARTEFACT"
GEOMETRY_IDENTITIES = (CONFIRMED_WALL_GEOMETRY, WALL_GEOMETRY_CANDIDATE, NON_WALL_ARTEFACT)

# why a band is not wall geometry - kept as a reason, because "artefact" on its own is not a finding
JUNCTION_ARTEFACT = "JUNCTION_ARTEFACT"
DUPLICATED_LINE_ARTEFACT = "DUPLICATED_LINE_ARTEFACT"
COLUMN_OR_STRUCTURE = "COLUMN_OR_STRUCTURE"
ARTEFACT_REASONS = (JUNCTION_ARTEFACT, DUPLICATED_LINE_ARTEFACT, COLUMN_OR_STRUCTURE)

# ---------------------------------------------------------------- axis two: what is it made of?
MASONRY_CONFIRMED = "MASONRY_CONFIRMED"
CONCRETE_CONFIRMED = "CONCRETE_CONFIRMED"
PARTITION_SYSTEM_CONFIRMED = "PARTITION_SYSTEM_CONFIRMED"
MATERIAL_UNKNOWN = "MATERIAL_UNKNOWN"
MATERIAL_IDENTITIES = (MASONRY_CONFIRMED, CONCRETE_CONFIRMED, PARTITION_SYSTEM_CONFIRMED, MATERIAL_UNKNOWN)

# Only these can state a material.  Shape and topology are deliberately absent.
MATERIAL_EVIDENCE_SOURCES = ("DRAWING_ANNOTATION", "DRAWING_LEGEND", "SPECIFICATION",
                             "OWNER_CONFIRMED_PROJECT_INPUT", "ACTIVE_PROJECT_STANDARD")

# A band is billed as masonry only when both axes say so.
BILLABLE_GEOMETRY = (CONFIRMED_WALL_GEOMETRY,)
BILLABLE_MATERIAL = (MASONRY_CONFIRMED,)

# A wall is longer than it is thick.  An object as long as it is wide is a column, a junction or an artefact.
WALL_ASPECT_MIN = 2.0
# A thickness that occurs once in a whole drawing is not a construction standard.
FAMILY_MIN_MEMBERS = 2
# Two lines that occupy the same place are one object drawn twice.
DUPLICATE_SHARE = 0.80
# A junction is covered by the walls that cross there.
JUNCTION_COVERAGE = 0.80


def family_key(thickness, tolerance):
    """The thickness a band belongs to, quantised to the distance the drawing distinguishes."""
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
        f["PROVES_MATERIAL"] = False
        f["WHY_NOT_MATERIAL"] = ("a thickness family says the drawing uses this dimension repeatedly.  It "
                                 "cannot say what the wall is built from, and it is never read as material "
                                 "evidence")
    return {"FAMILIES": dict(sorted(fams.items())), "MIN_MEMBERS_FOR_A_FAMILY": FAMILY_MIN_MEMBERS,
            "DISCOVERED_FROM": "the wall lines of this source alone"}


def _segment_note(line, annotations):
    """What the drawing says about the segments a wall line was assembled from."""
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


def classify_material(ref, note, material_claims, material_map, tolerance, subject=None, revision=None):
    """What is this band made of?  Only a source that states a material may answer.

    `material_claims` maps a component reference to evidence.Claim-like records whose `reference` names the
    document that states the material and whose `detail["MATERIAL"]` names it.  They go through the same
    lifecycle as every other claim, so a superseded specification cannot answer either.
    """
    claims = list(material_claims.get(ref, []) if material_claims else [])
    stated = (note or {}).get("MATERIAL")
    if stated:
        claims = claims + [EV.Claim(1.0, EV.DRAWING_DIMENSION, (note or {}).get("REFERENCE") or f"ANNOTATION::{ref}",
                                    {"MATERIAL": str(stated).upper(),
                                     "EVIDENCE_SOURCE": "DRAWING_ANNOTATION"})]
    eligible = []
    ineligible = []
    for c in claims:
        ok, kind, why = EV.eligibility(c, subject, revision)
        if ok and (c.detail or {}).get("EVIDENCE_SOURCE") in MATERIAL_EVIDENCE_SOURCES:
            eligible.append(c)
        else:
            ineligible.append(dict(c.as_dict(), INELIGIBLE_BECAUSE=(
                kind if not ok else "NOT_A_SOURCE_THAT_CAN_STATE_A_MATERIAL"),
                WHY=(why if not ok else
                     "material may be stated only by an annotation, a legend, a specification, an owner input "
                     "or an active standard")))
    if not eligible:
        return {"MATERIAL_IDENTITY": MATERIAL_UNKNOWN, "MATERIAL_EVIDENCE": None,
                "MATERIAL_INELIGIBLE": ineligible, "CONFIDENCE": CONFIDENCE_NONE,
                "WHY": "no applicable source states what this band is made of; its geometry is measurable and "
                       "its material is a question"}
    best = sorted(eligible, key=lambda c: (EV.rank_of(c.source), str(c.reference)))[0]
    material = str((best.detail or {}).get("MATERIAL", "")).upper()
    identity = material_map.get(material, MATERIAL_UNKNOWN) if material_map else MATERIAL_UNKNOWN
    return {"MATERIAL_IDENTITY": identity,
            "MATERIAL_EVIDENCE": {"MATERIAL": material, "REFERENCE": best.reference, "SOURCE": best.source,
                                  "EVIDENCE_SOURCE": (best.detail or {}).get("EVIDENCE_SOURCE")},
            "MATERIAL_INELIGIBLE": ineligible,
            "CONFIDENCE": CONFIDENCE_PROVEN if identity != MATERIAL_UNKNOWN else CONFIDENCE_NONE,
            "WHY": (f"{best.reference} states this band's material" if identity != MATERIAL_UNKNOWN else
                    f"{best.reference} states a material this source does not map to a bill item")}


def identity_blocks(ident):
    """The open questions a line's own identity raises, in one place.

    Two different consumers need this answer - the dependency graph, which decides which nodes are held up, and
    the quantity rows, which decide which figures may be published.  Working it out twice is how a report comes
    to say that a hundred and twenty-seven rows are blocked and that only thirty-eight lines are, in the same
    document.  One function, one answer, two readers.
    """
    if not ident:
        return []
    geometry, material = ident.get("GEOMETRY_IDENTITY"), ident.get("MATERIAL_IDENTITY")
    if geometry == NON_WALL_ARTEFACT:
        # settled, not open: the drawing answers this one, and the answer is that it is not a wall
        return []
    reasons = []
    if material is not None and material not in BILLABLE_MATERIAL:
        reasons.append({"KIND": "WALL_MATERIAL_NOT_ESTABLISHED", "MATERIAL_IDENTITY": material,
                        "WHY": ident.get("WHY_MATERIAL") or
                               "no applicable source states what this wall is made of, and shape is not "
                               "material evidence"})
    if geometry == WALL_GEOMETRY_CANDIDATE:
        reasons.append({"KIND": "WALL_GEOMETRY_NOT_ESTABLISHED",
                        "WHY": ident.get("WHY_GEOMETRY") or "this band is not established to be a wall"})
    return reasons


def classify_wall_identity(lines, tolerance, annotations=None, families=None, material_claims=None,
                           material_map=None, revision=None, wall_layers=()):
    """Decide what each band IS - as geometry, and separately as material - before anything measures it."""
    annotations = annotations or {}
    material_map = material_map or {}
    # Layers the SOURCE uses for wall lines.  A layer named for walls is the drawing saying "this is a wall",
    # which is geometry evidence of the same kind as a door block is opening evidence.  It says nothing about
    # what the wall is built from, and this module never reads it as material.
    wall_layers = {str(x).upper() for x in (wall_layers or ())}
    fams = families or thickness_families(lines, tolerance)
    records = []

    for ln in sorted(lines, key=lambda c: c.component_ref):
        note = annotations.get(ln.component_ref) or _segment_note(ln, annotations)
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

        # ---------------------------------------------------------- axis one: geometry
        if ln.kind == KIND_COLUMN:
            geometry, reason, gconf = (NON_WALL_ARTEFACT, COLUMN_OR_STRUCTURE,
                                       CONFIDENCE_PROVEN)
            gwhy = "the source draws this as a column, which is structure and not a run of wall"
        elif aspect is not None and aspect < WALL_ASPECT_MIN and junction_share >= JUNCTION_COVERAGE:
            geometry, reason, gconf = NON_WALL_ARTEFACT, JUNCTION_ARTEFACT, CONFIDENCE_STRONG
            gwhy = ("this band is as short as it is thick and lies inside the crossing of walls running the "
                    "other way; it is where two walls meet, and its area is already in them")
        elif twin is not None:
            geometry, reason, gconf = NON_WALL_ARTEFACT, DUPLICATED_LINE_ARTEFACT, CONFIDENCE_STRONG
            gwhy = f"this band occupies the same place as {twin.component_ref}; one object drawn twice"
        elif aspect is not None and aspect < WALL_ASPECT_MIN:
            geometry, reason, gconf = NON_WALL_ARTEFACT, COLUMN_OR_STRUCTURE, CONFIDENCE_WEAK
            gwhy = "this band is as short as it is thick, so whatever it is, it is not a run of wall"
        elif aspect is not None and aspect >= WALL_ASPECT_MIN and (
                fam["PROVED"] or (ln.layer or "").upper() in wall_layers):
            geometry, reason, gconf = CONFIRMED_WALL_GEOMETRY, None, CONFIDENCE_STRONG
            gwhy = ("this band runs far enough to be a wall, and " + (
                "its thickness is one this drawing uses repeatedly" if fam["PROVED"] else
                f"the source draws it on {ln.layer}, a layer it uses for walls"))
        else:
            geometry, reason, gconf = WALL_GEOMETRY_CANDIDATE, None, CONFIDENCE_WEAK
            gwhy = (f"its thickness occurs {fam['MEMBER_COUNT']} time(s) in the whole drawing and its shape "
                    "does not settle whether this is a wall")

        # ---------------------------------------------------------- axis two: material
        subject = {"OBJECT_KIND": "WALL", "THICKNESS_FAMILY_M": key, "FLOOR": ln.floor}
        mat = classify_material(ln.component_ref, note, material_claims, material_map, tolerance,
                                subject=subject, revision=revision)

        billable = geometry in BILLABLE_GEOMETRY and mat["MATERIAL_IDENTITY"] in BILLABLE_MATERIAL
        ln.evidence.append(Evidence("WALL_IDENTITY", {
            "GEOMETRY_IDENTITY": geometry, "MATERIAL_IDENTITY": mat["MATERIAL_IDENTITY"],
            "WHY_GEOMETRY": gwhy, "WHY_MATERIAL": mat["WHY"]}))
        records.append({
            "COMPONENT_REF": ln.component_ref, "FLOOR": ln.floor, "THICKNESS_M": ln.thickness,
            "THICKNESS_FAMILY_M": key,
            "GEOMETRY_IDENTITY": geometry, "GEOMETRY_ARTEFACT_REASON": reason,
            "GEOMETRY_CONFIDENCE": gconf, "WHY_GEOMETRY": gwhy,
            "MATERIAL_IDENTITY": mat["MATERIAL_IDENTITY"], "MATERIAL_EVIDENCE": mat["MATERIAL_EVIDENCE"],
            "MATERIAL_INELIGIBLE": mat["MATERIAL_INELIGIBLE"], "MATERIAL_CONFIDENCE": mat["CONFIDENCE"],
            "WHY_MATERIAL": mat["WHY"],
            "BILLABLE_AS_MASONRY": billable,
            "MATERIAL_LENGTH_M": round(ln.material_length if ln.material_length is not None else ln.length, 6),
            "ASPECT_LENGTH_OVER_THICKNESS": None if aspect is None else round(aspect, 4),
            "ASPECT_REQUIRED_FOR_A_WALL": WALL_ASPECT_MIN,
            "THICKNESS_FAMILY_MEMBERS": fam.get("MEMBER_COUNT"),
            "THICKNESS_FAMILY_PROVED": fam.get("PROVED"),
            "THICKNESS_FAMILY_PROVES_MATERIAL": False,
            "COVERED_BY_CROSSING_WALLS": round(junction_share, 6),
            "DUPLICATE_OF": twin.component_ref if twin is not None else None,
            "ANNOTATION": note or None,
            "GEOMETRY_EVIDENCE_USED": ["DRAWING_TOPOLOGY", "THICKNESS_FAMILY", "SHAPE", "WALL_LAYER"],
            "LAYER": ln.layer,
            "MATERIAL_EVIDENCE_SOURCES_ACCEPTED": list(MATERIAL_EVIDENCE_SOURCES)})

    return {"REGISTER": records, "THICKNESS_FAMILIES": fams,
            "FAMILIES_DISCOVERED_FROM": ("the whole source, supplied by the caller" if families
                                         else "the wall lines passed to this call"),
            "GEOMETRY_COUNTS": {k: sum(1 for r in records if r["GEOMETRY_IDENTITY"] == k)
                                for k in GEOMETRY_IDENTITIES},
            "MATERIAL_COUNTS": {k: sum(1 for r in records if r["MATERIAL_IDENTITY"] == k)
                                for k in MATERIAL_IDENTITIES},
            "BILLABLE_COUNT": sum(1 for r in records if r["BILLABLE_AS_MASONRY"]),
            "GEOMETRY_IDENTITIES": list(GEOMETRY_IDENTITIES),
            "MATERIAL_IDENTITIES": list(MATERIAL_IDENTITIES),
            "ARTEFACT_REASONS": list(ARTEFACT_REASONS),
            "RULE": "geometry identity and material identity are established independently; a band is billed "
                    "as masonry only when the drawing's shapes say it is a wall AND an applicable source says "
                    "what it is made of.  A thickness family is never material evidence"}
