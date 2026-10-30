"""T-373 LAP_AUTHORITY_LINE_BINDING_V1 (research code, stdlib; read-only on every candidate and ledger).

Binds every reinforcement line of a candidate BOQ that carries a lap, development (anchorage) or starter component to
the printed authority of its length, and proposes the line's status for a Checker DOWNGRADE-ONLY record
(owner 2026-10-24 23:57: a record may only move a line to HELD / CONFLICT, never promote it).

Rule R-T373-1 (every villa; provenance T-366 F-T366-2 / T-373): a lap or development length is valued only from a
printed authority whose wording names the bar population (sheet / note / detail), or from an answered owner rule.
A note that names another group (ST p.8 note 9 names STARTER bars only, OWNER_RULE_REBAR_2026-10-24 s.4 / s.6) is no
authority for beams, columns at storey joints, ground-beam ends or slabs: such a line is HELD by name, BLANK, never 0
and never a borrowed length. Nothing here computes a new length.

    python3 -I research/agents_t373/t373_lap_binding.py <run>/V3_0_27_BOQ_LINES.json \
        --csv research/agents_t373/T373_LAP_BINDING.csv --json research/agents_t373/T373_SUMMARY.json
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t366"))

SCHEMA = "LAP_AUTHORITY_LINE_BINDING_V1"
NOTE9 = re.compile(r"note\s*9|NOTE_9", re.I)

# authorities that print a length for a NAMED bar group (T-366 census, merged 51be6eab; ST7757 p.8, p.13, p.15)
AUTHORITIES = {
    "P8-NOTE9": {"ref": "ST p.8 general notes, note 9 (Arabic, PDF only)", "names": {"STARTER"},
                 "value": ">= 70 d tension / >= 40 d compression, zone not printed", "category": "STARTER_BARS"},
    "P13-40D": {"ref": "ST p.13 TYP. DETAIL OF ISOLATED FOOTING (right): '40 ø' starter projection", "names": {"STARTER"},
                "value": "40 ø (typical); conflicts with note 9 in a tension zone (F-T366-1)", "category": "STARTER_BARS"},
    "P15-NOTE1": {"ref": "ST p.15 NOTE 1 'LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40xDIA'",
                  "names": {"TEMPERATURE"}, "value": "40 d exact", "category": "LAP_SPLICE"},
    "P15-DRAWN": {"ref": "ST p.15 TYP. SLAB ON BEAMS DETAIL: drawn straight part to '40 CL.' (T-307 / T-318)",
                  "names": {"SLAB_END"}, "value": "w - 0.040 m drawn (a bar part, not a lap)", "category": "DRAWN_BAR"},
}

# population (T-366 binding) -> group that a printed authority must name
GROUP = {"NECK-STARTER-SHALLOW|NECK-STARTER-DEEP": "STARTER", "SLAB-TEMPERATURE": "TEMPERATURE",
         "COL-MAIN": "COLUMN_MAIN", "GB-MAIN": "GROUND_BEAM_MAIN", "STRAP-MAIN": "GROUND_BEAM_MAIN",
         "BEAM-SIMPLE-MAIN": "BEAM_MAIN", "CB-BOTTOM": "BEAM_MAIN", "CB-TOP-THROUGH": "BEAM_MAIN",
         "CB-SUPPORT-TOP": "BEAM_MAIN", "SLAB-BOTTOM-MAIN": "SLAB_END", "SLAB-TOP-SUPPORT": "SLAB_END"}

REPORT_GROUP = {"BEAM-SIMPLE-MAIN": "beam ends", "CB-BOTTOM": "beam ends", "CB-TOP-THROUGH": "beam ends",
                "CB-SUPPORT-TOP": "beam ends", "COL-MAIN": "column storey laps", "GB-MAIN": "GB bar ends",
                "STRAP-MAIN": "GB bar ends", "SLAB-BOTTOM-MAIN": "slab development",
                "SLAB-TOP-SUPPORT": "slab top bars", "NECK-STARTER-SHALLOW|NECK-STARTER-DEEP": "starters",
                "SLAB-TEMPERATURE": "slab temperature laps"}
T366_COUNTS = {"beam ends": 254, "column storey laps": 56, "GB bar ends": 62, "slab development": 98}   # V3.0.16, 470


class BindingError(ValueError):
    pass


# ---------------------------------------------------------------- rule R-T373-1 (pure, every villa)
def lap_authority(group, cited, authorities=AUTHORITIES, owner_rules=()):
    """group: the bar group of the line; cited: authority ids the line's length rests on.
    Returns (authority_class, proposed_status, reason)."""
    if not group:
        raise BindingError("a line without a bar group cannot be bound")
    if group in set(owner_rules):
        return "OWNER_RULE", "KEEP", f"answered owner rule names {group}"
    named = [a for a in cited if a in authorities and group in authorities[a]["names"]]
    foreign = [a for a in cited if a in authorities and group not in authorities[a]["names"]]
    unknown = [a for a in cited if a not in authorities]
    if unknown:
        raise BindingError(f"unknown authority {unknown}: an authority is a printed sheet / note / detail id")
    if named:
        return "PRINTED", "KEEP", " + ".join(authorities[a]["ref"] for a in named)
    if foreign:
        a = foreign[0]
        cls = "NOTE9_OUTSIDE_GROUP" if a == "P8-NOTE9" else "PRINTED_FOR_OTHER_GROUP"
        return cls, "HELD", (f"{authorities[a]['ref']} names {sorted(authorities[a]['names'])} only; the line's "
                             f"group {group} has no printed lap / development length: HELD by name, BLANK")
    return "NONE", "HELD", f"no printed authority names {group}: HELD by name, BLANK"


def value_line(proposed, low, high):
    """kg after the proposal: KEEP keeps the line's figure; HELD is BLANK (None), never 0."""
    if proposed == "HELD":
        return None, None
    if proposed == "KEEP":
        return low, high
    raise BindingError(f"unknown status {proposed}")


