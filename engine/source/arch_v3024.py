"""ARCH_TAKEOFF_V3.0.24 (T-338): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.23 (engine.source.arch_v30,
arch_v301 .. arch_v3023), extended with ONE piece, LINE_STATE_TEXT: the line-state findings of the T-334 check fixed
in the lines' TEXT and STATE fields only, so that every line states ONE state. Not a new method family and not the
released default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the released
ARCH_TAKEOFF_V2.9. No quantity, no state word, no range and no line id changes here: a status never rises.

The question (ERS 2026-10-22 s.2.1, s.3; UP-QTY-STATUS-001; WORKFLOW_CONTROLS s.5): a canonical line states its state
four times: the evidence_state word, the measured_net figure, the bounded_range and the printed calculation.formula
(which the export prints). When they disagree, a reader of one BOQ row sees two states (a released kg under a 'held: '
text; a taken-off line keeping its old figure; a formula whose concluding figure is the gross or another element's
reading, not the line's own quantity). Each such line is corrected from ITS OWN record, never from a new reading:

  REBAR_FORMULA   a released reinforcement line (SOURCE_DERIVED, kg, its ledger record RELEASED) whose formula opens
                  with a hold word (the arch_v303 fallback 'held: ' + no reasons) prints its arithmetic from the
                  record's own inputs: count x length_m x kg/m = kg, kg/m from the project's unit-mass method
                  (engine.source.rebar_unit_mass, method named in the inputs) of the bar diameter the line carries
                  (its subtrade '<element> / <d> mm', written by arch_v303 from the record's dia_mm). The product must
                  equal the line's measured_net to its rounding (|product - net| <= 0.0005 kg, the export tolerance);
                  otherwise the line is refused (its quantity does not follow from its inputs: a state question for
                  the Lead, never fixed here).
  NA_GROSS        a NOT_APPLICABLE_WITH_EVIDENCE line that still carries a numeric gross drops the gross (None): a line
                  taken off carries no figure. The old gross is kept in calculation.inputs (and in the line's own
                  earlier record, e.g. base_ownership_v3021.before).
  FORMULA_END     a line whose formula concludes (its last '= x <unit>' / 'net x <unit>') on a figure that is not its
                  own quantity (a quantity line: not its measured_net; a bounded line: outside its range) gets its own
                  figure appended LAST: 'net <measured_net> <unit>' or 'held net <low> <unit> .. <high> <unit>'. The
                  earlier text (the gross, another element's area) stays as a reading; nothing is deleted.

Each fixed line records what it was (calculation.inputs.line_state_v3024: kind, before formula / gross, task, source)
and a note. A line the scan finds that is NOT of these kinds (a valued line under a hold text that is not a released
ledger record, a held line with a figure that is not NOT_APPLICABLE, a held line with no range concluding on a figure)
is never fixed: the inputs list it under 'for_lead' with the reason, and it stays byte-identical.

Refused (InputsError / ValueError, nothing written): a line listed twice or in two kinds; a listed line the run does not
carry or that does not show its finding (stale inputs); a line the scan finds that the inputs neither fix nor list for
the Lead (the family is integrated whole); a rebar line without numeric count / length, without a diameter, with a
product that is not its net, or whose record is not RELEASED; an unknown unit-mass method; a declared count or kg that
is not the records' sum; any change to quantity, state word, range, rfi, line id, project block or any field outside
calculation / notes (and gross on an NA_GROSS line); after the fix, a fixed line that still shows a finding. Every
other V3.0.23 line is byte-identical (asserted); the merged default guard runs again over the result
(arch_v307.guard_changes) and may not flag a line this version changes.

Files: V3_0_24_BOQ_LINES.json / .csv, V3_0_24_INTEGRATION_LEDGER.json / .csv (per line: kind, before and after
formula / gross, quantity before = after, released V2.9, status, source), V3_0_24_DIFF.csv (every line against V3.0.23
and the released V2.9), V3_0_24_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate: every value
comes from the lines and the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3023 as A3023
from engine.source import rebar_unit_mass as UM

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: it rewrites line text; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.24"
EXTENDS = A3023.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T338_ARCH_V3_0_24"
INPUTS_SCHEMA = "URBAN_V3024_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3024_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
QTY_TOL = 0.0005                        # tools/boq_export_v1 QTY_MATCH_TOL: the export's own quantity tolerance
SUM_TOL = 1e-4                          # declared totals vs the records' sums
RULE = ("R-LINE-STATE-1", "T-338")
REBAR_CODE = "STR.REBAR"
NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
KINDS = ("REBAR_FORMULA", "NA_GROSS", "FORMULA_END")
QUANTITY = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
CHANGE_KEYS = {"REBAR_FORMULA": ("calculation", "notes"), "NA_GROSS": ("calculation", "notes", "gross"),
               "FORMULA_END": ("calculation", "notes")}
# the T-334 reading of a printed formula (tools/t334_line_state_check.py, the export guard): a formula that OPENS with
# a hold word states a hold; its concluding figure is the last '= x <unit>' or 'net x <unit>'
HOLD_WORDS = ("held", "hold", "unresolved", "blocked", "conflict", "not measured", "not quantified", "unquantified")
HOLD_RE = re.compile(r"^\s*(?:" + "|".join(re.escape(w) for w in HOLD_WORDS) + r")\b", re.IGNORECASE)
DIA_RE = re.compile(r"/\s*(\d+(?:\.\d+)?)\s*mm\s*$")

PIECES = {
    "LINE_STATE_TEXT": {
        "module": "engine/source/arch_v3024.py (the T-334 line-state findings fixed in the lines' formula / notes text "
                  "and the gross of a taken-off line; no quantity, state, range or id changes)",
        "policy": "LINE_STATE_TEXT_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["UP-QTY-STATUS-001 (one state per line; held never 0)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.5 (evidence and release status kept apart)",
                        "owner 2026-10-24 23:57 downgrade-only record rules (a status never rises in this package)",
                        "ERS 2026-10-22 s.2.1 (state the physical element and what the figure is)"],
        "owner_manual_method": "the owner's manual method prints, per row, the arithmetic that gives the row's figure "
                               "(count x length x unit mass = kg for steel; length x height less openings = net for "
                               "faces); a row it does not take carries no figure: shown beside, the same rule here",
        "drawing_method": "no drawing is read: each line is corrected from its own record (the released ledger "
                          "record's count, length and bar diameter; the line's own net or range); the quantities "
                          "stay those of V3.0.23"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3023.WAITING)
WAITING.update({
    "LINE_STATE_FOR_LEAD": "lines whose state word itself may be wrong (valued but should be HELD, or the reverse) are "
                           "never fixed by a text change: listed in the inputs' for_lead with the reason",
})


# ================================================================================================ the T-334 reading
def hold_text(formula):
    return bool(HOLD_RE.match(str(formula or "")))


def concluding_figure(formula, unit):
    """the formula's concluding figure in the line's own unit -> (value, printed decimals) or (None, None)."""
    if not formula or not unit:
        return None, None
    pat = r"(?:=|\bnet)\s*(-?\d+(?:\.\d+)?)\s*" + re.escape(unit) + r"(?![A-Za-z0-9])"
    ms = list(re.finditer(pat, str(formula)))
    if not ms:
        return None, None
    x = ms[-1].group(1)
    return float(x), (len(x.split(".")[1]) if "." in x else 0)


def _formula(ln):
    return str(((ln.get("calculation") or {}).get("formula")) or "")


def _valued(ln):
    return ln.get("evidence_state") in QUANTITY and _num(ln.get("measured_net"))


def _end_disagrees(ln):
    """True when the formula's concluding figure is not the line's own quantity (T-334 FORMULA_FIGURE_DISAGREES)."""
    fig, dec = concluding_figure(_formula(ln), ln.get("unit"))
    if fig is None:
        return False
    tol = max(0.5 * 10 ** -dec, QTY_TOL) + 1e-9
    if _valued(ln):
        return abs(fig - ln["measured_net"]) > tol
    br = ln.get("bounded_range")
    if ln.get("evidence_state") not in QUANTITY and isinstance(br, dict):
        lo, hi = br.get("low"), br.get("high")
        return _num(lo) and _num(hi) and not (lo - tol <= fig <= hi + tol)
    return ln.get("evidence_state") not in QUANTITY and br is None


def scan(lines):
    """-> {line_id: (kind or None, reason)} for every line showing a finding this version handles or must list."""
    out = {}
    for ln in lines:
        lid, ev = ln["line_id"], ln.get("evidence_state")
        if _valued(ln) and hold_text(_formula(ln)):
            ok = (ln["item_code"] == REBAR_CODE and ln["unit"] == "kg" and ev == "SOURCE_DERIVED" and
                  (((ln.get("calculation") or {}).get("inputs") or {}).get("ledger_state")) == "RELEASED")
            out[lid] = ("REBAR_FORMULA" if ok else None, "a quantity line whose formula opens with a hold word")
        elif ev not in QUANTITY and _num(ln.get("gross")):
            out[lid] = ("NA_GROSS" if ev == NA_STATE else None, f"a {ev} line carrying a numeric gross")
        elif _end_disagrees(ln):
            br = ln.get("bounded_range")
            ok = _valued(ln) or (isinstance(br, dict) and _num(br.get("low")) and _num(br.get("high")))
            out[lid] = ("FORMULA_END" if ok else None, "the formula concludes on a figure that is not the line's own")
    return out


# ================================================================================================ inputs
def load_inputs(doc, project_id=None):
    """URBAN_V3024_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}] (the merged T-334 check),
         "unit_mass": {"method" (rebar_unit_mass.METHODS), "source"},
         "fixes": [{"line_id", "kind" (KINDS), "task"}],
         "for_lead": [{"line_id", "why"}] (lines kept as they are: a state question, never a text fix),
         "declared": {"REBAR_FORMULA": {"lines", "kg"}, "NA_GROSS": {"lines", "gross"}, "FORMULA_END": {"lines"}},
         "guard": as URBAN_V307_INPUTS_V1 "guard" (optional)}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged line-state check the fixes come from")
    tasks = set()
    for s in srcs:
        A3018._source(s, "sources")
        tasks.add(s["task"])
    um = doc.get("unit_mass") or {}
    try:
        UM.validate(_um_cfg(um))
    except UM.UnitMassError as e:
        raise InputsError(f"unit_mass: {e}") from None
    if not um.get("source"):
        raise InputsError("unit_mass: the source of the project's unit-mass method (never a default)")
    seen = set()
    fixes = doc.get("fixes") or []
    if not fixes:
        raise InputsError("no fixes")
    for i, f in enumerate(fixes):
        if f.get("kind") not in KINDS:
            raise InputsError(f"fix {i}: kind {f.get('kind')!r} not one of {KINDS}")
        if not f.get("line_id"):
            raise InputsError(f"fix {i}: line_id required")
        if f.get("task") not in tasks:
            raise InputsError(f"fix {f['line_id']}: task {f.get('task')!r} is not a source")
        if f["line_id"] in seen:
            raise InputsError(f"fix {f['line_id']}: a line listed twice (one fix per line)")
        seen.add(f["line_id"])
    for i, x in enumerate(doc.get("for_lead") or ()):
        if not (x.get("line_id") and x.get("why")):
            raise InputsError(f"for_lead {i}: {{line_id, why}}")
        if x["line_id"] in seen:
            raise InputsError(f"for_lead {x['line_id']}: a line both fixed and listed for the Lead")
        seen.add(x["line_id"])
    dec = doc.get("declared") or {}
    for k in KINDS:
        n = sum(1 for f in fixes if f["kind"] == k)
        d = (dec.get(k) or {}).get("lines")
        if d != n:
            raise InputsError(f"declared {k}.lines {d} != the fixes' {n}")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ fixes
