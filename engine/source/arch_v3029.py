"""ARCH_TAKEOFF_V3.0.29 (T-327): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.28 (engine.source.arch_v30,
arch_v301 .. arch_v3028), extended with ONE piece, SILL_THRESHOLD_FILL: door thresholds and window sills booked as
their own item, opening by opening, from the Checker-merged sills / thresholds ledger (T-325) and its Checker-merged
binding to the candidate line ids (T-340: FILL table, closure traces). Not a new method family and not the released
default (owner management decision 2026-10-20 sections 2 and 5); rollback is running ARCH_TAKEOFF_V2.9.

The physical element (ERS 2026-10-22 s.2.1): ONE strip per doorway, the clear door width (the drawn jamb gap) x the
wall thickness, at floor level (UP-THR-001); its finish by the owner rule (a wet doorway: marble,
URBAN-WET-SERVICE-MARBLE-THRESHOLD v1; a dry doorway: the floor porcelain continued once; an external entrance: by
specification, HELD); and per raised window ONE external sill surface (frame to outer face), per floor-level window ONE
outside strip (the adjoining floor continued where a floor at the same level lies beyond, an external sill at floor
level over air). Area (m2), length along the opening (m.l) and count (pcs) are three measures of the one strip; the m2
is the line quantity, m.l and pcs are recorded beside it, never relabelled as one another.

  RETYPE    a BLOCKED threshold strip whose polygon is the door symbol's CLOSURE polygon (it runs past the jambs over
            the wall-end nib and across the cross wall): the closure line is retired (NOT_APPLICABLE_WITH_EVIDENCE,
            pointing at its successor) and the strip is booked ONCE in the finish line the owner rule names
            (FIN.MARBLE.THRESHOLD / FIN.FLOOR.PORCELAIN) at clear width x wall thickness. The closure polygon is
            superseded only when its excess over the strip is traced (nib + cross wall, residual <= 0.0001 m2);
            untraced, the line stays BLANK with the residual named (TRACE_HELD);
  FILL      (every villa) a blank ARCH.WINDOW_REVEAL line bound to ONE window's external sill / outside strip: that
            surface only (the frame bed is not a finish surface); an outside strip onto a floor is refused unless the
            floor line is shown to stop at the wall face (counted once, never as terrace AND sill);
  HOLD_ADD  an opening with no threshold line whose strip is not established: ONE BLANK line by name (never 0);
  CARRIED   (asserted, nothing moves) every strip another line already carries, with the figure the ledger states.

R-T327-1 (every villa): a threshold = drawn clear width x wall thickness, never the closure polygon; wet marble only on
a doorway the wet rule names (never on a dry door, never on an external entrance); a dry doorway's strip is the floor
porcelain continued once; an external entrance's material stays HELD (the strip area kept in its own line); a strip
whose polygon overlaps a room floor line by more than OVERLAP_TOL is refused (already counted in the floor); each
opening's strip once, one line one opening; HELD is BLANK, never 0.

Every line outside the records is byte-identical to V3.0.28 (asserted). Files: V3_0_29_BOQ_LINES.json / .csv,
V3_0_29_INTEGRATION_LEDGER.json / .csv, V3_0_29_DIFF.csv, V3_0_29_RUN.json. Nothing here names a project, a sheet, a
layer or a coordinate: every value comes from the inputs.
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.29"
EXTENDS = A3028.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T327_ARCH_V3_0_29"
INPUTS_SCHEMA = "URBAN_V3029_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3029_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3015.InputsError
_r = A3018._r
RULE_ID, RULE_VERSION = "R-T327-1", "T-327"
UNIT = "m2"
PIECE = "SILL_THRESHOLD_FILL"
REC_KEY = "sill_threshold_v3029"
THRESHOLD_CODE, MARBLE_CODE, PORCELAIN_CODE, SILL_CODE = (
    "ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN", "ARCH.WINDOW_REVEAL")
ITEMS = (THRESHOLD_CODE, MARBLE_CODE, PORCELAIN_CODE, SILL_CODE)
# doorway class -> (finish line, material, physical element of that family's strip lines)
RETYPE_TARGET = {"WET": (MARBLE_CODE, "MARBLE", "marble threshold"),
                 "DRY": (PORCELAIN_CODE, "FLOOR PORCELAIN", "doorway strip")}
WET_RULE = "URBAN-WET-SERVICE-MARBLE-THRESHOLD"
DOOR_KINDS = ("DOOR",)
SILL_COMPONENTS = ("SILL_OUT", "THRESHOLD_OUT")
OUTSIDE = ("AIR", "FLOOR")
HELD_STATES = ("HELD", "UNRESOLVED", "UNKNOWN")
TOL = 1e-6
RES_TOL = 1e-4          # a traced closure residual (polygon vertex rounding) is at most 0.0001 m2
OVERLAP_TOL = 1e-3      # a strip overlapping a room floor polygon by more than 0.001 m2 is already in the floor

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3029.py (sills and thresholds as their own item: BLOCKED closure strips "
                  "retyped to the finish line the owner rule names at clear width x wall thickness, window sills "
                  "filled once, unestablished strips BLANK by name; m2 / m.l / pcs three measures)",
        "policy": "SILL_THRESHOLD_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["UP-THR-001 (a threshold strip = clear door width x wall thickness; dry doorway: floor "
                        "porcelain continued once)", "URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 (every wet doorway: "
                        "marble; external entrances not applicable)", "UP-REVEAL-001 (the sill surface its own item)",
                        "Q-37 A", "OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (outdoor floor finishes)",
                        "UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 "
                        "s.2 - s.4"],
        "owner_manual_method": "owner method (UP-THR-001): threshold = clear width x wall thickness per doorway, "
                               "marble in every wet doorway, porcelain continued in a dry one, external entrance by "
                               "specification; window sill (UP-REVEAL-001) its own item, material by specification",
        "drawing_method": "per opening: clear width = the drawn jamb gap (wall-face line ends, door symbol frame; "
                          "T-237 / T-340), wall thickness T-150; the closure polygon reconciled to the strip by its "
                          "wall-end nib and cross-wall terms (T-340 CLOSURE_TRACE); wet / dry from the T-237 room "
                          "names (T-325); strip vs room floor overlap from ARCH_FLOOR_AREAS (T-325)"},
}
WAITING = dict(A3028.WAITING)
WAITING.pop("THRESHOLD_RETYPE", None)
WAITING.update({
    "SILL_MATERIAL": "the external window sill material (23 sills + 2 floor-level strips over air): no specification "
                     "printed, no owner rule (consultant item A13): area kept, material UNKNOWN",
    "EXTERNAL_THRESHOLD_MATERIAL": "the six external-entrance thresholds: area kept in their bounded lines, material "
                                   "by specification (HELD)",
    "ARCHED_SET_THRESHOLDS": "A-GF-01 threshold strip (arch outline HELD, D-45; T-377 held set) and W17 sills (curved, "
                             "T-302) stay BLANK by name; W03 floor glazing strips are carried by the V3.0.28 held "
                             "reveal lines",
    "DOWNGRADE_DGP_T373_LAP": "the Checker-issued note-9 lap downgrade record (verdicts/V3.0.28/DOWNGRADES.json) was "
                              "not issued when T-327 was built: not applied here",
})


# ================================================================================================ inputs
def _src(s):
    for k in ("task", "file", "sha256", "merge_commit", "checker_run"):
        if not s.get(k):
            raise InputsError(f"source {s}: {k} missing (a merged, checker-verified ledger only)")


def _pos(x, where, what="m2"):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x <= TOL:
        raise InputsError(f"{where}: {what} {x!r} (a valued strip is > 0; held is BLANK, never 0)")
    return float(x)


def _strip(rec, where):
    """width x depth = m2, m.l = width, pcs = 1: three measures of one strip, never relabelled."""
    w, d = _pos(rec.get("width_m"), where, "width_m"), _pos(rec.get("depth_m"), where, "depth_m")
    m2 = _pos(rec.get("m2"), where)
    if abs(w * d - m2) > TOL:
        raise InputsError(f"{where}: {m2} m2 is not width {w} x depth {d} = {_r(w * d)} (clear width x wall "
                          f"thickness, R-T327-1)")
    if rec.get("ml") is None or abs(float(rec["ml"]) - w) > TOL:
        raise InputsError(f"{where}: m.l {rec.get('ml')!r} is not the strip's length along the opening {w} (m2, m.l "
                          f"and pcs are three measures, never one relabelled)")
    if rec.get("pcs") != 1 or isinstance(rec.get("pcs"), bool):
        raise InputsError(f"{where}: pcs {rec.get('pcs')!r} (one strip per opening)")
    if d > 0.6:
        raise InputsError(f"{where}: depth {d} m is not a wall / reveal thickness (a units error?)")
    return w, d, m2


def _overlap(rec, where):
    ov = rec.get("floor_overlap_m2")
    if not isinstance(ov, (int, float)) or ov < 0:
        raise InputsError(f"{where}: the strip's overlap with the room floor polygons is required (R-T327-1)")
    if ov > OVERLAP_TOL:
        raise InputsError(f"{where}: the strip overlaps a room floor line by {ov} m2 (> {OVERLAP_TOL}): it is "
                          f"already counted in the floor tile line, refused")
    return float(ov)


def _trace(rec, w, d, where):
    """the closure polygon reconciled to the strip: polygon - strip = (nib + cross wall) x depth (+ named terms),
    residual <= RES_TOL. -> 'TRACED' | 'UNTRACED'."""
    poly = rec.get("closure_polygon_m2")
    if poly is None:
        return "NO_POLYGON"
    poly = _pos(poly, where, "closure_polygon_m2")
    t = rec.get("trace") or {}
    excess = t.get("polygon_minus_clear_m2")
    if abs(poly - float(rec["m2"])) <= TOL and isinstance(excess, (int, float)) and excess > RES_TOL:
        raise InputsError(f"{where}: the closure polygon {poly} m2 offered as the threshold (superseded figure; the "
                          f"strip is clear width x wall thickness)")
    res = t.get("residual_m2")
    if not t.get("cause") or not isinstance(excess, (int, float)) or not isinstance(res, (int, float)):
        return "UNTRACED"
    if abs((poly - w * d) - excess) > RES_TOL:
        raise InputsError(f"{where}: polygon {poly} - strip {_r(w * d)} != the traced excess {excess}")
    return "TRACED" if abs(res) <= RES_TOL else "UNTRACED"


def load_inputs(doc, project_id=None):
    """URBAN_V3029_INPUTS_V1 -> the validated doc."""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    if doc.get("unit") != UNIT:
        raise InputsError(f"inputs unit {doc.get('unit')!r}: strips are booked in m2 (m.l and pcs beside)")
    srcs = {}
    for s in doc.get("sources") or ():
        _src(s)
        srcs.setdefault(s["task"], s)
    owner, lines_seen = {}, {}

    def book(op, comp, who, line_id=None):
        k = (op, comp)
        if k in owner:
            raise InputsError(f"{op} {comp}: already carried by {owner[k]} (one strip, one line)")
        owner[k] = who
        if line_id is not None:
            if line_id in lines_seen and lines_seen[line_id] != op:
                raise InputsError(f"line {line_id}: carries {lines_seen[line_id]} and {op} (one line, one opening)")
            lines_seen[line_id] = op

    def need_src(r, where):
        if r.get("source_task") not in srcs:
            raise InputsError(f"{where}: no merged source for {r.get('source_task')!r}")

    carried = []
    for c in doc.get("carried") or ():
        where = f"carried {c.get('opening')} {c.get('line_id')}"
        need_src(c, where)
        if c.get("item_code") not in ITEMS:
            raise InputsError(f"{where}: item {c.get('item_code')!r}")
        if c.get("m2") is not None:
            _pos(c["m2"], where)
        book(c["opening"], c["component"], f"{c['item_code']} {c['line_id']}", c["line_id"])
        carried.append(c)
    retype = []
    for r in doc.get("retype") or ():
        where = f"retype {r.get('opening')} {r.get('line_id')}"
        need_src(r, where)
        if r.get("kind") not in DOOR_KINDS:
            raise InputsError(f"{where}: kind {r.get('kind')!r}: a closure strip is a doorway's")
        if r.get("external"):
            raise InputsError(f"{where}: an external entrance's sill is by specification (HELD): never retyped to a "
                              f"finish line")
        cls = r.get("doorway")
        if cls not in RETYPE_TARGET:
            raise InputsError(f"{where}: doorway class {cls!r} (WET or DRY)")
        tgt, mat, _phys = RETYPE_TARGET[cls]
        if r.get("target_item") != tgt or r.get("material") != mat:
            raise InputsError(f"{where}: a {cls} doorway is {tgt} / {mat}, not {r.get('target_item')} / "
                              f"{r.get('material')} (wet marble only where the wet rule names the doorway)")
        if cls == "WET" and WET_RULE not in str(r.get("material_source") or ""):
            raise InputsError(f"{where}: marble needs the wet-doorway rule {WET_RULE} as its source")
        if cls == "DRY" and "UP-THR-001" not in str(r.get("material_source") or ""):
            raise InputsError(f"{where}: the dry strip's porcelain is UP-THR-001 (floor continued once)")
        w, d, m2 = _strip(r, where)
        _overlap(r, where)
        tr = _trace(r, w, d, where)
        book(r["opening"], "THRESHOLD", f"retype {r['line_id']}", r["line_id"])
        retype.append(dict(r, m2=m2, width_m=w, depth_m=d, trace_state=tr))
    sills = []
    for s in doc.get("sills") or ():
        where = f"sill {s.get('opening')} {s.get('line_id')}"
        need_src(s, where)
        if s.get("component") not in SILL_COMPONENTS:
            raise InputsError(f"{where}: component {s.get('component')!r} (a window strip line takes the external "
                              f"sill / outside strip only)")
        if s.get("outside") not in OUTSIDE:
            raise InputsError(f"{where}: outside {s.get('outside')!r}: not established -> HELD, never filled")
        if s["outside"] == "FLOOR" and s.get("outdoor_line_excludes_strip") is not True:
            raise InputsError(f"{where}: the outside strip onto a floor must be shown outside that floor's line "
                              f"(else it is counted as both terrace and sill)")
        if s.get("material") not in ("UNKNOWN",) and not s.get("material_source"):
            raise InputsError(f"{where}: a sill material only from a print or an owner rule (else UNKNOWN)")
        if str(s.get("material") or "").upper() == "MARBLE" and WET_RULE in str(s.get("material_source") or ""):
            raise InputsError(f"{where}: the wet-doorway marble rule does not set a window sill")
        w, d, m2 = _strip(s, where)
        book(s["opening"], s["component"], f"sill {s['line_id']}", s["line_id"])
        sills.append(dict(s, m2=m2, width_m=w, depth_m=d))
    held = []
    for h in doc.get("held") or ():
        where = f"held {h.get('opening')}"
        need_src(h, where)
        if h.get("item_code") not in (THRESHOLD_CODE, SILL_CODE):
            raise InputsError(f"{where}: item {h.get('item_code')!r}")
        if h.get("state") not in HELD_STATES:
            raise InputsError(f"{where}: state {h.get('state')!r}")
        if any(h.get(k) not in (None, "") for k in ("m2", "ml", "pcs")):
            raise InputsError(f"{where}: a held strip given a figure (held is BLANK, never 0)")
        if not h.get("basis"):
            raise InputsError(f"{where}: the held strip names why")
        book(h["opening"], h.get("component") or "THRESHOLD", f"held {h['item_code']}")
        held.append(h)
    return dict(doc, carried=carried, retype=retype, sills=sills, held=held, _sources=srcs, _owner=owner)


# ================================================================================================ lines
def _rec(src, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(src):
    return {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
            "ledger": src["file"], "ledger_sha256": src["sha256"]}


def _fmt(x):
    return f"{_r(x, 6):.6f}".rstrip("0").rstrip(".") if x is not None else ""


def _live(ln):
    return ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL", "BOUNDED_EXPOSURE")


def _figure(ln):
    if ln["evidence_state"] == "BOUNDED_EXPOSURE":
        br = ln.get("bounded_range") or {}
        return (br.get("low"), br.get("high"))
    return (ln.get("measured_net"), ln.get("measured_net"))


def element_id(floor, opening, phys, held=False):
    return f"{floor}-THRESHOLD-{opening}:{phys}" + (":HELD" if held else "")


def _template(lines, code, floor):
    cand = [ln for ln in lines if ln["item_code"] == code and ln["unit"] == UNIT]
    same = [ln for ln in cand if (ln.get("location") or {}).get("floor") == floor]
    pick = same or cand
    if not pick:
        raise InputsError(f"no {code} line in the candidate to take the plan documents from")
    return sorted(pick, key=lambda x: x["line_id"])[0]


def _assert_closure(b, r):
    if b is None:
        raise InputsError(f"line {r['line_id']}: the candidate does not carry this line (stale ledger)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"line {r['line_id']}: already retyped (applied once)")
    if (b["item_code"], b["unit"]) != (THRESHOLD_CODE, UNIT) or b["evidence_state"] != "BLOCKED_RFI" or \
            b.get("measured_net") is not None or b.get("bounded_range"):
        raise InputsError(f"line {r['line_id']}: {b['item_code']} {b['evidence_state']} is not a blank threshold "
                          f"strip (stale ledger)")
    if (b.get("location") or {}).get("floor") != r["floor"]:
        raise InputsError(f"line {r['line_id']}: floor {(b.get('location') or {}).get('floor')} != {r['floor']}")


def _strip_rec(r):
    return {"component": "THRESHOLD", "m2": _r(r["m2"]), "ml": _r(r["width_m"]), "pcs": 1,
            "width_m": r["width_m"], "depth_m": r["depth_m"]}


def retire_line(b, r, new_id, src):
    ln = copy.deepcopy(b)
    tr = r.get("trace") or {}
    ln["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
    ln["rfi"] = None
    ln["calculation"]["formula"] = (
        f"{r['opening']} threshold RETYPED: booked once in {r['target_item']} {new_id} at clear width x wall "
        f"thickness {_fmt(r['width_m'])} x {_fmt(r['depth_m'])} (that line carries the figure); this line's closure "
        f"polygon ({_fmt(r.get('closure_polygon_m2'))} in m2) is superseded, no figure here "
        f"({tr.get('cause') or 'traced'})")[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, **{REC_KEY: _rec(
        src, action="RETIRE", before=A3018._before_rec(b), opening=r["opening"], successor=new_id,
        superseded_polygon_m2=r.get("closure_polygon_m2"), trace=tr, faces=[],
        evidence_status="DRAWING-CONFIRMED (superseded by its successor line)")})
    A305._note(ln, f"{METHOD}: retyped to {r['target_item']} {new_id} ({src['task']} MERGED {src['merge_commit'][:8]}); "
                   f"the closure polygon is not the threshold (R-T327-1)")
    return _validate(ln)


def _validate(ln):
    from engine.source import boq_line as BL
    return BL.validate(ln)


def retyped_line(b, r, src, tmpl):
    from engine.source import boq_line as BL
    tgt, mat, phys = RETYPE_TARGET[r["doorway"]]
    pr = tmpl["project"]
    eid = element_id(r["floor"], r["opening"], phys)
    tr = r.get("trace") or {}
    formula = (f"{r['opening']} {r['doorway'].lower()} doorway threshold: clear width {_fmt(r['width_m'])} x wall "
               f"thickness {_fmt(r['depth_m'])} = {_fmt(r['m2'])} m2 ({_fmt(r['width_m'])} m.l, 1 pc); {mat} "
               f"({r['material_source']}); replaces the closure polygon {_fmt(r.get('closure_polygon_m2'))} m2 of "
               f"{b['line_id']} ({tr.get('cause') or ''})")
    lrec = _rec(src, action="RETYPE", opening=r["opening"], kind=r["kind"], doorway=r["doorway"], from_line=b["line_id"],
                faces=[_strip_rec(r)], material=mat, material_source=r["material_source"],
                floor_overlap_m2=r.get("floor_overlap_m2"), superseded_polygon_m2=r.get("closure_polygon_m2"),
                trace=tr, evidence_status="DRAWING-CONFIRMED", correction_note=r.get("note"))
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"], item_code=tgt,
                      unit=UNIT, evidence_state="MEASURED", measured_net=_r(r["m2"]), element_id=eid,
                      floor=r["floor"], room_id=(b.get("location") or {}).get("room_id"),
                      physical_element=phys, formula=formula[:700], inputs={REC_KEY: lrec},
                      documents=copy.deepcopy(b["source"]["documents"]),
                      geometry_source=b["source"]["geometry_source"],
                      geometry_confidence=b["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="URBAN_METHOD",
                      notes=(f"{METHOD}: threshold of {r['opening']} as its own item ({src['task']} MERGED "
                             f"{src['merge_commit'][:8]}); m2 / m.l / pcs = {_fmt(r['m2'])} / {_fmt(r['width_m'])} / "
                             f"1")[:600])
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln), lrec


def hold_trace_line(b, r, src):
    """an untraced closure residual: the line stays BLANK, the residual named (never the polygon, never 0)."""
    ln = copy.deepcopy(b)
    q = (f"{r['opening']} threshold HELD: the closure polygon {_fmt(r.get('closure_polygon_m2'))} m2 exceeds clear "
         f"width x wall thickness {_fmt(r['m2'])} m2 by {_fmt(r['closure_polygon_m2'] - r['m2'])} m2 and the excess is "
         f"not traced to the wall-end nib / cross wall (residual named; blank, never 0)")
    ln["rfi"] = {"question": q[:900], "unlocks": (b.get("location") or {}).get("element_id")}
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, **{REC_KEY: _rec(
        src, action="TRACE_HELD", before=A3018._before_rec(b), opening=r["opening"], faces=[],
        superseded_polygon_m2=None, residual_m2=_r(r["closure_polygon_m2"] - r["m2"]), evidence_status="HELD")})
    A305._note(ln, f"{METHOD}: closure residual untraced: HELD by name")
    return _validate(ln)


def fill_sill(b, s, src):
    ln = copy.deepcopy(b)
    ln["evidence_state"] = "MEASURED"
    ln["measured_net"] = _r(s["m2"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["calculation"]["formula"] = (
        f"{s['opening']} {'outside strip' if s['component'] == 'THRESHOLD_OUT' else 'external sill'} only: "
        f"{_fmt(s['width_m'])} x {_fmt(s['depth_m'])} = {_fmt(s['m2'])} m2 ({_fmt(s['width_m'])} m.l, 1 pc); outside "
        f"{s['outside'].lower()}; material {s['material']}")[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, **{REC_KEY: _rec(
        src, action="FILL", before=A3018._before_rec(b), opening=s["opening"],
        faces=[{"component": s["component"], "m2": _r(s["m2"]), "ml": _r(s["width_m"]), "pcs": 1,
                "width_m": s["width_m"], "depth_m": s["depth_m"]}], outside=s["outside"],
        material=s["material"], material_source=s.get("material_source"), evidence_status="DRAWING-CONFIRMED")})
    A305._note(ln, f"{METHOD}: window strip filled ({src['task']} MERGED {src['merge_commit'][:8]}); material "
                   f"{s['material']}")
    return _validate(ln)


def held_line(h, src, tmpl):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    phys = "threshold strip" if h["item_code"] == THRESHOLD_CODE else "window reveal strip"
    eid = element_id(h["floor"], h["opening"], phys, held=True)
    q = (f"HELD (blank in the BOQ, never 0): {h['opening']} {phys} {h['state']}: {h['basis']}")
    lrec = _rec(src, action="HOLD_ADD", opening=h["opening"], faces=[], state=h["state"], basis=h["basis"],
                material=h.get("material"), evidence_status="HELD")
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=h["item_code"], unit=UNIT, evidence_state="BLOCKED_RFI", measured_net=None,
                      element_id=eid, floor=h["floor"], physical_element=phys, formula=q[:700],
                      inputs={REC_KEY: lrec}, documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source=tmpl["source"]["geometry_source"],
                      geometry_confidence=tmpl["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="BY_SPEC",
                      rfi={"question": q[:900], "unlocks": eid},
                      notes=f"{METHOD}: strip HELD by name ({src['task']} MERGED {src['merge_commit'][:8]})")
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln), lrec


def _assert_carried(by, c):
    b = by.get(c["line_id"])
    if b is None:
        raise InputsError(f"carried {c['opening']}: line {c['line_id']} is not in the candidate (stale ledger)")
    if b["item_code"] != c["item_code"]:
        raise InputsError(f"carried {c['opening']}: line {c['line_id']} is {b['item_code']}, not {c['item_code']}")
    lo, hi = _figure(b)
    if c.get("m2") is None:
        if _live(b):
            raise InputsError(f"carried {c['opening']}: held strip but {c['line_id']} carries a figure "
                              f"{b['evidence_state']} {lo} .. {hi}")
        return
    if not _live(b) or lo is None or abs(lo - c["m2"]) > TOL or abs(hi - c["m2"]) > TOL:
        raise InputsError(f"carried {c['opening']}: line {c['line_id']} {b['evidence_state']} {lo} .. {hi} is not the "
                          f"ledger's {c['m2']} m2 (line differs from the verified ledger)")


def changes_for(doc, l3028):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3028}
    for c in doc["carried"]:
        _assert_carried(by, c)
    seen = set(by)
    changes = []
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "m2": {}, "ml": {}, "pcs": {},
           "lines": {}, "carried_checked": len(doc["carried"])}

    def tally(k, m2=None, ml=None, pcs=None):
        log["by_action"][k] = log["by_action"].get(k, 0) + 1
        for key, v in (("m2", m2), ("ml", ml), ("pcs", pcs)):
            if v is not None:
                log[key][k] = _r(log[key].get(k, 0) + v)

    for r in doc["retype"]:
        b = by.get(r["line_id"])
        _assert_closure(b, r)
        src = doc["_sources"][r["source_task"]]
        if r["trace_state"] == "UNTRACED":
            after = hold_trace_line(b, r, src)
            changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference=src["file"],
                                        held=[{"what": f"{THRESHOLD_CODE} {r['opening']}", "why": after["rfi"]
                                               ["question"][:300], "range": None, "scenario": None}], downstream=[],
                                        verification=_ver(src), evidence_status="HELD",
                                        codes=[PIECE, "TRACE_HELD"], group=THRESHOLD_CODE))
            tally("TRACE_HELD")
            log["lines"][b["line_id"]] = {"action": "TRACE_HELD", "opening": r["opening"]}
            continue
        new, _lrec = retyped_line(b, r, src, b)
        if new["line_id"] in seen:
            raise ValueError(f"{METHOD}: the retyped line of {r['opening']} repeats a line id")
        seen.add(new["line_id"])
        old = retire_line(b, r, new["line_id"], src)
        changes.append(A305._change(PIECE, "REPLACE", b, old, drawing_reference=src["file"], held=[], downstream=[
            new["line_id"]], verification=_ver(src), evidence_status="DRAWING-CONFIRMED (retired, successor named)",
            codes=[PIECE, "RETIRE"], group=THRESHOLD_CODE))
        changes.append(A305._change(PIECE, "ADD", None, new, drawing_reference=src["file"], held=[], downstream=[],
                                    verification=_ver(src), evidence_status="DRAWING-CONFIRMED",
                                    codes=[PIECE, "RETYPE", r["doorway"]], group=new["item_code"]))
        tally(f"RETYPE {new['item_code']}", r["m2"], r["width_m"], 1)
        log["lines"][b["line_id"]] = {"action": "RETIRE", "opening": r["opening"], "successor": new["line_id"]}
        log["lines"][new["line_id"]] = {"action": "RETYPE", "opening": r["opening"], "item_code": new["item_code"]}
    for s in doc["sills"]:
        b = by.get(s["line_id"])
        A3028._assert_fill(b, s)
        if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
            raise InputsError(f"line {s['line_id']}: already filled (applied once)")
        src = doc["_sources"][s["source_task"]]
        after = fill_sill(b, s, src)
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference=src["file"], held=[], downstream=[],
                                    verification=_ver(src), evidence_status="DRAWING-CONFIRMED",
                                    codes=[PIECE, "FILL"], group=SILL_CODE))
        tally("FILL", s["m2"], s["width_m"], 1)
        log["lines"][b["line_id"]] = {"action": "FILL", "opening": s["opening"]}
    for h in doc["held"]:
        src = doc["_sources"][h["source_task"]]
        tmpl = _template(l3028, h["item_code"], h["floor"])
        ln, _lrec = held_line(h, src, tmpl)
        if ln["line_id"] in seen:
            raise ValueError(f"{METHOD}: the held line of {h['opening']} repeats a line id")
        seen.add(ln["line_id"])
        changes.append(A305._change(PIECE, "ADD", None, ln, drawing_reference=src["file"],
                                    held=[{"what": f"{h['item_code']} {h['opening']}", "why": f"{h['state']}: "
                                           f"{h['basis']}"[:300], "range": None, "scenario": None}],
                                    downstream=[], verification=_ver(src), evidence_status="HELD",
                                    codes=[PIECE, "HOLD_ADD"], group=h["item_code"]))
        tally(f"HOLD_ADD {h['item_code']}")
        log["lines"][ln["line_id"]] = {"action": "HOLD_ADD", "opening": h["opening"]}
    return changes, log


# ================================================================================================ integrate / write
def check_strips(lines):
    """on finished lines: each opening's strip booked by ONE live V3.0.29 record; a retired line names a live
    successor; valued lines equal their strip, held lines carry no figure. -> summary."""
    out = {"retyped": 0, "retired": 0, "filled": 0, "held_added": 0, "trace_held": 0, "m2": {}, "ml": {}, "pcs": {}}
    by = {ln["line_id"]: ln for ln in lines}
    ops = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        act = rec.get("action")
        if act == "RETIRE":
            out["retired"] += 1
            nxt = by.get(rec.get("successor"))
            if ln["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or ln.get("measured_net") is not None or \
                    nxt is None or not _live(nxt):
                raise ValueError(f"{METHOD}: retired line {ln['line_id']} has no live successor or still a figure")
            continue
        if act in ("HOLD_ADD", "TRACE_HELD"):
            out["held_added" if act == "HOLD_ADD" else "trace_held"] += 1
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held strip line {ln['line_id']} carries a figure (held is BLANK)")
        else:
            net = ln.get("measured_net")
            f = (rec.get("faces") or [{}])[0]
            if len(rec.get("faces") or ()) != 1 or not isinstance(net, (int, float)) or net <= TOL or \
                    abs(float(f.get("m2")) - net) > TOL or abs(f["width_m"] * f["depth_m"] - net) > TOL:
                raise ValueError(f"{METHOD}: strip line {ln['line_id']} {net} is not its one strip")
            out["retyped" if act == "RETYPE" else "filled"] += 1
            k = ln["item_code"]
            out["m2"][k] = _r(out["m2"].get(k, 0.0) + net)
            out["ml"][k] = _r(out["ml"].get(k, 0.0) + f["ml"])
            out["pcs"][k] = out["pcs"].get(k, 0) + f["pcs"]
        o = rec.get("opening")
        if o in ops:
            raise ValueError(f"{METHOD}: {o} strip booked by {ops[o]} and {ln['line_id']} (double count)")
        ops[o] = ln["line_id"]
    for k in ("m2", "ml", "pcs"):
        out[k] = dict(sorted(out[k].items()))
    out["openings"] = len(ops)
    return out


def integrate(l3028, changes, for_lead=()):
    """-> (V3.0.29 lines, identity). Every line outside the V3.0.29 rows is byte-identical to the V3.0.28 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3028}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != PIECE:
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only books sills and thresholds)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.28, or its id changed")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            a = c["after"]
            if a["line_id"] in sid or a["item_code"] not in ITEMS or a["unit"] != UNIT:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.28 line id or is not a strip m2 line")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3028] + adds
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
    strips = check_strips(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by28 = {ln["line_id"]: ln for ln in l3028}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by28[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3028):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.29 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by28[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_28_lines": len(l3028), "v3_0_29_lines": len(out), "v3_0_29_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_28": len(outside), "sills_thresholds": strips, "opening_reveals": rev,
             "slab_bar_ends": ends, "blockwork": blk, "outdoor_family": outdoor, "parapet_family": par,
             "wall_tile_family": tile, "line_state": state,
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
        rows.append({"version": METHOD, "action": rec["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "opening": rec.get("opening"), "faces": rec.get("faces"),
                     "material": rec.get("material"), "before_released_v2_9": b29,
                     "before_v3_0_28": (A30._qty(c["before"]) if c["before"] is not None else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_28")),
                     "after_v3_0_29": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "opening", "m2", "ml", "pcs", "material", "unit",
              "v2_9", "v3_0_28", "v3_0_29", "evidence_status", "held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_28", "vs_released_v2_9", "v2_9",
            "v3_0_28", "v3_0_29")


def _fmt_q(q):
    return A302._q(q) if q else ""


def ledger_csv(rows):
    def f0(r, k):
        fs = r["faces"] or ()
        return "" if len(fs) != 1 or fs[0].get(k) is None else str(fs[0][k])
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "opening": r["opening"],
                       "m2": f0(r, "m2"), "ml": f0(r, "ml"), "pcs": f0(r, "pcs"), "material": r["material"] or "",
                       "unit": r["unit"], "v2_9": _fmt_q(r["before_released_v2_9"]),
                       "v3_0_28": _fmt_q(r["before_v3_0_28"]), "v3_0_29": _fmt_q(r["after_v3_0_29"]),
                       "evidence_status": r["evidence_status"],
                       "held": "; ".join(f"{h['what']}: {h['why']}" for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''}"
                                       .strip()} for r in rows], LEDGER_CSV)


def diff_rows(l3028, l3029, released_lines=None):
    b28 = {ln["line_id"]: ln for ln in l3028}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3029:
        o = b28.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_28": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_28": A302._q(A30._qty(o)) if o else "", "v3_0_29": A302._q(A30._qty(ln))})
    return out


def write(out, l3028, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_29_* files beside the V3_0_28_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3029, ident = integrate(l3028, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3028, l3029, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_28", {}).setdefault(d["vs_v3_0_28"], 0)
        dsum["vs_v3_0_28"][d["vs_v3_0_28"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t28, t29 = A304.code_totals(l3028), A304.code_totals(l3029)
    moved = {k: {"v3_0_28": t28.get(k), "v3_0_29": t29.get(k)} for k in sorted(set(t28) | set(t29))
             if t28.get(k) != t29.get(k)}
    if any(k.split("|")[0] not in ITEMS or not k.endswith(f"|{UNIT}") for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the sill / threshold items: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_29_BOQ_LINES.json": BL.dumps(l3029),
             "V3_0_29_BOQ_LINES.csv": A30._lines_csv(l3029),
             "V3_0_29_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_29_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_29_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_29_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(ITEMS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "retire_line",
           "retyped_line", "fill_sill", "held_line", "element_id", "changes_for", "check_strips", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError"]
