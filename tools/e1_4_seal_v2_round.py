"""E1.4 §17 — seal the inputs a new cold V2 round is allowed to see.

    python -m tools.e1_4_seal_v2_round --out <run dir> --sandbox <dir>

A cold round is only cold if what reached the reader is recorded. This
builds one folder per candidate holding exactly four things - the
overlay, the brief, the legend, and that candidate's own frozen
source-only observation - and writes a seal naming every file with its
hash, and naming what was deliberately kept out.

The E1.3 Round 2 answers are not here. Neither is the E1.3 proposal, any
benchmark quantity, any expected geometry, any known area, or any
statement of what this run would like the answer to be.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from engine import export_provenance as prov
from engine import visual_challenger_v2 as vc

WHAT_THIS_SANDBOX_CONTAINS = (
    "for each candidate: one overlay image, the V2 brief, the legend for "
    "that overlay, and that candidate's own frozen source-only "
    "observation. Nothing else")

WHAT_IT_DOES_NOT_CONTAIN = (
    "the E1.3 Round 2 answers",
    "the E1.3 proposal, or any E1.3 register",
    "any benchmark quantity",
    "any expected geometry",
    "any known area",
    "any statement of what this run would like the answer to be",
    "any CAD coordinate",
)

WHY_THE_EARLIER_OBSERVATION_IS_ALLOWED = (
    "the two-stage challenge shows a reader its OWN earlier observation "
    "of the same crop, taken before anything was proposed. That is the "
    "design: it is what makes the second stage a comparison rather than a "
    "first impression. Every V1 crop in this run came back byte for byte "
    "identical to the one that observation was made of, so it is an "
    "observation of this picture and not of another")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sandbox", required=True)
    a = ap.parse_args(argv)

    run = Path(a.out)
    box = Path(a.sandbox)
    if box.exists():
        shutil.rmtree(box)
    box.mkdir(parents=True)

    v2 = json.loads((run / "E1_4_VISUAL_V2_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v1 = json.loads((run / "E1_4_VISUAL_V1_REGISTER.json")
                    .read_text(encoding="utf-8"))
    v1_by = {c["candidate_id"]: c for c in v1["CROPS"]}

    rows, missing = [], []
    for t in v2["task_manifests"]:
        cid = t["CANDIDATE_ID"]
        src = run / t["OVERLAY_PATH_IN_THE_RUN"]
        if not src.exists():
            missing.append({"candidate_id": cid, "path": str(src)})
            continue
        identity = next((i.get("value") for i in t.get("inputs", ())
                         if i.get("kind") == "IDENTITY_TEXT_ONLY"), None)
        d = box / cid
        d.mkdir()
        shutil.copy(src, d / "OVERLAY.png")
        (d / "BRIEF.txt").write_text(
            f"CANDIDATE: {cid}\nTHE LABEL DRAWN IN THIS AREA: {identity}\n\n"
            + vc.V2_BRIEF + "\n\nLEGEND FOR THE OVERLAY\n"
            + "\n".join("  " + x for x in t["OVERLAY_LEGEND"]) + "\n",
            encoding="utf-8")
        ans = v1_by.get(cid, {}).get("FROZEN_E1_3_V1_ANSWER") or {}
        (d / "YOUR_EARLIER_OBSERVATION.json").write_text(
            json.dumps({k: v for k, v in ans.items()
                        if k not in ("ANSWER_SHA256", "source_file")},
                       indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        rows.append({
            "candidate_id": cid,
            "identity": identity,
            "THE_PROPOSAL_CHANGED_SINCE_E1_3":
                t.get("THE_PROPOSAL_CHANGED_SINCE_E1_3"),
            "THIS_IS_A_PROPOSED_BOUNDARY":
                t.get("THIS_IS_A_PROPOSED_BOUNDARY"),
            "OVERLAY_SHA256": prov.raw_sha256(d / "OVERLAY.png"),
            "BRIEF_SHA256": prov.raw_sha256(d / "BRIEF.txt"),
            "EARLIER_OBSERVATION_SHA256": prov.raw_sha256(
                d / "YOUR_EARLIER_OBSERVATION.json"),
            "THE_EARLIER_OBSERVATION_IS_PRESENT": bool(ans),
        })

    seal = {
        "WHAT_THIS_SANDBOX_CONTAINS": WHAT_THIS_SANDBOX_CONTAINS,
        "WHAT_IT_DOES_NOT_CONTAIN": list(WHAT_IT_DOES_NOT_CONTAIN),
        "why_the_earlier_observation_is_allowed":
            WHY_THE_EARLIER_OBSERVATION_IS_ALLOWED,
        "the_challenger_may_not_move_a_coordinate":
            vc.THE_CHALLENGER_MAY_NOT_MOVE_A_COORDINATE,
        "CANDIDATES": rows,
        "candidates_sealed": len(rows),
        "OVERLAYS_NOT_FOUND": missing,
    }
    (box / "SEAL.json").write_text(
        json.dumps(seal, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"sealed": len(rows), "missing": len(missing),
                      "sandbox": str(box)}, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
