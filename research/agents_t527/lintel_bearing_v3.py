"""LINTEL_BEARING_V3 (T-527, Checker finding F-C-T519-1): a lintel end that runs towards a CURVED BAY reads the DRAWN
masonry end (the curved wall's own face arcs), not the chord MASONRY_CENTRELINE_V2 constructs. Research only; successor
of research/agents_t519/lintel_bearing_v2.py (V2, imported read-only and left unchanged: its linear tolerance, leading-
edge rule and columns-first stopper are kept as they are).

Physical element. A curved (bay) wall leaves a straight wall band through a drawn opening of the band: the bay's
interior (the room enlarged by the bay) and the bay's own glazed sectors. The masonry the lintel can bear on is the band's
built material up to where the drawn bay boundary cuts it ACROSS THE FULL WALL THICKNESS. The curved wall is drawn as two
concentric WALL-layer face arcs (r_in, r_out) about one centre; inside r_in is the bay interior (no wall), between r_in
and r_out is the curved wall itself (masonry where the arc is drawn on a WALL layer, glazing where a WINDOW-layer arc of
the same centre spans that angle).

Why V2 is wrong there. V2 removes, from the band, a rectangle whose ends are the points where the bay's CENTRELINE circle
meets the band CENTRELINE (stretch 'CURVED_GLAZED_BAY ... (CENTRELINE_MEETING)'). That chord point is a construction:
nothing is drawn there. On the development villa the band's far face runs on, drawn, to the inner face arc, 0.100 m
beyond the chord point (W18 END: V2 0.478 m, drawn 0.578 m; the drawn face line ends exactly at the arc crossing).

V3 rule (every villa; provenance F-C-T519-1, T-527):
  1. Each V2 stretch bridged by CURVED_GLAZED_BAY is matched to exactly one drawn bay: a centre carrying at least two
     concentric WALL-role arcs (1 mm centre tolerance) whose inner circle cuts the band within the stretch +- MATCH_M.
     r_in = the smallest, r_out = the largest WALL-role radius of that centre.
  2. The bay's open region = disk(r_in) + every annular sector [r_in, r_out] spanned by a WINDOW-role arc of the same
     centre. V3 masonry = V2 masonry with the chord rectangle given back to the band (minus columns / other gaps) and the
     band's part of the open region removed (a gap removes masonry from its OWN band only, as in T-516).
  3. The reach and the stopper are V2's (linear 0.5 mm tolerance; columns first). A probe slice that meets the bay's open
     region is stopper END_OF_MASONRY with id CURVED_BAY:<stretch> (the drawn end of the masonry), so the state logic of
     T-516 (R-T516-1) is unchanged.
  4. No drawn bay found for a CURVED_GLAZED_BAY stretch (no concentric WALL arcs, two candidate centres, or a centre whose
     inner circle does not cut the band): every end whose V2 reach stops at that stretch is HELD by name
     (CURVED_BAY_NO_DRAWN_END): never the chord value, never the 0.40 minimum, never 0.
The tolerance never lengthens the reach and a zero-area touch (an arc tangent to a face) does not stop it (V2's hairline
rule): the reach ends where the open region begins across the full thickness.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t519"))
import lintel_bearing_v2 as V2  # noqa: E402  (read only)

VERSION = "LINTEL_BEARING_V3"
RULE_ID = "R-T527-1"
CENTRE_TOL_M = 0.001
MATCH_M = 0.50
QUAD_SEGS = 1024          # disk polygon: sagitta r (1 - cos(pi / 4096)) < 0.6 micrometre at r = 2 m
CURVED = "CURVED_GLAZED_BAY"
NO_DRAWN_END = "CURVED_BAY_NO_DRAWN_END"


class BearingV3Error(ValueError):
    pass


def _metres(x, where):
    if x is None or not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x < 0:
        raise BearingV3Error(f"{where}: {x!r} is not a length in metres")
    return float(x)


def arc_groups(arcs):
    """arcs: [{'c': (x, y) m, 'r': m, 'role': 'WALL'|'WINDOW'|..., 'a0': rad, 'a1': rad (CCW sweep a0 -> a1)}].
    -> [{'c', 'wall_r': sorted radii, 'window': [(a0, a1, r)]}] grouped by centre (CENTRE_TOL_M)."""
    groups = []
    for a in arcs:
        if a.get("role") not in ("WALL", "WINDOW"):
            continue
        r = _metres(a.get("r"), "arc radius")
        g = next((g for g in groups if math.dist(g["c"], a["c"]) <= CENTRE_TOL_M), None)
        if g is None:
            g = {"c": tuple(a["c"]), "wall_r": [], "window": []}
            groups.append(g)
        if a["role"] == "WALL":
            if all(abs(r - x) > CENTRE_TOL_M for x in g["wall_r"]):
                g["wall_r"].append(r)
        else:
            g["window"].append((float(a["a0"]), float(a["a1"]), r))
    for g in groups:
        g["wall_r"].sort()
    return groups


def sector(c, r0, r1, a0, a1, n=256):
    """annular sector between radii r0 < r1, CCW from a0 to a1 (radians)."""
    sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
    k = max(8, int(n * sweep / (2 * math.pi)) + 1)
    outer = [(c[0] + r1 * math.cos(a0 + sweep * i / k), c[1] + r1 * math.sin(a0 + sweep * i / k)) for i in range(k + 1)]
    inner = [(c[0] + r0 * math.cos(a0 + sweep * i / k), c[1] + r0 * math.sin(a0 + sweep * i / k)) for i in range(k, -1, -1)]
    return Polygon(outer + inner).buffer(0)


def match_bay(groups, band_rect, chord_rect):
    """the one drawn bay of a CURVED_GLAZED_BAY stretch -> (group, open_region) or (None, why)."""
    window = chord_rect.buffer(MATCH_M, cap_style=2, join_style=2)
    hits = []
    for g in groups:
        if len(g["wall_r"]) < 2:
            continue
        r_in = g["wall_r"][0]
        disk = Point(g["c"]).buffer(r_in, quad_segs=QUAD_SEGS)
        cut = disk.intersection(band_rect)
        if cut.area > 1e-8 and cut.intersects(window):
            hits.append((g, disk))
    if len(hits) != 1:
        return None, (f"{len(hits)} drawn bay centres (concentric WALL face arcs) cut the band at this stretch: "
                      f"the masonry end is not drawn unambiguously")
    g, disk = hits[0]
    r_in, r_out = g["wall_r"][0], g["wall_r"][-1]
    region = unary_union([disk] + [sector(g["c"], r_in, r_out, a0, a1) for a0, a1, _r in g["window"]])
    return g, region


def masonry_v3(M2, band, band_rect, chord_rect, region, columns, other_gaps_of_band):
    """V2 masonry with the chord rectangle given back to its band and the band's part of the drawn open region removed."""
    give_back = band_rect.intersection(chord_rect)
    if other_gaps_of_band:
        give_back = give_back.difference(unary_union(other_gaps_of_band))
    if columns:
        give_back = give_back.difference(unary_union(columns))
    return unary_union([M2, give_back]).difference(band_rect.intersection(region))


