"""QS_MEASUREMENT_REGION_EXPERIMENT_01 - declared before anything is built.

The question is NOT whether any quantity is correct. Nothing here computes
an area, a length total for a trade, or a quantity of any kind.

The question is whether the owner's real manual AutoCAD workflow

    PHYSICAL / TOPOLOGICAL MODEL
            -> TRADE-SPECIFIC MEASUREMENT REGION
            -> QUANTITY ENGINE

can be represented deterministically WITHOUT contaminating physical
topology. The experiment therefore measures the SEPARATION, not the
numbers.
"""

from __future__ import annotations

import hashlib

EXPERIMENT_ID = "QS_MEASUREMENT_REGION_EXPERIMENT_01"
EXPERIMENT_CLASS = "ARCHITECTURE_SEPARATION_TEST_NOT_A_QUANTITY_RUN"
PROTOCOL_VERSION = 1

THE_PURPOSE = (
    "to test whether a trade-specific measurement region can be built "
    "deterministically on top of a frozen physical/topological model "
    "without changing it, without repairing it, and without borrowing "
    "any of its authority")

WHAT_THIS_IS_NOT = (
    "it is not a quantity run. No area is computed. No length is summed "
    "for any trade. No known room value is opened, compared or "
    "approached. A measurement region that closes is not thereby correct "
    "and is not thereby evidence that anything physical exists")

# ==================================================================
# 1. the frozen input - section 1
# ==================================================================

E1_4_DIR = "data/runs/7757/e1_4"

INPUTS_ALLOWED = (
    "E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json",
    "E1_4_GAP_ONTOLOGY_REGISTER.json",
    "E1_4_PORTAL_EVIDENCE_REGISTER.json",
    "E1_4_DOOR_ENTITY_REGISTER.json",
    "E1_4_WALL_END_REGISTER.json",
    "E1_4_COMPLETENESS_REGISTER.json",
    "E1_4_OPENING_DISCOVERY_REGISTER.json",
    "E1_4_BOUNDARY_CAPABILITY_REGISTER.json",
    "E1_4_INPUT_MANIFEST.json",
    "E1_4_FREEZE.json",
)

INPUTS_FORBIDDEN = (
    "any A19 semantic answer, from any experiment",
    "any reference or checker reading from the SAFETY_SAMPLE rounds",
    "any prior human Excel quantity",
    "any manual benchmark area",
    "any known Kitchen, Salon, Pantry or other target value",
    "closure success as evidence of physical truth",
    "room area as a criterion for choosing a closure",
)

NOTHING_IS_WRITTEN_BACK = (
    "this experiment reads the E1.4 registers and writes only inside its "
    "own directory. E1.4 is not modified, not re-run and not re-derived. "
    "E1.5 is not created")

# ==================================================================
# 2. the three layers - section 2
# ==================================================================

LAYER_A = "PHYSICAL_TOPOLOGY"
LAYER_B = "QS_MEASUREMENT_TOPOLOGY"
LAYER_C = "TRADE_QUANTITY_BASIS"

LAYERS = (
    (LAYER_A, "what exists physically and how spaces connect. IMMUTABLE "
              "in this experiment"),
    (LAYER_B, "synthetic constructs used only to make a measurement "
              "region calculable"),
    (LAYER_C, "which physical edges, surfaces and openings actually "
              "contribute to a particular quantity"),
)

THEY_MAY_NEVER_BE_COLLAPSED = (
    "no object may belong to more than one layer. A measurement closure "
    "is never returned by a physical-geometry query, and a physical face "
    "never carries a trade contribution of its own - the contribution is "
    "a statement about the pair (edge, trade), held in layer C")

# ==================================================================
# 3. the measurement closure - section 3
# ==================================================================

CLOSURE_FIELDS = (
    "closure_id", "source_opening_id", "endpoint_a", "endpoint_b",
    "source_evidence_ids", "measurement_basis", "applicable_trade",
    "physical_material_present", "physical_wall", "physical_separator",
    "changes_connectivity", "quantity_length_contribution", "synthetic",
    "reversible", "status", "provenance",
)

CLOSURE_CONSTANTS = {
    "physical_material_present": False,
    "physical_wall": False,
    "physical_separator": False,
    "changes_connectivity": False,
    "quantity_length_contribution": 0,
    "synthetic": True,
    "reversible": True,
}

