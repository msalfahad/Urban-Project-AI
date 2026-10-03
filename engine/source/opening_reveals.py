"""OPENING REVEAL SURFACES (R8.14) - the jambs and soffit of an opening as their own surfaces, each owned once.

For an open passage (OPEN_PASSAGE_SITE) with source-measured geometry (width along the wall, depth = wall thickness):
  LEFT_JAMB / RIGHT_JAMB   depth x clear height, ONLY where the jamb has physical authority: a drawn admitted segment
                           across the band end, or an owner physical fact binding that wall end; a zero-material
                           topology closure alone creates NO surface
  TOP_SOFFIT               width x depth, only for a passage WITH a head (owner / source): the soffit footprint leaves
                           the normal CEILING region; a FULL_HEIGHT passage has no soffit
Ownership (double-count guard): the room WALL FACE loses the opening rectangle (width x clear height per side); the
reveal surfaces are separate; the CEILING loses the soffit footprint. A footprint is owned by exactly one region.
Finish comes from authority only (e.g. PLASTER); paint is never inferred.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "OPENING_REVEAL_POLICY_V2"          # V2 (R8.15): reveal depth basis (source first, default fallback)
LEFT_JAMB, RIGHT_JAMB, TOP_SOFFIT = "LEFT_JAMB", "RIGHT_JAMB", "TOP_SOFFIT"
WITH_HEAD, FULL_HEIGHT, HEAD_NOT_ESTABLISHED = "WITH_HEAD", "FULL_HEIGHT", "HEAD_NOT_ESTABLISHED"
NO_JAMB_AUTHORITY = "NO_JAMB_AUTHORITY"
SOURCE_DEPTH, DEFAULT_DEPTH, DEPTH_UNRESOLVED = "SOURCE_PHYSICAL_DEPTH", "METHOD_DEFAULT_FALLBACK", "DEPTH_UNRESOLVED"


def reveal_depth(source_m, default_m=None, default_ref=None) -> dict:
    """V2: a measured source depth always wins; a method default (e.g. US-07 0.25 m) is a FALLBACK used only where
    no source depth exists, and is otherwise kept as a counterfactual - never an override."""
    if source_m is not None:
        return {"depth_m": source_m, "basis": SOURCE_DEPTH, "default_m": default_m, "default_ref": default_ref,
                "default_used": False}
    if default_m is not None:
        return {"depth_m": default_m, "basis": DEFAULT_DEPTH, "default_m": default_m, "default_ref": default_ref,
                "default_used": True}
    return {"depth_m": None, "basis": DEPTH_UNRESOLVED, "default_m": None, "default_ref": None, "default_used": False}


def shoelace(poly) -> float:
    return abs(math.fsum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                         for i in range(len(poly)))) / 2


def passage_reveals(passage: dict, *, head, clear_height, jamb_authority: dict, finish: dict, unit_to_m: float,
                    source_refs=(), default_depth_m=None, default_ref=None, height_basis=None,
                    jamb_absent=None) -> dict:
    """passage: an OPEN_PASSAGE_SITE record (polygon, width, wall_thickness); head: WITH_HEAD / FULL_HEIGHT /
    HEAD_NOT_ESTABLISHED; clear_height (m) or None; jamb_authority: {LEFT_JAMB: ref or None, RIGHT_JAMB: ...};
    finish: {surface: finish or None} from authority."""
    w = passage["width"] * unit_to_m
    dep = reveal_depth(passage["wall_thickness"] * unit_to_m if passage.get("wall_thickness") else None,
                       default_depth_m, default_ref)
    d = dep["depth_m"]
    foot = shoelace(passage["polygon"]) * unit_to_m ** 2
    surfaces, missing = [], []
    for side in (LEFT_JAMB, RIGHT_JAMB):
        auth = jamb_authority.get(side)
        if not auth:
            missing.append({"surface": side, "state": (jamb_absent or {}).get(side, NO_JAMB_AUTHORITY)})
            continue
        surfaces.append({"surface": side, "opening": passage["passage_id"], "depth_m": d, "height_m": clear_height,
                         "height_basis": height_basis, "depth_basis": dep["basis"],
                         "area_m2": None if clear_height is None or d is None else d * clear_height,
                         "area_at_default_depth_m2": None if clear_height is None or default_depth_m is None else
                         default_depth_m * clear_height, "authority": auth,
                         "finish": finish.get(side), "trade": "PLASTER" if finish.get(side) == "PLASTER" else None})
    if head == WITH_HEAD:
        surfaces.append({"surface": TOP_SOFFIT, "opening": passage["passage_id"], "width_m": w, "depth_m": d,
                         "depth_basis": dep["basis"], "height_m": clear_height, "area_m2": foot, "footprint_m2": foot,
                         "area_at_default_depth_m2": None if default_depth_m is None else w * default_depth_m,
                         "finish": finish.get(TOP_SOFFIT), "trade": "PLASTER" if finish.get(TOP_SOFFIT) == "PLASTER"
                         else None, "authority": list(source_refs)})
    own = {"CEILING_EXCLUDES_M2": foot if head == WITH_HEAD else 0.0,
           "CEILING_STATE": {WITH_HEAD: "SOFFIT_FOOTPRINT_REMOVED", FULL_HEIGHT: "CEILING_CONTINUES",
                             HEAD_NOT_ESTABLISHED: "HEAD_CONDITION_NOT_ESTABLISHED"}[head],
           "ROOM_WALL_FACE_LOSES": {"width_m": w, "height_m": clear_height, "per_side_m2":
                                    None if clear_height is None else w * clear_height, "sides": 2},
           "PAINT": "NOT_AUTHORISED (a separate trade authority)"}
    if head == FULL_HEIGHT:
        missing.append({"surface": TOP_SOFFIT, "state": "NO_HEAD_FULL_HEIGHT"})
    return {"passage": passage["passage_id"], "head": head, "footprint_m2": foot, "width_m": w, "depth_m": d,
            "depth": dep, "surfaces": surfaces, "missing": missing, "ownership": own}


def ownership_guard(claims) -> list:
    """claims: [(footprint id, region)] - a footprint claimed by more than one region is a double count."""
    by = {}
    for fid, region in claims:
        by.setdefault(fid, set()).add(region)
    return sorted([f, sorted(r)] for f, r in by.items() if len(r) > 1)


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "surfaces": [LEFT_JAMB, RIGHT_JAMB, TOP_SOFFIT],
           "depth_basis": [SOURCE_DEPTH, DEFAULT_DEPTH, DEPTH_UNRESOLVED],
           "depth_rule": "a measured source depth always wins; a method default is fallback-only (else counterfactual)",
           "head": [WITH_HEAD, FULL_HEIGHT, HEAD_NOT_ESTABLISHED],
           "never": ["a soffit and a ceiling over one footprint", "a jamb surface from a topology closure alone",
                     "a jamb counted as room wall face and as reveal", "paint without authority",
                     "a head height transferred from another revision", "a default depth over a measured one",
                     "a top soffit on a FULL_HEIGHT passage"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
