"""T-677 read-only run: ARCH_TAKEOFF_V3.0.66 (CONCRETE_GATE_B_V5, R-T677-1) on the candidate V3.0.65 (T-671, Gate B
PASS, merge 271ba60f). Exactly research/agents_t671/v3065_run.py (its inputs unchanged; it runs the whole chain and
asserts V3_0_64 = d227173a), with --method ARCH_TAKEOFF_V3.0.66 and --v3066-inputs (t677_inputs.py: the merged
T-673 / T-674 / T-658 ledgers, bound to the T-671 V3.0.65 line index, sha-pinned) added to the one hub call:

    .work/venv/bin/python -I research/agents_t677/v3066_run.py <plan.dxf> <structural.dxf> --out <private>/t677 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_65 of this run must be the T-671 run of record 38af7909 (asserted). Every output goes to --out (outside the
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
          ROOT / "research" / "agents_t671", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3065_run as R65  # noqa: E402  (T-671; imports T-668's v3064_run and the whole chain)
import t677_inputs as L66  # noqa: E402

V65_SHA = "38af7909"             # V3_0_65_BOQ_LINES.json, T-671 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-671 v3065_run, re-pointed at V3.0.66 (same inputs + --v3066-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.65", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.66"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3066_inputs.json"
        pid = R65.R64.R63.R62.R61.R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID
        f.write_text(json.dumps(L66.build(pid), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3066-inputs", str(f)])
    M.main = hub
    try:
        R65.main(argv)        # its own wrapper re-points V3.0.64 -> .65 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b65 = hashlib.sha256((d / "V3_0_65_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_66_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b65.startswith(V65_SHA):
        raise SystemExit(f"V3_0_65 {b65[:8]} is not the T-671 run of record {V65_SHA}")
    run = json.loads((d / "V3_0_66_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_65", b65[:8], "lines", ident["base_lines"], "-> V3_0_66_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_66_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "confirmed",
                                                          "not_applicable", "revalued", "moved_plan",
                                                          "outside_rows_identical_to_base", "concrete", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_66_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->", _q(r["after_v3_0_66"]),
              "|", " -> ".join(r["class"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
