"""Two labels in one room are usually one name written twice.

Round 2 blocked every room on P7757 with
`IDENTITY_AMBIGUOUS_MULTIPLE_LABELS`, because each stamp carries an English
string and an Arabic one and the code counted strings. `SALOON` and `صالون`
are not two identities in conflict; they are one identity stated twice, and
seeing two of them should make the identity STRONGER, not unusable.

So observations at one place are reconciled rather than counted:

    SAME_CONCEPT              they name the same architectural concept.
                              Two independent statements of one identity
    COMPATIBLE                one is known and the other is UNKNOWN, or
                              they agree at the class level without naming
                              the same concept. Nothing contradicts
    DIFFERENT_FUNCTIONAL_ZONE a room concept and a zone concept together:
                              a zone within a space, not a rival room
    CONFLICT                  two different room concepts in one place.
                              Something is wrong and nothing releases
    UNKNOWN                   nothing in the vocabulary recognised either

WHAT RECONCILIATION MAY NOT DO

It may not invent agreement. Two different rooms named at one point are a
CONFLICT and stay one — that is a real defect in the drawing or in the
measurement, and hiding it would be worse than reporting it.

It may not make identity a precondition for geometry. §10: a physical space
can be VALIDATED with its identity UNKNOWN. This module answers "what is it
called"; nothing here touches where its boundary runs.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field

from engine import architectural_ontology as onto

RECONCILER = "MULTILINGUAL_IDENTITY_RECONCILER_V1"

# Relationships between observations that share a place.
SAME_CONCEPT = "SAME_CONCEPT"
COMPATIBLE = "COMPATIBLE"
DIFFERENT_FUNCTIONAL_ZONE = "DIFFERENT_FUNCTIONAL_ZONE"
CONFLICT = "CONFLICT"
UNKNOWN_REL = "UNKNOWN"

# What the reconciled group says about identity.
IDENTITY_ESTABLISHED = "IDENTITY_ESTABLISHED"
IDENTITY_UNKNOWN = "IDENTITY_UNKNOWN"
IDENTITY_CONFLICT = "IDENTITY_CONFLICT"

# How near two observations must be to be talking about the same place. A
# bilingual pair is written one line above the other inside the same stamp,
# so this is a stamp's own extent — not a room's. Two metres is larger than
# any text block and smaller than any room it could stray into.
COINCIDENCE_MM = 2000.0

# Text-height difference is not used to separate observations: a drawing
# routinely sets the Arabic and English of one stamp at different heights.


@dataclass(frozen=True)
class Observation:
    """One authored label, with what the vocabulary makes of it."""

    observation_id: str
    text: str
    x: float
    y: float
    lookup: object
    carrier_block: str = ""
    decode_status: str = "TEXT_DECODED"

    @property
    def concept(self) -> str:
        return self.lookup.concept

    @property
    def concept_class(self) -> str:
        return self.lookup.concept_class

    def record(self) -> dict:
        return {"observation_id": self.observation_id, "text": self.text,
                "at_mm": [round(self.x, 1), round(self.y, 1)],
                "carrier_block": self.carrier_block,
                "text_decode_status": self.decode_status,
                **self.lookup.record()}


@dataclass(frozen=True)
class Reconciled:
    """One place, the observations made there, and what they jointly say."""

    group_id: str
    x: float
    y: float
    observations: tuple
    relationship: str
    identity_status: str
    normalized_identity: str
    concept_class: str
    evidence: tuple

    @property
    def is_established(self) -> bool:
        return self.identity_status == IDENTITY_ESTABLISHED

    @property
    def supporting_observations(self) -> int:
        """How many independent statements back the identity."""
        return sum(1 for o in self.observations
                   if o.concept == self.normalized_identity)

    def record(self) -> dict:
        return {
            "group_id": self.group_id,
            "at_mm": [round(self.x, 1), round(self.y, 1)],
            "observations": [o.record() for o in self.observations],
            "relationship": self.relationship,
            "identity_status": self.identity_status,
            "normalized_identity": self.normalized_identity,
            "concept_class": self.concept_class,
            "independent_statements": self.supporting_observations,
            "evidence": list(self.evidence),
            "note": ("identity is reported separately from geometry. An "
                     "UNKNOWN identity never invalidates a measured space"),
        }


@dataclass
class Report:
    groups: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def established(self) -> list:
        return [g for g in self.groups if g.is_established]

    def conflicts(self) -> list:
        return [g for g in self.groups
                if g.identity_status == IDENTITY_CONFLICT]

    def bilingual(self) -> list:
        """Groups whose identity rests on more than one statement."""
        return [g for g in self.groups
                if g.is_established and g.supporting_observations > 1]

    def counts(self) -> dict:
        return {
            "groups": len(self.groups),
            "by_relationship": dict(Counter(
                g.relationship for g in self.groups).most_common()),
            "by_identity_status": dict(Counter(
                g.identity_status for g in self.groups).most_common()),
            "identity_established": len(self.established()),
            "identity_conflicts": len(self.conflicts()),
            "reconciled_multi_statement_identities": len(self.bilingual()),
        }

    def record(self) -> dict:
        return {
            "reconciler": RECONCILER,
            "MULTILINGUAL_IDENTITY_HASH": reconciler_hash(),
            "ontology": onto.summary(),
            "counts": self.counts(),
            "groups": [g.record() for g in self.groups],
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "RECONCILER": RECONCILER,
        "COINCIDENCE_MM": COINCIDENCE_MM,
        "why": {
            "COINCIDENCE_MM": (
                "a bilingual pair is written one line above the other inside "
                "one stamp, so this is a stamp's extent, not a room's. Two "
                "metres is larger than any text block and smaller than any "
                "room it could stray into"),
            "no_text_height_test": (
                "a drawing routinely sets the Arabic and English of one "
                "stamp at different heights, so height never separates them"),
        },
    }


def reconciler_hash() -> str:
    parts = [RECONCILER, str(COINCIDENCE_MM), onto.ontology_hash(),
             SAME_CONCEPT, COMPATIBLE, DIFFERENT_FUNCTIONAL_ZONE, CONFLICT,
             UNKNOWN_REL]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _relate(obs) -> tuple:
    """The relationship among a group's observations, and why."""
    known = [o for o in obs if o.lookup.is_known]
    unknown = [o for o in obs if not o.lookup.is_known]
    ev = []

    if not known:
        return (UNKNOWN_REL, IDENTITY_UNKNOWN, "", onto.UNKNOWN,
                ("no observation here is in the architectural vocabulary. "
                 "That is an honest answer, not a defect",))

    concepts = {o.concept for o in known}
    classes = {o.concept_class for o in known}

    if len(concepts) == 1:
        concept = next(iter(concepts))
        cls = next(iter(classes))
        if len(known) > 1:
            langs = ", ".join(repr(o.text) for o in known)
            ev.append(f"{len(known)} observations name the same concept "
                      f"{concept}: {langs}. Two statements of one identity, "
                      "which STRENGTHENS it rather than conflicting")
            rel = SAME_CONCEPT
        else:
            ev.append(f"one observation names {concept}")
            rel = COMPATIBLE if unknown else SAME_CONCEPT
        if unknown:
            ev.append(f"{len(unknown)} further observation(s) are not in the "
                      "vocabulary. UNKNOWN does not contradict a known name")
        return (rel, IDENTITY_ESTABLISHED, concept, cls, tuple(ev))

    # More than one concept named here.
    room_like = {o.concept for o in known
                 if o.concept_class == onto.ROOM}
    zone_like = {o.concept for o in known
                 if o.concept_class == onto.FUNCTIONAL_ZONE}

    if len(room_like) > 1:
        ev.append(f"two different room concepts named in one place: "
                  f"{sorted(room_like)}. Something is wrong — either the "
                  "drawing or the measurement — and nothing releases from "
                  "an unresolved contradiction")
        return (CONFLICT, IDENTITY_CONFLICT, "", onto.ROOM, tuple(ev))

    if room_like and zone_like:
        room = sorted(room_like)[0]
        ev.append(f"a room concept ({room}) and a zone concept "
                  f"({sorted(zone_like)}) together: a zone WITHIN a space, "
                  "not a rival room")
        return (DIFFERENT_FUNCTIONAL_ZONE, IDENTITY_ESTABLISHED, room,
                onto.ROOM, tuple(ev))

    if len(classes) == 1:
        cls = next(iter(classes))
        ev.append(f"different concepts of the same class ({cls}) — they "
                  "agree about what KIND of thing this is without naming "
                  "the same one")
        return (COMPATIBLE, IDENTITY_UNKNOWN, "", cls, tuple(ev))

    ev.append(f"observations of incompatible classes here: {sorted(classes)}")
    return (CONFLICT, IDENTITY_CONFLICT, "", "", tuple(ev))


