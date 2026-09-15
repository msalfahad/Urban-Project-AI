"""E50 — one workbook, one analysis state. Enforced, not hoped for.

The last workbook mixed runs. Wall Extraction QA carried V2 data while the
Exceptions sheet still reported 115 components and 228 termini from V1, and
said planar extraction had not started after it had. Every individual sheet was
internally correct and the workbook as a whole was a lie, which is the worst
shape a report can take: nothing looks wrong.

It happened because each stage wrote its own JSON and the exporter read
whichever files happened to be on disk. Freshness was a property of the
filesystem, not of the data.

So a run now carries LINEAGE. Each stage records the id and content hash of the
stage it consumed, `check()` verifies the chain, and `build_workbook` REFUSES a
bundle whose stages disagree. A stale workbook is not a formatting problem —
it is a decision made on the wrong numbers.

    IF WALL EXTRACTION IS V2 AND THE EXCEPTIONS ARE V1, THE EXPORT FAILS.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

CURRENT_RUN = "CURRENT_RUN"
PRIOR_RUN = "PRIOR_RUN"
SUPERSEDED = "SUPERSEDED"

LINEAGE_CLASSES = (CURRENT_RUN, PRIOR_RUN, SUPERSEDED)

# The stages a workbook depends on, in the order each consumes the last.
#
# `portal_detection` and `space_topology` are named separately from
# `wall_graph` and `topology` on purpose. A space face is produced by a
# DIFFERENT GRAPH from a material face, and a workbook that cannot tell which
# stage a face came from can show a stale material-graph face as the new space
# topology result without anything looking wrong.
STAGES = ("frame", "wall_extraction", "wall_graph", "portal_detection",
          "opening_detection", "space_boundary_graph", "space_topology",
          "topology",
          # The replacement spine, one stage per step. The graph stages
          # above are demoted to DIAGNOSTIC_TOPOLOGY_PATH and may not
          # release geometry.
          #
          # These six are separate on purpose. Collapsing them into
          # "wall_solid" and "free_space" hid where an area came from: a
          # reader could not tell whether an envelope was derived before or
          # after the barriers were applied, and lineage is the point.
          "wall_polygon_run", "wall_solid_run", "portal_partition_run",
          "building_envelope_run", "free_space_run", "space_resolution_run",
          "source_audit", "semantic", "release_matrix")

# Retired stage names, kept so an old manifest can still be read and so a
# reader who greps for them finds out what replaced them rather than
# nothing.
SUPERSEDED_STAGES = {
    "wall_solid": ("wall_polygon_run", "wall_solid_run"),
    "free_space": ("portal_partition_run", "building_envelope_run",
                   "free_space_run", "space_resolution_run"),
}


class ManifestError(RuntimeError):
    """A workbook was assembled from more than one analysis state."""


def content_hash(payload) -> str:
    """A stable hash of a stage's output."""
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


@dataclass(frozen=True)
class StageRecord:
    """One stage, what it produced, and what it consumed.

    `consumed` names the upstream stage hashes this stage was computed from.
    A stage that cannot name them cannot be checked, so the field is required
    for every stage but the first.
    """

    stage: str
    run_id: str
    output_hash: str
    consumed: tuple[tuple[str, str], ...] = ()
    note: str = ""

    def record(self) -> dict:
        return {"stage": self.stage, "run_id": self.run_id,
                "output_hash": self.output_hash,
                "consumed": [list(c) for c in self.consumed],
                "note": self.note}


@dataclass
class RunManifest:
    """Everything a workbook must be able to prove about its own numbers."""

    project_id: str
    drawing_id: str
    drawing_revision: str
    drawing_source_hash: str
    stages: dict = field(default_factory=dict)
    rule_set_versions: dict = field(default_factory=dict)
    # Which length ontology the quantities in this run were measured on. A
    # workbook built before the bases existed measured different things under
    # the same column names.
    measurement_basis_version: str = ""
    generated_at: str = ""

    def add(self, stage: str, run_id: str, payload, *, consumed=(),
            note: str = "") -> StageRecord:
        if stage not in STAGES:
            raise ManifestError(
                f"unknown stage {stage!r}. Known: {STAGES}. A stage nobody "
                "declared cannot be checked for freshness")
        rec = StageRecord(stage, run_id, content_hash(payload),
                          tuple(consumed), note)
        self.stages[stage] = rec
        return rec

    def check(self) -> list[str]:
        """Every complaint about this run's coherence. Empty is the only pass.

        Two things are verified: that each stage consumed the hash its upstream
        actually produced, and that every present stage shares one run id. The
        first catches a stale input; the second catches two runs interleaved.
        """
        out: list[str] = []
        present = {s: r for s, r in self.stages.items()}
        run_ids = {r.run_id for r in present.values()}
        if len(run_ids) > 1:
            out.append(
                f"this workbook mixes {len(run_ids)} analysis runs: "
                f"{sorted(run_ids)}. Every sheet must describe ONE state")
        for stage, rec in present.items():
            for upstream, expected in rec.consumed:
                got = present.get(upstream)
                if got is None:
                    out.append(
                        f"{stage} consumed {upstream}, which is not in this "
                        "manifest at all")
                elif got.output_hash != expected:
                    out.append(
                        f"{stage} was computed from {upstream} "
                        f"{expected}, but this run's {upstream} is "
                        f"{got.output_hash}. The {stage} numbers describe an "
                        "earlier state of the drawing")
        return out

    def assert_coherent(self) -> None:
        problems = self.check()
        if problems:
            raise ManifestError(
                "the workbook would mix analysis runs:\n  - "
                + "\n  - ".join(problems)
                + "\nRe-run the stale stages before exporting. A workbook "
                  "whose sheets disagree is worse than no workbook: nothing "
                  "in it looks wrong.")

    def record(self) -> dict:
        return {
            "project_id": self.project_id, "drawing_id": self.drawing_id,
            "drawing_revision": self.drawing_revision,
            "drawing_source_hash": self.drawing_source_hash,
            "stages": {s: r.record() for s, r in sorted(self.stages.items())},
            "rule_set_versions": dict(self.rule_set_versions),
            "measurement_basis_version": self.measurement_basis_version,
            "workbook_generated_at": self.generated_at
            or datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "coherent": not self.check(),
            "problems": self.check(),
        }


def lineage_of(row_run_id: str, manifest: RunManifest) -> str:
    """Is a finding's run this run, an earlier one, or superseded?"""
    current = {r.run_id for r in manifest.stages.values()}
    if not row_run_id:
        return SUPERSEDED
    return CURRENT_RUN if row_run_id in current else PRIOR_RUN
