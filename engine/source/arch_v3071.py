"""ARCH_TAKEOFF_V3.0.71 (T-704, lane I, CONCRETE GATE B ROUND 8 integration package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.70 (engine.source.arch_v30, arch_v301 .. arch_v3070), extended with ONE piece built from the
Checker-merged T-699 ledger (R-T699-1): the one-sided bounds of HELD blank STR.CONC.LINTEL lines. No quantity, range or
code total moves; every line it names stays HELD blank (BLOCKED_RFI):

  LINTEL_SIDE   a named HELD blank lintel line gains its one-sided statement BESIDE it (never in it):
                  AT_MOST       existence OPEN, or a CONDITIONAL EXCLUSION naming the member whose soffit may serve the
                                opening: the line is 0 (no lintel) or at most B x D x (w + the bearing taken at each
                                end), RECOMPUTED here from its terms (section, width used, each end's stopper, drawn
                                available length and the bearing taken) with directed rounding (ceiling at 6 dp) and
                                asserted equal to the merged ledger; the 'if REQUIRED' least figure is shown beside as
                                CONDITIONAL, never as a bound (the line may be 0);
                  DATUM_NAMED   no one-sided bound is formed (a curved head, an end with no recorded stopper, no jamb
                                evidence): the exact missing datum and its cause class are named; no figure in the line.
                A line already carrying a one-sided figure from an earlier version (V3.0.67 LOWER_ONLY) is confirmed in the
                run record, never restated.

R-T704-1 (every villa; = R-T693-1 (a) .. (z) as written where they apply, plus): (aa) a one-sided bound of a blank
lintel line is the product of its own terms recomputed at wiring time (section B x D in metres, width used, two ends
each with a recorded stopper and a bearing taken no longer than the drawn available length rounded up to 1 mm), the
AT_MOST ceiled and the conditional least figure floored at 6 dp (R-T696-1), equal to the merged ledger; (bb) the line
stays HELD blank: no measured_net, no bounded_range, its question names the deciding datum, and it is never summed into
a code total (a family AT_MOST is a run-record figure, with a pier both lines take whole counted once); (cc) AT_MOST is
stated with existence OPEN or a CONDITIONAL EXCLUSION (the member named); an AT_LEAST bound needs existence REQUIRED
and is not formed here; (dd) the conditional least figure never exceeds the AT_MOST and is never called a bound.
Files: V3_0_71_BOQ_LINES.json / .csv, V3_0_71_INTEGRATION_LEDGER.json / .csv, V3_0_71_DIFF.csv, V3_0_71_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
from decimal import ROUND_CEILING, ROUND_FLOOR, Context, Decimal

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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books a Checker-merged member ledger onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.71"
EXTENDS = A3070.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T704_ARCH_V3_0_71"
INPUTS_SCHEMA = "URBAN_V3071_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3071_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T704-1", "T-704"
REC_KEY = "concrete_ledger_v3071"
P_LS = "LINTEL_SIDE"
ACTIONS = ("AT_MOST", "DATUM_NAMED")
LINTEL = "STR.CONC.LINTEL"
UNIT = "m3"
BLANK = A3063.BLANK
EXISTENCE = ("OPEN", "CONDITIONAL_EXCLUSION")
CAUSES = ("DESIGNER ITEM", "NEEDS OWNER RULE", "MEASURABLE NOW", "METHOD GAP")
RECORDED = ("COLUMN", "END_OF_MASONRY", "END", "OPENING", "SEARCH_LIMIT")
CONVENTIONS = ("CEILING", "MIN_BEARING")
TOT_TOL = A3063.TOT_TOL
_CTX = Context(prec=50)                  # local context only (never the process-global precision: F-T648-2)
Q6 = Decimal("0.000001")
MM = Decimal("0.001")

PIECES = {
    P_LS: {"module": "engine/source/arch_v3071.py (HELD blank STR.CONC.LINTEL lines given the one-sided bound the "
                     "Checker-merged T-699 ledger states BESIDE them, recomputed from its terms, or the exact missing "
                     "datum named; no quantity, range or total moves)",
           "policy": "CONCRETE_GATE_B_V8", "rule_id": "R-T699-1 / R-T673-3 / R-T696-1 (R-T704-1)",
           "owner_rules": ["R-CONC-OWN-1 (one physical element once: a lintel whose head reaches a member soffit is "
                           "owned by the member)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "owner lintel rule 2026-11-02 (precast 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, 15 cm minimum "
                           "bearing: the manual method beside; the drawing's printed schedule bearing governs the m3)",
                           "ERS s.2-5 (drawn element first; statuses; a blank line is not 'no figure at all')"],
           "owner_manual_method": "one precast lintel per opening, the shortest standard piece >= opening + 2 x 0.15 m; "
                                  "existence decided by the head vs the soffit on the drawings; a head not printed is "
                                  "held with a designer request",
           "drawing_method": "the merged T-699 ledger: RC cast lintel B (host wall) x D (ST p.13 schedule depth) x "
                             "(w + the bearing taken at each end to its drawn stopper: the available length 1 mm up "
                             "when both ends are bounded (CEILING), the schedule bearing 0.40 at a bounded end and the "
                             "whole available length at a deficit end (MIN_BEARING)); the line is 0 or at most that "
                             "figure while existence is open (R-T699-1)"},
}
WAITING = dict(A3070.WAITING)
WAITING.update({
    "T704_EXISTENCE": "the 16 AT_MOST lintel lines stay HELD blank: existence UNRESOLVED on designer items (D-39 / "
                      "Q-54 B annex slab top, T-207 sill, R-T228-3 stair-shaft members, D-43 lift tie beam, T-581 width, "
                      "T-227 dome ring, D-04 BM-2F-017 depth, D-45 lift / P-GF-01 heads)",
    "T704_JUNCTION_END": "D-GF-04 / D-1F-06 (V3.0.67 AT_LEAST 0.048 / 0.036 beside, confirmed): the high end needs a "
                         "Lead / Checker ruling on a junction END (METHOD GAP, no owner question)",
    "T704_DATUM_NAMED": "A-GF-01 (curved head, T-238), D-GF-05 (START stopper unrecorded + Q-67), D-GF-14 (GF-W30 jambs: "
                        "MEASURABLE NOW, a lane S read): no one-sided figure",
    "T704_DOWNSTREAM": "lintel formwork / rebar / bed mortar of these 21 openings stay as V3.0.70 (not re-derived from a "
                       "one-sided figure)",
})


# ================================================================================================ arithmetic
def _d(x, w):
    if x is None or isinstance(x, bool) or not isinstance(x, (int, float, str)):
        raise InputsError(f"{w}: {x!r} is not a number (a missing input is never 0)")
    v = Decimal(repr(x)) if isinstance(x, float) else Decimal(x)
    if not v.is_finite():
        raise InputsError(f"{w}: not finite")
    return v


def _mul(*xs):
    out = Decimal(1)
    for x in xs:
        out = _CTX.multiply(out, x)
    return out


def ceil6(x):
    return x.quantize(Q6, rounding=ROUND_CEILING)


def floor6(x):
    return x.quantize(Q6, rounding=ROUND_FLOOR)


def section(s, w="section"):
    """B x D in metres; refused outside 0.05 .. 0.60 / 0.10 .. 0.80 (a cm or mm slip)."""
    if not isinstance(s, dict):
        raise InputsError(f"{w}: section B x D not known: HELD by name, never 0")
    B, D = _d(s.get("B_m"), f"{w} B"), _d(s.get("D_m"), f"{w} D")
    if not (Decimal("0.05") <= B <= Decimal("0.60") and Decimal("0.10") <= D <= Decimal("0.80")):
        raise InputsError(f"{w}: section {B} x {D} is not in metres")
    return B, D


def at_most(e, w="AT_MOST"):
    """R-T704-1 (aa): -> (exact, ceiled, length). e = {section, width_m, end_terms [2 x {side, stopper, available_m,
    taken_m}], length_m}."""
    B, D = section(e.get("section"), w)
    wd = _d(e.get("width_m"), f"{w} width")
    if not Decimal(0) < wd <= Decimal(10):
        raise InputsError(f"{w}: width {wd} is not in metres")
    ts = e.get("end_terms")
    if not isinstance(ts, list) or len(ts) != 2 or sorted(t.get("side") for t in ts) != ["END", "START"]:
        raise InputsError(f"{w}: two ends (START, END), each with its stopper (no jamb evidence: no AT_MOST)")
    length = wd
    for t in ts:
        if t.get("stopper") not in RECORDED:
            raise InputsError(f"{w} {t.get('side')}: stopper {t.get('stopper')!r} not recorded (an OPEN end gives no "
                              f"AT_MOST)")
        a, k = _d(t.get("available_m"), f"{w} {t['side']} available"), _d(t.get("taken_m"), f"{w} {t['side']} taken")
        if a < 0 or a > 10 or k < 0:
            raise InputsError(f"{w} {t['side']}: available {a} / taken {k} m")
        if k > a.quantize(MM, rounding=ROUND_CEILING):
            raise InputsError(f"{w} {t['side']}: bearing taken {k} beyond the drawn available {a} (1 mm up)")
        length = _CTX.add(length, k)
    if length != _d(e.get("length_m"), f"{w} length"):
        raise InputsError(f"{w}: length {length} is not the ledger's {e.get('length_m')}")
    exact = _mul(B, D, length)
    return exact, ceil6(exact), length


def if_required(c, sec, w="if REQUIRED"):
    """R-T704-1 (dd): the conditional least figure B x D x (w + n x b_min), floored at 6 dp (never a bound)."""
    if c is None:
        return None
    B, D = section(sec, w)
    n = c.get("bounded_ends")
    if n not in (0, 1, 2):
        raise InputsError(f"{w}: bounded ends {n!r}")
    wd, b = _d(c.get("width_m"), f"{w} width"), _d(c.get("b_min_m"), f"{w} bearing")
    if not Decimal("0.05") <= b <= Decimal("1.0"):
        raise InputsError(f"{w}: bearing {b} is not in metres")
    v = floor6(_mul(B, D, _CTX.add(wd, _mul(Decimal(n), b))))
    if v != _d(c.get("value_m3"), f"{w} value") or v <= 0:
        raise InputsError(f"{w}: {c.get('value_m3')} is not the recomputed {v}")
    return v


# ================================================================================================ inputs
def _entry(x, srcs):
    a = x.get("action")
    w = f"{a} {x.get('line_id')}"
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}: V3.0.71 states AT_MOST or DATUM_NAMED beside a blank lintel only "
                          f"(an AT_LEAST needs existence REQUIRED, R-T704-1 (cc))")
    if not isinstance(x.get("line_id"), str) or not A3063.LINE_ID_RE.match(x["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(x, srcs, w)
    A3063._need(x, ("expect", "member", "basis", "existence", "cause", "opening"), w)
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    if ex["item_code"] != LINTEL or ex["unit"] != UNIT or ex["class"] != "HELD" or \
            ex.get("low") is not None or ex.get("high") is not None:
        raise InputsError(f"{w}: {ex} is not a HELD blank {LINTEL} line")
    if ex["element_id"] != f"LINTEL:{x['opening']}":
        raise InputsError(f"{w}: element {ex['element_id']} is not the opening {x['opening']}")
    if x["existence"] not in EXISTENCE:
        raise InputsError(f"{w}: existence {x['existence']!r} (OPEN or CONDITIONAL_EXCLUSION here; REQUIRED lines "
                          f"carry their lower end from an earlier version)")
    if (x["existence"] == "CONDITIONAL_EXCLUSION") != bool(x.get("excluded_by")):
        raise InputsError(f"{w}: a conditional exclusion names the member that may serve the opening, and only then")
    c = x["cause"]
    A3063._need(c, ("class", "ref", "deciding_datum"), w)
    if c["class"] not in CAUSES:
        raise InputsError(f"{w}: cause class {c['class']!r}")
    e = dict(x)
    if a == "AT_MOST":
        if x.get("convention") not in CONVENTIONS:
            raise InputsError(f"{w}: convention {x.get('convention')!r}")
        exact, hi, length = at_most(x, w)
        if hi != _d(x.get("at_most_m3"), f"{w} AT_MOST") or hi <= 0:
            raise InputsError(f"{w}: ledger AT_MOST {x.get('at_most_m3')} is not the recomputed {hi} (R-T704-1 (aa))")
        lo = if_required(x.get("if_required"), x["section"], w)
        if lo is not None and lo > hi:
            raise InputsError(f"{w}: conditional least {lo} above the AT_MOST {hi} (R-T704-1 (dd))")
        e.update(_exact=exact, _hi=float(hi), _lo=None if lo is None else float(lo), _length=float(length))
    else:
        if x.get("at_most_m3") is not None or x.get("end_terms"):
            raise InputsError(f"{w}: a datum-named line carries no one-sided figure")
        if not x.get("why_no_bound"):
            raise InputsError(f"{w}: why no bound is formed")
        lo = None
        if x.get("if_required") is not None:
            sec = x.get("section") or {"B_m": None, "D_m": None}
            lo = if_required(x["if_required"], sec, w)
        e.update(_exact=None, _hi=None, _lo=None if lo is None else float(lo), _length=None)
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3071_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"action" AT_MOST | DATUM_NAMED, "line_id", "source_tasks", "opening", "member", "basis",
                  "expect" {item_code, element_id, unit, class HELD, low None, high None},
                  "existence" OPEN | CONDITIONAL_EXCLUSION, "excluded_by", "cause" {class, ref, deciding_datum},
                  AT_MOST: "section" {B_m, D_m, source}, "width_m", "width_note", "end_terms" [{side, stopper,
                  stopper_id, available_m, taken_m, why}], "length_m", "convention", "at_most_m3";
                  DATUM_NAMED: "why_no_bound" (+ "section" when a conditional figure is given);
                  "if_required" {value_m3, width_m, bounded_ends, b_min_m, meaning} | None, "owner_manual"}],
     "confirm": [{"line_id", "opening", "kind" AT_LEAST_M3, "value", "carried_by", ...}] (asserted unchanged),
     "family": {"at_most_m3", "lines", "shared_piers": [{"lines", "pier_m", "double_counted_m3"}], ...}}"""
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
    ids = [e["line_id"] for e in ents] + [c.get("line_id") for c in doc.get("confirm") or ()]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one statement)")
    for c in doc.get("confirm") or ():
        A3063._need(c, ("line_id", "kind", "value", "carried_by"), "confirm")
        if c["kind"] != "AT_LEAST_M3":
            raise InputsError(f"confirm {c['line_id']}: kind {c['kind']}")
    fam = family(ents, doc.get("family"))
    return dict(doc, _sources=srcs, _entries=ents, _family=fam)


