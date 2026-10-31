"""T-402 r2: every section cut of the structural set, the held bands it reaches and what its section view PRINTS.

Read on the drawing (private Drive copy, outside the repo), never from the engine:
  * cuts: S-SEC.LINE polylines; a cut 'reaches' a band when the cut line intersects the band polygon, and is listed as
    'near' when it passes within 0.50 m (a cut drawn a little short is still reported, never silently dropped);
  * labels: S-SEC-TEXT letters within 1.5 m of a cut end; titles: '%%USECTION X-X' texts (S-TEXT.D);
  * section view: the layer-1 outline polyline whose lower-left corner is nearest above its title (<= 5.0 drawing m);
  * printed sizes: DIMENSION entities whose extension points (defpoint2 / defpoint3) lie in the view (+ 0.30 drawing m),
    each with its measurement, its DIMLFAC override, its text override and the text the sheet SHOWS (the dimension's
    geometry block); value printed = measurement x DIMLFAC, checked against the shown text;
    the axis (V / H) from the rotated dimension's angle (0 = H, 90 = V), never from the extension-point spread;
  * notes: texts in the view with the leader line they sit on (a note on a bar leader is a bar note, not a size note).
Output: <private>/t402/SECTIONS_T402.json (handles, printed values; no coordinates are written to tracked files).

    python3 -I research/agents_t402/t402_sections.py <private>/ST7757_dxf.dxf <private>/t402/bands.json \
        <private>/t402/SECTIONS_T402.json
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t402_read as T  # noqa: E402

VIEW_PAD = 300.0          # drawing units (mm of the model) around a section outline
TITLE_REACH = 5000.0
NOTE_REACH = 1800.0      # drawing units to the right of a view where its bar / size notes stand


def read(path):
    import ezdxf
    from shapely.geometry import LineString
    msp = ezdxf.readfile(path).modelspace()
    cuts, labels, titles, outlines, dims, texts, leaders = [], [], [], [], [], [], []
    for e in msp:
        if not e.dxf.hasattr("layer"):
            continue
        lay, t = e.dxf.layer, e.dxftype()
        if lay == "S-SEC.LINE" and t == "LWPOLYLINE":
            cuts.append((e.dxf.handle, [(p[0], p[1]) for p in e.get_points("xy")]))
        elif t == "TEXT" and lay == "S-SEC-TEXT":
            labels.append((e.dxf.handle, e.dxf.text.strip(), (e.dxf.insert[0], e.dxf.insert[1])))
        elif t == "TEXT" and re.search(r"SECTION\s+([A-Z])-\1", e.dxf.text.upper()):
            m = re.search(r"SECTION\s+([A-Z])-\1", e.dxf.text.upper())
            titles.append((e.dxf.handle, m.group(1), (e.dxf.insert[0], e.dxf.insert[1])))
        elif t == "LWPOLYLINE" and lay == "1":
            outlines.append((e.dxf.handle, [(p[0], p[1]) for p in e.get_points("xy")]))
        elif t == "DIMENSION":
            p2, p3 = e.dxf.get("defpoint2"), e.dxf.get("defpoint3")
            if p2 is None or p3 is None:
                continue
            try:
                meas = float(e.get_measurement())
            except Exception:  # noqa: BLE001 - an unreadable dimension is listed, not dropped
                meas = None
            lf = e.override().get("dimlfac")
            blk = e.get_geometry_block()
            shown = [re.sub(r"\\A\d;", "", (t.dxf.text if t.dxftype() == "TEXT" else t.text))
                     for t in (blk or []) if t.dxftype() in ("TEXT", "MTEXT")]
            ang = float(e.dxf.get("angle") or 0.0) if (e.dxf.dimtype & 7) == 0 else None
            dims.append(dict(handle=e.dxf.handle, p2=(p2[0], p2[1]), p3=(p3[0], p3[1]), measurement=meas, angle=ang,
                             dimlfac=lf, text_override=e.dxf.get("text", ""), layer=lay,
                             shown=" ".join(shown)))
        elif t == "TEXT":
            texts.append((e.dxf.handle, lay, e.dxf.text, (e.dxf.insert[0], e.dxf.insert[1])))
        elif t == "LINE" and lay in ("S-OPENING", "S-TEXT.D"):
            a, b = e.dxf.start, e.dxf.end
            leaders.append((e.dxf.handle, LineString([(a[0], a[1]), (b[0], b[1])])))
    return cuts, labels, titles, outlines, dims, texts, leaders


def view_of(title, outlines):
    _, _, (tx, ty) = title
    best = None
    for h, pts in outlines:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, y0 = min(xs), min(ys)
        if y0 < ty or y0 - ty > TITLE_REACH or abs(x0 - tx) > TITLE_REACH:
            continue
        d = math.hypot(x0 - tx, y0 - ty)
        if best is None or d < best[0]:
            best = (d, h, (x0, y0, max(xs), max(ys)))
    return best


def sections(dxf_path, bands):
    from shapely.geometry import LineString, Point, Polygon
    cuts, labels, titles, outlines, dims, texts, leaders = read(dxf_path)
    out = {"cuts": [], "views": {}}
    for h, pts in cuts:
        ls = LineString([(x / 1000, y / 1000) for x, y in pts])
        ends = [pts[0], pts[-1]]
        lab = sorted({t for _, t, p in labels for e in ends if math.dist(p, e) < 1500})
        reach = [b for b, v in bands.items() if Polygon(v["pts"]).intersects(ls)]
        near = [b for b, v in bands.items() if b not in reach and Polygon(v["pts"]).distance(ls) < 0.5]
        held_reach = [lid for lid, b in T.HELD.items() if b in reach]
        held_near = [lid for lid, b in T.HELD.items() if b in near]
        out["cuts"].append(dict(handle=h, labels=lab, reaches=reach, near=near, held_reached=held_reach,
                                held_near=held_near, length_m=round(ls.length, 3)))
    for th, letter, tp in titles:
        v = view_of((th, letter, tp), outlines)
        if not v:
            out["views"][letter] = {"title": th, "outline": None, "dims": [], "notes": []}
            continue
        _, oh, (x0, y0, x1, y1) = v
        box = (x0 - VIEW_PAD, y0 - VIEW_PAD, x1 + VIEW_PAD, y1 + VIEW_PAD)

        def inside(p):
            return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
        ds = []
        for d in dims:
            if inside(d["p2"]) and inside(d["p3"]):
                a = d["angle"]   # rotated linear dimension: the measured direction is its angle, not the point spread
                axis = ("H" if abs(math.sin(math.radians(a))) < 1e-6 else "V" if abs(math.cos(math.radians(a))) < 1e-6
                        else f"ROT{a:g}") if a is not None else "NOT_LINEAR"
                pv = None if d["measurement"] is None else round(d["measurement"] * (d["dimlfac"] or 1.0), 2)
                ds.append(dict(handle=d["handle"], axis=axis, measurement=d["measurement"], dimlfac=d["dimlfac"],
                               printed=pv, shown=d["shown"], text_override=d["text_override"]))
        notes = []
        nbox = (box[0], box[1], box[2] + NOTE_REACH, box[3])   # notes stand to the right of the view on their leaders
        for h, lay, s, p in texts:
            if nbox[0] <= p[0] <= nbox[2] and nbox[1] <= p[1] <= nbox[3] and lay != "S-TEXT.D":
                on = [lh for lh, g in leaders if g.distance(Point(p)) < 150]
                notes.append(dict(handle=h, layer=lay, text=s, on_leader=on))
        out["views"][letter] = {"title": th, "outline": oh, "outline_w_units": round(x1 - x0, 1),
                                "outline_h_units": round(y1 - y0, 1), "dims": ds, "notes": notes}
    return out


def main(argv):
    dxf, bands_p, out_p = argv[1:4]
    bands = json.load(open(bands_p, encoding="utf-8"))
    res = sections(dxf, bands)
    json.dump(res, open(out_p, "w"), indent=1)
    for c in res["cuts"]:
        print("cut", c["handle"], c["labels"], "reaches", c["reaches"], "held", c["held_reached"], "near-held", c["held_near"])
    for k, v in res["views"].items():
        print("view", k, v["outline"], v.get("outline_w_units"), v.get("outline_h_units"),
              [(d["handle"], d["axis"], d["printed"], d["shown"], d["dimlfac"]) for d in v["dims"]],
              [(n["handle"], n["text"], n["on_leader"]) for n in v["notes"]])


if __name__ == "__main__":
    main(sys.argv)
