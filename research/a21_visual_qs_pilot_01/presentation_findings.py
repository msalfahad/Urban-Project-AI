"""The classified findings of the presentation experiment.

Every claimed improvement names the evidence that caused it. Where the
cause is NOT the presentation - and in two of the six cases it is not -
that is said plainly and the case is excluded from the presentation
verdict rather than counted toward it.

    python3 -m research.a21_visual_qs_pilot_01.presentation_findings
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_visual_qs_pilot_01 import improved_protocol as IP

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")

# ==================================================================
# DEV-03 - found by auditing the improved run, present in the baseline
# ==================================================================

DEV_03 = {
    "DEVIATION_ID": "DEV-03",
    "READERS": "all four CASE-5 readings - both baseline passes and both "
               "improved passes",
    "WHAT_HAPPENED": (
        "CASE-5-EXTERNAL-FACADE was declared with three sources - the SE "
        "elevation, the ground floor plan and Section A-A. Every reading "
        "of it cites SECTION_B_B, which the case does not list. Counted "
        "references: baseline 5 and 1, improved 4 and 13"),
    "HOW_IT_CAME_TO_LIGHT": (
        "NOT self-reported this time. I found it by checking each "
        "improved reading's citations against its own declared source "
        "list, after noticing that the improved pass-2 plaster height "
        "cited a sheet I had not put in that packet"),
    "IT_WAS_IN_THE_BASELINE_TOO": (
        "and I did not catch it when I froze the baseline. I checked the "
        "CASE-6 deviation because two readers disclosed it, and did not "
        "run the same check across the other five cases. That is a gap "
        "in my own audit, not in the readers"),
    "IS_IT_A_BENCHMARK_LEAK": False,
    "WHY_NOT": (
        "SECTION_B_B is a permitted drawing sheet carrying no result, no "
        "benchmark quantity and no sealed height. It sits in the CASE-4 "
        "and CASE-6 directories of the same sandbox"),
    "WHAT_IT_DOES_AFFECT": (
        "the CASE-5 comparison, fundamentally. The single established "
        "APPLICABLE_PLASTER_HEIGHT in the whole experiment - 5.35 m in "
        "improved pass 2 - is read off the printed '535' on SECTION_B_B, "
        "a sheet that is not in CASE-5's packet. That result therefore "
        "cannot be attributed to source presentation"),
    "THE_DESIGN_DEFECT_IS_MINE_AGAIN": (
        "this is the same shape as DEV-02. Four readers across two runs "
        "independently needed a sheet CASE-5 did not declare, because "
        "the external face height of this facade is dimensioned on "
        "Section B-B and nowhere else in the packet. A case packet that "
        "cannot answer its own question is a design defect, and this is "
        "the second one of those I have shipped"),
    "CONSEQUENCE_FOR_THE_RECORD": (
        "all four CASE-5 readings are marked SOURCE_SET_EXCEEDED_AS_"
        "DECLARED. None is discarded and none is corrected. CASE-5 is "
        "reclassified so it is not read as one-variable presentation "
        "evidence"),
    "FIX_FOR_ANY_LATER_RUN": (
        "add SECTION_B_B to CASE-5's declared sources, exactly as CASE-6 "
        "received it - and, before any future run, check EVERY case's "
        "citations against its own manifest instead of only the ones a "
        "reader volunteers"),
    "DEV_01_AND_DEV_02_REMAIN_AS_WRITTEN": True,
}

CASE_5_RECLASSIFIED = "SOURCE_PRESENTATION_PLUS_UNDECLARED_SOURCE"

CLEAN_ONE_VARIABLE_CASES = ("CASE-1-NORMAL-PLASTER", "CASE-2-TILE-PREP",
                            "CASE-3-DOOR-AND-WINDOW", "CASE-4-STAIR")
NOT_ONE_VARIABLE = {
    "CASE-5-EXTERNAL-FACADE": CASE_5_RECLASSIFIED,
    "CASE-6-ROOF-PARAPET": IP.CASE_6_CLASSIFICATION,
}

# ==================================================================
# THE CLASSIFIED FIELDS
# ==================================================================

FINDINGS = (
    {
        "FIELD": "source citation quality (citations naming a sheet)",
        "SCOPE": "all six cases, both passes",
        "BASELINE": "5,11 / 5,8 / 8,10 / 9,12 / 8,7 / 4,8",
        "IMPROVED": "8,10 / 8,10 / 8,11 / 11,14 / 14,12 / 9,12",
        "CLASSIFICATION": "PRESENTATION_IMPROVED_EXTRACTION",
        "THE_EVIDENCE_THAT_CAUSED_IT": (
            "the improved reading names the sheet AND the dimension it "
            "read there far more often. The clearest examples are CASE-6 "
            "(4 -> 9 in pass 1) and CASE-5 (8 -> 14 in pass 1), which are "
            "exactly the two cases whose sheets gained the most usable "
            "resolution: the SE elevation at 1.47x and Section A-A at "
            "1.40x after rotation, content trim and a single LANCZOS "
            "reduction instead of two"),
        "CONFIDENCE": "the strongest signal in the run - it moves in the "
                      "same direction on all six cases",
    },
    {
        "FIELD": "printed dimension extraction",
        "SCOPE": "cases 4-6 versus cases 1-3",
        "BASELINE": "C4 10,12  C5 8,7  C6 7,7   |   C1 2,2  C2 5,7  C3 6,5",
        "IMPROVED": "C4 8,12  C5 12,10  C6 10,12  |  C1 3,1  C2 6,5  C3 8,2",
        "CLASSIFICATION": "PRESENTATION_IMPROVED_EXTRACTION",
        "THE_EVIDENCE_THAT_CAUSED_IT": (
            "printed-dimension citations rise on CASE-5 and CASE-6, whose "
            "SHEETS gained 1.40-1.47x, and do not rise on cases 1-3, "
            "whose sheets gained only 1.08x and which instead gained a "
            "native detail crop. The gain tracks the sheets that got "
            "sharper, which is what a presentation effect should look "
            "like"),
        "CONFIDENCE": (
            "SUGGESTIVE, NOT PROVEN. Six cases, two passes, no control "
            "for case difficulty, and the counts vary as much between "
            "the two passes of one run as between runs. I am reporting a "
            "pattern, not a measured effect size"),
    },
    {
        "FIELD": "CASE-5 STOREY_HEIGHT_VALUE",
        "BASELINE": "4.0 (pass 1) vs 4.5 (pass 2) - the frozen "
                    "HEIGHT_DIFFERENCE",
        "IMPROVED": "4.5 and 4.5",
        "CLASSIFICATION": "PRESENTATION_REDUCED_AMBIGUITY",
        "THE_EVIDENCE_THAT_CAUSED_IT": (
            "the baseline divergence was about WHICH BLOCK fronts the "
            "street: pass 1 took the dewaneya's printed 400, pass 2 took "
            "the main house's printed 450. Both improved readings take "
            "450 AND separate the dewaneya explicitly - improved pass 1 "
            "writes 'This is the MAIN HOUSE ground storey. The DEWANEYA "
            "part of this same facade is a different storey: 400 clear, "
            "480 overall (both printed)'. The ambiguity was not resolved "
            "by picking a side; it was dissolved by seeing that the "
            "facade has two blocks with two printed heights"),
        "CONFIDENCE": "good - the improved readings state the distinction "
                      "the baseline readings were silently split over",
    },
    {
        "FIELD": "CASE-5 APPLICABLE_PLASTER_HEIGHT",
        "BASELINE": "PLASTER_HEIGHT_NOT_ESTABLISHED, both passes",
        "IMPROVED": "NOT_ESTABLISHED (pass 1) / ESTABLISHED 5.35 m (pass 2)",
        "CLASSIFICATION": "UNRESOLVED",
        "WHY_NOT_AN_IMPROVEMENT": (
            "the 5.35 m is read off the printed '535' on SECTION_B_B - a "
            "sheet CASE-5 does not declare. See DEV-03. A number that "
            "arrives by reading an undeclared sheet is not evidence that "
            "better presentation established a height. It is also the "
            "ONLY established plaster height in twenty-four case "
            "readings, and it disagrees with its own pass-1 partner"),
        "IT_IS_NOT_DISCARDED": (
            "it is a well-argued reading - it distinguishes the external "
            "face height from the storey height, which is exactly the "
            "distinction Decision 1 exists to protect - and its own "
            "SCOPE_CHECK admits it extends one wall face by inference. "
            "It stands, labelled, unadopted"),
    },
    {
        "FIELD": "CASE-6 APPLICABLE_PLASTER_HEIGHT / parapet",
        "BASELINE": "NOT_ESTABLISHED (pass 1) / ESTABLISHED_WITH_CAVEAT "
                    "1.30 m (pass 2) - the frozen REFUSAL_STATUS_DIFFERENCE",
        "IMPROVED": "NOT_ESTABLISHED for the main roof in BOTH passes; "
                    "ESTABLISHED 0.50 m for the penthouse roof",
        "CLASSIFICATION": "SOURCE_PACKET_CORRECTION_EFFECT",
        "THE_EVIDENCE_THAT_CAUSED_IT": (
            "the improved readings split one parapet into two and say why "
            "the 130 must not be used: improved pass 2 reads the element "
            "the '130' measures to as a METAL BALUSTRADE with a top rail, "
            "dimensioned '104' on the elevation over an undimensioned "
            "upstand, with the rest of that edge a solid ogee curve whose "
            "only dimensioned point is its high point. It then states "
            "that measuring the run from the section alone would overstate "
            "the parapet face by about 40 per cent"),
        "WHY_THIS_IS_THE_MOST_IMPORTANT_RESULT": (
            "the baseline's pass-2 1.30 m was the kind of answer that "
            "looks like progress. The improved run, with the sheet it "
            "actually needed legitimately in its packet, did not produce "
            "MORE numbers there - it produced a BETTER REFUSAL, and named "
            "the physical reason. A metal balustrade has no plasterable "
            "face. That is the experiment working"),
        "COMPARABILITY": (
            "CASE-6 carries both the packet correction and the "
            "presentation change and is NOT one-variable evidence"),
    },
    {
        "FIELD": "refusal stability (APPLICABLE_PLASTER_HEIGHT)",
        "BASELINE": "11 of 12 readings refused; 1 established with caveat",
        "IMPROVED": "11 of 12 readings refused; 1 established (CASE-5, "
                    "off an undeclared sheet)",
        "CLASSIFICATION": "REFUSAL_STABLE",
        "THE_EVIDENCE": (
            "every one of the twelve improved readings reads the printed "
            "storey height correctly - 4.50, 4.20 - and eleven of them "
            "still decline to convert it into a treatment height, giving "
            "the same reason as the baseline: no slab thickness, no beam "
            "depth, no ceiling line and no finish rule is printed "
            "anywhere. Making the drawing easier to read did not make the "
            "missing information appear"),
        "THIS_IS_THE_EXPECTED_AND_ACCEPTABLE_OUTCOME": True,
        "DECISION_1_HELD": (
            "no reading derived a height by subtracting an assumed slab "
            "and beam, and 3.20 m appears nowhere in any of the twelve"),
    },
    {
        "FIELD": "contradictions detected",
        "BASELINE": "cases 4-6 only: 4,3 / 4,4 / 4,6 = 25 across four "
                    "readings; cases 1-3 declared none (no such field in "
                    "their schema)",
        "IMPROVED": "5,3 / 5,3 / 5,4 = 25 across four readings",
        "CLASSIFICATION": "PRESENTATION_NO_EFFECT",
        "THE_EVIDENCE": (
            "the totals are identical and the headline contradictions are "
            "the same ones: the SE elevation is drawn as a section, three "
            "external ground datums on one facade, the plan/elevation "
            "chain mismatch (451 vs 470-480), the sheet titled 2nd FLOOR "
            "PLAN, and the solid-parapet-versus-open-balustrade conflict. "
            "Better presentation did not find more contradictions. It did "
            "let the improved readings quantify two of them - the 40 per "
            "cent parapet overstatement and the 19 cm chain gap with both "
            "alternative answers shown"),
    },
    {
        "FIELD": "room / boundary interpretation on the open-plan zones",
        "BASELINE": "CASE-1 and CASE-3 perimeters NOT_ESTABLISHED; the two "
                    "passes disagreed on segment counts and lengths",
        "IMPROVED": "same conclusion, reached faster and stated harder - "
                    "improved pass 2 gives the whole open space as 15.97 x "
                    "8.95 m, both printed, and says RECEPTION and SALOON "
                    "are zones of it rather than rooms",
        "CLASSIFICATION": "PRESENTATION_NO_EFFECT",
        "THE_EVIDENCE": (
            "no wall is drawn between DINING, RECEPTION and SALOON. That "
            "is a property of the building, not of the image. A sharper "
            "picture of an absent wall is still an absent wall"),
    },
    {
        "FIELD": "unsupported assumptions and scaled measurements",
        "BASELINE": "assumption citations 1,3 / 5,3 / 4,4 / 5,5 / 6,8 / 0,1",
        "IMPROVED": "7,3 / 4,5 / 4,1 / 7,1 / 8,0 / 0,0",
        "CLASSIFICATION": "PRESENTATION_INTRODUCED_NEW_UNCERTAINTY",
        "THE_EVIDENCE": (
            "the counts do not fall. On CASE-1 improved pass 1 they rise "
            "from 1 to 7. Reading the drawing more easily appears to "
            "invite MORE interpretation of what is drawn, not less - the "
            "improved CASE-1 reading offers more opinions about the lift "
            "shaft, the under-stair wall and the dashed X than the "
            "baseline did. Sharper images did not make the readers more "
            "cautious"),
        "HONEST_CAVEAT": (
            "these are counts of self-declared labels. A reader who "
            "labels more of its own reasoning VISUAL_INTERPRETATION looks "
            "worse on this axis while behaving better. The axis cannot "
            "separate the two, and I am not going to pretend it can"),
    },
)

# ==================================================================
# THE VERDICT
# ==================================================================

VERDICT = {
    "DID_PRESENTATION_HELP": (
        "yes, narrowly and specifically: readers cite their sources far "
        "better, and on the two cases whose sheets gained the most "
        "resolution they cite more printed dimensions. One frozen "
        "baseline divergence - the CASE-5 4.0 vs 4.5 - is dissolved, and "
        "the improved readings explain why it happened"),
    "DID_IT_PRODUCE_MORE_QUANTITIES": (
        "no, and that was never the test. Eleven of twelve improved "
        "readings still return PLASTER_HEIGHT_NOT_ESTABLISHED, for the "
        "same reason as before"),
    "THE_ONE_NEW_ESTABLISHED_HEIGHT_DOES_NOT_COUNT": (
        "CASE-5's 5.35 m rests on an undeclared sheet - DEV-03 - and is "
        "not attributable to presentation"),
    "THE_BEST_RESULT_IS_A_REFUSAL": (
        "CASE-6. With Section B-B legitimately in its packet the improved "
        "readings did not repeat the baseline's 1.30 m; they identified "
        "that the 130 measures to a metal balustrade and refused the "
        "parapet face while establishing the penthouse parapet at the "
        "printed 0.50 m. A more discriminating refusal is worth more than "
        "a new number"),
    "WHAT_PRESENTATION_CANNOT_FIX": (
        "everything this drawing does not contain. No slab thickness, no "
        "beam depth, no ceiling line, no door or window schedule, no "
        "finishes specification, and no wall between the open-plan zones. "
        "The binding constraint on A21 is the source document, not the "
        "rendering of it"),
    "WOULD_A_THIRD_PRESENTATION_RUN_HELP": (
        "no. The remaining gains are in the SOURCE SET - the two packet "
        "defects DEV-02 and DEV-03 - and in the schema, not in pixels"),
}

LIMITATIONS = (
    "six cases, two passes, one drawing set, one model family",
    "SHARED_SOURCE, SHARED_RULE, SHARED_METHOD - agreement between "
    "passes shows repeatability, never correctness",
    "no reading in either run has been checked against physical truth, "
    "because nothing in this experiment can do that",
    "the count axes measure what a reading SAYS about its own sources",
    "two of six cases are not one-variable comparisons (CASE-5, CASE-6)",
    "the improved run's own audit found a defect the baseline freeze "
    "missed, so the baseline's clean record was partly my not looking",
)


def build() -> dict:
    body = {
        "EXPERIMENT_ID": IP.EXPERIMENT_ID,
        "ARTIFACT": "A21_SOURCE_PRESENTATION_FINDINGS",
        "BASELINE_RUN_ID": IP.BASELINE_RUN_ID,
        "IMPROVED_RUN_ID": IP.RUN_ID,
        "NO_AVERAGING_NO_WINNER_NO_SELECTION": True,
        "MORE_QUANTITIES_IS_NOT_A_METRIC": True,
        "DEVIATIONS": [DEV_03],
        "CLEAN_ONE_VARIABLE_CASES": list(CLEAN_ONE_VARIABLE_CASES),
        "NOT_ONE_VARIABLE": NOT_ONE_VARIABLE,
        "FINDINGS": list(FINDINGS),
        "VERDICT": VERDICT,
        "LIMITATIONS": list(LIMITATIONS),
        "FOLLOW_ON_DESIGN_ITEM": IP.FOLLOW_ON_DESIGN_ITEM,
        "A22_WAS_NOT_RUN": True,
        "EXCEL_WAS_NOT_OPENED": True,
        "E1_4_WAS_NOT_EXPOSED": True,
        "SEALED_OWNER_HEIGHTS_NEVER_INTRODUCED": True,
    }
    out = RUN_DIR / "A21_SOURCE_PRESENTATION_FINDINGS.json"
    out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return {"FILE": out.name,
            "SHA256": hashlib.sha256(out.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
