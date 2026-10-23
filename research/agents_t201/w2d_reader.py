"""T-201: minimal reader for the 2D vector stream (.w2d, WHIP! format) inside a DWF 6 package (any villa).

Why: an architect's DWF plot of the model space carries every sheet (elevations, sections, fence) as VECTOR geometry,
while the PDF set may be raster scans. Drawn geometry read here is CAD geometry (1 logical unit = 1 / Units scale
drawing units), never a raster scaling. The drawing's own note ("dimensions not to scale") still applies: a value read
here is DRAWING-CONFIRMED BY GEOMETRY only after it is bound to the opening, re-datumed on a level marker of the same
view, and checked against the current issue (see heads_from_geometry.py).

Reads: extended ASCII opcodes "( ... )" (Units transform kept), extended binary "{ ... }" (skipped), and the single-byte
opcodes seen in AutoCAD ePlot output: origin 'O', lines 0x0C / 'l', polylines 0x10 / 'p', polytriangles 0x14 / 't',
contours 0x0B / 'k', circles 0x12 / 'r', circular arcs 0x92, ellipses 'e', text 'x' / 0x18 (position + string), set
font 0x06, colour 'c' / 0x03, line weight 0x17, layer 0xAC, visibility 'V' / 'v', fill 'F' / 'f', object nodes 0x0E /
'n' / 'N', polymarkers 0x8C / 0x8D. Any other opcode raises W2DError with its offset: nothing is skipped silently.
Coordinates are relative to the running current point (16- or 32-bit), exactly as the format defines.

No drawing data is stored in the repository; the module reads a file path given at run time.
"""
from __future__ import annotations

import re
import struct
import zipfile
from pathlib import Path

__all__ = ["W2DError", "parse_w2d", "units_transform", "read_dwf_graphics", "to_model"]


class W2DError(ValueError):
    pass


def units_transform(header: bytes):
    """(sx, sy, ox, oy) from the first '(Units ...)' opcode: logical = s * drawing + o. None if absent."""
    m = re.search(rb"\(Units\s+'[^']*'\s*\(\(([-\d.eE+]+)\s+[-\d.eE+]+\s+[-\d.eE+]+\s+[-\d.eE+]+\)\s*"
                  rb"\([-\d.eE+]+\s+([-\d.eE+]+)\s+[-\d.eE+]+\s+[-\d.eE+]+\)\s*\([^)]*\)\s*"
                  rb"\(([-\d.eE+]+)\s+([-\d.eE+]+)", header)
    if not m:
        return None
    sx, sy, ox, oy = (float(v) for v in m.groups())
    if sx <= 0 or sy <= 0:
        raise W2DError("Units scale must be positive")
    return sx, sy, ox, oy


def to_model(p, tr):
    sx, sy, ox, oy = tr
    return ((p[0] - ox) / sx, (p[1] - oy) / sy)


def _string(d, i):
    while d[i] == 0x20:
        i += 1
    if d[i] == 0x27:                                   # quoted ASCII, backslash escapes
        j = i + 1
        while d[j] != 0x27:
            j += 2 if d[j] == 0x5C else 1
        return d[i + 1:j].decode("latin-1"), j + 1
    if d[i] == 0x7B:                                   # {int32 n, n UTF-16 chars}
        n = struct.unpack_from("<i", d, i + 1)[0]
        return d[i + 5:i + 5 + 2 * n].decode("utf-16-le", "replace"), i + 5 + 2 * n + 1
    j = i
    while d[j] not in b" ()":
        j += 1
    return d[i:j].decode("latin-1"), j


