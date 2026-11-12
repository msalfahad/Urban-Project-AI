"""ARCH_TAKEOFF_V3.0.75 (T-729, lane I, FORMWORK GATE B + CONCRETE ROUND 10 integration package, hub H5f + C10): the
SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.74 (engine.source.arch_v30, arch_v301 .. arch_v3074), extended
with TWO pieces built from the Checker-merged formwork / concrete research as mapped line by line by the merged T-730
readiness (R-T730-1, hubs T-729 and C10). No line outside STR.FORMWORK, STR.FORMWORK.STAIR and STR.CONC.* moves:

  FW_WIRE   every named HELD BLANK STR.FORMWORK / STR.FORMWORK.STAIR line takes the ONE live statement of its merged
            ledger (T-714 R-T714-1/-2 restated by T-724 F-V714-1, T-732 R-T732-1 and T-735 R-T735-1/-2; stair T-725
            R-T725-1..3 restated by T-731 R-T731-1):
              RELEASE   a T-638 fix row (R-T714-2): the face measured CALCULATED by the released formwork method and held
                        only for a per-line split / a held framing member that does not change it -> the line is valued
                        at the merged figure (candidate only; the released default never moves); a RELEASE_LOW_END
                        row keeps its HELD companion (the column's joint faces) BESIDE, never summed;
              BOUND     HELD BOUNDED low .. high (0 < low <= high), the sums of the face lows / highs;
              AT_LEAST  HELD blank, the lower-end figure beside (upper end open), never in a code total;
              CAP       HELD blank, the upper-end cap beside (AT_MOST: every face 0 .. x), never a quantity; a 0 cap is
                        refused (R-T730-1 (4)): it would state the quantity as 0;
              NAMED     HELD blank, the holding cause named (OQ-10, member blank, drawn item); no figure.
  CONC_C10  concrete round 10 (R-T724-3 / R-T724-4 / R-T731-1):
              CAP       the STR.CONC line whose held range starts at 0 (a 0 low is no floor) becomes HELD blank with the
                        range's high beside as its AT_MOST cap (gross, DRAWING-CONFIRMED); the code's bounded set loses it;
              AT_LEAST  a lower-end figure beside a blank line is RESTATED where the merged ledger names the earlier figure
                        (rounding R-T696-1), never added as a second statement;
              ADD_NAMED a drawn piece no line carries (R-T724-4) is a NEW HELD blank child line of its member's code,
                        named with its plan area per metre of depth (information, never a bound, never 0).

R-T729-1 (every villa): (a) a line is wired only from a Checker-merged ledger that names it by line id, through the
merged readiness map; where two merged pieces state a line, only the one that DECLARES the restatement is wired (T-735
over T-732 / T-707 / T-714, T-732 over T-714, T-724 over T-714, T-731 over T-725) and the superseded forms are carried
on the record, never summed and never picked by size; (b) every entry binds to the candidate line as the map read it
(item, element, unit, HELD, blank or the named range; for a restated figure the figure beside it) and stops on a stale
line; (c) a BOUND is 0 < low <= high; an AT_LEAST low > 0; a CAP > 0; a figure beside a line never enters a code total;
(d) a RELEASE is allowed only for a fix row of the merged wiring form, on its unchanged HELD blank line, at the merged
CALCULATED figure; its companion stays HELD beside; (e) only STR.FORMWORK|m2, STR.FORMWORK.STAIR|m2 and STR.CONC.*|m3
code totals move, each exactly by the changes; every other line is byte-identical (asserted); the earlier concrete /
lintel / masonry / finish checks re-run on the result; (f) held stays held: nothing here is VERIFIED; blank is never 0.
Files: V3_0_75_BOQ_LINES.json / .csv, V3_0_75_INTEGRATION_LEDGER.json / .csv, V3_0_75_DIFF.csv, V3_0_75_RUN.json.
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
from engine.source import arch_v3046 as A3046
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged formwork / concrete ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.75"
EXTENDS = A3074.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T729_ARCH_V3_0_75"
INPUTS_SCHEMA = "URBAN_V3075_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3075_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T729-1", "T-729"
REC_KEY = "formwork_gate_b_v3075"
CONC_PREFIX = A3063.CODE_PREFIX
FW, FWS = "STR.FORMWORK", "STR.FORMWORK.STAIR"
FW_CODES = (FW, FWS)
P_FW, P_C10 = "FW_WIRE", "CONC_C10"
FW_ACTIONS = ("RELEASE", "BOUND", "AT_LEAST", "CAP", "NAMED")
C10_ACTIONS = ("CAP", "AT_LEAST", "ADD_NAMED")
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
RELEASED_STATE = "PROVISIONAL"           # the valued state of the released CALCULATED formwork lines (181 of 244 on
                                         # V3.0.74; the other 63 SOURCE_DERIVED); never MEASURED / VERIFIED here
TOL = 1e-6
TOT_TOL = 5e-6
MAX_FW = 500.0                           # one formwork line above 500 m2 is a unit slip
MAX_C = A3063.MAX_Q
# concrete records that may carry a one-sided figure beside a STR.CONC line (A3073.figures_beside order, then ours)
CONC_KEYS = tuple(A3073.OTHER_FIGURES) + A3073.EARLIER_KEYS + (A3073.REC_KEY,)
STATUSES = ("DRAWING-CONFIRMED", "HELD")             # WORKFLOW_CONTROLS s.5; never VERIFIED here
D = Decimal

PIECES = {
    P_FW: {"module": "engine/source/arch_v3075.py (the 370 B10-13 formwork lines of the merged T-714 ledger with the "
                     "T-724 / T-732 / T-735 restatements, and the 20 stair formwork lines of T-725 with the T-731 "
                     "restatement, by line id as mapped by T-730: fix rows released, bounds, one-sided figures and caps "
                     "beside, causes named)",
           "policy": "FORMWORK_GATE_B_V1", "rule_id": "R-T714-1/-2, R-T724-1, R-T732-1/-2, R-T735-1/-2, "
                                                    "R-T725-1..3, R-T731-1 (R-T729-1)",
           "owner_rules": ["R-CONC-OWN-1 (stair concrete + formwork = S; one owner per joint)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "R-T696-1 (lows floor, highs round up at 6 dp)",
                           "OQ-10 (below natural ground: formed or earth-cast, designer item)",
                           "ERS s.2-5 (drawn element first; one physical element once)"],
           "owner_manual_method": "contact area of every cast face not cast against earth, blinding, masonry or an "
                                  "earlier pour: column perimeter x clear height, beam sides L x (D - t) + soffit b x "
                                  "L, slab edges and soffits, stair soffits / risers / strings; a dimension the "
                                  "drawings do not print is held with the designer list",
           "drawing_method": "the merged face ledgers (formwork r4 / r5 walk, T-264 / T-308 / T-332) with each member's "
                             "held dimension passed face by face (R-T714-1: INDEPENDENT / TWO_READINGS / SCALED / "
                             "CAP_ONLY / FLOOR_ONLY / DEPENDENT / BLOCK); moved columns floored at P_min x (least "
                             "panel top - base - D_max) (R-T732-1 / R-T735-1); stair faces on the coherent readings "
                             "(R-T731-1)"},
    P_C10: {"module": "engine/source/arch_v3075.py (concrete round 10: the 0 .. x ground-beam range record capped "
                      "blank (R-T724-3), the MS1-L AT_LEAST restated to its floored exact sum (R-T731-1 / R-T696-1), "
                      "four roof-edge projection pieces added as named blank children (R-T724-4))",
            "policy": "CONCRETE_GATE_B_V10", "rule_id": "R-T724-3 / R-T724-4 / R-T731-1 (R-T729-1)",
            "owner_rules": ["UP-QTY-STATUS-001", "R-T696-1", "M4 / Q-28 (boundary columns 'see arch plan': count "
                            "not printed)", "D-05 / D-26 (projection: no section / mark / bars / material)"],
            "owner_manual_method": "member by member: section x run (ground beams, beams), steps + waist (stairs); a "
                                   "count or dimension the drawings do not print is held with the designer list",
            "drawing_method": "boundary ground beam: S-BOUN bands 8.814 m2 / 0.20 = 44.07 m x 0.20 x 0.40 = 3.5256 m3 "
                              "gross less n x 0.024 per boundary column (n not printed): a cap, never a floor; MS1-L "
                              "reading A exact sum floored; projection pieces by their drawn plan outline"},
}
WAITING = dict(A3074.WAITING)
WAITING.pop("T722_FORMWORK", None)           # the column formwork follows its columns here (T-732 / T-735)
WAITING.pop("T722_GB_ZERO_LOW", None)        # capped here (R-T724-3)
WAITING.update({
    "T729_OQ10": "126 formwork lines below natural ground stay HELD blank by name (OQ-10: formed or earth-cast, "
                 "working space / excavation method; one designer item with B1 OQ-13)",
    "T729_CAPS_NOT_SUMMED": "58 STR.FORMWORK and 12 STR.FORMWORK.STAIR caps (AT_MOST) and 42 AT_LEAST figures sit "
                            "beside blank lines: run-record sums only, never added to a code total",
    "T729_COMPANIONS": "4 released column shafts (RELEASE_LOW_END) keep their joint faces HELD beside (T-638 "
                       "companion): no line is opened for them",
    "T729_GB_BOUNDARY_N": "the boundary ground beam's net = 3.5256 - n x 0.024 m3 with the boundary-column count n "
                          "not printed (M4 / Q-28): capped blank until the count is printed",
    "T729_STRIP_CHILDREN": "4 roof-edge projection pieces (D-05 / D-26) are blank children: section, mark, bars and "
                           "material not printed; their formwork faces are not opened",
})


# ================================================================================================ inputs
def _d(x, w, lo=0.0, hi=MAX_FW, zero=False):
    if isinstance(x, bool) or x is None:
        raise InputsError(f"{w}: not a number ({x!r})")
    try:
        v = D(str(x))
    except Exception:  # noqa: BLE001
        raise InputsError(f"{w}: not a number ({x!r})") from None
    if not v.is_finite() or v < D(str(lo)) or v > D(str(hi)) or (v == 0 and not zero):
        raise InputsError(f"{w}: {x!r} outside {'0' if zero else '>0'} .. {hi} (never 0, unit slip)")
    return v


def _entry(x, srcs):
    a, lid = x.get("action"), x.get("line_id")
    w = f"{a} {lid or x.get('child_key')}"
    A3043._tasks(x, srcs, w)
    piece = x.get("piece")
    if piece == P_FW:
        if a not in FW_ACTIONS:
            raise InputsError(f"{w}: formwork action {a!r} (one of {FW_ACTIONS})")
    elif piece == P_C10:
        if a not in C10_ACTIONS:
            raise InputsError(f"{w}: concrete action {a!r} (one of {C10_ACTIONS})")
    else:
        raise InputsError(f"{w}: piece {piece!r}")
    if x.get("status") == "VERIFIED" or x.get("status") not in STATUSES:
        raise InputsError(f"{w}: status {x.get('status')!r} (HELD / DRAWING-CONFIRMED only; never VERIFIED here)")
    e = dict(x)
    if a == "ADD_NAMED":
        A3063._need(x, ("child_key", "host_line_id", "item", "member", "why"), w)
        if lid is not None or not A3063.LINE_ID_RE.match(str(x["host_line_id"])):
            raise InputsError(f"{w}: a child line names its host line, never a line id of its own")
        if any(x.get(k) is not None for k in ("low", "high", "value", "cap")):
            raise InputsError(f"{w}: a named child carries no figure (R-T724-4)")
        return e
    if not isinstance(lid, str) or not A3063.LINE_ID_RE.match(lid):
        raise InputsError(f"{w}: line id")
    A3063._need(x, ("expect", "why"), w)
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    want_unit = "m2" if piece == P_FW else "m3"
    if (piece == P_FW and ex["item_code"] not in FW_CODES) or \
            (piece == P_C10 and not str(ex["item_code"]).startswith(CONC_PREFIX)) or ex["unit"] != want_unit or \
            ex["class"] != "HELD":
        raise InputsError(f"{w}: {ex['item_code']} {ex['unit']} {ex['class']} is not a HELD line of this piece")
    top = MAX_FW if piece == P_FW else MAX_C
    if a == "RELEASE":
        if not x.get("fix") or x.get("kind") not in ("RELEASE", "RELEASE_LOW_END"):
            raise InputsError(f"{w}: a release names its merged fix row (R-T729-1 (d))")
        e["_value"] = _d(x.get("value"), w, hi=top)
        comp = x.get("companion")
        if (x["kind"] == "RELEASE_LOW_END") != bool(comp):
            raise InputsError(f"{w}: a RELEASE_LOW_END row carries its HELD companion; a RELEASE row none")
        if comp:
            if _d(comp.get("low"), f"{w} companion", hi=top) > _d(comp.get("high"), f"{w} companion", hi=top):
                raise InputsError(f"{w}: companion low > high")
    elif a == "BOUND":
        lo, hi = _d(x.get("low"), f"{w} low", hi=top), _d(x.get("high"), f"{w} high", hi=top)
        if lo > hi:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        e.update(_low=lo, _high=hi)
    elif a == "AT_LEAST":
        e["_value"] = _d(x.get("low"), f"{w} low", hi=top)
        if x.get("high") is not None or x.get("cap") is not None:
            raise InputsError(f"{w}: an AT_LEAST line carries no high and no cap")
        rs = x.get("restates")
        if rs is not None:
            A3063._need(rs, ("value", "why"), f"{w} restates")
            _d(rs["value"], f"{w} restates", hi=top)
    elif a == "CAP":
        if x.get("cap") is not None and D(str(x["cap"])) == 0:
            raise InputsError(f"{w}: a cap of 0 states the quantity as 0: refused (R-T730-1 (4))")
        e["_value"] = _d(x.get("cap"), f"{w} cap", hi=top)
        if x.get("low") is not None or x.get("high") is not None:
            raise InputsError(f"{w}: a capped line is blank (cap beside, no range)")
    else:                                               # NAMED
        if any(x.get(k) is not None for k in ("low", "high", "value", "cap")):
            raise InputsError(f"{w}: a NAMED line carries no figure")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3075_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"piece" FW_WIRE | CONC_C10, "action", "line_id" (or "child_key" + "host_line_id" for ADD_NAMED),
                  "source_tasks", "rule", "status", "why", "expect" {item_code, element_id, unit, class HELD, low,
                  high, beside (the figure the candidate carries beside, for a restatement)},
                  RELEASE: "fix", "kind", "value", "basis", "companion" {low, high, why};
                  BOUND: "low", "high"; AT_LEAST: "low", "restates" {value, why}; CAP: "cap"; NAMED: -;
                  ADD_NAMED: "item", "member", "per_unit", "item_code" (optional, else the host's),
                  "faces", "supersedes" (records only)}],
     "expect_totals": {"<code>|<unit>": {...}} (optional)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents = [_entry(x, srcs) for x in doc.get("entries") or ()]
    if not ents:
        raise InputsError("no entry in the inputs")
    ids = [e["line_id"] or f"ADD:{e['child_key']}" for e in ents]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one statement: R-T730-1 (2))")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ figures
def conc_figures(ln):
    """the one-sided m3 figure the LIVE record carries beside a STR.CONC line (A3073 order, then this version)."""
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    r = inp.get(REC_KEY)
    if isinstance(r, dict):
        b = r.get("beside") or {}
        return [(REC_KEY, b["kind"], float(b["value"]))] if b.get("kind") in ("AT_LEAST_M3", "AT_MOST_M3") else []
    return A3073.figures_beside(ln)


def fw_beside(ln):
    """the one-sided m2 figure this version carries beside a formwork line: [(kind, value)] or []"""
    r = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
    b = (r or {}).get("beside") or {}
    return [(b["kind"], float(b["value"]))] if b.get("kind") in ("AT_LEAST_M2", "AT_MOST_M2") else []


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[kw["piece"]]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _assert_before(b, e):
    x, a, w = e["expect"], e["action"], f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and line_class(b) == "HELD" and b.get("measured_net") is None)
    r = A3063._view_range(b)
    if ok and x.get("low") is not None:            # the range the line carries in its record (a BLOCKED_RFI line
        ok = b["evidence_state"] in (BOUNDED, BLANK) and r is not None and abs(r[0] - x["low"]) <= TOL and \
            abs(r[1] - x["high"]) <= TOL              # may carry a 0 .. x record the code totals count blocked)
    elif ok:
        ok = r is None
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} {r} "
                          f"is not the map's {x} (stale binding: re-read)")
    if e["piece"] == P_FW:
        if fw_beside(b):
            raise InputsError(f"{w}: the line already carries this version's record (applied twice)")
        return
    figs = conc_figures(b)
    if a == "CAP":
        if x.get("low") is None or abs(x["low"]) > TOL:
            raise InputsError(f"{w}: CAP restates a range from 0 only (a 0 low is no floor, R-T724-3)")
        if abs(float(e["_value"]) - x["high"]) > TOL or figs:
            raise InputsError(f"{w}: the cap {e['_value']} is not the range's high {x.get('high')} or a figure is "
                              f"beside ({figs})")
    elif a == "AT_LEAST":
        rs = e.get("restates")
        want = (x.get("beside") or {}).get("value")
        if rs is None or len(figs) != 1 or figs[0][1] != "AT_LEAST_M3" or abs(figs[0][2] - float(rs["value"])) > 1e-9 \
                or want is None or abs(float(want) - figs[0][2]) > 1e-9:
            raise InputsError(f"{w}: the line carries {figs}; the entry restates {rs}: one live statement per line")
        if abs(float(e["_value"]) - figs[0][2]) <= 1e-9:
            raise InputsError(f"{w}: the same figure: confirm it, never restate it")


def _supersede(inp):
    return {k: inp.pop(k) for k in CONC_KEYS if k in inp}


def _faces_text(e):
    fs = e.get("faces") or ()
    return f"{len(fs)} face(s): " + ", ".join(f"{f.get('face_id')} {f.get('dep')}" for f in fs[:6]) + \
        (" ..." if len(fs) > 6 else "") if fs else "faces as the merged ledger"


def _restate(b, e, srcs):
    a, piece = e["action"], e["piece"]
    u = b["unit"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b),
           "beside": [{"record": r, "kind": k, "value": v} for r, k, v in
                      (conc_figures(b) if piece == P_C10 else [])]}
    beside, after, companion = None, {}, None
    why = str(e["why"])[:400]
    if a == "RELEASE":
        v = float(e["_value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"], ln["rfi"] = \
            RELEASED_STATE, _r(v), _r(v), None, None
        head = f"VALUED (CALCULATED, merged fix row {e['fix']}) {_fmt(v)} {u}"
        body = str(e.get("basis") or "")[:400]
        if e.get("companion"):
            c = e["companion"]
            companion = {"kind": "HELD_COMPANION_M2", "low": float(c["low"]), "high": float(c["high"]),
                         "why": str(c.get("why") or "")[:300]}
            body += f"; HELD companion beside (joint faces, never summed): {_fmt(companion['low'])} .. " \
                    f"{_fmt(companion['high'])} {u}"
        after = {"value": _r(v)}
    elif a == "BOUND":
        lo, hi = float(e["_low"]), float(e["_high"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi), "basis": f"{e.get('rule')}: {why}"[:200]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} {u}"
        body = _faces_text(e)
        after = {"low": _r(lo), "high": _r(hi)}
    elif a in ("AT_LEAST", "CAP"):
        v = float(e["_value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        kind = ("AT_LEAST_" if a == "AT_LEAST" else "AT_MOST_") + ("M2" if u == "m2" else "M3")
        beside = {"kind": kind, "value": _r(v), "basis": why}
        head = (f"HELD, LOWER END ONLY (blank): at least {_fmt(v)} {u} beside, upper end open" if a == "AT_LEAST" else
                f"HELD BLANK with a cap beside: at most {_fmt(v)} {u} (never a quantity, never 0)")
        body = _faces_text(e) if piece == P_FW else why
        if e.get("restates"):
            body += f"; restates the earlier figure {_fmt(float(e['restates']['value']))} ({e['restates']['why']})"
        after = {"beside": beside}
    else:                                               # NAMED
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        head = "HELD BLANK, CAUSE NAMED: no figure is formed"
        body = _faces_text(e)
    if a != "RELEASE":
        ln["rfi"] = {"question": f"open: {why}"[:400], "blocks": [b["line_id"]]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head}; {e.get('rule')}: {body}; held on: {why}" if a != "RELEASE" else
        f"{METHOD}: {head}: {body}")[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['line_id']}: the formula would conclude on a figure (write bounds as 'at least')")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    sup = _supersede(inp) if piece == P_C10 else {}
    inp[REC_KEY] = _rec(srcs, piece=piece, action=a, was=was, after=after, beside=beside, companion=companion,
                        restates=e.get("restates"), fix=e.get("fix"), why=why, rule=e.get("rule"),
                        evidence_status=e["status"], faces=e.get("faces"), supersedes=e.get("supersedes"),
                        superseded=sup)
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); "
                   f"{'CANDIDATE ONLY (the released default never moves)' if a == 'RELEASE' else 'NOT RELEASED'}")
    return A3063._fin(ln)


def _child_line(host, e, srcs):
    from engine.source import boq_line as BL
    code = e.get("item_code") or host["item_code"]
    if not code.startswith(CONC_PREFIX) or host["unit"] != "m3":
        raise InputsError(f"ADD_NAMED {e['child_key']}: host {host['line_id']} is not a STR.CONC m3 line")
    loc = host.get("location") or {}
    eid = f"T729:CHILD:{(loc.get('element_id') or '').split('#')[0]}#{e['child_key']}"
    why = str(e["why"])[:400]
    rec = _rec(srcs, piece=P_C10, action="ADD_NAMED", host_line_id=host["line_id"], member=e["member"],
               item=e["item"], per_unit=e.get("per_unit"), why=why, rule=e.get("rule"), evidence_status=e["status"],
               record_slivers_m2=e.get("record_slivers_m2"))
    pu = str(e.get("per_unit") or "")[:200].replace("=", "gives")
    f = (f"{METHOD}: drawn piece no line carries (R-T724-4), child of {e['member']} = HELD blank (never 0): "
         f"{why}; per unit of the missing depth (information, never a bound): {pu}")
    ln = BL.make_line(project_id=host["project"]["project_id"],
                      revision_set_sha256=host["project"]["revision_set_sha256"], item_code=code, unit="m3",
                      evidence_state=BLANK, element_id=eid, floor=loc.get("floor"),
                      physical_element=f"projection piece of {e['member']}"[:200], formula=f[:1500],
                      inputs={REC_KEY: rec, "evidence_status": e["status"]},
                      documents=copy.deepcopy(host["source"]["documents"]),
                      geometry_source=host["source"]["geometry_source"],
                      geometry_confidence=host["source"]["geometry_confidence"], rule_id=RULE_ID,
                      rule_version=RULE_VERSION, material_state="PROJECT_OWNER_FACT",
                      rfi={"question": f"open: {e['item']}"[:400], "blocks": [host["line_id"]]},
                      notes=f"child of {host['line_id']} (never summed into it); HELD blank, never 0; NOT RELEASED")
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"ADD_NAMED {e['child_key']}: the formula would conclude on a figure")
    return A3046._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T729", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.75 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T729", "state": "RUN", "by_piece_action": {}, "lines": 0,
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        srcs = [S[t] for t in e["source_tasks"]]
        k = f"{e['piece']}:{e['action']}"
        log["by_piece_action"][k] = log["by_piece_action"].get(k, 0) + 1
        if e["action"] == "ADD_NAMED":
            h = by.get(e["host_line_id"])
            if h is None or line_class(h) != "HELD":
                raise InputsError(f"ADD_NAMED {e['child_key']}: host {e['host_line_id']} is not a HELD candidate line")
            after = _child_line(h, e, srcs)
            if after["line_id"] in by:
                raise InputsError(f"ADD_NAMED {e['child_key']}: the child id is already a candidate line")
            changes.append(A305._change(e["piece"], "ADD", None, after, drawing_reference="; ".join(
                s["file"] for s in srcs), held=[{"what": e["member"], "why": e["item"], "range": None}],
                downstream=[], verification=A3036._ver(srcs), evidence_status=e["status"], group=after["item_code"],
                step=e["action"]))
            continue
        b = by.get(e["line_id"])
        _assert_before(b, e)
        after = _restate(b, e, srcs)
        q = A30._qty(after)
        held = [] if e["action"] == "RELEASE" else [{"what": e["line_id"], "why": str(e["why"])[:300],
                                                      "range": [q["low"], q["high"]] if q["low"] is not None else None,
                                                      "beside": (after["calculation"]["inputs"][REC_KEY] or {}).get(
                                                          "beside")}]
        changes.append(A305._change(e["piece"], "CHANGE", b, after, drawing_reference="; ".join(
            s["file"] for s in srcs), held=held, downstream=[], verification=A3036._ver(srcs),
            evidence_status=e["status"], group=b["item_code"], step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def _code_ok(k):
    code, unit = k.split("|")
    return (code in FW_CODES and unit == "m2") or (code.startswith(CONC_PREFIX) and unit == "m3")


def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T729-1 (e): only STR.FORMWORK / STR.FORMWORK.STAIR m2 and STR.CONC.* m3 totals move, each exactly by the
    changes; a STR.CONC released quantity never moves."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if not _code_ok(k))
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside the formwork / concrete codes: {bad}")
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
        if k.startswith(CONC_PREFIX) and abs(a["released"] - (t0.get(k) or {}).get("released", 0.0)) > TOT_TOL:
            raise ValueError(f"{METHOD}: {k} released concrete moved")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_75": a}
    return out


def check_lines(lines, before=None):
    """on finished lines: every V3.0.75 line is in the state its action names; with `before`, no line outside the
    formwork codes became RELEASED and no released concrete moved. -> {piece:action: n}"""
    out = {}
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a, p = rec["action"], rec["piece"]
        cls = line_class(ln)
        r = A3063._range(ln)
        bs = rec.get("beside") or {}
        if a == "RELEASE":
            ok = p == P_FW and cls == "RELEASED" and ln["item_code"] in FW_CODES and r is None and \
                float(ln["measured_net"]) > 0 and rec["was"]["class"] == "HELD"
        elif a == "BOUND":
            ok = cls == "HELD" and r is not None and 0 < r[0] <= r[1] + 1e-9 and not bs
        elif a in ("AT_LEAST", "CAP"):
            ok = cls == "HELD" and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and \
                float(bs.get("value") or 0) > 0 and bs.get("kind", "").startswith(
                    "AT_LEAST" if a == "AT_LEAST" else "AT_MOST")
        elif a in ("NAMED", "ADD_NAMED"):
            ok = cls == "HELD" and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and not bs and \
                ln.get("measured_net") is None
        else:
            ok = False
        ok = ok and (p == P_FW) == (ln["item_code"] in FW_CODES) and rec["release_status"] == "NOT RELEASED"
        if ok and a != "RELEASE":
            ok = bool((ln.get("rfi") or {}).get("question"))
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {p} {a} line is not in its state")
        out[f"{p}:{a}"] = out.get(f"{p}:{a}", 0) + 1
    if old is not None:
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None or ln["item_code"] in FW_CODES:
                continue
            if line_class(ln) == "RELEASED" and (line_class(o) != "RELEASED" or
                                                 o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released quantity outside formwork moved")
    return out


def census(lines, codes=FW_CODES + ("STR.CONC.GROUND_BEAM", "STR.CONC.STAIR", "STR.CONC.BEAM")):
    """per code: released n / qty, bounded n / low .. high, blank n with the figures beside (AT_LEAST / AT_MOST: n and
    run-record sums, never summed into anything else), excluded n."""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if c not in codes:
            continue
        z = out.setdefault(c, {"unit": ln["unit"], "lines": 0, "released": 0, "released_q": 0.0, "bounded": 0,
                               "low": 0.0, "high": 0.0, "blank": 0, "beside_n": {}, "beside_sum_run_record_only": {},
                               "excluded": 0})
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
            z["low"] += r[0]
            z["high"] += r[1]
        else:
            z["blank"] += 1
            figs = fw_beside(ln) if c in FW_CODES else [(kk, v) for _r0, kk, v in conc_figures(ln)]
            for kind, v in figs:
                z["beside_n"][kind] = z["beside_n"].get(kind, 0) + 1
                z["beside_sum_run_record_only"][kind] = z["beside_sum_run_record_only"].get(kind, 0.0) + v
    for z in out.values():
        for f in ("released_q", "low", "high"):
            z[f] = round(z[f], 6)
        z["beside_sum_run_record_only"] = {k: round(v, 6) for k, v in z["beside_sum_run_record_only"].items()}
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.75 lines, identity). Changed lines replace their candidate line in place, added children follow the
    base; every other candidate line byte-identical (asserted); the earlier state checks re-run."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if not ((a["item_code"] in FW_CODES and a["unit"] == "m2") or
                (a["item_code"].startswith(CONC_PREFIX) and a["unit"] == "m3")):
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if c["piece"] != P_C10 or a["line_id"] in sid:
                raise ValueError(f"{METHOD}: only named concrete children are added, never over a candidate id")
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
    ident = {"base_lines": len(prev), "v3_0_75_lines": len(out), "v3_0_75_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_64": A3064.check_concrete(out),
             "concrete_v3_0_65": A3065.check_concrete(out), "concrete_v3_0_66": A3066.check_concrete(out),
             "concrete_v3_0_67": A3067.check_concrete(out, prev), "lintels_v3_0_67": A3067.check_lintels(out),
             "masonry_v3_0_68": A3068.check_masonry(out), "finishes_v3_0_69": A3069.check_finishes(out),
             "concrete_v3_0_70": A3070.check_concrete(out, prev), "lintels_v3_0_71": A3071.check_lintels(out, prev),
             "masonry_v3_0_72": A3072.check_masonry(out, prev), "concrete_v3_0_73": A3073.check_concrete(out, prev),
             "finishes_v3_0_74": A3074.check_finishes(out, prev), "formwork_concrete": check_lines(out, prev),
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
                     "element_id": loc.get("element_id"), "unit": a["unit"], "host_line_id": rec.get("host_line_id"),
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_75": A30._qty(a), "class": [None if c.get("before") is None else
                                                            line_class(c["before"]), line_class(a)],
                     "beside": rec.get("beside"), "companion": rec.get("companion"), "restates": rec.get("restates"),
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "rule": rec.get("rule"), "fix": rec.get("fix"), "why": rec.get("why"),
                     "supersedes": rec.get("supersedes"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_75", "beside", "class", "rule", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_75")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        b = r.get("beside")
        t = "none" if not b else f"{'at least' if b['kind'].startswith('AT_LEAST') else 'at most'} {_fmt(b['value'])}"
        if r.get("companion"):
            t += f"; companion HELD {_fmt(r['companion']['low'])} .. {_fmt(r['companion']['high'])}"
        if r.get("restates"):
            t += f" (restates {_fmt(float(r['restates']['value']))})"
        return t
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_75": q(r.get("after_v3_0_75")), "beside": bs(r),
                       "class": " -> ".join(str(x) for x in r["class"]), "rule": r.get("rule") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_74"}, v3_0_75=d["v3_0_74"])
            for d in A3074.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_75_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    files = {"V3_0_75_BOQ_LINES.json": BL.dumps(new),
             "V3_0_75_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_75_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_75_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_75_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_75_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": list(FW_CODES) + [CONC_PREFIX + "*"]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "conc_figures", "fw_beside", "census", "check_lines", "check_totals", "expected_totals", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
