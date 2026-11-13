"""ARCH_TAKEOFF_V3.0.79 (T-314 r3, lane I, EXTERIOR RENDER + EXTERIOR PAINT integration package; owner gap #1 of
2026-11-13): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.78 (engine.source.arch_v30, arch_v301 ..
arch_v3078), extended with THREE pieces built from the Checker-merged T-756 face ledger (re-based by line id onto the
candidate; its mapped ids re-checked on V3.0.78: none changed), by line id. No line outside FIN.EXT.FINISH,
FIN.EXT.PAINT and the one FIN.EXT.PAINT.EDGE line named below moves; no released quantity moves:

  RENDER_FACES  every exterior rendered face band (storey band F.F.L. -> next level, parapet outer / inner / top, plinth,
                slab-edge band) is ONE face row of ONE line, with its net render m2 after its holes (Q-73 A: each opening
                once, on the face that holds it); a FIN.EXT.FINISH line is the SUM of its face rows: all faces valued ->
                HELD BOUNDED low .. high (a point when low = high; held, never released here); any face blank -> the
                line is HELD BLANK with the valued part beside (never summed, never 0). The three storey lines are
                CHANGED in place; the twelve parapet / plinth / slab-edge lines are ADDED with the ids the merged ledger
                reserved (R-T314-1 1.0.0 line ids, re-derived here and asserted).
  PAINT_FACES   the exterior paint (Sigma) of the same faces: OWNER RULE PAINT 2026-11-12 (UP-FIN-PAINT-002) paint m2 =
                render m2 of the same faces, face by face; no exterior face carries a printed other finish (T-747) and
                there is no false ceiling outside, so nothing is deducted; one FIN.EXT.PAINT m2 line per render line,
                the same element id, the same figures and state (blank stays blank), bound by id to its render line.
  EDGE_DELTA    a merged edge verdict on a FIN.EXT.PAINT.EDGE line (T-754 F-T754-1 via T-756 R-T756-3): the line takes
                the merged after-figure; corners and window / door edges stay lm lines, never paint m2.

R-T314-3 (every villa): (a) a line is wired only from a Checker-merged face ledger that names it by line id; every face
row once, on one line, of the line's element (a parapet / plinth / slab-edge band in a storey line is refused); (b) the
line figure is recomputed here from its face rows and asserted equal to the ledger's line figure (stop on a difference);
(c) a CHANGE binds the candidate line as the ledger read it (item, element, unit, HELD, blank or the named range) and
stops on a stale line; an ADD id is re-derived and must be free; (d) paint = render face by face (UP-FIN-PAINT-002), on
its own code, never folded into the render line; edges stay lm; (e) only the codes of this version move, each exactly by
the changes; released lines and every other line byte-identical (asserted); the earlier state checks re-run on the
result; (f) held stays held: nothing here is VERIFIED or released; blank is never 0.
Files: V3_0_79_BOQ_LINES.json / .csv, V3_0_79_INTEGRATION_LEDGER.json / .csv, V3_0_79_DIFF.csv, V3_0_79_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
from decimal import Decimal

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3064 as A3064
from engine.source import arch_v3065 as A3065
from engine.source import arch_v3066 as A3066
from engine.source import arch_v3067 as A3067
from engine.source import arch_v3068 as A3068
from engine.source import arch_v3069 as A3069
from engine.source import arch_v3070 as A3070
from engine.source import arch_v3071 as A3071
from engine.source import arch_v3072 as A3072
from engine.source import arch_v3073 as A3073
from engine.source import arch_v3074 as A3074
from engine.source import arch_v3075 as A3075
from engine.source import arch_v3076 as A3076
from engine.source import arch_v3077 as A3077
from engine.source import arch_v3078 as A3078

DEFAULT_GUARD_CLASS = "TOOLING"          # books a Checker-merged face ledger onto candidate lines; sums its rows only
METHOD = "ARCH_TAKEOFF_V3.0.79"
EXTENDS = A3078.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T314_ARCH_V3_0_79"
INPUTS_SCHEMA = "URBAN_V3079_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3079_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T314-3", "T-314 r3"
ADD_RULE = ("R-T314-1", "1.0.0")         # the rule the merged ledger reserved the added render ids under (T-756 NEW_FREE)
PAINT_RULE = ("R-T314-3", "1.0.0")       # the paint lines' own id rule (one per render line, same element id)
REC_KEY = "ext_render_paint_v3079"
RENDER, PAINT, EDGE = "FIN.EXT.FINISH", "FIN.EXT.PAINT", "FIN.EXT.PAINT.EDGE"
CODES = {RENDER: "m2", PAINT: "m2", EDGE: "lm"}
ELEMENTS = ("STOREY", "PARAPET_OUTER", "PARAPET_INNER", "PARAPET_TOP", "PLINTH", "SLAB_EDGE")
P_RENDER, P_PAINT, P_EDGE = "RENDER_FACES", "PAINT_FACES", "EDGE_DELTA"
STATUSES = ("DRAWING-CONFIRMED", "HELD", "ASSUMED — OWNER-APPROVED")      # WORKFLOW_CONTROLS s.5; never VERIFIED
PAINT_ITEM = ("External paint (Sigma), wall faces", "دهان خارجي (سيجما) للواجهات", "PAINT")
RENDER_ITEM = ("External render (exterior plaster), wall faces", "لياسة خارجية للواجهات", "PLASTER")
TOL = 1e-6
TOT_TOL = 5e-6
MAX_FACE = 500.0                         # m2 of one face: above it is a unit slip (mm2 / cm2)
MAX_EDGE = 100.0                         # lm of one edge line
D = Decimal
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK

PIECES = {
    P_RENDER: {"module": "engine/source/arch_v3079.py (the FIN.EXT.FINISH lines as the sum of their face rows of the "
                         "merged T-756 face ledger: 3 storey lines changed, 12 parapet / plinth / slab-edge lines added)",
               "policy": "EXT_RENDER_GATE_B_V1", "rule_id": "R-T314-1 / R-T756-1..4 (R-T314-3)",
               "owner_rules": ["OWNER_NOTES_SIGMA 2026-10-21 (Sigma = the exterior plaster area; domes excluded)",
                               "Q-07 B (bands measured from the floor)", "Q-73 A (every actual opening in full)",
                               "Q-55 C (2F door 2.20 m, owner-approved)", "UP-QTY-STATUS-001 (held never 0)"],
               "owner_manual_method": "OWNER_NOTES_SIGMA 2026-10-21: elevation length x height per face, parapets and "
                                      "plinth with the faces, openings deducted (owner: in full, Q-73), corners their "
                                      "own m.l line; the freelancer's half-opening deduction is NOT an owner rule",
               "drawing_method": "each drawn face band: run x band height between its printed levels (F.F.L. -> next "
                                 "level; parapet / plinth / slab-edge bands their own element), less its openings by "
                                 "schedule size on the face that holds them (T-305 / T-311 / T-348 / T-567 / T-747 / "
                                 "T-751 / T-754, re-based by T-756)"},
    P_PAINT: {"module": "engine/source/arch_v3079.py (one FIN.EXT.PAINT m2 line per render line, figures = render face "
                        "by face)",
              "policy": "EXT_PAINT_GATE_B_V1", "rule_id": "UP-FIN-PAINT-002 (R-T314-3)",
              "owner_rules": ["OWNER RULE PAINT 2026-11-12 (paint m2 = plaster m2 of the same faces, inside and "
                              "outside; corners / edges lm)", "UP-QTY-STATUS-001"],
              "owner_manual_method": "paint area = plaster area of the same faces (owner 2026-11-12); edges and "
                                     "corners as lm, never extra area",
              "drawing_method": "face by face: render net m2 less a printed other finish (none on any exterior face, "
                                "T-747) and less a false-ceiling band (none outside) = render net m2"},
    P_EDGE: {"module": "engine/source/arch_v3079.py (the merged T-754 corner verdict on one FIN.EXT.PAINT.EDGE line, "
                       "via T-756 R-T756-3)",
             "policy": "EXT_EDGE_DELTA_V1", "rule_id": "R-T756-3 / F-T754-1 (R-T314-3)",
             "owner_rules": ["OWNER RULE PAINT 2026-11-12 (corners lm)", "UP-QTY-STATUS-001"],
             "owner_manual_method": "outside corners in m.l per arris", "drawing_method": "drawn vertical arrises in the "
                                                                                          "band; a straight run is no corner"},
}
WAITING = dict(A3078.WAITING)
WAITING.update({
    "T314_SLAB_EDGE_1F": "1F slab-edge render / paint L-22e75c39 + its paint line stay HELD BLANK (six faces: NE-1, "
                         "SW-1, SW-2 raster only; NW-4, NW-5 hidden; SE-1 2.30 x 0.80 band unbound to GF/SE-2 / T-360 "
                         "C-1): valued part 0.535 .. 2.00625 m2 beside, never summed",
    "T314_HELD_FACES": "W02 / D-GF-07 holes, D-39 parapet inner split, T-324 D bands, pool-court plinth bottom: the "
                       "render / paint lines stay HELD BOUNDED until the designer items close",
    "T314_MISSING": "parapet blockwork x 4 (no MAS.* parapet line), parapet top arrises x 4 (T-337 horizontals), "
                    "passage substrate split: MISSING by name (T-756 A), never 0",
    "T314_OPEN_VERDICTS": "F-T754-1 (8.40 lm inside L-1f1149d7), F-T751-2 (NE-2 parapet top +10.80 .. +11.30), SE-1 "
                          "slab-edge 1.840 m2 ownership: open, not decided here",
})


# ================================================================================================ inputs
def _d(x, w, hi, zero=False):
    if isinstance(x, bool) or x is None:
        raise InputsError(f"{w}: not a number ({x!r})")
    try:
        v = D(str(x))
    except Exception:  # noqa: BLE001
        raise InputsError(f"{w}: not a number ({x!r})") from None
    if not v.is_finite() or v < 0 or v > D(str(hi)) or (v == 0 and not zero):
        raise InputsError(f"{w}: {x!r} outside {'0' if zero else '>0'} .. {hi} (never 0, unit slip)")
    return v


def _pair(x, w, hi):
    if x is None:
        return None
    if not isinstance(x, (list, tuple)) or len(x) != 2:
        raise InputsError(f"{w}: a figure is [low, high] or null (blank)")
    lo, h = _d(x[0], f"{w} low", hi, zero=True), _d(x[1], f"{w} high", hi)    # a 0 .. h range is a held bound;
    #                                                                             a point 0 is refused (never 0)
    if lo > h:
        raise InputsError(f"{w}: low {lo} > high {h}")
    return lo, h


def _status(s, w):
    if s not in STATUSES:
        raise InputsError(f"{w}: status {s!r} (DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED / HELD; never VERIFIED)")
    return s


def element_of(element_id):
    """the face element a FIN.EXT.FINISH element id names: '<F>-FACADE:facade' -> STOREY, '<F>-FACADE:<EL>[:...]'"""
    tail = str(element_id).split(":", 1)[1] if ":" in str(element_id) else ""
    if tail == "facade":
        return "STOREY"
    el = tail.split(":")[0]
    if el not in ELEMENTS:
        raise InputsError(f"{element_id}: element {el!r} is not one of {ELEMENTS}")
    return el


def _line(x, srcs, faces_seen):
    lid = x.get("line_id")
    w = f"{P_RENDER}:{x.get('action')} {lid}"
    A3043._tasks(x, srcs, w)
    A3063._need(x, ("action", "element_id", "faces", "why", "rule", "status"), w)
    if "expect_after" not in x:
        raise InputsError(f"{w}: missing expect_after (the ledger's line figure, or null for a blank line)")
    if not isinstance(lid, str) or not A3063.LINE_ID_RE.match(lid):
        raise InputsError(f"{w}: line id")
    if x["action"] not in ("CHANGE", "ADD"):
        raise InputsError(f"{w}: a render line is CHANGED or ADDED")
    el = element_of(x["element_id"])
    e = dict(x, _status=_status(x["status"], w), _element=el)
    if x["action"] == "CHANGE":
        A3063._need(x, ("expect",), w)
        ex = x["expect"]
        A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
        if ex["item_code"] != RENDER or ex["unit"] != "m2" or ex["class"] != "HELD" or \
                ex["element_id"] != x["element_id"]:
            raise InputsError(f"{w}: {ex} is not a HELD {RENDER} m2 line of this element")
    else:
        A3063._need(x, ("host_line_id",), w)
        if el == "STOREY":
            raise InputsError(f"{w}: a storey line is changed in place, never added")
    rows, lo, hi, blank = [], D(0), D(0), []
    if not x["faces"]:
        raise InputsError(f"{w}: a line with no face row")
    for f in x["faces"]:
        A3063._need(f, ("face_id", "element"), f"{w} face")
        fid = f["face_id"]
        if fid in faces_seen:
            raise InputsError(f"{w}: face {fid} booked on two lines ({faces_seen[fid]})")
        faces_seen[fid] = lid
        if f["element"] != el:
            raise InputsError(f"{w}: face {fid} is a {f['element']} band, the line is {el} (R-T314-3 (a): the "
                              f"element owns the band)")
        r = _pair(f.get("render"), f"{w} face {fid}", MAX_FACE)
        if r is None:
            blank.append(fid)
        else:
            lo, hi = lo + r[0], hi + r[1]
        rows.append(dict(f, _render=r))
    e["_faces"] = rows
    e["_blank_faces"] = blank
    e["_sum"] = (lo, hi)
    want = _pair(x["expect_after"], f"{w} expect_after", 5000.0) if x["expect_after"] is not None else None
    if blank:
        if want is not None:
            raise InputsError(f"{w}: a blank face makes the line blank; the ledger states {want}")
        if x.get("valued_part") is not None:
            vp = _pair(x["valued_part"], f"{w} valued_part", 5000.0)
            if abs(vp[0] - lo) > D("1e-6") or abs(vp[1] - hi) > D("1e-6"):
                raise InputsError(f"{w}: valued part {vp} is not the sum of the valued faces {(lo, hi)}")
    else:
        if want is None or abs(want[0] - lo) > D("1e-6") or abs(want[1] - hi) > D("1e-6"):
            raise InputsError(f"{w}: face sum {lo} .. {hi} is not the ledger's line figure {want} (R-T314-3 (b))")
    return e


def _edge(x, srcs):
    lid = x.get("line_id")
    w = f"{P_EDGE} {lid}"
    A3043._tasks(x, srcs, w)
    A3063._need(x, ("expect", "low", "high", "why", "rule", "status"), w)
    if not isinstance(lid, str) or not A3063.LINE_ID_RE.match(lid):
        raise InputsError(f"{w}: line id")
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class", "low", "high"), w)
    if ex["item_code"] != EDGE or ex["unit"] != "lm" or ex["class"] != "HELD":
        raise InputsError(f"{w}: {ex} is not a HELD {EDGE} lm line")
    lo, hi = _d(x["low"], f"{w} low", MAX_EDGE), _d(x["high"], f"{w} high", MAX_EDGE)
    if lo > hi:
        raise InputsError(f"{w}: low > high")
    return dict(x, _status=_status(x["status"], w), _low=lo, _high=hi)


def load_inputs(doc, project_id=None):
    """URBAN_V3079_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "render": [{"line_id", "action" CHANGE | ADD, "element_id", "host_line_id" (ADD: the floor's storey render line),
                 "source_tasks", "rule", "status", "why", "expect" (CHANGE: {item_code, element_id, unit, class}),
                 "faces": [{"face_id", "element", "render" [low, high] | null (blank), "holes", "state", "cause"}],
                 "expect_after": [low, high] | null, "valued_part": [low, high] (blank lines only)}],
     "edges": [{"line_id", "expect" {item_code, element_id, unit, class, low, high}, "low", "high", "source_tasks",
                "rule", "status", "why"}],
     "statements": [...] (records only: KEEP rows, MISSING items), "expect_totals": {...} (optional)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    seen = {}
    rend = [_line(x, srcs, seen) for x in doc.get("render") or ()]
    edges = [_edge(x, srcs) for x in doc.get("edges") or ()]
    if not rend:
        raise InputsError("no render line in the inputs")
    ids = [e["line_id"] for e in rend + edges]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one statement)")
    els = [e["element_id"] for e in rend]
    if len(set(els)) != len(els):
        raise InputsError("two render lines on one element id")
    return dict(doc, _sources=srcs, _render=rend, _edges=edges)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[kw["piece"]]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _face_rec(e):
    return [{"face_id": f["face_id"], "element": f["element"], "holes": f.get("holes") or "",
             "render": None if f["_render"] is None else [_r(f["_render"][0]), _r(f["_render"][1])],
             "state": f.get("state"), "cause": f.get("cause") or None} for f in e["_faces"]]


