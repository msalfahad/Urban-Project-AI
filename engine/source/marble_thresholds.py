"""MARBLE THRESHOLDS (R8.15) - a door threshold whose whole strip is a separate MARBLE_THRESHOLD trade element.

Authority, in order (never inferred from text alone, never from a photograph's dimensions):
  EXPLICIT_PROJECT_FACT   an applying owner physical fact (THRESHOLD_FINISH_CONSTRUCTION) bound to the door
  URBAN_METHOD_RULE       a versioned owner method rule: either side of the door has an authoritative ROOM TYPE in
                          the rule's applicability list (the room-type map entry must carry this trade in scope)
  -                       otherwise no marble: the floor-transition rules apply
Geometry comes ONLY from the established threshold OPENING_SITE: width = the face-closure length (the doorway
opening between the jamb caps), depth = the separation of the two face closures, plan area = the site area
(door_transition checks width x depth). Unresolved geometry blocks the marble quantity.
A rule's rise (e.g. 20 mm) is a VERTICAL elevation attribute above the adjoining finished floor - never a plan
dimension, a depth or a volume. A function such as WATER_CONTAINMENT_BARRIER is recorded intent, never a hydraulic,
slope, drainage or waterproofing inference. No rate, no price.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

POLICY_ID = "MARBLE_THRESHOLD_POLICY_V1"
TRADE = "MARBLE_THRESHOLD"
EXPLICIT = "EXPLICIT_PROJECT_FACT"
RULE = "URBAN_METHOD_RULE"
APPLIES, NOT_APPLICABLE, TYPE_UNRESOLVED = "RULE_APPLIES", "RULE_NOT_APPLICABLE", "ROOM_TYPE_UNRESOLVED"
COMPUTED, BLOCKED_GEOMETRY = "MARBLE_COMPUTED", "MARBLE_BLOCKED_GEOMETRY"
NOT_STATED = "NOT_STATED"


@dataclass(frozen=True)
class MarbleRule:
    rule_id: str
    version: int
    authority: tuple
    applies_to: tuple                  # owner ROOM TYPES
    rise_mm: float | None
    function: str | None
    measurement: dict = field(default_factory=dict)
    never: tuple = ()

    @property
    def ref(self):
        return f"{self.rule_id}@v{self.version}"


def rule_from_record(rec: dict) -> MarbleRule:
    m = rec["measurement"]
    return MarbleRule(rec["rule_id"], int(rec["version"]), tuple(rec["authority"]), tuple(rec["applicability"]),
                      m.get("rise_mm"), rec.get("function"), dict(m), tuple(rec.get("never", ())))


def rule_evidence(rule: MarbleRule, side_types: dict) -> dict:
    """side_types: {"A": room type or None, "B": ...} from a trade-scoped room-type map (None = no authoritative
    type). The rule applies when either side is an applicable type; when no side is and a side is unresolved, the
    answer is ROOM_TYPE_UNRESOLVED (fail closed: no marble, no silent porcelain either)."""
    hit = sorted(k for k, t in side_types.items() if t in rule.applies_to)
    if hit:
        return {"state": APPLIES, "kind": RULE, "ref": rule.ref, "sides": hit,
                "room_types": {k: side_types[k] for k in hit}, "rise_mm": rule.rise_mm, "function": rule.function}
    if any(t is None for t in side_types.values()):
        return {"state": TYPE_UNRESOLVED, "kind": RULE, "ref": rule.ref}
    return {"state": NOT_APPLICABLE, "kind": RULE, "ref": rule.ref}


def explicit_evidence(fact_ref: str, statement: dict) -> dict:
    return {"state": APPLIES, "kind": EXPLICIT, "ref": fact_ref,
            "rise_mm": statement.get("rise_mm", NOT_STATED), "function": statement.get("function"),
            "scope_side": statement.get("scope_side")}


def choose(explicit, rule_ev) -> dict | None:
    """Explicit project evidence first; the rule second; otherwise None."""
    if explicit is not None:
        return dict(explicit, corroborating_rule=rule_ev["ref"] if rule_ev and rule_ev["state"] == APPLIES else None)
    if rule_ev is not None and rule_ev["state"] == APPLIES:
        return rule_ev
    return None


def record(threshold_id: str, alloc: dict, evidence: dict, *, unit_to_mm: float) -> dict:
    """The MARBLE_THRESHOLD trade record from a door_transition allocation made WITH this evidence."""
    p = alloc["plane"]
    if alloc["state"] != "MARBLE_THRESHOLD_EXPLICIT":
        return {"threshold": threshold_id, "state": BLOCKED_GEOMETRY, "allocation_state": alloc["state"],
                "authority": evidence, "trade": TRADE}
    w_mm, d_mm = p["width"] * unit_to_mm, p["thickness"] * unit_to_mm
    area = alloc["regions"][0]["area"] * (unit_to_mm / 1000) ** 2
    return {"threshold": threshold_id, "state": COMPUTED, "trade": TRADE,
            "authority_kind": evidence["kind"], "authority": evidence["ref"],
            "corroborating_rule": evidence.get("corroborating_rule"),
            "clear_width_mm": round(w_mm, 3), "clear_width_basis": "face-closure length = the doorway opening "
                                                                   "between the jamb caps (source)",
            "depth_mm": round(d_mm, 3), "depth_basis": "separation of the two face closures = wall thickness "
                                                       "at the doorway (source)",
            "plan_area_m2": round(area, 6), "length_lm": round(w_mm / 1000, 6),
            "width_x_depth_m2": round(w_mm * d_mm / 1e6, 6),
            "vertical_rise_mm": evidence.get("rise_mm") if evidence.get("rise_mm") is not None else NOT_STATED,
            "rise_is": "VERTICAL elevation above the adjoining finished floor (never a plan dimension)",
            "function": evidence.get("function"),
            "water_containment": evidence.get("function") == "WATER_CONTAINMENT_BARRIER",
            "counted_once": True, "never": ["a price or rate", "a volume", "a waterproofing / slope / drain change"]}


def quantities(records) -> dict:
    ok = [r for r in records if r["state"] == COMPUTED]
    return {"MARBLE_THRESHOLD_PLAN_AREA_M2": round(math.fsum(r["plan_area_m2"] for r in ok), 6),
            "MARBLE_THRESHOLD_LENGTH_LM": round(math.fsum(r["length_lm"] for r in ok), 6),
            "count": len(ok), "blocked": [r["threshold"] for r in records if r["state"] != COMPUTED]}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "trade": TRADE, "authority_order": [EXPLICIT, RULE],
           "rule_states": [APPLIES, NOT_APPLICABLE, TYPE_UNRESOLVED], "record_states": [COMPUTED, BLOCKED_GEOMETRY],
           "geometry": "the threshold OPENING_SITE only: width = face-closure length, depth = face separation, area = "
                       "site area", "rise": "vertical attribute only",
           "never": ["marble from text alone", "dimensions from a photograph", "a rise as a plan depth",
                     "a universal horizontal depth", "a half-tile contribution inside a marble strip",
                     "a waterproofing / slope / drainage inference", "a price"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
