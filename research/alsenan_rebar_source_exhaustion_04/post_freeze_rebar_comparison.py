"""ALSENAN ROUND 4 - POST-FREEZE rebar comparison (a finding, never a target; nothing is tuned).

Refuses to run unless every Round-4 register still matches registers/INDEX.json. Only then is the human benchmark
row (REBAR / ALL) read. Round 3 and Round 4 buckets are reported side by side - there is no single "total rebar"
because PROJECT_REBAR_FINAL_ESTABLISHED is false.

    python3 research/alsenan_rebar_source_exhaustion_04/post_freeze_rebar_comparison.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = HERE / "registers"
R3 = ROOT / "research/alsenan_rebar_truth_03/registers"


def verify_freeze():
    idx = json.loads((REG / "INDEX.json").read_text())
    bad = [k for k, h in idx["files"].items()
           if hashlib.sha256((REG / f"{k}.json").read_bytes()).hexdigest() != h]
    if bad:
        raise SystemExit(f"REFUSED: registers changed after the freeze: {bad}")
    return idx


def _t(d):
    return {k: round(v / 1000.0, 3) for k, v in d.items() if isinstance(v, (int, float))}


def main():
    idx = verify_freeze()
    st = json.loads((REG / "PROJECT_REBAR_STATUS.json").read_text())
    r4 = _t(st["trade_totals"])
    r3 = _t(json.loads((R3 / "REBAR_OCCURRENCE_REGISTER.json").read_text())["trade_totals"])
    bench = [r for r in json.loads((ROOT / "tests/alsenan/registers_v3b_eval/BENCHMARK_EVALUATION_V3B.json")
                                   .read_text())["rows"] if r["benchmark"] == "REBAR / ALL"][0]
    bq = bench["benchmark_qty"]

    def view(t):
        v = round(t["verified_complete_kg"] + t["lower_bound_kg"], 3)
        p = round(v + t["provisional_kg"] + t.get("budget_kg", 0.0), 3)
        return {"verified_complete": t["verified_complete_kg"], "verified_lower_bound": t["lower_bound_kg"],
                "provisional": t["provisional_kg"], "budget": t.get("budget_kg", 0.0),
                "blocked_audit_never_released": t["audit_kg"], "verified_complete_plus_lower_bound": v,
                "plus_provisional_and_budget": p,
                "verified_vs_benchmark_pct": round(100 * (v - bq) / bq, 1),
                "verified_plus_provisional_vs_benchmark_pct": round(100 * (p - bq) / bq, 1)}

    out = {"SCHEMA": "URBAN_ALSENAN_POST_FREEZE_REBAR_COMPARISON_R4",
           "frozen_index_sha256": hashlib.sha256((REG / "INDEX.json").read_bytes()).hexdigest(),
           "verified_register_hashes": idx["files"],
           "benchmark": {"item": "REBAR / ALL", "qty_t": bq, "class": "WEAK_HUMAN_REFERENCE (round-1 register)",
                         "use": "FINDING_ONLY - never a target"},
           "project_status": st["PROJECT_REBAR_STATUS"],
           "PROJECT_REBAR_FINAL_ESTABLISHED": st["PROJECT_REBAR_FINAL_ESTABLISHED"],
           "round3_t": view(r3), "round4_t": view(r4),
           "known_components_bbs_t": {k: round(v / 1000.0, 3) for k, v in st["known_components_bbs"].items()
                                      if k.endswith("_KG")},
           "reading": "the gap to the benchmark is the BLOCKED populations (temperature steel, anchorage / hooks, "
                      "boundary wall, stair, lift tie beams, planted columns, parapets, ground slab, D5 / CB "
                      "occurrences) plus the provisional share; it is never closed by tuning",
           "rule": "run after the freeze; INDEX hashes verified first"}
    (REG.parent / "POST_FREEZE_REBAR_COMPARISON.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"r3": out["round3_t"], "r4": out["round4_t"], "bench_t": bq}, indent=1))


if __name__ == "__main__":
    main()