def reconcile(observations, *, coincidence_mm: float = COINCIDENCE_MM
              ) -> Report:
    """Group observations by place and lineage, then reconcile each group.

    Two observations join a group when they are spatially coincident AND
    share a block lineage, or are coincident and neither carries one. The
    lineage test matters: two stamps of different rooms can fall within a
    couple of metres of each other near a shared wall, and merging those
    would invent an identity conflict out of a layout accident.
    """
    rep = Report()
    groups: list = []
    for o in sorted(observations, key=lambda r: (r.x, r.y, r.text)):
        for g in groups:
            if math.hypot(g["x"] - o.x, g["y"] - o.y) > coincidence_mm:
                continue
            if g["block"] != o.carrier_block:
                continue
            g["obs"].append(o)
            break
        else:
            groups.append({"x": o.x, "y": o.y, "block": o.carrier_block,
                           "obs": [o]})

    for n, g in enumerate(sorted(groups, key=lambda r: (-r["y"], r["x"])), 1):
        rel, status, identity, cls, ev = _relate(g["obs"])
        rep.groups.append(Reconciled(
            group_id=f"IDG-{n:03d}", x=g["x"], y=g["y"],
            observations=tuple(g["obs"]), relationship=rel,
            identity_status=status, normalized_identity=identity,
            concept_class=cls, evidence=ev))

    rep.notes["why_not_count_strings"] = (
        "round 2 blocked every room with IDENTITY_AMBIGUOUS_MULTIPLE_LABELS "
        "because it counted strings. An English and an Arabic label naming "
        "one concept are one identity stated twice")
    rep.notes["what_a_conflict_means"] = (
        "two different ROOM concepts in one place. It is reported, never "
        "averaged away, and it releases nothing")
    return rep


def observations_from(texts, *, decode_status_of=None) -> list:
    """Turn normalized text observations into vocabulary lookups."""
    out = []
    for t in texts:
        carrier = (t.provenance.block_path[-1]
                   if t.provenance.block_path else "")
        out.append(Observation(
            observation_id=f"OBS-{t.provenance.object_id}",
            text=t.value, x=t.x, y=t.y,
            lookup=onto.classify_term(t.value), carrier_block=carrier,
            decode_status=(decode_status_of(t) if decode_status_of
                           else "TEXT_DECODED")))
    return out
