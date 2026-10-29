"""T-323: a slab HATCH is not the slab PANEL (any villa). Research code, NOT engine code, not wired.

Physical element: a suspended slab panel is the plate between the faces of the members that carry it (beam / column /
wall faces) and any free slab edge (a cantilever tip, an opening edge). A hatch on a slab plan is a REGION MARKER
drawn over that panel (legend: 'Sunken slab.', 'Cantilever portion.', ...). The drafter stops the hatch pattern where
an annotation sits (a slab-tag circle, a bar label frame, a beam mark): the hatch boundary then follows the
annotation, not the concrete. The concrete does not stop there.

So every piece of a hatch's outer boundary is classified (UP-WALL-GEOM-001: geometry from drawn entities):

  MEMBER_FACE     the piece lies on a drawn member face (beam / column / wall line)            -> panel edge
  FREE_EDGE       the piece lies on a drawn slab-edge line that is not a member face            -> panel edge
  ANNOTATION_CUT  the piece lies on (or inside) an annotation's drawn extent (circle, frame)    -> NOT a panel edge
  UNEXPLAINED     none of the above                                                             -> panel HELD

and the panel is rebuilt from the member faces (the faces polygonised from the drawn member / edge lines, given by
the caller), never from the hatch boundary. The residual (panel area - hatch region area) is split into the part
under annotations (named per annotation) and the rest (named by the caller, or reported UNNAMED).

Refusals (ERS s.2 - s.3; never a silent number):
  - an ANNOTATION_CUT piece used as a free (step / riser / edge-form) edge -> HatchEdgeError;
  - a hatch whose boundary has ANNOTATION_CUT / UNEXPLAINED pieces and no member face that covers it -> the panel is
    HELD (area None), never the hatch area and never 0;
  - coordinates that are not metres (a 3 x 4 m panel given in mm reads as 1.2e7 m2) -> HatchEdgeError.

Hatch region = the union of its region loops; islands holding an annotation are NOT deducted (T-213 rule (a), reused
by citation, research/agents_t213/sunken_panels.py). No drawing data is stored here: geometry comes from the caller
(a private reader or a synthetic fixture).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

__all__ = ["HatchEdgeError", "CLASSES", "PANEL_EDGE_CLASSES", "Classified", "region_of", "classify_boundary",
           "rebuild_panel", "free_edge_length", "check_metres"]

CLASSES = ("MEMBER_FACE", "FREE_EDGE", "ANNOTATION_CUT", "UNEXPLAINED")
PANEL_EDGE_CLASSES = ("MEMBER_FACE", "FREE_EDGE")
AREA_EPS = 1e-6
SIN_PARALLEL = math.sin(math.radians(5.0))   # a face piece runs along its drawn segment within 5 degrees
MAX_PANEL_M2 = 2000.0          # one slab hatch above this is a unit slip (mm read as m), refused


class HatchEdgeError(ValueError):
    pass


def check_metres(loops):
    """Refuse coordinates that cannot be metres: a single slab hatch region above MAX_PANEL_M2."""
    for lp in loops:
        if len(lp) >= 3 and Polygon(lp).buffer(0).area > MAX_PANEL_M2:
            raise HatchEdgeError("hatch loop above %.0f m2: coordinates are not metres (mm given as m?)" % MAX_PANEL_M2)


def _poly(pts):
    p = Polygon(pts)
    if not p.is_valid:
        p = p.buffer(0)
    if p.is_empty or p.area <= AREA_EPS:
        raise HatchEdgeError("degenerate hatch loop")
    return p


def region_of(loops, touch_tol=0.02):
    """(region polygon with islands filled, [island polygons]). T-213 rule: the largest loop seeds the region, a loop
    that only touches it (no shared area) is another region part (a hatch split by an annotation arc), a loop that
    overlaps it is an island."""
    if not loops:
        raise HatchEdgeError("no boundary loop")
    check_metres(loops)
    polys = sorted((_poly(lp) for lp in loops), key=lambda p: -p.area)
    region, pending = [polys[0]], polys[1:]
    changed = True
    while changed:
        changed = False
        for p in list(pending):
            u = unary_union(region)
            if u.intersection(p).area <= AREA_EPS and u.distance(p) <= touch_tol:
                region.append(p)
                pending.remove(p)
                changed = True
    u = unary_union(region)
    if u.geom_type != "Polygon":       # a drafting seam between touching parts: close it (corner fillets < 1e-4 m2)
        u = u.buffer(touch_tol / 2).buffer(-touch_tol / 2)
    islands = []
    for p in pending:
        if u.intersection(p).area <= AREA_EPS:
            raise HatchEdgeError("a loop lies apart from the hatch region (two regions in one hatch?)")
        islands.append(p)
    if u.geom_type != "Polygon":
        raise HatchEdgeError("hatch region parts do not form one region")
    return Polygon(u.exterior), islands, len(region)


@dataclass
class Classified:
    region: Polygon
    lengths: dict                                  # class -> m
    pieces: list = field(default_factory=list)     # (class, length m, detail)
    annotations_hit: dict = field(default_factory=dict)   # annotation label -> m of boundary on it
    islands: int = 0
    region_loops: int = 1

    @property
    def perimeter(self):
        return self.region.exterior.length

    @property
    def is_panel_outline(self):
        """True only when every boundary piece is a member face or a free edge (the hatch IS the panel)."""
        return self.lengths["ANNOTATION_CUT"] <= 1e-6 and self.lengths["UNEXPLAINED"] <= 1e-6


def _pieces(ring, piece_m):
    cs = list(ring.coords)
    for a, b in zip(cs, cs[1:]):
        L = math.dist(a, b)
        if L <= 1e-9:          # a repeated vertex (numerical zero-length segment) is no piece
            continue
        n = max(1, int(math.ceil(L / piece_m)))
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            yield p0, p1, L / n


def _segments(lines):
    """[(segment LineString, unit dx, unit dy)] of every straight piece of the given lines."""
    out = []
    for ln in lines:
        cs = list(ln.coords)
        for a, b in zip(cs, cs[1:]):
            L = math.dist(a, b)
            if L > 1e-9:
                out.append((LineString([a, b]), (b[0] - a[0]) / L, (b[1] - a[1]) / L))
    return out


def classify_boundary(loops, *, member_lines, free_lines=(), annotations=(), tol=0.02, piece_m=0.05):
    """member_lines / free_lines: [LineString or point lists] (metres); annotations: [(label, shapely geometry)] =
    each annotation's DRAWN extent (a circle as a polygon, a text frame as a box). Each boundary piece is tested at its
    midpoint and its two ends (all three must agree for a face class): member face first, then free edge, then on /
    inside an annotation extent, else UNEXPLAINED. A face class also needs the piece to run along the nearest drawn
    segment (within 5 degrees): an annotation arc that leaves a member face is not that face for its first tol metres."""
    region, islands, nparts = region_of(loops, tol)
    mls = [l if isinstance(l, LineString) else LineString(l) for l in member_lines]
    fls = [l if isinstance(l, LineString) else LineString(l) for l in free_lines]
    mem = (unary_union(mls), _segments(mls)) if mls else None
    fre = (unary_union(fls), _segments(fls)) if fls else None
    anns = [(lab, g) for lab, g in annotations]
    lengths = {c: 0.0 for c in CLASSES}
    pieces, hit = [], {}

    def on(lines, pts):
        """All three points within tol of the lines AND the piece runs ALONG the nearest drawn segment (a curve
        leaving a face at right angles is not that face for its first tol metres)."""
        if lines is None:
            return False
        geom, segs = lines
        if not all(geom.distance(Point(p)) <= tol for p in pts):
            return False
        mid = Point(pts[1])
        dx, dy = pts[2][0] - pts[0][0], pts[2][1] - pts[0][1]
        n = math.hypot(dx, dy)
        near = min(segs, key=lambda sg: sg[0].distance(mid))
        return n > 0 and abs(dx * near[2] - dy * near[1]) / n <= SIN_PARALLEL

    for p0, p1, L in _pieces(region.exterior, piece_m):
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        pts = (p0, mid, p1)
        if on(mem, pts):
            c, det = "MEMBER_FACE", ""
        elif on(fre, pts):
            c, det = "FREE_EDGE", ""
        else:
            lab = next((lab for lab, g in anns if g.buffer(tol).contains(Point(mid))), None)
            c, det = ("ANNOTATION_CUT", lab) if lab is not None else ("UNEXPLAINED", "")
            if lab is not None:
                hit[lab] = hit.get(lab, 0.0) + L
        lengths[c] += L
        if pieces and pieces[-1][0] == c and pieces[-1][2] == det:
            pieces[-1] = (c, pieces[-1][1] + L, det)
        else:
            pieces.append((c, L, det))
    return Classified(region, lengths, pieces, hit, len(islands), nparts)


def rebuild_panel(classified, faces, *, annotations=(), min_share=0.5, tol=0.02):
    """The panel = the union of the member faces (polygons from the drawn member / edge lines) that the hatch region
    covers by at least `min_share` of the face area. Returns a dict:
      status      DRAWING-CONFIRMED (the panel is closed by drawn faces) or HELD (no face closes it)
      area_m2 / perimeter_m      the panel (None when HELD: never the hatch area, never 0)
      hatch_m2 / residual_m2     the hatch region and panel - hatch
      residual_annotation_m2     panel area the hatch leaves out inside each annotation extent
      outside_annotation_m2      hatch area beyond the panel inside each annotation extent (a notch redrawn by hand
                                 around a tag circle can sit off the member face)
      residual_annotation_net_m2 the net of the two, over the union of the annotation extents
      residual_other_m2          residual - that net (the caller names it; never silently absorbed)"""
    reg = classified.region
    chosen = [f for f in faces if f.area > AREA_EPS and f.intersection(reg).area >= min_share * f.area]
    hosts = [f for f in faces if f.area > AREA_EPS and f not in chosen and f.intersection(reg).area > 1e-4]
    out = {"hatch_m2": reg.area, "hatch_perimeter_m": reg.exterior.length, "faces": len(chosen),
           "host_faces": [(f.area, f.intersection(reg).area) for f in hosts]}
    if not chosen:
        why = ("the hatch marks a PORTION of a larger drawn face (a division inside one member or panel), not a "
               "panel" if hosts else "no drawn member face closes the hatch region (panel left open)")
        out.update(status="HELD", area_m2=None, perimeter_m=None, residual_m2=None,
                   residual_annotation_m2={}, outside_annotation_m2={}, residual_annotation_net_m2=None,
                   residual_other_m2=None, why=why)
        return out
    panel = unary_union(chosen)
    if panel.geom_type != "Polygon":
        panel = panel.buffer(tol / 2).buffer(-tol / 2)
    if panel.geom_type != "Polygon":
        out.update(status="HELD", area_m2=None, perimeter_m=None, residual_m2=None,
                   residual_annotation_m2={}, outside_annotation_m2={}, residual_annotation_net_m2=None,
                   residual_other_m2=None,
                   why="the faces under the hatch do not form one panel")
        return out
    panel = Polygon(panel.exterior)
    gap, over = panel.difference(reg), reg.difference(panel)      # panel not hatched / hatch beyond the panel
    per_ann, per_over, zones = {}, {}, []
    for lab, g in annotations:
        z = g.buffer(tol)
        a, b = gap.intersection(z).area, over.intersection(z).area
        if a > AREA_EPS:
            per_ann[lab] = a
        if b > AREA_EPS:
            per_over[lab] = b
        if a > AREA_EPS or b > AREA_EPS:
            zones.append(z)
    zone = unary_union(zones) if zones else None
    ann_gap = gap.intersection(zone).area if zone is not None else 0.0
    ann_over = over.intersection(zone).area if zone is not None else 0.0
    out.update(status="DRAWING-CONFIRMED", area_m2=panel.area, perimeter_m=panel.exterior.length,
               residual_m2=panel.area - reg.area,
               residual_annotation_m2=per_ann,            # panel area the hatch leaves out, under each annotation
               outside_annotation_m2=per_over,            # hatch area beyond the panel, under each annotation
               residual_annotation_net_m2=ann_gap - ann_over,
               residual_other_m2=(panel.area - reg.area) - (ann_gap - ann_over),
               outside_panel_m2=over.area, panel=panel)
    return out


def free_edge_length(classified, use_classes):
    """The length of hatch boundary a caller wants to treat as FREE slab edge (a step riser, an edge form). An
    ANNOTATION_CUT or UNEXPLAINED piece is never a slab edge: asking for it is refused."""
    bad = [c for c in use_classes if c not in PANEL_EDGE_CLASSES]
    if bad:
        raise HatchEdgeError(f"{bad} pieces are not slab edges (the hatch stops for an annotation, the slab does not)")
    if "FREE_EDGE" not in use_classes:
        raise HatchEdgeError("only FREE_EDGE pieces are free slab edges; member faces carry no step concrete")
    return classified.lengths["FREE_EDGE"]
