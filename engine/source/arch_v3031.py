"""ARCH_TAKEOFF_V3.0.31 (T-328): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.30 (engine.source.arch_v30,
arch_v301 .. arch_v3030), extended with the BOQ category the candidate lacked (registry family B13-01):

  ROOF_BUILDUP_FILL  the roof / terrace build-up as one line per (roof, layer) from the Checker-merged layer ledger
                     (T-321) and its Checker-merged line binding (T-339 FILL table): SCREED TO FALLS (one m3 volume per
                     roof), INSULATION (m2), PROTECTION (m2) and the walking FINISH (m2); the membrane and its upturn
                     stay the existing waterproofing lines (FIN.WP.ROOF / FIN.WP.ROOF_UPTURN), bound and untouched.

The physical element (ERS 2026-10-22 s.2.1): a roof build-up is a stack of layers over the roof slab, each layer one
item with ONE owner trade, each measured to its OWN drawn edge (face layers to the wall / parapet INNER faces; the finish
to the designer's finish hatch); a layer exists only by a print or an owner rule (else UNKNOWN: a row, blank, never 0);
a thickness only from a print (else HELD). The falls layer is ONE physical volume: owner Q-41 ('if it is roof or
balconies it is screed', its own line) books it as SCREED; Q-45 ('roofs: thickness from the falls') sets that layer's
mix only and never opens a second falls volume (Lead ruling, ELEMENT_REGISTER 2026-10-29). A screed to falls is a
WEDGE (t0 at the outlet + the rise to the far point), never a constant layer on a sloped roof. A layer stops at the
parapet inner face; it runs up a parapet only where an upturn is printed (the membrane's 0.20 m upturn is its own lm
line); the parapet's RC / block body (STR.CONC.PARAPET, T-319) and its faces are other lines, never inside a roof layer.

Line states (never a value of this module's own):
  FINISH area DRAWING-CONFIRMED -> MEASURED (m2), material BY_SPEC (no tile / paving type printed: HELD by name);
  SCREED (m3)                  -> BLOCKED_RFI, BLANK: t0 unprinted (designer D-39); the basis plan area beside;
  INSULATION / PROTECTION      -> BLOCKED_RFI, BLANK: scope UNKNOWN (printed nowhere, no owner rule);
  a HELD roof (owner Q-34)     -> every layer BLOCKED_RFI, BLANK; the drawing-derived area beside, never released.
A range (lo .. hi) is carried beside a line only with its named cause (layer edge reading, D band); it is never a line
figure and never chosen.

R-T328-1 (every villa): one line per (roof, layer), one owner trade per layer; ONE screed volume per roof (a second
falls / bed volume refused; Q-45 is the mix of that line); a constant-thickness volume on a sloped roof refused; no
layer area above its roof outline (the face plan inside the parapet inner faces); a layer up a parapet only with a
printed upturn; the bound membrane / upturn / parapet lines must stand in the candidate as bound (stale binding stops);
HELD and UNKNOWN are BLANK, never 0.

Every V3.0.30 line is byte-identical in V3.0.31 (this package only ADDS lines; asserted). Files: V3_0_31_BOQ_LINES.json /
.csv, V3_0_31_INTEGRATION_LEDGER.json / .csv, V3_0_31_DIFF.csv, V3_0_31_RUN.json. Nothing here names a project, a sheet,
a layer or a coordinate: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3029 as A3029
from engine.source import arch_v3030 as A3030

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.31"
EXTENDS = A3030.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T328_ARCH_V3_0_31"
INPUTS_SCHEMA = "URBAN_V3031_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3031_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3030.InputsError
_r = A3018._r
RULE_ID, RULE_VERSION = "R-T328-1", "T-328"
PIECE = "ROOF_BUILDUP_FILL"
REC_KEY = "roof_buildup_v3031"
SCREED, INSUL, PROT, FINISH = "FIN.ROOF.SCREED", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION", "FIN.ROOF.FINISH"
WP_ROOF, WP_UPTURN, PARAPET = "FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN", "STR.CONC.PARAPET"
NEW_ITEMS = {   # item master entries for the codes boq_line.ITEMS does not carry (en, ar, trade, subtrade)
    SCREED: ("Roof screed to falls (one volume per roof)", "ميول السطح (لياسة / سكريد)", "ROOFING", "SCREED"),
    INSUL: ("Roof thermal insulation layer", "عزل حراري للسطح", "ROOFING", None),
    PROT: ("Roof protection layer", "طبقة حماية العزل", "ROOFING", None),
    FINISH: ("Roof / terrace walking finish (area; material by specification)", "تشطيب أرضيات السطح", "ROOFING", None),
}
LAYERS = {"FALLS_SCREED": (SCREED, "m3"), "INSULATION": (INSUL, "m2"), "PROTECTION": (PROT, "m2"),
          "FINISH": (FINISH, "m2")}
ITEMS = {c: u for c, u in LAYERS.values()}
OWNER_TRADE = {"FALLS_SCREED": "SCREED", "INSULATION": "ROOFING B13-01", "PROTECTION": "ROOFING B13-01",
               "FINISH": "ROOFING B13-01"}
LAYER_STATUSES = ("DRAWING-CONFIRMED", "HELD", "UNKNOWN")
EDGES = ("FACE", "FINISH")              # face layers to the wall / parapet INNER faces; finish to its hatch
REFUSED_EDGES = ("PARAPET_OUTER_FACE", "PARAPET_OUTER", "OUTER_FACE")
TOL = 1e-6

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3031.py (roof build-up as its own line family: one line per (roof, layer) of "
                  "the Checker-merged T-321 layer ledger bound by the Checker-merged T-339 FILL table; held / unknown "
                  "layers BLANK; the membrane / upturn lines bound, untouched)",
        "policy": "ROOF_BUILDUP_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["Q-41 (owner 2026-10-19 20:45: 'if it is roof or balconies it is screed', its own line)",
                        "Q-45 (the mix of that screed layer only; never a second falls volume: Lead ruling "
                        "ELEMENT_REGISTER 2026-10-29)", "Q-34 (the top roof stays HELD: no number, never 0)",
                        "UP-WP-ROOF-001 / Q-24 (membrane inside the parapet with its 0.20 m upturn: existing lines)",
                        "D-39 (designer: roof build-up detail, t0 and layer thicknesses)", "UP-QTY-STATUS-001",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner rule Q-41: a roof screed is its own line, measured as its volume (area x "
                               "thickness, the falls included); the thickness is not given by the owner (D-39), so "
                               "the volume is HELD; the area basis is the plan inside the parapet / wall faces; no "
                               "owner rule measures roof insulation or protection (scope UNKNOWN) and none sets a "
                               "roof finish material (finish area only)",
        "drawing_method": "per roof, each layer to its own drawn edge by entity handle (T-321, re-bound by T-339): "
                          "face layers inside the wall / parapet inner faces (the D band a named range), the finish "
                          "to the designer's finish hatch (annotation islands, symbol frames and door swings are not "
                          "edges); the falls model (t0 + the 1 % rise) beside, t0 unprinted"},
}
WAITING = dict(A3030.WAITING)
WAITING.update({
    "ROOF_SCREED_T0": "the screed-to-falls volume of every roof: t0 (the screed thickness at the outlet) is unprinted "
                      "(designer D-39); one m3 line per roof BLANK with its basis area and the falls model beside",
    "ROOF_INSULATION_PROTECTION": "roof insulation and protection layers: printed nowhere and no owner rule (scope "
                                  "UNKNOWN, designer D-39): one BLANK line per roof, never 0",
    "ROOF_FINISH_MATERIAL": "roof / terrace finish material (no tile / paving type printed; no owner rule for roofs): "
                            "the area lines are MEASURED, the material BY_SPEC",
    "ROOF_TOP_Q34": "the top roof (owner Q-34): every layer BLANK; drawing-derived area beside, never released",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, zero_ok=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x < 0 or (x == 0 and not zero_ok):
        raise InputsError(f"{where}: {x!r} is not a positive figure")
    return float(x)


def _range(r, where):
    """a (lo, hi) basis: both or neither; lo <= hi; lo < hi only with a named cause (never chosen)."""
    lo, hi = r.get("basis_lo"), r.get("basis_hi")
    if (lo is None) != (hi is None):
        raise InputsError(f"{where}: a basis range needs both ends")
    if lo is None:
        return None, None
    lo, hi = _num(lo, where), _num(hi, where)
    if lo > hi + TOL:
        raise InputsError(f"{where}: basis low {lo} above high {hi}")
    if hi - lo > TOL and not r.get("range_cause"):
        raise InputsError(f"{where}: a range {lo} .. {hi} needs its named cause (layer edge reading), never chosen")
    return lo, hi


def load_inputs(doc, project_id=None):
    """URBAN_V3031_INPUTS_V1 -> the validated doc (one line per roof x layer; one screed volume per roof; held blank)."""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    roofs, bound = {}, {}
    for rf in doc.get("roofs") or ():
        rid = rf.get("roof")
        where = f"roof {rid}"
        _need(rf, ("roof", "element_id", "floor"), where)
        if rid in roofs:
            raise InputsError(f"{where}: one roof, one entry")
        held = rf.get("held_roof")
        if held is not None and not held.get("reason"):
            raise InputsError(f"{where}: a held roof names its owner decision")
        outline = None
        if held is None:
            outline = _num(rf.get("outline_m2"), f"{where} outline (face plan inside the parapet inner faces)")
        slope = rf.get("fall_printed_pct")
        if slope is not None:
            _num(slope, f"{where} printed fall", zero_ok=True)
        for k in ("membrane_line", "upturn_line"):
            b = rf.get(k)
            if b is not None:
                _need(b, ("line_id", "item_code", "evidence_state"), f"{where} {k}")
                if b["item_code"] != {"membrane_line": WP_ROOF, "upturn_line": WP_UPTURN}[k]:
                    raise InputsError(f"{where} {k}: {b['item_code']} is not the roof waterproofing line")
                if b["line_id"] in bound:
                    raise InputsError(f"{where} {k}: {b['line_id']} bound twice")
                bound[b["line_id"]] = b
        seen = {}
        for ly in rf.get("layers") or ():
            name = ly.get("layer")
            lw = f"{where} layer {name}"
            if name not in LAYERS:
                raise InputsError(f"{lw}: not a build-up layer {sorted(LAYERS)} (a 'falls' or tile-bed volume beside "
                                  f"the screed is the same physical layer: refused; Q-45 is the screed's mix)")
            if name in seen:
                raise InputsError(f"{lw}: booked twice on one roof (one line per roof and layer; Q-41 and Q-45 "
                                  f"describe ONE falls layer)")
            seen[name] = ly
            if ly.get("source_task") not in srcs:
                raise InputsError(f"{lw}: no merged source for {ly.get('source_task')!r}")
            if ly.get("status") not in LAYER_STATUSES:
                raise InputsError(f"{lw}: status {ly.get('status')!r}")
            if ly.get("owner_trade") != OWNER_TRADE[name]:
                raise InputsError(f"{lw}: owner trade {ly.get('owner_trade')!r}, the register gives {OWNER_TRADE[name]}")
            if ly.get("unit") != LAYERS[name][1]:
                raise InputsError(f"{lw}: unit {ly.get('unit')!r} (the {name} line is in {LAYERS[name][1]})")
            edge = str(ly.get("edge") or "")
            if edge.upper() in REFUSED_EDGES or edge not in EDGES:
                raise InputsError(f"{lw}: edge {edge!r}: a layer stops at the wall / parapet INNER face (or its "
                                  f"finish hatch); the parapet footprint is the parapet's line")
            if ly.get("runs_up_parapet") and not ly.get("upturn_printed"):
                raise InputsError(f"{lw}: a layer up a parapet without a printed upturn")
            lo, hi = _range(ly, lw)
            if outline is not None and hi is not None and hi > outline + TOL:
                raise InputsError(f"{lw}: basis {hi} m2 above the roof outline {outline} m2")
            q, t = ly.get("quantity"), ly.get("thickness_m")
            if t is not None and not ly.get("thickness_source"):
                raise InputsError(f"{lw}: a thickness without its print (no default thickness)")
            if ly["status"] == "DRAWING-CONFIRMED":
                if held is not None:
                    raise InputsError(f"{lw}: a valued layer on a held roof ({held['reason'][:80]})")
                _num(q, lw)
                if outline is not None and ly["unit"] == "m2" and q > outline + TOL:
                    raise InputsError(f"{lw}: {q} m2 above the roof outline {outline} m2")
                if name == "FALLS_SCREED":
                    _screed_volume(ly, slope, lw)
            elif q is not None:
                raise InputsError(f"{lw}: a {ly['status']} layer given a figure (held is BLANK, never 0)")
            elif not ly.get("held_reason"):
                raise InputsError(f"{lw}: a {ly['status']} layer names why it is blank")
        if set(seen) != set(LAYERS):
            raise InputsError(f"{where}: layers {sorted(seen)}: every roof carries all {sorted(LAYERS)} (an unknown "
                              f"layer is a blank row, never a silent omission)")
        roofs[rid] = dict(rf, _layers=seen)
    if not roofs:
        raise InputsError("no roof in the inputs")
    par = {}
    for p in doc.get("parapet_lines") or ():
        _need(p, ("line_id", "item_code", "evidence_state"), "parapet line")
        if p["item_code"] != PARAPET:
            raise InputsError(f"parapet line {p['line_id']}: {p['item_code']} is not {PARAPET}")
        par[p["line_id"]] = p
    return dict(doc, _sources=srcs, _roofs=roofs, _bound=bound, _parapets=par)


def _screed_volume(ly, slope, where):
    """a valued screed volume is a wedge: area x t0 + the falls rise (both printed); a constant layer on a sloped roof
    is refused."""
    t0, rise = ly.get("thickness_m"), ly.get("above_t0_m3")
    area = ly.get("basis_lo")
    if t0 is None or not ly.get("thickness_source") or area is None or ly.get("basis_hi") != area:
        raise InputsError(f"{where}: a screed volume needs a printed t0 and one basis area")
    if slope and rise is None:
        raise InputsError(f"{where}: a constant-thickness screed on a roof with a printed fall {slope} % (the falls "
                          f"are a wedge: t0 + the rise; refused)")
    want = area * t0 + (rise or 0.0)
    if abs(want - ly["quantity"]) > 1e-4:
        raise InputsError(f"{where}: {ly['quantity']} m3 is not area x t0 + the rise = {_r(want)} m3")


# ================================================================================================ lines
def _rec(src, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(src):
    return {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
            "ledger": src["file"], "ledger_sha256": src["sha256"]}


_fmt = A3030._fmt


def _new(tmpl, *, item_code, unit, evidence_state, element_id, floor, phys, formula, rec, measured_net=None, rfi=None,
         notes=""):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    en, ar, tr, sub = NEW_ITEMS[item_code]
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"], item_code=item_code,
                      unit=unit, evidence_state=evidence_state, measured_net=measured_net, element_id=element_id,
                      floor=floor, physical_element=phys, formula=formula[:700], inputs={REC_KEY: rec},
                      documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source=tmpl["source"]["geometry_source"],
                      geometry_confidence=tmpl["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="BY_SPEC", rfi=rfi,
                      notes=notes[:600], item_en=en, item_ar=ar, trade=tr, subtrade=sub)
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def _ev_status(rf, ly):
    if rf.get("held_roof") is not None:
        return "HELD"
    return {"DRAWING-CONFIRMED": "DRAWING-CONFIRMED", "HELD": "HELD", "UNKNOWN": "UNKNOWN"}[ly["status"]] + (
        "; scope ASSUMED — OWNER-APPROVED (Q-41)" if ly["layer"] == "FALLS_SCREED" else "")


def layer_line(rf, ly, src, tmpl):
    """one (roof, layer) row -> its line."""
    name = ly["layer"]
    code, unit = LAYERS[name]
    eid = f"ROOF:{rf['roof']}:{name}"
    held = rf.get("held_roof")
    lo, hi = ly.get("basis_lo"), ly.get("basis_hi")
    basis = (None if lo is None else {"lo": lo, "hi": hi, "cause": ly.get("range_cause")})
    ev = _ev_status(rf, ly)
    rec = _rec(src, action="ADD", roof=rf["roof"], roof_element=rf["element_id"], layer=name,
               owner_trade=OWNER_TRADE[name], status=ly["status"], edge=ly.get("edge"),
               edge_handles=ly.get("edge_handles"), basis=basis, quantity=ly.get("quantity"),
               thickness_m=ly.get("thickness_m"), thickness_source=ly.get("thickness_source"),
               above_t0_m3=ly.get("above_t0_m3"), falls_beside=ly.get("falls_beside"),
               scope_source=ly.get("scope_source"), held_reason=ly.get("held_reason"),
               bounds_beside=ly.get("bounds_beside"), held_roof=held, evidence_status=ev,
               membrane_line=(rf.get("membrane_line") or {}).get("line_id"),
               upturn_line=(rf.get("upturn_line") or {}).get("line_id"))
    phys = f"roof build-up: {name.lower().replace('_', ' ')}"
    hs = " ".join(ly.get("edge_handles") or [])[:200]
    if ly["status"] == "DRAWING-CONFIRMED" and held is None:
        formula = (f"{rf['roof']} {name.lower()}: {_fmt(ly['quantity'])} {unit} to its own edge "
                   f"({ly.get('edge')}: {hs}); roof outline {_fmt(rf['outline_m2'])} m2; one line, one owner trade "
                   f"({OWNER_TRADE[name]})")
        return _new(tmpl, item_code=code, unit=unit, evidence_state="MEASURED", element_id=eid, floor=rf["floor"],
                    phys=phys, formula=formula, rec=rec, measured_net=_r(ly["quantity"]),
                    notes=f"{METHOD}: roof layer ({src['task']} MERGED {src['merge_commit'][:8]}); {ev}; "
                          f"material by specification; NOT RELEASED")
    why = (f"{'HELD' if held or ly['status'] == 'HELD' else 'UNKNOWN'} (blank in the BOQ, never 0): {rf['roof']} "
           f"{name.lower()} ({unit}): {ly.get('held_reason') or ''}"
           + (f"; held roof: {held['reason']}" if held else "")
           + (f"; basis plan {_fmt(lo)}" + (f" .. {_fmt(hi)}" if hi is not None and abs(hi - lo) > TOL else "")
              + f" m2 beside{' (' + ly['range_cause'] + ')' if ly.get('range_cause') else ''}" if lo is not None else "")
           + (f"; {ly['bounds_beside']}" if ly.get("bounds_beside") else ""))
    return _new(tmpl, item_code=code, unit=unit, evidence_state="BLOCKED_RFI", element_id=eid, floor=rf["floor"],
                phys=phys, formula=why, rec=rec, rfi={"question": why[:900], "unlocks": eid},
                notes=f"{METHOD}: roof layer {ev} by name ({src['task']} MERGED {src['merge_commit'][:8]})")


def _assert_bound(b, c):
    """a bound line must stand in the candidate exactly as bound (stale binding stops)."""
    if b is None:
        raise InputsError(f"bound line {c['line_id']}: not in the candidate (stale binding)")
    q, cq = b.get("measured_net"), c.get("measured_net")
    same = b["item_code"] == c["item_code"] and b["evidence_state"] == c["evidence_state"] and (
        (q is None and cq is None) or (q is not None and cq is not None and abs(q - cq) <= TOL))
    if c.get("element_id") is not None:
        same = same and (b.get("location") or {}).get("element_id") == c["element_id"]
    if not same:
        raise InputsError(f"bound line {c['line_id']}: {b['item_code']} {b['evidence_state']} {q} is not the bound "
                          f"{c['item_code']} {c['evidence_state']} {cq} (stale binding: re-bind before integrating)")


def changes_for(doc, l3030):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3030}
    if any(ln["item_code"] in ITEMS for ln in l3030) or \
            any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3030):
        raise InputsError("the candidate already carries roof build-up lines (applied once)")
    for c in list(doc["_bound"].values()) + list(doc["_parapets"].values()):
        _assert_bound(by.get(c["line_id"]), c)
    seen = set(by)
    changes, log = [], {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "m2": {}, "m3": {},
                        "roofs": len(doc["_roofs"]), "lines": 0}
    for rid in sorted(doc["_roofs"]):
        rf = doc["_roofs"][rid]
        tmpl = by[rf["membrane_line"]["line_id"]] if rf.get("membrane_line") else A3030._template(
            l3030, (WP_ROOF, WP_UPTURN))
        for name in LAYERS:
            ly = rf["_layers"][name]
            src = doc["_sources"][ly["source_task"]]
            ln = layer_line(rf, ly, src, tmpl)
            if ln["line_id"] in seen:
                raise ValueError(f"{METHOD}: line {ln['location']['element_id']} repeats an id")
            seen.add(ln["line_id"])
            held = None
            if ln["evidence_state"] == "BLOCKED_RFI":
                held = [{"what": f"{ln['item_code']} {ln['location']['element_id']}",
                         "why": ln["rfi"]["question"][:300], "range": ln["calculation"]["inputs"][REC_KEY]["basis"],
                         "scenario": None}]
            ev = ln["calculation"]["inputs"][REC_KEY]["evidence_status"]
            changes.append(A305._change(PIECE, "ADD", None, ln, drawing_reference=src["file"], held=held or [],
                                        downstream=[], verification=_ver(src), evidence_status=ev,
                                        codes=[PIECE, rid, name, ly["status"]], group=ln["item_code"]))
            k = f"{ln['item_code']} {ln['evidence_state']}"
            log["by_action"][k] = log["by_action"].get(k, 0) + 1
            log["lines"] += 1
            if ln["evidence_state"] == "MEASURED":
                log[ln["unit"]][ln["item_code"]] = _r(log[ln["unit"]].get(ln["item_code"], 0) + ln["measured_net"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ integrate / write
def check_roof_buildup(lines):
    """on finished lines: one line per (roof, layer); one screed volume per roof; every roof layer line carries its
    record; held / unknown BLANK; no roof layer on a parapet element; the bound membrane line of each roof present.
    -> summary."""
    out = {"lines": 0, "roofs": 0, "valued": {}, "blank": {}}
    seen, roofs = {}, {}
    ids = {ln["line_id"] for ln in lines}
    par_elems = {(ln.get("location") or {}).get("element_id") for ln in lines if ln["item_code"] == PARAPET}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] in ITEMS:
                raise ValueError(f"{METHOD}: {ln['line_id']} {ln['item_code']} has no V3.0.31 record")
            continue
        if ln["item_code"] not in ITEMS or LAYERS.get(rec["layer"], (None,))[0] != ln["item_code"]:
            raise ValueError(f"{METHOD}: {ln['line_id']} layer {rec.get('layer')} on {ln['item_code']}")
        key = (rec["roof"], rec["layer"])
        if key in seen:
            raise ValueError(f"{METHOD}: {key} on {seen[key]} and {ln['line_id']} (one line per roof and layer)")
        seen[key] = ln["line_id"]
        roofs.setdefault(rec["roof"], set()).add(rec["layer"])
        if (ln.get("location") or {}).get("element_id") in par_elems:
            raise ValueError(f"{METHOD}: {ln['line_id']} is a roof layer on a parapet element (the parapet is its own "
                             f"line: STRUCTURE / FACADE, never a roof layer)")
        for b in (rec.get("membrane_line"),):
            if b and b not in ids:
                raise ValueError(f"{METHOD}: {ln['line_id']} binds membrane line {b}, not in the candidate")
        k = f"{ln['item_code']}|{ln['unit']}"
        out["lines"] += 1
        if ln["evidence_state"] == "MEASURED":
            out["valued"][k] = _r(out["valued"].get(k, 0.0) + ln["measured_net"])
        elif ln["evidence_state"] == "BLOCKED_RFI":
            if ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held line {ln['line_id']} carries a figure (held is BLANK)")
            out["blank"][k] = out["blank"].get(k, 0) + 1
        else:
            raise ValueError(f"{METHOD}: {ln['line_id']} state {ln['evidence_state']}")
    for r, ls in roofs.items():
        if ls != set(LAYERS):
            raise ValueError(f"{METHOD}: roof {r} carries layers {sorted(ls)}, not all {sorted(LAYERS)}")
    screeds = [ln for ln in lines if ln["item_code"] == SCREED]
    if len(screeds) != len(roofs) or any(ln["unit"] != "m3" for ln in screeds):
        raise ValueError(f"{METHOD}: {len(screeds)} screed lines for {len(roofs)} roofs (one m3 volume per roof)")
    out["roofs"] = len(roofs)
    out["valued"] = dict(sorted(out["valued"].items()))
    out["blank"] = dict(sorted(out["blank"].items()))
    return out


def integrate(l3030, changes, for_lead=()):
    """-> (V3.0.31 lines, identity). Every V3.0.30 line is byte-identical (this package only adds lines)."""
    sid = {ln["line_id"] for ln in l3030}
    adds = []
    for c in changes:
        if c["piece"] != PIECE or c["action"] != "ADD":
            raise ValueError(f"{METHOD}: {c['piece']} {c['action']} (this version only adds roof build-up lines)")
        a = c["after"]
        if a["line_id"] in sid or a["item_code"] not in ITEMS or a["unit"] != ITEMS[a["item_code"]]:
            raise ValueError(f"{METHOD}: an added line repeats a V3.0.30 id or is not a roof build-up line")
        adds.append(a)
    out = list(l3030) + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = _family_guards(out, for_lead)       # every family guard up to V3.0.30, on the V3.0.31 lines
    roof = check_roof_buildup(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by30 = {ln["line_id"]: ln for ln in l3030}
    outside = out[:len(l3030)]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by30[ln["line_id"]]) != A30.line_sha(ln)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.30 line(s) differ")
    ident = {"v3_0_30_lines": len(l3030), "v3_0_31_lines": len(out), "v3_0_31_rows": len(changes), "replaced": 0,
             "added": len(adds), "outside_rows": len(outside), "outside_rows_identical_to_v3_0_30": len(outside),
             "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def _family_guards(out, for_lead):
    """every family guard V3.0.30 runs on its own lines, run again on the V3.0.31 lines (same functions)."""
    from engine.source import boq_line as BL
    from engine.source import arch_v3010 as A3010
    from engine.source import arch_v3011 as A3011
    from engine.source import arch_v3012 as A3012
    from engine.source import arch_v3014 as A3014
    from engine.source import arch_v3015 as A3015
    from engine.source import arch_v3021 as A3021
    from engine.source import arch_v3023 as A3023
    from engine.source import arch_v3024 as A3024
    from engine.source import arch_v3025 as A3025
    from engine.source import arch_v3026 as A3026
    from engine.source import arch_v3027 as A3027
    from engine.source import arch_v3028 as A3028
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    return {"wall_tile_family": A3021.check_tile_family(out), "parapet_family": A3023.check_parapet_family(out),
            "line_state": A3024.check_line_state(out, for_lead), "outdoor_family": A3025.check_outdoor_family(out),
            "blockwork": A3026.check_blockwork(out), "slab_bar_ends": A3027.check_slab_ends(out),
            "opening_reveals": A3028.check_reveals(out), "sills_thresholds": A3029.check_strips(out),
            "formwork_metalwork": A3030.check_formwork_metalwork(out)}


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"][REC_KEY]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": PIECE, "action": "ADD", "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "roof": rec["roof"], "roof_element": rec["roof_element"],
                     "layer": rec["layer"], "owner_trade": rec["owner_trade"], "status": rec["status"],
                     "edge": rec["edge"], "edge_handles": rec["edge_handles"], "basis": rec["basis"],
                     "membrane_line": rec["membrane_line"], "upturn_line": rec["upturn_line"],
                     "before_released_v2_9": b29, "before_v3_0_30": dict(A30._qty(None), state="NOT_IN_V3_0_30"),
                     "after_v3_0_31": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "line_id", "item_code", "floor", "element_id", "unit", "roof", "layer", "owner_trade",
              "status", "edge", "edge_handles", "basis_lo", "basis_hi", "range_cause", "membrane_line", "v2_9",
              "v3_0_30", "v3_0_31", "evidence_status", "held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_30", "vs_released_v2_9", "v2_9",
            "v3_0_30", "v3_0_31")


def ledger_csv(rows):
    def b(r, k):
        x = (r.get("basis") or {}).get(k)
        return "" if x is None else _fmt(x)
    return A305._csv([{"version": r["version"], "line_id": r["line_id"], "item_code": r["item_code"],
                       "floor": r["floor"] or "", "element_id": r["element_id"], "unit": r["unit"], "roof": r["roof"],
                       "layer": r["layer"], "owner_trade": r["owner_trade"], "status": r["status"],
                       "edge": r["edge"] or "", "edge_handles": " ".join(r["edge_handles"] or ())[:300],
                       "basis_lo": b(r, "lo"), "basis_hi": b(r, "hi"),
                       "range_cause": (r.get("basis") or {}).get("cause") or "",
                       "membrane_line": r["membrane_line"] or "",
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_30": "NOT_IN_V3_0_30", "v3_0_31": A302._q(r["after_v3_0_31"]),
                       "evidence_status": r["evidence_status"],
                       "held": "; ".join(f"{h['what']}: {h['why']}" for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit', '')[:8]}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3030, l3031, released_lines=None):
    b30 = {ln["line_id"]: ln for ln in l3030}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3031:
        o = b30.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_30": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_30": A302._q(A30._qty(o)) if o else "", "v3_0_31": A302._q(A30._qty(ln))})
    return out


def write(out, l3030, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_31_* files beside the V3_0_30_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3031, ident = integrate(l3030, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3030, l3031, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_30", {}).setdefault(d["vs_v3_0_30"], 0)
        dsum["vs_v3_0_30"][d["vs_v3_0_30"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t30, t31 = A304.code_totals(l3030), A304.code_totals(l3031)
    moved = {k: {"v3_0_30": t30.get(k), "v3_0_31": t31.get(k)} for k in sorted(set(t30) | set(t31))
             if t30.get(k) != t31.get(k)}
    if any(k.split("|")[0] not in ITEMS for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the roof build-up items: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "named_not_lines": (doc or {}).get("named_not_lines") or [], "waiting_pieces": WAITING,
           "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_31_BOQ_LINES.json": BL.dumps(l3031),
             "V3_0_31_BOQ_LINES.csv": A30._lines_csv(l3031),
             "V3_0_31_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_31_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_31_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_31_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(ITEMS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "layer_line",
           "changes_for", "check_roof_buildup", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
