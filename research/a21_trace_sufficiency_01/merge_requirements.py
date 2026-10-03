"""Merge the two source-sufficiency paths into CASE_SOURCE_REQUIREMENTS.

Conservative union, never a vote. Omission risk is asymmetric: a
necessary sheet left out produces a FALSE UNKNOWN that looks exactly like
a real one, which is how DEV-02 and DEV-03 happened. One extra legitimate
architectural sheet costs attention. So if EITHER path names a specific
sheet as necessary and gives a defensible reason, it is mounted.

Mounting a sheet is not evidence that the sheet supports a measurement.
It only means the reader is allowed to look at a legitimate source.

    python3 -m research.a21_trace_sufficiency_01.merge_requirements
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import document_graph as DG
from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import source_sufficiency as S

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")

REQUIREMENT_STATUSES = ("REQUIRED", "OPTIONAL_CONTEXT", "POSSIBLY_RELEVANT",
                        "NOT_REQUIRED", "UNRESOLVED")
DISCOVERED_BY = ("DOCUMENT_GRAPH", "VISUAL_PREREAD", "BOTH")
CONFIDENCE = ("ESTABLISHED", "PROVISIONAL", "UNRESOLVED")

MOUNTING_IS_NOT_EVIDENCE = (
    "a sheet in the packet is a sheet the reader is ALLOWED to look at. "
    "It is not a claim that the sheet supports any measurement, and no "
    "result may be upgraded because a sheet was mounted")


def _visual(draft: dict) -> dict:
    """Pull sheet relationships out of the pre-read's own field layout.

    The pre-read put FIRST_FLOOR_PLAN under REQUIRED_DETAILS and said so
    itself, flagging that the schema had no second required-plan slot.
    That is a schema defect on my side, not a mistake on its side, so the
    entry is honoured as a required sheet rather than dropped.
    """
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]
    out = {}
    for c in draft["CASES"]:
        rels = {}
        why = c.get("WHY_EACH_SOURCE_IS_REQUIRED") or {}

        def put(sheet, status):
            if sheet and sheet in idx:
                rels[sheet] = {"REQUIREMENT_STATUS": status,
                               "REASON": why.get(sheet, "")}
        put(c.get("PRIMARY_PLAN"), "REQUIRED")
        for s in (c.get("REQUIRED_SECTIONS") or []):
            put(s, "REQUIRED")
        for s in (c.get("REQUIRED_ELEVATIONS") or []):
            put(s, "REQUIRED")
        for s in (c.get("REQUIRED_DETAILS") or []):
            put(s, "REQUIRED")
        for s in (c.get("OPTIONAL_CONTEXT") or []):
            if s not in rels:
                put(s, "OPTIONAL_CONTEXT")
        out[c["CASE_ID"]] = {
            "RELATIONSHIPS": rels,
            "REQUIRED_SCHEDULES": c.get("REQUIRED_SCHEDULES") or [],
            "MISSING_SOURCE": c.get("MISSING_SOURCE") or [],
            "PRIMARY_PLAN": c.get("PRIMARY_PLAN"),
            "NON_SHEET_DETAILS_CLAIMED": [
                s for s in (c.get("REQUIRED_DETAILS") or []) if s not in idx],
        }
    return out


def _document(doc: dict) -> dict:
    out = {}
    for c in doc["CASES"]:
        out[c["CASE_ID"]] = {
            "RELATIONSHIPS": {r["SHEET_ID"]: {
                "REQUIREMENT_STATUS": r["REQUIREMENT_STATUS"],
                "REASON": r["REASON"]} for r in c["SHEET_RELATIONSHIPS"]},
            "REQUIRED_SCHEDULES": c.get("REQUIRED_SCHEDULES") or [],
            "MISSING_SOURCE": c.get("MISSING_SOURCE") or [],
        }
    return out


STRENGTH = {"REQUIRED": 0, "OPTIONAL_CONTEXT": 1, "POSSIBLY_RELEVANT": 2,
            "UNRESOLVED": 3, "NOT_REQUIRED": 4}


def merge() -> dict:
    draft = json.loads(
        (OUT / "CASE_SOURCE_REQUIREMENTS_DRAFT.json").read_text("utf-8"))
    doc = json.loads(
        (OUT / "DOCUMENT_GRAPH_CANDIDATES.json").read_text("utf-8"))
    vis, dgr = _visual(draft), _document(doc)

    cases, n = [], 0
    for cid in sorted(set(vis) | set(dgr)):
        v = vis.get(cid, {"RELATIONSHIPS": {}})
        d = dgr.get(cid, {"RELATIONSHIPS": {}})
        buckets = {"REQUIRED_BY_BOTH": [], "REQUIRED_BY_DOCUMENT_GRAPH": [],
                   "REQUIRED_BY_VISUAL_PREREAD": [], "POSSIBLY_RELEVANT": [],
                   "UNRESOLVED_REQUIREMENT": []}
        records = []
        for sheet in sorted(set(v["RELATIONSHIPS"]) | set(d["RELATIONSHIPS"])):
            vr = v["RELATIONSHIPS"].get(sheet)
            dr = d["RELATIONSHIPS"].get(sheet)
            vreq = bool(vr and vr["REQUIREMENT_STATUS"] == "REQUIRED")
            dreq = bool(dr and dr["REQUIREMENT_STATUS"] == "REQUIRED")
            if vreq and dreq:
                bucket, by, conf = "REQUIRED_BY_BOTH", "BOTH", "ESTABLISHED"
                status = "REQUIRED"
            elif vreq:
                bucket, by = "REQUIRED_BY_VISUAL_PREREAD", "VISUAL_PREREAD"
                status, conf = "REQUIRED", "PROVISIONAL"
            elif dreq:
                bucket, by = "REQUIRED_BY_DOCUMENT_GRAPH", "DOCUMENT_GRAPH"
                status, conf = "REQUIRED", "PROVISIONAL"
            else:
                bucket = "POSSIBLY_RELEVANT"
                by = ("BOTH" if vr and dr
                      else ("VISUAL_PREREAD" if vr else "DOCUMENT_GRAPH"))
                status = min([r["REQUIREMENT_STATUS"] for r in (vr, dr) if r],
                             key=lambda s: STRENGTH[s])
                conf = "PROVISIONAL"
            buckets[bucket].append(sheet)
            n += 1
            records.append({
                "SOURCE_REQUIREMENT_ID": f"SR-{n:03d}",
                "CASE_ID": cid, "SHEET_ID": sheet,
                "REQUIREMENT_STATUS": status,
                "REASON_DOCUMENT_GRAPH": (dr or {}).get("REASON"),
                "REASON_VISUAL_PREREAD": (vr or {}).get("REASON"),
                "DISCOVERED_BY": by,
                "SOURCE_REQUIREMENT_CONFIDENCE_STATUS": conf,
                "PATHS_DISAGREE": bool(vr) != bool(dr) or (
                    vr and dr and vr["REQUIREMENT_STATUS"]
                    != dr["REQUIREMENT_STATUS"]),
            })

        mount = sorted(set(buckets["REQUIRED_BY_BOTH"]
                           + buckets["REQUIRED_BY_DOCUMENT_GRAPH"]
                           + buckets["REQUIRED_BY_VISUAL_PREREAD"]))
        missing = sorted(set(v.get("MISSING_SOURCE", [])
                             + d.get("MISSING_SOURCE", [])))
        cases.append({
            "CASE_ID": cid,
            "QUESTION": S.QUESTIONS[cid],
            "PRIMARY_PLAN": v.get("PRIMARY_PLAN"),
            "BUCKETS": buckets,
            "SOURCE_REQUIREMENTS": records,
            "CONSERVATIVE_UNION_MOUNTED": mount,
            "MOUNTED_COUNT": len(mount),
            "NOT_MOUNTED": sorted(
                set(json.loads((OUT / "SHEET_INDEX.json")
                               .read_text("utf-8"))["SHEETS"]) - set(mount)),
            "REQUIRED_SCHEDULES": sorted(set(
                v.get("REQUIRED_SCHEDULES", []) + d.get(
                    "REQUIRED_SCHEDULES", []))),
            "MISSING_SOURCE": missing,
            "NON_SHEET_DETAILS_CLAIMED": v.get("NON_SHEET_DETAILS_CLAIMED", []),
            "CASE_SOURCE_STATUS": ("SOURCE_SET_INCOMPLETE" if missing
                                   else "SOURCE_SET_COMPLETE"),
        })

    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "CASE_SOURCE_REQUIREMENTS",
        "TWO_PATHS": ["DOCUMENT_GRAPH", "VISUAL_PREREAD"],
        "NO_MAJORITY_VOTE": True,
        "WHY_CONSERVATIVE_UNION": (
            "omission risk is asymmetric. A necessary sheet left out "
            "produces a false UNKNOWN indistinguishable from a real one - "
            "that is exactly DEV-02 and DEV-03. An extra legitimate "
            "architectural sheet costs attention and nothing else"),
        "MOUNTING_IS_NOT_EVIDENCE": MOUNTING_IS_NOT_EVIDENCE,
        "E1_4_WAS_NOT_CONSULTED_BY_EITHER_PATH": True,
        "REQUIREMENT_STATUSES": list(REQUIREMENT_STATUSES),
        "DISCOVERED_BY_VALUES": list(DISCOVERED_BY),
        "CONFIDENCE_STATUSES": list(CONFIDENCE),
        "NO_NUMERIC_CONFIDENCE_SCORE": True,
        "A_MISSING_SOURCE_DOES_NOT_UPGRADE_ANYTHING": (
            "A21 may still inspect the available geometry, but no result "
            "may be upgraded to ESTABLISHED because the missing source was "
            "unavailable"),
        "CASES": cases,
    }
    p = OUT / "CASE_SOURCE_REQUIREMENTS.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "MOUNTED": {c["CASE_ID"]: c["CONSERVATIVE_UNION_MOUNTED"]
                        for c in cases},
            "BUCKETS": {c["CASE_ID"]: {k: v for k, v in c["BUCKETS"].items()
                                       if v} for c in cases},
            "STATUS": {c["CASE_ID"]: c["CASE_SOURCE_STATUS"] for c in cases},
            "MISSING": {c["CASE_ID"]: c["MISSING_SOURCE"] for c in cases}}


if __name__ == "__main__":
    print(json.dumps(merge(), indent=2))
