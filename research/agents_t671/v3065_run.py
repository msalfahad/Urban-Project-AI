"""T-671 read-only run: ARCH_TAKEOFF_V3.0.65 (CONCRETE_GATE_B_V4, R-T671-1) on the candidate V3.0.64 (T-668, Gate B
PASS, merge 033b52b9). Exactly research/agents_t668/v3064_run.py (its inputs unchanged; it runs the whole chain and
asserts V3_0_63 = 09ec4c1a), with --method ARCH_TAKEOFF_V3.0.65 and --v3065-inputs (t671_inputs.py: the merged
T-669 / T-647 / T-642 ledgers, bound to the T-668 V3.0.64 line index, sha-pinned) added to the one hub call:

    .work/venv/bin/python -I research/agents_t671/v3065_run.py <plan.dxf> <structural.dxf> --out <private>/t671 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_64 of this run must be the T-668 run of record d227173a (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t661", ROOT / "research" / "agents_t665", ROOT / "research" / "agents_t668",
          HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3064_run as R64  # noqa: E402  (T-668; imports T-665's v3063_run and the whole chain)
import t671_inputs as L65  # noqa: E402

V64_SHA = "d227173a"             # V3_0_64_BOQ_LINES.json, T-668 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-668 v3064_run, re-pointed at V3.0.65 (same inputs + --v3065-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.64", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.65"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3065_inputs.json"
        pid = R64.R63.R62.R61.R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID
        f.write_text(json.dumps(L65.build(pid), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3065-inputs", str(f)])
    M.main = hub
    try:
        R64.main(argv)        # its own wrapper re-points V3.0.63 -> .64 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b64 = hashlib.sha256((d / "V3_0_64_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_65_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b64.startswith(V64_SHA):
        raise SystemExit(f"V3_0_64 {b64[:8]} is not the T-668 run of record {V64_SHA}")
    run = json.loads((d / "V3_0_65_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_64", b64[:8], "lines", ident["base_lines"], "-> V3_0_65_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_65_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "confirmed",
                                                          "not_applicable", "outside_rows_identical_to_base",
                                                          "concrete", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_65_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->", _q(r["after_v3_0_65"]),
              "|", " -> ".join(r["class"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
