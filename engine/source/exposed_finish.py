"""EXPOSED OBJECT FACE FINISH (R8.19) - finish on COLUMN / DUCT (built obstacle) faces only where the face is PHYSICALLY
EXPOSED to a certified room site, following the room's own wall treatment by an owner method rule.

Exposure (exposure): a face is exposed to a site exactly where a one-sided boundary edge of that certified TS01 site
lies on it (the wall-face spans of class COLUMN_FACE / OBSTACLE_FACE). Every span length is attributed to the object
part segment(s) named in its sources; per segment: exposed length per site, hidden length = segment length - exposed.
An embedded / wall-buried / internal face is never a site edge, so it is hidden by construction AND listed as hidden.
Fail closed: a span of the object class with no object-part source (identity unresolved), or exposed > segment length.

Assignment (assign): the face takes the trades the room applies for its wall plane, under a rule that requires
PHYSICAL_EXPOSURE (and OWNER_PHYSICAL_AUTHORITY for a duct / built obstacle) and lists the room classes it covers;
outside the rule -> UNRESOLVED (never inferred). Skirting is never created here: it stays on the frozen contact path.
The physical class (COLUMN_FACE / OBSTACLE_FACE) is kept on every surface record; it never becomes WALL_FACE.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "EXPOSED_OBJECT_FINISH_POLICY_V1"
COLUMN_FACE, OBSTACLE_FACE = "COLUMN_FACE", "OBSTACLE_FACE"
EXPOSED, PARTIAL, HIDDEN = "EXPOSED", "PARTIALLY_EXPOSED", "HIDDEN"
INCLUDED, UNRESOLVED, NOT_APPLICABLE = "INCLUDED", "UNRESOLVED", "NOT_APPLICABLE"
TOL_M = 1e-6


def _r(v):
    return round(v, 6)


def exposure(segments: dict, spans_by_site: dict, face_class: str) -> dict:
    """segments: {segment_key: {"object": id, "length_m": L}}; spans_by_site: {site: [span]} with span
    {"class", "length_m", "sources", "geom"}. Returns per-segment exposure and the per-site exposed surfaces."""
    exp = {k: {} for k in segments}
    faces, errors = [], []
    for sid, spans in sorted(spans_by_site.items()):
        for sp in spans:
            if sp["class"] != face_class:
                continue
            own = sorted(s for s in sp["sources"] if s in segments)
            if len(own) != 1:
                errors.append({"site": sid, "span": sp, "error": "OBJECT_IDENTITY_UNRESOLVED" if not own else
                               "SPAN_ON_MORE_THAN_ONE_OBJECT_SEGMENT"})
                continue
            k = own[0]
            exp[k][sid] = exp[k].get(sid, 0.0) + sp["length_m"]
            faces.append({"site": sid, "class": face_class, "object": segments[k]["object"], "segment": k,
                          "length_m": _r(sp["length_m"]), "sources": sorted(sp["sources"]), "geom": sp.get("geom")})
    out = {}
    for k, seg in sorted(segments.items()):
        e = math.fsum(exp[k].values())
        hidden = seg["length_m"] - e
        if hidden < -TOL_M:
            errors.append({"segment": k, "error": "EXPOSED_LONGER_THAN_SEGMENT", "exposed_m": _r(e),
                           "length_m": seg["length_m"]})
        st = HIDDEN if e <= TOL_M else (EXPOSED if hidden <= TOL_M else PARTIAL)
        out[k] = {"object": seg["object"], "length_m": _r(seg["length_m"]),
                  "exposed_m": {s: _r(v) for s, v in sorted(exp[k].items())}, "exposed_total_m": _r(e),
                  "hidden_m": _r(max(hidden, 0.0)), "state": st}
    return {"policy": POLICY_ID, "face_class": face_class, "segments": out, "faces": faces, "errors": errors,
            "state": "PASS" if not errors else "FAIL"}


def assign(face_class: str, room_class: str, room_trades: list, rule: dict | None, *,
           owner_physical_authority: bool) -> dict:
    """Trades for an exposed object face in a room. rule: {"rule_id", "face_class", "requires": [...],
    "room_classes": [...], "follows": "ROOM_WALL_TRADES"}."""
    if not rule or rule.get("face_class") != face_class:
        return {"state": UNRESOLVED, "trades": [], "why": f"no finish rule for {face_class}"}
    if "OWNER_PHYSICAL_AUTHORITY" in rule.get("requires", ()) and not owner_physical_authority:
        return {"state": UNRESOLVED, "trades": [], "rule": rule["rule_id"],
                "why": "no owner physical authority for this object: no finish inferred"}
    if room_class not in rule.get("room_classes", ()):
        return {"state": UNRESOLVED, "trades": [], "rule": rule["rule_id"],
                "why": f"rule does not cover room class {room_class}"}
    if rule.get("follows") != "ROOM_WALL_TRADES":
        return {"state": UNRESOLVED, "trades": [], "rule": rule["rule_id"], "why": "rule states no trade source"}
    return {"state": INCLUDED, "trades": sorted(room_trades), "rule": rule["rule_id"],
            "why": "follows the room's wall treatment"}


def surfaces(faces: list, *, site: str, height_m, height_authority, assignment: dict) -> list:
    """Surface records (length x height) of the exposed faces of one site, physical class preserved."""
    if assignment["state"] != INCLUDED or height_m is None:
        return []
    return [{"class": f["class"], "site": site, "object": f["object"], "segment": f["segment"],
             "length_m": f["length_m"], "height_m": height_m, "height_authority": height_authority,
             "area_m2": _r(f["length_m"] * height_m), "trades": assignment["trades"], "rule": assignment["rule"],
             "sources": f["sources"], "geom": f["geom"]} for f in faces if f["site"] == site]


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "classes": [COLUMN_FACE, OBSTACLE_FACE],
           "exposure": "one-sided certified site-boundary spans attributed to the object's own part segments; hidden = "
                       "segment length - exposed (listed per segment)",
           "assignment": "the room's wall trades under a rule requiring PHYSICAL_EXPOSURE (+ OWNER_PHYSICAL_AUTHORITY "
                         "for a built obstacle) for the listed room classes; otherwise UNRESOLVED",
           "skirting": "never created here (frozen contact path only)",
           "never": ["a finish because an object is a column or duct", "a hidden / embedded / internal face",
                     "an obstacle finish without owner physical authority", "an object face merged into WALL_FACE",
                     "a duct rule applied to a room class it does not cover", "new skirting"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
