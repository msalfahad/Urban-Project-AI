"""T-687 read-only run: ARCH_TAKEOFF_V3.0.69 (FINISH_GATE_B_V1, R-T687-1) on the candidate V3.0.68 (T-672, Gate B
PASS). Exactly research/agents_t672/v3068_run.py (its inputs unchanged; it runs the whole chain and asserts V3_0_67 =
a29a11a9), with --method ARCH_TAKEOFF_V3.0.69 and --v3069-inputs (t687_inputs.py: the merged T-676 / T-680 / T-686 /
T-690 ledgers, sha-pinned) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-687 research/agents_t687/v3069_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t687 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

V3_0_68 of this run must be the T-672 run of record d1de50cb (asserted). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t682", ROOT / "research" / "agents_t677", ROOT / "research" / "agents_t672",
          HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3068_run as R68  # noqa: E402  (T-672; imports T-682's v3067_run and the whole chain)
import t687_inputs as L69  # noqa: E402

V68_SHA = "d1de50cb"             # V3_0_68_BOQ_LINES.json, T-672 run of record (Gate B PASS)


def main(argv=None):
    from tools import urban_boq_m9 as M
    seen = {}
    real = M.main

    def hub(args):
        """the one hub call of T-672 v3068_run, re-pointed at V3.0.69 (same inputs + --v3069-inputs)."""
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.68", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.69"
        o = Path(args[args.index("--out") + 1])
        f = o.parent / "v3069_inputs.json"
        f.write_text(json.dumps(L69.build(), ensure_ascii=False, indent=1), encoding="utf-8")
        seen["out"] = o
        return real(args + ["--v3069-inputs", str(f)])
    M.main = hub
    try:
        R68.main(argv)        # its own wrapper re-points V3.0.67 -> .68 and calls this one (its asserts run)
    finally:
        M.main = real
    d = seen["out"]
    b68 = hashlib.sha256((d / "V3_0_68_BOQ_LINES.json").read_bytes()).hexdigest()
    new = hashlib.sha256((d / "V3_0_69_BOQ_LINES.json").read_bytes()).hexdigest()
    if not b68.startswith(V68_SHA):
        raise SystemExit(f"V3_0_68 {b68[:8]} is not the T-672 run of record {V68_SHA}")
    run = json.loads((d / "V3_0_69_RUN.json").read_text(encoding="utf-8"))
    ident = run["identity"]
    print("base: V3_0_68", b68[:8], "lines", ident["base_lines"], "-> V3_0_69_BOQ_LINES.json", new[:8], "lines",
          ident["v3_0_69_lines"])
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows", "finishes",
                                                          "outside_rows_identical_to_base", "diff")}, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    for r in json.loads((d / "V3_0_69_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))["rows"]:
        print("row", r["piece"], r["action"], r["line_id"], r["item_code"], r["element_id"], "|",
              _q(r["before_base"]), "->", _q(r["after_v3_0_69"]), "|", " -> ".join(str(x) for x in r["class"]), "|",
              r["evidence_status"])
    return 0


def _q(q):
    from engine.source import arch_v302 as A302
    return A302._q(q) if q and (q.get("value") is not None or q.get("low") is not None) else "blank"


if __name__ == "__main__":
    main()
