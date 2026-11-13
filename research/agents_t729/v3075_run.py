"""T-729 read-only run: ARCH_TAKEOFF_V3.0.75 (FORMWORK_GATE_B_V1 + CONCRETE_GATE_B_V10, R-T729-1) on the candidate
V3.0.74 (T-717 r2, Gate B PASS, merge e6481b43). Exactly research/agents_t717/v3074_run.py (its inputs unchanged; it
runs the whole chain, its region check and asserts V3_0_73 = c5a0b128), with --method ARCH_TAKEOFF_V3.0.75 and
--v3075-inputs (t729_inputs.inputs(): the merged T-714 / T-724 / T-725 / T-731 / T-732 / T-735 ledgers and the T-730
map, sha-pinned, checked line by line against the V3.0.74 line index) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-729 research/agents_t729/v3075_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t729 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_74 of this run must be the T-717 run of record (asserted by its line index: research/agents_t717/out/
LINE_INDEX_V3_0_74.json names the lines sha). Every output goes to --out (outside the repository); printed: item codes,
units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t682", ROOT / "research" / "agents_t677", ROOT / "research" / "agents_t672",
          ROOT / "research" / "agents_t687", ROOT / "research" / "agents_t693", ROOT / "research" / "agents_t704",
          ROOT / "research" / "agents_t703", ROOT / "research" / "agents_t722", ROOT / "research" / "agents_t717",
          HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3074_run as R74  # noqa: E402  (T-717; imports T-722's v3073_run and the whole chain)
import t729_inputs as L75  # noqa: E402

INDEX74 = ROOT / "research/agents_t717/out/LINE_INDEX_V3_0_74.json"


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-717 v3074_run, re-pointed at V3.0.75 (same inputs + --v3075-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.74", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.75"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3075_inputs.json"
        f.write_text(json.dumps(L75.inputs(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3075-inputs", str(f)])
    M.main = hub
    try:
        R74.main(argv)        # its own wrappers re-point .72 -> .73 -> .74 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b74 = hashlib.sha256((d / "V3_0_74_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_75_BOQ_LINES.json").read_bytes()).hexdigest()
    want = json.loads(INDEX74.read_text(encoding="utf-8"))["inputs"]["lines"]
    if b74 != want:
        raise SystemExit(f"V3_0_74 {b74[:8]} is not the T-717 run of record {want[:8]} (its line index)")
    run = json.loads((d / "V3_0_75_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_74", b74[:8], "lines", ident["base_lines"], "-> V3_0_75_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_75_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "formwork_concrete",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps({k: {f: round(v["v3_0_75"][f] - (v["base"] or {}).get(f, 0), 6)
                                           for f in ("released", "held_low", "held_high", "lines", "bounded_lines",
                                                     "blocked_lines")}
                                       for k, v in run["totals_moved_by_code"].items()}, sort_keys=True))
    for code in sorted(ident["census_after"]):
        print("census", code, "before", json.dumps(ident["census_before"].get(code), sort_keys=True))
        print("census", code, "after ", json.dumps(ident["census_after"][code], sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
