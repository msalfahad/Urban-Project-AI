"""BOQ EVIDENCE MAPPING (R8.20) - which release blockers can change a quantity.

A row's release blockers are classified before the BOQ report status is derived:
  RELEASE_ONLY        the quantity is complete; the blocker gates release, not the number
                      (SOURCE_ANCHOR, SHADOW_ONLY)
  QUANTITY_AFFECTING  an open authority / evidence gap that could change the number (OBJECT_FOOTPRINT_IMPLICIT, ...)
  UNKNOWN blocker     treated as QUANTITY_AFFECTING (fail closed)
A row with any quantity-affecting blocker is never COMPUTED_SHADOW_COMPLETE: its unresolved list carries the blocker,
so BOQ_REPORT_LAYER_V1 shows AUTHORISED_SUBTOTAL.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "BOQ_EVIDENCE_MAPPING_V1"
RELEASE_ONLY, QUANTITY_AFFECTING = "RELEASE_ONLY", "QUANTITY_AFFECTING"
RELEASE_ONLY_PREFIXES = ("SOURCE_ANCHOR", "SHADOW_ONLY")


def classify(blocker: str) -> str:
    head = str(blocker).split(":", 1)[0].strip()
    return RELEASE_ONLY if head in RELEASE_ONLY_PREFIXES else QUANTITY_AFFECTING


def unresolved(blockers, contributors=()) -> list:
    """The unresolved list of an evidence row: its unresolved contributors + every quantity-affecting blocker."""
    return list(contributors) + [{"blocker": b, "effect": QUANTITY_AFFECTING} for b in blockers or ()
                                 if classify(b) == QUANTITY_AFFECTING]


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "release_only": list(RELEASE_ONLY_PREFIXES),
           "rule": "any other blocker is QUANTITY_AFFECTING (fail closed) and keeps the row out of "
                   "COMPUTED_SHADOW_COMPLETE",
           "never": ["a quantity-affecting gap shown as a complete quantity", "an unknown blocker treated as "
                     "release-only"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
