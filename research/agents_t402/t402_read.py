"""T-402 own reading of every HELD beam line of the candidate on the structural DXF (private Drive copy, outside the repo).

For each held run the route G band polygon (research/agents_t110/scripts/bands.py, fit <= 0.6 mm) locates the member.
Read on the drawing, not taken from the engine:
  * edge lines: LINE on layers 1 / 2 / 5 / S-BEAM parallel to the band axis (<= 0.5 deg), within the band's width
    + 0.10 m on either side and overlapping it along the axis; the drawn width is the spread of the two outermost
    face offsets; each face's clipped length is its face-to-face length;
  * end supports: S-COL.BON closed outlines and other bands within 15 mm of a band end;
  * section cuts: S-SEC.LINE polylines / lines crossing the band (a governing section, if any);
  * marks: beam-mark texts (S-TEXT) within 1.2 m of the band centre.
Output (private): READ_T402.json with handles, offsets and lengths; nothing tracked carries coordinates.

    python3 -I research/agents_t402/t402_read.py <private>/ST7757_dxf.dxf <private>/bands.json <private>/texts.json \
        <private>/t402/READ_T402.json
"""
from __future__ import annotations

import json
import math
import re
import sys

EDGE_LAYERS = {"1", "2", "5", "S-BEAM"}
TOL_ANG = math.radians(0.5)
MARGIN = 0.10

# held runs of the candidate (line id -> band@storey); bands from the T-252 ledger / route G ids
HELD = {
    "L-9e4895663f76d7f03ac9": "BAND0008@GF", "L-2c7b0b1e1a439d9ffd1e": "BAND0036.1@GF",
    "L-60f09eece6568b15f6ce": "BAND0036.2@GF", "L-1fd49f3e7c5a7dd19d4d": "BAND0042@GF",
    "L-88ccf8d4505411deb9e5": "BAND0019.2@GF", "L-634cefe5e8a7fb458e16": "BAND0031.1@GF",
    "L-331d4bbef719a7f0bbca": "BAND0031.2@GF", "L-8ea71184fff91b4357b7": "BAND0046.2@GF",
    "L-efd3f7806bf10b6a8e98": "BAND0030.2@GF",
    "L-39ca5340879eafc35355": "BAND0009@1F", "L-50667f69855b6d588011": "BAND0026.1@1F",
    "L-43e804ba4a4c07529fd5": "BAND0026.2@1F", "L-67f3d325019e618328eb": "BAND0013.1@1F",
    "L-54e397fe7b1485b2e8fe": "BAND0013.2@1F", "L-56d278bedc8dda2837a9": "BAND0025@1F",
    "L-a9d5e7dc22013e24d691": "BAND0014@1F", "L-bb49e831f053bd30a6ce": "BAND0023@1F",
    "L-f83c4a469845c7e14dfa": "BAND0005.1@1F",
    "L-8d031491396379f0cbb1": "BAND0001.3@2F", "L-d62d2fcf3d0023ad1ad1": "BAND0006.1@2F",
    "L-dc8cbfc119d006ff3927": "BAND0008.1@2F", "L-7c3edce23ec8faa3d674": "BAND0011.1@2F",
}


def axis(pts):
    s = max(((pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))), key=lambda s: math.dist(*s))
    (x0, y0), (x1, y1) = s
    L = math.dist(*s)
    return (x0, y0), ((x1 - x0) / L, (y1 - y0) / L)


def pr(p, o, u):
    return (p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1]


def pp(p, o, u):
    return -(p[0] - o[0]) * u[1] + (p[1] - o[1]) * u[0]


