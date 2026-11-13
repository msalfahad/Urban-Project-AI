"""T-750 read-only run: ARCH_TAKEOFF_V3.0.80 (WP_GATE_B_V1 + ROOF_LAYER_GATE_B_V1, R-T750-1) on the candidate V3.0.79
(T-314 r3, Gate B READY on 597d2820; stacked build). Exactly research/agents_t314/v3079_run.py (its inputs unchanged; it
runs the whole chain and asserts V3_0_78 = the T-738 run of record) with --method ARCH_TAKEOFF_V3.0.80 and
--v3080-inputs (t750_inputs.inputs(): the merged T-691 / T-702 / T-710 / T-734 ledgers as mapped by T-748 hub H4,
sha-pinned, checked against the V3.0.79 line index) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-750 research/agents_t750/v3080_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t750 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_79 of this run must be the T-314 r3 run of record (asserted by its line index). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT / "research" / "agents_t314") not in sys.path:
    sys.path.insert(0, str(ROOT / "research" / "agents_t314"))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import v3079_run as R79  # noqa: E402  (T-314 r3; imports T-738's v3078_run and the whole chain)
import t750_inputs as L80  # noqa: E402

INDEX79 = ROOT / "research/agents_t314/out/LINE_INDEX_V3_0_79.json"


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-314 r3 v3079_run, re-pointed at V3.0.80 (same inputs + --v3080-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.79", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.80"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3080_inputs.json"
        f.write_text(json.dumps(L80.inputs(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3080-inputs", str(f)])
    M.main = hub
    try:
        R79.main(argv)        # its own wrappers re-point .72 -> ... -> .79 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b79 = hashlib.sha256((d / "V3_0_79_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_80_BOQ_LINES.json").read_bytes()).hexdigest()
    want = json.loads(INDEX79.read_text(encoding="utf-8"))["inputs"]["lines"]
    if b79 != want:
        raise SystemExit(f"V3_0_79 {b79[:8]} is not the T-314 r3 run of record {want[:8]} (its line index)")
    run = json.loads((d / "V3_0_80_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_79", b79[:8], "lines", ident["base_lines"], "-> V3_0_80_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_80_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "wp_roof",
                                                          "roof_buildup_v3_0_31", "outside_rows_identical_to_base",
                                                          "diff")}, sort_keys=True))
    print("totals moved:", json.dumps({k: {f: round((v["v3_0_80"] or {}).get(f, 0) - (v["base"] or {}).get(f, 0), 6)
                                           for f in ("released", "held_low", "held_high", "lines", "bounded_lines",
                                                     "blocked_lines")}
                                       for k, v in run["totals_moved_by_code"].items()}, sort_keys=True))
    for code in sorted(set(ident["census_after"]) | set(ident["census_before"])):
        print("census", code, "before", json.dumps(ident["census_before"].get(code), sort_keys=True))
        print("census", code, "after ", json.dumps(ident["census_after"].get(code), sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
