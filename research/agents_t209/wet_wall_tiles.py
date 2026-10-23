"""T-209: wet-room wall tile m2 room by room, two methods side by side (research piece, unwired; NOT engine code).

Physical element (ENGINEERING_REASONING_STANDARD s.2.1): the porcelain / ceramic wall tile laid on the inner wall faces
of a wet room, from the finished floor to the underside of the decor (false) ceiling (owner Q-48 A, UP-FIN-WALL-001 full
height), less the openings that are physically not wall (UP-CER-005; Q-73 / T-175 full openings, subject to the
physical scope). Installed m2 only; tile pieces / boxes / waste are procurement and are not computed here.

  face_m      wall-face run of the room = walked contour less its open sides (no wall drawn: nothing to tile)
  gross       = face_m x H
  door        = width x min(head, H); a door head not printed and not covered by an approved fallback -> the
                deduction is a RANGE (0 .. width x H) and the net is HELD
  window      = width x max(0, min(head, H) - max(sill, 0)): only the part inside the tiled band [0, H] is deducted
                (a window wholly above the band deducts nothing; a sill / head not established -> HELD range)
  net         = gross - doors - windows
Any missing height, face length or opening datum keeps the quantity HELD; it never becomes 0.

Method A, OWNER MANUAL (G1, OWNER_RECONCILIATION_2026-10-20): H = floor-to-floor - 0.60 - 0.15 - 0.10 (Q-43 / Q-48 A),
  ASSUMED - OWNER-APPROVED; the door head 2.20 m where no drawing prints one (Q-55 C), ASSUMED - OWNER-APPROVED.
Method B, DRAWING-DERIVED: H = the room's own finished-floor-to-decor-ceiling height read from the drawings (here the
  T-128 r3 bounded value), HELD wherever the soffit datum over the room is not established.
Q-48 rough-sum convention (the hand sum in the Q-48 question text: "each door taken out over its width only", i.e. the
  wall over a door head not tiled) is computed beside, as a reconciliation column only: the physical over-door band is
  wall and is tiled (Q-73 / T-175: the deduction is the opening, not the full storey height).
"""
from __future__ import annotations

import math

DOOR_HEAD_FALLBACK_M = 2.20          # Q-55 C, UP knowledge 1.5.0 owner_reference_height_m (bathroom / internal PVC)
WALL_MORTAR_M = 0.02                 # Q-45 B (owner accepted, PROVISIONAL): wall mortar 2 cm, 1:4
OWNER_BAGS_PER_M3 = 8.0              # Q-45 B / G4: 8 x 50 kg bags per m3 of 1:4 mortar (owner purchasing method)
OWNER_SAND_PER_M3 = 1.10             # Q-45 B / G4: 1.10 m3 loose sand per m3 of 1:4 mortar
THEORY_BAGS_PER_M3 = 0.266 * 1440 / 50   # G4 comparison: 1.33 / 5 = 0.266 m3 cement x 1,440 kg/m3 / 50 kg = 7.661
THEORY_SAND_PER_M3 = 1.33 * 4 / 5        # G4 comparison: 1.064 m3
WASTE = 0.05                         # Q-09 / Q-45, G4: separate column, applied once, before rounding
ADHESIVE_M2_PER_BAG = 5.0            # Q-45 answer: 20 kg bag covers about 5 m2 of ceramic / porcelain

MAX_STOREY_H_M = 8.0                 # unit guard: a tile height above 8 m is a millimetre / centimetre input, refused
MAX_FACE_M = 500.0                   # unit guard on the wall-face run of one room
R4 = lambda v: None if v is None else round(v + 0.0, 4)  # noqa: E731


def window_band(width, sill, head, H):
    """m2 of one window inside the tiled band [0, H]; None when a datum is missing (never 0 for unknown)."""
    if width is None or sill is None or head is None or H is None:
        return None
    if head <= sill or width <= 0:
        raise ValueError("window head must be above its sill and the width positive")
    return width * max(0.0, min(head, H) - max(sill, 0.0))


def door_band(width, head, H):
    """m2 of one door / arch / doorway inside [0, H]; head None -> None (the caller makes a range)."""
    if width is None or H is None or head is None:
        return None
    return width * min(head, H)


