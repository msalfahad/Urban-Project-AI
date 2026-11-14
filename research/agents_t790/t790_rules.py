"""T-790 rules (every villa; research module, unwired).

R-T790-1 WALL VIEW LINES: ARCH.WALL_PANEL (m2) and ARCH.WALL_VOLUME (m3) are geometry views of the SAME wall group that
  MAS.BLOCK bills (V3.0.26 R-MAS-PANEL-SAME-1): panel m2 = the MAS.BLOCK m2 of the same element id, volume = panel x the
  group thickness; label and basis are the MAS.BLOCK line's. They are REFERENCE lines (no B9 family in the master
  registry): never added to the Blockwork subtotal, so block m2 is counted once. A HELD / EXCLUDED block line gives a
  HELD / EXCLUDED view, never 0.
R-T790-2 COURSE LEVELS (owner Q-77): a mesh strip / sharmat level sits on every 3rd course; course k top =
  first_bed + k x block_h + (k - 1) x joint; level j = course 3j; it exists where block stands above it
  (level + joint < top). Black mortared 0.19 + 0.01 (module 0.20, first bed 0.01 -> levels 0.60 j); white AAC family A
  0.25 + 0.001 thin bed, first bed 0.01 (T-362 R-T362-1 band low corner: levels 0.762, 1.515, ...).
R-T790-3 STRIP ON A PIECE: per level, strip = piece length - every opening cut at that level: below the head the
  opening width; inside the lintel band [head, head + lintel depth) the lintel length (width + both bearings); at or
  above the lintel top nothing (R-T355-6). Sharmat at a junction = the number of levels on the block beside the column.
"""
from __future__ import annotations

BLACK = (0.19, 0.01, 0.01)      # block height, joint, first bed (m)
WHITE_A = (0.25, 0.001, 0.01)


def view_lines(block_net, block_class, t):
    """R-T790-1: (panel m2, volume m3) of a wall group from its MAS.BLOCK line."""
    if block_class != "RELEASED":
        return None                      # stays HELD / EXCLUDED with its block line (never 0)
    if t is None or not (0.05 <= t <= 0.60):
        raise ValueError("thickness missing or not in metres")
    if block_net is None or block_net <= 0:
        raise ValueError("a released block line must carry a positive m2")
    return block_net, block_net * t


def levels(top, course=BLACK):
    """R-T790-2: mesh / tie levels (m above the wall base) on block of the given top."""
    if top is None or top <= 0:
        raise ValueError("block top unknown: HELD, never 0")
    if top > 20:
        raise ValueError("top looks like mm, not m")
    h, j, b = course
    out, k = [], 3
    while True:
        z = b + k * h + (k - 1) * j
        if z + j >= top - 1e-9:
            return out
        out.append(round(z, 6))
        k += 3


def strip(length, top, openings=(), course=BLACK):
    """R-T790-3: net strip (m) on one block piece of the given top; openings = (width, sill, head, lintel_length,
    lintel_depth), heights from the wall base (a door has sill 0)."""
    if length is None or length <= 0:
        raise ValueError("piece length missing")
    tot = 0.0
    for z in levels(top, course):
        cut = 0.0
        for w, sill, head, ll, ld in openings:
            if ll < w:
                raise ValueError("lintel shorter than its opening")
            if sill <= z < head - 1e-9:
                cut += w
            elif head <= z < head + ld - 1e-9:
                cut += ll
        if cut > length + 1e-9:
            raise ValueError("openings longer than the piece")
        tot += length - cut
    return tot


def ties(top, course=BLACK):
    return len(levels(top, course))
