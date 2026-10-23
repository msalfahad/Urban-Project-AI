"""ARCH_TAKEOFF_V3.0.6 (T-187): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.5 (engine.source.arch_v30,
arch_v301 .. arch_v305), extended with (1) the default guard (engine.source.default_guard, T-186) run over every
candidate line and (2) the checker-merged stair concrete ledger of a storey the route folds away. Not a new method
family and not the released default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the
released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.6`):
  1. the run is the V3.0.5 candidate exactly: its V3_0_* .. V3_0_5_* files are written unchanged (arch_v30 .. arch_v305
     are not edited);
  2. STAIR LEDGER (piece STAIR_CONCRETE): the project inputs name one checker-merged ledger (file sha256, task, merge
     commit, checker run) with one record per stair piece (RELEASED / HELD_RANGE / HELD_DEFINED / UNQUANTIFIED, as
     V3.0.5). Before a line is ADDED, every candidate line of the same item code and physical element on a floor of the
     scope must be accounted for: superseded by name (scope.supersede_lines: the same physical element), declared as
     another physical element of the same item (scope.other_elements: kept as it is), or shown by the drawing NOT to
     be this item at all (scope.misread_lines: e.g. dome ribs read as a winder stair; HELD, BLOCKED_RFI, its figure
     kept as information, never summed, never 0), each with its reason. An unaccounted line refuses the run (T-179
     lesson: an integration that only adds is refused when the element may already be carried). Each record names
     the register element and part it carries (guard_element), so the guard sees that part as carried;
  3. DEFAULT GUARD (piece DEFAULT_GUARD): the merged guard runs over the V3.0.5 lines + the added ledger lines with the
     project's guard evidence (document register, printed records, drawn inventory, engine element -> register element
     mapping, plus the mapping_additions of the inputs for engine element ids the evidence file does not know, each
     with its reason) and the convention set the route ran on (file and sha256 named in the inputs). The inputs say which
     checks HOLD and which are only RECORDED:
       a LIVE line (a quantity) with a finding of a holding check -> BLOCKED_RFI; its figure, every finding and every
                                         printed value it cites kept in its inputs as information (never summed,
                                         never 0); its RFI names the findings; a line an earlier version changed is
                                         held the same way and says so;
       a line that carries no quantity (held range, blocked, superseded, excluded) -> listed with its findings, never
                                         re-held;
       a finding of a recorded-only check -> listed per line in the run file, the line is not changed;
       with "equal_value_rebase" in the inputs: a CONVENTION_WHERE_PRINTED finding whose printed structural value(s)
                                         EQUAL the convention value the line used (the quantity already rests on the
                                         printed number) is listed as REBASED_ON_PRINTED with its citation, not held;
                                         any other finding on the line still holds it;
       SILENT_OMISSION (a drawn element part no line carries) -> one HELD placeholder line (BLOCKED_RFI, no quantity)
                                         per part, with the item code / floor / physical element the inputs give for
                                         it; a part with no placeholder entry refuses the run (nothing is silent);
  4. the V3_0_6_* files are written beside them: every line outside the V3.0.6 rows is byte-identical to the V3.0.5
     line (asserted on every run), and V3_0_6_DIFF.csv lists every line against V3.0.5 and against the released V2.9.

Rules: owner decision 2026-10-20 sections 2 and 5; WORKFLOW_CONTROLS 2026-10-21 sections 1, 4, 5; ENGINEERING_
REASONING_STANDARD 2026-10-22 sections 2.2, 3 and 7 (DEFAULT GUARD row: no convention where the documents print the
value); UP-STAIR-002 (drawing first), UP-STAIR-003, owner Q-19 / Q-46 A / Q-47 A / Q-62 A (stair concrete by the owner
formula), R-CONC-OWN-1 / -1a (one owner per concrete solid, proposed, checker-merged with T-189 / T-192),
UP-QTY-STATUS-001 (held is a range or blocked, never 0).
Nothing here names a project, a sheet, a layer, a mark or a coordinate; every number comes from the run or the inputs.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import default_guard as DG

METHOD = "ARCH_TAKEOFF_V3.0.6"
EXTENDS = A305.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T187_ARCH_V3_0_6"
LEDGER_SCHEMA = "URBAN_V306_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V306_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
STATES = A305.STATES
GUARD_CHECKS = tuple(sorted(DG.CODES))
LIVE_EVIDENCE = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")

PIECES = {
    "STAIR_CONCRETE": {
        "module": "engine/source/arch_v306.py (typed hand-ledger records)", "policy": "STAIR_CONCRETE_LEDGER_V1",
        "rule_id": "UP-STAIR-003", "rule_version": "owner-Q19-Q47A-Q62A",
        "owner_rules": ["UP-STAIR-002 (drawing first)", "Q-19 (steps = 1/2 riser x tread x width per step)",
                        "Q-47 A (waist between the first and the last riser line, printed slab thickness)",
                        "Q-62 A cond (wedge at a landing deducted once)", "Q-46 A", "R-CONC-OWN-1 / -1a (proposed: "
                        "a flight head / foot inside a member billed at full depth is owned by that member)",
                        "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off flight by flight: steps 1/2 r x g x w per riser + the waist slab "
                               "(printed thickness / cos) between the first and the last riser line, landings at the "
                               "printed slab thickness; the floor-arrival landings stay with the floor slab",
        "drawing_method": "hand ledger per flight and landing from the structural slab plans (riser lines, widths), "
                          "the architectural section (risers, levels) and the stair panels' printed thickness; parts "
                          "inside a beam billed at full depth through the stair deducted (owned by the beam)"},
    "DEFAULT_GUARD": {
        "module": "engine/source/default_guard.py (T-186) via engine/source/arch_v306.py", "policy": "DEFAULT_GUARD_V1",
        "rule_id": "R-DG-1", "rule_version": "proposed-2026-10-22",
        "owner_rules": ["ENGINEERING_REASONING_STANDARD s.7 DEFAULT GUARD (owner 2026-10-22)",
                        "WORKFLOW_CONTROLS s.4 (a fallback only when approved and the documents do not print the "
                        "value)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "the owner's take-off uses the value the drawings print for each element; a convention "
                               "only where the documents genuinely do not establish the value and an answered owner "
                               "decision approves it",
        "drawing_method": "every candidate line that rests on a convention value is compared with the printed "
                          "records of the project's guard evidence; flagged live lines are held with the printed "
                          "value cited (never re-valued by the guard); drawn element parts no line carries get a "
                          "held placeholder"},
}
WAITING = dict(A305.WAITING)
WAITING.update({
    "STAIR_GF_1F_LEDGER": "ST-01 GF -> 1F, ST-01b, ST-02, ST-03 hand-ledger lines (T-184 / T-192): the route G stair "
                          "lines of those storeys stay route lines (held by the guard where a convention is used); "
                          "replacing them by the ledger is a later V3.0.x package",
    "SEARCH_RECORD": "DG-2 (documents searched) is recorded, not holding: route G lines cite one source document "
                     "(T-186 s.3: a line-format gap, not a defect per line); a documents_searched field is needed",
})


class InputsError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


# ================================================================================================ project inputs
def load_inputs(doc, project_id=None):
    """URBAN_V306_INPUTS_V1 or None:
        {"schema", "project",
         "stair": {"piece": "STAIR_CONCRETE", "item_code", "unit": "m3", "source": {file, sha256, task, merge_commit,
                   checker_run}, "scope": {"physical_element", "floors", "supersede_lines": [{element_id, floor, why}],
                   "other_elements": [{element_id, floor, why}]},
                   "records": [{element, component, part, floor, state, value | low/high, reasons, verified_by,
                                guard_element: {element_id, part}, ...}], "declared_totals"},
         "guard": {"source": {file, sha256, task, merge_commit, checker_run},
                   "evidence": {documents, printed, inventory, mapping, doc_alias}, "evidence_file", "evidence_sha256",
                   "conventions": [...], "conventions_file", "conventions_sha256",
                   "holding_checks": [...], "recorded_checks": [...],
                   "placeholders": {"<element>:<part>": {item_code, floor, physical_element}}}}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    st = doc.get("stair")
    if st is not None:
        if st.get("piece") != "STAIR_CONCRETE" or st.get("unit") != "m3" or not st.get("item_code"):
            raise InputsError("stair ledger: piece STAIR_CONCRETE, unit m3 and an item_code are required")
        _source(st.get("source"), "stair ledger")
        sc = st.get("scope") or {}
        if not sc.get("physical_element") or not sc.get("floors"):
            raise InputsError("stair ledger: scope needs physical_element and floors")
        for k in ("supersede_lines", "other_elements", "misread_lines"):
            for x in sc.get(k) or ():
                if not x.get("element_id") or not x.get("floor") or not x.get("why"):
                    raise InputsError(f"stair ledger: every scope.{k} entry has element_id, floor and why")
        ids = set()
        for r in st.get("records") or ():
            key = (r.get("element"), r.get("component"), r.get("part") or "")
            if not r.get("element") or not r.get("component") or key in ids:
                raise InputsError(f"stair ledger: every record has a unique element / component / part: {key}")
            ids.add(key)
            s = r.get("state")
            if s not in STATES:
                raise InputsError(f"stair ledger {key}: state {s!r} not one of {STATES}")
            if s == "RELEASED" and not (_num(r.get("value")) and r["value"] >= 0):
                raise InputsError(f"stair ledger {key}: a RELEASED record carries value >= 0")
            if s == "HELD_RANGE" and not (_num(r.get("low")) and _num(r.get("high")) and 0 <= r["low"] <= r["high"]):
                raise InputsError(f"stair ledger {key}: a HELD_RANGE record carries 0 <= low <= high")
            if s == "HELD_DEFINED" and not _num(r.get("value")):
                raise InputsError(f"stair ledger {key}: a HELD_DEFINED record carries its defined value")
            if s != "RELEASED" and not r.get("reasons"):
                raise InputsError(f"stair ledger {key}: a held record names why it is held")
            if r.get("floor") not in sc["floors"]:
                raise InputsError(f"stair ledger {key}: floor {r.get('floor')!r} outside the scope {sc['floors']}")
            ge = r.get("guard_element") or {}
            if not ge.get("element_id") or not ge.get("part"):
                raise InputsError(f"stair ledger {key}: guard_element (register element_id and part) is required")
    g = doc.get("guard")
    if g is not None:
        _source(g.get("source"), "guard")
        ev = g.get("evidence") or {}
        for k in ("documents", "printed", "inventory", "mapping"):
            if k not in ev:
                raise InputsError(f"guard: evidence.{k} is required")
        if not g.get("conventions"):
            raise InputsError("guard: the convention set the route ran on is required")
        for k in ("evidence_file", "evidence_sha256", "conventions_file", "conventions_sha256"):
            if not g.get(k):
                raise InputsError(f"guard: {k} is required")
        hold, rec = set(g.get("holding_checks") or ()), set(g.get("recorded_checks") or ())
        if not hold or (hold | rec) - set(GUARD_CHECKS) or hold & rec:
            raise InputsError(f"guard: holding_checks (not empty) and recorded_checks are disjoint subsets of "
                              f"{GUARD_CHECKS}")
        if "DG-1" not in hold or "DG-5" not in hold:
            raise InputsError("guard: DG-1 (convention where printed) and DG-5 (silent omission) always hold")
        for k, m in (g.get("mapping_additions") or {}).items():
            if not m.get("element_id") or not m.get("element_kind") or not m.get("part") or not m.get("why"):
                raise InputsError(f"guard: mapping addition {k!r} needs element_id, element_kind, part and why")
            if k in ev["mapping"]:
                raise InputsError(f"guard: mapping addition {k!r} is already in the evidence mapping")
        for k, p in (g.get("placeholders") or {}).items():
            if ":" not in k or not p.get("item_code") or not p.get("floor") or not p.get("physical_element"):
                raise InputsError(f"guard: placeholder {k!r} needs '<element>:<part>', item_code, floor, "
                                  "physical_element")
    return doc


