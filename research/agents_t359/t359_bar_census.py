"""T-359 bar-detail source census (research only, unwired; every villa).

For the elements outside the released rebar route (stairs, pool, domes, roof tank, lift pit, boundary wall) this module
records, per bar population, which attributes the drawings PRINT and which they do not, and from that whether the
population is countable now, countable after a named RFI, owned by another line, or not drawn at all.

It computes NO kg and NO bar count: it reads the notation before any arithmetic (ENGINEERING_REASONING_STANDARD s.3,
owner 2026-10-25 10:33: no reinforcement calculation change before approval).

Attribute states:
  PRINTED          the set prints it for this population (sheet, detail, handle or position given)
  PRINTED_TYPICAL  printed only on a typical / N.T.S. detail that no project print ties to this element
  NOT_PRINTED      the set does not print it
  NOT_APPLICABLE   the attribute does not exist for this population (e.g. a single nosing bar has no spacing)
  RULE             not printed, but an answered owner rule settles it (rule id given)

Population status:
  COUNTABLE_NOW       every attribute it needs is PRINTED / RULE / NOT_APPLICABLE
  COUNTABLE_AFTER     each blocking attribute is named in an existing RFI (ids validated against the RFI register)
  GAP                 at least one blocking attribute is asked nowhere: a NEW gap id for the Lead
  OWNED_ELSEWHERE     the population belongs to a line of another ledger (beam / slab / footing); never counted here
  NOT_DRAWN           the element exists but no bar of it is printed anywhere

Repeat: python -I t359_bar_census.py ALSENAN_BAR_DETAIL_INPUT.json --csv T359_MATRIX.csv --json T359_SUMMARY.json
"""
from __future__ import annotations

import csv
import json
import re
import sys

ATTRS = ("mark", "diameter", "spacing_or_count", "layer", "direction", "extent", "end_shape")
STATES = ("PRINTED", "PRINTED_TYPICAL", "NOT_PRINTED", "NOT_APPLICABLE", "RULE")
STATUSES = ("COUNTABLE_NOW", "COUNTABLE_AFTER", "GAP", "OWNED_ELSEWHERE", "NOT_DRAWN")
# notation kinds
RATE = "RATE"                      # "n ø d/m": n bars per metre of distribution width (a density, not a count)
SPACING = "SPACING"                # "ø d/s cm": one bar every s
COUNT = "COUNT"                    # "n ø d": an explicit number of bars
COUNT_PER_SPACING = "COUNT_PER_SPACING"  # "n ø d/s cm": meaning not settled (width class or spacing; cf. RFI-B-S19)
DIAMETER_MISSING = "DIAMETER_MISSING"    # "d/s cm" with no bar symbol: the diameter is not printed
UNPARSED = "UNPARSED"


def _norm(text: str) -> str:
    t = text.strip()
    for sym in ("%%c", "%%C", "Ø", "φ", "Φ"):
        t = t.replace(sym, "ø")
    t = re.sub(r"(?i)\s*\((?:t&b|b\.w|top|bot)\)\s*$", "", t)   # trailing qualifiers are read as layer notes
    t = re.sub(r"(?i)/top$", "", t)
    t = re.sub(r"(?i)\s*stirrups?$", "", t)
    t = re.sub(r"(?i)mm", "", t)
    t = re.sub(r"\s+", "", t)
    return t.rstrip(".")


def parse_notation(text: str) -> dict:
    """Read a printed bar label. Never turns a rate or a spacing into a count."""
    t = _norm(text)
    m = re.fullmatch(r"(\d+)ø(\d+)/m", t)
    if m:
        return {"kind": RATE, "n_per_m": int(m.group(1)), "d": int(m.group(2)), "s_m": None, "count": None,
                "unit_printed": True}
    m = re.fullmatch(r"(\d+)ø(\d+)/(\d+)(cm)?", t)
    if m:
        return {"kind": COUNT_PER_SPACING, "n": int(m.group(1)), "d": int(m.group(2)),
                "s_raw": int(m.group(3)), "unit_printed": bool(m.group(4)), "count": None, "n_per_m": None}
    m = re.fullmatch(r"ø(\d+)/(\d+)(cm)?", t)
    if m:
        unit = bool(m.group(3))
        return {"kind": SPACING, "d": int(m.group(1)), "s_m": (int(m.group(2)) / 100.0) if unit else None,
                "s_raw": int(m.group(2)), "unit_printed": unit, "count": None, "n_per_m": None}
    m = re.fullmatch(r"(\d+)ø(\d+)", t)
    if m:
        return {"kind": COUNT, "count": int(m.group(1)), "d": int(m.group(2)), "n_per_m": None, "unit_printed": True}
    m = re.fullmatch(r"(\d+)/(\d+)(cm)?", t)
    if m:
        return {"kind": DIAMETER_MISSING, "d": None, "s_raw": int(m.group(2)), "unit_printed": bool(m.group(3)),
                "count": None, "n_per_m": None}
    return {"kind": UNPARSED, "d": None, "count": None, "n_per_m": None, "unit_printed": False}


