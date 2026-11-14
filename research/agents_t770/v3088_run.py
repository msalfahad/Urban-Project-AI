"""T-770 r11 read-only run: ARCH_TAKEOFF_V3.0.88 (FILL_WIRE_V7 unchanged, R-T770-1 .. -8) on the candidate V3.0.87 (T-770 r10).
Exactly research/agents_t770/v3087_run.py (its chain and asserts unchanged), with --method ARCH_TAKEOFF_V3.0.88 and
--v3088-inputs (the committed research/agents_t770/V3088_PACKAGE.json, built by v3088_index.py) added to the one hub
call:

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3088_run.py <plan.dxf> <structural.dxf> \
        --out <private>/t770 --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3088_run.py --check-dir <the hub output dir>

The line check is v3081_run.check (T-479 classification + the Checker downgrades the committed index records APPLIED;
the one named re-binding downgrade of r3 stays a named finding) run eight times: V3_0_81 .. V3_0_88 BOQ lines against the committed
LINE_INDEX_V3_0_81 .. _87 (the bases are the runs of record) / _88.
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
INDEX84 = HERE / "out/LINE_INDEX_V3_0_84.json"
INDEX85 = HERE / "out/LINE_INDEX_V3_0_85.json"
INDEX86 = HERE / "out/LINE_INDEX_V3_0_86.json"
INDEX87 = HERE / "out/LINE_INDEX_V3_0_87.json"
INDEX88 = HERE / "out/LINE_INDEX_V3_0_88.json"
PACKAGE81 = HERE / "V3081_PACKAGE.json"
PACKAGE82 = HERE / "V3082_PACKAGE.json"
PACKAGE83 = HERE / "V3083_PACKAGE.json"
PACKAGE84 = HERE / "V3084_PACKAGE.json"
PACKAGE85 = HERE / "V3085_PACKAGE.json"
PACKAGE86 = HERE / "V3086_PACKAGE.json"
PACKAGE87 = HERE / "V3087_PACKAGE.json"
PACKAGE88 = HERE / "V3088_PACKAGE.json"


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
        args[i + 1] = "ARCH_TAKEOFF_V3.0.88"
        seen["out"] = Path(args[args.index("--out") + 1])
        return real(args + ["--v3081-inputs", str(PACKAGE81), "--v3082-inputs", str(PACKAGE82),
                           "--v3083-inputs", str(PACKAGE83), "--v3084-inputs", str(PACKAGE84), "--v3085-inputs", str(PACKAGE85),
                           "--v3086-inputs", str(PACKAGE86), "--v3087-inputs", str(PACKAGE87), "--v3088-inputs", str(PACKAGE88)])
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
    lines84 = json.loads((d / "V3_0_84_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines85 = json.loads((d / "V3_0_85_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines86 = json.loads((d / "V3_0_86_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines87 = json.loads((d / "V3_0_87_BOQ_LINES.json").read_text(encoding="utf-8"))
    lines88 = json.loads((d / "V3_0_88_BOQ_LINES.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_88_RUN.json").read_text(encoding="utf-8"))
    bad81, _r = R81.check(lines81, json.loads(INDEX81.read_text(encoding="utf-8")))
    bad82, _r = R81.check(lines82, json.loads(INDEX82.read_text(encoding="utf-8")))
    bad83, _r = R81.check(lines83, json.loads(INDEX83.read_text(encoding="utf-8")))
    bad84, _r = R81.check(lines84, json.loads(INDEX84.read_text(encoding="utf-8")))
    bad85, _r = R81.check(lines85, json.loads(INDEX85.read_text(encoding="utf-8")))
    bad86, _r = R81.check(lines86, json.loads(INDEX86.read_text(encoding="utf-8")))
    bad87, _r = R81.check(lines87, json.loads(INDEX87.read_text(encoding="utf-8")))
    bad88, rebind = R81.check(lines88, json.loads(INDEX88.read_text(encoding="utf-8")))
    for r in rebind:
        print("FINDING (Checker's call, carried from r3):", json.dumps(r, sort_keys=True))
    print("V3_0_81 lines", len(lines81), "-> V3_0_82 lines", len(lines82), "-> V3_0_83 lines", len(lines83),
          "-> V3_0_84 lines", len(lines84), "-> V3_0_85 lines", len(lines85), "-> V3_0_86 lines", len(lines86),
          "-> V3_0_87 lines", len(lines87), "-> V3_0_88 lines", len(lines88), "| identity",
          json.dumps(run["identity"], sort_keys=True))
    for name, bad in (("V3_0_81_BOQ_LINES.json", bad81), ("V3_0_82_BOQ_LINES.json", bad82),
                      ("V3_0_83_BOQ_LINES.json", bad83), ("V3_0_84_BOQ_LINES.json", bad84),
                      ("V3_0_85_BOQ_LINES.json", bad85), ("V3_0_86_BOQ_LINES.json", bad86),
                      ("V3_0_87_BOQ_LINES.json", bad87), ("V3_0_88_BOQ_LINES.json", bad88)):
        print(name, hashlib.sha256((d / name).read_bytes()).hexdigest()[:8],
              "| lines disagreeing with the committed index:", len(bad), bad[:5])
    return 1 if (bad81 or bad82 or bad83 or bad84 or bad85 or bad86 or bad87 or bad88) else 0


if __name__ == "__main__":
    sys.exit(main())
