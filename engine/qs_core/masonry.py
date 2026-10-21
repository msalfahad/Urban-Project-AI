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


# ---------------------------------------------------------------- the scope a material claim applies to
#
# R6 asked one material question per THICKNESS FAMILY and assumed one answer covered every wall of that
# thickness.  That is the same unsupported inference the round before had just removed from the other
# direction: thickness does not prove material, and it does not delimit material either.  External walls,
# internal partitions, structural walls and service enclosures are routinely drawn at the same thickness and
# built of different things.
#
# So a material claim carries an explicit applicability scope, stated as attributes the SOURCE distinguishes,
# and it answers a band only where every attribute it names matches that band.  A claim with no scope at all
# may answer project-wide only when the evidence itself says that is its scope.
SCOPE_ATTRIBUTES = ("WALL_TYPE_CODE", "LAYER", "FLOOR", "THICKNESS_FAMILY_M", "ROLE", "TAG_SET")
SCOPE_STATED = "SCOPE_STATED_BY_THE_EVIDENCE"
SCOPE_PROJECT_WIDE = "PROJECT_WIDE_AND_THE_EVIDENCE_SAYS_SO"
SCOPE_NOT_STATED = "SCOPE_NOT_STATED_SO_IT_CANNOT_PROPAGATE"


def band_attributes(line, family_key_value, note=None):
    """The attributes of a band a material claim may be scoped against.  All of them come from the source."""
    note = note or {}
    return {
        "WALL_TYPE_CODE": note.get("WALL_TYPE_CODE"),
        "LAYER": None if line.layer is None else str(line.layer).upper(),
        "FLOOR": line.floor,
        "THICKNESS_FAMILY_M": family_key_value,
        "ROLE": note.get("ROLE"),
        "TAG_SET": note.get("TAG_SET"),
    }


def scope_matches(scope, attrs):
    """Does this claim's stated scope cover this band?  Every attribute it names has to match."""
    scope = dict(scope or {})
    stated = bool(scope.pop(SCOPE_STATED, False))
    named = {k: v for k, v in scope.items() if k in SCOPE_ATTRIBUTES and v is not None}
    if not named:
        # an unscoped claim answers everything only if the evidence itself says it is project-wide
        return (stated, SCOPE_PROJECT_WIDE if stated else SCOPE_NOT_STATED)
    for k, v in sorted(named.items()):
        got = attrs.get(k)
        if isinstance(v, (list, tuple, set)):
            if got not in set(v):
                return (False, f"SCOPE_{k}_DOES_NOT_COVER_{got!r}")
        elif got != v:
            return (False, f"SCOPE_{k}_IS_{v!r}_AND_THIS_BAND_IS_{got!r}")
    return (True, "SCOPE_" + "_AND_".join(f"{k}={named[k]!r}" for k in sorted(named)))


def scope_key(attrs):
    """The group a material question is asked about: the attributes the source distinguishes, all of them.

    This is a QUESTION GROUP, not a wall-type identity.  Two bands in one group share every attribute the
    drawing states about them, which is why one answer can plausibly cover both - and the answer still only
    propagates as far as its own stated scope.
    """
    parts = [f"{k}={attrs.get(k)!r}" for k in ("FLOOR", "LAYER", "THICKNESS_FAMILY_M")]
    return "MATERIAL_SCOPE::" + "::".join(parts)


def applicable_scoped_claims(scopes, attrs):
    """Split the caller's scoped material claims into the ones that cover this band and the ones that do not."""
    applies, rejected = [], []
    for c in scopes or ():
        ok, why = scope_matches(getattr(c, "scope", None) or (c.detail or {}).get("SCOPE"), attrs)
        (applies if ok else rejected).append(
            c if ok else dict(c.as_dict(), OUT_OF_SCOPE_BECAUSE=why))
    return applies, rejected


