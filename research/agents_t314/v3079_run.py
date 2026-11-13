"""T-314 r3 read-only run: ARCH_TAKEOFF_V3.0.79 (EXT_RENDER_GATE_B_V1 + EXT_PAINT_GATE_B_V1 + EXT_EDGE_DELTA_V1,
R-T314-3) on the candidate V3.0.78 (T-738 r2, Gate B READY on 49d21678; stacked build). Exactly
research/agents_t738/v3078_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_77 = the T-749 run of
record), with --method ARCH_TAKEOFF_V3.0.79 and --v3079-inputs (t314_inputs.inputs(): the merged T-756 face ledger,
sha-pinned, checked against the V3.0.78 line index) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-314 research/agents_t314/v3079_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t314 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_78 of this run must be the T-738 run of record (asserted by its line index). Every output goes to --out (outside
the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
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
          ROOT / "research" / "agents_t729", ROOT / "research" / "agents_t736", ROOT / "research" / "agents_t749",
          ROOT / "research" / "agents_t738", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3078_run as R78  # noqa: E402  (T-738; imports T-749's v3077_run and the whole chain)
import t314_inputs as L79  # noqa: E402

INDEX78 = ROOT / "research/agents_t738/out/LINE_INDEX_V3_0_78.json"


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-738 v3078_run, re-pointed at V3.0.79 (same inputs + --v3079-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.78", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.79"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3079_inputs.json"
        f.write_text(json.dumps(L79.inputs(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3079-inputs", str(f)])
    M.main = hub
    try:
        R78.main(argv)        # its own wrappers re-point .72 -> .73 -> ... -> .78 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b78 = hashlib.sha256((d / "V3_0_78_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_79_BOQ_LINES.json").read_bytes()).hexdigest()
    want = json.loads(INDEX78.read_text(encoding="utf-8"))["inputs"]["lines"]
    if b78 != want:
        raise SystemExit(f"V3_0_78 {b78[:8]} is not the T-738 run of record {want[:8]} (its line index)")
    run = json.loads((d / "V3_0_79_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_78", b78[:8], "lines", ident["base_lines"], "-> V3_0_79_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_79_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "ext_render_paint",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps({k: {f: round((v["v3_0_79"] or {}).get(f, 0) - (v["base"] or {}).get(f, 0), 6)
                                           for f in ("released", "held_low", "held_high", "lines", "bounded_lines",
                                                     "blocked_lines")}
                                       for k, v in run["totals_moved_by_code"].items()}, sort_keys=True))
    for code in sorted(set(ident["census_after"]) | set(ident["census_before"])):
        print("census", code, "before", json.dumps(ident["census_before"].get(code), sort_keys=True))
        print("census", code, "after ", json.dumps(ident["census_after"].get(code), sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
