"""SEMANTIC_EDGE_SCORING_01 - the scoring protocol, written before scoring.

SEMANTIC_EDGE_EXPERIMENT_01 is frozen at

    FREEZE_SHA256 39bdf0d3b38eee7fc6df2f59d0e680bd355e370754772afca6ea8bdb049ee856
    PROTOCOL_HASH f5c5581988cd070bad570bcc7859490b08b7d0b7ff5216619903dbe3be63357d

and E1.4 stays frozen at

    d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb

Nothing here modifies either. Nothing here feeds a semantic finding into
any geometry pass, computes an area, or opens a quantity benchmark.

WHAT THIS STAGE IS FOR

The frozen experiment reports that A19 and a cold checker agreed on ten
of eleven high-impact groups. That is INTER-READER AGREEMENT. It is not
accuracy. Two readings of the same picture by the same kind of reader can
agree and both be wrong, and a checker that merely correlates with A19
adds nothing but comfort.

    CHECKER_AGREE  is not  CORRECT

So this stage builds an INDEPENDENT REFERENCE INTERPRETATION, blind to
every A19 output, freezes it, and only then opens A19's answers.

THE ORDER IS THE WHOLE METHOD

    1. canonicalise the sample using source geometry only
    2. build reference packages that contain no A19 answer and no E1.4
       classification
    3. read them cold, twice for the categories that could move geometry
    4. FREEZE the reference labels and hash them
    5. only then load A19 and score

A reference produced after seeing the thing it grades is not a reference.

THE REFERENCE MAY NOT GUESS

Where the drawing does not establish whether something is glazing or
frame, water edge or coping, wall or low partition, the reference says
UNRESOLVED. A fabricated ground truth would make every number below
meaningless and would look exactly like a good result.
"""

from __future__ import annotations

import hashlib

from research.semantic_edge_experiment_01 import protocol as SE

SCORING_ID = "SEMANTIC_EDGE_SCORING_01"
SCORING_CLASS = "RESEARCH_ONLY_INDEPENDENT_SCORING_NOT_A_PRODUCTION_RUN"
MODEL = "AGREEMENT_IS_NOT_ACCURACY_A_REFERENCE_IS_READ_BLIND_AND_FROZEN_V1"

EXPERIMENT_ID = SE.EXPERIMENT_ID
EXPERIMENT_PROTOCOL_HASH = (
    "f5c5581988cd070bad570bcc7859490b08b7d0b7ff5216619903dbe3be63357d")
EXPERIMENT_FREEZE_SHA256 = (
    "39bdf0d3b38eee7fc6df2f59d0e680bd355e370754772afca6ea8bdb049ee856")
E1_4_RUN_HASH = SE.E1_4_RUN_HASH

AGREEMENT_IS_NOT_ACCURACY = (
    "the frozen experiment's checker agreed with A19 on ten of eleven "
    "high-impact groups. That measures whether two readers of the same "
    "picture say the same thing. It does not measure whether either is "
    "right, and a checker that only correlates with A19 is a comfort, "
    "not a control. Nothing in this stage treats CHECKER_AGREE as CORRECT")

NOTHING_IS_FED_BACK = (
    "no label, score or readiness class produced here reaches E1.4, room "
    "tracing, the boundary walk, any arrangement or any area calculation. "
    "This stage measures. What is done about the measurement is a later "
    "decision taken by the owner")

NO_QUANTITY_BENCHMARK = (
    "semantic source interpretation needs no quantity benchmark. No "
    "workbook, no room area, no known m2, no manually corrected polygon "
    "and no commercial quantity is opened at any point")

# ==================================================================
# 1. canonicalising the sample - §2
# ==================================================================

CANONICAL_ID_PREFIX = "CF-"

WHY_CANONICALISATION_IS_NEEDED = (
    "the frozen experiment asked 34 questions about fewer architectural "
    "features, because overlapping seed neighbourhoods generated "
    "duplicate questions. Scoring per question would weight a feature "
    "that happened to be sampled three times three times as heavily. The "
    "frozen experiment is not altered; this clustering exists only for "
    "scoring")

