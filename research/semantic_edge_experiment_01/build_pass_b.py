"""Assemble the Pass B sandbox, after Pass A is frozen and not before.

Pass B shows a reader the same picture, its own frozen Pass A reading, and
what the deterministic CAD classifier says about the same members. It asks
one question: does the deterministic classification agree with what is
visibly there?

It cannot run until PASS_A_FEATURE_ASSERTIONS.json exists, because a
reader shown a deterministic answer first finds reasons it is right.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.semantic_edge_experiment_01 import a19 as A19
from research.semantic_edge_experiment_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
A19_DIR = OUT / "a19"


def write(path: Path, body) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (body if isinstance(body, str)
            else json.dumps(body, indent=2, ensure_ascii=False,
                            default=str) + "\n")
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    a_path = A19_DIR / "PASS_A_FEATURE_ASSERTIONS.json"
    if not a_path.exists():
        raise SystemExit("Pass A is not frozen yet; Pass B may not be built")
    frozen = json.loads(a_path.read_text(encoding="utf-8"))
    by_gid = {r["FEATURE_GROUP_ID"]: r for r in frozen["ANSWERS"]}
    base = {g["FEATURE_GROUP_ID"]: g for g in json.loads(
        (OUT / "04_E1_4_BASELINE.json").read_text(encoding="utf-8"))["GROUPS"]}

    box = A19_DIR / "pass_b_sandbox"
    if box.exists():
        shutil.rmtree(box)
    rows = []
    for gid, ans in by_gid.items():
        src = A19_DIR / "pass_a_sandbox" / gid
        d = box / gid
        d.mkdir(parents=True)
        for png in sorted(src.glob("*.png")):
            shutil.copy(png, d / png.name)
        shutil.copy(src / "TASK.json", d / "TASK.json")
        shutil.copy(src / "FLOOR_CONTEXT.txt", d / "FLOOR_CONTEXT.txt")
        write(d / "BRIEF.txt", A19.PASS_B_BRIEF)
        write(d / "YOUR_FROZEN_PASS_A_READING.json",
              {k: v for k, v in ans.items()
               if k not in ("ANSWER_SHA256", "source_file")})
        write(d / "WHAT_THE_DETERMINISTIC_CLASSIFIER_SAYS.json", {
            "FEATURE_GROUP_ID": gid,
            "WHAT_THIS_IS": (
                "the deterministic CAD classifier's current reading of the "
                "same marked members. It is not a correct answer and it is "
                "not a target. It is the thing you are being asked to "
                "compare against the picture"),
            "MEMBERS": (base.get(gid) or {}).get("MEMBERS", []),
        })
        write(d / "ANSWER_SCHEMA.json", A19.PASS_B_SCHEMA)
        rows.append({
            "FEATURE_GROUP_ID": gid,
            "PASS_A_READING_SHA256": hashlib.sha256(
                (d / "YOUR_FROZEN_PASS_A_READING.json").read_bytes()
            ).hexdigest(),
            "DETERMINISTIC_READING_SHA256": hashlib.sha256(
                (d / "WHAT_THE_DETERMINISTIC_CLASSIFIER_SAYS.json")
                .read_bytes()).hexdigest(),
            "BRIEF_SHA256": hashlib.sha256(
                (d / "BRIEF.txt").read_bytes()).hexdigest(),
        })

    h = write(A19_DIR / "PASS_B_INPUT_MANIFEST.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PASS": P.PASS_B,
        "PROTOCOL_HASH": P.protocol_hash(),
        "A19_BRIEF_HASH": A19.brief_hash(),
        "PASS_A_FEATURE_ASSERTIONS_SHA256": hashlib.sha256(
            a_path.read_bytes()).hexdigest(),
        "pass_a_is_frozen_before_pass_b_exists":
            P.PASS_A_IS_FROZEN_BEFORE_PASS_B_EXISTS,
        "WHAT_THE_SANDBOX_CONTAINS": (
            "the same crops, the same marked-member table, the reader's "
            "own frozen Pass A reading, and what the deterministic "
            "classifier says about those members"),
        "WHAT_IT_STILL_DOES_NOT_CONTAIN": [
            "any benchmark, expected area or known quantity",
            "any corrected polygon or target geometry",
            "any other reader's answer",
        ],
        "tasks": len(rows),
        "TASKS": rows,
    })
    print(json.dumps({"tasks": len(rows),
                      "PASS_B_INPUT_MANIFEST_SHA256": h}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
