"""T-297 extract (read-only): from a finished ARCH_TAKEOFF_V3.0.16 run on the development villa's Drive copies, write
the committed input of the line-to-member basis ledger: every candidate line of the REINFORCEMENT trade / item STR.REBAR
(engine ids, item codes, states, quantities, ledger keys and their printed readings only; no names), plus the identity of
the run (csv / json sha256, project id, revision set).

    python3 -I research/agents_t297/t297_extract.py <run>/v3016 --out research/agents_t297
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

KEEP_INPUTS = ("policy", "ledger", "ledger_sha256", "element", "mark", "component", "part", "printed", "count",
               "length_m", "readings", "reasons", "ledger_state", "would_be_kg", "schedule_row", "held_defined_kg",
               "lower_bound_kg", "upper_bound", "dia_mm", "verified_by", "source", "piece", "task", "cover",
               "bar_length_m", "kg_per_m", "count_range")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d["lines"] if isinstance(d, dict) else d


def slim(l):
    c = l.get("calculation") or {}
    inp = c.get("inputs") or {}
    return {"line_id": l["line_id"], "item_code": l["item_code"], "trade": l.get("trade"), "subtrade": l.get("subtrade"),
            "floor": (l.get("location") or {}).get("floor"), "element_id": (l.get("location") or {}).get("element_id"),
            "physical_element": l.get("physical_element"), "unit": l["unit"], "evidence_state": l["evidence_state"],
            "measured_net": l.get("measured_net"),
            "bounded_range": l.get("bounded_range"),
            "formula": c.get("formula"), "inputs": {k: inp[k] for k in KEEP_INPUTS if k in inp},
            "input_keys": sorted(inp), "conventions": (l.get("rule") or {}).get("conventions_used"),
            "rule_id": (l.get("rule") or {}).get("rule_id"),
            "rfi": _cut((l.get("rfi") or {}).get("question")), "notes": _cut(l.get("notes"))}


def _cut(t, n=240):
    """long evidence texts are cut (the full text stays in the run); ids, states and quantities are kept whole"""
    return t if not isinstance(t, str) or len(t) <= n else t[:n] + " [...]"


def is_rebar(l):
    return l.get("item_code") == "STR.REBAR" or (l.get("trade") or "") == "REINFORCEMENT"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="the V3.0.16 output directory (holding V3_0_16_BOQ_LINES.json)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--also", help="a later candidate run dir (e.g. <run>/v3017 holding V3_0_17_BOQ_LINES.json): "
                                   "writes REBAR_EQUIVALENCE_T297.json (are its reinforcement lines the same?)")
    a = ap.parse_args(argv)
    run = Path(a.run)
    jp, cp = run / "V3_0_16_BOQ_LINES.json", run / "V3_0_16_BOQ_LINES.csv"
    L = _lines(jp)
    reb = sorted((l for l in L if is_rebar(l)), key=lambda x: x["line_id"])
    out = {"schema": "T297_CANDIDATE_V3016_REBAR_LINES", "candidate": "ARCH_TAKEOFF_V3.0.16",
           "candidate_lines_csv_sha256": _sha(cp) if cp.exists() else None, "candidate_lines_json_sha256": _sha(jp),
           "project": L[0]["project"], "lines_in_candidate": len(L), "rebar_lines": len(reb),
           "lines": [slim(l) for l in reb]}
    o = Path(a.out)
    o.mkdir(parents=True, exist_ok=True)
    head = json.dumps({k: v for k, v in out.items() if k != "lines"}, ensure_ascii=False)[:-1]
    body = ",\n".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in out["lines"])
    (o / "CANDIDATE_V3016_REBAR_LINES.json").write_text(head + ', "lines": [\n' + body + "\n]}\n", encoding="utf-8")
    print("lines", len(L), "rebar", len(reb), "csv", out["candidate_lines_csv_sha256"])
    if a.also:
        later = Path(a.also)
        jp2 = sorted(later.glob("V3_0_*_BOQ_LINES.json"))[-1]
        L2 = _lines(jp2)
        reb2 = {l["line_id"]: l for l in L2 if is_rebar(l)}
        key = ("evidence_state", "measured_net", "bounded_range", "location", "physical_element", "unit")
        diff = sorted(k for k, l in ((l["line_id"], l) for l in reb)
                      if k not in reb2 or any(l.get(x) != reb2[k].get(x) for x in key))
        eq = {"schema": "T297_REBAR_EQUIVALENCE", "base": out["candidate"],
              "base_csv_sha256": out["candidate_lines_csv_sha256"], "later_file": jp2.name,
              "later_csv_sha256": _sha(jp2.with_suffix(".csv")), "later_json_sha256": _sha(jp2),
              "later_lines": len(L2), "rebar_lines_base": len(reb), "rebar_lines_later": len(reb2),
              "same_line_ids": set(reb2) == {l["line_id"] for l in reb}, "lines_differing_on": list(key),
              "differing": diff}
        (o / "REBAR_EQUIVALENCE_T297.json").write_text(json.dumps(eq, indent=1) + "\n", encoding="utf-8")
        print("later", jp2.name, "rebar", len(reb2), "differing", len(diff))
    return 0


if __name__ == "__main__":
    main()
