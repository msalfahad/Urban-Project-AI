"""SEMANTIC_SAFETY_EXPERIMENT_02 - the protocol, written before anything ran.

E1.4 stays frozen at

    d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb

SEMANTIC_EDGE_EXPERIMENT_01 is frozen at 39bdf0d3..., and
SEMANTIC_EDGE_SCORING_01 at 8a6dd659..., which classified A19

    A19_NOT_READY

on one critical false positive: where an independent reference reads an
OPENING in a stair-hall wall, A19 asserted VISIBLE_MATERIAL_WALL_FACE.
That gate is not weakened here. Nothing in this experiment feeds geometry,
computes an area, or opens a quantity benchmark.

THE NARROWER QUESTION

The earlier work answered "can a multimodal reader understand
architectural feature assemblies" well enough to keep testing. This one
asks the production question:

    can A19 SAFELY distinguish the relations that change geometry -
    above all PHYSICAL SEPARATOR from OPENING and from NON-SEPARATOR

and it is built to falsify that, not to confirm it. It is not a general
vocabulary benchmark, and a reader that names every subtype beautifully
while calling one opening a wall has failed it.

WHY THE SAMPLE IS BUILT FROM SCRATCH

The frozen experiment exposed three defects in its own apparatus, each
found by a blind reader before the code found it:

    FEATURE DUPLICATION   34 questions over about 27 features, and the
                          scoring canonicalisation still split one window
                          across four features, because it required a
                          shared parent entity and a window is several
                          entities
    LABEL COLLISION       39 of 382 marked members had their index label
                          overprinted at every crop level, so no reader
                          could tie a label to a line
    QUESTION MIS-TRIGGER  5 of 5 groups asked the curve-family question
                          had no arc among their marked members

None of that is repaired in place: the frozen experiments stand as they
were produced. This one fixes the apparatus BEFORE a reader sees anything,
and refuses to admit a feature whose markup it cannot prove legible.

THE ORDER, WHICH IS THE METHOD

    1. this protocol is written and hashed
    2. canonical features are built from source geometry alone, so each
       physical feature appears exactly once
    3. crops are rendered with leader lines and a collision test, and a
       machine gate refuses any feature whose tags it cannot prove
       unambiguous
    4. specialised questions are asked only where the source carries the
       evidence to answer them
    5. the reference is read blind, twice for every geometry-changing
       feature, and frozen
    6. only then does A19 run, and the checker runs blind of both
"""

from __future__ import annotations

import hashlib

EXPERIMENT_ID = "SEMANTIC_SAFETY_EXPERIMENT_02"
PROTOCOL_VERSION = 3

SUPERSEDED_PROTOCOL_V1_HASH = (
    "6eb2edb4ce04272545c056cbeee21058b1a5ba9e628d2ec68dcd3c7ff2bda4ed")
SUPERSEDED_PROTOCOL_V2_HASH = (
    "9042244ddc40a812da0e051010a888f3372642164c31d8026eb64621a2765e1a")

WHY_V2_WAS_SUPERSEDED_BEFORE_ANY_READER_RAN = (
    "v2 still carried a collision, and this one was in the drawing rather "
    "than in the code. The feature holding the prior critical error is a "
    "doorway whose wall opening the drawing overlays with a door block's "
    "linework, so several of its members are drawn coincident with each "
    "other. The tag placer, trying ten radii by eight directions by seven "
    "anchor positions per member at up to 3600 pixels, can place five of "
    "fourteen tags without a leader running under another member's "
    "anchor. Those members cannot be pointed at individually by anyone.\n\n"
    "So the render gate and the regression rule could not both hold for "
    "that one feature, and the owner decided: admit it, tag what can be "
    "tagged, and declare the rest.\n\n"
    "v3 adds PARTIAL_TAGGING_ADMISSION, available ONLY to a feature the "
    "regression rule requires. Every other feature still faces the "
    "absolute gate, because a gate with a general exception is not a "
    "gate. Decided and recorded before any reference reader, A19 or "
    "checker saw anything")

PARTIAL_TAGGING_ADMISSION = "PARTIAL_TAGGING_ADMISSION"

PARTIAL_TAGGING_RULE = (
    "a feature admitted this way shows every member in the member colour "
    "and tags only those whose tags the placer can prove legible. Its "
    "task declares how many members are shown without an individual tag "
    "and why. The PRIMARY output - the feature's physical relation to the "
    "space around it - needs no per-member tag and is scored normally. "
    "The untagged members are excluded from tertiary sub-role scoring and "
    "the exclusion is recorded on the feature. Only a feature the "
    "regression rule requires may be admitted this way")

WHY_THE_PRIMARY_QUESTION_SURVIVES_PARTIAL_TAGGING = (
    "whether space flows through a doorway is a question about the "
    "feature, not about which of its lines is the jamb. A reader that "
    "cannot say which line is which can still say that this is an opening "
    "in a separator, and that is the claim this experiment exists to "
    "test")