def _figure(e):
    """-> (evidence_state, bounded_range | None, head text, after, beside)"""
    u = "m2"
    why = str(e["why"])[:300]
    if e["_blank_faces"]:
        lo, hi = e["_sum"]
        beside = {"kind": "VALUED_PART", "low": _r(lo), "high": _r(hi), "blank_faces": list(e["_blank_faces"]),
                  "basis": "the valued faces of a line with blank faces; never summed, never a quantity"}
        head = (f"HELD BLANK: {len(e['_blank_faces'])} face(s) not measurable from the drawings read "
                f"({', '.join(e['_blank_faces'])}); valued part {_fmt(lo)} .. {_fmt(hi)} {u} beside, never 0")
        return BLANK, None, head, {"blank": True}, beside
    lo, hi = float(e["_sum"][0]), float(e["_sum"][1])
    br = {"low": _r(lo), "high": _r(hi), "basis": f"{e['rule']}: sum of {len(e['_faces'])} face rows; {why}"[:200]}
    head = (f"HELD at the drawn figure {_fmt(lo)} {u} (low = high; held, not released)" if abs(hi - lo) <= 1e-12 else
            f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} {u}")
    head += f": sum of {len(e['_faces'])} face rows, holes once by face"
    return BOUNDED, br, head, {"low": _r(lo), "high": _r(hi)}, None


