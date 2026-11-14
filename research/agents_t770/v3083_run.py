"""T-770 r6 read-only run: ARCH_TAKEOFF_V3.0.83 (FILL_WIRE_V3, R-T770-1 .. -4) on the candidate V3.0.82 (T-770 r5).
Exactly research/agents_t770/v3082_run.py (its chain and asserts unchanged), with --method ARCH_TAKEOFF_V3.0.83 and
--v3083-inputs (the committed research/agents_t770/V3083_PACKAGE.json, built by v3083_index.py) added to the one hub
call:

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3083_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t770 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3083_run.py --check-dir <the hub output dir>

The line check is v3081_run.check (T-479 classification + the Checker downgrades the committed index records APPLIED;
the one named re-binding downgrade of r3 stays a named finding) run three times: V3_0_81 / V3_0_82 / V3_0_83 BOQ lines against the committed
LINE_INDEX_V3_0_81 / _82 (the bases are the runs of record) / _83.
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
INDEX83 = HERE / "out/LINE_INDEX_V3_0_83.json"
PACKAGE81 = HERE / "V3081_PACKAGE.json"
PACKAGE82 = HERE / "V3082_PACKAGE.json"
PACKAGE83 = HERE / "V3083_PACKAGE.json"


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
        args[i + 1] = "ARCH_TAKEOFF_V3.0.83"
        seen["out"] = Path(args[args.index("--out") + 1])
        return real(args + ["--v3081-inputs", str(PACKAGE81), "--v3082-inputs", str(PACKAGE82),
                           "--v3083-inputs", str(PACKAGE83)])
    M.main = hub
    try:
        R81.R79.main(argv)        # T-314's wrapper re-points .78 -> .79 and calls this one (its asserts run)
    finally:
        M.main = real
    return _report(seen["out"])


def _report(d):
    lines81 = json.loads((d / "V3_0_81_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines82 = json.loads((d / "V3_0_82_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines83 = json.loads((d / "V3_0_83_BOQ_LINES.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_83_RUN.json").read_text(encoding="utf-8"))
    bad81, _r = R81.check(lines81, json.loads(INDEX81.read_text(encoding="utf-8")))
    bad82, _r = R81.check(lines82, json.loads(INDEX82.read_text(encoding="utf-8")))
    bad83, rebind = R81.check(lines83, json.loads(INDEX83.read_text(encoding="utf-8")))
    for r in rebind:
        print("FINDING (Checker's call, carried from r3):", json.dumps(r, sort_keys=True))
    print("V3_0_81 lines", len(lines81), "-> V3_0_82 lines", len(lines82), "-> V3_0_83 lines", len(lines83), "| identity",
          json.dumps(run["identity"], sort_keys=True))
    for name, bad in (("V3_0_81_BOQ_LINES.json", bad81), ("V3_0_82_BOQ_LINES.json", bad82),
                      ("V3_0_83_BOQ_LINES.json", bad83)):
        print(name, hashlib.sha256((d / name).read_bytes()).hexdigest()[:8],
              "| lines disagreeing with the committed index:", len(bad), bad[:5])
    return 1 if (bad81 or bad82 or bad83) else 0


if __name__ == "__main__":
    sys.exit(main())