# The rule, declared before it is run. It uses SOURCE geometry and source
# entity identity only, and never an A19 answer, a reference answer or an
# E1.4 classification.
CANONICAL_RULE = (
    "two frozen feature groups belong to the same canonical feature when "
    "their PRIMARY members include intervals of the same parent CAD "
    "entity AND their member bounding boxes overlap. Canonical features "
    "are the transitive closure of that relation")

WHY_PARENT_ENTITY_AND_NOT_INTERVAL = (
    "an interval is a stretch of a drawn entity, cut where the evidence "
    "could change. Two questions about different stretches of one drawn "
    "line are two questions about the same drawn thing. Clustering on "
    "interval identity alone would miss exactly the duplication a reader "
    "reported: the same window marked through different members")

WHY_THE_BOUNDING_BOX_CONDITION = (
    "one long entity can run past several unrelated features. Requiring "
    "the two groups' extents to overlap keeps a shared long line from "
    "welding distant features into one cluster. It is a geometric test "
    "on frozen source geometry and it consults no meaning")

SENSITIVITY_RULES = (
    "SHARED_PRIMARY_INTERVAL: the two groups share at least one primary "
    "interval id",
    "SHARED_ANY_MEMBER_ENTITY: the two groups share any member's parent "
    "entity, ignoring the bounding-box condition",
)

THE_COUNT_IS_REPORTED_NOT_ASSUMED = (
    "the earlier redundancy measurement suggested about 27 distinct "
    "features under a narrower rule. That number is not assumed here. "
    "Whatever the declared rule produces is what is reported, beside the "
    "sensitivity rules, so the effect of the choice is visible")

CLUSTER_FIELDS = (
    "CANONICAL_FEATURE_CLUSTER_ID",
    "MEMBER_FEATURE_GROUP_IDS",
    "PRIMARY_ENTITY_UNION",
    "CONTEXT_ENTITY_UNION",
    "OVERLAP_REASON",
)

# ==================================================================
# 2. the curve-question artefact - §3
# ==================================================================

CURVE_QUESTION_NOT_APPLICABLE = "CURVE_QUESTION_NOT_APPLICABLE"
CURVE_ROLE_INCORRECT = "CURVE_ROLE_INCORRECT"

CURVE_ARTEFACT_RULE = (
    "the frozen sampling protocol put a group in the curve stratum when "
    "an arc lay NEAR the seed, so some groups were asked the curve-family "
    "question with no arc among their marked members. Where no marked "
    "member of a group is an ARC or a CIRCLE, its curve answer is "
    "CURVE_QUESTION_NOT_APPLICABLE and is excluded from curve scoring "
    "entirely. Returning UNRESOLVED to an inapplicable question is not an "
    "error by the reader; it is an error by the apparatus, and it is "
    "counted against the apparatus in the sampling-defect register")

# ==================================================================
# 3. the reference - §4 to §8
# ==================================================================

REFERENCE_PACKAGE_CONTAINS = (
    "the frozen source context crop",
    "the frozen feature crop",
    "the frozen detail crop where one exists",
    "the tagged CAD entities, as the frozen experiment marked them",
    "neutral CAD metadata: layer, linetype, entity type, block membership",
)

REFERENCE_PACKAGE_MUST_NOT_CONTAIN = (
    "any A19 Pass A answer",
    "any A19 Pass B answer",
    "the cold checker's answer",
    "the E1.4 classification of any entity",
    "any earlier visual finding from any experiment",
    "any expected label, benchmark, area or quantity",
)

THE_REFERENCE_IS_READ_COLD = (
    "a new reader that has never seen an A19 result determines the "
    "architectural meaning independently. It is given the same pictures "
    "and the same neutral metadata, and nothing about what anyone else "
    "concluded")

