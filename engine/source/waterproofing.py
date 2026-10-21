"""WET-ROOM WATERPROOFING (R8.18) - its own path, never the skirting path.

  WATERPROOFING_FLOOR_M2   the wet-room floor area (the certified TS01 site area)
  WATERPROOFING_UPTURN_LM  the GROSS room perimeter: every one-sided boundary edge of the site - walls, columns,
                           door / sliding-door / glazed closures (doorways are NOT deducted), windows, internal
                           obstacle perimeters (holes, when included); interior stubs are not perimeter
  upturn height            a method parameter with its own authority (Urban: 0.15 m); the derived upturn m2 is
                           informational only
Independent of skirting, wall tile and marble (a threshold changes no waterproofing unless an explicit rule says so).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

from . import wall_contact_path as WC

POLICY_ID = "WATERPROOFING_POLICY_V1"
FLOOR, UPTURN = "WATERPROOFING_FLOOR_M2", "WATERPROOFING_UPTURN_LM"


def wet_room(edges, *, area_m2, u, upturn_height_m, upturn_authority, include_holes=True) -> dict:
    by = defaultdict(float)
    total = 0.0
    for e in edges:
        if e.get("hole") and not include_holes:
            continue
        c = WC.classify_v4(e)
        L = e["length"] * u
        by["HOLE_PERIMETER" if e.get("hole") else c] += L
        total += L
    ok = upturn_height_m is not None and bool(upturn_authority) and area_m2 is not None
    return {"policy": POLICY_ID, "state": "COMPUTED" if ok else "BLOCKED", FLOOR: round(area_m2, 6),
            UPTURN: round(total, 6), "upturn_height_m": upturn_height_m, "upturn_authority": upturn_authority,
            "upturn_m2_informational": round(total * upturn_height_m, 6) if ok else None,
            "perimeter_by_class_m": {k: round(v, 6) for k, v in sorted(by.items())},
            "doorways_deducted": False, "holes_included": include_holes}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "rows": [FLOOR, UPTURN], "floor": "the wet-room TS01 site area",
           "upturn_path": "the GROSS site boundary (doorways NOT deducted; holes included by default)",
           "never": ["the skirting path", "a doorway deduction", "a marble-threshold modification without an explicit "
                     "rule", "a perimeter from a room polygon outside the certified topology"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