def family(ents, fam):
    """R-T704-1 (bb): the family AT_MOST of the AT_MOST lines (a run-record figure, never a total): the sum of the
    exact figures less every pier two lines both take whole, ceiled at 6 dp; equal to the ledger's when given."""
    rows = {e["line_id"]: e for e in ents if e["action"] == "AT_MOST"}
    tot = Decimal(0)
    for e in rows.values():
        tot = _CTX.add(tot, e["_exact"])
    piers = []
    for p in (fam or {}).get("shared_piers") or ():
        if len(p.get("lines") or ()) != 2 or any(x not in rows for x in p["lines"]):
            raise InputsError(f"shared pier {p}: two AT_MOST lines of this set")
        dbl, pm = _d(p.get("double_counted_m3"), "shared pier"), _d(p.get("pier_m"), "shared pier")
        a, b = (rows[x] for x in p["lines"])
        for one, other in ((a, b), (b, a)):
            if not any(t.get("stopper") == "OPENING" and t.get("stopper_id") == other["opening"] and
                       _d(t["taken_m"], "pier") == pm for t in one["end_terms"]):
                raise InputsError(f"shared pier {p}: {one['opening']} does not take the pier to {other['opening']} "
                                  f"whole")
        B, D = section(rows[p["lines"][0]]["section"], "shared pier")
        if _mul(B, D, _d(p["pier_m"], "pier")) != dbl:
            raise InputsError(f"shared pier {p}: double count {dbl} is not B x D x pier")
        tot = tot - dbl
        piers.append(p)
    out = {"at_most_m3": float(ceil6(tot)), "lines": len(rows), "shared_piers": piers}
    if fam and fam.get("at_most_m3") is not None:
        if ceil6(tot) != _d(fam["at_most_m3"], "family"):
            raise InputsError(f"family AT_MOST {fam['at_most_m3']} is not the recomputed {ceil6(tot)}")
        if fam.get("lines") not in (None, len(rows)):
            raise InputsError(f"family lines {fam['lines']} vs {len(rows)}")
    return out


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_LS, "policy": PIECES[P_LS]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _assert_before(b, e):
    x, w = e["expect"], f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and line_class(b) == "HELD" and b["evidence_state"] == BLANK and b.get("measured_net") is None
          and A3063._view_range(b) is None)
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{A3063._view_range(b)} is not a HELD blank {x['element_id']} (stale binding)")
    inp = (b.get("calculation") or {}).get("inputs") or {}
    old = [k for k in (A3063.REC_KEY, A3067.REC_KEY)
           if ((inp.get(k) or {}).get("beside") or {}).get("kind") in ("AT_LEAST_M3", "AT_MOST_M3")]
    if old:
        raise InputsError(f"{w}: the line already carries a figure beside ({old}): confirm it, never restate it")


