"""T-665: the integration-package summary of one finished v3063_run.py run (V3_0_62 -> V3_0_63), item codes, engine
ids, states and quantities only (no coordinates, no names):

  - per B10 item code (STR.CONC.*|m3): released, held bounded low .. high, bounded / blank line counts, V3.0.62 ->
    V3.0.63 (and the released V2.9 + route G figure where the run carries it);
  - per changed line: action, before -> after, the measure beside, the set-aside bound;
  - the whole-BOQ diff counts and the identity block; every CONFIRM line asserted SAME;
  - the sha256 of V3_0_62 / V3_0_63 BOQ_LINES.

    python3 -I research/agents_t665/t665_summary.py <run dir> --out research/agents_t665/summary_t665.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v30 as A30  # noqa: E402


def _lines(p):
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["lines"] if isinstance(d, dict) else d


def summarise(run):
    run = Path(run)
    l61, l62 = _lines(run / "V3_0_62_BOQ_LINES.json"), _lines(run / "V3_0_63_BOQ_LINES.json")
    t61, t62 = A304.code_totals(l61), A304.code_totals(l62)
    b10 = {k: {"v3_0_62": t61.get(k), "v3_0_63": t62.get(k)} for k in sorted(set(t61) | set(t62))
           if k.startswith("STR.CONC.") and k.endswith("|m3")}
    moved = {k for k in set(t61) | set(t62) if t61.get(k) != t62.get(k)}
    led = json.loads((run / "V3_0_63_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_63_RUN.json").read_text(encoding="utf-8"))
    diff = list(csv.DictReader((run / "V3_0_63_DIFF.csv").open(encoding="utf-8")))
    dmap = {d["line_id"]: d for d in diff}
    conf = led["confirmed_unchanged"]
    assert all(dmap[x]["vs_base"] == "SAME" for x in conf), "a CONFIRM line moved"
    rows = [{"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "member": r["member"],
             "before": r["before_base"], "after": r["after_v3_0_63"], "class": r["class"],
             "beside": r.get("beside"), "set_aside": r.get("set_aside"), "v2_9": r.get("before_released_v2_9"),
             "vs_base": dmap[r["line_id"]]["vs_base"]} for r in led["rows"]]
    by_action = {}
    for r in rows:
        a = by_action.setdefault(f"{r['item_code']} {r['action']}", {"lines": 0, "before_low": 0.0, "before_high": 0.0,
                                                                    "after_low": 0.0, "after_high": 0.0,
                                                                    "after_value": 0.0, "beside": 0.0})
        a["lines"] += 1
        b, z = r["before"], r["after"]
        a["before_low"] += b["low"] or 0.0
        a["before_high"] += b["high"] or 0.0
        a["after_low"] += z["low"] or 0.0
        a["after_high"] += z["high"] or 0.0
        a["after_value"] += (z["value"] or 0.0) if z["state"] != "BLOCKED_RFI" else 0.0
        a["beside"] += (r["beside"] or {}).get("value") or 0.0
    by_action = {k: {f: round(v, 6) if isinstance(v, float) else v for f, v in x.items()} for k, x in
                 sorted(by_action.items())}
    return {"schema": "T665_SUMMARY_V1", "method": rj["method"], "extends": rj["extends"],
            "released_default": rj["released_default"],
            "lines_sha256": {"V3_0_62": hashlib.sha256((run / "V3_0_62_BOQ_LINES.json").read_bytes()).hexdigest(),
                             "V3_0_63": hashlib.sha256((run / "V3_0_63_BOQ_LINES.json").read_bytes()).hexdigest()},
            "lines": {"V3_0_62": len(l61), "V3_0_63": len(l62)},
            "identity": {k: rj["identity"][k] for k in ("replaced", "added", "outside_rows", "confirmed",
                                                         "outside_rows_identical_to_base", "concrete", "diff")},
            "totals_moved": sorted(moved), "b10_code_totals": b10, "by_code_action": by_action,
            "confirmed_unchanged": conf, "rows": rows, "waiting": led["waiting_pieces"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = summarise(a.run)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("lines_sha256", "lines", "identity", "totals_moved")}, indent=1))
    for k, v in doc["b10_code_totals"].items():
        if v["v3_0_62"] != v["v3_0_63"]:
            print(k, v["v3_0_62"], "->", v["v3_0_63"])
    for k, v in doc["by_code_action"].items():
        print(k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
