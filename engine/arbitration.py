"""E1.2 §9 — A18 is a challenger, not the answer.

E1.1 withheld any candidate the frozen blind reading called open, even
where CAD had a coherent ring and nothing else disagreed. That is safe
and it is incomplete: it makes one witness final.

Neither witness is final here. A18 read a sheet and can misread it; CAD
closes rings and a ring closes as happily round a counter as round a
wall. So a disagreement is ARBITRATED on evidence:

    exact CAD entity and interval evidence
    portal and door evidence
    the cold visual V1 observation and the V2 challenge

and only a conflict that the evidence does not settle blocks release for
good.
"""

from __future__ import annotations

import hashlib

from engine import visual_challenger as vc

MODEL = "A18_IS_A_CHALLENGER_NOT_GROUND_TRUTH_V1"

A18_CONFIRMED = "A18_CONFIRMED"
A18_CHALLENGED = "A18_CHALLENGED_BY_CAD_AND_VISUAL"
CAD_CHALLENGED = "CAD_CHALLENGED_BY_A18_AND_VISUAL"
BOTH_PARTIALLY_CORRECT = "BOTH_PARTIALLY_CORRECT"
UNRESOLVED = "UNRESOLVED"
STATES = (A18_CONFIRMED, A18_CHALLENGED, CAD_CHALLENGED,
          BOTH_PARTIALLY_CORRECT, UNRESOLVED)

ONLY_UNRESOLVED_BLOCKS_FOREVER = (
    "a resolved disagreement is a result, not a blocker. Where the CAD "
    "entity evidence and the cold visual pass agree against the frozen "
    "reading, the frozen reading is what was wrong, and saying so is the "
    "point of arbitrating rather than deferring")

NEITHER_WITNESS_IS_FINAL = (
    "A18 read a printed sheet and can misread it. CAD closes rings and a "
    "ring closes as happily round a counter as round a wall. The evidence "
    "decides, and where it does not, the conflict stands as UNRESOLVED")


def model_hash() -> str:
    parts = [MODEL] + list(STATES)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def arbitrate(*, a18_says_open, cad_open, cad_has_portal,
              portal_evidence=(), ambiguous_band_on_ring=(),
              v1_open_sides=None, v2_statuses=()) -> dict:
    """Resolve a topology disagreement on evidence, or leave it open."""
    v2 = set(v2_statuses or ())
    notes, state = [], UNRESOLVED

    visual_says_open = None
    if vc.OPEN_SIDE_FALSELY_CLOSED in v2:
        visual_says_open = True
        notes.append("the cold visual challenge says a side the drawing "
                     "leaves open has been closed")
    elif vc.WALL_FALSELY_REMOVED in v2:
        visual_says_open = False
        notes.append("the cold visual challenge says a drawn wall is "
                     "missing from the ring")
    elif v1_open_sides is not None:
        visual_says_open = bool(v1_open_sides)
        notes.append(f"the cold source-only pass reported "
                     f"{len(v1_open_sides or [])} open side(s)")

    if a18_says_open is None:
        state = UNRESOLVED
        notes.append("the frozen reading states no topology for this space")
    elif a18_says_open == cad_open:
        state = A18_CONFIRMED
        notes.append("the frozen reading and the CAD ring agree")
    elif a18_says_open and not cad_open:
        if ambiguous_band_on_ring:
            state = CAD_CHALLENGED
            notes.append("the ring is closed by a band CAD itself cannot "
                         "tell from a counter or a bar, so the frozen "
                         "reading of an open side is not contradicted")
        elif visual_says_open is True:
            state = CAD_CHALLENGED
            notes.append("the visual pass agrees with the frozen reading "
                         "against the CAD ring")
        elif visual_says_open is False:
            state = A18_CHALLENGED
            notes.append("the CAD ring is material and the visual pass "
                         "sees enclosure, so the frozen reading of an open "
                         "side is what was wrong")
        elif cad_has_portal and portal_evidence:
            state = BOTH_PARTIALLY_CORRECT
            notes.append("the side is broken by an opening with evidence: "
                         "the frozen reading saw the opening, the CAD ring "
                         "saw the wall it is cut into")
        else:
            state = UNRESOLVED
            notes.append("nothing independent settles which reading is "
                         "right")
    else:
        if visual_says_open is False:
            state = A18_CONFIRMED
            notes.append("the frozen reading called it enclosed and the "
                         "visual pass sees enclosure; the open edge in the "
                         "CAD ring is a gap in the drawing")
        else:
            state = UNRESOLVED
            notes.append("the frozen reading called it enclosed and the "
                         "CAD ring is not closed by drawn material")

    return {
        "ARBITRATION_STATE": state,
        "a18_says_open": a18_says_open,
        "cad_open": cad_open,
        "cad_has_portal": cad_has_portal,
        "portal_evidence": list(portal_evidence),
        "ambiguous_band_on_ring": sorted(set(ambiguous_band_on_ring)),
        "visual_says_open": visual_says_open,
        "v2_statuses": sorted(v2),
        "notes": notes,
        "blocks_release": state == UNRESOLVED,
        "only_unresolved_blocks_forever": ONLY_UNRESOLVED_BLOCKS_FOREVER,
        "neither_witness_is_final": NEITHER_WITNESS_IS_FINAL,
    }


def frozen_parameters() -> dict:
    return {"MODEL": MODEL, "STATES": list(STATES),
            "why": {"neither_witness_is_final": NEITHER_WITNESS_IS_FINAL,
                    "only_unresolved_blocks_forever":
                        ONLY_UNRESOLVED_BLOCKS_FOREVER}}