def _source(src, what):
    for k in ("file", "sha256", "task", "merge_commit", "checker_run"):
        if not (src or {}).get(k):
            raise InputsError(f"{what}: source.{k} is required (a piece without a checker MERGED verdict is not "
                              "integrated)")


# ================================================================================================ stair ledger
def _scope_lines(st, lines):
    """the candidate lines of the ledger's item code and physical element on the scope floors."""
    sc = st["scope"]
    return [ln for ln in lines if ln["item_code"] == st["item_code"] and ln["unit"] == st["unit"]
            and str(ln.get("physical_element")) == sc["physical_element"]
            and (ln.get("location") or {}).get("floor") in sc["floors"]]


def stair_changes(inputs, lines, earlier_changed=()):
    """-> (changes, log). Every scope line accounted for (superseded by name or declared another element)."""
    st = (inputs or {}).get("stair")
    if not st:
        return [], {"piece": "STAIR_CONCRETE", "state": "NO_PROJECT_INPUT"}
    sc, src = st["scope"], st["source"]
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    named = {(x["element_id"], x["floor"]): x["why"] for x in sc.get("supersede_lines") or ()}
    other = {(x["element_id"], x["floor"]): x["why"] for x in sc.get("other_elements") or ()}
    misread = {(x["element_id"], x["floor"]): x["why"] for x in sc.get("misread_lines") or ()}
    if (set(named) & set(other)) or (set(named) & set(misread)) or (set(other) & set(misread)):
        raise InputsError("stair ledger: a scope line is accounted for twice (supersede / other / misread)")
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "ledger": src["file"], "ledger_sha256": src["sha256"]}
    ref = st.get("drawing_reference") or src["file"]
    log = {"piece": "STAIR_CONCRETE", "state": "RUN", "ledger": src["file"], "ledger_sha256": src["sha256"],
           "scope": sc, "item_code": st["item_code"], "unit": st["unit"], "scope_lines": [], "by_floor": {},
           "evidence_status": {}}
    changes, seen = [], set()
    for ln in _scope_lines(st, lines):
        k = ((ln.get("location") or {}).get("element_id"), ln["location"].get("floor"))
        q = A30._qty(ln)
        entry = {"line_id": ln["line_id"], "element_id": k[0], "floor": k[1], "evidence_state": ln["evidence_state"],
                 "quantity": A302._q(q)}
        if k in other:
            log["scope_lines"].append(dict(entry, accounted="OTHER_ELEMENT", why=other[k]))
            seen.add(k)
            continue
        if k in misread:
            if ln["line_id"] in earlier:
                raise ValueError(f"{METHOD}: line {ln['line_id']} was changed by an earlier version; never held here")
            if ln.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
                raise ValueError(f"{METHOD}: line {ln['line_id']} is approved: never re-held by the candidate")
            seen.add(k)
            after = copy.deepcopy(ln)
            after.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_range=None, gross=None)
            after["rfi"] = {"question": f"MISREAD_AS_{sc['physical_element']}: {misread[k]}"[:900], "unlocks": k[0]}
            after["calculation"] = dict(after["calculation"], inputs=dict(
                after["calculation"].get("inputs") or {},
                misread={"policy": PIECES["STAIR_CONCRETE"]["policy"], "info_qty_v3_0_5": q, "why": misread[k]}))
            A305._note(after, f"{METHOD}: HELD - the drawing shows this {ln['item_code']} line is not a "
                              f"{sc['physical_element'].lower()} element ({misread[k][:200]}); V3.0.5 figure "
                              f"{A302._q(q)} {ln['unit']} kept as information, never summed")
            changes.append(A305._change("STAIR_CONCRETE", "REPLACE", ln, after, drawing_reference=misread[k][:300],
                                        held=[{"what": f"{ln['item_code']} {k[0]}", "why": misread[k], "range": None}],
                                        downstream=list(st.get("misread_downstream") or ()), verification=verif,
                                        evidence_status="HELD", codes=[f"MISREAD_AS_{sc['physical_element']}"]))
            log["scope_lines"].append(dict(entry, accounted="MISREAD_HELD", why=misread[k]))
            continue
        if k not in named:
            raise InputsError(f"stair ledger: candidate line {ln['line_id']} ({k[0]} {k[1]}, {A302._q(q)} "
                              f"{ln['unit']}) is of the same item and physical element on a scope floor and is "
                              "neither superseded by name nor declared another element: an integration that only "
                              "adds is refused")
        if ln["line_id"] in earlier:
            raise ValueError(f"{METHOD}: line {ln['line_id']} was changed by an earlier version; never replaced here")
        seen.add(k)
        after = copy.deepcopy(ln)
        after.update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None, bounded_range=None, rfi=None)
        A305._note(after, f"{METHOD}: SUPERSEDED - route G {ln['evidence_state']} {A302._q(q)} {ln['unit']} is replaced "
                          f"by the {src['task']} ledger lines (MERGED {src['merge_commit']}): {named[k]}")
        changes.append(A305._change("STAIR_CONCRETE", "REPLACE", ln, after, drawing_reference=ref, held=[],
                                    downstream=[], verification=verif, evidence_status="DRAWING-CONFIRMED"))
        log["scope_lines"].append(dict(entry, accounted="SUPERSEDED", why=named[k]))
    missing = (set(named) | set(other) | set(misread)) - seen
    if missing:
        raise InputsError(f"stair ledger: scope names line(s) the candidate does not have: {sorted(missing)}")
    lg = {"piece": "STAIR_POOL_TANK_STEEL", "item_code": st["item_code"], "unit": st["unit"], "source": src,
          "scope": {"physical_element": sc["physical_element"], "floors": sc["floors"]}}
    for r in st.get("records") or ():
        ln, evs = A305.record_line(pid, rev, docs, "STAIR_POOL_TANK_STEEL", lg, r)
        _restamp(ln, r, src)
        if ln["line_id"] in have:
            raise ValueError(f"{METHOD}: ledger line {r['element']} {r['component']} repeats a candidate line id")
        held = []
        if ln["evidence_state"] != "SOURCE_DERIVED":
            held = [{"what": f"{r['element']} {r['component']}" + (f" {r['part']}" if r.get("part") else ""),
                     "why": ln["rfi"]["question"],
                     "range": [ln["bounded_range"]["low"], ln["bounded_range"]["high"]]
                     if ln.get("bounded_range") else None}]
        changes.append(A305._change("STAIR_CONCRETE", "ADD", None, ln, drawing_reference=r.get("printed") or ref,
                                    held=held, downstream=list(r.get("downstream") or ()),
                                    verification=dict(verif, record_verified_by=r.get("verified_by")),
                                    evidence_status=evs, guard_element=r["guard_element"]))
        b = log["by_floor"].setdefault(r["floor"], {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0,
                                                    "held_defined": 0.0, "unquantified": 0})
        b["lines"] += 1
        if r["state"] == "RELEASED":
            b["released"] += r["value"]
        elif r["state"] == "HELD_RANGE":
            b["held_low"] += r["low"]
            b["held_high"] += r["high"]
        elif r["state"] == "HELD_DEFINED":
            b["held_defined"] += r["value"]
        else:
            b["unquantified"] += 1
        log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
    tot = {}
    for v in log["by_floor"].values():
        for k, x in v.items():
            tot[k] = tot.get(k, 0) + x
    log["totals"] = {k: _r(v) if isinstance(v, float) else v for k, v in sorted(tot.items())}
    for v in log["by_floor"].values():
        for k in list(v):
            if isinstance(v[k], float):
                v[k] = _r(v[k])
    dec = st.get("declared_totals") or {}
    for k, v in dec.items():
        if k in log["totals"] and abs((log["totals"][k] or 0) - v) > 0.0006:
            raise ValueError(f"{METHOD}: stair ledger {k} {log['totals'][k]} != the ledger's own total {v}")
    log["declared_totals"] = dec
    return changes, log


