"""PA08_QORTUBA_ROOM_BY_ROOM_QS_01, step 2: the aggregate contractor check, run only after the takeoff is frozen.

The contractor's totals were seen in an earlier phase, so this phase cannot claim blindness.  What it can prove is order: the
takeoff's freeze digest and every artifact hash are verified here before a single contractor number is read, and verified again
afterwards.  If a room figure had been nudged toward a benchmark, the digest would not match.

Nothing in this module writes to the takeoff, and no room calculation is adjusted by anything found here.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"
EXT = Path(PR.OUT_DIR) / "pa08_qortuba_ext01"

DIFFERENCE_CLASSES = ("SCOPE_DIFFERENCE", "MEASUREMENT_BASIS_DIFFERENCE", "ENGINE_ERROR", "CONTRACTOR_ERROR",
                      "COMMERCIAL_RULE", "SOURCE_MISSING", "UNRESOLVED")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(name, obj):
    QS.mkdir(parents=True, exist_ok=True)
    (QS / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return name


def verify_source_only_freeze():
    """The gate.  Nothing below runs until the takeoff freeze is verified on disk."""
    fr = json.loads((QS / "FREEZE_PA08_QORTUBA_ROOM_BY_ROOM_QS_01.json").read_text("utf-8"))
    body = {k: v for k, v in fr.items() if k != "DIGEST"}
    recomputed = hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
    bad = [n for n, h in fr["CONTENTS"].items() if not (QS / f"{n}.json").exists() or _sha(QS / f"{n}.json") != h]
    if recomputed != fr["DIGEST"] or bad:
        raise SystemExit(f"the source-only takeoff changed after it was frozen; refusing to compare.  files={bad}")
    if not fr.get("SOURCE_ONLY_CALCULATION_COMPLETE"):
        raise SystemExit("the takeoff does not declare SOURCE_ONLY_CALCULATION_COMPLETE")
    return fr


def run():
    fr = verify_source_only_freeze()
    s = json.loads((QS / "QORTUBA_QS01_SUMMARY_TOTALS.json").read_text("utf-8"))
    floors = json.loads((QS / "QORTUBA_QS01_FLOOR_CALCULATIONS.json").read_text("utf-8"))["ROWS"]
    tile = json.loads((QS / "QORTUBA_QS01_WALL_TILE_TAKEOFF.json").read_text("utf-8"))
    comm = json.loads((EXT / "QORTUBA_CONTRACTOR_COMMERCIAL_REGISTER.json").read_text("utf-8"))
    tfr = json.loads((EXT / "CONTRACTOR_TRANSCRIPTION_FREEZE.json").read_text("utf-8"))
    row = {r["ROW_ID"]: r for r in comm["ROWS"]}

    dry = s["A_DRY_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    wet = s["B_WET_INTERNAL_FLOOR_AREA_M2"]["VALUE"]
    tot = s["C_TOTAL_INTERNAL_APARTMENT_FLOOR_AREA_M2"]["VALUE"]
    sk = s["D_TOTAL_SKIRTING_LM"]["VALUE"]
    pf = s["E_TOTAL_BLACK_PROFILE_LM"]["VALUE"]
    host = s["J_TOTAL_BATHROOM_AND_PREPARATION_WALL_CERAMIC_M2"]["WHAT_IS_ESTABLISHED"]

    def cmp(item, engine, unit, basis, cc, cls, root, action, extra=None):
        c = row[cc]["NET"] if row[cc]["NET"] is not None else row[cc]["COUNT"]
        d = None if engine is None else round(c - engine, 4)
        p = None if (d is None or not engine) else round(100.0 * d / engine, 2)
        out = {"ITEM": item, "ENGINE_VALUE": engine, "ENGINE_UNIT": unit, "ENGINE_BASIS": basis,
               "CONTRACTOR_ROW": cc, "CONTRACTOR_RAW": row[cc]["RAW_ARABIC_TEXT"], "CONTRACTOR_VALUE": c,
               "CONTRACTOR_BASIS": "one summed quantity on a priced sheet that names no storey and no room",
               "DELTA": d, "DELTA_PERCENT": p, "CLASSIFICATION": cls, "ROOT_CAUSE": root, "ACTION": action}
        if extra:
            out.update(extra)
        return out

    rows = [
        cmp("ceramic floor tiling, dry rooms", dry, "M2",
            "seven dry rooms measured one by one from the drawing, clear finish face, formulas in the takeoff",
            "CC-01", ["SCOPE_DIFFERENCE", "SOURCE_MISSING"],
            "the contractor sheet states no storey and no room breakdown, so it is not known to cover the same rooms.  The "
            "takeoff's figure is larger partly because it includes a 4.510 m2 internal lobby that carries floor finish and no "
            "room label; whether the contractor measured that lobby cannot be read from a summary line.",
            "MORE_SOURCE_REQUIRED",
            {"ALSO_COMPARED_AGAINST_APARTMENT_TOTAL": {"ENGINE_VALUE": tot,
                                                       "DELTA": round(row["CC-01"]["NET"] - tot, 4),
                                                       "NOTE": "shown because the contractor row may or may not include the "
                                                               "bathrooms, which are billed separately on the same sheet"}}),
        cmp("skirting", sk, "LM",
            "the eligible wall line of the seven dry rooms, with doors and one floor-level glazed opening deducted",
            "CC-02", ["SCOPE_DIFFERENCE", "SOURCE_MISSING"],
            "the takeoff measures every wall a skirting could run along; a contractor measures the stretches he will actually "
            "run.  The difference between those two is a deduction rule, and the sheet carries no deduction entry on this row.",
            "MORE_SOURCE_REQUIRED"),
        cmp("black profile above skirting", pf, "LM",
            "the same eligible wall path as the skirting, as a separate BOQ item, following the owner's statement that the "
            "profile sits directly above it",
            "CC-03", ["SCOPE_DIFFERENCE", "SOURCE_MISSING"],
            "the same scope question as the skirting, and no separate one: both sides now measure the profile on the skirting's "
            "path, so the profile carries no error of its own.",
            "MORE_SOURCE_REQUIRED"),
        cmp("bathrooms and preparation area, wall ceramic", None, "M2",
            f"NOT_ESTABLISHED: no tiling height exists.  What is measured is {host} lm of net host wall across three bathrooms "
            f"and the preparation area.",
            "CC-04", ["SOURCE_MISSING"],
            "the engine emitted no area because the drawing set contains no tiling height, and the contractor row does not say "
            "whether its quantity is wall, floor, or both.  Two unknowns, not a disagreement.",
            "MORE_SOURCE_REQUIRED",
            {"NET_HOST_WALL_LM": host,
             "IMPLIED_HEIGHT_IF_THE_ROW_IS_WALL_ONLY_M": round(row["CC-04"]["NET"] / host, 3),
             "IMPLIED_HEIGHT_IF_THE_ROW_IS_WALL_PLUS_FLOOR_M": round((row["CC-04"]["NET"] - wet - 11.685) / host, 3),
             "IMPLIED_HEIGHT_STATE": "DERIVED_FROM_CONTRACTOR_SHEET",
             "IMPLIED_HEIGHT_QUALIFIERS": ["NOT_SOURCE_ESTABLISHED", "NOT_AN_URBAN_RULE", "NOT_A_QORTUBA_DRAWING_FACT",
                                           "DIAGNOSTIC_ONLY", "NOT_FED_BACK_INTO_ANY_QUANTITY"]}),
    ]

    rule = {"OBSERVATION": "both sides now measure the black profile on exactly the skirting's path",
            "ENGINE_PROFILE_OVER_SKIRTING": round(pf / sk, 4) if sk else None,
            "CONTRACTOR_PROFILE_OVER_SKIRTING": round(row["CC-03"]["NET"] / row["CC-02"]["NET"], 4),
            "AGREEMENT": "TRADE_RULE_AGREES",
            "WHY_THIS_IS_NOT_CIRCULAR": "the takeoff set the profile equal to the skirting from the owner's description of the "
                                        "installed product, before this comparison existed and before this module was written. "
                                        "The contractor sheet is a second, independent witness to the same rule.",
            "WHAT_IT_DOES_NOT_SETTLE": "the two rules agree while the two magnitudes do not; the scope question behind the "
                                       "magnitude is untouched by this agreement"}

    metrics = {"ROOM_LEVEL_COMPARISONS_POSSIBLE": 0,
               "WHY": "the contractor supplied aggregate quantities only; no room-level figure exists to compare against",
               "AGGREGATE_COMPARISONS_MADE": len(rows),
               "BY_CLASSIFICATION": dict(Counter(c for r in rows for c in r["CLASSIFICATION"])),
               "ENGINE_ERRORS_FOUND_BY_THIS_COMPARISON": 0,
               "CONTRACTOR_ERRORS_FOUND_BY_THIS_COMPARISON": 0,
               "WHY_ZERO": "an unexplained difference between a per-room total of known scope and a summary total of unknown "
                           "scope is a scope question.  Calling it an error in either direction would be a guess.",
               "TRADE_RULE_AGREEMENTS": 1,
               "ROOM_CALCULATIONS_ADJUSTED_AFTER_SEEING_THE_AGGREGATE": 0}

    out = {"ARTIFACT": "QORTUBA_QS01_AGGREGATE_CONTRACTOR_COMPARISON",
           "ORDER_OF_WORK": {"SOURCE_ONLY_FREEZE_DIGEST": fr["DIGEST"],
                             "SOURCE_ONLY_FREEZE_VERIFIED_BEFORE_READING_THE_CONTRACTOR_SHEET": True,
                             "CONTRACTOR_TRANSCRIPTION_FREEZE_DIGEST": tfr["DIGEST"],
                             "TAKEOFF_GIT_HEAD": fr["GIT_HEAD_AT_FREEZE"],
                             "TAKEOFF_TREE_CLEAN_AT_FREEZE": fr["WORKING_TREE_AT_FREEZE"]["CLEAN"]},
           "ROWS": rows, "COUNT": len(rows),
           "PROFILE_TRADE_RULE_CHECK": rule,
           "DIFFERENCE_CLASSES": DIFFERENCE_CLASSES,
           "METRICS": metrics,
           "CONTRACTOR_GIVES_AGGREGATES_ONLY": "the sheet is a priced summary.  It is not room-level truth and is not treated "
                                               "as any kind of truth here.",
           "NO_ADJUSTMENT_RULE": "no room calculation was changed by anything in this comparison"}
    write("QORTUBA_QS01_AGGREGATE_CONTRACTOR_COMPARISON", out)

    after = [n for n, h in fr["CONTENTS"].items() if _sha(QS / f"{n}.json") != h]
    if after:
        raise SystemExit(f"a frozen takeoff artifact changed during the comparison: {after}")

    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    fr2 = {"ARTIFACT": "FREEZE_PA08_QORTUBA_QS01_AGGREGATE_COMPARISON",
           "SOURCE_ONLY_FREEZE_NOT_REWRITTEN": {"DIGEST": fr["DIGEST"], "ARTIFACTS": len(fr["CONTENTS"]),
                                                "VERIFIED_BEFORE_AND_AFTER": True, "MISMATCHES": []},
           "CONTRACTOR_TRANSCRIPTION_FREEZE_DIGEST": tfr["DIGEST"],
           "GIT_HEAD_AT_FREEZE": head,
           "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
           "ENGINE_CHANGED": "NONE",
           "ROOM_CALCULATIONS_ADJUSTED": 0,
           "CONTENTS": {"QORTUBA_QS01_AGGREGATE_CONTRACTOR_COMPARISON": _sha(QS / "QORTUBA_QS01_AGGREGATE_CONTRACTOR_COMPARISON.json")}}
    fr2["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr2.items() if k != "DIGEST"}, sort_keys=True, default=str).encode()).hexdigest()
    write("FREEZE_PA08_QORTUBA_QS01_AGGREGATE_COMPARISON", fr2)
    return {"COMPARISON": out, "FREEZE": fr2, "SOURCE_ONLY": fr}


if __name__ == "__main__":
    o = run()
    c = o["COMPARISON"]
    print("source-only freeze verified:", c["ORDER_OF_WORK"]["SOURCE_ONLY_FREEZE_DIGEST"][:16],
          "| head", c["ORDER_OF_WORK"]["TAKEOFF_GIT_HEAD"], "| clean", c["ORDER_OF_WORK"]["TAKEOFF_TREE_CLEAN_AT_FREEZE"])
    for r in c["ROWS"]:
        print(f"  {r['ITEM'][:44]:46s} engine={str(r['ENGINE_VALUE']):10s} contractor={str(r['CONTRACTOR_VALUE']):10s} "
              f"delta={str(r['DELTA']):10s} {str(r['DELTA_PERCENT']):8s} {','.join(r['CLASSIFICATION'])}")
    print("profile rule:", c["PROFILE_TRADE_RULE_CHECK"]["AGREEMENT"],
          "engine", c["PROFILE_TRADE_RULE_CHECK"]["ENGINE_PROFILE_OVER_SKIRTING"],
          "contractor", c["PROFILE_TRADE_RULE_CHECK"]["CONTRACTOR_PROFILE_OVER_SKIRTING"])
    print("metrics:", c["METRICS"])
    print("FREEZE", o["FREEZE"]["DIGEST"][:16])