def _restate_render(b, e, srcs):
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    st, br, head, after, beside = _figure(e)
    why = str(e["why"])[:400]
    ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = st, None, None, br
    ln["deductions"], ln["additions"] = [], []
    ln["rfi"] = {"question": f"open: {e.get('open') or why}"[:400], "blocks": [b["line_id"]]}
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: {head}; {e['rule']}: {why}"[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{b['line_id']}: the formula would conclude on a figure")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=P_RENDER, action="CHANGE", element=e["_element"], was=was, after=after,
                        beside=beside, faces=_face_rec(e), why=why, rule=e["rule"], evidence_status=e["_status"])
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def _new_line(host, e, srcs, code, rule, render_line_id=None):
    from engine.source import boq_line as BL
    st, br, head, after, beside = _figure(e)
    why = str(e["why"])[:400]
    item = RENDER_ITEM if code == RENDER else PAINT_ITEM
    piece = P_RENDER if code == RENDER else P_PAINT
    if code == PAINT:
        head = f"paint = render of the same faces (UP-FIN-PAINT-002), render line {render_line_id}: " + head
    rec = _rec(srcs, piece=piece, action="ADD", element=e["_element"], host_line_id=host["line_id"],
               render_line_id=render_line_id, after=after, beside=beside, faces=_face_rec(e), why=why,
               rule=e["rule"] if code == RENDER else "UP-FIN-PAINT-002", evidence_status=e["_status"])
    loc = host.get("location") or {}
    f = f"{METHOD}: {head}; {rec['rule']}: {why}"[:1500]
    ln = BL.make_line(project_id=host["project"]["project_id"],
                      revision_set_sha256=host["project"]["revision_set_sha256"], item_code=code, unit="m2",
                      evidence_state=st, element_id=e["element_id"], floor=loc.get("floor"), room_id=loc.get("room_id"),
                      physical_element=(f"the {e['_element'].lower().replace('_', ' ')} exterior face band(s), "
                                        f"{'rendered' if code == RENDER else 'painted (Sigma)'}, net of its holes"),
                      bounded_range=br, formula=f, inputs={REC_KEY: rec, "evidence_status": e["_status"]},
                      documents=copy.deepcopy(host["source"]["documents"]),
                      geometry_source=host["source"]["geometry_source"],
                      geometry_confidence=host["source"]["geometry_confidence"], rule_id=rule[0],
                      rule_version=rule[1], material_state="BY_SPEC",
                      rfi={"question": f"open: {e.get('open') or why}"[:400], "blocks": [host["line_id"]]},
                      notes=(f"own face line beside {host['line_id']} (never summed into it); HELD, never 0; NOT "
                             f"RELEASED" if code == RENDER else
                             f"paint of render line {render_line_id} face by face (never summed into it); HELD, never "
                             f"0; NOT RELEASED"), item_en=item[0], item_ar=item[1], trade=item[2],
                      subtrade="EXT_RENDER" if code == RENDER else "EXT_PAINT")
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['element_id']}: the formula would conclude on a figure")
    return A3063._fin(ln)


