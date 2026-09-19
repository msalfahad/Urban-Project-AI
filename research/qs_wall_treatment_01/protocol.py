"""P7757_WALL_TREATMENT_ESTIMATE_01 - the phase after the owner-input gate.

Continues from the frozen state the long-horizon orchestrator verified from
disk (see VERIFIED_INPUTS): the A21 trace pilot, its final validator, and
the deterministic path that ended at the owner-input gate. The owner has
now answered the gate (see owner_parameters), reviewed the CASE-6 overlay
and set the rule TRACE OVERLAP != MATERIAL OVERLAP, and authorised the
architectural DWG on a deterministic CAD path for exact curves.

What this phase produces, in order:

    OVERLAP_AUDIT             material-role exclusivity over the traces
    DIMENSION_OWNER_REGISTER  which element each printed height belongs to
    CAD_CURVE_REGISTER        exact arc lengths from the DWG, kept apart
    SOURCE_INVENTORY          what documents exist, what is NOT PROVIDED
    P7757_WALL_TREATMENT_ESTIMATE   per face / zone / floor / trade / project
    QS_TRACE.md               the human-readable derivation
    SENSITIVITY               scenario mode only
    FREEZE                    hashes of everything above
    A22_STRUCTURAL_COMPARISON then, and only then, the benchmark unseal

    python3 -m research.qs_wall_treatment_01.run_all
"""

from __future__ import annotations

PHASE_ID = "P7757_WALL_TREATMENT_ESTIMATE_01"
PROJECT_ID = "P7757"

# §0 - what the orchestrator verified from disk before anything new
VERIFIED_INPUTS = {
    "GIT_HEAD_EXPECTED": "bcc2578",
    "TRACE_PILOT_REPORT_SHA256_PREFIX": "6b21ce40",
    "FINAL_VALIDATOR_SHA256_PREFIX": "25fc1bce",
    "DETERMINISTIC_PATH_FREEZE_SHA256_PREFIX": "4207b1bd",
}

TRACE_REGISTER = "data/experiments/A21_TRACE_SUFFICIENCY_01/TRACE_REGISTER.json"
CASE_SANDBOX = "data/experiments/A21_TRACE_SUFFICIENCY_01/case_sandbox"
OUT_DIR = "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01"

CASES = ("CASE-1-NORMAL-PLASTER", "CASE-3-DOOR-AND-WINDOW", "CASE-4-STAIR",
         "CASE-6-ROOF-PARAPET")

STANDING_PROHIBITIONS = (
    "the frozen A21 raw outputs and register are never edited",
    "DWG answers are never fed back into frozen A21",
    "E1.4 is not modified and not exposed to A21",
    "no production BOQ, no APPROVED_BOQ, no Firebase write",
    "no historic P7757 manual value repairs geometry",
    "the benchmark stays sealed until A22 is frozen",
    "a smaller partial quantity with truthful unresolved scope is better "
    "than a complete fabricated total",
)

PARTIAL_QUANTITY_ARCHITECTURE = (
    "every quantity line carries ESTABLISHED_SUBTOTAL, COMPLETE_TOTAL_STATUS, "
    "COVERAGE_STATUS and UNRESOLVED_SCOPE. An established subtotal is never "
    "called the total, and a total is never reported where scope is unresolved")

THREE_STATUS_FAMILIES_KEPT_APART = (
    "TEXT_READ_ESTABLISHED (the value was read), DIMENSION_OWNER_STATUS (the "
    "value belongs to that element), CAD_GEOMETRY_STATUS (the DWG establishes "
    "the curve) are three different facts and are never merged")
