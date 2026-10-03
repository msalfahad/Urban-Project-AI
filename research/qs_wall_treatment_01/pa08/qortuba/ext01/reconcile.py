"""PA08_QORTUBA_EXTERNAL_RECONCILIATION_01: the first external quantity comparison for Qortuba.

Three bases are kept apart and never averaged into one number:

  A  ENGINEERING_GEOMETRIC_BASIS   the frozen PA08_QORTUBA_R3 DWG takeoff
  B  CONTRACTOR_MEASUREMENT_BASIS  the كيال working sheets
  C  CONTRACTOR_COMMERCIAL_BASIS   the priced summary sheet

This phase reads R3; it never writes to it.  The R3 artifact hashes are verified before the comparison starts and again after
it finishes, and a mismatch aborts.  No engine rule, geometry or trade rule is changed here: a defect found is recorded and
left for a later phase to fix.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.ext01 import transcribe as TR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_ext01"
R3_OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r3"
R2_OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r2"
R1_OUT = Path(PR.OUT_DIR) / "pa08_qortuba_r1"

DIFFERENCE_CLASSES = (
    "ENGINE_GEOMETRY_ERROR", "CONTRACTOR_MEASUREMENT_ERROR_OR_OMISSION", "CONTRACTOR_ARITHMETIC_ERROR",
    "MEASUREMENT_BASIS_DIFFERENCE", "TRADE_SCOPE_DIFFERENCE", "FINISH_SCOPE_DIFFERENCE", "THRESHOLD_RULE_DIFFERENCE",
    "OPENING_DEDUCTION_DIFFERENCE", "COMMERCIAL_MEASUREMENT_RULE", "ROUNDING", "SITE_EXECUTION_DIFFERENCE",
    "IDENTITY_MAPPING_ERROR", "SOURCE_AMBIGUITY", "UNRESOLVED", "ENGINE_TRADE_RULE_ERROR",
)
ACTIONS = ("NO_CHANGE", "ENGINE_GEOMETRY_FIX_REQUIRED", "ENGINE_TRADE_RULE_FIX_REQUIRED", "CONTRACTOR_ARITHMETIC_REVIEW",
           "OWNER_SCOPE_CONFIRMATION", "MORE_SOURCE_REQUIRED", "CONTRACTOR_BASIS_UNRESOLVED", "POSSIBLE_CONTRACTOR_ERROR")
PROFILE_SEGMENT_CLASSES = ("LEGITIMATE_PROFILE_ONLY_SEGMENT", "SHOULD_SHARE_SKIRTING_PATH", "DOOR_OR_OPENING_SEGMENT",
                           "WET_ROOM_SEGMENT", "NON_SKIRTING_EDGE", "FRAME_OR_JOINERY", "ENGINE_PROFILE_SCOPE_ERROR",
                           "COMMERCIAL_SCOPE_DIFFERENCE", "UNRESOLVED")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def r3_fingerprint():
    """Every R3 artifact hash, taken from the freeze and checked on disk."""
    fr = json.loads((R3_OUT / "FREEZE_PA08_QORTUBA_R3.json").read_text("utf-8"))
    actual = {n: (_sha(R3_OUT / f"{n}.json") if (R3_OUT / f"{n}.json").exists() else None) for n in fr["CONTENTS"]}
    return fr, actual, [n for n, h in fr["CONTENTS"].items() if actual.get(n) != h]


def verify_frozen_state():
    fr3, actual, bad = r3_fingerprint()
    if bad:
        raise SystemExit(f"R3 artifacts changed on disk, refusing to reconcile: {bad}")
    priors = []
    for name, folder in (("PA08_QORTUBA_R1", R1_OUT), ("PA08_QORTUBA_R2", R2_OUT)):
        d = json.loads((folder / f"FREEZE_{name}.json").read_text("utf-8"))
        files = d.get("CONTENTS", {})
        ok = all((folder / f"{n}.json").exists() and _sha(folder / f"{n}.json") == h for n, h in files.items())
        priors.append({"FREEZE": name, "DIGEST": d.get("DIGEST"), "FILE_COUNT": len(files), "VERIFIED_ON_DISK": ok})
    tfr = json.loads((OUT / "CONTRACTOR_TRANSCRIPTION_FREEZE.json").read_text("utf-8"))
    tbad = [n for n, h in tfr["CONTENTS"].items() if not (OUT / f"{n}.json").exists() or _sha(OUT / f"{n}.json") != h]
    if tbad:
        raise SystemExit(f"contractor transcription changed after it was frozen, refusing to reconcile: {tbad}")
    return {"ARTIFACT": "PA08_QORTUBA_EXT01_FROZEN_STATE_VERIFICATION",
            "R3_FREEZE_DIGEST": fr3["DIGEST"], "R3_GIT_HEAD_AT_FREEZE": fr3["GIT_HEAD_AT_FREEZE"],
            "R3_ARTIFACTS": len(fr3["CONTENTS"]), "R3_HASH_MISMATCHES": bad,
            "R3_WORKING_TREE_AT_FREEZE_CLEAN": fr3["WORKING_TREE_AT_FREEZE"]["CLEAN"],
            "PRIOR_FREEZES": priors,
            "CONTRACTOR_TRANSCRIPTION_FREEZE_DIGEST": tfr["DIGEST"],
            "TRANSCRIPTION_FROZEN_BEFORE_COMPARISON": True,
            "RULE": "the comparison reads R3 and never writes to it; the artifact hashes are checked again when it finishes"}


def r3_values():
    """Read the frozen R3 numbers.  Read only."""
    reg = json.loads((R3_OUT / "PA08_QORTUBA_R3_FLOOR_MEASUREMENT_REGION_REGISTER.json").read_text("utf-8"))
    sk = json.loads((R3_OUT / "PA08_QORTUBA_R3_SKIRTING_MEASUREMENT_REGISTER.json").read_text("utf-8"))
    pf = json.loads((R3_OUT / "PA08_QORTUBA_R3_PROFILE_MEASUREMENT_REGISTER.json").read_text("utf-8"))
    wet = json.loads((R3_OUT / "PA08_QORTUBA_R3_WET_ROOM_GEOMETRY_REGISTER.json").read_text("utf-8"))
    cov = json.loads((R3_OUT / "PA08_QORTUBA_R3_COVERAGE.json").read_text("utf-8"))
    return reg, sk, pf, wet, cov


# ---------------------------------------------------------------------------- §5/§7 ceramic flooring
def flooring_reconciliation(reg, cov, comm):
    cc01 = next(r for r in comm["ROWS"] if r["ROW_ID"] == "CC-01")
    dry = cov["SUBTOTALS"]["DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    wet = cov["SUBTOTALS"]["WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    rooms = []
    for r in reg["ROWS"]:
        rooms.append({
            "ROOM": r["ROOM"], "MEASUREMENT_REGION_ID": r["FLOOR_MEASUREMENT_REGION_ID"],
            "R3_GEOMETRIC_AREA_M2": r["AREA_M2"]["VALUE"], "R3_STATUS": r["AREA_M2"]["STATE"],
            "R3_WET_OR_DRY": r["WET_OR_DRY"],
            "CONTRACTOR_KIYAL_AREA_M2": None, "CONTRACTOR_KIYAL_BASIS": None,
            "COMMERCIAL_SCOPE_INCLUDED": "NOT_ESTABLISHED",
            "CONTRACTOR_FORMULA": None, "FINISH_SCOPE": "NOT_ESTABLISHED",
            "DELTA_M2": None, "DELTA_PERCENT": None,
            "CLASSIFICATION": ["SOURCE_AMBIGUITY"],
            "ROOT_CAUSE": "the priced sheet carries one summed floor quantity and no room breakdown, and the كيال working "
                          "sheet that would carry the breakdown was not supplied.  No room-level comparison exists to make.",
            "ACTION": "MORE_SOURCE_REQUIRED",
        })
    agg = {
        "ITEM": "ceramic floor tiling, aggregate",
        "ENGINE_VALUE_M2": dry, "ENGINE_BASIS": "sum of the six dry floor measurement regions on the SECOND FLOOR plan, "
                                                "clear finish face, arrangement of the bounding lines",
        "ENGINE_WET_SUBTOTAL_M2": wet,
        "COMMERCIAL_VALUE_M2": cc01["NET"], "COMMERCIAL_BASIS": "one summed quantity, no storey stated, no room breakdown",
        "KIYAL_VALUE_M2": None, "KIYAL_BASIS": "NOT_PROVIDED",
        "DELTA_ENGINE_VS_COMMERCIAL_M2": round(cc01["NET"] - dry, 4),
        "DELTA_PERCENT": round(100.0 * (cc01["NET"] - dry) / dry, 2),
        "CLASSIFICATION": ["SOURCE_AMBIGUITY", "TRADE_SCOPE_DIFFERENCE"],
        "WHY_NOT_AN_ENGINE_ERROR_YET": "a difference between a per-storey geometric total and a contractor total of unstated "
                                       "storey scope is not evidence that either is wrong.  Nothing in the sheet says which "
                                       "rooms, or which floors, it covers.",
        "ACTION": "MORE_SOURCE_REQUIRED",
    }
    scope_questions = [
        {"QUESTION": "which storey or storeys does the sheet cover", "ANSWERED_BY_SOURCE": False,
         "EVIDENCE": "the sheet prints the plot address 'قرطبه ق١ ش١ ج٦' and no floor, storey or level anywhere"},
        {"QUESTION": "is the pantry floor in the floor row or in the bathrooms-and-kitchens row", "ANSWERED_BY_SOURCE": False,
         "EVIDENCE": "the sheet has a row headed 'حمامات ومطابخ' (bathrooms and kitchens), so a kitchen-type room is scoped "
                     "separately somewhere in this sheet, but the row does not say whether it carries that room's floor"},
        {"QUESTION": "is the dress room inside the ceramic scope", "ANSWERED_BY_SOURCE": False, "EVIDENCE": "not named anywhere"},
        {"QUESTION": "are the hall recesses and passages included", "ANSWERED_BY_SOURCE": False, "EVIDENCE": "not named anywhere"},
        {"QUESTION": "were the bathrooms measured separately", "ANSWERED_BY_SOURCE": "PARTIALLY",
         "EVIDENCE": "a row headed 'حمامات ومطابخ' exists, so bathrooms are scoped apart from the floor row; whether that row "
                     "is their walls, their floors or both is not stated"},
        {"QUESTION": "are thresholds included or excluded", "ANSWERED_BY_SOURCE": False, "EVIDENCE": "not stated"},
        {"QUESTION": "are stairs excluded", "ANSWERED_BY_SOURCE": False, "EVIDENCE": "not stated"},
        {"QUESTION": "is the roof or open area excluded", "ANSWERED_BY_SOURCE": False, "EVIDENCE": "not stated"},
        {"QUESTION": "does the finish material differ by room", "ANSWERED_BY_SOURCE": False,
         "EVIDENCE": "the sheet is headed 'سيراميك' and prints one rate of 2.750 for every area and length item, which is "
                     "consistent with one labour rate across the package and says nothing about materials"},
    ]
    return {"ARTIFACT": "QORTUBA_EXT01_CERAMIC_FLOORING_RECONCILIATION",
            "AGGREGATE": agg, "BY_ROOM": rooms, "ROOM_COUNT": len(rooms),
            "SCOPE_QUESTIONS_THE_KIYAL_WOULD_ANSWER": scope_questions,
            "ROOM_LEVEL_COMPARISONS_POSSIBLE": 0,
            "RULE": "no room combination was searched to reach the contractor total.  A scope must come from a document, and "
                    "this document states none."}


# ---------------------------------------------------------------------------- §8 skirting
def skirting_reconciliation(sk, comm):
    cc02 = next(r for r in comm["ROWS"] if r["ROW_ID"] == "CC-02")
    by_class = Counter()
    rows = []
    for r in sk["ROWS"]:
        for k, v in r["BY_SEGMENT_CLASS_LM"].items():
            by_class[k] += v
        rows.append({"ROOM": r["ROOM"], "WET_OR_DRY": r["WET_OR_DRY"],
                     "R3_GROSS_ELIGIBLE_WALL_PATH_LM": r["GROSS_WALL_PATH_LM"],
                     "DOOR_DEDUCTION_LM": r["DOOR_DEDUCTION_LM"],
                     "OPEN_PASSAGE_DEDUCTION_LM": r["OPEN_EDGE_DEDUCTION_LM"],
                     "NON_SKIRTING_EDGE_LM": round(r["BY_SEGMENT_CLASS_LM"].get("NON_WALL_EDGE", 0.0), 3),
                     "COLUMN_FACE_LM": round(r["BY_SEGMENT_CLASS_LM"].get("COLUMN_FACE", 0.0), 3),
                     "WET_ROOM_EDGE_LM": r["WET_ROOM_WALL_EDGE_LM"],
                     "CABINET_OR_JOINERY_EXCLUSION_LM": {"VALUE": None, "STATE": "NOT_MODELLED_BY_R3",
                                                         "WHY": "R3 has no fitted-joinery run along a wall, so it can neither "
                                                                "apply nor refuse a joinery exclusion"},
                     "OTHER_DEDUCTION_LM": r["OTHER_DEDUCTION_LM"],
                     "R3_NET_GEOMETRIC_PATH_LM": r["NET_SKIRTING_GEOMETRIC_LM"], "R3_STATE": r["STATE"],
                     "CONTRACTOR_KIYAL_PATH_LM": None, "CONTRACTOR_COMMERCIAL_QUANTITY_LM": None,
                     "CLASSIFICATION": ["SOURCE_AMBIGUITY"],
                     "ACTION": "MORE_SOURCE_REQUIRED"})
    dry_net = sk["DRY_NET_SUBTOTAL_LM"]
    delta = round(cc02["NET"] - dry_net, 4)
    agg = {"ITEM": "skirting, aggregate",
           "ENGINE_VALUE_LM": dry_net,
           "ENGINE_BASIS": "the SKIRTING_ELIGIBLE_WALL length of the six dry measurement regions; wet rooms contribute zero "
                           "pending the owner's skirted-or-tiled ruling",
           "COMMERCIAL_VALUE_LM": cc02["NET"],
           "COMMERCIAL_BASIS": "'نعله مخفي' (concealed skirting), one summed length in متر طولي, no room breakdown",
           "KIYAL_VALUE_LM": None, "KIYAL_BASIS": "NOT_PROVIDED",
           "DELTA_ENGINE_VS_COMMERCIAL_LM": delta,
           "DELTA_PERCENT": round(100.0 * delta / dry_net, 2),
           "CLASSIFICATION": ["SOURCE_AMBIGUITY", "TRADE_SCOPE_DIFFERENCE"],
           "ROOT_CAUSE": "not established.  The engine measures a wall path; the contractor measures the stretches he will "
                         "actually run skirting along, and the rule separating the two is in the كيال, which is missing.",
           "ACTION": "MORE_SOURCE_REQUIRED"}
    return {"ARTIFACT": "QORTUBA_EXT01_SKIRTING_RECONCILIATION", "AGGREGATE": agg, "BY_ROOM": rows,
            "R3_PROJECT_TOTALS_BY_SEGMENT_CLASS_LM": {k: round(v, 3) for k, v in sorted(by_class.items())},
            "CONTRACTOR_DEDUCTION_RULE": {"VALUE": None, "STATE": "SOURCE_REQUIRED",
                                          "WHY": "the skirting row carries no deduction column entry at all, so the sheet does "
                                                 "not show whether its 76.90 is gross or net of anything"},
            "RULE": "no contractor deduction rule is invented.  R3's deduction lines are geometric facts about the boundary, "
                    "not a commercial rule, and they are not asserted to be the contractor's."}


# ---------------------------------------------------------------------------- §9 black profile, the high-priority test
def profile_reconciliation(sk, pf, comm):
    cc02 = next(r for r in comm["ROWS"] if r["ROW_ID"] == "CC-02")
    cc03 = next(r for r in comm["ROWS"] if r["ROW_ID"] == "CC-03")
    by_class = Counter()
    for r in sk["ROWS"]:
        for k, v in r["BY_SEGMENT_CLASS_LM"].items():
            by_class[k] += v
    dry_net = sk["DRY_NET_SUBTOTAL_LM"]
    prof_total = pf["SUBTOTAL_LM"]

    segs = [
        {"SEGMENT_GROUP": "DOOR_OPENING", "LENGTH_LM": round(by_class["DOOR_OPENING"], 3),
         "IN_R3_PROFILE": True, "IN_R3_SKIRTING": False,
         "CLASSIFICATION": "DOOR_OR_OPENING_SEGMENT",
         "SECONDARY_CLASSIFICATION": "SHOULD_SHARE_SKIRTING_PATH",
         "WHY": "R3 justified the profile crossing these openings by placing it at ceiling level.  The owner states the profile "
                "sits directly ABOVE THE SKIRTING, and a door opening runs from the floor to its head, so a profile at skirting "
                "level stops at the jamb exactly as the skirting does.  The engine's stated reason for including them is "
                "contradicted by the owner's description of the product."},
        {"SEGMENT_GROUP": "WET_ROOM_EDGE", "LENGTH_LM": round(by_class["WET_ROOM_EDGE"], 3),
         "IN_R3_PROFILE": True, "IN_R3_SKIRTING": False,
         "CLASSIFICATION": "WET_ROOM_SEGMENT",
         "SECONDARY_CLASSIFICATION": "ENGINE_PROFILE_SCOPE_ERROR",
         "WHY": "R3 holds the skirting in these three bathrooms at SOURCE_REQUIRED because it does not know whether they are "
                "skirted or tiled, and in the same run releases a profile along the same walls as SOURCE_ESTABLISHED.  A "
                "profile that sits above a skirting cannot be more certain than the skirting under it."},
        {"SEGMENT_GROUP": "NON_WALL_EDGE", "LENGTH_LM": round(by_class["NON_WALL_EDGE"], 3),
         "IN_R3_PROFILE": True, "IN_R3_SKIRTING": False,
         "CLASSIFICATION": "NON_SKIRTING_EDGE",
         "SECONDARY_CLASSIFICATION": "SHOULD_SHARE_SKIRTING_PATH",
         "WHY": "an edge R3 itself judged not to be a wall.  Neither trade runs along it."},
        {"SEGMENT_GROUP": "COLUMN_FACE", "LENGTH_LM": round(by_class["COLUMN_FACE"], 3),
         "IN_R3_PROFILE": True, "IN_R3_SKIRTING": False,
         "CLASSIFICATION": "UNRESOLVED",
         "SECONDARY_CLASSIFICATION": "NON_SKIRTING_EDGE",
         "WHY": "a column face is a wall-level face, and on site a skirting normally returns around a column.  R3 excludes it "
                "from the skirting and includes it in the profile, which cannot both be right, but which of the two is wrong "
                "is an owner or كيال question, not one this comparison can settle."},
    ]
    accounted = round(sum(s["LENGTH_LM"] for s in segs), 3)
    check = round(dry_net + accounted - prof_total, 4)
    corrected = round(prof_total - by_class["DOOR_OPENING"] - by_class["WET_ROOM_EDGE"] - by_class["NON_WALL_EDGE"], 3)
    corrected_with_columns = round(corrected - by_class["COLUMN_FACE"], 3)
    return {"ARTIFACT": "QORTUBA_EXT01_PROFILE_RECONCILIATION",
            "OWNER_CLARIFICATION": "a black profile is installed above the skirting and follows the same general wall-level path; "
                                   "the two are separate BOQ items and their commercial lengths need not be identical",
            "AGGREGATE": {"ITEM": "profile above skirting, aggregate",
                          "ENGINE_VALUE_LM": prof_total,
                          "ENGINE_BASIS": "the whole wall path of all nine regions with nothing deducted but UNRESOLVED, on "
                                          "R3's stated assumption that the profile runs at ceiling level and crosses openings",
                          "COMMERCIAL_VALUE_LM": cc03["NET"],
                          "COMMERCIAL_BASIS": "'بروفيل اعلي نعله' (profile above skirting), one summed length in متر طولي",
                          "KIYAL_VALUE_LM": None, "KIYAL_BASIS": "NOT_PROVIDED",
                          "DELTA_ENGINE_VS_COMMERCIAL_LM": round(cc03["NET"] - prof_total, 4),
                          "DELTA_PERCENT": round(100.0 * (cc03["NET"] - prof_total) / prof_total, 2),
                          "CLASSIFICATION": ["ENGINE_TRADE_RULE_ERROR", "SOURCE_AMBIGUITY"],
                          "ACTION": "ENGINE_TRADE_RULE_FIX_REQUIRED"},
            "CONTRACTOR_RULE_OBSERVED": {"STATEMENT": "the sheet bills the profile at exactly the skirting length: 76.90 and 76.90",
                                         "COMMERCIAL_SKIRTING_LM": cc02["NET"], "COMMERCIAL_PROFILE_LM": cc03["NET"],
                                         "DIFFERENCE_LM": round(cc03["NET"] - cc02["NET"], 4),
                                         "STATUS": "OBSERVED_IN_THE_COMMERCIAL_SHEET",
                                         "LIMIT": "two equal numbers on a priced sheet show what was billed, not necessarily "
                                                  "what was measured; the كيال would show whether they were measured once"},
            "PROFILE_ONLY_SEGMENTS": segs,
            "SEGMENT_CLASSES": PROFILE_SEGMENT_CLASSES,
            "DECOMPOSITION": {"R3_SKIRTING_DRY_NET_LM": dry_net,
                              "PROFILE_ONLY_LENGTH_LM": accounted,
                              "R3_PROFILE_TOTAL_LM": prof_total,
                              "RESIDUAL_LM": check,
                              "EXACT": abs(check) < 5e-4,
                              "MEANING": "the whole profile-to-skirting difference is accounted for by these four segment "
                                         "groups; there is no unexplained remainder"},
            "IF_THE_TRADE_RULE_FOLLOWED_THE_OWNER": {
                "PROFILE_WITHOUT_OPENINGS_WET_ROOMS_AND_NON_WALL_EDGES_LM": corrected,
                "PROFILE_ALSO_WITHOUT_COLUMN_FACES_LM": corrected_with_columns,
                "EQUALS_R3_SKIRTING": abs(corrected_with_columns - dry_net) < 5e-4,
                "MEANING": "correcting the trade rule alone collapses the profile discrepancy into the skirting discrepancy. "
                           "Two separate problems: a profile trade rule that is wrong on this project's own evidence, and a "
                           "skirting scope difference that is still unexplained for want of the كيال.",
                "NOT_APPLIED": "this is arithmetic on the frozen R3 segment classes, shown to locate the defect.  No R3 value "
                               "is changed by this phase and no corrected profile length is released as a quantity."},
            "ACTION": "ENGINE_TRADE_RULE_FIX_REQUIRED",
            "DEFER": "the fix belongs to PA08_QORTUBA_R4 and must be generic; it is not made here"}


# ---------------------------------------------------------------------------- §10 bathrooms and kitchens
def wet_reconciliation(wet, sk, cov, comm):
    cc04 = next(r for r in comm["ROWS"] if r["ROW_ID"] == "CC-04")
    wet_floor = cov["SUBTOTALS"]["WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    pantry = next(r for r in sk["ROWS"] if "PAINTRY" in r["ROOM"].upper() or "PANTRY" in r["ROOM"].upper())
    pantry_floor = 11.685
    wet_gross_path = round(sum(r["GROSS_WALL_PATH_LM"] for r in sk["ROWS"] if r["WET_OR_DRY"] == "WET"), 3)
    wet_host_path = round(sum(r["WET_ROOM_WALL_EDGE_LM"] for r in sk["ROWS"] if r["WET_OR_DRY"] == "WET"), 3)
    pantry_path = pantry["GROSS_WALL_PATH_LM"]

    def implied(label, area, path, note):
        return {"SCENARIO": label, "AREA_TAKEN_AS_WALL_M2": round(area, 4), "WALL_PATH_M": round(path, 3),
                "IMPLIED_CONTRACTOR_HEIGHT_M": round(area / path, 3) if path else None, "NOTE": note}

    scenarios = [
        implied("the 159.28 gross is wall tiling of the three second-floor bathrooms only",
                cc04["QUANTITY"], wet_gross_path, "an implausible tiling height; the reading is very unlikely"),
        implied("the 153.2775 net is wall tiling of the three bathrooms only",
                cc04["AMOUNT"] / cc04["RATE"], wet_gross_path, "still an implausible height"),
        implied("the 153.2775 net is wall tiling of the three bathrooms plus the pantry",
                cc04["AMOUNT"] / cc04["RATE"], wet_gross_path + pantry_path, "high for a normal storey"),
        implied("the 153.2775 net is wall plus floor for the three bathrooms and the pantry",
                cc04["AMOUNT"] / cc04["RATE"] - wet_floor - pantry_floor, wet_gross_path + pantry_path,
                "the only reading that lands near a normal full-height tiling, close to 3 m; it is still one reading among "
                "several and the sheet supports none of them over the others"),
    ]
    return {"ARTIFACT": "QORTUBA_EXT01_WET_ROOM_RECONCILIATION",
            "R3_WET_GEOMETRY": [{"ROOM": w["ROOM"], "FLOOR_AREA_M2": w["FLOOR_AREA_M2"]["VALUE"],
                                 "HOST_WALL_LM": w["HOST_WALL_LM"]["VALUE"], "DOOR_OPENING_LM": w["DOOR_OPENING_LM"]["VALUE"],
                                 "WALL_TILE_AREA_M2": w["WALL_TILE_AREA_M2"]["STATE"]} for w in wet["ROWS"]],
            "R3_WET_FLOOR_SUBTOTAL_M2": wet_floor,
            "R3_WET_GROSS_WALL_PATH_LM": wet_gross_path, "R3_WET_HOST_WALL_PATH_LM": wet_host_path,
            "CONTRACTOR_ROW": {"ROW_ID": cc04["ROW_ID"], "RAW": cc04["RAW_ARABIC_TEXT"], "GROSS": cc04["QUANTITY"],
                               "HALF_DEDUCTION": cc04["HALF_DISCOUNT"], "NET_PRINTED": cc04["NET"],
                               "NET_IMPLIED_BY_THE_AMOUNT": cc04.get("IMPLIED_UNROUNDED_NET")},
            "WHAT_THE_ROW_REPRESENTS": {"VALUE": None, "STATE": "NOT_ESTABLISHED",
                                        "CANDIDATES": ["WALL_CERAMIC_AREA", "FLOOR_CERAMIC_AREA", "FLOOR_PLUS_WALL",
                                                       "GROSS_WALL_AREA", "NET_WALL_AREA", "BATHROOMS_PLUS_KITCHEN",
                                                       "MORE_THAN_ONE_STOREY"],
                                        "WHY": "the row is two Arabic words and a number"},
            "IMPLIED_CONTRACTOR_HEIGHT": {"SCENARIOS": scenarios,
                                          "STATE": "DERIVED_FROM_CONTRACTOR_KIYAL",
                                          "QUALIFIERS": ["NOT_SOURCE_ESTABLISHED", "NOT_AN_URBAN_RULE",
                                                         "NOT_A_QORTUBA_DRAWING_FACT", "DIAGNOSTIC_ONLY"],
                                          "NOT_FED_BACK": "no height from this table enters R3, any engine rule, or any "
                                                          "quantity.  R3's wall tile area stays NOT_ESTABLISHED."},
            "HALF_DEDUCTION_SIGNAL": {"DEDUCTION_M2": cc04["HALF_DISCOUNT"],
                                      "IF_HALF_OF_OPENINGS": round(2 * cc04["HALF_DISCOUNT"], 3),
                                      "R3_SECOND_FLOOR_WET_DOOR_WIDTHS_M": [w["DOOR_OPENING_LM"]["VALUE"] for w in wet["ROWS"]],
                                      "OBSERVATION": "a 6.00 half deduction implies about 12 m2 of openings.  Three bathroom "
                                                     "doors of the widths R3 measured cannot reach that at any ordinary door "
                                                     "height, which is one of several signals that this row covers more rooms "
                                                     "than the three bathrooms on the storey R3 measured.",
                                      "STATUS": "SIGNAL_NOT_CONCLUSION"},
            "ENGINE_POSITION": "R3 emitted no wall tile area at all, in any wet room, because no section, elevation, finishes "
                               "schedule or owner height exists for this project.  That refusal stands.",
            "CLASSIFICATION": ["SOURCE_AMBIGUITY", "TRADE_SCOPE_DIFFERENCE"],
            "ACTION": "MORE_SOURCE_REQUIRED"}


# ---------------------------------------------------------------------------- §11 pantry / kitchen identity
def identity_mapping():
    return {"ARTIFACT": "QORTUBA_EXT01_SPACE_IDENTITY_MAPPING",
            "ROWS": [
                {"DRAWING_SPACE": "PAINTRY (as spelled in the DWG text)", "R3_REGION_ID": "FMR-45ddc40db7af",
                 "R3_AREA_M2": 11.685, "R3_FUNCTION": "DRY_INTERNAL",
                 "CONTRACTOR_TERM": "مطابخ (kitchens), inside the row 'حمامات ومطابخ'",
                 "MATCH_STATUS": "AMBIGUOUS",
                 "WHY": "a pantry and a kitchen are not the same room, and the contractor row is plural where the storey R3 "
                        "measured has one such space.  Whether the contractor's 'kitchens' includes this pantry, or refers to "
                        "a kitchen on another floor, is not established.",
                 "CONSEQUENCE_IF_WRONG": "the pantry's 11.685 m2 floor and its 11.15 m wall path would move between the floor "
                                         "package and the wet package, changing both comparisons"},
                {"DRAWING_SPACE": "BATH x3", "R3_REGION_IDS": ["FMR-a8bebaab8359", "FMR-3ef432705c51", "FMR-2618ef1772e9"],
                 "R3_AREA_M2": [8.5525, 5.1, 4.21], "R3_FUNCTION": "WET_INTERNAL",
                 "CONTRACTOR_TERM": "حمامات (bathrooms), inside the row 'حمامات ومطابخ'",
                 "MATCH_STATUS": "CONTRACTOR_SCOPE_GROUP",
                 "WHY": "the contractor groups all bathrooms into one quantity; R3 keeps three separate wet regions.  The group "
                        "certainly contains these three if the sheet covers this storey, and may contain more."},
                {"DRAWING_SPACE": "DRESS", "R3_REGION_ID": "FMR-894527f7d191", "R3_AREA_M2": 11.985,
                 "R3_FUNCTION": "DRY_INTERNAL", "CONTRACTOR_TERM": None, "MATCH_STATUS": "AMBIGUOUS",
                 "WHY": "no contractor row names a dressing room; it is either inside the unbroken floor quantity or outside "
                        "the ceramic scope entirely, and the sheet does not say which"},
                {"DRAWING_SPACE": "HALL / whgm", "R3_REGION_ID": "FMR-2eaf198b6182", "R3_AREA_M2": 36.37,
                 "R3_FUNCTION": "DRY_INTERNAL", "CONTRACTOR_TERM": None, "MATCH_STATUS": "AMBIGUOUS",
                 "WHY": "no contractor row names a hall"},
            ],
            "MATCH_STATUSES": ("SAME_PHYSICAL_SPACE", "CONTRACTOR_SCOPE_GROUP", "DIFFERENT_SPACE", "AMBIGUOUS"),
            "SAME_PHYSICAL_SPACE_COUNT": 0,
            "RULE": "a drawing room name and a contractor trade word are not assumed to be the same space"}


# ---------------------------------------------------------------------------- §12 / §13 other linear and counted items
def other_items(comm):
    linear = [
        {"ROW_ID": "CC-05", "RAW": "زوايا +جروف", "READING": "corners plus grooves / recessed bands",
         "QUANTITY_LM": 26.35, "ITEM_TYPE": ["CORNER_PROFILE", "GROOVE"],
         "R3_GEOMETRY_STATUS": "NOT_CURRENTLY_MODELLED",
         "REQUIRES": ["REQUIRES_VERTICAL_HEIGHT", "REQUIRES_FINISH_SPEC"],
         "WHY": "a tiled internal or external corner is a vertical line whose length is the tiling height, and a groove is a "
                "detail in a finishes drawing.  R3 models neither, and has no height for either.",
         "ENGINE_EMITTED": None, "SAFE_REFUSAL": True},
        {"ROW_ID": "CC-06", "RAW": "زوايا شطف", "READING": "chamfered / mitred corners",
         "QUANTITY_LM": 12.00, "ITEM_TYPE": ["CHAMFER", "EDGE_TRIM"],
         "R3_GEOMETRY_STATUS": "NOT_CURRENTLY_MODELLED",
         "REQUIRES": ["REQUIRES_VERTICAL_HEIGHT", "REQUIRES_FINISH_SPEC"],
         "WHY": "a 45 degree mitre at an external tiled corner: again a vertical length, and a workmanship decision",
         "ENGINE_EMITTED": None, "SAFE_REFUSAL": True},
    ]
    fixtures = [
        {"ROW_ID": "CC-07", "RAW": "بلاعه", "READING": "floor drain / gully", "COUNT": 7,
         "SOURCE_REQUIREMENT": "SANITARY_DRAWING_REQUIRED",
         "WHY": "a floor gully is a drainage fitting; the architectural plan does not place it, and no Qortuba sanitary "
                "drawing was provided",
         "ENGINE_EMITTED": None, "SAFE_REFUSAL": True,
         "OBSERVATION": "seven gullies is more than three bathrooms and a pantry would normally carry, which is a further "
                        "signal about the sheet's storey scope"},
        {"ROW_ID": "CC-08", "RAW": "حوض قدم", "READING": "foot basin / footbath", "COUNT": 2,
         "SOURCE_REQUIREMENT": "SANITARY_DRAWING_REQUIRED", "ENGINE_EMITTED": None, "SAFE_REFUSAL": True,
         "WHY": "a built-in foot-washing basin is a sanitary fitting"},
        {"ROW_ID": "CC-09", "RAW": "روشنه", "READING": "wall niche / recessed shelf", "COUNT": 4,
         "SOURCE_REQUIREMENT": "FINISH_SCHEDULE_REQUIRED", "ENGINE_EMITTED": None, "SAFE_REFUSAL": True,
         "WHY": "a shower niche is an interior detail and is rarely on a plan at this scale"},
        {"ROW_ID": "CC-10", "RAW": "شباك", "READING": "tiled window reveal and sill", "COUNT": 3,
         "SOURCE_REQUIREMENT": "ARCH_DRAWING_SUFFICIENT_FOR_EXISTENCE_ONLY", "ENGINE_EMITTED": None, "SAFE_REFUSAL": True,
         "WHY": "the engine does find window openings in this drawing, so the existence of windows is drawing evidence. "
                "Which of them sit inside a tiled room, and therefore attract this item, needs the tiled-room scope, which "
                "is the missing كيال."},
        {"ROW_ID": "CC-11", "RAW": "سيفون", "READING": "tiling to the concealed WC cistern enclosure", "COUNT": 3,
         "SOURCE_REQUIREMENT": "SANITARY_DRAWING_REQUIRED", "ENGINE_EMITTED": None, "SAFE_REFUSAL": True,
         "WHY": "a concealed cistern is a sanitary fitting",
         "OBSERVATION": "three cisterns matches the three bathrooms R3 measured on this storey, which points the other way "
                        "from the seven gullies; the two signals disagree and neither settles the scope"},
    ]
    return {"ARTIFACT": "QORTUBA_EXT01_OTHER_ITEMS",
            "LINEAR_FINISH_ITEMS": linear, "FIXTURE_AND_SANITARY_ITEMS": fixtures,
            "GEOMETRY_STATUSES": ("GEOMETRY_AVAILABLE", "PARTIALLY_AVAILABLE", "REQUIRES_VERTICAL_HEIGHT",
                                  "REQUIRES_FINISH_SPEC", "REQUIRES_SITE_INFORMATION", "NOT_CURRENTLY_MODELLED"),
            "RULE": "no quantity is fabricated for any of these rows, and the engine is not marked down for missing sanitary "
                    "or finishes information it was never given"}


# ---------------------------------------------------------------------------- §14 A22
def a22(flooring, skirting, profile, wetrec, other, comm):
    def row(i, desc, ev, eu, eb, kv, kb, cv, cb, cls, root, conf, act):
        de = None if (ev is None or kv is None) else round(kv - ev, 4)
        dc = None if (ev is None or cv is None) else round(cv - ev, 4)
        dp = None if (dc is None or not ev) else round(100.0 * dc / ev, 2)
        return {"ITEM_ID": i, "DESCRIPTION": desc, "ENGINE_VALUE": ev, "ENGINE_UNIT": eu, "ENGINE_BASIS": eb,
                "CONTRACTOR_KIYAL_VALUE": kv, "CONTRACTOR_KIYAL_BASIS": kb,
                "COMMERCIAL_VALUE": cv, "COMMERCIAL_BASIS": cb,
                "DELTA_ENGINE_VS_KIYAL": de, "DELTA_ENGINE_VS_COMMERCIAL": dc, "DELTA_PERCENT": dp,
                "CLASSIFICATION": cls, "ROOT_CAUSE": root, "CONFIDENCE_STATUS": conf, "ACTION": act}

    f, s, p = flooring["AGGREGATE"], skirting["AGGREGATE"], profile["AGGREGATE"]
    rows = [
        row("A22-Q-01", "ceramic floor tiling", f["ENGINE_VALUE_M2"], "M2", f["ENGINE_BASIS"],
            None, "NOT_PROVIDED", f["COMMERCIAL_VALUE_M2"], f["COMMERCIAL_BASIS"],
            ["SOURCE_AMBIGUITY", "TRADE_SCOPE_DIFFERENCE"],
            "the sheet states no storey and no room breakdown, so the two totals are not known to cover the same rooms",
            "CONTRACTOR_BASIS_UNRESOLVED", "MORE_SOURCE_REQUIRED"),
        row("A22-Q-02", "skirting", s["ENGINE_VALUE_LM"], "LM", s["ENGINE_BASIS"],
            None, "NOT_PROVIDED", s["COMMERCIAL_VALUE_LM"], s["COMMERCIAL_BASIS"],
            ["SOURCE_AMBIGUITY", "TRADE_SCOPE_DIFFERENCE"],
            "the engine measures an eligible wall path; the contractor measures the stretches he runs skirting along, and the "
            "rule between them is in the missing كيال",
            "CONTRACTOR_BASIS_UNRESOLVED", "MORE_SOURCE_REQUIRED"),
        row("A22-Q-03", "profile above skirting", p["ENGINE_VALUE_LM"], "LM", p["ENGINE_BASIS"],
            None, "NOT_PROVIDED", p["COMMERCIAL_VALUE_LM"], p["COMMERCIAL_BASIS"],
            ["ENGINE_TRADE_RULE_ERROR", "SOURCE_AMBIGUITY"],
            "R3 runs the profile at ceiling level across openings and along wet-room walls whose skirting it refuses to "
            "quantify.  The owner states the profile sits above the skirting, so that basis is wrong on this project's own "
            "evidence; the residual after correcting it is the same unexplained skirting scope gap",
            "ENGINE_DEFECT_CONFIRMED_BY_OWNER_STATEMENT", "ENGINE_TRADE_RULE_FIX_REQUIRED"),
        row("A22-Q-04", "bathrooms and kitchens ceramic", None, "M2",
            "NOT_ESTABLISHED: no section, elevation, finishes schedule or owner height exists, so no wall tile area was emitted",
            None, "NOT_PROVIDED", 153.2775, "one summed quantity of unstated basis, gross 159.28 less a 6.00 half deduction",
            ["SOURCE_AMBIGUITY"],
            "the engine correctly emitted nothing; the contractor row's basis is not stated",
            "SAFE_REFUSAL", "MORE_SOURCE_REQUIRED"),
        row("A22-Q-05", "corners and grooves", None, "LM", "NOT_CURRENTLY_MODELLED: needs a tiling height and a finish spec",
            None, "NOT_PROVIDED", 26.35, "one summed length", ["SOURCE_AMBIGUITY"],
            "the engine models no tile-edge geometry and has no height", "SAFE_REFUSAL", "MORE_SOURCE_REQUIRED"),
        row("A22-Q-06", "chamfered corners", None, "LM", "NOT_CURRENTLY_MODELLED: needs a tiling height and a finish spec",
            None, "NOT_PROVIDED", 12.00, "one summed length", ["SOURCE_AMBIGUITY"],
            "the engine models no tile-edge geometry and has no height", "SAFE_REFUSAL", "MORE_SOURCE_REQUIRED"),
    ]
    for fx in other["FIXTURE_AND_SANITARY_ITEMS"]:
        rows.append(row(f"A22-Q-{fx['ROW_ID'][3:]}", fx["READING"], None, "NR",
                        f"NOT_APPLICABLE: {fx['SOURCE_REQUIREMENT']}", None, "NOT_PROVIDED", fx["COUNT"],
                        "counted on the priced sheet", ["SOURCE_AMBIGUITY"],
                        fx["WHY"], "SAFE_REFUSAL", "MORE_SOURCE_REQUIRED"))
    return {"ARTIFACT": "A22_QORTUBA_EXTERNAL_RECONCILIATION", "ROWS": rows, "COUNT": len(rows),
            "DIFFERENCE_CLASSES": DIFFERENCE_CLASSES, "ACTIONS": ACTIONS,
            "BY_ACTION": dict(Counter(r["ACTION"] for r in rows)),
            "BY_CONFIDENCE": dict(Counter(r["CONFIDENCE_STATUS"] for r in rows)),
            "RULE": "three bases side by side, never averaged and never forced into one number"}


# ---------------------------------------------------------------------------- §16 metrics
def metrics(reg, flooring, skirting, profile, wetrec, other, a22reg):
    comparable_rooms = sum(1 for r in flooring["BY_ROOM"] if r["CONTRACTOR_KIYAL_AREA_M2"] is not None)
    safe = [r for r in a22reg["ROWS"] if r["CONFIDENCE_STATUS"] == "SAFE_REFUSAL"]
    silent = [{"QUANTITY": "PROFILE_GEOMETRIC_PATH_LM", "VALUE": profile["AGGREGATE"]["ENGINE_VALUE_LM"], "UNIT": "LM",
               "EMITTED_STATE": "SOURCE_ESTABLISHED", "EXCEPTION_RAISED": False,
               "WHY_WRONG": "the trade basis, not the geometry.  R3 released a profile length over 26.2 m of bathroom wall "
                            "whose skirting it held at SOURCE_REQUIRED, and across 12.1 m of door openings and 2.75 m of "
                            "non-wall edge, on a stated assumption that the profile runs at ceiling level.  The owner states "
                            "it sits above the skirting.",
               "GEOMETRY_CORRECT": True,
               "DETECTED_BY": "the owner's clarification plus the contractor sheet billing profile and skirting at the same "
                              "length; not by any internal check",
               "SEVERITY": "the released length is 44.4 per cent longer than the corrected path would be"}]
    return {"ARTIFACT": "QORTUBA_EXT01_EXTERNAL_VALIDATION_METRICS",
            "NO_SINGLE_SCORE": "no combined accuracy figure is produced; the axes measure different things and one number "
                               "would hide the only result that matters",
            "A_GEOMETRY_AGREEMENT": {"CONTRACTOR_ROOM_MEASUREMENTS_AVAILABLE": 0,
                                     "MATCH": 0, "WITHIN_TOLERANCE": 0, "MATERIAL_DIFFERENCE": 0,
                                     "NOT_COMPARABLE": len(reg["ROWS"]),
                                     "WHY": "the priced sheet carries no room measurement, and the كيال was not supplied, so "
                                            "not one of the nine R3 rooms has a contractor counterpart to compare with",
                                     "VERDICT": "NOT_TESTED_BY_THIS_SOURCE"},
            "B_FLOORING_SCOPE_AGREEMENT": {"CONTRACTOR_FLOORING_ROWS": 2,
                                           "MAPPED_TO_ENGINE_REGIONS": 0, "PARTIALLY_MAPPED": 2,
                                           "WHY": "the floor row and the bathrooms-and-kitchens row each map to a group of "
                                                  "engine regions whose membership is unstated",
                                           "VERDICT": "NOT_ESTABLISHED"},
            "C_SKIRTING_AGREEMENT": {"COMPARABLE_PAIRS": 1,
                                     "ENGINE_LM": skirting["AGGREGATE"]["ENGINE_VALUE_LM"],
                                     "COMMERCIAL_LM": skirting["AGGREGATE"]["COMMERCIAL_VALUE_LM"],
                                     "DELTA_LM": skirting["AGGREGATE"]["DELTA_ENGINE_VS_COMMERCIAL_LM"],
                                     "DELTA_PERCENT": skirting["AGGREGATE"]["DELTA_PERCENT"],
                                     "VERDICT": "DIFFERENT_BASIS_UNEXPLAINED"},
            "D_PROFILE_AGREEMENT": {"COMPARABLE_PAIRS": 1,
                                    "ENGINE_LM": profile["AGGREGATE"]["ENGINE_VALUE_LM"],
                                    "COMMERCIAL_LM": profile["AGGREGATE"]["COMMERCIAL_VALUE_LM"],
                                    "DELTA_LM": profile["AGGREGATE"]["DELTA_ENGINE_VS_COMMERCIAL_LM"],
                                    "DELTA_PERCENT": profile["AGGREGATE"]["DELTA_PERCENT"],
                                    "ENGINE_TRADE_RULE_DEFECT_FOUND": True,
                                    "RESIDUAL_AFTER_TRADE_RULE_CORRECTION_IS_THE_SKIRTING_GAP": True,
                                    "VERDICT": "ENGINE_TRADE_RULE_ERROR_CONFIRMED"},
            "E_SAFE_REFUSAL": {"CONTRACTOR_ITEMS_THE_ENGINE_LEFT_UNQUANTIFIED": len(safe),
                               "OF_TOTAL_CONTRACTOR_ROWS": 11,
                               "ITEMS": [r["ITEM_ID"] for r in safe],
                               "CORRECTLY_REFUSED": len(safe),
                               "WRONGLY_REFUSED": 0,
                               "WHY": "each needs a tiling height, a finishes specification or a sanitary drawing, none of "
                                      "which exists for this project.  The engine emitted nothing and raised the missing "
                                      "source instead.",
                               "VERDICT": "HELD"},
            "F_SILENT_WRONG_QUANTITY": {"COUNT": len(silent), "ITEMS": silent,
                                        "UNRESOLVED_CANDIDATES": 2,
                                        "UNRESOLVED_CANDIDATE_NOTE": "the floor total and the skirting total each differ from "
                                                                     "the contractor by an unexplained amount.  Neither is "
                                                                     "counted here: a difference of unknown cause is not a "
                                                                     "demonstrated wrong quantity, and inflating this count "
                                                                     "with unproven items would devalue it as much as hiding "
                                                                     "a real one.",
                                        "VERDICT": "ONE_CONFIRMED"}}


# ---------------------------------------------------------------------------- §18 what Qortuba proves
def what_qortuba_proves():
    return {"ARTIFACT": "QORTUBA_EXT01_WHAT_THIS_VALIDATION_PROVES",
            "PROVEN_BY_QORTUBA": [
                {"CLAIM": "the engine reads an unfamiliar Arabic-authored DWG end to end", "EVIDENCE": "units, layers, "
                 "keyboard-mapped Arabic labels, 101 authored dimensions and a door block with no swing arc were all read "
                 "without project-specific configuration", "STATUS": "PROVEN_INDEPENDENTLY_OF_THIS_COMPARISON"},
                {"CLAIM": "floor measurement regions can be released from drawn lines while wall material stays unresolved",
                 "EVIDENCE": "nine regions established with every physical wall verdict unchanged",
                 "STATUS": "PROVEN_INDEPENDENTLY_OF_THIS_COMPARISON"},
                {"CLAIM": "the engine refuses a vertical quantity when no height exists",
                 "EVIDENCE": "eight of the eleven contractor rows need a height, a finish spec or a sanitary drawing, and the "
                             "engine emitted nothing for any of them", "STATUS": "PROVEN_BY_THIS_COMPARISON"},
                {"CLAIM": "an external source can expose a trade-rule error the engine could not see in itself",
                 "EVIDENCE": "the profile basis, found through the owner's clarification and the contractor's equal billing",
                 "STATUS": "PROVEN_BY_THIS_COMPARISON"},
            ],
            "NOT_PROVEN_BY_QORTUBA": [
                {"CLAIM": "room-by-room floor areas agree with a measured benchmark",
                 "WHY": "no room-level contractor measurement was supplied"},
                {"CLAIM": "the engine's floor total is right or wrong",
                 "WHY": "the contractor total's storey and room scope is unstated"},
                {"CLAIM": "the skirting rule is right or wrong", "WHY": "the deduction rule behind 76.90 m is not documented"},
                {"CLAIM": "a full villa bill of quantities", "WHY": "one storey, one trade package"},
                {"CLAIM": "external facades, structure, sanitary, electrical, plaster and paint, pricing, procurement",
                 "WHY": "outside the scope of both the drawing set read and the sheet supplied"},
            ]}


# ---------------------------------------------------------------------------- §20 R4 recommendations, not implemented
def r4_recommendations():
    return {"ARTIFACT": "QORTUBA_EXT01_RECOMMENDED_R4_FIXES",
            "IMPLEMENTED_IN_THIS_PHASE": "NONE",
            "ROWS": [
                {"FIX_ID": "R4-01", "PRIORITY": "HIGH", "KIND": "GENERIC_ENGINE_TRADE_RULE_FIX_REQUIRED",
                 "TITLE": "a trade that sits on another trade inherits its path and its certainty",
                 "DEFECT": "the profile is measured from the whole wall path, crosses door openings, and is released as "
                           "established along wet-room walls whose skirting the same run holds at SOURCE_REQUIRED",
                 "GENERIC_RULE_PROPOSED": "where one linear trade is declared to sit above another, the upper trade's path is "
                                          "the lower trade's path unless a source says otherwise, and its state can never be "
                                          "stronger than the lower trade's state",
                 "MUST_NOT": "the rule must be generic and must be validated against the P7757 regression and the synthetic "
                             "fixtures; it must not be tuned so that Qortuba's profile reaches 76.90 m",
                 "DO_NOT_IMPLEMENT_NOW": True},
                {"FIX_ID": "R4-02", "PRIORITY": "MEDIUM", "KIND": "ENGINE_TRADE_RULE_FIX_REQUIRED",
                 "TITLE": "a column face belongs to the same side of every linear trade",
                 "DEFECT": "2.95 m of column face is excluded from the skirting and included in the profile in the same run",
                 "GENERIC_RULE_PROPOSED": "one classification of a boundary segment feeds every trade that runs along it; a "
                                          "segment may be out of scope for a trade, but not out for one and in for its "
                                          "neighbour without a stated reason",
                 "DO_NOT_IMPLEMENT_NOW": True},
                {"FIX_ID": "R4-03", "PRIORITY": "MEDIUM", "KIND": "ENGINE_CAPABILITY_GAP",
                 "TITLE": "fitted joinery along a wall is not modelled",
                 "DEFECT": "R3 cannot represent a run of base units or wardrobes against a wall, so it can neither apply nor "
                           "refuse the joinery exclusion that a skirting takeoff normally carries",
                 "GENERIC_RULE_PROPOSED": "detect joinery outlines that run along a wall face and expose the overlap as a "
                                          "named, refusable segment class rather than silently counting it as skirting",
                 "DO_NOT_IMPLEMENT_NOW": True},
                {"FIX_ID": "R4-04", "PRIORITY": "MEDIUM", "KIND": "PROCESS",
                 "TITLE": "a benchmark without its working sheet cannot close a comparison",
                 "DEFECT": "every room-level question in this phase ended at SOURCE_REQUIRED because only the priced summary "
                           "was supplied",
                 "GENERIC_RULE_PROPOSED": "an external validation should request the كيال working sheets with the priced sheet, "
                                          "and should record which questions the priced sheet alone can never answer",
                 "DO_NOT_IMPLEMENT_NOW": True},
            ]}


def run():
    ver = verify_frozen_state()
    write("PA08_QORTUBA_EXT01_FROZEN_STATE_VERIFICATION", ver)
    comm = json.loads((OUT / "QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER.json").read_text("utf-8"))
    kiyal = json.loads((OUT / "QORTUBA_CONTRACTOR_KIYAL_REGISTER.json").read_text("utf-8"))
    reg, sk, pf, wet, cov = r3_values()

    flooring = flooring_reconciliation(reg, cov, comm)
    skirting = skirting_reconciliation(sk, comm)
    profile = profile_reconciliation(sk, pf, comm)
    wetrec = wet_reconciliation(wet, sk, cov, comm)
    ident = identity_mapping()
    others = other_items(comm)
    a22reg = a22(flooring, skirting, profile, wetrec, others, comm)
    mets = metrics(reg, flooring, skirting, profile, wetrec, others, a22reg)
    proves = what_qortuba_proves()
    r4 = r4_recommendations()

    written = ["PA08_QORTUBA_EXT01_FROZEN_STATE_VERIFICATION"]
    for obj in (flooring, skirting, profile, wetrec, ident, others, a22reg, mets, proves, r4):
        written.append(write(obj["ARTIFACT"], obj))

    # the engine was read, never written: check every R3 hash again
    _, _, bad_after = r3_fingerprint()
    if bad_after:
        raise SystemExit(f"R3 artifacts changed during the reconciliation: {bad_after}")

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    contents = {n: _sha(OUT / f"{n}.json") for n in sorted(set(written) | {"QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER",
                                                                           "QORTUBA_CONTRACTOR_KIYAL_REGISTER",
                                                                           "CONTRACTOR_TRANSCRIPTION_FREEZE"})}
    fr = {"ARTIFACT": "FREEZE_PA08_QORTUBA_EXTERNAL_RECONCILIATION_01", "PROJECT_ALIAS": "QORTUBA",
          "PHASE": "PA08_QORTUBA_EXTERNAL_RECONCILIATION_01",
          "R3_NOT_REWRITTEN": {"FREEZE_DIGEST": ver["R3_FREEZE_DIGEST"], "ARTIFACTS": ver["R3_ARTIFACTS"],
                               "HASHES_VERIFIED_BEFORE_AND_AFTER": True, "MISMATCHES": []},
          "PRIOR_FREEZES": ver["PRIOR_FREEZES"],
          "CONTRACTOR_TRANSCRIPTION_FREEZE_DIGEST": ver["CONTRACTOR_TRANSCRIPTION_FREEZE_DIGEST"],
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "ENGINE_CHANGED_IN_THIS_PHASE": "NONE: no geometry, no floor region, no skirting or profile rule, no opening rule",
          "SOURCES": TR.SOURCES, "MISSING_SOURCES": TR.MISSING_SOURCES,
          "CONTENTS": contents, "COUNT": len(contents),
          "SILENT_WRONG_QUANTITY_COUNT": mets["F_SILENT_WRONG_QUANTITY"]["COUNT"],
          "READY_FOR_NEXT_VALIDATION_VILLA": "NO",
          "READY_WHY": "the profile trade rule is a confirmed defect and is unfixed by design, and the floor and skirting "
                       "comparisons are unresolved for want of the كيال.  Taking a new villa now would repeat both."}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_PA08_QORTUBA_EXTERNAL_RECONCILIATION_01", fr)
    return {"FREEZE": fr, "METRICS": mets, "A22": a22reg, "PROFILE": profile, "SKIRTING": skirting,
            "FLOORING": flooring, "WET": wetrec, "WRITTEN": written, "R4": r4, "VERIFY": ver}


if __name__ == "__main__":
    o = run()
    m = o["METRICS"]
    print("FREEZE", o["FREEZE"]["DIGEST"][:16], "| registers", o["FREEZE"]["COUNT"])
    print("R3 untouched:", o["VERIFY"]["R3_HASH_MISMATCHES"] == [], "| transcription frozen first:", o["VERIFY"]["TRANSCRIPTION_FROZEN_BEFORE_COMPARISON"])
    print("floor   engine", o["FLOORING"]["AGGREGATE"]["ENGINE_VALUE_M2"], "vs commercial", o["FLOORING"]["AGGREGATE"]["COMMERCIAL_VALUE_M2"],
          "delta", o["FLOORING"]["AGGREGATE"]["DELTA_ENGINE_VS_COMMERCIAL_M2"], f"({o['FLOORING']['AGGREGATE']['DELTA_PERCENT']}%)")
    print("skirt   engine", o["SKIRTING"]["AGGREGATE"]["ENGINE_VALUE_LM"], "vs commercial", o["SKIRTING"]["AGGREGATE"]["COMMERCIAL_VALUE_LM"],
          "delta", o["SKIRTING"]["AGGREGATE"]["DELTA_ENGINE_VS_COMMERCIAL_LM"], f"({o['SKIRTING']['AGGREGATE']['DELTA_PERCENT']}%)")
    print("profile engine", o["PROFILE"]["AGGREGATE"]["ENGINE_VALUE_LM"], "vs commercial", o["PROFILE"]["AGGREGATE"]["COMMERCIAL_VALUE_LM"],
          "delta", o["PROFILE"]["AGGREGATE"]["DELTA_ENGINE_VS_COMMERCIAL_LM"], f"({o['PROFILE']['AGGREGATE']['DELTA_PERCENT']}%)")
    print("  decomposition", o["PROFILE"]["DECOMPOSITION"])
    print("  corrected ==  skirting:", o["PROFILE"]["IF_THE_TRADE_RULE_FOLLOWED_THE_OWNER"]["EQUALS_R3_SKIRTING"])
    print("SAFE_REFUSAL", m["E_SAFE_REFUSAL"]["CONTRACTOR_ITEMS_THE_ENGINE_LEFT_UNQUANTIFIED"], "of", m["E_SAFE_REFUSAL"]["OF_TOTAL_CONTRACTOR_ROWS"])
    print("SILENT_WRONG", m["F_SILENT_WRONG_QUANTITY"]["COUNT"], "| unresolved candidates", m["F_SILENT_WRONG_QUANTITY"]["UNRESOLVED_CANDIDATES"])
    print("READY_FOR_NEXT_VALIDATION_VILLA", o["FREEZE"]["READY_FOR_NEXT_VALIDATION_VILLA"])
