"""The source-preparation decision, pre-registered by hash.

The decision document itself lives with the run data, which is gitignored
under the client-data policy. Its hash is recorded HERE, in tracked code,
committed before any A21 reader output was inspected - so the claim "this
was decided before we saw the results" is checkable rather than asserted.

    python3 -m research.a21_visual_qs_pilot_01.source_preparation
"""

from __future__ import annotations

import hashlib
from pathlib import Path

DOC = Path("data/experiments/A21_VISUAL_QS_PILOT_01/"
           "SOURCE_PREPARATION_DECISION.md")

DECISION_SHA256 = (
    "31ade8b0cab3c835e0fecdc881698799379d39df2cbdfa500db604ed45ebc2af")

# ------------------------------------------------------------------
# measured from the actual PDF, not assumed
# ------------------------------------------------------------------
SOURCE_FACTS = {
    "pages": 10,
    "page_size_pt": (842, 1192),
    "page_size_mm": (297, 421),
    "embedded_image_px": (4672, 6624),
    "images_per_page": 1,
    "vector_paths_per_page": 0,
    "extractable_characters": 0,
    "NATIVE_DPI": 399.5,
    "WHAT_THIS_MEANS": (
        "the PDF is a 400 DPI scan in a wrapper. There is no vector "
        "geometry and no text to extract, so nothing is gained by feeding "
        "the native PDF, and NOTHING IS GAINED BY RENDERING ABOVE NATIVE"),
}

RUNTIME_FACTS = {
    "DISPLAY_LONG_EDGE_CAP_PX": 2000,
    "HOW_IT_WAS_MEASURED": (
        "the harness reported rendering a 2600x1404 image at 2000x1080"),
    "PX_PER_METRE_AT_1_TO_100_AND_400_DPI": 157,
    "DIGIT_PX_NATIVE_2_5MM": 39.3,
    "DIGIT_PX_IN_A_FULL_SHEET": 12,
    "DIGIT_PX_IN_A_2840_CROP": 27,
}

# ------------------------------------------------------------------
# the read tests, run on the same model family that reads the drawings
# ------------------------------------------------------------------
READ_TESTS = (
    ("FULL_PAGE_AT_1058x1500",
     "most dimensions readable; the small ones (20, 40, 45, 52, 77) at the "
     "edge of reliability"),
    ("NATIVE_CROP_1500x1500",
     "every dimension crisp; room names legible in English and Arabic"),
    ("SAME_CROP_ROTATED_MINUS_90",
     "WORSE THAN NOT ROTATING AT ALL - everything inverted"),
    ("SAME_CROP_ROTATED_PLUS_90_CCW",
     "clearly best; every label and dimension reads naturally"),
)

# ------------------------------------------------------------------
# the decision
# ------------------------------------------------------------------
PACKET_LEVELS = (
    ("LEVEL_1_CONTEXT", "full upright sheet - orientation, sheet identity, "
                        "section markers, adjacent rooms, north"),
    ("LEVEL_2_DETAIL", "upright crop, about 12 m across, at most 2000 px, "
                       "so the runtime passes it through untouched"),
    ("LEVEL_3_CROSS_SHEET", "section and/or elevation, upright, only where "
                            "the measurement needs it"),
)

REFINEMENTS = (
    "cap every render at NATIVE resolution - 399.5 DPI is the ceiling and "
    "anything above it is invented detail",
    "size crops in METRES of building, not pixels: ~12 m, which lands just "
    "under the 2000 px lossless ceiling at 157 px per metre",
    "rotation must be DETERMINED AND VERIFIED per sheet, never assumed - a "
    "wrong rotation measured worse than no rotation",
)

NO_FOURTH_LEVEL = (
    "three levels is enough for this drawing set. Each extra image costs "
    "attention better spent on the drawing")

MONTAGE_RULE = (
    "a montage is a navigation aid, never a measurement source. It must "
    "not reduce the resolution of the thing being measured")

# ------------------------------------------------------------------
# the honest verdict on the run already in flight
# ------------------------------------------------------------------
BASELINE_VERDICT = {
    "RUN_ID": "A21_SOURCE_PRESENTATION_BASELINE",
    "MATERIALLY_INFERIOR_ON": (
        "ORIENTATION - the sheets are not rotated, so every reader must "
        "mentally undo 90 degrees on every label and every dimension"),
    "MILDLY_SUBOPTIMAL_ON": (
        "crop resolution - 2840 px is downscaled about 0.70 by the "
        "runtime, leaving digits near 27 px, which is still workable"),
    "ALREADY_CORRECT": (
        "three-level context, sheet identity in the filename, and both "
        "sections supplied for the height cases"),
    "IT_IS_A_BASELINE_NOT_A_WASTED_RUN": True,
    "ITS_RESULTS_ARE_KEPT_WHOLE": True,
}

PROPOSED_SECOND_RUN = {
    "RUN_ID": "A21_SOURCE_PRESENTATION_IMPROVED",
    "CHANGES_ONLY": "the source presentation",
    "UNCHANGED": (
        "the six cases", "the QS rules", "the blindness rules",
        "the withheld heights", "the door and window default policy",
        "the A21 schema", "no Excel", "no E1.4 exposure"),
    "WHY_IT_IS_NOT_BENCHMARK_TUNING": (
        "this decision is hashed and committed before any reader result "
        "was inspected, so the justification cannot have been shaped by "
        "the quantities produced"),
}

INDEPENDENCE_LIMITATION = (
    "a difference between the two runs is evidence about SOURCE "
    "PRESENTATION. It is not evidence that either reading is correct. The "
    "classification stands: SHARED_SOURCE, SHARED_RULE, SHARED_METHOD")


def verify() -> dict:
    """Does the decision document still hash to what was pre-registered?"""
    if not DOC.exists():
        return {"DOCUMENT_PRESENT": False,
                "EXPECTED_SHA256": DECISION_SHA256}
    got = hashlib.sha256(DOC.read_bytes()).hexdigest()
    return {"DOCUMENT_PRESENT": True,
            "EXPECTED_SHA256": DECISION_SHA256,
            "ACTUAL_SHA256": got,
            "UNCHANGED_SINCE_PRE_REGISTRATION": got == DECISION_SHA256}


if __name__ == "__main__":
    import json
    print(json.dumps({"verify": verify(),
                      "NATIVE_DPI": SOURCE_FACTS["NATIVE_DPI"],
                      "RUNTIME_CAP_PX": RUNTIME_FACTS[
                          "DISPLAY_LONG_EDGE_CAP_PX"],
                      "BASELINE_MATERIALLY_INFERIOR_ON":
                          BASELINE_VERDICT["MATERIALLY_INFERIOR_ON"]},
                     indent=2))
