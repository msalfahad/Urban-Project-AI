"""T-770 r7: register rules/coverage/BOQ_FAMILY_MASTER_1.84.0.json in rules/RULES_MANIFEST.json with the manifest tool
(tools/m9_rules_manifest.build, unchanged; run again after the in-merge --promote rewrite; T-507 / T-637 / T-525 / T-651 precedent: no hand digest). Refuses when any copy, export or
store file had drifted before the rebuild.

    bash scripts/agent_env.sh run --tree <tree> research/agents_t770/write_manifest_1_84_0.py   (the T-314 tool, pointed at 1.84.0)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import m9_rules_manifest as M  # noqa: E402

REL = "coverage/BOQ_FAMILY_MASTER_1.84.0.json"


def main():
    if REL not in M.AUTHORED:
        raise SystemExit(f"{REL} is not in tools/m9_rules_manifest.AUTHORED")
    before = [p for p in M.check() if REL not in str(p)]
    if before:
        raise SystemExit(f"manifest drift before the rebuild (not this file): {before}")
    M.build()
    after = M.check()
    print("manifest rebuilt; problems:", after)
    return 0 if not after else 1


if __name__ == "__main__":
    sys.exit(main())
