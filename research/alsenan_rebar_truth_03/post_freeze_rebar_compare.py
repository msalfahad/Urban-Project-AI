"""ALSENAN ROUND 3 - POST-FREEZE rebar benchmark comparison (a finding, never a target; nothing is tuned).

Refuses to run unless every Round-3 register still matches registers/INDEX.json. Only then is the human benchmark
row (REBAR / ALL) read from the V3b post-freeze evaluation. The Round-3 buckets are reported beside it - there is no
single "total rebar" because the project population is not complete.

    python3 research/alsenan_rebar_truth_03/post_freeze_rebar_compare.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = HERE / "registers"


def verify_freeze():
    idx = json.loads((REG / "INDEX.json").read_text())
    bad = [k for k, h in idx["registers"].items()
           if hashlib.sha256((REG / f"{k}.json").read_bytes()).hexdigest() != h]
    if bad:
        raise SystemExit(f"REFUSED: registers changed after the freeze: {bad}")
    return idx


def main():
    idx = verify_freeze()
    t = json.loads((REG / "REBAR_OCCURRENCE_REGISTER.json").read_text())["trade_totals"]
    bench = [r for r in json.loads((ROOT / "tests/alsenan/registers_v3b_eval/BENCHMARK_EVALUATION_V3B.json")
                                   .read_text())["rows"] if r["benchmark"] == "REBAR / ALL"][0]
    r2 = json.loads((ROOT / "research/alsenan_control_plane_02/registers/ALSENAN_CONTROL_V2_CANDIDATE.json")
                    .read_text())["totals_by_trade_unit"]["REBAR|kg"]
    t_ = {k: round(v / 1000.0, 3) for k, v in t.items() if isinstance(v, (int, float))}
    vc_lb = t_["verified_complete_kg"] + t_["lower_bound_kg"]
    bq = bench["benchmark_qty"]
    out = {"SCHEMA": "URBAN_ALSENAN_POST_FREEZE_REBAR_BENCHMARK_V3",
           "frozen_index_sha256": hashlib.sha256((REG / "INDEX.json").read_bytes()).hexdigest(),
           "verified_register_hashes": idx["registers"],
           "benchmark": {"item": "REBAR / ALL", "qty_t": bq, "class": "WEAK_HUMAN_REFERENCE (round-1 register)"},
           "round3_t": {"verified_complete": t_["verified_complete_kg"], "verified_lower_bound": t_["lower_bound_kg"],
                        "provisional": t_["provisional_kg"], "budget": t_["budget_kg"],
                        "blocked_audit_never_released": t_["audit_kg"], "verified_complete_plus_lower_bound": vc_lb,
                        "plus_provisional_and_budget": round(vc_lb + t_["provisional_kg"] + t_["budget_kg"], 3),
                        "project_final_rebar_total": t["project_final_rebar_total"]},
           "round2_t": {k: round(v / 1000.0, 3) for k, v in r2.items() if k != "lines_blocked"},
           "v3b_technical_t": bench["v3b_technical"],
           "differences_pct": {"verified_vs_benchmark": round(100 * (vc_lb - bq) / bq, 1),
                               "verified_plus_provisional_budget_vs_benchmark":
                                   round(100 * (vc_lb + t_["provisional_kg"] + t_["budget_kg"] - bq) / bq, 1)},
           "use": "FINDING_ONLY",
           "rule": "run after the freeze; a difference is explained by blocked / unread populations and never closed by "
                   "tuning"}
    (HERE / "POST_FREEZE_REBAR_BENCHMARK.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["round3_t"]), out["differences_pct"])


if __name__ == "__main__":
    main()
