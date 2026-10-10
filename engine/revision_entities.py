"""E46 — entity identity across revisions. The layer E11 needs underneath it.

E11 (`engine.revision_delta`) already compares two BOQ snapshots keyed by item
id and reports the cost impact. It assumes the hard part is solved: that a line
in the new snapshot can be recognised as the same line as one in the old. This
module is that assumption, made explicit and testable one level down — at the
level of spaces, walls, openings and quantities, before any of them becomes a
BOQ line.

Project 23010 has exactly one analysed revision. The model is built now anyway,
because retro-fitting entity identity is how systems end up unable to answer
"what changed", and because one rule has to be in place BEFORE a second
revision arrives:

    AN ENTITY'S IDENTITY MUST NOT DEPEND ON LIST ORDER.

A space matched by its position in a list changes identity the moment a room is
inserted. Bathroom-03 must stay Bathroom-03 after a 100 mm wall move, and the
matcher must record WHICH evidence decided that, because a wrong match reports
a change that never happened.

WITH ONE REVISION THIS REPORTS "NO PRIOR REVISION AVAILABLE". It does not
fabricate a comparison and it does not report zero changes: zero changes and
nothing to compare look identical in a report and mean opposite things.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

UNCHANGED = "UNCHANGED"
ADDED = "ADDED"
REMOVED = "REMOVED"
GEOMETRY_CHANGED = "GEOMETRY_CHANGED"
SEMANTIC_CHANGED = "SEMANTIC_CHANGED"
RULE_CHANGED = "RULE_CHANGED"
SCOPE_CHANGED = "SCOPE_CHANGED"

CHANGE_KINDS = (UNCHANGED, ADDED, REMOVED, GEOMETRY_CHANGED, SEMANTIC_CHANGED,
                RULE_CHANGED, SCOPE_CHANGED)

# How the entity was matched. Recorded, because a match made on weak evidence
# is a change report nobody should trust.
BY_ID = "STABLE_ID"
BY_GEOMETRY = "GEOMETRY_WITHIN_TOLERANCE"
BY_SEMANTIC = "SEMANTIC_AND_LOCATION"
UNMATCHED = "UNMATCHED"

NO_PRIOR = "NO_PRIOR_REVISION_AVAILABLE"

# A space whose centroid moved less than this is the same room, moved.
GEOMETRY_MATCH_TOLERANCE_MM = 500.0
# An area change smaller than this is measurement noise, not a redesign.
AREA_NOISE_M2 = 0.05


class RevisionEntityError(RuntimeError):
    """A comparison was attempted that would have invented a baseline."""


@dataclass(frozen=True)
class EntityChange:
    entity_type: str
    entity_id: str
    change: str
    matched_by: str
    prior_id: str = ""
    detail: str = ""

    def record(self) -> dict:
        return {"entity_type": self.entity_type, "entity_id": self.entity_id,
                "change": self.change, "matched_by": self.matched_by,
                "prior_id": self.prior_id, "detail": self.detail}


@dataclass(frozen=True)
class QuantityDelta:
    quantity_id: str
    use: str
    unit: str
    old_value: float | None
    new_value: float | None

    @property
    def absolute_change(self) -> float | None:
        if self.old_value is None or self.new_value is None:
            return None
        return self.new_value - self.old_value

    @property
    def percentage_change(self) -> float | None:
        """None when there is nothing to divide by — never 0, never 100."""
        if self.old_value in (None, 0) or self.new_value is None:
            return None
        return (self.new_value - self.old_value) / self.old_value * 100

    def record(self) -> dict:
        return {"quantity_id": self.quantity_id, "use": self.use,
                "unit": self.unit, "old_value": self.old_value,
                "new_value": self.new_value,
                "absolute_change": self.absolute_change,
                "percentage_change": (
                    None if self.percentage_change is None
                    else round(self.percentage_change, 2))}


def match_spaces(prior, current, *,
                 tolerance_mm: float = GEOMETRY_MATCH_TOLERANCE_MM) -> dict:
    """Pair spaces across revisions: identity first, geometry second.

    Never by list position. Each pairing records the evidence it used so a
    reviewer can distrust a weak one.
    """
    prior_by_id = {s["space_id"]: s for s in prior}
    used: set[str] = set()
    out: dict[str, tuple[str, str]] = {}
    for s in current:
        sid = s["space_id"]
        if sid in prior_by_id:
            out[sid] = (sid, BY_ID)
            used.add(sid)
            continue
        best = None
        for p in prior:
            if p["space_id"] in used:
                continue
            if p.get("centroid_mm") is None or s.get("centroid_mm") is None:
                continue
            (ax, ay), (bx, by) = p["centroid_mm"], s["centroid_mm"]
            d = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
            if d <= tolerance_mm and (best is None or d < best[0]):
                best = (d, p["space_id"])
        if best is not None:
            out[sid] = (best[1], BY_GEOMETRY)
            used.add(best[1])
        else:
            out[sid] = ("", UNMATCHED)
    return out


def compare(prior_run: dict | None, current_run: dict) -> dict:
    """The entity delta, or an honest statement that there is no baseline."""
    if prior_run is None:
        return {
            "status": NO_PRIOR,
            "prior_revision": None,
            "current_revision": current_run.get("revision_id", ""),
            "entity_changes": [], "quantity_deltas": [],
            "why": ("only one revision of this drawing has been analysed. This "
                    "is NOT a report of zero changes — there is no baseline to "
                    "have changed from"),
        }

    prior_spaces = prior_run.get("spaces", [])
    current_spaces = current_run.get("spaces", [])
    matches = match_spaces(prior_spaces, current_spaces)
    prior_by_id = {s["space_id"]: s for s in prior_spaces}

    changes: list[EntityChange] = []
    for s in current_spaces:
        sid = s["space_id"]
        pid, how = matches.get(sid, ("", UNMATCHED))
        if how == UNMATCHED:
            changes.append(EntityChange("SPACE", sid, ADDED, UNMATCHED,
                                        detail="no counterpart in the prior run"))
            continue
        p = prior_by_id[pid]
        if p.get("scope") != s.get("scope"):
            changes.append(EntityChange(
                "SPACE", sid, SCOPE_CHANGED, how, pid,
                f"{p.get('scope')} -> {s.get('scope')}"))
        elif p.get("room_type") != s.get("room_type"):
            changes.append(EntityChange(
                "SPACE", sid, SEMANTIC_CHANGED, how, pid,
                f"{p.get('room_type')} -> {s.get('room_type')}"))
        elif (p.get("floor_area_m2") is not None
              and s.get("floor_area_m2") is not None
              and abs(p["floor_area_m2"] - s["floor_area_m2"]) > AREA_NOISE_M2):
            changes.append(EntityChange(
                "SPACE", sid, GEOMETRY_CHANGED, how, pid,
                f"{p['floor_area_m2']} -> {s['floor_area_m2']} m2"))
        else:
            changes.append(EntityChange("SPACE", sid, UNCHANGED, how, pid))

    matched = {pid for pid, how in matches.values() if how != UNMATCHED}
    for p in prior_spaces:
        if p["space_id"] not in matched:
            changes.append(EntityChange(
                "SPACE", p["space_id"], REMOVED, UNMATCHED,
                detail="present in the prior run, absent from this one"))

    prior_q = {q["quantity_id"]: q for q in prior_run.get("quantities", [])}
    deltas = [QuantityDelta(
        quantity_id=q["quantity_id"], use=q.get("use", ""),
        unit=q.get("unit", ""),
        old_value=None if prior_q.get(q["quantity_id"]) is None
        else prior_q[q["quantity_id"]].get("value"),
        new_value=q.get("value")) for q in current_run.get("quantities", [])]

    return {
        "status": "COMPARED",
        "prior_revision": prior_run.get("revision_id", ""),
        "current_revision": current_run.get("revision_id", ""),
        "entity_changes": [c.record() for c in changes],
        "quantity_deltas": [d.record() for d in deltas],
        "summary": dict(Counter(c.change for c in changes)),
        "matched_by": dict(Counter(c.matched_by for c in changes)),
    }
