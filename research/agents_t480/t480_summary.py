"""T-480 (read-only): the run record research/agents_t480/summary_t480.json from a finished v3054_run.py run directory:
chain hashes, identity, totals moved and every B7-09 FIN.RAILING line before / after (engine ids, states, quantities and
record fields only; no coordinate, no name, no drawing text).

    python3 -I research/agents_t480/t480_summary.py <run dir> --out research/agents_t480/summary_t480.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REC = "rail_runs_v3054"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _row(ln):
    rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC) or {}
    return {"line_id": ln["line_id"], "item_code": ln["item_code"], "element_id": ln["location"]["element_id"],
            "floor": ln["location"].get("floor"), "state": ln["evidence_state"], "lm": ln.get("measured_net"),
            "action": rec.get("action"), "run": rec.get("run"), "physical_flight": rec.get("physical_flight"),
            "home_lines": rec.get("home_lines"),
            "pieces": [{k: p.get(k) for k in ("piece_id", "kind", "status", "plan_m", "rise_m", "length_lm")}
                       for p in rec.get("pieces") or ()] or None}


def build(d):
    d = Path(d)
    chain = {f"V3_0_{n}": _sha(d / f"V3_0_{n}_BOQ_LINES.json") for n in (51, 53, 54)}
    run = json.loads((d / "V3_0_54_RUN.json").read_text(encoding="utf-8"))
    b = json.loads((d / "V3_0_53_BOQ_LINES.json").read_text(encoding="utf-8"))
    a = json.loads((d / "V3_0_54_BOQ_LINES.json").read_text(encoding="utf-8"))
    codes = ("FIN.RAILING", "MET.RAILING.GUARD", "FIN.HANDRAIL")
    before = {ln["line_id"]: _row(ln) for ln in b if ln["item_code"] in codes}
    after = [_row(ln) for ln in a if ln["item_code"] in codes]
    ident = run["identity"]
    return {"task": "T-480", "method": run["method"], "extends": run["extends"], "chain": chain,
            "identity": {k: ident[k] for k in ("base_lines", "v3_0_54_lines", "replaced", "added", "outside_rows",
                                               "outside_rows_identical_to_base", "rail_runs", "diff")},
            "totals_moved_by_code": run["totals_moved_by_code"], "piece_log": run["piece_logs"][0],
            "railing_lines": [dict(r, before=before.get(r["line_id"])) for r in after]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    s = build(a.run_dir)
    Path(a.out).write_text(json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("chain", "identity", "totals_moved_by_code")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
