"""SEMANTIC_EDGE_EXPERIMENT_01 - the protocol, written before anything ran.

This is a research experiment. It is not E1.5, it is not production E2, it
does not touch E1.4, which stays frozen at

    d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb

and nothing it produces is fed back into any geometry pass.

WHY THIS EXPERIMENT EXISTS

ARRANGEMENT_EXPERIMENT_01 failed under its own frozen survival criteria,
and in failing it isolated the bottleneck. It is not the geometry:

    3287 atomic intervals on the ground floor
    1049 of them - 479.8 m - carry no established semantic role
    839 of those are continuous linework the line semantics place
        squarely IN the cut plane
    the role layer establishes ZERO glazing anywhere on the floor

Refuse that linework and real rooms leak into the exterior because their
fourth side is a window nobody classified. Admit it wholesale and four
rooms merge into one 376 m2 face. Neither is a geometry problem, so no
further geometry algorithm can solve it.

THE HYPOTHESIS

    VISION UNDERSTANDS WHAT
    CAD KNOWS WHERE
    CODE CALCULATES

WHAT WOULD FALSIFY IT

The hypothesis does not survive if a semantic reader, given the source
crop and the tagged entities, cannot say what a local feature IS at a
rate better than the deterministic layer it is meant to supplement -
or if it can only do so by inventing geometry, which the answer schema
makes impossible by containing no numeric field at all.

This experiment does not score that. It generates the evidence and
freezes it. Scoring is a separate, later, independent act.

ENTITY IS NOT ARCHITECTURAL FEATURE

The mistake this protocol is built to avoid: asking what one line means.
A window is glass lines, frame lines, jambs, wall returns and mullions. A
door is a leaf, a swing, two jambs, an opening and a threshold. A pool is
a water boundary, a coping, a rim and a set of reference curves. The
meaning lives in the GROUP, so the unit of sampling, of cropping and of
asking is the FEATURE NEIGHBOURHOOD.

    CAD ENTITY  ->  LOCAL FEATURE ASSEMBLY  ->  SEMANTIC SUB-ROLES

WHY THE SAMPLING RULE IS WRITTEN HERE

Choosing which neighbourhoods to look at AFTER seeing which ones the
reader would do well on is choosing the exam. Every predicate below is
mechanical, uses source evidence only - layer, linetype, entity type,
geometry, adjacency - and never consults the semantic answer. This module
is hashed into 00_PROTOCOL.json before 01_SAMPLE_SELECTION.json exists.
"""

from __future__ import annotations

import hashlib

EXPERIMENT_ID = "SEMANTIC_EDGE_EXPERIMENT_01"
EXPERIMENT_CLASS = "RESEARCH_ONLY_NOT_A_PRODUCTION_RUN"
MODEL = "VISION_UNDERSTANDS_WHAT_CAD_KNOWS_WHERE_CODE_CALCULATES_V1"

E1_4_RUN_ID = "E1_4-P7757-GF-001"
E1_4_RUN_HASH = (
    "d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb")

THE_HYPOTHESIS = (
    "a multimodal reader can correctly understand what local CAD geometry "
    "REPRESENTS, while CAD remains the authority for WHERE it is")

THE_THREE_AUTHORITIES = (
    "VISION UNDERSTANDS WHAT",
    "CAD KNOWS WHERE",
    "CODE CALCULATES",
)

AI_IS_NEVER_THE_GEOMETRY_OWNER = (
    "the reader may say that a group of lines is one window and that a "
    "particular member of it is the glass. It may not move a coordinate, "
    "propose a corrected polygon, close an open space, state a dimension, "
    "an area or a perimeter, or choose a reading because it would help a "
    "topology close. The answer schema contains no numeric field of any "
    "kind, because a model that cannot state a number cannot invent one")

WHAT_THE_ARRANGEMENT_EXPERIMENT_ESTABLISHED = (
    "the bottleneck is SEMANTIC COVERAGE OF ARCHITECTURAL CAD LINEWORK. "
    "Conservative exclusion makes real spaces leak; indiscriminate "
    "inclusion makes false large regions. Another geometry algorithm "
    "cannot solve an upstream evidence problem")

NOTHING_IS_FED_BACK = (
    "no classification from this experiment reaches E1.4, room tracing, "
    "the boundary walk, any arrangement or any area calculation. "
    "Recognition is tested first and frozen. Whether it ever deserves "
    "authority as evidence is a separate decision made afterwards")

NO_BENCHMARK_AND_NO_KNOWN_GEOMETRY = (
    "no benchmark workbook, no manual area, no expected m2, no corrected "
    "polygon, no known room total and no reconciliation is opened here. "
    "This experiment is semantic only")

