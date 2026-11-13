"""T-704 read-only run: ARCH_TAKEOFF_V3.0.71 (CONCRETE_GATE_B_V8, R-T704-1) on the candidate V3.0.70 (T-693, Gate B
PASS). Exactly research/agents_t693/v3070_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_69 =
7ea65f9b), with --method ARCH_TAKEOFF_V3.0.71 and --v3071-inputs (t704_inputs.py: the merged T-699 ledger, sha-pinned)
added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-704 research/agents_t704/v3071_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t704 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_70 of this run must be the T-693 run of record e8e001de (asserted). Every output goes to --out (outside the
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
          ROOT / "research" / "agents_t687", ROOT / "research" / "agents_t693", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3070_run as R70  # noqa: E402  (T-693; imports T-687's v3069_run and the whole chain)
import t704_inputs as L71  # noqa: E402

V70_SHA = "e8e001de"             # V3_0_70_BOQ_LINES.json, T-693 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-693 v3070_run, re-pointed at V3.0.71 (same inputs + --v3071-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.70", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.71"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3071_inputs.json"
        f.write_text(json.dumps(L71.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3071-inputs", str(f)])
    M.main = hub
    try:
        R70.main(argv)        # its own wrapper re-points V3.0.69 -> .70 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b70 = hashlib.sha256((d / "V3_0_70_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_71_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b70.startswith(V70_SHA):
        raise SystemExit(f"V3_0_70 {b70[:8]} is not the T-693 run of record {V70_SHA}")
    run = json.loads((d / "V3_0_71_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_70", b70[:8], "lines", ident["base_lines"], "-> V3_0_71_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_71_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "lintels",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], sort_keys=True))
    print("family / confirmed:", json.dumps({k: run["piece_logs"][0][k] for k in ("family_at_most",
                                                                                 "confirmed_unchanged")}))
    for r in json.loads((d / "V3_0_71_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["piece"], r["action"], r["line_id"], r["element_id"], "|", r["existence"], "| beside",
              (r["beside"] or {}).get("value"), "| if REQUIRED", (r["if_required"] or {}).get("value_m3"), "|",
              " -> ".join(str(x) for x in r["class"]))
    return 0


if __name__ == "__main__":
    main()
