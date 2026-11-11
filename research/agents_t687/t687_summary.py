"""T-687: the integration-package summary of one finished v3069_run.py run (V3_0_68 -> V3_0_69), item codes, engine
ids, states and quantities only (no coordinates, no names):

  - per finish item code (FIN.PLASTER / FIN.PAINT): released, held bounded low .. high, bounded / blank line counts, V3.0.68 -> V3.0.69
    (m2; a blank line is counted, never summed as 0);
  - per changed / added line: piece, action, before -> after, evidence status;
  - the whole-BOQ diff counts, the identity block;
  - the sha256 of V3_0_68 / V3_0_69 BOQ_LINES.

    bash scripts/agent_env.sh run --tree task-T-687 research/agents_t687/t687_summary.py <run dir> \
        --out research/agents_t687/summary_t687.json
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
    l67, l68 = _lines(run / "V3_0_68_BOQ_LINES.json"), _lines(run / "V3_0_69_BOQ_LINES.json")
    t67, t68 = A304.code_totals(l67), A304.code_totals(l68)
    mas = {k: {"v3_0_68": t67.get(k), "v3_0_69": t68.get(k)} for k in sorted(set(t67) | set(t68))
           if k.split("|")[0] in ("FIN.PLASTER", "FIN.PAINT")}
    moved = sorted(k for k in set(t67) | set(t68) if t67.get(k) != t68.get(k))
    led = json.loads((run / "V3_0_69_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_69_RUN.json").read_text(encoding="utf-8"))
    rows = [{"piece": r["piece"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
             "item_code": r["item_code"], "element_id": r["element_id"], "unit": r["unit"], "before": r["before_base"],
             "after": r["after_v3_0_69"], "class": r["class"], "evidence_status": r["evidence_status"],
             "v2_9": r.get("before_released_v2_9")} for r in led["rows"]]
    na = {}
    for ln in l68:
        if ln["item_code"] in ("FIN.PLASTER", "FIN.PAINT") and ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            na[ln["item_code"]] = na.get(ln["item_code"], 0) + 1
    return {"schema": "T687_SUMMARY_V1", "method": rj["method"], "extends": rj["extends"],
            "released_default": rj["released_default"],
            "lines_sha256": {"V3_0_68": hashlib.sha256((run / "V3_0_68_BOQ_LINES.json").read_bytes()).hexdigest(),
                             "V3_0_69": hashlib.sha256((run / "V3_0_69_BOQ_LINES.json").read_bytes()).hexdigest()},
            "lines": {"V3_0_68": len(l67), "V3_0_69": len(l68)},
            "identity": {k: rj["identity"][k] for k in ("replaced", "added", "outside_rows", "finishes",
                                                         "outside_rows_identical_to_base", "diff")},
            "totals_moved": moved, "fin_code_totals": mas, "not_applicable_v3_0_69": na, "rows": rows,
            "waiting": led["waiting_pieces"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = summarise(a.run)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("lines_sha256", "lines", "identity", "totals_moved")}, indent=1))
    for k, v in doc["fin_code_totals"].items():
        print(k, v["v3_0_68"], "->", v["v3_0_69"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