def _um_cfg(um):
    return {k: v for k, v in um.items() if k != "source"}


def _fmt(x):
    s = f"{float(x):.6f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def rebar_arithmetic(ln, um):
    """-> (count, length_m, dia_mm, kg_per_m, product) of a released rebar line from its own record, or raise."""
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    lid = ln["line_id"]
    if inp.get("ledger_state") != "RELEASED" or ln["evidence_state"] != "SOURCE_DERIVED" or ln["unit"] != "kg":
        raise InputsError(f"rebar fix {lid}: not a released SOURCE_DERIVED kg ledger line")
    n, L = inp.get("count"), inp.get("length_m")
    if not (_num(n) and _num(L) and n > 0 and L > 0):
        raise InputsError(f"rebar fix {lid}: the record carries no numeric count / length_m ({n!r}, {L!r})")
    m = DIA_RE.search(str(ln.get("subtrade") or ""))
    if not m:
        raise InputsError(f"rebar fix {lid}: no bar diameter on the line (subtrade {ln.get('subtrade')!r})")
    d = float(m.group(1))
    kgm = UM.kg_per_m(d, _um_cfg(um))
    prod = n * L * kgm
    if abs(prod - ln["measured_net"]) > QTY_TOL:
        raise InputsError(f"rebar fix {lid}: count {n} x length {L} m x {_fmt(kgm)} kg/m = {_fmt(prod)} kg is not the "
                          f"line's {ln['measured_net']} kg: the quantity does not follow from its inputs (a state "
                          "question for the Lead, never a text fix)")
    return n, L, d, kgm, prod


