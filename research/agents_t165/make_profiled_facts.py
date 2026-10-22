"""T-165: writes (or --check-s) the facts file pinned by baselines/V29_ROUTEG_PROFILED.json: exactly the project facts the
V3.0.x runners give their V2.9 base (research/agents_t131/alsenan_v30_run.py facts(), plan file name P7757.dxf). Its
inputs are files already in this repository (sanitary reading T-010, exterior spaces T-071, the pantry's printed size
as a typed project data record, owner Q-17 A / Q-37 A). On ARCH_TAKEOFF_V2.9 this file changes no quantity and no
evidence state (T-165 report, finding F2): only the project id moves the line ids.

    python3 -I research/agents_t165/make_profiled_facts.py [--check]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t131"))

import alsenan_v30_run as T131  # noqa: E402

OUT = Path(__file__).resolve().parent / "baselines" / "v29_profiled_facts.json"


def main(argv=None):
    text = json.dumps(T131.facts("P7757.dxf"), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--check" in (argv if argv is not None else sys.argv[1:]):
        same = OUT.read_text(encoding="utf-8") == text
        print("facts file", "matches" if same else "DIFFERS from", "the T-131 facts()")
        return 0 if same else 1
    OUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
