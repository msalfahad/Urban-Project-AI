"""OBJECT FOOTPRINT AUTHORITY (RC1) - may a trade measure through the objects that stand on a site?

resolve() takes the site's space class, the trade, the proven non-partition objects inside the site (with their
object class) and the accepted footprint policies (owner facts / Urban rules, each with an explicit scope: trade,
space classes, object classes, treatment). A site is RESOLVED only when ONE policy's scope covers the trade, the
site class and EVERY object class present; otherwise it is UNRESOLVED and the result names each object and, for
every policy, the exact scope reason it does not apply. Nothing is assumed: no 'included by convention', no zero.
A site with no objects needs no footprint authority (NOT_REQUIRED).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "OBJECT_FOOTPRINT_AUTHORITY_V1"
RESOLVED, UNRESOLVED, NOT_REQUIRED, CONFLICT = "RESOLVED", "UNRESOLVED", "NOT_REQUIRED", "CONFLICT"
ANY = "ANY_NON_PARTITION_OBJECT"


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def _why_not(p, *, trade, space_class, object_classes):
    why = []
    if p["trade"] != trade:
        why.append(f"trade {p['trade']} is not {trade}")
    if space_class not in p["space_classes"]:
        why.append(f"space classes {p['space_classes']} do not include {space_class}")
    oc = set(p["object_classes"])
    if ANY not in oc and not set(object_classes) <= oc:
        why.append(f"object classes {sorted(oc)} do not cover {sorted(set(object_classes) - oc)}")
    for x in p.get("excludes") or ():
        if x.get("space_class") == space_class or x.get("trade_scope") == trade and x.get("space_class") in (
                None, space_class):
            why.append(f"explicitly excluded: {x.get('text')}")
    return why


def resolve(*, site: str, space_class: str, trade: str, objects: list, policies: list) -> dict:
    """objects: [{"key", "object_class", "layer", "geometry"}]; policies: [{"policy_id", "trade", "space_classes",
    "object_classes", "treatment", "excludes"}]."""
    if not objects:
        return {"site": site, "trade": trade, "state": NOT_REQUIRED, "objects": [], "policy": None,
                "treatment": None, "rejected": []}
    classes = sorted({o["object_class"] for o in objects})
    ok, rejected = [], []
    for p in policies:
        why = _why_not(p, trade=trade, space_class=space_class, object_classes=classes)
        (rejected.append({"policy": p["policy_id"], "why": why}) if why else ok.append(p))
    treatments = sorted({p["treatment"] for p in ok})
    state = RESOLVED if len(treatments) == 1 else CONFLICT if len(treatments) > 1 else UNRESOLVED
    return {"site": site, "trade": trade, "space_class": space_class, "state": state, "objects": objects,
            "object_classes": classes, "policy": [p["policy_id"] for p in ok] or None,
            "treatment": treatments[0] if state == RESOLVED else None, "rejected": rejected}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID,
           "rule": "RESOLVED only when one accepted policy covers trade + space class + every object class present",
           "never": ["a topology convention as authority", "a dry-room fact transferred to a wet / service room",
                     "a silent zero or a silent full-room assumption"]}
    rec["digest"] = _digest(rec)
    return rec
