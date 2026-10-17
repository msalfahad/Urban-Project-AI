"""S8.2: the pool_qto helpers checked independently on the real ST7757 geometry.

pool_qto.py was partly reconstructed after a container loss, so its helpers are not trusted because synthetic tests
pass. Each check here takes its reference from the raw DXF through ezdxf (not the S1 reader) and from shapely, never
from pool_qto. Skipped when the private client drawings are not restored."""

from __future__ import annotations

import collections
import importlib.util
import math
from pathlib import Path

import pytest
from shapely.geometry import LineString, Point, Polygon

from engine.source import pool_qto as PQ

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_swimming_pool_s8_2"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
pytestmark = pytest.mark.skipif(not DXF.exists(), reason="private client drawings not restored in data/inputs/by_sha256")


@pytest.fixture(scope="module")
def ctx():
    spec = importlib.util.spec_from_file_location("build_s8_2_geom", PKG / "build_s8_2.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    import alsenan_structural_s1 as S1M
    src = S1M.Source(m.DXF)
    det = m.det_evidence(src)
    reg = m.section_regions(det["sec"])
    bars = m.det_bars(det, reg)
    runs0, dups = m.runs_of(bars["main"], reg["regions"])
    return {"m": m, "src": src, "raw": {e.dxf.handle: e for e in src.doc.modelspace()}, "det": det, "reg": reg,
            "bars": bars, "runs0": runs0, "dups": dups, "pg": m.plan_geometry(src), "labels": m.det_labels(det),
            "frame": {k: src.sheets[k]["frame"][:2] for k in ("DET", "GBP")}}


def _true_polygon(ctx, h, n_arc=20000):
    """The raw LWPOLYLINE with each bulge sampled on its true circle (ezdxf.math.bulge_to_arc)."""
    from ezdxf.math import bulge_to_arc
    gx, gy = ctx["frame"]["GBP"]
    v = [(p[0] - gx, p[1] - gy, p[4]) for p in ctx["raw"][h].get_points("xyseb")]
    pts = []
    for i, (x, y, bulge) in enumerate(v):
        pts.append((x, y))
        if abs(bulge) > 1e-12:
            c, a0, a1, r = bulge_to_arc((x, y), v[(i + 1) % len(v)][:2], bulge)
            sweep = (a1 - a0) % (2 * math.pi)
            for k in range(1, n_arc):
                t = a1 - sweep * k / n_arc if bulge < 0 else a0 + sweep * k / n_arc
                pts.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return Polygon(pts)


def _arc_line(s, n=4000):
    t0, t1 = s[4], s[5]
    return LineString([(s[2][0] + s[3] * math.cos(t0 + (t1 - t0) * i / n), s[2][1] + s[3] * math.sin(t0 + (t1 - t0) * i / n))
                       for i in range(n + 1)])


def test_areas_band_and_lengths_against_the_raw_polylines(ctx):
    pg = ctx["pg"]
    P_out, P_in = _true_polygon(ctx, "7C6"), _true_polygon(ctx, "7C5")
    assert PQ.region_area_m2([pg["rings"]["outer"]]) == pytest.approx(P_out.area / 1e6, abs=1e-7)
    assert PQ.region_area_m2([pg["rings"]["inner"]]) == pytest.approx(P_in.area / 1e6, abs=1e-7)
    assert P_in.within(P_out)
    assert pg["band"] == pytest.approx(P_out.difference(P_in).area / 1e6, abs=1e-7)
    assert math.fsum(pg["run_area"].values()) == pytest.approx(P_out.difference(P_in).area / 1e6, abs=1e-7)
    assert pg["L_out"] == pytest.approx(P_out.exterior.length / 1000, abs=1e-6)
    assert pg["L_in"] == pytest.approx(P_in.exterior.length / 1000, abs=1e-6)


def test_segment_ends_and_lengths_against_ezdxf(ctx):
    fx, fy = ctx["frame"]["DET"]
    for s in ctx["bars"]["main"] + ctx["bars"]["corner"]:
        e = ctx["raw"][s[1].split("#")[0]]
        if s[0] == "LINE" and e.dxftype() == "LINE":
            a, b = (e.dxf.start.x - fx, e.dxf.start.y - fy), (e.dxf.end.x - fx, e.dxf.end.y - fy)
            ref_len = math.dist(a, b)
        elif s[0] == "ARC":
            ce = e.construction_tool()
            a, b = (ce.start_point.x - fx, ce.start_point.y - fy), (ce.end_point.x - fx, ce.end_point.y - fy)
            ref_len = math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360) * e.dxf.radius
        else:
            continue
        assert math.dist(PQ._seg_end(s, 0), a) < 0.01 and math.dist(PQ._seg_end(s, 1), b) < 0.01, s[1]
        assert PQ._seg_len(s) == pytest.approx(ref_len, abs=0.01), s[1]


def test_the_arc_across_zero_degrees_is_unwrapped(ctx):
    arc = next(s for s in ctx["bars"]["main"] if s[1] == "1849")        # drawn from 270 to 0 degrees
    assert arc[5] > arc[4] and math.degrees(arc[5] - arc[4]) == pytest.approx(90.0)
    r4 = next(r for r in ctx["runs0"].values() if "1849" in r["run_segments"])
    assert [round(t) for t in r4["shape_detail"]["turns_deg"]][:3] == [90, 90, 90]


