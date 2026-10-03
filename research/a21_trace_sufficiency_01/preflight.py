"""Source-sufficiency PREFLIGHT: one command, every gate, refuses to pass
a packet a reader should not receive.

    python3 -m research.a21_trace_sufficiency_01.preflight

Order is fixed and each step must succeed before the next runs:

  1  the sheet index exists and every sheet hashes as indexed
  2  the document-graph candidates exist
  3  the sealed pre-read draft exists (the one model step; it is NOT run
     here - preflight verifies its presence and shape, never its content)
  4  CASE_SOURCE_REQUIREMENTS is the conservative union of 2 and 3
  5  every case sandbox mounts exactly the declared union, nothing else
  6  every reader-visible file passes the pre-read leak screen
  7  every mounted sheet has a controller-side reason

A failure at any step is a refusal to launch, with the step named. A
reader is never started against a packet that has not passed all seven.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research.a21_trace_sufficiency_01 import reader_manifest as RM
from research.a21_trace_sufficiency_01 import source_sufficiency as S

OUT = S.OUT


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run() -> dict:
    steps = []

    def step(name, ok, detail=None):
        steps.append({"STEP": name, "PASSED": bool(ok), "DETAIL": detail})
        if not ok:
            raise SystemExit(json.dumps({
                "PREFLIGHT": "REFUSED", "FAILED_AT": name,
                "DETAIL": detail, "STEPS": steps}, indent=2))

    # 1 sheet index integrity
    idx_p = OUT / "SHEET_INDEX.json"
    step("SHEET_INDEX_PRESENT", idx_p.exists())
    idx = json.loads(idx_p.read_text("utf-8"))["SHEETS"]
    bad = [sid for sid, r in idx.items()
           if not (S.INDEX_BOX / r["PREPARED_FILE"]).exists()
           or _sha(S.INDEX_BOX / r["PREPARED_FILE"])
           != r["SOURCE_PRESENTATION_HASH"]]
    step("SHEET_INDEX_HASHES_MATCH", not bad, bad or None)

    # 2 document graph
    dg = OUT / "DOCUMENT_GRAPH_CANDIDATES.json"
    step("DOCUMENT_GRAPH_PRESENT", dg.exists())

    # 3 pre-read draft - presence and shape only
    pr = OUT / "CASE_SOURCE_REQUIREMENTS_DRAFT.json"
    step("VISUAL_PREREAD_DRAFT_PRESENT", pr.exists())
    draft = json.loads(pr.read_text("utf-8"))
    shape_bad = [c.get("CASE_ID") for c in draft.get("CASES", [])
                 if not all(k in c for k in ("PRIMARY_PLAN",
                                             "MISSING_SOURCE",
                                             "WHY_EACH_SOURCE_IS_REQUIRED"))]
    step("VISUAL_PREREAD_DRAFT_SHAPE", not shape_bad, shape_bad or None)

    # 4 merged requirements are a union, not a vote
    req_p = OUT / "CASE_SOURCE_REQUIREMENTS.json"
    step("CASE_SOURCE_REQUIREMENTS_PRESENT", req_p.exists())
    req = json.loads(req_p.read_text("utf-8"))
    step("NO_MAJORITY_VOTE", req.get("NO_MAJORITY_VOTE") is True)
    union_bad = []
    for c in req["CASES"]:
        b = c["BUCKETS"]
        expect = sorted(set(b["REQUIRED_BY_BOTH"]
                            + b["REQUIRED_BY_DOCUMENT_GRAPH"]
                            + b["REQUIRED_BY_VISUAL_PREREAD"]))
        if expect != sorted(c["CONSERVATIVE_UNION_MOUNTED"]):
            union_bad.append(c["CASE_ID"])
    step("MOUNT_LIST_IS_THE_CONSERVATIVE_UNION", not union_bad,
         union_bad or None)

    # 5 sandbox = declared union, nothing else
    sb_bad = []
    for c in req["CASES"]:
        d = S.CASE_BOX / c["CASE_ID"]
        if not d.exists():
            sb_bad.append({"CASE_ID": c["CASE_ID"], "WHY": "no sandbox"})
            continue
        mounted = sorted(p.stem for p in d.glob("*.jpeg"))
        extra = sorted(p.name for p in d.iterdir()
                       if p.suffix not in (".jpeg", ".json")
                       or (p.suffix == ".json" and p.name != "TASK.json"))
        if mounted != sorted(c["CONSERVATIVE_UNION_MOUNTED"]) or extra:
            sb_bad.append({"CASE_ID": c["CASE_ID"], "MOUNTED": mounted,
                           "DECLARED": c["CONSERVATIVE_UNION_MOUNTED"],
                           "EXTRA_FILES": extra})
    step("SANDBOX_MOUNTS_EXACTLY_THE_DECLARED_SET", not sb_bad, sb_bad or None)

    # 6 leak screen (reader_manifest.build raises on any leak)
    try:
        rm = RM.build()
        step("READER_VISIBLE_FILES_PASS_LEAK_SCREEN", rm["LEAKS"] == 0, rm)
    except SystemExit as e:
        step("READER_VISIBLE_FILES_PASS_LEAK_SCREEN", False, str(e))

    # 7 every mounted sheet has a controller reason
    no_reason = []
    for c in req["CASES"]:
        reasons = {r["SHEET_ID"] for r in c["SOURCE_REQUIREMENTS"]
                   if r.get("REASON_VISUAL_PREREAD")
                   or r.get("REASON_DOCUMENT_GRAPH")}
        for sid in c["CONSERVATIVE_UNION_MOUNTED"]:
            if sid not in reasons:
                no_reason.append({"CASE_ID": c["CASE_ID"], "SHEET_ID": sid})
    step("EVERY_MOUNTED_SHEET_HAS_A_CONTROLLER_REASON", not no_reason,
         no_reason or None)

    body = {"PREFLIGHT": "PASSED", "STEPS": steps,
            "CASES_CLEARED_TO_LAUNCH": [c["CASE_ID"] for c in req["CASES"]],
            "SOURCE_SET_STATUS": {c["CASE_ID"]: c["CASE_SOURCE_STATUS"]
                                  for c in req["CASES"]}}
    p = OUT / "PREFLIGHT_RESULT.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    body["SHA256"] = _sha(p)
    return body


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("PREFLIGHT", "CASES_CLEARED_TO_LAUNCH",
                                        "SOURCE_SET_STATUS", "SHA256")},
                     indent=2))
    sys.exit(0)
