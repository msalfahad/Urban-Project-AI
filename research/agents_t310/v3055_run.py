"""T-310 r6 read-only run: ARCH_TAKEOFF_V3.0.55 (the WET-AREA / POOL WATERPROOFING package, R-T310-1) on the candidate
of record V3.0.54 (T-480, merge 1b66b719). Exactly research/agents_t480/v3054_run.py (its inputs unchanged; it runs
research/agents_t487/v3053_run.py, which asserts V3_0_51 = c0b6d664, and asserts V3_0_53 = 36863f6c), with --method
ARCH_TAKEOFF_V3.0.55 and --v3055-inputs (t310_inputs.py: the merged T-303 / T-309 / T-286 pieces, sha-pinned) added to
the one hub call:

    .work/venv/bin/python -I research/agents_t310/v3055_run.py <plan.dxf> <structural.dxf> --out <private>/t310 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

The V3_0_54_BOQ_LINES.json of this run must be the candidate of record c85c4630 (asserted). Every output goes to --out
(outside the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

History: r4 ran the same package as ARCH_TAKEOFF_V3.0.52 on V3.0.51 (c0b6d664 -> 2a51ae59, research/agents_t310/
v3052_run.py, replaced by this file in r6: T-487 took V3.0.53 and T-480 V3.0.54 meanwhile; merge-order rule: the
package READY later rebases and renumbers).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t480", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3054_run as R54  # noqa: E402  (puts every earlier inputs builder on sys.path)
import t310_inputs as L55  # noqa: E402

BASE_SHA = "c85c4630"            # V3_0_54_BOQ_LINES.json, candidate of record (T-480 Gate B, merge 1b66b719)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of v3054_run, re-pointed at V3.0.55 (same inputs + --v3055-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.54", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.55"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3055_inputs.json"
        f.write_text(json.dumps(L55.build(R54.R53.R51.R50.R48.T131.PID), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3055-inputs", str(f)])
    M.main = hub
    try:
        R54.main(argv)
    finally:
        M.main = real
    d = seen["out"]
    base = hashlib.sha256((d / "V3_0_54_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_55_BOQ_LINES.json").read_bytes()).hexdigest()
    if not base.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {base[:8]} is not {BASE_SHA} (not the candidate of record)")
    run = json.loads((d / "V3_0_55_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_54", base[:8], "lines", ident["base_lines"], "-> V3_0_55_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_55_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "wet_area_wp", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    # T-310 bindings, asserted on the candidate of record: each duplicate transition line carries the closure the
    # Checker named; each missing door's candidate opening has a doorway line and no transition line
    lb = {ln["line_id"]: ln for ln in json.loads((d / "V3_0_54_BOQ_LINES.json").read_text(encoding="utf-8"))}
    for lid, (door, closure) in L55.DUPLICATES.items():
        if closure not in json.dumps(lb[lid]["location"]):
            raise SystemExit(f"{lid}: closure {closure} of door {door} not in its location (stale binding)")
    for door, (floor, op, dwl) in L55.MISSING_DOORS.items():   # opening ids are per floor
        dw = lb[dwl]
        codes = {ln["item_code"] for ln in lb.values() if ln["location"].get("floor") == floor
                 and ln["location"].get("room_id") == dw["location"]["room_id"]
                 and str(ln["location"].get("element_id") or "").endswith(f" {op}")}
        if dw["item_code"] != "FIN.WP.DOORWAY" or dw["location"].get("floor") != floor or \
                not str(dw["location"]["element_id"]).endswith(f" {op}") or "FIN.WP.DOORWAY_TRANSITION" in codes:
            raise SystemExit(f"door {door} ({floor} {op}): doorway / transition lines {sorted(codes)} (stale binding)")
    for r in json.loads((d / "V3_0_55_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["action"], r["line_id"], r["item_code"], r.get("room_id"), r.get("element_id"), "|",
              _q(r["before_base"]), "->", _q(r["after_v3_0_55"]))
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q else ""


if __name__ == "__main__":
    main()