WHY_V1_WAS_SUPERSEDED_BEFORE_ANY_READER_RAN = (
    "v1 carried two rules that collided on this drawing. The regression "
    "rule says the feature holding the prior critical error is admitted "
    "whatever the quotas do; the member cap says a feature with more "
    "members than the cap is not admitted. The feature holding that error "
    "grew to forty-two members, so both rules applied and disagreed.\n\n"
    "The collision exposed the real defect: growth was capped by EXTENT "
    "alone, so a wall junction pulled in everything touching it and the "
    "floor split into many single-interval features and a tail of "
    "forty-member blobs. A blob is not an architectural feature and could "
    "never have been tagged legibly.\n\n"
    "v2 stops growth on the member cap as well as the extent cap, so "
    "every feature is feature-sized by construction and the collision "
    "cannot arise, and it offers the tag placer more candidate radii. "
    "Nothing else changes.\n\n"
    "This was done BEFORE any reference reader, A19 or checker saw "
    "anything, and before any semantic answer existed. v1's hash is "
    "recorded above so the change is checkable, and no rule is touched "
    "once a reader has run")
EXPERIMENT_CLASS = "RESEARCH_ONLY_NOT_A_PRODUCTION_RUN"
MODEL = "A_READER_IS_SAFE_ONLY_IF_IT_NEVER_CALLS_AN_OPENING_A_WALL_V1"

E1_4_RUN_HASH = (
    "d72610c27ffa85e8acff75361f913578a7f1574d811c3e0d4e78047dac5b2aeb")
EDGE_EXPERIMENT_FREEZE = (
    "39bdf0d3b38eee7fc6df2f59d0e680bd355e370754772afca6ea8bdb049ee856")
EDGE_SCORING_FREEZE = (
    "8a6dd659d8fda50cfcd98f70bc7e2431ac0a2c80bbd4ee322d68fb452c959a74")

THE_QUESTION = (
    "can A19 safely distinguish the architectural relations that change "
    "geometry, above all PHYSICAL SEPARATOR from OPENING and from "
    "NON-SEPARATOR")

THIS_IS_BUILT_TO_FALSIFY_IT = (
    "a reader that names every subtype correctly and calls one opening a "
    "wall has failed this experiment. Nothing here rewards vocabulary")

THE_GATE_IS_NOT_WEAKENED = (
    "the prior stage classified A19 NOT READY on a single critical false "
    "positive. That standard stands: one high-confidence critical "
    "physical-relation error disqualifies A19 from affecting geometry, "
    "whatever any average says")

NOTHING_IS_FED_BACK = (
    "no result from this experiment reaches E1.4, room boundaries, "
    "fragment recovery, any arrangement, opening geometry or any area. "
    "Freeze and score first")

NO_QUANTITY_BENCHMARK = (
    "no workbook, no room area, no known m2, no corrected polygon and no "
    "commercial quantity is opened at any point")

# ==================================================================
# 1. the dangerous errors - §2
# ==================================================================

FALSE_SEPARATOR_ERRORS = (
    "OPENING_AS_WALL", "WINDOW_AS_SOLID_WALL", "COUNTER_AS_WALL",
    "CABINET_AS_WALL", "DIMENSION_AS_WALL", "ANNOTATION_AS_WALL",
    "DOOR_SWING_AS_WALL", "HIDDEN_LINE_AS_VISIBLE_SEPARATOR",
)
MISSED_SEPARATOR_ERRORS = (
    "REAL_WALL_AS_OPENING", "REAL_SEPARATOR_AS_NON_SEPARATOR",
    "GLAZED_SEPARATOR_AS_OPEN_VOID",
)

WHY_THESE_AND_NOT_SUBTYPES = (
    "each of these changes topology, room extent or perimeter. A "
    "disagreement between WINDOW_FRAME and WINDOW_JAMB changes nothing "
    "downstream. The matrix is never averaged with subtype disagreements")

# ==================================================================
# 2. canonical features - §4
# ==================================================================

CANONICAL_ID_PREFIX = "CAF-"

THE_SAMPLING_UNIT = "CANONICAL_ARCHITECTURAL_FEATURE"

WHAT_A_CANONICAL_FEATURE_IS = (
    "a maximal set of source intervals that the drawing's own geometry "
    "joins into one local thing, grown from a seed in stable id order and "
    "stopped before it outgrows a single architectural feature. Every "
    "interval belongs to exactly one, so no feature can be sampled twice")

GROUPING_RELATIONS = (
    "SAME_PARENT_ENTITY: another interval of the same drawn entity",
    "SHARED_ENDPOINT: an endpoint within JOIN_MM",
    "INTERSECTION: the two cross",
    "PARALLEL_PAIR: parallel within PARALLEL_DEG, overlapping by at least "
    "MIN_PARALLEL_OVERLAP_MM, at an offset within FEATURE_OFFSET_MM",
    "COMMON_BLOCK: placed by the same block reference",
)

THE_EXTENT_CAP_IS_WHAT_KEEPS_A_FEATURE_A_FEATURE = (
    "without a cap the wall network is one component and the whole floor "
    "is one feature. Growth stops when adding an interval would push the "
    "feature past MAX_FEATURE_EXTENT_MM in extent OR past "
    "MAX_FEATURE_MEMBERS in members. Both are geometric limits declared "
    "in advance and neither consults meaning. The member limit stops "
    "growth rather than rejecting a grown feature afterwards, so a "
    "feature is feature-sized by construction")

NOTHING_SEMANTIC_IS_USED_TO_GROUP = (
    "no A19 answer, no reference answer, no expected semantic class, no "
    "room area and no closure result takes any part in forming a feature. "
    "Only entity identity, endpoints, intersection, parallelism, block "
    "membership and extent")