FEATURE_ASSEMBLY_TYPES = SE.FEATURE_ASSEMBLY_TYPES
ENTITY_SUB_ROLES = SE.ENTITY_SUB_ROLES
RELATIONS = SE.RELATIONS
CONFIDENCE_CLASSES = SE.CONFIDENCE_CLASSES

REFERENCE_FIELDS = (
    "REFERENCE_ROLE", "REFERENCE_CONFIDENCE", "REFERENCE_EVIDENCE",
    "NEEDS_ADDITIONAL_CONTEXT",
)

THE_REFERENCE_MAY_NOT_GUESS = (
    "where the drawing does not establish whether something is glazing or "
    "frame, a water edge or a coping, a wall or a low partition, the "
    "reference is UNRESOLVED. Reference quality matters more than forcing "
    "every feature into a class, because a fabricated ground truth "
    "produces numbers that look exactly like a good result")

NO_NUMERIC_CONFIDENCE = (
    "HIGH, MEDIUM, LOW, UNRESOLVED. No probability, no percentage, and "
    "no number anywhere in a reference answer, for the same reason the "
    "reader's schema has none")

# §7 - the categories that could materially move physical geometry
HIGH_IMPACT_ASSEMBLIES = (
    SE.WALL_ASSEMBLY,
    SE.WINDOW_OR_GLAZING_ASSEMBLY,
    SE.DOOR_ASSEMBLY,
    SE.COLUMN_OR_PIER_ASSEMBLY,
    SE.COUNTER_OR_CABINET_ASSEMBLY,
    SE.POOL_OR_WATER_FEATURE,
    SE.STAIR_ASSEMBLY,
)

WHY_THESE_ARE_HIGH_IMPACT = (
    "each of these, read wrongly, changes what bounds a space or what "
    "does not. A counter read as a wall invents a room division; a window "
    "read as solid wall closes an opening that exists; a stair edge read "
    "as a wall cuts a floor. A dimension line read wrongly costs nothing "
    "downstream, so it is not in this list")

SECOND_REFERENCE_RULE = (
    "a canonical feature whose FIRST reference reading falls in a "
    "high-impact category is read again by a second independent reference "
    "reader that has seen neither A19 nor the first reference. The "
    "selection depends on the first reference's own category and on "
    "nothing from A19")

REFERENCE_CONFLICT = "REFERENCE_CONFLICT"

NO_AUTOMATIC_VOTE = (
    "where the two reference readers disagree the feature is "
    "REFERENCE_CONFLICT. It is excluded from strict accuracy, reported "
    "separately, and never resolved by voting. Two readers disagreeing is "
    "evidence that the drawing is ambiguous there, which is itself a "
    "result")

THE_REFERENCE_FREEZES_FIRST = (
    "REFERENCE_LABEL_REGISTER.json is written and hashed before any A19 "
    "output is loaded by any scoring code. A reference that could still "
    "move after seeing the answers is not a reference")

# ==================================================================
# 4. feature-assembly scoring - §9
# ==================================================================

EXACT_MATCH = "EXACT_MATCH"
COMPATIBLE_PARENT_MATCH = "COMPATIBLE_PARENT_MATCH"
WRONG_ASSEMBLY = "WRONG_ASSEMBLY"
A19_UNRESOLVED = "A19_UNRESOLVED"
REFERENCE_UNRESOLVED = "REFERENCE_UNRESOLVED"
INCONSISTENT_WITHIN_CLUSTER = "INCONSISTENT_WITHIN_CLUSTER"

ASSEMBLY_OUTCOMES = (EXACT_MATCH, COMPATIBLE_PARENT_MATCH, WRONG_ASSEMBLY,
                     A19_UNRESOLVED, REFERENCE_UNRESOLVED, REFERENCE_CONFLICT,
                     INCONSISTENT_WITHIN_CLUSTER)