# ---------------------------------------------------------------- candidate binding (Alsenan run)
def _fig(line):
    br = line.get("bounded_range") or None
    net = line.get("measured_net")
    if net is not None:
        return Decimal(str(net)), Decimal(str(net))
    if br and br.get("low") is not None:
        return Decimal(str(br["low"])), Decimal(str(br["high"]))
    return None, None


def _slim(l):
    if "location" not in l and "element_id" in l:      # the merged T-297 extract form (V3.0.16), already slim
        return {k: l.get(k) for k in ("line_id", "element_id", "evidence_state", "measured_net", "bounded_range",
                                      "subtrade", "floor", "item_code", "trade", "unit")} | {
            "formula": l.get("formula") or "", "inputs": l.get("inputs") or {}}
    loc = l.get("location") or {}
    c = l.get("calculation") or {}
    inp = c.get("inputs") or {}
    return {"line_id": l["line_id"], "element_id": loc.get("element_id"), "evidence_state": l["evidence_state"],
            "measured_net": l.get("measured_net"), "bounded_range": l.get("bounded_range"),
            "formula": c.get("formula") or "", "inputs": inp, "subtrade": l.get("subtrade"), "floor": loc.get("floor"),
            "item_code": l.get("item_code"), "trade": l.get("trade"), "unit": l.get("unit")}


