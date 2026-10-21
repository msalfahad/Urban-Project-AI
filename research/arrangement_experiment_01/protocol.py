"""ARRANGEMENT_EXPERIMENT_01 - the protocol, written before anything ran.

This is a research experiment. It is not a production run, it is not E1.5,
and it does not touch E1.4, which stays frozen at

    d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb

WHAT IS BEING TESTED

    a planar cell arrangement is a better PRIMARY geometry representation
    than per-room seed-to-ring discovery, especially for open-plan and
    partial spaces

WHAT WOULD FALSIFY IT

The hypothesis does not survive if any of the seven conditions in
SURVIVAL_CONDITIONS fails. A failure is reported as a failure. It is not
rescued with a special case, and no rule in this experiment names a room.

WHY THE SELECTION RULE IS WRITTEN HERE

Case 7 is chosen from the frozen cold-review register. Choosing it after
looking at the candidates would be choosing the case that suits the
method. The rule is mechanical, it is stated before the register is read,
and its output is recorded with the rule beside it.
"""

from __future__ import annotations

import hashlib

EXPERIMENT_ID = "ARRANGEMENT_EXPERIMENT_01"
EXPERIMENT_CLASS = "RESEARCH_ONLY_NOT_A_PRODUCTION_RUN"

E1_4_RUN_ID = "E1_4-P7757-GF-001"
E1_4_RUN_HASH = (
    "d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb")

THE_PROPOSITION = (
    "a planar cell arrangement is a better primary geometry "
    "representation than per-room seed-to-ring discovery, especially for "
    "open-plan and partial spaces")

THIS_EXPERIMENT_TRIES_TO_FALSIFY_IT = (
    "the experiment is built to break the proposition, not to support "
    "it. A method that releases more regions has not thereby won: the "
    "question is whether the REPRESENTATION can hold what the drawing "
    "establishes without inventing anything")

SURVIVAL_CONDITIONS = (
    "1. every selected physical region has a meaningful cell representation",
    "2. the open-plan cluster is expressible without inventing a physical "
    "wall",
    "3. Pantry can remain physically open without disappearing from the "
    "data model",
    "4. the closed W.C and Kitchen representations are not degraded "
    "relative to E1.4",
    "5. curves remain traceable to analytical source geometry",
    "6. door and open connections appear as adjacency and topology rather "
    "than fake wall closure",
    "7. A19 can group or classify cells without inventing geometry",
)

NO_BENCHMARK_UNTIL_EVERY_METHOD_IS_FROZEN = (
    "no human take-off, no manual room area, no expected geometry, no "
    "corrected target, no known total for any room, and no reconciliation "
    "ranking is opened while any method is still generating. P7757 is a "
    "regression project and generation still runs target-free")

# ---------------------------------------------------- the two boundary layers
HARD_PHYSICAL = "HARD_PHYSICAL_ARRANGEMENT"
SOFT_SEMANTIC = "SOFT_SEMANTIC_PARTITION"

A_SOFT_PARTITION_IS_NEVER_A_WALL = (
    "a soft partition subdivides a physical space for a functional or "
    "trade reason. It creates no material. It carries MATERIAL_PRESENT = "
    "false, WALL_LENGTH_CONTRIBUTION = 0 and PHYSICAL_SEPARATION = false, "
    "and no pass may promote it to a wall. The floor finish changing at a "
    "line nobody built does not build a line")

# What the hard layer may be made of.
MATERIAL_WALL = "MATERIAL_WALL"
EXTERNAL_ENCLOSURE = "EXTERNAL_ENCLOSURE"
GLAZING_BOUNDARY = "GLAZING_BOUNDARY"
EXPOSED_STRUCTURAL_OBSTACLE = "EXPOSED_STRUCTURAL_OBSTACLE"
COLUMN_INTRUSION = "COLUMN_INTRUSION"
CONFIRMED_DOOR_PORTAL = "CONFIRMED_DOOR_PORTAL"
OPEN_PHYSICAL_CONNECTION = "OPEN_PHYSICAL_CONNECTION"
UNRESOLVED_EDGE = "UNRESOLVED_EDGE"

HARD_EDGE_ROLES = (MATERIAL_WALL, EXTERNAL_ENCLOSURE, GLAZING_BOUNDARY,
                   EXPOSED_STRUCTURAL_OBSTACLE, COLUMN_INTRUSION,
                   CONFIRMED_DOOR_PORTAL, OPEN_PHYSICAL_CONNECTION,
                   UNRESOLVED_EDGE)

# Which of them physically separate free space.
SEPARATES = (MATERIAL_WALL, EXTERNAL_ENCLOSURE, GLAZING_BOUNDARY,
             EXPOSED_STRUCTURAL_OBSTACLE, COLUMN_INTRUSION)
DOES_NOT_SEPARATE = (CONFIRMED_DOOR_PORTAL, OPEN_PHYSICAL_CONNECTION)
SEPARATION_UNRESOLVED = (UNRESOLVED_EDGE,)

