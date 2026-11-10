"""T-665 read-only run: ARCH_TAKEOFF_V3.0.63 (CONCRETE_GATE_B_V2, R-T665-1) on the candidate V3.0.62 (T-661, Gate B
PASS, merge ea1533e4, published 7a9ccbff). Exactly research/agents_t661/v3062_run.py (its inputs unchanged; it runs the
whole chain and asserts V3_0_61 = 2bc99980), with --method ARCH_TAKEOFF_V3.0.63 and --v3063-inputs (t665_inputs.py:
the merged T-658 r2 ledger and the T-595 footing bound, bound to the T-661 V3.0.62 line index, sha-pinned) added to
the one hub call:

    .work/venv/bin/python -I research/agents_t665/v3063_run.py <plan.dxf> <structural.dxf> --out <private>/t665 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_62 of this run must be the T-661 run of record 56207c79 (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t661", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3062_run as R62  # noqa: E402  (T-661; imports T-563's v3061_run and the whole chain)
import t665_inputs as L63  # noqa: E402

V62_SHA = "56207c79"             # V3_0_62_BOQ_LINES.json, T-661 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-661 v3062_run, re-pointed at V3.0.63 (same inputs + --v3063-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.62", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.63"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3063_inputs.json"
        pid = R62.R61.R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID
        f.write_text(json.dumps(L63.build(pid), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3063-inputs", str(f)])
    M.main = hub
    try:
        R62.main(argv)        # its own wrapper re-points V3.0.61 -> .62 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b62 = hashlib.sha256((d / "V3_0_62_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_63_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b62.startswith(V62_SHA):
        raise SystemExit(f"V3_0_62 {b62[:8]} is not the T-661 run of record {V62_SHA}")
    run = json.loads((d / "V3_0_63_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_62", b62[:8], "lines", ident["base_lines"], "-> V3_0_63_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_63_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "confirmed",
                                                          "outside_rows_identical_to_base", "concrete", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_63_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->", _q(r["after_v3_0_63"]),
              "|", " -> ".join(r["class"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
