"""E48 — two statuses, because one word was being used for two questions.

The written report said the workbook was BLOCKED. The workbook's own dashboard
said VALIDATED_PARTIAL. Both were defensible readings of one field, which is
exactly the problem: the field was answering two different questions at once.

    TAKEOFF_COVERAGE_STATUS   how much has the engine validated so far?
                              An internal progress question. VALIDATED_PARTIAL
                              is a normal, useful state — some gross figures
                              are usable internally.

    FINAL_BOQ_STATUS          may a bill of quantities be produced from this?
                              A commercial question, and on 23010 the answer is
                              no, whatever the coverage says.

A project can legitimately be VALIDATED_PARTIAL and BLOCKED_FOR_FINAL_BOQ at
the same time. Collapsing them let progress on the first read as permission on
the second.

FINAL BOQ IS GATED, NOT SCORED. It does not improve gradually with coverage:
every gate must hold, and any one failing blocks the whole thing. That
asymmetry is the point — a takeoff that is 90% covered is 0% quotable.
"""

from __future__ import annotations

from dataclasses import dataclass

COMPLETE = "COMPLETE"
VALIDATED_PARTIAL = "VALIDATED_PARTIAL"
NO_VALIDATED_OUTPUT = "NO_VALIDATED_OUTPUT"

COVERAGE_STATUSES = (COMPLETE, VALIDATED_PARTIAL, NO_VALIDATED_OUTPUT)

READY_FOR_FINAL_BOQ = "READY_FOR_FINAL_BOQ"
BLOCKED_FOR_FINAL_BOQ = "BLOCKED_FOR_FINAL_BOQ"

BOQ_STATUSES = (READY_FOR_FINAL_BOQ, BLOCKED_FOR_FINAL_BOQ)


class StatusError(RuntimeError):
    """A status was claimed that the underlying states do not support."""


@dataclass(frozen=True)
class TopLevelStatus:
    coverage_status: str
    boq_status: str
    coverage_reason: str
    boq_blockers: tuple[str, ...] = ()

    def __post_init__(self):
        if self.boq_status == READY_FOR_FINAL_BOQ and self.boq_blockers:
            raise StatusError(
                "READY_FOR_FINAL_BOQ with blockers still listed: "
                f"{list(self.boq_blockers)}")
        if self.boq_status == BLOCKED_FOR_FINAL_BOQ and not self.boq_blockers:
            raise StatusError(
                "BLOCKED_FOR_FINAL_BOQ naming no blocker. A block that cannot "
                "name its cause cannot be cleared")

    def record(self) -> dict:
        return {"TAKEOFF_COVERAGE_STATUS": self.coverage_status,
                "coverage_reason": self.coverage_reason,
                "FINAL_BOQ_STATUS": self.boq_status,
                "boq_blockers": list(self.boq_blockers)}


def assess(*, uses_total: int, uses_with_ready_spaces: int,
           net_uses_ready: int, validated_physical_spaces: int,
           total_in_scope_spaces: int, openings_validated: int,
           signed_trade_rules: int, unresolved_topology_spaces: int,
           graph_gate_passed: bool,
           openings_deduction_ready: bool = False) -> TopLevelStatus:
    """Both statuses, from the states that actually determine each.

    Coverage is a proportion. BOQ readiness is a conjunction. They are computed
    separately on purpose — no arithmetic connects them, because no amount of
    coverage earns a BOQ.
    """
    if uses_total <= 0:
        raise StatusError("no uses declared; coverage over nothing is not a "
                          "status, it is an empty project")

    if validated_physical_spaces == 0 or uses_with_ready_spaces == 0:
        coverage = NO_VALIDATED_OUTPUT
        creason = ("no use has a ready quantity in any validated physical "
                   "space")
    elif (net_uses_ready > 0
          and uses_with_ready_spaces == uses_total
          and validated_physical_spaces == total_in_scope_spaces):
        coverage = COMPLETE
        creason = "every use is ready in every in-scope space"
    else:
        coverage = VALIDATED_PARTIAL
        creason = (f"{uses_with_ready_spaces} of {uses_total} uses have a ready "
                   f"quantity somewhere; {validated_physical_spaces} of "
                   f"{total_in_scope_spaces} in-scope spaces are validated")

    blockers = []
    # §22 — "no opening validated" became FALSE the moment two portals reached
    # GEOMETRY_VALIDATED, and the sentence was still being printed. The real
    # blocker was never the count: it is that opening DEDUCTIONS are not
    # complete or approved, which no number of validated portals fixes on its
    # own. So the blocker states the actual condition and carries the count.
    if openings_validated == 0:
        blockers.append(
            "no opening is validated anywhere, so every wall figure is GROSS "
            "and no net quantity exists")
    elif openings_deduction_ready is False:
        blockers.append(
            f"{openings_validated} opening(s) are validated, but opening "
            "deductions are not complete or production-approved: no trade's "
            "deduction rule is signed, so no NET quantity may be released "
            "from them")
    if net_uses_ready == 0:
        blockers.append("no NET quantity is ready for any use")
    if signed_trade_rules == 0:
        blockers.append("no trade rule or assembly is signed for this project")
    if unresolved_topology_spaces:
        blockers.append(f"{unresolved_topology_spaces} space(s) have unresolved "
                        "physical topology")
    if not graph_gate_passed:
        blockers.append("the wall graph does not pass its E31A gates, so room "
                        "polygons cannot be reconstructed")

    return TopLevelStatus(
        coverage_status=coverage, coverage_reason=creason,
        boq_status=BLOCKED_FOR_FINAL_BOQ if blockers else READY_FOR_FINAL_BOQ,
        boq_blockers=tuple(blockers))