def _record(before, kind, src, extra):
    return dict({"policy": PIECES["LINE_STATE_TEXT"]["policy"], "kind": kind, "task": src["task"],
                 "source": src["file"], "source_sha256": src["sha256"], "merge_commit": src["merge_commit"],
                 "checker_run": src["checker_run"], "before_formula": _formula(before),
                 "before_gross": before.get("gross"), "rule_id": RULE[0], "rule_version": RULE[1]}, **extra)


def fixed_line(before, kind, src, um):
    """-> (the fixed line, record). Only calculation / notes (and the gross of an NA line) change."""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    lid = before["line_id"]
    calc = ln["calculation"]
    if kind == "REBAR_FORMULA":
        if not hold_text(_formula(before)):
            raise InputsError(f"rebar fix {lid}: its formula does not open with a hold word (stale inputs)")
        n, L, d, kgm, prod = rebar_arithmetic(before, um)
        calc["formula"] = (f"{_fmt(n)} x {_fmt(L)} m x {_fmt(kgm)} kg/m ({_fmt(d)} mm, "
                           f"{UM.describe(_um_cfg(um))}) = {_fmt(before['measured_net'])} kg (released ledger record; "
                           f"product {_fmt(prod)} to 3 decimals; {METHOD})")
        rec = _record(before, kind, src, {"count": n, "length_m": L, "dia_mm": d, "kg_per_m": _r(kgm, 6),
                                          "product_kg": _r(prod, 6), "unit_mass_method": um["method"],
                                          "unit_mass_source": um["source"][:300]})
        note = (f"{METHOD}: the released quantity prints its arithmetic (count x length x unit mass) in place of the "
                f"empty 'held: ' text of the arch_v303 fallback; quantity and state unchanged")
    elif kind == "NA_GROSS":
        if before["evidence_state"] != NA_STATE or not _num(before.get("gross")):
            raise InputsError(f"NA fix {lid}: not a {NA_STATE} line with a numeric gross (stale inputs)")
        ln["gross"] = None
        rec = _record(before, kind, src, {})
        note = (f"{METHOD}: a line taken off carries no figure: gross {before['gross']} {before['unit']} removed "
                f"(kept in calculation.inputs.line_state_v3024.before_gross); state unchanged")
    elif kind == "FORMULA_END":
        if not _end_disagrees(before):
            raise InputsError(f"formula-end fix {lid}: its formula already ends on its own figure (stale inputs)")
        u = before["unit"]
        if _valued(before):
            end = f"net {_fmt(before['measured_net'])} {u}"
        else:
            br = before.get("bounded_range") or {}
            if not (_num(br.get("low")) and _num(br.get("high"))):
                raise InputsError(f"formula-end fix {lid}: a line without a quantity or a range (for the Lead)")
            end = f"held net {_fmt(br['low'])} {u} .. {_fmt(br['high'])} {u}"
        calc["formula"] = (f"{_formula(before)}; {METHOD}: this line {end} (an earlier figure is a gross or another "
                           f"element's reading, not this line's quantity)")
        rec = _record(before, kind, src, {"appended": end})
        note = f"{METHOD}: the formula now ends on the line's own figure ({end}); quantity and state unchanged"
    else:
        raise InputsError(f"fix {lid}: kind {kind!r}")
    calc.setdefault("inputs", {})["line_state_v3024"] = rec
    A305._note(ln, note)
    return BL.validate(ln), rec


