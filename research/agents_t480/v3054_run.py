"""T-480 read-only run: ARCH_TAKEOFF_V3.0.54 (B7-09 railing runs, R-T480-1) on the candidate of record V3.0.53 (T-487,
merge dbc619fd). Exactly research/agents_t487/v3053_run.py (its inputs unchanged; it asserts V3_0_51 = c0b6d664), with
--method ARCH_TAKEOFF_V3.0.54 and --v3054-inputs (t480_inputs.py: the merged T-476 census) added to the one hub call:

    .work/venv/bin/python -I research/agents_t480/v3054_run.py <plan.dxf> <structural.dxf> --out <private>/t480 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_53_BOQ_LINES.json of this run must be the candidate of record 36863f6c (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t487", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3053_run as R53  # noqa: E402  (puts every earlier inputs builder on sys.path)
import t480_inputs as L54  # noqa: E402

BASE_SHA = "36863f6c"            # V3_0_53_BOQ_LINES.json, candidate of record (T-487 Gate B, merge dbc619fd)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of v3053_run, re-pointed at V3.0.54 (same inputs + --v3054-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.53", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.54"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3054_inputs.json"
        f.write_text(json.dumps(L54.build(R53.R51.R50.R48.T131.PID), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3054-inputs", str(f)])
    M.main = hub
    try:
        R53.main(argv)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_53_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_54_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_54_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_53", base[:8], "lines", ident["base_lines"], "-> V3_0_54_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_54_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "rail_runs", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