WHY_A_NON_MATERIAL_EDGE_EXISTS_AT_ALL = (
    "a cell has to be bounded or it leaks across the whole floor. Where a "
    "doorway or an unclassified gap interrupts the fabric, an edge is "
    "carried across it SO THAT THE CELL CLOSES, and it is marked as "
    "carrying no material and as not separating - or, for an unclassified "
    "gap, as not settled either way. This is the opposite of inventing a "
    "wall: the edge exists to hold the topology and it is disqualified "
    "from every material question by its own record")

# What a cell is.
FREE_SPACE_CELL = "FREE_SPACE_CELL"
MATERIAL_SOLID_CELL = "MATERIAL_SOLID_CELL"
OBSTACLE_CELL = "OBSTACLE_CELL"
OUTSIDE_CELL = "OUTSIDE_THE_DRAWN_FABRIC"
CELL_CLASSES = (FREE_SPACE_CELL, MATERIAL_SOLID_CELL, OBSTACLE_CELL,
                OUTSIDE_CELL)

WALL_THICKNESS_IS_NOT_ROOM = (
    "the inside of a wall is a cell like any other in a planar "
    "arrangement, and it is not floor. A cell bounded by both faces of "
    "one wall body is the wall, and it is classified as material solid "
    "before anything is grouped. The thing we group is free space")

# ------------------------------------------------------- the data model
DATA_MODEL = (
    "HARD_PHYSICAL_CELL -> grouped into -> PHYSICAL_SPACE",
    "PHYSICAL_SPACE -> optionally subdivided or grouped by SOFT "
    "partitions -> FUNCTIONAL_ZONE",
    "FUNCTIONAL_ZONE -> independently subdivided or grouped -> "
    "TRADE_MEASUREMENT_ZONE",
)

CARDINALITY = (
    "one physical space may contain several functional zones",
    "one functional zone may contain several trade zones",
    "several functional zones may belong to one trade zone",
)

NO_TRADE_DECISION_IS_MADE_HERE = (
    "this experiment proves only that the representation can carry the "
    "three layers. It makes no trade decision, computes no quantity and "
    "opens no rule library")

# ------------------------------------------------- the seven cases
CASE_CATEGORIES = (
    "1_SIMPLE_ENCLOSED_WC_RELEASED_BY_E1_4",
    "2_KITCHEN",
    "3_PANTRY",
    "4_OPEN_PLAN_CLUSTER_SALON_DINING_RECEPTION",
    "5_CURVED_BOUNDARY_POOL",
    "6_STAIR_ADJACENT",
    "7_MECHANICALLY_SELECTED_WALL_FALSELY_REMOVED_DOORWAY",
)

# Categories 1-6 are identified by the English token the drawing itself
# carries, which is source identity and not an expected area. Where more
# than one candidate carries the token, the lowest stable candidate id
# wins, so the choice cannot follow the result.
CASE_TOKEN = {
    "1_SIMPLE_ENCLOSED_WC_RELEASED_BY_E1_4": "W.C",
    "2_KITCHEN": "KITCHEN",
    "3_PANTRY": "PANTRY",
    "4_OPEN_PLAN_CLUSTER_SALON_DINING_RECEPTION": "SALOON",
    "5_CURVED_BOUNDARY_POOL": "SWIMMING POOL",
    "6_STAIR_ADJACENT": "DRIVER",
}

CASE_1_EXTRA_RULE = (
    "case 1 must be a W.C that frozen E1.4 RELEASED. Among released "
    "candidates carrying that token, the lowest stable candidate id wins")

CASE_6_RULE = (
    "case 6 is the stair-adjacent case. The candidate is chosen "
    "mechanically: among all candidates, the one whose frozen E1.4 "
    "boundary evidence carries the most intervals whose semantic role is "
    "STAIR_GEOMETRY within its own crop window, ties broken by lowest "
    "stable candidate id. If no candidate carries stair geometry, the "
    "case is recorded as NOT_PRESENT_ON_THIS_FLOOR and the experiment "
    "runs with six cases, which is reported rather than patched")

CASE_7_SELECTION_RULE = (
    "case 7 is selected from the frozen E1.4 cold-review register, "
    "before any candidate-specific result is read, by this rule: take "
    "every candidate whose frozen V2 answer carries WALL_FALSELY_REMOVED; "
    "keep those that also carry drawn door evidence in the frozen door "
    "register within their crop window; order by stable candidate id "
    "ascending; take the first. If none qualifies, relax only the door "
    "condition, and record that the relaxation was used")

THE_RULE_IS_WRITTEN_BEFORE_THE_REGISTER_IS_READ = (
    "this module is hashed into the experiment's protocol record before "
    "01_CASE_SELECTION.json is produced. A rule chosen after seeing which "
    "candidate would suit the method is not a rule, it is a preference")