def notation_states(label: str | None) -> dict:
    """mark / diameter / spacing_or_count states that the label itself establishes."""
    if not label:
        return {a: {"state": "NOT_PRINTED", "note": "no label"} for a in ("mark", "diameter", "spacing_or_count")}
    p = parse_notation(label)
    k = p["kind"]
    out = {"mark": {"state": "PRINTED", "note": label}}
    out["diameter"] = ({"state": "PRINTED", "note": f"d {p['d']} mm"} if p.get("d") else
                       {"state": "NOT_PRINTED", "note": "no bar diameter in the label"})
    if k == RATE:
        out["spacing_or_count"] = {"state": "PRINTED", "note": f"{p['n_per_m']} bars per metre (a rate, not a count)"}
    elif k == SPACING and p["unit_printed"]:
        out["spacing_or_count"] = {"state": "PRINTED", "note": f"spacing {p['s_m']:.2f} m (a spacing, not a count)"}
    elif k == SPACING:
        out["spacing_or_count"] = {"state": "NOT_PRINTED", "note": f"'/{p['s_raw']}' without a unit"}
    elif k == COUNT:
        out["spacing_or_count"] = {"state": "PRINTED", "note": f"{p['count']} bars (explicit count)"}
    elif k == COUNT_PER_SPACING:
        out["spacing_or_count"] = {"state": "NOT_PRINTED",
                                   "note": f"'{p['n']} per {p['s_raw']}': width class or spacing, total or per face not printed"}
    elif k == DIAMETER_MISSING:
        out["spacing_or_count"] = {"state": "PRINTED" if p["unit_printed"] else "NOT_PRINTED",
                                   "note": f"spacing /{p['s_raw']}"}
    else:
        out["mark"] = {"state": "NOT_PRINTED", "note": f"label not readable as a bar notation: {label!r}"}
        out["spacing_or_count"] = {"state": "NOT_PRINTED", "note": "unparsed"}
    out["_kind"] = k
    return out


def classify(pop: dict, known_rfis: set[str], answered_rules: set[str]) -> dict:
    """Status of one population. Raises on an RFI id that is not in the register or a rule not answered."""
    for rid in pop.get("rfi", {}).values():
        for one in rid.split("+"):
            if one not in known_rfis:
                raise ValueError(f"{pop['pop_id']}: RFI id {one!r} is not in the RFI register")
    if pop.get("not_drawn"):
        return {"status": "NOT_DRAWN", "blocking": [], "after": sorted(set(pop.get("rfi", {}).values())),
                "gap": pop.get("gap", "")}
    if pop.get("owned_by"):
        return {"status": "OWNED_ELSEWHERE", "blocking": [], "after": [], "gap": ""}
    states = notation_states(pop.get("label"))
    attrs = {}
    for a in ATTRS:
        given = pop.get("attrs", {}).get(a)
        if a in ("mark", "diameter", "spacing_or_count"):
            st = dict(states[a])
            if given:
                if given["state"] == "NOT_APPLICABLE":
                    st = dict(given)
                elif given["state"] == "PRINTED" and st["state"] == "NOT_PRINTED":
                    # another print of the same population supplies it (e.g. the DXF text where the PDF is clipped)
                    if not given.get("ref"):
                        raise ValueError(f"{pop['pop_id']}: {a} claimed PRINTED without a reference")
                    st = dict(given)
                elif given.get("ref"):
                    st["ref"] = given["ref"]   # the label decides the state; a reading only adds its reference
            attrs[a] = st
        else:
            if not given:
                raise ValueError(f"{pop['pop_id']}: attribute {a} not read (every attribute needs a state)")
            attrs[a] = given
        if attrs[a]["state"] not in STATES:
            raise ValueError(f"{pop['pop_id']}: bad state {attrs[a]['state']}")
        if attrs[a]["state"] == "RULE" and attrs[a].get("rule") not in answered_rules:
            raise ValueError(f"{pop['pop_id']}: {a} RULE {attrs[a].get('rule')!r} is not an answered owner rule")
    if pop.get("typical_only"):
        # a typical / N.T.S. detail gives an arrangement, never a project value, unless a project print ties it
        for a in ATTRS:
            if attrs[a]["state"] == "PRINTED":
                attrs[a] = {**attrs[a], "state": "PRINTED_TYPICAL"}
    blocking = [a for a in ATTRS if attrs[a]["state"] in ("NOT_PRINTED", "PRINTED_TYPICAL")]
    rfi = pop.get("rfi", {})
    if not blocking:
        return {"status": "COUNTABLE_NOW", "blocking": [], "after": [], "gap": "", "attrs": attrs}
    missing = [a for a in blocking if a not in rfi]
    if missing:
        if not pop.get("gap"):
            raise ValueError(f"{pop['pop_id']}: blocking {missing} asked in no RFI and no NEW gap named")
        return {"status": "GAP", "blocking": blocking, "after": sorted(set(rfi[a] for a in blocking if a in rfi)),
                "gap": pop["gap"], "attrs": attrs}
    return {"status": "COUNTABLE_AFTER", "blocking": blocking, "after": sorted(set(rfi[a] for a in blocking)),
            "gap": "", "attrs": attrs}