def read(path):
    import ezdxf
    msp = ezdxf.readfile(path).modelspace()
    lines, cols, secs = [], [], []
    for e in msp:
        if not e.dxf.hasattr("layer"):
            continue
        lay, t = e.dxf.layer, e.dxftype()
        if t == "LINE" and lay in EDGE_LAYERS:
            a, b = e.dxf.start, e.dxf.end
            lines.append((e.dxf.handle, lay, (a[0] / 1000, a[1] / 1000), (b[0] / 1000, b[1] / 1000)))
        elif t == "LWPOLYLINE" and lay == "S-COL.BON" and e.closed:
            cols.append((e.dxf.handle, [(p[0] / 1000, p[1] / 1000) for p in e.get_points("xy")]))
        elif lay == "S-SEC.LINE" and t in ("LWPOLYLINE", "LINE"):
            pts = ([(p[0] / 1000, p[1] / 1000) for p in e.get_points("xy")] if t == "LWPOLYLINE"
                   else [(e.dxf.start[0] / 1000, e.dxf.start[1] / 1000), (e.dxf.end[0] / 1000, e.dxf.end[1] / 1000)])
            secs.append((e.dxf.handle, pts))
    return lines, cols, secs


def measure(band, lines, cols, secs, texts):
    from shapely.geometry import LineString, Polygon
    pts = band["pts"]
    o, u = axis(pts)
    ss = [pr(p, o, u) for p in pts]
    ws = [pp(p, o, u) for p in pts]
    s0, s1, w0, w1 = min(ss), max(ss), min(ws), max(ws)
    faces = []
    for h, lay, a, b in lines:
        d = (b[0] - a[0], b[1] - a[1])
        L = math.hypot(*d)
        if L < 1e-6:
            continue
        ang = abs(math.asin(max(-1.0, min(1.0, (d[0] * u[1] - d[1] * u[0]) / L))))
        if ang > TOL_ANG:
            continue
        wa, wb = pp(a, o, u), pp(b, o, u)
        if not (w0 - MARGIN <= (wa + wb) / 2 <= w1 + MARGIN):
            continue
        sa, sb = sorted((pr(a, o, u), pr(b, o, u)))
        lo, hi = max(sa, s0), min(sb, s1)
        if hi - lo < 0.05:
            continue
        faces.append({"handle": h, "layer": lay, "offset_m": round((wa + wb) / 2 - w0, 4),
                      "clipped_m": round(hi - lo, 4), "entity_m": round(L, 4),
                      "beyond_band_m": round((sb - sa) - (hi - lo), 4)})
    offs = sorted({f["offset_m"] for f in faces})
    poly = Polygon(pts)
    sup = [h for h, cp in cols if Polygon(cp).buffer(0.015).intersects(poly)]
    cut = [h for h, sp in secs if len(sp) > 1 and LineString(sp).intersects(poly)]
    cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    marks = sorted({t["t"].strip() for t in texts if t["l"] == "S-TEXT" and math.dist((t["x"], t["y"]), (cx, cy)) < 1.2
                    and re.match(r"^(C?B\d+|CA|B\.W)", t["t"].strip())})
    return {"band_length_m": round(s1 - s0, 4), "band_width_m": round(w1 - w0, 4), "faces": faces,
            "face_offsets_m": offs, "drawn_width_m": round(offs[-1] - offs[0], 4) if len(offs) > 1 else None,
            "supports_col_handles": sup, "section_cuts": cut, "marks_within_1_2m": marks,
            "title": band.get("title", "")}


def main(argv):
    dxf, bands_p, texts_p, out_p = argv[1:5]
    bands = json.load(open(bands_p, encoding="utf-8"))
    texts = json.load(open(texts_p, encoding="utf-8"))
    lines, cols, secs = read(dxf)
    out = {lid: dict(band=b, **measure(bands[b], lines, cols, secs, texts)) for lid, b in HELD.items() if b in bands}
    missing = [b for b in HELD.values() if b not in bands]
    json.dump({"runs": out, "bands_missing": missing, "section_lines": len(secs)}, open(out_p, "w"), indent=1)
    for lid, r in out.items():
        print(lid, r["band"], r["title"], "L", r["band_length_m"], "w_band", r["band_width_m"], "drawn", r["drawn_width_m"],
              "offs", r["face_offsets_m"], "sup", len(r["supports_col_handles"]), "cut", r["section_cuts"],
              "marks", r["marks_within_1_2m"])
    print("missing", missing)


if __name__ == "__main__":
    main(sys.argv)