def face_crossings(group, a, ux, uy, half):
    """s (along the band from a) where the inner face circle cuts each band face n = -half, +half: drawn evidence."""
    cx, cy = group["c"]
    s_c = (cx - a[0]) * ux + (cy - a[1]) * uy
    n_c = -(cx - a[0]) * uy + (cy - a[1]) * ux
    r = group["wall_r"][0]
    out = {}
    for name, n in (("face_minus", -half), ("face_plus", half)):
        d = r * r - (n - n_c) ** 2
        out[name] = None if d < 0 else (s_c - math.sqrt(d), s_c + math.sqrt(d))
    return out


def reach_v3(M3, a, ux, uy, jamb, sign, half, columns, gaps, bays):
    """-> (e, capped, stopper, stopper_id). bays: [(stretch_id, region)]. V2's reach; stopper columns first, then the
    bay's open region (END_OF_MASONRY, CURVED_BAY:<id>), then the remaining gaps."""
    e, capped = V2.reach(M3, a, ux, uy, jamb, sign, half)
    # V2's 0.5 mm lateral inset lengthens the reach at an OBLIQUE boundary (an arc meets the face at an angle: inset x
    # its cotangent, 0.33 mm on the fixture); a drawn bay ends the masonry where its open region first meets the FULL
    # thickness strip, so the reach is capped there (the tolerance never lengthens the reach)
    for _sid, region in bays:
        s0, s1 = sorted((jamb, jamb + sign * e))
        piece = V2.strip(a, ux, uy, s0, s1, half).intersection(region)
        if not piece.is_empty and piece.area > 1e-12:
            pts = [c for g in getattr(piece, "geoms", [piece]) if hasattr(g, "exterior") for c in g.exterior.coords]
            first = min(((x - a[0]) * ux + (y - a[1]) * uy - jamb) * sign for x, y in pts)
            e, capped = max(0.0, min(e, first)), False
    if capped:
        return e, True, "SEARCH_LIMIT", ""
    s0, s1 = sorted((jamb + sign * e, jamb + sign * (e + V2.PROBE_M)))
    probe = V2.strip(a, ux, uy, s0, s1, half - V2.INSET)
    if columns and probe.intersection(unary_union(columns)).area > 1e-12:
        return e, False, "COLUMN", ""
    for sid, region in bays:
        if probe.intersection(region).area > 1e-12:
            return e, False, "END_OF_MASONRY", f"CURVED_BAY:{sid}"
    stop, gid = V2.stopper(e, False, a, ux, uy, jamb, sign, half, [], gaps)
    return e, False, stop, gid
