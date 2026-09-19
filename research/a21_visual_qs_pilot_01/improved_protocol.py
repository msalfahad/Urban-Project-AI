"""A21_SOURCE_PRESENTATION_IMPROVED - the protocol, declared before the run.

ONE variable is under test: how the drawing is PRESENTED to the reader.
Nothing else moves. The cases, the QS rules, the blindness rules, the
withheld heights, the default policy, the height hierarchy, the schema and
the refusal logic are all carried across from the frozen baseline unchanged.

    python3 -m research.a21_visual_qs_pilot_01.improved_protocol

The baseline is not touched. This module asserts its hashes on import, so
if anything in the frozen baseline moved, nothing here can run.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from research.a21_visual_qs_pilot_01 import freeze_registry as B

RUN_ID = "A21_SOURCE_PRESENTATION_IMPROVED"
EXPERIMENT_ID = "A21_VISUAL_QS_PILOT_01"
BASELINE_RUN_ID = "A21_SOURCE_PRESENTATION_BASELINE"

# ==================================================================
# WHAT THIS RUN IS FOR
# ==================================================================

PURPOSE = (
    "test whether improved visual source presentation improves A21's "
    "ability to read printed dimensions, understand room/wall/opening "
    "relationships, locate cross-sheet evidence, reduce reader-to-reader "
    "divergence, reduce UNKNOWNs that were caused by presentation rather "
    "than by the drawing, and detect contradictions more consistently")

THIS_RUN_IS_NOT_JUDGED_BY = (
    "producing more quantities",
    "producing quantities closer to any benchmark",
    "reducing refusals at any cost",
    "matching E1.4",
    "matching Excel",
)

A_REFUSAL_REMAINS_CORRECT = (
    "if the source truly does not establish the input, the refusal is the "
    "right answer and counts as such. BASELINE=UNKNOWN -> IMPROVED=NUMBER "
    "is NOT automatically an improvement. An improved result must show "
    "STRONGER SOURCE EVIDENCE, named, or it is not an improvement")

# ==================================================================
# THE PRESENTATION CHANGE - the whole of the experimental variable
# ==================================================================

PACKET_LEVELS = (
    ("LEVEL_1_CONTEXT",
     "the case's own sheet, rotated to its VERIFIED natural reading "
     "orientation, mechanically trimmed to its drawn content, and "
     "downscaled by LANCZOS so its long edge lands on the runtime's own "
     "ceiling - so nothing is thrown away twice"),
    ("LEVEL_2_DETAIL",
     "a NATIVE-resolution lossless (PNG) crop of the subject, sized in "
     "metres of building, not pixels"),
    ("LEVEL_3_CROSS_SHEET",
     "section, elevation or roof plan, only where the case needs it, "
     "prepared exactly like LEVEL 1 and NEVER cropped selectively"),
)

# ------------------------------------------------------------------
# rotation
# ------------------------------------------------------------------
ROTATION_RULE = (
    "rotation is VERIFIED per page and never assumed. A wrong rotation "
    "measured WORSE than no rotation at all in the source-preparation "
    "tests, so each page is checked on its own")

ROTATION_RECORD_FIELDS = (
    "ORIGINAL_PAGE_ID", "ORIGINAL_HASH", "ROTATION_DEGREES",
    "ROTATED_RENDER_HASH", "COORDINATE_TRANSFORM",
)

NO_GEOMETRIC_DISTORTION = (
    "aspect ratio is preserved exactly. Rotation is a lossless 90 degree "
    "transpose, not a resample. Scaling is uniform in both axes")

# ------------------------------------------------------------------
# resolution
# ------------------------------------------------------------------
NATIVE_DPI = 399.5
PX_PER_METRE_AT_1_TO_100 = 157.3
RUNTIME_LONG_EDGE_CAP_PX = 2000

RESOLUTION_RULES = (
    "never render above native - 399.5 DPI is the ceiling and anything "
    "above it is invented detail",
    "the LEVEL 2 detail crop keeps NATIVE pixels and is written lossless, "
    "so no small printed dimension is softened by a JPEG pass",
    "size the detail crop in METRES of building: 12 m, which lands at "
    "about 1888 px and therefore passes the runtime untouched",
    "the LEVEL 1 and LEVEL 3 sheet images are reduced only as far as the "
    "runtime ceiling forces, and the reduction is done HERE with LANCZOS "
    "rather than left to an unknown resampler",
    "trim mechanically to the drawn content before reducing - blank paper "
    "costs resolution and carries nothing",
)

DETAIL_CROP_METRES = 12.0

# ------------------------------------------------------------------
# the anti-steering constraint - the most important line in this file
# ------------------------------------------------------------------
CROSS_SHEET_SOURCES_ARE_NEVER_CROPPED_SELECTIVELY = (
    "I have read the baseline results. I therefore KNOW where the height "
    "evidence sits on the sections. Cropping a section towards it would "
    "not be better presentation - it would be feeding a baseline "
    "discovery back to the reader as a pointer. Sections and elevations "
    "are supplied whole: rotated, content-trimmed, reduced, and never "
    "narrowed towards anything I know is there")

NO_SELECTIVE_DETAIL_CROP_FOR = ("CASE-4-STAIR", "CASE-5-EXTERNAL-FACADE",
                                "CASE-6-ROOF-PARAPET")

WHY_NOT_FOR_THOSE_THREE = (
    "a room has a seed point that predates this run and locating it is "
    "mechanical. A stair, a facade run and a parapet run do not. Placing "
    "a detail crop on them would mean ME choosing which part of the sheet "
    "matters, after having seen what the baseline found there. Those "
    "three cases therefore get the presentation improvements that are "
    "mechanical - rotation, trim, LANCZOS, no double downscale - and no "
    "crop. The uneven treatment is recorded rather than smoothed over")

# ==================================================================
# CASE-6 - the packet correction, and why it is not comparable
# ==================================================================

CASE_PACKET_CORRECTION = {
    "CASE_ID": "CASE-6-ROOF-PARAPET",
    "ADDED_SOURCE": "SECTION_B_B",
    "WHY": (
        "two sealed readers, in separate passes, independently reached "
        "for it to interpret the parapet, and both disclosed doing so. "
        "The parapet evidence the case turns on is dimensioned there. The "
        "declared source set could not answer the question I asked"),
    "THIS_IS_NOT_BENCHMARK_DRIVEN": (
        "the reason was established and frozen in PROTOCOL_DEVIATIONS "
        "before any benchmark, any A22 reconciliation and any Excel. No "
        "quantity informed it"),
    "DEV_01_AND_DEV_02_ARE_PRESERVED": (
        "both deviations stay in the experimental history exactly as "
        "written, including DEV-01's superseded fix. The record of my "
        "first wrong instinct - isolate the directories harder - is part "
        "of the result"),
}

CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON = (
    "CASE-6 carries TWO changes: improved presentation AND the correction "
    "of an incomplete declared source packet. It is reported separately "
    "as SOURCE_PRESENTATION_PLUS_PACKET_CORRECTION and is never pooled "
    "with cases 1-5 as presentation evidence")

CASE_6_CLASSIFICATION = "SOURCE_PRESENTATION_PLUS_PACKET_CORRECTION"
CASES_1_TO_5_CLASSIFICATION = "SOURCE_PRESENTATION_ONLY"

# ==================================================================
# CARRIED ACROSS UNCHANGED
# ==================================================================

UNCHANGED_FROM_BASELINE = (
    "the six selected cases", "case identities", "the Urban QS rules",
    "the blindness rules", "the withheld owner heights",
    "the door default policy", "the window default policy",
    "the height hierarchy", "the A21 calculation schema",
    "the treatment classifications", "the A21 refusal logic",
    "A22 disabled", "no Excel", "no E1.4 interpretation", "no benchmark",
    "no Firebase", "no BOQ",
)

PROMPTS_ARE_NOT_TUNED = (
    "the rules text is carried across BYTE-IDENTICAL from the frozen "
    "baseline prompts. The only permitted edits are the sandbox path, the "
    "case list, and a neutral description of what the three packet levels "
    "are. Every edit is recorded as a declared delta and diffed")

HEIGHT_EXPECTATION = (
    "easier reading is NOT a reason to relax Decision 1. If the drawing "
    "establishes STOREY_HEIGHT but not APPLICABLE_PLASTER_HEIGHT, the "
    "answer remains PLASTER_HEIGHT_NOT_ESTABLISHED. That outcome is "
    "expected and acceptable. 3.20 m is never derived from historical "
    "plausibility")

# ==================================================================
# BASELINE RESULTS ARE NOT PERMITTED INPUTS
# ==================================================================

BASELINE_DISCOVERIES_THAT_MUST_NOT_REACH_A_READER = (
    "that SALOON and the pool were previously separated",
    "that two readers disagreed on the CASE-2 east wall",
    "that two readers disagreed on the CASE-3 straight-wall length",
    "that CASE-5 produced 4.0 in one pass and 4.5 in the other",
    "that CASE-6 produced 1.30 m in one pass",
    "that readers previously found any particular contradiction",
    "that any particular dimension was previously read successfully",
)

# strings that must not appear anywhere a reader can see, on top of the
# baseline FORBIDDEN list. These are baseline RESULTS.
FEEDBACK_SCREEN = (
    "1.30", "130 parapet", "4.0 vs 4.5", "ESTABLISHED_WITH_CAVEAT",
    "previously", "pass 1", "PASS_1", "pass 2", "PASS_2",
    "a21_raw", "A21_reader", "the other reader", "last time",
    "east wall disagree", "SOURCE_SET_EXCEEDED", "DEV-01", "DEV-02",
    # run-sense only - see WHY_THE_BARE_WORD_BASELINE_IS_NOT_SCREENED
    "BASELINE_FREEZE", "A21_SOURCE_PRESENTATION_BASELINE",
    "baseline run", "baseline result", "baseline reader", "baseline pass",
)

WHY_THE_BARE_WORD_BASELINE_IS_NOT_SCREENED = (
    "the first screen was written with the bare token 'baseline' in it "
    "and it fired - on CASE-1's own task text, 'normal internal plaster, "
    "baseline gross wall face'. That is the QS sense of the word, it is "
    "byte-identical to the frozen baseline packet, and it therefore "
    "cannot be feedback from a run that had not happened when it was "
    "written. The right fix was to narrow the SCREEN to the run senses "
    "of the word, not to reword the task and introduce a second "
    "experimental variable to make a screen quiet")

# ==================================================================
# TWO SEALED READINGS PER CASE
# ==================================================================

READER_STRUCTURE = {
    "PASSES": 2,
    "READINGS_PER_CASE": 2,
    "READER_B_MUST_NOT_SEE_READER_A": True,
    "BYTE_IDENTICAL_TASK_INSTRUCTIONS_PER_CASE": True,
    "EACH_PASS_FROZEN_INDEPENDENTLY_BEFORE_THE_OTHER_IS_READ": True,
    "NO_AVERAGING": True,
    "NO_PLAUSIBILITY_SELECTION": True,
    "NO_MAJORITY": True,
}

EVIDENCE_INDEPENDENCE_STATUS = "PARTIALLY_SHARED"
INDEPENDENCE_COMPONENTS = ("SHARED_SOURCE", "SHARED_RULE", "SHARED_METHOD")
WHAT_AGREEMENT_SHOWS = (
    "repeatability of one visual method under fixed inputs. Not "
    "independent truth. An echo is not a witness")

# ==================================================================
# HOW THE COMPARISON IS SCORED - declared before any answer exists
# ==================================================================

COMPARISON_AXES = (
    "printed dimension extraction",
    "source citation quality",
    "room / boundary interpretation",
    "opening identification",
    "cross-sheet linkage",
    "height evidence interpretation",
    "number and type of unsupported assumptions",
    "number and type of SOURCE_REQUIRED fields",
    "reader-to-reader disagreement",
    "contradictions detected",
    "accidental inference beyond evidence",
    "refusal stability",
)

CLASSIFICATION_VOCABULARY = (
    "PRESENTATION_IMPROVED_EXTRACTION",
    "PRESENTATION_REDUCED_AMBIGUITY",
    "PRESENTATION_NO_EFFECT",
    "PRESENTATION_CHANGED_INTERPRETATION",
    "PRESENTATION_INTRODUCED_NEW_UNCERTAINTY",
    "SOURCE_PACKET_CORRECTION_EFFECT",
    "REFUSAL_STABLE",
    "UNRESOLVED",
)

EVERY_CLAIMED_IMPROVEMENT_MUST_NAME_ITS_CAUSE = (
    "for each field classified as improved, the comparison must identify "
    "the additional or clearer EVIDENCE that caused it. 'The reader said "
    "a better thing' is not a finding. 'The reader cited the printed 130 "
    "on a sheet it could now read' is")

MORE_QUANTITIES_IS_NOT_A_METRIC = True

# ==================================================================
# DEFERRED ON PURPOSE
# ==================================================================

FOLLOW_ON_DESIGN_ITEM = {
    "NAME": "A21_VISUAL_TRACE_SCHEMA",
    "THE_DEFECT": (
        "the A21 schema records LENGTH_M and SOURCE_LOCATION but no "
        "coordinate, so a segment id cannot be placed on the drawing and "
        "no overlay can be drawn without inventing positions"),
    "WHY_IT_IS_NOT_FIXED_IN_THIS_RUN": (
        "changing the schema now would add a second experimental "
        "variable to a run designed to isolate one"),
    "WHAT_IT_WILL_ADD_LATER": (
        "sheet id", "pixel anchor", "bounding box / polyline reference",
        "source-to-original transform"),
    "NO_OVERLAY_IS_FAKED_IN_THIS_RUN": True,
}

# ==================================================================
# AFTER
# ==================================================================

AFTER_THE_RUN = (
    "freeze both improved passes independently",
    "then build A21_SOURCE_PRESENTATION_COMPARISON - baseline vs improved",
    "no averaging, no winner",
    "return the comparison to the owner, then STOP",
)

STOP_AFTER = (
    "do not run A22", "do not open Excel", "do not expose E1.4",
    "do not introduce the sealed owner heights", "do not reconcile",
    "do not modify E1.4", "do not start E1.5 or E2",
    "do not generate a BOQ", "do not write to Firebase",
)


def protocol_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def assert_baseline_intact() -> None:
    """Nothing here runs if the frozen baseline moved."""
    bad = {k: v for k, v in B.verify().items()
           if v["PRESENT"] and not v["UNCHANGED"]}
    if bad:
        raise SystemExit(f"the frozen baseline has moved: {sorted(bad)}")
    d = B.verify_freeze_digest()
    if d["PRESENT"] and not d["MATCHES"]:
        raise SystemExit("the baseline freeze digest no longer reproduces")


assert_baseline_intact()


if __name__ == "__main__":
    import json
    print(json.dumps({
        "RUN_ID": RUN_ID,
        "PROTOCOL_HASH": protocol_hash(),
        "BASELINE_INTACT": True,
        "BASELINE_A21_FREEZE_SHA256": B.A21_FREEZE_SHA256,
        "THE_ONE_VARIABLE": "source presentation",
        "CASE_6_IS_REPORTED_AS": CASE_6_CLASSIFICATION,
        "DETAIL_CROP_METRES": DETAIL_CROP_METRES,
        "NO_SELECTIVE_DETAIL_CROP_FOR": list(NO_SELECTIVE_DETAIL_CROP_FOR),
    }, indent=2))
