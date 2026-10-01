"""Synthetic builders for the R8.8 tests (test side only; no project data)."""

from __future__ import annotations

from engine.source import canonical_input as CI

REV = "REV_A"
REGION = "R1"


def rev(rid=REV, sha="a" * 64):
    return CI.SourceRevision(rid, CI.EXACT_SOURCE, sha, None, "TEST")


def steps(path, names=None):
    names = names or {}
    return tuple(CI.LineageStep(h, "B" + h, names.get(h, "BLK" + h)) for h in path)


def part(h, kind, geom, layer="WALL", path=(), idx=0, names=None, etype=None, vis=CI.VISIBLE, rid=REV):
    etype = etype or {"SEGMENT": "LINE", "ARC": "ARC", "CIRCLE": "CIRCLE", "ELLIPTICAL_ARC": "ELLIPSE"}[kind]
    return CI.CanonicalPart(CI.SourceIdentity(rid, str(h), tuple(path), kind, idx), kind, tuple(geom), layer, vis,
                            steps(path, names), f"T:{h}", etype)


def seg(h, x1, y1, x2, y2, **kw):
    return part(h, "SEGMENT", (x1, y1, x2, y2), **kw)


def text(h, value, x, y, path=(), layer="TEXT", vis=CI.VISIBLE, rid=REV, names=None):
    return CI.PlacedText(CI.SourceIdentity(rid, str(h), tuple(path), "TEXT", 0), value, x, y, 20.0, layer, vis,
                         steps(path, names), "TEXT")


def dim(h, pts=((0.0, 0.0), (100.0, 0.0)), m=100.0, vis=CI.VISIBLE, rid=REV, path=()):
    return CI.PlacedDimension(CI.SourceIdentity(rid, str(h), tuple(path), "DIMENSION", 0), pts, pts, m, "", 1.0, "21",
                              "DIM", vis, steps(path))


def inp(parts=(), texts=(), dims=(), revision=None, region_id=REGION, unit=10.0, review=None):
    return CI.CanonicalMeasurementInput(revision or rev(), region_id, "MF:" + region_id, unit, "UNIT-CLAIM",
                                        tuple(parts), tuple(texts), tuple(dims), dict(review or {}), {})


def box(h0, x0, y0, x1, y1, layer="WALL", path=(), names=None):
    """Four wall lines of a closed rectangle (single-line walls), handles h0..h0+3."""
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [seg(h0 + i, *pts[i], *pts[(i + 1) % 4], layer=layer, path=path, names=names) for i in range(4)]


def two_rooms(gap=None, h0=100):
    """Two 500 x 400 rooms side by side sharing a partition at x = 500 (single-line walls, cm units).
    `gap`: (y0, y1) leaves an opening in the partition."""
    out = [seg(h0, 0, 0, 1000, 0), seg(h0 + 1, 1000, 0, 1000, 400), seg(h0 + 2, 1000, 400, 0, 400),
           seg(h0 + 3, 0, 400, 0, 0)]
    if gap is None:
        out.append(seg(h0 + 4, 500, 0, 500, 400))
    else:
        out += [seg(h0 + 4, 500, 0, 500, gap[0]), seg(h0 + 5, 500, gap[1], 500, 400)]
    return out
