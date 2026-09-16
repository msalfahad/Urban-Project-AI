"""What kind of space this is — on positive evidence, or not at all.

Round 5 called 43 of 57 polygons `VOID_OR_SHAFT`. Every one arrived through
a single branch of the round-2 classifier:

    elif not obs:  role = VOID_OR_SHAFT

All 43 had `obs=0 nested=0 partitions=0 voids=0`, and exactly one of the 43
contained any text at all. They held no label because they were slivers of
sliced rooms — but the branch would be wrong even with perfect walls:

    NOBODY NAMING A SPACE IS NOT EVIDENCE THAT IT IS A VOID.

So `VOID` and `SHAFT` become CLAIMS, and a claim needs evidence:

    an explicit shaft, duct, riser, lift or stair concept
    enclosed with no opening anywhere on its boundary
    the same footprint repeated at the same place on another plan — a
      vertical penetration runs through floors, and a room does not

and the default, when nothing positive is established, is one of

    INTERIOR_SPACE_UNCLASSIFIED
    EXTERIOR_SPACE_UNCLASSIFIED
    SPACE_ROLE_UNRESOLVED

WHAT THIS DOES NOT DO

It does not touch `enclosure_role`, which is round 2's safety gate and
stays exactly as frozen. That gate only ever REFUSES — a site, an envelope,
a super-region or a frame may not release as a room — and round 6 does not
loosen it. This classifier runs beside it and is the role the engine
REPORTS; the trade layer will read this one, because a floor is measured in
an interior space whether or not anyone wrote a name in it.

It is also NOT `engine/space_role`, which is project 1's raster-side role
classifier for topology regions and is untouched.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from engine import architectural_ontology as onto
from engine import cad_profile as cprofile
from engine import interior_exterior as ie

CLASSIFIER = "POSITIVE_EVIDENCE_CAD_SPACE_ROLE_V1"

SPACE_ROLE_UNRESOLVED = "SPACE_ROLE_UNRESOLVED"
INTERIOR_SPACE_UNCLASSIFIED = "INTERIOR_SPACE_UNCLASSIFIED"
INTERIOR_ROOM = "INTERIOR_ROOM"
EXTERIOR_SPACE_UNCLASSIFIED = "EXTERIOR_SPACE_UNCLASSIFIED"
EXTERNAL_SPACE = "EXTERNAL_SPACE"
SHAFT = "SHAFT"
STAIR = "STAIR"
LIFT = "LIFT"
VOID_OR_SHAFT = "VOID_OR_SHAFT_ON_EVIDENCE"

ROLES = (SPACE_ROLE_UNRESOLVED, INTERIOR_SPACE_UNCLASSIFIED, INTERIOR_ROOM,
         EXTERIOR_SPACE_UNCLASSIFIED, EXTERNAL_SPACE, SHAFT, STAIR, LIFT,
         VOID_OR_SHAFT)

INTERIOR_ROLES = (INTERIOR_SPACE_UNCLASSIFIED, INTERIOR_ROOM)
EXTERIOR_ROLES = (EXTERIOR_SPACE_UNCLASSIFIED, EXTERNAL_SPACE)
PENETRATION_ROLES = (SHAFT, STAIR, LIFT, VOID_OR_SHAFT)

# Concepts the frozen vocabulary already carries. Nothing is added here.
SHAFT_CONCEPTS = frozenset({"SHAFT"})
STAIR_CONCEPTS = frozenset({"STAIR"})
LIFT_CONCEPTS = frozenset({"LIFT"})

EV_SHAFT_SEMANTICS = "A_SHAFT_DUCT_OR_RISER_CONCEPT_SITS_IN_IT"
EV_STAIR_SEMANTICS = "A_STAIR_CONCEPT_SITS_IN_IT"
EV_LIFT_SEMANTICS = "A_LIFT_CONCEPT_SITS_IN_IT"
EV_ROOM_SEMANTICS = "A_ROOM_CONCEPT_SITS_IN_IT"
EV_NO_OPENING = "NO_OPENING_ANYWHERE_ON_ITS_BOUNDARY"
EV_REPEATED_ACROSS_PLANS = "THE_SAME_FOOTPRINT_APPEARS_ON_ANOTHER_PLAN"
EV_INTERIOR = "ESTABLISHED_INTERIOR"
EV_EXTERIOR = "ESTABLISHED_EXTERIOR"
EV_NOTHING = "NOTHING_POSITIVE_WAS_ESTABLISHED"

EVIDENCE = (EV_SHAFT_SEMANTICS, EV_STAIR_SEMANTICS, EV_LIFT_SEMANTICS,
            EV_ROOM_SEMANTICS, EV_NO_OPENING, EV_REPEATED_ACROSS_PLANS,
            EV_INTERIOR, EV_EXTERIOR, EV_NOTHING)

# A vertical penetration nobody named needs TWO independent positive signs,
# and one of them must be the cross-plan repetition — being shut is not by
# itself a claim about what is above or below.
UNNAMED_PENETRATION_NEEDS = (EV_NO_OPENING, EV_REPEATED_ACROSS_PLANS)

# Two footprints are the same footprint when they agree to within the
# smallest separation this engine will call a wall. The profile's own
# constant; nothing new is introduced.
FOOTPRINT_TOL_MM = cprofile.MIN_WALL_THICKNESS_MM


@dataclass(frozen=True)
class RoleVerdict:
    space_id: str
    region_id: str
    role: str
    interior_exterior: str
    evidence: tuple = ()
    concepts: tuple = ()
    has_identity: bool = False
    no_opening_on_any_boundary: bool = False
    repeated_on_plans: tuple = ()
    why: str = ""

    @property
    def is_interior(self) -> bool:
        return self.role in INTERIOR_ROLES

    @property
    def is_exterior(self) -> bool:
        return self.role in EXTERIOR_ROLES

    @property
    def is_vertical_penetration(self) -> bool:
        return self.role in PENETRATION_ROLES

    def record(self) -> dict:
        return {
            "space_id": self.space_id,
            "drawing_region_id": self.region_id,
            "SPACE_ROLE": self.role,
            "INTERIOR_EXTERIOR": self.interior_exterior,
            "is_interior": self.is_interior,
            "is_exterior": self.is_exterior,
            "is_vertical_penetration": self.is_vertical_penetration,
            "has_readable_identity": self.has_identity,
            "no_opening_on_any_boundary": self.no_opening_on_any_boundary,
            "repeated_on_plans": list(self.repeated_on_plans),
            "concepts_observed": list(self.concepts),
            "evidence": list(self.evidence),
            "why": self.why,
            "never": ("an unnamed space is never called a void. VOID and "
                      "SHAFT are claims and they need evidence"),
        }


@dataclass
class RoleReport:
    verdicts: list = field(default_factory=list)
    envelopes: dict = field(default_factory=dict)
    thickness_modes: tuple = ()
    notes: dict = field(default_factory=dict)

    # Re-exported so a caller can name a role without importing the module.
    SHAFT = SHAFT
    VOID_OR_SHAFT = VOID_OR_SHAFT
    INTERIOR_SPACE_UNCLASSIFIED = INTERIOR_SPACE_UNCLASSIFIED

    def counts(self) -> dict:
        return {
            "spaces_classified": len(self.verdicts),
            "by_role": dict(Counter(v.role for v in self.verdicts
                                    ).most_common()),
            "by_interior_exterior": dict(Counter(
                v.interior_exterior for v in self.verdicts).most_common()),
            "interior": sum(1 for v in self.verdicts if v.is_interior),
            "exterior": sum(1 for v in self.verdicts if v.is_exterior),
            "vertical_penetrations": sum(
                1 for v in self.verdicts if v.is_vertical_penetration),
            "no_opening_anywhere": sum(
                1 for v in self.verdicts if v.no_opening_on_any_boundary),
            "regions_with_an_envelope": sum(
                1 for m in self.envelopes.values() if m.has_envelope),
        }

    def record(self, *, limit: int = 40) -> dict:
        return {
            "classifier": CLASSIFIER,
            "CAD_SPACE_ROLE_HASH": classifier_hash(),
            "INTERIOR_EXTERIOR_HASH": ie.model_hash(),
            "roles": list(ROLES),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "envelopes": [m.record() for m in self.envelopes.values()],
            "verdicts": [v.record() for v in self.verdicts[:limit]],
            "what_replaced_what": (
                "round 2's `elif not obs: VOID_OR_SHAFT` produced 43 of "
                "P7757's 57 polygons. It is not consulted here. The round-2 "
                "classifier still runs as the ROOM-RELEASE safety gate and "
                "is unchanged"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "CLASSIFIER": CLASSIFIER,
        "UNNAMED_PENETRATION_NEEDS": list(UNNAMED_PENETRATION_NEEDS),
        "FOOTPRINT_TOL_MM": FOOTPRINT_TOL_MM,
        "why": {
            "positive_evidence_only": (
                "VOID and SHAFT are claims about what is above and below a "
                "space. Nobody writing a name in it is not such a claim"),
            "FOOTPRINT_TOL_MM": (
                "the profile's smallest wall separation. Two footprints "
                "agreeing to less than the thinnest thing this engine "
                "calls a wall are the same footprint"),
            "no_area_rule": (
                "no role here is decided by how big a space is"),
        },
    }


def classifier_hash() -> str:
    parts = [CLASSIFIER, "|".join(ROLES), "|".join(EVIDENCE),
             "|".join(UNNAMED_PENETRATION_NEEDS), str(FOOTPRINT_TOL_MM),
             ie.model_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _footprints(rows, regions):
    """Group faces by their footprint in REGION-LOCAL coordinates.

    A shaft sits at the same place on every floor plan of a building. Two
    faces whose local extents agree are the same opening through the slab —
    a room's footprint repeating exactly on another plan is the same claim.
    """
    from shapely.wkt import loads

    local = {}
    for r in rows:
        if not r.enclosure or not r.enclosure.polygon_wkt:
            continue
        reg = None
        for cand in (regions.regions if regions else ()):
            if cand.region_id == r.region_id:
                reg = cand
                break
        if reg is None:
            continue
        try:
            x0, y0, x1, y1 = loads(r.enclosure.polygon_wkt).bounds
        except Exception:      # noqa: BLE001
            continue
        local[r.space_id] = (r.region_id,
                             x0 - reg.x0, y0 - reg.y0,
                             x1 - reg.x0, y1 - reg.y0)
    repeats = defaultdict(list)
    ids = sorted(local)
    for i, a in enumerate(ids):
        ra, *ba = local[a]
        for b in ids[i + 1:]:
            rb, *bb = local[b]
            if ra == rb:
                continue
            if all(abs(u - v) <= FOOTPRINT_TOL_MM for u, v in zip(ba, bb)):
                repeats[a].append(b)
                repeats[b].append(a)
    return repeats


def classify(rows, *, regions=None, envelopes=None, identity_concepts=None,
             thickness_modes=(), semantic_observations=()) -> RoleReport:
    """Give every measured space a role, and never guess a void.

    `envelopes` maps region id to an `interior_exterior.EnvelopeModel`.
    `identity_concepts` maps space id to the ontology concepts observed in
    it, so this module reads the frozen vocabulary rather than any string.
    """
    rep = RoleReport()
    rep.envelopes = dict(envelopes or {})
    rep.thickness_modes = tuple(thickness_modes)
    concepts_of = dict(identity_concepts or {})
    repeats = _footprints(rows, regions)

    for r in rows:
        model = rep.envelopes.get(r.region_id)
        rows_concepts = concepts_of.get(r.space_id, ())
        concept_names = tuple(c for c, _cls in rows_concepts)
        concept_classes = tuple(cls for _c, cls in rows_concepts)
        pt = r.seed_mm
        if model is not None:
            inex = ie.classify_point(
                model, pt[0], pt[1], concepts=concept_classes,
                space_id=r.space_id,
                reachable_from_interior=bool(r.boundary_openings))
        else:
            inex = ie.Verdict(r.space_id, r.region_id, ie.UNRESOLVED,
                              (ie.EV_NO_ENVELOPE,),
                              "no envelope model for this region")

        ev = []
        if concept_names:
            ev.append(EV_ROOM_SEMANTICS)
        if SHAFT_CONCEPTS & set(concept_names):
            ev.append(EV_SHAFT_SEMANTICS)
        if STAIR_CONCEPTS & set(concept_names):
            ev.append(EV_STAIR_SEMANTICS)
        if LIFT_CONCEPTS & set(concept_names):
            ev.append(EV_LIFT_SEMANTICS)
        no_opening = bool(r.is_complete and not r.boundary_openings)
        if no_opening:
            ev.append(EV_NO_OPENING)
        repeated = tuple(repeats.get(r.space_id, ()))
        if repeated:
            ev.append(EV_REPEATED_ACROSS_PLANS)
        if inex.verdict == ie.INTERIOR:
            ev.append(EV_INTERIOR)
        elif inex.verdict == ie.EXTERIOR:
            ev.append(EV_EXTERIOR)

        # ---- the rules, named and in order ---------------------------
        if EV_SHAFT_SEMANTICS in ev:
            role = SHAFT
            why = ("a shaft, duct or riser concept sits in it — the "
                   "architect's own statement about what it is")
        elif EV_STAIR_SEMANTICS in ev:
            role = STAIR
            why = "a stair concept sits in it"
        elif EV_LIFT_SEMANTICS in ev:
            role = LIFT
            why = "a lift concept sits in it"
        elif inex.verdict == ie.EXTERIOR:
            role = (EXTERNAL_SPACE if ie.EV_EXTERNAL_SEMANTICS in
                    inex.evidence else EXTERIOR_SPACE_UNCLASSIFIED)
            why = inex.why
        elif all(t in ev for t in UNNAMED_PENETRATION_NEEDS) and \
                not concept_names:
            role = VOID_OR_SHAFT
            why = ("nothing names it, nothing opens onto it, and the same "
                   "footprint appears on another plan. That is a vertical "
                   "penetration on evidence — which of void or shaft is "
                   "NOT established and is not guessed")
        elif inex.verdict == ie.INTERIOR:
            role = INTERIOR_ROOM if concept_names else \
                INTERIOR_SPACE_UNCLASSIFIED
            why = (inex.why + (". A room concept names it"
                               if concept_names else
                               ". Nobody named it, which says nothing about "
                               "what it is"))
        else:
            if concept_names:
                role = INTERIOR_ROOM
                why = ("a room concept sits in it, though which side of "
                       "the building it is on was not established")
            else:
                role = SPACE_ROLE_UNRESOLVED
                ev.append(EV_NOTHING)
                why = ("nothing positive was established: no envelope in "
                       "this region, no concept inside it, and no "
                       "cross-plan repetition. UNRESOLVED is the answer")

        rep.verdicts.append(RoleVerdict(
            space_id=r.space_id, region_id=r.region_id, role=role,
            interior_exterior=inex.verdict, evidence=tuple(ev),
            concepts=concept_names, has_identity=bool(concept_names),
            no_opening_on_any_boundary=no_opening,
            repeated_on_plans=repeated, why=why))

    # ---- the ground between the site line and the fabric ---------------
    #
    # Not room candidates, and they never were. A floor trade has to KNOW
    # about them to leave them out, so they are classified rather than
    # dropped — which is the only way the round-5 garden strip could ever
    # have been recognised for what it is.
    from shapely.geometry import Point
    from shapely.wkt import loads

    obs = list(semantic_observations or ())
    for model in rep.envelopes.values():
        for face in model.exterior_faces:
            x, y = face["point"]
            try:
                shape = loads(face["wkt"])
            except Exception:       # noqa: BLE001
                shape = None
            inside = [o for o in obs
                      if shape is not None and shape.contains(
                          Point(getattr(o, "x", 0.0), getattr(o, "y", 0.0)))]
            classes = tuple(
                onto.classify_term(getattr(o, "text", "")).concept_class
                for o in inside)
            names = tuple(
                onto.classify_term(getattr(o, "text", "")).concept
                for o in inside
                if onto.classify_term(getattr(o, "text", "")).is_known)
            verdict = ie.classify_point(model, x, y, concepts=classes,
                                        space_id=face["face_id"])
            role = (EXTERNAL_SPACE
                    if ie.EV_EXTERNAL_SEMANTICS in verdict.evidence
                    else EXTERIOR_SPACE_UNCLASSIFIED)
            rep.verdicts.append(RoleVerdict(
                space_id=face["face_id"], region_id=face["region_id"],
                role=role, interior_exterior=verdict.verdict,
                evidence=tuple(verdict.evidence) + (EV_EXTERIOR,),
                concepts=names, has_identity=bool(names),
                why=(face["why"] + ". " + verdict.why)))

    rep.notes["unknown_is_not_void"] = (
        "an unnamed bounded space is INTERIOR_SPACE_UNCLASSIFIED where the "
        "envelope puts it inside, EXTERIOR_SPACE_UNCLASSIFIED where it puts "
        "it outside, and SPACE_ROLE_UNRESOLVED where the drawing gives no "
        "envelope at all. None of those is a void")
    rep.notes["no_opening_is_a_flag"] = (
        "a space with no opening anywhere on its boundary is reported. On "
        "its own it decides nothing — a room whose door this engine could "
        "not grade looks exactly the same")
    return rep
