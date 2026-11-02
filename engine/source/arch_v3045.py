"""ARCH_TAKEOFF_V3.0.45 (T-478, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.43
(engine.source.arch_v30, arch_v301 .. arch_v3043), extended with the CONC.BLINDING package of the Checker-verified
T-445 pieces (merged ab6bd617) in ONE step:

  SPLIT      a valued blinding line that mixes a VERIFIED layer with held pieces is SPLIT, never held whole: the line
             keeps its id and carries ONLY the verified layer (valued, SOURCE_DERIVED, evidence VERIFIED by the named
             Checker verdict); every held piece becomes its own line (BOUNDED_EXPOSURE, the admissible range, the
             blocker named; never 0). The pieces re-add to the former value (asserted to TOL).
  RANGE_FIX  a held blinding line whose admissible range the merged ledger corrects gets that range (state, id,
             measured_net (blank) unchanged; the former range kept in the record).
  NETTING    a held strip line (ground beams) is re-checked against the pit layer by PLAN OVERLAP (F-C-T445-2): the
             record states the overlap area, which reading nets it (merged: strip minus the pit layer) and which is a
             separate layer (own layer at beam level); the range moves only when the merged ledger proves it.
  ADD_HELD   a printed blinding element carried by no line becomes a HELD BLANK line by name (BLOCKED_RFI, no value,
             never 0), with any per-unit bound beside, never in the quantity.

Version: the Lead's merge-order rule (2026-11-02 20:17) lets this package and T-422 build without each other; the
number 3.0.45 is the one free after the READY V3.0.44; whichever merges second rebases on the first merged candidate
(EXTENDS below then names it). The changes touch ONLY STR.CONC.BLINDING lines, so they apply to either base.

R-T478-1 (every villa; integrates R-BLIND-PIECE-1 (T-445) and its Checker findings F-C-T445-1 / F-C-S06-1 /
F-C-T445-2): (a) blinding = printed thickness x the grown plan (outline + the printed projection on the governing
detail) of the member a detail draws it under; no printed thickness -> HELD, no printed projection -> HELD AT_LEAST
(projection 0); (b) one layer where grown pit plans overlap, the overlap owned by the deeper pit (a tie is refused);
(c) the part of a grown plan beyond the plot line is its own HELD piece (0 .. its area x t), never silently in or out;
(d) a strip (ground beam / strap) blinding is netted against the pit layer by plan overlap in the merged reading and
listed as its own layer in the other; the overlap area is stated; (e) a two-tag outline is a CONFLICT of scenarios and
its range runs from the smallest scenario with the plot-line clip applied to the largest without it; (f) a line mixing
VERIFIED and held pieces is SPLIT; (g) a printed element with no line is added HELD BLANK; (h) a reference plate (one
rectangle x t) is never a piece: it is restated term by term (piece terms + the scope RULE_DIFFERENCE remainder).

Nothing else moves: every V3.0.43 line not named by the inputs is byte-identical (asserted); totals move only in
STR.CONC.BLINDING (asserted). Files: V3_0_45_BOQ_LINES.json / .csv, V3_0_45_INTEGRATION_LEDGER.json / .csv,
V3_0_45_DIFF.csv, V3_0_45_PLATE.json, V3_0_45_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re

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
from engine.source import arch_v3035 as A3035
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040
from engine.source import arch_v3041 as A3041
from engine.source import arch_v3042 as A3042
from engine.source import arch_v3043 as A3043

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.45"
EXTENDS = A3043.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T478_ARCH_V3_0_45"
INPUTS_SCHEMA = "URBAN_V3045_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3045_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T478-1", "T-478"
REC_KEY = "blinding_v3045"
BL_CODE = "STR.CONC.BLINDING"
P_SPLIT, P_RANGE, P_NET, P_ADD = "SPLIT", "RANGE_FIX", "NETTING", "ADD_HELD"
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
RANGE_STATE, HELD_STATE = "BOUNDED_EXPOSURE", "BLOCKED_RFI"
VER = "VERIFIED"
PIECE_STATUS = ("VERIFIED", "HELD", "CONFLICT", "AT_LEAST", "UNMEASURED")
TOL = 0.0000015
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
FORMULA_END_RE = A3043.FORMULA_END_RE

PIECES = {
    P_SPLIT: {"module": "engine/source/arch_v3045.py (a mixed blinding line split: the verified layer valued on its "
                        "own id, each held piece its own held line)", "policy": "BLINDING_SPLIT_V1",
              "rule_id": "R-BLIND-PIECE-1 (T-445), R-T478-1 a, b, c, f",
              "owner_rules": ["UP-QTY-STATUS-001 (held is never 0)", "owner 2026-10-24 23:57 (a downgrade cannot "
                              "split a line: the integration does)", "Q-21 C", "RFI register S06 (plot line), S08 "
                              "(FF projection, ESTIMATED label never VERIFIED)"],
              "owner_manual_method": "owner method: blinding under each footing = (L + 2 x printed projection) x "
                                     "(W + 2 x printed projection) x printed thickness, one layer where pits touch",
              "drawing_method": "DXF footing outlines by handle grown by the printed 0.10 projection (mitred), union "
                                "with the overlap owned by the deeper pit, clipped to the plot line, x printed 0.10 "
                                "(T-445 ledger; Checker re-measure of all 24 pits AGREE exactly)"},
    P_RANGE: {"module": "engine/source/arch_v3045.py (a held blinding line's admissible range corrected)",
              "policy": "BLINDING_RANGE_V1", "rule_id": "R-T478-1 c, e (F-C-T445-1, F-C-S06-1)",
              "owner_rules": ["owner 2026-11-02: the F10 / F10 + F / drawn-outline scenarios, each consistent across "
                              "trades", "RFI S02 (two tags), S06 (plot line)", "UP-QTY-STATUS-001"],
              "owner_manual_method": "the held line shows the range the scenarios allow, its low end a bound under "
                                     "every open item",
              "drawing_method": "per scenario: grown plan x t without the clip (high) and with the plot-line clip "
                                "(low), the outline position read from the DXF"},
    P_NET: {"module": "engine/source/arch_v3045.py (strip blinding netted against the pit layer by plan overlap)",
            "policy": "BLINDING_NETTING_V1", "rule_id": "R-T478-1 d (F-C-T445-2)",
            "owner_rules": ["Q-21 C (founding level open: which footing detail governs)", "RFI S09 / S11",
                            "ELEMENT_REGISTER buried structure (each element once)"],
            "owner_manual_method": "ground-beam blinding = strip (b + 2p) x run length x t, not counted again where "
                                   "it lies over a footing's blinding",
            "drawing_method": "ROUTE_G_SCOPE_V1 blinding_scope (REACH): merged low = union(pit layer + strips) - "
                              "union(pit layer) (plan overlap netted); own-layer high = union(strips) - column "
                              "footprints at beam level (a separate layer, no plan overlap inside it)"},
    P_ADD: {"module": "engine/source/arch_v3045.py (a printed blinding element with no line, added HELD BLANK)",
            "policy": "BLINDING_ADD_HELD_V1", "rule_id": "R-T478-1 g",
            "owner_rules": ["UP-QTY-STATUS-001 (never 0)", "MISSION drawing-first (a printed element is a line)"],
            "owner_manual_method": "blinding under the boundary-wall pads = pad count x (pad + projection) x t",
            "drawing_method": "the typical boundary-wall section prints the blinding (t, projection past the toe, "
                              "pad size); the pad count is not printed: HELD BLANK, the per-pad bound beside"},
}
WAITING = dict(A3043.WAITING)
WAITING.update({
    "T478_DOWNGRADE_RECORD": "DG-3521554d2fd011b9 (Checker, LINE_CONTENT_V1 binding on L-98eb2d58) held the whole "
                             "footing-blinding line for its FF piece; after the SPLIT its content no longer exists (the "
                             "line carries the 24 VERIFIED pits only, FF is its own held line): the Checker's "
                             "downgrade check records it resolved by this split; the record file is not edited here "
                             "(T-479 registry / verdict binding refresh)",
    "T478_EARTHWORKS_BOUND_LISTS": "the V3.0.43 earthworks zones name L-98eb2d58 as a displacement line of the pits "
                                   "zone and the FF zone; the two new held lines (FF raft, beyond the plot line) are "
                                   "bound in the next earthworks round (held blank lines, no quantity moves)",
    "T478_GB_NOT_REMEASURED": "the ground-beam blinding range is netted by plan overlap by construction (route G "
                              "REACH low end) and stays HELD on S09 / S11; no Checker re-measure of the strips exists, "
                              "so no value and no range change",
    "T478_STRAPS": "strap blinding L-35382b18 stays HELD at its V3.0.43 range (S07 / D-15: no strap section on any "
                   "sheet); the 0 .. 0.913 ledger is kept beside (F-T347-2)",
    "T478_BW_PAD_COUNT": "boundary-wall base blinding: pad count and spacing not printed (M2, RFI S04): the new line is "
                         "HELD BLANK; per pad at least 1.30 x 0.90 x 0.10 = 0.117 m3 beside; the band between pads is "
                         "not drawn on blinding",
})
ACTIONS = ("SPLIT_VALUE", "SPLIT_ADD", "RANGE_FIX", "NETTING", "ADD_HELD")


# ================================================================================================ pieces (every villa)
def _poly(pts, u):
    from shapely.geometry import Polygon
    if not pts or len(pts) < 3:
        raise InputsError("an outline needs at least three vertices")
    p = Polygon([(float(x) * u, float(y) * u) for x, y in pts])
    if not p.is_valid or p.area <= 0:
        raise InputsError("an outline is not a simple closed polygon")
    return p


def blinding_pieces(pits, plot, members=(), unit_m=1.0):
    """R-T478-1 a - d on plain geometry (any villa). pits: [{"id", "outline": [(x, y)...], "depth" (m, for the
    overlap owner), "t" (printed thickness m or None), "p" (printed projection m or None)}]; plot: [(x, y)...] or None
    (no plot line: nothing beyond); members: [{"id", "strip": [(x, y)...] (the beam / strap plan), "t", "p"}].
    Coordinates in drawing units, unit_m metres per unit. -> {"pits": [...], "layer": {...}, "members": [...]}
    Areas in m2, volumes in m3 (6 dp). A pit with no printed t is HELD (no figure); with t but no printed p it is
    AT_LEAST (p = 0); an equal-depth overlap is refused (no owner)."""
    from shapely.ops import unary_union
    if not isinstance(unit_m, (int, float)) or unit_m <= 0:
        raise InputsError("unit_m must be positive (metres per drawing unit)")
    P = _poly(plot, unit_m) if plot else None
    seen, rows = set(), []
    for f in pits:
        if f.get("id") in seen or not f.get("id"):
            raise InputsError(f"pit {f.get('id')!r}: one id per pit")
        seen.add(f["id"])
        o = _poly(f.get("outline"), unit_m)
        t, p = f.get("t"), f.get("p")
        for k, v in (("t", t), ("p", p)):
            if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or v > 1.0):
                raise InputsError(f"pit {f['id']}: {k} {v!r} is not a thickness / projection in metres")
        if t == 0:
            raise InputsError(f"pit {f['id']}: a printed thickness of 0 is not a blinding (held is never 0)")
        g = o.buffer(p, join_style=2) if p else o
        rows.append({"id": f["id"], "depth": f.get("depth"), "t": t, "p": p, "_g": g,
                     "status": "HELD" if t is None else ("AT_LEAST" if p is None else "MEASURED"),
                     "outline_m2": _r(o.area), "grown_m2": _r(g.area)})
    # overlap owner: the deeper pit keeps it, the shallower one is clipped (D-32 / T-445); a tie is refused
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ov = a["_g"].intersection(b["_g"]).area
            if ov <= 1e-12:
                continue
            if a.get("depth") is None or b.get("depth") is None or a["depth"] == b["depth"]:
                raise InputsError(f"pits {a['id']} / {b['id']} overlap {ov:.6f} m2 with no deeper owner (refused)")
            lo, hi = (a, b) if a["depth"] < b["depth"] else (b, a)
            lo.setdefault("_clip", []).append(hi["_g"])
            lo.setdefault("ceded", []).append({"to": hi["id"], "m2": _r(ov)})
    out, inside_g = [], []
    for r in rows:
        g = r["_g"]
        if r.get("_clip"):
            g = g.difference(unary_union(r["_clip"]))
        ins = g.intersection(P) if P is not None else g
        bey = g.difference(P) if P is not None else g.difference(g)
        rec = {k: v for k, v in r.items() if not k.startswith("_")}
        rec.update(own_m2=_r(g.area), inside_m2=_r(ins.area), beyond_m2=_r(bey.area))
        if r["t"] is not None:
            rec.update(inside_m3=_r(ins.area * r["t"]), beyond_high_m3=_r(bey.area * r["t"]))
            if r["status"] == "MEASURED":
                inside_g.append(g)
        else:
            rec.update(inside_m3=None, beyond_high_m3=None)
        out.append(rec)
    meas = [x for x in out if x["status"] == "MEASURED"]
    layer = {"pits_measured": len(meas), "inside_m2": _r(sum(x["inside_m2"] for x in meas)),
             "inside_m3": _r(sum(x["inside_m3"] for x in meas)), "beyond_m2": _r(sum(x["beyond_m2"] for x in meas)),
             "beyond_high_m3": _r(sum(x["beyond_high_m3"] for x in meas)),
             "held": [x["id"] for x in out if x["status"] == "HELD"],
             "at_least": [x["id"] for x in out if x["status"] == "AT_LEAST"]}
    U = unary_union([r["_g"] for r in rows]) if rows else None
    mem = []
    for m in members:
        s = _poly(m.get("strip"), unit_m)
        t, p = m.get("t"), m.get("p")
        if t is None:
            mem.append({"id": m["id"], "status": "HELD", "why": "thickness not printed", "merged_m3": None,
                        "own_layer_m3": None, "overlap_m2": None})
            continue
        g = s.buffer(p, join_style=2) if p else s
        ov = g.intersection(U).area if U is not None else 0.0
        mem.append({"id": m["id"], "status": "HELD_RANGE", "strip_m2": _r(g.area), "overlap_m2": _r(ov),
                    "merged_m3": _r((g.area - ov) * t), "own_layer_m3": _r(g.area * t),
                    "why": "which detail governs (merged with the pit layer, or its own layer at beam level)"})
    # two members crossing the same pit: the merged reading nets each strip against the pits AND each other once
    if members:
        Gs = [(_poly(m["strip"], unit_m).buffer(m["p"], join_style=2) if m.get("p") else _poly(m["strip"], unit_m))
              for m in members if m.get("t") is not None]
        ts = [m["t"] for m in members if m.get("t") is not None]
        if Gs and len(set(ts)) == 1:
            SU = unary_union(Gs)
            layer["members_merged_m3"] = _r((unary_union([SU, U]).area - (U.area if U is not None else 0)) * ts[0])
            layer["members_own_layer_m3"] = _r(SU.area * ts[0])
            layer["members_overlap_with_pits_m2"] = _r(SU.intersection(U).area if U is not None else 0.0)
    return {"pits": out, "layer": layer, "members": mem}


def plate_terms(plate_m3, terms):
    """R-T478-1 h: a reference plate (one rectangle x t, printed nowhere as blinding) restated term by term. terms:
    [{"term", "low", "high", "cause"}] = the pieces INSIDE the plate's rectangle (engine valued - piece, per end).
    -> the rows + the RULE_DIFFERENCE remainder at both ends; the restatement closes exactly at both ends."""
    if not isinstance(plate_m3, (int, float)) or plate_m3 <= 0:
        raise InputsError("plate figure must be positive m3")
    rows, lo, hi = [], 0.0, 0.0
    for x in terms:
        if x.get("low") is None or x.get("high") is None or x["low"] > x["high"] + 1e-12:
            raise InputsError(f"plate term {x.get('term')}: needs low <= high (a held piece without a range is "
                              f"listed in the remainder by name)")
        rows.append(dict(x))
        lo += x["low"]
        hi += x["high"]
    rd_lo, rd_hi = plate_m3 - hi, plate_m3 - lo        # the remainder is largest when the pieces are smallest
    if rd_lo < -1e-9:
        raise InputsError("the pieces exceed the plate: it is not a plate over these pieces")
    rows.append({"term": "RULE_DIFFERENCE", "low": _r(rd_lo), "high": _r(rd_hi),
                 "cause": "the plate's one layer over the whole rectangle is drawn on no sheet (scope, not a "
                          "measurement error)"})
    return {"plate_m3": _r(plate_m3), "rows": rows, "pieces_low": _r(lo), "pieces_high": _r(hi),
            "closes_low": abs(lo + rd_hi - plate_m3) < 1e-9, "closes_high": abs(hi + rd_lo - plate_m3) < 1e-9}


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False):
    return A3043._num(x, where, pos)


def _tasks(r, srcs, where):
    A3043._tasks(r, srcs, where)


def _expect(x, where):
    e = x.get("expect") or {}
    if not e:
        raise InputsError(f"{where}: expect (the V3.0.43 quantity it replaces) missing")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3045_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "split": [{"line_id", "expect": {"value"}, "verified": {"value", "area_m2", "t", "pieces", "verdict", "basis",
                "physical_element", "source_tasks"},
                "held": [{"key", "element_id", "physical_element", "low", "high", "at_least", "status", "blocker",
                          "basis", "source_tasks"}]}],
     "ranges": [{"line_id", "expect": {"low", "high"}, "low", "high", "scenarios", "basis", "why", "source_tasks"}],
     "netting": [{"line_id", "expect": {"low", "high"}, "overlap", "basis", "why", "source_tasks"}],
     "add": [{"key", "element_id", "physical_element", "floor", "per_unit_at_least", "per_unit", "held_items",
              "basis", "source_tasks"}],
     "plate": {"m3", "basis", "source_tasks", "beside"}}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    named, keys = set(), set()

    def once(lid, w):
        if not LINE_ID_RE.match(str(lid)):
            raise InputsError(f"{w}: {lid!r} is not a BOQ line id")
        if lid in named:
            raise InputsError(f"{w}: line {lid} named twice (one action per line)")
        named.add(lid)

    def key(k, w):
        if not k or k in keys:
            raise InputsError(f"{w}: key {k!r} missing or repeated")
        keys.add(k)

    splits = []
    for s in doc.get("split") or ():
        w = f"split {s.get('line_id')}"
        _need(s, ("line_id", "verified", "held"), w)
        once(s["line_id"], w)
        e = _expect(s, w)
        ev = _num(e.get("value"), f"{w} expect.value", pos=True)
        v = s["verified"]
        _need(v, ("value", "area_m2", "t", "verdict", "basis", "physical_element"), f"{w} verified")
        _tasks(v, srcs, f"{w} verified")
        vv = _num(v["value"], f"{w} verified.value", pos=True)
        a, t = _num(v["area_m2"], f"{w} area", pos=True), _num(v["t"], f"{w} t", pos=True)
        if abs(a * t - vv) > TOL:
            raise InputsError(f"{w}: verified {vv} m3 is not area {a} x t {t} (= {a * t:.7f})")
        held = []
        for h in s["held"]:
            hw = f"{w} held {h.get('key')}"
            _need(h, ("key", "element_id", "physical_element", "status", "blocker", "basis"), hw)
            key(h["key"], hw)
            _tasks(h, srcs, hw)
            if h["status"] not in ("HELD", "AT_LEAST", "CONFLICT"):
                raise InputsError(f"{hw}: status {h['status']} (a split-off piece is held, never VERIFIED here)")
            if "value" in h and h["value"] not in (None, ""):
                raise InputsError(f"{hw}: HELD_WITH_VALUE (a held piece carries a range, never a value)")
            lo, hi = _num(h.get("low"), f"{hw} low"), _num(h.get("high"), f"{hw} high", pos=True)
            if lo > hi:
                raise InputsError(f"{hw}: low {lo} > high {hi}")
            al = h.get("at_least")
            if al not in (None, ""):
                al = _num(al, f"{hw} at_least", pos=True)
                if al > lo + TOL:
                    raise InputsError(f"{hw}: at_least {al} above the range low {lo}")
            held.append(dict(h, _lo=lo, _hi=hi, _al=al if al not in (None, "") else None))
        if not held:
            raise InputsError(f"{w}: a split without a held piece is a re-value, not a split")
        # the pieces re-add to the former value: the verified layer + the held pieces at the ends the former value
        # used (the 'former' figure of each piece), within TOL
        former = [_num(h.get("former"), f"{w} held {h['key']} former") for h in held]
        if abs(vv + sum(former) - ev) > TOL:
            raise InputsError(f"{w}: verified {vv} + held as formerly counted {sum(former):.6f} does not re-add to "
                              f"{ev} (residual {vv + sum(former) - ev:.7f})")
        splits.append(dict(s, _expect=ev, _v=vv, _a=a, _t=t, _held=held))
    ranges = []
    for x in doc.get("ranges") or ():
        w = f"range fix {x.get('line_id')}"
        _need(x, ("line_id", "basis", "why", "scenarios"), w)
        once(x["line_id"], w)
        _tasks(x, srcs, w)
        e = _expect(x, w)
        _num(e.get("low"), f"{w} expect.low")
        _num(e.get("high"), f"{w} expect.high")
        lo, hi = _num(x.get("low"), f"{w} low"), _num(x.get("high"), f"{w} high", pos=True)
        if lo > hi:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        sc = x["scenarios"]
        los = [_num(c.get("clipped_m3"), f"{w} scenario {c.get('name')} clipped") for c in sc]
        his = [_num(c.get("unclipped_m3"), f"{w} scenario {c.get('name')} unclipped", pos=True) for c in sc]
        if abs(min(los) - lo) > TOL or abs(max(his) - hi) > TOL:
            raise InputsError(f"{w}: range {lo} .. {hi} is not min(clipped) {min(los)} .. max(unclipped) {max(his)} "
                              f"of its scenarios (R-T478-1 e)")
        ranges.append(dict(x, _lo=lo, _hi=hi))
    nets = []
    for x in doc.get("netting") or ():
        w = f"netting {x.get('line_id')}"
        _need(x, ("line_id", "basis", "why", "overlap"), w)
        once(x["line_id"], w)
        _tasks(x, srcs, w)
        e = _expect(x, w)
        _num(e.get("low"), f"{w} expect.low")
        _num(e.get("high"), f"{w} expect.high")
        nets.append(dict(x))
    adds = []
    for x in doc.get("add") or ():
        w = f"add {x.get('key')}"
        _need(x, ("key", "element_id", "physical_element", "floor", "held_items", "basis"), w)
        key(x["key"], w)
        _tasks(x, srcs, w)
        if x.get("value") not in (None, ""):
            raise InputsError(f"{w}: HELD_WITH_VALUE (an added element is held blank)")
        pu = x.get("per_unit_at_least")
        if pu not in (None, ""):
            _num(pu, f"{w} per_unit_at_least", pos=True)
            if not x.get("per_unit"):
                raise InputsError(f"{w}: a per-unit bound names its unit (e.g. per pad)")
        adds.append(dict(x))
    pl = doc.get("plate")
    if pl:
        _need(pl, ("m3", "basis"), "plate")
        _tasks(pl, srcs, "plate")
        _num(pl["m3"], "plate m3", pos=True)
    if not (splits or ranges or nets or adds):
        raise InputsError("no blinding action in the inputs")
    return dict(doc, _sources=srcs, _splits=splits, _ranges=ranges, _nets=nets, _adds=adds, _plate=pl)


# ================================================================================================ helpers
def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _base(ln):
    new = copy.deepcopy(ln)
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    return new


def _plain(t):
    return A3043._plain(t)


def _valued(ln, s, srcs):
    v = s["verified"]
    new = _base(ln)
    was = A302._q(A30._qty(ln))
    new["evidence_state"] = "SOURCE_DERIVED"
    new["measured_net"] = s["_v"]
    new["gross"] = s["_v"]
    new["bounded_range"] = None
    new["rfi"] = None
    new["physical_element"] = v["physical_element"]
    split_off = "; ".join(f"{h['key']} {_fmt(h['_lo'])} .. {_fmt(h['_hi'])} ({h['blocker']})" for h in s["_held"])
    new["calculation"]["formula"] = (
        f"{METHOD}: {v['physical_element']} = {_fmt(s['_a'])} m2 (grown plans, one layer, inside the plot line; "
        f"{v['basis']}) x printed t {_fmt(s['_t'])} m = {_fmt(s['_v'])} m3, VERIFIED ({v['verdict']}); split off "
        f"to their own held lines, never in this figure: {split_off}; was {was} (R-T478-1 f)")[:1500]
    new["calculation"]["inputs"][REC_KEY] = _rec(
        P_SPLIT, srcs, action="SPLIT_VALUE", was=was, formula_before=ln["calculation"]["formula"],
        area_m2=s["_a"], t=s["_t"], value_m3=s["_v"], verdict=v["verdict"], pieces=v.get("pieces"),
        split_off=[{"key": h["key"], "low": h["_lo"], "high": h["_hi"], "former": h["former"]} for h in s["_held"]],
        evidence_status=VER)
    new["calculation"]["inputs"]["evidence_status"] = VER
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: SPLIT (R-T478-1 f): VALUED at the Checker-verified layer "
                    f"only ({v['verdict']}); held pieces on their own lines; NOT RELEASED")[:2000]
    return _fin(new)


def _held_line(tpl, h, srcs, parent):
    from engine.source import boq_line as BL
    loc = tpl["location"]
    al = f"; at least {_fmt(h['_al'])} m3" if h["_al"] is not None else ""
    formula = (f"{METHOD}: HELD {h['status']} (never a value) {_plain(h['physical_element'])}: range "
               f"{_fmt(h['_lo'])} .. {_fmt(h['_hi'])} m3{al} | {_plain(h['basis'])} | held by: {_plain(h['blocker'])}"
               f" | split from {parent} (R-T478-1 f)")[:1500]
    if FORMULA_END_RE.search(formula):
        raise InputsError(f"held piece {h['key']}: the formula would conclude on a figure")
    rec = _rec(P_SPLIT, srcs, action="SPLIT_ADD", key=h["key"], parent_line=parent, low=h["_lo"], high=h["_hi"],
               at_least=h["_al"], status=h["status"], blocker=h["blocker"], basis=h["basis"], former=h["former"],
               evidence_status="HELD")
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=BL_CODE, unit="m3", evidence_state=RANGE_STATE, measured_net=None, gross=None,
        bounded_range={"low": h["_lo"], "high": h["_hi"], "basis": f"{h['basis']} ({RULE_ID})"[:300]},
        element_id=h["element_id"], floor=loc.get("floor"), physical_element=h["physical_element"],
        formula=formula, inputs={REC_KEY: rec, "evidence_status": "HELD"},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": f"{h['physical_element']}: {h['blocker']}"[:900], "unlocks": h["element_id"]},
        notes=f"{METHOD}: held piece split from {parent}; NOT RELEASED",
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    return _fin(ln)


def _ranged(ln, x, srcs):
    new = _base(ln)
    br = dict(new.get("bounded_range") or {})
    was = {"low": br.get("low"), "high": br.get("high"), "basis": br.get("basis")}
    br.update({"low": x["_lo"], "high": x["_hi"],
               "basis": f"{x['basis']} (was {_fmt(was['low'])} .. {_fmt(was['high'])}; {RULE_ID})"[:300]})
    new["bounded_range"] = br
    new["calculation"]["inputs"][REC_KEY] = _rec(
        P_RANGE, srcs, action="RANGE_FIX", was=was, low=x["_lo"], high=x["_hi"], why=x["why"],
        scenarios=x["scenarios"], evidence_status=new["calculation"]["inputs"].get("evidence_status") or "HELD")
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: held range {_fmt(was['low'])} .. {_fmt(was['high'])} -> "
                    f"{_fmt(x['_lo'])} .. {_fmt(x['_hi'])} m3 ({x['why']}); state unchanged")[:2000]
    return _fin(new)


def _netted(ln, x, srcs):
    new = _base(ln)
    new["calculation"]["inputs"][REC_KEY] = _rec(
        P_NET, srcs, action="NETTING", overlap=x["overlap"], basis=x["basis"], why=x["why"],
        range_unchanged={"low": (ln.get("bounded_range") or {}).get("low"),
                         "high": (ln.get("bounded_range") or {}).get("high")},
        evidence_status=new["calculation"]["inputs"].get("evidence_status") or "HELD")
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: netted against the pit layer by plan overlap "
                    f"(F-C-T445-2): {x['why']}; range and state unchanged")[:2000]
    return _fin(new)


def _added(tpl, x, srcs):
    from engine.source import boq_line as BL
    pu = x.get("per_unit_at_least")
    bound = (f"bound beside (never the quantity): at least {_fmt(pu)} m3 {x['per_unit']}" if pu not in (None, "")
             else "no bound proved")
    formula = (f"{METHOD}: HELD BLANK (never a value, never 0) {_plain(x['physical_element'])}: {_plain(x['basis'])} "
               f"| held by: {_plain(x['held_items'])} | {bound} (R-T478-1 g)")[:1500]
    if FORMULA_END_RE.search(formula):
        raise InputsError(f"add {x['key']}: the formula would conclude on a figure")
    rec = _rec(P_ADD, srcs, action="ADD_HELD", key=x["key"], per_unit_at_least=pu, per_unit=x.get("per_unit"),
               held_items=x["held_items"], basis=x["basis"], evidence_status="HELD")
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=BL_CODE, unit="m3", evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=x["element_id"], floor=x["floor"], physical_element=x["physical_element"], formula=formula,
        inputs={REC_KEY: rec, "evidence_status": "HELD"}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": f"{x['physical_element']}: {x['held_items']}"[:900], "unlocks": x["element_id"],
             "bound_beside": bound[:300]},
        notes=f"{METHOD}: printed blinding element carried by no line, added HELD BLANK; NOT RELEASED",
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    return _fin(ln)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a candidate line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_SPLIT, P_RANGE, P_NET, P_ADD)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.45 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_SPLIT, P_RANGE, P_NET, P_ADD)), "state": "RUN", "sources": doc["sources"],
           "by_action": {}, "lines_added": 0, "lines_changed": 0, "valued_m3": 0.0}

    def add(piece, action, after, before=None, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise ValueError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        srcs = kw.pop("srcs")
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs), verification=A3043._ver(srcs),
                                    downstream=kw.pop("downstream", []), group=after["item_code"], **kw))

    def line(lid, w):
        ln = by.get(lid)
        if ln is None or ln["item_code"] != BL_CODE or ln["unit"] != "m3":
            raise InputsError(f"{w}: not a {BL_CODE} m3 line of the candidate (stale binding)")
        return ln

    for s in doc["_splits"]:
        w = f"split {s['line_id']}"
        ln = line(s["line_id"], w)
        if ln["evidence_state"] not in VALUED or abs((ln.get("measured_net") or 0) - s["_expect"]) > TOL:
            raise InputsError(f"{w}: {ln['evidence_state']} {ln.get('measured_net')} is not the valued line of "
                              f"{s['_expect']} m3 the merged ledger split (stale binding)")
        vs = [S[t] for t in s["verified"]["source_tasks"]]
        new = _valued(ln, s, vs)
        add(P_SPLIT, "SPLIT_VALUE", new, before=ln, srcs=vs, evidence_status=VER,
            held=[{"what": h["key"], "why": h["blocker"][:300], "range": f"{_fmt(h['_lo'])} .. {_fmt(h['_hi'])}",
                   "scenario": "split to its own held line"} for h in s["_held"]],
            downstream=["concrete roll-up: blinding valued +" + _fmt(s["_v"]) + " m3 (was held whole by the "
                        "downgrade record)", "earthworks: displacement line unchanged in id"])
        log["valued_m3"] = _r(log["valued_m3"] + s["_v"])
        for h in s["_held"]:
            hs = [S[t] for t in h["source_tasks"]]
            nl = _held_line(ln, h, hs, ln["line_id"])
            add(P_SPLIT, "SPLIT_ADD", nl, srcs=hs, evidence_status="HELD",
                held=[{"what": h["key"], "why": h["blocker"][:300], "range": f"{_fmt(h['_lo'])} .. {_fmt(h['_hi'])}",
                       "scenario": h["status"]}],
                downstream=["concrete roll-up: held range of the code +" + f"{_fmt(h['_lo'])} .. {_fmt(h['_hi'])}"])
    for x in doc["_ranges"]:
        w = f"range fix {x['line_id']}"
        ln = line(x["line_id"], w)
        if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None:
            raise InputsError(f"{w}: {ln['evidence_state']} is not a held ranged line")
        br, e = ln.get("bounded_range") or {}, x["expect"]
        if abs((br.get("low") or 0) - e["low"]) > TOL or abs((br.get("high") or 0) - e["high"]) > TOL:
            raise InputsError(f"{w}: held range {br.get('low')} .. {br.get('high')} is not {e['low']} .. {e['high']} "
                              f"(stale binding)")
        srcs = [S[t] for t in x["source_tasks"]]
        add(P_RANGE, "RANGE_FIX", _ranged(ln, x, srcs), before=ln, srcs=srcs, evidence_status="HELD",
            held=[{"what": x["line_id"], "why": x["why"][:300], "range": f"{_fmt(x['_lo'])} .. {_fmt(x['_hi'])}",
                   "scenario": "held range only"}],
            downstream=["concrete roll-up: held range of the code moves; released total unchanged"])
    for x in doc["_nets"]:
        w = f"netting {x['line_id']}"
        ln = line(x["line_id"], w)
        br, e = ln.get("bounded_range") or {}, x["expect"]
        if ln["evidence_state"] != RANGE_STATE or abs((br.get("low") or 0) - e["low"]) > TOL or \
                abs((br.get("high") or 0) - e["high"]) > TOL:
            raise InputsError(f"{w}: not the held range {e['low']} .. {e['high']} (stale binding)")
        srcs = [S[t] for t in x["source_tasks"]]
        add(P_NET, "NETTING", _netted(ln, x, srcs), before=ln, srcs=srcs, evidence_status="HELD",
            held=[{"what": x["line_id"], "why": x["why"][:300], "range": f"{_fmt(e['low'])} .. {_fmt(e['high'])}",
                   "scenario": "record only; range unchanged"}], downstream=["none (record only)"])
    tpl = next((by[s["line_id"]] for s in doc["_splits"]), None) or next(
        (ln for ln in prev if ln["item_code"] == BL_CODE), None)
    for x in doc["_adds"]:
        if tpl is None:
            raise InputsError("no blinding line to template the added line from")
        srcs = [S[t] for t in x["source_tasks"]]
        add(P_ADD, "ADD_HELD", _added(tpl, x, srcs), srcs=srcs, evidence_status="HELD",
            held=[{"what": x["key"], "why": str(x["held_items"])[:300], "range": None, "scenario": "held blank"}],
            downstream=["coverage: the printed element is now a line (held)"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_blinding(lines, before=None):
    """R-T478-1 on the integrated lines: a SPLIT_VALUE line is valued at area x t with evidence VERIFIED and no range;
    every SPLIT_ADD line is BOUNDED_EXPOSURE at its record's range and names an existing parent; every ADD_HELD line is
    BLOCKED_RFI blank; a RANGE_FIX / NETTING line stays held and blank and keeps its rfi, state and id; no held
    blinding line carries a value (held never 0). -> summary."""
    out = {"valued_lines": 0, "valued_m3": 0.0, "split_lines": 0, "added_held": 0, "ranges_fixed": 0, "netted": 0}
    ids = {ln["line_id"] for ln in lines}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        act = rec.get("action")
        if ln["item_code"] != BL_CODE:
            raise ValueError(f"{METHOD}: {act} on a non-blinding line {ln['line_id']}")
        br = ln.get("bounded_range") or {}
        if act == "SPLIT_VALUE":
            if ln["evidence_state"] not in VALUED or ln.get("bounded_range") is not None or \
                    abs(ln["measured_net"] - rec["value_m3"]) > 1e-9 or \
                    abs(rec["area_m2"] * rec["t"] - rec["value_m3"]) > TOL or rec.get("evidence_status") != VER:
                raise ValueError(f"{METHOD}: split line {ln['line_id']} is not valued at its verified layer")
            out["valued_lines"] += 1
            out["valued_m3"] = _r(out["valued_m3"] + ln["measured_net"])
        elif act == "SPLIT_ADD":
            if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None or \
                    abs(br.get("low") - rec["low"]) > 1e-9 or abs(br.get("high") - rec["high"]) > 1e-9 or \
                    rec["high"] <= 0:
                raise ValueError(f"{METHOD}: split-off line {ln['line_id']} is not held at its range")
            if rec.get("parent_line") not in ids:
                raise ValueError(f"{METHOD}: split-off line {ln['line_id']} names no parent in the candidate")
            out["split_lines"] += 1
        elif act == "ADD_HELD":
            if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or \
                    ln.get("bounded_range") is not None or ln.get("gross") is not None:
                raise ValueError(f"{METHOD}: added line {ln['line_id']} is not HELD BLANK")
            out["added_held"] += 1
        elif act in ("RANGE_FIX", "NETTING"):
            if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None:
                raise ValueError(f"{METHOD}: {act} line {ln['line_id']} is not held")
            if act == "RANGE_FIX" and (abs(br.get("low") - rec["low"]) > 1e-9 or abs(br.get("high") - rec["high"])
                                       > 1e-9):
                raise ValueError(f"{METHOD}: re-ranged line {ln['line_id']} is not at its corrected range")
            o = b4.get(ln["line_id"])
            if o is not None:
                keep = ("evidence_state", "measured_net", "gross", "rfi", "item_code", "unit", "location")
                keep = keep + (("bounded_range",) if act == "NETTING" else ())
                for k in keep:
                    if o.get(k) != ln.get(k):
                        raise ValueError(f"{METHOD}: {act} line {ln['line_id']} moved {k}")
            out["ranges_fixed" if act == "RANGE_FIX" else "netted"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act}")
        if FORMULA_END_RE.search(ln["calculation"].get("formula") or "") and act != "SPLIT_VALUE":
            raise ValueError(f"{METHOD}: held line {ln['line_id']} formula concludes on a figure")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.45 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != BL_CODE:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a candidate id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    ident = {"base_lines": len(prev), "v3_0_45_lines": len(out), "v3_0_45_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3043.check_earthworks(out), "blinding": check_blinding(out, prev)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    ident.update(outside_rows=len(outside), outside_rows_identical_to_base=len(outside),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest())
    return out, ident


def plate_restatement(doc, lines):
    """R-T478-1 h on the integrated lines: the reference plate restated term by term from the blinding lines (their
    inside-the-plate part, as the inputs' plate.beside states it), the remainder RULE_DIFFERENCE. -> dict or None."""
    pl = (doc or {}).get("_plate")
    if not pl:
        return None
    by = {ln["line_id"]: ln for ln in lines}
    terms = []
    bykey = {((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY, {}).get("key"): ln for ln in lines
             if ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY, {}).get("key")}
    for t in pl.get("terms") or ():
        if t.get("line_id") or t.get("key"):
            ln = by.get(t["line_id"]) if t.get("line_id") else bykey.get(t["key"])
            if ln is None:
                raise InputsError(f"plate term {t['term']}: line {t.get('line_id') or t.get('key')} not in the "
                                  f"candidate")
            q = A30._qty(ln)
            lo = q["value"] if q["value"] is not None else q["low"]
            hi = q["value"] if q["value"] is not None else q["high"]
            if t.get("inside_low") is not None:      # the part of the line beyond the plate rectangle is not his
                lo, hi = t["inside_low"], t["inside_high"]
            if lo is None:
                continue
            terms.append({"term": t["term"], "line_id": ln["line_id"], "low": lo, "high": hi, "cause": t["cause"],
                          "state": ln["evidence_state"]})
    res = plate_terms(pl["m3"], terms)
    res["basis"], res["beside"] = pl["basis"], pl.get("beside")
    vals = [r for r in res["rows"] if r.get("state") in VALUED]
    res["engine_valued_m3"] = _r(sum(r["low"] for r in vals))
    res["engine_vs_plate_m3"] = _r(res["engine_valued_m3"] - pl["m3"])
    res["engine_vs_plate_pct"] = round(100.0 * res["engine_vs_plate_m3"] / pl["m3"], 2)
    return res


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"].get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_45": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_45", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_45")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_45": q(r.get("after_v3_0_45")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    b = {ln["line_id"]: ln for ln in prev}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in new:
        o = b.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_base": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_45": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=(), doc=None):
    """the V3_0_45_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    moved = {k: {"base": t0.get(k), "v3_0_45": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
    for k in moved:
        if k != f"{BL_CODE}|m3":
            raise ValueError(f"{METHOD}: totals moved outside this version's code: {k}")
    plate = plate_restatement(doc, new)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING, "plate": plate}
    files = {"V3_0_45_BOQ_LINES.json": BL.dumps(new),
             "V3_0_45_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_45_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_45_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_45_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_45_PLATE.json": A30._j(plate),
             "V3_0_45_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "BL_CODE", "blinding_pieces",
           "plate_terms", "load_inputs", "changes_for", "check_blinding", "integrate", "plate_restatement",
           "ledger_rows", "diff_rows", "write", "InputsError"]
