"""PA08 Project-3 readiness gate v4: twelve executable conditions, each PASS / FAIL / NOT_TESTED with its evidence.

READY_FOR_CONTROLLED_DRAFT_ONLY requires every condition PASS.  A NOT_TESTED condition (no independent validation
executed yet) keeps the gate NOT_READY: that is the correct result, not a failure of the engine.  Even READY means
DRAFT BOQ + HUMAN REVIEW, never an automated quantity.
"""

from __future__ import annotations

CONDITIONS = [
    ("C01_NO_CRITICAL_SILENT_PATH", "no CRITICAL_SILENT finding open in the PA07R1 (or PA07R2) cold review"),
    ("C02_INDEPENDENT_VALIDATION_EXECUTED", "the independent blind validation was executed on an ACCEPTED source package"),
    ("C03_SILENT_WRONG_QUANTITY_ZERO", "SILENT_WRONG_QUANTITY_COUNT == 0 in the validation result"),
    ("C04_SPACE_COUNT_EXACT", "physical space count exact in every truth case (no falsely merged, no falsely split)"),
    ("C05_NO_ROLE_MISMATCH_FEEDS_A_QUANTITY", "no ROLE_MISMATCH row lies in a case whose space received a bridge-allowed quantity line"),
    ("C06_CURVED_PASSES_OR_REFUSES", "every curved fact is WITHIN_TOLERANCE, EXACT_MATCH or HUMAN_REVIEW_SAFE"),
    ("C07_COLUMN_PASSES_OR_REFUSES", "every column exposed-face fact is correct or HUMAN_REVIEW_SAFE"),
    ("C08_UNRESOLVED_TOPOLOGY_EMITS_NO_NUMBER", "no bridge-allowed line whose space is BOUNDARY_PROVISIONAL or whose boundary carries an unresolved site"),
    ("C09_UNITS_ESTABLISHED", "source units SOURCE_ESTABLISHED for the validation source"),
    ("C10_FILE_ACCESS_AUDIT_CLEAN", "the blind run opened only permitted files (no violation in BLIND_ACCESS_LOG)"),
    ("C11_TRUTH_SEALED_UNTIL_FREEZE", "the truth pack hash was recorded before the blind run and the blind output was frozen before the truth was opened"),
    ("C12_LEAKAGE_SCAN_CLEAN", "no P7757 / benchmark / contractor token in the generic engine (leakage scan)"),
]


def _cond(cid, status, evidence):
    desc = dict(CONDITIONS)[cid]
    return {"ID": cid, "CONDITION": desc, "STATUS": status, "EVIDENCE": evidence}


