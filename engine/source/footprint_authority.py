"""OBJECT FOOTPRINT AUTHORITY (RC1; V2 at RC1 final) - may a trade measure through the objects that stand on a site?

identify() first applies OBJECT IDENTITY facts: an owner / specification fact may re-class named source objects
(e.g. FIXTURE-layer lines identified as a counter = LATER_INSTALLED_CABINETRY). It applies only to the exact keys it
names and only when the object's observed role is one the fact accepts; the observed role is kept as evidence.
Nothing is re-classed by shape or layer alone.

resolve() takes the site's space class, the trade, the proven non-partition objects inside the site (with their
object class) and the accepted footprint policies (owner facts / Urban rules, each with an explicit scope: trade,
space classes, object classes, treatment). A site is RESOLVED only when ONE policy's scope covers the trade, the
site class and EVERY object class present; otherwise it is UNRESOLVED and the result names each object and, for
every policy, the exact scope reason it does not apply. Nothing is assumed: no 'included by convention', no zero.
A site with no objects needs no footprint authority (NOT_REQUIRED). V2: a policy may list EXCLUDED object classes
(physical built obstacles such as a masonry plinth, a curb, a shaft): any such object present rejects the policy, so
a sequencing method can never carry a finish through built construction.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "OBJECT_FOOTPRINT_AUTHORITY_V2"
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
    built = set(object_classes) & set(p.get("excluded_object_classes") or ())
    if built:
        why.append(f"object classes {sorted(built)} are built obstacles this policy never covers")
    if ANY not in oc and not set(object_classes) <= oc:
        why.append(f"object classes {sorted(oc)} do not cover {sorted(set(object_classes) - oc)}")
    for x in p.get("excludes") or ():
        if x.get("space_class") == space_class or x.get("trade_scope") == trade and x.get("space_class") in (
                None, space_class):
            why.append(f"explicitly excluded: {x.get('text')}")
    return why


def identify(objects: list, identity_facts: list) -> list:
    """identity_facts: [{"fact_id", "object_keys", "accepts_roles", "object_class"}] -> objects with object_class
    replaced where a fact names the key AND accepts the observed role; 'observed_class' and 'identity_authority' kept."""
    out = []
    for o in objects:
        f = next((f for f in identity_facts if o["key"] in set(f["object_keys"]) and
                  o["object_class"] in set(f["accepts_roles"])), None)
        out.append(dict(o, observed_class=o["object_class"], object_class=f["object_class"],
                        identity_authority=f["fact_id"]) if f else dict(o))
    return out


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
           "rule": "RESOLVED only when an accepted policy covers trade + space class + every object class present and "
                   "no object is an excluded built-obstacle class; identity facts re-class only the exact keys they "
                   "name, and only from an accepted observed role",
           "never": ["a topology convention as authority", "a dry-room fact transferred to a wet / service room",
                     "a silent zero or a silent full-room assumption", "cabinetry inferred from shape or layer",
                     "a finish carried through a built obstacle"]}
    rec["digest"] = _digest(rec)
    return rec