def _terms_text(e):
    t = " + ".join(f"{x['side']} {x['stopper']} {_fmt(x['taken_m'])} (of {_fmt(x['available_m'])})"
                   for x in e["end_terms"])
    return f"{_fmt(e['section']['B_m'])} x {_fmt(e['section']['D_m'])} x (w {_fmt(e['width_m'])} + {t})"


def _question(e):
    c = e["cause"]
    q = f"{c['class']}: {c['ref']}; deciding datum: {c['deciding_datum']}"
    if e.get("excluded_by"):
        q += f"; no lintel if {e['excluded_by']} serves the opening"
    return q[:400]


def _restate(b, e, srcs):
    a = e["action"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b)}
    if a == "AT_MOST":
        beside = {"kind": "AT_MOST_M3", "value": e["_hi"], "convention": e["convention"], "length_m": e["_length"],
                  "basis": _terms_text(e), "width_note": e.get("width_note")}
        head = (f"HELD, UPPER END ONLY (blank): 0 or at most {_fmt(e['_hi'])} m3 beside, existence {e['existence']}"
                + (f" (no lintel if {e['excluded_by']} serves the opening)" if e.get("excluded_by") else ""))
        body = f"{_terms_text(e)}, {e['convention']}, ceiled at 6 dp (R-T696-1)"
    else:
        beside = None
        head = f"HELD BLANK, DATUM NAMED: no one-sided figure ({e['why_no_bound'][:160]})"
        body = f"existence {e['existence']}"
    if e["_lo"] is not None:
        body += f"; if REQUIRED (never a bound) at least {_fmt(e['_lo'])} m3"
    ln["rfi"] = {"question": _question(e), "blocks": [b["line_id"]]}
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head}; {body}; held on {e['cause']['class']}: {e['cause']['ref']}")[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['line_id']}: the formula would conclude on a figure (write bounds as 'at most')")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, action=a, opening=e["opening"], member=e["member"], was=was, beside=beside,
                        existence=e["existence"], excluded_by=e.get("excluded_by"), cause=e["cause"],
                        section=e.get("section"), width_m=e.get("width_m"), end_terms=e.get("end_terms"),
                        if_required=None if e["_lo"] is None else dict(e["if_required"], value_m3=e["_lo"]),
                        why_no_bound=e.get("why_no_bound"), basis=e["basis"][:600],
                        owner_manual=e.get("owner_manual"))
    A305._note(ln, f"{METHOD}: {head[:300]}; NOT RELEASED")
    return A3063._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T704", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.71 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    confirmed = []
    for c in doc.get("confirm") or ():
        b = by.get(c["line_id"])
        r = (((b or {}).get("calculation") or {}).get("inputs") or {}).get(A3067.REC_KEY) or {}
        bs = r.get("beside") or {}
        if b is None or b["evidence_state"] != BLANK or r.get("action") != "LOWER_ONLY" or \
                bs.get("kind") != c["kind"] or abs(float(bs.get("value") or -1) - float(c["value"])) > 1e-9:
            raise InputsError(f"confirm {c['line_id']}: the candidate does not carry {c['kind']} {c['value']} from "
                              f"V3.0.67 (stale binding)")
        confirmed.append({"line_id": c["line_id"], "kind": c["kind"], "value": c["value"],
                          "carried_by": c["carried_by"], "line_sha": A30.line_sha(b)})
    changes = []
    log = {"piece": "T704", "state": "RUN", "by_action": {}, "lines": 0, "confirmed_unchanged": confirmed,
           "family_at_most": doc["_family"],
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        _assert_before(b, e)
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        held = [{"what": e["member"], "why": _question(e),
                 "beside": None if e["_hi"] is None else {"at_most_m3": e["_hi"]}}]
        changes.append(A305._change(P_LS, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                    codes=[P_LS], group=b["item_code"], step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def check_totals(t0, t1, changes, expect=None):
    """R-T704-1 (bb): no code total moves (a one-sided figure is beside a blank line, never summed). -> {}"""
    moved = sorted(k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k))
    if moved:
        raise ValueError(f"{METHOD}: code totals moved: {moved} (a one-sided figure is never summed)")
    return {}


def check_lintels(lines, before=None):
    """on finished lines: every V3.0.71 line is a HELD blank lintel (BLOCKED_RFI, no measured_net, no range) with its
    question; an AT_MOST line carries its positive figure beside, a DATUM_NAMED line none; a conditional least figure
    never exceeds the AT_MOST; with `before`, the line was blank. -> summary"""
    out = {a: 0 for a in ACTIONS}
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec.get("action")
        bs = rec.get("beside")
        lo = (rec.get("if_required") or {}).get("value_m3")
        ok = (ln["item_code"] == LINTEL and ln["unit"] == UNIT and ln["evidence_state"] == BLANK and
              ln.get("measured_net") is None and ln.get("bounded_range") is None and line_class(ln) == "HELD" and
              bool((ln.get("rfi") or {}).get("question")) and rec["was"]["class"] == "HELD" and
              rec["was"]["bounded_range"] is None and rec.get("existence") in EXISTENCE)
        if a == "AT_MOST":
            ok = ok and isinstance(bs, dict) and bs.get("kind") == "AT_MOST_M3" and (bs.get("value") or 0) > 0 and \
                (lo is None or lo <= bs["value"] + 1e-12)
        elif a == "DATUM_NAMED":
            ok = ok and bs is None and bool(rec.get("why_no_bound"))
        else:
            ok = False
        if ok and old is not None:
            o = old.get(ln["line_id"])
            ok = o is not None and o["evidence_state"] == BLANK and o.get("measured_net") is None
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {a} line is not a HELD blank lintel with its statement")
        out[a] += 1
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.71 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier state checks re-run: V3.0.64 .. V3.0.67 / V3.0.70 concrete, V3.0.67
    lintels, V3.0.68 masonry, V3.0.69 finishes (nothing of theirs may move)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != LINTEL or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.71 adds no line)")
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
    ident = {"base_lines": len(prev), "v3_0_71_lines": len(out), "v3_0_71_rows": len(changes), "replaced": len(repl),
             "added": 0, "concrete_v3_0_64": A3064.check_concrete(out), "concrete_v3_0_65": A3065.check_concrete(out),
             "concrete_v3_0_66": A3066.check_concrete(out), "concrete_v3_0_67": A3067.check_concrete(out, prev),
             "lintels_v3_0_67": A3067.check_lintels(out), "masonry_v3_0_68": A3068.check_masonry(out),
             "finishes_v3_0_69": A3069.check_finishes(out), "concrete_v3_0_70": A3070.check_concrete(out, prev),
             "lintels": check_lintels(out, prev),
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
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "member": rec["member"], "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_71": A30._qty(ref), "class": [rec["was"]["class"], line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "beside": rec.get("beside"),
                     "if_required": rec.get("if_required"), "existence": rec.get("existence"),
                     "excluded_by": rec.get("excluded_by"), "cause": rec.get("cause"),
                     "end_terms": rec.get("end_terms"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED", "basis": rec["basis"], "owner_manual": rec.get("owner_manual"),
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_71", "beside", "existence", "cause", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_71")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_71": q(r.get("after_v3_0_71")),
                       "beside": (f"at most {_fmt(r['beside']['value'])}" if r.get("beside") else "none") +
                                 (f"; if REQUIRED {_fmt(r['if_required']['value_m3'])}" if r.get("if_required")
                                  else ""),
                       "existence": r.get("existence") or "", "cause": (r.get("cause") or {}).get("class") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_70"}, v3_0_71=d["v3_0_70"])
            for d in A3070.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_71_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_71_BOQ_LINES.json": BL.dumps(new),
             "V3_0_71_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_71_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_71_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_71_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_71_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "at_most", "if_required", "family", "check_lintels", "check_totals", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError", "line_class"]
