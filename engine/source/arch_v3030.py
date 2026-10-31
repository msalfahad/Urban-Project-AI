"""ARCH_TAKEOFF_V3.0.30 (T-199): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.29 (engine.source.arch_v30,
arch_v301 .. arch_v3029), extended with the two BOQ categories the candidate lacked, each as its own line family:

  FORMWORK_FILL   formwork contact area (m2) of every cast-in-place member, face by face, from the Checker-merged
                  formwork ledger bound to the candidate concrete lines (T-332 r2 FILL table on the formwork r5 faces
                  = T-163 r3 + T-264 r4 + T-293 + T-308 r5) and the stair side faces (T-352): ONE formwork line per
                  (concrete line, status, alternative, method) of the FILL table, beside the concrete line that owns
                  the member (never inside its m3); STR.FORMWORK (B10-13) for every member, STR.FORMWORK.STAIR (B7-13)
                  for the stair lines;
  METALWORK_FILL  railings / balustrades (lm, installed path) and shutters (pcs) from the Checker-merged census
                  (T-164): ONE line per railing run and per drawn shutter pair.

The physical element (ERS 2026-10-22 s.2.1): a formed face is a concrete surface cast against a form; it bounds ONE
member and is booked once, beside the line carrying that member's concrete. A face cast against ground, blinding or
masonry has no form. Below the existing ground the owner question OQ-10 is open: the FORMED and EARTH_CAST readings
travel together on ONE blank line, never summed, never chosen. A railing run is its installed length (sloping on a
flight, UP-STAIR-012), never the plan projection; height and material are specification. A shutter is counted by leaf;
its area basis is not set by any rule (HELD).

Line states (never a value of this module's own):
  CALCULATED faces  -> the concrete line's own state (SOURCE_DERIVED / PROVISIONAL): measured_net = the face sum;
  HELD / CONFLICT   -> BLOCKED_RFI, BLANK (never 0); the face ids, bounds and held_from beside it, the cause named;
  OQ-10 alternatives-> BLOCKED_RFI, BLANK; FORMED and EARTH_CAST figures beside it, never added to each other;
  NOT_APPLICABLE    -> NOT_APPLICABLE_WITH_EVIDENCE with the face ledger's reason;
  untied HELD faces -> one BLANK line per face (no candidate concrete line carries the member);
  railings          -> DRAWING-CONFIRMED runs MEASURED (lm); HELD / UNKNOWN runs BLANK with the measured part named;
                       EXCLUDED runs EXCLUDED_WITH_REASON;
  shutters          -> leaves MEASURED (pcs, a drawn count); the m2 line BLANK (no rule basis).

R-T199-1 (every villa): formwork is booked face by face, once, beside its member's concrete line; E (element method) is
the comparison method, carried beside the drawing method G, never a second line; a valued formwork line needs a live
concrete line with the same id, element, state and quantity as the ledger's binding (else the binding is stale and the
build stops); a valued line on a concrete line a Checker downgrade record holds is refused; an S1 scenario face is never
in the candidate; OQ-10 alternatives are never summed or chosen; HELD is BLANK, never 0. Railings: installed length,
one run one line, a HELD part never inside a confirmed run; shutters by count, area HELD.

Every V3.0.29 line is byte-identical in V3.0.30 (this package only ADDS lines; asserted). Files: V3_0_30_BOQ_LINES.json /
.csv, V3_0_30_INTEGRATION_LEDGER.json / .csv, V3_0_30_DIFF.csv, V3_0_30_RUN.json. Nothing here names a project, a sheet,
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
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3023 as A3023
from engine.source import arch_v3024 as A3024
from engine.source import arch_v3025 as A3025
from engine.source import arch_v3026 as A3026
from engine.source import arch_v3027 as A3027
from engine.source import arch_v3028 as A3028
from engine.source import arch_v3029 as A3029

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.30"
EXTENDS = A3029.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T199_ARCH_V3_0_30"
INPUTS_SCHEMA = "URBAN_V3030_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3030_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3015.InputsError
_r = A3018._r
RULE_ID, RULE_VERSION = "R-T199-1", "T-199"
FW, FW_PIECE, MW_PIECE = "FW", "FORMWORK_FILL", "METALWORK_FILL"
REC_KEY = "formwork_metalwork_v3030"
FW_CODE, FW_STAIR_CODE = "STR.FORMWORK", "STR.FORMWORK.STAIR"
STAIR_CONC = "STR.CONC.STAIR"
RAIL_STAIR, RAIL_GUARD, HANDRAIL, SHUTTER = "FIN.RAILING", "MET.RAILING.GUARD", "FIN.HANDRAIL", "ARCH.SHUTTER"
NEW_ITEMS = {   # item master entries for the codes boq_line.ITEMS does not carry (en, ar, trade)
    FW_CODE: ("Formwork, contact area (cast-in-place members)", "شدة خشبية (مساحة التلامس)", "FORMWORK"),
    FW_STAIR_CODE: ("Stair formwork, contact area", "شدة الدرج", "FORMWORK"),
    RAIL_GUARD: ("Guard railing, installed length (roof / floor edge / fence)", "درابزين حماية (الطول المركب)",
                 "RAILING"),
    SHUTTER: ("Shutters", "شتر", "OPENINGS"),
}
ITEMS = {FW_CODE: "m2", FW_STAIR_CODE: "m2", RAIL_STAIR: "lm", RAIL_GUARD: "lm", HANDRAIL: "lm", SHUTTER: "pcs|m2"}
FW_STATUSES = ("CALCULATED", "HELD", "CONFLICT")
FW_METHODS = ("G", "E=G")
LIVE_CONC = ("SOURCE_DERIVED", "PROVISIONAL")
OQ10 = ("OQ10_FORMED", "OQ10_EARTH_CAST")
RAIL_KIND = {"STAIR_GUARD": RAIL_STAIR, "STAIR_GUARD_OR_STRING": RAIL_STAIR, "WALL_HANDRAIL": HANDRAIL,
             "ROOF_GUARD": RAIL_GUARD, "BALCONY_GUARD": RAIL_GUARD, "FLOOR_EDGE_GUARD": RAIL_GUARD,
             "FENCE_RAILING": RAIL_GUARD}
RAIL_STATUSES = ("DRAWING-CONFIRMED", "HELD", "UNKNOWN", "EXCLUDED")
TOL = 1e-6

PIECES = {
    FW_PIECE: {
        "module": "engine/source/arch_v3030.py (formwork as its own line family: one line per FILL row of the "
                  "Checker-merged face ledger, beside the concrete line owning the member; held faces BLANK)",
        "policy": "FORMWORK_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["none on record for formwork (OWNER_QUESTIONS_ANSWERED searched: 'formwork', 'shuttering'; "
                        "OQ-10 below-ground faces open)", "Q-74 A (oblique straps: formwork on its own geometry, "
                        "the T-174 axis lengths)", "UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 "
                        "s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "none on record: no answered owner rule measures formwork; OQ-10 (formed vs earth-cast "
                               "below the existing ground) is open, so both readings are carried, never chosen",
        "drawing_method": "per member, the drawn faces cast against a form (method G: slab soffits, beam soffits and "
                          "sides below the slab, column shafts, slab edges, stair soffits / risers / sides, pool "
                          "faces above EG) on 'ST7757 dxf.dxf' by handle (T-163 r3 .. T-308 r5, T-332 r2, T-352); the "
                          "element method E (struct_n10 formwork()) carried beside as the comparison"},
    MW_PIECE: {
        "module": "engine/source/arch_v3030.py (railings by run in lm on the installed path, shutters by leaf in "
                  "pcs, from the Checker-merged census; held runs and areas BLANK)",
        "policy": "METALWORK_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["UP-STAIR-012 v2.0.0 (installed 3-D path, never the plan)", "UP-STAIR-013 v1.0.0 (wall "
                        "handrail only where shown)", "Q-33 (windows aluminium; shutters are not windows: "
                        "material HELD)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "owner rule UP-STAIR-012: a stair guard is billed on its sloping installed length; "
                               "roof / floor-edge guards by their drawn length; no owner rule sets a shutter area "
                               "basis (count only)",
        "drawing_method": "railing = the 50 mm plan band's centreline (corners once), cross-checked on the "
                          "elevations; stair guards per tread along the band (T-164); shutters counted on the "
                          "elevations (W14 SE, W11 / W12 fence elevation)"},
}
WAITING = dict(A3029.WAITING)
WAITING.update({
    "FORMWORK_OQ10": "below-ground footing / ground-beam / strap / pool faces: FORMED or EARTH_CAST (owner question "
                     "OQ-10 open): both readings beside a BLANK line, never summed, never chosen",
    "FORMWORK_HELD_FACES": "faces held in the ledger (joint faces, sunken-panel edges, stair wall / member sides, "
                           "parapet RC faces with no line, lift-pit walls D-43, SPLIT_UNRESOLVED pieces, the F8 / "
                           "pool conflict, the pool back face Q-28): BLANK by name",
    "RAILINGS_HELD": "RL-04 GF sea strip (plan vs elevation; neither metalwork nor the parapet chain carries a figure), "
                     "RL-07 ST-01 inner balustrade (winder and half-landing turns not dimensioned), RL-09 ST-02 outer "
                     "band (guard or string UNKNOWN), RL-10 fence railing (length not printed), RL-11 ST-03 entrance "
                     "guard (none drawn): BLANK by name",
    "SHUTTER_AREA": "shutter m2 and material: no owner rule sets the basis (panel / leaf / opening): HELD",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _pos(x, where, zero_ok=False):
    if not isinstance(x, (int, float)) or x != x or x < 0 or (x == 0 and not zero_ok):
        raise InputsError(f"{where}: {x!r} is not a positive figure")
    return float(x)


def load_inputs(doc, project_id=None):
    """URBAN_V3030_INPUTS_V1 -> the validated doc (every face once; held blank; S1 never)."""
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
    faces = {}

    def book(fid, who):
        if "S1" in str(fid).upper().split("."):
            raise InputsError(f"face {fid}: an S1 scenario face is never in the candidate (ScenarioLeak)")
        if fid in faces:
            raise InputsError(f"face {fid}: booked by {faces[fid]} and {who} (one face, one line)")
        faces[fid] = who

    def src_of(r, where):
        if r.get("source_task") not in srcs:
            raise InputsError(f"{where}: no merged source for {r.get('source_task')!r}")

    conc = {}
    for c in doc.get("bound_concrete_lines") or ():
        _need(c, ("line_id", "item_code", "evidence_state"), "bound concrete line")
        if not str(c["item_code"]).startswith("STR.CONC."):
            raise InputsError(f"bound line {c['line_id']}: {c['item_code']} is not a concrete line")
        conc[c["line_id"]] = c
    dg = set(doc.get("downgrade_bound_lines") or ())
    for r in doc.get("formwork") or ():
        where = f"formwork {r.get('line_id')} {r.get('status')} {r.get('alternative')} {r.get('method')}"
        src_of(r, where)
        if r.get("line_id") not in conc:
            raise InputsError(f"{where}: its concrete line is not in the binding")
        if r.get("status") not in FW_STATUSES or r.get("method") not in FW_METHODS:
            raise InputsError(f"{where}: status / method (E is the comparison method, never a line)")
        if r.get("alternative") and r["status"] == "CALCULATED":
            raise InputsError(f"{where}: an OQ-10 reading is an alternative, never a valued line of its own")
        if r["status"] == "CALCULATED":   # a traced 0 (an end on a drawn face: no form) is a measured value
            _pos(r.get("m2"), where, zero_ok=True)
            if conc[r["line_id"]]["evidence_state"] not in LIVE_CONC:
                raise InputsError(f"{where}: a valued face on a {conc[r['line_id']]['evidence_state']} concrete line "
                                  f"(held with its line, never valued)")
            if r["line_id"] in dg:
                raise InputsError(f"{where}: a valued face on a concrete line a Checker downgrade record holds")
        elif r.get("m2") is not None:
            raise InputsError(f"{where}: a held face given a figure (held is BLANK, never 0)")
        for f in r.get("face_ids") or ():
            book(f, where)
        if len(r.get("face_ids") or ()) != r.get("faces"):
            raise InputsError(f"{where}: {r.get('faces')} faces but {len(r.get('face_ids') or ())} face ids")
    for a in doc.get("alternatives") or ():
        where = f"OQ-10 {a.get('line_id')} {a.get('method')}"
        src_of(a, where)
        alts = a.get("alternatives") or {}
        if "OQ10_FORMED" not in alts or set(alts) - set(OQ10) or a.get("line_id") not in conc:
            raise InputsError(f"{where}: FORMED with its EARTH_CAST twin on a bound concrete line")
        for k, v in alts.items():
            for f in v.get("face_ids") or ():
                book(f, where)
    for r in doc.get("not_applicable") or ():
        where = f"not applicable {r.get('line_id')}"
        src_of(r, where)
        if not r.get("basis") or r.get("m2") is not None:
            raise InputsError(f"{where}: needs its reason and carries no figure")
        for f in r.get("face_ids") or ():
            book(f, where)
    for u in doc.get("untied") or ():
        where = f"untied face {u.get('face_id')}"
        src_of(u, where)
        if not u.get("reason"):
            raise InputsError(f"{where}: an untied face names why no line carries it")
        if u.get("m2") is not None:
            raise InputsError(f"{where}: held is BLANK, never 0")
        book(u["face_id"], where)
    for r in doc.get("stair_sides") or ():
        where = f"stair side {r.get('line_id')} {r.get('status')}"
        src_of(r, where)
        if r.get("line_id") not in conc or conc[r["line_id"]]["item_code"] != STAIR_CONC:
            raise InputsError(f"{where}: not a bound stair concrete line")
        if r.get("status") == "CALCULATED":
            _pos(r.get("m2"), where)
            if conc[r["line_id"]]["evidence_state"] not in LIVE_CONC:
                raise InputsError(f"{where}: a valued side on a blank stair line")
        elif r.get("status") in ("HELD", "CONFLICT"):
            if r.get("m2") is not None:
                raise InputsError(f"{where}: held is BLANK, never 0")
        else:
            raise InputsError(f"{where}: status {r.get('status')!r}")
        for f in r.get("face_ids") or ():
            book(f, where)
    runs = set()
    for r in doc.get("railings") or ():
        where = f"railing {r.get('run')}"
        src_of(r, where)
        if r.get("run") in runs:
            raise InputsError(f"{where}: one run, one line")
        runs.add(r["run"])
        if r.get("kind") not in RAIL_KIND or r.get("status") not in RAIL_STATUSES:
            raise InputsError(f"{where}: kind / status {r.get('kind')} / {r.get('status')}")
        if r["status"] == "DRAWING-CONFIRMED":
            _pos(r.get("lm"), where)
            segs = [s.get("lm") for s in r.get("segments") or ()]
            if any(s is None for s in segs) or abs(sum(segs) - r["lm"]) > TOL:
                raise InputsError(f"{where}: a confirmed run is the sum of its measured segments")
            if any(s.get("status") != "DRAWING-CONFIRMED" for s in r.get("segments") or ()):
                raise InputsError(f"{where}: a HELD segment inside a confirmed run")
        elif r.get("lm") is not None:
            raise InputsError(f"{where}: a {r['status']} run carries no lm (its measured part beside it)")
        if r.get("verified") and r["status"] != "DRAWING-CONFIRMED":
            raise InputsError(f"{where}: only a confirmed run can carry the Checker's re-measure")
    ops = set()
    for s in doc.get("shutters") or ():
        where = f"shutters {s.get('opening')}"
        src_of(s, where)
        if s.get("opening") in ops or not isinstance(s.get("pcs"), int) or s["pcs"] <= 0:
            raise InputsError(f"{where}: one pair line per opening, a drawn leaf count")
        if s.get("m2") is not None:
            raise InputsError(f"{where}: shutter area has no rule basis (HELD, blank)")
        ops.add(s["opening"])
    return dict(doc, _sources=srcs, _faces=faces, _conc=conc, _dg=dg)


# ================================================================================================ lines
def _rec(src, piece, **kw):
    return dict({"policy": PIECES[piece]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(src):
    return {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
            "ledger": src["file"], "ledger_sha256": src["sha256"]}


def _fmt(x):
    return "" if x is None else f"{_r(x, 6):.6f}".rstrip("0").rstrip(".")


def _new(tmpl, *, item_code, unit, evidence_state, element_id, floor, phys, formula, rec, measured_net=None, rfi=None,
         notes="", material_state="BY_SPEC"):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    en, ar, tr = NEW_ITEMS.get(item_code, (None, None, None))
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"], item_code=item_code,
                      unit=unit, evidence_state=evidence_state, measured_net=measured_net, element_id=element_id,
                      floor=floor, physical_element=phys, formula=formula[:700], inputs={REC_KEY: rec},
                      documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source=tmpl["source"]["geometry_source"],
                      geometry_confidence=tmpl["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=material_state, rfi=rfi,
                      notes=notes[:600], item_en=en, item_ar=ar, trade=tr)
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def _assert_binding(b, c):
    """the concrete line the ledger bound must stand in the candidate exactly as bound (stale binding stops)."""
    if b is None:
        raise InputsError(f"concrete line {c['line_id']}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    lo, hi = A3029._figure(b) if b["evidence_state"] == "BOUNDED_EXPOSURE" else (None, None)
    same = (b["item_code"] == c["item_code"] and b["evidence_state"] == c["evidence_state"] and
            (c.get("element_id") is None or loc.get("element_id") == c["element_id"]))
    q, cq = b.get("measured_net"), c.get("measured_net")
    same = same and ((q is None and cq is None) or (q is not None and cq is not None and abs(q - cq) <= TOL))
    if b["evidence_state"] == "BOUNDED_EXPOSURE":
        same = same and abs((lo or 0) - (c.get("bounded_low") or 0)) <= TOL and \
            abs((hi or 0) - (c.get("bounded_high") or 0)) <= TOL
    if not same:
        raise InputsError(f"concrete line {c['line_id']}: {b['item_code']} {b['evidence_state']} {q} is not the bound "
                          f"{c['item_code']} {c['evidence_state']} {cq} (stale binding: re-bind before integrating)")


def _fw_code(item):
    return FW_STAIR_CODE if item == STAIR_CONC else FW_CODE


def _member(b):
    return f"{b['item_code'].split('.')[-1].lower().replace('_', ' ')} {(b.get('location') or {}).get('element_id')}"


def _ev_status(r):
    """the s.5 evidence status of a formwork row as merged: CALCULATED stays CALCULATED; a face the ledger marks
    ASSUMED - OWNER-APPROVED keeps that mark beside it (never promoted)."""
    if r["status"] != "CALCULATED":
        return "HELD"
    asm = sorted(f for f, e in (r.get("face_evidence") or {}).items() if "OWNER-APPROVED" in str(e))
    return "CALCULATED" + (f"; ASSUMED — OWNER-APPROVED on {' '.join(asm)}" if asm else "")


def fw_line(b, r, src, comparison_e=None):
    """one FILL row (line, status, alternative, method) or one T-352 stair side row -> its formwork line."""
    code = _fw_code(b["item_code"])
    kind = r.get("kind", "FACES")
    st = r["status"]
    alt = r.get("alternative") or "-"
    eid = f"FW:{b['line_id']}:{kind}:{st}:{alt}:{r.get('method') or 'G'}"
    floor = (b.get("location") or {}).get("floor")
    ids = r.get("face_ids") or []
    member = _member(b)
    bounds = {k: r.get(k) for k in ("lo", "hi", "held_from") if r.get(k) is not None}
    rec = _rec(src, FW_PIECE, action="ADD", status=st, alternative=r.get("alternative"), method=r.get("method"),
               concrete_line=b["line_id"], concrete_item=b["item_code"], concrete_state=b["evidence_state"],
               face_ids=ids, faces=len(ids), m2=r.get("m2"), bounds=bounds or None,
               bound_classes=r.get("bound_classes"), comparison_method_e_m2=comparison_e,
               face_evidence=r.get("face_evidence"), evidence_status=_ev_status(r), notes=r.get("notes") or None)
    part = "side faces" if kind == "SIDE" else "formed faces"
    if st == "CALCULATED":
        formula = (f"formwork of {member} ({part}, method {r.get('method') or 'G'}): {len(ids)} face(s) "
                   f"{' '.join(ids)[:300]} = {_fmt(r['m2'])} m2 contact area, beside concrete line {b['line_id']}"
                   + (f"; element method E on the same member {_fmt(comparison_e)} m2 (comparison only)"
                      if comparison_e is not None else ""))
        return _new(b, item_code=code, unit="m2", evidence_state=b["evidence_state"], element_id=eid, floor=floor,
                    phys=f"formwork {part}", formula=formula, rec=rec, measured_net=_r(r["m2"]),
                    notes=f"{METHOD}: formwork booked face by face ({src['task']} MERGED {src['merge_commit'][:8]}); "
                          f"CALCULATED, NOT RELEASED")
    why = (f"HELD (blank in the BOQ, never 0): formwork of {member} ({part}) {st}: {len(ids)} face(s) "
           f"{' '.join(ids)[:200]}; bounds {json.dumps(bounds) if bounds else 'none'}; classes "
           f"{r.get('bound_classes') or '-'}; the concrete line is {b['evidence_state']}")
    return _new(b, item_code=code, unit="m2", evidence_state="BLOCKED_RFI", element_id=eid, floor=floor,
                phys=f"formwork {part}", formula=why, rec=rec, rfi={"question": why[:900], "unlocks": eid},
                notes=f"{METHOD}: formwork faces HELD by name ({src['task']} MERGED {src['merge_commit'][:8]})")


def alt_line(b, a, src):
    eid = f"FW:{b['line_id']}:OQ10:{a['method']}"
    al = a["alternatives"]
    fm, ec = al.get("OQ10_FORMED") or {}, al.get("OQ10_EARTH_CAST") or {}
    member = _member(b)
    q = (f"HELD on owner question OQ-10 (blank in the BOQ, never 0, never summed): formwork of {member} below the "
         f"existing ground, method {a['method']}: FORMED {_fmt(fm.get('m2'))} m2 ({' '.join(fm.get('face_ids') or [])[:150]})"
         f" or EARTH_CAST {_fmt(ec.get('m2')) if ec else 'no row'} m2 "
         f"({' '.join(ec.get('face_ids') or [])[:150]}); which one is the owner's decision")
    rec = _rec(src, FW_PIECE, action="ADD", status="ALTERNATIVE", alternative="OQ-10", method=a["method"],
               concrete_line=b["line_id"], concrete_item=b["item_code"], concrete_state=b["evidence_state"],
               face_ids=sorted((fm.get("face_ids") or []) + (ec.get("face_ids") or [])), alternatives=al,
               evidence_status="HELD (OQ-10 alternatives)")
    return _new(b, item_code=_fw_code(b["item_code"]), unit="m2", evidence_state="BLOCKED_RFI", element_id=eid,
                floor=(b.get("location") or {}).get("floor"), phys="formwork below existing ground", formula=q,
                rec=rec, rfi={"question": q[:900], "unlocks": eid},
                notes=f"{METHOD}: OQ-10 readings beside a blank line ({src['task']} MERGED {src['merge_commit'][:8]})")


def na_line(b, r, src):
    eid = f"FW:{b['line_id']}:FACES:NOT_APPLICABLE:-:{r.get('method') or 'G'}"
    rec = _rec(src, FW_PIECE, action="ADD", status="NOT_APPLICABLE", concrete_line=b["line_id"],
               face_ids=r["face_ids"], faces=len(r["face_ids"]), evidence_status="NOT_APPLICABLE", basis=r["basis"])
    return _new(b, item_code=_fw_code(b["item_code"]), unit="m2", evidence_state="NOT_APPLICABLE_WITH_EVIDENCE",
                element_id=eid, floor=(b.get("location") or {}).get("floor"), phys="formwork faces",
                formula=f"formwork of {_member(b)}: not applicable ({' '.join(r['face_ids'])}): {r['basis']}", rec=rec,
                notes=f"{METHOD}: not applicable: {r['basis']}")


def untied_line(u, src, tmpl):
    code = FW_STAIR_CODE if u["element"] == "STAIR" else FW_CODE
    eid = f"FW:FACE:{u['face_id']}"
    bounds = {k: u.get(k) for k in ("lo", "hi", "held_from") if u.get(k) is not None}
    q = (f"HELD (blank in the BOQ, never 0): formwork face {u['face_id']} ({u['element'].lower()}, {u['item']}) "
         f"{u['tie']}: {u['reason']}; bounds {json.dumps(bounds) if bounds else 'none'}; no candidate concrete line "
         f"carries the member")
    rec = _rec(src, FW_PIECE, action="ADD", status="HELD", tie=u["tie"], face_ids=[u["face_id"]], faces=1,
               element=u["element"], method=u.get("method"), alternative=u.get("alternative"), bounds=bounds or None,
               concrete_line=None, evidence_status="HELD")
    return _new(tmpl, item_code=code, unit="m2", evidence_state="BLOCKED_RFI", element_id=eid, floor=u.get("floor"),
                phys=f"formwork, {u['element'].lower()} (no concrete line)", formula=q, rec=rec,
                rfi={"question": q[:900], "unlocks": eid},
                notes=f"{METHOD}: untied formwork face HELD by name ({src['task']} MERGED {src['merge_commit'][:8]})")


def rail_line(r, src, tmpl):
    code = RAIL_KIND[r["kind"]]
    eid = f"RAIL:{r['run']}"
    segs = r.get("segments") or []
    ev = ("VERIFIED (Checker re-measure, T-164 verdict e / f)" if r.get("verified") else r["status"])
    rec = _rec(src, MW_PIECE, action="ADD", run=r["run"], kind=r["kind"], status=r["status"], segments=segs,
               lm=r.get("lm"), measured_part_lm=r.get("measured_part_lm"),
               unmeasured_segments=r.get("unmeasured_segments"), height_printed_m=r.get("height_printed_m"),
               evidence_status=ev, source_ref=r.get("source"))
    phys = r["kind"].lower().replace("_", " ")
    seg_txt = " + ".join(_fmt(s["lm"]) for s in segs if s.get("lm") is not None)
    if r["status"] == "DRAWING-CONFIRMED":
        formula = (f"{r['run']} {phys}: installed length {seg_txt} = {_fmt(r['lm'])} lm ({len(segs)} segment(s), "
                   f"corners once; height {_fmt(r.get('height_printed_m')) or 'not printed'} is specification, not a "
                   f"length)")
        return _new(tmpl, item_code=code, unit="lm", evidence_state="MEASURED", element_id=eid, floor=None, phys=phys,
                    formula=formula, rec=rec, measured_net=_r(r["lm"]),
                    notes=f"{METHOD}: railing run as its own line ({src['task']} MERGED {src['merge_commit'][:8]}); "
                          f"{ev}; material by specification")
    if r["status"] == "EXCLUDED":
        why = f"{r['run']} {phys}: {r.get('note') or ''} {segs[0]['segment'] if segs else ''}".strip()
        return _new(tmpl, item_code=code, unit="lm", evidence_state="EXCLUDED_WITH_REASON", element_id=eid, floor=None,
                    phys=phys, formula=f"EXCLUDED: {why} (UP-STAIR-013: a wall handrail only where shown)", rec=rec,
                    notes=f"{METHOD}: excluded: none drawn (UP-STAIR-013)")
    q = (f"{r['status']} (blank in the BOQ, never 0): {r['run']} {phys}: "
         + (f"measured part {_fmt(r['measured_part_lm'])} lm ({seg_txt}), " if r.get("measured_part_lm") else "")
         + (f"{r['unmeasured_segments']} segment(s) not measurable; " if r.get("unmeasured_segments") else "")
         + f"{r.get('note') or ''}")
    return _new(tmpl, item_code=code, unit="lm", evidence_state="BLOCKED_RFI", element_id=eid, floor=None, phys=phys,
                formula=q, rec=rec, rfi={"question": q[:900], "unlocks": eid},
                notes=f"{METHOD}: railing run {r['status']} by name ({src['task']} MERGED {src['merge_commit'][:8]})")


def shutter_lines(s, src, tmpl):
    phys = "shutter leaves"
    rec = _rec(src, MW_PIECE, action="ADD", opening=s["opening"], pcs=s["pcs"], leaf_size_m=s.get("leaf_size_m"),
               evidence_status="DRAWING-CONFIRMED (count)", source_ref=s.get("source"))
    a = _new(tmpl, item_code=SHUTTER, unit="pcs", evidence_state="MEASURED", element_id=f"SHUTTER:{s['opening']}",
             floor=None, phys=phys, measured_net=s["pcs"], rec=rec,
             formula=f"{s['opening']} shutters: {s['pcs']} leaves drawn ({s.get('source') or ''})",
             notes=f"{METHOD}: shutters by leaf count ({src['task']} MERGED {src['merge_commit'][:8]}); material HELD")
    q = (f"HELD (blank in the BOQ, never 0): {s['opening']} shutter area: no owner rule sets the basis (louvre panel, "
         f"leaf outline or opening); leaf outline {s.get('leaf_size_m') or 'not printed'}; material not printed")
    rec2 = _rec(src, MW_PIECE, action="ADD", opening=s["opening"], evidence_status="HELD")
    b = _new(tmpl, item_code=SHUTTER, unit="m2", evidence_state="BLOCKED_RFI",
             element_id=f"SHUTTER:{s['opening']}:AREA", floor=None, phys="shutter area", formula=q, rec=rec2,
             rfi={"question": q[:900], "unlocks": f"SHUTTER:{s['opening']}:AREA"},
             notes=f"{METHOD}: shutter area HELD by name")
    return a, b


def _template(lines, codes, unit=None):
    pick = [ln for ln in lines if ln["item_code"] in codes and (unit is None or ln["unit"] == unit)]
    if not pick:
        raise InputsError(f"no {codes} line in the candidate to take the plan documents from")
    return sorted(pick, key=lambda x: x["line_id"])[0]


def changes_for(doc, l3029):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": FW_PIECE, "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3029}
    if any(ln["item_code"] in (FW_CODE, FW_STAIR_CODE, RAIL_GUARD, SHUTTER) for ln in l3029) or \
            any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3029):
        raise InputsError("the candidate already carries formwork / metalwork lines of this package (applied once)")
    for c in doc["_conc"].values():
        _assert_binding(by.get(c["line_id"]), c)
    seen = set(by)
    changes, log = [], {"piece": f"{FW_PIECE}+{MW_PIECE}", "state": "RUN", "sources": doc["sources"],
                        "by_action": {}, "m2": {}, "lm": {}, "pcs": {}, "faces": len(doc["_faces"]),
                        "named_not_lines": len(doc.get("named_not_lines") or ())}

    def add(ln, src, piece, ev, codes, held=None):
        if ln["line_id"] in seen:
            raise ValueError(f"{METHOD}: line {ln['location']['element_id']} repeats an id")
        seen.add(ln["line_id"])
        changes.append(A305._change(piece, "ADD", None, ln, drawing_reference=src["file"], held=held or [],
                                    downstream=[], verification=_ver(src), evidence_status=ev, codes=codes,
                                    group=ln["item_code"]))
        k = f"{ln['item_code']} {ln['evidence_state']}"
        log["by_action"][k] = log["by_action"].get(k, 0) + 1
        if ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL"):
            u = {"m2": "m2", "lm": "lm", "pcs": "pcs"}[ln["unit"]]
            log[u][ln["item_code"]] = _r(log[u].get(ln["item_code"], 0) + ln["measured_net"])

    def held_of(ln):
        return [{"what": f"{ln['item_code']} {ln['location']['element_id']}", "why": (ln.get("rfi") or {}).get(
            "question", "")[:300], "range": None, "scenario": None}]

    cmp_e = doc.get("comparison_e_m2") or {}
    for r in doc.get("formwork") or ():
        src = doc["_sources"][r["source_task"]]
        ln = fw_line(by[r["line_id"]], r, src, cmp_e.get(r["line_id"]))
        st = r["status"]
        add(ln, src, FW_PIECE, "CALCULATED" if st == "CALCULATED" else "HELD", [FW_PIECE, st, r["method"]],
            None if st == "CALCULATED" else held_of(ln))
    for a in doc.get("alternatives") or ():
        src = doc["_sources"][a["source_task"]]
        ln = alt_line(by[a["line_id"]], a, src)
        add(ln, src, FW_PIECE, "HELD (OQ-10 alternatives)", [FW_PIECE, "OQ10", a["method"]], held_of(ln))
    for r in doc.get("not_applicable") or ():
        src = doc["_sources"][r["source_task"]]
        add(na_line(by[r["line_id"]], r, src), src, FW_PIECE, "NOT_APPLICABLE", [FW_PIECE, "NOT_APPLICABLE"])
    for r in doc.get("stair_sides") or ():
        src = doc["_sources"][r["source_task"]]
        rr = dict(r, kind="SIDE", method="G", alternative=None)
        ln = fw_line(by[r["line_id"]], rr, src)
        add(ln, src, FW_PIECE, _ev_status(r), [FW_PIECE, "STAIR_SIDE", r["status"]], None if r["status"] == "CALCULATED" else held_of(ln))
    conc_tmpl = _template(l3029, ("STR.CONC.SLAB", "STR.CONC.BEAM"))
    for u in doc.get("untied") or ():
        src = doc["_sources"][u["source_task"]]
        ln = untied_line(u, src, conc_tmpl)
        add(ln, src, FW_PIECE, "HELD", [FW_PIECE, "UNTIED", u["tie"]], held_of(ln))
    rail_tmpl = _template(l3029, (RAIL_STAIR, "ARCH.WINDOW", "ARCH.WINDOW_REVEAL"))
    for r in doc.get("railings") or ():
        src = doc["_sources"][r["source_task"]]
        ln = rail_line(r, src, rail_tmpl)
        ev = ln["calculation"]["inputs"][REC_KEY]["evidence_status"]
        add(ln, src, MW_PIECE, ev, [MW_PIECE, r["run"], r["status"]],
            held_of(ln) if ln["evidence_state"] == "BLOCKED_RFI" else None)
    for s in doc.get("shutters") or ():
        src = doc["_sources"][s["source_task"]]
        a, b = shutter_lines(s, src, rail_tmpl)
        add(a, src, MW_PIECE, "DRAWING-CONFIRMED (count)", [MW_PIECE, "SHUTTER", "PCS"])
        add(b, src, MW_PIECE, "HELD", [MW_PIECE, "SHUTTER", "M2"], held_of(b))
    for k in ("m2", "lm", "pcs"):
        log[k] = dict(sorted(log[k].items()))
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ integrate / write
def check_formwork_metalwork(lines):
    """on finished lines: every face once across the formwork lines; a valued formwork line beside a live concrete line
    of the same id and equal to its faces' m2 record; held / alternative lines BLANK; no S1 face; every railing run
    once. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    faces, runs, out = {}, {}, {"formwork_lines": 0, "metalwork_lines": 0, "valued": {}, "blank": {},
                                "faces": 0, "oq10_lines": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] in (FW_CODE, FW_STAIR_CODE, RAIL_GUARD, SHUTTER):
                raise ValueError(f"{METHOD}: {ln['line_id']} {ln['item_code']} has no V3.0.30 record")
            continue
        k = f"{ln['item_code']}|{ln['unit']}"
        if rec["policy"] == PIECES[FW_PIECE]["policy"]:
            out["formwork_lines"] += 1
            for f in rec.get("face_ids") or ():
                if "S1" in str(f).upper().split("."):
                    raise ValueError(f"{METHOD}: S1 face {f} in the candidate (ScenarioLeak)")
                if f in faces:
                    raise ValueError(f"{METHOD}: face {f} on {faces[f]} and {ln['line_id']} (double count)")
                faces[f] = ln["line_id"]
            if rec.get("status") == "ALTERNATIVE":
                out["oq10_lines"] += 1
            cl = rec.get("concrete_line")
            if ln["evidence_state"] in ("SOURCE_DERIVED", "PROVISIONAL"):
                c = by.get(cl)
                if c is None or c["evidence_state"] != ln["evidence_state"] or not str(c["item_code"]).startswith(
                        "STR.CONC.") or abs(float(rec["m2"]) - ln["measured_net"]) > TOL:
                    raise ValueError(f"{METHOD}: valued formwork {ln['line_id']} not beside its live concrete line "
                                     f"{cl} or not its faces' m2")
        else:
            out["metalwork_lines"] += 1
            run = rec.get("run") or f"SHUTTER {rec.get('opening')} {ln['unit']}"
            if run in runs:
                raise ValueError(f"{METHOD}: {run} on {runs[run]} and {ln['line_id']}")
            runs[run] = ln["line_id"]
        if ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL"):
            out["valued"][k] = _r(out["valued"].get(k, 0.0) + ln["measured_net"])
        elif ln["evidence_state"] == "BLOCKED_RFI":
            if ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held line {ln['line_id']} carries a figure (held is BLANK)")
            out["blank"][k] = out["blank"].get(k, 0) + 1
    # the per-flight FIN.RAILING lines of the plan reader (UP-STAIR-012 per open side) describe the same stair guards
    # as the runs: while a run line carries a figure, a per-flight line with a figure would count the guard twice
    runs_valued = any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) and ln["item_code"] == RAIL_STAIR
                      and ln["evidence_state"] == "MEASURED" for ln in lines)
    flights = [ln for ln in lines if ln["item_code"] == RAIL_STAIR and not ((ln.get("calculation") or {}).get(
        "inputs") or {}).get(REC_KEY)]
    if runs_valued and any(ln.get("measured_net") is not None or ln.get("bounded_range") for ln in flights):
        raise ValueError(f"{METHOD}: a per-flight {RAIL_STAIR} line carries a figure beside the railing run lines "
                         f"(the same guard twice: retire the per-flight line first)")
    out["per_flight_railing_lines_blank"] = len(flights)
    out["faces"] = len(faces)
    out["valued"] = dict(sorted(out["valued"].items()))
    out["blank"] = dict(sorted(out["blank"].items()))
    return out