CANONICAL_FEATURE_FIELDS = (
    "CANONICAL_FEATURE_ID", "SOURCE_ENTITY_IDS", "SOURCE_INTERVAL_IDS",
    "ORIGINATING_SEED_IDS", "MERGE_EVIDENCE",
)

JOIN_MM = 25.0
PARALLEL_DEG = 3.0
MIN_PARALLEL_OVERLAP_MM = 150.0
FEATURE_OFFSET_MM = 700.0
MAX_FEATURE_EXTENT_MM = 4500.0
MAX_FEATURE_MEMBERS = 14

WHY_MEMBERS_ARE_CAPPED = (
    "every member of a scored feature must carry a legible tag, and a "
    "crop cannot carry more than about this many without them colliding. "
    "The cap stops growth, so no feature is ever built that could not be "
    "marked, and nothing has to be thrown away for being too big")

# ==================================================================
# 3. the renderer and its gate - §5
# ==================================================================

RENDER_RULES = (
    "each tagged member's label is placed in a box joined to the member by "
    "a leader line, never printed on the member itself",
    "candidate label positions are tried in a declared order - eight "
    "directions at increasing radius - and the first that passes every "
    "test is used",
    "a position passes when its box lies wholly inside the crop with a "
    "margin, overlaps no box already placed, and its leader crosses no "
    "box already placed and no other member's anchor",
    "if no candidate position passes, the member has no legible tag and "
    "its feature fails admission",
)

TAG_BOX_W_PX = 46
TAG_BOX_H_PX = 20
TAG_MARGIN_PX = 6
TAG_MIN_GAP_PX = 4
LEADER_CLEAR_PX = 8
TAG_RADII_PX = (26, 38, 52, 70, 92, 118, 150, 190, 240, 300)
TAG_DIRECTIONS_DEG = (315, 45, 225, 135, 0, 180, 90, 270)

RENDER_QA_FIELDS = ("TAG_VISIBLE", "TAG_TO_ENTITY_LINK_UNAMBIGUOUS")

ADMISSION_FAILS_WHEN = (
    "two tag boxes overlap by more than TAG_MIN_GAP_PX",
    "a leader line crosses another member's tag box or passes within "
    "LEADER_CLEAR_PX of another member's anchor",
    "a tag box falls outside the rendered crop",
    "a tagged member has no drawable geometry inside the crop",
)

THE_READER_IS_NOT_ASKED_TO_WORK_AROUND_BAD_MARKUP = (
    "in the frozen experiment 39 members were unreadable at every scale "
    "and the readers correctly answered UNRESOLVED, which cost the "
    "measurement and told us nothing about the reader. Here the markup is "
    "proved legible by machine before a reader sees it, and a feature "
    "that cannot be marked legibly is left out and counted")

# ==================================================================
# 4. question applicability - §6
# ==================================================================

APPLICABILITY_RULES = (
    "CURVE_FAMILY is asked only when at least one tagged member is an ARC "
    "or a CIRCLE",
    "FENESTRATION_DETAIL is asked only when the feature carries a member "
    "on a layer the drawing uses for openings, or lies in the outer "
    "envelope band",
    "DOOR_RELATION is asked only when door or opening evidence from the "
    "frozen E1.4 source layer lies within DOOR_REACH_MM",
)

DOOR_REACH_MM = 1200.0
ENVELOPE_BAND_MM = 1500.0

NO_IRRELEVANT_QUESTION_REACHES_THE_READER = (
    "asking about curves where there are none taught us nothing and "
    "produced five UNRESOLVED answers that scored against nobody. Every "
    "specialised question now carries its own applicability evidence, and "
    "an inapplicable question is not asked at all")

# ==================================================================
# 5. the sample - §7
# ==================================================================

SAMPLE_MIN = 32
SAMPLE_MAX = 40

# Source signatures, not semantic claims. Each is a mechanical property of
# the drawing chosen to make a target category likely to appear. What a
# feature IS remains for the reference to say.
STRATA = (
    ("S1_PAIRED_BAND", 6,
     "the feature contains a pair of parallel members at a separation "
     "inside the drawing's own wall-thickness band"),
    ("S2_OPENING_LAYER", 6,
     "the feature contains a member on a layer the drawing uses for "
     "openings, or spans a gap the frozen gap register recorded"),
    ("S3_DOOR_EVIDENCE", 6,
     "door geometry from the frozen source layer lies within "
     "DOOR_REACH_MM of the feature"),
    ("S4_FITTED_UNIT_OFFSET", 5,
     "the feature runs parallel to established material at a separation "
     "inside the fitted-unit depth band"),
    ("S5_STRUCTURAL_LOOP", 4,
     "the feature contains a small closed loop, or members on a layer "
     "holding almost nothing but such loops"),
    ("S6_STAIR_OR_NOT_IN_CUT_PLANE", 4,
     "stair geometry lies near the feature, or its members carry a "
     "linetype the drawing uses for geometry above or below the cut"),
    ("S7_ANNOTATION_LAYER", 3,
     "the feature's members sit on a dimension or annotation layer"),
    ("S8_OTHER_HIGH_IMPACT_AMBIGUITY", 6,
     "anything else in the cut plane whose role the deterministic layer "
     "did not settle"),
)