WHY_INCONSISTENT_WITHIN_CLUSTER_EXISTS = (
    "this outcome is not in the brief and is added because the "
    "canonicalisation makes it visible and it would otherwise be hidden. "
    "Where one canonical feature was asked about more than once and A19 "
    "answered differently each time, that is neither a match nor a plain "
    "miss: it is the reader contradicting itself about one drawn thing, "
    "which matters more for production than either")

COMPATIBILITY_RULE = (
    "MIXED_FEATURE is a COMPATIBLE_PARENT_MATCH against any specific "
    "assembly type in either direction: it is a weaker claim about the "
    "same thing, not a different claim. Every other pair of distinct "
    "types is WRONG_ASSEMBLY. UNRESOLVED_FEATURE from A19 is "
    "A19_UNRESOLVED and is never scored as wrong")

REPORT_BY_A19_CONFIDENCE = (SE.HIGH, SE.MEDIUM, SE.LOW,
                            SE.CONFIDENCE_UNRESOLVED)

HIGH_CONFIDENCE_WRONG_IS_THE_RISK = (
    "a reader that says UNRESOLVED costs a human a look. A reader that "
    "says HIGH and is wrong costs a wrong building. HIGH_CONFIDENCE_WRONG "
    "is reported on its own line and no summary average is allowed to "
    "absorb it")

# ==================================================================
# 5. entity and sub-role scoring - §10
# ==================================================================

EXACT_ROLE_MATCH = "EXACT_ROLE_MATCH"
COMPATIBLE_ROLE_FAMILY = "COMPATIBLE_ROLE_FAMILY"
ROLE_MISMATCH = "ROLE_MISMATCH"

ROLE_OUTCOMES = (EXACT_ROLE_MATCH, COMPATIBLE_ROLE_FAMILY, ROLE_MISMATCH,
                 A19_UNRESOLVED, REFERENCE_UNRESOLVED)

ROLE_FAMILIES = {
    "WALL": ("VISIBLE_MATERIAL_WALL_FACE", "WALL_OTHER_FACE",
             "CURVED_MATERIAL_WALL"),
    "WINDOW": ("GLAZING", "WINDOW_FRAME", "WINDOW_MULLION", "WINDOW_JAMB"),
    "DOOR_OR_OPENING": ("DOOR_JAMB", "DOOR_LEAF", "DOOR_SWING", "OPENING",
                        "THRESHOLD"),
    "JOINERY": ("COUNTER_EDGE", "CABINET_EDGE", "FURNITURE"),
    "STRUCTURE": ("COLUMN_OR_PIER",),
    "STAIR": ("STAIR_VISIBLE_EDGE", "STAIR_TREAD_OR_RISER",
              "STAIR_OVERHEAD_OR_BELOW_CUT"),
    "POOL_OR_NON_FLOOR": ("POOL_WATER_EDGE", "POOL_COPING_INNER_EDGE",
                          "POOL_COPING_OUTER_EDGE", "POOL_RIM_OR_FINISH_EDGE"),
    "ANNOTATION": ("DIMENSION_LINE", "DIMENSION_WITNESS", "ANNOTATION"),
    "OTHER": ("EXTERNAL_SITE_EDGE", "STRUCTURAL_HIDDEN",
              "OTHER_NON_BOUNDARY"),
}

DO_NOT_MIX_THE_TWO_LEVELS = (
    "assembly accuracy and member-role accuracy are reported separately "
    "and are never averaged together. A correct assembly with unresolved "
    "members is usable; a confident member role inside a wrongly "
    "assembled group is not")

# ==================================================================
# 6. the critical error matrix - §11
# ==================================================================
#
# Each entry is (name, what the reference established, what A19 said).
# These are the errors that change what bounds a space.