def test_reverse_and_direction_against_numerical_tangents(ctx):
    for s in ctx["bars"]["main"] + ctx["bars"]["corner"]:
        for k in (0, 1):
            if s[0] == "LINE":
                d = (s[3][0] - s[2][0], s[3][1] - s[2][1])
            else:
                t = s[4] if k == 0 else s[5]
                sg = 1 if s[5] > s[4] else -1
                d = (-math.sin(t) * sg, math.cos(t) * sg)
            n = math.hypot(*d)
            assert math.dist(PQ._dir(s, k), (d[0] / n, d[1] / n)) < 1e-6
        rv = PQ._reverse(s)
        assert PQ._seg_end(rv, 0) == PQ._seg_end(s, 1) and PQ._seg_end(rv, 1) == PQ._seg_end(s, 0)
        assert math.dist(PQ._dir(rv, 0), tuple(-v for v in PQ._dir(s, 1))) < 1e-9


def test_runs_are_continuous_and_duplicates_are_exact(ctx):
    for r in ctx["runs0"].values():
        for a, b in zip(r["_segs"], r["_segs"][1:]):
            assert math.dist(PQ._seg_end(a, 1), PQ._seg_end(b, 0)) <= 0.5
    key = collections.defaultdict(list)
    for s in ctx["bars"]["main"] + ctx["bars"]["corner"]:
        if "#" in s[1]:
            continue
        e = ctx["raw"][s[1]]
        if e.dxftype() == "ARC":
            k = ("A", round(e.dxf.center.x, 3), round(e.dxf.center.y, 3), round(e.dxf.radius, 3),
                 round(e.dxf.start_angle % 360, 4), round(e.dxf.end_angle % 360, 4))
        else:
            k = ("L",) + tuple(sorted(((round(e.dxf.start.x, 3), round(e.dxf.start.y, 3)),
                                       (round(e.dxf.end.x, 3), round(e.dxf.end.y, 3)))))
        key[k].append(s[1])
    brute = sorted(tuple(sorted(v)) for v in key.values() if len(v) > 1)
    assert sorted(tuple(sorted(d)) for d in ctx["dups"]) == brute == [("1922", "1924")]


def test_distances_against_shapely(ctx):
    tips = [p for l in ctx["labels"] for p in l["tips"]] + [l["p"] for l in ctx["labels"]]
    for s in ctx["bars"]["main"] + ctx["bars"]["corner"]:
        if s[0] == "LINE":
            ls = LineString([s[2], s[3]])
            assert all(abs(PQ._pt_seg(p, s[2], s[3]) - ls.distance(Point(p))) < 1e-6 for p in tips)
        else:
            al = _arc_line(s)
            assert all(abs(PQ.target_distance(p, ("ARC", s[2], s[3], s[4], s[5])) - al.distance(Point(p))) < 1e-2
                       for p in tips)
    for d in ctx["bars"]["dots"]:
        assert all(abs(PQ.target_distance(p, ("DOT", d["c"], d["r"])) -
                       max(0.0, Point(p).distance(Point(d["c"])) - d["r"])) < 1e-9 for p in tips)


def test_leg_lengths_against_shapely_clipping(ctx):
    regions = ctx["reg"]["regions"]
    for r in ctx["runs0"].values():
        lines = {"_segs": [s for s in r["_segs"] if s[0] == "LINE"]}
        got = PQ.leg_lengths_in(lines, regions)
        for rid, polys in regions.items():
            ref = sum(Polygon(pp).intersection(LineString([s[2], s[3]])).length for pp in polys for s in lines["_segs"])
            assert got[rid] == pytest.approx(ref, abs=1e-6)
        for s in r["_segs"]:
            if s[0] == "ARC":
                g = PQ.leg_lengths_in({"_segs": [s]}, regions)
                mid = _arc_line(s).interpolate(0.5, normalized=True)
                owner = [rid for rid, polys in regions.items() if any(Polygon(pp).buffer(1e-9).contains(mid) for pp in polys)]
                assert [k for k, v in g.items() if v > 0] == owner
                assert sum(g.values()) == pytest.approx(_arc_line(s).length, abs=0.01)


def test_notation_of_the_26_labels(ctx):
    expect = {"7%%c14/m": (PQ.RATE, 14, 7.0), "7%%C14/m": (PQ.RATE, 14, 7.0), "7%%C12/m": (PQ.RATE, 12, 7.0),
              "6%%c12/m": (PQ.RATE, 12, 6.0), "6%%c14/m": (PQ.RATE, 14, 6.0), "%%c12/20cm": (PQ.SPACING, 12, 5.0),
              "%%c10/20cm": (PQ.SPACING, 10, 5.0), "3%%c16": (PQ.FINITE_GROUP, 16, None),
              "4%%c16": (PQ.FINITE_GROUP, 16, None)}
    labels = ctx["labels"]
    assert len(labels) == 26
    assert all((l["notation"]["kind"], l["notation"]["dia_mm"], l["notation"]["per_m"]) == expect[l["raw"]]
               for l in labels)