def parse_w2d(d: bytes):
    """Return {'polylines': [[(x, y), ...]], 'arcs': [...], 'texts': [(x, y, text, visible)], 'units': tr|None}
    in LOGICAL coordinates. Raises W2DError on an unknown opcode or a truncated stream."""
    i, n = 0, len(d)
    cx = cy = 0
    vis = True
    out = {"polylines": [], "arcs": [], "texts": [], "units": units_transform(d[:20000])}

    def cnt():
        nonlocal i
        c = d[i]
        i += 1
        if c == 0:
            c = struct.unpack_from("<H", d, i)[0] + 256
            i += 2
        return c

    def pts(k, wide):
        nonlocal i, cx, cy
        fmt, size = ("<ii", 8) if wide else ("<hh", 4)
        res = []
        for _ in range(k):
            dx, dy = struct.unpack_from(fmt, d, i)
            i += size
            cx += dx
            cy += dy
            res.append((cx, cy))
        return res

    try:
        while i < n:
            op = d[i]
            i += 1
            if op in b" \t\r\n":
                continue
            if op == 0x28:                                   # extended ASCII
                depth, q = 1, False
                while depth:
                    c = d[i]
                    i += 1
                    if q and c == 0x5C:
                        i += 1
                        continue
                    if c == 0x27:
                        q = not q
                    elif not q:
                        depth += (c == 0x28) - (c == 0x29)
                continue
            if op == 0x7B:                                   # extended binary: int32 size then payload
                i += 4 + struct.unpack_from("<i", d, i)[0]
                continue
            if op == 0x56:
                vis = True
            elif op == 0x76:
                vis = False
            elif op in (0x46, 0x66, 0x0E):
                pass
            elif op == 0x63:
                i += 1
            elif op in (0x03, 0x17, 0xAC, 0x4E):
                i += 4
            elif op == 0x6E:
                i += 2
            elif op == 0x4F:
                cx, cy = struct.unpack_from("<ii", d, i)
                i += 8
            elif op in (0x0C, 0x6C):
                out["polylines"].append(pts(2, op == 0x6C))
            elif op in (0x10, 0x70):
                k = cnt()
                out["polylines"].append(pts(k, op == 0x70))
            elif op in (0x14, 0x74, 0x8C, 0x8D):
                k = cnt()
                pts(k, op in (0x74, 0x8D))
            elif op in (0x0B, 0x6B):
                ks = [cnt() for _ in range(cnt())]
                for k in ks:
                    pts(k, op == 0x6B)
            elif op in (0x12, 0x72):
                c = pts(1, op == 0x72)[0]
                r = struct.unpack_from("<H" if op == 0x12 else "<I", d, i)[0]
                i += 2 if op == 0x12 else 4
                out["arcs"].append(("CIRCLE", c, r, 0, 65536))
            elif op == 0x92:
                c = pts(1, True)[0]
                r, a0, a1 = struct.unpack_from("<IHH", d, i)
                i += 8
                out["arcs"].append(("ARC", c, r, a0, a1))
            elif op == 0x65:
                c = pts(1, True)[0]
                a, b, s0, s1, tilt = struct.unpack_from("<IIHHH", d, i)
                i += 14
                out["arcs"].append(("ELLIPSE", c, (a, b, tilt), s0, s1))
            elif op == 0x06:                                 # set font: field mask, then the present fields
                mask = struct.unpack_from("<H", d, i)[0]
                i += 2
                if mask & 1:
                    _, i = _string(d, i)
                for bit, size in ((2, 1), (4, 1), (8, 1), (0x10, 1), (0x20, 4), (0x40, 2), (0x80, 2), (0x100, 2),
                                  (0x200, 2), (0x400, 4)):
                    if mask & bit:
                        i += size
            elif op in (0x78, 0x18):
                p = pts(1, True)[0]
                t, i = _string(d, i)
                if op == 0x18:                               # overscore, underscore, bounds, reserved
                    for _ in range(2):
                        if d[i] != 1:
                            raise W2DError(f"text score list not supported at {i}")
                        i += 1
                    i += 1 if d[i] == 1 else 32
                    if d[i] != 1:
                        raise W2DError(f"text reserved field not supported at {i}")
                    i += 1
                out["texts"].append((p[0], p[1], t, vis))
            else:
                raise W2DError(f"unknown opcode 0x{op:02x} at offset {i - 1}")
    except (IndexError, struct.error) as e:
        raise W2DError(f"truncated stream near offset {i}: {e}") from None
    return out


def read_dwf_graphics(path):
    """The '2d streaming graphics' streams of a DWF 6 package: [(member name, parsed)]."""
    p = Path(path)
    raw = p.read_bytes()
    if not raw.startswith(b"(DWF V06"):
        raise W2DError("not a DWF 6 package")
    res = []
    with zipfile.ZipFile(p) as z:
        for name in z.namelist():
            if not name.lower().endswith(".w2d"):
                continue
            d = z.read(name)
            if b"(Units" in d[:20000]:
                res.append((name, parse_w2d(d)))
    return res
