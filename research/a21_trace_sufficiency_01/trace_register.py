"""Assemble the TRACE_REGISTER from whatever trace readings exist.

Every trace is validated against the schema, stamped with the source and
presentation hashes of the sheet it sits on, and projected back to the
original PDF page through that sheet's stored inverse transform. A trace
that fails validation is kept and marked REJECTED with the reason - a
register that silently drops its bad rows is not a register.

    python3 -m research.a21_trace_sufficiency_01.trace_register
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import hashlib as _h

from research.a21_trace_sufficiency_01 import protocol as P
from research.a21_trace_sufficiency_01 import source_access_guard as SAG
from research.a21_trace_sufficiency_01 import visual_trace as VT

VALIDATOR_FILE = Path("research/a21_trace_sufficiency_01/visual_trace.py")

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
RAW = OUT / "trace_raw"

FIVE_STATUSES = ("GEOMETRY_STATUS", "IDENTITY_STATUS", "DIMENSION_STATUS",
                 "TREATMENT_STATUS", "PARAMETER_STATUS")


def _project(geom_field, geom, tr: VT.SheetTransform):
    """Same shape, in original-page pixels.

    Dispatch on the SHAPE the field name declares, not on one exact
    name: TEXT_BBOX is a bbox just as PIXEL_BBOX is, and the dimension
    and extension lines are polylines. A rotated bbox is not a bbox, so
    its corners are transformed and re-bounded.
    """
    if geom_field.endswith("_POINT"):
        return list(tr.to_original(*geom))
    if geom_field.endswith("_BBOX"):
        x0, y0, x1, y1 = geom
        a = tr.to_original(x0, y0)
        b = tr.to_original(x1, y1)
        return [min(a[0], b[0]), min(a[1], b[1]),
                max(a[0], b[0]), max(a[1], b[1])]
    return [list(tr.to_original(*p)) for p in geom]


def build() -> dict:
    idx = json.loads((OUT / "SHEET_INDEX.json").read_text("utf-8"))["SHEETS"]
    transforms = {sid: VT.SheetTransform(rec) for sid, rec in idx.items()}

    traces, rejected, per_case = [], [], {}
    for f in sorted(RAW.glob("*.json")):
        doc = json.loads(f.read_text("utf-8"))
        cid = doc["CASE_ID"]
        per_case[cid] = {
            "SOURCE_FILE": f.name,
            "SOURCE_SHA256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "TRACES_SUBMITTED": len(doc.get("TRACES") or []),
            "NEW_SOURCE_REQUIREMENTS": doc.get("NEW_SOURCE_REQUIREMENTS") or [],
            "SOURCE_SET_INCOMPLETE_ITEMS":
                doc.get("SOURCE_SET_INCOMPLETE_ITEMS") or [],
            "WHERE_I_MIGHT_BE_WRONG": doc.get("WHERE_I_MIGHT_BE_WRONG") or [],
        }
        for t in doc.get("TRACES") or []:
            t = dict(t)
            t.setdefault("CASE_ID", cid)
            rec_status, reasons = VT.record_status(t, idx)
            missing = [st for st in FIVE_STATUSES if not t.get(st)]
            if missing:
                rec_status = "INVALID"
                reasons.append(f"missing statuses: {','.join(missing)}")
            t["TRACE_RECORD_STATUS"] = rec_status
            t["TRACE_LOCATABILITY_STATUS"] = VT.locatability_status(t)
            t["EFFECTIVE_CLAIM_TYPE"] = VT.effective_claim_type(t)
            if rec_status == "INVALID":
                rejected.append({"TRACE_ID": t.get("TRACE_ID"),
                                 "CASE_ID": cid, "REASONS": reasons,
                                 "KEPT_FOR_THE_RECORD": True, "TRACE": t})
                continue
            sid = t["SHEET_ID"]
            rec, tr = idx[sid], transforms[sid]
            t["SOURCE_FILE_HASH"] = rec["ORIGINAL_HASH"]
            t["SOURCE_PRESENTATION_HASH"] = rec["SOURCE_PRESENTATION_HASH"]
            t["SOURCE_COORDINATE_SYSTEM"] = rec["SOURCE_COORDINATE_SYSTEM"]
            t["ORIGINAL_PDF_PAGE"] = rec["ORIGINAL_PDF_PAGE"]
            t["ORIGINAL_PAGE_COORDINATE_TRANSFORM"] = rec[
                "ORIGINAL_PAGE_COORDINATE_TRANSFORM"]
            fields = [gg for gg in VT.geometry_fields_for(t["CLAIM_TYPE"])
                      if t.get(gg)]
            t["ORIGINAL_PAGE_GEOMETRY"] = (
                {f: {"FIELD": f, "COORDINATES": _project(f, t[f], tr)}
                 for f in fields} if fields
                else {"WHY_NOT": "the trace carries no geometry, so there "
                                 "is nothing to project and nothing "
                                 "honest to draw"})
            traces.append(t)

    by_type, by_status, by_case, by_eff = {}, {}, {}, {}
    for t in traces:
        by_type[t["CLAIM_TYPE"]] = by_type.get(t["CLAIM_TYPE"], 0) + 1
        by_eff[t["EFFECTIVE_CLAIM_TYPE"]] = by_eff.get(
            t["EFFECTIVE_CLAIM_TYPE"], 0) + 1
        s = t["VISUAL_TRACE_STATUS"]
        by_status[s] = by_status.get(s, 0) + 1
        by_case[t["CASE_ID"]] = by_case.get(t["CASE_ID"], 0) + 1

    # the linkage that matters: does a dimension support a geometry trace
    ids = {t["TRACE_ID"] for t in traces}
    dims = {t["TRACE_ID"] for t in traces
            if t["CLAIM_TYPE"] in ("PRINTED_DIMENSION", "HEIGHT_DIMENSION")}
    supported, dangling = 0, []
    for t in traces:
        sb = t.get("SUPPORTED_BY")
        if not sb:
            continue
        for ref in ([sb] if isinstance(sb, str) else sb):
            if ref in ids:
                supported += 1
            else:
                dangling.append({"TRACE_ID": t["TRACE_ID"],
                                 "SUPPORTED_BY": ref,
                                 "PROBLEM": "no such trace in the register"})

    locatable = [t for t in traces
                 if t["TRACE_LOCATABILITY_STATUS"] == "LOCATABLE"]
    access = SAG.audit_all()
    body = {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "TRACE_REGISTER",
        "VALIDATOR_SHA256": _h.sha256(VALIDATOR_FILE.read_bytes()).hexdigest(),
        "CASES_PRESENT": sorted(per_case),
        "PER_CASE": per_case,
        # the three statuses, reported separately and never collapsed
        "VALID_TRACE_RECORDS": len(traces),
        "LOCATABLE_TRACES": len(locatable),
        "NON_LOCATABLE_VALID_TRACES": len(traces) - len(locatable),
        "INVALID_TRACE_RECORDS": len(rejected),
        "A_NON_LOCATABLE_VALID_TRACE_IS_NOT_A_FAILURE": (
            "it is how a reader says 'there is something here I cannot "
            "place'. It is counted, kept, and never drawn"),
        "SOURCE_ACCESS_AUDIT": access,
        "SOURCE_ACCESS_ALL_WITHIN_SANDBOX": all(
            v["STATUS"] == "WITHIN_SANDBOX" for v in access.values()),
        "TRACES_ACCEPTED": len(traces),
        "TRACES_REJECTED": len(rejected),
        "BY_CLAIM_TYPE": dict(sorted(by_type.items())),
        "BY_EFFECTIVE_CLAIM_TYPE": dict(sorted(by_eff.items())),
        "BY_VISUAL_TRACE_STATUS": dict(sorted(by_status.items())),
        "BY_CASE": dict(sorted(by_case.items())),
        "DIMENSION_TRACES": len(dims),
        "SUPPORTED_BY_LINKS_RESOLVED": supported,
        "DANGLING_SUPPORTED_BY": dangling,
        "TRACES_WITH_GEOMETRY": sum(
            1 for t in traces
            if "WHY_NOT" not in t["ORIGINAL_PAGE_GEOMETRY"]),
        "TRACES_WITHOUT_GEOMETRY": sum(
            1 for t in traces
            if "WHY_NOT" in t["ORIGINAL_PAGE_GEOMETRY"]),
        "PROJECTED_GEOMETRIES": sum(
            len(t["ORIGINAL_PAGE_GEOMETRY"]) for t in traces
            if "WHY_NOT" not in t["ORIGINAL_PAGE_GEOMETRY"]),
        "EVERY_TRACE_WITH_GEOMETRY_CARRIES_ITS_ORIGINAL_PAGE_GEOMETRY": True,
        "REJECTED_ARE_KEPT_NOT_DROPPED": (
            "a register that silently drops its bad rows is not a "
            "register. Each rejection carries its reasons and its trace"),
        "TRACES": traces,
        "REJECTED": rejected,
    }
    p = OUT / "TRACE_REGISTER.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "VALIDATOR_SHA256": body["VALIDATOR_SHA256"],
            "VALID": len(traces), "LOCATABLE": len(locatable),
            "NON_LOCATABLE_VALID": len(traces) - len(locatable),
            "INVALID": len(rejected),
            "SOURCE_ACCESS_ALL_WITHIN_SANDBOX":
                body["SOURCE_ACCESS_ALL_WITHIN_SANDBOX"],
            "BY_EFFECTIVE_CLAIM_TYPE": body["BY_EFFECTIVE_CLAIM_TYPE"],
            "ACCEPTED": len(traces), "REJECTED": len(rejected),
            "BY_CLAIM_TYPE": body["BY_CLAIM_TYPE"],
            "BY_VISUAL_TRACE_STATUS": body["BY_VISUAL_TRACE_STATUS"],
            "SUPPORTED_BY_LINKS_RESOLVED": supported,
            "DANGLING": len(dangling)}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
