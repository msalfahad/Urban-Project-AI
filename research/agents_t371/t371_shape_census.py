"""T-371 bar-shape source census for B11-02 (bar bending schedule): research only, unwired; every villa.

For every bar population of the released rebar route and the candidate (footings, necks, columns, ground / strap
beams, beams, slabs) this module records which SHAPE attributes the drawings print (body shape, each end, leg length,
hook, bend diameter, crank) and from that whether a bar bending schedule line of that population can carry a shape now,
after a named RFI, or only after a NEW gap is asked. It computes NO kg, NO bar count and NO length (owner 2026-10-25
10:33; ENGINEERING_REASONING_STANDARD s.3: the notation is read before any arithmetic).

Attribute states:
  PRINTED              printed for this population (sheet / detail / handle or position in `ref`)
  PRINTED_TYPICAL      printed on a typical detail whose own title names this element class (`applies_to` must equal
                       the population's `element_class`: a typical of another element is never borrowed)
  PRINTED_MINIMUM      printed as a minimum ('Min. 30cm'): a bound, not a schedulable exact value
  DRAWN_UNDIMENSIONED  the part is drawn but not dimensioned (owner option B 2026-10-29: counted only where drawn and
                       dimensioned; the leg / hook is HELD, never given a length)
  NOT_PRINTED          the set prints nothing for it
  NOT_APPLICABLE       the attribute does not exist for this shape (a straight bar has no hook)
  RULE                 settled by an ANSWERED owner rule (`rule` must be in the register's answered_rules)
  CONFLICT             two prints disagree (`refs` lists both); blocking, never resolved by choice

Population status:
  SCHEDULABLE_NOW    every attribute is PRINTED / PRINTED_TYPICAL / NOT_APPLICABLE / RULE
  SCHEDULABLE_AFTER  every blocking attribute names an RFI id of the register (rfi/A or rfi/B)
  GAP                at least one blocking attribute is asked in no RFI: it carries a NEW gap id for the Lead
  OWNED_ELSEWHERE    the population's open item is another census's (lap length T-366, special elements T-359)

Repeat: python -I t371_shape_census.py ALSENAN_BAR_SHAPE_INPUT.json LINE_BINDING_T371.json --csv T371_MATRIX.csv
        --json T371_SUMMARY.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys

POLICY = "BAR_SHAPE_SOURCE_CENSUS_V1"
ATTRS = ("body", "end_1", "end_2", "leg_length", "hook", "bend_diameter", "crank")
OK_STATES = {"PRINTED", "PRINTED_TYPICAL", "NOT_APPLICABLE", "RULE"}
BLOCKING = {"PRINTED_MINIMUM", "DRAWN_UNDIMENSIONED", "NOT_PRINTED", "CONFLICT"}
STATES = OK_STATES | BLOCKING
STATUSES = ("SCHEDULABLE_NOW", "SCHEDULABLE_AFTER", "GAP", "OWNED_ELSEWHERE")
FORBIDDEN_KEYS = re.compile(r"(^|_)(kg|mass|tonnes?|weight)($|_)", re.I)
LENGTH_KEYS = ("value_m", "length_m", "leg_m", "hook_m")

# ---- notation (read before any arithmetic) -------------------------------------------------------------------------
_SYM = r"(?:ø|Ø|%%c|%%C|φ|Φ|T|Y)"
COUNT, RATE, SPACING, COUNT_PER_SPACING, UNKNOWN = "COUNT", "RATE", "SPACING", "COUNT_PER_SPACING", "UNKNOWN"


def parse_notation(text: str) -> dict:
    """Classify a bar label. Only 'n ø d' is a count; 'n ø d/m' is a rate (bars per metre), 'ø d/s cm' a spacing."""
    t = (text or "").replace(" ", "")
    m = re.fullmatch(rf"(\d+){_SYM}(\d+)/m", t, re.I)
    if m:
        return {"kind": RATE, "n_per_m": int(m.group(1)), "d": int(m.group(2)), "count": None}
    m = re.fullmatch(rf"{_SYM}(\d+)(?:/|@)(\d+)(cm|mm)?", t, re.I)
    if m:
        unit = m.group(3)
        s = None if unit is None else int(m.group(2)) / (100.0 if unit.lower() == "cm" else 1000.0)
        return {"kind": SPACING, "d": int(m.group(1)), "s_m": s, "unit_printed": unit is not None, "count": None}
    m = re.fullmatch(rf"(\d+){_SYM}(\d+)/(\d+)(cm|mm)?", t, re.I)
    if m:
        return {"kind": COUNT_PER_SPACING, "n": int(m.group(1)), "d": int(m.group(2)), "count": None}
    m = re.fullmatch(rf"(\d+){_SYM}(\d+)", t, re.I)
    if m:
        return {"kind": COUNT, "count": int(m.group(1)), "d": int(m.group(2))}
    return {"kind": UNKNOWN, "count": None}


def count_from_label(text: str) -> int:
    """A bar count is taken only from an explicit 'n ø d' label; a rate or a spacing is refused as a count."""
    p = parse_notation(text)
    if p["kind"] != COUNT:
        raise ValueError(f"'{text}' is a {p['kind']}, not a count: a spacing or rate is never read as a bar count")
    return p["count"]


# ---- validation ------------------------------------------------------------------------------------------------------
def _walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}", k
            yield from _walk_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_keys(v, f"{path}[{i}]")


def check_attr(pop: dict, name: str, a: dict, register: dict) -> None:
    pid = pop["pop_id"]
    st = a.get("state")
    if st not in STATES:
        raise ValueError(f"{pid}.{name}: unknown state {st!r}")
    if st in ("PRINTED", "PRINTED_TYPICAL", "PRINTED_MINIMUM", "DRAWN_UNDIMENSIONED") and not a.get("ref"):
        raise ValueError(f"{pid}.{name}: {st} needs a sheet / detail / handle ref")
    if st == "PRINTED_TYPICAL" and a.get("applies_to") != pop["element_class"]:
        raise ValueError(f"{pid}.{name}: typical detail of {a.get('applies_to')!r} borrowed for "
                         f"{pop['element_class']!r}: a typical of another element is never applied")
    if st == "RULE" and a.get("rule") not in register.get("answered_rules", []):
        raise ValueError(f"{pid}.{name}: RULE {a.get('rule')!r} is not an answered owner rule")
    if st == "CONFLICT" and len(a.get("refs", [])) < 2:
        raise ValueError(f"{pid}.{name}: CONFLICT needs both refs")
    for k in LENGTH_KEYS:
        if a.get(k) is not None and st not in ("PRINTED", "PRINTED_TYPICAL"):
            raise ValueError(f"{pid}.{name}: a length is given to a {st} part: an undimensioned / unprinted leg or "
                             f"hook never gets a length (owner option B)")
    if st in BLOCKING and not (a.get("rfi") or a.get("gap") or pop.get("owned_by")):
        raise ValueError(f"{pid}.{name}: blocking {st} names no RFI, no gap and no owning census")
    if a.get("rfi") and a["rfi"] not in register.get("rfi_register", []):
        raise ValueError(f"{pid}.{name}: RFI {a['rfi']!r} is not in the RFI register")


def check_population(pop: dict, register: dict) -> None:
    for path, k in _walk_keys(pop):
        if FORBIDDEN_KEYS.search(k):
            raise ValueError(f"{pop.get('pop_id')}: field {path} is a mass: the census computes no kg")
    for k in ("pop_id", "element_class", "description", "attrs"):
        if k not in pop:
            raise ValueError(f"population without {k}: {pop.get('pop_id')}")
    missing = [a for a in ATTRS if a not in pop["attrs"]]
    if missing:
        raise ValueError(f"{pop['pop_id']}: attributes missing {missing}")
    for name in ATTRS:
        check_attr(pop, name, pop["attrs"][name], register)
    if pop.get("count_label"):
        count_from_label(pop["count_label"])


def status(pop: dict) -> tuple[str, list[str]]:
    blocking = [(n, pop["attrs"][n]) for n in ATTRS if pop["attrs"][n]["state"] in BLOCKING]
    if not blocking:
        return "SCHEDULABLE_NOW", []
    if pop.get("owned_by") and all(not a.get("rfi") and not a.get("gap") for _, a in blocking):
        return "OWNED_ELSEWHERE", [pop["owned_by"]]
    ids = sorted({a.get("gap") or a.get("rfi") for _, a in blocking if a.get("gap") or a.get("rfi")})
    if any(a.get("gap") for _, a in blocking):
        return "GAP", ids
    return "SCHEDULABLE_AFTER", ids


def check_binding(data: dict, binding: dict) -> dict:
    """Every candidate reinforcement line bound once to an existing population (or to a named other census)."""
    pops = {p["pop_id"] for p in data["populations"]}
    if len(pops) != len(data["populations"]):
        raise ValueError("duplicate population id")
    others = set(data["register"].get("other_census", []))
    lines = binding["lines"]
    if len(set(lines)) != len(lines):
        raise ValueError("a candidate line is bound twice")
    expected = set(binding["candidate_line_ids"])
    if set(lines) != expected:
        miss = sorted(expected - set(lines))[:3]
        extra = sorted(set(lines) - expected)[:3]
        raise ValueError(f"binding incomplete: unbound {miss} / unknown {extra}")
    per = {}
    for lid, pid in lines.items():
        if pid not in pops and pid not in others:
            raise ValueError(f"line {lid} bound to unknown population {pid}")
        per[pid] = per.get(pid, 0) + 1
    return per


def leg_bound_proposal(pop: dict) -> dict:
    """F-T318-1 (Checker): a drawn, undimensioned slab-end leg may later be bounded from the drawing. Returned as a
    PROPOSAL text only: never a value (owner option B: the leg stays HELD blank)."""
    leg = pop["attrs"]["leg_length"]
    if leg["state"] != "DRAWN_UNDIMENSIONED":
        raise ValueError(f"{pop['pop_id']}: a bound is proposed only for a drawn, undimensioned leg")
    return {"pop_id": pop["pop_id"], "status": "PROPOSAL_ONLY", "value": None,
            "basis": pop.get("leg_bound_basis", ""), "holds_under": "owner option B 2026-10-29: leg HELD blank"}


def run(data: dict, binding: dict) -> dict:
    reg = data["register"]
    for p in data["populations"]:
        check_population(p, reg)
    per = check_binding(data, binding)
    rows, counts = [], {s: 0 for s in STATUSES}
    for p in data["populations"]:
        st, ids = status(p)
        if st == "SCHEDULABLE_NOW" and per.get(p["pop_id"], 0) == 0 and not p.get("no_line_reason"):
            raise ValueError(f"{p['pop_id']}: no candidate line and no reason")
        counts[st] += 1
        row = {"pop_id": p["pop_id"], "element_class": p["element_class"], "description": p["description"],
               "status": st, "blocking_ids": ";".join(ids), "candidate_lines": per.get(p["pop_id"], 0),
               "no_line_reason": p.get("no_line_reason", "")}
        for n in ATTRS:
            a = p["attrs"][n]
            row[f"{n}"] = a["state"] + (f": {a['value']}" if a.get("value") else "")
            row[f"{n}_ref"] = a.get("ref", "") or " / ".join(a.get("refs", []))
        rows.append(row)
    proposals = [leg_bound_proposal(p) for p in data["populations"] if p.get("leg_bound_basis")]
    other = {k: v for k, v in per.items() if k in set(reg.get("other_census", []))}
    return {"policy": POLICY, "populations": len(rows), "status_counts": counts, "rows": rows,
            "lines_bound": sum(per.values()), "lines_to_other_census": other, "leg_bound_proposals": proposals,
            "gaps": data.get("gaps", {}), "findings": data.get("findings", [])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("binding")
    ap.add_argument("--csv")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    data = json.load(open(a.input, encoding="utf-8"))
    binding = json.load(open(a.binding, encoding="utf-8"))
    out = run(data, binding)
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out["rows"][0]))
            w.writeheader()
            w.writerows(out["rows"])
    summary = {k: v for k, v in out.items() if k != "rows"}
    if a.json:
        json.dump(summary, open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summary["status_counts"]), "lines bound", summary["lines_bound"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
