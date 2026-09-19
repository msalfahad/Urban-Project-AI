"""Adapter: frozen trace register + declarations  ->  face-set inputs.

Deterministic. Reads traces, writes nothing back. A face's length comes
from the trace's own LENGTH_M when the reader marked DIMENSION_STATUS
ESTABLISHED (as engine.trace_to_region does), or from a declared
DERIVED_CHAIN (PROVISIONAL by rule). Its material role comes from the
overlap audit's physical-object records (claim-type default or a recorded
controller override). Nothing is scaled off the sheet.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine import material_role_audit as MRA
from research.qs_wall_treatment_01 import declarations as D
from research.qs_wall_treatment_01 import protocol as P

OPENING_TYPES = ("DOOR", "WINDOW", "GLAZING")


def _length(t: dict, by_id: dict):
    sup = t.get("SUPPORTED_BY")
    sup = [sup] if isinstance(sup, str) else (sup or [])
    dims = [s for s in sup if s in by_id and by_id[s]["EFFECTIVE_CLAIM_TYPE"]
            in ("PRINTED_DIMENSION", "HEIGHT_DIMENSION")]
    if t.get("DIMENSION_STATUS") == "ESTABLISHED" and isinstance(
            t.get("LENGTH_M"), (int, float)):
        return t["LENGTH_M"], "DRAWING_PRINTED_DIMENSION", "PRINTED_DIMENSION", dims
    return None, None, None, dims


def load_register() -> dict:
    return json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))


def face_set_inputs(plan: dict, reg: dict, owner_records: dict | None = None) -> dict:
    cid = plan["CASE"]
    traces = [t for t in reg["TRACES"] if t["CASE_ID"] == cid]
    by_id = {t["TRACE_ID"]: t for t in traces}
    objs = {o["TRACE_ID"]: o for o in MRA.physical_objects(
        traces, object_map=D.OBJECT_MAP.get(cid),
        role_overrides=D.ROLE_OVERRIDES.get(cid),
        solid_base_of=D.SOLID_BASE_OF.get(cid))}
    owners = {r["TRACE_ID"]: r for r in (owner_records or {}).get(cid, [])}
    faces = []
    for fid in plan["FACES"]:
        t = by_id[fid]
        o = objs[fid]
        L, src, basis, dims = _length(t, by_id)
        rec = {
            "FACE_ID": fid, "PHYSICAL_OBJECT_ID": o["PHYSICAL_OBJECT_ID"],
            "MATERIAL_ROLE": o["MATERIAL_ROLE"], "ROLE_ASSIGNED_BY": o["ROLE_ASSIGNED_BY"],
            "SIDE": plan["SIDE"], "SHEET_ID": t["SHEET_ID"],
            "length_m": L, "length_source": src, "length_basis": basis,
            "supporting_dimensions": dims, "trace_ids": [fid],
            "VISUAL_TRACE_STATUS": t["VISUAL_TRACE_STATUS"],
            "DIMENSION_STATUS": t.get("DIMENSION_STATUS"),
            "HOST_OBJECT": o.get("HOST_OBJECT"),
        }
        dl = D.DERIVED_LENGTHS.get((cid, fid))
        if dl and L is None:
            rec.update({"length_m": dl["length_m"], "length_basis": dl["length_basis"],
                        "length_source": "DRAWING_PRINTED_DIMENSION",
                        "supporting_dimensions": dl["supporting_dimensions"],
                        "LENGTH_FORMULA": dl["FORMULA"],
                        "WHY_PROVISIONAL": dl["WHY_PROVISIONAL"]})
        fd = D.FACE_DIMENSIONS.get((cid, fid))
        if fd:
            for k in ("height_m", "height_source", "width_m", "width_source"):
                if k in fd:
                    rec[k] = fd[k]
            rec["DIMENSION_NOTE"] = fd.get("NOTE")
            rec["DIMENSION_OWNER_STATUS"] = {
                d: owners[d]["DIMENSION_OWNER_STATUS"]
                for d in fd.get("supporting_dimensions", []) if d in owners}
        if plan.get("HEIGHT_PARAMETER"):
            rec["HEIGHT_PARAMETER"] = plan["HEIGHT_PARAMETER"]
        ur = (plan.get("UNRESOLVED_FACES") or {}).get(fid)
        if ur:
            rec["MATERIAL_ROLE"] = "UNRESOLVED"
            rec["ROLE_ASSIGNED_BY"] = "FACE_SET_PLAN_DECLARATION"
            rec["WHY_UNRESOLVED_IN_THIS_SET"] = ur
        faces.append(rec)
    openings = []
    for oid in plan["OPENINGS"]:
        t = by_id[oid]
        L, src, basis, dims = _length(t, by_id)
        host = t.get("HOSTED_IN")
        host = host[0] if isinstance(host, list) and host else host
        openings.append({
            "OPENING_ID": oid, "TYPE": (t["EFFECTIVE_CLAIM_TYPE"]
                                        if t["EFFECTIVE_CLAIM_TYPE"] in OPENING_TYPES
                                        else "UNRESOLVED"),
            "HOSTED_IN": host, "width_m": L, "width_source": src,
            "height_m": None, "height_source": None,
            "trace_ids": [oid] + dims, "VISUAL_TRACE_STATUS": t["VISUAL_TRACE_STATUS"],
        })
    return {"faces": faces, "openings": openings}
