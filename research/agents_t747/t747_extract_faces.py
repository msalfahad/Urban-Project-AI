"""T-747: extract the face rows of the QUEUED T-314 r2 stage (agents/task-T-314 @ 080ccaa5, not on the working branch)
into one small pinned input file: research/agents_t747/in/T314_FACES_T747.json.

The stage's own input builder (research/agents_t314/t314_inputs.py at 080ccaa5) is run unchanged on the 12 merged
sources it reads; every source must have the git blob id that T-737 pinned for the stage
(research/agents_t737/in/T314_STAGE_T737.json 'source_blobs'), so the faces are the stage's faces, not a re-reading.

Usage (from the checkout root of a task tree):
    mkdir -p <dir>/research/agents_t314
    git show 080ccaa5:research/agents_t314/t314_inputs.py > <dir>/research/agents_t314/t314_inputs.py
    python3 -I research/agents_t747/t747_extract_faces.py <dir>
The script copies the 12 sources from this tree into <dir> (blob ids asserted) and writes the JSON. Only face keys,
line keys, elements, levels, quantities and states are kept: no drawing content, no client data.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "in" / "T314_FACES_T747.json"
PIN = ROOT / "research" / "agents_t737" / "in" / "T314_STAGE_T737.json"
INPUTS_REL = "research/agents_t314/t314_inputs.py"


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def extract(d: Path) -> dict:
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    blobs = pin["source_blobs"]
    inputs_bytes = (d / INPUTS_REL).read_bytes()
    if git_blob_id(inputs_bytes) != pin["stage"]["inputs_blob"]:
        raise SystemExit("t314_inputs.py is not the stage's (blob id differs from the T-737 pin)")
    for rel, bid in blobs.items():
        src = ROOT / rel
        if git_blob_id(src.read_bytes()) != bid:
            raise SystemExit(f"source {rel} differs from the stage's blob {bid}: STALE_SOURCE, re-run T-737 first")
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, d / rel)
    spec = importlib.util.spec_from_file_location("t314_inputs_stage", d / INPUTS_REL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    b = mod.build()
    lines = [{k: ln.get(k) for k in ("key", "line_id", "element", "floor", "element_id", "why_held")}
             for ln in b["lines"]]
    faces = [{k: f.get(k) for k in ("face_id", "line", "element", "bottom", "top", "lo", "hi", "status")}
             for f in b["faces"]]
    ops = [{k: o.get(k) for k in ("opening_id", "face_id", "status", "hole_m2", "cap_m2", "sill", "head")}
           for o in b["openings"]]
    return {"schema": "URBAN_T747_STAGE_FACES_V1",
            "stage": {"branch": "agents/task-T-314", "commit": "080ccaa5", "inputs_blob": git_blob_id(inputs_bytes),
                      "pin": "research/agents_t737/in/T314_STAGE_T737.json"},
            "source_blobs": blobs, "lines": lines, "faces": faces, "openings": ops,
            "expect": b["expect"]}


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
