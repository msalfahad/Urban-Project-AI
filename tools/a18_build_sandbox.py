"""Assemble a cold agent's sandbox from a plan, and verify it before launch.

    python -m tools.a18_build_sandbox --plan <plan>.json --root <sandbox dir> \
        --manifest <input manifest>.json

The plan names inputs. The contract decides which of them may exist. The
sandbox is written only through engine.agent_sandbox, so a refused input
cannot be placed at all, and the last thing this tool does is require

    SANDBOX_CONTENTS == ADMITTED_INPUT_MANIFEST

byte for byte. It exits non-zero and prints the mismatch rather than
launching anything, because a sandbox that has not been checked is not
ready however complete it looks.

A plan entry is either a file on disk (`path`) or a projection read from
JSON (`content_file`). Declared `working_dirs` are created empty for the
agent, and must still be empty when the check runs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import agent_sandbox as sbx
from engine import blind_input_contract as bic

FIELDS = ("input_id", "kind", "what_it_is", "derived_from", "crop_basis",
          "origin", "supplied_by", "media_type")


def build(plan_path, root, *, manifest_path="") -> dict:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    run = bic.BlindRun(run_id=plan.get("run_id", ""),
                       pass_id=plan.get("pass_id", "A18"),
                       subject=plan.get("subject", ""),
                       floor=plan.get("floor", ""))
    for key, value in (plan.get("notes") or {}).items():
        run.notes[key] = value
    box = sbx.Sandbox(root=Path(root), run=run,
                      working_dirs=tuple(plan.get("working_dirs", ())))

    placed, refused = 0, []
    for entry in plan["inputs"]:
        kwargs = {k: entry[k] for k in FIELDS if k in entry}
        if "crop_box_px" in entry:
            kwargs["crop_box_px"] = tuple(entry["crop_box_px"])
        if entry.get("content_file"):
            kwargs["content"] = json.loads(
                Path(entry["content_file"]).read_text(encoding="utf-8"))
        elif entry.get("path"):
            kwargs["path"] = entry["path"]
        try:
            box.place(bic.Input(**kwargs), at=entry["at"])
            placed += 1
        except sbx.RefusedInput as exc:
            refused.append({"at": entry["at"], "why": str(exc)})

    report = box.verify()
    man = box.manifest()
    man["plan"] = {"file": str(plan_path),
                   "inputs_in_the_plan": len(plan["inputs"]),
                   "placed": placed,
                   "refused_and_not_placed": refused}
    if manifest_path:
        Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
        Path(manifest_path).write_text(
            json.dumps(man, indent=2, ensure_ascii=False, default=str)
            + "\n", encoding="utf-8")
    return {"box": box, "report": report, "manifest": man,
            "refused": refused}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--manifest", default="")
    a = ap.parse_args(argv)
    out = build(a.plan, a.root, manifest_path=a.manifest)
    report, box = out["report"], out["box"]
    print(json.dumps({
        "status": report["status"],
        "admitted_files": report["admitted_files"],
        "files_on_disk": report["files_on_disk"],
        "refused_and_not_placed": [r["at"] for r in out["refused"]],
        "problems": report["problems"][:6],
        "SANDBOX_HASH": report["SANDBOX_HASH"][:16],
    }, indent=2, ensure_ascii=False))
    if report["status"] != sbx.EQUAL:
        print("NOT READY: " + sbx.A_GATE_YOU_CAN_WALK_AROUND)
        return 1
    print("LAUNCH_TOKEN " + box.launch_token()[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
