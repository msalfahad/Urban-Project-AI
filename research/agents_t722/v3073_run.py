"""T-722 read-only run: ARCH_TAKEOFF_V3.0.73 (CONCRETE_GATE_B_V9, R-T722-1) on the candidate V3.0.72 (T-703, Gate B
PASS). Exactly research/agents_t703/v3072_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_71 =
fc0bd98f), with --method ARCH_TAKEOFF_V3.0.73 and --v3073-inputs (t722_inputs.py: the merged T-707 / T-711 / T-712 /
T-721 ledgers and the T-723 map, sha-pinned, each ledger rebuilt by its own builder) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-722 research/agents_t722/v3073_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t722 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_72 of this run must be the T-703 run of record (asserted by its line index: research/agents_t703/out/
LINE_INDEX_V3_0_72.json names the lines sha). Every output goes to --out (outside the repository); printed: item codes,
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
          ROOT / "research" / "agents_t703", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3072_run as R72  # noqa: E402  (T-703; imports T-704's v3071_run and the whole chain)
import t722_inputs as L73  # noqa: E402

INDEX72 = ROOT / "research/agents_t703/out/LINE_INDEX_V3_0_72.json"


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-703 v3072_run, re-pointed at V3.0.73 (same inputs + --v3073-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.72", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.73"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3073_inputs.json"
        L73.rebuild_ledgers()
        f.write_text(json.dumps(L73.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3073-inputs", str(f)])
    M.main = hub
    try:
        R72.main(argv)        # its own wrappers re-point V3.0.71 -> .72 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b72 = hashlib.sha256((d / "V3_0_72_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_73_BOQ_LINES.json").read_bytes()).hexdigest()
    want = json.loads(INDEX72.read_text(encoding="utf-8"))["inputs"]["lines"]
    if b72 != want:
        raise SystemExit(f"V3_0_72 {b72[:8]} is not the T-703 run of record {want[:8]} (its line index)")
    run = json.loads((d / "V3_0_73_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_72", b72[:8], "lines", ident["base_lines"], "-> V3_0_73_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_73_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "concrete",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps({k: {f: round(v["v3_0_73"][f] - (v["base"] or {}).get(f, 0), 6)
                                           for f in ("released", "held_low", "held_high", "bounded_lines",
                                                     "blocked_lines")}
                                       for k, v in run["totals_moved_by_code"].items()}, sort_keys=True))
    print("confirmed:", json.dumps([(c["line_id"], c["value"], c["record"]) for c in
                                    run["piece_logs"][0]["confirmed_unchanged"]]))
    print("restated:", json.dumps(run["piece_logs"][0]["restated"]))
    for code in sorted(ident["conc_census_after"]):
        print("census", code, "before", json.dumps(ident["conc_census_before"][code], sort_keys=True))
        print("census", code, "after ", json.dumps(ident["conc_census_after"][code], sort_keys=True))
    for r in json.loads((d / "V3_0_73_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", (r["beside"] or {}).get("value"), "| range",
              (r["after_v3_0_73"] or {}).get("low"), (r["after_v3_0_73"] or {}).get("high"), "| was",
              (r["before_base"] or {}).get("low"), (r["before_base"] or {}).get("high"), "| before beside",
              [b["value"] for b in r["beside_before"] or ()], "|", " -> ".join(str(x) for x in r["class"]))
    return 0


if __name__ == "__main__":
    main()
