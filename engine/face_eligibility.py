"""E31A gating — local, per component, and split from project release.

The old gate answered one question and was used for two:

    can we safely BUILD and TEST the face engine?   -> E31A_ENGINE_DEVELOPMENT
    can 23010 RELEASE quantities from the result?   -> PROJECT_TOPOLOGY_RELEASE

Conflating them meant 109 unresolved termini somewhere on the sheet blocked
testing the face walker on a closed bathroom on the other side of the building.
Most of those termini belong to components that will never bound a room.

So eligibility is LOCAL. A bad component must not stop the engine working on a
good one, and each component gets its own verdict with its own reasons:

    FACE_ELIGIBLE         walk it; the result is still only a hypothesis
    FACE_HYPOTHESIS_ONLY  walk it, but something it depends on is unproven
    FACE_BLOCKED          do not walk it, and say what is missing

PRODUCTION RELEASE GATES ARE NOT WEAKENED BY ANY OF THIS. Every face this
engine produces is unreleasable by construction — `Face.releasable` returns
False always — and the project release status keeps the whole-sheet gates it
had.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

FACE_ELIGIBLE = "FACE_ELIGIBLE"
FACE_HYPOTHESIS_ONLY = "FACE_HYPOTHESIS_ONLY"
FACE_BLOCKED = "FACE_BLOCKED"

# Engine development status — may we build and test?
READY_FOR_DIAGNOSTIC_RUN = "READY_FOR_DIAGNOSTIC_RUN"
NOT_ENOUGH_LOCAL_TOPOLOGY = "NOT_ENOUGH_LOCAL_TOPOLOGY"

# Project topology release status — may a quantity come out of it?
TOPOLOGY_RELEASE_BLOCKED = "BLOCKED"
TOPOLOGY_RELEASE_PARTIAL = "VALIDATED_PARTIAL"
TOPOLOGY_RELEASE_READY = "READY"


class EligibilityError(RuntimeError):
    """A component was admitted or refused without a stated reason."""


@dataclass(frozen=True)
class ComponentEligibility:
    component_id: str
    verdict: str
    edges: int
    independent_cycles: int
    termini: int
    unresolved_termini: int
    ambiguous_stitches: int
    rejected_clusters: int
    total_length_m: float
    reasons: tuple[str, ...] = ()
    affected_space_ids: tuple[str, ...] = ()

    def __post_init__(self):
        if self.verdict != FACE_ELIGIBLE and not self.reasons:
            raise EligibilityError(
                f"{self.component_id}: {self.verdict} with no reason. A "
                "component refused without a reason cannot be repaired")

    def record(self) -> dict:
        return {"component_id": self.component_id, "verdict": self.verdict,
                "edges": self.edges,
                "independent_cycles": self.independent_cycles,
                "termini": self.termini,
                "unresolved_termini": self.unresolved_termini,
                "ambiguous_stitches": self.ambiguous_stitches,
                "rejected_clusters": self.rejected_clusters,
                "total_length_m": round(self.total_length_m, 2),
                "affected_space_ids": list(self.affected_space_ids),
                "reasons": list(self.reasons)}


def assess_components(*, components, cycles=(), termini=(), stitches=(),
                      length_drift_mm: float = 0.0,
                      region_points=None) -> list[ComponentEligibility]:
    """One verdict per component, from that component's own health.

    The whole-sheet numbers appear here only where they genuinely apply to
    every component: unexplained length drift is global, because a wall that
    vanished could have vanished from anywhere.
    """
    by_edge_term: dict[str, list] = {}
    for t in termini:
        by_edge_term.setdefault(t.edge_id, []).append(t)
    amb_by_edge: dict[str, int] = {}
    for s in stitches:
        if s.status == "STITCH_AMBIGUOUS":
            amb_by_edge[s.edge_a] = amb_by_edge.get(s.edge_a, 0) + 1
            amb_by_edge[s.edge_b] = amb_by_edge.get(s.edge_b, 0) + 1

    out: list[ComponentEligibility] = []
    for c in components:
        # The component's OWN cycle count. Reading it from a separately-sorted
        # list by index paired every component with another one's numbers.
        cycles_here = c.independent_cycles
        edges = set(c.edge_ids)
        terms = [t for e in edges for t in by_edge_term.get(e, ())]
        unresolved = [t for t in terms if t.kind == "UNRESOLVED"]
        amb = sum(amb_by_edge.get(e, 0) for e in edges)

        spaces = ()
        if region_points:
            x0, y0, x1, y1 = c.bbox_mm
            spaces = tuple(sorted(
                sid for sid, (px, py) in region_points.items()
                if x0 <= px <= x1 and y0 <= py <= y1))

        reasons = []
        if length_drift_mm and abs(length_drift_mm) > 1.0:
            reasons.append(
                f"unexplained wall-length drift of {length_drift_mm:.1f} mm on "
                "the sheet: a wall that vanished could have vanished from here")
        if cycles_here == 0:
            reasons.append(
                "no independent cycle: this component is a tree and bounds no "
                "face however much wall it holds")

        if cycles_here == 0 or (length_drift_mm and abs(length_drift_mm) > 1.0):
            verdict = FACE_BLOCKED
        elif unresolved or amb:
            verdict = FACE_HYPOTHESIS_ONLY
            if unresolved:
                reasons.append(
                    f"{len(unresolved)} unresolved terminus/termini on this "
                    "component: a face here may be bounded by a wall end "
                    "nobody has classified")
            if amb:
                reasons.append(
                    f"{amb} ambiguous stitch reference(s): closing this "
                    "component may depend on a gap that has not been resolved")
        else:
            verdict = FACE_ELIGIBLE

        out.append(ComponentEligibility(
            component_id=c.component_id, verdict=verdict, edges=len(edges),
            independent_cycles=cycles_here, termini=len(terms),
            unresolved_termini=len(unresolved), ambiguous_stitches=amb,
            rejected_clusters=0,
            total_length_m=c.total_length_mm / 1000,
            reasons=tuple(reasons), affected_space_ids=spaces))
    return out


def engine_development_status(eligibility) -> dict:
    """May we build and test the face engine? A LOCAL question.

    Yes as soon as one component can be walked. Waiting for the whole sheet
    would mean building the engine blind and discovering its bugs later, on
    harder geometry, with nothing known-good to compare against.
    """
    usable = [e for e in eligibility
              if e.verdict in (FACE_ELIGIBLE, FACE_HYPOTHESIS_ONLY)]
    eligible = [e for e in eligibility if e.verdict == FACE_ELIGIBLE]
    return {
        "E31A_ENGINE_DEVELOPMENT_STATUS": (
            READY_FOR_DIAGNOSTIC_RUN if usable else NOT_ENOUGH_LOCAL_TOPOLOGY),
        "why": (f"{len(eligible)} component(s) fully eligible and "
                f"{len(usable) - len(eligible)} walkable as hypothesis only, "
                f"out of {len(eligibility)}"
                if usable else
                "no component has an independent cycle, so there is no face to "
                "walk anywhere on the sheet"),
        "components_eligible": len(eligible),
        "components_hypothesis_only": len(usable) - len(eligible),
        "components_blocked": len(eligibility) - len(usable),
        "by_verdict": dict(Counter(e.verdict for e in eligibility)),
    }


def project_release_status(gate: dict, eligibility) -> dict:
    """May 23010 release quantities from topology? A WHOLE-SHEET question.

    Unchanged and unweakened. It reads the same E31A gates it always did: a
    face produced from a locally healthy component is still a hypothesis, and
    a hypothesis does not become a quantity because the engine that made it
    ran cleanly.
    """
    failed = list(gate.get("failed", ()))
    unmeasured = list(gate.get("not_measured", ()))
    blockers = []
    if failed:
        blockers.append("failing gates: " + ", ".join(failed))
    if unmeasured:
        blockers.append("not yet measured: " + ", ".join(unmeasured))
    hypothesis = [e for e in eligibility if e.verdict == FACE_HYPOTHESIS_ONLY]
    if hypothesis:
        blockers.append(
            f"{len(hypothesis)} component(s) can only produce hypothesis faces")
    return {
        "PROJECT_TOPOLOGY_RELEASE_STATUS": (
            TOPOLOGY_RELEASE_BLOCKED if blockers else TOPOLOGY_RELEASE_READY),
        "blockers": blockers,
        "why": ("every face this engine produces is unreleasable by "
                "construction; migration to a measurement basis is explicit "
                "and has not happened"),
    }
