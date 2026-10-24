"""ARCH_TAKEOFF_V3.0.10 (T-232): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.9 (engine.source.arch_v30,
arch_v301 .. arch_v309), extended with doors and windows as BOTH counts (pcs) and measured m2, from ONE opening list.
Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5); rollback
is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.10`):
  1. the run is the V3.0.9 candidate exactly: its V3_0_* .. V3_0_9_* files are written unchanged (arch_v30 .. arch_v309
     are not edited);
  2. OPENING RECORDS (piece OPENINGS, project inputs URBAN_V3010_INPUTS_V1): one record per drawn opening of a door or
     window class, taken from checker-merged opening ledgers (sources named with file sha256, task, merge commit and
     checker run). ONE opening definition serves the count and the area (and is the id the masonry / finish deductions
     of the same opening carry): the structural opening between the jambs (reveals), never the leaf or the frame; a
     double leaf is ONE opening; window area = the owner's enclosing rectangle on the opening line (Q-32 A), an arch to
     its opening crown, never a surround band or an archivolt;
  3. every candidate line of the piece's item codes on the scope floors is accounted for before a line is added (T-179 /
     T-231 lesson): superseded by name with the opening it was (the figure it carries is stated and must be the line's),
     or declared another element; an unaccounted line, or a named line the candidate does not have, refuses the run;
  4. LINES, aggregation key written on every line (item code / floor / part): for each item code and floor, a pcs line
     and an m2 line per part, where part is
       SETTLED:<evidence>  openings whose class, count and both dimensions are established: pcs = the number of openings
                           (SOURCE_DERIVED, DRAWING-CONFIRMED count), m2 = sum of width x height (SOURCE_DERIVED when
                           every height is DRAWING-CONFIRMED, PROVISIONAL when it rests on an owner-approved fallback,
                           ASSUMED - OWNER-APPROVED with its source on the line);
       HELD                openings with a hold cause on that unit: BOUNDED_EXPOSURE, the sum of each opening's
                           [low, high] (a class-held opening is answered in EACH candidate class with low 0, T-181 rule
                           4, so no class line is silently compared low);
       HELD_NO_FIGURE      held openings without a bound on that unit: BLOCKED_RFI, figures only as information.
     A per-opening table (opening ids, width, height, area, count, status) sits in each line's inputs. pcs and m2 are
     never converted into each other;
  5. the SAME-OPENINGS rule (owner 2026-10-23: one opening definition for count and area): for every item code the
     opening ids of its pcs lines equal the opening ids of its m2 lines, each id at most once per unit and code; an
     opening counted in pcs but missing from m2 (or the reverse) refuses the run, as does an opening settled in two
     classes; an area that disagrees with width x height by more than AREA_TOL_M2 is refused; missing is never 0;
  6. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.10 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  7. the V3_0_10_* files are written beside them: every line outside the V3.0.10 rows is byte-identical to the V3.0.9
     line (asserted on every run), and V3_0_10_DIFF.csv lists every line against V3.0.9 and against the released V2.9.

Rules: owner 2026-10-23 17:50 ("doors and windows must report both counts and measured m2, with explicit aggregation and
consistent opening definitions"); Q-32 A (window m2 = enclosing rectangle to the top of the opening); Q-38 A (curved
glazing in a straight opening: the printed width); Q-39 C (window curved on plan: outer arc); Q-55 C (door head 2.20
only where no sheet prints one: ASSUMED - OWNER-APPROVED); UP-DOOR-CLS-001 .. 005 (door classes); UP-QTY-STATUS-001
(held is a range or blocked, never 0); WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5 / s.8; ERS 2026-10-22 s.2.2, s.3, s.7.
Nothing here names a project, a sheet, a layer, a room or a coordinate; every number comes from the run or the inputs.
"""

from __future__ import annotations

import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v308 as A308
from engine.source import arch_v309 as A309

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.10"
EXTENDS = A309.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T232_ARCH_V3_0_10"
LEDGER_SCHEMA = "URBAN_V3010_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V3010_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
KINDS = ("DOOR", "WINDOW")
PCS_STATES = ("SETTLED", "HELD")
M2_STATES = ("RELEASED", "BOUNDED", "UNQUANTIFIED")
DIM_STATUS = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED")
RELEASED_STATUS = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED")
HELD_STATUS = ("HELD", "UNKNOWN")
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
NO_FIGURE = A309.NO_FIGURE
AREA_TOL_M2 = 0.0005                    # stated area vs width x height (3-decimal ledgers)
MAX_DIM_M = 20.0                        # an opening dimension above this is a unit slip (mm given as m), refused
UNITS = ("pcs", "m2")
InputsError = A307.InputsError
_num = A307._num