# ==================================================================
# the sampling protocol - §4
# ==================================================================

SAMPLE_TARGET = 40
UNIT_OF_SAMPLING = "FEATURE_NEIGHBOURHOOD"

A_SEED_IS_NOT_THE_FEATURE = (
    "a seed is one entity the mechanical rule can point at. The thing "
    "sampled, cropped and asked about is the neighbourhood assembled "
    "around it. Two seeds that assemble the same neighbourhood are one "
    "sample, and the collision is recorded")

# Which entities may seed at all: the ones the deterministic layer did not
# settle. Establishedness is read from frozen E1.4 and nothing else.
SEED_IS_ELIGIBLE_WHEN = (
    "its established semantic role is UNKNOWN",
    "or its role is one the role layer itself marks unsettled: "
    "COLUMN_CANDIDATE_UNRESOLVED, AMBIGUOUS_PAIRED_BAND",
    "or its role carries a NOT_ESTABLISHED or LOW confidence",
)

# The ten strata, in the order a seed is tested against them. A seed joins
# the FIRST stratum whose predicate it satisfies, so assignment cannot
# depend on the order the drawing happens to be read in.
STRATUM_A = "A_EXTERIOR_OR_OPENING_NEIGHBOURHOOD"
STRATUM_B = "B_REPEATED_PARALLEL_LINE_GROUP"
STRATUM_C = "C_DOOR_OR_SWING_NEIGHBOURHOOD"
STRATUM_D = "D_WALL_LIKE_UNRESOLVED_GROUP"
STRATUM_E = "E_COUNTER_OR_CABINET_NEIGHBOURHOOD"
STRATUM_F = "F_STAIR_NEIGHBOURHOOD"
STRATUM_G = "G_CURVED_OR_POOL_NEIGHBOURHOOD"
STRATUM_H = "H_EXTERIOR_ENVELOPE_JUNCTION"
STRATUM_I = "I_OPEN_PLAN_SEPARATOR_CANDIDATE"
STRATUM_J = "J_MISCELLANEOUS_IN_CUT_PLANE_UNRESOLVED"

STRATA = (STRATUM_A, STRATUM_B, STRATUM_C, STRATUM_D, STRATUM_E,
          STRATUM_F, STRATUM_G, STRATUM_H, STRATUM_I, STRATUM_J)

# Every predicate below is geometric or source-metadata only.
STRATUM_PREDICATE = {
    STRATUM_A: ("the seed's midpoint lies within ENVELOPE_BAND_MM of the "
                "boundary of the convex hull of all established material "
                "linework, so it sits where a facade is"),
    STRATUM_B: ("the seed has at least PARALLEL_FAMILY_MIN parallel "
                "neighbours within PARALLEL_FAMILY_SPAN_MM at distinct "
                "offsets, which is how a layered assembly is drawn"),
    STRATUM_C: ("an interval whose established role is DOOR lies within "
                "DOOR_REACH_MM of the seed"),
    STRATUM_D: ("the seed has exactly one parallel partner at a "
                "separation inside the drawing's own wall-thickness band"),
    STRATUM_E: ("the seed runs parallel to an established material face "
                "at a separation inside the fitted-unit depth band"),
    STRATUM_F: ("an interval whose established role is STAIR_GEOMETRY "
                "lies within STAIR_REACH_MM of the seed"),
    STRATUM_G: ("the seed is an ARC or CIRCLE, or an ARC or CIRCLE lies "
                "within CURVE_REACH_MM of it"),
    STRATUM_H: ("an endpoint of the seed meets an endpoint of established "
                "material within JUNCTION_MM, and that junction lies "
                "within ENVELOPE_BAND_MM of the hull boundary"),
    STRATUM_I: ("neither end of the seed meets anything within "
                "JUNCTION_MM, and it is at least SEPARATOR_MIN_LENGTH_MM "
                "long: a free-standing run of the kind an open plan is "
                "divided by, or not"),
    STRATUM_J: ("anything else eligible whose line semantics place it in "
                "the cut plane"),
}

PER_STRATUM_QUOTA = 4
TIE_BREAK = "lowest stable CAD interval id ascending"
TOP_UP_RULE = (
    "quotas are filled per stratum in stable-id order. A stratum that "
    "cannot fill its quota records the shortfall and is not backfilled "
    "from another stratum's meaning. The sample is then topped up to "
    "SAMPLE_TARGET from the remaining eligible seeds in stable-id order "
    "across all strata, and every topped-up row is marked TOPPED_UP so "
    "the composition of the sample is visible")

