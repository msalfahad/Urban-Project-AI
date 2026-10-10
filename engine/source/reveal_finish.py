"""REVEAL OWNERSHIP + FINISH (R8.18) - a reveal is a PHYSICAL surface owned by ONE room side; its FINISH is a separate
decision.

Ownership (frame_split): the frame / leaf / track plane(s) inside the wall split the wall depth; each side owns the
depth between its face and the nearest frame line; a frame flush with a face leaves that side NO reveal; a reveal face
the source does not draw on its side (a cavity) is UNRESOLVED, never invented. No frame evidence -> the whole depth
is UNRESOLVED (unless a method states the side).

Finish states (finish_state):
  PORCELAIN_EXPLICIT / OTHER_EXPLICIT  only with an explicit project / source instruction for that reveal
  PLASTER_AND_PAINT                    the owning side is a painted dry surface and nothing replaces the paint
  PLASTER_DEFAULT                      otherwise (the owner default); a wet / service owner never gets paint by default
  UNRESOLVED                           ownership or surface not established (that reveal only)

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "REVEAL_FINISH_POLICY_V1"
PLASTER_DEFAULT, PLASTER_AND_PAINT = "PLASTER_DEFAULT", "PLASTER_AND_PAINT"
PORCELAIN_EXPLICIT, OTHER_EXPLICIT, UNRESOLVED = "PORCELAIN_EXPLICIT", "OTHER_EXPLICIT", "UNRESOLVED"
STATES = (PLASTER_DEFAULT, PLASTER_AND_PAINT, PORCELAIN_EXPLICIT, OTHER_EXPLICIT, UNRESOLVED)
TRADES = {PLASTER_DEFAULT: ("PLASTER",), PLASTER_AND_PAINT: ("PLASTER", "PAINT"), PORCELAIN_EXPLICIT: ("PORCELAIN",),
          OTHER_EXPLICIT: (), UNRESOLVED: ()}


def frame_split(depth_m, frame_offsets_m, *, side_a, side_b, eps=1e-6) -> dict:
    """Depth owned by each side: frame offsets are measured from side A's face (0 .. depth). Empty -> UNRESOLVED."""
    if not frame_offsets_m:
        return {side_a: None, side_b: None, "state": UNRESOLVED, "why": "no frame / leaf / track position in source"}
    lo, hi = min(frame_offsets_m), max(frame_offsets_m)
    a, b = max(0.0, lo), max(0.0, depth_m - hi)
    return {side_a: round(a, 6) if a > eps else 0.0, side_b: round(b, 6) if b > eps else 0.0, "state": "ESTABLISHED",
            "frame_offsets_m": sorted(frame_offsets_m)}


def finish_state(*, ownership_established, owner_painted_dry, explicit=None) -> str:
    if not ownership_established:
        return UNRESOLVED
    if explicit == "PORCELAIN":
        return PORCELAIN_EXPLICIT
    if explicit:
        return OTHER_EXPLICIT
    return PLASTER_AND_PAINT if owner_painted_dry else PLASTER_DEFAULT


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "states": list(STATES), "trades": {k: list(v) for k, v in TRADES.items()},
           "ownership": "frame / leaf / track plane splits the depth; flush -> no reveal on that side; an undrawn reveal "
                        "face -> UNRESOLVED; no frame evidence -> UNRESOLVED",
           "default": "PLASTER (owner method URBAN-REVEAL-FINISH-METHOD@v1); porcelain only explicit; paint only on a "
                      "painted dry owner",
           "never": ["porcelain because an adjacent room is wet", "paint invented in a wet / service room",
                     "one reveal in two room finishes", "a reveal surface the source does not show",
                     "the sill as a reveal"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