def classify_material(ref, note, material_claims, material_map, tolerance, subject=None, revision=None,
                      scoped_claims=()):
    """What is this band made of?  Only a source that states a material may answer.

    `material_claims` maps a component reference to evidence.Claim-like records whose `reference` names the
    document that states the material and whose `detail["MATERIAL"]` names it.  They go through the same
    lifecycle as every other claim, so a superseded specification cannot answer either.
    """
    claims = list(material_claims.get(ref, []) if material_claims else []) + list(scoped_claims or ())
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
                           material_map=None, revision=None, wall_layers=(), material_scopes=None,
                           exclusion_evidence=None):
    """Decide what each band IS - as geometry, and separately as material - before anything measures it."""
    annotations = annotations or {}
    material_map = material_map or {}
    # Layers the SOURCE uses for wall lines.  A layer named for walls is the drawing saying "this is a wall",
    # which is geometry evidence of the same kind as a door block is opening evidence.  It says nothing about
    # what the wall is built from, and this module never reads it as material.
    wall_layers = {str(x).upper() for x in (wall_layers or ())}
    # Positive source evidence that a band is NOT a wall: the drawing names it a column, or a caller-supplied
    # record says so.  Nothing is excluded from the trade on shape alone.
    exclusion_evidence = exclusion_evidence or {}
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
        #
        # Exclusion is permanent and silent: an excluded band leaves the trade and asks nobody anything.  It
        # therefore needs POSITIVE evidence that the object is not a wall - the source naming it a column, the
        # same object drawn twice, or a junction whose area is already inside the walls that cross there.
        # Shortness is not that evidence.  A pier, a wall return, a jamb nib and an isolated fragment of wall
        # are all shorter than twice their thickness, and R6 excluded twenty-three bands on a wall layer for
        # exactly that reason, on WEAK confidence, without asking anyone.
        named_column = exclusion_evidence.get(ln.component_ref) or {}
        on_a_wall_layer = (ln.layer or "").upper() in wall_layers
        if ln.kind == KIND_COLUMN or named_column.get("KIND") == COLUMN_OR_STRUCTURE:
            geometry, reason, gconf = (NON_WALL_ARTEFACT, COLUMN_OR_STRUCTURE,
                                       CONFIDENCE_PROVEN)
            gwhy = ("the source draws this as a column, which is structure and not a run of wall"
                    if ln.kind == KIND_COLUMN else
                    f"the source names this a column ({named_column.get('REFERENCE')})")
        elif aspect is not None and aspect < WALL_ASPECT_MIN and junction_share >= JUNCTION_COVERAGE:
            geometry, reason, gconf = NON_WALL_ARTEFACT, JUNCTION_ARTEFACT, CONFIDENCE_STRONG
            gwhy = ("this band is as short as it is thick and lies inside the crossing of walls running the "
                    "other way; it is where two walls meet, and its area is already in them")
        elif twin is not None:
            geometry, reason, gconf = NON_WALL_ARTEFACT, DUPLICATED_LINE_ARTEFACT, CONFIDENCE_STRONG
            gwhy = f"this band occupies the same place as {twin.component_ref}; one object drawn twice"
        elif aspect is not None and aspect < WALL_ASPECT_MIN:
            geometry, reason, gconf = WALL_GEOMETRY_CANDIDATE, None, CONFIDENCE_WEAK
            gwhy = ("this band is shorter than twice its thickness, which is true of a pier, a wall return, a "
                    "jamb nib and an isolated fragment of wall as well as of a column; nothing in the source "
                    "settles which"
                    + (f", and the source draws it on {ln.layer}, a layer it uses for walls"
                       if on_a_wall_layer else ""))
        elif aspect is not None and aspect >= WALL_ASPECT_MIN and (
                fam["PROVED"] or on_a_wall_layer):
            geometry, reason, gconf = CONFIRMED_WALL_GEOMETRY, None, CONFIDENCE_STRONG
            gwhy = ("this band runs far enough to be a wall, and " + (
                "its thickness is one this drawing uses repeatedly" if fam["PROVED"] else
                f"the source draws it on {ln.layer}, a layer it uses for walls"))
        else:
            geometry, reason, gconf = WALL_GEOMETRY_CANDIDATE, None, CONFIDENCE_WEAK
            gwhy = (f"its thickness occurs {fam['MEMBER_COUNT']} time(s) in the whole drawing and its shape "
                    "does not settle whether this is a wall")

        # ---------------------------------------------------------- axis two: material
        attrs = band_attributes(ln, key, note)
        scoped, out_of_scope = applicable_scoped_claims(material_scopes, attrs)
        subject = dict(attrs, OBJECT_KIND="WALL")
        mat = classify_material(ln.component_ref, note, material_claims, material_map, tolerance,
                                subject=subject, revision=revision, scoped_claims=scoped)
        mat["MATERIAL_INELIGIBLE"] = list(mat["MATERIAL_INELIGIBLE"]) + out_of_scope

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
            "THICKNESS_FAMILY_IS_NOT_A_WALL_TYPE": ("walls of one thickness may be built of different things; "
                                                    "this family groups a QUESTION, never a material"),
            "MATERIAL_SCOPE_KEY": scope_key(attrs),
            "MATERIAL_SCOPE_ATTRIBUTES": attrs,
            "MATERIAL_SCOPES_OUT_OF_SCOPE": [c.get("OUT_OF_SCOPE_BECAUSE") for c in out_of_scope],
            "ON_A_SOURCE_WALL_LAYER": on_a_wall_layer,
            "EXCLUDED_ON": (None if geometry != NON_WALL_ARTEFACT else reason),
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