THE_SAMPLE_CANNOT_DEPEND_ON_THE_ANSWER = (
    "no predicate above asks what the geometry means. They ask where it "
    "is, what it is near, how it is drawn and what its layer and linetype "
    "say. A sample chosen by what the reader would get right is not a "
    "sample, it is a demonstration")

# Geometric parameters, all declared before selection.
ENVELOPE_BAND_MM = 1500.0
PARALLEL_FAMILY_MIN = 2
PARALLEL_FAMILY_SPAN_MM = 600.0
DOOR_REACH_MM = 1200.0
STAIR_REACH_MM = 1500.0
CURVE_REACH_MM = 2000.0
JUNCTION_MM = 25.0
SEPARATOR_MIN_LENGTH_MM = 900.0
WALL_SEPARATION_MIN_MM = 75.0
WALL_SEPARATION_MAX_MM = 400.0
CASEWORK_DEPTH_MIN_MM = 450.0
CASEWORK_DEPTH_MAX_MM = 800.0
PARALLEL_DEG = 3.0
MIN_PARALLEL_OVERLAP_MM = 150.0

# ==================================================================
# local feature assembly - §5
# ==================================================================

ASSEMBLY_ASKS_ONLY_WHAT_TO_SHOW_TOGETHER = (
    "this stage infers no meaning. It answers one question: which CAD "
    "entities should be shown together so that a local architectural "
    "feature can be understood at all. Getting this wrong by being too "
    "narrow is the failure that matters - a window shown without its "
    "jambs is unreadable - so the rules err towards including context "
    "and every included entity is recorded as context, not as part of "
    "the thing being asked about")

ASSEMBLY_RULES = (
    "SHARED_ENDPOINT: an endpoint within JOIN_MM of a seed endpoint",
    "INTERSECTION: the entity crosses the seed",
    "PARALLEL_OFFSET: parallel within PARALLEL_DEG, overlapping by at "
    "least MIN_PARALLEL_OVERLAP_MM, at an offset within "
    "ASSEMBLY_OFFSET_MM",
    "COMMON_PARENT_OBJECT: it is another interval of the same CAD entity",
    "COMMON_BLOCK: it was placed by the same block reference",
    "LOCAL_REGION: its geometry meets the seed's bounding box grown by "
    "ASSEMBLY_HALO_MM",
    "NEARBY_ARC: an ARC or CIRCLE within CURVE_REACH_MM",
    "NEARBY_OPENING: an interval whose role is DOOR within DOOR_REACH_MM",
    "NEIGHBOURING_LAYER: recorded for every gathered entity, never used "
    "to gather one",
)

JOIN_MM = 25.0
ASSEMBLY_OFFSET_MM = 900.0
ASSEMBLY_HALO_MM = 700.0
MAX_CONTEXT_ENTITIES = 120

WHY_THERE_IS_A_CAP = (
    "a crop that shows two hundred entities shows nothing. The cap is "
    "applied by distance from the seed, nearest first, and the number "
    "dropped is recorded on the group so a group that was truncated can "
    "be told from one that was small")

FEATURE_GROUP_FIELDS = (
    "FEATURE_GROUP_ID", "PRIMARY_ENTITY_IDS", "CONTEXT_ENTITY_IDS",
    "LAYERS", "LINETYPES", "ENTITY_TYPES", "BLOCK_IDS", "LOCAL_TOPOLOGY",
    "SOURCE_HANDLES",
)

# ==================================================================
# multi-scale crops - §6
# ==================================================================

LEVEL_A = "LEVEL_A_CONTEXT"
LEVEL_B = "LEVEL_B_FEATURE"
LEVEL_C = "LEVEL_C_DETAIL"
CROP_LEVELS = (LEVEL_A, LEVEL_B, LEVEL_C)

CROP_RULES = (
    "every crop box is computed from the group's own extent by the rules "
    "below. No crop in this experiment is placed by hand",
    "LEVEL_A shows the surrounding architectural context, so that a "
    "window can be told from a wall and a counter from a partition",
    "LEVEL_B shows the feature itself",
    "LEVEL_C is produced only where the feature is small or carries "
    "curves, and shows jamb, frame and curve detail",
    "each level is rendered twice: once clean, and once with the group's "
    "primary entities and context entities marked, so the reader knows "
    "WHICH lines it is being asked about without being told what they are",
    "a crop cannot carry a hundred legible labels. The group's primary "
    "members, and then its nearest context members up to "
    "MAX_LABELLED_MEMBERS, are drawn with an index label and are the "
    "members a per-entity answer may name. The rest are drawn in the "
    "context colour without labels: they are there to be seen, not to be "
    "asked about",
)

