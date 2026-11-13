"""T-737: extract the QUEUED T-314 r2 stage (agents/task-T-314 @ 080ccaa5, not on the working branch) into one small
pinned input file: research/agents_t737/in/T314_STAGE_T737.json.

Usage: copy the stage blobs with `git show 080ccaa5:<path> > <dir>/<path>` for the summary, the inputs script and the
merged sources it lists, then
    python3 -I research/agents_t737/t737_extract_stage.py <dir>
Each file is pinned by its git blob id (sha1 of 'blob <n>\\0' + bytes): anyone re-checks it with
`git rev-parse 080ccaa5:<path>`. Only line identities, states and quantities are kept; no drawing content, no client
data.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from t737_rules import git_blob_id  # noqa: E402

OUT = HERE / "in" / "T314_STAGE_T737.json"
STAGE = {"branch": "agents/task-T-314", "commit": "080ccaa5", "base": "ARCH_TAKEOFF_V3.0.61",
         "stage": "ARCH_TAKEOFF_V3.0.62 (stage; renumbered at claim)"}
SUMMARY = "research/agents_t314/out/summary_t314.json"
INPUTS = "research/agents_t314/t314_inputs.py"
SOURCES = [  # = t314_inputs.SOURCES (stage) + the two FILL tables it reads beside them
    "research/agents_t305/FACE_LINE_LEDGER_T305.csv", "research/agents_t311/PARAPET_RUN_LEDGER_T311.csv",
    "research/agents_t324/T-324_PARAPET_COMPONENTS.md", "research/agents_t337/BINDING_T337.csv",
    "research/agents_t337/OPENINGS_T337.csv", "research/agents_t337/ITEMS_T337.csv",
    "research/agents_t337/FILL_T314_T337.csv", "research/agents_t337/FILL_ITEMS_T314_T337.csv",
    "research/agents_t349/CLOSURE_T349.csv", "research/agents_t348/FILL_T314_T348.csv",
    "research/agents_t348/FACES_T348.csv", "research/agents_t567/out/FACES_T567.csv",
]


def _b(x):
    x = x or {}
    return {k: x.get(k) for k in ("state", "value", "low", "high")}


def extract(d: Path) -> dict:
    raw = (d / SUMMARY).read_bytes()
    s = json.loads(raw)
    rows = [{"action": r["action"], "line_id": r.get("line_id"), "line_key": r["line_key"],
             "element_id": r["element_id"], "floor": r["floor"], "element": r["element"],
             "evidence_status": r["evidence_status"], "faces": r.get("faces"), "openings": r.get("openings"),
             "before": _b(r.get("before")), "after": _b(r.get("after")), "net": r.get("net"),
             "gross": r.get("gross")} for r in s["rows"]]
    return {"schema": "URBAN_T737_STAGE_V1", "stage": dict(STAGE, summary_blob=git_blob_id(raw),
                                                           inputs_blob=git_blob_id((d / INPUTS).read_bytes()),
                                                           base_short=s.get("base_v3_0_61"),
                                                           stage_short=s.get("v3_0_62")),
            "identity": s["identity"], "rows": rows, "missing_items": s["log"]["missing_items"],
            "totals_moved": s["totals_moved"],
            "source_blobs": {p: git_blob_id((d / p).read_bytes()) for p in SOURCES}}


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(extract(Path(argv[1])), ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