def material_scope_register(records, claims_by_scope=None):
    """Every distinct question group, what is in it, and how far an answer about it would travel."""
    groups = {}
    for r in records:
        g = groups.setdefault(r["MATERIAL_SCOPE_KEY"], {
            "SCOPE_KEY": r["MATERIAL_SCOPE_KEY"],
            "ATTRIBUTES": r["MATERIAL_SCOPE_ATTRIBUTES"],
            "MEMBERS": [], "MATERIAL_IDENTITIES": set(), "ANSWERED_BY": None})
        g["MEMBERS"].append(r["COMPONENT_REF"])
        g["MATERIAL_IDENTITIES"].add(r["MATERIAL_IDENTITY"])
        if r["MATERIAL_EVIDENCE"]:
            g["ANSWERED_BY"] = r["MATERIAL_EVIDENCE"].get("REFERENCE")
    out = []
    for key in sorted(groups):
        g = groups[key]
        out.append({
            "SCOPE_KEY": key, "ATTRIBUTES": g["ATTRIBUTES"], "MEMBERS": sorted(g["MEMBERS"]),
            "MEMBER_COUNT": len(g["MEMBERS"]),
            "MATERIAL_IDENTITIES_IN_THIS_GROUP": sorted(g["MATERIAL_IDENTITIES"]),
            "ANSWERED_BY": g["ANSWERED_BY"],
            "ANSWER_PROPAGATES": ("only as far as the answering evidence states its own scope; membership of "
                                  "this group is not itself a reason to propagate"),
            "OFFERED_CLAIM": (claims_by_scope or {}).get(key),
        })
    return {
        "GROUPS": out,
        "GROUP_COUNT": len(out),
        "SCOPE_ATTRIBUTES": list(SCOPE_ATTRIBUTES),
        "WHAT_A_GROUP_IS": "a set of bands sharing every attribute the source states about them, so that one "
                           "question can sensibly be asked about all of them",
        "WHAT_A_GROUP_IS_NOT": "a wall type.  Walls of one thickness, on one layer, on one floor may still be "
                               "built of different things, and only the answering document may say otherwise",
        "RULE": "a material answer applies to a band when the answering evidence's own stated scope covers "
                "that band's attributes; an unscoped answer propagates project-wide only when the evidence "
                "says that is its scope",
    }