MAX_LABELLED_MEMBERS = 12

CONTEXT_MARGIN_MM = 4000.0
CONTEXT_MIN_HALF_MM = 5000.0
FEATURE_MARGIN_MM = 900.0
FEATURE_MIN_HALF_MM = 1200.0
DETAIL_MARGIN_MM = 250.0
DETAIL_MIN_HALF_MM = 450.0
DETAIL_TRIGGER_EXTENT_MM = 3000.0
CROP_PIXELS = (1400, 1400)

A_MARK_IS_NOT_A_LABEL = (
    "the tagged crop marks which entities the question is about. It does "
    "not say what any of them is, it carries no role name, and it is "
    "drawn in one colour for the primaries and one for the context. A "
    "crop that colour-codes by meaning would be handing over the answer")

# ==================================================================
# A19 - the visual CAD semantic reader, §7 to §12
# ==================================================================

A19 = "A19_VISUAL_CAD_SEMANTIC_READER"

A19_MAY_NOT = (
    "create or state a coordinate",
    "move a CAD entity",
    "invent a dimension",
    "state an area",
    "state a perimeter",
    "calculate any quantity",
    "create a room polygon",
    "close an open space",
    "choose a role because it helps a topology close",
)

A19_RECEIVES = (
    "the source crops for its feature group",
    "the tagged entity ids of that group, primaries and context",
    "each entity's layer, linetype, entity type and block membership "
    "where the CAD exposes them",
    "a frozen whole-floor semantic context, as context and not as answer",
    "general architectural semantics",
)

A19_HAS_NO_NUMERIC_FIELD = (
    "the answer schema contains no numeric field of any kind - no "
    "dimension, no area, no count that could stand in for one, and no "
    "probability. A model that cannot state a number cannot invent one, "
    "which is a stronger guarantee than screening numbers on the way in. "
    "The screen runs as well")

# --- first output level: what the assembly is -----------------------
WALL_ASSEMBLY = "WALL_ASSEMBLY"
WINDOW_OR_GLAZING_ASSEMBLY = "WINDOW_OR_GLAZING_ASSEMBLY"
DOOR_ASSEMBLY = "DOOR_ASSEMBLY"
COLUMN_OR_PIER_ASSEMBLY = "COLUMN_OR_PIER_ASSEMBLY"
COUNTER_OR_CABINET_ASSEMBLY = "COUNTER_OR_CABINET_ASSEMBLY"
STAIR_ASSEMBLY = "STAIR_ASSEMBLY"
POOL_OR_WATER_FEATURE = "POOL_OR_WATER_FEATURE"
EXTERNAL_SITE_FEATURE = "EXTERNAL_SITE_FEATURE"
DIMENSION_OR_ANNOTATION_FEATURE = "DIMENSION_OR_ANNOTATION_FEATURE"
MIXED_FEATURE = "MIXED_FEATURE"
UNRESOLVED_FEATURE = "UNRESOLVED_FEATURE"

FEATURE_ASSEMBLY_TYPES = (
    WALL_ASSEMBLY, WINDOW_OR_GLAZING_ASSEMBLY, DOOR_ASSEMBLY,
    COLUMN_OR_PIER_ASSEMBLY, COUNTER_OR_CABINET_ASSEMBLY, STAIR_ASSEMBLY,
    POOL_OR_WATER_FEATURE, EXTERNAL_SITE_FEATURE,
    DIMENSION_OR_ANNOTATION_FEATURE, MIXED_FEATURE, UNRESOLVED_FEATURE,
)

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
CONFIDENCE_UNRESOLVED = "UNRESOLVED"
CONFIDENCE_CLASSES = (HIGH, MEDIUM, LOW, CONFIDENCE_UNRESOLVED)

CONFIDENCE_IS_A_CLASS_NOT_A_NUMBER = (
    "four words, and no probability. A number invites arithmetic on it, "
    "and there is nothing here to do arithmetic with")

