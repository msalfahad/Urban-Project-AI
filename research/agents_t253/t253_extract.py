"""T-253 extraction on the development villa's Drive drawing (values, ids and DXF handles only; no coordinates).

    .work/venv/bin/python -I research/agents_t253/t253_extract.py <structural.dxf> [--out <dir>]

Input (Drive "Alsenan chalet project"): "ST7757 dxf.dxf" (sha 9f9d1179). GROUND BEAMS PLAN frame as T-141 / T-242.
What it reads, by layer and handle (nothing typed):
- S-BOUN closed bands of the ground-beams plan (the boundary-wall ground beam at natural ground, ST p.14 "GROUND BEAM
  (20x40)"): split into runs by `boundary_court.band_runs` (each corner square in one run), and for every run end face
  the member drawn on it: S-COL.BON column outline, S-BW pool outline (bulges flattened), a layer-1 ground-beam face
  line, another S-BOUN band, or nothing;
- openings drawn across the band (layer 2 / D entities lying in the band: gate, door) with their length along the run;
- layer-1 ground-beam face lines whose end lies on an S-BOUN band face (a building beam ending on the boundary beam);
- plan overlaps of the bands with columns / the pool / the ground-beam strips (T-242 found 0.0000 m2);
- the level marks of the sheet: the '+-0.00' level blocks (layer 3, block LEL) and whether each lies outside the plot
  outline; the LEVEL texts inside the plot.
Writes ALSENAN_BOUNDARY_INPUT.json (lengths in m, areas in m2, rounded to 0.1 mm / 0.0001 m2).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import boundary_court as BC  # noqa: E402

spec = importlib.util.spec_from_file_location("r141", os.path.join(ROOT, "research/agents_t141/run_t141_alsenan.py"))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

TOL = 5.0   # mm: a member drawn on an end face


def r4(v):
    return round(float(v) + 0.0, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("structural")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    from ezdxf import path as ezpath
    from shapely.geometry import LineString, Point, Polygon, box

    if R.sha(a.structural) != R.DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(a.structural)
    msp = doc.modelspace()
    GBP = R.GBP

    def poly_of(e):
        return Polygon([(v.x, v.y) for v in ezpath.make_path(e).flattening(5.0)]).buffer(0)

    bands = {}
    for e in msp.query("LWPOLYLINE[layer=='S-BOUN']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if e.closed and R.inb(*pts[0], GBP):
            bands[e.dxf.handle] = (pts, Polygon(pts))
    cols = {h: Polygon(p).buffer(0) for h, p, _ in R.outlines(msp, "S-COL.BON", GBP)}
    pool = {e.dxf.handle: poly_of(e) for e in msp.query("LWPOLYLINE[layer=='S-BW']")
            if R.inb(*tuple(e.get_points()[0][:2]), GBP) and e.closed}
    l1 = {e.dxf.handle: LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])
          for e in msp.query("LINE[layer=='1']") if R.inb(*tuple(e.dxf.start)[:2], GBP)}
    # plot outline on this sheet = the S-BOUN rectangle drawn on no other sheet frame: the outer edges of the bands
    allb = None
    for _, P in bands.values():
        allb = P if allb is None else allb.union(P)
    plot = box(*allb.bounds)

    out_bands = []
    for h, (pts, P) in sorted(bands.items()):
        br = BC.band_runs(pts, 200.0, tol=0.5)
        width = min(P.bounds[2] - P.bounds[0], P.bounds[3] - P.bounds[1]) if len(pts) == 4 else 200.0
        runs = []
        for k, run in enumerate(br["runs"], start=1):
            ends = []
            for f in run["end_faces"]:
                if f is None:
                    ends.append({"kind": "CORNER", "refs": []})
                    continue
                ax, c, s0, s1 = f
                seg = LineString([(c, s0), (c, s1)]) if ax == "X" else LineString([(s0, c), (s1, c)])
                mid = seg.interpolate(0.5, normalized=True)
                hit = []
                for ch, Q in cols.items():
                    if Q.exterior.distance(mid) < TOL and Q.boundary.intersection(seg.buffer(TOL)).length >= seg.length - 2 * TOL:
                        hit.append(("COLUMN", ch))
                for ph, Q in pool.items():
                    if Q.exterior.distance(mid) < TOL:
                        hit.append(("POOL_WALL", ph))
                for lh, Ls in l1.items():
                    if Ls.distance(mid) < TOL and Ls.buffer(TOL).contains(seg):
                        hit.append(("GROUND_BEAM_FACE", lh))
                for oh, (_, Q) in bands.items():
                    if oh != h and Q.exterior.distance(mid) < TOL:
                        hit.append(("BOUNDARY_BAND", oh))
                kinds = sorted({k_ for k_, _ in hit})
                ends.append({"kind": "+".join(kinds) if kinds else "NONE", "refs": sorted(x for _, x in hit),
                             "face_m": r4(seg.length / 1000.0)})
            runs.append({"run_id": f"{h}#{k}", "axis": run["axis"], "length_m": r4(run["length"] / 1000.0),
                         "corners_owned": run["corners_owned"], "ends": ends})
        # openings drawn across the band (layer 2 / D) and their length inside it
        opens = []
        for e in msp.query("LINE LWPOLYLINE"):
            if e.dxf.layer not in ("2", "D"):
                continue
            if e.dxftype() == "LINE":
                g = LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])
            else:
                q = [tuple(p[:2]) for p in e.get_points()]
                if len(q) < 2:
                    continue
                g = LineString(q + ([q[0]] if e.closed else []))
            if not R.inb(*g.coords[0], GBP):
                continue
            inside = g.intersection(P.buffer(1.0))
            if inside.length > 100.0:
                bx = g.bounds
                span = max(bx[2] - bx[0], bx[3] - bx[1])
                opens.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "type": e.dxftype(),
                              "extent_along_run_m": r4(span / 1000.0)})
        ov_cols = sum(P.intersection(Q).area for Q in cols.values())
        ov_pool = sum(P.intersection(Q).area for Q in pool.values())
        out_bands.append({"handle": h, "plan_m2": r4(P.area / 1e6), "width_m": r4(width / 1000.0),
                          "band_area_from_runs_m2": r4(br["runs_area"] / 1e6), "runs": runs,
                          "openings_drawn_across": sorted(opens, key=lambda d: d["handle"]),
                          "overlap_columns_m2": r4(ov_cols / 1e6), "overlap_pool_m2": r4(ov_pool / 1e6)})

    # building ground-beam face lines ending on a boundary band face
    # END_ON_FACE: the line meets a band edge at right angles away from the band's corners (a beam framing into
    # the boundary beam); CORNER_CONTACT: the line only continues a band edge from one of its corners (collinear)
    touching = []
    for lh, Ls in sorted(l1.items()):
        (x0, y0), (x1, y1) = Ls.coords[0], Ls.coords[-1]
        horiz = abs(y1 - y0) < TOL
        for end in (Point(x0, y0), Point(x1, y1)):
            for bh, (pts_b, Q) in bands.items():
                if Q.exterior.distance(end) >= TOL:
                    continue
                at_corner = min(Point(p).distance(end) for p in pts_b) < TOL
                ex = [LineString([pts_b[i], pts_b[(i + 1) % len(pts_b)]]) for i in range(len(pts_b))]
                edge = min(ex, key=lambda g: g.distance(end))
                (ex0, ey0), (ex1, ey1) = edge.coords[0], edge.coords[-1]
                perpendicular = (abs(ey1 - ey0) < TOL) != horiz
                kind = "END_ON_FACE" if perpendicular and not at_corner else "CORNER_CONTACT"
                touching.append({"line": lh, "boundary_band": bh, "line_m": r4(Ls.length / 1000.0), "kind": kind})
    # level marks: the +-0.00 blocks and the LEVEL texts
    lel = []
    for e in msp.query("INSERT[name=='LEL']"):
        x, y = e.dxf.insert[0], e.dxf.insert[1]
        if R.inb(x, y, GBP):
            txt = [v.dxf.text for v in e.virtual_entities() if v.dxftype() in ("TEXT", "MTEXT")]
            lel.append({"handle": e.dxf.handle, "text": txt[0].replace("%%p", "+-") if txt else None,
                        "outside_plot": not plot.contains(Point(x, y)),
                        "distance_to_plot_m": r4(plot.exterior.distance(Point(x, y)) / 1000.0)})
    levels = sorted(e.dxf.text for e in msp.query("TEXT[layer=='LEVEL']")
                    if R.inb(e.dxf.insert[0], e.dxf.insert[1], GBP))
    res = {"source": {"structural_sha256": R.DXF_SHA, "drive": "Alsenan chalet project / ST7757 dxf.dxf",
                      "sheet": "GROUND BEAMS PLAN (p.3)"},
           "plot_outline_m": [r4((plot.bounds[2] - plot.bounds[0]) / 1000.0),
                              r4((plot.bounds[3] - plot.bounds[1]) / 1000.0)],
           "boundary_bands": out_bands, "ground_beam_lines_ending_on_boundary": touching,
           "level_blocks_pm000": lel, "level_texts_inside": levels,
           "columns_drawn_in_bands": sum(1 for Q in cols.values() for _, P in bands.values()
                                         if P.intersection(Q).area > 1.0)}
    with open(os.path.join(a.out, "ALSENAN_BOUNDARY_INPUT.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
