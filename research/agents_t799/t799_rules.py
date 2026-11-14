"""T-799 rules (every villa; research module, unwired). New rule version beside R-T788-3 (t788_rules.py, not edited).

R-T788-4 DOORS ARE BARRIERS FOR THE OUTDOOR RAY TEST (Checker F-V788-1, 2026-11-14): R-T788-3 calls a clip piece
  OUTDOOR when straight rays (16 directions, 40 m) from one interior point reach no barrier line (wall, column, window)
  in at least 2 directions. Door openings were not barriers, so an indoor piece facing two aligned door gaps (an
  interior door and an exterior door on the same axis, both sides) escapes in 2 rays and is dropped from its zone.
  A door leaf closes its opening: every door gap is a barrier. The door barrier is the closing chord of the opening
  (jamb to jamb) or the door block's own drawn geometry (leaf + swing), whichever the caller has; both cross the gap.
  `door_lines` is required: None = doors not read -> HELD (ValueError), never assumed absent; [] = a plan with no door.
  Only the barrier set changes (rays, length and the 2-escape threshold of R-T788-3 are kept). Adding barriers can only
  turn OUTDOOR into INDOOR, never the reverse, so an R-T788-3 result moves only where a door gap was the escape path.
"""
from __future__ import annotations

import importlib.util
import pathlib

_P = pathlib.Path(__file__).resolve().parents[1] / "agents_t788/t788_rules.py"
_s = importlib.util.spec_from_file_location("t788_rules", _P)
R3 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(R3)


def is_outdoor_v4(piece, barriers, door_lines, **kw):
    """R-T788-4: R-T788-3 enclosure test with the door gaps added to the barrier lines."""
    if door_lines is None:
        raise ValueError("door openings not read: enclosure unknown (HELD, never assumed indoor or outdoor)")
    return R3.is_outdoor(piece, list(barriers) + list(door_lines), **kw)


def split_outdoor_v4(face, region, barriers, door_lines):
    """R-T788-4: (indoor part, [outdoor pieces]) of face x region, doors as barriers."""
    from shapely.ops import unary_union

    part = face.intersection(region)
    pieces = [part] if part.geom_type == "Polygon" else [g for g in getattr(part, "geoms", []) if g.area > 0]
    indoor, outdoor = [], []
    for g in pieces:
        (outdoor if is_outdoor_v4(g, barriers, door_lines) else indoor).append(g)
    return unary_union(indoor), outdoor