PIECES = {
    "OPENINGS": {
        "module": "engine/source/arch_v3010.py (checker-merged opening records: pcs and m2 from one opening list)",
        "policy": "OPENINGS_PCS_AND_M2_V1", "rule_id": "Q-32", "rule_version": "owner-2026-10-19",
        "owner_rules": ["owner 2026-10-23 17:50 (doors and windows: counts AND measured m2, explicit aggregation, one "
                        "opening definition)",
                        "Q-32 A (window m2 = enclosing rectangle on the opening line, to the top of the opening)",
                        "Q-38 A (curved glazing in a straight opening: the printed width)",
                        "Q-39 C (a window curved on plan: the outer arc)",
                        "Q-55 C (door head 2.20 m only where no sheet prints one: ASSUMED - OWNER-APPROVED)",
                        "UP-DOOR-CLS-001 .. 005 (door classes by the spaces on each side)",
                        "UP-QTY-STATUS-001 (a held opening is a range or blocked, never 0)"],
        "owner_manual_method": "manual QS schedule of doors and windows: one row per type and floor, the number of "
                               "openings and the area of each (width x height of the opening; a door 2.20 high where "
                               "no sheet prints its head), summed per type; a double leaf is one door",
        "drawing_method": "each opening from the drawn tags and jamb lines of the plans, its height from the printed "
                          "chains or the vector geometry of the elevations / sections re-datumed to the floor's "
                          "level, an arch to its opening crown (not the band or archivolt around it); the same "
                          "opening id carries the count, the area and the masonry / finish deductions"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A309.WAITING)
WAITING.update({
    "OPENING_INVENTORY_ENGINE_FREE": "T-249: the opening list is the checker-merged census (seeded from the engine's own "
                                     "list and corrected by drawing reads); an opening both missed is not excluded until "
                                     "the tag-based inventory replaces the seed",
    "ARCHED_WINDOW_W17_OWNER_ITEM": "owner item Q-76 (the curved arched window's crown: opening arch vs archivolt): "
                                    "HELD as a range, never the larger end",
    "OPENING_DEDUCTIONS_IN_FINISH_LINES": "the masonry / plaster / paint deductions of the same opening ids are wired "
                                          "by their own packages (T-237 crosswalk, T-244); not changed here",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


# ================================================================================================ dimensions
def _dim(d, what):
    """a dimension {value} or {range: [low, high]} -> (low, high)."""
    if not isinstance(d, dict):
        raise InputsError(f"{what}: a dimension is {{value}} or {{range: [low, high]}}")
    if _num(d.get("value")):
        if d["value"] <= 0:
            raise InputsError(f"{what}: a dimension is > 0 (missing is never 0)")
        if d["value"] > MAX_DIM_M:
            raise InputsError(f"{what}: {d['value']} m is not an opening dimension (unit slip? metres only)")
        return float(d["value"]), float(d["value"])
    rg = d.get("range")
    if isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg) and 0 < rg[0] <= rg[1]:
        if rg[1] > MAX_DIM_M:
            raise InputsError(f"{what}: {rg[1]} m is not an opening dimension (unit slip? metres only)")
        return float(rg[0]), float(rg[1])
    raise InputsError(f"{what}: a dimension is {{value}} or {{range: [low, high]}}, 0 < low <= high")


def area_of(o):
    """(low, high) m2 of one opening from its width and height; None when a dimension is not established."""
    if o.get("width") is None or o.get("height") is None:
        return None
    wl, wh = _dim(o["width"], f"opening {o.get('id')} width")
    hl, hh = _dim(o["height"], f"opening {o.get('id')} height")
    return wl * hl, wh * hh


def _range_ok(rg):
    return isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg) and 0 <= rg[0] <= rg[1]


def _check_opening(o, codes, floors):
    oid = o.get("id")
    if not oid:
        raise InputsError("every opening record has an id (the census id that the deductions carry too)")
    if o.get("kind") not in KINDS:
        raise InputsError(f"opening {oid}: kind {o.get('kind')!r} not one of {KINDS}")
    if o.get("floor") not in floors:
        raise InputsError(f"opening {oid}: floor {o.get('floor')!r} outside the scope {floors}")
    cls = o.get("classes")
    if not (isinstance(cls, list) and cls and len(set(cls)) == len(cls) and set(cls) <= set(codes)):
        raise InputsError(f"opening {oid}: classes must be item codes of the piece, each once")
    if len(cls) > 1 and not o.get("class_hold"):
        raise InputsError(f"opening {oid}: two candidate classes need the class hold cause (class_hold)")
    if not o.get("opening_definition"):
        raise InputsError(f"opening {oid}: opening_definition (structural opening / leaf / frame) is required")
    if not o.get("sources"):
        raise InputsError(f"opening {oid}: sources (checker-merged ledgers) are required")
    held_class = len(cls) > 1
    # ---- count
    p = o.get("pcs") or {}
    if p.get("state") not in PCS_STATES:
        raise InputsError(f"opening {oid}: pcs.state {p.get('state')!r} not one of {PCS_STATES}")
    if p["state"] == "SETTLED":
        if held_class or o.get("class_hold"):
            raise InputsError(f"opening {oid}: a class-held opening is never a settled count")
        if p.get("count") != 1:
            raise InputsError(f"opening {oid}: a settled opening counts 1 (a double leaf is ONE opening)")
    else:
        if not p.get("reasons"):
            raise InputsError(f"opening {oid}: a held count names why")
        if not (_range_ok(p.get("range")) and p["range"][1] >= 1):
            raise InputsError(f"opening {oid}: a held count carries a range [low, high], high >= 1 (never 0)")
        if held_class and p["range"][0] != 0:
            raise InputsError(f"opening {oid}: a class-held opening answers each candidate class from 0")
    # ---- area
    m = o.get("m2") or {}
    st = m.get("state")
    if st not in M2_STATES:
        raise InputsError(f"opening {oid}: m2.state {st!r} not one of {M2_STATES}")
    a = area_of(o)
    if st == "RELEASED":
        if held_class or o.get("class_hold"):
            raise InputsError(f"opening {oid}: a class-held opening's area is never released")
        if a is None or abs(a[1] - a[0]) > 1e-12:
            raise InputsError(f"opening {oid}: a released area has both dimensions established (a range is BOUNDED)")
        if not (_num(m.get("value")) and m["value"] > 0):
            raise InputsError(f"opening {oid}: a released area carries a value > 0 (missing is never 0)")
        if abs(a[0] - m["value"]) > AREA_TOL_M2:
            raise InputsError(f"opening {oid}: area {m['value']} != width x height {round(a[0], 4)}")
        hs = (o.get("height") or {}).get("status")
        ws = (o.get("width") or {}).get("status")
        if hs not in DIM_STATUS or ws not in DIM_STATUS:
            raise InputsError(f"opening {oid}: a released area names the status of its width and height {DIM_STATUS}")
        if m.get("evidence_status") not in RELEASED_STATUS:
            raise InputsError(f"opening {oid}: a released area is one of {RELEASED_STATUS}")
        want = "ASSUMED - OWNER-APPROVED" if "ASSUMED - OWNER-APPROVED" in (hs, ws) else "DRAWING-CONFIRMED"
        if m["evidence_status"] != want and not (m["evidence_status"] == "VERIFIED" and want == "DRAWING-CONFIRMED"):
            raise InputsError(f"opening {oid}: area status {m['evidence_status']!r}, its dimensions make it {want!r}")
        if want == "ASSUMED - OWNER-APPROVED" and not o.get("assumption"):
            raise InputsError(f"opening {oid}: an owner-approved fallback stays on the line with its source "
                              "(assumption, WORKFLOW_CONTROLS s.4)")
        if m["evidence_status"] == "VERIFIED" and not m.get("verified_by"):
            raise InputsError(f"opening {oid}: VERIFIED names the checker run that re-measured the opening")
    else:
        if not m.get("reasons") or m.get("evidence_status") not in HELD_STATUS:
            raise InputsError(f"opening {oid}: a {st} area names why and its status HELD / UNKNOWN")
    if st == "BOUNDED":
        rg = m.get("range")
        if not (_range_ok(rg) and rg[1] > 0):
            raise InputsError(f"opening {oid}: a BOUNDED area carries a range [low, high], 0 <= low <= high, high > 0")
        if held_class and rg[0] != 0:
            raise InputsError(f"opening {oid}: a class-held opening answers each candidate class from 0 m2")
        if a is not None and not held_class:
            if abs(a[0] - rg[0]) > AREA_TOL_M2 or abs(a[1] - rg[1]) > AREA_TOL_M2:
                if not m.get("range_basis"):
                    raise InputsError(f"opening {oid}: range {rg} != width x height {round(a[0], 4)} .. "
                                      f"{round(a[1], 4)} and no range_basis says why")
        if a is not None and held_class and abs(a[1] - rg[1]) > AREA_TOL_M2:
            raise InputsError(f"opening {oid}: class-held range top {rg[1]} != width x height {round(a[1], 4)}")


def load_inputs(doc, project_id=None):
    """URBAN_V3010_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "OPENINGS", "item_codes": [...], "source": {...}, "sources": [...],
                     "scope": {"floors", "supersede_lines": [{element_id, floor, item_code, unit, opening, why,
                                                              carried}],
                               "other_elements": [{element_id, floor, item_code, why}]},
                     "openings": [{id, kind, floor, classes, class_hold, leaves, opening_definition,
                                   width {value | range, status, source}, height {value | range, status, source},
                                   assumption, pcs {state, count | range, reasons}, m2 {state, value | range,
                                   evidence_status, verified_by, reasons, range_basis, info}, sources, freelancer}],
                     "excluded": [{id, why}] (census openings that are no door / window supply item),
                     "declared_totals": {item_code: {"pcs": {settled, held: [low, high], no_figure},
                                                     "m2": {released, bounded: [low, high], unquantified}}}}],
         "guard": as URBAN_V307_INPUTS_V1 "guard"}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p != "OPENINGS" or p in seen:
            raise InputsError(f"piece {p!r}: OPENINGS, once")
        seen.add(p)
        codes = pc.get("item_codes")
        if not (isinstance(codes, list) and codes and all(codes) and len(set(codes)) == len(codes)):
            raise InputsError(f"piece {p}: item_codes are required, each once")
        A307._source(pc.get("source"), f"piece {p}")
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
        sc = pc.get("scope") or {}
        if not sc.get("floors"):
            raise InputsError(f"piece {p}: scope needs floors")
        ids = set()
        for o in pc.get("openings") or ():
            if o.get("id") in ids:
                raise InputsError(f"piece {p}: opening {o.get('id')} listed twice (one record per opening)")
            _check_opening(o, codes, sc["floors"])
            ids.add(o["id"])
        if not ids:
            raise InputsError(f"piece {p}: no openings")
        for x in pc.get("excluded") or ():
            if not x.get("id") or not x.get("why") or x["id"] in ids:
                raise InputsError(f"piece {p}: an excluded opening has an id, a why, and no opening record")
        for k in ("supersede_lines", "other_elements"):
            for x in sc.get(k) or ():
                if not x.get("element_id") or not x.get("floor") or not x.get("why") or x.get("item_code") not in codes:
                    raise InputsError(f"piece {p}: every scope.{k} entry has element_id, floor, item_code and why")
                if k == "supersede_lines":
                    if x.get("carried") is None:
                        raise InputsError(f"piece {p}: scope.{k} {x['element_id']} states the figure it carries "
                                          f"(or {NO_FIGURE})")
                    if x.get("opening") not in ids:
                        raise InputsError(f"piece {p}: superseded line {x['element_id']} names an opening record "
                                          f"({x.get('opening')!r} is none)")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ grouping
def _part_pcs(o, code):
    p = o["pcs"]
    if p["state"] == "SETTLED":
        return "SETTLED:DRAWING-CONFIRMED", 1.0, None
    return "HELD", None, [float(p["range"][0]), float(p["range"][1])]


def _part_m2(o, code):
    m = o["m2"]
    if m["state"] == "RELEASED":
        return f"SETTLED:{m['evidence_status']}", float(m["value"]), None
    if m["state"] == "BOUNDED":
        return "HELD", None, [float(m["range"][0]), float(m["range"][1])]
    return "HELD_NO_FIGURE", None, None


def group_openings(pc):
    """{(item_code, floor, unit, part): [entry]} with entry {id, qty | range, ...}; the same-openings rule checked."""
    groups = {}
    ids_by = {}
    settled_class = {}
    for o in pc["openings"]:
        held_class = len(o["classes"]) > 1
        for code in o["classes"]:
            for unit, fn in (("pcs", _part_pcs), ("m2", _part_m2)):
                part, q, rg = fn(o, code)
                k = (code, unit)
                if o["id"] in ids_by.setdefault(k, set()):
                    raise InputsError(f"opening {o['id']}: answered twice in {code} {unit}")
                ids_by[k].add(o["id"])
                a = area_of(o)
                rec = o["pcs"] if unit == "pcs" else o["m2"]
                if part.startswith("SETTLED"):
                    status = part.split(":", 1)[1]
                else:
                    status = rec.get("evidence_status") or "HELD"
                groups.setdefault((code, o["floor"], unit, part), []).append({
                    "id": o["id"], "kind": o["kind"], "qty": q, "range": rg,
                    "width": o.get("width"), "height": o.get("height"),
                    "area_from_dims": None if a is None else [_r(a[0], 4), _r(a[1], 4)],
                    "leaves": o.get("leaves"), "class_hold": o.get("class_hold"),
                    "candidate_classes": o["classes"] if held_class else None, "status": status,
                    "reasons": list(rec.get("reasons") or ()), "info": rec.get("info")})
        if not held_class:
            if o["id"] in settled_class:
                raise InputsError(f"opening {o['id']}: settled in two classes")
            settled_class[o["id"]] = o["classes"][0]
    for v in groups.values():          # the order of the records never changes a line
        v.sort(key=lambda e: e["id"])
    # the same-openings rule: one opening list per item code for both units
    for code in pc["item_codes"]:
        a, b = ids_by.get((code, "pcs"), set()), ids_by.get((code, "m2"), set())
        if a != b:
            raise InputsError(f"{code}: the pcs and m2 lines must come from the same openings: in pcs only "
                              f"{sorted(a - b)}, in m2 only {sorted(b - a)}")
    return groups


def group_line(pid, rev, docs, pc, key, entries):
    """one BOQ line for one (item code, floor, unit, part). -> (line, evidence status, held)"""
    from engine.source import boq_line as BL
    code, floor, unit, part = key
    p, src = PIECES["OPENINGS"], pc["source"]
    eid = f"OPENINGS:{A305._slug(code)}:{floor}:{A305._slug(part)}"
    ids = [e["id"] for e in entries]
    agg = {"item_code": code, "floor": floor, "unit": unit, "part": part}
    reasons = sorted({f"{e['id']}: {r}" for e in entries for r in e["reasons"]})
    if part.startswith("SETTLED"):
        evs = part.split(":", 1)[1]
        q = sum(e["qty"] for e in entries)
        ev = "SOURCE_DERIVED" if (unit == "pcs" or evs in ("DRAWING-CONFIRMED", "VERIFIED")) else "PROVISIONAL"
        br, rfi, net = None, None, _r(q, 4)
        formula = (f"count of the openings {', '.join(ids)}" if unit == "pcs" else
                   "sum of width x height of the openings " + " + ".join(
                       f"{e['id']} {_r(e['qty'], 4)}" for e in entries))
    elif part == "HELD":
        evs = "HELD"
        lo, hi = sum(e["range"][0] for e in entries), sum(e["range"][1] for e in entries)
        ev, net = "BOUNDED_EXPOSURE", None
        br = {"low": _r(lo, 4), "high": _r(hi, 4), "basis": "; ".join(reasons)[:300] or "held openings"}
        rfi = {"question": "; ".join(reasons)[:900], "unlocks": eid}
        formula = "held: " + " + ".join(f"{e['id']} [{_r(e['range'][0], 4)} .. {_r(e['range'][1], 4)}]"
                                        for e in entries)
    else:
        evs = "HELD"
        ev, net, br = "BLOCKED_RFI", None, None
        rfi = {"question": "; ".join(reasons)[:900], "unlocks": eid}
        formula = ("held, no figure: " + "; ".join(reasons))[:400]
    table = [{k: e[k] for k in ("id", "kind", "qty", "range", "width", "height", "area_from_dims", "leaves",
                                "class_hold", "candidate_classes", "status", "reasons", "info")} for e in entries]
    assumptions = sorted({o.get("assumption") for o in pc["openings"] if o["id"] in ids and o.get("assumption")})
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=code, unit=unit, evidence_state=ev,
                      measured_net=net, bounded_range=br, element_id=eid, floor=floor, room_id=None,
                      physical_element=f"{'doors' if code.startswith('DOOR') else 'windows'} ({part.lower()})",
                      subtrade=f"openings by type and floor ({unit})", formula=formula[:600],
                      inputs={"policy": p["policy"], "source": src["file"], "source_sha256": src["sha256"],
                              "aggregation_key": agg, "opening_ids": ids, "openings": table,
                              "evidence_status": evs, "assumptions": assumptions,
                              "same_openings_rule": "the pcs and m2 lines of this item code carry the same opening ids",
                              "opening_definition": "structural opening between the jambs (reveals); a double leaf "
                                                    "is one opening; window area Q-32 A on the opening line"},
                      documents=docs, geometry_source="CAD_VECTOR",
                      geometry_confidence="TOLERANCE_CERTIFIED" if part.startswith("SETTLED") else "INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="BY_SPEC", rfi=rfi,
                      notes=f"{METHOD}: doors / windows by type and floor from checker-merged opening records "
                            f"({src['task']}, MERGED {src['merge_commit']}); pcs and m2 from the same opening ids")
    held = [] if part.startswith("SETTLED") else [{"what": f"{code} {floor} {unit}", "why": rfi["question"],
                                                   "range": [br["low"], br["high"]] if br else None}]
    return ln, evs, held


# ================================================================================================ changes
def _scope_lines(pc, lines):
    sc = pc["scope"]
    codes = set(pc["item_codes"])
    return [ln for ln in lines if ln["item_code"] in codes and (ln.get("location") or {}).get("floor") in sc["floors"]]


def record_changes(inputs, lines, earlier_changed=()):
    """the OPENINGS piece on the V3.0.9 lines. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        return [], [{"piece": "OPENINGS", "state": "NO_PROJECT_INPUT"}]
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    changes, logs, touched = [], [], set()
    for pc in inputs["pieces"]:
        sc, src = pc["scope"], pc["source"]
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "source": src["file"], "source_sha256": src["sha256"],
                 "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                                for s in pc.get("sources") or ()]}
        key = lambda x: (x["element_id"], x["floor"], x["item_code"])  # noqa: E731
        named = {key(x): x for x in sc.get("supersede_lines") or ()}
        other = {key(x): x for x in sc.get("other_elements") or ()}
        if set(named) & set(other):
            raise InputsError("piece OPENINGS: a scope line is accounted for twice (supersede / other)")
        log = {"piece": "OPENINGS", "state": "RUN", "source": src, "sources": pc.get("sources") or [],
               "item_codes": pc["item_codes"], "scope": {"floors": sc["floors"]}, "scope_lines": [], "lines": [],
               "excluded": pc.get("excluded") or [], "evidence_status": {}}
        seen = set()
        sup = {}
        outside = sorted({(ln.get("location") or {}).get("floor") or "" for ln in lines
                          if ln["item_code"] in set(pc["item_codes"])
                          and (ln.get("location") or {}).get("floor") not in sc["floors"]})
        if outside:
            raise InputsError(f"piece OPENINGS: the candidate carries {pc['item_codes']} lines on floor(s) {outside} "
                              "outside the scope: every door / window line is accounted for, on every floor")
        for ln in _scope_lines(pc, lines):
            loc = ln.get("location") or {}
            k = (loc.get("element_id"), loc.get("floor"), ln["item_code"])
            entry = {"line_id": ln["line_id"], "element_id": k[0], "floor": k[1], "item_code": k[2],
                     "unit": ln["unit"], "evidence_state": ln["evidence_state"],
                     "quantity": A302._q(A30._qty(ln)), "earlier_change": ln["line_id"] in earlier}
            if k in other:
                seen.add(k)
                log["scope_lines"].append(dict(entry, accounted="OTHER_ELEMENT", why=other[k]["why"]))
                continue
            if k not in named:
                raise InputsError(f"piece OPENINGS: candidate line {ln['line_id']} ({k[0]} {k[1]} {k[2]}, "
                                  f"{A302._q(A30._qty(ln))}) is inside the scope and is neither superseded by name nor "
                                  "declared another element: an integration that only adds is refused")
            if ln["line_id"] in touched:
                raise ValueError(f"{METHOD}: line {ln['line_id']} superseded twice")
            x = named[k]
            if x.get("unit") not in (None, ln["unit"]):
                raise InputsError(f"piece OPENINGS: line {k[0]} is in {ln['unit']}, the inputs say {x['unit']}")
            A308._check_replaceable(ln, earlier, x)
            cq = A309._carried(ln)
            if not A309._same(cq, x["carried"]):
                raise InputsError(f"piece OPENINGS: line {k[0]} carries {cq}, the inputs state {x['carried']}: the "
                                  "superseded figure must be the one the line carries")
            seen.add(k)
            s = sup.setdefault((ln["item_code"], ln["unit"]), {"value": 0.0, "lines": 0})
            s["lines"] += 1
            if _num(cq):
                s["value"] += float(cq)
            note = (f"{METHOD}: SUPERSEDED - {A302._q(A30._qty(ln))} {ln['unit']} (V3.0.9 state "
                    f"{ln['evidence_state']}) = opening {x['opening']}, now carried in pcs AND m2 by the type / floor "
                    f"lines of {src['task']} (MERGED {src['merge_commit']}): {x['why']}")
            codes = ["SUPERSEDED_BY_RECORD"] + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else [])
            changes.append(A307._retire(ln, x["why"], note, verif, "OPENINGS", codes,
                                        x.get("drawing_reference") or src["file"]))
            touched.add(ln["line_id"])
            log["scope_lines"].append(dict(entry, accounted="SUPERSEDED", why=x["why"], carried=cq,
                                           opening=x["opening"]))
        missing = (set(named) | set(other)) - seen
        if missing:
            raise InputsError(f"piece OPENINGS: scope names line(s) the candidate does not have: {sorted(missing)}")
        groups = group_openings(pc)
        tot = {}
        for gk in sorted(groups):
            ln, evs, held = group_line(pid, rev, docs, pc, gk, groups[gk])
            if ln["line_id"] in have:
                raise ValueError(f"{METHOD}: group {gk} repeats a candidate line id")
            have.add(ln["line_id"])
            code, floor, unit, part = gk
            t = tot.setdefault(code, {"pcs": {"settled": 0.0, "held": [0.0, 0.0], "no_figure": 0},
                                      "m2": {"released": 0.0, "bounded": [0.0, 0.0], "unquantified": 0}})
            if unit == "pcs":
                if part.startswith("SETTLED"):
                    t["pcs"]["settled"] += ln["measured_net"]
                elif ln.get("bounded_range"):
                    t["pcs"]["held"][0] += ln["bounded_range"]["low"]
                    t["pcs"]["held"][1] += ln["bounded_range"]["high"]
                else:
                    t["pcs"]["no_figure"] += len(groups[gk])
            else:
                if part.startswith("SETTLED"):
                    t["m2"]["released"] += ln["measured_net"]
                elif ln.get("bounded_range"):
                    t["m2"]["bounded"][0] += ln["bounded_range"]["low"]
                    t["m2"]["bounded"][1] += ln["bounded_range"]["high"]
                else:
                    t["m2"]["unquantified"] += len(groups[gk])
            changes.append(A305._change("OPENINGS", "ADD", None, ln, drawing_reference=src["file"], held=held,
                                        downstream=[], verification=verif, evidence_status=evs,
                                        guard_element={"element_id": ln["location"]["element_id"], "part": part}))
            log["lines"].append({"key": {"item_code": code, "floor": floor, "unit": unit, "part": part},
                                 "line_id": ln["line_id"], "opening_ids": [e["id"] for e in groups[gk]],
                                 "evidence_state": ln["evidence_state"], "evidence_status": evs,
                                 "quantity": ln["measured_net"], "range": ln.get("bounded_range")})
            log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        log["totals"] = {c: {"pcs": {"settled": _r(t["pcs"]["settled"], 4),
                                     "held": [_r(t["pcs"]["held"][0], 4), _r(t["pcs"]["held"][1], 4)],
                                     "no_figure": t["pcs"]["no_figure"]},
                             "m2": {"released": _r(t["m2"]["released"], 4),
                                    "bounded": [_r(t["m2"]["bounded"][0], 4), _r(t["m2"]["bounded"][1], 4)],
                                    "unquantified": t["m2"]["unquantified"]}} for c, t in sorted(tot.items())}
        log["superseded"] = {f"{c} {u}": {"lines": v["lines"], "value": _r(v["value"], 4)}
                             for (c, u), v in sorted(sup.items())}
        for c, v in (pc.get("declared_totals") or {}).items():
            got = log["totals"].get(c)
            if got is None:
                raise ValueError(f"{METHOD}: declared totals for {c}, which has no line")
            ok = (abs(got["pcs"]["settled"] - v["pcs"]["settled"]) <= 1e-9
                  and all(abs(a - b) <= 1e-9 for a, b in zip(got["pcs"]["held"], v["pcs"]["held"]))
                  and got["pcs"]["no_figure"] == v["pcs"]["no_figure"]
                  and abs(got["m2"]["released"] - v["m2"]["released"]) <= AREA_TOL_M2 * 4
                  and all(abs(a - b) <= AREA_TOL_M2 * 4 for a, b in zip(got["m2"]["bounded"], v["m2"]["bounded"]))
                  and got["m2"]["unquantified"] == v["m2"]["unquantified"])
            if not ok:
                raise ValueError(f"{METHOD}: {c} totals {got} != the declared {v}")
        log["declared_totals"] = pc.get("declared_totals") or {}
        logs.append(log)
    return changes, logs