# --- second output level: what a member of it is --------------------
ENTITY_SUB_ROLES = (
    "VISIBLE_MATERIAL_WALL_FACE", "WALL_OTHER_FACE", "GLAZING",
    "WINDOW_FRAME", "WINDOW_MULLION", "WINDOW_JAMB", "DOOR_JAMB",
    "DOOR_LEAF", "DOOR_SWING", "OPENING", "THRESHOLD", "COUNTER_EDGE",
    "CABINET_EDGE", "FURNITURE", "COLUMN_OR_PIER", "STAIR_VISIBLE_EDGE",
    "STAIR_TREAD_OR_RISER", "STAIR_OVERHEAD_OR_BELOW_CUT",
    "POOL_WATER_EDGE", "POOL_COPING_INNER_EDGE", "POOL_COPING_OUTER_EDGE",
    "POOL_RIM_OR_FINISH_EDGE", "CURVED_MATERIAL_WALL",
    "EXTERNAL_SITE_EDGE", "DIMENSION_LINE", "DIMENSION_WITNESS",
    "ANNOTATION", "STRUCTURAL_HIDDEN", "OTHER_NON_BOUNDARY", "UNRESOLVED",
)

DO_NOT_FORCE_A_SUBTYPE = (
    "if only the parent assembly is understandable, name the assembly and "
    "leave the members UNRESOLVED. A forced subtype is worse than an "
    "honest gap, because a later pass cannot tell the two apart")

# --- relations, which may be the more reliable output ---------------
RELATIONS = (
    "THESE_ENTITIES_FORM_ONE_WINDOW",
    "THESE_ENTITIES_FORM_ONE_WALL_BODY",
    "THESE_CURVES_BELONG_TO_ONE_POOL_ASSEMBLY",
    "THESE_LINES_ARE_PARALLEL_WALL_FACES",
    "THIS_OPENING_BELONGS_TO_THIS_WALL",
    "THIS_COUNTER_IS_NOT_A_ROOM_SEPARATOR",
    "THIS_DASHED_LINE_IS_NOT_IN_THE_VISIBLE_CUT_PLANE",
    "THIS_FEATURE_PHYSICALLY_SEPARATES_SPACE",
    "THIS_FEATURE_DOES_NOT_PHYSICALLY_SEPARATE_SPACE",
    "UNRESOLVED_RELATION",
)

A_RELATION_IS_SEMANTIC_EVIDENCE_AND_NOT_GEOMETRY = (
    "saying that six lines are one window changes no coordinate. It is "
    "the kind of claim a reader is actually good at, and it may well "
    "survive where a per-line role does not")

# --- §11 the fenestration test --------------------------------------
FENESTRATION_READINGS = ("SOLID_WALL", "WINDOW_OR_GLAZING", "DOOR",
                         "OPEN_VOID", "MIXED_OPENING", "UNRESOLVED")

FENESTRATION_IS_ASKED_OF = (STRATUM_A, STRATUM_H)

WHY_THE_FENESTRATION_TEST_EXISTS = (
    "frozen E1.4 establishes no glazing anywhere on this floor, and the "
    "arrangement showed what that costs: a room whose fourth side is a "
    "window has no fourth side. The test is run on MECHANICALLY selected "
    "exterior and junction neighbourhoods. No window is hand-picked, and "
    "some of the selected groups will not be windows at all, which is "
    "the point")

# --- §12 the curve family test --------------------------------------
CURVE_FAMILY_QUESTION = "DO_THESE_CURVES_BELONG_TO_ONE_ARCHITECTURAL_FEATURE"
CURVE_FAMILY_ANSWERS = ("YES", "NO", "UNRESOLVED")
CURVE_READINGS = ("POOL_WATER_EDGE", "COPING_INNER", "COPING_OUTER",
                  "POOL_WALL_OR_RIM", "CURVED_BUILDING_WALL", "DOOR_SWING",
                  "DECORATIVE_OR_REFERENCE_CURVE", "UNRESOLVED")

CURVE_FAMILY_IS_ASKED_OF = (STRATUM_G,)

A_SHAPE_IS_NOT_A_ROLE = (
    "an arc is a shape. A pool edge, a coping, a curved wall, a door "
    "swing and a setting-out reference can all be drawn as one. The "
    "grouping question is asked before any per-curve reading, and if the "
    "crop cannot tell which concentric arc is water and which is coping, "
    "the answer is UNRESOLVED")

TOPOLOGY_CLOSURE_IS_NOT_EVIDENCE = (
    "no curve is read as a pool edge because reading it that way would "
    "close a face. The arrangement experiment measured what that "
    "reasoning is worth: three arcs whose centres differ by up to 450 mm "
    "were grouped as rings of one round object, and the 207.8 m2 they "
    "appeared to enclose was an artefact")

# ==================================================================
# the two passes - §13
# ==================================================================

PASS_A = "PASS_A_BLIND_SOURCE_SEMANTICS"
PASS_B = "PASS_B_SEMANTIC_CHALLENGE"

PASS_A_NEVER_RECEIVES = (
    "E1.4's current semantic answer for any entity in the group",
    "any earlier visual verdict",
    "any room target geometry",
    "any benchmark, expected area or known quantity",
    "any statement of what this experiment would like the answer to be",
)

