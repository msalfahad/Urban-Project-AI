"""T-498 r3 read-only run: ARCH_TAKEOFF_V3.0.59 (blockwork material lines, R-T498-1) on the candidate of record
V3.0.58 (T-507, merge c94b35c1). Exactly research/agents_t507/v3058_run.py (its inputs unchanged; it runs T-310's
v3057_run and asserts V3_0_57 = 25a8b406), with --method ARCH_TAKEOFF_V3.0.59 and --v3059-inputs (t498_inputs.py)
added to the one hub call (r1 ran this package as V3.0.57, r2 as V3.0.58; T-310 and T-507 merged those numbers first):

    .work/venv/bin/python -I research/agents_t498/v3059_run.py <plan.dxf> <structural.dxf> --out <private>/t498 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_58_BOQ_LINES.json of this run must be the candidate of record c9570e6c (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t488", ROOT / "research" / "agents_t508", ROOT / "research" / "agents_t310",
          ROOT / "research" / "agents_t507", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3058_run as R58  # noqa: E402  (T-507; imports T-310's v3057_run, which puts every earlier builder on sys.path)
import t498_inputs as L59  # noqa: E402

BASE_SHA = "c9570e6c"            # V3_0_58_BOQ_LINES.json, candidate of record (T-507 Gate B, merge c94b35c1)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-507 v3058_run, re-pointed at V3.0.59 (same inputs + --v3059-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.58", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.59"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3059_inputs.json"
        f.write_text(json.dumps(L59.build(R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID), ensure_ascii=False,
                                indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3059-inputs", str(f)])
    M.main = hub
    try:
        R58.main(argv)        # its own wrappers re-point V3.0.53 -> .. -> .58 and call this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_58_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_59_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_59_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_58", base[:8], "lines", ident["base_lines"], "-> V3_0_59_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_59_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "materials", "diff")},
                                  sort_keys=True))
    print("totals moved (T-512 view):", json.dumps({k: {"base": v["view_base"]["text"] if v["view_base"] else None,
                                                        "v3_0_59": v["view_v3_0_59"]["text"]}
                                                    for k, v in run["totals_moved_by_code"].items()},
                                                   indent=1, sort_keys=True))
    print("codes with no valued line (printed HELD, never 0.0):", len(run["codes_held_no_valued_line"]))
    return 0


if __name__ == "__main__":
    main()