def integrate(l3029, changes, for_lead=()):
    """-> (V3.0.30 lines, identity). Every V3.0.29 line is byte-identical (this package only adds lines)."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3029}
    adds = []
    for c in changes:
        if c["piece"] not in (FW_PIECE, MW_PIECE) or c["action"] != "ADD":
            raise ValueError(f"{METHOD}: {c['piece']} {c['action']} (this version only adds formwork / metalwork)")
        a = c["after"]
        if a["line_id"] in sid or a["item_code"] not in ITEMS or a["unit"] not in ITEMS[a["item_code"]].split("|"):
            raise ValueError(f"{METHOD}: an added line repeats a V3.0.29 id or is not a formwork / metalwork line")
        adds.append(a)
    out = list(l3029) + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    tile = A3021.check_tile_family(out)
    par = A3023.check_parapet_family(out)
    state = A3024.check_line_state(out, for_lead)
    outdoor = A3025.check_outdoor_family(out)
    blk = A3026.check_blockwork(out)
    ends = A3027.check_slab_ends(out)
    rev = A3028.check_reveals(out)
    strips = A3029.check_strips(out)
    fwmw = check_formwork_metalwork(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by29 = {ln["line_id"]: ln for ln in l3029}
    outside = out[:len(l3029)]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by29[ln["line_id"]]) != A30.line_sha(ln)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.29 line(s) differ")
    ident = {"v3_0_29_lines": len(l3029), "v3_0_30_lines": len(out), "v3_0_30_rows": len(changes), "replaced": 0,
             "added": len(adds), "outside_rows": len(outside), "outside_rows_identical_to_v3_0_29": len(outside),
             "formwork_metalwork": fwmw, "sills_thresholds": strips, "opening_reveals": rev, "slab_bar_ends": ends,
             "blockwork": blk, "outdoor_family": outdoor, "parapet_family": par, "wall_tile_family": tile,
             "line_state": state,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


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
        piece = c["piece"]
        rows.append({"version": METHOD, "piece": piece, "action": "ADD", "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "concrete_line": rec.get("concrete_line"), "run": rec.get("run"),
                     "opening": rec.get("opening"), "status": rec.get("status"), "method": rec.get("method"),
                     "face_ids": rec.get("face_ids"), "bounds": rec.get("bounds"),
                     "alternatives": rec.get("alternatives"), "comparison_method_e_m2": rec.get(
                         "comparison_method_e_m2"), "before_released_v2_9": b29,
                     "before_v3_0_29": dict(A30._qty(None), state="NOT_IN_V3_0_29"), "after_v3_0_30": A30._qty(ref),
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED", "owner_manual_method": PIECES[piece]["owner_manual_method"],
                     "drawing_derived_method": PIECES[piece]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "line_id", "item_code", "floor", "element_id", "unit", "concrete_line", "run",
              "status", "method", "faces", "face_ids", "lo", "hi", "held_from", "formed_m2", "earth_cast_m2",
              "comparison_e_m2", "v2_9", "v3_0_29", "v3_0_30", "evidence_status", "held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_29", "vs_released_v2_9", "v2_9",
            "v3_0_29", "v3_0_30")


def _fmt_q(q):
    return A302._q(q) if q else ""


def ledger_csv(rows):
    def b(r, k):
        x = (r.get("bounds") or {}).get(k)
        return "" if x is None else _fmt(x)

    def al(r, k):
        x = ((r.get("alternatives") or {}).get(k) or {}).get("m2")
        return "" if x is None else _fmt(x)
    return A305._csv([{"version": r["version"], "piece": r["piece"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"] or "", "element_id": r["element_id"],
                       "unit": r["unit"], "concrete_line": r["concrete_line"] or "", "run": r["run"] or "",
                       "status": r["status"] or "", "method": r["method"] or "",
                       "faces": len(r["face_ids"] or ()), "face_ids": " ".join(r["face_ids"] or ())[:900],
                       "lo": b(r, "lo"), "hi": b(r, "hi"), "held_from": b(r, "held_from"),
                       "formed_m2": al(r, "OQ10_FORMED"), "earth_cast_m2": al(r, "OQ10_EARTH_CAST"),
                       "comparison_e_m2": _fmt(r["comparison_method_e_m2"]),
                       "v2_9": _fmt_q(r["before_released_v2_9"]), "v3_0_29": "NOT_IN_V3_0_29",
                       "v3_0_30": _fmt_q(r["after_v3_0_30"]), "evidence_status": r["evidence_status"],
                       "held": "; ".join(f"{h['what']}: {h['why']}" for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit', '')[:8]}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3029, l3030, released_lines=None):
    b29 = {ln["line_id"]: ln for ln in l3029}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3030:
        o = b29.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_29": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_29": A302._q(A30._qty(o)) if o else "", "v3_0_30": A302._q(A30._qty(ln))})
    return out


def write(out, l3029, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_30_* files beside the V3_0_29_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3030, ident = integrate(l3029, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3029, l3030, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_29", {}).setdefault(d["vs_v3_0_29"], 0)
        dsum["vs_v3_0_29"][d["vs_v3_0_29"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t29, t30 = A304.code_totals(l3029), A304.code_totals(l3030)
    moved = {k: {"v3_0_29": t29.get(k), "v3_0_30": t30.get(k)} for k in sorted(set(t29) | set(t30))
             if t29.get(k) != t30.get(k)}
    if any(k.split("|")[0] not in ITEMS for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the formwork / metalwork items: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "named_not_lines": (doc or {}).get("named_not_lines") or [], "waiting_pieces": WAITING,
           "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_30_BOQ_LINES.json": BL.dumps(l3030),
             "V3_0_30_BOQ_LINES.csv": A30._lines_csv(l3030),
             "V3_0_30_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_30_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_30_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_30_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(ITEMS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "fw_line", "alt_line",
           "na_line", "untied_line", "rail_line", "shutter_lines", "changes_for", "check_formwork_metalwork",
           "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
