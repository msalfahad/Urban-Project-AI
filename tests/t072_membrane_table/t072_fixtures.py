"""T-072 synthetic areas (not any client project): rooms given in drawing units (mm or m), turned into waterproofed
areas through the engine's own Phase 2B-2 feature builder and built by waterproofing_system.build_area(v26=True),
exactly as tests/m9_p2b5/install_engine.py does, with the drawing unit as a parameter. Every expected value of the
tests is written by hand in test_membrane_table.py; this file holds none."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests" / "m9_p2b2")]

import p2b2_fixtures as F                                     # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402
from engine.source import wp_geometry as WG                   # noqa: E402


def rect(x, y):
    return [(0, 0), (x, 0), (x, y), (0, y)]


def transform(poly, *, deg=0.0, mirror=False, dx=0.0, dy=0.0):
    """rotate by deg about the origin, mirror in the y axis first if asked, then shift."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = []
    for x, y in poly:
        if mirror:
            x = -x
        out.append((x * c - y * s + dx, x * s + y * c + dy))
    if mirror:
        out.reverse()                                          # keep the ring's turning sense
    return out


def area(poly, *, unit=1e-3, room_id="A1", floor="GF", name_en=None, codes=("BATHROOM",), scope="WET", doors=(),
         holes=(), mirrored=False):
    """doors: {"id", "edge", "t0", "t1", "depth", "other_side"} in drawing units along the ring edge (for a
    mirrored ring the edge index is that of the reversed ring)."""
    ring = [(x * unit, y * unit) for x, y in poly]
    hs = [[(x * unit, y * unit) for x, y in h] for h in holes]
    gaps = [(d["edge"], d["t0"] * unit, d["t1"] * unit, "DOOR", d["id"]) for d in doors]
    feats = F.walls(ring, gaps)
    for h in hs:
        feats += F.walls(h)
    pieces = [{"opening_id": d["id"], "width_m": (d["t1"] - d["t0"]) * unit, "depth_m": d["depth"] * unit}
              for d in doors]
    doorways = [dict(p, other_side=d["other_side"]) for p, d in zip(pieces, doors)]
    rm = {"room_id": room_id, "floor": floor, "name_en": name_en or room_id, "codes": list(codes), "polygon_m": ring,
          "hole_polygons_m": hs, "polygon": list(poly), "hole_polygons": [list(h) for h in holes]}
    net = abs(WG.signed_area(ring)) - sum(abs(WG.signed_area(h)) for h in hs)
    with K.using("1.1.0"):
        a = WS.make_area(rm, feats, scope=scope, net_m2=net, continuation_pieces=pieces, doorways=doorways,
                         ents={}, unit_m=unit, keep_segments=True)
        return WS.build_area(a, F.resolver(), v26=True)


def plans(areas):
    with K.using("1.1.0"):
        return WS.cutting_plan(areas, exact=True, cut_ids=True)