# ------------------------------------------------------------ methods
METHOD_0 = "METHOD_0_E1_4_FROZEN_BASELINE"
METHOD_1 = "METHOD_1_HARD_ARRANGEMENT_ONLY"
METHOD_2 = "METHOD_2_DETERMINISTIC_GROUPING"
METHOD_3 = "METHOD_3_A19_EDGE_AND_GROUPING_ORACLE"
A20_PASS_1 = "A20_PASS_1_SOURCE_ONLY"
A20_PASS_2 = "A20_PASS_2_GROUPING_CHALLENGE"
EXTERNAL = "OPTIONAL_EXTERNAL_CHALLENGER"

METHODS = (METHOD_0, METHOD_1, METHOD_2, METHOD_3, A20_PASS_1,
           A20_PASS_2, EXTERNAL)

WHAT_THE_ARRANGEMENT_MAY_NOT_BE_GIVEN = (
    "dimension lines and witness lines",
    "hidden, overhead and below-cut-plane geometry",
    "counters and cabinet fronts",
    "door swing arcs as material",
    "the pool water contour as masonry",
    "annotation and level or grid marks",
    "any soft semantic boundary",
)

A19_HAS_NO_NUMERIC_FIELD = (
    "the A19 answer schema contains no numeric field of any kind. A model "
    "that cannot state a number cannot invent one, which is a stronger "
    "guarantee than screening numbers on the way in")

A20_IS_NOT_SHOWN_THE_ANSWER_FIRST = (
    "the verifier answers from the source crop alone and that answer is "
    "frozen before it is shown any grouping. A verifier shown a proposal "
    "and asked whether it agrees is measuring anchoring, not geometry")


def protocol_hash() -> str:
    parts = ([EXPERIMENT_ID, THE_PROPOSITION] + list(SURVIVAL_CONDITIONS)
             + list(CASE_CATEGORIES) + [CASE_7_SELECTION_RULE, CASE_6_RULE,
                                        CASE_1_EXTRA_RULE]
             + list(HARD_EDGE_ROLES) + list(CELL_CLASSES) + list(METHODS))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    return {
        "EXPERIMENT_ID": EXPERIMENT_ID,
        "EXPERIMENT_CLASS": EXPERIMENT_CLASS,
        "THIS_IS_NOT_E1_5_AND_NOT_PRODUCTION_E2": True,
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_ID": E1_4_RUN_ID,
        "E1_4_RUN_HASH": E1_4_RUN_HASH,
        "THE_PROPOSITION": THE_PROPOSITION,
        "this_experiment_tries_to_falsify_it":
            THIS_EXPERIMENT_TRIES_TO_FALSIFY_IT,
        "SURVIVAL_CONDITIONS": list(SURVIVAL_CONDITIONS),
        "no_benchmark_until_every_method_is_frozen":
            NO_BENCHMARK_UNTIL_EVERY_METHOD_IS_FROZEN,
        "TWO_BOUNDARY_LAYERS": {
            HARD_PHYSICAL: list(HARD_EDGE_ROLES),
            SOFT_SEMANTIC: "creates no material; never becomes a wall",
            "a_soft_partition_is_never_a_wall":
                A_SOFT_PARTITION_IS_NEVER_A_WALL,
        },
        "SEPARATES": list(SEPARATES),
        "DOES_NOT_SEPARATE": list(DOES_NOT_SEPARATE),
        "SEPARATION_UNRESOLVED": list(SEPARATION_UNRESOLVED),
        "why_a_non_material_edge_exists_at_all":
            WHY_A_NON_MATERIAL_EDGE_EXISTS_AT_ALL,
        "CELL_CLASSES": list(CELL_CLASSES),
        "wall_thickness_is_not_room": WALL_THICKNESS_IS_NOT_ROOM,
        "DATA_MODEL": list(DATA_MODEL),
        "CARDINALITY": list(CARDINALITY),
        "no_trade_decision_is_made_here": NO_TRADE_DECISION_IS_MADE_HERE,
        "CASE_CATEGORIES": list(CASE_CATEGORIES),
        "CASE_TOKEN": dict(CASE_TOKEN),
        "CASE_1_EXTRA_RULE": CASE_1_EXTRA_RULE,
        "CASE_6_RULE": CASE_6_RULE,
        "CASE_7_SELECTION_RULE": CASE_7_SELECTION_RULE,
        "the_rule_is_written_before_the_register_is_read":
            THE_RULE_IS_WRITTEN_BEFORE_THE_REGISTER_IS_READ,
        "METHODS": list(METHODS),
        "what_the_arrangement_may_not_be_given":
            list(WHAT_THE_ARRANGEMENT_MAY_NOT_BE_GIVEN),
        "a19_has_no_numeric_field": A19_HAS_NO_NUMERIC_FIELD,
        "a20_is_not_shown_the_answer_first": A20_IS_NOT_SHOWN_THE_ANSWER_FIRST,
        "PROTOCOL_HASH": protocol_hash(),
    }
