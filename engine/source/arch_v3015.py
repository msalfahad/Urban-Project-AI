"""ARCH_TAKEOFF_V3.0.15 (T-270): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.14 (engine.source.arch_v30,
arch_v301 .. arch_v3014), extended with ONE new line family: the waterproofing of the foundations (the underlay between
the blinding and each footing, its protection screed, the lift-pit membrane / protection board / screed, and the liquid
coating of the buried concrete faces), carried exactly as the Checker merged it. Not a new method family and not the
released default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the released
ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): the layers printed between two structural elements (blinding below,
footing above) belong to no structural trade: they are elements of their own trade with their own lines. The membrane
and its screed lie on the FOOTING outline (the typical footing details end both at the footing faces; only the plain
concrete projects), never on the blinding's grown outline; the blinding stays a CONCRETE line, byte-identical. A
liquid coating 'on all surfaces in contact with earth' is a per-face condition (a face with earth against it in the
finished work), never 'every buried member'. Installed area and procurement are kept apart: procurement (rolls, laps,
coats) is HELD until a product is printed.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.15`):
  1. the run is the V3.0.14 candidate exactly: its V3_0_* .. V3_0_14_* files are written unchanged (arch_v30 ..
     arch_v3014 are not edited);
  2. FOUNDATION_WP (project inputs URBAN_V3015_INPUTS_V1): one record per BOQ line, each from a checker-merged ledger
     (source file sha256, task, merge commit, checker run):
       RELEASED  -> SOURCE_DERIVED; its value is the sum of its components (each component one drawn element, measured
                    once); evidence VERIFIED where the record names the checker run that re-measured EVERY component,
                    else DRAWING-CONFIRMED (a partial own check is named, never promoted); NOT RELEASED (owner only);
       HELD      -> BLOCKED_RFI, BLANK: no figure, no range in the BOQ (owner 2026-10-24 10:56: a held quantity is
                    blank in the BOQ; readings and ranges go to the scenario file V3_0_15_SCENARIOS.json only), with
                    the named item and why it is held; never 0;
     extent rules (refused otherwise): an underlay component (membrane / protection screed under a footing) lies on
     the footing outline: its m2 equals the outline area and differs from the blinding outline area; a screed m3 is the
     outline area x the printed screed thickness; a component appears once per item code and unit; a released record
     with no component, a held record with a figure (0 included), or a record of an item code the candidate already
     carries is refused;
  3. no candidate line is replaced: the family is ADDED; every blinding / concrete line stays byte-identical (asserted);
  4. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.15 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  5. the V3_0_15_* files are written beside them: every line outside the V3.0.15 rows is byte-identical to the V3.0.14
     line (asserted on every run), V3_0_15_DIFF.csv lists every line against V3.0.14 and the released V2.9, and
     V3_0_15_SCENARIOS.json carries the held readings (never summed, never in the BOQ).

Rules: ERS 2026-10-22 s.2.1 / s.3 (element first; installed vs procurement); UP-WP-001 .. UP-WP-005 and UP-WP-LAY-001
(roll procurement only for a printed sheet product: HELD here), UP-WP-MAT-001 (product not printed: HELD), UP-WP-003
(the 0.20 upturn is scoped to wet areas / balconies / terraces / roofs: none on a footing), Q-21 C (the founding level
decides the footing detail: side faces HELD with both readings), Q-31 C (an outline with two footing tags: HELD), owner
2026-10-24 10:56 (held is blank in the BOQ, ranges only in the scenario report), UP-QTY-STATUS-001 (held never 0),
WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5. Nothing here names a project, a sheet, a layer, a room or a coordinate; every
number comes from the inputs.
"""

from __future__ import annotations

import hashlib
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.15"
EXTENDS = A3014.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T270_ARCH_V3_0_15"
LEDGER_SCHEMA = "URBAN_V3015_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V3015_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
STATES = ("RELEASED", "HELD")
DC, VER = "DRAWING-CONFIRMED", "VERIFIED"
TOL = 1e-6                               # a component sum vs the record value (6-decimal ledgers)
TOL_AREA = 5e-4                          # a component m2 vs its outline area (3-decimal outlines)
InputsError = A307.InputsError
_num = A307._num

