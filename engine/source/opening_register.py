"""OPENING REGISTER (RC1) - one record per physical opening occurrence, with the authority of every attribute.

Input observations come from the frozen wall-face records: the same occurrence is usually seen from the two sites it
joins. consolidate() merges them into one record (FROM / TO sites; a side that is no measured site is OUTSIDE_SCOPE)
and refuses to merge observations that disagree on kind, width or height (state CONFLICT). Every attribute carries
its basis, one of BASES:
  SOURCE                    measured from source geometry (face closures, wall-face spans)
  OWNER_FACT                a project-bound owner physical / method fact
  OWNER_PROJECT_PARAMETER   an owner-confirmed project value (rung 2), e.g. a door height where none is drawn
  URBAN_STANDARD            an approved Urban standard (rung 3)
  TEMPORARY_DEFAULT         a stated placeholder (never source truth)
  NOT_ESTABLISHED           no authority: the attribute stays empty
An AREA is only given when width AND height exist; its basis is the weaker of the two. A material needs an explicit
authority; 'glazed' is never 'aluminium' by itself.

schedules() derives the counts: internal doors, the entrance door(s), sliding glazed doors, windows, open passages
(door_present = False: never counted as a door - an open passage is an opening with nothing in it), and the records
outside the measured scope (listed, never counted).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "OPENING_REGISTER_V1"
BASES = ("SOURCE", "OWNER_FACT", "OWNER_PROJECT_PARAMETER", "URBAN_STANDARD", "TEMPORARY_DEFAULT", "NOT_ESTABLISHED")
RANK = {b: n for n, b in enumerate(BASES)}
DOOR, WINDOW, SLIDING, PASSAGE = "DOOR", "WINDOW", "SLIDING_GLAZED_DOOR", "OPEN_PASSAGE"
OUTSIDE = "OUTSIDE_SCOPE"
IN_SCOPE, OUT_OF_SCOPE, CONFLICT = "IN_SCOPE", "OUT_OF_MEASURED_SCOPE", "CONFLICT"


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def _weaker(*bases):
    return max(bases, key=lambda b: RANK[b])


def consolidate(observations: list, *, scope_sites, tol: float) -> list:
    """observations: [{"occurrence", "site", "kind", "width_m", "width_basis", "height_m", "height_basis",
    "height_authority", "sill_m", "sill_basis", "sill_authority", "sources", ...extra}]. scope_sites: the measured
    sites. Returns one record per occurrence, sorted by occurrence id."""
    groups = {}
    for o in observations:
        groups.setdefault(o["occurrence"], []).append(o)
    scope = set(scope_sites)
    out = []
    for occ in sorted(groups):
        obs = groups[occ]
        f = obs[0]
        sites = sorted({o["site"] for o in obs if o.get("site") in scope})
        conflicts = []
        for k in ("kind", "width_basis", "height_basis"):
            if len({o.get(k) for o in obs}) > 1:
                conflicts.append(k)
        for k in ("width_m", "height_m"):
            vals = [o.get(k) for o in obs]
            if any(v is None for v in vals) != all(v is None for v in vals) or (
                    vals[0] is not None and any(abs(v - vals[0]) > tol for v in vals)):
                conflicts.append(k)
        frm = sites[0] if sites else OUTSIDE
        to = sites[1] if len(sites) > 1 else (f.get("other_side") or OUTSIDE)
        w, h = f.get("width_m"), f.get("height_m")
        wb = f.get("width_basis") or ("SOURCE" if w is not None else "NOT_ESTABLISHED")
        hb = f.get("height_basis") or ("NOT_ESTABLISHED" if h is None else None)
        if hb is None or hb not in BASES or wb not in BASES:
            conflicts.append("basis")
            hb = hb if hb in BASES else "NOT_ESTABLISHED"
        area = round(w * h, 6) if w is not None and h is not None else None
        rec = {"opening_id": occ, "kind": f["kind"], "from_site": frm, "to_site": to,
               "clear_width_m": w, "width_basis": wb, "height_m": h, "height_basis": hb,
               "height_authority": f.get("height_authority"), "area_m2": area,
               "area_basis": _weaker(wb, hb) if area is not None else "NOT_ESTABLISHED",
               "sill_m": f.get("sill_m"), "sill_basis": f.get("sill_basis") or ("NOT_ESTABLISHED" if
                                                                               f.get("sill_m") is None else None),
               "sill_authority": f.get("sill_authority"),
               "door_present": f["kind"] in (DOOR, SLIDING), "sources": sorted({s for o in obs
                                                                                for s in o.get("sources") or ()}),
               "seen_from": sorted({o["site"] for o in obs}),
               "state": CONFLICT if conflicts else (IN_SCOPE if sites else OUT_OF_SCOPE), "conflicts": conflicts}
        for k, v in f.items():
            if k not in rec and k not in ("occurrence", "site", "width_m", "height_m"):
                rec[k] = v
        rec.setdefault("material", None)
        rec.setdefault("material_basis", "NOT_ESTABLISHED")
        rec.setdefault("material_authority", None)
        out.append(rec)
    return out


def schedules(records: list) -> dict:
    inside = [r for r in records if r["state"] == IN_SCOPE]
    role = lambda r: r.get("role") or "INTERNAL"   # noqa: E731
    doors = [r for r in inside if r["kind"] == DOOR and role(r) == "INTERNAL"]
    entrance = [r for r in inside if r["kind"] == DOOR and role(r) == "ENTRANCE"]
    return {"internal_doors": [r["opening_id"] for r in doors], "internal_door_count": len(doors),
            "entrance_doors": [r["opening_id"] for r in entrance], "entrance_door_count": len(entrance),
            "sliding_glazed_doors": [r["opening_id"] for r in inside if r["kind"] == SLIDING],
            "windows": [r["opening_id"] for r in inside if r["kind"] == WINDOW],
            "window_count": sum(1 for r in inside if r["kind"] == WINDOW),
            "open_passages": [r["opening_id"] for r in inside if r["kind"] == PASSAGE],
            "out_of_scope": [r["opening_id"] for r in records if r["state"] == OUT_OF_SCOPE],
            "conflicts": [r["opening_id"] for r in records if r["state"] == CONFLICT]}


def validate(records: list) -> dict:
    errors = []
    for r in records:
        if r["state"] == CONFLICT:
            errors.append({"error": "OBSERVATIONS_DISAGREE", "opening": r["opening_id"], "fields": r["conflicts"]})
        if r["kind"] == PASSAGE and r["door_present"]:
            errors.append({"error": "PASSAGE_WITH_DOOR", "opening": r["opening_id"]})
        if r["material"] is not None and (r["material_basis"] == "NOT_ESTABLISHED" or not r["material_authority"]):
            errors.append({"error": "MATERIAL_WITHOUT_AUTHORITY", "opening": r["opening_id"]})
        if r["height_m"] is None and r["height_basis"] != "NOT_ESTABLISHED":
            errors.append({"error": "HEIGHT_BASIS_WITHOUT_HEIGHT", "opening": r["opening_id"]})
        if r["height_m"] is not None and r["height_basis"] == "NOT_ESTABLISHED":
            errors.append({"error": "HEIGHT_WITHOUT_BASIS", "opening": r["opening_id"]})
        if r["area_m2"] is not None and RANK[r["area_basis"]] < max(RANK[r["width_basis"]], RANK[r["height_basis"]]):
            errors.append({"error": "AREA_BASIS_STRONGER_THAN_INPUTS", "opening": r["opening_id"]})
    sch = schedules(records)
    overlap = set(sch["internal_doors"]) & set(sch["open_passages"])
    if overlap:
        errors.append({"error": "PASSAGE_COUNTED_AS_DOOR", "openings": sorted(overlap)})
    return {"state": "PASS" if not errors else "FAIL", "errors": errors, "records": len(records),
            "schedules": sch, "digest": _digest(records)}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "bases": list(BASES),
           "identity": "one record per opening occurrence; FROM / TO = the measured sites it joins",
           "area": "width x height only when both exist; basis = the weaker basis",
           "never": ["an inferred attribute", "a fallback presented as source", "an open passage in a door count",
                     "a material without explicit authority ('glazed' is not 'aluminium')",
                     "an out-of-scope opening in a count"]}
    rec["digest"] = _digest(rec)
    return rec
