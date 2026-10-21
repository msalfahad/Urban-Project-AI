"""T-060 read-only run: the frozen route-G concrete ledger vs CONCRETE_LEDGER_V2 on one finished engine run.

    python3 -I research/agents_t060/run_v2.py --run RUN --structural ST.dxf --conventions CONV.json --out RUN_V2
        [--member-types TYPES.json]

RUN is the output folder of `tools/urban_boq_m9.py arch ... --structural ST.dxf --conventions CONV.json` (the frozen
run). This script recomputes route G on the same structural drawing in-process (tools/urban_boq_m2.compute, frozen,
completeness on), checks that its canonical structural lines are exactly the frozen run's structural lines, then
writes RUN_V2 = the same BOQ lines with the structural lines rebuilt from concrete_ledger_v2.apply (superseded frozen
items replaced, every other line byte-identical), the frozen BOQ_RELEASE_REPORT.json copied unchanged, and
V2_LEDGER.json (re-measured findings, strip census, line diff). Score both folders with tools/alsenan_keymap.py.
Writes only under --out. Names no project, sheet or layer of its own.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import boq_line as BL                 # noqa: E402
from engine.source import concrete_ledger_v2 as V2       # noqa: E402
from tools import urban_boq_m2 as M2                     # noqa: E402
from tools import urban_boq_m9 as M9                     # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--structural", required=True)
    ap.add_argument("--conventions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--member-types")
    a = ap.parse_args(argv)
    run, out = Path(a.run), Path(a.out)
    lines = json.loads((run / "BOQ_LINES.json").read_text(encoding="utf-8"))
    R = M2.compute([a.structural], conventions=a.conventions, route="G", completeness=True)
    frozen_s = M9.structural_lines(R)
    ids = {ln["line_id"] for ln in frozen_s}
    in_run = [ln for ln in lines if ln["line_id"] in ids]
    if len(in_run) != len(frozen_s):
        raise SystemExit(f"the in-process route G gives {len(frozen_s)} structural lines, the run holds {len(in_run)} "
                         "of them: not the same run")
    mt = json.loads(Path(a.member_types).read_text(encoding="utf-8")) if a.member_types else None
    v2 = V2.measure(R, member_types=mt)
    R2 = dict(R, items=V2.apply(R, v2))
    v2_s = M9.structural_lines(R2)
    by_old = {ln["line_id"] for ln in frozen_s}
    new_lines, placed = [], False
    for ln in lines:
        if ln["line_id"] in by_old:
            if not placed:
                new_lines.extend(v2_s)
                placed = True
            continue
        new_lines.append(ln)
    out.mkdir(parents=True, exist_ok=True)
    (out / "BOQ_LINES.json").write_text(BL.dumps(new_lines), encoding="utf-8")
    rel = run / "BOQ_RELEASE_REPORT.json"
    if rel.exists():
        shutil.copyfile(rel, out / "BOQ_RELEASE_REPORT.json")
    old_ids, new_ids = {ln["line_id"] for ln in frozen_s}, {ln["line_id"] for ln in v2_s}
    diff = {"removed": sorted({(ln["item_code"], ln["location"].get("element_id"), ln.get("measured_net"))
                               for ln in frozen_s if ln["line_id"] not in new_ids}, key=str),
            "added": sorted({(ln["item_code"], ln["location"].get("element_id"), ln["evidence_state"],
                              ln.get("measured_net")) for ln in v2_s if ln["line_id"] not in old_ids}, key=str),
            "unchanged_structural_lines": len(old_ids & new_ids), "lines_frozen": len(lines),
            "lines_v2": len(new_lines)}
    (out / "V2_LEDGER.json").write_text(json.dumps({"method": V2.METHOD, "findings": v2["findings"],
                                                    "census": v2["census"], "supersedes": v2["supersedes"],
                                                    "line_diff": diff}, indent=1, default=str), encoding="utf-8")
    print(json.dumps(diff, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
