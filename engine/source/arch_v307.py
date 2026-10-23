"""ARCH_TAKEOFF_V3.0.7 (T-193): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.6 (engine.source.arch_v30,
arch_v301 .. arch_v306), extended with checker-VERIFIED concrete solids that replace route convention lines the
V3.0.6 default guard held. Not a new method family and not the released default (owner management decision
2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.7`):
  1. the run is the V3.0.6 candidate exactly: its V3_0_* .. V3_0_6_* files are written unchanged (arch_v30 .. arch_v306
     are not edited);
  2. VERIFIED SOLIDS (one entry per piece of the project inputs, URBAN_V307_INPUTS_V1): the piece names its checker-
     merged source (file sha256, task, merge commit, checker run), the item code, unit m3, the physical element and the
     floors in scope. Before a line is ADDED every candidate line of that item code and physical element on a scope
     floor must be accounted for (T-179 lesson):
       supersede_lines  the same physical element carried by a convention line: it becomes NOT_APPLICABLE_WITH_
                        EVIDENCE (never deleted, never summed). Its convention figure is stated in the inputs and must
                        equal the figure the line carries (live) or the V3.0.6 guard kept as information (held), so the
                        move of each item is exactly verified minus convention. A line V3.0.1 .. V3.0.5 changed is never
                        superseded here; a line V3.0.6 changed only when V3.0.6 HELD it (guard / misread);
       other_elements   another physical element of the same item (kept byte-identical, e.g. a held placeholder of a
                        part no drawing details);
       retire_lines     a line of ANY item that the drawing shows to be this element misread as another item (e.g. dome
                        ribs read as a winder stair): retired NOT_APPLICABLE_WITH_EVIDENCE naming the record that now
                        carries the element (counted once), only when V3.0.6 already held it;
     an unaccounted scope line, or a named line the candidate does not have, refuses the run;
  3. one line per record: RELEASED -> SOURCE_DERIVED (VERIFIED where the record names the checker run that re-measured
     it, else DRAWING-CONFIRMED; NOT RELEASED, only the owner releases); UNQUANTIFIED -> BLOCKED_RFI (HELD or UNKNOWN as
     the record says), its figures only as information; missing is never 0. A record that states its dimensions is
     recomputed here and refused when it disagrees (> 0.0005 m3):
       PRISM               plan area (m2) x height (m); the height basis must be STRUCTURAL (a FINISHED depth, a
                           water depth or a level difference without the build-up is not a structural height): any
                           other basis turns the record HELD with its figure as information;
       SPHERICAL_CAP_SHELL chord, rise and thickness (m), each PRINTED: the solid between concentric spheres,
                           R_o = (c^2 / 4 + h^2) / 2h, R_i = R_o - t, h_i = h - t,
                           V = pi / 3 [h^2 (3 R_o - h) - h_i^2 (3 R_i - h_i)]; a rise or thickness not printed (a
                           convention, rise = radius) turns the record HELD;
  4. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged T-186 guard runs again over the V3.0.7 lines with the project's
     guard evidence (a NEW evidence version may add printed records; each new record is reported with the lines it now
     confirms or flags). Element parts are carried by the V3.0.6 ledger lines and placeholders (their guard element) and
     by the added records; a line this version adds may carry no guard finding (refused); a new holding finding on a
     live line holds it (BLOCKED_RFI, figure as information, printed values cited); an equal printed value is listed
     REBASED_ON_PRINTED; a SILENT_OMISSION with no placeholder line refuses the run;
  5. scenario lines beside the approved design (e.g. a client-requested change S1) are written to the run file only,
     never as BOQ lines and never in a total;
  6. the V3_0_7_* files are written beside them: every line outside the V3.0.7 rows is byte-identical to the V3.0.6
     line (asserted on every run), and V3_0_7_DIFF.csv lists every line against V3.0.6 and against the released V2.9.

Rules: owner decision 2026-10-20 sections 2 and 5; WORKFLOW_CONTROLS 2026-10-21 sections 1, 4, 5;
ENGINEERING_REASONING_STANDARD 2026-10-22 sections 2.2, 3 and 7; UP-QTY-STATUS-001 (held is a range or blocked, never
0); R-POOL-4 r2 (RC wall height from the rim to the structure line; a finished depth alone is HELD); the dome shell
rule of T-185 (printed chord / rise / thickness, exact concentric solid; no structural detail = HELD); the client-change
scenario rule of T-185 (S1 beside S0, never released).
Nothing here names a project, a sheet, a layer, a mark or a coordinate; every number comes from the run or the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import math

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v306 as A306
from engine.source import default_guard as DG

METHOD = "ARCH_TAKEOFF_V3.0.7"
EXTENDS = A306.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T193_ARCH_V3_0_7"
LEDGER_SCHEMA = "URBAN_V307_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V307_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
STATES = ("RELEASED", "UNQUANTIFIED")
HELD_STATUS = ("HELD", "UNKNOWN")
DIM_TOL_M3 = 0.0005
LIVE_EVIDENCE = A306.LIVE_EVIDENCE
V306_HOLD_KEYS = ("default_guard", "misread")   # calculation inputs V3.0.6 writes on a line it held

PIECES = {
    "POOL_CONCRETE": {
        "module": "engine/source/arch_v307.py (typed checker-verified records)", "policy": "POOL_CONCRETE_VERIFIED_V1",
        "rule_id": "R-POOL-4", "rule_version": "r2",
        "owner_rules": ["Q-26 A (flat floor; the printed base thickness; 1.15 = the finished water depth)",
                        "R-POOL-4 r2 (RC wall height = rim to the structure line; a finished depth alone is HELD)",
                        "owner 2026-10-22 11:50 / 16:45 (whole-line rule; steps NOT DRAWN = consultant item, never 0)",
                        "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off of an open RC tank: base slab = outer plan footprint x the printed "
                               "base thickness (wall foot included, measured once at the junction); walls = wall band "
                               "x the RC height from the base top to the rim; steps / benches only where drawn",
        "drawing_method": "outer and water outlines of the tank from the structural plan (curved part on its true "
                          "arc), the printed base thickness from the pool detail, the rim and the structure line from "
                          "the architectural cut through the pool; route G's pool conventions (floor and wall "
                          "thickness, wall height, half the wall ring) superseded"},
    "DOME_SHELL": {
        "module": "engine/source/arch_v307.py (typed checker-verified records)", "policy": "DOME_SHELL_VERIFIED_V1",
        "rule_id": "R-DOME-SHELL-1", "rule_version": "proposed-2026-10-22",
        "owner_rules": ["Q-27 A (three domes: two on the first-floor roof, one on the upper roof)",
                        "Q-18 (dome size basis held until printed; no default)",
                        "Q-29 + owner 2026-10-22 (client request only: S0 approved design kept, S1 beside, never "
                        "released, S2 only from a consultant-issued drawing)",
                        "Q-44 A / Q-61 C (the ring stays its own line, never duplicated)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off of a dome shell from its detail: chord, rise and thickness as "
                               "printed, the shell solid above the springing; the ring and the drum are their own "
                               "items; a dome with no structural detail is held",
        "drawing_method": "exact solid between concentric spheres from the printed chord / rise / thickness of the "
                          "dome detail; route G's dome conventions (rise = radius, convention thickness, outer area x "
                          "thickness) superseded; route lines that read the same dome's ribs as another item retired"},
    "DEFAULT_GUARD": A306.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A306.WAITING)
WAITING.pop("DOME_SHELL", None)
WAITING.update({
    "POOL_BAR_POPULATIONS": "pool wall / base bar populations (T-191, R1 / R2 from the verified structure) are a later "
                            "V3.0.x package; the pool line group stays PARTIALLY VERIFIED until they and the steps are "
                            "resolved",
    "DOME_RING_DRUM_TOWER": "S0 dome rings (plan band vs detail ring, depth not printed), drums (material, thickness "
                            "not printed) and the upper-roof dome (no structural detail) stay HELD",
    "MISSING_CATEGORIES": "formwork and railings / balustrades / shutters (T-199, V3.0.8), plaster and paint (T-211, "
                          "V3.0.9)",
})


class InputsError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


# ================================================================================================ geometry
def spherical_cap_shell_m3(chord_m, rise_m, thickness_m):
    """the solid between two concentric spherical caps: outer chord c and rise h at the springing plane, shell
    thickness t (radial). R_o = (c^2/4 + h^2) / 2h; R_i = R_o - t; the inner cap cut by the same plane has h_i = h - t."""
    c, h, t = float(chord_m), float(rise_m), float(thickness_m)
    if c <= 0 or h <= 0 or t <= 0 or t >= h:
        raise InputsError(f"spherical cap shell: chord {c}, rise {h}, thickness {t} (all > 0, thickness < rise)")
    ro = (c * c / 4.0 + h * h) / (2.0 * h)
    ri, hi = ro - t, h - t
    return math.pi / 3.0 * (h * h * (3.0 * ro - h) - hi * hi * (3.0 * ri - hi))


def dims_check(r):
    """-> (recomputed m3 or None, hold reason or None). Refuses a stated value that disagrees with its dimensions."""
    d = r.get("dims")
    if not d:
        return None, None
    kind = d.get("kind")
    if kind == "PRISM":
        if not (_num(d.get("area_m2")) and _num(d.get("height_m"))):
            raise InputsError(f"record {r['element']} {r['component']}: PRISM needs area_m2 and height_m")
        v = float(d["area_m2"]) * float(d["height_m"])
        basis = d.get("height_basis")
        hold = None if basis == "STRUCTURAL" else (
            f"height {d['height_m']} m has basis {basis!r}: a structural height (base top to rim / structure line) is "
            "required; a finished depth or a level difference without its build-up is not a structural dimension")
    elif kind == "SPHERICAL_CAP_SHELL":
        for k in ("chord_m", "rise_m", "thickness_m"):
            if not _num(d.get(k)):
                raise InputsError(f"record {r['element']} {r['component']}: SPHERICAL_CAP_SHELL needs {k}")
        v = spherical_cap_shell_m3(d["chord_m"], d["rise_m"], d["thickness_m"])
        bases = {k: (d.get("basis") or {}).get(k) for k in ("chord_m", "rise_m", "thickness_m")}
        bad = sorted(k for k, b in bases.items() if b != "PRINTED")
        hold = None if not bad else (f"{', '.join(bad)} not printed ({bases}): a dome shell is measured from its "
                                     "printed chord, rise and thickness; a convention (rise = radius, a default "
                                     "thickness) is never used")
    else:
        raise InputsError(f"record {r['element']} {r['component']}: dims.kind {kind!r} (PRISM, SPHERICAL_CAP_SHELL)")
    if r.get("state") == "RELEASED" and abs(v - float(r["value"])) > DIM_TOL_M3:
        raise InputsError(f"record {r['element']} {r['component']}: value {r['value']} m3 disagrees with its "
                          f"dimensions {_r(v)} m3 (more than {DIM_TOL_M3} m3)")
    return v, hold


# ================================================================================================ project inputs
def _source(src, what):
    for k in ("file", "sha256", "task", "merge_commit", "checker_run"):
        if not (src or {}).get(k):
            raise InputsError(f"{what}: source.{k} is required (a piece without a checker MERGED verdict is not "
                              "integrated)")


def load_inputs(doc, project_id=None):
    """URBAN_V307_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": POOL_CONCRETE | DOME_SHELL, "item_code", "unit": "m3", "source": {...},
                     "scope": {"physical_element", "floors", "supersede_lines": [{element_id, floor, why,
                               convention_qty}], "other_elements": [{element_id, floor, why}],
                               "retire_lines": [{element_id, floor, item_code, why, counted_by, convention_qty}]},
                     "records": [{element, component, part, floor, state, value, dims, verified_by, reasons,
                                  evidence_status (UNQUANTIFIED: HELD | UNKNOWN), guard_element: {element_id, part},
                                  printed, formula, info}],
                     "declared_totals": {...}, "line_group": {...}}],
         "beside": [{scenario, element, item, unit, qty, status, basis}]  (run file only, never a line, never summed),
         "guard": as URBAN_V306_INPUTS_V1 "guard", plus "new_records": [ids of printed records new in this evidence
                  version]}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p not in PIECES or p == "DEFAULT_GUARD" or p in seen:
            raise InputsError(f"piece {p!r}: one of POOL_CONCRETE / DOME_SHELL, once each")
        seen.add(p)
        if pc.get("unit") != "m3" or not pc.get("item_code"):
            raise InputsError(f"piece {p}: unit m3 and an item_code are required")
        _source(pc.get("source"), f"piece {p}")
        sc = pc.get("scope") or {}
        if not sc.get("physical_element") or not sc.get("floors"):
            raise InputsError(f"piece {p}: scope needs physical_element and floors")
        for k in ("supersede_lines", "other_elements", "retire_lines"):
            for x in sc.get(k) or ():
                if not x.get("element_id") or not x.get("floor") or not x.get("why"):
                    raise InputsError(f"piece {p}: every scope.{k} entry has element_id, floor and why")
                if k != "other_elements" and not _num(x.get("convention_qty")):
                    raise InputsError(f"piece {p}: scope.{k} {x['element_id']} states the convention_qty it carries")
                if k == "retire_lines" and (not x.get("item_code") or not x.get("counted_by")):
                    raise InputsError(f"piece {p}: retire line {x['element_id']} needs item_code and counted_by")
        ids = set()
        for r in pc.get("records") or ():
            key = (r.get("element"), r.get("component"), r.get("part") or "")
            if not r.get("element") or not r.get("component") or key in ids:
                raise InputsError(f"piece {p}: every record has a unique element / component / part: {key}")
            ids.add(key)
            st = r.get("state")
            if st not in STATES:
                raise InputsError(f"piece {p} {key}: state {st!r} not one of {STATES}")
            if st == "RELEASED" and not (_num(r.get("value")) and r["value"] > 0):
                raise InputsError(f"piece {p} {key}: a RELEASED record carries a value > 0 (missing is never 0)")
            if st == "UNQUANTIFIED" and (not r.get("reasons") or r.get("evidence_status") not in HELD_STATUS):
                raise InputsError(f"piece {p} {key}: an UNQUANTIFIED record names why and its status HELD / UNKNOWN")
            if r.get("floor") not in sc["floors"]:
                raise InputsError(f"piece {p} {key}: floor {r.get('floor')!r} outside the scope {sc['floors']}")
            ge = r.get("guard_element") or {}
            if not ge.get("element_id") or not ge.get("part"):
                raise InputsError(f"piece {p} {key}: guard_element (register element_id and part) is required")
            dims_check(r)
        rec_keys = {f"{r['element']}:{r['component']}" for r in pc.get("records") or ()}
        for x in sc.get("retire_lines") or ():
            if x["counted_by"] not in rec_keys:
                raise InputsError(f"piece {p}: retire line {x['element_id']} counted_by {x['counted_by']!r} is not a "
                                  "record of this piece (the element must be carried once)")
    for b in doc.get("beside") or ():
        if b.get("scenario") in (None, "S0") or b.get("released") not in (None, False):
            raise InputsError("beside: a scenario other than S0, never released")
    g = doc.get("guard")
    if g is not None:
        A306.load_inputs({"schema": A306.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
        known = {p["id"] for p in g["evidence"]["printed"]}
        for i in g.get("new_records") or ():
            if i not in known:
                raise InputsError(f"guard: new record {i!r} is not in the evidence")
    return doc


# ================================================================================================ verified solids
def _scope_lines(pc, lines):
    sc = pc["scope"]
    return [ln for ln in lines if ln["item_code"] == pc["item_code"] and ln["unit"] == pc["unit"]
            and str(ln.get("physical_element")) == sc["physical_element"]
            and (ln.get("location") or {}).get("floor") in sc["floors"]]


def _held_by_v306(ln):
    """the V3.0.6 hold record of a line (guard or misread), or None."""
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    for k in V306_HOLD_KEYS:
        if inp.get(k) is not None:
            return k, inp[k]
    return None


def _carried_qty(ln):
    """the convention figure a line carries: its live quantity, or the figure V3.0.6 kept as information."""
    h = _held_by_v306(ln)
    if h is not None:
        q = h[1].get("info_qty_v3_0_5")
        return (q or {}).get("value") if isinstance(q, dict) else q
    if ln["evidence_state"] in LIVE_EVIDENCE:
        return A30._qty(ln)["value"]
    return None


def _check_replaceable(ln, earlier, v306):
    lid = ln["line_id"]
    if lid in earlier:
        raise ValueError(f"{METHOD}: line {lid} was changed by V3.0.1 .. V3.0.5; never replaced here")
    if lid in v306 and _held_by_v306(ln) is None:
        raise ValueError(f"{METHOD}: line {lid} was changed by V3.0.6 without being held; never replaced here")
    if ln.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
        raise ValueError(f"{METHOD}: line {lid} is {ln.get('approval_state')}: an approved line is never replaced")


def record_line(pid, rev, docs, piece, pc, r):
    """one BOQ line for one record. -> (line, evidence status, recomputed m3)"""
    from engine.source import boq_line as BL
    p, src = PIECES[piece], pc["source"]
    v, dim_hold = dims_check(r)
    st = r["state"]
    reasons = list(r.get("reasons") or ())
    info = dict(r.get("info") or {})
    evs = r.get("evidence_status")
    if st == "RELEASED" and dim_hold:
        st, evs = "UNQUANTIFIED", "HELD"
        reasons.append(dim_hold)
        info["figure_not_released_m3"] = _r(r["value"])
    ev = "SOURCE_DERIVED" if st == "RELEASED" else "BLOCKED_RFI"
    eid = f"HL:{piece}:{r['element']}:{A305._slug(r['component'])}" + (
        f":{A305._slug(r['part'])}" if r.get("part") else "")
    rfi = None if ev == "SOURCE_DERIVED" else {"question": "; ".join(reasons)[:900], "unlocks": eid}
    pe = r.get("physical_element") or pc["scope"]["physical_element"]
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=pc["item_code"], unit="m3",
                      evidence_state=ev, measured_net=_r(r["value"]) if ev == "SOURCE_DERIVED" else None,
                      element_id=eid, floor=r["floor"], physical_element=pe, subtrade=pe,
                      formula=r.get("formula") or ("held: " + "; ".join(reasons))[:400],
                      inputs=dict({"policy": p["policy"], "source": src["file"], "source_sha256": src["sha256"],
                                   "element": r["element"], "component": r["component"], "part": r.get("part"),
                                   "printed": r.get("printed"), "dims": r.get("dims"),
                                   "recomputed_m3": _r(v), "reasons": reasons, "record_state": r["state"],
                                   "guard_element": r["guard_element"]}, **info),
                      documents=docs, geometry_source=r.get("geometry_source") or "SCHEDULE_ONLY",
                      geometry_confidence="TOLERANCE_CERTIFIED" if ev == "SOURCE_DERIVED" else "INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="SOURCE", rfi=rfi,
                      notes=f"{METHOD}: {piece.lower().replace('_', ' ')} by checker-verified record ({src['task']}, "
                            f"MERGED {src['merge_commit']})")
    if st == "RELEASED":
        evs = "VERIFIED" if r.get("verified_by") else "DRAWING-CONFIRMED"
    return ln, evs, v


def _retire(ln, why, note, verif, piece, codes, drawing_reference, downstream=()):
    after = copy.deepcopy(ln)
    after.update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None, bounded_range=None, gross=None,
                 rfi=None)
    A305._note(after, note)
    return A305._change(piece, "REPLACE", ln, after, drawing_reference=drawing_reference[:300], held=[],
                        downstream=list(downstream), verification=verif, evidence_status="DRAWING-CONFIRMED",
                        codes=codes, why=why)


