"""T-497 read-only run: ARCH_TAKEOFF_V3.0.50 (excavation zone ownership, R-T497-1) on the candidate of record V3.0.48
(T-350 r4, merge 5de697ff). Exactly research/agents_t350r4/v3048_run.py (its inputs unchanged; it asserts V3_0_47 =
e86a53a8), with --method ARCH_TAKEOFF_V3.0.50 and --v3050-inputs (t497_inputs.py: the T-497 re-measure, pinned, equal to
the Checker's F-C-T350R4-1 figures) added to the one hub call it makes:

    .work/venv/bin/python -I research/agents_t497/v3050_run.py <plan.dxf> <structural.dxf> --out <private>/t497 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_48_BOQ_LINES.json of this run must be the candidate of record 33a81c53 (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t350r4", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3048_run as R48  # noqa: E402  (puts every earlier inputs builder on sys.path)
import t497_inputs as L50  # noqa: E402

BASE_SHA = "33a81c53"            # V3_0_48_BOQ_LINES.json, candidate of record (T-350 r4 Gate B, merge 5de697ff)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of v3048_run, re-pointed at V3.0.50 (same inputs + --v3050-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.48", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.50"
        o = Path(args[args.index("--out") + 1])
        args[args.index("--out") + 1] = str(o.parent / "v3050")
        f = o.parent / "v3050_inputs.json"
        f.write_text(json.dumps(L50.build(R48.T131.PID), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o.parent / "v3050"
        rc = real(args + ["--v3050-inputs", str(f)])
        # v3048_run reads its own out dir next: point it at the same files (V3_0_47 / V3_0_48 are written there too)
        o.mkdir(parents=True, exist_ok=True)
        for name in ("V3_0_47_BOQ_LINES.json", "V3_0_48_BOQ_LINES.json", "V3_0_48_RUN.json"):
            (o / name).write_bytes((seen["out"] / name).read_bytes())
        return rc
    M.main = hub
    try:
        R48.main(argv)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_48_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_50_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_50_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_48", base[:8], "lines", ident["base_lines"], "-> V3_0_50_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_50_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "earthworks", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
