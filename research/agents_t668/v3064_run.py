"""T-668 read-only run: ARCH_TAKEOFF_V3.0.64 (CONCRETE_GATE_B_V3, R-T668-1) on the candidate V3.0.63 (T-665, Gate B
PASS, merge 12acd3d4, published b5df949c). Exactly research/agents_t665/v3063_run.py (its inputs unchanged; it runs the
whole chain and asserts V3_0_62 = 56207c79), with --method ARCH_TAKEOFF_V3.0.64 and --v3064-inputs (t668_inputs.py:
the merged T-666 / T-659 / T-667 ledgers, bound to the T-665 V3.0.63 line index, sha-pinned) added to the one hub
call:

    .work/venv/bin/python -I research/agents_t668/v3064_run.py <plan.dxf> <structural.dxf> --out <private>/t668 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_63 of this run must be the T-665 run of record 09ec4c1a (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t661", ROOT / "research" / "agents_t665", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3063_run as R63  # noqa: E402  (T-665; imports T-661's v3062_run and the whole chain)
import t668_inputs as L64  # noqa: E402

V63_SHA = "09ec4c1a"             # V3_0_63_BOQ_LINES.json, T-665 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-665 v3063_run, re-pointed at V3.0.64 (same inputs + --v3064-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.63", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.64"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3064_inputs.json"
        pid = R63.R62.R61.R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID
        f.write_text(json.dumps(L64.build(pid), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3064-inputs", str(f)])
    M.main = hub
    try:
        R63.main(argv)        # its own wrapper re-points V3.0.62 -> .63 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b63 = hashlib.sha256((d / "V3_0_63_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_64_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b63.startswith(V63_SHA):
        raise SystemExit(f"V3_0_63 {b63[:8]} is not the T-665 run of record {V63_SHA}")
    run = json.loads((d / "V3_0_64_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_63", b63[:8], "lines", ident["base_lines"], "-> V3_0_64_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_64_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "confirmed",
                                                          "outside_rows_identical_to_base", "concrete", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_64_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->", _q(r["after_v3_0_64"]),
              "|", " -> ".join(r["class"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