def _restamp(ln, r, src):
    """the V3.0.5 record line, re-labelled for this piece (policy, rule, note); the line id is recomputed."""
    from engine.source import boq_line as BL
    p = PIECES["STAIR_CONCRETE"]
    ln["calculation"]["inputs"]["policy"] = p["policy"]
    ln["calculation"]["inputs"]["guard_element"] = r["guard_element"]
    ln["rule"]["rule_id"], ln["rule"]["version"] = p["rule_id"], p["rule_version"]
    ln["notes"] = f"{METHOD}: stair concrete by hand ledger ({src['task']}, MERGED {src['merge_commit']})"
    ln["location"]["element_id"] = ln["location"]["element_id"].replace("HL:STAIR_POOL_TANK_STEEL:", "HL:STAIR_CONCRETE:")
    if ln["rfi"]:
        ln["rfi"]["unlocks"] = ln["location"]["element_id"]
    ln["line_id"] = BL.line_id(ln["project"]["project_id"], ln["item_code"], ln["location"]["element_id"],
                               p["rule_id"], p["rule_version"], ln["unit"])
    BL.validate(ln)


# ================================================================================================ default guard
def _guard_lines(g, lines, added_map):
    """guard lines: every candidate line resting on a convention (adapter of T-186), and every other line carried
    (state from its evidence) so the drawn inventory is checked against the whole candidate."""
    ev = g["evidence"]
    mapping = dict(ev["mapping"], **(g.get("mapping_additions") or {}))
    glines = DG.lines_from_canonical(lines, g["conventions"], mapping=mapping, doc_alias=ev.get("doc_alias"))
    conv_ids = {x["id"] for x in glines}
    carried = []
    for ln in lines:
        if ln["line_id"] in conv_ids:
            continue
        eid = (ln.get("location") or {}).get("element_id")
        m = added_map.get(ln["line_id"]) or mapping.get(eid) or {}
        carried.append({"id": ln["line_id"], "element_id": m.get("element_id", eid),
                        "element_kind": m.get("element_kind", ln.get("physical_element")),
                        "part": m.get("part", "WHOLE"), "trade": ln["trade"], "unit": ln["unit"], "qty": None,
                        "state": "EXCLUDED", "values": {}})
    return glines, carried


