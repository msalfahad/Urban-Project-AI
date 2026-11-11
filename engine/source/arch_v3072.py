"""ARCH_TAKEOFF_V3.0.72 (T-703, lane I, MASONRY GATE B ROUND 4 integration package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.71 (engine.source.arch_v30, arch_v301 .. arch_v3071), extended with TWO pieces built from the
Checker-merged masonry research T-696 (R-T696-1 BOUND_ROUNDING_V1, the blank B9 census) and T-713 (R-T713-1
PARENT_ONE_END_V1); no concrete, finish or other line moves:

  ONE_SIDED     a named HELD blank masonry line (MAS.BLOCK parent, MAS.UNITS.BLACK, MAS.MORTAR.BLACK, MAS.GLUE.AAC)
                gains its one-ended figure BESIDE it (never in it): AT_MOST (the host's area at its drawn physical
                maximum, e.g. the roof build-up b_r >= 0 or an unlabelled member depth >= 0) or AT_LEAST (only from
                components with a positive drawn minimum, and for a material only of the colour that minimum is).
                The figure is RECOMPUTED here: a parent's area from its components (every component must have an upper
                end for an AT_MOST; only positive drawn lower ends for an AT_LEAST), a material as area x its rate
                (12.5 black units per m2, Q-75 / Q-80; laying mortar per m2 at the wall thickness, T-670; AAC glue
                3.5 / 4.5 kg per m2, owner 2026-11-02), AT_MOST rounded UP and AT_LEAST DOWN at 6 dp (R-T696-1), and
                asserted equal to the merged ledger. The line stays HELD blank; nothing is summed.
  BOUND_ROUNDING  a HELD BOUNDED B9 line whose printed range does not contain its exact interval (half-way rounding of
                each end, or a sum of half-way-rounded components) has its range restated with R-T696-1: the low
                rounded toward minus infinity, the high toward plus infinity, from the exact decimal ends RECOMPUTED
                from the line's own inputs (material base x rate, bearing x factor, drawn + held bands + held pieces)
                and asserted equal to the merged ledger. A line whose print already contains its exact interval stays
                byte-identical.

R-T703-1 (every villa; = R-T672-1 (a) .. (f) where they apply, plus): (g) a one-ended figure of a blank masonry line is
recomputed at wiring time from its own terms and stated beside the line with its kind (AT_MOST / AT_LEAST), never a
range, never a point, never 0, never summed into a code total; (h) a parent's AT_MOST exists only when every component
has an upper end, its AT_LEAST only from positive drawn minima; a material line is never firmer than its host (an
AT_LEAST material only for the colour of the minimum; white units and the perimeter joint get no figure without a count
rule or piece ends); (i) a printed bound contains the exact quantity: low DOWN, high UP at 6 dp (R-T696-1), from exact
inputs, never from rounded components; (j) a line already carrying a one-sided figure is refused for restatement; a
line in two pieces is refused (one line, one statement).
Files: V3_0_72_BOQ_LINES.json / .csv, V3_0_72_INTEGRATION_LEDGER.json / .csv, V3_0_72_DIFF.csv, V3_0_72_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re
from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3058 as A3058
from engine.source import arch_v3059 as A3059
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3064 as A3064
from engine.source import arch_v3065 as A3065
from engine.source import arch_v3066 as A3066
from engine.source import arch_v3067 as A3067
from engine.source import arch_v3068 as A3068
from engine.source import arch_v3069 as A3069
from engine.source import arch_v3070 as A3070
from engine.source import arch_v3071 as A3071

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged masonry ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.72"
EXTENDS = A3071.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T703_ARCH_V3_0_72"
INPUTS_SCHEMA = "URBAN_V3072_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3072_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T703-1 (R-T696-1 / R-T713-1)", "T-703"
REC_KEY = "masonry_gate_b_v3072"
P_OS, P_BR = "ONE_SIDED", "BOUND_ROUNDING"
KINDS = ("AT_MOST", "AT_LEAST")
BLOCK = A3059.SRC_CODE
U_BLACK, U_WHITE, MORTAR, GLUE = A3059.U_BLACK, A3059.U_WHITE, A3059.MORTAR, A3059.GLUE
PERIM, BED = A3068.PERIM, A3068.BED
OS_CODES = (BLOCK, U_BLACK, MORTAR, GLUE)            # white units: no count rule (Q-60); perimeter: no piece ends
BR_CODES = (U_BLACK, MORTAR, GLUE, PERIM, BED)
UNIT = {BLOCK: "m2", U_BLACK: "pcs", MORTAR: "m3", GLUE: "kg", PERIM: "m3", BED: "m3"}
COLOUR = {U_BLACK: "BLACK", MORTAR: "BLACK", GLUE: "WHITE"}
RATE_KEY = {U_BLACK: "units_black_per_m2", MORTAR: "mortar_black_m3_per_m2", GLUE: "glue_aac_kg_per_m2"}
FORMS = ("BASE_X_RATE", "BEARING_X_F", "DRAWN_PLUS_HELD")
CAUSES = ("DESIGNER ITEM", "OPEN BOUND", "NEEDS OWNER RULE", "METHOD GAP", "MEASURABLE NOW")
BLANK, BOUNDED = A3063.BLANK, A3063.BOUNDED
TOT_TOL = A3068.TOT_TOL
_CTX = Context(prec=50)                  # local context only (never the process-global precision: F-T648-2)
Q6 = Decimal("0.000001")
T_RE = re.compile(r"walls t=(0\.\d+)")
OA = "ASSUMED - OWNER-APPROVED"

PIECES = {
    P_OS: {"module": "engine/source/arch_v3072.py (HELD blank masonry lines given the one-ended figure the "
                     "Checker-merged T-696 / T-713 ledgers state BESIDE them, recomputed from the host area and the rate; "
                     "the line stays blank; no quantity, range or total moves)",
           "policy": "MASONRY_GATE_B_V4", "rule_id": "R-T696-1 / R-T713-1 (R-T703-1)",
           "owner_rules": ["UPC-BLACK-BLOCK-001 1.1.0 (Q-75 / Q-80: 12.5 black blocks per m2, 40 x 20 face, 15 and 20 cm)",
                           "owner 2026-11-02 (AAC glue 25 kg bag: 3.5 kg/m2 at 15 cm, 4.5 kg/m2 at 20 cm)",
                           "Q-78 (black-block mortar 1:4) + owner 2026-10-29 (10 mm joint, PROVISIONAL)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "register: mesh / sharmat never inside the block m2 (separate optional items)",
                           "ERS s.2-5 (drawn element first; a one-ended statement is not a range)"],
           "owner_manual_method": "block m2 = wall length x height (floor to the soffit) less openings, x 12.5 blocks per "
                                  "m2, mortar 1:4, glue by the bag rate; a height not printed is held with a designer "
                                  "request",
           "drawing_method": "the merged T-696 census / T-713 parents: the host area at its drawn physical maximum (roof "
                             "build-up b_r >= 0, member depth >= 0) or its positive drawn minimum (GF-W22 conflict low "
                             "end; MAIN_S h >= 0.70 one leaf), x the rate; one-ended, beside the HELD blank line"},
    P_BR: {"module": "engine/source/arch_v3072.py (HELD BOUNDED B9 lines whose print does not contain the exact interval: "
                     "range restated low DOWN / high UP at 6 dp from the exact ends recomputed from the line's inputs)",
           "policy": "MASONRY_GATE_B_V4", "rule_id": "R-T696-1 BOUND_ROUNDING_V1 (R-T703-1 (i))",
           "owner_rules": ["UP-QTY-STATUS-001 (a range is reported low with low and high with high)"],
           "owner_manual_method": "not a quantity rule: the reporting precision of a held range",
           "drawing_method": "the merged T-696 bounds ledger (T-670 bases, T-675 bearings / bands / pieces, T-372 drawn "
                             "perimeter): exact decimal ends, low floored and high ceiled at 6 dp"},
}
WAITING = dict(A3071.WAITING)
WAITING.update({
    "T703_HELD": "every ONE_SIDED line stays HELD blank: D-39 roof build-up b_r (2F part hosts), D-04 unlabelled member "
                 "depth (2F 0.15 parent), annex datum D-06 / D-17 + GF-W30 + A-GF-01 width (GF 0.15 parent upper end), "
                 "MAIN_S leaf thickness and soffit (AT_LEAST only)",
    "T703_NO_FIGURE": "white units (no AAC count rule, Q-60), the perimeter joint of the 2F / parent hosts (piece ends "
                      "and soffit courses not drawn), the five blank parents (an open component opens the sum) and "
                      "ANNEX_S (D-35): blank with their cause",
    "T703_HOST_M2": "the six 2F roof-datum part host MAS.BLOCK lines keep no m2 figure beside: their materials carry it "
                    "(T-696 states the material base only)",
    "T703_PROCUREMENT": "waste, procurement and bag rounding stay HELD (installed only)",
})


# ================================================================================================ arithmetic
def _d(x, w):
    if x is None or isinstance(x, bool) or not isinstance(x, (int, float, str)):
        raise InputsError(f"{w}: {x!r} is not a number (a missing input is never 0)")
    v = Decimal(repr(x)) if isinstance(x, float) else Decimal(x)
    if not v.is_finite():
        raise InputsError(f"{w}: not finite")
    return v


def _mul(a, b):
    return _CTX.multiply(a, b)


def _add(*xs):
    out = Decimal(0)
    for x in xs:
        out = _CTX.add(out, x)
    return out


def up6(x):
    return x.quantize(Q6, rounding=ROUND_CEILING)


def down6(x):
    return x.quantize(Q6, rounding=ROUND_FLOOR)


def directed(kind, x):
    """R-T696-1: an upper end rounds UP, a lower end DOWN, at 6 dp."""
    return up6(x) if kind == "AT_MOST" else down6(x)


def host_t(host):
    """the wall thickness printed in a host id ('... walls t=0.15 ...'), else None."""
    m = T_RE.search(host or "")
    return m.group(1) if m else None


def parent_area(kind, comps, w="parent"):
    """R-T713-1: -> exact area. AT_MOST = sum of every component's upper end (one open upper end: no AT_MOST);
    AT_LEAST = sum of the positive drawn lower ends (none: no AT_LEAST)."""
    if not isinstance(comps, list) or not comps:
        raise InputsError(f"{w}: no component (an empty parent is no bound)")
    if kind == "AT_MOST":
        if any(c.get("upper") is None for c in comps):
            raise InputsError(f"{w}: a component has no upper end: the parent has no AT_MOST (an open term opens the "
                              f"sum)")
        vals = [_d(c["upper"], f"{w} {c.get('id')} upper") for c in comps]
    else:
        vals = [_d(c["lower"], f"{w} {c.get('id')} lower") for c in comps if c.get("lower") is not None]
        vals = [v for v in vals if v > 0]
        if not vals:
            raise InputsError(f"{w}: no positive drawn minimum: no AT_LEAST")
    if any(v < 0 or v > 1000 for v in vals):
        raise InputsError(f"{w}: a component area outside 0 .. 1000 m2 (unit slip)")
    return _add(*vals)


def material(code, area, rates, t, w="material"):
    """-> (exact, rate): area (m2) x the code's rate at thickness t."""
    rk = RATE_KEY.get(code)
    if rk is None:
        raise InputsError(f"{w}: {code} gets no figure here (white units: no count rule; perimeter: no piece ends)")
    r = (rates or {}).get(rk)
    if code == U_BLACK:
        rate = _d((r or {}).get("value"), f"{w} rate {rk}")
    else:
        rate = _d(((r or {}).get("by_t") or {}).get(t), f"{w} rate {rk} at t={t}")
    if rate <= 0:
        raise InputsError(f"{w}: rate {rate}")
    return _mul(area, rate), rate


