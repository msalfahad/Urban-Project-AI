"""BOQ TRACEABILITY (M9 Phase 2B-3, ARCH_TAKEOFF_V2.5 only) - one chain per BOQ line:

    OWNER RULE -> DRAWING EVIDENCE -> MEASUREMENT FORMULA -> INDEPENDENT EXPECTED RESULT -> ENGINE RESULT -> BOQ LINE

    chain(lines, sheet, independent=None)  -> {"rows", "summary", "methods"}

Status of each line (never upgraded by a passing unit test alone):
    INDEPENDENTLY_VERIFIED     an independent expected value for THIS line (URBAN_INDEPENDENT_CHECKS_V1: a hand
                               calculation or an independently reviewed figure) agrees with the engine within its
                               tolerance
    FAILED_VALIDATION          an independent expected value for this line disagrees
    ENGINE_TESTED_ONLY         a measured quantity with no independent value for this line (its method may still be
                               proven on the proof library's cases: method_status says so)
    PROVISIONAL                the line is released as PROVISIONAL (an assumed value or a provisional geometry)
    BLOCKED_MISSING_EVIDENCE   no quantity (BLOCKED_RFI / BOUNDED_EXPOSURE / withheld)

method_status of an item code: INDEPENDENTLY_PROVEN_ON_CASES (the Phase 2B-3 proof cases that prove it, their hand
calculation and the independent reference calculator agreeing with the engine - tests/m9_p2b3 re-runs every listed
case) or ENGINE_TESTED_ONLY. Project-agnostic; stdlib only."""

from __future__ import annotations

POLICY_ID = "BOQ_TRACEABILITY_V1"
SCHEMA_CHECKS = "URBAN_INDEPENDENT_CHECKS_V1"
STATUSES = ("INDEPENDENTLY_VERIFIED", "ENGINE_TESTED_ONLY", "PROVISIONAL", "BLOCKED_MISSING_EVIDENCE",
            "FAILED_VALIDATION")
# (item code, physical element or None for every element) -> the proof cases (tests/m9_p2b3) that prove its
# measurement method; every case listed here is re-run by tests/m9_p2b3/test_p2b3_traceability.py, so the table cannot
# claim a proof that does not pass
METHOD_PROOFS = {
    ("FIN.WP.FLOOR", None): ("A net = the waterproofed floor polygon area",
                             ("WP-A", "WP-B", "WP-D", "WP-E", "WP-F", "WP-G")),
    ("FIN.WP.WALL_UPTURN", None): ("eligible boundary (walls, columns, sill walls) x upturn height",
                                   ("WP-A", "WP-B", "WP-S", "WP-D", "WP-E", "WP-F", "WP-G", "RS-02")),
    ("FIN.WP.DOORWAY", None): ("door width x wall depth (the doorway continuation)",
                               ("WP-B", "WP-D", "WP-E", "WP-G")),
    ("FIN.WP.DOORWAY_TRANSITION", None): ("the selected alternative of the project detail; withheld with its range "
                                          "without one", ("WP-B", "WP-BX")),
    ("FIN.WP.TERMINATION", None): ("edge length, by the termination detail", ("WP-F",)),
    ("FIN.WP.PENETRATION", None): ("drains / outlets / sleeves drawn inside the area",
                                   ("WP-C", "WP-CX", "WP-E", "WP-F")),
    ("DOOR.INTERNAL.PVC", None): ("one door set per physical door; CAD wall opening x height",
                                  ("DR-01", "DR-02", "DR-10")),
    ("DOOR.MAIN_ENTRANCE", None): ("one door set; CAD wall opening x height (2.50 m owner reference)", ("DR-09",)),
    ("FIN.PLASTER", "door jambs and head"): ("2 x wall t x door height (by category) + t x opening width",
                                             ("DR-09", "DR-10")),
}
MATERIAL_PROOFS = ("WP-A", "WP-B", "WP-S", "WP-C", "WP-CX", "WP-BX", "WP-LX", "WP-D", "WP-E", "WP-F", "WP-G", "WP-W",
                   "WP-H")
