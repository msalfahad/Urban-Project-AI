"""T-704: the integration-package summary of one finished v3070_run.py run (V3_0_70 -> V3_0_71), item codes, engine
ids, states and quantities only (no coordinates, no names):

  - per concrete item code (STR.CONC.*): released, held bounded low .. high, bounded / blank line counts, V3.0.70 -> V3.0.71
    (m2; a blank line is counted, never summed as 0);
  - per changed / added line: piece, action, before -> after, evidence status;
  - the whole-BOQ diff counts, the identity block;
  - the sha256 of V3_0_70 / V3_0_71 BOQ_LINES.

    bash scripts/agent_env.sh run --tree task-T-704 research/agents_t704/t704_summary.py <run dir> \
        --out research/agents_t704/summary_t704.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402


def _lines(p):
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["lines"] if isinstance(d, dict) else d


def lintel_census(lines):
    """STR.CONC.LINTEL: released m3 / bounded low .. high / blank lines by what sits beside them (never summed)."""
    out = {"lines": 0, "released_lines": 0, "released_m3": 0.0, "bounded_lines": 0, "bounded_low": 0.0,
           "bounded_high": 0.0, "blank_at_most": 0, "blank_at_least": 0, "blank_datum_only": 0,
           "at_most_beside_sum_m3_not_a_total": 0.0, "at_least_beside_sum_m3_not_a_total": 0.0}
    for ln in lines:
        if ln["item_code"] != "STR.CONC.LINTEL":
            continue
        out["lines"] += 1
        br = ln.get("bounded_range") or {}
        if ln.get("measured_net") is not None:
            out["released_lines"] += 1
            out["released_m3"] = round(out["released_m3"] + ln["measured_net"], 6)
        elif ln["evidence_state"] == "BOUNDED_EXPOSURE":
            out["bounded_lines"] += 1
            out["bounded_low"] = round(out["bounded_low"] + br["low"], 6)
            out["bounded_high"] = round(out["bounded_high"] + br["high"], 6)
        else:
            inp = (ln.get("calculation") or {}).get("inputs") or {}
            bs = [(inp.get(k) or {}).get("beside") or {} for k in ("concrete_ledger_v3071", "concrete_ledger_v3067")]
            kinds = {b.get("kind"): b.get("value") for b in bs if b.get("kind")}
            if "AT_MOST_M3" in kinds:
                out["blank_at_most"] += 1
                out["at_most_beside_sum_m3_not_a_total"] = round(out["at_most_beside_sum_m3_not_a_total"]
                                                                 + kinds["AT_MOST_M3"], 6)
            elif "AT_LEAST_M3" in kinds:
                out["blank_at_least"] += 1
                out["at_least_beside_sum_m3_not_a_total"] = round(out["at_least_beside_sum_m3_not_a_total"]
                                                                  + kinds["AT_LEAST_M3"], 6)
            else:
                out["blank_datum_only"] += 1
    return out


def summarise(run):
    run = Path(run)
    l67, l68 = _lines(run / "V3_0_70_BOQ_LINES.json"), _lines(run / "V3_0_71_BOQ_LINES.json")
    t67, t68 = A304.code_totals(l67), A304.code_totals(l68)
    mas = {k: {"v3_0_70": t67.get(k), "v3_0_71": t68.get(k)} for k in sorted(set(t67) | set(t68))
           if k.startswith("STR.CONC.")}
    moved = sorted(k for k in set(t67) | set(t68) if t67.get(k) != t68.get(k))
    led = json.loads((run / "V3_0_71_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_71_RUN.json").read_text(encoding="utf-8"))
    rows = [{"piece": r["piece"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
             "item_code": r["item_code"], "element_id": r["element_id"], "unit": r["unit"], "before": r["before_base"],
             "after": r["after_v3_0_71"], "class": r["class"], "evidence_status": r["evidence_status"],
             "v2_9": r.get("before_released_v2_9")} for r in led["rows"]]
    na = {}
    for ln in l68:
        if ln["item_code"].startswith("STR.CONC.") and ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            na[ln["item_code"]] = na.get(ln["item_code"], 0) + 1
    return {"schema": "T704_SUMMARY_V1", "lintel_census": {"V3_0_70": lintel_census(l67), "V3_0_71": lintel_census(l68)},
            "family_at_most": rj["piece_logs"][0].get("family_at_most"),
            "confirmed_unchanged": rj["piece_logs"][0].get("confirmed_unchanged"), "method": rj["method"], "extends": rj["extends"],
            "released_default": rj["released_default"],
            "lines_sha256": {"V3_0_70": hashlib.sha256((run / "V3_0_70_BOQ_LINES.json").read_bytes()).hexdigest(),
                             "V3_0_71": hashlib.sha256((run / "V3_0_71_BOQ_LINES.json").read_bytes()).hexdigest()},
            "lines": {"V3_0_70": len(l67), "V3_0_71": len(l68)},
            "identity": {k: rj["identity"][k] for k in ("replaced", "added", "outside_rows", "lintels",
                                                         "outside_rows_identical_to_base", "diff")},
            "totals_moved": moved, "conc_code_totals": mas, "not_applicable_v3_0_71": na, "rows": rows,
            "waiting": led["waiting_pieces"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = summarise(a.run)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("lines_sha256", "lines", "identity", "totals_moved", "lintel_census",
                                          "family_at_most")}, indent=1))
    for k, v in doc["conc_code_totals"].items():
        if v["v3_0_70"] != v["v3_0_71"]:
            print(k, v["v3_0_70"], "->", v["v3_0_71"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
