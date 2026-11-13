"""T-661 read-only run: ARCH_TAKEOFF_V3.0.62 (CONCRETE_GATE_B_V1, R-T661-1) on the candidate V3.0.61 (T-563, Gate B,
merge e04d99d9; promoted 1.62.0 by T-655). Exactly research/agents_t563/v3061_run.py (its inputs unchanged; it runs the
whole chain and asserts V3_0_59 = 75331a76, V3_0_60 = 8c8a9642), with --method ARCH_TAKEOFF_V3.0.62 and
--v3062-inputs (t661_inputs.py: the merged T-657 / T-659 / T-660 member ledgers bound to the T-655 V3.0.61 line index,
sha-pinned) added to the one hub call:

    .work/venv/bin/python -I research/agents_t661/v3062_run.py <plan.dxf> <structural.dxf> --out <private>/t661 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_61 of this run must be the run of record 2bc99980 (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t563", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3061_run as R61  # noqa: E402  (T-563; imports T-423's v3060_run and the whole chain)
import t661_inputs as L62  # noqa: E402

V61_SHA = "2bc99980"             # V3_0_61_BOQ_LINES.json, T-563 run of record (reproduced by T-655)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-563 v3061_run, re-pointed at V3.0.62 (same inputs + --v3062-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.61", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.62"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3062_inputs.json"
        f.write_text(json.dumps(L62.build(R61.R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID),
                                ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3062-inputs", str(f)])
    M.main = hub
    try:
        R61.main(argv)        # its own wrappers re-point V3.0.53 -> .. -> .61 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b61 = hashlib.sha256((d / "V3_0_61_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_62_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b61.startswith(V61_SHA):
        raise SystemExit(f"V3_0_61 {b61[:8]} is not the T-563 run of record {V61_SHA}")
    run = json.loads((d / "V3_0_62_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_61", b61[:8], "lines", ident["base_lines"], "-> V3_0_62_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_62_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "confirmed",
                                                          "outside_rows_identical_to_base", "concrete", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_62_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->", _q(r["after_v3_0_62"]),
              "|", " -> ".join(r["class"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
