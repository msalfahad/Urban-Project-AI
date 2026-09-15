"""E58 — the control set is chosen by RULE, and frozen before the answer.

A control picked after seeing the error is not a control. The previous round
drifted into exactly that: the rooms reported were the ones the algorithm had
happened to produce a cycle for, which makes the resulting percentages a
statement about the selection rather than about the engine.

So the set is defined here, in committed code, by a rule that cannot see a
single measurement:

    the LOWEST-NUMBERED IN-SCOPE space of each required room type

Nothing about faces, cycles, areas or errors enters the choice. Run the rule,
freeze the list, then measure — and a control that produced no geometry at all
stays in the list as a row saying so, because dropping it would quietly turn
the set back into "the ones that worked".

The required types are a coverage requirement, not a convenience: a bathroom
is small and wet, a bedroom is large and simple, a store is small and awkward,
and an engine that works on only one of them has not been tested.
"""

from __future__ import annotations

from dataclasses import dataclass

# What the control set must cover. Named types, not named rooms.
REQUIRED_TYPES = ("BATHROOM", "BEDROOM", "STORE")

# Rooms that may never be controls, with the reason each is disqualified.
# These are STATED DEFECTS, established in earlier rounds — not rooms that
# measured badly this round.
EXCLUDED = {
    "WSH-01": ("region identity FAILED: the associated region is the hatched "
               "shaft beside the wash room, not the wash floor"),
    "BED-04": ("physical topology MERGED: the printed 1600 x 3000 bathroom "
               "never separates from the bedroom"),
    "STA-01": ("stairs must not be measured as floor"),
}

SELECTION_RULE = ("the lowest-numbered IN_SCOPE space of each required room "
                  "type, excluding spaces with a stated prior defect")


class ControlError(RuntimeError):
    """A control set was chosen from results instead of from a rule."""


@dataclass(frozen=True)
class Control:
    space_id: str
    room_type: str
    why_selected: str

    def record(self) -> dict:
        return {"space_id": self.space_id, "room_type": self.room_type,
                "why_selected": self.why_selected}


def select(spaces, *, required=REQUIRED_TYPES) -> list[Control]:
    """Apply the rule. `spaces` is the space map — no geometry, no results.

    The signature is the guarantee: this function is never given an area, an
    error, a face or a cycle, so it cannot choose by one.
    """
    for s in spaces:
        for forbidden in ("area_m2", "error_pct", "face_id", "iou"):
            if forbidden in s:
                raise ControlError(
                    f"the control selector was handed {forbidden!r}. A "
                    "control chosen after seeing a measurement is not a "
                    "control — it is the measurement choosing itself")
    out = []
    for rt in required:
        pool = sorted(
            (s for s in spaces
             if s.get("room_type") == rt
             and s.get("scope") == "IN_SCOPE"
             and s["space_id"] not in EXCLUDED),
            key=lambda s: s["space_id"])
        if not pool:
            continue
        out.append(Control(
            pool[0]["space_id"], rt,
            f"lowest-numbered IN_SCOPE {rt} of {len(pool)} available "
            f"({', '.join(s['space_id'] for s in pool)})"))
    return out


def manifest(controls, *, excluded=EXCLUDED) -> dict:
    """The frozen set, stated before any comparison runs."""
    return {
        "selection_rule": SELECTION_RULE,
        "required_room_types": list(REQUIRED_TYPES),
        "controls": [c.record() for c in controls],
        "covered_types": sorted({c.room_type for c in controls}),
        "missing_types": sorted(set(REQUIRED_TYPES)
                                - {c.room_type for c in controls}),
        "excluded_with_reasons": dict(excluded),
        "frozen_before_comparison": True,
        "note": ("chosen from the space map alone. No area, error, face or "
                 "cycle took part in the selection, and a control that "
                 "produced no geometry stays in the set as a row saying so"),
    }