# ================================================================================================ inputs
def _os_entry(x, srcs, rates):
    w = f"{P_OS} {x.get('line_id')}"
    if not isinstance(x.get("line_id"), str) or not A3063.LINE_ID_RE.match(x["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(x, srcs, w)
    A3063._need(x, ("item_code", "unit", "kind", "host", "cause", "printed", "exact"), w)
    code, kind = x["item_code"], x["kind"]
    if code not in OS_CODES or x["unit"] != UNIT[code]:
        raise InputsError(f"{w}: {code} {x['unit']} gets no one-ended figure here")
    if kind not in KINDS:
        raise InputsError(f"{w}: kind {kind!r} (AT_MOST or AT_LEAST: one end, never a range or a point)")
    c = x["cause"]
    A3063._need(c, ("class", "ref", "deciding_datum"), w)
    if c["class"] not in CAUSES:
        raise InputsError(f"{w}: cause class {c['class']!r}")
    t = host_t(x["host"])
    if code == BLOCK:
        if x.get("host_line_id") not in (None, x["line_id"]):
            raise InputsError(f"{w}: a MAS.BLOCK parent is its own host")
        exact = parent_area(kind, x.get("components"), w)
        rate = None
    else:
        if not x.get("host_line_id") or x["host_line_id"] == x["line_id"]:
            raise InputsError(f"{w}: a material line names its MAS.BLOCK host line")
        if t is None:
            t = x.get("t_conditional")
            if t is None or not x.get("condition"):
                raise InputsError(f"{w}: host {x['host']!r} prints no thickness: a figure needs the stated condition")
        elif x.get("t_conditional") is not None:
            raise InputsError(f"{w}: the host prints t={t}: no conditional thickness")
        area = _d(x.get("area_m2"), f"{w} area")
        if not Decimal(0) < area <= Decimal(1000):
            raise InputsError(f"{w}: area {area} m2 (unit slip, or 0 for a held host)")
        if kind == "AT_LEAST" and x.get("min_colour") != COLOUR[code]:
            raise InputsError(f"{w}: an AT_LEAST {code} needs a {COLOUR[code]} drawn minimum (min colour "
                              f"{x.get('min_colour')!r}: never firmer than the host, R-T703-1 (h))")
        exact, rate = material(code, area, rates, t, w)
    if exact != _d(x["exact"], f"{w} exact"):
        raise InputsError(f"{w}: ledger exact {x['exact']} is not the recomputed {exact}")
    fig = directed(kind, exact)
    if fig != _d(x["printed"], f"{w} printed") or fig <= 0:
        raise InputsError(f"{w}: ledger figure {x['printed']} is not the recomputed {fig} ({kind}, R-T696-1)")
    return dict(x, _exact=exact, _value=float(fig), _rate=None if rate is None else str(rate), _t=t)


def recompute_ends(x, w="bound"):
    """R-T696-1: the exact decimal ends of a bounded line from its own inputs. -> (lo, hi)"""
    f, i = x.get("form"), x.get("inputs") or {}
    if f == "BASE_X_RATE":
        b, r = i.get("base_m2") or [None, None], _d(i.get("rate"), f"{w} rate")
        return _mul(_d(b[0], f"{w} base low"), r), _mul(_d(b[1], f"{w} base high"), r)
    if f == "BEARING_X_F":
        b, k = i.get("bearing_m") or [None, None], _d(i.get("f_m3_per_m"), f"{w} factor")
        return _mul(_d(b[0], f"{w} bearing low"), k), _mul(_d(b[1], f"{w} bearing high"), k)
    if f == "DRAWN_PLUS_HELD":
        dr = i.get("drawn") or [None, None]
        return (_d(dr[0], f"{w} drawn low"),
                _add(_d(dr[1], f"{w} drawn high"), _d(i.get("bands_high"), f"{w} bands"),
                     _d(i.get("pieces_high"), f"{w} pieces")))
    raise InputsError(f"{w}: form {f!r}")


def _br_entry(x):
    w = f"{P_BR} {x.get('line_id')}"
    if not isinstance(x.get("line_id"), str) or not A3063.LINE_ID_RE.match(x["line_id"]):
        raise InputsError(f"{w}: line id")
    A3063._need(x, ("item_code", "unit", "form", "exact", "was", "restated"), w)
    if x["item_code"] not in BR_CODES or x["unit"] != UNIT[x["item_code"]]:
        raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a B9 bounded material code")
    lo, hi = recompute_ends(x, w)
    if lo < 0 or lo > hi:
        raise InputsError(f"{w}: exact ends {lo} .. {hi} inverted or negative")
    if [lo, hi] != [_d(v, f"{w} exact") for v in x["exact"]]:
        raise InputsError(f"{w}: ledger exact {x['exact']} is not the recomputed {[str(lo), str(hi)]}")
    new = [down6(lo), up6(hi)]
    if new != [_d(v, f"{w} restated") for v in x["restated"]]:
        raise InputsError(f"{w}: ledger restated {x['restated']} is not the recomputed {new} (R-T696-1)")
    was = [_d(v, f"{w} was") for v in x["was"]]
    return dict(x, _lo=float(new[0]), _hi=float(new[1]), _exact=(lo, hi), _was=[float(v) for v in was],
                _moves=new != was)


def load_inputs(doc, project_id=None):
    """URBAN_V3072_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "rates": {units_black_per_m2 {value, source}, mortar_black_m3_per_m2 {by_t {"0.15", "0.20"}, source},
               glue_aac_kg_per_m2 {by_t, source}},
     "one_sided": [{"line_id", "source_tasks", "item_code", "unit", "kind" AT_MOST | AT_LEAST, "host",
                    "host_line_id", MAS.BLOCK: "components" [{id, upper, lower, class}]; material: "area_m2",
                    "min_colour" (AT_LEAST), "t_conditional" + "condition" (a host with no printed thickness);
                    "exact", "printed", "cause" {class, ref, deciding_datum}, "basis"}],
     "rounding": [{"line_id", "source_tasks", "item_code", "unit", "form", "inputs", "exact" [lo, hi],
                   "was" [lo, hi] (the candidate's print), "restated" [lo, hi]}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    rates = doc.get("rates") or {}
    os_ = [_os_entry(x, srcs, rates) for x in doc.get("one_sided") or ()]
    br = []
    for x in doc.get("rounding") or ():
        A3043._tasks(x, srcs, f"{P_BR} {x.get('line_id')}")
        br.append(_br_entry(x))
    if not os_ and not br:
        raise InputsError("no entry in the inputs")
    ids = [e["line_id"] for e in os_ + br]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one statement, R-T703-1 (j))")
    by = {e["line_id"]: e for e in os_}
    for e in os_:                                            # R-T703-1 (h): a material is never firmer than its host
        h = by.get(e.get("host_line_id"))
        if e["item_code"] != BLOCK and h is not None:
            if h["kind"] != e["kind"]:
                raise InputsError(f"{e['line_id']}: {e['kind']} on a host stated {h['kind']}")
            if _d(e["area_m2"], "area") != _d(h["printed"], "host"):
                raise InputsError(f"{e['line_id']}: area {e['area_m2']} is not its host's figure {h['printed']}")
    return dict(doc, _sources=srcs, _one_sided=os_, _rounding=br)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[P_OS]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _figures_beside(b):
    """every one-ended figure an earlier record already states beside the line"""
    out = []
    for k, v in ((b.get("calculation") or {}).get("inputs") or {}).items():
        bs = v.get("beside") if isinstance(v, dict) else None
        if isinstance(bs, dict) and str(bs.get("kind") or "").startswith(("AT_LEAST", "AT_MOST")):
            out.append(k)
    return out


def _assert_os(b, e, by):
    w = f"{P_OS} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    host_eid = e["host"]
    want = host_eid if e["item_code"] == BLOCK else f"MATERIAL:{host_eid}"
    ok = (b["item_code"] == e["item_code"] and b["unit"] == e["unit"] and loc.get("element_id") == want and
          line_class(b) == "HELD" and b["evidence_state"] == BLANK and b.get("measured_net") is None and
          A3063._view_range(b) is None)
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{A3063._view_range(b)} is not a HELD blank {e['item_code']} on {want} (stale binding)")
    if e["item_code"] != BLOCK:
        h = by.get(e["host_line_id"])
        if h is None or h["item_code"] != BLOCK or (h.get("location") or {}).get("element_id") != host_eid or \
                line_class(h) != "HELD":
            raise InputsError(f"{w}: host {e['host_line_id']} is not the HELD MAS.BLOCK line {host_eid}")
    old = _figures_beside(b)
    if old:
        raise InputsError(f"{w}: the line already carries a figure beside ({old}): confirm it, never restate it")


def _assert_br(b, e):
    w = f"{P_BR} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    r = A3063._view_range(b)
    if b["item_code"] != e["item_code"] or b["unit"] != e["unit"] or b["evidence_state"] != BOUNDED or r is None or \
            abs(r[0] - e["_was"][0]) > 1e-12 or abs(r[1] - e["_was"][1]) > 1e-12:
        raise InputsError(f"{w}: candidate {b['item_code']} {b['evidence_state']} {r} is not the bounded print "
                          f"{e['_was']} (stale binding)")


def _restate_os(b, e, srcs):
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"),
           "bounded_range": b.get("bounded_range"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    u = e["unit"]
    word = "at most" if e["kind"] == "AT_MOST" else "at least"
    if e["item_code"] == BLOCK:
        terms = " + ".join(f"{c.get('id')} {_fmt(float(_d(c['upper' if e['kind'] == 'AT_MOST' else 'lower'], 'c')))}"
                           for c in e["components"]
                           if (c.get("upper") if e["kind"] == "AT_MOST" else c.get("lower")) is not None)
        basis = f"sum of the components ({terms}) m2 (R-T713-1)"
    else:
        basis = f"{e['area_m2']} m2 x {e['_rate']} {u}/m2 at t={e['_t']} (R-T696-1 / R-T713-1)"
        if e.get("condition"):
            basis += f"; {e['condition']}"
    beside = {"kind": f"{e['kind']}_{u.upper()}", "value": e["_value"], "unit": u, "exact": str(e["_exact"]),
              "basis": basis[:600], "never": "a range, a point, 0 or a total"}
    if e.get("condition"):
        beside["condition"] = e["condition"]
    head = (f"HELD, {'UPPER' if e['kind'] == 'AT_MOST' else 'LOWER'} END ONLY (blank): {word} {_fmt(e['_value'])} {u} "
            f"beside")
    f = f"{METHOD}: {head}; {basis}; held on {e['cause']['class']}: {e['cause']['ref']}"
    if was["formula"]:
        f += f" | was: {was['formula']}"
    ln["calculation"] = dict(ln.get("calculation") or {}, formula=f[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['line_id']}: the formula would conclude on a figure (write bounds as 'at most')")
    if not (ln.get("rfi") or {}).get("question"):
        ln["rfi"] = {"question": f"{e['cause']['class']}: {e['cause']['ref']}; deciding datum: "
                                 f"{e['cause']['deciding_datum']}"[:400], "blocks": [b["line_id"]]}
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=P_OS, action=e["kind"], was=was, beside=beside, cause=e["cause"],
                        host_line_id=e.get("host_line_id") or e["line_id"], host=e["host"],
                        components=e.get("components"), area_m2=e.get("area_m2"), per_m2=e["_rate"], t=e["_t"],
                        min_colour=e.get("min_colour"), evidence_status="HELD", basis=(e.get("basis") or "")[:600])
    A305._note(ln, f"{METHOD}: {head}; NOT RELEASED")
    return A3063._fin(ln)


def _restate_br(b, e, srcs):
    ln = copy.deepcopy(b)
    br = dict(ln["bounded_range"])
    was = {"bounded_range": b["bounded_range"], "evidence_state": b["evidence_state"]}
    br["low"], br["high"] = e["_lo"], e["_hi"]
    ln["bounded_range"] = br
    lo, hi = e["_exact"]
    add = (f" | {METHOD} R-T696-1: range restated to {_fmt(e['_lo'])} .. {_fmt(e['_hi'])} {e['unit']} (low down, high "
           f"up at 6 dp from the exact {lo} .. {hi}; the {_fmt(e['_was'][0])} .. {_fmt(e['_was'][1])} print did not "
           f"contain it)")
    ln["calculation"] = dict(ln["calculation"], formula=((ln["calculation"].get("formula") or "") + add)[-1500:])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]) and \
            not A3043.FORMULA_END_RE.search((b.get("calculation") or {}).get("formula") or ""):
        raise InputsError(f"{e['line_id']}: the formula would conclude on a figure")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=P_BR, action="RESTATE_RANGE", was=was, exact=[str(lo), str(hi)],
                        restated=[e["_lo"], e["_hi"]], form=e["form"],
                        terms={("per_m2" if k == "rate" else k): v for k, v in e["inputs"].items()},
                        evidence_status=OA)
    A305._note(ln, f"{METHOD}: range restated with R-T696-1 (directed rounding); NOT RELEASED")
    return A3063._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T703", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.72 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, unchanged = [], []
    log = {"piece": "T703", "state": "RUN", "by_piece": {P_OS: {}, P_BR: 0}, "lines": 0,
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_one_sided"]:
        b = by.get(e["line_id"])
        _assert_os(b, e, by)
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate_os(b, e, srcs)
        k = f"{e['item_code']} {e['kind']}"
        log["by_piece"][P_OS][k] = log["by_piece"][P_OS].get(k, 0) + 1
        changes.append(A305._change(P_OS, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[{"what": e["host"], "why": f"{e['cause']['class']}: {e['cause']['ref']}",
                                           "beside": {e["kind"].lower(): e["_value"], "unit": e["unit"]}}],
                                    downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                    codes=[P_OS], group=b["item_code"], step=e["kind"]))
    for e in doc["_rounding"]:
        b = by.get(e["line_id"])
        _assert_br(b, e)
        if not e["_moves"]:
            unchanged.append({"line_id": e["line_id"], "range": e["_was"], "line_sha": A30.line_sha(b)})
            continue
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate_br(b, e, srcs)
        log["by_piece"][P_BR] += 1
        changes.append(A305._change(P_BR, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[{"what": "range", "range": [e["_lo"], e["_hi"]]}], downstream=[],
                                    verification=A3036._ver(srcs), evidence_status=OA, codes=[P_BR],
                                    group=b["item_code"], step="RESTATE_RANGE"))
    log["rounding_exact_already_inside"] = unchanged
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def check_totals(t0, t1, changes):
    """R-T703-1 (g) / (i): only the held range of the restated B9 codes moves, each exactly by its changes (a one-ended
    figure is beside a blank line: never summed, its code's totals unchanged). -> {code: {base, v3_0_72}}"""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    br = {f"{c['after']['item_code']}|{c['after']['unit']}" for c in changes if c["piece"] == P_BR}
    bad = sorted(k for k in moved if k not in br)
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside the restated ranges: {bad} (a one-ended figure is never "
                         f"summed)")
    want = A3068.expected_totals(t0, [c for c in changes if c["piece"] == P_BR])
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
        if a["lines"] != z["lines"] or a["bounded_lines"] != z["bounded_lines"] or \
                a["blocked_lines"] != z["blocked_lines"] or abs(a["released"] - z["released"]) > TOT_TOL or \
                any(abs(a[f] - z[f]) > TOT_TOL for f in ("held_low", "held_high")):
            raise ValueError(f"{METHOD}: {k} totals {a} are not the changes' {z}")
        out[k] = {"base": t0.get(k), "v3_0_72": a, "view": A3058.total_view(a)}
    return out


def check_masonry(lines, before=None):
    """on finished lines: a ONE_SIDED line is a HELD blank masonry line (BLOCKED_RFI, no measured_net, no range) with
    its question and one positive figure beside of its kind; a BOUND_ROUNDING line is bounded and its range contains
    its exact ends; with `before`, a one-sided line was blank and a rounding line was bounded. -> summary"""
    out = {P_OS: 0, P_BR: 0}
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        p = rec.get("piece")
        if p == P_OS:
            bs = rec.get("beside") or {}
            ok = (ln["item_code"] in OS_CODES and ln["evidence_state"] == BLANK and ln.get("measured_net") is None and
                  ln.get("bounded_range") is None and line_class(ln) == "HELD" and
                  bool((ln.get("rfi") or {}).get("question")) and rec["was"]["class"] == "HELD" and
                  rec["was"]["bounded_range"] is None and rec.get("action") in KINDS and
                  bs.get("kind") == f"{rec['action']}_{ln['unit'].upper()}" and (bs.get("value") or 0) > 0)
            if ok and old is not None:
                o = old.get(ln["line_id"])
                ok = o is not None and o["evidence_state"] == BLANK and o.get("measured_net") is None
        elif p == P_BR:
            r = A3063._view_range(ln)
            lo, hi = (Decimal(x) for x in rec.get("exact") or ("nan", "nan"))
            ok = (ln["item_code"] in BR_CODES and ln["evidence_state"] == BOUNDED and r is not None and
                  Decimal(repr(r[0])) <= lo and Decimal(repr(r[1])) >= hi)
            if ok and old is not None:
                o = old.get(ln["line_id"])
                ok = o is not None and o["evidence_state"] == BOUNDED
        else:
            ok = False
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {p} line is not in its state")
        out[p] += 1
    return out


def b9_census(lines):
    """per B9 code and unit: released / bounded / one-sided beside (AT_MOST, AT_LEAST) / blank / excluded lines
    (counts only; figures are never summed across lines here)."""
    out = {}
    for ln in lines:
        if ln["item_code"] not in (BLOCK,) + A3059.CODES + (PERIM, BED):
            continue
        k = out.setdefault(f"{ln['item_code']}|{ln['unit']}", {"released": 0, "bounded": 0, "at_most": 0,
                                                               "at_least": 0, "blank": 0, "excluded": 0})
        c = line_class(ln)
        if c == "EXCLUDED":
            k["excluded"] += 1
        elif c == "RELEASED":
            k["released"] += 1
        elif A3063._view_range(ln) is not None:
            k["bounded"] += 1
        else:
            kinds = [str((((ln.get("calculation") or {}).get("inputs") or {}).get(r) or {}).get("beside", {}).get(
                "kind") or "") for r in _figures_beside(ln)]
            if any(x.startswith("AT_MOST") for x in kinds):
                k["at_most"] += 1
            elif any(x.startswith("AT_LEAST") for x in kinds):
                k["at_least"] += 1
            else:
                k["blank"] += 1
    return dict(sorted(out.items()))


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.72 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier state checks re-run: V3.0.64 .. V3.0.67 / V3.0.70 concrete, V3.0.67 /
    V3.0.71 lintels, V3.0.68 masonry, V3.0.69 finishes (nothing of theirs may move)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        codes = OS_CODES if c["piece"] == P_OS else BR_CODES
        if a["item_code"] not in codes or a["unit"] != UNIT[a["item_code"]]:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this piece may touch")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.72 adds no line)")
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
    ident = {"base_lines": len(prev), "v3_0_72_lines": len(out), "v3_0_72_rows": len(changes), "replaced": len(repl),
             "added": 0, "concrete_v3_0_64": A3064.check_concrete(out), "concrete_v3_0_65": A3065.check_concrete(out),
             "concrete_v3_0_66": A3066.check_concrete(out), "concrete_v3_0_67": A3067.check_concrete(out, prev),
             "lintels_v3_0_67": A3067.check_lintels(out), "masonry_v3_0_68": A3068.check_masonry(out),
             "finishes_v3_0_69": A3069.check_finishes(out), "concrete_v3_0_70": A3070.check_concrete(out, prev),
             "lintels_v3_0_71": A3071.check_lintels(out, prev), "masonry": check_masonry(out, prev),
             "b9_census_before": b9_census(prev), "b9_census_after": b9_census(out),
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


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
                     "line_id": ref["line_id"], "item_code": ref["item_code"],
                     "family": "B9-01" if ref["item_code"] in (BLOCK, U_BLACK, U_WHITE) else "B9-04",
                     "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_72": A30._qty(ref), "class": [rec["was"].get("class") or line_class(c["before"]),
                                                               line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "beside": rec.get("beside"),
                     "exact": rec.get("exact"), "restated": rec.get("restated"), "cause": rec.get("cause"),
                     "host_line_id": rec.get("host_line_id"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED", "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "family", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_72", "beside", "cause", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_72")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        b = r.get("beside")
        if not b:
            return "none"
        return f"{'at most' if b['kind'].startswith('AT_MOST') else 'at least'} {_fmt(b['value'])} {b['unit']}"
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "family": r["family"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_72": q(r.get("after_v3_0_72")), "beside": bs(r),
                       "cause": (r.get("cause") or {}).get("class") or "", "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_71"}, v3_0_72=d["v3_0_71"])
            for d in A3071.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_72_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_72_BOQ_LINES.json": BL.dumps(new),
             "V3_0_72_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_72_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_72_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_72_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_72_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "kinds": list(KINDS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "parent_area", "material", "recompute_ends", "directed", "host_t", "check_masonry", "check_totals",
           "b9_census", "integrate", "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