def family_changes(doc, l3023):
    """-> (changes, log)."""
    by = {ln["line_id"]: ln for ln in l3023}
    found = scan(l3023)
    listed = {f["line_id"]: f["kind"] for f in doc["fixes"]}
    lead = {x["line_id"]: x["why"] for x in doc.get("for_lead") or ()}
    for lid in list(listed) + list(lead):
        if lid not in by:
            raise InputsError(f"line {lid}: the run carries no such line (stale inputs)")
    for lid, (kind, why) in sorted(found.items()):
        if lid in lead:
            continue
        if lid not in listed:
            raise InputsError(f"line {lid}: {why} ({kind or 'not a text fix'}) is neither fixed nor listed for the "
                              "Lead (the line-state family is integrated whole)")
        if kind is None:
            raise InputsError(f"line {lid}: {why}: not a text fix of this version; list it for the Lead")
        if kind != listed[lid]:
            raise InputsError(f"line {lid}: listed as {listed[lid]}, the line shows {kind}")
    for lid in listed:
        if lid not in found:
            raise InputsError(f"line {lid}: listed as {listed[lid]} but shows no finding (stale inputs)")
    um = doc["unit_mass"]
    changes = []
    log = {"piece": "LINE_STATE_TEXT", "state": "RUN", "sources": doc["sources"], "kinds": {}, "rebar_kg": 0.0,
           "na_gross": 0.0, "for_lead": sorted(lead)}
    for f in doc["fixes"]:
        b = by[f["line_id"]]
        src = A3018._src_of(doc, f["task"])
        after, rec = fixed_line(b, f["kind"], src, um)
        k = f["kind"]
        log["kinds"][k] = log["kinds"].get(k, 0) + 1
        if k == "REBAR_FORMULA":
            log["rebar_kg"] = _r(log["rebar_kg"] + b["measured_net"], 6)
        if k == "NA_GROSS":
            log["na_gross"] = _r(log["na_gross"] + b["gross"], 6)
        changes.append(A305._change("LINE_STATE_TEXT", "REPLACE", b, after, drawing_reference=None, held=[],
                                    downstream=[], verification={"task": src["task"],
                                                                 "merge_commit": src["merge_commit"],
                                                                 "verifier_run": src["checker_run"],
                                                                 "ledger": src["file"], "ledger_sha256": src["sha256"]},
                                    evidence_status=None, codes=["LINE_STATE_TEXT", k], group=k, record=rec))
    dec = doc.get("declared") or {}
    for k, key, v in (("REBAR_FORMULA", "kg", log["rebar_kg"]), ("NA_GROSS", "gross", log["na_gross"])):
        d = (dec.get(k) or {}).get(key)
        if (log["kinds"].get(k) or (d is not None)) and not (_num(d) and abs(d - v) <= SUM_TOL):
            raise InputsError(f"declared {k}.{key} {d} != the lines' {v}")
    return changes, log


