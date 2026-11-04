"""T-487 read-only run: ARCH_TAKEOFF_V3.0.53 (B9-02 lintel lines, R-T487-1) on the candidate of record V3.0.51 (T-483
r2, merge ea7d375f). Exactly research/agents_t483/v3051_run.py (its inputs unchanged; it asserts V3_0_50 = d40c4ec5),
with --method ARCH_TAKEOFF_V3.0.53 and --v3053-inputs (t487_inputs.py: the merged T-453 r2 lintel ledger) added to the one
hub call it makes:

    .work/venv/bin/python -I research/agents_t487/v3053_run.py <plan.dxf> <structural.dxf> --out <private>/t487 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_51_BOQ_LINES.json of this run must be the candidate of record c0b6d664 (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t350r4", ROOT / "research" / "agents_t497", ROOT / "research" / "agents_t483",
          HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3051_run as R51  # noqa: E402  (puts every earlier inputs builder on sys.path)
import t487_inputs as L53  # noqa: E402

BASE_SHA = "c0b6d664"            # V3_0_51_BOQ_LINES.json, candidate of record (T-483 r2 Gate B, merge ea7d375f)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of v3051_run, re-pointed at V3.0.53 (same inputs + --v3053-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.51", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.53"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3053_inputs.json"
        f.write_text(json.dumps(L53.build(R51.R50.R48.T131.PID), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3053-inputs", str(f)])
    M.main = hub
    try:
        R51.main(argv)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_51_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_53_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_53_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_51", base[:8], "lines", ident["base_lines"], "-> V3_0_53_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_53_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "lintels", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
