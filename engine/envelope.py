"""E39 — the building envelope, from several kinds of evidence.

`EXTERIOR_END = 0` has been true for three rounds because nothing could tell an
outside wall from an inside one, which left every genuinely external wall end
falling through to UNRESOLVED and kept gate G3 red.

THE TRAP THIS MODULE IS BUILT TO AVOID. The obvious approach is to flood the
raster from the sheet border and call everything it touches external. That is
one observation dressed as a conclusion: a terrace, a light well and an
unclosed room all connect to the border, and a courtyard does not connect to
it while being thoroughly outside. So raster free space is ONE evidence
source among several, and it never classifies alone.

    DO NOT CLASSIFY EXTERNAL PURELY FROM A RASTER-SPACE UNION.

Evidence, by family, so that correlated observations of one construction
cannot be counted as independent proofs:

    PLANAR    the wall lies on a component's unbounded face
    RASTER    one side of the wall reaches border-connected free space
    GEOMETRY  wall separation is in the external band for this project
    SOURCE    the pen weight and layer the architect drew it with

Two independent families before VALIDATED. One is a hypothesis. None is
UNRESOLVED, and UNRESOLVED is a perfectly good answer.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

INTERNAL = "INTERNAL"
EXTERNAL = "EXTERNAL"
UNRESOLVED = "UNRESOLVED"

FAMILY_PLANAR = "PLANAR"
FAMILY_RASTER = "RASTER"
FAMILY_GEOMETRY = "GEOMETRY"
FAMILY_SOURCE = "SOURCE"

E_ON_UNBOUNDED_FACE = "LIES_ON_AN_UNBOUNDED_FACE"
E_BOUNDS_TWO_FACES = "BOUNDS_TWO_BOUNDED_FACES"
E_BORDER_FREE_SPACE = "REACHES_BORDER_CONNECTED_FREE_SPACE"
E_ENCLOSED_BOTH_SIDES = "ENCLOSED_SPACE_ON_BOTH_SIDES"
E_THICK_FOR_EXTERNAL = "SEPARATION_IN_THE_EXTERNAL_BAND"
E_THIN_FOR_PARTITION = "SEPARATION_IN_THE_PARTITION_BAND"

EVIDENCE_FAMILY = {
    E_ON_UNBOUNDED_FACE: FAMILY_PLANAR,
    E_BOUNDS_TWO_FACES: FAMILY_PLANAR,
    E_BORDER_FREE_SPACE: FAMILY_RASTER,
    E_ENCLOSED_BOTH_SIDES: FAMILY_RASTER,
    E_THICK_FOR_EXTERNAL: FAMILY_GEOMETRY,
    E_THIN_FOR_PARTITION: FAMILY_GEOMETRY,
}

MIN_FAMILIES_FOR_VALIDATED = 2

# Separation bands observed on AR-00: 190 pairs at 60-120, 61 at 120-180, 30 at
# 180-260, 15 at 260-400. Thickness is EVIDENCE, never a classification — a
# 250 mm internal party wall exists and so does a 200 mm external one.
EXTERNAL_BAND_MM = 260.0
PARTITION_BAND_MM = 120.0


class EnvelopeError(RuntimeError):
    """A wall was classified without the evidence to carry it."""


@dataclass(frozen=True)
class EdgeClassification:
    edge_id: str
    classification: str
    evidence: tuple[str, ...]
    why: str
    separation_mm: float | None = None

    @property
    def families(self) -> set:
        return {EVIDENCE_FAMILY[e] for e in self.evidence}

    @property
    def validated(self) -> bool:
        return (self.classification != UNRESOLVED
                and len(self.families) >= MIN_FAMILIES_FOR_VALIDATED)

    def record(self) -> dict:
        return {"edge_id": self.edge_id,
                "classification": self.classification,
                "evidence": list(self.evidence),
                "families": sorted(self.families),
                "validated": self.validated,
                "separation_mm": (None if self.separation_mm is None
                                  else round(self.separation_mm, 1)),
                "why": self.why}


def classify(edges, *, unbounded_edge_ids=(), bounded_edge_counts=None,
             border_free_edge_ids=()) -> list[EdgeClassification]:
    """One verdict per wall edge, with the families that carried it.

    `bounded_edge_counts` maps edge_id -> how many BOUNDED faces it borders.
    An edge bordering two bounded faces has rooms on both sides and is
    internal; one on an unbounded face has the outside on one side.
    """
    counts = bounded_edge_counts or {}
    unbounded = set(unbounded_edge_ids)
    border = set(border_free_edge_ids)
    out: list[EdgeClassification] = []
    for e in edges:
        ev: list[str] = []
        sep = e.wall_face_separation_mm
        if e.edge_id in unbounded:
            ev.append(E_ON_UNBOUNDED_FACE)
        if counts.get(e.edge_id, 0) >= 2:
            ev.append(E_BOUNDS_TWO_FACES)
        if e.edge_id in border:
            ev.append(E_BORDER_FREE_SPACE)
        if sep >= EXTERNAL_BAND_MM:
            ev.append(E_THICK_FOR_EXTERNAL)
        elif sep <= PARTITION_BAND_MM:
            ev.append(E_THIN_FOR_PARTITION)

        ext = [x for x in ev if x in (E_ON_UNBOUNDED_FACE, E_BORDER_FREE_SPACE,
                                      E_THICK_FOR_EXTERNAL)]
        internal = [x for x in ev if x in (E_BOUNDS_TWO_FACES,
                                           E_THIN_FOR_PARTITION)]
        ext_fams = {EVIDENCE_FAMILY[x] for x in ext}
        int_fams = {EVIDENCE_FAMILY[x] for x in internal}

        if E_BOUNDS_TWO_FACES in ev:
            cls = INTERNAL
            why = ("bounded rooms on both sides: whatever its thickness, this "
                   "wall has inside on each face")
            ev_used = tuple(internal)
        elif len(ext_fams) >= MIN_FAMILIES_FOR_VALIDATED:
            cls = EXTERNAL
            why = (f"{len(ext_fams)} independent families agree: "
                   + ", ".join(sorted(ext_fams)))
            ev_used = tuple(ext)
        elif len(int_fams) >= MIN_FAMILIES_FOR_VALIDATED:
            cls = INTERNAL
            why = (f"{len(int_fams)} independent families agree: "
                   + ", ".join(sorted(int_fams)))
            ev_used = tuple(internal)
        else:
            cls = UNRESOLVED
            ev_used = tuple(ev)
            why = ("no two independent families agree. Thickness alone is "
                   "evidence, never a classification: a 250 mm internal party "
                   "wall exists and so does a 200 mm external one"
                   if ev else
                   "no evidence of any kind reaches this edge")
            if len(ev) == 1:
                why = (f"one evidence family only ({sorted(ext_fams | int_fams)[0]}): "
                       "a hypothesis, not a classification. " + why)
        out.append(EdgeClassification(e.edge_id, cls, ev_used, why, sep))
    return out


def summary(classified) -> dict:
    return {
        "edges": len(classified),
        "by_classification": dict(Counter(c.classification
                                          for c in classified)),
        "validated": sum(1 for c in classified if c.validated),
        "single_family_only": sum(1 for c in classified
                                  if len(c.families) == 1),
        "no_evidence": sum(1 for c in classified if not c.evidence),
        "by_family_count": dict(Counter(len(c.families) for c in classified)),
        "note": ("EXTERNAL requires two independent evidence families. "
                 "Raster free space never classifies alone: a terrace, a light "
                 "well and an unclosed room all reach the sheet border, and a "
                 "courtyard reaches nothing while being outside"),
    }