def component_of(s, pop):
    e = (s["element_id"] or "").upper()
    comp = str((s["inputs"] or {}).get("component") or "").lower()
    if pop == "NECK-STARTER-SHALLOW|NECK-STARTER-DEEP":
        return "STARTER", "STARTER_PROJECTION"
    if pop == "SLAB-TEMPERATURE":
        return "LAP", "TEMPERATURE_LAP"
    if "LAP" in e and pop == "COL-MAIN":
        return "LAP", "COLUMN_STOREY_LAP"
    if "LAPS" in e:
        return "LAP", "PROCUREMENT_LAP"
    if "BAR_ENDS" in e and pop in ("GB-MAIN", "STRAP-MAIN"):
        return "DEVELOPMENT", "GB_BAR_END_DEVELOPMENT"
    if "NOTE_9" in e or "ends (note 9" in comp:
        return "DEVELOPMENT", "BEAM_END_DEVELOPMENT"
    if "#SLAB_BAR_ENDS:VALUED" in e and "DEVELOPMENT" in e:
        return "DEVELOPMENT", "SLAB_DEV_DRAWN_PART"
    if "DEVELOPMENT" in e:
        return "DEVELOPMENT", "SLAB_DEVELOPMENT"
    return None, None


def cited_of(s, pop, kind):
    """authority ids the line's FIGURE rests on (formula / bound basis / component only; notes are history)."""
    br = s.get("bounded_range") or {}
    txt = " ".join([s["formula"], str(br.get("basis") or ""), str((s["inputs"] or {}).get("component") or ""),
                    s["element_id"] or ""])
    out = []
    if NOTE9.search(txt):
        out.append("P8-NOTE9")
    if kind == "STARTER_PROJECTION":
        out += ["P13-40D"] if "P8-NOTE9" in out else ["P8-NOTE9", "P13-40D"]
    if kind == "TEMPERATURE_LAP":
        out.append("P15-NOTE1")
    if kind == "SLAB_DEV_DRAWN_PART":
        out = ["P15-DRAWN"]
    return out


def bind_candidate(lines, bind_pop):
    rows = []
    for l in lines:
        if not (l.get("item_code") == "STR.REBAR" or (l.get("trade") or "") == "REINFORCEMENT"):
            continue
        s = _slim(l)
        if s.get("unit") not in ("kg", None):
            raise BindingError(f"line {s['line_id']} in {s['unit']}: the binding reads kg only (t only at export)")
        pop = bind_pop({"element_id": s["element_id"], "inputs": s["inputs"]})
        lo, hi = _fig(s)
        if pop.startswith("OUT:"):
            if NOTE9.search(s["formula"] + str((s.get("bounded_range") or {}).get("basis") or "")) and lo is not None:
                rows.append(_row(s, "OUT_OF_ROUTE(T-359)", "DEVELOPMENT", "POOL_STAIR_TANK", ["P8-NOTE9"],
                                 ("NOTE9_OUTSIDE_GROUP", "LISTED_ONLY", "T-359 scope (outside the released route): "
                                  "listed for the Lead, no proposal here"), lo, hi, (lo, hi)))
            continue
        cat, kind = component_of(s, pop)
        if kind is None:
            continue
        cited = cited_of(s, pop, kind)
        group = GROUP.get(pop)
        if lo is None:
            res = ("NOT_BOOKED", "KEEP", f"no figure on the line ({s['evidence_state']}): nothing to downgrade")
        elif kind == "STARTER_PROJECTION":
            res = ("PRINTED_CONFLICT", "KEEP", "starter group named by p.8 note 9 and p.13 '40 ø' (F-T366-1 CONFLICT)")
        else:
            res = lap_authority(group, cited)
        after = value_line(res[1], lo, hi) if res[1] in ("KEEP", "HELD") else (lo, hi)
        rows.append(_row(s, pop, cat, kind, cited, res, lo, hi, after))
    seen = collections.Counter(r["line_id"] for r in rows)
    dup = [k for k, v in seen.items() if v > 1]
    if dup:
        raise BindingError(f"line bound twice: {dup[:3]}")
    return rows