def _same_as_printed(f, gline):
    """a CONVENTION_WHERE_PRINTED finding whose cited structural printed values all equal the convention value used."""
    if f["code"] != "CONVENTION_WHERE_PRINTED":
        return False
    param = f["detail"].split(":", 1)[0]
    conv = ((gline.get("values") or {}).get(param) or {}).get("value")
    vals = [c["value"] for c in f.get("citation") or () if c.get("basis", "STRUCTURAL") == "STRUCTURAL"]
    return _num(conv) and bool(vals) and all(_num(v) and abs(float(v) - float(conv)) <= 1e-9 for v in vals)


def _findings_by_line(findings):
    out = {}
    for f in findings:
        if f["line_id"] is not None:
            out.setdefault(f["line_id"], []).append(f)
    return out


def guard_changes(inputs, lines, added=(), earlier_changed=()):
    """the default guard over the candidate lines (+ the lines this version adds). -> (changes, log)"""
    g = (inputs or {}).get("guard")
    if not g:
        return [], {"piece": "DEFAULT_GUARD", "state": "NO_PROJECT_INPUT"}
    src = g["source"]
    pid, rev, docs = A302._proj(lines)
    hold, rec = set(g["holding_checks"]), set(g.get("recorded_checks") or ())
    disabled = tuple(c for c in GUARD_CHECKS if c not in hold | rec)
    added_map = {c["after"]["line_id"]: c["guard_element"] for c in added if c.get("guard_element")}
    allv = list(lines) + [c["after"] for c in added]
    glines, carried = _guard_lines(g, allv, added_map)
    ev = g["evidence"]
    res = DG.guard(glines + carried, documents=ev["documents"], printed=ev["printed"], inventory=ev["inventory"],
                   members=ev.get("members") or (), revisions=ev.get("revisions") or (), disabled=disabled)
    by_line = _findings_by_line(res["findings"])
    gby = {x["id"]: x for x in glines}
    byid = {ln["line_id"]: ln for ln in lines}
    addid = {c["after"]["line_id"] for c in added}
    earlier = set(earlier_changed)
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "evidence": g["evidence_file"], "evidence_sha256": g["evidence_sha256"],
             "conventions": g["conventions_file"], "conventions_sha256": g["conventions_sha256"]}
    log = {"piece": "DEFAULT_GUARD", "state": "RUN", "holding_checks": sorted(hold), "recorded_checks": sorted(rec),
           "disabled_checks": list(disabled), "convention_lines": len(glines), "lines_checked": len(glines) + len(carried),
           "findings_by_code": {}, "held_live": [], "listed_not_live": [], "recorded_only": [], "placeholders": [],
           "rebased_on_printed": [], "equal_value_rebase": bool(g.get("equal_value_rebase")),
           "held_by_trade_unit": {}, "convention_live_by_trade_unit": {}, "pass_convention_lines": 0}
    for f in res["findings"]:
        log["findings_by_code"][f["code"]] = log["findings_by_code"].get(f["code"], 0) + 1
    for x in glines:
        if x["state"] == "PROVISIONAL":
            k = f"{x['trade']} {x['unit']}"
            log["convention_live_by_trade_unit"][k] = log["convention_live_by_trade_unit"].get(k, 0.0) + x["qty"]
    changes = []
    for lid, fl in sorted(by_line.items()):
        if lid in addid:
            raise ValueError(f"{METHOD}: the guard flags a line this version adds ({lid}): "
                             f"{[f['code'] for f in fl]}; the ledger is not integrated over a guard finding")
        if lid not in byid:          # a carried line id that is not a candidate line cannot occur
            raise ValueError(f"{METHOD}: guard finding on an unknown line {lid}")
        ln = byid[lid]
        holding = [f for f in fl if f["check"] in hold]
        recorded = [f for f in fl if f["check"] in rec]
        if g.get("equal_value_rebase") and lid in gby:
            same = [f for f in holding if _same_as_printed(f, gby[lid])]
            if same:
                log["rebased_on_printed"].append({"line_id": lid, "item_code": ln["item_code"],
                                                  "element_id": (ln.get("location") or {}).get("element_id"),
                                                  "quantity": A302._q(A30._qty(ln)),
                                                  "citations": [c for f in same for c in f.get("citation") or ()]})
                holding = [f for f in holding if f not in same]
        if recorded:
            log["recorded_only"].append({"line_id": lid, "codes": sorted({f["code"] for f in recorded})})
        if not holding:
            continue
        live = ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None
        q = A30._qty(ln)
        entry = {"line_id": lid, "item_code": ln["item_code"], "floor": (ln.get("location") or {}).get("floor"),
                 "element_id": (ln.get("location") or {}).get("element_id"), "unit": ln["unit"],
                 "evidence_state": ln["evidence_state"], "quantity": A302._q(q),
                 "codes": sorted({f["code"] for f in holding})}
        if not live:
            log["listed_not_live"].append(entry)
            continue
        if ln.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
            raise ValueError(f"{METHOD}: line {lid} is {ln.get('approval_state')}: an approved line is never re-held")
        cites = [c for f in holding for c in f.get("citation") or ()]
        why = "; ".join(f"{f['code']}: {f['detail']}" for f in holding)
        after = copy.deepcopy(ln)
        after.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_range=None)
        after["gross"] = None
        after["rfi"] = {"question": ("DEFAULT GUARD: " + why)[:900],
                        "unlocks": (ln.get("location") or {}).get("element_id")}
        after["calculation"] = dict(after["calculation"], inputs=dict(
            after["calculation"].get("inputs") or {},
            default_guard={"policy": PIECES["DEFAULT_GUARD"]["policy"], "info_qty_v3_0_5": A30._qty(ln),
                           "findings": [{k: f.get(k) for k in ("check", "code", "detail", "citation")}
                                        for f in holding],
                           "guard_element": {k: gby[lid].get(k) for k in ("element_id", "element_kind", "part")}
                           if lid in gby else None,
                           "changed_by_earlier_version": lid in earlier}))
        A305._note(after, f"{METHOD}: HELD by the default guard ({', '.join(entry['codes'])}); V3.0.5 figure "
                          f"{A302._q(q)} {ln['unit']} kept as information, never summed")
        changes.append(A305._change("DEFAULT_GUARD", "REPLACE", ln, after,
                                    drawing_reference="; ".join(f"{c.get('printed_id')}: {c.get('value')} "
                                                                f"{c.get('unit')} ({c.get('doc')})"
                                                                for c in cites)[:600] or "drawn inventory",
                                    held=[{"what": f"{ln['item_code']} {entry['element_id']}", "why": why[:900],
                                           "range": None}],
                                    downstream=[], verification=verif, evidence_status="HELD",
                                    codes=entry["codes"], citations=cites))
        log["held_live"].append(entry)
        k = f"{ln['trade']} {ln['unit']}"
        log["held_by_trade_unit"][k] = log["held_by_trade_unit"].get(k, 0.0) + (q["value"] or 0.0)
    # SILENT_OMISSION placeholders
    have = {ln["line_id"] for ln in allv}
    ph = g.get("placeholders") or {}
    for f in res["findings"]:
        if f["code"] != "SILENT_OMISSION":
            continue
        part = f["detail"].rsplit(" part ", 1)[1].split(" ")[0]
        key = f"{f['element_id']}:{part}"
        if key not in ph:
            raise InputsError(f"guard: SILENT_OMISSION of {key} has no placeholder entry in the inputs (item code, "
                              "floor, physical element): nothing drawn is left silent")
        p = ph[key]
        from engine.source import boq_line as BL
        eid = f"DG5:{key}"
        ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=p["item_code"], unit=p.get("unit", "m3"),
                          evidence_state="BLOCKED_RFI", element_id=eid, floor=p["floor"],
                          physical_element=p["physical_element"],
                          formula="held: drawn element part carried by no candidate line (default guard DG-5)",
                          inputs={"policy": PIECES["DEFAULT_GUARD"]["policy"], "element": f["element_id"],
                                  "part": part, "detail": f["detail"], "why": p.get("why")},
                          documents=docs, geometry_source="SCHEDULE_ONLY", geometry_confidence="INFERRED_CANDIDATE",
                          rule_id=PIECES["DEFAULT_GUARD"]["rule_id"],
                          rule_version=PIECES["DEFAULT_GUARD"]["rule_version"], material_state="SOURCE",
                          rfi={"question": f"SILENT_OMISSION: {f['detail']}"[:900], "unlocks": eid},
                          notes=f"{METHOD}: held placeholder for a drawn element part no line carries "
                                f"({src['task']} guard, MERGED {src['merge_commit']})")
        if ln["line_id"] in have:
            raise ValueError(f"{METHOD}: placeholder {key} repeats a line id")
        have.add(ln["line_id"])
        changes.append(A305._change("DEFAULT_GUARD", "ADD", None, ln, drawing_reference=p.get("why") or f["detail"],
                                    held=[{"what": key, "why": f["detail"], "range": None}], downstream=[],
                                    verification=verif, evidence_status="UNKNOWN", codes=["SILENT_OMISSION"]))
        log["placeholders"].append({"key": key, "line_id": ln["line_id"], "item_code": p["item_code"],
                                    "floor": p["floor"], "detail": f["detail"]})
    log["pass_convention_lines"] = sum(1 for x in glines if x["id"] not in by_line)
    for d in ("held_by_trade_unit", "convention_live_by_trade_unit"):
        log[d] = {k: _r(v, 3) for k, v in sorted(log[d].items())}
    log["findings_by_code"] = dict(sorted(log["findings_by_code"].items()))
    log["guard_summary"] = res["summary"]
    return changes, log


