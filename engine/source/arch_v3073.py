"""ARCH_TAKEOFF_V3.0.73 (T-722, lane I, CONCRETE GATE B ROUND 9 integration package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.72 (engine.source.arch_v30, arch_v301 .. arch_v3072), extended with ONE piece built from the
Checker-merged concrete research T-707 (R-T707-1 / -2: column plate transfer, tank columns), T-711 (R-T711-1..3: the
blank concrete tail), T-712 (R-T712-1..3: ground-beam floors) and T-721 (R-T721-1..3: beam blanks, the east dome ring),
as mapped line by line by the merged T-723 readiness (R-T723-1). No released quantity moves:

  CONC_SIDE   a named HELD STR.CONC line is restated by one of:
                NARROW     a HELD BOUNDED line whose merged ledger raises the low end (a slab-top lower bound transferred
                           over ONE plane, R-T707-1): the new low is RECOMPUTED from its terms (least section reading x
                           least drawn height, floored at 6 dp) and asserted equal to the ledger; the high end is kept;
                           the new range lies inside the old one (never widened, never a new high);
                AT_LEAST   a HELD blank line gains its lower-end figure BESIDE it (never in it, never a range, never
                           0): the line stays blank; where an earlier version carries a DIFFERENT lower figure beside
                           the same line, that figure is RESTATED (named in the entry, kept under `superseded`), never
                           added as a second statement; the SAME figure is confirmed, never restated (not an entry);
                NAMED      a HELD blank line with no figure beside gains the exact item that holds it and, where the
                           ledger states one, its measure per unit of the missing datum (information, never a bound,
                           never a quantity); no figure enters the line.

R-T722-1 (every villa; = R-T704-1 (bb) / R-T703-1 (j) where they apply, plus): (a) every entry binds to the line as the
candidate carries it (item, element, unit, HELD, range or blank to 1e-6, the figure already beside it) and stops on a
stale line; (b) a NARROW low is the product of its own terms (min section m2 x min height m, floored at 6 dp,
R-T696-1), inside the old range, the high unchanged; (c) an AT_LEAST figure is > 0 and sits beside a blank line,
never summed into a code total; a different earlier figure on the line is restated only when the entry names it
(value and record), else refused (one live statement per line, R-T723-1 (4)); (d) a NAMED line carries no figure and
is refused where a figure is already beside it (text never removes a figure); (e) only STR.CONC.*|m3 code totals move,
each exactly by the restatement; released never moves; every other line is byte-identical (asserted); (f) a range from
0 is not a bound: no entry may write one.
Files: V3_0_73_BOQ_LINES.json / .csv, V3_0_73_INTEGRATION_LEDGER.json / .csv, V3_0_73_DIFF.csv, V3_0_73_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
from decimal import ROUND_FLOOR, Context, Decimal

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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.73"
EXTENDS = A3072.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T722_ARCH_V3_0_73"
INPUTS_SCHEMA = "URBAN_V3073_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3073_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T722-1", "T-722"
REC_KEY = "concrete_ledger_v3073"
EARLIER_KEYS = A3070.EARLIER_KEYS + (A3070.REC_KEY, A3071.REC_KEY)
P_CS = "CONC_SIDE"
ACTIONS = ("NARROW", "AT_LEAST", "NAMED")
CODE_PREFIX, UNIT = A3063.CODE_PREFIX, A3063.UNIT
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
TOT_TOL = A3063.TOT_TOL
TOL = 1e-6
MAX_Q = A3063.MAX_Q
FIGURE_KINDS = ("AT_LEAST_M3", "AT_MOST_M3")
_CTX = Context(prec=50)                  # local context only (never the process-global precision: F-T648-2)

PIECES = {
    P_CS: {"module": "engine/source/arch_v3073.py (named HELD STR.CONC lines restated from the Checker-merged T-707 / "
                     "T-711 / T-712 / T-721 ledgers as mapped by T-723: column lows raised by a one-plane slab-top "
                     "transfer, lower-end figures beside blank lines, the exact holding item named on blank lines; "
                     "nothing else moves, released m3 never)",
           "policy": "CONCRETE_GATE_B_V9", "rule_id": "R-T707-1/2 / R-T711-1..3 / R-T712-1..3 / R-T721-1..3 "
                                                      "(R-T722-1)",
           "owner_rules": ["UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "UP-CONC-JOINT-001 / R-CONC-OWN-1 (column top = slab top; one owner per joint)",
                           "Q-65 C (parapet: material above the upstand)", "Q-61 C / X6 (section conflicts held with "
                           "both readings)", "R-T704-2 (one geometry per bound)",
                           "ERS s.2-5 (drawn element first; one physical element once)"],
           "owner_manual_method": "member by member: section x storey height (columns), section x run (beams, ground "
                                  "beams, parapets), steps + waist (stairs); a dimension the drawings do not print is "
                                  "held with the designer list (no generic value)",
           "drawing_method": "the merged ledgers: a column low = least section reading x (slab-top lower bound on one "
                             "plane - base) (R-T707-1); a blank member's AT_LEAST = drawn plan area or section x the "
                             "least printed depth / height that must exist (R-T711-1, R-T712-1, R-T721-1), the upper end "
                             "open by the named designer item; a blank member with no positive drawn minimum is named "
                             "with its measure per unit of the missing datum (R-T711-3, R-T712-3, R-T721-2)"},
}
WAITING = dict(A3072.WAITING)
WAITING.pop("T693_F_T689_1", None)           # settled from the drawing by T-707 (R-T707-1) and wired here
WAITING.update({
    "T722_FORMWORK": "the STR.FORMWORK lines of the restated columns follow their column lines in the T-714 formwork "
                     "package; nothing of the formwork moves here",
    "T722_COLUMN_TANK_HIGH": "the 2F tank columns C2 40F / C3 424 keep their high end open (D-44: B15 up / down stand); "
                             "the DOWN / UP-STAND height ceilings 4.25 / 5.27 m are readings, not a bound",
    "T722_BLANK_DESIGNER": "18 lines stay blank with their item named: D-43 lift tie beam, C-ST-3 / S-9 / D-08 stair "
                           "parts, D-35 court ground beams, D-05 / D-26 edge projections (DESIGNER_QUESTIONS.md)",
    "T722_GB_ZERO_LOW": "STR.CONC.GROUND_BEAM boundary G.B at N.G. (T254:GROUND_BEAMS:GROUND:BOUNDARY_GB_NG) carries a "
                        "0 .. 3.5256 range record while BLOCKED_RFI (counted blocked by the code totals): no merged "
                        "ledger restates it; a range from 0 is not a bound (R-T722-1 (f)); it is listed for the Lead",
})


# ================================================================================================ arithmetic
def _d(x, w):
    if isinstance(x, bool) or x is None:
        raise InputsError(f"{w}: not a number ({x!r})")
    try:
        v = Decimal(str(x))
    except Exception:  # noqa: BLE001
        raise InputsError(f"{w}: not a number ({x!r})") from None
    if not v.is_finite():
        raise InputsError(f"{w}: not a number ({x!r})")
    return v


def floor6(x):
    return x.quantize(Decimal("0.000001"), rounding=ROUND_FLOOR, context=_CTX)


def narrow_low(terms, w="NARROW"):
    """R-T722-1 (b): low = least section reading (m2) x least drawn height (m), floored at 6 dp (R-T696-1)."""
    if not isinstance(terms, dict):
        raise InputsError(f"{w}: terms must be a record")
    areas = terms.get("areas_m2")
    if not areas or not isinstance(areas, (list, tuple)):
        raise InputsError(f"{w}: terms.areas_m2 (the section readings) missing")
    a = [_d(x, f"{w} area") for x in areas]
    if any(x <= 0 or x > 4 for x in a):
        raise InputsError(f"{w}: a section {a} outside 0 .. 4 m2 (unit slip: cm2 / mm2 refused)")
    h = _d(terms.get("h_lo_m"), f"{w} h_lo_m")
    if h <= 0 or h > 12:
        raise InputsError(f"{w}: least height {h} outside 0 .. 12 m (unit slip)")
    return floor6(_CTX.multiply(min(a), h))


def figures_beside(ln):
    """the one-sided figures an earlier concrete version carries beside a line: [(record key, kind, value)]"""
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    out = []
    for k in EARLIER_KEYS:
        b = (inp.get(k) or {}).get("beside") or {}
        if b.get("kind") in FIGURE_KINDS and b.get("value") is not None:
            out.append((k, b["kind"], float(b["value"])))
    return out


# ================================================================================================ inputs
def _entry(x, srcs):
    a = x.get("action")
    w = f"{a} {x.get('line_id')}"
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}: V3.0.73 states NARROW, AT_LEAST or NAMED only (released m3 never "
                          f"moves; an upper-end figure is not formed here)")
    if not isinstance(x.get("line_id"), str) or not A3063.LINE_ID_RE.match(x["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(x, srcs, w)
    A3063._need(x, ("expect", "member", "basis", "item", "question"), w)
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    if not str(ex["item_code"]).startswith(CODE_PREFIX) or ex["unit"] != UNIT or ex["class"] != "HELD":
        raise InputsError(f"{w}: {ex['item_code']} {ex['unit']} {ex['class']} is not a HELD STR.CONC.* m3 line")
    e = dict(x)
    af = x.get("after") or {}
    if a == "NARROW":
        if ex.get("low") is None or ex.get("high") is None:
            raise InputsError(f"{w}: NARROW restates a BOUNDED line (expect low / high)")
        lo0, hi0 = float(ex["low"]), float(ex["high"])
        lo = narrow_low(x.get("terms"), w)
        if lo != _d(af.get("low"), f"{w} low"):
            raise InputsError(f"{w}: ledger low {af.get('low')} is not the recomputed {lo} (R-T722-1 (b))")
        hi = _d(af.get("high"), f"{w} high")
        if abs(float(hi) - hi0) > TOL:
            raise InputsError(f"{w}: the high end {hi} moved from {hi0} (NARROW raises the low only)")
        if float(lo) <= 0:
            raise InputsError(f"{w}: a range from 0 is not a bound (R-T722-1 (f))")
        if float(lo) < lo0 - TOL or float(lo) > hi0 + TOL:
            raise InputsError(f"{w}: new low {lo} outside the old range {lo0} .. {hi0} (never widened)")
        if abs(float(lo) - lo0) <= TOL:
            raise InputsError(f"{w}: the low did not move: not an entry (confirm, never restate)")
        e.update(_low=float(lo), _high=hi0)
    elif a == "AT_LEAST":
        if ex.get("low") is not None or ex.get("high") is not None:
            raise InputsError(f"{w}: an AT_LEAST figure sits beside a blank line (expect no range)")
        if af:
            raise InputsError(f"{w}: an AT_LEAST line carries no quantity and no range (blank, figure beside)")
        b = x.get("beside") or {}
        A3063._need(b, ("value", "basis"), f"{w} beside")
        v = _d(b["value"], f"{w} beside")
        if v <= 0 or float(v) > MAX_Q:
            raise InputsError(f"{w}: AT_LEAST {v} outside 0 .. {MAX_Q} m3 (never 0, unit slip)")
        rs = x.get("restates")
        if rs is not None:
            A3063._need(rs, ("record", "value", "why"), f"{w} restates")
            if rs["record"] not in EARLIER_KEYS:
                raise InputsError(f"{w}: restates an unknown record {rs['record']!r}")
        e.update(_value=float(v))
    else:                                               # NAMED
        if ex.get("low") is not None or ex.get("high") is not None or af or x.get("beside") is not None:
            raise InputsError(f"{w}: a NAMED line carries no figure and no range (R-T722-1 (d))")
        if not x.get("why"):
            raise InputsError(f"{w}: why no figure is formed")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3073_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"action" NARROW | AT_LEAST | NAMED, "line_id", "source_tasks", "member", "item", "basis",
                  "question", "expect" {item_code, element_id, unit, class HELD, low, high},
                  NARROW: "terms" {areas_m2, h_lo_m, top_lo_m, kind}, "after" {low, high};
                  AT_LEAST: "beside" {value, basis, hand}, "restates" {record, value, why} (only where an earlier
                  version carries a different figure);
                  NAMED: "why", "per_unit" (information)}],
     "confirm": [{"line_id", "kind" AT_LEAST_M3, "value", "record" (optional)}] (asserted unchanged, not restated),
     "expect_totals": {"<code>|m3": {...}} (optional, asserted on the code totals)}"""
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
    conf = [dict(c) for c in doc.get("confirm") or ()]
    for c in conf:
        if c.get("kind") not in FIGURE_KINDS or not A3063.LINE_ID_RE.match(str(c.get("line_id"))) or \
                c.get("record") not in (None,) + EARLIER_KEYS:
            raise InputsError(f"confirm {c.get('line_id')}: kind / record / line id")
        _d(c.get("value"), f"confirm {c['line_id']}")
    ids = [e["line_id"] for e in ents] + [c["line_id"] for c in conf]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one statement)")
    return dict(doc, _sources=srcs, _entries=ents, _confirm=conf)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_CS, "policy": PIECES[P_CS]["policy"], "tasks": [s["task"] for s in srcs],
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
    if ok and a == "NARROW":
        ok = b["evidence_state"] == BOUNDED and r is not None and abs(r[0] - x["low"]) <= TOL and \
            abs(r[1] - x["high"]) <= TOL
    elif ok:
        ok = b["evidence_state"] == BLANK and r is None
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} {r} "
                          f"is not the ledger's {x} (stale binding: re-read)")
    figs = figures_beside(b)
    if a == "NARROW" and figs:
        raise InputsError(f"{w}: a bounded line with a one-sided figure beside it ({figs}): refused")
    if a == "NAMED" and figs:
        raise InputsError(f"{w}: a figure is already beside the line ({figs}): a name never removes it "
                          f"(R-T722-1 (d))")
    if a == "AT_LEAST":
        rs = e.get("restates")
        if any(k == "AT_MOST_M3" for _r, k, _v in figs):
            raise InputsError(f"{w}: an AT_MOST figure is beside the line ({figs}): not this version's form")
        same = [f for f in figs if abs(f[2] - e["_value"]) <= 1e-9]
        if same:
            raise InputsError(f"{w}: the same figure is already beside ({same}): confirm it, never restate it")
        if figs and (rs is None or len(figs) != 1 or figs[0][0] != rs["record"] or
                     abs(figs[0][2] - float(rs["value"])) > 1e-9):
            raise InputsError(f"{w}: the line carries {figs}; the entry restates {rs}: one live statement per line "
                              f"(R-T722-1 (c))")
        if not figs and rs is not None:
            raise InputsError(f"{w}: the entry restates {rs} but no figure is beside the line (stale binding)")