def _row(s, pop, cat, kind, cited, res, lo, hi, after):
    return {"line_id": s["line_id"], "element_id": s["element_id"], "floor": s["floor"], "subtrade": s["subtrade"],
            "population": pop, "report_group": ("GB procurement laps" if kind == "PROCUREMENT_LAP" else
                                            REPORT_GROUP.get(pop, pop)), "component": cat, "kind": kind,
            "length_used": _length_used(s, kind), "authority_cited": "+".join(cited) or "NONE",
            "authority_class": res[0], "proposed": res[1], "reason": res[2], "state_now": s["evidence_state"],
            "kg_low_now": _f(lo), "kg_high_now": _f(hi), "kg_low_after": _f(after[0]), "kg_high_after": _f(after[1])}


def _length_used(s, kind):
    br = s.get("bounded_range") or {}
    b = str(br.get("basis") or "")
    if kind == "SLAB_DEV_DRAWN_PART":
        return "p.15 straight part w - 0.040 m (drawn)"
    comp = str((s.get("inputs") or {}).get("component") or "")
    m = re.search(r"2 x 40 d \.\. 2 x 70 d|\d+ ?d ?\.\. ?\d+ ?d", b + " " + comp + " " + s["formula"])
    return m.group(0) if m else (b or "not stated")[:60]


def _f(x):
    return "" if x is None else format(x, "f")


def totals(rows):
    agg = collections.OrderedDict()
    for r in rows:
        k = (r["report_group"], r["proposed"])
        a = agg.setdefault(k, {"lines": 0, "low_now": Decimal(0), "high_now": Decimal(0), "low_after": Decimal(0),
                               "high_after": Decimal(0), "held_blank": 0})
        a["lines"] += 1
        for f in ("low_now", "high_now"):
            v = r["kg_" + f.replace("_now", "") + "_now"]
            a[f] += Decimal(v) if v else 0
        if r["proposed"] == "HELD":
            a["held_blank"] += 1
        else:
            a["low_after"] += Decimal(r["kg_low_after"]) if r["kg_low_after"] else 0
            a["high_after"] += Decimal(r["kg_high_after"]) if r["kg_high_after"] else 0
    res = []
    for k, v in sorted(agg.items()):
        t = {"group": k[0], "proposed": k[1], **{x: (str(y) if isinstance(y, Decimal) else y) for x, y in v.items()}}
        if k[1] == "HELD":                     # a HELD group has no valued figure after the record: BLANK, never 0
            t["low_after"] = t["high_after"] = "BLANK"
        res.append(t)
    return res


T318_CLASS = {"NOT_APPLICABLE_WITH_EVIDENCE": ("REBOOKED_T318_NA", "every end continuous: p.15 draws no development "
                                              "(T-318 V3.0.27: NOT_APPLICABLE_WITH_EVIDENCE, no figure)"),
              "HELD": ("REBOOKED_T318_BLANK", "T-318 V3.0.27 already BLANK by name (note-9 basis dropped)"),
              "BOUND_PART_WITH_HELD": ("REBOOKED_T318_BLANK", "T-318 V3.0.27: parent BLANK, held ends named; "
                                                              "drawn straight part on its own valued line")}