TIE_BREAK = "lowest stable source interval id ascending"

DO_NOT_FABRICATE_TO_MEET_A_QUOTA = (
    "a stratum that cannot fill its target records the shortfall. No "
    "feature is invented, stretched or hand-picked to make a number, and "
    "no easy example is chosen because it is easy. The strata are source "
    "signatures and they are not predictions of the answer")

# ==================================================================
# 6. the regression case - §13
# ==================================================================

REGRESSION_SOURCE_INTERVALS = ("E1_2:CAD-1021#01", "E1_2:CAD-1021#02")

REGRESSION_RULE = (
    "whichever canonical feature contains the source intervals of the "
    "prior critical error is admitted to the scored sample, whatever the "
    "strata quotas do. It is rendered, asked and scored by exactly the "
    "same pipeline as every other feature: its prompt is not altered, its "
    "expected answer is not named anywhere, and no reader is told it is a "
    "regression case. Its only purpose is that the failure mode cannot be "
    "quietly forgotten")

THE_REGRESSION_CASE_IS_NOT_THE_ONLY_OPENING = (
    "an experiment that contained one opening would measure whether the "
    "reader remembered one picture. The opening strata are filled "
    "mechanically and the regression feature is one of them")

# ==================================================================
# 7. the relation vocabulary - §8, §10
# ==================================================================

PHYSICAL_SEPARATOR = "PHYSICAL_SEPARATOR"
GLAZED_PHYSICAL_SEPARATOR = "GLAZED_PHYSICAL_SEPARATOR"
OPENING_IN_SEPARATOR = "OPENING_IN_SEPARATOR"
NON_SEPARATOR_FEATURE = "NON_SEPARATOR_FEATURE"
OBSTACLE = "OBSTACLE"
OVERHEAD_OR_HIDDEN = "OVERHEAD_OR_HIDDEN"
ANNOTATION_OR_DIMENSION = "ANNOTATION_OR_DIMENSION"
RELATION_UNRESOLVED = "UNRESOLVED"

PHYSICAL_RELATIONS = (
    PHYSICAL_SEPARATOR, GLAZED_PHYSICAL_SEPARATOR, OPENING_IN_SEPARATOR,
    NON_SEPARATOR_FEATURE, OBSTACLE, OVERHEAD_OR_HIDDEN,
    ANNOTATION_OR_DIMENSION, RELATION_UNRESOLVED,
)

# Which of them assert that space is physically divided here.
SEPARATING = (PHYSICAL_SEPARATOR, GLAZED_PHYSICAL_SEPARATOR)
NOT_SEPARATING = (OPENING_IN_SEPARATOR, NON_SEPARATOR_FEATURE,
                  OVERHEAD_OR_HIDDEN, ANNOTATION_OR_DIMENSION)
SEPARATION_ASIDE = (OBSTACLE,)

GLAZING_IS_NOT_MASONRY_AND_IS_NOT_A_HOLE = (
    "a glazed separator divides space and carries no masonry. Folding it "
    "into PHYSICAL_SEPARATOR loses the fact that it is not a wall; "
    "folding it into OPENING loses the fact that a person cannot walk "
    "through it. It is scored as its own class and confusing it with "
    "either direction is a critical error")

ASSEMBLY_TYPES = (
    "WALL_ASSEMBLY", "WINDOW_OR_GLAZING_ASSEMBLY", "DOOR_ASSEMBLY",
    "COLUMN_OR_PIER_ASSEMBLY", "COUNTER_OR_CABINET_ASSEMBLY",
    "STAIR_ASSEMBLY", "POOL_OR_WATER_FEATURE", "MIXED_FEATURE", "OTHER",
    "UNRESOLVED",
)

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

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
CONFIDENCE_UNRESOLVED = "UNRESOLVED"
CONFIDENCE_CLASSES = (HIGH, MEDIUM, LOW, CONFIDENCE_UNRESOLVED)

THE_PRIMARY_OUTPUT_IS_THE_RELATION = (
    "readiness is decided by the physical relation and not by the "
    "assembly name. Knowing that a thing is a window matters less than "
    "knowing that space does not flow through it")

# ==================================================================
# 8. A19 still owns no geometry - §11
# ==================================================================

A19_MAY_NOT = (
    "create a line", "move a line", "create a coordinate",
    "state a dimension", "state an area", "state a perimeter",
    "close a polygon", "create opening geometry", "invent wall thickness",
)

IT_ONLY_INTERPRETS_WHAT_IS_TAGGED = (
    "A19 reads a picture of geometry the CAD file already owns and says "
    "what the tagged feature is to the space around it. The answer schema "
    "carries no numeric field of any kind and the screen runs as well")

# ==================================================================
# 9. context escalation - §12
# ==================================================================

ESCALATION_RULE = (
    "a reader may ask for more context once, by answering "
    "NEEDS_MORE_CONTEXT with a reason. The wider crop is then produced by "
    "a declared rule - the feature's own half extent multiplied by "
    "ESCALATION_FACTOR, not less than ESCALATION_MIN_HALF_MM - and nobody "
    "chooses the window by hand. If the feature is still unresolved after "
    "the wider crop, the answer is UNRESOLVED and no classification is "
    "forced")

ESCALATION_FACTOR = 3.0
ESCALATION_MIN_HALF_MM = 8000.0
ESCALATIONS_ALLOWED = 1

