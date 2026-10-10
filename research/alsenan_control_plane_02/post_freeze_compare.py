"""ALSENAN CONTROL-PLANE ROUND 2 - POST-FREEZE benchmark comparison (differences only; nothing is tuned).

Runs only after build_control_v2.py has frozen registers/INDEX.json: every register hash is re-verified first and the
script refuses to run if any differs. Only then are the human benchmark rows read (registers_v3b_eval). The output
reports, per benchmark item, the V2 verified / lower-bound / provisional totals beside the benchmark and the old V3b
technical total. A difference is a finding, never a target.

    python3 research/alsenan_control_plane_02/post_freeze_compare.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = HERE / "registers"

# benchmark item -> V3b summary rows: re-used verbatim from the V3b post-freeze evaluation (alsenan_v3b_evaluation.MAP)
# so the old and the new comparison select exactly the same lines; a summary row selects lines, never a value
sys.path.insert(0, str(ROOT / "research" / "external_engine_lab"))
from alsenan_v3b_evaluation import MAP as V3B_MAP  # noqa: E402

MAP = {f"{bt} / {bs}": items for (bt, bs), items, _cause, _next in V3B_MAP}


def verify_freeze():
    idx = json.loads((REG / "INDEX.json").read_text())
    bad = [k for k, h in idx["registers"].items()
           if hashlib.sha256((REG / f"{k}.json").read_bytes()).hexdigest() != h]
    if bad:
        raise SystemExit(f"REFUSED: registers changed after the freeze: {bad}")
    return idx


def main():
    idx = verify_freeze()
    cand = json.loads((REG / "ALSENAN_CONTROL_V2_CANDIDATE.json").read_text())
    mig = {r["code"] + "|" + r["line_id"]: r for r in
           json.loads((REG / "RELEASE_V2_MIGRATION_REGISTER.json").read_text())["rows"]}
    bench = json.loads((ROOT / "tests/alsenan/registers_v3b_eval/BENCHMARK_EVALUATION_V3B.json").read_text())["rows"]
    rows = []
    for b in bench:
        items = {(t, i, u) for t, i, u in MAP[b["benchmark"]]}
        unit = next(iter(items))[2]
        acc = {"verified": 0.0, "lower_bound": 0.0, "provisional": 0.0, "budget": 0.0, "blocked_audit": 0.0,
               "old_v3b_technical": 0.0}
        n = 0
        for ln in cand["lines"]:
            if ln["no_total"] or not ln["sumrow"] or (ln["trade"], ln["sumrow"], ln["unit"]) not in items:
                continue
            n += 1
            m = mig[ln["code"] + "|" + ln["line_id"]]
            for k, v in ln["v2_qty"].items():    # the same per-state quantities the candidate totals use
                if v is not None:
                    acc["blocked_audit" if k == "audit" else k] += v
            if m["old_in_technical_total"] and m["old_qty"] is not None:
                acc["old_v3b_technical"] += m["old_qty"]
        scale = 0.001 if unit == "kg" else 1.0
        acc = {k: round(v * scale, 3) for k, v in acc.items()}
        bq = b["benchmark_qty"]
        rows.append({"benchmark": b["benchmark"], "benchmark_qty": bq, "benchmark_unit": b["unit"], "lines": n,
                     "v3b_eval_technical": b["v3b_technical"],
                     "line_selection_identical_to_v3b_eval": round(acc["old_v3b_technical"], 3) == b["v3b_technical"],
                     **{f"v2_{k}": v for k, v in acc.items()},
                     "v2_verified_plus_lower_bound": round(acc["verified"] + acc["lower_bound"], 3),
                     "diff_verified_pct": round(100 * (acc["verified"] - bq) / bq, 1) if bq else None,
                     "diff_verified_plus_lower_bound_pct":
                         round(100 * (acc["verified"] + acc["lower_bound"] - bq) / bq, 1) if bq else None,
                     "use": "FINDING_ONLY"})
    assert all(r["line_selection_identical_to_v3b_eval"] for r in rows), "line selection differs from the V3b eval"
    out = {"SCHEMA": "URBAN_ALSENAN_POST_FREEZE_BENCHMARK_COMPARISON_V1", "frozen_index_sha256":
           hashlib.sha256((REG / "INDEX.json").read_bytes()).hexdigest(), "verified_register_hashes": idx["registers"],
           "rows": rows,
           "rule": "run after the freeze; every register hash verified first; differences are findings, never "
                   "targets; benchmark classes (WEAK / STRONG) are in round-1 BENCHMARK_CONFIDENCE_REGISTER"}
    (HERE / "POST_FREEZE_BENCHMARK_COMPARISON.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for r in rows:
        print(f"{r['benchmark']:34s} bench {r['benchmark_qty']:>10} verified {r['v2_verified']:>10} "
              f"+LB {r['v2_verified_plus_lower_bound']:>10} prov {r['v2_provisional']:>10}")


if __name__ == "__main__":
    main()
