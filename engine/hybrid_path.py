"""E95 — run the hybrid path end to end, and keep each stage's answer apart.

    raster / vision      ->  TOPOLOGY_REGION          (where the spaces are)
    vector / CAD-like    ->  MEASURED_SPACE_CANDIDATE (what they measure)
    document / AI        ->  observations             (what the sheet says)
    deterministic code   ->  RELEASED_PHYSICAL_SPACE  (what may be quantified)

This module is the orchestration only. Every decision lives in the stage
that owns it: segmentation in `raster_topology`, tracing in
`region_boundary`, selection in `boundary_match`, roles in `space_role`,
release in `space_objects`. Nothing here invents a coordinate, and the
order is fixed so that the automatic topology is hashed BEFORE anything
human or golden is read.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine import boundary_match as bm
from engine import space_role as sr
from engine.region_boundary import simplify, trace
from engine.space_objects import (
    MEASUREMENT_COMPLETE_PRODUCTION, TOPOLOGY_RESOLVED, assess_release,
    summary as objects_summary)


@dataclass
class HybridResult:
    topology: object = None
    regions: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    releases: list = field(default_factory=list)
    roles: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)
    pool: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def by_region(self) -> dict:
        return {c.region_id: c for c in self.candidates}

    def record(self, *, limit: int = 40) -> dict:
        match = bm.MatchReport(candidates=self.candidates)
        return {
            "AUTOMATIC_TOPOLOGY_OUTPUT_HASH": (
                self.topology.output_hash if self.topology else ""),
            "stages": {
                "1_raster_topology": "where the connected spaces are",
                "2_vector_boundary_match": "what each one measures",
                "3_role_and_identity": "what each one physically is",
                "4_release": "which may carry a quantity",
            },
            "objects": objects_summary(
                regions=self.regions, candidates=self.candidates,
                releases=self.releases),
            "vector_candidate_pool": {
                "lines": len(self.pool),
                "by_source": {
                    s: sum(1 for c in self.pool if c.source_type == s)
                    for s in sorted({c.source_type for c in self.pool})},
                "what_a_line_is": (
                    "one DRAWN interval that could be a finish face: a wall "
                    "face over the extent where it was actually drawn, a "
                    "wall end cap, or an opening jamb"),
            },
            "boundary_matching": match.record(limit=limit),
            "unresolved_diagnosis": bm.unresolved_summary(self.unresolved),
            "roles": sr.summary(self.roles),
            "notes": dict(self.notes),
        }


def run(topology, *, wall_polys, caps=(), barriers=(), frame,
        px_mm: float, classify=None, search_window_mm: float | None = None,
        labels_inside=None, portals_of=None, fixtures_of=None) -> HybridResult:
    """Trace, match, classify and assess every automatic region."""
    pool = (bm.candidates_from_walls(wall_polys, classify=classify)
            + bm.candidates_from_caps(caps)
            + bm.candidates_from_portals(barriers))
    kw = ({} if search_window_mm is None
          else {"search_window_mm": search_window_mm})

    res = HybridResult(topology=topology, pool=pool)
    labels_inside = labels_inside or {}

    for region in topology.regions:
        label = topology.region_label_of.get(region.region_id)
        if label is None:
            continue
        runs = simplify(trace(topology.labels, label, frame, px_mm,
                              min_run_px=1))
        cand = bm.match_region(region.region_id, runs, pool, **kw)
        res.candidates.append(cand)
        res.unresolved.append(
            bm.diagnose_unresolved(runs, cand, pool, **kw))

        here = tuple(labels_inside.get(region.region_id, ()))
        res.roles.append(sr.classify_role(
            region,
            portals=(portals_of(region.region_id) if portals_of else
                     len(region.candidate_opening_ids)),
            connects=len(region.adjacent_region_ids),
            fixtures=(fixtures_of(region.region_id) if fixtures_of else 0),
            labels=here,
            enclosed=not region.candidate_opening_ids))

        # A region is TOPOLOGY_RESOLVED once its own outline could be
        # traced and matched at all — which is a statement about the
        # TOPOLOGY, not about the measurement being complete.
        res.regions.append(
            type(region)(**{**region.__dict__,
                            "status": TOPOLOGY_RESOLVED}))

        role = res.roles[-1]
        res.releases.append(assess_release(
            cand, space_id=(here[0] if len(here) == 1 else region.region_id),
            identity_valid=(len(here) == 1 and role.role == sr.ROLE_ROOM),
            portal_evidence_approved=False,
            portal_note=("every portal on this sheet rests on "
                         "SAME_DRAWING evidence only, so no space's "
                         "partition is approved for release")))

    res.notes["regions_traced"] = len(res.candidates)
    res.notes["production_complete"] = sum(
        1 for c in res.candidates
        if c.measurement_status == MEASUREMENT_COMPLETE_PRODUCTION)
    res.notes["order"] = (
        "the automatic topology was hashed before any label, golden region "
        "or benchmark was read. Labels enter only as identity evidence and "
        "as the §16 score's input")
    return res


# ------------------------------------------------------------ §24 the gate

GATE_SUCCESS_CONTROL = "A_RECOVERED_A_CONTROL_AS_A_COMPLETE_MEASURED_SPACE"
GATE_SUCCESS_RECALL = "B_MATERIALLY_MORE_COMPLETE_MEASURED_SPACES"
GATE_SUCCESS_TOPOLOGY = "C_SIGNIFICANTLY_BETTER_TOPOLOGY_RECALL"
GATE_FAILURE = ("MANY_TOPOLOGY_REGIONS_WHOSE_BOUNDARIES_CANNOT_BE_MATCHED"
                "_TO_VECTOR_EVIDENCE_LOCALLY")


def gate(*, controls_complete, complete_measured_spaces,
         deterministic_complete_spaces, topology_recall_pct,
         deterministic_single_room_spaces, expected_spaces,
         mean_boundary_measured_pct) -> dict:
    """§24. Success needs ONE of three; failure has its own condition."""
    met = []
    if controls_complete:
        met.append(GATE_SUCCESS_CONTROL)
    if complete_measured_spaces > deterministic_complete_spaces:
        met.append(GATE_SUCCESS_RECALL)
    det_pct = (100.0 * deterministic_single_room_spaces
               / max(expected_spaces, 1))
    if topology_recall_pct >= det_pct * 2:
        met.append(GATE_SUCCESS_TOPOLOGY)

    # The failure condition is not "not success": it is specifically many
    # regions found and their boundaries unmatchable.
    failed = (not met) and mean_boundary_measured_pct < 50.0
    return {
        "conditions_met": met,
        "verdict": ("SUCCESS" if met else
                    "FAILURE" if failed else "NEITHER_SUCCEEDED_NOR_FAILED"),
        "A_control_recovered_as_a_complete_measured_space": bool(
            controls_complete),
        "B_complete_measured_spaces": {
            "hybrid": complete_measured_spaces,
            "deterministic_vector": deterministic_complete_spaces,
        },
        "C_topology_recall": {
            "hybrid_pct": round(topology_recall_pct, 1),
            "deterministic_pct": round(det_pct, 1),
            "threshold": "at least double the deterministic figure",
        },
        "failure_condition": GATE_FAILURE,
        "failure_condition_met": failed,
        "mean_boundary_measured_pct": round(mean_boundary_measured_pct, 1),
        "what_failure_would_mean": (
            "the next product decision becomes PDF support with "
            "human-assisted boundary confirmation, rather than continuing "
            "to invent automation"),
        "what_neither_means": (
            "a condition was met on finding rooms and not on measuring "
            "them, or the boundaries matched substantially but did not "
            "close. That is progress with a named blocker, and it is "
            "neither the success the round asked for nor the failure it "
            "defined"),
    }
