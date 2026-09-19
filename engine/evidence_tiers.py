"""E99 — orthogonality is not independence, and conflating them was wrong.

Round 2 required two different SOURCE_INDEPENDENCE_CLASS values before a
portal could be VALIDATED. That rule was right about one thing and wrong
about what follows from it.

RIGHT: a raster render of a PDF is the same drawing observed twice. Two
views of one primitive are one piece of evidence, and counting them as two
is how a wall came to be "confirmed" by itself.

WRONG: the conclusion that nothing on a single drawing can validate
anything. A professional takeoff reads openings off a plan every day, and
what makes that sound is not a second document — it is that the plan says
the same thing in DIFFERENT AUTHORED WAYS. A gap in a wall, a door swing
arc, a leaf symbol and a printed opening width are four things a
draughtsman drew separately, by hand, for different reasons. They can
disagree, and that is exactly what makes their agreement informative.

So evidence has two axes, and they are recorded separately:

    SOURCE INDEPENDENCE   how far from this document did it come?
    EVIDENCE ORTHOGONALITY how differently was it authored?

A doorway with gap geometry + a swing arc + a printed width is
SAME_DOCUMENT and highly ORTHOGONAL. A wall measured twice off the same
polyline is SAME_DOCUMENT and NOT orthogonal at all. The first is strong;
the second is one observation wearing two hats.

This module does not lower any geometric standard. Exact coordinates still
come from source geometry and never from a model reading a picture.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# --- axis 1: how far from this document ----------------------------------
SRC_SAME_PRIMITIVE = "SAME_PRIMITIVE"
SRC_SAME_DRAWING = "SAME_DRAWING"
SRC_SAME_DOCUMENT_SET = "SAME_DOCUMENT_SET"
SRC_INDEPENDENT = "INDEPENDENT_SOURCE"

SOURCE_RANK = {SRC_SAME_PRIMITIVE: 0, SRC_SAME_DRAWING: 1,
               SRC_SAME_DOCUMENT_SET: 2, SRC_INDEPENDENT: 3}

# --- axis 2: how differently authored ------------------------------------
# A channel is a distinct authoring act. Two observations in the SAME
# channel corroborate almost nothing; two in different channels can
# disagree, which is what makes agreement worth something.
CH_GEOMETRY = "DRAWN_GEOMETRY"          # the lines themselves
CH_SYMBOL = "DRAWN_SYMBOL"              # a swing arc, a leaf, a hatch
CH_ANNOTATION = "PRINTED_ANNOTATION"    # a dimension, a tag, a note
CH_STRUCTURE = "DOCUMENT_STRUCTURE"     # a schedule row, a legend
CH_RENDER = "RENDER_OF_THE_SAME_GEOMETRY"   # the raster. NOT a channel.
CH_MODEL = "MODEL_READING"              # a vision transcription

CHANNELS = (CH_GEOMETRY, CH_SYMBOL, CH_ANNOTATION, CH_STRUCTURE,
            CH_RENDER, CH_MODEL)

# A render of geometry is the geometry. A model reading an annotation is
# that annotation. Neither adds a channel — they relay one.
RELAYS = {CH_RENDER: CH_GEOMETRY, CH_MODEL: None}

# Strength tiers, from the two axes together.
TIER_SINGLE = "SINGLE_OBSERVATION"
TIER_CORRELATED = "CORRELATED_REPEAT_OF_ONE_OBSERVATION"
TIER_DRAWING_ORTHOGONAL = "SAME_DRAWING_ORTHOGONAL"
TIER_DOCUMENT_ORTHOGONAL = "SAME_DOCUMENT_SET_ORTHOGONAL"
TIER_INDEPENDENT = "INDEPENDENTLY_SOURCED"

TIER_RANK = {TIER_SINGLE: 0, TIER_CORRELATED: 0, TIER_DRAWING_ORTHOGONAL: 1,
             TIER_DOCUMENT_ORTHOGONAL: 2, TIER_INDEPENDENT: 3}


@dataclass(frozen=True)
class Observation:
    """One piece of evidence, with both axes recorded."""

    observation_id: str
    what: str
    channel: str
    source_class: str = SRC_SAME_DRAWING
    relays: str = ""            # the observation this one merely repeats
    note: str = ""

    @property
    def effective_channel(self) -> str:
        """A relay contributes its ORIGINAL channel, not a new one."""
        mapped = RELAYS.get(self.channel, self.channel)
        return mapped or self.channel

    def record(self) -> dict:
        return {"observation_id": self.observation_id, "what": self.what,
                "channel": self.channel,
                "effective_channel": self.effective_channel,
                "source_class": self.source_class,
                "relays": self.relays, "note": self.note}


@dataclass
class Assessment:
    tier: str = TIER_SINGLE
    channels: tuple[str, ...] = ()
    source_classes: tuple[str, ...] = ()
    observations: tuple = ()
    discounted: tuple = ()
    why: str = ""

    @property
    def rank(self) -> int:
        return TIER_RANK.get(self.tier, 0)

    def record(self) -> dict:
        return {
            "EVIDENCE_TIER": self.tier,
            "tier_rank": self.rank,
            "orthogonal_channels": list(self.channels),
            "source_classes_present": list(self.source_classes),
            "observations": [o.record() for o in self.observations],
            "discounted_as_correlated": [
                {"observation_id": o.observation_id, "because": why}
                for o, why in self.discounted],
            "the_two_axes": {
                "SOURCE_INDEPENDENCE": "how far from this document it came",
                "EVIDENCE_ORTHOGONALITY": "how differently it was authored",
                "why_both": (
                    "a wall measured twice off one polyline is one "
                    "observation wearing two hats. A gap, a swing arc and "
                    "a printed width are three things a draughtsman drew "
                    "separately, which is why their agreement is "
                    "informative even on one sheet"),
            },
            "what_this_does_not_do": (
                "lower any geometric standard. Exact coordinates still "
                "come from source geometry, never from a model reading a "
                "picture"),
            "why": self.why,
        }


def assess(observations) -> Assessment:
    """Combine observations into a tier on both axes."""
    obs = list(observations)
    if not obs:
        return Assessment(tier=TIER_SINGLE, why="no evidence was offered")

    kept, discounted = [], []
    seen_relay: set = set()
    for o in obs:
        if o.relays:
            if o.relays in seen_relay or any(
                    x.observation_id == o.relays for x in obs):
                discounted.append((o, (
                    f"it relays {o.relays}, which is already counted. A "
                    "render of geometry is that geometry, and a model "
                    "reading a dimension is that dimension")))
                continue
        seen_relay.add(o.observation_id)
        kept.append(o)

    channels = tuple(sorted({o.effective_channel for o in kept}))
    classes = tuple(sorted({o.source_class for o in kept},
                           key=lambda c: SOURCE_RANK.get(c, 0)))
    best_source = max((SOURCE_RANK.get(c, 0) for c in classes), default=0)

    if best_source >= SOURCE_RANK[SRC_INDEPENDENT]:
        tier = TIER_INDEPENDENT
        why = ("corroborated from outside this document set — a CAD model, "
               "a site measurement or an as-built survey")
    elif len(channels) >= 2 and best_source >= SOURCE_RANK[
            SRC_SAME_DOCUMENT_SET]:
        tier = TIER_DOCUMENT_ORTHOGONAL
        why = (f"{len(channels)} differently authored channels, at least "
               "one of them from another document in the set — a schedule, "
               "a section or a detail")
    elif len(channels) >= 2:
        tier = TIER_DRAWING_ORTHOGONAL
        why = (f"{len(channels)} differently authored channels on one "
               f"drawing ({', '.join(channels)}). They could have "
               "disagreed, and they do not")
    elif len(kept) > 1:
        tier = TIER_CORRELATED
        why = (f"{len(kept)} observations, all in the same channel "
               f"({channels[0] if channels else '?'}). That is one "
               "observation repeated, not two agreeing")
    else:
        tier = TIER_SINGLE
        why = "one observation, in one channel, from one source"

    return Assessment(tier=tier, channels=channels, source_classes=classes,
                      observations=tuple(kept),
                      discounted=tuple(discounted), why=why)


# ------------------------------------------------------- §9 portal grades

PORTAL_UNVALIDATED = "PORTAL_UNVALIDATED"
PORTAL_DRAWING_VALIDATED = "PORTAL_DRAWING_VALIDATED"
PORTAL_DOCUMENT_VALIDATED = "PORTAL_DOCUMENT_VALIDATED"
PORTAL_SOURCE_VALIDATED = "PORTAL_SOURCE_VALIDATED"

GRADE_RANK = {PORTAL_UNVALIDATED: 0, PORTAL_DRAWING_VALIDATED: 1,
              PORTAL_DOCUMENT_VALIDATED: 2, PORTAL_SOURCE_VALIDATED: 3}

# What a grade may be used for. The change Round 3 asks for: an ordinary
# doorway, read off a plan with exact geometry and orthogonal same-drawing
# support, may carry a production quantity. It does NOT need a site visit.
MAY_RELEASE_FROM = PORTAL_DRAWING_VALIDATED

# An opening this wide is not an ordinary doorway. A 4 m gap may be a
# missing wall, an open-plan transition or a folding screen, and getting it
# wrong changes a room's area by square metres rather than by a jamb.
ORDINARY_OPENING_MAX_MM = 2600.0


@dataclass(frozen=True)
class PortalGrade:
    portal_id: str
    grade: str
    assessment: Assessment
    geometry_exact: bool
    host_compatible: bool
    contradicted: bool
    opening_width_mm: float
    needs_human_qa: bool
    why: str = ""

    @property
    def may_release(self) -> bool:
        return (GRADE_RANK[self.grade] >= GRADE_RANK[MAY_RELEASE_FROM]
                and not self.needs_human_qa)

    def record(self) -> dict:
        return {
            "portal_id": self.portal_id,
            "PORTAL_GRADE": self.grade,
            "may_release_a_quantity": self.may_release,
            "needs_human_qa": self.needs_human_qa,
            "opening_width_mm": round(self.opening_width_mm, 1),
            "exact_geometry_from_source": self.geometry_exact,
            "host_wall_compatible": self.host_compatible,
            "contradicted_by_other_evidence": self.contradicted,
            "evidence": self.assessment.record(),
            "geometric_standard_unchanged": (
                "the opening's coordinates come from the drawn jamb "
                "geometry. The evidence tier decides whether the opening is "
                "THERE, never where it is"),
            "why": self.why,
        }


def grade_portal(portal_id: str, observations, *,
                 geometry_exact: bool, host_compatible: bool,
                 contradicted: bool = False,
                 opening_width_mm: float = 0.0) -> PortalGrade:
    """Grade one portal on evidence strength, not on a binary rule."""
    ev = assess(observations)

    if contradicted or not geometry_exact or not host_compatible:
        grade = PORTAL_UNVALIDATED
    elif ev.rank >= TIER_RANK[TIER_INDEPENDENT]:
        grade = PORTAL_SOURCE_VALIDATED
    elif ev.rank >= TIER_RANK[TIER_DOCUMENT_ORTHOGONAL]:
        grade = PORTAL_DOCUMENT_VALIDATED
    elif ev.rank >= TIER_RANK[TIER_DRAWING_ORTHOGONAL]:
        grade = PORTAL_DRAWING_VALIDATED
    else:
        grade = PORTAL_UNVALIDATED

    wide = opening_width_mm > ORDINARY_OPENING_MAX_MM
    needs_qa = (wide and GRADE_RANK[grade]
                < GRADE_RANK[PORTAL_DOCUMENT_VALIDATED])

    if grade == PORTAL_UNVALIDATED:
        reasons = []
        if contradicted:
            reasons.append("other evidence contradicts it")
        if not geometry_exact:
            reasons.append("its geometry does not come from source lines")
        if not host_compatible:
            reasons.append("it is not compatible with its host wall")
        if not reasons:
            reasons.append(
                f"its evidence is {ev.tier}: {ev.why}")
        why = "refused because " + "; ".join(reasons)
    elif needs_qa:
        why = (f"a {opening_width_mm:.0f} mm opening is not an ordinary "
               "doorway. At this width a wrong call moves square metres, "
               "not a jamb, so it is held for human QA until a document or "
               "independent source supports it")
    else:
        why = (f"{ev.tier}: {ev.why}. The geometry is exact and the host "
               "wall is compatible, so an ordinary doorway read off a plan "
               "may carry a quantity — no site visit is required for it")

    return PortalGrade(portal_id=portal_id, grade=grade, assessment=ev,
                       geometry_exact=geometry_exact,
                       host_compatible=host_compatible,
                       contradicted=contradicted,
                       opening_width_mm=opening_width_mm,
                       needs_human_qa=needs_qa, why=why)


def summary(grades) -> dict:
    items = list(grades)
    return {
        "portals_graded": len(items),
        "by_grade": dict(Counter(g.grade for g in items)),
        "may_release": sum(1 for g in items if g.may_release),
        "held_for_human_qa": sum(1 for g in items if g.needs_human_qa),
        "release_threshold": MAY_RELEASE_FROM,
        "ordinary_opening_max_mm": ORDINARY_OPENING_MAX_MM,
        "what_changed_from_round_2": (
            "requiring two SOURCE INDEPENDENCE classes meant no doorway on "
            "a single architectural sheet could ever be validated, which is "
            "not how a professional takeoff works. The requirement is now "
            "two differently AUTHORED channels — a gap, a swing arc, a "
            "printed width — with independence recorded separately and "
            "still required for the openings where a wrong call is "
            "expensive"),
        "what_did_not_change": (
            "exact opening coordinates come from drawn geometry. No tier "
            "lets a model's reading supply a millimetre"),
    }