# the line family: item code -> (en, ar, unit(s), kind). kind UNDERLAY = a layer on a footing outline (extent checked),
# FACE = a surface of a drawn member, PIT = a lift-pit component, PROCUREMENT = a supply quantity (HELD unless a product
# is printed). Item codes live here (the item master in boq_line is shared and not edited).
FAMILY = "WATERPROOFING.FOUNDATION"
ITEMS = {
    "WP.FOUNDATION.FOOTING_MEMBRANE": ("Waterproofing membrane under footings (on the footing outline)",
                                       "عازل مائي تحت القواعد", ("m2",), "UNDERLAY"),
    "WP.FOUNDATION.FOOTING_SCREED": ("Protection screed 5 cm over the footing membrane", "طبقة حماية (سكريد) فوق عازل القواعد",
                                     ("m2", "m3"), "UNDERLAY"),
    "WP.FOUNDATION.FOOTING_SIDES": ("Waterproofing of footing side faces (by the governing detail)",
                                    "عزل جوانب القواعد", ("m2",), "FACE"),
    "WP.FOUNDATION.LIFT_PIT_MEMBRANE": ("Lift pit waterproofing membrane", "عازل مائي لحفرة المصعد", ("m2",), "PIT"),
    "WP.FOUNDATION.LIFT_PIT_BOARD": ("Lift pit membrane protection board", "لوح حماية العازل لحفرة المصعد", ("m2",),
                                     "PIT"),
    "WP.FOUNDATION.LIFT_PIT_SCREED": ("Screed under the lift pit base", "سكريد تحت قاعدة المصعد", ("m2", "m3"), "PIT"),
    "WP.FOUNDATION.BURIED_LIQUID": ("Liquid waterproofing, two layers, on buried concrete faces in contact with earth",
                                    "عزل سائل طبقتين للخرسانة الملامسة للتربة", ("m2",), "FACE"),
    "WP.FOUNDATION.PROCUREMENT": ("Foundation waterproofing procurement (rolls, laps, coats): product not printed",
                                  "توريد مواد عزل الأساسات (لفات / طبقات)", ("item",), "PROCUREMENT"),
}
EXTENTS = ("FOOTING_OUTLINE",)          # the only extent an underlay component may carry