ESCALATION_FIELDS = ("ORIGINAL_CROP", "ESCALATED_CROP",
                     "WHY_CONTEXT_REQUESTED")

# ==================================================================
# 10. the reference - §8, §9
# ==================================================================

REFERENCE_SEES = (
    "the clean source context crop",
    "the clean feature crop",
    "the detail crop",
    "the tagged CAD members, each with a legible leader-line tag",
    "neutral layer, linetype and entity-type metadata",
)

REFERENCE_DOES_NOT_SEE = (
    "any A19 output from this or any earlier experiment",
    "the E1.4 semantic classification of any entity",
    "any earlier checker or visual finding",
    "any expected role, benchmark, area or quantity",
)

REFERENCE_ANSWERS_THE_RELATION_FIRST = (
    "the reference says what the feature is to the space around it before "
    "it says what kind of assembly it is, because that is the claim the "
    "experiment is about")

DUAL_REFERENCE_RULE = (
    "every feature whose FIRST reference relation is geometry-changing - "
    "separator, glazed separator, opening, non-separator or obstacle - is "
    "read again by a second reference reader who has seen neither A19 nor "
    "the first reference"
)

GEOMETRY_CHANGING_RELATIONS = (
    PHYSICAL_SEPARATOR, GLAZED_PHYSICAL_SEPARATOR, OPENING_IN_SEPARATOR,
    NON_SEPARATOR_FEATURE, OBSTACLE,
)

REFERENCE_CONFLICT = "REFERENCE_CONFLICT"

NO_MANUFACTURED_TRUTH = (
    "where the two reference readers disagree about the relation the "
    "feature is REFERENCE_CONFLICT: excluded from strict accuracy, "
    "reported on its own, never resolved by a vote. Two independent "
    "readers disagreeing is evidence that the drawing is ambiguous there, "
    "which is itself a finding")

THE_REFERENCE_MAY_NOT_GUESS = (
    "where the drawing does not establish the relation, the reference "
    "says UNRESOLVED. A fabricated ground truth makes every number below "
    "meaningless and looks exactly like a good result")

# ==================================================================
# 11. the checker - §14
# ==================================================================

CHECKER_QUESTION = "IS_THERE_A_PHYSICAL_SEPARATOR_AT_THIS_FEATURE"
CHECKER_ANSWERS = ("YES", "NO", "GLAZED", "OPENING", "OBSTACLE",
                   "UNRESOLVED")

WHY_THE_CHECKER_WAS_REDESIGNED = (
    "the old checker agreed with A19 on ten of eleven groups and caught "
    "no error, because there was no error in its groups to catch. Its "
    "value was unproven, not demonstrated. It now answers one narrow "
    "question that maps onto the thing that matters, so that agreement "
    "and disagreement both mean something")

CHECKER_SEES = ("the source crops", "the tagged members")
CHECKER_DOES_NOT_SEE = ("A19's answer", "the reference", "E1.4",
                        "any benchmark")

NO_VOTING = (
    "the checker is compared with A19 and with the reference after all "
    "three are frozen. It is never averaged with either and never breaks "
    "a tie")

# ==================================================================
# 12. scoring - §15, §16
# ==================================================================

PHYSICAL_RELATION_EXACT_MATCH = "PHYSICAL_RELATION_EXACT_MATCH"
PHYSICAL_RELATION_WRONG = "PHYSICAL_RELATION_WRONG"
A19_UNRESOLVED = "A19_UNRESOLVED"
REFERENCE_UNRESOLVED = "REFERENCE_UNRESOLVED"

RELATION_OUTCOMES = (PHYSICAL_RELATION_EXACT_MATCH,
                     PHYSICAL_RELATION_WRONG, A19_UNRESOLVED,
                     REFERENCE_UNRESOLVED, REFERENCE_CONFLICT)

CRITICAL_FALSE_SEPARATOR = "CRITICAL_FALSE_SEPARATOR"
CRITICAL_MISSED_SEPARATOR = "CRITICAL_MISSED_SEPARATOR"

CRITICAL_DEFINITIONS = (
    (CRITICAL_FALSE_SEPARATOR,
     "A19 says a separator or a glazed separator where the reference "
     "establishes an opening, a non-separator, annotation or hidden "
     "geometry. Space is divided that the drawing leaves open"),
    (CRITICAL_MISSED_SEPARATOR,
     "A19 says an opening, a non-separator, annotation or hidden geometry "
     "where the reference establishes a separator or a glazed separator. "
     "Space flows through something the drawing builds"),
    ("GLAZED_CONFUSED_WITH_SOLID",
     "A19 and the reference disagree between PHYSICAL_SEPARATOR and "
     "GLAZED_PHYSICAL_SEPARATOR. Space is divided either way, so this is "
     "reported apart from the two critical classes and is never folded "
     "into them"),
    ("GLAZED_CONFUSED_WITH_OPEN",
     "A19 says a glazed separator where the reference establishes an "
     "opening, or the reverse. This IS a critical error: a person can "
     "walk through one and not the other"),
)

ABSTAINING_IS_NOT_AN_ERROR = (
    "A19 answering UNRESOLVED has asserted nothing. It is counted and "
    "reported, and it never triggers a critical-error gate. A reader that "
    "abstains costs a human a look; a reader that guesses costs a wrong "
    "building, and the two are not scored alike")