def double_count(pops: list[dict], results: dict, released: list[dict]) -> list[dict]:
    """Populations that this census would count AND a released rebar line already counts (must be empty)."""
    rel = {(r["element_id"], r["component"]): r["line_id"] for r in released}
    hits = []
    for p in pops:
        st = results[p["pop_id"]]["status"]
        if st in ("OWNED_ELSEWHERE", "NOT_DRAWN"):
            continue
        key = (p["element_id"], p["component"])
        if key in rel:
            hits.append({"pop_id": p["pop_id"], "released_line": rel[key]})
        for alias in p.get("same_physical_bars_as", []):
            if tuple(alias) in rel:
                hits.append({"pop_id": p["pop_id"], "released_line": rel[tuple(alias)]})
    return hits


def run(data: dict) -> dict:
    known = set(data["rfi_register"])
    rules = set(data["answered_rules"])
    results = {}
    seen = set()
    for p in data["populations"]:
        if p["pop_id"] in seen:
            raise ValueError(f"duplicate population {p['pop_id']}")
        seen.add(p["pop_id"])
        results[p["pop_id"]] = classify(p, known, rules)
    dc = double_count(data["populations"], results, data.get("released_lines", []))
    by_el: dict[str, dict] = {}
    for p in data["populations"]:
        r = results[p["pop_id"]]
        e = by_el.setdefault(p["element"], {s: 0 for s in STATUSES})
        e[r["status"]] += 1
    elements_required = data.get("elements_required", [])
    missing_el = [e for e in elements_required if e not in by_el]
    if missing_el:
        raise ValueError(f"elements with no census row: {missing_el}")
    totals = {s: sum(1 for r in results.values() if r["status"] == s) for s in STATUSES}
    gaps = sorted({r["gap"] for r in results.values() if r["gap"]})
    return {"results": results, "double_count": dc, "by_element": by_el, "totals": totals, "gaps": gaps,
            "kg_computed": 0}


def matrix_rows(data: dict, out: dict) -> list[dict]:
    rows = []
    for p in data["populations"]:
        r = out["results"][p["pop_id"]]
        row = {"element": p["element"], "element_id": p["element_id"], "pop_id": p["pop_id"],
               "component": p["component"], "label": p.get("label") or "", "source": p.get("source", "")}
        for a in ATTRS:
            st = r.get("attrs", {}).get(a)
            if st is None:
                row[a] = "NOT_APPLICABLE (owned elsewhere)" if r["status"] == "OWNED_ELSEWHERE" else (
                    "NOT_PRINTED (not drawn)" if r["status"] == "NOT_DRAWN" else "")
            else:
                ref = st.get("ref") or st.get("rule") or ""
                row[a] = st["state"] + (f" [{ref}]" if ref else "") + (f" {st['note']}" if st.get("note") else "")
        row["status"] = r["status"]
        row["after"] = "; ".join(r["after"])
        row["gap"] = r["gap"]
        row["owned_by"] = p.get("owned_by", "")
        row["note"] = p.get("note", "")
        rows.append(row)
    return rows


def main(argv: list[str]) -> int:
    data = json.load(open(argv[1], encoding="utf-8"))
    out = run(data)
    rows = matrix_rows(data, out)
    if "--csv" in argv:
        path = argv[argv.index("--csv") + 1]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    summary = {"schema": "T359_SUMMARY_V1", "totals": out["totals"], "by_element": out["by_element"],
               "gaps": out["gaps"], "double_count": out["double_count"], "kg_computed": 0,
               "populations": len(rows)}
    if "--json" in argv:
        json.dump(summary, open(argv[argv.index("--json") + 1], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 0 if not out["double_count"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