CRITICAL_ERRORS = (
    ("COUNTER_AS_WALL", ("COUNTER_EDGE",), ROLE_FAMILIES["WALL"]),
    ("CABINET_AS_WALL", ("CABINET_EDGE", "FURNITURE"), ROLE_FAMILIES["WALL"]),
    ("DIMENSION_AS_WALL", ("DIMENSION_LINE", "DIMENSION_WITNESS"),
     ROLE_FAMILIES["WALL"]),
    ("ANNOTATION_AS_WALL", ("ANNOTATION",), ROLE_FAMILIES["WALL"]),
    ("DOOR_SWING_AS_WALL", ("DOOR_SWING", "DOOR_LEAF"),
     ROLE_FAMILIES["WALL"]),
    ("HIDDEN_LINE_AS_VISIBLE_WALL",
     ("STRUCTURAL_HIDDEN", "STAIR_OVERHEAD_OR_BELOW_CUT"),
     ("VISIBLE_MATERIAL_WALL_FACE",)),
    ("GLAZING_AS_SOLID_WALL", ("GLAZING",), ROLE_FAMILIES["WALL"]),
    ("SOLID_WALL_AS_GLAZING", ROLE_FAMILIES["WALL"], ("GLAZING",)),
    ("DOOR_OPENING_MISSED", ("OPENING", "DOOR_JAMB", "THRESHOLD"),
     ROLE_FAMILIES["WALL"] + ("UNRESOLVED",)),
    ("FALSE_DOOR_OPENING", ROLE_FAMILIES["WALL"],
     ("OPENING", "DOOR_JAMB", "THRESHOLD")),
    ("COLUMN_AS_WALL", ("COLUMN_OR_PIER",), ROLE_FAMILIES["WALL"]),
    ("WALL_AS_COLUMN", ROLE_FAMILIES["WALL"], ("COLUMN_OR_PIER",)),
    ("POOL_EDGE_AS_WALL", ROLE_FAMILIES["POOL_OR_NON_FLOOR"],
     ROLE_FAMILIES["WALL"]),
    ("WALL_AS_POOL_EDGE", ROLE_FAMILIES["WALL"],
     ROLE_FAMILIES["POOL_OR_NON_FLOOR"]),
)

# A19 relation claims that assert or deny physical separation.
SEPARATOR_CLAIMS = {
    "THIS_FEATURE_PHYSICALLY_SEPARATES_SPACE": True,
    "THIS_FEATURE_DOES_NOT_PHYSICALLY_SEPARATE_SPACE": False,
}
SEPARATION_ERRORS = ("PHYSICAL_SEPARATOR_AS_NON_SEPARATOR",
                     "NON_SEPARATOR_AS_PHYSICAL_SEPARATOR")

CRITICAL_ERRORS_MATTER_MORE = (
    "a disagreement between WINDOW_FRAME and WINDOW_JAMB costs a "
    "downstream pass nothing. A counter called a wall invents a room "
    "division, and a window called solid wall closes an opening that is "
    "there. The matrix is reported on its own and is never folded into an "
    "average with subtype disagreements")

# ==================================================================
# 7. fenestration, relations, checker - §12, §13, §14
# ==================================================================

FENESTRATION_OUTCOMES = ("A19_DETECTED_ASSEMBLY", "A19_MISSED_ASSEMBLY",
                         "A19_UNRESOLVED")

WHY_FENESTRATION_HAS_ITS_OWN_SCORE = (
    "frozen E1.4 establishes no glazing anywhere on this floor, and the "
    "arrangement experiment showed what that costs: a room whose fourth "
    "side is a window has no fourth side. Whether a reader can see "
    "fenestration the deterministic layer cannot is the single most "
    "consequential question in this stage")

FENESTRATION_IS_NOT_INFERRED_FROM_CLOSURE = (
    "no feature is counted as a window because calling it one would close "
    "a region. Closure is not evidence and no closure is computed here")