A_CLOSURE_MAY_ONLY_BRIDGE = (
    "an opening site already ESTABLISHED by the frozen evidence, whose "
    "two endpoints are themselves established. On this drawing that "
    "means a gap the frozen ontology classed CONFIRMED_DOOR_PORTAL, "
    "carrying confirming evidence and two host wall faces")

AN_UNRESOLVED_GAP_MAY_NEVER_RECEIVE_ONE = (
    "an UNRESOLVED_GAP has no established relation. Bridging it would be "
    "inventing the building, and it is the single easiest way to turn "
    "this layer into the back door for every repair the architecture "
    "note warned about")

A_CLOSURE_MAY_NOT_BE_INFERRED_BECAUSE = (
    "a polygon would otherwise remain open",
    "the closure produces a plausible area",
    "the closure agrees with a benchmark",
    "the closure improves room-release statistics",
    "nearby geometry looks like a door without established evidence",
)

THE_BUILDER_IS_BLIND_TO_WHETHER_IT_SUCCEEDED = (
    "closures are constructed from the opening register alone, before "
    "any region is attempted. The construction step cannot see whether a "
    "region closed, so it cannot be tempted by the result. This is "
    "asserted by ordering, and the ordering is part of the protocol")

# ==================================================================
# 4. edge contribution semantics - section 4
# ==================================================================

TOPOLOGICAL_ROLES = (
    "PHYSICAL_BOUNDARY",
    "OPENING",
    "SYNTHETIC_MEASUREMENT_BOUNDARY",
    "OPEN_PHYSICAL_EDGE",
    "UNRESOLVED_EDGE",
)

# The trades named here are named only so the CONTRIBUTION QUESTION can
# be asked of an edge. No quantity is computed for any of them.
TRADES_CONSIDERED = ("PLASTER", "MATERIAL_WALL_LENGTH", "FLOOR_AREA",
                     "WALL_CERAMIC")

THE_MANDATORY_INVARIANT = (
    "POLYGON PERIMETER MAY NEVER SILENTLY BECOME WALL LENGTH. Every edge "
    "of a measurement region states its TOPOLOGICAL_ROLE and, separately, "
    "its contribution for each trade considered. A synthetic measurement "
    "boundary and an open physical edge contribute zero material length, "
    "and the register says so on the edge itself rather than leaving it "
    "to be inferred by whoever sums the perimeter")

# ==================================================================
# 5. what may be reported - section 5, section 12
# ==================================================================

NO_AREA_IS_COMPUTED = (
    "this experiment reports whether a region CAN BE FORMED, not how big "
    "it is. No polygon area is computed anywhere, so no figure here can "
    "be compared with a benchmark even by accident")

METRICS_REPORTED_SEPARATELY = (
    "PHYSICAL_REGIONS_ENCLOSED_BY_DRAWN_MATERIAL",
    "PHYSICAL_REGIONS_OPEN",
    "MEASUREMENT_REGIONS_CLOSED",
    "MEASUREMENT_REGIONS_WITH_UNRESOLVED_GAPS",
    "MEASUREMENT_CLOSURES_CREATED",
    "CONFIRMED_OPENINGS_USED",
    "UNRESOLVED_GAPS_NOT_BRIDGED",
)

NO_GENERIC_CLOSED_ROOMS_METRIC = (
    "there is no combined 'closed rooms' figure anywhere in this "
    "experiment's output, because the whole point is that the two kinds "
    "of closure are different facts about different layers")

A_CLOSURE_MAY_ONLY_IMPROVE_A_MEASUREMENT_METRIC = (
    "a measurement closure may move MEASUREMENT_REGIONS_CLOSED. It may "
    "never move PHYSICAL_REGIONS_ENCLOSED_BY_DRAWN_MATERIAL. The "
    "reversibility test exists to prove that it did not")

# ==================================================================
# 6. failure is allowed - section 13
# ==================================================================

MEASUREMENT_REGION_NOT_ESTABLISHED = "MEASUREMENT_REGION_NOT_ESTABLISHED"

NOT_ESTABLISHED_REASONS = (
    "AN_UNRESOLVED_GAP_LIES_ON_THE_BOUNDARY",
    "THE_BOUNDARY_CHAIN_DOES_NOT_MEET_ITSELF",
    "AN_ENDPOINT_OF_AN_OPENING_IS_NOT_ESTABLISHED",
    "THE_WALK_ESTABLISHED_NO_RING_AROUND_THE_POINT",
    "INSUFFICIENT_SOURCE_EVIDENCE",
)