def solid_changes(inputs, lines, earlier_changed=(), v306_changed=()):
    """the verified-solid pieces on the V3.0.6 lines. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        return [], [{"piece": p, "state": "NO_PROJECT_INPUT"} for p in ("POOL_CONCRETE", "DOME_SHELL")]
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier, v306 = set(earlier_changed), set(v306_changed)
    changes, logs, touched = [], [], set()
    for pc in inputs["pieces"]:
        piece, sc, src = pc["piece"], pc["scope"], pc["source"]
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "source": src["file"], "source_sha256": src["sha256"]}
        recs = {f"{r['element']}:{r['component']}": r for r in pc.get("records") or ()}
        named = {(x["element_id"], x["floor"]): x for x in sc.get("supersede_lines") or ()}
        other = {(x["element_id"], x["floor"]): x for x in sc.get("other_elements") or ()}
        if set(named) & set(other):
            raise InputsError(f"piece {piece}: a scope line is accounted for twice (supersede / other)")
        log = {"piece": piece, "state": "RUN", "source": src, "item_code": pc["item_code"], "unit": pc["unit"],
               "scope": {"physical_element": sc["physical_element"], "floors": sc["floors"]}, "scope_lines": [],
               "retired": [], "records": [], "evidence_status": {}, "line_group": pc.get("line_group")}
        seen = set()
        conv_total = 0.0
        for ln in _scope_lines(pc, lines):
            k = ((ln.get("location") or {}).get("element_id"), ln["location"].get("floor"))
            entry = {"line_id": ln["line_id"], "element_id": k[0], "floor": k[1],
                     "evidence_state": ln["evidence_state"], "quantity": A302._q(A30._qty(ln)),
                     "held_by_v3_0_6": (_held_by_v306(ln) or (None,))[0]}
            if k in other:
                seen.add(k)
                log["scope_lines"].append(dict(entry, accounted="OTHER_ELEMENT", why=other[k]["why"]))
                continue
            if k not in named:
                raise InputsError(f"piece {piece}: candidate line {ln['line_id']} ({k[0]} {k[1]}, "
                                  f"{A302._q(A30._qty(ln))}) is of the same item and physical element on a scope "
                                  "floor and is neither superseded by name nor declared another element: an "
                                  "integration that only adds is refused")
            x = named[k]
            _check_replaceable(ln, earlier, v306)
            cq = _carried_qty(ln)
            if cq is None or abs(float(cq) - float(x["convention_qty"])) > 1e-6:
                raise InputsError(f"piece {piece}: line {k[0]} carries {cq} m3, the inputs state "
                                  f"{x['convention_qty']}: the superseded figure must be the one the line carries")
            seen.add(k)
            conv_total += float(cq)
            note = (f"{METHOD}: SUPERSEDED - convention {_r(cq)} {ln['unit']} (V3.0.6 state {ln['evidence_state']}) "
                    f"replaced by the checker-verified {piece.lower().replace('_', ' ')} lines of {src['task']} "
                    f"(MERGED {src['merge_commit']}): {x['why']}")
            changes.append(_retire(ln, x["why"], note, verif, piece, ["SUPERSEDED_BY_VERIFIED"],
                                   x.get("drawing_reference") or src["file"]))
            touched.add(ln["line_id"])
            log["scope_lines"].append(dict(entry, accounted="SUPERSEDED", why=x["why"], convention_qty=_r(cq)))
        missing = (set(named) | set(other)) - seen
        if missing:
            raise InputsError(f"piece {piece}: scope names line(s) the candidate does not have: {sorted(missing)}")
        for x in sc.get("retire_lines") or ():
            hit = [ln for ln in lines if (ln.get("location") or {}).get("element_id") == x["element_id"]
                   and ln["location"].get("floor") == x["floor"] and ln["item_code"] == x["item_code"]]
            if len(hit) != 1:
                raise InputsError(f"piece {piece}: retire line {x['element_id']} {x['floor']} found {len(hit)} "
                                  "time(s); exactly one is required")
            ln = hit[0]
            if ln["line_id"] in touched:
                raise ValueError(f"{METHOD}: line {ln['line_id']} retired and superseded")
            _check_replaceable(ln, earlier, v306)
            if _held_by_v306(ln) is None:
                raise InputsError(f"piece {piece}: retire line {x['element_id']} was not held by V3.0.6: a live line "
                                  "of another item is never retired by an integration (it goes to the guard first)")
            cq = _carried_qty(ln)
            if cq is None or abs(float(cq) - float(x["convention_qty"])) > 1e-6:
                raise InputsError(f"piece {piece}: retire line {x['element_id']} carries {cq}, the inputs state "
                                  f"{x['convention_qty']}")
            note = (f"{METHOD}: RETIRED - not {ln['item_code']}: {x['why']}; the element is carried once by "
                    f"{x['counted_by']} ({piece.lower().replace('_', ' ')}, {src['task']}); V3.0.6 figure {_r(cq)} "
                    f"{ln['unit']} kept as information, never summed")
            changes.append(_retire(ln, x["why"], note, verif, piece, ["RETIRED_MISREAD", f"COUNTED_BY {x['counted_by']}"],
                                   x.get("drawing_reference") or src["file"]))
            touched.add(ln["line_id"])
            log["retired"].append({"line_id": ln["line_id"], "item_code": ln["item_code"],
                                   "element_id": x["element_id"], "floor": x["floor"], "info_qty": _r(cq),
                                   "counted_by": x["counted_by"], "why": x["why"]})
        released = 0.0
        for key, r in recs.items():
            ln, evs, v = record_line(pid, rev, docs, piece, pc, r)
            if ln["line_id"] in have:
                raise ValueError(f"{METHOD}: record {key} repeats a candidate line id")
            have.add(ln["line_id"])
            held = []
            if ln["evidence_state"] != "SOURCE_DERIVED":
                held = [{"what": f"{r['element']} {r['component']}", "why": ln["rfi"]["question"], "range": None}]
            else:
                released += ln["measured_net"]
            changes.append(A305._change(piece, "ADD", None, ln, drawing_reference=r.get("printed") or src["file"],
                                        held=held, downstream=list(r.get("downstream") or ()),
                                        verification=dict(verif, record_verified_by=r.get("verified_by")),
                                        evidence_status=evs, guard_element=r["guard_element"]))
            log["records"].append({"record": key, "line_id": ln["line_id"], "floor": r["floor"],
                                   "evidence_state": ln["evidence_state"], "evidence_status": evs,
                                   "quantity": ln["measured_net"], "recomputed_m3": _r(v)})
            log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        log["totals"] = {"released_added": _r(released), "convention_superseded": _r(conv_total),
                         "item_move": _r(released - conv_total)}
        for k, v in (pc.get("declared_totals") or {}).items():
            if k in log["totals"] and abs((log["totals"][k] or 0) - v) > 0.0006:
                raise ValueError(f"{METHOD}: piece {piece} {k} {log['totals'][k]} != the declared {v}")
        log["declared_totals"] = pc.get("declared_totals") or {}
        logs.append(log)
    return changes, logs


# ================================================================================================ guard re-check
def _carried_map(lines, added):
    """{line id: register element / part} for the lines that carry a drawn part without being route lines: the V3.0.6
    ledger lines and placeholders (from their own inputs) and the lines this version adds."""
    out = {}
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        ge = inp.get("guard_element")
        if isinstance(ge, dict) and ge.get("element_id"):
            out[ln["line_id"]] = {"element_id": ge["element_id"], "part": ge.get("part", "WHOLE")}
        elif inp.get("policy") == A306.PIECES["DEFAULT_GUARD"]["policy"] and inp.get("element") and inp.get("part"):
            out[ln["line_id"]] = {"element_id": inp["element"], "part": inp["part"]}
    for c in added:
        out[c["after"]["line_id"]] = dict(c["guard_element"])
    return out


def guard_changes(inputs, lines, added=(), touched=()):
    """the default guard over the V3.0.7 view (V3.0.6 lines with this version's replacements) + the added lines."""
    g = (inputs or {}).get("guard")
    if not g:
        return [], {"piece": "DEFAULT_GUARD", "state": "NO_PROJECT_INPUT"}
    src = g["source"]
    hold, rec = set(g["holding_checks"]), set(g.get("recorded_checks") or ())
    disabled = tuple(c for c in A306.GUARD_CHECKS if c not in hold | rec)
    allv = list(lines) + [c["after"] for c in added]
    glines, carried = A306._guard_lines(g, allv, _carried_map(lines, added))
    ev = g["evidence"]
    res = DG.guard(glines + carried, documents=ev["documents"], printed=ev["printed"], inventory=ev["inventory"],
                   members=ev.get("members") or (), revisions=ev.get("revisions") or (), disabled=disabled)
    by_line = A306._findings_by_line(res["findings"])
    gby = {x["id"]: x for x in glines}
    byid = {ln["line_id"]: ln for ln in lines}
    addid = {c["after"]["line_id"] for c in added}
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "evidence": g["evidence_file"], "evidence_sha256": g["evidence_sha256"],
             "conventions": g["conventions_file"], "conventions_sha256": g["conventions_sha256"]}
    new_ids = set(g.get("new_records") or ())
    log = {"piece": "DEFAULT_GUARD", "state": "RUN", "evidence_file": g["evidence_file"],
           "evidence_sha256": g["evidence_sha256"], "holding_checks": sorted(hold), "recorded_checks": sorted(rec),
           "convention_lines": len(glines), "lines_checked": len(glines) + len(carried), "findings_by_code": {},
           "held_live_new": [], "listed_not_live": [], "recorded_only": 0, "rebased_on_printed": [],
           "new_records": {i: [] for i in sorted(new_ids)}, "silent_omissions": []}
    for f in res["findings"]:
        log["findings_by_code"][f["code"]] = log["findings_by_code"].get(f["code"], 0) + 1
        for c in f.get("citation") or ():
            if c.get("printed_id") in new_ids:
                ln = byid.get(f["line_id"]) or {}
                log["new_records"][c["printed_id"]].append(
                    {"line_id": f["line_id"], "item_code": ln.get("item_code"),
                     "element_id": (ln.get("location") or {}).get("element_id"), "code": f["code"],
                     "line_state": ln.get("evidence_state"), "convention": f["detail"].split(":", 1)[0]})
    changes = []
    for lid, fl in sorted(by_line.items()):
        if lid in addid:
            raise ValueError(f"{METHOD}: the guard flags a line this version adds ({lid}): "
                             f"{[f['code'] for f in fl]}; a verified record is not integrated over a guard finding")
        ln = byid.get(lid)
        if ln is None:
            raise ValueError(f"{METHOD}: guard finding on an unknown line {lid}")
        holding = [f for f in fl if f["check"] in hold]
        log["recorded_only"] += sum(1 for f in fl if f["check"] in rec)
        live = ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None
        if live and g.get("equal_value_rebase") and lid in gby:
            same = [f for f in holding if A306._same_as_printed(f, gby[lid])]
            if same:
                log["rebased_on_printed"].append({"line_id": lid, "item_code": ln["item_code"],
                                                  "element_id": (ln.get("location") or {}).get("element_id"),
                                                  "quantity": A302._q(A30._qty(ln)),
                                                  "citations": [c["printed_id"] for f in same
                                                                for c in f.get("citation") or ()]})
                holding = [f for f in holding if f not in same]
        if not holding:
            continue
        entry = {"line_id": lid, "item_code": ln["item_code"], "floor": (ln.get("location") or {}).get("floor"),
                 "element_id": (ln.get("location") or {}).get("element_id"), "evidence_state": ln["evidence_state"],
                 "quantity": A302._q(A30._qty(ln)), "codes": sorted({f["code"] for f in holding})}
        if not live:
            log["listed_not_live"].append(entry)
            continue
        if lid in touched:
            raise ValueError(f"{METHOD}: the guard holds a line this version replaces ({lid})")
        if ln.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
            raise ValueError(f"{METHOD}: line {lid} is {ln.get('approval_state')}: an approved line is never re-held")
        cites = [c for f in holding for c in f.get("citation") or ()]
        why = "; ".join(f"{f['code']}: {f['detail']}" for f in holding)
        after = copy.deepcopy(ln)
        after.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_range=None, gross=None)
        after["rfi"] = {"question": ("DEFAULT GUARD: " + why)[:900],
                        "unlocks": (ln.get("location") or {}).get("element_id")}
        after["calculation"] = dict(after["calculation"], inputs=dict(
            after["calculation"].get("inputs") or {},
            default_guard_v307={"policy": PIECES["DEFAULT_GUARD"]["policy"], "info_qty_v3_0_6": A30._qty(ln),
                                "findings": [{k: f.get(k) for k in ("check", "code", "detail", "citation")}
                                             for f in holding]}))
        A305._note(after, f"{METHOD}: HELD by the default guard re-check ({', '.join(entry['codes'])}); V3.0.6 "
                          f"figure {entry['quantity']} {ln['unit']} kept as information, never summed")
        changes.append(A305._change("DEFAULT_GUARD", "REPLACE", ln, after,
                                    drawing_reference="; ".join(f"{c.get('printed_id')}: {c.get('value')} "
                                                                f"{c.get('unit')} ({c.get('doc')})"
                                                                for c in cites)[:600],
                                    held=[{"what": f"{ln['item_code']} {entry['element_id']}", "why": why[:900],
                                           "range": None}], downstream=[], verification=verif,
                                    evidence_status="HELD", codes=entry["codes"], citations=cites))
        log["held_live_new"].append(entry)
    for f in res["findings"]:
        if f["code"] == "SILENT_OMISSION":
            log["silent_omissions"].append(f["detail"])
    if log["silent_omissions"]:
        raise InputsError(f"{METHOD}: drawn element part(s) carried by no line: {log['silent_omissions']} (the V3.0.6 "
                          "placeholders carry their parts; a part this version leaves silent is refused)")
    log["findings_by_code"] = dict(sorted(log["findings_by_code"].items()))
    log["guard_summary"] = res["summary"]
    return changes, log