def evaluate(review=None, validation=None, acceptance=None, blind=None, truth_seal=None, leakage=None, blind_registers=None, dry_run=False):
    """Every input may be None (not available): the condition is then NOT_TESTED, never PASS by default."""
    out = []
    # C01
    if review is None:
        out.append(_cond("C01_NO_CRITICAL_SILENT_PATH", "NOT_TESTED", "no cold review record supplied"))
    else:
        crit = [f["FINDING_ID"] for f in review.get("FINDINGS", []) if f.get("SEVERITY") == "CRITICAL_SILENT" and f.get("STATUS", "OPEN") not in ("GUARDED_PA07R2", "FIXED_PA07R2", "CLOSED")]
        out.append(_cond("C01_NO_CRITICAL_SILENT_PATH", "PASS" if not crit else "FAIL", {"OPEN_CRITICAL_SILENT": crit, "REVIEW": review.get("ARTIFACT")}))
    # C02
    executed = validation is not None and validation.get("STATUS") == "EXECUTED" and acceptance is not None and acceptance.get("INDEPENDENT_VALIDATION_STATUS") == "ACCEPTED" and not dry_run
    if validation is None:
        out.append(_cond("C02_INDEPENDENT_VALIDATION_EXECUTED", "NOT_TESTED", "no validation result: no independent source package exists yet"))
    else:
        out.append(_cond("C02_INDEPENDENT_VALIDATION_EXECUTED", "PASS" if executed else "FAIL",
                         {"VALIDATION_STATUS": validation.get("STATUS"), "ACCEPTANCE": (acceptance or {}).get("INDEPENDENT_VALIDATION_STATUS"), "DRY_RUN": dry_run,
                          "NOTE": "a dry run on a synthetic villa is never independent validation" if dry_run else None}))
    m = (validation or {}).get("METRICS") or {}
    rows = (validation or {}).get("ROWS") or []
    if validation is None:
        for cid in ("C03_SILENT_WRONG_QUANTITY_ZERO", "C04_SPACE_COUNT_EXACT", "C05_NO_ROLE_MISMATCH_FEEDS_A_QUANTITY", "C06_CURVED_PASSES_OR_REFUSES", "C07_COLUMN_PASSES_OR_REFUSES", "C08_UNRESOLVED_TOPOLOGY_EMITS_NO_NUMBER"):
            out.append(_cond(cid, "NOT_TESTED", "no validation result"))
    else:
        swq = m.get("SILENT_WRONG_QUANTITY_COUNT")
        out.append(_cond("C03_SILENT_WRONG_QUANTITY_ZERO", "PASS" if swq == 0 else "FAIL", {"SILENT_WRONG_QUANTITY_COUNT": swq, "LINES": m.get("SILENT_WRONG_QUANTITY_LINES")}))
        sp_rows = [r for r in rows if r["FACT"] == "PHYSICAL_SPACE_COUNT"]
        bad = [r["CASE_ID"] for r in sp_rows if r["CLASS"] != "EXACT_MATCH"]
        out.append(_cond("C04_SPACE_COUNT_EXACT", "NOT_TESTED" if not sp_rows else ("PASS" if not bad else "FAIL"), {"CASES_NOT_EXACT": bad, "CASES_TESTED": len(sp_rows)}))
        role_cases = {r["CASE_ID"] for r in rows if r["CLASS"] == "ROLE_MISMATCH"}
        fed = sorted(role_cases & set((validation or {}).get("CRITICAL_MISMATCHES") or [])) if m.get("SILENT_WRONG_QUANTITY_COUNT") else []
        out.append(_cond("C05_NO_ROLE_MISMATCH_FEEDS_A_QUANTITY", "PASS" if not fed else "FAIL", {"ROLE_MISMATCH_CASES": sorted(role_cases), "FEEDING_A_QUANTITY": fed}))
        cur = [r for r in rows if r["FACT"] == "CURVED_SEGMENT"]
        badc = [r["ID"] for r in cur if r["CLASS"] not in ("WITHIN_TOLERANCE", "EXACT_MATCH", "HUMAN_REVIEW_SAFE")]
        out.append(_cond("C06_CURVED_PASSES_OR_REFUSES", "NOT_TESTED" if not cur else ("PASS" if not badc else "FAIL"), {"CURVED_FACTS": len(cur), "FAILING": badc}))
        col = [r for r in rows if r["FACT"] == "COLUMN"]
        badk = [r["ID"] for r in col if r["CLASS"] not in ("EXACT_MATCH", "WITHIN_TOLERANCE", "HUMAN_REVIEW_SAFE")]
        out.append(_cond("C07_COLUMN_PASSES_OR_REFUSES", "NOT_TESTED" if not col else ("PASS" if not badk else "FAIL"), {"COLUMN_FACTS": len(col), "FAILING": badk}))
        # C08 from the blind registers themselves
        if blind_registers is None:
            out.append(_cond("C08_UNRESOLVED_TOPOLOGY_EMITS_NO_NUMBER", "NOT_TESTED", "blind registers not supplied"))
        else:
            safety = blind_registers.get("PA07_QUANTITY_SAFETY_REGISTER", {}).get("ROWS", [])
            spaces = {s["SPACE_ID"]: s for s in blind_registers.get("PA07_PHYSICAL_SPACE_REGISTER", {}).get("ROWS", [])}
            leak = [r["SAFETY_ID"] for r in safety if r["BRIDGE_ALLOWED"] and (spaces.get(r["SPACE_ID"], {}).get("GEOMETRY_STATUS") != "ESTABLISHED" or spaces.get(r["SPACE_ID"], {}).get("UNRESOLVED_MM", 0) > 0)]
            out.append(_cond("C08_UNRESOLVED_TOPOLOGY_EMITS_NO_NUMBER", "PASS" if not leak else "FAIL", {"BRIDGE_ALLOWED": sum(1 for r in safety if r["BRIDGE_ALLOWED"]), "LEAKING": leak}))
    # C09
    if blind_registers is None:
        out.append(_cond("C09_UNITS_ESTABLISHED", "NOT_TESTED", "blind registers not supplied"))
    else:
        units = blind_registers.get("PA06_SOURCE_UNIT_REGISTER", {}).get("ROWS", [])
        st = [u["STATUS"] for u in units]
        out.append(_cond("C09_UNITS_ESTABLISHED", "PASS" if st and all(s == "SOURCE_ESTABLISHED" for s in st) else ("NOT_TESTED" if not st else "FAIL"), {"STATUSES": st}))
    # C10
    if blind is None:
        out.append(_cond("C10_FILE_ACCESS_AUDIT_CLEAN", "NOT_TESTED", "no blind run record"))
    else:
        v = blind.get("VIOLATIONS") or []
        out.append(_cond("C10_FILE_ACCESS_AUDIT_CLEAN", "PASS" if blind.get("STATUS") == "COMPLETED" and not v else "FAIL", {"STATUS": blind.get("STATUS"), "VIOLATIONS": v[:10], "FILES_OPENED": len(blind.get("FILES_OPENED") or [])}))
    # C11
    if truth_seal is None or blind is None:
        out.append(_cond("C11_TRUTH_SEALED_UNTIL_FREEZE", "NOT_TESTED", "no truth seal or no blind run"))
    else:
        ok = truth_seal.get("SEALED_BEFORE_BLIND_RUN") is True and bool(blind.get("FREEZE")) and blind.get("TRUTH_OPENED_BEFORE_FREEZE") is False and not any(
            "sealed" in str(p).lower() or "truth" in str(p).lower() for p in (blind.get("FILES_OPENED") or []))
        out.append(_cond("C11_TRUTH_SEALED_UNTIL_FREEZE", "PASS" if ok else "FAIL", {"TRUTH_SHA256": truth_seal.get("SHA256"), "BLIND_FREEZE_DIGEST": (blind.get("FREEZE") or {}).get("DIGEST")}))
    # C12
    if leakage is None:
        out.append(_cond("C12_LEAKAGE_SCAN_CLEAN", "NOT_TESTED", "no leakage scan supplied"))
    else:
        out.append(_cond("C12_LEAKAGE_SCAN_CLEAN", "PASS" if leakage.get("CLEAN") else "FAIL", {k: leakage.get(k) for k in ("CLEAN", "HITS", "FILES_SCANNED") if k in leakage}))
    statuses = [c["STATUS"] for c in out]
    ready = all(s == "PASS" for s in statuses)
    return {"ARTIFACT": "PA08_PROJECT_3_GATE_V4", "VERSION": "PA08-G4-1", "CONDITIONS": out,
            "COUNTS": {"PASS": statuses.count("PASS"), "FAIL": statuses.count("FAIL"), "NOT_TESTED": statuses.count("NOT_TESTED")},
            "READINESS": "READY_FOR_CONTROLLED_DRAFT_ONLY" if ready else "NOT_READY",
            "MEANING": "READY means a DRAFT BOQ with mandatory human review of every line, never an automated quantity; NOT_TESTED conditions keep the gate closed",
            "DRY_RUN": dry_run}