PASS_A_IS_FROZEN_BEFORE_PASS_B_EXISTS = (
    "shown a deterministic answer first, a reader finds reasons it is "
    "right. Asked what is there first, the same reader describes the "
    "drawing. Pass A is sealed and hashed before Pass B is assembled")

PASS_B_STATUSES = (
    "AGREES",
    "DETERMINISTIC_FALSE_POSITIVE",
    "DETERMINISTIC_FALSE_NEGATIVE",
    "ROLE_MISMATCH",
    "FEATURE_GROUPING_MISMATCH",
    "VISION_UNRESOLVED",
    "BOTH_UNRESOLVED",
)

PASS_B_MAY_NOT_EDIT_GEOMETRY = (
    "Pass B compares two readings of the same picture. It moves nothing, "
    "corrects nothing in CAD, and produces no geometry")

# ==================================================================
# whole-floor context - §14
# ==================================================================

A18_CONTEXT_MAY_SAY = (
    "the likely identities of rooms on this floor, as the drawing's own "
    "labels give them",
    "which spaces read as open to one another",
    "roughly where the exterior facade lies",
    "roughly where the pool, the stairs and the service core lie",
)

A18_CONTEXT_MAY_NOT_SAY = (
    "that a particular entity is glazing",
    "that a particular line is the pool edge",
    "any entity id at all",
    "any coordinate, dimension or area",
)

WHY_CONTEXT_IS_NOT_AN_ANSWER = (
    "knowing that a facade runs along this side of the plan helps a "
    "reader tell a window from a partition. Being told which line is the "
    "window is not a reading, it is a relay. The context file is checked "
    "for entity ids and for numbers before it is sealed")

# ==================================================================
# the optional checker and the external detector - §15, §16
# ==================================================================

CHECKER_SEES = ("the same source crops", "the same entity tags")
CHECKER_DOES_NOT_SEE = ("A19's result", "E1.4's answer", "any benchmark")
CHECKER_COMPARISONS = ("AGREE", "DISAGREE", "ONE_UNRESOLVED")

NO_AUTOMATIC_MAJORITY_VOTE = (
    "two readers disagreeing is evidence that the question is hard, and "
    "it becomes a HUMAN_REVIEW row. It does not become a majority of "
    "one plus one")

EXTERNAL_DETECTOR_IS_A_CANDIDATE_NEVER_AN_AUTHORITY = (
    "a specialised floor-plan detector, if one is reachable, supplies "
    "EXTERNAL_SEMANTIC_CANDIDATE rows. It never supplies geometry, and "
    "if none is reachable the experiment does not wait for one: a test "
    "specification is written for later instead")

# ==================================================================
# scoring - §19, §20
# ==================================================================

NOTHING_IS_SCORED_HERE = (
    "this experiment returns distributions and counts. It does not "
    "report accuracy, does not judge whether a reading is right, and "
    "does not open anything that would let it. Scoring is later and "
    "independent")

THE_LATER_SCORER_EVALUATES_TWO_LEVELS = (
    "A. FEATURE ASSEMBLY ACCURACY - these lines together represent one "
    "window",
    "B. ENTITY OR SUB-ROLE ACCURACY - this specific member is the glass, "
    "the frame or the jamb",
    "assembly accuracy matters at least as much as per-line accuracy, "
    "because a correct assembly with unresolved members is usable and a "
    "confident per-line answer inside a wrongly assembled group is not",
)