# ================================================================================================ integrate / write
def integrate(l305, v306_changes):
    """-> (V3.0.6 lines, identity). Every line outside the V3.0.6 rows is byte-identical to the V3.0.5 line; a line
    two V3.0.6 rows change, an added line repeating an id, or a row naming a line V3.0.5 does not have, is refused."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l305}
    rep, adds = {}, []
    for c in v306_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.5 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.5 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l305] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    by305 = {ln["line_id"]: ln for ln in l305}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by305[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l305):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.6 rows differ from {EXTENDS}")
    ident = {"v3_0_5_lines": len(l305), "v3_0_6_lines": len(out), "v3_0_6_rows": len(v306_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_5": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b305 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_5")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_5": b305, "after_v3_0_6": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_5",
              "v3_0_6", "evidence_status", "release_status", "codes", "drawing_reference", "verification", "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_5": A302._q(r["before_v3_0_5"]), "v3_0_6": A302._q(r["after_v3_0_6"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}"
                                       + (f" / {r['verification']['record_verified_by']}"
                                          if r["verification"].get("record_verified_by") else ""),
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_5", "vs_released_v2_9", "v2_9", "v3_0_5",
            "v3_0_6")


def diff_rows(l305, l306, released_lines=None):
    b305 = {ln["line_id"]: ln for ln in l305}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l306:
        o = b305.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_5": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_5": A302._q(A30._qty(o)) if o else "", "v3_0_6": A302._q(A30._qty(ln))})
    return out


def changes_for(inputs, l305, earlier_changed=()):
    """the stair ledger first (its lines are guard-checked as carried), then the guard. -> (changes, logs)"""
    ch_s, log_s = stair_changes(inputs, l305, earlier_changed)
    rep_s = {c["before"]["line_id"]: c["after"] for c in ch_s if c["action"] == "REPLACE"}
    view = [rep_s.get(ln["line_id"], ln) for ln in l305]
    ch_g, log_g = guard_changes(inputs, view, [c for c in ch_s if c["action"] == "ADD"], earlier_changed)
    clash = {c["before"]["line_id"] for c in ch_g if c["action"] == "REPLACE"} & set(rep_s)
    if clash:
        raise ValueError(f"{METHOD}: the guard holds a line the stair ledger supersedes: {sorted(clash)}")
    return ch_s + ch_g, [log_s, log_g]


def write(out, l305, v306_changes, logs, inputs, released_lines=None):
    """the V3_0_6_* files beside the V3_0_5_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l306, ident = integrate(l305, v306_changes)
    rows = ledger_rows(v306_changes, released_lines)
    diff = diff_rows(l305, l306, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_5", {}).setdefault(d["vs_v3_0_5"], 0)
        dsum["vs_v3_0_5"][d["vs_v3_0_5"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t305, t306 = A304.code_totals(l305), A304.code_totals(l306)
    moved = {k: {"v3_0_5": t305.get(k), "v3_0_6": t306.get(k)} for k in sorted(set(t305) | set(t306))
             if t305.get(k) != t306.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"stair": {k: ((inputs or {}).get("stair") or {}).get(k)
                                for k in ("piece", "item_code", "unit", "source", "scope", "declared_totals")},
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "mapping_additions", "placeholders")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_6_BOQ_LINES.json": BL.dumps(l306),
             "V3_0_6_BOQ_LINES.csv": A30._lines_csv(l306),
             "V3_0_6_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_6_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_6_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_6_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "load_inputs", "stair_changes", "guard_changes", "changes_for", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError"]
