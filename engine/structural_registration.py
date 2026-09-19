"""Vector structural PDF <-> architectural DWG registration (§21).

A plotted structural PDF whose sheets are exact 1:100 plots (1 pt =
35.2778 mm on paper x 100) is VECTOR DRAWING GEOMETRY: second in the
source hierarchy after authored DWG geometry, above printed dimensions.
The registration is a pure translation per sheet, voted by matching the
filled column rectangles to the architectural column-bonding loops, then
refined on the inliers. Scale is never fitted: it is the plot scale, and
the residuals report whether that assumption holds.

    CAD_x = a + S * pdf_y ;  CAD_y = b + S * pdf_x   (sheet /Rotate 270)
"""

from __future__ import annotations

import collections
import statistics

PT_MM_AT_1_100 = 25.4 / 72.0 * 100.0   # 35.2778 mm per point


def column_rects(page, min_pt=2.0, max_pt=40.0) -> list:
    out = []
    for dr in page.get_drawings():
        if dr.get("fill") == (0.0, 0.0, 0.0):
            r = dr["rect"]
            if min_pt < r.width < max_pt and min_pt < r.height < max_pt:
                out.append((r.x0, r.y0, r.x1, r.y1))
    return out


def register(cad_loops, rects, *, scale=PT_MM_AT_1_100, vote_bin_mm=50, inlier_mm=150) -> dict:
    cc = [((l[0] + l[2]) / 2, (l[1] + l[3]) / 2, l[2] - l[0], l[3] - l[1]) for l in cad_loops]
    rc = [((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, (r[2] - r[0]) * scale, (r[3] - r[1]) * scale)
          for r in rects]
    votes = collections.Counter()
    for c in cc:
        for r in rc:
            a = c[0] - scale * r[1]
            b = c[1] - scale * r[0]
            votes[(round(a / vote_bin_mm) * vote_bin_mm, round(b / vote_bin_mm) * vote_bin_mm)] += 1
    if not votes:
        return {"STATUS": "NOT_REGISTERED", "WHY": "no candidates"}
    (a0, b0), n = votes.most_common(1)[0]
    inl = [(c, r) for c in cc for r in rc
           if abs(c[0] - (a0 + scale * r[1])) < inlier_mm and abs(c[1] - (b0 + scale * r[0])) < inlier_mm]
    if len(inl) < 4:
        return {"STATUS": "NOT_REGISTERED", "WHY": f"only {len(inl)} inliers"}
    a = statistics.mean(c[0] - scale * r[1] for c, r in inl)
    b = statistics.mean(c[1] - scale * r[0] for c, r in inl)
    res = [(c[0] - (a + scale * r[1]), c[1] - (b + scale * r[0])) for c, r in inl]
    return {"STATUS": "REGISTERED", "SCALE_MM_PER_PT": scale, "SCALE_FITTED": False,
            "A_MM": round(a, 1), "B_MM": round(b, 1), "INLIERS": len(inl),
            "CAD_LOOPS": len(cc), "PDF_RECTS": len(rc),
            "MAX_RESIDUAL_MM": round(max(max(abs(x), abs(y)) for x, y in res), 1),
            "MATCHES": [{"CAD_CENTRE_MM": [round(c[0]), round(c[1])], "CAD_SIZE_MM": [c[2], c[3]],
                         "PDF_CENTRE_PT": [round(r[0], 2), round(r[1], 2)],
                         "PDF_SIZE_MM": [round(r[2]), round(r[3])]} for c, r in inl]}


def to_cad(reg: dict, pdf_x: float, pdf_y: float) -> tuple:
    S = reg["SCALE_MM_PER_PT"]
    return reg["A_MM"] + S * pdf_y, reg["B_MM"] + S * pdf_x


def to_pdf(reg: dict, cad_x: float, cad_y: float) -> tuple:
    S = reg["SCALE_MM_PER_PT"]
    return (cad_y - reg["B_MM"]) / S, (cad_x - reg["A_MM"]) / S
