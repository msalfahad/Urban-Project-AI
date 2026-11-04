"""T-423 read-only run: ARCH_TAKEOFF_V3.0.58 (the T-246 split remainder, R-T423-1) on the candidate of record
V3.0.57 (T-310 r7, merge 87ef8718). Exactly research/agents_t310/v3057_run.py (its inputs unchanged; it asserts
V3_0_56 = 4e25c54f), with --method ARCH_TAKEOFF_V3.0.58 and --v3058-inputs (t423_inputs.py: merged T-283 / T-284 /
T-335 / T-388 / T-312 / T-329 / T-327 pieces, sha-pinned) added to the one hub call:

    .work/venv/bin/python -I research/agents_t423/v3058_run.py <plan.dxf> <structural.dxf> --out <private>/t423 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_57_BOQ_LINES.json of this run must be the candidate of record 25a8b406 (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t310", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3057_run as R57  # noqa: E402  (T-310 r7; puts every earlier inputs builder on sys.path)
import t423_inputs as L58  # noqa: E402

BASE_SHA = "25a8b406"            # V3_0_57_BOQ_LINES.json, candidate of record (T-310 r7 Gate B, merge 87ef8718)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-310 v3057_run, re-pointed at V3.0.58 (same inputs + --v3058-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.57", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.58"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3058_inputs.json"
        f.write_text(json.dumps(L58.build(R57.R56.R55.R54.R53.R51.R50.R48.T131.PID), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3058-inputs", str(f)])
    M.main = hub
    try:
        R57.main(argv)        # its own wrappers re-point V3.0.53 -> .. -> .57 and call this one
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_57_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_58_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_58_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_57", base[:8], "lines", ident["base_lines"], "-> V3_0_58_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_58_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "split_remainder", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_58_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], r.get("element_id"), "|", _q(r["before_base"]), "->",
              _q(r["after_v3_0_58"]), "|", " -> ".join(r["material_state"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