# §16 - declared before any score exists
THE_ASYMMETRIC_GATE = (
    "A19 cannot become geometry-affecting semantic evidence if ANY "
    "HIGH-confidence critical physical-relation error occurs - a false "
    "separator, a missed separator, or glazing confused with an opening. "
    "One is enough. No average overrides it")

# ==================================================================
# 13. authority levels - §17
# ==================================================================

LEVEL_0 = "LEVEL_0_DIAGNOSTIC_ONLY"
LEVEL_1 = "LEVEL_1_FEATURE_ASSEMBLY_CANDIDATE_EVIDENCE"
LEVEL_2 = "LEVEL_2_RELATION_CANDIDATE_EVIDENCE"
LEVEL_3 = "LEVEL_3_CORROBORATED_SEMANTIC_EVIDENCE"
LEVEL_4 = "LEVEL_4_SEMANTIC_AUTHORITY"

AUTHORITY_LEVELS = (LEVEL_0, LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4)

LEVEL_MEANING = {
    LEVEL_0: "diagnostic only",
    LEVEL_1: ("can identify likely windows, doors, walls and the rest, "
              "and may not change topology"),
    LEVEL_2: ("a high-confidence relation may enter an evidence ledger "
              "and cannot independently change geometry"),
    LEVEL_3: ("a high-confidence relation may affect geometry ONLY when "
              "independently corroborated by deterministic CAD evidence "
              "or another independent source"),
    LEVEL_4: ("semantic authority. Not expected at this stage and "
              "requiring substantially broader blind validation "
              "including a third project"),
}

# Read in order; the first that fits decides. Written before any score.
AUTHORITY_RULES = (
    (LEVEL_0,
     "any HIGH-confidence critical physical-relation error, or fewer than "
     "ten reference-resolved features to judge on, or high-confidence "
     "relation accuracy at or below two thirds"),
    (LEVEL_1,
     "no HIGH-confidence critical error, but a critical error at any "
     "lower confidence, or high-confidence relation accuracy below nine "
     "in ten"),
    (LEVEL_2,
     "no critical physical-relation error at any confidence, and "
     "high-confidence relation accuracy of nine in ten or better"),
    (LEVEL_3,
     "all of LEVEL 2, and the independent checker agrees with the "
     "reference on every high-confidence A19 relation, so that a second "
     "independent source corroborates each one"),
)

LEVEL_4_IS_NOT_REACHABLE_HERE = (
    "one project cannot establish semantic authority however well it "
    "scores. LEVEL 4 is not assignable by this experiment and the rules "
    "above cannot produce it")

DO_NOT_PROMOTE_ON_ONE_PROJECT = (
    "every figure here comes from one ground floor of one villa. A level "
    "is a statement about what the evidence supports, not a plan")

THE_SAMPLE_IS_NOT_RANDOM = (
    "the features are chosen by source signatures deliberately weighted "
    "towards the hard and the geometry-changing. No rate measured here "
    "may be multiplied out to a floor, a project or a portfolio")

DO_NOT_HIDE_THE_DENOMINATOR = (
    "every accuracy is reported with the count it was computed over, and "
    "with the reference-unresolved and reference-conflict cases stated "
    "beside it rather than dropped")


def _params() -> dict:
    return {
        "JOIN_MM": JOIN_MM, "PARALLEL_DEG": PARALLEL_DEG,
        "MIN_PARALLEL_OVERLAP_MM": MIN_PARALLEL_OVERLAP_MM,
        "FEATURE_OFFSET_MM": FEATURE_OFFSET_MM,
        "MAX_FEATURE_EXTENT_MM": MAX_FEATURE_EXTENT_MM,
        "MAX_FEATURE_MEMBERS": MAX_FEATURE_MEMBERS,
        "DOOR_REACH_MM": DOOR_REACH_MM,
        "ENVELOPE_BAND_MM": ENVELOPE_BAND_MM,
        "TAG_BOX_W_PX": TAG_BOX_W_PX, "TAG_BOX_H_PX": TAG_BOX_H_PX,
        "TAG_MARGIN_PX": TAG_MARGIN_PX, "TAG_MIN_GAP_PX": TAG_MIN_GAP_PX,
        "LEADER_CLEAR_PX": LEADER_CLEAR_PX,
        "TAG_RADII_PX": list(TAG_RADII_PX),
        "TAG_DIRECTIONS_DEG": list(TAG_DIRECTIONS_DEG),
        "ESCALATION_FACTOR": ESCALATION_FACTOR,
        "ESCALATION_MIN_HALF_MM": ESCALATION_MIN_HALF_MM,
        "ESCALATIONS_ALLOWED": ESCALATIONS_ALLOWED,
        "SAMPLE_MIN": SAMPLE_MIN, "SAMPLE_MAX": SAMPLE_MAX,
    }


