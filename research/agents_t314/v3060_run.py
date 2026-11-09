"""T-314 read-only run: ARCH_TAKEOFF_V3.0.60 (exterior plaster / Sigma face rows, R-T314-1) on the candidate of record
V3.0.59 (T-498, merge 4c37ce2c). Exactly research/agents_t498/v3059_run.py (its inputs unchanged; it asserts V3_0_58
= c9570e6c), with --method ARCH_TAKEOFF_V3.0.60 and --v3060-inputs (t314_inputs.py) added to the one hub call:

    .work/venv/bin/python -I research/agents_t314/v3060_run.py <plan.dxf> <structural.dxf> --out <private>/t314 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_59_BOQ_LINES.json of this run must be the candidate of record 75331a76 (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t498", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3059_run as R59  # noqa: E402  (T-498; wraps T-507 v3058_run and every earlier builder)
import t314_inputs as L60  # noqa: E402

BASE_SHA = "75331a76"            # V3_0_59_BOQ_LINES.json, candidate of record (T-498 Gate B, merge 4c37ce2c)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-498 v3059_run, re-pointed at V3.0.60 (same inputs + --v3060-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.59", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.60"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3060_inputs.json"
        f.write_text(json.dumps(L60.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3060-inputs", str(f)])
    M.main = hub
    try:
        R59.main(argv)        # its own wrappers re-point V3.0.53 -> .. -> .59 and call this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_59_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_60_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_60_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_59", base[:8], "lines", ident["base_lines"], "-> V3_0_60_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_60_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "faces", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps({k: {"base": v["view_base"]["text"] if v["view_base"] else None,
                                           "v3_0_60": v["view_v3_0_60"]["text"]}
                                       for k, v in run["totals_moved_by_code"].items()}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