def check_same_openings(lines):
    """the same-openings rule on finished lines (any candidate that carries this piece's lines): per item code, the
    opening ids of its pcs lines equal those of its m2 lines, each id once per unit and code. -> {code: n openings}"""
    ids = {}
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        if inp.get("policy") != PIECES["OPENINGS"]["policy"]:
            continue
        if ln["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
            continue
        agg = inp.get("aggregation_key") or {}
        if agg.get("item_code") != ln["item_code"] or agg.get("unit") != ln["unit"] or \
                agg.get("floor") != (ln.get("location") or {}).get("floor"):
            raise InputsError(f"line {ln['line_id']}: its aggregation key does not describe the line")
        if ln["unit"] not in UNITS:
            raise InputsError(f"line {ln['line_id']}: an opening line is in pcs or m2, not {ln['unit']}")
        bucket = ids.setdefault(ln["item_code"], {"pcs": [], "m2": []})[ln["unit"]]
        bucket.extend(inp.get("opening_ids") or ())
    out = {}
    for code, u in sorted(ids.items()):
        for unit in UNITS:
            if len(set(u[unit])) != len(u[unit]):
                raise InputsError(f"{code} {unit}: an opening is carried twice")
        if set(u["pcs"]) != set(u["m2"]):
            raise InputsError(f"{code}: the pcs and m2 lines must come from the same openings: in pcs only "
                              f"{sorted(set(u['pcs']) - set(u['m2']))}, in m2 only "
                              f"{sorted(set(u['m2']) - set(u['pcs']))}")
        out[code] = len(set(u["pcs"]))
    return out


# ================================================================================================ integrate / write
def changes_for(inputs, l309, earlier_changed=()):
    """the opening records, then the guard re-check over the result. -> (changes, logs)"""
    ch_r, logs = record_changes(inputs, l309, earlier_changed)
    rep = {c["before"]["line_id"]: c["after"] for c in ch_r if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l309]
    ch_g, log_g = A307.guard_changes(inputs, view, [c for c in ch_r if c["action"] == "ADD"], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch_r + ch_g, logs + [log_g]


def integrate(l309, v3010_changes):
    """-> (V3.0.10 lines, identity). Every line outside the V3.0.10 rows is byte-identical to the V3.0.9 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l309}
    rep, adds = {}, []
    for c in v3010_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.9 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.9 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l309] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    check_same_openings(out)
    by309 = {ln["line_id"]: ln for ln in l309}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by309[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l309):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.10 rows differ from {EXTENDS}")
    ident = {"v3_0_9_lines": len(l309), "v3_0_10_lines": len(out), "v3_0_10_rows": len(v3010_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_9": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b309 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_9")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_9": b309, "after_v3_0_10": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_9", "v3_0_10", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_9": A302._q(r["before_v3_0_9"]), "v3_0_10": A302._q(r["after_v3_0_10"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_9", "vs_released_v2_9", "v2_9", "v3_0_9",
            "v3_0_10")


def diff_rows(l309, l3010, released_lines=None):
    b309 = {ln["line_id"]: ln for ln in l309}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3010:
        o = b309.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_9": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_9": A302._q(A30._qty(o)) if o else "", "v3_0_10": A302._q(A30._qty(ln))})
    return out


def write(out, l309, v3010_changes, logs, inputs, released_lines=None):
    """the V3_0_10_* files beside the V3_0_9_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3010, ident = integrate(l309, v3010_changes)
    rows = ledger_rows(v3010_changes, released_lines)
    diff = diff_rows(l309, l3010, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_9", {}).setdefault(d["vs_v3_0_9"], 0)
        dsum["vs_v3_0_9"][d["vs_v3_0_9"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t309, t3010 = A304.code_totals(l309), A304.code_totals(l3010)
    moved = {k: {"v3_0_9": t309.get(k), "v3_0_10": t3010.get(k)} for k in sorted(set(t309) | set(t3010))
             if t309.get(k) != t3010.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "item_codes", "source", "sources", "scope",
                                                          "excluded", "declared_totals")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_10_BOQ_LINES.json": BL.dumps(l3010),
             "V3_0_10_BOQ_LINES.csv": A30._lines_csv(l3010),
             "V3_0_10_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_10_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_10_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_10_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "NO_FIGURE", "load_inputs", "area_of",
           "group_openings", "check_same_openings", "record_changes", "changes_for", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError"]
