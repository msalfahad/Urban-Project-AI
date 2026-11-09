"""T-563 read-only run: ARCH_TAKEOFF_V3.0.61 (PLASTER_HEIGHT_V1_WIRING, R-T563-1) on the candidate V3.0.60 (T-423 r3,
READY bdbbb8db; rebased at merge). Exactly research/agents_t423/v3060_run.py (its inputs unchanged; it runs T-498's
v3059_run and asserts V3_0_59 = 75331a76), with --method ARCH_TAKEOFF_V3.0.61 and --v3061-inputs (t563_inputs.py:
merged T-556 table + T-558 manifest, bound to the T-651 V3.0.59 line index, sha-pinned) added to the one hub call:

    .work/venv/bin/python -I research/agents_t563/v3061_run.py <plan.dxf> <structural.dxf> --out <private>/t563 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_59_BOQ_LINES.json of this run must be the candidate of record 75331a76 and V3_0_60 must be the T-423 r3
run of record (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t488", ROOT / "research" / "agents_t508", ROOT / "research" / "agents_t310",
          ROOT / "research" / "agents_t507", ROOT / "research" / "agents_t498", ROOT / "research" / "agents_t423", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3060_run as R60  # noqa: E402  (T-423 r3; imports T-498's v3059_run -> T-507 -> T-310 and every builder)
import t563_inputs as L61  # noqa: E402

BASE_SHA = "75331a76"            # V3_0_59_BOQ_LINES.json, candidate of record (T-498 r3 Gate B, merge 4c37ce2c)
V60_SHA = "8c8a9642"             # V3_0_60_BOQ_LINES.json of the T-423 r3 run (its package section; rebased at merge)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-423 v3060_run, re-pointed at V3.0.61 (same inputs + --v3061-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.60", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.61"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3061_inputs.json"
        f.write_text(json.dumps(L61.build(R60.R59.R58.R57.R56.R55.R54.R53.R51.R50.R48.T131.PID), ensure_ascii=False,
                                indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3061-inputs", str(f)])
    M.main = hub
    try:
        R60.main(argv)        # its own wrappers re-point V3.0.53 -> .. -> .60 and call this one (their asserts run)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_59_BOQ_LINES.json").read_bytes()).hexdigest()
    b60 = hashlib.sha256((d / "V3_0_60_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_61_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    if not b60.startswith(V60_SHA):
        raise SystemExit(f"V3_0_60 {b60[:8]} is not the T-423 r3 run {V60_SHA}")
    run = json.loads((d / "V3_0_61_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_60", b60[:8], "lines", ident["base_lines"], "-> V3_0_61_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_61_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "plaster_height", "diff",
                                                          "restated")}, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_61_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["room"], r["line_id"], r["item_code"], r.get("element_id"), "|", _q(r["before_base"]), "->",
              _q(r["after_v3_0_61"]), "|", " -> ".join(r["class"]), "| paint", r["paint_line_id"])
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