CSV_COLUMNS = ("line_id", "item_code", "floor", "room_id", "element", "unit", "owner_rule", "rule_set",
               "drawing_evidence", "evidence_state", "formula", "independent_expected", "independent_source",
               "engine_result", "difference", "status", "method_status", "proof_cases", "rules_sha256")


def _checks(independent):
    if not independent:
        return {}
    if independent.get("schema") != SCHEMA_CHECKS:
        raise ValueError(f"independent checks: schema must be {SCHEMA_CHECKS}")
    out = {}
    for c in independent.get("checks") or ():
        out[(c["room_id"], c["item_code"], c.get("element"))] = c
    return out


def chain(lines, sheet, independent=None):
    chk = _checks(independent)
    used = set()
    rows = []
    for ln in sorted(lines, key=lambda x: (x["location"].get("floor") or "", x["location"].get("room_id") or "",
                                           x["item_code"], x.get("physical_element") or "", x["line_id"])):
        code, loc = ln["item_code"], ln["location"]
        ev, net = ln["evidence_state"], ln.get("measured_net")
        mp = METHOD_PROOFS.get((code, ln.get("physical_element"))) or METHOD_PROOFS.get((code, None))
        key = next((k for k in ((loc.get("room_id"), code, ln.get("physical_element")),
                                (loc.get("room_id"), code, None)) if k in chk), None)
        c = chk.get(key) if key else None
        diff = None
        if net is None:
            status = "BLOCKED_MISSING_EVIDENCE"
        elif c is not None:
            used.add(key)
            diff = round(net - c["value"], 6)
            status = "INDEPENDENTLY_VERIFIED" if abs(diff) <= c.get("tolerance", 0.001) + 1e-9 else \
                "FAILED_VALIDATION"
        elif ev == "PROVISIONAL":
            status = "PROVISIONAL"
        else:
            status = "ENGINE_TESTED_ONLY"
        rule = ln.get("rule") or {}
        src = ln.get("source") or {}
        rows.append({"line_id": ln["line_id"], "item_code": code, "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element": ln.get("physical_element"), "unit": ln.get("unit"),
                     "owner_rule": f"{rule.get('rule_id')} {rule.get('version') or ''}".strip(),
                     "rule_set": rule.get("rule_set"),
                     "drawing_evidence": "; ".join(f"{d.get('file')} {str(d.get('sha256') or '')[:12]}"
                                                   for d in src.get("documents") or ()) + (
                         f" ({src.get('geometry_source')})" if src.get("geometry_source") else ""),
                     "evidence_state": ev, "formula": (ln.get("calculation") or {}).get("formula"),
                     "independent_expected": None if c is None else c["value"],
                     "independent_source": None if c is None else c.get("source"),
                     "engine_result": net, "difference": diff, "status": status,
                     "method_status": "INDEPENDENTLY_PROVEN_ON_CASES" if mp else "ENGINE_TESTED_ONLY",
                     "proof_cases": ", ".join(mp[1]) if mp else "",
                     "rules_sha256": sheet.get("rules_sha256")})
    unmatched = [{"room_id": k[0], "item_code": k[1], "element": k[2]} for k in chk if k not in used]
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in STATUSES}
    return {"policy": POLICY_ID, "statuses": list(STATUSES), "rows": rows,
            "summary": {"lines": len(rows), "by_status": counts,
                        "independent_checks": len(chk), "independent_checks_unmatched": len(unmatched),
                        "methods_proven_on_cases": sorted({r["item_code"] for r in rows
                                                           if r["method_status"] != "ENGINE_TESTED_ONLY"})},
            "unmatched_checks": unmatched,
            "methods": [{"item_code": k[0], "element": k[1], "formula": v[0], "proof_cases": list(v[1])}
                        for k, v in sorted(METHOD_PROOFS.items(), key=lambda x: (x[0][0], x[0][1] or ""))],
            "material_proof_cases": list(MATERIAL_PROOFS),
            "never": "a line marked INDEPENDENTLY_VERIFIED because its unit tests pass: only an independent value for "
                     "that line does it"}


def policy_record():
    return {"policy": POLICY_ID, "statuses": list(STATUSES), "checks_schema": SCHEMA_CHECKS,
            "methods": sorted(f"{k[0]} ({k[1] or 'every element'})" for k in METHOD_PROOFS)}
