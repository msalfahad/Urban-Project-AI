"""Is this stretch of wall still there when nobody drew it?

There are five honest answers and the default is the unhelpful one.

    ESTABLISHED_CONTINUATION   something physically accounts for the span:
                               one face runs across it, or another wall's
                               material occupies it
    SUPPORTED_CONTINUATION     several independent signs agree that the
                               wall continues, but nothing occupies it
    OPENING_INTERRUPTION       a door, a window or a supported archway is
                               there. Round 4 already closes this, with a
                               VIRTUAL boundary and zero material
    NO_CONTINUATION            the wall ends. There is nothing beyond it
    UNRESOLVED_GAP             none of the above is established

    THERE IS NO `bridge_collinear_gap()` IN THIS MODULE AND THERE MAY NOT
    BE ONE.

§8 is the load-bearing rule: if the evidence cannot tell an opening from a
missing face from a drafting break from an open-plan connection from a wall
that simply stops, the answer is UNRESOLVED_GAP. **False subdivision is as
dangerous as false merging** — one invents a room, the other loses one, and
both are wrong in a way a quantity surveyor would have to unpick by hand.

EVIDENCE IS NAMED AND NEVER AVERAGED

Every token below is recorded on every span, and the verdict comes from
STATED RULES over those tokens. No token has a weight, nothing is summed,
and no score crosses a threshold.

TWO AUTHORITIES, NEVER ONE (§6)

A span this module recovers can be strong enough to say TWO ROOMS ARE
SEPARATE and still not strong enough to let anybody measure blockwork
across it. So every span carries both:

    TOPOLOGY_AUTHORITY   may this close a room boundary
    MATERIAL_AUTHORITY   may blockwork, plaster, paint or ceramic be taken

`topology = VALIDATED, material = CANDIDATE` is a normal, expected result.
It is what stops geometry repair from quietly creating a bill of
quantities.

OPENINGS ARE NEGATIVE EVIDENCE (§7)

Round 4's doors and windows now work against recovery. **No material span
is ever recovered across a validated opening.** For room topology the
portal already supplies a virtual boundary; for material the opening stays
absent, which is what it is.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_openings as op
from engine import physical_wall as pw

MODEL = "NAMED_EVIDENCE_PARTITION_CONTINUITY_V1"

# ---------------------------------------------------------------- verdicts
ESTABLISHED = "ESTABLISHED_CONTINUATION"
SUPPORTED = "SUPPORTED_CONTINUATION"
OPENING_INTERRUPTION = "OPENING_INTERRUPTION"
UNRESOLVED_GAP = "UNRESOLVED_GAP"
NO_CONTINUATION = "NO_CONTINUATION"

VERDICTS = (ESTABLISHED, SUPPORTED, OPENING_INTERRUPTION, UNRESOLVED_GAP,
            NO_CONTINUATION)

# ------------------------------------------------------------- authorities
TOPOLOGY_VALIDATED = "TOPOLOGY_VALIDATED"
TOPOLOGY_SUPPORTED = "TOPOLOGY_SUPPORTED"
TOPOLOGY_PORTAL = "TOPOLOGY_FROM_A_VALIDATED_PORTAL"
TOPOLOGY_NONE = "TOPOLOGY_NOT_ESTABLISHED"

MATERIAL_ESTABLISHED = "MATERIAL_ESTABLISHED"
MATERIAL_CANDIDATE = "MATERIAL_CANDIDATE"
MATERIAL_ANOTHER_WALL = "MATERIAL_BELONGS_TO_ANOTHER_WALL"
MATERIAL_ABSENT = "MATERIAL_ABSENT_AT_AN_OPENING"
MATERIAL_NONE = "MATERIAL_NOT_ESTABLISHED"

WHAT_EACH_AUTHORITY_PERMITS = {
    TOPOLOGY_VALIDATED: "it may close a room boundary, and a space closed "
                        "with it may be released",
    TOPOLOGY_SUPPORTED: "it may close a room boundary for measurement, and "
                        "a space that needs it is DIAGNOSTIC — the "
                        "subdivision is reported, not released",
    TOPOLOGY_PORTAL: "round 4's virtual boundary already closes this. "
                     "Nothing is recovered here",
    TOPOLOGY_NONE: "it closes nothing. The face stays as it is",
    MATERIAL_ESTABLISHED: "both faces are drawn. Blockwork may be measured",
    MATERIAL_CANDIDATE: "the wall appears to continue, and one of its faces "
                        "is not drawn. A quantity taken from here would be "
                        "measuring a line nobody drew",
    MATERIAL_ANOTHER_WALL: "the material across this span belongs to the "
                           "wall that crosses it, and is measured there. "
                           "Counting it twice is the error this prevents",
    MATERIAL_ABSENT: "there is no material across an opening",
    MATERIAL_NONE: "nothing establishes material here",
}

# ---------------------------------------------------------------- evidence
EV_A_COLLINEAR = "A_COLLINEAR_RUNS_FLANK_THE_SPAN"
EV_B_THICKNESS = "B_WALL_THICKNESS_IS_SUPPORTED_EITHER_SIDE"
EV_C_OPPOSITE_FACE = "C_THE_OPPOSITE_FACE_RUNS_ACROSS_THE_SPAN"
EV_D_T_JUNCTION = "D_ANOTHER_WALL_MEETS_THIS_ONE_INSIDE_THE_SPAN"
EV_E_CROSSES = "E_ANOTHER_ESTABLISHED_WALL_OCCUPIES_THE_SPAN"
EV_F_HOSTS_OPENING = "F_A_SUPPORTED_OPENING_OCCUPIES_THE_SPAN"
EV_G_REPEATED_BAND = "G_THE_SAME_WALL_BAND_REPEATS_BEYOND_THE_SPAN"
EV_H_MATCHING_ENDS = "H_THE_FLANKING_RUNS_END_AT_MATCHING_STATIONS"
EV_I_THROUGH_OPENING = "I_THE_WALL_CONTINUES_BEYOND_A_VALIDATED_OPENING"
EV_J_SAME_ENTITY = "J_THE_FLANKING_RUNS_SHARE_CAD_ENTITY_PROVENANCE"

EVIDENCE = (EV_A_COLLINEAR, EV_B_THICKNESS, EV_C_OPPOSITE_FACE,
            EV_D_T_JUNCTION, EV_E_CROSSES, EV_F_HOSTS_OPENING,
            EV_G_REPEATED_BAND, EV_H_MATCHING_ENDS, EV_I_THROUGH_OPENING,
            EV_J_SAME_ENTITY)

# WHICH TOKENS MAY RAISE A VERDICT, AND WHICH MAY NOT.
#
# A, B, G and H are all consequences of ONE fact — that runs of this wall
# exist either side of the span. They are recorded because they are true,
# and they may never raise a verdict on their own, because a rule resting
# on them IS `bridge_collinear_gap()` under another name. A first version
# of this module let them through and promptly "recovered" a plain
# unexplained gap.
#
# Only these say something the collinearity does not:
#
#   E  another established wall's MATERIAL occupies the span
#   D  another wall TERMINATES into the span — its end is the reason this
#      one is broken there
#
# and they are applied as named rules, not counted or weighted.
RAISING_TOKENS = (EV_E_CROSSES, EV_D_T_JUNCTION)
CONSEQUENCES_OF_COLLINEARITY = (EV_A_COLLINEAR, EV_B_THICKNESS,
                                EV_G_REPEATED_BAND, EV_H_MATCHING_ENDS,
                                EV_J_SAME_ENTITY)

# How much of a span an opening must occupy to BE that span's explanation.
# Not a tolerance: an opening that covers a gap end to end is that gap.
COVERS_FRACTION = 1.0


@dataclass(frozen=True)
class Continuation:
    """One span of one wall, and whether the wall is there across it."""

    span_id: str
    wall_id: str
    region_id: str
    axis: str
    lo: float
    hi: float
    coverage: str
    verdict: str
    topology_authority: str
    material_authority: str
    evidence: tuple = ()
    missing_face_mm: float | None = None
    faces_mm: tuple = ()
    why: str = ""

    @property
    def length_mm(self) -> float:
        return self.hi - self.lo

    @property
    def may_subdivide(self) -> bool:
        return self.topology_authority in (TOPOLOGY_VALIDATED,
                                           TOPOLOGY_SUPPORTED)

    @property
    def may_release(self) -> bool:
        return self.topology_authority == TOPOLOGY_VALIDATED

    def record(self) -> dict:
        return {
            "span_id": self.span_id,
            "wall_id": self.wall_id,
            "drawing_region_id": self.region_id,
            "axis": self.axis,
            "interval_mm": [round(self.lo, 2), round(self.hi, 2)],
            "length_mm": round(self.length_mm, 1),
            "coverage": self.coverage,
            "verdict": self.verdict,
            "TOPOLOGY_AUTHORITY": self.topology_authority,
            "MATERIAL_AUTHORITY": self.material_authority,
            "topology_permits": WHAT_EACH_AUTHORITY_PERMITS[
                self.topology_authority],
            "material_permits": WHAT_EACH_AUTHORITY_PERMITS[
                self.material_authority],
            "may_subdivide_a_face": self.may_subdivide,
            "may_be_released_through": self.may_release,
            "evidence": list(self.evidence),
            "recovered_on_face_mm": (None if self.missing_face_mm is None
                                     else round(self.missing_face_mm, 2)),
            "wall_faces_mm": [round(v, 2) for v in self.faces_mm],
            "why": self.why,
        }


@dataclass
class ContinuityReport:
    region_id: str = ""
    spans: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def by_verdict(self) -> dict:
        return dict(Counter(s.verdict for s in self.spans).most_common())

    def recovered(self) -> list:
        return [s for s in self.spans if s.may_subdivide]

    def counts(self) -> dict:
        return {
            "spans_examined": len(self.spans),
            "by_verdict": self.by_verdict(),
            "established_continuations": sum(
                1 for s in self.spans if s.verdict == ESTABLISHED),
            "supported_continuations": sum(
                1 for s in self.spans if s.verdict == SUPPORTED),
            "opening_interruptions": sum(
                1 for s in self.spans if s.verdict == OPENING_INTERRUPTION),
            "unresolved_gaps": sum(
                1 for s in self.spans if s.verdict == UNRESOLVED_GAP),
            "no_continuation": sum(
                1 for s in self.spans if s.verdict == NO_CONTINUATION),
            "may_subdivide": len(self.recovered()),
            "may_release_through": sum(1 for s in self.spans
                                       if s.may_release),
            "by_material_authority": dict(Counter(
                s.material_authority for s in self.spans).most_common()),
            "recovered_length_m": round(sum(
                s.length_mm for s in self.recovered()) / 1000, 3),
        }

    def record(self, *, limit: int = 40) -> dict:
        return {
            "model": MODEL,
            "PARTITION_CONTINUITY_HASH": continuity_hash(),
            "drawing_region_id": self.region_id,
            "verdicts": list(VERDICTS),
            "evidence_considered": list(EVIDENCE),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "spans": [s.record() for s in self.spans[:limit]],
            "the_two_authorities": {
                "TOPOLOGY_AUTHORITY": "may this close a room boundary",
                "MATERIAL_AUTHORITY": "may blockwork be taken across it",
                "why_they_are_separate": (
                    "geometry repair must not quietly create a bill of "
                    "quantities. `topology = VALIDATED, material = "
                    "CANDIDATE` is a normal result"),
            },
            "never": ("no gap is bridged because it is collinear. There is "
                      "no bridge_collinear_gap rule here, evidence is "
                      "never averaged, and an unexplained gap stays "
                      "UNRESOLVED_GAP"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "RAISING_TOKENS": list(RAISING_TOKENS),
        "CONSEQUENCES_OF_COLLINEARITY": list(CONSEQUENCES_OF_COLLINEARITY),
        "COVERS_FRACTION": COVERS_FRACTION,
        "inherited": pw.frozen_parameters(),
        "why": {
            "which_tokens_may_raise_a_verdict": (
                "only the two that say something collinearity does not: "
                "another wall's material occupying the span, or another "
                "wall terminating into it. Collinearity, matching ends, a "
                "repeated band and shared entity provenance are all "
                "consequences of runs existing either side, and a rule "
                "resting on them is bridge_collinear_gap() renamed"),
            "no_averaging": (
                "tokens are named and counted. Nothing is weighted, "
                "nothing is summed into a score, and no score crosses a "
                "threshold"),
            "no_new_number": (
                "every geometric tolerance comes from the physical wall "
                "model, which took them from the profile and the frozen "
                "enclosure"),
        },
    }


def continuity_hash() -> str:
    parts = [MODEL, "|".join(VERDICTS), "|".join(EVIDENCE),
             "|".join(RAISING_TOKENS), str(COVERS_FRACTION),
             TOPOLOGY_VALIDATED, TOPOLOGY_SUPPORTED, TOPOLOGY_PORTAL,
             TOPOLOGY_NONE, MATERIAL_ESTABLISHED, MATERIAL_CANDIDATE,
             MATERIAL_ANOTHER_WALL, MATERIAL_ABSENT, MATERIAL_NONE,
             pw.wall_band_hash()]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------------ helpers

def _openings_over(openings, axis, lo, hi, faces) -> list:
    """Opening hypotheses lying on this wall, across this span."""
    out = []
    f_lo, f_hi = min(faces), max(faces)
    for o in openings:
        if o.axis != axis:
            continue
        of = o.wall_faces_mm or (o.fixed_mm,)
        if max(of) < f_lo - 1.0 or min(of) > f_hi + 1.0:
            continue
        if min(hi, o.end_mm) - max(lo, o.start_mm) <= 0:
            continue
        out.append(o)
    return out


def _supported(o) -> bool:
    """An opening that ROUND 4 was willing to let close a boundary."""
    return o.may_close_boundary


def _covers(o, lo: float, hi: float) -> bool:
    return o.start_mm <= lo + 1.0 and o.end_mm >= hi - 1.0


def _crossing_walls(walls, wall, lo, hi) -> list:
    """Walls of the other axis whose material occupies this span."""
    out = []
    for other in walls:
        if other.wall_id == wall.wall_id or other.axis == wall.axis:
            continue
        a, b = sorted((other.face_a_mm, other.face_b_mm))
        if b < lo or a > hi:
            continue
        o_lo, o_hi = other.observed_extent
        if o_hi < min(wall.face_a_mm, wall.face_b_mm) or \
                o_lo > max(wall.face_a_mm, wall.face_b_mm):
            continue
        out.append(other)
    return out


def _touching_walls(walls, wall, lo, hi) -> list:
    """Walls of the other axis that END inside this span (a T-junction)."""
    out = []
    for other in walls:
        if other.wall_id == wall.wall_id or other.axis == wall.axis:
            continue
        a, b = sorted((other.face_a_mm, other.face_b_mm))
        if b < lo or a > hi:
            continue
        o_lo, o_hi = other.observed_extent
        near = min(abs(o_lo - wall.face_a_mm), abs(o_lo - wall.face_b_mm),
                   abs(o_hi - wall.face_a_mm), abs(o_hi - wall.face_b_mm))
        if near <= max(wall.thickness_mm, other.thickness_mm):
            out.append(other)
    return out


def _flanks(wall, lo, hi) -> tuple:
    """Are there drawn runs of this wall before and after the span?"""
    before = any(s.hi <= lo + pw.JOIN_MM and s.coverage != pw.NEITHER_FACE
                 for s in wall.spans)
    after = any(s.lo >= hi - pw.JOIN_MM and s.coverage != pw.NEITHER_FACE
                for s in wall.spans)
    return before, after


def _same_entity(wall, lo, hi) -> bool:
    """Do the runs either side of the span come from one CAD entity?"""
    before, after = set(), set()
    for run in list(wall.face_a) + list(wall.face_b):
        base = {oid.split(".")[0].split("@")[0] for oid in run.object_ids}
        if run.hi <= lo + pw.JOIN_MM:
            before |= base
        if run.lo >= hi - pw.JOIN_MM:
            after |= base
    return bool(before & after)


def assess(walls, *, openings=(), region_id: str = "DR-001"
           ) -> ContinuityReport:
    """Ask, of every undrawn or half-drawn span, whether the wall is there."""
    rep = ContinuityReport(region_id=region_id)
    wall_list = list(walls)

    for wall in wall_list:
        faces = (wall.face_a_mm, wall.face_b_mm)
        for span in wall.spans:
            if span.coverage == pw.BOTH_FACES:
                continue
            lo, hi = span.lo, span.hi
            span_id = (f"CONT-{wall.wall_id}-{round(lo, 1)}")
            ev, why = [], ""
            before, after = _flanks(wall, lo, hi)
            if before and after:
                ev.append(EV_A_COLLINEAR)
                ev.append(EV_B_THICKNESS)
                ev.append(EV_G_REPEATED_BAND)
            if span.coverage == pw.ONE_FACE_ONLY:
                ev.append(EV_C_OPPOSITE_FACE)
            if _same_entity(wall, lo, hi):
                ev.append(EV_J_SAME_ENTITY)
            if before and after:
                ev.append(EV_H_MATCHING_ENDS)

            here = _openings_over(openings, wall.axis, lo, hi, faces)
            supported_here = [o for o in here if _supported(o)]
            covering = [o for o in supported_here if _covers(o, lo, hi)]
            if supported_here:
                ev.append(EV_F_HOSTS_OPENING)
            if supported_here and (before and after):
                ev.append(EV_I_THROUGH_OPENING)

            crossing = _crossing_walls(wall_list, wall, lo, hi)
            touching = _touching_walls(wall_list, wall, lo, hi)
            if crossing:
                ev.append(EV_E_CROSSES)
            if touching:
                ev.append(EV_D_T_JUNCTION)

            missing = None
            if span.coverage == pw.ONE_FACE_ONLY:
                missing = (wall.face_b_mm if span.face == "A"
                           else wall.face_a_mm)

            # ---- the rules, stated in order --------------------------
            #
            # §7 FIRST, ALWAYS. An opening is negative evidence, and it
            # outranks every positive sign: a door drawn across a span is
            # the reason the span is empty.
            if covering:
                verdict = OPENING_INTERRUPTION
                topo, mat = TOPOLOGY_PORTAL, MATERIAL_ABSENT
                why = ("a supported opening occupies this span end to end. "
                       "Round 4 closes it with a VIRTUAL boundary carrying "
                       "zero material, and NO material is recovered here")
            elif supported_here:
                verdict = UNRESOLVED_GAP
                topo, mat = TOPOLOGY_NONE, MATERIAL_NONE
                why = ("a supported opening overlaps this span without "
                       "explaining all of it. What the rest is cannot be "
                       "told from the geometry, so it stays unresolved")
            elif span.coverage == pw.ONE_FACE_ONLY:
                verdict = ESTABLISHED
                topo, mat = TOPOLOGY_VALIDATED, MATERIAL_CANDIDATE
                why = ("one face of this wall runs continuously across the "
                       "span at a supported thickness and no opening is "
                       "drawn in it. The PHYSICAL wall is continuous here; "
                       "the missing face is NOT fabricated, and material "
                       "may not be taken across it")
            elif crossing:
                verdict = ESTABLISHED
                topo, mat = TOPOLOGY_VALIDATED, MATERIAL_ANOTHER_WALL
                why = ("another established wall's material occupies this "
                       "span. The partition is continuous through the "
                       "junction, and the material there is measured on "
                       "that other wall, not on this one")
            elif not (before and after):
                verdict = NO_CONTINUATION
                topo, mat = TOPOLOGY_NONE, MATERIAL_NONE
                why = ("nothing of this wall is drawn beyond the span. It "
                       "ends here, and an end is not a gap")
            elif touching:
                verdict = SUPPORTED
                topo, mat = TOPOLOGY_SUPPORTED, MATERIAL_CANDIDATE
                why = ("another wall terminates into this span, which is a "
                       "physical reason for the break: drafters routinely "
                       "stop the through-wall at a junction. That is "
                       "enough to SUBDIVIDE and not enough to RELEASE")
            else:
                verdict = UNRESOLVED_GAP
                topo, mat = TOPOLOGY_NONE, MATERIAL_NONE
                why = ("this may be an opening, a missing face, a drafting "
                       "break, an open-plan connection or a wall that "
                       "stops. Nothing here distinguishes them, so nothing "
                       "is decided")

            rep.spans.append(Continuation(
                span_id=span_id, wall_id=wall.wall_id, region_id=region_id,
                axis=wall.axis, lo=lo, hi=hi, coverage=span.coverage,
                verdict=verdict, topology_authority=topo,
                material_authority=mat, evidence=tuple(ev),
                missing_face_mm=missing, faces_mm=faces, why=why))

    rep.notes["order_of_the_rules"] = (
        "openings are tested FIRST and outrank every positive sign. A door "
        "drawn across a span is the reason the span is empty, and "
        "recovering material there would be filling a doorway with "
        "blockwork")
    rep.notes["default"] = (
        "UNRESOLVED_GAP. False subdivision is as dangerous as false "
        "merging, so a gap nothing explains stays a gap nothing explains")
    return rep


def recovered_candidates(report, *, source_type=None) -> list:
    """The lines a recovery adds to the arrangement — inferred, not drawn.

    Their ids say RECOVERED so no downstream stage can mistake one for a
    line somebody drew, and each carries its own authorities.
    """
    from engine.boundary_match import VectorCandidate
    from engine.space_objects import SRC_VECTOR_OPENING_JAMB

    src = source_type or SRC_VECTOR_OPENING_JAMB
    out = []
    for s in report.recovered():
        fixed = s.missing_face_mm
        if fixed is None:
            # A junction recovery: the partition continues on BOTH faces.
            for i, f in enumerate(s.faces_mm):
                out.append(VectorCandidate(
                    object_id=f"RECOVERED-{s.span_id}-F{i}", axis=s.axis,
                    fixed_mm=f, start_mm=s.lo, end_mm=s.hi,
                    source_type=src, validation_class="ESTABLISHED"))
            continue
        out.append(VectorCandidate(
            object_id=f"RECOVERED-{s.span_id}", axis=s.axis, fixed_mm=fixed,
            start_mm=s.lo, end_mm=s.hi, source_type=src,
            validation_class="ESTABLISHED"))
    return out


def recovered_authorities(report) -> dict:
    """Which authorities each recovered line carries, by its object id.

    The two authorities travel WITH the line into the arrangement, so a
    space closed by a supported-but-not-validated span cannot be released
    by a downstream stage that never asked.
    """
    out = {}
    for s in report.recovered():
        row = {"TOPOLOGY_AUTHORITY": s.topology_authority,
               "MATERIAL_AUTHORITY": s.material_authority,
               "verdict": s.verdict, "span_id": s.span_id,
               "wall_id": s.wall_id}
        if s.missing_face_mm is None:
            for i, _f in enumerate(s.faces_mm):
                out[f"RECOVERED-{s.span_id}-F{i}"] = row
        else:
            out[f"RECOVERED-{s.span_id}"] = row
    return out
