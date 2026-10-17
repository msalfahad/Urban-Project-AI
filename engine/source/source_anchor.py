"""SOURCE ANCHOR - CONTROLLED EXPORT IDENTITY (R8.20).

Compares two decoded DXF record sets (the current measurement DXF and a controlled owner re-export of the same DWG)
entity by entity: identity = source handle (+ block-instance path), compared on layer, entity type and geometry within
a stated tolerance. The anchor is IDENTICAL only when every entity of A has exactly one partner in B with equal layer /
type / geometry, and vice versa. Anything else lists the differences; it never 'mostly matches'.

The protocol record states what the owner does in AutoCAD (no edits; SAVEAS DXF + SAVEAS DWG in a format the pinned
decoder reads) and what must be recorded (build, timestamps, hashes) for the export to count.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "SOURCE_EXPORT_IDENTITY_POLICY_V1"
IDENTICAL, DIFFERENT = "IDENTICAL", "DIFFERENT"
PROTOCOL = {
    "steps": ["open the authoritative DWG in AutoCAD (record the AutoCAD product, version and build)",
              "make NO edit, no purge, no audit-fix, no regen-save of the source",
              "SAVEAS DXF (AutoCAD 2018 DXF, the same format as the current DXF) to a NEW file",
              "SAVEAS DWG in AutoCAD 2013 format (AC1027) to a NEW file (for the pinned libredwg K1 route)",
              "close WITHOUT saving the original",
              "record local timestamps of both exports",
              "compute SHA-256 of the source DWG (before and after: must be unchanged) and of both exports",
              "send the four hashes, the AutoCAD build and the two exported files"],
    "counts_only_if": ["the source DWG hash equals the anchored DWG hash e4babbc2ded1...",
                       "the source DWG hash is unchanged after the session",
                       "both exports carry the stated format headers ($ACADVER)"],
    "then": ["DXF identity: current DXF vs re-exported DXF, entity by entity (this policy)",
             "cross-route: K1 (pinned libredwg on the AC1027 DWG) vs K2 (ezdxf on the DXF) topology agreement"],
    "never": ["an edited or re-saved source", "an export by an unrecorded tool", "a partial match called identity"]}


def _key(e):
    return (e["handle"], tuple(e.get("instance_path") or ()))


def _geom_equal(a, b, tol):
    if a is None or b is None or len(a) != len(b):
        return a == b
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def compare(records_a: list, records_b: list, *, tol: float) -> dict:
    """records: [{"handle", "instance_path", "layer", "entity_type", "geometry": [floats]}]."""
    ia, ib = {}, {}
    dup = []
    for name, recs, idx in (("A", records_a, ia), ("B", records_b, ib)):
        for e in recs:
            k = _key(e)
            if k in idx:
                dup.append({"side": name, "key": [k[0], list(k[1])]})
            idx[k] = e
    only_a = sorted([k[0], list(k[1])] for k in set(ia) - set(ib))
    only_b = sorted([k[0], list(k[1])] for k in set(ib) - set(ia))
    changed = []
    for k in sorted(set(ia) & set(ib)):
        a, b = ia[k], ib[k]
        diff = [f for f in ("layer", "entity_type") if a.get(f) != b.get(f)]
        if not _geom_equal(a.get("geometry"), b.get("geometry"), tol):
            diff.append("geometry")
        if diff:
            changed.append({"key": [k[0], list(k[1])], "fields": diff})
    ok = not (only_a or only_b or changed or dup)
    return {"policy": POLICY_ID, "state": IDENTICAL if ok else DIFFERENT, "entities_a": len(ia), "entities_b": len(ib),
            "only_in_a": only_a, "only_in_b": only_b, "changed": changed, "duplicate_keys": dup, "tolerance": tol}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "identity": "handle + instance path; equal layer, entity type and geometry within "
                                              "tolerance; both directions", "protocol": PROTOCOL,
           "never": ["'mostly identical'", "identity by entity counts or bounding boxes", "a hash of a re-saved source"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