def protocol_hash() -> str:
    parts = ([EXPERIMENT_ID, MODEL, THE_HYPOTHESIS]
             + list(THE_THREE_AUTHORITIES)
             + list(SEED_IS_ELIGIBLE_WHEN)
             + list(STRATA)
             + [f"{k}:{v}" for k, v in sorted(STRATUM_PREDICATE.items())]
             + [TOP_UP_RULE, TIE_BREAK,
                f"QUOTA={PER_STRATUM_QUOTA}", f"TARGET={SAMPLE_TARGET}"]
             + list(ASSEMBLY_RULES)
             + list(FEATURE_GROUP_FIELDS)
             + list(CROP_LEVELS) + list(CROP_RULES)
             + list(A19_MAY_NOT) + list(A19_RECEIVES)
             + list(FEATURE_ASSEMBLY_TYPES) + list(CONFIDENCE_CLASSES)
             + list(ENTITY_SUB_ROLES) + list(RELATIONS)
             + list(FENESTRATION_READINGS) + list(CURVE_READINGS)
             + list(PASS_A_NEVER_RECEIVES) + list(PASS_B_STATUSES)
             + list(A18_CONTEXT_MAY_NOT_SAY)
             + list(CHECKER_COMPARISONS)
             + [f"{k}={v}" for k, v in sorted(_PARAMS().items())])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _PARAMS() -> dict:
    return {
        "ENVELOPE_BAND_MM": ENVELOPE_BAND_MM,
        "PARALLEL_FAMILY_MIN": PARALLEL_FAMILY_MIN,
        "PARALLEL_FAMILY_SPAN_MM": PARALLEL_FAMILY_SPAN_MM,
        "DOOR_REACH_MM": DOOR_REACH_MM,
        "STAIR_REACH_MM": STAIR_REACH_MM,
        "CURVE_REACH_MM": CURVE_REACH_MM,
        "JUNCTION_MM": JUNCTION_MM,
        "SEPARATOR_MIN_LENGTH_MM": SEPARATOR_MIN_LENGTH_MM,
        "WALL_SEPARATION_MIN_MM": WALL_SEPARATION_MIN_MM,
        "WALL_SEPARATION_MAX_MM": WALL_SEPARATION_MAX_MM,
        "CASEWORK_DEPTH_MIN_MM": CASEWORK_DEPTH_MIN_MM,
        "CASEWORK_DEPTH_MAX_MM": CASEWORK_DEPTH_MAX_MM,
        "PARALLEL_DEG": PARALLEL_DEG,
        "MIN_PARALLEL_OVERLAP_MM": MIN_PARALLEL_OVERLAP_MM,
        "JOIN_MM": JOIN_MM,
        "ASSEMBLY_OFFSET_MM": ASSEMBLY_OFFSET_MM,
        "ASSEMBLY_HALO_MM": ASSEMBLY_HALO_MM,
        "MAX_CONTEXT_ENTITIES": MAX_CONTEXT_ENTITIES,
        "CONTEXT_MARGIN_MM": CONTEXT_MARGIN_MM,
        "CONTEXT_MIN_HALF_MM": CONTEXT_MIN_HALF_MM,
        "FEATURE_MARGIN_MM": FEATURE_MARGIN_MM,
        "FEATURE_MIN_HALF_MM": FEATURE_MIN_HALF_MM,
        "DETAIL_MARGIN_MM": DETAIL_MARGIN_MM,
        "DETAIL_MIN_HALF_MM": DETAIL_MIN_HALF_MM,
        "DETAIL_TRIGGER_EXTENT_MM": DETAIL_TRIGGER_EXTENT_MM,
        "CROP_PIXELS": list(CROP_PIXELS),
        "MAX_LABELLED_MEMBERS": MAX_LABELLED_MEMBERS,
    }


