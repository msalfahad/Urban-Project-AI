"""T-672: the integration-package summary of one finished v3068_run.py run (V3_0_67 -> V3_0_68), item codes, engine
ids, states and quantities only (no coordinates, no names):

  - per masonry item code (MAS.*): released, held bounded low .. high, bounded / blank line counts, V3.0.67 -> V3.0.68
    (units, m3 and kg are never summed together);
  - per changed / added line: piece, action, before -> after, evidence status;
  - the whole-BOQ diff counts, the identity block and the correlated lintel scenarios beside;
  - the sha256 of V3_0_67 / V3_0_68 BOQ_LINES.

    bash scripts/agent_env.sh run --tree task-T-672 research/agents_t672/t672_summary.py <run dir> \
        --out research/agents_t672/summary_t672.json
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


def summarise(run):
    run = Path(run)
    l67, l68 = _lines(run / "V3_0_67_BOQ_LINES.json"), _lines(run / "V3_0_68_BOQ_LINES.json")
    t67, t68 = A304.code_totals(l67), A304.code_totals(l68)
    mas = {k: {"v3_0_67": t67.get(k), "v3_0_68": t68.get(k)} for k in sorted(set(t67) | set(t68))
           if k.startswith("MAS.")}
    moved = sorted(k for k in set(t67) | set(t68) if t67.get(k) != t68.get(k))
    led = json.loads((run / "V3_0_68_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_68_RUN.json").read_text(encoding="utf-8"))
    rows = [{"piece": r["piece"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
             "item_code": r["item_code"], "element_id": r["element_id"], "unit": r["unit"], "before": r["before_base"],
             "after": r["after_v3_0_68"], "class": r["class"], "evidence_status": r["evidence_status"],
             "v2_9": r.get("before_released_v2_9")} for r in led["rows"]]
    na = {}
    for ln in l68:
        if ln["item_code"].startswith("MAS.") and ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            na[ln["item_code"]] = na.get(ln["item_code"], 0) + 1
    return {"schema": "T672_SUMMARY_V1", "method": rj["method"], "extends": rj["extends"],
            "released_default": rj["released_default"],
            "lines_sha256": {"V3_0_67": hashlib.sha256((run / "V3_0_67_BOQ_LINES.json").read_bytes()).hexdigest(),
                             "V3_0_68": hashlib.sha256((run / "V3_0_68_BOQ_LINES.json").read_bytes()).hexdigest()},
            "lines": {"V3_0_67": len(l67), "V3_0_68": len(l68)},
            "identity": {k: rj["identity"][k] for k in ("replaced", "added", "outside_rows", "masonry", "scenarios",
                                                         "outside_rows_identical_to_base", "diff")},
            "totals_moved": moved, "mas_code_totals": mas, "not_applicable_v3_0_68": na, "rows": rows,
            "waiting": led["waiting_pieces"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = summarise(a.run)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("lines_sha256", "lines", "identity", "totals_moved")}, indent=1))
    for k, v in doc["mas_code_totals"].items():
        print(k, v["v3_0_67"], "->", v["v3_0_68"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
