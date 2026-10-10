"""E48 — four statuses, because one word was being used for four questions.

The written report said the workbook was BLOCKED. The workbook's own dashboard
said VALIDATED_PARTIAL. Both were defensible readings of one field, which is
exactly the problem: the field was answering two different questions at once.

    GEOMETRY_MECHANISM_PROVEN does the measurement METHOD work? Its
                              invariants hold, a control was frozen before
                              any reference was opened, and the disagreement
                              with that reference is decomposed and
                              attributed. This is a claim about the
                              mechanism and about nothing else.

    PROJECT_SPACE_RECALL      how many of THIS floor's rooms came out as
                              their own polygon? A proven mechanism can still
                              return four rooms out of thirty-six, and it
                              does: most components hold several merged
                              rooms.

    TAKEOFF_COVERAGE_STATUS   how much has the engine validated so far?
                              An internal progress question. VALIDATED_PARTIAL
                              is a normal, useful state — some gross figures
                              are usable internally.

    FINAL_BOQ_STATUS          may a bill of quantities be produced from this?
                              A commercial question, and on 23010 the answer is
                              no, whatever the others say.

The first two are the pair most easily confused, and the confusion runs one
way: a round that proves the method reads as a round that measured the
building. It did not. GEOMETRY_MECHANISM_PROVEN = PASS beside
PROJECT_SPACE_RECALL = PARTIAL is the honest pair of sentences.

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

MECHANISM_PROVEN = "PASS"
MECHANISM_NOT_PROVEN = "FAIL"
MECHANISM_STATUSES = (MECHANISM_PROVEN, MECHANISM_NOT_PROVEN)

RECALL_COMPLETE = "COMPLETE"
RECALL_PARTIAL = "PARTIAL"
RECALL_NONE = "NONE"
RECALL_STATUSES = (RECALL_COMPLETE, RECALL_PARTIAL, RECALL_NONE)


class StatusError(RuntimeError):
    """A status was claimed that the underlying states do not support."""


@dataclass(frozen=True)
class TopLevelStatus:
    coverage_status: str
    boq_status: str
    coverage_reason: str
    boq_blockers: tuple[str, ...] = ()
    mechanism_status: str = MECHANISM_NOT_PROVEN
    mechanism_reason: str = ""
    recall_status: str = RECALL_NONE
    recall_reason: str = ""

    def __post_init__(self):
        if (self.mechanism_status == MECHANISM_PROVEN
                and self.recall_status == RECALL_COMPLETE
                and self.boq_status == BLOCKED_FOR_FINAL_BOQ
                and not self.boq_blockers):
            raise StatusError(
                "a proven mechanism with complete recall and no named "
                "blocker cannot be BLOCKED")
        if self.boq_status == READY_FOR_FINAL_BOQ and self.boq_blockers:
            raise StatusError(
                "READY_FOR_FINAL_BOQ with blockers still listed: "
                f"{list(self.boq_blockers)}")
        if self.boq_status == BLOCKED_FOR_FINAL_BOQ and not self.boq_blockers:
            raise StatusError(
                "BLOCKED_FOR_FINAL_BOQ naming no blocker. A block that cannot "
                "name its cause cannot be cleared")

    def record(self) -> dict:
        return {"GEOMETRY_MECHANISM_PROVEN": self.mechanism_status,
                "mechanism_reason": self.mechanism_reason,
                "PROJECT_SPACE_RECALL": self.recall_status,
                "recall_reason": self.recall_reason,
                "TAKEOFF_COVERAGE_STATUS": self.coverage_status,
                "coverage_reason": self.coverage_reason,
                "FINAL_BOQ_STATUS": self.boq_status,
                "boq_blockers": list(self.boq_blockers),
                "these_are_four_questions": (
                    "a proven MECHANISM is not a measured PROJECT, a "
                    "measured project is not full COVERAGE, and full "
                    "coverage is not permission to BILL. Any one of them "
                    "read as another is how a method that works becomes a "
                    "floor that is finished")}


def assess(*, uses_total: int, uses_with_ready_spaces: int,
           net_uses_ready: int, validated_physical_spaces: int,
           total_in_scope_spaces: int, openings_validated: int,
           signed_trade_rules: int, unresolved_topology_spaces: int,
           graph_gate_passed: bool = True,
           openings_deduction_ready: bool = False,
           free_space_invariants_hold: bool | None = None,
           controls_frozen: int = 0, controls_accepted: int = 0,
           single_room_space_geometries: int | None = None,
           ) -> TopLevelStatus:
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
    # The graph gate is NOT a BOQ blocker any more, and saying it was is
    # what made the workbook's authority mixed. Room polygons do not come
    # from the wall graph: they come from the free-space path, and the graph
    # path is a diagnostic whose invariants are falsified on this drawing.
    # Blocking the BOQ on a diagnostic's gate would hold the project on a
    # condition nothing downstream depends on, while leaving the condition
    # that matters unstated.
    if free_space_invariants_hold is False:
        blockers.append(
            "the free-space construction's invariants do not hold, so no "
            "area it produced may be quoted at all")

    # GEOMETRY_MECHANISM_PROVEN — about the METHOD, not about the floor.
    if free_space_invariants_hold is None:
        mech, mreason = MECHANISM_NOT_PROVEN, (
            "the free-space invariants were not run, so the mechanism is "
            "unproven — not failed, unproven")
    elif not free_space_invariants_hold:
        mech, mreason = MECHANISM_NOT_PROVEN, (
            "the free-space construction's invariants do not hold")
    elif controls_accepted <= 0:
        mech, mreason = MECHANISM_NOT_PROVEN, (
            f"the invariants hold and {controls_frozen} control(s) were "
            "frozen, but none was accepted, so nothing has been measured "
            "against a reference under freeze discipline")
    else:
        mech, mreason = MECHANISM_PROVEN, (
            f"the free-space invariants hold and {controls_accepted} of "
            f"{controls_frozen} control(s) were frozen and accepted BEFORE "
            "any reference was opened. This says the METHOD works. It says "
            "nothing about how much of this floor it resolved")

    # PROJECT_SPACE_RECALL — about the floor, not about the method.
    got = (0 if single_room_space_geometries is None
           else single_room_space_geometries)
    if single_room_space_geometries is None:
        recall, rreason = RECALL_NONE, (
            "the count of single-room space geometries was not supplied")
    elif got <= 0:
        recall, rreason = RECALL_NONE, (
            "no space geometry holds exactly one labelled room")
    elif total_in_scope_spaces and got >= total_in_scope_spaces:
        recall, rreason = RECALL_COMPLETE, (
            f"all {total_in_scope_spaces} in-scope space(s) came out as "
            "their own polygon")
    else:
        recall, rreason = RECALL_PARTIAL, (
            f"{got} of {total_in_scope_spaces} in-scope space(s) came out as "
            "their own polygon. The rest are inside components holding "
            "several merged rooms, and a merged component's area is not a "
            "room's area")

    return TopLevelStatus(
        coverage_status=coverage, coverage_reason=creason,
        boq_status=BLOCKED_FOR_FINAL_BOQ if blockers else READY_FOR_FINAL_BOQ,
        boq_blockers=tuple(blockers),
        mechanism_status=mech, mechanism_reason=mreason,
        recall_status=recall, recall_reason=rreason)
