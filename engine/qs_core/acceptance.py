"""An acceptance gate that reads the published document, not the engine that produced it.

Most of the invariants compare one engine structure against another engine structure.  That establishes internal
consistency - the wall rows agree with the register the wall rows were built from - and internal consistency is
exactly what a confidently wrong engine has.  This gate is written from the other side: it is handed a published
output and asked whether that output is fit to be read as quantities, with no access to the code that made it.

It is deliberately capable of rejecting the output this engine produced before this round; a gate that only ever
passes the current build proves nothing about the current build.
"""

from __future__ import annotations

PASS, FAIL = "PASS", "FAIL"


def _chk(code, title, ok, found, why):
    return {"CHECK": code, "TITLE": title, "RESULT": PASS if ok else FAIL, "FOUND": found, "WHY": why}


def grade(doc):
    """Grade one published document.  `doc` is the output, in the shape the publisher wrote it."""
    checks = []

    # A1 -------------------------------------------------------- blocked quantities excluded from totals
    rows = doc.get("WALL_ROWS") or []
    blocked = [r for r in rows if r.get("STATUS") != "FINAL_QUANTITY_AVAILABLE"]
    published = []
    pub = doc.get("PUBLICATION")
    if pub:
        for key, sub in pub.get("SUBTOTALS", {}).items():
            if sub.get("FINAL_QUANTITY") is not None:
                published.append({"SUBTOTAL": key, "QUANTITY": sub["FINAL_QUANTITY"],
                                  "ROWS_BLOCKED": sub.get("ROWS_BLOCKED", 0)})
    for q in doc.get("PUBLISHED_QUANTITIES") or []:
        published.append({"SUBTOTAL": q.get("REF"), "QUANTITY": q.get("QUANTITY"),
                          "ROWS_BLOCKED": q.get("ROWS_BLOCKED")})
    bad = [p for p in published if p["QUANTITY"] is not None and (p.get("ROWS_BLOCKED") or 0) > 0]
    if published and blocked and not pub:
        bad = bad or [{"SUBTOTAL": p["SUBTOTAL"], "QUANTITY": p["QUANTITY"],
                       "ROWS_BLOCKED": len(blocked),
                       "WHY": "quantities were published beside rows that are all blocked, with no per-subtotal "
                              "record of which rows fed them"} for p in published if p["QUANTITY"]]
    checks.append(_chk("A1", "blocked quantities are excluded from published totals", not bad,
                       {"PUBLISHED_SUBTOTALS": len(published), "BLOCKED_ROWS": len(blocked),
                        "OFFENDERS": bad},
                       "a subtotal may be a number only when every row behind it is final"))

    # A2 -------------------------------------------------------- opening population normalisation
    pop = doc.get("OPENING_POPULATION")
    ok = bool(pop) and pop.get("CANDIDATES_IN") == len(pop.get("POPULATION", [])) \
        and all(c.get("CLASSIFICATION") for c in pop.get("POPULATION", []))
    checks.append(_chk("A2", "every opening candidate is classified before host assignment", ok,
                       {"HAS_POPULATION": bool(pop),
                        "CANDIDATES_IN": (pop or {}).get("CANDIDATES_IN"),
                        "CLASSIFIED": sum(1 for c in (pop or {}).get("POPULATION", [])
                                          if c.get("CLASSIFICATION")),
                        "COUNTS": (pop or {}).get("COUNTS")},
                       "geometry, the drawing register and the schedule must be normalised to one physical "
                       "population, with every candidate carrying a classification and its provenance"))

    # A3 -------------------------------------------------------- noise is rejected, and only on evidence
    noise_bad = []
    for c in (pop or {}).get("POPULATION", []):
        res = (pop or {}).get("DRAFTING_RESOLUTION_M")
        if res is None:
            continue
        if c.get("DRAWN_WIDTH_M") is not None and c["DRAWN_WIDTH_M"] < res \
                and c.get("CLASSIFICATION") == "CONFIRMED_OPENING":
            noise_bad.append(c["CANDIDATE_REF"])
    checks.append(_chk("A3", "a candidate below the source's drafting resolution is never confirmed",
                       bool(pop) and not noise_bad,
                       {"DRAFTING_RESOLUTION_M": (pop or {}).get("DRAFTING_RESOLUTION_M"),
                        "CONFIRMED_BELOW_RESOLUTION": noise_bad,
                        "NOISE_REJECTED": (pop or {}).get("COUNTS", {}).get("DRAWING_NOISE")},
                       "a drafting gap must not become a deduction, and a narrow opening that the source "
                       "vouches for must not be deleted"))

    # A4 -------------------------------------------------------- continuity is proved, not permitted
    gaps = doc.get("GAP_LOG")
    proofs = {"BRIDGED_BY_A_CONFIRMED_OPENING", "BRIDGED_BY_CONTINUATION_GEOMETRY",
              "BRIDGED_BY_DECLARED_CAD_CONTINUITY"}
    unproved = [g for g in (gaps or []) if g.get("BRIDGED") and g.get("RELATION") not in proofs]
    checks.append(_chk("A4", "a wall is continued across a gap only where something spans it",
                       gaps is not None and not unproved,
                       {"HAS_GAP_LOG": gaps is not None, "GAPS": len(gaps or []),
                        "BRIDGED_WITHOUT_EVIDENCE": unproved},
                       "a maximum opening span may reject a join; it may not prove one"))

    # A5 -------------------------------------------------------- the basis is per wall line
    basis = doc.get("OPENING_BASIS")
    per_line = bool(basis) and all(b.get("BASIS") for b in basis.values())
    global_boolean = doc.get("WALL_GEOMETRY_INCLUDES_OPENINGS")
    checks.append(_chk("A5", "opening inclusion is evidenced per wall line, not asserted for the source",
                       per_line and global_boolean is None,
                       {"HAS_PER_LINE_BASIS": bool(basis), "LINES_WITH_A_BASIS": len(basis or {}),
                        "BASES": sorted({b.get("BASIS") for b in (basis or {}).values()}),
                        "SOURCE_WIDE_BOOLEAN": global_boolean},
                       "one Boolean for a whole revision is an assumption about a mixed population"))

    # A6 -------------------------------------------------------- thickness is not identity
    ident = doc.get("WALL_IDENTITY")
    ident_by_ref = {r["COMPONENT_REF"]: r for r in (ident or {}).get("REGISTER", [])}
    billed_without_identity = []
    for r in rows:
        if r.get("STATUS") != "FINAL_QUANTITY_AVAILABLE":
            continue
        i = ident_by_ref.get(r.get("COMPONENT_REF"))
        if i is None or not i.get("BILLABLE_AS_MASONRY"):
            billed_without_identity.append(r.get("COMPONENT_REF"))
    checks.append(_chk("A6", "an atypical band is not billed merely because it has a thickness",
                       ident is not None and not billed_without_identity,
                       {"HAS_IDENTITY_REGISTER": ident is not None,
                        "IDENTITY_COUNTS": (ident or {}).get("COUNTS"),
                        "BILLED_WITHOUT_ESTABLISHED_IDENTITY": billed_without_identity},
                       "a measurable thickness is a measurement, not an identity"))

    # A7 -------------------------------------------------------- height provenance on every deduction
    missing = []
    for o in doc.get("OPENING_REGISTER_ROWS") or []:
        if o.get("AREA_M2") is None:
            continue
        adm = o.get("ADMISSION") or {}
        h = adm.get("HEIGHT_EVIDENCE") or {}
        if h.get("STATUS") != "ESTABLISHED":
            missing.append({"OPENING_REF": o.get("OPENING_REF"),
                            "HEIGHT_SOURCE": o.get("HEIGHT_SOURCE"),
                            "HEIGHT_STATUS": h.get("STATUS", "NO_RECORD")})
    checks.append(_chk("A7", "every deducted opening carries established height evidence", not missing,
                       {"DEDUCTED_OPENINGS": sum(1 for o in doc.get("OPENING_REGISTER_ROWS") or []
                                                 if o.get("AREA_M2") is not None),
                        "WITHOUT_HEIGHT_EVIDENCE": missing},
                       "an area deducted from a wall is two facts; a height nobody established is not one"))

    # A8-A10 ---------------------------------------------------- the metamorphic results
    meta = doc.get("METAMORPHIC") or {}
    for code, key, title in (("A8", "RIGID_MOTION", "quantities are invariant under translation and rotation"),
                             ("A9", "SEGMENTATION", "quantities are invariant under how the source is cut up"),
                             ("A10", "REPRESENTATION",
                              "equivalent CAD representations produce equivalent quantities")):
        rec = meta.get(key)
        checks.append(_chk(code, title, bool(rec) and rec.get("EQUIVALENT") is True,
                           {"RECORD": rec},
                           "the same building, described differently, has to measure the same; a result that "
                           "moves is a result that depends on the description"))

    failed = [c for c in checks if c["RESULT"] == FAIL]
    return {"GATE": "QS_CORE_ACCEPTANCE", "CHECKS": checks, "PASSED": len(checks) - len(failed),
            "OF": len(checks), "ALL_PASS": not failed,
            "BLOCKERS": [{"CHECK": c["CHECK"], "TITLE": c["TITLE"], "WHY": c["WHY"], "FOUND": c["FOUND"]}
                         for c in failed],
            "READS": "only the published document; no access to the engine that produced it"}
