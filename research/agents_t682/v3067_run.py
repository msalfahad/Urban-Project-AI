"""T-682 read-only run: ARCH_TAKEOFF_V3.0.67 (CONCRETE_GATE_B_V6, R-T682-2) on the candidate V3.0.66 (T-677, Gate B
PASS, merge 8a28bce5). Exactly research/agents_t677/v3066_run.py (its inputs unchanged; it runs the whole chain and
asserts V3_0_65 = 38af7909), with --method ARCH_TAKEOFF_V3.0.67 and --v3067-inputs (t682_inputs.py: the merged T-678
ledger, bound to the T-677 V3.0.66 line index, sha-pinned) added to the one hub call:

    .work/venv/bin/python -I research/agents_t682/v3067_run.py <plan.dxf> <structural.dxf> --out <private>/t682 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_66 of this run must be the T-677 run of record c411617d (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t677", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3066_run as R66  # noqa: E402  (T-677; imports T-671's v3065_run and the whole chain)
import t682_inputs as L67  # noqa: E402

V66_SHA = "c411617d"             # V3_0_66_BOQ_LINES.json, T-677 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-677 v3066_run, re-pointed at V3.0.67 (same inputs + --v3067-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.66", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.67"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3067_inputs.json"
        f.write_text(json.dumps(L67.build(R66.R65.R64.R63.R62.R61.R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3067-inputs", str(f)])
    M.main = hub
    try:
        R66.main(argv)        # its own wrapper re-points V3.0.65 -> .66 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b66 = hashlib.sha256((d / "V3_0_66_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_67_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b66.startswith(V66_SHA):
        raise SystemExit(f"V3_0_66 {b66[:8]} is not the T-677 run of record {V66_SHA}")
    run = json.loads((d / "V3_0_67_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_66", b66[:8], "lines", ident["base_lines"], "-> V3_0_67_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_67_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "assumed_owner_approved",
                                                          "plane_transferred", "outside_rows_identical_to_base",
                                                          "concrete", "lintels", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_67_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], "|", _q(r["before_base"]), "->", _q(r["after_v3_0_67"]),
              "|", " -> ".join(r["class"]), "|", (r.get("existence") or {}).get("status"))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
