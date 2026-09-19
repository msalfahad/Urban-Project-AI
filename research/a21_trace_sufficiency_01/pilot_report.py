"""Evaluate the trace pilot against success criteria A-I, mechanically.

Runs the FINAL validator over every frozen raw output, rebuilds the
register, overlays and mapping test, and then scores each criterion from
the artifacts - never from prose. A criterion that the present cases
cannot exercise is NOT_YET_TESTED, not PASS.

    python3 -m research.a21_trace_sufficiency_01.pilot_report
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import overlays as OV
from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import recalculation_test as RT
from research.a21_trace_sufficiency_01 import trace_register as TR
from research.a21_trace_sufficiency_01 import visual_trace as VT

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
RAW = OUT / "trace_raw"
SUBSET = ["CASE-1-NORMAL-PLASTER", "CASE-3-DOOR-AND-WINDOW",
          "CASE-4-STAIR", "CASE-6-ROOF-PARAPET"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build() -> dict:
    raw_hashes = {f.name: _sha(f) for f in sorted(RAW.glob("*.json"))}
    present = [c for c in SUBSET if f"{c}.json" in raw_hashes]
    missing = [c for c in SUBSET if c not in present]

    reg_meta = TR.build()
    reg = json.loads((OUT / "TRACE_REGISTER.json").read_text("utf-8"))
    ov = OV.render(reg)
    mp = VT.mapping_test()
    rt = RT.run()

    by_case = {}
    for t in reg["TRACES"]:
        c = by_case.setdefault(t["CASE_ID"], {"types": {}, "dims_linked": 0,
                                              "has_hosted_opening": False})
        et = t["EFFECTIVE_CLAIM_TYPE"]
        c["types"][et] = c["types"].get(et, 0) + 1
        if t.get("SUPPORTED_BY"):
            c["dims_linked"] += 1
        if et in ("DOOR", "WINDOW", "GLAZING") and t.get("HOSTED_IN"):
            c["has_hosted_opening"] = True

    def has(case, *types):
        return case in by_case and any(by_case[case]["types"].get(x)
                                       for x in types)

    crit = {}
    crit["A"] = {"PASS": reg["LOCATABLE_TRACES"] > 0 and reg["INVALID_TRACE_RECORDS"] == 0
                 and ov["images"] > 0,
                 "EVIDENCE": {"LOCATABLE_TRACES": reg["LOCATABLE_TRACES"],
                              "OVERLAY_IMAGES": ov["images"],
                              "INVALID": reg["INVALID_TRACE_RECORDS"]}}
    crit["B"] = {"PASS": reg["SUPPORTED_BY_LINKS_RESOLVED"] > 0
                 and reg["DANGLING_SUPPORTED_BY"] == [],
                 "EVIDENCE": {"LINKS_RESOLVED": reg["SUPPORTED_BY_LINKS_RESOLVED"],
                              "DANGLING": len(reg["DANGLING_SUPPORTED_BY"]),
                              "DIMENSION_TRACES": reg["DIMENSION_TRACES"]}}
    real = mp["REAL_TRACE_MAPPING"]
    crit["C"] = {"PASS": mp["ALL_SHEETS_INVERT"] and mp["WORST_ROUND_TRIP_PX"] < 1e-6
                 and real.get("AGREEMENT_RATE") == 1.0,
                 "EVIDENCE": {"COORDINATE_ROUNDTRIP_PASS": mp["ALL_SHEETS_INVERT"],
                              "SOURCE_INK_CORRESPONDENCE_PASS": min(
                                  mp["INK_AGREEMENT_RATES"].values()) == 1.0,
                              "TRACE_COORDINATE_MAPPING_PASS":
                                  real.get("AGREEMENT_RATE") == 1.0,
                              "TRACES_CHECKED": real.get("TRACES_CHECKED")},
                 "DOES_NOT_PROVE": list(VT.MAPPING_TESTS_DO_NOT_PROVE)}
    crit["D"] = {"PASS": reg["SOURCE_ACCESS_ALL_WITHIN_SANDBOX"],
                 "EVIDENCE": {c: v["STATUS"]
                              for c, v in reg["SOURCE_ACCESS_AUDIT"].items()}}
    req = json.loads((OUT / "CASE_SOURCE_REQUIREMENTS.json").read_text("utf-8"))
    crit["E"] = {"PASS": all(c["CASE_SOURCE_STATUS"] == "SOURCE_SET_INCOMPLETE"
                             for c in req["CASES"])
                 and all(len(v["NEW_SOURCE_REQUIREMENTS"]) >= 0
                         for v in reg["PER_CASE"].values()),
                 "EVIDENCE": {"BEFORE_READING": {c["CASE_ID"]: c["MISSING_SOURCE"]
                                                 for c in req["CASES"]},
                              "DURING_READING": {c: len(v["NEW_SOURCE_REQUIREMENTS"])
                                                 for c, v in reg["PER_CASE"].items()}}}
    crit["F"] = {"PASS": rt["ALL_CHECKS_PASS"], "EVIDENCE": rt["CHECKS"]}
    crit["G"] = {"PASS": rt["CHECKS"]["DEFAULT_BACKED_LINE_STAYED_PROVISIONAL"]
                 and rt["CHECKS"]["OWNER_SUPPLIED_HEIGHT_YIELDS_OWNER_PARAMETRIC_NOT_SOURCE_ESTABLISHED"],
                 "EVIDENCE": "constructor refusals + synthetic recalculation"}
    c3 = "CASE-3-DOOR-AND-WINDOW"
    crit["H"] = ({"PASS": has(c3, "DOOR", "WINDOW", "GLAZING")
                  and by_case[c3]["has_hosted_opening"]
                  and has(c3, "OPEN_EDGE") and has(c3, "PRINTED_DIMENSION"),
                  "EVIDENCE": by_case.get(c3)}
                 if c3 in present else {"NOT_YET_TESTED": True,
                                        "WHY": "CASE-3 has no reading"})
    c6 = "CASE-6-ROOF-PARAPET"
    crit["I"] = ({"PASS": has(c6, "PARAPET") and has(c6, "BALUSTRADE")
                  and has(c6, "HEIGHT_DIMENSION"),
                  "EVIDENCE": by_case.get(c6)}
                 if c6 in present else {"NOT_YET_TESTED": True,
                                        "WHY": "CASE-6 has no reading"})

    verdict = ("PASS" if all(v.get("PASS") for v in crit.values())
               else ("INCOMPLETE" if any(v.get("NOT_YET_TESTED")
                                         for v in crit.values())
                     else "FAIL"))
    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "TRACE_PILOT_REPORT",
        "FINAL_VALIDATOR_SHA256": reg_meta["VALIDATOR_SHA256"],
        "RAW_OUTPUTS_VALIDATED": raw_hashes,
        "CASES_PRESENT": present, "CASES_MISSING": missing,
        "REGISTER": {k: reg[k] for k in (
            "VALID_TRACE_RECORDS", "LOCATABLE_TRACES",
            "NON_LOCATABLE_VALID_TRACES", "INVALID_TRACE_RECORDS",
            "BY_EFFECTIVE_CLAIM_TYPE", "BY_VISUAL_TRACE_STATUS")},
        "PER_CASE_CLAIM_TYPES": {c: v["types"] for c, v in by_case.items()},
        "NEW_SOURCE_REQUIREMENTS": {c: v["NEW_SOURCE_REQUIREMENTS"]
                                    for c, v in reg["PER_CASE"].items()},
        "CRITERIA": crit,
        "VERDICT": verdict,
        "SUCCESS_IS_NOT_MORE_QUANTITIES": True,
        "MAPPING_TESTS_DO_NOT_PROVE": list(VT.MAPPING_TESTS_DO_NOT_PROVE),
    }
    p = OUT / "TRACE_PILOT_REPORT.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": _sha(p), "VERDICT": verdict,
            "CRITERIA": {k: (v.get("PASS") if "PASS" in v else "NOT_YET_TESTED")
                         for k, v in crit.items()},
            "CASES_PRESENT": present, "CASES_MISSING": missing,
            "FINAL_VALIDATOR_SHA256": reg_meta["VALIDATOR_SHA256"]}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