FAILURE_IS_A_RESULT = (
    "a candidate that cannot form a measurement region returns "
    "MEASUREMENT_REGION_NOT_ESTABLISHED with the exact reason. It is not "
    "closed heuristically, A19 is not asked to rescue it, and no "
    "benchmark decides it")

# ==================================================================
# 7. reversibility - section 11
# ==================================================================

REVERSIBILITY_RULE = (
    "REVERSIBLE is proved, never stored. STATE A is the frozen "
    "physical/topological model, hashed. STATE B is that model with every "
    "measurement closure present. Every closure is then removed, giving "
    "STATE C. HASH(A) must equal HASH(C) for every physical artefact that "
    "should be invariant. If it does not, the experiment FAILS and says "
    "so")

# ==================================================================
# 8. the topological site - section 7, section 8
# ==================================================================

SITE_TYPES = (
    "CONFIRMED_DOOR_OPENING",
    "CONFIRMED_WINDOW_OPENING",
    "CONFIRMED_OPEN_PASSAGE",
    "CONFIRMED_GLAZED_SEPARATOR",
    "MATERIAL_CONTINUITY",
    "UNRESOLVED_GAP",
)

A_SITE_MAY_EXIST_BETWEEN_ENTITIES = (
    "the SAFETY_SAMPLE rounds established that an opening is frequently "
    "an ABSENCE of drawn geometry: across three independently designed "
    "samples a blind reference established exactly one OPENING_IN_"
    "SEPARATOR each time, because a unit built from drawn intervals can "
    "only offer an opening where the drawing gives the opening its own "
    "ink.\n\n"
    "A TOPOLOGICAL_SITE is therefore defined as wall termination A + the "
    "void + wall termination B, with door leaf or arc evidence OPTIONAL. "
    "The void is a valid site with no line in it. This experiment "
    "evaluates that representation; it does not build a new classifier "
    "and asks no model to populate it")

NO_NEW_SEMANTIC_CLASSIFIER = (
    "site types are read from the frozen gap ontology. Nothing here "
    "re-classifies a gap, and no AI is consulted")

# ==================================================================
# 9. physical regions need not close - section 9, section 10
# ==================================================================

BOTH_MAY_BE_TRUE_AT_ONCE = (
    "PHYSICAL_REGION_STATUS = OPEN and "
    "PLASTER_MEASUREMENT_REGION_STATUS = CLOSED may both be correct at "
    "the same place at the same time. Physical closure is not forced "
    "because a quantity engine wants a closed cell")

ONE_REGION_IS_NOT_ONE_ROOM = (
    "one closed measurement region does not equal one physical room, one "
    "functional zone or one finish zone. An open Salon and Dining, or an "
    "open Pantry, must stay representable without inserting a fake "
    "physical wall, and no known value for this project may be used to "
    "decide any of it")