def changes_for(doc, l3023):
    """-> (changes, logs). The guard re-check runs over the result (arch_v307) and may flag no line changed here."""
    if not doc:
        return [], [{"piece": "LINE_STATE_TEXT", "state": "NO_PROJECT_INPUT"}]
    ch, log = family_changes(doc, l3023)
    rep = {c["before"]["line_id"]: c["after"] for c in ch}
    view = [rep.get(ln["line_id"], ln) for ln in l3023]
    ch_g, log_g = A307.guard_changes(doc, view, [], set(rep))
    for c in ch_g:
        lid = c["before"]["line_id"]
        if lid in rep:
            raise ValueError(f"{METHOD}: the guard flags a line this version changes ({lid})")
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g]


# ================================================================================================ integrate / write
def check_line_state(lines, for_lead=()):
    """-> summary; every line outside for_lead shows none of the handled findings (else ValueError)."""
    left = {lid: v for lid, v in scan(lines).items() if lid not in set(for_lead)}
    if left:
        head = "; ".join(f"{k} {v[1]}" for k, v in sorted(left.items())[:5])
        raise ValueError(f"{METHOD}: {len(left)} line(s) still state two states: {head}")
    return {"lines": len(lines), "for_lead": len(set(for_lead)), "findings_left": 0}


