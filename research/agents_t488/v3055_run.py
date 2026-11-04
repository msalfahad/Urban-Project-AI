"""T-488 read-only run: ARCH_TAKEOFF_V3.0.55 (blockwork wiring conditions, R-T488-1) on the candidate of record
V3.0.54 (T-480, merge 1b66b719). Exactly research/agents_t480/v3054_run.py (its inputs unchanged; it asserts V3_0_53 =
36863f6c), with --method ARCH_TAKEOFF_V3.0.55 and --v3055-inputs (t488_inputs.py: the merged T-449 r3 register and
T-482 conditions) added to the one hub call it makes:

    .work/venv/bin/python -I research/agents_t488/v3055_run.py <plan.dxf> <structural.dxf> --out <private>/t488 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_54_BOQ_LINES.json of this run must be the candidate of record c85c4630 (asserted). Every output goes to --out
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
          ROOT / "research" / "agents_t487", ROOT / "research" / "agents_t480", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3054_run as R54  # noqa: E402  (puts every earlier inputs builder on sys.path)
import t488_inputs as L55  # noqa: E402

BASE_SHA = "c85c4630"            # V3_0_54_BOQ_LINES.json, candidate of record (T-480 Gate B, merge 1b66b719)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of v3054_run, re-pointed at V3.0.55 (same inputs + --v3055-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.54", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.55"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3055_inputs.json"
        f.write_text(json.dumps(L55.build(R54.R53.R51.R50.R48.T131.PID), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3055-inputs", str(f)])
    M.main = hub
    try:
        R54.main(argv)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_54_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_55_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_55_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_54", base[:8], "lines", ident["base_lines"], "-> V3_0_55_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_55_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "wiring", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
