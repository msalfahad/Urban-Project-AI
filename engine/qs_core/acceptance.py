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

    # A11 ------------------------------------------------------- the named source population is covered
    pop = doc.get("OPENING_POPULATION") or {}
    named = set(pop.get("NAMED_BY_THE_SOURCE") or [])
    rows = {c["CANDIDATE_REF"]: c for c in pop.get("POPULATION", [])}
    missing = sorted(named - set(rows))
    checks.append(_chk("A11", "every opening the source names appears in the published population",
                       bool(pop) and not missing,
                       {"NAMED_BY_THE_SOURCE": len(named), "IN_THE_POPULATION": len(rows),
                        "MISSING": missing},
                       "an object the drawing names individually cannot be absent from the register that "
                       "claims to be the population"))

    # A12 ------------------------------------------------------- nothing appears or disappears
    counts = pop.get("COUNTS") or {}
    total = sum(counts.values()) if counts else None
    conserved = bool(pop) and total == pop.get("CANDIDATES_IN") == len(rows)
    checks.append(_chk("A12", "admitted plus excluded plus unresolved equals the source population", conserved,
                       {"CANDIDATES_IN": pop.get("CANDIDATES_IN"), "SUM_OF_CLASSES": total,
                        "POPULATION_ROWS": len(rows), "COUNTS": counts},
                       "a classification that does not add up has either invented an object or lost one"))

    # A13 ------------------------------------------------------- a named door stays admitted
    physical = set(pop.get("PHYSICAL_OPENING_REFS") or [])
    dropped = []
    for ref in sorted(named - physical):
        row = rows.get(ref, {})
        cls = row.get("CLASSIFICATION")
        if cls in ("DUPLICATE_OF_CONFIRMED_OPENING", "OPENING_CANDIDATE_UNRESOLVED"):
            continue                       # a duplicate, or a contradiction the source itself creates
        dropped.append({"REF": ref, "CLASSIFICATION": cls, "EVIDENCE": row.get("EVIDENCE")})
    hosts = doc.get("HOST_REGISTER") or {}
    unresolved_hosts = set(hosts.get("HOST_UNRESOLVED_REFS") or [])
    retracted = sorted(unresolved_hosts - physical)
    checks.append(_chk("A13", "a named opening stays admitted even where its host is unresolved",
                       bool(pop) and not dropped and not retracted,
                       {"NAMED": len(named), "PHYSICAL": len(physical),
                        "HOST_UNRESOLVED": len(unresolved_hosts),
                        "DROPPED_WITHOUT_CONTRADICTORY_EVIDENCE": dropped,
                        "RETRACTED_BY_HOST_FAILURE": retracted},
                       "failing to work out which wall a door is in is not evidence that the door is not "
                       "there"))

    # A14 ------------------------------------------------------- height coverage over the whole population
    reg_rows = doc.get("OPENING_REGISTER_ROWS") or []
    relevant = [o for o in reg_rows if o.get("OPENING_REF") in physical] or reg_rows
    without = [{"OPENING_REF": o.get("OPENING_REF"),
                "HEIGHT_STATUS": ((o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE") or {}).get("STATUS",
                                                                                               "NO_RECORD")}
               for o in relevant
               if ((o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE") or {}).get("STATUS") != "ESTABLISHED"]
    # a document with no stated physical population cannot claim to have checked one
    checked_all = bool(pop) and bool(physical) and len(relevant) >= len(physical)
    checks.append(_chk("A14", "height evidence is examined across the whole physical population",
                       checked_all,
                       {"PHYSICAL_OPENINGS": len(physical), "ROWS_EXAMINED": len(relevant),
                        "WITHOUT_ESTABLISHED_HEIGHT": without},
                       "checking only the openings that survived to a deduction reports a coverage the run "
                       "did not achieve; an opening with no height is a question, and it has to be counted"))

    # A15 ------------------------------------------------------- superseded evidence never wins
    winners = []
    for o in reg_rows:
        adm = o.get("ADMISSION") or {}
        for what in ("WIDTH_EVIDENCE", "HEIGHT_EVIDENCE"):
            rec = adm.get(what) or {}
            if rec.get("STATUS") != "ESTABLISHED":
                continue
            chosen = rec.get("REFERENCE")
            for c in rec.get("CONSIDERED", []):
                if c.get("REFERENCE") == chosen and c.get("STATUS") in ("SUPERSEDED", "WITHDRAWN"):
                    winners.append({"OPENING_REF": o.get("OPENING_REF"), "WHAT": what,
                                    "REFERENCE": chosen, "STATUS": c.get("STATUS")})
    with_records = [o for o in reg_rows if (o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE")]
    checks.append(_chk("A15", "a superseded or withdrawn claim never resolves a dimension",
                       bool(with_records) and not winners,
                       {"ROWS_READ": len(reg_rows), "ROWS_CARRYING_EVIDENCE_RECORDS": len(with_records),
                        "OFFENDERS": winners},
                       "seniority is not eligibility: a value the project retired outranks the standard that "
                       "replaced it for ever, so rank alone will keep choosing it.  A document that carries "
                       "no lifecycle records cannot show that it respected them"))

    # A16 / A17 -------------------------------------------------- categories come from rooms, not defaults
    cat = doc.get("ROOM_CATEGORY_REGISTER") or {}
    cat_rows = cat.get("REGISTER") or []
    without_room = [r["OPENING_REF"] for r in cat_rows
                    if (r.get("CATEGORY") or {}).get("CATEGORY")
                    and not ((r.get("CATEGORY") or {}).get("ROOM") or {}).get("ROOM_ID")]
    no_categories_needed = bool(cat) and cat.get("OPENINGS") == 0
    checks.append(_chk("A16", "every resolved category carries the host-room evidence it came from",
                       bool(cat) and not without_room and (bool(cat_rows) or no_categories_needed),
                       {"ROWS": len(cat_rows), "RESOLVED": cat.get("CATEGORY_RESOLVED"),
                        "WITHOUT_HOST_ROOM": without_room},
                       "a category with no room behind it is a default, whatever it is called"))
    rooms = len(cat.get("DISTINCT_ROOMS") or [])
    distinct = cat.get("DISTINCT_CATEGORY_COUNT")
    defaulted = [r["OPENING_REF"] for r in cat_rows
                 if ((r.get("CATEGORY") or {}).get("SOURCE") or "").endswith("DEFAULT")]
    one_for_many = bool(cat_rows) and rooms > 1 and distinct == 1
    checks.append(_chk("A17", "rooms of different use do not all receive one unexplained category",
                       bool(cat) and not defaulted and not one_for_many,
                       {"DISTINCT_ROOMS": rooms, "DISTINCT_CATEGORIES": distinct,
                        "MARKED_AS_A_DEFAULT": defaulted},
                       "one category across many rooms is a project-wide default; the point of a category is "
                       "that it differs by use"))

    # A18 ------------------------------------------------------- material proof is independent of geometry
    ident_rows = doc.get("WALL_IDENTITY_REGISTER") or []
    bad_material = []
    for r in ident_rows:
        if r.get("MATERIAL_IDENTITY") in (None, "MATERIAL_UNKNOWN"):
            continue
        ev = r.get("MATERIAL_EVIDENCE") or {}
        if not ev.get("REFERENCE") or ev.get("EVIDENCE_SOURCE") not in (
                r.get("MATERIAL_EVIDENCE_SOURCES_ACCEPTED") or []):
            bad_material.append({"COMPONENT_REF": r.get("COMPONENT_REF"), "EVIDENCE": ev})
        if r.get("THICKNESS_FAMILY_PROVES_MATERIAL"):
            bad_material.append({"COMPONENT_REF": r.get("COMPONENT_REF"),
                                 "WHY": "a thickness family was treated as material evidence"})
    two_axes = all("GEOMETRY_IDENTITY" in r and "MATERIAL_IDENTITY" in r for r in ident_rows)
    checks.append(_chk("A18", "material identity is proved independently of wall geometry",
                       bool(ident_rows) and two_axes and not bad_material,
                       {"BANDS": len(ident_rows), "TWO_AXES_PRESENT": two_axes,
                        "OFFENDERS": bad_material},
                       "shape and repetition establish a wall; only a document can establish what it is "
                       "built from"))

    # A19 ------------------------------------------------------- questions are not double counted
    qs = doc.get("QUESTIONS") or {}
    roots = qs.get("ROOT_QUESTIONS") or []
    ids = [r["ROOT_QUESTION_ID"] for r in roots]
    duplicate_ids = sorted({i for i in ids if ids.count(i) > 1})
    orphans = qs.get("IMPACTS_WITHOUT_A_ROOT_QUESTION") or []
    subjects = [(r["KIND"], r["SUBJECT_REF"]) for r in roots]
    duplicate_subjects = sorted({s for s in subjects if subjects.count(s) > 1})
    checks.append(_chk("A19", "one unanswered fact is one root question, and impacts do not inflate the count",
                       bool(qs) and not duplicate_ids and not duplicate_subjects and not orphans,
                       {"ROOT_QUESTIONS": len(roots), "IMPACTS": qs.get("DEPENDENCY_IMPACT_COUNT"),
                        "DUPLICATE_IDS": duplicate_ids, "DUPLICATE_SUBJECTS": duplicate_subjects,
                        "IMPACTS_WITHOUT_A_ROOT": orphans},
                       "the same fact counted twice makes the source look worse than it is and the work list "
                       "impossible to close"))

    # A20 ------------------------------------------------------- the narrative agrees with the registers
    def _at(path):
        node = doc
        for part in path.split("."):
            if isinstance(node, list):
                try:
                    node = node[int(part)]
                    continue
                except (ValueError, IndexError):
                    return None
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    assertions = doc.get("NARRATIVE_ASSERTIONS") or []
    wrong = []
    for a in assertions:
        actual = _at(a.get("REGISTER_PATH", ""))
        if actual != a.get("VALUE"):
            wrong.append({"STATEMENT": a.get("STATEMENT"), "REGISTER_PATH": a.get("REGISTER_PATH"),
                          "SAID": a.get("VALUE"), "REGISTER_SAYS": actual})
    checks.append(_chk("A20", "every statement in the narrative is checkable against a register and agrees",
                       bool(assertions) and not wrong,
                       {"ASSERTIONS": len(assertions), "DISAGREEMENTS": wrong},
                       "a report that contradicts its own registers is the failure that made the last round "
                       "unusable, and it is the one thing no internal invariant can see"))

    # A21 ------------------------------------------------------- row status and line blocking say the same
    status = doc.get("WALL_LINE_STATUS") or {}
    blocked_lines = set(status.get("BLOCKED") or [])
    open_lines = set(status.get("NOT_BLOCKED") or [])
    wall_rows = doc.get("WALL_ROWS") or []
    contradictions = []
    for r in wall_rows:
        ref, st = r.get("COMPONENT_REF"), r.get("STATUS")
        if st == "BLOCKED_PENDING_ANSWERS" and ref not in blocked_lines:
            contradictions.append({"COMPONENT_REF": ref, "ROW_SAYS": st, "LINE_SAYS": "NOT_BLOCKED"})
        elif st == "FINAL_QUANTITY_AVAILABLE" and ref in blocked_lines:
            contradictions.append({"COMPONENT_REF": ref, "ROW_SAYS": st, "LINE_SAYS": "BLOCKED"})
    stated = ((doc.get("PUBLICATION") or {}).get("ROW_CATEGORIES") or {})
    counted = {"FINAL": sum(1 for r in wall_rows if r.get("STATUS") == "FINAL_QUANTITY_AVAILABLE"),
               "BLOCKED": sum(1 for r in wall_rows if r.get("STATUS") == "BLOCKED_PENDING_ANSWERS"),
               "EXCLUDED": sum(1 for r in wall_rows if r.get("STATUS") == "EXCLUDED_NOT_MASONRY"),
               "OF": len(wall_rows)}
    miscounted = {k: {"SAID": stated.get(k), "ROWS_SAY": v} for k, v in counted.items()
                  if stated.get(k) != v}
    checks.append(_chk("A21", "the row categories and the line blocking are the same statement twice",
                       bool(wall_rows) and bool(status) and not contradictions and not miscounted,
                       {"WALL_ROWS": len(wall_rows), "BLOCKED_LINES": len(blocked_lines),
                        "NOT_BLOCKED_LINES": len(open_lines), "STATED_CATEGORIES": stated or None,
                        "ROWS_SAY": counted, "CONTRADICTIONS": contradictions,
                        "MISCOUNTED": miscounted},
                       "a document that calls a line blocked in one table and released in another lets a "
                       "reader pick the number they prefer, and one of the two is always wrong"))

    # A22 ------------------------------------------------------- the derived registers describe one moment
    final = doc.get("FINAL_OPENING_STATE") or {}
    frozen = {r["OPENING_REF"]: r for r in final.get("OPENINGS", [])}
    reg_rows = doc.get("OPENING_REGISTER_ROWS") or []
    disagree = []
    for row in reg_rows:
        want = frozen.get(row.get("OPENING_REF"))
        if want is None:
            disagree.append({"OPENING_REF": row.get("OPENING_REF"), "WHY": "not in the final state"})
            continue
        for field in ("WIDTH_M", "HEIGHT_M", "AREA_M2"):
            a, b = want.get(field), row.get(field)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9):
                disagree.append({"OPENING_REF": row.get("OPENING_REF"), "FIELD": field,
                                 "FINAL_STATE": a, "REGISTER": b})
        wa = (want.get("WIDTH_EVIDENCE") or {}).get("REFERENCE")
        wb = ((row.get("ADMISSION") or {}).get("WIDTH_EVIDENCE") or {}).get("REFERENCE")
        ha = (want.get("HEIGHT_EVIDENCE") or {}).get("REFERENCE")
        hb = ((row.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE") or {}).get("REFERENCE")
        if (wa, ha) != (wb, hb):
            disagree.append({"OPENING_REF": row.get("OPENING_REF"), "FIELD": "SELECTED_EVIDENCE",
                             "FINAL_STATE": [wa, ha], "REGISTER": [wb, hb]})
    checks.append(_chk("A22", "every opening register agrees with the final evidence state",
                       bool(final) and bool(reg_rows) and not disagree,
                       {"HAS_FINAL_STATE": bool(final), "OPENINGS": len(frozen),
                        "REGISTER_ROWS": len(reg_rows), "DISAGREEMENTS": disagree},
                       "a register built before the last piece of evidence arrived describes an earlier "
                       "moment; two such registers side by side let a reader read a resolved height beside a "
                       "null area and a question asking for the height that was resolved"))

    # A23/A24 --------------------------------------------------- questions match the evidence, both ways
    qs = doc.get("QUESTIONS") or {}
    roots = qs.get("ROOT_QUESTIONS") or []
    height_qs = {r["SUBJECT_REF"]: 0 for r in roots if r.get("KIND") == "OPENING_HEIGHT_NOT_ESTABLISHED"}
    for r in roots:
        if r.get("KIND") == "OPENING_HEIGHT_NOT_ESTABLISHED":
            height_qs[r["SUBJECT_REF"]] += 1
    answered_but_asked, unanswered_but_silent, asked_twice = [], [], []
    for ref, row in sorted(frozen.items()):
        established = (row.get("HEIGHT_EVIDENCE") or {}).get("STATUS") == "ESTABLISHED"
        asked = height_qs.get(ref, 0)
        if established and asked:
            answered_but_asked.append({"OPENING_REF": ref,
                                       "HEIGHT": (row.get("HEIGHT_EVIDENCE") or {}).get("VALUE"),
                                       "ANSWERED_BY": (row.get("HEIGHT_EVIDENCE") or {}).get("REFERENCE")})
        if not established and row.get("HOST_ASSIGNMENT_STATUS") == "HOST_ASSIGNED" and asked == 0:
            unanswered_but_silent.append({"OPENING_REF": ref})
        if asked > 1:
            asked_twice.append({"OPENING_REF": ref, "QUESTIONS": asked})
    checks.append(_chk("A23", "an established dimension carries no question asking for it",
                       bool(frozen) and not answered_but_asked,
                       {"ESTABLISHED_HEIGHTS": sum(1 for r in frozen.values()
                                                   if (r.get("HEIGHT_EVIDENCE") or {}).get("STATUS")
                                                   == "ESTABLISHED"),
                        "ANSWERED_BUT_STILL_ASKED": answered_but_asked},
                       "a question may exist only while its fact is unanswered; a work list that asks for "
                       "answers it already holds cannot be closed"))
    checks.append(_chk("A24", "an unresolved required dimension carries exactly one question",
                       bool(frozen) and not unanswered_but_silent and not asked_twice,
                       {"UNANSWERED_AND_UNASKED": unanswered_but_silent, "ASKED_MORE_THAN_ONCE": asked_twice},
                       "a missing fact nobody asks about is a quantity published on nothing, and the same "
                       "fact asked twice is a work list that cannot be finished"))

    # A25 ------------------------------------------------------- one evidence version across the registers
    versions = doc.get("EVIDENCE_VERSIONS") or {}
    want_version = final.get("EVIDENCE_VERSION")
    mixed = {k: v for k, v in versions.items() if v != want_version}
    checks.append(_chk("A25", "every derived register records the evidence version it was built from",
                       bool(want_version) and bool(versions) and not mixed,
                       {"EVIDENCE_VERSION": want_version, "REGISTERS": versions, "MISMATCHED": mixed},
                       "the deduction, the dependency graph and the question register must be derived from "
                       "the same state, and must be able to prove it"))

    # A26 ------------------------------------------------------- impacts are a set
    seen = {}
    for i in qs.get("DEPENDENCY_IMPACTS", []):
        key = (i.get("ROOT_QUESTION_ID"), str(i.get("NODE")), i.get("NODE_KIND"), i.get("EFFECT"))
        seen[key] = seen.get(key, 0) + 1
    dupes = [{"KEY": list(k), "ROWS": n} for k, n in sorted(seen.items()) if n > 1]
    checks.append(_chk("A26", "dependency impacts are unique and idempotent",
                       "DEPENDENCY_IMPACTS" in qs and not dupes,
                       {"IMPACT_ROWS": len(qs.get("DEPENDENCY_IMPACTS", [])), "DISTINCT_EDGES": len(seen),
                        "DUPLICATES": dupes},
                       "an impact count inflated by the number of construction paths measures the graph "
                       "walk, not the work an answer would release"))

    # A27 ------------------------------------------------------- "releases" means no blocker remains
    blockers = doc.get("BLOCKER_SETS") or {}
    wrong_release = []
    for node, rec in sorted((blockers.get("NODES") or {}).items()):
        claimed = rec.get("ANSWER_ALONE_RELEASES_NODE")
        if claimed is not None and len(rec.get("BLOCKER_IDS") or []) != 1:
            wrong_release.append({"NODE": node, "CLAIMED": claimed,
                                  "BLOCKERS": rec.get("BLOCKER_IDS")})
    for qid, rec in sorted((blockers.get("BY_ROOT_QUESTION") or {}).items()):
        for node in rec.get("RELEASES_NODES", []):
            n = (blockers.get("NODES") or {}).get(node, {})
            if sorted(n.get("BLOCKER_IDS") or []) != [qid]:
                wrong_release.append({"NODE": node, "CLAIMED_BY": qid,
                                      "BLOCKERS": n.get("BLOCKER_IDS")})
    checks.append(_chk("A27", "a question is said to release a node only when nothing else blocks it",
                       bool(blockers) and not wrong_release,
                       {"NODES": len(blockers.get("NODES") or {}),
                        "RELEASED_BY_ONE_ANSWER": blockers.get("NODES_RELEASED_BY_ONE_ANSWER"),
                        "SEVERAL_BLOCKERS": blockers.get("NODES_WITH_SEVERAL_BLOCKERS"),
                        "OVERCLAIMED": wrong_release},
                       "removing one of three blockers releases nothing, and a report that calls it a "
                       "release promises work the answer will not deliver"))

    # A28 ------------------------------------------------------- material answers carry their own scope
    ident_rows = doc.get("WALL_IDENTITY_REGISTER") or []
    unscoped = [r for r in ident_rows
                if r.get("MATERIAL_IDENTITY") not in (None, "MATERIAL_UNKNOWN")
                and not (r.get("MATERIAL_EVIDENCE") or {}).get("REFERENCE")]
    no_scope_field = [r["COMPONENT_REF"] for r in ident_rows if not r.get("MATERIAL_SCOPE_KEY")]
    family_as_type = [r["COMPONENT_REF"] for r in ident_rows
                      if r.get("THICKNESS_FAMILY_PROVES_MATERIAL")]
    material_questions = [r for r in roots if r.get("KIND") == "WALL_MATERIAL_NOT_ESTABLISHED"]
    keyed_on_thickness_alone = [r["SUBJECT_REF"] for r in material_questions
                                if str(r.get("SUBJECT_REF", "")).startswith("THICKNESS_FAMILY::")]
    checks.append(_chk("A28", "a material answer applies only where its own scope says it does",
                       bool(ident_rows) and not unscoped and not no_scope_field
                       and not family_as_type and not keyed_on_thickness_alone,
                       {"BANDS": len(ident_rows), "MATERIAL_WITHOUT_A_DOCUMENT": len(unscoped),
                        "BANDS_WITHOUT_A_SCOPE_KEY": no_scope_field,
                        "THICKNESS_TREATED_AS_MATERIAL_PROOF": family_as_type,
                        "QUESTIONS_KEYED_ON_THICKNESS_ALONE": keyed_on_thickness_alone},
                       "walls of one thickness may be built of different things; grouping a question by "
                       "thickness is convenient, and treating the group as a wall type is an inference the "
                       "source has not made"))

    # A29 ------------------------------------------------------- weak evidence never excludes a quantity
    weak_exclusions = [{"COMPONENT_REF": r.get("COMPONENT_REF"), "REASON": r.get("GEOMETRY_ARTEFACT_REASON"),
                        "CONFIDENCE": r.get("GEOMETRY_CONFIDENCE"),
                        "ON_A_SOURCE_WALL_LAYER": r.get("ON_A_SOURCE_WALL_LAYER")}
                       for r in ident_rows
                       if r.get("GEOMETRY_IDENTITY") == "NON_WALL_ARTEFACT"
                       and r.get("GEOMETRY_CONFIDENCE") == "WEAK"]
    shape_only = [r.get("COMPONENT_REF") for r in ident_rows
                  if r.get("GEOMETRY_IDENTITY") == "NON_WALL_ARTEFACT"
                  and r.get("GEOMETRY_ARTEFACT_REASON") == "COLUMN_OR_STRUCTURE"
                  and not r.get("ANNOTATION") and r.get("GEOMETRY_CONFIDENCE") != "PROVEN"]
    checks.append(_chk("A29", "nothing leaves the trade on weak evidence or on its shape alone",
                       bool(ident_rows) and not weak_exclusions and not shape_only,
                       {"EXCLUDED": sum(1 for r in ident_rows
                                        if r.get("GEOMETRY_IDENTITY") == "NON_WALL_ARTEFACT"),
                        "EXCLUDED_ON_WEAK_EVIDENCE": weak_exclusions,
                        "EXCLUDED_AS_A_COLUMN_WITHOUT_THE_SOURCE_SAYING_SO": shape_only},
                       "an exclusion is permanent and silent, so it needs positive evidence: a pier, a wall "
                       "return and a jamb nib are all shorter than twice their thickness and all of them are "
                       "masonry"))

    # A30 ------------------------------------------------------- an open area is not a room
    cats = doc.get("ROOM_CATEGORY_REGISTER") or {}
    competing = []
    for row in cats.get("REGISTER", []):
        room = row.get("ROOM") or {}
        if room.get("STATUS") != "HOST_ROOM_AMBIGUOUS":
            continue
        roles = [c.get("ROLE") for c in room.get("CANDIDATES", []) if c.get("LABEL")]
        enclosed = [r for r in roles if r == "ENCLOSED_ROOM"]
        if len(enclosed) <= 1 and any(r == "EXTERNAL_OR_OPEN_AREA" for r in roles):
            competing.append({"OPENING_REF": row.get("OPENING_REF"), "ROLES": roles})
    checks.append(_chk("A30", "an external or open area never competes with a room for a room-use standard",
                       "REGISTER" in cats and not competing,
                       {"WINDOWS": len(cats.get("REGISTER", [])),
                        "AMBIGUOUS_BECAUSE_OF_AN_OPEN_AREA": competing},
                       "a window separates an occupied room from the outside; reading the standard off "
                       "whichever labelled polygon is nearer lets a roof terrace answer for a bedroom"))

    # A31 ------------------------------------------------------- every claim in the report is traceable
    claims = doc.get("REPORT_CLAIMS") or {}
    rows = claims.get("CLAIMS") or []
    unverified = [c for c in rows if c.get("VERIFIED") is not True]
    checks.append(_chk("A31", "every numerical or causal claim in the report is declared and traceable",
                       bool(rows) and not unverified,
                       {"DECLARED_CLAIMS": len(rows), "UNVERIFIED": unverified,
                        "WHAT_THIS_MEANS": claims.get("WHAT_THIS_CHECK_DOES_NOT_PROVE")},
                       "this proves that every DECLARED claim agrees with its register.  It does not prove "
                       "that the prose contains no undeclared claim, and must never be reported as if it did"))

    failed = [c for c in checks if c["RESULT"] == FAIL]
    return {"GATE": "QS_CORE_ACCEPTANCE", "CHECKS": checks, "PASSED": len(checks) - len(failed),
            "OF": len(checks), "ALL_PASS": not failed,
            "BLOCKERS": [{"CHECK": c["CHECK"], "TITLE": c["TITLE"], "WHY": c["WHY"], "FOUND": c["FOUND"]}
                         for c in failed],
            "READS": "only the published document; no access to the engine that produced it"}