RELATIONS_SCORED = (
    "THESE_ENTITIES_FORM_ONE_WINDOW",
    "THESE_ENTITIES_FORM_ONE_WALL_BODY",
    "THIS_OPENING_BELONGS_TO_THIS_WALL",
    "THIS_FEATURE_PHYSICALLY_SEPARATES_SPACE",
    "THIS_FEATURE_DOES_NOT_PHYSICALLY_SEPARATE_SPACE",
    "THIS_DASHED_LINE_IS_NOT_IN_THE_VISIBLE_CUT_PLANE",
    "THESE_CURVES_BELONG_TO_ONE_POOL_ASSEMBLY",
)

RELATIONS_MAY_BE_THE_USEFUL_OUTPUT = (
    "saying that six lines are one window may survive where a per-line "
    "subtype does not, and a grouping claim is exactly what the "
    "deterministic layer cannot make. Relations are scored and reported "
    "on their own line")

CHECKER_CELLS = ("A19_CORRECT_CHECKER_AGREES", "A19_WRONG_CHECKER_AGREES",
                 "A19_CORRECT_CHECKER_DISAGREES",
                 "A19_WRONG_CHECKER_DISAGREES", "REFERENCE_UNRESOLVED")

WHAT_THE_CHECKER_TABLE_ANSWERS = (
    "whether a second reader of the same kind catches A19's mistakes or "
    "merely repeats them. A19_WRONG_CHECKER_AGREES is the cell that "
    "matters: every entry in it is a mistake the checker was blind to, "
    "and a checker with many of them is not a control")

# ==================================================================
# 8. readiness - §16, §17
# ==================================================================

A19_NOT_READY = "A19_NOT_READY"
A19_DIAGNOSTIC_ONLY = "A19_DIAGNOSTIC_ONLY"
A19_CANDIDATE_SEMANTIC_EVIDENCE = "A19_CANDIDATE_SEMANTIC_EVIDENCE"
A19_STRONG_SEMANTIC_EVIDENCE = "A19_STRONG_SEMANTIC_EVIDENCE"

READINESS_CLASSES = (A19_NOT_READY, A19_DIAGNOSTIC_ONLY,
                     A19_CANDIDATE_SEMANTIC_EVIDENCE,
                     A19_STRONG_SEMANTIC_EVIDENCE)

# Declared before the scores exist, so the class cannot be chosen to suit
# them. Each rule is read in order; the first that fits decides.
READINESS_RULES = (
    (A19_NOT_READY,
     "any critical false positive in the geometry-impacting matrix, or a "
     "high-confidence assembly accuracy at or below half, or fewer than "
     "five reference-resolved canonical features to judge on"),
    (A19_DIAGNOSTIC_ONLY,
     "no critical false positive, but high-confidence assembly accuracy "
     "below four in five, or any high-confidence wrong assembly"),
    (A19_CANDIDATE_SEMANTIC_EVIDENCE,
     "no critical false positive, no high-confidence wrong assembly, and "
     "high-confidence assembly accuracy of four in five or better"),
    (A19_STRONG_SEMANTIC_EVIDENCE,
     "all of the above, and no reference conflict among high-impact "
     "features, and entity-role accuracy at exact or compatible-family "
     "level of four in five or better"),
)

USE_EVIDENCE_NOT_OPTIMISM = (
    "the readiness rules are written before the scores are computed and "
    "are applied as written. A class is not chosen because the work would "
    "be disappointing otherwise")

THE_SAMPLE_IS_NOT_RANDOM = (
    "the 34 questions came from a quota-stratified sample of 1110 "
    "eligible seeds, deliberately weighted towards the hard strata. It is "
    "not a random sample of the floor's unclassified linework, so no rate "
    "measured here may be multiplied out to the whole floor. The coverage "
    "analysis says what fraction of the SAMPLE it addresses and states "
    "this limit beside every figure")

COVERAGE_ANALYSIS_IS_ANALYSIS_ONLY = (
    "the question of what a HIGH-confidence-only admission policy could "
    "address is answered as an illustration on frozen data. It changes no "
    "production code, admits no edge anywhere, and is not a "
    "recommendation")