def _restate_edge(b, e, srcs):
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    lo, hi = float(e["_low"]), float(e["_high"])
    why = str(e["why"])[:400]
    ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
    ln["bounded_range"] = {"low": _r(lo), "high": _r(hi), "basis": f"{e['rule']}: {why}"[:200]}
    head = (f"HELD at the drawn figure {_fmt(lo)} lm (merged edge verdict)" if abs(hi - lo) <= 1e-12 else
            f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} lm (merged edge verdict)")
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: {head}; {e['rule']}: {why}"[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=P_EDGE, action="CHANGE", was=was, after={"low": _r(lo), "high": _r(hi)}, why=why,
                        rule=e["rule"], evidence_status=e["_status"])
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def _assert_before(b, e):
    x, w = e["expect"], f"{e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and line_class(b) == "HELD" and b.get("measured_net") is None)
    r = A3063._view_range(b)
    if ok and x.get("low") is not None:
        ok = r is not None and abs(r[0] - float(x["low"])) <= TOL and abs(r[1] - float(x["high"])) <= TOL
    elif ok:
        ok = r is None
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} {r} "
                          f"is not the ledger's {x} (stale binding: re-read)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"{w}: the line already carries this version's record (applied twice)")


def changes_for(doc, prev):
    """-> (changes, log)."""
    from engine.source import boq_line as BL
    if not doc:
        return [], {"piece": "T314", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.79 records (applied once)")
    if any(ln["item_code"] == PAINT for ln in prev):
        raise InputsError(f"the candidate already carries {PAINT} lines (this version forms them)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, render_after = [], {}
    log = {"piece": "T314", "state": "RUN", "by_piece_action": {}, "lines": 0,
           "statements": len(doc.get("statements") or ()),
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}

    def count(k):
        log["by_piece_action"][k] = log["by_piece_action"].get(k, 0) + 1

    for e in doc["_render"]:
        srcs = [S[t] for t in e["source_tasks"]]
        common = dict(drawing_reference="; ".join(s["file"] for s in srcs), downstream=[],
                      verification=A3036._ver(srcs), evidence_status=e["_status"])
        if e["action"] == "CHANGE":
            b = by.get(e["line_id"])
            _assert_before(b, e)
            after = _restate_render(b, e, srcs)
            host = b
            changes.append(A305._change(P_RENDER, "CHANGE", b, after, group=RENDER, step="CHANGE",
                                        held=[{"what": e["line_id"], "why": str(e["why"])[:300]}], **common))
        else:
            host = by.get(e["host_line_id"])
            if host is None or host["item_code"] != RENDER or element_of(host["location"]["element_id"]) != "STOREY":
                raise InputsError(f"ADD {e['line_id']}: host {e['host_line_id']} is not a storey {RENDER} line")
            want = BL.line_id(host["project"]["project_id"], RENDER, e["element_id"], *ADD_RULE, "m2")
            if want != e["line_id"]:
                raise InputsError(f"ADD {e['line_id']}: the reserved id is not {want} for {e['element_id']}")
            if e["line_id"] in by or any((ln.get("location") or {}).get("element_id") == e["element_id"] and
                                         ln["item_code"] == RENDER for ln in prev):
                raise InputsError(f"ADD {e['line_id']}: the id or element is already a candidate line (collision)")
            after = _new_line(host, e, srcs, RENDER, ADD_RULE)
            if after["line_id"] != e["line_id"]:
                raise InputsError(f"ADD {e['line_id']}: formed {after['line_id']}")
            changes.append(A305._change(P_RENDER, "ADD", None, after, group=RENDER, step="ADD",
                                        held=[{"what": e["line_id"], "why": str(e["why"])[:300]}], **common))
        count(f"{P_RENDER}:{e['action']}")
        render_after[e["line_id"]] = after
        p = _new_line(host if e["action"] == "ADD" else b, e, srcs, PAINT, PAINT_RULE, render_line_id=e["line_id"])
        if p["line_id"] in by:
            raise InputsError(f"paint of {e['line_id']}: id collision")
        changes.append(A305._change(P_PAINT, "ADD", None, p, group=PAINT, step="ADD",
                                    held=[{"what": p["line_id"], "why": "paint = render (UP-FIN-PAINT-002)"}],
                                    **dict(common, evidence_status=e["_status"])))
        count(f"{P_PAINT}:ADD")
    for e in doc["_edges"]:
        srcs = [S[t] for t in e["source_tasks"]]
        b = by.get(e["line_id"])
        _assert_before(b, e)
        after = _restate_edge(b, e, srcs)
        changes.append(A305._change(P_EDGE, "CHANGE", b, after, group=EDGE, step="CHANGE",
                                    held=[{"what": e["line_id"], "why": str(e["why"])[:300]}],
                                    drawing_reference="; ".join(s["file"] for s in srcs), downstream=[],
                                    verification=A3036._ver(srcs), evidence_status=e["_status"]))
        count(f"{P_EDGE}:CHANGE")
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T314-3 (e): only FIN.EXT.FINISH / FIN.EXT.PAINT / FIN.EXT.PAINT.EDGE move, each exactly by the changes; their
    released quantity never moves."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if CODES.get(k.split("|")[0]) != k.split("|")[1])
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside the exterior render / paint codes: {bad}")
    want = expected_totals(t0, changes)
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
        if z is None or a is None:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
        if a["lines"] != z["lines"] or a["bounded_lines"] != z["bounded_lines"] or \
                a["blocked_lines"] != z["blocked_lines"] or \
                any(abs(a[f] - z[f]) > TOT_TOL for f in ("released", "held_low", "held_high")):
            raise ValueError(f"{METHOD}: {k} totals {a} are not the changes' {z}")
        if abs(a["released"] - (t0.get(k) or {}).get("released", 0.0)) > TOT_TOL:
            raise ValueError(f"{METHOD}: {k} released quantity moved")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_79": a}
    return out


def check_lines(lines, before=None):
    """on finished lines: every render line is the sum of its face rows, every face once, one element per line; every
    paint line equals its render line (state and figures) and its render line exists; the edge line is in its state;
    with `before`, no released line moved and no line became RELEASED. -> {piece:action: n}"""
    out, faces, paint_of = {}, {}, {}
    by = {x["line_id"]: x for x in lines}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] == PAINT:
                raise ValueError(f"{METHOD}: {ln['line_id']} a {PAINT} line with no V3.0.79 record")
            continue
        p, a, cls, r = rec["piece"], rec["action"], line_class(ln), A3063._range(ln)
        ok = CODES.get(ln["item_code"]) == ln["unit"] and rec["release_status"] == "NOT RELEASED" and \
            cls == "HELD" and ln.get("measured_net") is None
        if p in (P_RENDER, P_PAINT):
            ok = ok and ln["item_code"] == (RENDER if p == P_RENDER else PAINT)
            lo = sum(f["render"][0] for f in rec["faces"] if f["render"] is not None)
            hi = sum(f["render"][1] for f in rec["faces"] if f["render"] is not None)
            blank = [f["face_id"] for f in rec["faces"] if f["render"] is None]
            ok = ok and all(f["element"] == rec["element"] for f in rec["faces"]) and \
                element_of((ln.get("location") or {}).get("element_id")) == rec["element"]
            if blank:
                bs = rec.get("beside") or {}
                ok = ok and ln["evidence_state"] == BLANK and r is None and bs.get("kind") == "VALUED_PART" and \
                    abs(bs["low"] - lo) <= TOT_TOL and abs(bs["high"] - hi) <= TOT_TOL
            else:
                ok = ok and r is not None and 0 <= r[0] <= r[1] + 1e-9 and r[1] > 0 and abs(r[0] - lo) <= TOT_TOL and \
                    abs(r[1] - hi) <= TOT_TOL
            if p == P_RENDER:
                for f in rec["faces"]:
                    if f["face_id"] in faces:
                        raise ValueError(f"{METHOD}: face {f['face_id']} on two lines")
                    faces[f["face_id"]] = ln["line_id"]
            else:
                rl = by.get(rec.get("render_line_id"))
                ok = ok and rl is not None and rl["item_code"] == RENDER and rl["evidence_state"] == \
                    ln["evidence_state"] and A3063._range(rl) == r and \
                    (rl.get("location") or {}).get("element_id") == (ln.get("location") or {}).get("element_id") and \
                    rec["render_line_id"] not in paint_of
                paint_of[rec.get("render_line_id")] = ln["line_id"]
        elif p == P_EDGE:
            ok = ok and ln["item_code"] == EDGE and r is not None and 0 < r[0] <= r[1] + 1e-9
        else:
            ok = False
        ok = ok and bool((ln.get("rfi") or {}).get("question"))
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {p} {a} line is not in its state")
        out[f"{p}:{a}"] = out.get(f"{p}:{a}", 0) + 1
    rend = [x["line_id"] for x in lines if (((x.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {})
            .get("piece") == P_RENDER]
    if set(rend) != set(paint_of):
        raise ValueError(f"{METHOD}: a render line without its paint line or a paint line without its render line")
    if before is not None:
        old = {x["line_id"]: x for x in before}
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None:
                continue
            if (line_class(ln) == "RELEASED") != (line_class(o) == "RELEASED") or \
                    (line_class(o) == "RELEASED" and o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released quantity moved or a line became released")
    return out


def census(lines, codes=tuple(CODES)):
    """per code: released n / qty, bounded n / low .. high (points apart), blank n with the valued parts beside (run
    record only, never summed), excluded n."""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if c not in codes:
            continue
        z = out.setdefault(c, {"unit": ln["unit"], "lines": 0, "released": 0, "released_q": 0.0, "bounded": 0,
                               "points": 0, "low": 0.0, "high": 0.0, "blank": 0, "valued_part_run_record_only":
                                   [0.0, 0.0], "excluded": 0})
        z["lines"] += 1
        k = line_class(ln)
        r = A3063._range(ln)
        if k == "EXCLUDED":
            z["excluded"] += 1
        elif k == "RELEASED":
            z["released"] += 1
            z["released_q"] += float(ln["measured_net"])
        elif r is not None:
            z["bounded"] += 1
            z["points"] += 1 if abs(r[1] - r[0]) <= 1e-12 else 0
            z["low"] += r[0]
            z["high"] += r[1]
        else:
            z["blank"] += 1
            bs = ((((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}).get("beside") or {})
            if bs.get("kind") == "VALUED_PART":
                z["valued_part_run_record_only"][0] += bs["low"]
                z["valued_part_run_record_only"][1] += bs["high"]
    for z in out.values():
        for f in ("released_q", "low", "high"):
            z[f] = round(z[f], 6)
        z["valued_part_run_record_only"] = [round(x, 6) for x in z["valued_part_run_record_only"]]
    return out


# ================================================================================================ integrate / write
def older_view(lines, base):
    """the lines as the V3.0.64 .. V3.0.78 state checks see them: a line this version changed in its V3.0.78 form (the
    base line of the same id), the lines this version added left out (no older check reads FIN.EXT.FINISH /
    FIN.EXT.PAINT; V3.0.77's edge check runs on the lines as they are); then V3.0.78's own view."""
    b = {ln["line_id"]: ln for ln in base}
    view = []
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            view.append(ln)
        elif rec["action"] == "CHANGE":
            view.append(b[ln["line_id"]])
    return A3078.older_view(view)


def integrate(prev, changes, for_lead=()):
    """-> (V3.0.79 lines, identity). Changed lines replace their candidate line in place, added lines follow the base;
    every other candidate line byte-identical (asserted); the earlier state checks re-run."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if CODES.get(a["item_code"]) != a["unit"]:
            raise ValueError(f"{METHOD}: {a['item_code']} {a['unit']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl or a["item_code"] == PAINT:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if a["line_id"] in sid or a["item_code"] == EDGE:
                raise ValueError(f"{METHOD}: only render / paint face lines are added, never over a candidate id")
            add.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + add
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    v, pv = older_view(out, prev), A3078.older_view(prev)
    if len(v) != len(pv) or any(A30.line_sha(x) != A30.line_sha(y) for x, y in zip(v, pv)):
        raise ValueError(f"{METHOD}: the older-check view is not the base")
    ident = {"base_lines": len(prev), "v3_0_79_lines": len(out), "v3_0_79_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_64": A3064.check_concrete(v),
             "concrete_v3_0_65": A3065.check_concrete(v), "concrete_v3_0_66": A3066.check_concrete(v),
             "concrete_v3_0_67": A3067.check_concrete(v, pv), "lintels_v3_0_67": A3067.check_lintels(v),
             "masonry_v3_0_68": A3068.check_masonry(v), "finishes_v3_0_69": A3069.check_finishes(v),
             "concrete_v3_0_70": A3070.check_concrete(v, pv), "lintels_v3_0_71": A3071.check_lintels(v, pv),
             "masonry_v3_0_72": A3072.check_masonry(v, pv), "concrete_v3_0_73": A3073.check_concrete(v, pv),
             "finishes_v3_0_74": A3074.check_finishes(v, pv), "formwork_concrete_v3_0_75":
                 A3075.check_lines(v, pv), "beads_ceiling_v3_0_76": A3076.check_lines(v, pv),
             "paint_rule_v3_0_77": A3077.check_lines(out, prev), "tile_stair_v3_0_78": A3078.check_lines(out, prev),
             "ext_render_paint": check_lines(out, prev),
             "older_checks_view_is_base": True,
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        a = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(a)]) if A30._key(a) in rel else dict(A30._qty(None), state="NOT_IN_RELEASED")
        rec = a["calculation"]["inputs"][REC_KEY]
        loc = a.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": a["line_id"], "item_code": a["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": a["unit"], "element": rec.get("element"),
                     "host_line_id": rec.get("host_line_id"), "render_line_id": rec.get("render_line_id"),
                     "faces": len(rec.get("faces") or ()), "before_released_v2_9": b29,
                     "before_base": A30._qty(c.get("before")), "after_v3_0_79": A30._qty(a),
                     "class": [None if c.get("before") is None else line_class(c["before"]), line_class(a)],
                     "beside": rec.get("beside"), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "rule": rec.get("rule"), "why": rec.get("why"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "faces",
              "v2_9", "base", "v3_0_79", "beside", "class", "rule", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_79")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        b = r.get("beside")
        if not b:
            return "none"
        return f"valued part {_fmt(b['low'])} .. {_fmt(b['high'])} (blank faces {len(b['blank_faces'])})"
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"], "faces": r["faces"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_79": q(r.get("after_v3_0_79")), "beside": bs(r),
                       "class": " -> ".join(str(x) for x in r["class"]), "rule": r.get("rule") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_78"}, v3_0_79=d["v3_0_78"])
            for d in A3078.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_79_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] != "SAME" and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, census_before=census(prev), census_after=census(new))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_79_BOQ_LINES.json": BL.dumps(new),
             "V3_0_79_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_79_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_79_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_79_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_79_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": dict(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "element_of", "census", "check_lines", "check_totals", "expected_totals", "integrate", "older_view",
           "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
