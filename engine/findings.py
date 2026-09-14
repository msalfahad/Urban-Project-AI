"""E49 — exceptions generated from the current diagnostic, never hand-written.

The workbook's top exception said the wall graph was broken because "wall faces
are drawn as thousands of short segments". The same round's diagnostic had
disproved that: heavy-pen wall paths are not fragmented at all, the tiny
segments are glyph outlines and fine detail, and the real cause was missing
wall end caps. A superseded explanation had survived into a new workbook,
sounding exactly as authoritative as a true one.

It survived because it was PROSE I TYPED, sitting in a list, with nothing tying
it to a measurement. So the fix is structural rather than editorial:

    a finding is DERIVED from a diagnostic run, or it does not exist

Every finding carries `diagnostic_run_id`, `finding_id` and
`evidence_reference`, and its narrative is composed from the numbers in that
run. Re-run the diagnostic and the narrative changes with it; fail to re-run
and `stale_against()` says so rather than letting the old text through.

AND: ENGINEERING ACTION IS NOT OWNER ACTION.

The same exception listed "supply DXF/DWG of AR-00" as the owner action, which
quietly said the PDF pipeline cannot proceed. It can, and it must — a stronger
source must never be made to look mandatory when the engine has work left to
do. Three fields now, not one:

    engineering_next_action          what WE do next. Always present.
    owner_input_required             what only the owner can decide. Often none.
    owner_input_helpful_if_available what would make it easier. Never a blocker.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# WHERE A FINDING COMES FROM. The Exceptions sheet defaults to
# CURRENT_DIAGNOSTIC plus unresolved GOLDEN_KNOWN_DEFECTs; a LEGACY_HYPOTHESIS
# may be kept for history but must never be presented as a current cause.
#
# This exists because a sentence survived two rounds after being disproved:
# "the wash room's south edge is a dashed threshold" was still being printed as
# the cause after this project measured ZERO dashed strokes on the sheet and
# found the nearby marks to be shaft hatch.
CURRENT_DIAGNOSTIC = "CURRENT_DIAGNOSTIC"
GOLDEN_KNOWN_DEFECT = "GOLDEN_KNOWN_DEFECT"
LEGACY_HYPOTHESIS = "LEGACY_HYPOTHESIS"
HUMAN_NOTE = "HUMAN_NOTE"
SUPERSEDED = "SUPERSEDED"

PROVENANCE_CLASSES = (CURRENT_DIAGNOSTIC, GOLDEN_KNOWN_DEFECT,
                      LEGACY_HYPOTHESIS, HUMAN_NOTE, SUPERSEDED)

# Which classes may appear as a CURRENT cause.
CURRENT_CLASSES = (CURRENT_DIAGNOSTIC, GOLDEN_KNOWN_DEFECT, HUMAN_NOTE)

BLOCKING = "BLOCKING"
UNDERSTATED = "UNDERSTATES_A_QUANTITY"
ADVISORY = "ADVISORY"

SEVERITIES = (BLOCKING, UNDERSTATED, ADVISORY)


class FindingError(RuntimeError):
    """A finding was asserted without a measurement behind it."""


@dataclass(frozen=True)
class Finding:
    """One defect, tied to the run that measured it."""

    finding_id: str
    diagnostic_run_id: str
    severity: str
    area: str
    subject: str
    issue: str
    cause: str
    effect: str
    evidence_reference: str
    engineering_next_action: str
    owner_input_required: str = ""
    owner_input_helpful_if_available: str = ""
    affected_spaces: int | None = None
    affected_uses: int | None = None
    affected_boq_sections: str = ""
    coverage_unlocked: str = ""
    status: str = "OPEN"
    provenance_class: str = CURRENT_DIAGNOSTIC
    superseded_by: str = ""
    superseded_because: str = ""

    def __post_init__(self):
        if self.provenance_class not in PROVENANCE_CLASSES:
            raise FindingError(
                f"{self.finding_id}: provenance_class "
                f"{self.provenance_class!r} must be one of "
                f"{PROVENANCE_CLASSES}")
        if self.provenance_class == SUPERSEDED and not self.superseded_because:
            raise FindingError(
                f"{self.finding_id} is SUPERSEDED without saying why. A "
                "retired explanation that does not say what retired it reads "
                "exactly like a current one")
        if not self.diagnostic_run_id:
            raise FindingError(
                f"{self.finding_id} names no diagnostic run. A cause with no "
                "measurement behind it is the stale-prose failure again")
        if not self.evidence_reference:
            raise FindingError(
                f"{self.finding_id} cites no evidence. The narrative must be "
                "checkable against the numbers that produced it")
        if not self.engineering_next_action:
            raise FindingError(
                f"{self.finding_id} states no engineering action. Every finding "
                "has something WE can do next, even if the owner also has "
                "something to supply")
        if self.severity not in SEVERITIES:
            raise FindingError(f"{self.finding_id}: unknown severity "
                               f"{self.severity!r}")

    @property
    def is_current_cause(self) -> bool:
        """May this be presented as a CURRENT cause?

        A superseded hypothesis may be kept for history. It may not be printed
        where a reader will take it for the reason something is broken.
        """
        return self.provenance_class in CURRENT_CLASSES

    def stale_against(self, run_id: str) -> bool:
        """Measured by a different run than the current one?

        A GOLDEN_KNOWN_DEFECT is not stale for having an older run id: it is a
        standing defect recorded against the golden fixture, not a measurement
        of this run.
        """
        if self.provenance_class in (GOLDEN_KNOWN_DEFECT, HUMAN_NOTE):
            return False
        return self.diagnostic_run_id != run_id

    def record(self) -> dict:
        return {"finding_id": self.finding_id,
                "diagnostic_run_id": self.diagnostic_run_id,
                "severity": self.severity, "area": self.area,
                "subject": self.subject, "issue": self.issue,
                "cause": self.cause, "effect": self.effect,
                "evidence_reference": self.evidence_reference,
                "engineering_next_action": self.engineering_next_action,
                "owner_input_required": self.owner_input_required,
                "owner_input_helpful_if_available":
                    self.owner_input_helpful_if_available,
                "affected_spaces": self.affected_spaces,
                "affected_uses": self.affected_uses,
                "affected_boq_sections": self.affected_boq_sections,
                "coverage_unlocked": self.coverage_unlocked,
                "status": self.status,
                "provenance_class": self.provenance_class,
                "is_current_cause": self.is_current_cause,
                "superseded_by": self.superseded_by,
                "superseded_because": self.superseded_because}


def from_graph_diagnostic(diagnostic: dict, *, run_id: str,
                          reference: str, space_count: int,
                          use_count: int) -> list[Finding]:
    """Compose the graph findings from THIS run's numbers.

    Every sentence below is built from a value in `diagnostic`. There is no
    stored prose to go stale, because there is no stored prose.
    """
    conn = diagnostic.get("connectivity", {})
    h = diagnostic.get("noded_graph", {})
    src = diagnostic.get("source", {})
    stitch = diagnostic.get("stitching", {})
    gate = diagnostic.get("e31a_gate", {})
    frag = src.get("path_fragmentation", {})
    caps = diagnostic.get("end_caps", {})
    out: list[Finding] = []
    n = 0

    def add(**kw):
        nonlocal n
        n += 1
        out.append(Finding(finding_id=f"F-{run_id}-{n:03d}",
                           diagnostic_run_id=run_id,
                           evidence_reference=reference, **kw))

    comps = conn.get("components")
    major = conn.get("major_components")
    share = conn.get("share_of_length_in_major_components_pct")
    unexplained = conn.get("cause_histogram", {}).get("J_UNRESOLVED", 0)
    if comps:
        add(severity=BLOCKING, area="TOPOLOGY",
            subject="Vector wall graph connectivity",
            issue=(f"The wall graph is in {comps} components; {major} of them "
                   f"hold {share}% of the wall length."),
            cause=(f"Measured this run: source-path fragmentation is NOT the "
                   f"cause — only "
                   f"{frag.get('short_in_a_path_that_also_has_a_long_run')} of "
                   f"{frag.get('short_segments')} short marks share a path with "
                   f"a long run. {caps.get('found')} wall end caps were "
                   "recovered, a representation the pairing engine previously "
                   "had no way to express, and a wall end it cannot see is a "
                   "break in the graph."),
            effect=("Planar face extraction cannot reconstruct room polygons "
                    "from a graph whose cycles are incomplete, so no net "
                    "quantity can be built on it."),
            engineering_next_action=(
                f"Reduce the {unexplained} unexplained components and the "
                f"{conn.get('terminus_histogram', {}).get('UNRESOLVED')} "
                "unresolved termini: integrate dashed topology candidates and "
                "build the building-envelope classifier."),
            owner_input_helpful_if_available=(
                "An architectural DWG/DXF of AR-00 would make wall "
                "connectivity exact rather than reconstructed. It is NOT "
                "required — the PDF pipeline continues either way."),
            affected_spaces=space_count, affected_uses=use_count,
            affected_boq_sections="all wall and finish sections",
            coverage_unlocked="every net quantity on the project")

    hist = conn.get("terminus_histogram", {})
    unres = hist.get("UNRESOLVED")
    if unres:
        add(severity=BLOCKING, area="TOPOLOGY",
            subject="Unclassified wall ends",
            issue=(f"{unres} of {conn.get('termini')} termini are unresolved; "
                   f"{hist.get('LIKELY_MISSING_CONNECTION')} have a likely "
                   "missing connection."),
            cause=(f"{hist.get('EXTERIOR_END')} termini are classified as "
                   "exterior ends because the building-envelope classifier "
                   "does not exist yet, so every genuinely external wall end "
                   "falls through to UNRESOLVED."),
            effect=("An unclassified wall end is an open face boundary of "
                    "unknown cause: the walk cannot tell a doorway from a "
                    "missing wall, and one closes a room while the other "
                    "leaves it open."),
            engineering_next_action=(
                "Build the building envelope so termini can separate "
                "INTERIOR_END, EXTERIOR_END and OPENING_END with provenance."),
            affected_spaces=space_count, affected_uses=use_count,
            coverage_unlocked="terminus classification gate G3")

    if stitch:
        amb = stitch.get("STITCH_AMBIGUOUS", 0)
        if amb:
            add(severity=ADVISORY, area="TOPOLOGY",
                subject="Ambiguous wall stitches",
                issue=(f"{amb} stitch candidates are ambiguous, "
                       f"{stitch.get('ambiguous_because_door_sized')} of them "
                       "because the gap is door-sized."),
                cause=("A door-sized gap is exactly what an opening looks "
                       "like, and stitching it shut would erase the opening "
                       f"the engine is looking for. {stitch.get('rejected_by_end_cap')} "
                       "further candidates were rejected outright by an end "
                       "cap that says the wall stops there."),
                effect=("These gaps stay open until opening evidence resolves "
                        "them. No wall length is invented across them."),
                engineering_next_action=(
                    "Integrate dashed topology candidates as a second evidence "
                    "family, then re-run stitching."),
                owner_input_helpful_if_available=(
                    "A door/window schedule would resolve these directly."),
                affected_spaces=space_count,
                coverage_unlocked="opening validation")

    if gate and not gate.get("ready_for_e31a", True):
        add(severity=BLOCKING, area="GATE",
            subject="E31A readiness",
            issue=f"{gate.get('verdict')}",
            cause=("Failing gates: " + ", ".join(gate.get("failed", []))
                   + ". Not yet measurable: "
                   + ", ".join(gate.get("not_measured", []))),
            effect=("Planar face extraction is not started. Building it on "
                    "this graph would prove the face walker runs and produce "
                    "no faces."),
            engineering_next_action=(
                "Clear the failing gates: "
                + (", ".join(gate.get("failed", [])) or "none")
                + (". Still unmeasured: " + ", ".join(gate["not_measured"])
                   if gate.get("not_measured") else
                   ". Every gate is now measurable.")),
            affected_spaces=space_count, affected_uses=use_count,
            coverage_unlocked="room polygon reconstruction")

    if h.get("duplicate_removed_length_mm"):
        add(severity=ADVISORY, area="GEOMETRY",
            subject="Duplicate wall length removed",
            issue=(f"{h['duplicate_removed_length_mm']:.0f} mm of wall was "
                   "removed as duplicate geometry."),
            cause="Coincident edges: the same wall was in the graph twice.",
            effect=(f"Accounted for explicitly. Unexplained drift is "
                    f"{h.get('length_difference_mm')} mm."),
            engineering_next_action=(
                "No action: the removal is itemised per merged edge and the "
                "length invariant holds."),
            status="ACCOUNTED_FOR")
    return out


def summary(findings: list[Finding], *, current_run_id: str) -> dict:
    return {
        "findings": len(findings),
        "by_severity": dict(Counter(f.severity for f in findings)),
        "by_area": dict(Counter(f.area for f in findings)),
        "by_provenance_class": dict(Counter(f.provenance_class
                                            for f in findings)),
        "presentable_as_current_cause": sum(1 for f in findings
                                            if f.is_current_cause),
        "stale": [f.finding_id for f in findings
                  if f.stale_against(current_run_id)],
        "needing_owner_input": sum(1 for f in findings
                                   if f.owner_input_required),
        "with_engineering_action": sum(
            1 for f in findings if f.engineering_next_action),
    }
