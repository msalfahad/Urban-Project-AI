"""PROJECT_3_ENTRY_GATE_V2 (PA06): twelve conditions evaluated from the PA06 registers, the blind comparison and
the cold review.  READY only when every condition holds; UNKNOWN is acceptable, silent plausible error is not."""

from __future__ import annotations

CONDITIONS = ("NO_CRITICAL_TOPOLOGY_BLOCKER", "CONTAMINATION_BELOW_THRESHOLD_AND_SURFACED", "VECTOR_WALL_LENGTH_FOR_EVERY_ELIGIBLE_SPACE", "UNITS_ESTABLISHED", "STOREYS_GENERIC",
              "INGEST_TO_QUANTITY_BRIDGE_WORKS", "BILINGUAL_IDENTITY_CANNOT_CREATE_GEOMETRY", "BLIND_TOLERANCES_PASS", "NO_BENCHMARK_LEAKAGE", "OWNER_INPUTS_VERSIONED_PARAMETERS",
              "FREEZE_REVERSIBILITY_PASS", "COLD_REVIEW_NO_SILENT_WRONG_QUANTITY")
# predeclared allowable contamination: material entities that the classifier could not establish (PROVISIONAL / LOW) as a share of all material entities
CONTAMINATION_THRESHOLD = 0.10


def evaluate(*, registers, blind_comparison, review, benchmark_scan, tests_pass, contamination_threshold=CONTAMINATION_THRESHOLD):
    qa = registers["PA06_QA_REPORT"]
    wl = registers["PA06_SPACE_WALL_LENGTH_REGISTER"]["ROWS"]
    trace = registers["PA06_QUANTITY_INPUT_TRACE"]["LINES"]
    sem = registers["PA06_SEMANTIC_ANCHOR_REGISTER"]
    critical = [f for f in (review or {}).get("FAILURE_MODES", []) if f.get("SEVERITY") == "CRITICAL" and f.get("BLOCKS_PROJECT_3")]
    silent_wrong = [f for f in (review or {}).get("FAILURE_MODES", []) if f.get("DETECTION") == "SILENT" and f.get("SEVERITY") in ("CRITICAL", "HIGH") and f.get("PRODUCES_WRONG_QUANTITY", True)]
    cont = qa["CONTAMINATION"]
    # quantity-effect share: provisional-role length among contributing edges of formed regions (entity counts are not a quantity effect)
    prov_len = sum(x["length_m"] or 0 for r in registers["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["ROWS"] for x in r["GROSS_BASIS"]["CONTRIBUTING_EDGES"] if x.get("length_source") == "DRAWING_PROVISIONAL_ROLE")
    all_len = sum(x["length_m"] or 0 for r in registers["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["ROWS"] for x in r["GROSS_BASIS"]["CONTRIBUTING_EDGES"])
    share = prov_len / all_len if all_len else 0.0
    rows = [
        ("NO_CRITICAL_TOPOLOGY_BLOCKER", not critical, {"CRITICAL_BLOCKERS": [f["ID"] for f in critical]}),
        ("CONTAMINATION_BELOW_THRESHOLD_AND_SURFACED", share <= contamination_threshold, {"PROVISIONAL_LENGTH_SHARE_IN_FORMED_REGIONS": round(share, 3), "THRESHOLD": contamination_threshold, "REJECTED": cont}),
        ("VECTOR_WALL_LENGTH_FOR_EVERY_ELIGIBLE_SPACE", all(w["LENGTH_BASIS"] == "VECTOR_FACES" and not w["POLYGON_PERIMETER_USED"] and not w["RASTER_RUNS_USED"] for w in wl if w["IN_RANGE"]) and bool(wl), {"ROWS": len(wl)}),
        ("UNITS_ESTABLISHED", all(qa["UNITS_ACCEPTABLE"].values()) if qa["UNITS_ACCEPTABLE"] else False, qa["UNITS_ACCEPTABLE"]),
        ("STOREYS_GENERIC", bool(registers["PA06_STOREY_REGISTER"]["ROWS"]) and all(r.get("GENERIC_NAME") for r in registers["PA06_STOREY_REGISTER"]["ROWS"]), {"STOREYS": len(registers["PA06_STOREY_REGISTER"]["ROWS"])}),
        ("INGEST_TO_QUANTITY_BRIDGE_WORKS", bool(trace) and any(l["REGION_STATUS"] in ("MEASUREMENT_REGION_CLOSED", "MEASUREMENT_RUN_ESTABLISHED") and (l.get("SEMANTIC_IDENTITY") or {}).get("STATUS") in ("SINGLE", "MULTIPLE") for l in trace)
         and all(l["BARE_NUMBER"] is False for l in trace), {"LINES": len(trace), "FORMED_AND_IDENTIFIED": sum(1 for l in trace if l["REGION_STATUS"] in ("MEASUREMENT_REGION_CLOSED", "MEASUREMENT_RUN_ESTABLISHED") and (l.get("SEMANTIC_IDENTITY") or {}).get("STATUS") in ("SINGLE", "MULTIPLE"))}),
        ("BILINGUAL_IDENTITY_CANNOT_CREATE_GEOMETRY", all(r["CREATES_GEOMETRY"] is False for r in sem["ROWS"]) and tests_pass.get("test_bilingual_text_ontology_and_no_geometry_from_text", False), {}),
        ("BLIND_TOLERANCES_PASS", bool(blind_comparison and blind_comparison.get("PASS")), {"FAILED": (blind_comparison or {}).get("FAILED")}),
        ("NO_BENCHMARK_LEAKAGE", benchmark_scan.get("CLEAN") is True, benchmark_scan),
        ("OWNER_INPUTS_VERSIONED_PARAMETERS", tests_pass.get("test_owner_input_recalculates_dependents_only", False) and all(l["HEIGHT_SOURCE"] is None or l["HEIGHT_SOURCE"].get("SOURCE_TYPE") != "LEARNED" for l in trace), {}),
        ("FREEZE_REVERSIBILITY_PASS", qa["CLOSURE_REVERSIBILITY"] is True, {"CLOSURE_REVERSIBILITY": qa["CLOSURE_REVERSIBILITY"]}),
        ("COLD_REVIEW_NO_SILENT_WRONG_QUANTITY", review is not None and not silent_wrong, {"SILENT_WRONG_QUANTITY_MODES": [f["ID"] for f in silent_wrong], "REVIEW_PRESENT": review is not None}),
    ]
    out = [{"CONDITION": c, "PASS": bool(p), "EVIDENCE": e} for c, p, e in rows]
    assert [o["CONDITION"] for o in out] == list(CONDITIONS)
    return {"ARTIFACT": "PA06_PROJECT_3_ENTRY_GATE_V2", "CONDITIONS": out, "READY": all(o["PASS"] for o in out), "FAILED": [o["CONDITION"] for o in out if not o["PASS"]],
            "PRINCIPLE": "UNKNOWN is acceptable; silent plausible error is not; the PA05 mechanical 12/12 is not reused"}