# ================================================================================================ integrate / write
def changes_for(inputs, l306, earlier_changed=(), v306_changed=()):
    """the verified solids first, then the guard re-check over the result. -> (changes, logs)"""
    ch_s, logs = solid_changes(inputs, l306, earlier_changed, v306_changed)
    rep = {c["before"]["line_id"]: c["after"] for c in ch_s if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l306]
    ch_g, log_g = guard_changes(inputs, view, [c for c in ch_s if c["action"] == "ADD"], set(rep))
    return ch_s + ch_g, logs + [log_g]


def integrate(l306, v307_changes):
    """-> (V3.0.7 lines, identity). Every line outside the V3.0.7 rows is byte-identical to the V3.0.6 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l306}
    rep, adds = {}, []
    for c in v307_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.6 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.6 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l306] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    by306 = {ln["line_id"]: ln for ln in l306}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by306[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l306):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.7 rows differ from {EXTENDS}")
    ident = {"v3_0_6_lines": len(l306), "v3_0_7_lines": len(out), "v3_0_7_rows": len(v307_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_6": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b306 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_6")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        info = None
        if c["before"] is not None:
            info = _carried_qty(c["before"])
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_6": b306, "convention_figure_before": _r(info),
                     "after_v3_0_7": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_6",
              "convention_figure_before", "v3_0_7", "evidence_status", "release_status", "codes", "drawing_reference",
              "verification", "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_6": A302._q(r["before_v3_0_6"]),
                       "convention_figure_before": "" if r["convention_figure_before"] is None
                       else f"{r['convention_figure_before']:.6g}", "v3_0_7": A302._q(r["after_v3_0_7"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}"
                                       + (f" / {r['verification']['record_verified_by']}"
                                          if r["verification"].get("record_verified_by") else ""),
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_6", "vs_released_v2_9", "v2_9", "v3_0_6",
            "v3_0_7")


def diff_rows(l306, l307, released_lines=None):
    b306 = {ln["line_id"]: ln for ln in l306}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l307:
        o = b306.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_6": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_6": A302._q(A30._qty(o)) if o else "", "v3_0_7": A302._q(A30._qty(ln))})
    return out


def write(out, l306, v307_changes, logs, inputs, released_lines=None):
    """the V3_0_7_* files beside the V3_0_6_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l307, ident = integrate(l306, v307_changes)
    rows = ledger_rows(v307_changes, released_lines)
    diff = diff_rows(l306, l307, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_6", {}).setdefault(d["vs_v3_0_6"], 0)
        dsum["vs_v3_0_6"][d["vs_v3_0_6"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t306, t307 = A304.code_totals(l306), A304.code_totals(l307)
    moved = {k: {"v3_0_6": t306.get(k), "v3_0_7": t307.get(k)} for k in sorted(set(t306) | set(t307))
             if t306.get(k) != t307.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "item_code", "unit", "source", "scope",
                                                          "declared_totals", "line_group")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "mapping_additions", "placeholders",
                                                      "new_records")}},
           "beside_never_summed": (inputs or {}).get("beside") or [],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_7_BOQ_LINES.json": BL.dumps(l307),
             "V3_0_7_BOQ_LINES.csv": A30._lines_csv(l307),
             "V3_0_7_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_7_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_7_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_7_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "load_inputs", "spherical_cap_shell_m3", "dims_check", "solid_changes",
           "guard_changes", "changes_for", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
