"""T-698: extract the two PENDING packages the wiring readiness depends on into one small, pinned input file.

The pending packages live on task branches that are not on the working branch (yet):
  - T-314 r2 stage (agents/task-T-314 @ 080ccaa5, base V3.0.61): research/agents_t314/out/summary_t314.json
  - T-687 Gate B round 1 (agents/task-T-687 @ a8cf49c8, base V3.0.68): research/agents_t687/summary_t687.json

Usage (paths are local copies of those blobs, e.g. `git show <ref>:<path> > file`):
    python3 -I research/agents_t698/t698_extract_pending.py <summary_t314.json> <summary_t687.json>
Writes research/agents_t698/in/PENDING_STAGES_T698.json: per package the git blob id (sha1 of 'blob <n>\\0' + bytes,
so anyone can re-check it with `git rev-parse <ref>:<path>`) and only the line identities and states this task maps
to (line id, key, element id, floor, item, before / after state and bounds). No drawing content, no client data.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "in" / "PENDING_STAGES_T698.json"
REFS = {
    "T-314": {"branch": "agents/task-T-314", "commit": "080ccaa5", "path": "research/agents_t314/out/summary_t314.json",
              "base": "ARCH_TAKEOFF_V3.0.61", "stage": "ARCH_TAKEOFF_V3.0.62 (stage, renumbered at claim)"},
    "T-687": {"branch": "agents/task-T-687", "commit": "a8cf49c8", "path": "research/agents_t687/summary_t687.json",
              "base": "ARCH_TAKEOFF_V3.0.68", "stage": "ARCH_TAKEOFF_V3.0.69 (integration package, Gate B pending)"},
}


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _bound(x):
    x = x or {}
    return {"state": x.get("state"), "value": x.get("value"), "low": x.get("low"), "high": x.get("high")}


def extract(p314: Path, p687: Path) -> dict:
    b314, b687 = p314.read_bytes(), p687.read_bytes()
    s314, s687 = json.loads(b314), json.loads(b687)
    rows314 = [{"action": r["action"], "line_id": r["line_id"], "line_key": r["line_key"], "element_id": r["element_id"],
                "floor": r["floor"], "element": r["element"], "evidence_status": r["evidence_status"],
                "before": _bound(r.get("before")), "after": _bound(r.get("after")), "net": r.get("net")}
               for r in s314["rows"]]
    rows687 = [{"action": r["action"], "change": r["change"], "line_id": r["line_id"], "element_id": r["element_id"],
                "item_code": r["item_code"], "unit": r["unit"], "evidence_status": r["evidence_status"],
                "before": _bound(r.get("before")), "after": _bound(r.get("after"))}
               for r in s687["rows"]]
    return {
        "schema": "URBAN_T698_PENDING_STAGES_V1",
        "T-314": dict(REFS["T-314"], blob=git_blob_id(b314), base_short=s314.get("base_v3_0_61"),
                      stage_short=s314.get("v3_0_62"), identity=s314["identity"], rows=rows314,
                      missing_items=s314["log"]["missing_items"], totals_moved=s314["totals_moved"]),
        "T-687": dict(REFS["T-687"], blob=git_blob_id(b687), identity=s687["identity"], rows=rows687),
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit(__doc__)
    d = extract(Path(argv[1]), Path(argv[2]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: (v["blob"][:12], len(v["rows"])) for k, v in d.items() if k != "schema"}))


if __name__ == "__main__":
    main(sys.argv)