def room_tile(face_m, H, doors, windows, open_sides_m=0.0):
    """One wet room, one height. doors: [{'w', 'head' (None = not printed), 'fallback' (bool: Q-55 C applies)}];
    windows: [{'w', 'sill', 'head'}] (above the room's finished floor). Returns gross / deductions / net (lo, hi) and a
    status; a missing face or height -> HELD with None values (never 0)."""
    if face_m is None or H is None:
        return dict(status='HELD', why='face length or tile height not established', gross=None, net_lo=None,
                    net_hi=None, doors=None, windows=None, open_sides_m=open_sides_m)
    if face_m < 0 or H <= 0:
        raise ValueError("face length must be >= 0 and the height > 0")
    if H > MAX_STOREY_H_M or face_m > MAX_FACE_M:
        raise ValueError("height or face length out of range for metres (a millimetre value?)")
    gross = face_m * H
    d_lo = d_hi = 0.0
    held = []
    for d in doors:
        head = d.get('head')
        if head is None and d.get('fallback'):
            head = DOOR_HEAD_FALLBACK_M
        a = door_band(d['w'], head, H)
        if a is None:
            held.append(f"opening {d.get('id', '?')} head not printed")
            d_lo += 0.0
            d_hi += d['w'] * H
        else:
            d_lo += a
            d_hi += a
    w_sum = 0.0
    w_unknown = 0.0
    for w in windows:
        a = window_band(w['w'], w.get('sill'), w.get('head'), H)
        if a is None:
            held.append(f"window {w.get('id', '?')} sill / head not established")
            w_unknown += w['w'] * H
        else:
            w_sum += a
    net_hi = gross - d_lo - w_sum                      # least deduction
    net_lo = gross - d_hi - w_sum - w_unknown          # full-band deduction for every unknown
    return dict(status='HELD' if held else 'OK', why='; '.join(held) or None, gross=R4(gross), doors_lo=R4(d_lo),
                doors_hi=R4(d_hi), windows=R4(w_sum), net_lo=R4(net_lo), net_hi=R4(net_hi), open_sides_m=open_sides_m)


def q48_rough(face_m, H, doors, windows):
    """Q-48 question-text convention: (face - door widths) x H - windows in the band. Reconciliation column only."""
    if face_m is None or H is None:
        return None
    w_sum = 0.0
    for w in windows:
        a = window_band(w['w'], w.get('sill'), w.get('head'), H)
        if a is None:
            return None
        w_sum += a
    return R4((face_m - sum(d['w'] for d in doors)) * H - w_sum)


def over_door_band(H, doors):
    """the wall over the door heads that the Q-48 rough convention leaves untiled: sum w x (H - head) (fallback heads)."""
    s = 0.0
    for d in doors:
        head = d.get('head') if d.get('head') is not None else (DOOR_HEAD_FALLBACK_M if d.get('fallback') else None)
        if head is None or H is None:
            return None
        s += d['w'] * max(0.0, H - head)
    return R4(s)


def materials(area_m2):
    """wall mortar and adhesive for a tiled wall area (all PROVISIONAL owner practice values, Q-45 B / G4)."""
    if area_m2 is None:
        return None
    m3 = area_m2 * WALL_MORTAR_M
    return dict(mortar_m3=R4(m3), mortar_m3_with_waste=R4(m3 * (1 + WASTE)),
                cement_bags_owner=R4(m3 * OWNER_BAGS_PER_M3), cement_bags_owner_with_waste=R4(m3 * (1 + WASTE) * OWNER_BAGS_PER_M3),
                sand_m3_owner=R4(m3 * OWNER_SAND_PER_M3), sand_m3_owner_with_waste=R4(m3 * (1 + WASTE) * OWNER_SAND_PER_M3),
                cement_bags_theory=R4(m3 * THEORY_BAGS_PER_M3), sand_m3_theory=R4(m3 * THEORY_SAND_PER_M3),
                adhesive_bags=R4(area_m2 / ADHESIVE_M2_PER_BAG))


def buy(x):
    """whole purchase units, rounded up once on a sum (never per room)."""
    return None if x is None else int(math.ceil(x - 1e-9))
