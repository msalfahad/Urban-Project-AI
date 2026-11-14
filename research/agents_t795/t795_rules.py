"""T-795 rules (every villa; research module, unwired).

PHYSICAL ELEMENT: the cut edge of the wall tiling round a door / doorway / arch opening on a TILED face (wet room,
kitchen, laundry, pantry). The tile band runs from F.F.L. to the tile top T (owner 13 Nov: 3.00 m in every wet room);
an opening of head H inside the band leaves two jamb edges of min(H, T) and, when H < T, one head edge of the opening
width W. A door between two tiled rooms has the edge on BOTH faces (one count per tiled face).

R-T795-1 DOOR-OPENING TILE EDGE: lm per tiled face = 2 x min(H, T) + (W if H < T else 0).
  H: the opening table (OPENING_TABLE_V1: printed / schedule / drawing read), else the company door head 2.20 (Q-55 C,
  owner 2026-11-13 'head = nearest printed else 2.20'); W: the opening table, else the measured door face width.
  Missing W, H or T -> HELD (raise, never 0). The physical edge is carried whether or not a frame / architrave is later
  fitted over it: whether it is covered, mitred or profiled is the edge FORM (designer item, T-368 UP-CER-006 / 007),
  not the edge length. Supersedes the T-368 / T-771 HELD 0 .. perimeter range (FRAME_DETAIL_NOT_DRAWN), which made the
  frame question decide the length.
R-T795-2 HELD RANGE TO POINT: a HELD space / floor part whose low equals its high, or whose only open question is
  answered by the drawing at the cut plane (nothing drawn on wall / balustrade layers across it), is carried as its
  measured plan area.
"""
from __future__ import annotations

DEFAULT_DOOR_HEAD_M = 2.20          # Q-55 C / owner 2026-11-13 company default
WET_TILE_TOP_M = 3.00               # owner 2026-11-13: wall tiles 3.00 m from F.F.L. in every wet room
MAX_OPENING_M = 6.0                 # a single internal door / arch above 6 m wide or high is a units error


def door_edge_lm(width_m, head_m, tile_top_m):
    """R-T795-1: (total, jambs, head) lm of the tile edge on ONE tiled face of one opening."""
    for name, v in (("width", width_m), ("head", head_m), ("tile top", tile_top_m)):
        if v is None:
            raise ValueError(f"{name} missing: HELD, never 0")
        if not (0 < v <= MAX_OPENING_M):
            raise ValueError(f"{name} {v} not in metres")
    jambs = 2 * min(head_m, tile_top_m)
    head = width_m if head_m < tile_top_m else 0.0
    return round(jambs + head, 4), round(jambs, 4), round(head, 4)


def faces_total(faces, tile_top_m=WET_TILE_TOP_M):
    """sum of R-T795-1 over [{'room', 'opening', 'W', 'H'}] (one entry per tiled face); returns (total, jambs, heads)."""
    seen = set()
    tot = jb = hd = 0.0
    for f in faces:
        key = (f["room"], f["opening"])
        if key in seen:
            raise ValueError(f"face counted twice: {key}")
        seen.add(key)
        t, j, h = door_edge_lm(f["W"], f["H"], tile_top_m)
        tot, jb, hd = tot + t, jb + j, hd + h
    return round(tot, 4), round(jb, 4), round(hd, 4)


def range_to_point(low, high, cut_plane_clear):
    """R-T795-2: a HELD [low, high] becomes high when low == high or the cut plane shows nothing across it."""
    if low is None or high is None:
        raise ValueError("range bound missing: HELD")
    if high < low:
        raise ValueError("range reversed")
    if abs(high - low) < 1e-9 or cut_plane_clear:
        return high
    raise ValueError("range open and the cut plane does not settle it: HELD")
