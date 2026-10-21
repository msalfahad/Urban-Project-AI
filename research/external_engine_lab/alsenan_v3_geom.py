"""ALSENAN V3 - shapely adapter for engine.source.finish_height_v3 (the engine stays stdlib-only).

face_pieces(edge, bands, plate, plate_t_cm, eps) projects every band over the face line to stations along it and
answers plate containment per piece, then calls FH3.pieces.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point

from engine.source import finish_height_v3 as FH3


def coverage(edge, bands, eps=1.0):
    line = LineString(list(edge))
    cover = []
    for rec, poly in bands:
        inter = poly.buffer(2 * eps).intersection(line)
        if inter.is_empty:
            continue
        # the buffer only tolerates a face lying on the band edge; the band's own extent along the line ends it
        e = [line.project(Point(c)) for c in getattr(poly, "exterior", poly).coords]
        for g in getattr(inter, "geoms", [inter]):
            if g.length <= eps:
                continue
            s = sorted(line.project(Point(c)) for c in g.coords)
            cover.append((max(s[0], min(e)), min(s[-1], max(e)), rec))
    return line, cover


def face_pieces(edge, bands, plate=None, plate_t_cm=None, eps=1.0, min_piece=1.0):
    line, cover = coverage(edge, bands, eps)

    def inside(t0, t1):
        seg = LineString([line.interpolate(t0).coords[0], line.interpolate(t1).coords[0]])
        return plate.buffer(eps).contains(seg)
    return FH3.pieces(line.length, cover, inside if plate is not None else None, plate_t_cm, eps, min_piece)
