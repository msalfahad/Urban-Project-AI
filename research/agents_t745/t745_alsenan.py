"""T-745 read-only development-villa run: B12-02 drainage runs in lm from the sanitary sheet's vector paths
(t745_runs.DRAIN_RUN_CENSUS_T745_V1). Nothing in the repository is written.

Usage (from the checkout root, through the wrapper):
  bash scripts/agent_env.sh run --tree task-T-745 research/agents_t745/t745_alsenan.py <sanitary.pdf> \
      <private reading.json> --out <scratch>/t745_alsenan.json

<private reading.json> is the person's reading of the sheet: page -> floor, the plot rectangle edges and its printed
sides (the scale), the pen -> system map read from the sheet, the printed diameter labels (a point on the run each
names), the hand-entered runs of pens not extracted (the blue high-level stack offset), the risers with their printed
levels, the systems the set does not draw, and 'sheet_notes' {page: transcription of the NOTES / title-block text}
(the sheets' text is outlined vectors, so it is read by eye; a page with no transcription is refused). The notes set
each sheet's length basis (t745_runs.sheet_basis): on a not-to-scale sheet every plan run is
HELD_SCHEMATIC_NOT_TO_SCALE and its scaled length is an information figure only (T-745 r2, rule R-T380-1). It holds drawing coordinates, so it stays in .work/private. Output:
run ids, systems, diameters, statuses and lm only (no coordinates)."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t745_runs as R  # noqa: E402

FD_COLOUR = (1.0, 0.75, 0.0)
FD_SIZE_PT = (4.3, 5.0)          # the floor-drain square of this sheet set (T-743 machine check), page points


def _col(c):
    return tuple(round(x, 2) for x in c) if c else None


def page_paths(page):
    """(lines, dots, box_edges): lines = [(colour, width, (a, b))] drawn as line items, dots = [(colour, (x, y))],
    box_edges = the edges of rectangle / quad items (used only to find the plot frame, never as pipes); displayed
    page points."""
    import pymupdf
    M = page.rotation_matrix
    lines, dots, box_edges = [], [], []
    for g in page.get_drawings():
        col = _col(g.get("color")) or _col(g.get("fill"))
        w = round(g.get("width") or 0, 2)
        r = g["rect"] * M
        if max(r.width, r.height) < 1.6:
            dots.append((col, ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)))
        for it in g["items"]:
            if it[0] == "l":
                a, b = pymupdf.Point(it[1]) * M, pymupdf.Point(it[2]) * M
                lines.append((col, w, ((a.x, a.y), (b.x, b.y))))
            elif it[0] in ("re", "qu"):
                q = it[1].quad if it[0] == "re" else it[1]
                ps = [pymupdf.Point(v) * M for v in (q.ul, q.ur, q.lr, q.ll)]
                for i in range(4):
                    box_edges.append((col, w, ((ps[i].x, ps[i].y), (ps[(i + 1) % 4].x, ps[(i + 1) % 4].y))))
    return lines, dots, box_edges


def plot_scale(lines, plot):
    """measure the plot rectangle on the sheet from its four edge lines (each must be drawn on this sheet, at least
    half the side long) and derive the scale from its printed sides."""
    def edge(axis, v, lo, hi):
        covered = set()                       # 1-unit cells of the side covered by drawn pieces on the edge line
        pos = []
        for c, w, (a, b) in lines:
            if c != (0.0, 0.0, 0.0):
                continue
            i = 1 if axis == "h" else 0       # the fixed coordinate
            j = 1 - i
            if abs(a[i] - v) < 0.2 and abs(b[i] - v) < 0.2:
                s0, s1 = sorted((a[j], b[j]))
                covered.update(range(int(max(s0, lo)), int(min(s1, hi))))
                pos.append((a[i] + b[i]) / 2)
        if len(covered) < 0.5 * (hi - lo):
            raise R.RefusedSheet(f"plot edge {axis} {v} not drawn over half its side on this sheet")
        return sum(pos) / len(pos)
    xl = edge("v", plot["x_left"], plot["y_top"], plot["y_bottom"])
    xr = edge("v", plot["x_right"], plot["y_top"], plot["y_bottom"])
    yt = edge("h", plot["y_top"], plot["x_left"], plot["x_right"])
    yb = edge("h", plot["y_bottom"], plot["x_left"], plot["x_right"])
    long_u, short_u = xr - xl, yb - yt
    k = R.scale_from_dimensions([(plot["long_m"], long_u), (plot["short_m"], short_u)])
    return k, {"long_pt": round(long_u, 2), "short_pt": round(short_u, 2), "m_per_pt": round(k, 6),
               "scale_1_to": round(k / (0.0254 / 72), 1)}


def inside(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def fd_points(page):
    """floor-drain square centres (the T-743 machine rule), displayed page points."""
    import pymupdf
    M = page.rotation_matrix
    rs = [g["rect"] * M for g in page.get_drawings() if _col(g.get("color")) == FD_COLOUR]
    rs = [pymupdf.Rect(r) for r in rs]
    groups = []
    for r in rs:
        g = pymupdf.Rect(r.x0 - 0.3, r.y0 - 0.3, r.x1 + 0.3, r.y1 + 0.3)
        for gr in groups:
            if gr[0].intersects(g):
                gr[0] |= r
                break
        else:
            groups.append([pymupdf.Rect(r)])
    # one more pass to merge groups that touch
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if groups[i][0].intersects(groups[j][0]):
                    groups[i][0] |= groups[j][0]
                    groups.pop(j)
                    merged = True
                    break
            if merged:
                break
    out = []
    for (r,) in groups:
        if FD_SIZE_PT[0] <= r.width <= FD_SIZE_PT[1] and FD_SIZE_PT[0] <= r.height <= FD_SIZE_PT[1]:
            out.append(((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2))
    return out


def main(argv=None):
    import argparse
    import pymupdf
    ap = argparse.ArgumentParser()
    ap.add_argument("sanitary_pdf")
    ap.add_argument("reading")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rd = json.loads(Path(a.reading).read_text(encoding="utf-8"))
    doc = pymupdf.open(a.sanitary_pdf)
    plot = rd["plot"]
    box = (plot["x_left"] - 3, plot["y_top"] - 3, plot["x_right"] + 3, plot["y_bottom"] + 3)
    all_runs, scales, kfl, fd_cov, label_refused, basis = [], {}, {}, {}, [], {}
    for pg, floor in rd["pages"].items():
        basis[floor] = R.sheet_basis(rd.get("sheet_notes", {}).get(pg))
        page = doc[int(pg) - 1]
        lines, dots, box_edges = page_paths(page)
        k, sc = plot_scale(lines + box_edges, plot)
        scales[floor] = sc
        kfl[floor] = k
        runs = []
        for pen, (colour, width, system) in rd["pens"].items():
            colour = tuple(colour)
            segs = [s for c, w, s in lines if c == colour and w == width and inside(s[0], box) and inside(s[1], box)]
            pdots = [p for c, p in dots if c == colour and inside(p, box)]
            for r in R.build_runs(segs, pdots, floor=floor, pen=pen, scale=k):
                r.system = system
                r.scale = k
                runs.append(r)
        for i, (system, dia, pts, _note) in enumerate(rd.get("extra_runs", {}).get(pg, []), 1):
            r = R.Run(run_id=f"{floor}-X{i:02d}", floor=floor, pen="READ", system=system, diameter_in=dia,
                      segments=[(tuple(pts[j]), tuple(pts[j + 1])) for j in range(len(pts) - 1)])
            r.scale = k
            runs.append(r)
        R.flag_symbol_marks(runs, k)
        label_refused += [(floor, p, d, n) for p, d, n in
                          R.label_runs(runs, [(tuple(p), d) for p, d, _t in rd["labels"].get(pg, [])], tol=1.5)]
        fds = [q for q in fd_points(page) if inside(q, box)]     # the legend square is outside the plot
        cov = R.endpoint_coverage(fds, runs, tol=4.0)
        fd_cov[floor] = {"floor_drains": len(fds), "with_a_drawn_pipe": sum(1 for c in cov if c),
                         "without": sum(1 for c in cov if not c)}
        all_runs += runs
    risers = [R.Riser(riser_id=z["id"], system=z["system"], diameter_in=z["diameter_in"], top_level=z["top"],
                      bottom_level=z["bottom"], bottom_offset_m=z.get("offset", 0.0),
                      bottom_bounds=tuple(z["bounds"]) if z.get("bounds") else None, note=z["note"])
              for z in rd["risers"]]
    # each sheet keeps its own measured scale; the sheets of one set must agree (a sheet plotted differently is named)
    k = kfl
    R.scale_from_dimensions([(v, 1.0) for v in k.values()])
    rows, marks = R.table(all_runs, risers, k, not_drawn=[tuple(x) for x in rd.get("not_drawn", [])], basis=basis)
    out = {
        "method": R.METHOD_ID, "source": "Drive 'Alsenan chalet project' / sanitary-7757.pdf p.1-3",
        "sheet_scale": scales, "sheet_basis": basis, "pens": {p: v[2] for p, v in rd["pens"].items()},
        "runs": [dict(R.run_record(r, k, basis), pen=r.pen, segments=len(r.segments), bridged_gaps=len(r.bridges))
                 for r in all_runs],
        "risers": [{"riser_id": z.riser_id, "system": z.system, "diameter_in": z.diameter_in,
                    "lm": dict(zip(("status", "low", "high"), z.lm())), "note": z.note} for z in risers],
        "rows": rows, "totals_by_state": R.totals_by_state(rows), "symbol_marks": marks,
        "floor_drain_outlets": fd_cov, "labels_refused": label_refused,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"sheet_scale": scales, "floor_drain_outlets": fd_cov, "labels_refused": label_refused,
                      "totals_by_state": out["totals_by_state"]}, ensure_ascii=False))
    for r in rows:
        print(r["kind"], r["floor"], r["system"], r["diameter_in"], r["status"], r["runs"], r["lm"], r["lm_high"])
    for r in out["runs"]:
        print(" ", r["run_id"], r["system"], r["diameter_in"], r["status"], r["segments"], r["bridged_gaps"], r["lm"],
              r["scaled_info_lm"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