def record() -> dict:
    return {
        "EXPERIMENT_ID": EXPERIMENT_ID,
        "EXPERIMENT_CLASS": EXPERIMENT_CLASS,
        "MODEL": MODEL,
        "THIS_IS_NOT_E1_5_AND_NOT_PRODUCTION_E2": True,
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_ID": E1_4_RUN_ID,
        "E1_4_RUN_HASH": E1_4_RUN_HASH,

        "THE_HYPOTHESIS": THE_HYPOTHESIS,
        "THE_THREE_AUTHORITIES": list(THE_THREE_AUTHORITIES),
        "ai_is_never_the_geometry_owner": AI_IS_NEVER_THE_GEOMETRY_OWNER,
        "what_the_arrangement_experiment_established":
            WHAT_THE_ARRANGEMENT_EXPERIMENT_ESTABLISHED,
        "nothing_is_fed_back": NOTHING_IS_FED_BACK,
        "no_benchmark_and_no_known_geometry": NO_BENCHMARK_AND_NO_KNOWN_GEOMETRY,

        "ENTITY_IS_NOT_ARCHITECTURAL_FEATURE": {
            "PIPELINE": ["CAD_ENTITY", "LOCAL_FEATURE_ASSEMBLY",
                         "SEMANTIC_SUB_ROLES"],
            "a_seed_is_not_the_feature": A_SEED_IS_NOT_THE_FEATURE,
        },

        "SAMPLING": {
            "UNIT_OF_SAMPLING": UNIT_OF_SAMPLING,
            "SAMPLE_TARGET": SAMPLE_TARGET,
            "SEED_IS_ELIGIBLE_WHEN": list(SEED_IS_ELIGIBLE_WHEN),
            "STRATA": list(STRATA),
            "STRATUM_PREDICATE": dict(STRATUM_PREDICATE),
            "PER_STRATUM_QUOTA": PER_STRATUM_QUOTA,
            "TIE_BREAK": TIE_BREAK,
            "TOP_UP_RULE": TOP_UP_RULE,
            "the_sample_cannot_depend_on_the_answer":
                THE_SAMPLE_CANNOT_DEPEND_ON_THE_ANSWER,
        },

        "FEATURE_ASSEMBLY": {
            "asks_only_what_to_show_together":
                ASSEMBLY_ASKS_ONLY_WHAT_TO_SHOW_TOGETHER,
            "RULES": list(ASSEMBLY_RULES),
            "FIELDS": list(FEATURE_GROUP_FIELDS),
            "why_there_is_a_cap": WHY_THERE_IS_A_CAP,
        },

        "CROPS": {
            "LEVELS": list(CROP_LEVELS),
            "RULES": list(CROP_RULES),
            "a_mark_is_not_a_label": A_MARK_IS_NOT_A_LABEL,
        },

        "A19": {
            "NAME": A19,
            "MAY_NOT": list(A19_MAY_NOT),
            "RECEIVES": list(A19_RECEIVES),
            "has_no_numeric_field": A19_HAS_NO_NUMERIC_FIELD,
            "FEATURE_ASSEMBLY_TYPES": list(FEATURE_ASSEMBLY_TYPES),
            "CONFIDENCE_CLASSES": list(CONFIDENCE_CLASSES),
            "confidence_is_a_class_not_a_number":
                CONFIDENCE_IS_A_CLASS_NOT_A_NUMBER,
            "ENTITY_SUB_ROLES": list(ENTITY_SUB_ROLES),
            "do_not_force_a_subtype": DO_NOT_FORCE_A_SUBTYPE,
            "RELATIONS": list(RELATIONS),
            "a_relation_is_semantic_evidence_and_not_geometry":
                A_RELATION_IS_SEMANTIC_EVIDENCE_AND_NOT_GEOMETRY,
        },

        "FENESTRATION_TEST": {
            "READINGS": list(FENESTRATION_READINGS),
            "ASKED_OF_STRATA": list(FENESTRATION_IS_ASKED_OF),
            "why": WHY_THE_FENESTRATION_TEST_EXISTS,
        },

        "CURVE_FAMILY_TEST": {
            "QUESTION": CURVE_FAMILY_QUESTION,
            "ANSWERS": list(CURVE_FAMILY_ANSWERS),
            "READINGS": list(CURVE_READINGS),
            "ASKED_OF_STRATA": list(CURVE_FAMILY_IS_ASKED_OF),
            "a_shape_is_not_a_role": A_SHAPE_IS_NOT_A_ROLE,
            "topology_closure_is_not_evidence":
                TOPOLOGY_CLOSURE_IS_NOT_EVIDENCE,
        },

        "PASSES": {
            "PASS_A": PASS_A,
            "PASS_A_NEVER_RECEIVES": list(PASS_A_NEVER_RECEIVES),
            "pass_a_is_frozen_before_pass_b_exists":
                PASS_A_IS_FROZEN_BEFORE_PASS_B_EXISTS,
            "PASS_B": PASS_B,
            "PASS_B_STATUSES": list(PASS_B_STATUSES),
            "pass_b_may_not_edit_geometry": PASS_B_MAY_NOT_EDIT_GEOMETRY,
        },

        "WHOLE_FLOOR_CONTEXT": {
            "MAY_SAY": list(A18_CONTEXT_MAY_SAY),
            "MAY_NOT_SAY": list(A18_CONTEXT_MAY_NOT_SAY),
            "why_context_is_not_an_answer": WHY_CONTEXT_IS_NOT_AN_ANSWER,
        },

        "OPTIONAL_CHECKER": {
            "SEES": list(CHECKER_SEES),
            "DOES_NOT_SEE": list(CHECKER_DOES_NOT_SEE),
            "COMPARISONS": list(CHECKER_COMPARISONS),
            "no_automatic_majority_vote": NO_AUTOMATIC_MAJORITY_VOTE,
        },

        "EXTERNAL_DETECTOR": {
            "ROLE": "EXTERNAL_SEMANTIC_CANDIDATE",
            "why": EXTERNAL_DETECTOR_IS_A_CANDIDATE_NEVER_AN_AUTHORITY,
        },

        "SCORING": {
            "nothing_is_scored_here": NOTHING_IS_SCORED_HERE,
            "the_later_scorer_evaluates_two_levels":
                list(THE_LATER_SCORER_EVALUATES_TWO_LEVELS),
        },

        "PARAMETERS": _PARAMS(),
        "PROTOCOL_HASH": protocol_hash(),
    }
