"""T-703 read-only run: ARCH_TAKEOFF_V3.0.72 (MASONRY_GATE_B_V4, R-T703-1) on the candidate V3.0.71 (T-704 r2, Gate B
PASS). Exactly research/agents_t704/v3071_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_70 =
e8e001de), with --method ARCH_TAKEOFF_V3.0.72 and --v3072-inputs (t703_inputs.py: the merged T-696 / T-713 ledgers,
sha-pinned) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-703 research/agents_t703/v3072_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t703 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_71 of this run must be the T-704 r2 run of record fc0bd98f (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t682", ROOT / "research" / "agents_t677", ROOT / "research" / "agents_t672",
          ROOT / "research" / "agents_t687", ROOT / "research" / "agents_t693", ROOT / "research" / "agents_t704", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3071_run as R71  # noqa: E402  (T-704; imports T-693's v3070_run and the whole chain)
import t703_inputs as L72  # noqa: E402

V71_SHA = "fc0bd98f"             # V3_0_71_BOQ_LINES.json, T-704 r2 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-704 v3071_run, re-pointed at V3.0.72 (same inputs + --v3072-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.71", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.72"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3072_inputs.json"
        f.write_text(json.dumps(L72.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3072-inputs", str(f)])
    M.main = hub
    try:
        R71.main(argv)        # its own wrapper re-points V3.0.70 -> .71 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b71 = hashlib.sha256((d / "V3_0_71_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_72_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b71.startswith(V71_SHA):
        raise SystemExit(f"V3_0_71 {b71[:8]} is not the T-704 r2 run of record {V71_SHA}")
    run = json.loads((d / "V3_0_72_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_71", b71[:8], "lines", ident["base_lines"], "-> V3_0_72_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_72_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "masonry",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps({k: {f: v["v3_0_72"][f] - (v["base"] or {}).get(f, 0)
                                           for f in ("held_low", "held_high")}
                                       for k, v in run["totals_moved_by_code"].items()}, sort_keys=True))
    print("B9 census before:", json.dumps(ident["b9_census_before"], sort_keys=True))
    print("B9 census after: ", json.dumps(ident["b9_census_after"], sort_keys=True))
    print("rounding unchanged:", [x["line_id"] for x in run["piece_logs"][0]["rounding_exact_already_inside"]])
    for r in json.loads((d / "V3_0_72_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["piece"], r["action"], r["line_id"], r["item_code"], r["unit"], "|",
              (r["beside"] or {}).get("value"), "| range", (r["after_v3_0_72"] or {}).get("low"),
              (r["after_v3_0_72"] or {}).get("high"), "| was", (r["before_base"] or {}).get("low"),
              (r["before_base"] or {}).get("high"), "|", " -> ".join(str(x) for x in r["class"]))
    return 0


if __name__ == "__main__":
    main()