PIECES = {
    "FOUNDATION_WP": {
        "module": "engine/source/arch_v3015.py (checker-merged foundation waterproofing ledgers as their own lines)",
        "policy": "FOUNDATION_WP_LINES_V1", "rule_id": "R-WP-FOUND-1", "rule_version": "T-219-proposed",
        "owner_rules": ["UP-WP-001 .. UP-WP-005 (membrane: rolls 1 x 10 m, 0.10 lap, per area: wet areas and roofs; "
                        "not extended to foundations by assumption)",
                        "UP-WP-LAY-001 / UP-WP-MAT-001 (procurement only for a printed product: HELD)",
                        "UP-WP-003 (0.20 upturn: wet areas, balconies, terraces, roofs; none on footings)",
                        "Q-21 C (the founding level selects the footing detail: side faces HELD, both readings)",
                        "Q-31 C (an outline with two footing tags: HELD)",
                        "owner 2026-10-24 10:56 (held quantities BLANK in the BOQ; ranges only in the scenario "
                        "report)", "UP-QTY-STATUS-001 (held never 0)"],
        "owner_manual_method": "no owner manual method covers foundations (BOQ family B8-08): the owner's membrane "
                               "method (rolls per area, 0.10 lap, 0.20 upturn) is written for wet areas and roofs and "
                               "is NOT extended here; installed m2 / m3 only, procurement HELD",
        "drawing_method": "installed area from the drawings: the membrane and its 5 cm protection screed on each drawn "
                          "footing outline (L x W, a notch deducted once), the screed m3 = outline x the printed "
                          "0.05; the lift pit by component from its detail (base soffit, base + screed sides, base top "
                          "outside the pit envelope; board on sides and top; screed under the base), pit walls HELD "
                          "without the pit depth; the liquid coating per buried face with earth against it (depth "
                          "less the slab where a slab on fill bears on it; plinth faces above natural ground and "
                          "soffits cast on blinding excluded)"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3014.WAITING)
WAITING.update({
    "BURIED_FACES_TRACED": "T-276 (REJECTED narrow r2 at 2026-10-24 20:59): traced buried ground-beam faces (a delta "
                           "against the T-263 run faces carried here); joins the WP.FOUNDATION.BURIED_LIQUID line as a "
                           "delta after its Gate A, never estimated now",
    "FOOTING_DETAIL_SELECTION": "footing side faces, footing tops and necks: HELD until the founding level selects the "
                                "footing detail (Q-21 C; designer); readings in V3_0_15_SCENARIOS.json only",
    "LIFT_PIT_DEPTH": "lift pit wall membrane / board: HELD on the pit depth (lift maker, designer D-43)",
    "WP_PRODUCT": "membrane / liquid product, thickness-to-product, laps and coats not printed: procurement HELD "
                  "(UP-WP-MAT-001; designer item)",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_").upper()[:48] or "X"


# ================================================================================================ project inputs
def _check_component(rid, code, unit, c, kind, chain, seen):
    cid = c.get("id")
    if not cid:
        raise InputsError(f"record {rid}: every component names its drawn element (id)")
    if (code, unit, cid) in seen:
        raise InputsError(f"record {rid}: component {cid} counted twice in {code} {unit} (each element once)")
    seen.add((code, unit, cid))
    v = c.get("value")
    if not (_num(v) and v > 0):
        raise InputsError(f"record {rid}: component {cid} carries a value > 0 (a missing value is HELD, never 0)")
    if kind != "UNDERLAY":
        return
    if c.get("extent") not in EXTENTS:
        raise InputsError(f"record {rid}: component {cid} extent {c.get('extent')!r}: an underlay lies on the footing "
                          f"outline {EXTENTS} (the blinding alone projects)")
    oa, ba = c.get("outline_m2"), c.get("blinding_m2")
    if not (_num(oa) and oa > 0 and _num(ba) and ba > oa):
        raise InputsError(f"record {rid}: component {cid} needs outline_m2 > 0 and the blinding outline blinding_m2 > "
                          "outline_m2 (the extent is checked against both)")
    area = v if unit == "m2" else None
    if unit == "m3":
        t = chain.get("screed_t")
        if not (_num(t) and t > 0):
            raise InputsError(f"record {rid}: a screed m3 needs the printed screed thickness (chain.screed_t)")
        if abs(v - oa * t) > TOL_AREA * t + TOL:
            raise InputsError(f"record {rid}: component {cid} screed {v} m3 != outline {oa} x printed {t}")
        return
    if abs(area - ba) <= TOL_AREA:
        raise InputsError(f"record {rid}: component {cid} {area} m2 is the BLINDING outline area: the membrane / screed "
                          "lies on the footing outline, never on the blinding")
    if abs(area - oa) > TOL_AREA:
        raise InputsError(f"record {rid}: component {cid} {area} m2 != its footing outline {oa} m2")


def _check_record(r, chain, seen_comp, seen_rec):
    rid = r.get("id")
    if not rid:
        raise InputsError("every record has an id")
    if rid in seen_rec:
        raise InputsError(f"record {rid} twice")
    seen_rec.add(rid)
    code, unit, st = r.get("item_code"), r.get("unit"), r.get("state")
    if code not in ITEMS:
        raise InputsError(f"record {rid}: item code {code!r} is not one of the {FAMILY} codes {sorted(ITEMS)}")
    if unit not in ITEMS[code][2]:
        raise InputsError(f"record {rid}: unit {unit!r} not one of {ITEMS[code][2]} for {code}")
    if st not in STATES:
        raise InputsError(f"record {rid}: state {st!r} not one of {STATES}")
    if not r.get("floor") or not r.get("element"):
        raise InputsError(f"record {rid}: floor and element (the named BOQ item) are required")
    kind = ITEMS[code][3]
    if st == "RELEASED":
        if kind == "PROCUREMENT":
            raise InputsError(f"record {rid}: procurement is released only on a printed product (UP-WP-MAT-001)")
        comps = r.get("components") or []
        if not comps:
            raise InputsError(f"record {rid}: a released record lists its components (each drawn element once)")
        for c in comps:
            _check_component(rid, code, unit, c, kind, chain, seen_comp)
        v = r.get("value")
        if not (_num(v) and v > 0):
            raise InputsError(f"record {rid}: a released record carries value > 0")
        s = sum(c["value"] for c in comps)
        if abs(s - v) > TOL * max(1, len(comps)):
            raise InputsError(f"record {rid}: value {v} != the sum of its components {_r(s)}")
        vb = r.get("verified_by")
        if vb and not r.get("verified_components") == "ALL":
            raise InputsError(f"record {rid}: VERIFIED only when the checker re-measured every component "
                              "(verified_components: ALL); a partial own check goes to partial_check")
        pc = r.get("partial_check")
        if pc is not None and not (_num(pc.get("m2_or_unit")) and 0 < pc["m2_or_unit"] <= v + TOL and pc.get("run")):
            raise InputsError(f"record {rid}: partial_check names the checker run and the part (> 0, <= value) it "
                              "re-measured")
    else:
        for k in ("value", "low", "high", "components"):
            if r.get(k) is not None:
                raise InputsError(f"record {rid}: a HELD record carries no figure ({k}): it is BLANK in the BOQ (owner "
                                  "2026-10-24 10:56), readings only in scenario")
        if not r.get("reasons"):
            raise InputsError(f"record {rid}: a held record names why it is held")
        sc = r.get("scenario")
        if sc is not None:
            if not isinstance(sc, dict) or not sc.get("readings"):
                raise InputsError(f"record {rid}: scenario carries its readings (and basis)")
            for k, x in sc["readings"].items():
                if not (_num(x) and x > 0):
                    raise InputsError(f"record {rid}: scenario reading {k} must be > 0 (a reading of 0 is no reading)")


def load_inputs(doc, project_id=None):
    """URBAN_V3015_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "FOUNDATION_WP", "source": {file, sha256, task, merge_commit, checker_run},
                     "sources": [... the further merged ledgers each record cites by task],
                     "chain": {"screed_t", "membrane_extent"},
                     "blinding": {"item_codes": [...], "trade": "CONCRETE"} (asserted byte-identical),
                     "records": [{id, item_code, unit, state, floor, element, physical_element, task, value,
                                  components: [{id, value, extent, outline_m2, blinding_m2, ...}], verified_by,
                                  verified_components, partial_check, reasons, scenario, excluded, owner_trade_note,
                                  printed}],
                     "declared_totals": {"<item code> <unit>": {"released": x, "held_lines": n}}}],
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
        if p != "FOUNDATION_WP" or p in seen:
            raise InputsError(f"piece {p!r}: FOUNDATION_WP, once")
        seen.add(p)
        A307._source(pc.get("source"), f"piece {p}")
        tasks = {pc["source"]["task"]}
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
            tasks.add(s["task"])
        chain = pc.get("chain") or {}
        if chain.get("membrane_extent") not in EXTENTS:
            raise InputsError(f"piece {p}: chain.membrane_extent must be one of {EXTENTS} (as the detail prints it)")
        b = pc.get("blinding") or {}
        if not b.get("item_codes"):
            raise InputsError(f"piece {p}: blinding.item_codes (the concrete lines asserted unchanged) are required")
        recs = pc.get("records") or []
        if not recs:
            raise InputsError(f"piece {p}: no records")
        sc, sr = set(), set()
        for r in recs:
            _check_record(r, chain, sc, sr)
            if r.get("task") not in tasks:
                raise InputsError(f"record {r['id']}: task {r.get('task')!r} is not one of the merged sources "
                                  f"{sorted(tasks)}")
        if not pc.get("declared_totals"):
            raise InputsError(f"piece {p}: declared_totals per item code and unit are required")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ lines
def _src_of(pc, task):
    for s in [pc["source"]] + list(pc.get("sources") or ()):
        if s["task"] == task:
            return s
    raise InputsError(f"no merged source for task {task}")


def record_line(pid, rev, docs, pc, r):
    """one BOQ line for one record. -> (line, evidence status)"""
    from engine.source import boq_line as BL
    p = PIECES["FOUNDATION_WP"]
    en, ar, _units, kind = ITEMS[r["item_code"]]
    src = _src_of(pc, r["task"])
    held = r["state"] == "HELD"
    eid = f"WPF:{_slug(r['element'])}"
    inputs = {"policy": p["policy"], "family": FAMILY, "kind": kind, "ledger": src["file"],
              "ledger_sha256": src["sha256"], "task": src["task"], "merge_commit": src["merge_commit"],
              "checker_run": src["checker_run"], "element": r["element"], "printed": r.get("printed"),
              "record_state": r["state"]}
    if held:
        inputs.update(reasons=list(r["reasons"]), scenario_ref=("V3_0_15_SCENARIOS.json#" + r["id"])
                      if r.get("scenario") else None)
        formula = ("HELD (blank in the BOQ): " + "; ".join(r["reasons"]))[:400]
        rfi = {"question": "; ".join(r["reasons"])[:900], "unlocks": eid}
        ev, net = "BLOCKED_RFI", None
        evs = "UNKNOWN" if r.get("unknown") else "HELD"
    else:
        inputs.update(components=[dict(c) for c in r["components"]], verified_by=r.get("verified_by"),
                      verified_components=r.get("verified_components"), partial_check=r.get("partial_check"),
                      excluded=r.get("excluded"), line_status=r.get("line_status"))
        formula = (r.get("formula") or f"sum of {len(r['components'])} drawn components")[:400]
        rfi, ev, net = None, "SOURCE_DERIVED", _r(r["value"])
        evs = VER if r.get("verified_by") else DC
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=r["item_code"], unit=r["unit"],
                      evidence_state=ev, measured_net=net, bounded_range=None, element_id=eid, floor=r["floor"],
                      physical_element=r.get("physical_element") or "FOUNDATION", subtrade=FAMILY, formula=formula,
                      inputs={"foundation_wp_v3015": inputs}, documents=docs,
                      geometry_source=r.get("geometry_source") or "CAD_VECTOR",
                      geometry_confidence="INFERRED_CANDIDATE" if held else "TOLERANCE_CERTIFIED",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="BY_SPEC", rfi=rfi,
                      notes=(f"{METHOD}: {FAMILY} ({src['task']}, MERGED {src['merge_commit']}, {src['checker_run']})"
                             + ("; HELD: blank in the BOQ, never 0" if held else "")),
                      item_en=en, item_ar=ar, trade="WATERPROOFING")
    return ln, evs


def _blinding_lines(pc, lines):
    codes = set(pc["blinding"]["item_codes"])
    return [ln for ln in lines if ln["item_code"] in codes]


def wp_changes(pc, lines):
    """the FOUNDATION_WP piece on the V3.0.14 lines. -> (changes, log)"""
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    clash = sorted({ln["item_code"] for ln in lines if ln["item_code"] in ITEMS})
    if clash:
        raise InputsError(f"the candidate already carries {clash}: a family is added once (no double count)")
    if not _blinding_lines(pc, lines):
        raise InputsError(f"no blinding line {pc['blinding']['item_codes']} in the candidate: the underlay is placed "
                          "against a candidate that carries its blinding")
    changes = []
    log = {"piece": "FOUNDATION_WP", "state": "RUN", "family": FAMILY, "source": pc["source"],
           "sources": pc.get("sources") or [], "records": [], "totals": {}, "evidence_status": {},
           "blinding_lines": sorted(ln["line_id"] for ln in _blinding_lines(pc, lines))}
    for r in pc["records"]:
        ln, evs = record_line(pid, rev, docs, pc, r)
        if ln["line_id"] in have:
            raise ValueError(f"{METHOD}: record {r['id']} repeats a candidate line id")
        have.add(ln["line_id"])
        src = _src_of(pc, r["task"])
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "ledger": src["file"], "ledger_sha256": src["sha256"], "record_verified_by": r.get("verified_by"),
                 "partial_check": r.get("partial_check")}
        held = []
        if r["state"] == "HELD":
            held = [{"what": f"{r['item_code']} {r['unit']} {r['element']}", "why": "; ".join(r["reasons"])[:900],
                     "range": None, "scenario": ("V3_0_15_SCENARIOS.json#" + r["id"]) if r.get("scenario") else None}]
        changes.append(A305._change("FOUNDATION_WP", "ADD", None, ln, drawing_reference=r.get("printed") or src["file"],
                                    held=held, downstream=list(r.get("downstream") or ()), verification=verif,
                                    evidence_status=evs, codes=["NEW_FAMILY", r["state"]],
                                    guard_element={"element_id": ln["location"]["element_id"], "part": "WHOLE"}))
        key = f"{r['item_code']} {r['unit']}"
        t = log["totals"].setdefault(key, {"released": 0.0, "held_lines": 0})
        if r["state"] == "RELEASED":
            t["released"] += r["value"]
        else:
            t["held_lines"] += 1
        log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        log["records"].append({"id": r["id"], "line_id": ln["line_id"], "item_code": r["item_code"],
                               "unit": r["unit"], "state": r["state"], "value": r.get("value"),
                               "components": len(r.get("components") or ()), "evidence_status": evs,
                               "line_status": r.get("line_status"), "task": r["task"]})
    log["totals"] = {k: {"released": _r(v["released"]), "held_lines": v["held_lines"]}
                     for k, v in sorted(log["totals"].items())}
    for k, v in pc["declared_totals"].items():
        got = log["totals"].get(k)
        if got is None or abs(got["released"] - v["released"]) > 1e-6 or got["held_lines"] != v["held_lines"]:
            raise ValueError(f"{METHOD}: {k} totals {got} != the declared {v}")
    if set(log["totals"]) != set(pc["declared_totals"]):
        raise ValueError(f"{METHOD}: declared totals {sorted(pc['declared_totals'])} != the records' "
                         f"{sorted(log['totals'])}")
    log["declared_totals"] = pc["declared_totals"]
    return changes, log


def scenarios(inputs):
    """the held readings: never in the BOQ, never summed (owner 2026-10-24 10:56)."""
    out = []
    for pc in (inputs or {}).get("pieces") or ():
        for r in pc["records"]:
            if r["state"] == "HELD" and r.get("scenario"):
                out.append({"id": r["id"], "item_code": r["item_code"], "unit": r["unit"], "element": r["element"],
                            "task": r["task"], "reasons": r["reasons"], "readings": r["scenario"]["readings"],
                            "basis": r["scenario"].get("basis"), "status": "HELD - SCENARIO ONLY, NOT A BOQ QUANTITY"})
    return out


# ================================================================================================ integrate / write
def changes_for(inputs, l3014, earlier_changed=()):
    """the foundation waterproofing lines, then the guard re-check over the result. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        ch_g, log_g = A307.guard_changes(inputs, l3014, [], set())
        return ch_g, [{"piece": "FOUNDATION_WP", "state": "NO_PROJECT_INPUT"}, log_g]
    ch, log = wp_changes(inputs["pieces"][0], l3014)
    ch_g, log_g = A307.guard_changes(inputs, l3014, [c for c in ch if c["action"] == "ADD"], set())
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g]


def check_family(lines):
    """every line of the family: a held line is blank (no figure, no range), a released line > 0; -> summary."""
    out = {}
    for ln in lines:
        if ln["item_code"] not in ITEMS:
            continue
        k = f"{ln['item_code']} {ln['unit']}"
        d = out.setdefault(k, {"released": 0.0, "lines": 0, "held_lines": 0})
        d["lines"] += 1
        if ln["evidence_state"] == "SOURCE_DERIVED":
            if not (ln.get("measured_net") or 0) > 0:
                raise ValueError(f"{METHOD}: {ln['line_id']} released at 0")
            d["released"] += ln["measured_net"]
        elif ln["evidence_state"] == "BLOCKED_RFI":
            if ln.get("measured_net") is not None or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: held line {ln['line_id']} carries a figure in the BOQ")
            d["held_lines"] += 1
        else:
            raise ValueError(f"{METHOD}: {ln['line_id']} state {ln['evidence_state']} not in the family's states")
    return {k: {"released": _r(v["released"]), "lines": v["lines"], "held_lines": v["held_lines"]}
            for k, v in sorted(out.items())}


def integrate(l3014, v3015_changes, blinding_codes=("STR.CONC.BLINDING",)):
    """-> (V3.0.15 lines, identity). Every line outside the V3.0.15 rows is byte-identical to the V3.0.14 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3014}
    rep, adds = {}, []
    for c in v3015_changes:
        if c["action"] == "REPLACE":
            if c["piece"] != "DEFAULT_GUARD":
                raise ValueError(f"{METHOD}: the family is ADDED; only the guard re-check replaces a line")
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.14 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.14 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3014] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    fam = check_family(out)
    by14 = {ln["line_id"]: ln for ln in l3014}
    blind = [ln for ln in l3014 if ln["item_code"] in blinding_codes]
    if any(ln["line_id"] in rep for ln in blind):
        raise ValueError(f"{METHOD}: a blinding line is changed (the underlay never takes the blinding's place)")
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by14[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3014):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.15 rows differ from {EXTENDS}")
    ident = {"v3_0_14_lines": len(l3014), "v3_0_15_lines": len(out), "v3_0_15_rows": len(v3015_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_14": len(outside), "blinding_lines_identical": len(blind),
             "family": fam,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b14 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_14")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_14": b14, "after_v3_0_15": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_14", "v3_0_15", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_14": A302._q(r["before_v3_0_14"]), "v3_0_15": A302._q(r["after_v3_0_15"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_14", "vs_released_v2_9", "v2_9",
            "v3_0_14", "v3_0_15")


def diff_rows(l3014, l3015, released_lines=None):
    b14 = {ln["line_id"]: ln for ln in l3014}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3015:
        o = b14.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_14": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_14": A302._q(A30._qty(o)) if o else "", "v3_0_15": A302._q(A30._qty(ln))})
    return out


def write(out, l3014, v3015_changes, logs, inputs, released_lines=None):
    """the V3_0_15_* files beside the V3_0_14_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    bc = tuple(((inputs or {}).get("pieces") or [{}])[0].get("blinding", {}).get("item_codes") or ("STR.CONC.BLINDING",))
    l3015, ident = integrate(l3014, v3015_changes, bc)
    rows = ledger_rows(v3015_changes, released_lines)
    diff = diff_rows(l3014, l3015, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_14", {}).setdefault(d["vs_v3_0_14"], 0)
        dsum["vs_v3_0_14"][d["vs_v3_0_14"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t14, t15 = A304.code_totals(l3014), A304.code_totals(l3015)
    moved = {k: {"v3_0_14": t14.get(k), "v3_0_15": t15.get(k)} for k in sorted(set(t14) | set(t15))
             if t14.get(k) != t15.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "items": {k: list(v) for k, v in ITEMS.items()},
           "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "source", "sources", "chain", "blinding",
                                                         "declared_totals")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "family_v3_0_15": ident["family"], "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_15_BOQ_LINES.json": BL.dumps(l3015),
             "V3_0_15_BOQ_LINES.csv": A30._lines_csv(l3015),
             "V3_0_15_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_15_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_15_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_15_SCENARIOS.json": A30._j({"method": METHOD, "note": "HELD readings only: never a BOQ quantity, "
                                                                          "never summed (owner 2026-10-24 10:56)",
                                               "scenarios": scenarios(inputs)}),
             "V3_0_15_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "ITEMS", "FAMILY", "DEFAULT_GUARD_CLASS", "load_inputs", "record_line",
           "wp_changes", "changes_for", "check_family", "integrate", "scenarios", "ledger_rows", "diff_rows", "write",
           "InputsError"]
