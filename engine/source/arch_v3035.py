"""ARCH_TAKEOFF_V3.0.35 (T-400): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.34 (engine.source.arch_v30,
arch_v301 .. arch_v3034), extended with the BOQ category the candidate lacked (registry family B13-04 'fencing / gates'):

  BOUNDARY_FENCE  the plot boundary wall as a composite element, component by component and run by run, from the
                  Checker-merged ledgers of T-396 (masonry above N.G.: runs, printed height, wall plane), T-403 (below
                  N.G.: upper / lower ground beam, pads, masonry between the beams), T-404 (finish faces per side, the
                  top, the gate stop-end) and T-361 (gates):

    FENCE_VALUE   a NEW line whose geometry a merged verdict re-measured (DRAWING-CONFIRMED): the wall plane of a run
                  (run length x the printed height above N.G.), a physical finish face (side length x height, less
                  the gates on that face), the wall top (m.l). The figure is recomputed from its terms here and must
                  equal the ledger (else stop). The plane is the carrier geometry; the block net, block type / count
                  and every finish LAYER stay HELD beside it (Q-65 C; p.12 prints no finish);
    FENCE_HELD    a NEW line, BLANK (never 0), for every component the drawings do not settle: the sea element (Q-63 C)
                  and the passage closure, the block net per run (boundary columns 'SEE ARCH PLAN', none drawn: M4;
                  the lower 0.50 band material), the block type / count (Q-65 C), the masonry below N.G. (formation
                  printed only as a minimum: AT_LEAST beside), the boundary pads (count not printed), every plaster /
                  paint layer (HELD at most its face), the street faces / top / G-01 stop-end (undimensioned top
                  profile), the street gate G-01 leaf (no leaf drawn). The figure that bounds it (at most / at least /
                  comparison only / per unit) is carried beside, never as the line figure;
    HELD_BOUND    the existing HELD upper boundary ground-beam line: its held range restated to 0 .. the drawn gross
                  of the beam (44.07 x 0.20 x 0.40, T-403; the column joints are not printed): a range, never a value;
    BIND          (asserted, nothing moves) an element another line already carries, bound by line id and checked as
                  the merged ledger read it: the lower boundary band (its fence share 3.3976 .. 5.2884 m3 lies inside
                  the one band line, which carries a Checker line-content downgrade: never a second line), the street
                  fence railing RL-10 (the dip infill) and the sea gate G-02 = door D-GF-15 (counted once);
    RECORD        (no line) a component named and placed: the coping (NOT_DRAWN), the far G-01 jamb (the house wall:
                  house facade ledger), the G.B coating below N.G. (owned by T-263).

The physical element (ERS 2026-10-22 s.2.1): a boundary wall is lower G.B on pads and blinding, masonry below N.G.
between the two beams, upper G.B with its top at N.G., boundary columns, masonry above N.G. (the fence), gate openings,
infill and finishes per face; each component one line (or one named record) with ONE owner trade, never two. Above
N.G. vs below N.G. is split at the upper G.B top (0.000 m2 shared); a boundary face is not a house facade face (0.000
m2 shared, asserted from the merged face table and against every candidate line).

Every value comes from the inputs (Checker-merged ledgers pinned by sha256); this module types none. Every line outside
the rows is byte-identical to V3.0.34; inside the HELD_BOUND row only state, range, rfi, calculation and notes change
(asserted). Totals may move only in the codes this piece writes and the one restated code (asserted). Files:
V3_0_35_BOQ_LINES.json / .csv, V3_0_35_INTEGRATION_LEDGER.json / .csv, V3_0_35_DIFF.csv, V3_0_35_RUN.json. Nothing here
names a project, a sheet, a layer or a coordinate.

R-T400-1 (every villa): a boundary wall enters the candidate component by component, each bound to one new line, one
existing line (by id, checked as the verified ledger read it) or one named record; a valued component line carries
only geometry a merged verdict re-measured and its figure is the product of its printed / drawn terms; a held material
holds the type, count and layers, never the geometry; an at-most / at-least / per-unit figure stands beside a blank
line, never in it; an element already inside an existing line (above all one carrying a Checker line-content
downgrade) is bound, never booked again; a gate is counted once across the opening census and the fence family.
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
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.35"
EXTENDS = A3034.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T400_ARCH_V3_0_35"
INPUTS_SCHEMA = "URBAN_V3035_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3035_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T400-1", "T-400"
PIECE = "BOUNDARY_FENCE"
FAMILY = "B13-04"
REC_KEY = "boundary_fence_v3035"
ACTIONS = ("FENCE_VALUE", "FENCE_HELD", "HELD_BOUND", "BIND", "RECORD")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
HELD_STATES = ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
TOL = 1e-6
ROW_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "calculation", "gross")
BESIDE_KINDS = ("AT_MOST", "AT_LEAST", "COMPARISON_ONLY", "PER_UNIT", "OPENING_WIDTH")

WALL = "EXT.FENCE.WALL"
BLOCK = "EXT.FENCE.BLOCK"
BLOCK_COUNT = "EXT.FENCE.BLOCK_COUNT"
BELOW_NG = "EXT.FENCE.MASONRY_BELOW_NG"
FACE = "EXT.FENCE.FACE"
TOP = "EXT.FENCE.TOP"
PLASTER = "EXT.FENCE.PLASTER"
PAINT = "EXT.FENCE.PAINT"
GATE = "EXT.FENCE.GATE"
PAD = "STR.CONC.BOUNDARY_PAD"
NEW_ITEMS = {   # item master entries for the codes boq_line.ITEMS does not carry (en, ar, trade, subtrade, unit)
    WALL: ("Boundary fence wall plane above N.G. (run length x printed height; carrier geometry)",
           "مسطح جدار السور فوق منسوب الأرض الطبيعية", "EXTERNAL_WORKS", "BOUNDARY_WORKS", "m2"),
    BLOCK: ("Boundary fence blockwork net above N.G. (plane less boundary columns / plinth)", "بلوك السور صافي",
            "EXTERNAL_WORKS", "BOUNDARY_WORKS", "m2"),
    BLOCK_COUNT: ("Boundary fence blocks (type and count by specification)", "عدد بلوك السور", "EXTERNAL_WORKS",
                  "BOUNDARY_WORKS", "pcs"),
    BELOW_NG: ("Boundary wall masonry below N.G. between the ground beams", "بلوك السور تحت منسوب الأرض الطبيعية",
               "EXTERNAL_WORKS", "BOUNDARY_WORKS", "m2"),
    FACE: ("Boundary fence finish face (physical face per side; carrier geometry)", "وجه السور للتشطيب",
           "EXTERNAL_WORKS", "BOUNDARY_WORKS", "m2"),
    TOP: ("Boundary fence wall top (length along the run)", "رأس جدار السور", "EXTERNAL_WORKS", "BOUNDARY_WORKS", "lm"),
    PLASTER: ("Boundary fence plaster / render layer (per face)", "لياسة السور", "EXTERNAL_WORKS", "BOUNDARY_WORKS",
              "m2"),
    PAINT: ("Boundary fence paint / coating layer (per face)", "دهان السور", "EXTERNAL_WORKS", "BOUNDARY_WORKS", "m2"),
    GATE: ("Boundary gate leaf (count; type, size and material by specification)", "بوابة السور", "EXTERNAL_WORKS",
           "BOUNDARY_WORKS", "pcs"),
    PAD: ("Boundary wall pad footings", "قواعد السور", "CONCRETE", "BOUNDARY_WORKS", "m3"),
}
UNITS = {c: v[4] for c, v in NEW_ITEMS.items()}
VALUE_CODES = (WALL, FACE, TOP)          # only geometry a merged verdict re-measured may carry a figure
UPPER_GB = "STR.CONC.GROUND_BEAM"

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3035.py (B13-04 boundary fence and gates from the Checker-merged T-396 / "
                  "T-403 / T-404 / T-361 ledgers: wall plane, faces and top DRAWING-CONFIRMED; block net / type / "
                  "count, layers, sea / passage runs, masonry below N.G., pads and the G-01 leaf HELD blank by name; "
                  "the upper G.B held range to its drawn gross; lower band, RL-10 and G-02 = D-GF-15 bound by id)",
        "policy": "BOUNDARY_FENCE_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["Q-65 C (fence material HELD: block type / count; provisional alternatives comparison only)",
                        "Q-63 C (sea-side element HELD: material, height, structure, gate)",
                        "Q-28 A PROVISIONAL (footing crossings deducted only where the elevations overlap)",
                        "Q-21 C (the 1.50 m excavation note is a minimum)",
                        "UP-QTY-STATUS-001 (held is blank, never 0)",
                        "R-T396-1 .. 5 (runs on the band, corners once, gates by name; height only from a print; "
                        "plane vs block net; below-N.G. masonry its own component)",
                        "R-T403-1 .. 7 (component by component below N.G.; AT_LEAST from a printed minimum; band "
                        "split by owner class)",
                        "R-T404-1 .. 6 (faces per side; layer only from a note or an owner rule; coping NOT_DRAWN)",
                        "R-T361-1 .. 5 (a gate counted once; no assumed leaf)",
                        "ELEMENT_REGISTER 2026-10-31 16:20 / 20:20 (plot boundary wall: three trades; one physical "
                        "layer, one owner trade)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner blockwork method: run length x wall height less openings, per run (Q-65 C: the "
                               "block type is a held material, the m2 geometry is measured); finishes per face only "
                               "where a note or an owner rule names them (none for the fence); concrete member by "
                               "member (Q-61 C); a member whose dimension or count is not printed stays HELD",
        "drawing_method": "arch GF plan layer-5 fence bands (runs, corners once, gate gaps), p.12 FENCE SECTION '265' "
                          "= '50' + '215' and the elevation fence ends to +2.65 (T-396, Checker re-measure AGREE); "
                          "ST p.14 TYPICAL BOUNDARY WALL A-A and the S-BOUN bands (T-403, AGREE); p.12 faces per side "
                          "(T-404, AGREE); D120 block / HIDDEN gap (T-361, AGREE)"},
}
WAITING = dict(A3034.WAITING)
WAITING.update({
    "FENCE_COLUMNS_M4": "boundary columns 20 x 30 'SEE ARCH PLAN': none drawn in any fence band (count M4): the block "
                        "net (0.795 m2 per column above N.G.), the upper G.B net (0.024 m3 per joint) and the masonry "
                        "net below N.G. stay HELD",
    "FENCE_LOWER_050_BAND": "the p.12 lower '50' band: block or concrete plinth (18.485 m2 block / 3.697 m3 concrete "
                            "on north + street): designer fact; the block net stays HELD at most the plane",
    "FENCE_STREET_PROFILE": "street fence dip with X railing and the rounded gate-end top, undimensioned: the street "
                            "faces / top / stop-end HELD at most / at least",
    "FENCE_FINISH_LAYERS": "no finish printed on p.12 and OWNER_NOTES_SIGMA item 3 unanswered: every plaster / paint "
                           "layer HELD at most its face (never the house system by default, R-T404-5)",
    "LOWER_BAND_SPLIT_DG": "the lower boundary band line carries the Checker line-content downgrade (T-356 band): its "
                           "split by owner class (fence 3.3976 .. 5.2884 / pool 0.24 .. 0.42 / house 2.0016 .. 5.3244 "
                           "m3, T-403) waits for a Checker re-issue of that downgrade on the split lines; bound here, "
                           "never a second line",
    "BOUNDARY_BLINDING": "blinding under the boundary pads (0.117 .. 0.135 m3 per pad, T-403) and under the lower beam "
                         "between pads (not drawn): with the pad count (M4)",
    "BELOW_NG_COATING": "coating of the boundary masonry faces below N.G.: no note on ST p.14; HELD with the masonry "
                        "height (T-404); the G.B faces are T-263's",
    "HOUSE_SOUTH_GB_BLOCK": "block under the house south G.B 29.97 m (T-403 s.8, T-407): house masonry, not the fence "
                            "family (register ruling 2026-10-31 20:20)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _pos(x, where, zero_ok=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x < 0 or (x == 0 and not zero_ok):
        raise InputsError(f"{where}: {x!r} is not a positive figure (held is BLANK, never 0)")
    return float(x)


def _srcs(r, srcs, where):
    if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
        raise InputsError(f"{where}: no merged source named")


def term_value(code, t, where):
    """the figure of a valued component from its terms (metres): m2 = length x height - deduct; lm = length."""
    L = _pos(t.get("length_m"), f"{where} length_m")
    if UNITS[code] == "lm":
        if t.get("height_m") is not None:
            raise InputsError(f"{where}: a length line carries no height")
        return L
    H = _pos(t.get("height_m"), f"{where} height_m")
    if H > 10:
        raise InputsError(f"{where}: height {H} m (mm or cm read as m?)")
    D = _pos(t.get("deduct_m2", 0), f"{where} deduct_m2", zero_ok=True)
    if D >= L * H:
        raise InputsError(f"{where}: deduction {D} m2 is not smaller than the face {L * H} m2")
    return L * H - D


def load_inputs(doc, project_id=None):
    """URBAN_V3035_INPUTS_V1 -> the validated doc. {"schema", "project_id", "sources": [{"task", "file", "sha256",
    "merge_commit", "checker_run"}], "lines": [{"action": FENCE_VALUE | FENCE_HELD, "item_code", "element_id",
    "physical_element", "run", "side", "terms" (VALUE), "value" (VALUE), "held_reason" (HELD), "beside": {"kind",
    "value", "unit"} (HELD, optional), "evidence_status", "source_tasks", "cause"}], "restates": [{"action":
    "HELD_BOUND", "line_id", "expect", "gross_terms": {"length_m", "width_m", "depth_m"}, "cause", "source_tasks"}],
    "bindings": [{"action": "BIND", "line_id", "expect", "what", "share", "cause", "source_tasks"}], "records":
    [{"item", "status", "cause", "source_tasks"}], "checks": {"plane_total_m2", "faces_dc_total_m2",
    "facade_shared_m2", "gate_ids"}}"""
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
    rows, seen = [], set()
    for i, r in enumerate(doc.get("lines") or ()):
        act = r.get("action")
        where = f"line {i} {act} {r.get('element_id')}"
        if act not in ("FENCE_VALUE", "FENCE_HELD"):
            raise InputsError(f"{where}: action {act!r}")
        _need(r, ("item_code", "element_id", "physical_element", "evidence_status", "cause"), where)
        _srcs(r, srcs, where)
        code = r["item_code"]
        if code not in NEW_ITEMS:
            raise InputsError(f"{where}: {code} is not a B13-04 boundary code of this piece")
        if act == "FENCE_VALUE":
            if code not in VALUE_CODES:
                raise InputsError(f"{where}: {code} cannot carry a figure (a held material holds the type, count and "
                                  f"layers, never a value)")
            if r["evidence_status"] != "DRAWING-CONFIRMED":
                raise InputsError(f"{where}: a valued component is DRAWING-CONFIRMED geometry only")
            v = _pos(r.get("value"), f"{where} value")
            calc = term_value(code, r.get("terms") or {}, where)
            if abs(calc - v) > TOL:
                raise InputsError(f"{where}: value {v} is not its terms {_r(calc)} (never a typed figure)")
            if r.get("beside"):
                raise InputsError(f"{where}: a valued line carries no beside figure")
        else:
            _need(r, ("held_reason",), where)
            if r.get("value") is not None:
                raise InputsError(f"{where}: a held component is added BLANK, never with a value")
            if r["evidence_status"] not in ("HELD", "UNKNOWN"):
                raise InputsError(f"{where}: a blank line is HELD or UNKNOWN")
            b = r.get("beside")
            if b:
                _need(b, ("kind", "unit"), f"{where} beside")
                if b["kind"] not in BESIDE_KINDS:
                    raise InputsError(f"{where}: beside kind {b['kind']!r}")
                _pos(b.get("value"), f"{where} beside value")
        key = (code, r["element_id"])
        if key in seen:
            raise InputsError(f"{where}: element in two lines (one component, one line)")
        seen.add(key)
        rows.append(r)
    if not rows:
        raise InputsError("no boundary line in the inputs")
    rest = []
    for i, r in enumerate(doc.get("restates") or ()):
        where = f"restate {i} {r.get('line_id')}"
        if r.get("action") != "HELD_BOUND":
            raise InputsError(f"{where}: action {r.get('action')!r}")
        _need(r, ("line_id", "cause"), where)
        _srcs(r, srcs, where)
        e = r.get("expect") or {}
        _need(e, ("item_code", "evidence_state"), f"{where} expect")
        if e["item_code"] != UPPER_GB or e["evidence_state"] not in HELD_STATES:
            raise InputsError(f"{where}: a held bound is restated on a HELD ground-beam line only")
        g = r.get("gross_terms") or {}
        hi = _pos(g.get("length_m"), where) * _pos(g.get("width_m"), where) * _pos(g.get("depth_m"), where)
        if max(g["width_m"], g["depth_m"]) > 3:
            raise InputsError(f"{where}: a section of {g['width_m']} x {g['depth_m']} m (mm or cm read as m?)")
        if abs(hi - _pos(r.get("high"), f"{where} high")) > TOL:
            raise InputsError(f"{where}: high {r.get('high')} is not the drawn gross {_r(hi)}")
        if _pos(r.get("low", -1), f"{where} low", zero_ok=True) != 0:
            raise InputsError(f"{where}: the low end of a held bound whose deduction count is not printed is 0")
        rest.append(r)
    binds, bseen = [], set()
    for i, r in enumerate(list(doc.get("bindings") or ())):
        where = f"bind {i} {r.get('line_id')}"
        if r.get("action") != "BIND":
            raise InputsError(f"{where}: action {r.get('action')!r}")
        _need(r, ("line_id", "what", "cause"), where)
        _srcs(r, srcs, where)
        _need(r.get("expect") or {}, ("item_code", "evidence_state"), f"{where} expect")
        if r["line_id"] in bseen or r["line_id"] in {x["line_id"] for x in rest}:
            raise InputsError(f"{where}: a line bound twice or both bound and restated")
        bseen.add(r["line_id"])
        binds.append(r)
    recs = []
    for i, r in enumerate(doc.get("records") or ()):
        _need(r, ("item", "status", "cause"), f"record {i}")
        _srcs(r, srcs, f"record {i}")
        if r["status"] not in ("NOT_DRAWN", "OTHER_OWNER"):
            raise InputsError(f"record {i}: status {r['status']!r}")
        recs.append(r)
    ck = doc.get("checks") or {}
    _need(ck, ("plane_total_m2", "faces_dc_total_m2", "gate_ids"), "checks")
    if _pos(ck.get("facade_shared_m2", -1), "checks facade_shared_m2", zero_ok=True) != 0:
        raise InputsError("checks: a fence face shared with the house facade ledger is a double count (0.000 m2)")
    for code, k in ((WALL, "plane_total_m2"), (FACE, "faces_dc_total_m2")):
        s = sum(r["value"] for r in rows if r["action"] == "FENCE_VALUE" and r["item_code"] == code)
        if abs(s - _pos(ck[k], f"checks {k}")) > 1e-5:
            raise InputsError(f"checks: valued {code} lines sum to {_r(s)}, the verified total is {ck[k]}")
    return dict(doc, _sources=srcs, _rows=rows, _restates=rest, _bindings=binds, _records=recs)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "family": FAMILY, "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _terms_text(code, t):
    if UNITS[code] == "lm":
        return f"{_fmt(t['length_m'])} m"
    d = t.get("deduct_m2") or 0
    s = f"{_fmt(t['length_m'])} m x {_fmt(t['height_m'])} m"
    return s + (f" - {_fmt(d)} m2 ({t.get('deduct_what') or 'gate'})" if d else "")


def _new(tmpl, r, srcs):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    code = r["item_code"]
    en, ar, tr, sub, unit = NEW_ITEMS[code]
    S = "+".join(r["source_tasks"])
    if r["action"] == "FENCE_VALUE":
        v = _r(r["value"])
        formula = (f"{r['physical_element']} ({r['element_id']}): {_terms_text(code, r['terms'])} = {_fmt(v)} {unit} "
                   f"DRAWING-CONFIRMED ({r['cause']}; {S})")
        if len(formula) > 700:
            formula = f"{r['element_id']}: {_terms_text(code, r['terms'])} = {_fmt(v)} {unit}"
        ev, net, rfi = "MEASURED", v, None
        note = f"{METHOD}: {FAMILY} component, geometry DRAWING-CONFIRMED ({S}); material BY_SPEC; NOT RELEASED"
    else:
        b = r.get("beside")
        bt = (f"; {b['kind'].lower().replace('_', ' ')} {_fmt(b['value'])} {b['unit']} beside, never the line figure"
              if b else "")
        formula = (f"HELD (blank in the BOQ, never 0): {r['physical_element']} ({r['element_id']}): {r['held_reason']}"
                   f"{bt} ({S})")
        ev, net = "BLOCKED_RFI", None
        rfi = {"question": formula[:900], "unlocks": r["element_id"]}
        note = f"{METHOD}: {FAMILY} component HELD BLANK by name ({S}); never 0; NOT RELEASED"
    rec = _rec(srcs, action=r["action"], evidence_status=r["evidence_status"], run=r.get("run"), side=r.get("side"),
               terms=r.get("terms"), beside=r.get("beside"), cause=r["cause"], held_reason=r.get("held_reason"),
               owner_trade=r.get("owner_trade") or "BOUNDARY WORKS", never_with=r.get("never_with") or [])
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"], item_code=code,
                      unit=unit, evidence_state=ev, measured_net=net, element_id=r["element_id"],
                      floor=r.get("floor") or "SITE", physical_element=r["physical_element"],
                      gross=(None if net is None else net if unit == "lm" else
                             _r(r["terms"]["length_m"] * r["terms"]["height_m"])),
                      formula=formula[:700], inputs={REC_KEY: rec},
                      documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source="CAD_VECTOR", geometry_confidence="INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="BY_SPEC", rfi=rfi,
                      notes=note[:600], item_en=en, item_ar=ar, trade=tr, subtrade=sub)
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def _assert_line(b, e, lid):
    if b is None:
        raise InputsError(f"line {lid}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = b["item_code"] == e["item_code"] and b["evidence_state"] == e["evidence_state"]
    if ok and e.get("element_id") is not None:
        ok = loc.get("element_id") == e["element_id"]
    if ok and "measured_net" in e:
        ok = (b.get("measured_net") is None) if e["measured_net"] is None else \
            (b.get("measured_net") is not None and abs(b["measured_net"] - e["measured_net"]) <= TOL)
    if ok and e.get("high") is not None:
        ok = abs(((b.get("bounded_range") or {}).get("high") or -1) - e["high"]) <= TOL
    if not ok:
        raise InputsError(f"line {lid}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{b.get('measured_net')} is not the bound {e} (stale binding: re-bind before integrating)")


def bind_check(doc, lines):
    """BIND / RECORD on the lines given (V3.0.34 or V3.0.35): every bound line stands as the merged ledger read it. ->
    rows (records)."""
    if not doc:
        return []
    by = {ln["line_id"]: ln for ln in lines}
    S = doc["_sources"]
    out = []
    for r in doc["_bindings"]:
        b = by.get(r["line_id"])
        _assert_line(b, r["expect"], r["line_id"])
        srcs = [S[t] for t in r["source_tasks"]]
        out.append({"version": METHOD, "piece": PIECE, "action": "BIND", "family": FAMILY, "line_id": r["line_id"],
                    "item_code": b["item_code"], "element_id": (b.get("location") or {}).get("element_id"),
                    "unit": b["unit"], "what": r["what"], "share": r.get("share"), "cause": r["cause"],
                    "state": b["evidence_state"], "quantity": A30._qty(b), "lines_added": 0, "double_count": 0,
                    "evidence_status": r.get("evidence_status") or ("HELD" if b["evidence_state"] not in
                                                                    VALUED_STATES else "DRAWING-CONFIRMED"),
                    "verification": _ver(srcs), "release_status": "NOT RELEASED"})
    for r in doc["_records"]:
        srcs = [S[t] for t in r["source_tasks"]]
        out.append({"version": METHOD, "piece": PIECE, "action": "RECORD", "family": FAMILY, "line_id": None,
                    "item_code": None, "element_id": r["item"], "unit": r.get("unit"), "what": r["item"],
                    "share": None, "cause": r["cause"], "state": r["status"], "quantity": None, "lines_added": 0,
                    "double_count": 0, "evidence_status": "UNKNOWN" if r["status"] == "NOT_DRAWN" else "OTHER_OWNER",
                    "verification": _ver(srcs), "release_status": "NOT RELEASED"})
    return out


def changes_for(doc, l3034):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    if any(ln["item_code"] in NEW_ITEMS or ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
           for ln in l3034):
        raise InputsError("the candidate already carries B13-04 boundary lines (applied once)")
    by = {ln["line_id"]: ln for ln in l3034}
    S = doc["_sources"]
    tmpl = next((x for x in l3034 if x["item_code"] == "STR.CONC.BOUNDARY_WALL"), None) or l3034[0]
    changes, seen = [], set(by)
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines_added": 0,
           "lines_restated": 0, "valued": {}, "held_lines": 0}
    for r in doc["_rows"]:
        srcs = [S[t] for t in r["source_tasks"]]
        ln = _new(tmpl, r, srcs)
        if ln["line_id"] in seen:
            raise ValueError(f"{METHOD}: added line {r['element_id']} repeats an id")
        seen.add(ln["line_id"])
        held = [] if r["action"] == "FENCE_VALUE" else [
            {"what": f"{r['item_code']} {r['element_id']}", "why": r["held_reason"][:300],
             "range": None, "scenario": None}]
        changes.append(A305._change(PIECE, "ADD", None, ln, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=r.get("downstream") or [], verification=_ver(srcs),
                                    evidence_status=r["evidence_status"], codes=[PIECE, r["action"]],
                                    group=r["item_code"]))
        log["by_action"][r["action"]] = log["by_action"].get(r["action"], 0) + 1
        log["lines_added"] += 1
        if r["action"] == "FENCE_VALUE":
            k = f"{r['item_code']}|{UNITS[r['item_code']]}"
            log["valued"][k] = _r(log["valued"].get(k, 0.0) + r["value"])
        else:
            log["held_lines"] += 1
    for r in doc["_restates"]:
        b = by.get(r["line_id"])
        _assert_line(b, r["expect"], r["line_id"])
        if b.get("measured_net") is not None:
            raise InputsError(f"line {r['line_id']}: a held line carries a value")
        if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
            raise InputsError(f"line {r['line_id']}: already restated (applied once)")
        old = b.get("bounded_range") or {}
        if old.get("high") is not None and r["high"] > old["high"] + TOL:
            raise InputsError(f"line {r['line_id']}: the new bound {r['high']} is above the old {old['high']} (a "
                              f"bound fix never adds)")
        srcs = [S[t] for t in r["source_tasks"]]
        g = r["gross_terms"]
        lo, hi = 0.0, _r(r["high"])
        basis = (f"held bound 0 .. {_fmt(hi)} m3: drawn gross {_fmt(g['length_m'])} x {_fmt(g['width_m'])} x "
                 f"{_fmt(g['depth_m'])} m, less the column joints (count not printed)")[:300]
        rec = _rec(srcs, action="HELD_BOUND", evidence_status="HELD", before=A3018._before_rec(b), cause=r["cause"],
                   gross_terms=g, low=lo, high=hi)
        formula = (f"HELD (never a value): bound {_fmt(lo)} .. {_fmt(hi)} m3 (drawn gross {_fmt(g['length_m'])} x "
                   f"{_fmt(g['width_m'])} x {_fmt(g['depth_m'])}): {r['cause']}")
        ln = copy.deepcopy(b)
        ln["bounded_range"] = dict(old, low=lo, high=hi, basis=basis)
        ln["calculation"] = dict(ln.get("calculation") or {}, formula=formula[:700],
                                 inputs=dict((ln.get("calculation") or {}).get("inputs") or {}, **{REC_KEY: rec}))
        A305._note(ln, f"{METHOD}: held bound restated to the drawn gross ({'+'.join(r['source_tasks'])}); still "
                       f"HELD; NOT RELEASED")
        from engine.source import boq_line as BL
        after = BL.validate(ln)
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[{"what": f"{b['item_code']} {b['location'].get('element_id')}",
                                           "why": basis, "range": [lo, hi], "scenario": None}],
                                    downstream=[], verification=_ver(srcs), evidence_status="HELD",
                                    codes=[PIECE, "HELD_BOUND"], group=after["item_code"]))
        log["by_action"]["HELD_BOUND"] = log["by_action"].get("HELD_BOUND", 0) + 1
        log["lines_restated"] += 1
    brows = bind_check(doc, l3034)
    for b in brows:
        log["by_action"][b["action"]] = log["by_action"].get(b["action"], 0) + 1
    log["by_action"] = dict(sorted(log["by_action"].items()))
    log["bind_rows"] = brows
    return changes, log


# ================================================================================================ integrate / write
def check_boundary(lines, doc=None):
    """on finished lines: every B13-04 line is of this piece; valued only on the value codes, MEASURED with its terms
    reproduced; every other one BLANK BLOCKED_RFI; one line per (code, element); no line outside the piece names a
    fence element; the gates appear once (G-02 by its opening line, G-01 as one held leaf line). -> summary."""
    out = {"lines": 0, "valued": {}, "blank": 0, "by_code": {}}
    seen = set()
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        eid = str((ln.get("location") or {}).get("element_id") or "")
        if ln["item_code"] not in NEW_ITEMS:
            if eid.startswith("FENCE:"):
                raise ValueError(f"{METHOD}: {ln['line_id']} {ln['item_code']} names a fence element outside "
                                 f"{FAMILY} (one component, one owner)")
            continue
        if not rec or rec.get("action") not in ("FENCE_VALUE", "FENCE_HELD"):
            raise ValueError(f"{METHOD}: {ln['line_id']} {ln['item_code']} is not a V3.0.35 boundary line")
        key = (ln["item_code"], eid)
        if key in seen:
            raise ValueError(f"{METHOD}: {key} in two lines")
        seen.add(key)
        out["lines"] += 1
        out["by_code"][ln["item_code"]] = out["by_code"].get(ln["item_code"], 0) + 1
        if rec["action"] == "FENCE_VALUE":
            if ln["item_code"] not in VALUE_CODES or ln["evidence_state"] != "MEASURED" or \
                    abs(term_value(ln["item_code"], rec["terms"], ln["line_id"]) - ln["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: valued line {ln['line_id']} is not its terms")
            k = f"{ln['item_code']}|{ln['unit']}"
            out["valued"][k] = _r(out["valued"].get(k, 0.0) + ln["measured_net"])
        else:
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None or \
                    ln.get("bounded_range") or ln.get("gross") is not None:
                raise ValueError(f"{METHOD}: held line {ln['line_id']} is not BLANK (held is blank, never 0)")
            out["blank"] += 1
    gates = [ln for ln in lines if ln["item_code"] == GATE]
    if doc:
        gid = doc["checks"]["gate_ids"]
        held_ids = sorted(str(ln["location"]["element_id"]) for ln in gates)
        want = sorted(f"FENCE:{g}:LEAF" for g, how in gid.items() if how == "FENCE_GATE_LINE")
        if held_ids != want:
            raise ValueError(f"{METHOD}: gate lines {held_ids} are not {want} (a gate counted once)")
    out["by_code"] = dict(sorted(out["by_code"].items()))
    return out


def integrate(l3034, changes, for_lead=(), doc=None):
    """-> (V3.0.35 lines, identity). Every line outside the rows is byte-identical to V3.0.34."""
    sid = {ln["line_id"] for ln in l3034}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != PIECE:
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only carries the boundary fence)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid or \
                    c["after"]["item_code"] != c["before"]["item_code"] or c["after"]["item_code"] != UPPER_GB:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.34, its id / item changed or not "
                                 f"the upper boundary G.B")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            a = c["after"]
            if a["line_id"] in sid or a["item_code"] not in NEW_ITEMS:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.34 id or is not a B13-04 code")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3034] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)   # every family guard up to V3.0.30
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = A3034.check_zones(out)
    fence = check_boundary(out, doc)
    brows = bind_check(doc, out) if doc else []
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by34 = {ln["line_id"]: ln for ln in l3034}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by34[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3034):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.35 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only state, range, rfi, calculation and notes change
        a, b = copy.deepcopy(by34[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside state / range / text")
        if ln.get("measured_net") is not None:
            raise ValueError(f"{METHOD}: line {lid}: a held bound carries a value")
    ident = {"v3_0_34_lines": len(l3034), "v3_0_35_lines": len(out), "v3_0_35_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_34": len(outside), "fence": fence, "bound": len(brows),
             "tile_zones": zones, "corrections": corr, "ceilings": ceil, "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, brows, released_lines=None):
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
        rows.append({"version": METHOD, "piece": PIECE, "action": rec.get("action"), "family": FAMILY,
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "run": rec.get("run"),
                     "side": rec.get("side"), "terms": rec.get("terms"), "beside": rec.get("beside"),
                     "before_released_v2_9": b29,
                     "before_v3_0_34": (A30._qty(c["before"]) if c["before"] else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_34")),
                     "before_held_range_v3_0_34": (c["before"] or {}).get("bounded_range"),
                     "after_v3_0_35": A30._qty(ref), "after_held_range_v3_0_35": ref.get("bounded_range"),
                     "evidence_status": c.get("evidence_status"), "cause": rec.get("cause"),
                     "held_reason": rec.get("held_reason"), "owner_trade": rec.get("owner_trade"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    for b in brows:
        rows.append(dict(b, owner_manual_method=PIECES[PIECE]["owner_manual_method"],
                         drawing_derived_method=PIECES[PIECE]["drawing_method"], rollback=ROLLBACK))
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "element_id", "unit", "terms", "beside", "v2_9", "v3_0_34",
              "v3_0_35", "held_range_v3_0_35", "evidence_status", "cause", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_34", "vs_released_v2_9", "v2_9",
            "v3_0_34", "v3_0_35")


def _rg(br):
    return "" if not br else f"{_fmt(br.get('low'))} .. {_fmt(br.get('high'))}"


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x else ""

    def t(r):
        tt = r.get("terms")
        return "" if not tt else _terms_text(r["item_code"], tt)

    def bs(r):
        b = r.get("beside")
        return "" if not b else f"{b['kind']} {_fmt(b['value'])} {b['unit']}"
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r.get("line_id") or "",
                       "item_code": r.get("item_code") or "", "element_id": r.get("element_id") or "",
                       "unit": r.get("unit") or "", "terms": t(r), "beside": bs(r),
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_34": q(r.get("before_v3_0_34") or
                                                                              r.get("quantity")),
                       "v3_0_35": q(r.get("after_v3_0_35") or r.get("quantity")),
                       "held_range_v3_0_35": _rg(r.get("after_held_range_v3_0_35")),
                       "evidence_status": r["evidence_status"],
                       "cause": (r.get("held_reason") or r.get("cause") or "")[:400],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3034, l3035, released_lines=None):
    b34 = {ln["line_id"]: ln for ln in l3034}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3035:
        o = b34.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if (A30._qty(o) != A30._qty(ln) or
                                                       o.get("bounded_range") != ln.get("bounded_range"))
                                         else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_34": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_34": A302._q(A30._qty(o)) if o else "", "v3_0_35": A302._q(A30._qty(ln))})
    return out


def write(out, l3034, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_35_* files beside the V3_0_34_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3035, ident = integrate(l3034, changes, for_lead, doc)
    brows = bind_check(doc, l3035) if doc else []
    rows = ledger_rows(changes, brows, released_lines)
    diff = diff_rows(l3034, l3035, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_34", {}).setdefault(d["vs_v3_0_34"], 0)
        dsum["vs_v3_0_34"][d["vs_v3_0_34"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t34, t35 = A304.code_totals(l3034), A304.code_totals(l3035)
    moved = {k: {"v3_0_34": t34.get(k), "v3_0_35": t35.get(k)} for k in sorted(set(t34) | set(t35))
             if t34.get(k) != t35.get(k)}
    allowed = set(NEW_ITEMS) | {UPPER_GB}
    if any(k.split("|")[0] not in allowed for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the boundary codes: {sorted(moved)[:5]}")
    gb = {k: v for k, v in moved.items() if k.split("|")[0] == UPPER_GB}
    for k, v in gb.items():   # the restated beam: a held range may move; no released / valued total
        a, b = v["v3_0_34"] or {}, v["v3_0_35"] or {}
        if a.get("released") != b.get("released") or a.get("lines") != b.get("lines"):
            raise ValueError(f"{METHOD}: a valued ground-beam total moved: {k} {v}")
    log = {k: v for k, v in log.items() if k != "bind_rows"}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_35_BOQ_LINES.json": BL.dumps(l3035),
             "V3_0_35_BOQ_LINES.csv": A30._lines_csv(l3035),
             "V3_0_35_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_35_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_35_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_35_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "NEW_ITEMS", "load_inputs",
           "term_value", "bind_check", "changes_for", "check_boundary", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError"]
