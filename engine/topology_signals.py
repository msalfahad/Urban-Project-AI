"""E64 — raster is a second OPINION about topology, never a measurement.

Two rules, and the second is the one that is easy to get wrong.

    RASTER MAY CHALLENGE THE VECTOR RESULT. Where the segmentation separates
    two spaces the free-space engine merged, that is a missing-wall
    hypothesis worth acting on — and it is the cheapest lead available.

    RASTER MAY NOT SUPPLY A MILLIMETRE. No released area or perimeter comes
    from a pixel outline, at any resolution.

And a third, about honesty rather than architecture:

    RASTER SEGMENTATION OUTPUT IS NOT THE SAME THING AS THE GOLDEN-VALIDATED
    REGION STATE.

Project 23010's 35 identity-validated and 33 topology-validated regions were
established with HUMAN review and a golden overlay. Quoting them as evidence
that automatic raster segmentation is accurate would be circular — it would be
crediting the algorithm with a person's work. The two are counted separately
here, and the automatic figure is the one with no validation behind it at all.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# How a raster region and a vector free-space component relate.
AGREES = "AGREES"
VECTOR_SPLITS_RASTER = "VECTOR_SPLITS_RASTER"
RASTER_SPLITS_VECTOR = "RASTER_SPLITS_VECTOR"
VECTOR_ONLY = "VECTOR_ONLY"
RASTER_ONLY = "RASTER_ONLY"
AMBIGUOUS = "AMBIGUOUS"

RELATIONSHIPS = (AGREES, VECTOR_SPLITS_RASTER, RASTER_SPLITS_VECTOR,
                 VECTOR_ONLY, RASTER_ONLY, AMBIGUOUS)

# What a disagreement is worth as a lead. Hypotheses, not conclusions.
SPACE_SEPARATION_HYPOTHESIS = "SPACE_SEPARATION_HYPOTHESIS"
MISSING_WALL_HYPOTHESIS = "MISSING_WALL_HYPOTHESIS"
PORTAL_HYPOTHESIS = "PORTAL_HYPOTHESIS"

HYPOTHESIS_KINDS = (SPACE_SEPARATION_HYPOTHESIS, MISSING_WALL_HYPOTHESIS,
                    PORTAL_HYPOTHESIS)

# What raster may never do.
RASTER_MAY_NOT = (
    "supply a released area or perimeter",
    "supply any millimetre of a physical space boundary",
    "establish a room's identity",
    "seed or construct a vector polygon",
)


class SignalError(RuntimeError):
    """A raster observation was asked to be a measurement."""


@dataclass(frozen=True)
class TopologyHypothesis:
    """A lead produced by comparing two representations. Never a conclusion."""

    hypothesis_id: str
    kind: str
    relationship: str
    vector_space_geometry_ids: tuple[str, ...] = ()
    raster_region_ids: tuple = ()
    labelled_space_ids: tuple[str, ...] = ()
    where_mm: tuple | None = None
    why: str = ""

    @property
    def may_supply_measurement(self) -> bool:
        """Always False. The property exists so the answer is explicit."""
        return False

    def record(self) -> dict:
        return {"hypothesis_id": self.hypothesis_id, "kind": self.kind,
                "relationship": self.relationship,
                "vector_space_geometry_ids": list(
                    self.vector_space_geometry_ids),
                "raster_region_ids": list(self.raster_region_ids),
                "labelled_space_ids": list(self.labelled_space_ids),
                "where_mm": (None if self.where_mm is None
                             else [round(v, 1) for v in self.where_mm]),
                "may_supply_measurement": self.may_supply_measurement,
                "why": self.why}


def compare_topology(candidates, regions, *, contains) -> tuple[list, dict]:
    """Relate each free-space component to the labelled raster regions in it.

    `contains(candidate, centroid_mm) -> bool` is supplied by the caller so
    this module needs no geometry kernel of its own.
    """
    labelled = [(r["space_id"], r["centroid_mm"]) for r in regions.values()
                if r.get("space_id")]
    inside: dict = {}
    for c in candidates:
        inside[c.space_geometry_id] = tuple(sorted(
            sid for sid, pt in labelled if contains(c, pt)))
    placed = {sid for ids in inside.values() for sid in ids}

    hyps, rows, n = [], [], 0
    for c in candidates:
        ids = inside[c.space_geometry_id]
        if len(ids) == 1:
            rel, why = AGREES, (
                "one labelled region falls in this component and nothing else "
                "does. The two representations agree about the separation")
        elif len(ids) > 1:
            rel, why = RASTER_SPLITS_VECTOR, (
                f"the segmentation separates {len(ids)} spaces that this "
                "component holds as one. That is a MISSING-WALL hypothesis, "
                "and it is the cheapest lead on the sheet")
            n += 1
            hyps.append(TopologyHypothesis(
                f"TH-{n:04d}", MISSING_WALL_HYPOTHESIS, rel,
                vector_space_geometry_ids=(c.space_geometry_id,),
                labelled_space_ids=ids,
                why=("raster separates these; the vector free space does not. "
                     "Look for an unextracted or unpaired dividing wall — "
                     "raster may NOT supply the boundary itself")))
        else:
            rel, why = VECTOR_ONLY, (
                "no labelled region falls in this component: circulation "
                "nobody labelled, a void, or a component the segmentation "
                "did not produce")
        rows.append({"space_geometry_id": c.space_geometry_id,
                     "geometry_role": c.geometry_role,
                     "clear_internal_area_m2": round(c.area_m2, 3),
                     "labelled_space_ids": list(ids),
                     "relationship": rel, "why": why})

    for sid, _ in sorted(labelled):
        if sid in placed:
            continue
        n += 1
        hyps.append(TopologyHypothesis(
            f"TH-{n:04d}", SPACE_SEPARATION_HYPOTHESIS, RASTER_ONLY,
            labelled_space_ids=(sid,),
            why=(f"{sid} has a raster region and falls inside no free-space "
                 "component at all. Either the envelope excludes it or its "
                 "walls were not recovered")))
        rows.append({"space_geometry_id": "", "geometry_role": "",
                     "clear_internal_area_m2": None,
                     "labelled_space_ids": [sid],
                     "relationship": RASTER_ONLY,
                     "why": "the segmentation has it; the vector result does "
                            "not"})

    summary = {
        "rows": rows,
        "by_relationship": dict(Counter(r["relationship"] for r in rows)),
        "hypotheses": [h.record() for h in hyps],
        "by_hypothesis_kind": dict(Counter(h.kind for h in hyps)),
        "raster_may_not": list(RASTER_MAY_NOT),
        "note": ("raster challenges the vector result and never supplies it. "
                 "Every millimetre in this run came from a drawn wall face"),
    }
    return hyps, summary


def segmentation_vs_validated(*, auto_regions: int, auto_labelled: int,
                              human_identity_validated: int,
                              human_topology_validated: int,
                              validation_source: str) -> dict:
    """Keep the automatic count and the human-validated count apart.

    Quoting 35 identity-validated regions as evidence that automatic raster
    segmentation is accurate would credit the algorithm with a person's work.
    """
    return {
        "RASTER_SEGMENTATION_OUTPUT": {
            "regions_produced": auto_regions,
            "regions_carrying_a_label": auto_labelled,
            "automatic_accuracy_established": False,
            "why": ("the segmentation produced these. NOTHING here says they "
                    "are right: no automatic validation of raster topology "
                    "has been run on this project"),
        },
        "HUMAN_OR_GOLDEN_VALIDATED_REGION_STATE": {
            "identity_validated": human_identity_validated,
            "topology_validated": human_topology_validated,
            "validation_source": validation_source,
            "why": ("established by human review and the golden overlay. "
                    "These figures are evidence about the DRAWING, not about "
                    "the segmentation algorithm"),
        },
        "do_not_conflate": (
            "the validated counts may NOT be quoted as automatic raster "
            "accuracy. That would be circular, and it matters before "
            "generalisation: on an unseen project the human column starts "
            "empty"),
    }
