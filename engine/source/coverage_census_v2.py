"""COVERAGE CENSUS V2 (T-140) - one terminal state per BOQ family of BOQ_FAMILY_MASTER 1.1.0, with the line count and
the quantity of every unit apart (generic; stdlib).

    load_master(path=None)                                     -> the 1.1.0 master (sha256 checked against the manifest)
    census(lines, *, master=None, family_coverage=None, material_results=(), structural_run=None, arch_run=None,
           run_kind=None)                                      -> (rows (one per family, master order), run meta)
    summary(rows, census_meta=None)                            -> counts
    compare(v1_rows, v2_rows)                                  -> per family: census V1 state vs V2 state

Beside the existing census (engine/source/coverage_census.py, which keeps reading 1.0.0 for the released run and is not
changed). V2 maps every family to the line keys (item codes) that 1.1.0 itself records per family ('item_codes', each
code owned by one family only), so a family the released run answers is no longer reported NOT_FOUND_IN_SOURCE just
because the 1.0.0-era map lacked its code (T-130 census gaps: B8-03 FIN.WP.WALL_UPTURN, B6-02 .. B6-04, B9-01 wall
lines, B3-04 thresholds, B2-02 spaces).

States (one per family, each with its reason):
    FOUND                at least one line in a quantity state (MEASURED / SOURCE_DERIVED / PROVISIONAL) in a unit the
                         family is measured in
    HELD                 lines exist but none carries a quantity in the family's unit (bounded, blocked, or a quantity
                         only in another unit, e.g. a wall run in lm for block m2): quantity UNKNOWN, never 0
    EXCLUDED             every line is EXCLUDED_WITH_REASON / NOT_APPLICABLE_WITH_EVIDENCE
    COUNTED_IN_PARENT    no line; the route's own family census says the family sits inside another line
    NOT_FOUND_IN_SOURCE  the family has line keys, the route that emits them ran, and it produced none
    NOT_RUN              the family has line keys but the route that emits them did not run, or (run_kind) the
                         released method / the V3.0 candidate does not produce the family (1.1.0 fields)
    NO_LINE_KEY          the capability exists but writes no BOQ line (1.1.0 'item_codes' is empty): the reason says
                         where it is measured, if anywhere
    NOT_IMPLEMENTED      no capability (1.1.0 'capability')
    BLOCKED_BY_SOURCE    the capability needs documents the engine does not read

Quantities per unit, never mixed across units (owner management decision 2026-10-20 §3; UP-QTY-STATUS-001): 'found'
sums measured_net of quantity-state lines; held lines are counted apart, their bounded ranges summed apart as a
range ('complete' false while any held line is unbounded); the held quantity itself is always "UNKNOWN", never 0.
Of two lines one of which names the other never-additive, one is summed (as boq_line.totals, but independent of the
line order). Nothing here changes a line or a quantity; reinforcement is read only to report which families' steel
is missing (no ratio, no kg written).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from engine.source import boq_line as BL
from engine.source import coverage_census as CS1

CENSUS_VERSION = "URBAN_COVERAGE_CENSUS_V2"
ROOT = Path(__file__).resolve().parents[2]
MASTER_REL = "coverage/BOQ_FAMILY_MASTER_1.1.0.json"
STATES = ("FOUND", "HELD", "EXCLUDED", "COUNTED_IN_PARENT", "NOT_FOUND_IN_SOURCE", "NOT_RUN", "NO_LINE_KEY",
          "NOT_IMPLEMENTED", "BLOCKED_BY_SOURCE")
HELD_EVIDENCE = ("BOUNDED_EXPOSURE", "BLOCKED_RFI")
EXCLUDED_EVIDENCE = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
# route G family census state -> V2 state when NO line of the family exists (a route census never makes a family
# FOUND: a quantity that no BOQ line carries is not in the BOQ)
ROUTE_STATE = {"QUANTIFIED": "HELD", "PARTLY_QUANTIFIED": "HELD", "BOUNDED_NOT_MEASURED": "HELD",
               "DETECTED_NOT_QUANTIFIED": "HELD", "NO_EVIDENCE_FOUND": "NOT_FOUND_IN_SOURCE",
               "COUNTED_IN_PARENT": "COUNTED_IN_PARENT"}
_UNIT_RE = re.compile(r"[a-z0-9]+")


class MasterError(ValueError):
    pass


def load_master(path=None):
    """the 1.1.0 family master; the default file must match its sha256 in rules/RULES_MANIFEST.json."""
    p = Path(path) if path else ROOT / "rules" / MASTER_REL
    raw = p.read_bytes()
    if path is None:
        man = json.loads((ROOT / "rules" / "RULES_MANIFEST.json").read_text(encoding="utf-8"))
        want = man["files"][MASTER_REL]["sha256"]
        got = hashlib.sha256(raw).hexdigest()
        if got != want:
            raise MasterError(f"{MASTER_REL} sha256 {got} differs from the manifest {want}")
    m = json.loads(raw.decode("utf-8"))
    validate_master(m)
    return m


def validate_master(m):
    if m.get("master") != "URBAN_BOQ_FAMILY_MASTER":
        raise MasterError("not a BOQ family master")
    caps = set(m.get("capability_states") or ())
    seen, owner = set(), {}
    for f in m["families"]:
        if f["code"] in seen:
            raise MasterError(f"family {f['code']} listed twice")
        seen.add(f["code"])
        if f["capability"] not in caps:
            raise MasterError(f"{f['code']}: capability {f['capability']} is not in the master's vocabulary")
        for ic in f.get("item_codes") or ():
            if ic in owner:
                raise MasterError(f"item code {ic} is owned by {owner[ic]} and {f['code']}")
            owner[ic] = f["code"]
    both = set(owner) & set(m.get("item_codes_without_family") or {})
    if both:
        raise MasterError(f"item codes both owned and listed without family: {sorted(both)}")
    return owner


# count words of the master's unit texts that a line carries as pieces ('m2 / rolls' -> membrane roll lines in pcs)
UNIT_WORDS = {"rolls": "pcs", "bags": "pcs"}


def family_units(unit_text):
    """the line units a family's master unit text names ('m2 + lm' -> {'m2', 'lm'}; 'm2 / rolls' -> {'m2', 'pcs'};
    '-' -> empty)."""
    words = (UNIT_WORDS.get(u, u) for u in _UNIT_RE.findall(str(unit_text or "").lower()))
    return {u for u in words if u in BL.UNITS}


def _additive(lines):
    """(kept lines, ids not summed): of two lines one of which names the other never-additive, the first in the list
    is summed and the other is not, whichever of the two carries the name (boq_line.totals drops only a named line
    that comes later; here the order of the list never decides whether the pair is summed once)."""
    kept_ids, skip, kept, dropped = set(), set(), [], set()
    for ln in lines:
        lid = ln["line_id"]
        names = set(ln.get("never_additive_with") or ())
        if lid in skip or names & kept_ids:
            dropped.add(lid)
            continue
        kept_ids.add(lid)
        skip.update(names)
        kept.append(ln)
    return kept, dropped


def _cell():
    return {"found_lines": 0, "found_qty": 0.0, "held_lines": 0, "held_bounded_lines": 0, "held_bounded_low": 0.0,
            "held_bounded_high": 0.0, "held_unbounded_lines": 0, "excluded_lines": 0, "not_summed_lines": 0}


def _by_unit(ls, dropped):
    out = {}
    for ln in ls:
        c = out.setdefault(ln["unit"], _cell())
        ev = ln["evidence_state"]
        if ln["line_id"] in dropped:
            c["not_summed_lines"] += 1
        elif ev in BL.QUANTITY_STATES:
            c["found_lines"] += 1
            c["found_qty"] += ln["measured_net"]
        elif ev in HELD_EVIDENCE:
            c["held_lines"] += 1
            br = ln.get("bounded_range") or {}
            if ev == "BOUNDED_EXPOSURE" and br.get("low") is not None and br.get("high") is not None:
                c["held_bounded_lines"] += 1
                c["held_bounded_low"] += br["low"]
                c["held_bounded_high"] += br["high"]
            else:
                c["held_unbounded_lines"] += 1
        elif ev in EXCLUDED_EVIDENCE:
            c["excluded_lines"] += 1
        else:
            raise ValueError(f"{ln['line_id']}: evidence state {ev} is not a canonical line state")
    for c in out.values():
        c["found_qty"] = round(c["found_qty"], 6) if c["found_lines"] else None
        if c["held_lines"]:
            # HELD counts as UNKNOWN: the range covers the bounded lines only; any unbounded line leaves it open
            c["held_qty"] = "UNKNOWN"
            c["held_range"] = ({"low": round(c["held_bounded_low"], 6), "high": round(c["held_bounded_high"], 6),
                                "complete": c["held_unbounded_lines"] == 0} if c["held_bounded_lines"] else None)
        else:
            c["held_qty"], c["held_range"] = None, None
        del c["held_bounded_low"], c["held_bounded_high"]
    return dict(sorted(out.items()))


def _route_of(codes):
    kinds = {"STR" if c.startswith("STR.") else "ARCH" for c in codes}
    return kinds


def census(lines, *, master=None, family_coverage=None, material_results=(), structural_run=None, arch_run=None,
           run_kind=None):
    """run_kind: None, "released" (the released configuration: a family whose 1.1.0 'released_method_reads' is
    'none' and has no line is NOT_RUN, never NOT_FOUND_IN_SOURCE) or "candidate" (the V3.0 candidate: a family with
    'in_v3_0_candidate' 'no' and no line is NOT_RUN)."""
    if run_kind not in (None, "released", "candidate"):
        raise ValueError(f"run_kind {run_kind}")
    lines = list(lines)
    for ln in lines:
        BL.validate(ln)
    m = master if master is not None else load_master()
    owner = validate_master(m)
    without = m.get("item_codes_without_family") or {}
    if structural_run is None:
        structural_run = family_coverage is not None or any(ln["item_code"].startswith("STR.") for ln in lines)
    if arch_run is None:
        arch_run = any(not ln["item_code"].startswith("STR.") for ln in lines)
    kept, dropped = _additive(lines)
    by_code = {}
    for ln in lines:
        by_code.setdefault(ln["item_code"], []).append(ln)
    cov = {}
    for rec in family_coverage or []:
        code = CS1.COVERAGE_FAMILY.get(rec["FAMILY"])
        if code:
            cov.setdefault(code, []).append(rec)
    rows = []
    for f in m["families"]:
        code, cap, codes = f["code"], f["capability"], list(f.get("item_codes") or ())
        ls = [ln for ic in codes for ln in by_code.get(ic, [])]
        ev = Counter(ln["evidence_state"] for ln in ls)
        units = _by_unit(ls, dropped)
        flags = []
        state = reason = None
        fu = family_units(f.get("unit"))
        found_units = {u for u, c in units.items() if c["found_lines"]}
        if found_units and fu and not (found_units & fu):
            # a quantity only in a unit the family is not paid in (a wall run in lm for block m2) is geometry, not
            # the family's quantity: the family stays HELD
            state = "HELD"
            flags.append("QUANTITY_ONLY_OUTSIDE_FAMILY_UNIT")
        elif found_units:
            state = "FOUND"
        elif any(c["held_lines"] for c in units.values()):
            state = "HELD"
        elif ls and all(ln["evidence_state"] in EXCLUDED_EVIDENCE or ln["line_id"] in dropped for ln in ls):
            state = "EXCLUDED" if any(c["excluded_lines"] for c in units.values()) else "COUNTED_IN_PARENT"
        if state:
            per = "; ".join(f"{u}: {c['found_lines']} found, {c['held_lines']} held, {c['excluded_lines']} excluded"
                            for u, c in units.items())
            reason = f"{len(ls)} line(s) under {', '.join(sorted({ln['item_code'] for ln in ls}))} ({per})"
        route = "; ".join(f"{r['FAMILY']}: {r['STATE']}" for r in cov.get(code, ()))
        if state is None and code in cov:
            cs = sorted((ROUTE_STATE[r["STATE"]] for r in cov[code]), key=STATES.index)
            state = cs[0]
            reason = (f"no BOQ line; route G family census: " + "; ".join(
                f"{r['FAMILY']}: {r['STATE']} ({r.get('REASON') or r.get('EVIDENCE') or ''})" for r in cov[code]))[:400]
        if state is None and code == "B11-03" and structural_run:
            scope = [ln for ln in lines if ln["item_code"].startswith("STR.CONC.") and
                     (ln.get("physical_element") or "") in CS1.SCOPE_REBAR_FAMILIES and
                     ln["evidence_state"] != "BLOCKED_RFI"]
            steel = [ln for ln in lines if ln["item_code"] == "STR.REBAR" and
                     (ln.get("physical_element") or "") in CS1.SCOPE_REBAR_FAMILIES]
            if scope and not steel:
                state, reason = "HELD", (f"MISSING_DATA: {len(scope)} concrete line(s) of these families carry no bar "
                                         f"model (no kg/m3 ratio is ever used); quantity UNKNOWN")
        if state is None and code == "B8-05":
            mem = [r for r in material_results if (r.get("material_spec") or {}).get("kind") == "MEMBRANE_SHEET"]
            done = [r for r in mem if r["state"] != "BLOCKED"]
            if done:
                state, reason = "FOUND", (f"{len(done)} room roll plan(s) in the material results (procurement view, "
                                          f"never the BOQ net); no BOQ line")
                flags.append("FOUND_IN_MATERIAL_RESULTS_ONLY")
            elif mem:
                state, reason = "HELD", f"membrane roll plans blocked: {mem[0].get('blocked_by')}"
        if state is None:
            if cap == "NOT_IMPLEMENTED":
                state, reason = "NOT_IMPLEMENTED", f"no engine capability yet (next slice {f.get('next_slice')})"
            elif cap == "BLOCKED_BY_SOURCE":
                state, reason = "BLOCKED_BY_SOURCE", f"needs {f.get('source_needed')}"
            elif not codes:
                state, reason = "NO_LINE_KEY", (f"capability {cap} writes no BOQ line (1.1.0 item_codes empty); "
                                                f"released: {f.get('released_method_reads') or '-'}; missing: "
                                                f"{f.get('missing') or '-'}")[:400]
            elif run_kind == "released" and str(f.get("released_method_reads") or "").startswith("none"):
                state, reason = "NOT_RUN", (f"the released method emits no line of this family (1.1.0 "
                                            f"released_method_reads: {f.get('released_method_reads')}; opt-in: "
                                            f"{f.get('opt_in_readers')})")[:400]
            elif run_kind == "candidate" and f.get("in_v3_0_candidate") == "no":
                state, reason = "NOT_RUN", (f"the V3.0 candidate does not produce this family (1.1.0 "
                                            f"in_v3_0_candidate: no; opt-in: {f.get('opt_in_readers')})")[:400]
            else:
                kinds = _route_of(codes)
                ran = ("STR" in kinds and structural_run) or ("ARCH" in kinds and arch_run)
                if ran:
                    state, reason = "NOT_FOUND_IN_SOURCE", (f"the route that emits {', '.join(codes)} ran and "
                                                            f"produced no line")
                else:
                    state, reason = "NOT_RUN", ("no structural drawing in this run" if kinds == {"STR"} else
                                                "no architectural plan in this run")
        if cap in ("NOT_IMPLEMENTED", "BLOCKED_BY_SOURCE") and ls:
            flags.append(f"CAPABILITY_{cap}_BUT_LINES_EMITTED")
        off = sorted(u for u in units if fu and u not in fu)
        if off:
            flags.append("LINE_UNIT_OUTSIDE_FAMILY_UNIT: " + ", ".join(off))
        if any(c["not_summed_lines"] for c in units.values()):
            flags.append("NEVER_ADDITIVE_LINES_NOT_SUMMED")
        rows.append({"code": code, "group": f["group"], "item_en": f["item_en"], "item_ar": f["item_ar"],
                     "family_unit": f.get("unit"), "capability": cap, "in_v3_0_candidate": f.get("in_v3_0_candidate"),
                     "item_codes": codes, "run_state": state, "lines": len(ls),
                     "evidence": dict(sorted(ev.items())), "by_unit": units, "reason": reason,
                     "route_census": route or None, "flags": flags, "next_slice": f.get("next_slice")})
    bad = [r["code"] for r in rows if r["run_state"] not in STATES or not r["reason"]]
    if bad:
        raise ValueError(f"families without a terminal state or reason: {bad}")
    seen = Counter(ln["item_code"] for ln in lines)
    meta = {"census": CENSUS_VERSION, "master_version": m.get("version"), "lines": len(lines),
            "lines_not_summed_never_additive": len(dropped), "structural_run": bool(structural_run),
            "arch_run": bool(arch_run),
            "codes_without_family": {c: {"lines": n, "why": without[c]} for c, n in sorted(seen.items())
                                     if c not in owner and c in without},
            "unowned_codes": {c: n for c, n in sorted(seen.items()) if c not in owner and c not in without}}
    return rows, meta


def summary(rows, census_meta=None):
    out = {"census": CENSUS_VERSION, "families": len(rows),
           "by_run_state": dict(sorted(Counter(r["run_state"] for r in rows).items())),
           "by_capability": dict(sorted(Counter(r["capability"] for r in rows).items())),
           "silent_omissions": 0}
    if census_meta is not None:
        out["unowned_codes"] = census_meta["unowned_codes"]
        out["silent_omissions"] = sum(census_meta["unowned_codes"].values())
    return out


def compare(v1_rows, v2_rows):
    """census V1 (1.0.0 map) vs V2 per family code; V1 QUANTIFIED / BOUNDED_ONLY / BLOCKED have no V2 twin by name."""
    v1 = {r["code"]: r for r in v1_rows}
    out = []
    for r in v2_rows:
        a = v1.get(r["code"])
        out.append({"code": r["code"], "v1_state": a["run_state"] if a else None, "v1_lines": a["lines"] if a else None,
                    "v2_state": r["run_state"], "v2_lines": r["lines"], "item_codes": r["item_codes"],
                    "changed_lines": (a["lines"] if a else None) != r["lines"]})
    return out