def _supersede(inp):
    return {k: inp.pop(k) for k in EARLIER_KEYS if k in inp}


def _restate(b, e, srcs):
    a = e["action"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b),
           "beside": [{"record": r, "kind": k, "value": v} for r, k, v in figures_beside(b)]}
    beside, after = None, {}
    if a == "NARROW":
        lo, hi = e["_low"], e["_high"]
        t = e["terms"]
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": lo, "high": hi, "basis": f"{e['member']}: {e['basis']}"[:200]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m3"
        body = (f"low = least section {min(float(x) for x in t['areas_m2']):g} m2 x least height {t['h_lo_m']} m "
                f"(slab top >= {t.get('top_lo_m')} on one plane), floored at 6 dp; high kept")
        after = {"low": lo, "high": hi}
    elif a == "AT_LEAST":
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        beside = {"kind": "AT_LEAST_M3", "value": e["_value"], "basis": str(e["beside"]["basis"])[:400],
                  "hand": str(e["beside"].get("hand") or "")[:600]}
        head = f"HELD, LOWER END ONLY (blank): at least {_fmt(e['_value'])} m3 beside, upper end open"
        body = beside["basis"]
        if e.get("restates"):
            body += f"; restates the earlier figure {_fmt(float(e['restates']['value']))} ({e['restates']['why']})"
        after = {"beside": beside}
    else:                                               # NAMED
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        head = "HELD BLANK, ITEM NAMED: no figure is formed"
        body = str(e["why"])[:400]
        if e.get("per_unit"):
            body += f"; per unit of the missing datum (information, never a bound): {str(e['per_unit'])[:200]}"
    ln["rfi"] = {"question": str(e["question"])[:400], "blocks": [b["line_id"]]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head}; {e['member']}: {body}; held on {e['item']}")[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['line_id']}: the formula would conclude on a figure (write bounds as 'at least')")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    sup = _supersede(inp)
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], item=e["item"], was=was, after=after, beside=beside,
                        terms=e.get("terms"), restates=e.get("restates"), why=e.get("why"),
                        per_unit=e.get("per_unit"), basis=str(e["basis"])[:600], superseded=sup,
                        freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log). Confirm rows are asserted on the candidate line and change nothing."""
    if not doc:
        return [], {"piece": "T722", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.73 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    confirmed = []
    for c in doc["_confirm"]:
        b = by.get(c["line_id"])
        figs = figures_beside(b) if b else []
        if b is None or b["evidence_state"] != BLANK or len(figs) != 1 or \
                (c.get("record") is not None and figs[0][0] != c["record"]) or \
                figs[0][1] != c["kind"] or abs(figs[0][2] - float(c["value"])) > 1e-9:
            raise InputsError(f"confirm {c['line_id']}: the candidate does not carry {c['kind']} {c['value']} under "
                              f"{c.get('record') or 'any record'} (stale binding); it carries {figs}")
        confirmed.append({"line_id": c["line_id"], "kind": c["kind"], "value": float(c["value"]),
                          "record": figs[0][0], "line_sha": A30.line_sha(b)})
    changes = []
    log = {"piece": "T722", "state": "RUN", "by_action": {}, "lines": 0, "confirmed_unchanged": confirmed,
           "restated": [], "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")}
                                       for s in doc["sources"]]}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        _assert_before(b, e)
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        if e.get("restates"):
            log["restated"].append({"line_id": e["line_id"], "from": float(e["restates"]["value"]),
                                    "to": e["_value"]})
        q = A30._qty(after)
        held = [{"what": e["member"], "why": str(e["item"])[:300],
                 "range": [q["low"], q["high"]] if q["low"] is not None else None,
                 "beside": None if e["action"] != "AT_LEAST" else {"at_least_m3": e["_value"]}}]
        changes.append(A305._change(P_CS, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                    codes=[P_CS], group=b["item_code"], step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3065.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T722-1 (e): only STR.CONC.*|m3 code totals move, each exactly by the restatement, released never"""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if not (k.startswith(CODE_PREFIX) and k.endswith(f"|{UNIT}")))
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside STR.CONC.*|m3: {bad}")
    want = expected_totals(t0, changes)
    for k in moved:
        if k not in want:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
    out = {}
    for k, z in want.items():
        a = t1[k]
        ok = a["lines"] == z["lines"] and all(abs(a[f] - z[f]) <= TOT_TOL for f in ("released", "held_low",
                                                                                  "held_high")) and \
            a["bounded_lines"] == z["bounded_lines"] and a["blocked_lines"] == z["blocked_lines"]
        if not ok:
            raise ValueError(f"{METHOD}: {k} totals {t0.get(k)} -> {a} are not the restatement {z}")
        if abs(a["released"] - t0[k]["released"]) > TOT_TOL:
            raise ValueError(f"{METHOD}: {k} released moved {t0[k]['released']} -> {a['released']}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        if k in moved:
            out[k] = {"base": t0.get(k), "v3_0_73": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.73 line is in the state its action names (NARROW: HELD bounded, 0 < low <= high,
    inside its old range, high kept; AT_LEAST: HELD blank with one positive figure beside and no earlier figure left
    live; NAMED: HELD blank, no figure); with `before`, no STR.CONC line became RELEASED and no released quantity
    moved. -> summary"""
    out = {a: 0 for a in ACTIONS}
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        ok = ln["item_code"].startswith(CODE_PREFIX) and ln["unit"] == UNIT and line_class(ln) == "HELD" and \
            ln.get("measured_net") is None and bool((ln.get("rfi") or {}).get("question")) and \
            rec["was"]["class"] == "HELD" and not figures_beside(ln)
        if a == "NARROW":
            r = A3063._range(ln)
            w = rec["was"]["bounded_range"] or {}
            ok = ok and r is not None and 0 < r[0] <= r[1] + 1e-9 and w.get("low") is not None and \
                r[0] >= float(w["low"]) - TOL and abs(r[1] - float(w["high"])) <= TOL and rec.get("beside") is None
        elif a == "AT_LEAST":
            bs = rec.get("beside") or {}
            ok = ok and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and \
                bs.get("kind") == "AT_LEAST_M3" and float(bs.get("value") or 0) > 0
        elif a == "NAMED":
            ok = ok and ln["evidence_state"] == BLANK and ln.get("bounded_range") is None and rec.get("beside") is None
        else:
            ok = False
        if ok and old is not None:
            o = old.get(ln["line_id"])
            ok = o is not None and line_class(o) == "HELD"
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {a} line is not in its state")
        out[a] += 1
    if old is not None:
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None or not ln["item_code"].startswith(CODE_PREFIX):
                continue
            if line_class(ln) == "RELEASED" and (line_class(o) != "RELEASED" or
                                                 o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: released concrete moved (R-T722-1 (e))")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.73 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier state checks re-run: V3.0.64 .. V3.0.67 / V3.0.70 concrete, V3.0.67 /
    V3.0.71 lintels, V3.0.68 / V3.0.72 masonry, V3.0.69 finishes (nothing of theirs may move)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if not a["item_code"].startswith(CODE_PREFIX) or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.73 adds no line)")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    ident = {"base_lines": len(prev), "v3_0_73_lines": len(out), "v3_0_73_rows": len(changes), "replaced": len(repl),
             "added": 0, "concrete_v3_0_64": A3064.check_concrete(out), "concrete_v3_0_65": A3065.check_concrete(out),
             "concrete_v3_0_66": A3066.check_concrete(out), "concrete_v3_0_67": A3067.check_concrete(out, prev),
             "lintels_v3_0_67": A3067.check_lintels(out), "masonry_v3_0_68": A3068.check_masonry(out),
             "finishes_v3_0_69": A3069.check_finishes(out), "concrete_v3_0_70": A3070.check_concrete(out, prev),
             "lintels_v3_0_71": A3071.check_lintels(out, prev), "masonry_v3_0_72": A3072.check_masonry(out, prev),
             "concrete": check_concrete(out, prev),
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def census(lines, codes=None):
    """STR.CONC.* m3 census by code: released (n, m3), bounded (n, low, high), blank (n, with an AT_LEAST / AT_MOST
    figure beside: n and their run-record sum, never summed into anything else), excluded. -> {code: {...}}"""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if not c.startswith(CODE_PREFIX) or ln["unit"] != UNIT or (codes and c not in codes):
            continue
        z = out.setdefault(c, {"lines": 0, "released": 0, "released_m3": 0.0, "bounded": 0, "bounded_low_m3": 0.0,
                               "bounded_high_m3": 0.0, "blank": 0, "blank_with_beside": {},
                               "beside_sum_m3_run_record_only": {}, "excluded": 0})
        z["lines"] += 1
        k = line_class(ln)
        r = A3063._range(ln)
        if k == "EXCLUDED":
            z["excluded"] += 1
        elif k == "RELEASED":
            z["released"] += 1
            z["released_m3"] += float(ln["measured_net"])
        elif r is not None:
            z["bounded"] += 1
            z["bounded_low_m3"] += r[0]
            z["bounded_high_m3"] += r[1]
        else:
            z["blank"] += 1
            rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}
            figs = [(x[1], x[2]) for x in figures_beside(ln)]
            if (rec.get("beside") or {}).get("kind") in FIGURE_KINDS:
                figs.append((rec["beside"]["kind"], float(rec["beside"]["value"])))
            for kind, v in figs:
                kk = kind.replace("_M3", "")
                z["blank_with_beside"][kk] = z["blank_with_beside"].get(kk, 0) + 1
                z["beside_sum_m3_run_record_only"][kk] = z["beside_sum_m3_run_record_only"].get(kk, 0.0) + v
    for z in out.values():
        for f in ("released_m3", "bounded_low_m3", "bounded_high_m3"):
            z[f] = round(z[f], 6)
        z["beside_sum_m3_run_record_only"] = {k: round(v, 6) for k, v in z["beside_sum_m3_run_record_only"].items()}
    return out


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rec = ref["calculation"]["inputs"][REC_KEY]
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "member": rec["member"], "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_73": A30._qty(ref), "class": [rec["was"]["class"], line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "beside": rec.get("beside"),
                     "beside_before": rec["was"].get("beside"), "restates": rec.get("restates"),
                     "terms": rec.get("terms"), "item": rec.get("item"), "per_unit": rec.get("per_unit"),
                     "still_held": c.get("held"), "superseded_record_keys": sorted(rec.get("superseded") or {}),
                     "release_status": "NOT RELEASED", "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_73", "beside", "item", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_73")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        t = f"at least {_fmt(r['beside']['value'])}" if r.get("beside") else "none"
        if r.get("restates"):
            t += f" (restates {_fmt(float(r['restates']['value']))})"
        return t
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_73": q(r.get("after_v3_0_73")), "beside": bs(r), "item": str(r.get("item") or "")[:160],
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_72"}, v3_0_73=d["v3_0_72"])
            for d in A3072.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_73_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    if any(d["vs_base"] == "ADDED" for d in diff):
        raise ValueError(f"{METHOD}: a line was added")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    codes = sorted({c["after"]["item_code"] for c in changes})
    ident = dict(ident, diff=dsum, conc_census_before=census(prev, codes), conc_census_after=census(new, codes))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_73_BOQ_LINES.json": BL.dumps(new),
             "V3_0_73_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_73_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_73_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_73_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_73_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "narrow_low", "figures_beside", "census", "check_concrete", "check_totals", "expected_totals", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
