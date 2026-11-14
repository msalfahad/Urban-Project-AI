"""T-770 r5 read-only run: ARCH_TAKEOFF_V3.0.82 (FILL_WIRE_V2, R-T770-1 / -2 / -3) on the candidate V3.0.81 (T-770 r4).
Exactly research/agents_t770/v3081_run.py (its chain and asserts unchanged: V3_0_78 = the T-738 run of record, V3_0_79 =
the T-314 run of record), with --method ARCH_TAKEOFF_V3.0.82 and --v3082-inputs (the committed
research/agents_t770/V3082_PACKAGE.json, built by v3082_index.py) added to the one hub call:

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3082_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t770 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3082_run.py --check-dir <the hub output dir>

The line check is v3081_run.check (T-479 classification + the Checker downgrades the committed index records APPLIED;
the one named re-binding downgrade of r3 stays a named finding) run twice: V3_0_81_BOQ_LINES against the committed
LINE_INDEX_V3_0_81 (the base is the run of record) and V3_0_82_BOQ_LINES against the committed LINE_INDEX_V3_0_82.
Every output goes to --out (outside the repository); printed: item codes, units, states, quantities and engine ids only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT / "research" / "agents_t314", HERE, ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v3081_run as R81  # noqa: E402  (T-770 r4; imports T-314's v3079_run and the whole chain)

INDEX81 = HERE / "out/LINE_INDEX_V3_0_81.json"
INDEX82 = HERE / "out/LINE_INDEX_V3_0_82.json"
PACKAGE81 = HERE / "V3081_PACKAGE.json"
PACKAGE82 = HERE / "V3082_PACKAGE.json"


def main(argv=None):
    from tools import urban_boq_m9 as M
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--check-dir"]:
        return _report(Path(argv[1]))
    seen = {}
    real = M.main

    def hub(args):
        args = list(args)
        i = args.index("--method")
        assert args[i + 1] == "ARCH_TAKEOFF_V3.0.79", args[i + 1]
        args[i + 1] = "ARCH_TAKEOFF_V3.0.82"
        seen["out"] = Path(args[args.index("--out") + 1])
        return real(args + ["--v3081-inputs", str(PACKAGE81), "--v3082-inputs", str(PACKAGE82)])
    M.main = hub
    try:
        R81.R79.main(argv)        # T-314's wrapper re-points .78 -> .79 and calls this one (its asserts run)
    finally:
        M.main = real
    return _report(seen["out"])


def _report(d):
    lines81 = json.loads((d / "V3_0_81_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines82 = json.loads((d / "V3_0_82_BOQ_LINES.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_82_RUN.json").read_text(encoding="utf-8"))
    bad81, _r = R81.check(lines81, json.loads(INDEX81.read_text(encoding="utf-8")))
    bad82, rebind = R81.check(lines82, json.loads(INDEX82.read_text(encoding="utf-8")))
    for r in rebind:
        print("FINDING (Checker's call, carried from r3):", json.dumps(r, sort_keys=True))
    print("base: V3_0_81 lines", len(lines81), "-> V3_0_82 lines", len(lines82), "| identity",
          json.dumps(run["identity"], sort_keys=True))
    for name, bad in (("V3_0_81_BOQ_LINES.json", bad81), ("V3_0_82_BOQ_LINES.json", bad82)):
        print(name, hashlib.sha256((d / name).read_bytes()).hexdigest()[:8],
              "| lines disagreeing with the committed index:", len(bad), bad[:5])
    return 1 if (bad81 or bad82) else 0


if __name__ == "__main__":
    sys.exit(main())