def protocol_hash() -> str:
    parts = [EXPERIMENT_ID, f"V{PROTOCOL_VERSION}", EXPERIMENT_CLASS,
             THE_PURPOSE, WHAT_THIS_IS_NOT, NOTHING_IS_WRITTEN_BACK,
             THEY_MAY_NEVER_BE_COLLAPSED, A_CLOSURE_MAY_ONLY_BRIDGE,
             AN_UNRESOLVED_GAP_MAY_NEVER_RECEIVE_ONE,
             THE_BUILDER_IS_BLIND_TO_WHETHER_IT_SUCCEEDED,
             THE_MANDATORY_INVARIANT, NO_AREA_IS_COMPUTED,
             NO_GENERIC_CLOSED_ROOMS_METRIC,
             A_CLOSURE_MAY_ONLY_IMPROVE_A_MEASUREMENT_METRIC,
             FAILURE_IS_A_RESULT, REVERSIBILITY_RULE,
             A_SITE_MAY_EXIST_BETWEEN_ENTITIES, NO_NEW_SEMANTIC_CLASSIFIER,
             BOTH_MAY_BE_TRUE_AT_ONCE, ONE_REGION_IS_NOT_ONE_ROOM]
    parts += list(INPUTS_ALLOWED) + list(INPUTS_FORBIDDEN)
    parts += list(CLOSURE_FIELDS) + list(TOPOLOGICAL_ROLES)
    parts += list(TRADES_CONSIDERED) + list(METRICS_REPORTED_SEPARATELY)
    parts += list(NOT_ESTABLISHED_REASONS) + list(SITE_TYPES)
    parts += list(A_CLOSURE_MAY_NOT_BE_INFERRED_BECAUSE)
    parts += [f"{k}={v}" for k, v in sorted(CLOSURE_CONSTANTS.items())]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    return {
        "EXPERIMENT_ID": EXPERIMENT_ID,
        "EXPERIMENT_CLASS": EXPERIMENT_CLASS,
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
        "PROTOCOL_HASH": protocol_hash(),
        "THE_PURPOSE": THE_PURPOSE,
        "WHAT_THIS_IS_NOT": WHAT_THIS_IS_NOT,
        "E1_4_DIR": E1_4_DIR,
        "INPUTS_ALLOWED": list(INPUTS_ALLOWED),
        "INPUTS_FORBIDDEN": list(INPUTS_FORBIDDEN),
        "NOTHING_IS_WRITTEN_BACK": NOTHING_IS_WRITTEN_BACK,
        "LAYERS": [list(x) for x in LAYERS],
        "THEY_MAY_NEVER_BE_COLLAPSED": THEY_MAY_NEVER_BE_COLLAPSED,
        "CLOSURE_FIELDS": list(CLOSURE_FIELDS),
        "CLOSURE_CONSTANTS": dict(CLOSURE_CONSTANTS),
        "A_CLOSURE_MAY_ONLY_BRIDGE": A_CLOSURE_MAY_ONLY_BRIDGE,
        "AN_UNRESOLVED_GAP_MAY_NEVER_RECEIVE_ONE":
            AN_UNRESOLVED_GAP_MAY_NEVER_RECEIVE_ONE,
        "A_CLOSURE_MAY_NOT_BE_INFERRED_BECAUSE":
            list(A_CLOSURE_MAY_NOT_BE_INFERRED_BECAUSE),
        "THE_BUILDER_IS_BLIND_TO_WHETHER_IT_SUCCEEDED":
            THE_BUILDER_IS_BLIND_TO_WHETHER_IT_SUCCEEDED,
        "TOPOLOGICAL_ROLES": list(TOPOLOGICAL_ROLES),
        "TRADES_CONSIDERED": list(TRADES_CONSIDERED),
        "THE_MANDATORY_INVARIANT": THE_MANDATORY_INVARIANT,
        "NO_AREA_IS_COMPUTED": NO_AREA_IS_COMPUTED,
        "METRICS_REPORTED_SEPARATELY": list(METRICS_REPORTED_SEPARATELY),
        "NO_GENERIC_CLOSED_ROOMS_METRIC": NO_GENERIC_CLOSED_ROOMS_METRIC,
        "A_CLOSURE_MAY_ONLY_IMPROVE_A_MEASUREMENT_METRIC":
            A_CLOSURE_MAY_ONLY_IMPROVE_A_MEASUREMENT_METRIC,
        "MEASUREMENT_REGION_NOT_ESTABLISHED":
            MEASUREMENT_REGION_NOT_ESTABLISHED,
        "NOT_ESTABLISHED_REASONS": list(NOT_ESTABLISHED_REASONS),
        "FAILURE_IS_A_RESULT": FAILURE_IS_A_RESULT,
        "REVERSIBILITY_RULE": REVERSIBILITY_RULE,
        "SITE_TYPES": list(SITE_TYPES),
        "A_SITE_MAY_EXIST_BETWEEN_ENTITIES": A_SITE_MAY_EXIST_BETWEEN_ENTITIES,
        "NO_NEW_SEMANTIC_CLASSIFIER": NO_NEW_SEMANTIC_CLASSIFIER,
        "BOTH_MAY_BE_TRUE_AT_ONCE": BOTH_MAY_BE_TRUE_AT_ONCE,
        "ONE_REGION_IS_NOT_ONE_ROOM": ONE_REGION_IS_NOT_ONE_ROOM,
    }


if __name__ == "__main__":
    import json
    print(json.dumps({"PROTOCOL_HASH": protocol_hash()}, indent=2))
