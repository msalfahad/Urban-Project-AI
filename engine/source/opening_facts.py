"""OPENING PHYSICAL CLASS FACTS (R8.17) - what ONE bound opening IS (a sliding glass door, a full-height glazed
screen, ...) and whether it reaches the floor, read from an owner / source physical fact.

The fact is an ordinary owner PHYSICAL fact (owner_facts: kind OPENING_CONSTRUCTION, part-bound, all or nothing);
this module only turns an APPLYING binding into trade-path floor-contact records keyed by the bound source entities
and the glazed occurrences they drive. It never creates geometry, never edits a closure, never reaches topology and
never generalises: an opening the fact does not bind keeps whatever authority it had (often none).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

from . import owner_claims as OC
from . import owner_facts as OF
from . import wall_contact_path as WC

POLICY_ID = "OPENING_PHYSICAL_CLASS_POLICY_V1"
KIND = "OPENING_CONSTRUCTION"
DOMAIN = "OPENING_PHYSICAL_CLASS"
ALLOWED_DOMAINS = (DOMAIN, OF.BLOCKER_CLASSIFICATION)


def contact_map(fact: OF.PhysicalFact, binding: dict) -> dict:
    """Floor-contact records for every source entity and glazed occurrence the fact binds (empty unless APPLIES)."""
    if fact.kind != KIND or binding.get("binding") != OC.APPLIES or OF.TOPOLOGY_ROLE in fact.allowed_domains:
        return {}
    st = fact.statement
    rec = WC.opening_contact(physical_class=st.get("physical_class"), contact=st.get("floor_contact"),
                             authority=fact.ref)
    out = {}
    for key, _fp, _reading in fact.parts:
        for k in (key, WC._entity(key), f"GLAZED|{key}", f"CLOSURE|GLAZED|{key}"):
            out[k] = rec
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "kind": KIND, "domains": list(ALLOWED_DOMAINS),
           "binding": "owner_facts.bind: revision + anchor + region + frame + every bound part fingerprint",
           "resolution": "physical class first (a door class is never a window); floor contact from the fact",
           "never": ["a topology role or closure edit", "an opening the fact does not bind", "a transfer to another "
                     "revision / project", "'all glazed openings are sliding doors'", "a quantity"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
