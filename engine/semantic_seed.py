"""What a piece of authored text IS, before it is allowed to seed anything.

Round 1 seeded a measurement from every text observation that arrived
through a placed block. 27 of 48 candidates were not rooms: `NEIGHBOUR`,
`STREET`, `SEA VIEW`, level marks and plot dimensions are all text carried
by placed blocks, and all of them passed.

So the chain gains the step it was missing:

    TEXT_OBSERVATION            a string, a position, a lineage
    SEMANTIC_SPACE_OBSERVATION  what that string appears to BE
    SPATIAL_SEED                a point permitted to start a measurement
    PHYSICAL_SPACE              a measured, classified, released space

THE TESTS ARE STRUCTURAL, NOT LEXICAL

No string from any drawing steers a decision here — the words quoted above
name what went wrong and nothing reads them. The tests are properties any
drawing's annotation has, in any language:

  * A ROOM IS NOT NAMED BY A NUMBER. `31.37`, `15.00`, `+0.15`, `%%p0.00`
    are measurements — a level, a plot dimension, a setback. A room name is
    not a numeral, in Arabic or English or anything else. This one test
    removes every level mark and every plot dimension.

  * A SCALE RATIO MARKS A TITLE. `1:100` says the string describes the
    DRAWING rather than a space in it.

  * A LABEL OUTSIDE THE BUILT FABRIC NAMES SOMETHING OUTSIDE IT. A street,
    a neighbour, a view. This is decided by geometry supplied by the
    caller, never by the words.

  * AN ISOLATED LABEL IS AMBIGUOUS, NOT A ROOM. A string with no bounded
    geometry near it may be a note.

AMBIGUOUS RELEASES NOTHING. That is the whole point of having the class.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field

CLASSIFIER = "SEMANTIC_SEED_CLASSIFIER_V1"

# The four classes. Only ROOM_LIKE may seed a physical-space measurement,
# and even then only if its geometric context supports one (§5).
ROOM_LIKE = "ROOM_LIKE"
ZONE_LIKE = "ZONE_LIKE"
NON_SPACE_ANNOTATION = "NON_SPACE_ANNOTATION"
AMBIGUOUS = "AMBIGUOUS"

# Why a string was classified the way it was.
R_NUMERIC = "STRING_IS_A_MEASUREMENT_NOT_A_NAME"
R_SCALE = "STRING_CARRIES_A_DRAWING_SCALE_RATIO"
R_OUTSIDE = "OBSERVATION_LIES_OUTSIDE_THE_BUILT_FABRIC"
R_NO_CONTEXT = "NO_BOUNDED_GEOMETRY_NEAR_THE_OBSERVATION"
R_LOOSE = "TEXT_NOT_CARRIED_BY_A_PLACED_SYMBOL"
R_NAMELIKE = "STRING_BEHAVES_LIKE_A_NAME_INSIDE_BUILT_FABRIC"

# A string is a measurement when, stripped of the decorations a CAD level
# or dimension puts round a number, nothing but a number is left. The
# decorations are format characters, not words: sign, percent-escapes that
# AutoCAD uses for symbols, units, and separators.
_DECORATION = re.compile(r"""(?ix)
      %%[a-z%]            # AutoCAD escape: %%p, %%d, %%c. ONE
                          # character: [a-z0-9]{1,3} was greedy and
                          # ate the digits it existed to expose, so
                          # "%%p0.00" was left as ".00"
    | [\s+\-=~'"()\[\]]     # sign, brackets, quotes, whitespace
    | \b(?:mm|cm|m|km|ft|in|sq|m2|m²)\b
""")
_NUMBER = re.compile(r"^[0-9]+(?:[.,][0-9]+)?$")
# A scale ratio: two runs of digits either side of a colon.
_SCALE = re.compile(r"\b\d{1,4}\s*:\s*\d{1,5}\b")


@dataclass(frozen=True)
class SpaceObservation:
    """One semantic reading of one authored annotation."""

    observation_id: str
    text: str
    x: float
    y: float
    semantic_class: str
    reasons: tuple
    carrier_block: str = ""
    provenance: tuple = ()

    @property
    def may_seed(self) -> bool:
        return self.semantic_class == ROOM_LIKE

    def record(self) -> dict:
        return {
            "observation_id": self.observation_id,
            "text": self.text,
            "at_mm": [round(self.x, 1), round(self.y, 1)],
            "carrier_block": self.carrier_block,
            "semantic_class": self.semantic_class,
            "reasons": list(self.reasons),
            "may_seed_a_physical_space": self.may_seed,
            "provenance": list(self.provenance),
            "note": ("a label is evidence for IDENTITY. It is never "
                     "evidence for a BOUNDARY"),
        }


@dataclass
class SeedReport:
    observations: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def seeds(self) -> list:
        return [o for o in self.observations if o.may_seed]

    def counts(self) -> dict:
        return dict(Counter(o.semantic_class
                            for o in self.observations).most_common())

    def record(self) -> dict:
        return {
            "classifier": CLASSIFIER,
            "SEMANTIC_SEED_CLASSIFIER_HASH": classifier_hash(),
            "observations": len(self.observations),
            "by_class": self.counts(),
            "permitted_to_seed": len(self.seeds()),
            "rejected_annotation_seeds": [
                o.record() for o in self.observations
                if o.semantic_class == NON_SPACE_ANNOTATION],
            "ambiguous": [o.record() for o in self.observations
                          if o.semantic_class == AMBIGUOUS],
            "room_like": [o.record() for o in self.seeds()],
            "rules": frozen_rules(),
            "notes": dict(self.notes),
        }


def frozen_rules() -> dict:
    return {
        "CLASSIFIER": CLASSIFIER,
        "tests": [
            "a string that is a number once CAD decorations are stripped is "
            "a MEASUREMENT (a level, a plot dimension, a setback), never a "
            "room name — in any language",
            "a string carrying a scale ratio describes the DRAWING",
            "text not carried by a placed symbol is loose annotation",
            "an observation outside the built fabric names something "
            "outside it, decided by geometry the caller supplies",
            "an observation with no bounded geometry near it is AMBIGUOUS",
        ],
        "what_is_never_used": (
            "the actual words. No string from any real drawing appears in "
            "this module, and a room-name allowlist would make the engine "
            "right about one project and wrong about the next"),
        "AMBIGUOUS_releases_nothing": True,
    }


def classifier_hash() -> str:
    parts = [CLASSIFIER, ROOM_LIKE, ZONE_LIKE, NON_SPACE_ANNOTATION,
             AMBIGUOUS, _NUMBER.pattern, _SCALE.pattern, _DECORATION.pattern]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def is_measurement(text: str) -> bool:
    """True when the string is a number wearing CAD decoration."""
    stripped = _DECORATION.sub("", text or "")
    return bool(stripped) and bool(_NUMBER.match(stripped))


def is_drawing_title(text: str) -> bool:
    return bool(_SCALE.search(text or ""))


def classify(texts, *, built_fabric=None, bounded_context=None) -> SeedReport:
    """Classify every authored text observation.

    `built_fabric` is an optional callable `(x, y) -> bool` saying whether a
    point lies within the drawing's built extent. `bounded_context` is an
    optional callable `(x, y) -> bool` saying whether any bounded geometry
    surrounds the point. Both are GEOMETRY supplied by the caller; this
    module never decides them from words.
    """
    rep = SeedReport()
    for t in texts:
        reasons, cls = [], ROOM_LIKE
        carrier = (t.provenance.block_path[-1]
                   if t.provenance.block_path else "")

        if is_measurement(t.value):
            cls = NON_SPACE_ANNOTATION
            reasons.append(R_NUMERIC)
        elif is_drawing_title(t.value):
            cls = NON_SPACE_ANNOTATION
            reasons.append(R_SCALE)
        elif not carrier:
            # Loose text is as likely a note, a street name or a view. It is
            # not rejected outright — it is simply not permitted to seed.
            cls = AMBIGUOUS
            reasons.append(R_LOOSE)

        if cls == ROOM_LIKE and built_fabric is not None:
            if not built_fabric(t.x, t.y):
                cls = NON_SPACE_ANNOTATION
                reasons.append(R_OUTSIDE)

        if cls == ROOM_LIKE and bounded_context is not None:
            if not bounded_context(t.x, t.y):
                cls = AMBIGUOUS
                reasons.append(R_NO_CONTEXT)

        if cls == ROOM_LIKE:
            reasons.append(R_NAMELIKE)

        rep.observations.append(SpaceObservation(
            observation_id=f"OBS-{t.provenance.object_id}",
            text=t.value, x=t.x, y=t.y, semantic_class=cls,
            reasons=tuple(reasons), carrier_block=carrier,
            provenance=(t.provenance.object_id,)))

    rep.notes["what_a_seed_is_not"] = (
        "a seed says WHERE a space might be and WHAT it might be called. It "
        "says nothing about where that space's boundary runs, which comes "
        "from geometry alone")
    return rep