def protocol_hash() -> str:
    parts = ([EXPERIMENT_ID, f"V{PROTOCOL_VERSION}",
              SUPERSEDED_PROTOCOL_V1_HASH, SUPERSEDED_PROTOCOL_V2_HASH,
              PARTIAL_TAGGING_ADMISSION, PARTIAL_TAGGING_RULE,
              MODEL, THE_QUESTION, E1_4_RUN_HASH,
              EDGE_EXPERIMENT_FREEZE, EDGE_SCORING_FREEZE]
             + list(FALSE_SEPARATOR_ERRORS) + list(MISSED_SEPARATOR_ERRORS)
             + list(GROUPING_RELATIONS) + list(CANONICAL_FEATURE_FIELDS)
             + list(RENDER_RULES) + list(ADMISSION_FAILS_WHEN)
             + list(APPLICABILITY_RULES)
             + [f"{n}:{q}:{w}" for n, q, w in STRATA]
             + [REGRESSION_RULE] + list(REGRESSION_SOURCE_INTERVALS)
             + list(PHYSICAL_RELATIONS) + list(ASSEMBLY_TYPES)
             + list(ENTITY_SUB_ROLES) + list(CONFIDENCE_CLASSES)
             + list(A19_MAY_NOT) + [ESCALATION_RULE]
             + list(REFERENCE_SEES) + list(REFERENCE_DOES_NOT_SEE)
             + [DUAL_REFERENCE_RULE] + list(GEOMETRY_CHANGING_RELATIONS)
             + [CHECKER_QUESTION] + list(CHECKER_ANSWERS)
             + list(RELATION_OUTCOMES)
             + [f"{n}:{d}" for n, d in CRITICAL_DEFINITIONS]
             + [THE_ASYMMETRIC_GATE]
             + [f"{c}:{r}" for c, r in AUTHORITY_RULES]
             + [f"{k}={v}" for k, v in sorted(_params().items())])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    return {
        "EXPERIMENT_ID": EXPERIMENT_ID,
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
        "SUPERSEDED_PROTOCOL_V1_HASH": SUPERSEDED_PROTOCOL_V1_HASH,
        "SUPERSEDED_PROTOCOL_V2_HASH": SUPERSEDED_PROTOCOL_V2_HASH,
        "why_v1_was_superseded_before_any_reader_ran":
            WHY_V1_WAS_SUPERSEDED_BEFORE_ANY_READER_RAN,
        "why_v2_was_superseded_before_any_reader_ran":
            WHY_V2_WAS_SUPERSEDED_BEFORE_ANY_READER_RAN,
        "PARTIAL_TAGGING_ADMISSION": {
            "RULE": PARTIAL_TAGGING_RULE,
            "AVAILABLE_ONLY_TO_A_REGRESSION_FEATURE": True,
            "why_the_primary_question_survives_partial_tagging":
                WHY_THE_PRIMARY_QUESTION_SURVIVES_PARTIAL_TAGGING,
            "THE_GATE_REMAINS_ABSOLUTE_FOR_EVERY_OTHER_FEATURE": True,
            "DECIDED_BY_THE_OWNER_BEFORE_ANY_READER_RAN": True,
        },
        "NO_READER_HAD_SEEN_ANYTHING_WHEN_V1_WAS_REPLACED": True,
        "NO_SEMANTIC_ANSWER_EXISTED_WHEN_V1_WAS_REPLACED": True,
        "EXPERIMENT_CLASS": EXPERIMENT_CLASS,
        "MODEL": MODEL,
        "THIS_IS_NOT_E1_5_AND_NOT_PRODUCTION_E2": True,
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": E1_4_RUN_HASH,
        "SEMANTIC_EDGE_EXPERIMENT_01_FREEZE": EDGE_EXPERIMENT_FREEZE,
        "SEMANTIC_EDGE_SCORING_01_FREEZE": EDGE_SCORING_FREEZE,
        "THE_FROZEN_WORK_IS_NOT_REPAIRED_IN_PLACE": True,

        "THE_QUESTION": THE_QUESTION,
        "this_is_built_to_falsify_it": THIS_IS_BUILT_TO_FALSIFY_IT,
        "the_gate_is_not_weakened": THE_GATE_IS_NOT_WEAKENED,
        "nothing_is_fed_back": NOTHING_IS_FED_BACK,
        "no_quantity_benchmark": NO_QUANTITY_BENCHMARK,

        "THE_DANGEROUS_ERRORS": {
            "FALSE_SEPARATOR": list(FALSE_SEPARATOR_ERRORS),
            "MISSED_SEPARATOR": list(MISSED_SEPARATOR_ERRORS),
            "why_these_and_not_subtypes": WHY_THESE_AND_NOT_SUBTYPES,
        },

        "CANONICAL_FEATURES": {
            "THE_SAMPLING_UNIT": THE_SAMPLING_UNIT,
            "WHAT_IT_IS": WHAT_A_CANONICAL_FEATURE_IS,
            "GROUPING_RELATIONS": list(GROUPING_RELATIONS),
            "the_extent_cap_is_what_keeps_a_feature_a_feature":
                THE_EXTENT_CAP_IS_WHAT_KEEPS_A_FEATURE_A_FEATURE,
            "nothing_semantic_is_used_to_group":
                NOTHING_SEMANTIC_IS_USED_TO_GROUP,
            "FIELDS": list(CANONICAL_FEATURE_FIELDS),
            "why_members_are_capped": WHY_MEMBERS_ARE_CAPPED,
        },

        "RENDERER": {
            "RULES": list(RENDER_RULES),
            "QA_FIELDS": list(RENDER_QA_FIELDS),
            "ADMISSION_FAILS_WHEN": list(ADMISSION_FAILS_WHEN),
            "the_reader_is_not_asked_to_work_around_bad_markup":
                THE_READER_IS_NOT_ASKED_TO_WORK_AROUND_BAD_MARKUP,
        },

        "QUESTION_APPLICABILITY": {
            "RULES": list(APPLICABILITY_RULES),
            "FIELDS": ["QUESTION_APPLICABILITY", "APPLICABILITY_EVIDENCE"],
            "no_irrelevant_question_reaches_the_reader":
                NO_IRRELEVANT_QUESTION_REACHES_THE_READER,
        },

        "SAMPLE": {
            "SAMPLE_MIN": SAMPLE_MIN, "SAMPLE_MAX": SAMPLE_MAX,
            "STRATA": [{"NAME": n, "TARGET": q, "SOURCE_SIGNATURE": w}
                       for n, q, w in STRATA],
            "TIE_BREAK": TIE_BREAK,
            "do_not_fabricate_to_meet_a_quota":
                DO_NOT_FABRICATE_TO_MEET_A_QUOTA,
            "THE_STRATA_ARE_SOURCE_SIGNATURES_NOT_PREDICTED_ANSWERS": True,
        },

        "REGRESSION_CASE": {
            "SOURCE_INTERVALS": list(REGRESSION_SOURCE_INTERVALS),
            "RULE": REGRESSION_RULE,
            "it_is_not_the_only_opening":
                THE_REGRESSION_CASE_IS_NOT_THE_ONLY_OPENING,
            "NO_READER_IS_TOLD_IT_IS_A_REGRESSION_CASE": True,
        },

        "VOCABULARY": {
            "PRIMARY_PHYSICAL_RELATIONS": list(PHYSICAL_RELATIONS),
            "SEPARATING": list(SEPARATING),
            "NOT_SEPARATING": list(NOT_SEPARATING),
            "SEPARATION_ASIDE": list(SEPARATION_ASIDE),
            "glazing_is_not_masonry_and_is_not_a_hole":
                GLAZING_IS_NOT_MASONRY_AND_IS_NOT_A_HOLE,
            "SECONDARY_ASSEMBLY_TYPES": list(ASSEMBLY_TYPES),
            "TERTIARY_ENTITY_SUB_ROLES": list(ENTITY_SUB_ROLES),
            "CONFIDENCE_CLASSES": list(CONFIDENCE_CLASSES),
            "the_primary_output_is_the_relation":
                THE_PRIMARY_OUTPUT_IS_THE_RELATION,
        },

        "A19_OWNS_NO_GEOMETRY": {
            "MAY_NOT": list(A19_MAY_NOT),
            "it_only_interprets_what_is_tagged":
                IT_ONLY_INTERPRETS_WHAT_IS_TAGGED,
        },

        "CONTEXT_ESCALATION": {
            "RULE": ESCALATION_RULE,
            "FIELDS": list(ESCALATION_FIELDS),
            "ESCALATIONS_ALLOWED": ESCALATIONS_ALLOWED,
        },

        "REFERENCE": {
            "SEES": list(REFERENCE_SEES),
            "DOES_NOT_SEE": list(REFERENCE_DOES_NOT_SEE),
            "answers_the_relation_first": REFERENCE_ANSWERS_THE_RELATION_FIRST,
            "DUAL_REFERENCE_RULE": DUAL_REFERENCE_RULE,
            "GEOMETRY_CHANGING_RELATIONS": list(GEOMETRY_CHANGING_RELATIONS),
            "no_manufactured_truth": NO_MANUFACTURED_TRUTH,
            "may_not_guess": THE_REFERENCE_MAY_NOT_GUESS,
            "THE_REFERENCE_FREEZES_BEFORE_A19_IS_OPENED": True,
        },

        "CHECKER": {
            "QUESTION": CHECKER_QUESTION,
            "ANSWERS": list(CHECKER_ANSWERS),
            "SEES": list(CHECKER_SEES),
            "DOES_NOT_SEE": list(CHECKER_DOES_NOT_SEE),
            "why_it_was_redesigned": WHY_THE_CHECKER_WAS_REDESIGNED,
            "no_voting": NO_VOTING,
        },

        "SCORING": {
            "RELATION_OUTCOMES": list(RELATION_OUTCOMES),
            "CRITICAL_DEFINITIONS": [{"NAME": n, "MEANS": d}
                                     for n, d in CRITICAL_DEFINITIONS],
            "abstaining_is_not_an_error": ABSTAINING_IS_NOT_AN_ERROR,
            "THE_ASYMMETRIC_GATE": THE_ASYMMETRIC_GATE,
        },

        "AUTHORITY": {
            "LEVELS": list(AUTHORITY_LEVELS),
            "MEANING": dict(LEVEL_MEANING),
            "RULES": [{"LEVEL": c, "RULE": r} for c, r in AUTHORITY_RULES],
            "level_4_is_not_reachable_here": LEVEL_4_IS_NOT_REACHABLE_HERE,
            "do_not_promote_on_one_project": DO_NOT_PROMOTE_ON_ONE_PROJECT,
        },

        "the_sample_is_not_random": THE_SAMPLE_IS_NOT_RANDOM,
        "do_not_hide_the_denominator": DO_NOT_HIDE_THE_DENOMINATOR,
        "PARAMETERS": _params(),
        "PROTOCOL_HASH": protocol_hash(),
    }