def integrate(l3023, changes, doc=None):
    """-> (V3.0.24 lines, identity). Every line outside the V3.0.24 rows is byte-identical to the V3.0.23 line; inside
    a row only calculation / notes (and an NA line's gross) change; quantity, state, range, rfi and id never."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3023}
    rep, kinds = {}, {}
    for c in changes:
        if c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: action {c['action']} (this version adds no line)")
        lid = c["before"]["line_id"]
        if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
            raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.23, or its id changed")
        if c["piece"] != "LINE_STATE_TEXT":
            raise ValueError(f"{METHOD}: piece {c['piece']} changes line {lid} (only the line-state text changes)")
        rep[lid] = c["after"]
        kinds[lid] = (c.get("codes") or [None, None])[1]
    out = [rep.get(ln["line_id"], ln) for ln in l3023]
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
    state = check_line_state(out, [x["line_id"] for x in (doc or {}).get("for_lead") or ()]) if doc else None
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by23 = {ln["line_id"]: ln for ln in l3023}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by23[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3023):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.24 rows differ from {EXTENDS}")
    for lid, ln in rep.items():
        a, b = copy.deepcopy(by23[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in CHANGE_KEYS[kinds[lid]]:
                x.pop(k, None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside its formula / notes text")
        o = by23[lid]
        if (A30._qty(o) != A30._qty(ln) or o.get("bounded_range") != ln.get("bounded_range")
                or o.get("measured_net") != ln.get("measured_net") or o.get("rfi") != ln.get("rfi")):
            raise ValueError(f"{METHOD}: line {lid} changed its quantity, state, range or rfi")
        ci = {k: v for k, v in (o.get("calculation") or {}).items() if k not in ("formula", "inputs")}
        cn = {k: v for k, v in (ln.get("calculation") or {}).items() if k not in ("formula", "inputs")}
        oi = dict((o.get("calculation") or {}).get("inputs") or {})
        ni = dict((ln.get("calculation") or {}).get("inputs") or {})
        ni.pop("line_state_v3024", None)
        if ci != cn or oi != ni:
            raise ValueError(f"{METHOD}: line {lid} changed its calculation beyond the formula and its own record")
    ident = {"v3_0_23_lines": len(l3023), "v3_0_24_lines": len(out), "v3_0_24_rows": len(changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "by_kind": A302._count(kinds.values()), "outside_rows_identical_to_v3_0_23": len(outside),
             "line_state": state, "parapet_family": par, "wall_tile_family": tile,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref, b = c["after"], c["before"]
        rec = (ref["calculation"].get("inputs") or {}).get("line_state_v3024") or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "kind": (c.get("codes") or [None, None])[1],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "subtrade": ref.get("subtrade"),
                     "before_released_v2_9": b29, "before_v3_0_23": A30._qty(b), "after_v3_0_24": A30._qty(ref),
                     "before_formula": _formula(b), "after_formula": _formula(ref),
                     "before_gross": b.get("gross"), "after_gross": ref.get("gross"), "record": rec,
                     "release_status": "NOT RELEASED", "owner_manual_method": PIECES["LINE_STATE_TEXT"][
                         "owner_manual_method"], "drawing_derived_method": PIECES["LINE_STATE_TEXT"]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "kind", "line_id", "item_code", "floor", "element_id", "unit", "subtrade", "v2_9", "v3_0_23",
              "v3_0_24", "before_gross", "after_gross", "before_formula", "after_formula", "release_status",
              "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_23", "vs_released_v2_9", "v2_9",
            "v3_0_23", "v3_0_24")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "kind": r["kind"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "subtrade": r["subtrade"] or "",
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_23": A302._q(r["before_v3_0_23"]), "v3_0_24": A302._q(r["after_v3_0_24"]),
                       "before_gross": "" if r["before_gross"] is None else r["before_gross"],
                       "after_gross": "" if r["after_gross"] is None else r["after_gross"],
                       "before_formula": r["before_formula"][:300], "after_formula": r["after_formula"][:400],
                       "release_status": r["release_status"],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''}"
                                       f" {r['verification'].get('verifier_run') or ''}".strip()[:300]}
                      for r in rows if r["piece"] == "LINE_STATE_TEXT"], LEDGER_CSV)


def diff_rows(l3023, l3024, released_lines=None):
    b23 = {ln["line_id"]: ln for ln in l3023}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3024:
        o = b23.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_23": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_23": A302._q(A30._qty(o)) if o else "", "v3_0_24": A302._q(A30._qty(ln))})
    return out


def write(out, l3023, changes, logs, doc, released_lines=None):
    """the V3_0_24_* files beside the V3_0_23_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3024, ident = integrate(l3023, changes, doc)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3023, l3024, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_23", {}).setdefault(d["vs_v3_0_23"], 0)
        dsum["vs_v3_0_23"][d["vs_v3_0_23"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    if (dsum.get("vs_v3_0_23") or {}).get("CHANGED") or (dsum.get("vs_v3_0_23") or {}).get("ADDED"):
        raise ValueError(f"{METHOD}: a quantity or a line moved against {EXTENDS} (text-only version)")
    ident = dict(ident, diff=dsum)
    t23, t24 = A304.code_totals(l3023), A304.code_totals(l3024)
    moved = {k: {"v3_0_23": t23.get(k), "v3_0_24": t24.get(k)} for k in sorted(set(t23) | set(t24))
             if t23.get(k) != t24.get(k)}
    if moved:
        raise ValueError(f"{METHOD}: totals moved by code {sorted(moved)[:5]} (text-only version)")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "for_lead": doc.get("for_lead") or [], "unit_mass": doc.get("unit_mass"), "waiting_pieces": WAITING,
           "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "kind_counts": A302._count(r["kind"] for r in rows)}
    files = {"V3_0_24_BOQ_LINES.json": BL.dumps(l3024),
             "V3_0_24_BOQ_LINES.csv": A30._lines_csv(l3024),
             "V3_0_24_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_24_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_24_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_24_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "hold_text",
           "concluding_figure", "scan", "rebar_arithmetic", "fixed_line", "family_changes", "changes_for",
           "check_line_state", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