def rebook_t318(rows, t318_lines):
    """the V3.0.27 state of the slab development lines from the merged T-318 inputs (by line id): a line T-318 already
    re-booked is NOT downgraded a second time (acceptance (c)); its drawn part becomes its own PRINTED row."""
    by_id = {x["line_id"]: x for x in t318_lines if x["population"] == "DEVELOPMENT / ANCHORAGE"}
    out, hit = [], set()
    for r in rows:
        x = by_id.get(r["line_id"])
        if x is None:
            out.append(r)
            continue
        if r["kind"] != "SLAB_DEVELOPMENT":
            raise BindingError(f"T-318 line {r['line_id']} is bound as {r['kind']}")
        if (r["kg_low_now"], r["kg_high_now"]) != (format(Decimal(str(x["before"]["low"])), "f"),
                                                   format(Decimal(str(x["before"]["high"])), "f")):
            raise BindingError(f"T-318 'before' of {r['line_id']} differs from the bound line: stale input")
        hit.add(r["line_id"])
        cls, why = T318_CLASS[x["status"]]
        st = "NOT_APPLICABLE_WITH_EVIDENCE" if cls.endswith("NA") else "BLOCKED_RFI"
        out.append(dict(r, authority_class=cls, proposed="KEEP", reason=why, state_now=st, kg_low_now="",
                        kg_high_now="", kg_low_after="", kg_high_after="",
                        length_used="none (re-booked by T-318)", authority_cited="P15-DRAWN"))
        if x["status"] == "BOUND_PART_WITH_HELD":
            v = x["valued"]
            lo, hi = format(Decimal(str(v["low"])), "f"), format(Decimal(str(v["high"])), "f")
            out.append(dict(r, line_id=r["line_id"] + "#PART", element_id=f"{r['element_id']}#SLAB_BAR_ENDS:VALUED",
                            kind="SLAB_DEV_DRAWN_PART", authority_cited="P15-DRAWN", authority_class="PRINTED",
                            proposed="KEEP", reason=AUTHORITIES["P15-DRAWN"]["ref"] + " (a drawn bar part, not a lap)",
                            length_used="p.15 straight part w - 0.040 m (drawn)", state_now="BOUNDED_EXPOSURE",
                            kg_low_now=lo, kg_high_now=hi, kg_low_after=lo, kg_high_after=hi))
    missing = set(by_id) - hit
    if missing:
        raise BindingError(f"T-318 development lines not in the binding: {sorted(missing)[:3]}")
    return out


CSV_COLS = ("line_id", "element_id", "floor", "subtrade", "population", "report_group", "component", "kind",
            "length_used", "authority_cited", "authority_class", "proposed", "reason", "state_now", "kg_low_now",
            "kg_high_now", "kg_low_after", "kg_high_after")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", help="V3_0_27_BOQ_LINES.json of a reproduced run (outside the repository)")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--t318", action="store_true", help="the candidate is the V3.0.16 extract: re-book its slab "
                    "development lines to their V3.0.27 state from the merged T-318 inputs (research/agents_t318)")
    a = ap.parse_args(argv)
    import t366_alsenan_input as B
    raw = Path(a.candidate).read_bytes()
    d = json.loads(raw)
    lines = d["lines"] if isinstance(d, dict) else d
    rows = bind_candidate(lines, B.bind)
    view = "as given"
    if a.t318:
        sys.path.insert(0, str(ROOT / "research" / "agents_t318"))
        import t318_inputs as L27
        pid = d.get("project") if isinstance(d.get("project"), str) else (d.get("project") or {}).get("project_id")
        rows = rebook_t318(rows, L27.build(pid)["lines"])
        view = "V3.0.27 view: V3.0.16 extract (= V3.0.17, T-297) + the T-318 slab development re-booking by line id"
    rows.sort(key=lambda r: (r["report_group"], r["proposed"], r["line_id"]))
    with open(a.csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, CSV_COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    note9 = collections.Counter(r["report_group"] for r in rows if r["authority_class"] == "NOTE9_OUTSIDE_GROUP"
                                and r["proposed"] == "HELD")
    summ = {"schema": SCHEMA, "candidate": Path(a.candidate).name, "candidate_sha256": hashlib.sha256(raw).hexdigest(), "view": view,
            "rebar_lines": sum(1 for l in lines if l.get("item_code") == "STR.REBAR"),
            "bound_rows": len(rows), "by_class": dict(collections.Counter(f"{r['authority_class']} -> {r['proposed']}"
                                                                 for r in rows)),
            "note9_outside_group_held": dict(note9), "t366_counts_v3016": T366_COUNTS, "totals": totals(rows)}
    Path(a.json).write_text(json.dumps(summ, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: summ[k] for k in ("bound_rows", "by_class", "note9_outside_group_held")}, indent=1))
    return 0


if __name__ == "__main__":
    main()
