"""T-781: the unchanged geometry run (tools/urban_boq_m9.py arch, ARCH_TAKEOFF_V2.13, plan drawing only) whose
ARCH_OPENINGS.json feeds the opening table. Read-only: every output goes to --out (outside the repository).

    bash scripts/agent_env.sh run --tree task-T-781 research/agents_t781/geometry_t781.py <plan.dxf> --out <private dir>
"""
from __future__ import annotations

import argparse
import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", default="ARCH_TAKEOFF_V2.13")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M9
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M9.main(["arch", "--drawings", a.plan, "--out", a.out, "--method", a.method, "--project", "T781",
                      "--no-svg"])
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "M9_STDOUT.txt").write_text(buf.getvalue(), encoding="utf-8")
    print("rc", rc, "ARCH_OPENINGS.json", (Path(a.out) / "ARCH_OPENINGS.json").is_file())
    return rc


if __name__ == "__main__":
    sys.exit(main())