DO_NOT_HIDE_THE_DENOMINATOR = (
    "every accuracy figure is reported with the count it was computed "
    "over and with the reference-unresolved and reference-conflict cases "
    "stated beside it, never silently dropped from the denominator")


def protocol_hash() -> str:
    parts = ([SCORING_ID, MODEL, EXPERIMENT_FREEZE_SHA256, E1_4_RUN_HASH,
              CANONICAL_RULE, CURVE_ARTEFACT_RULE, COMPATIBILITY_RULE,
              SECOND_REFERENCE_RULE, THE_REFERENCE_FREEZES_FIRST]
             + list(CLUSTER_FIELDS) + list(SENSITIVITY_RULES)
             + list(REFERENCE_PACKAGE_CONTAINS)
             + list(REFERENCE_PACKAGE_MUST_NOT_CONTAIN)
             + list(REFERENCE_FIELDS) + list(HIGH_IMPACT_ASSEMBLIES)
             + list(ASSEMBLY_OUTCOMES) + list(ROLE_OUTCOMES)
             + [f"{k}:{','.join(v)}" for k, v in sorted(ROLE_FAMILIES.items())]
             + [f"{n}:{','.join(sorted(a))}->{','.join(sorted(b))}"
                for n, a, b in CRITICAL_ERRORS]
             + list(SEPARATION_ERRORS) + list(FENESTRATION_OUTCOMES)
             + list(RELATIONS_SCORED) + list(CHECKER_CELLS)
             + [f"{k}:{v}" for k, v in READINESS_RULES])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    return {
        "SCORING_ID": SCORING_ID,
        "SCORING_CLASS": SCORING_CLASS,
        "MODEL": MODEL,
        "THE_EXPERIMENT_BEING_SCORED": EXPERIMENT_ID,
        "EXPERIMENT_PROTOCOL_HASH": EXPERIMENT_PROTOCOL_HASH,
        "EXPERIMENT_FREEZE_SHA256": EXPERIMENT_FREEZE_SHA256,
        "THE_FROZEN_EXPERIMENT_IS_NOT_ALTERED": True,
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": E1_4_RUN_HASH,
        "THIS_IS_NOT_E1_5_AND_NOT_PRODUCTION_E2": True,

        "agreement_is_not_accuracy": AGREEMENT_IS_NOT_ACCURACY,
        "nothing_is_fed_back": NOTHING_IS_FED_BACK,
        "no_quantity_benchmark": NO_QUANTITY_BENCHMARK,

        "CANONICALISATION": {
            "why": WHY_CANONICALISATION_IS_NEEDED,
            "RULE": CANONICAL_RULE,
            "why_parent_entity_and_not_interval":
                WHY_PARENT_ENTITY_AND_NOT_INTERVAL,
            "why_the_bounding_box_condition": WHY_THE_BOUNDING_BOX_CONDITION,
            "SENSITIVITY_RULES": list(SENSITIVITY_RULES),
            "the_count_is_reported_not_assumed":
                THE_COUNT_IS_REPORTED_NOT_ASSUMED,
            "FIELDS": list(CLUSTER_FIELDS),
            "NO_SEMANTIC_ANSWER_IS_USED_TO_CLUSTER": True,
        },

        "CURVE_QUESTION_ARTEFACT": {
            "NOT_APPLICABLE": CURVE_QUESTION_NOT_APPLICABLE,
            "INCORRECT": CURVE_ROLE_INCORRECT,
            "RULE": CURVE_ARTEFACT_RULE,
        },

        "REFERENCE": {
            "PACKAGE_CONTAINS": list(REFERENCE_PACKAGE_CONTAINS),
            "PACKAGE_MUST_NOT_CONTAIN": list(REFERENCE_PACKAGE_MUST_NOT_CONTAIN),
            "read_cold": THE_REFERENCE_IS_READ_COLD,
            "FEATURE_ASSEMBLY_TYPES": list(FEATURE_ASSEMBLY_TYPES),
            "ENTITY_SUB_ROLES": list(ENTITY_SUB_ROLES),
            "RELATIONS": list(RELATIONS),
            "CONFIDENCE_CLASSES": list(CONFIDENCE_CLASSES),
            "FIELDS": list(REFERENCE_FIELDS),
            "may_not_guess": THE_REFERENCE_MAY_NOT_GUESS,
            "no_numeric_confidence": NO_NUMERIC_CONFIDENCE,
            "HIGH_IMPACT_ASSEMBLIES": list(HIGH_IMPACT_ASSEMBLIES),
            "why_these_are_high_impact": WHY_THESE_ARE_HIGH_IMPACT,
            "SECOND_REFERENCE_RULE": SECOND_REFERENCE_RULE,
            "no_automatic_vote": NO_AUTOMATIC_VOTE,
            "the_reference_freezes_first": THE_REFERENCE_FREEZES_FIRST,
        },

        "FEATURE_ASSEMBLY_SCORING": {
            "OUTCOMES": list(ASSEMBLY_OUTCOMES),
            "COMPATIBILITY_RULE": COMPATIBILITY_RULE,
            "why_inconsistent_within_cluster_exists":
                WHY_INCONSISTENT_WITHIN_CLUSTER_EXISTS,
            "REPORT_BY_A19_CONFIDENCE": list(REPORT_BY_A19_CONFIDENCE),
            "high_confidence_wrong_is_the_risk":
                HIGH_CONFIDENCE_WRONG_IS_THE_RISK,
        },

        "ENTITY_ROLE_SCORING": {
            "OUTCOMES": list(ROLE_OUTCOMES),
            "ROLE_FAMILIES": {k: list(v) for k, v in ROLE_FAMILIES.items()},
            "do_not_mix_the_two_levels": DO_NOT_MIX_THE_TWO_LEVELS,
        },

        "CRITICAL_ERROR_MATRIX": {
            "ERRORS": [{"NAME": n, "REFERENCE_ESTABLISHED": sorted(a),
                        "A19_SAID": sorted(b)} for n, a, b in CRITICAL_ERRORS],
            "SEPARATION_ERRORS": list(SEPARATION_ERRORS),
            "why": CRITICAL_ERRORS_MATTER_MORE,
        },

        "FENESTRATION_SCORING": {
            "OUTCOMES": list(FENESTRATION_OUTCOMES),
            "why": WHY_FENESTRATION_HAS_ITS_OWN_SCORE,
            "not_inferred_from_closure": FENESTRATION_IS_NOT_INFERRED_FROM_CLOSURE,
        },

        "RELATION_SCORING": {
            "RELATIONS_SCORED": list(RELATIONS_SCORED),
            "why": RELATIONS_MAY_BE_THE_USEFUL_OUTPUT,
        },

        "CHECKER_VALUE": {
            "CELLS": list(CHECKER_CELLS),
            "what_it_answers": WHAT_THE_CHECKER_TABLE_ANSWERS,
            "CHECKER_AGREEMENT_IS_NEVER_TRUTH": True,
        },

        "READINESS": {
            "CLASSES": list(READINESS_CLASSES),
            "RULES": [{"CLASS": c, "RULE": r} for c, r in READINESS_RULES],
            "use_evidence_not_optimism": USE_EVIDENCE_NOT_OPTIMISM,
            "NO_GEOMETRY_IS_MODIFIED_BY_ANY_OF_THIS": True,
        },

        "COVERAGE_ANALYSIS": {
            "the_sample_is_not_random": THE_SAMPLE_IS_NOT_RANDOM,
            "analysis_only": COVERAGE_ANALYSIS_IS_ANALYSIS_ONLY,
        },

        "do_not_hide_the_denominator": DO_NOT_HIDE_THE_DENOMINATOR,
        "SCORING_PROTOCOL_HASH": protocol_hash(),
    }
