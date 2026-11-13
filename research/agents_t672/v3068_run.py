"""T-672 read-only run: ARCH_TAKEOFF_V3.0.68 (MASONRY_GATE_B_V1, R-T672-1) on the candidate V3.0.67 (T-682, Gate B
PASS). Exactly research/agents_t682/v3067_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_66 =
c411617d), with --method ARCH_TAKEOFF_V3.0.68 and --v3068-inputs (t672_inputs.py: the merged T-670 / T-372 / T-675
ledgers, sha-pinned, and the merged V3.0.59 producer inputs) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-672 research/agents_t672/v3068_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t672 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_67 of this run must be the T-682 run of record a29a11a9 (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t682", ROOT / "research" / "agents_t677", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3067_run as R67  # noqa: E402  (T-682; imports T-677's v3066_run and the whole chain)
import t672_inputs as L68  # noqa: E402

V67_SHA = "a29a11a9"             # V3_0_67_BOQ_LINES.json, T-682 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-682 v3067_run, re-pointed at V3.0.68 (same inputs + --v3068-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.67", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.68"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3068_inputs.json"
        f.write_text(json.dumps(L68.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3068-inputs", str(f)])
    M.main = hub
    try:
        R67.main(argv)        # its own wrapper re-points V3.0.66 -> .67 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b67 = hashlib.sha256((d / "V3_0_67_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_68_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b67.startswith(V67_SHA):
        raise SystemExit(f"V3_0_67 {b67[:8]} is not the T-682 run of record {V67_SHA}")
    run = json.loads((d / "V3_0_68_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_67", b67[:8], "lines", ident["base_lines"], "-> V3_0_68_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_68_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "masonry", "scenarios",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_68_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["piece"], r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->",
              _q(r["after_v3_0_68"]), "|", " -> ".join(str(x) for x in r["class"]), "|", r["evidence_status"])
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
