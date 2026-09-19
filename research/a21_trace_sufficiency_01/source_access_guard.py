"""Generic source-access guard: did a reading cite only what was mounted?

Criterion D, checked after the fact and mechanically. DEV-03 went
unnoticed in a frozen experiment because this check was run only where a
reader volunteered a deviation; now it runs over every reading, every
time, and its verdict is stamped into the register.

    python3 -m research.a21_trace_sufficiency_01.source_access_guard
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")


def mounted_sheets(manifest: dict) -> dict:
    return {c["CASE_ID"]: sorted({s["SHEET_ID"] for s in c["SHEETS"]})
            for c in manifest["CASES"]}


def audit_reading(doc: dict, mounted: list, all_sheets: list) -> dict:
    cited = sorted({t.get("SHEET_ID") for t in doc.get("TRACES") or []
                    if t.get("SHEET_ID")})
    blob = json.dumps(doc, ensure_ascii=False)
    mentioned = sorted(s for s in all_sheets if s in blob)
    outside_cited = sorted(set(cited) - set(mounted))
    outside_mentioned = sorted(set(mentioned) - set(mounted))
    return {
        "MOUNTED": mounted,
        "SHEETS_CITED_AS_SHEET_ID": cited,
        "SHEETS_MENTIONED_ANYWHERE": mentioned,
        "CITED_OUTSIDE_SANDBOX": outside_cited,
        "MENTIONED_OUTSIDE_SANDBOX": outside_mentioned,
        "NEW_SOURCE_REQUIREMENTS_RAISED":
            len(doc.get("NEW_SOURCE_REQUIREMENTS") or []),
        "STATUS": ("SOURCE_SET_EXCEEDED" if outside_cited
                   else ("SOURCE_MENTIONED_NOT_CITED" if outside_mentioned
                         else "WITHIN_SANDBOX")),
    }


def audit_all() -> dict:
    manifest = json.loads(
        (OUT / "A21_READER_SOURCE_MANIFEST.json").read_text("utf-8"))
    all_sheets = sorted(
        json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"])
    mounted = mounted_sheets(manifest)
    out = {}
    for f in sorted((OUT / "trace_raw").glob("*.json")):
        doc = json.loads(f.read_text("utf-8"))
        cid = doc["CASE_ID"]
        out[cid] = audit_reading(doc, mounted.get(cid, []), all_sheets)
    return out


if __name__ == "__main__":
    print(json.dumps(audit_all(), indent=2))
