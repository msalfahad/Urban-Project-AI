"""Experiment D: the deterministic raster prototype (tests/m9_p2b5_bench/vision.py) on DXF fixtures rendered here
(ezdxf read, PIL drawing with the benchmark's pens), against the engine's CAD values. argv: repo tree, out dir, dxf..."""
import json, math, sys
from pathlib import Path
tree, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(tree / "tests" / "m9_p2b5_bench"))
import bench_drawings as BD, vision as VI
import ezdxf
from PIL import Image, ImageDraw, ImageFont

def render(dxf, png, mm_per_px=10.0):
    doc = ezdxf.readfile(str(dxf)); msp = doc.modelspace()
    k = 1000.0 if doc.header.get("$INSUNITS", 4) == 6 else 1.0
    segs, texts = [], []
    for e in msp:
        L = e.dxf.layer
        if L in ("A-FRAME", "A-TITLE"):
            continue
        if e.dxftype() == "LINE":
            segs.append((L, [(e.dxf.start.x * k, e.dxf.start.y * k), (e.dxf.end.x * k, e.dxf.end.y * k)]))
        elif e.dxftype() == "ARC":
            segs.append((L, [(v.x * k, v.y * k) for v in e.flattening(1.0 / k)]))
        elif e.dxftype() == "TEXT":
            texts.append((e.dxf.text, (e.dxf.insert.x * k, e.dxf.insert.y * k), e.dxf.height * k))
    xs = [p[0] for _, s in segs for p in s]; ys = [p[1] for _, s in segs for p in s]
    x0, y0, x1, y1 = min(xs) - 500, min(ys) - 500, max(xs) + 500, max(ys) + 500
    W, H = int(math.ceil((x1 - x0) / mm_per_px)), int(math.ceil((y1 - y0) / mm_per_px))
    img = Image.new("L", (W, H), 255); d = ImageDraw.Draw(img)
    P = lambda p: ((p[0] - x0) / mm_per_px, (y1 - p[1]) / mm_per_px)
    for L, s in segs:
        pen = BD.WALL_PEN_MM if L in ("A-WALL", "A-COL") else BD.THIN_PEN_MM
        d.line([P(p) for p in s], fill=0, width=max(1, int(round(pen / mm_per_px))))
    for t, p, h in texts:
        if h >= 200:
            d.text(P(p), t, fill=0, font=ImageFont.load_default(size=max(6, int(round(h / mm_per_px)))), anchor="ls")
    img.save(str(png))
    return {"x0": x0, "y1": y1, "mm_per_px": mm_per_px, "w": W, "h": H, "scan": False, "face_pen_mm": BD.WALL_PEN_MM}

res = {}
for f in sys.argv[3:]:
    f = Path(f); png = out / (f.stem + ".png")
    meta = render(f, png)
    r = VI.raster_rooms(png, meta)
    res[f.stem] = {"rooms": [{"label": x["label"], "area_m2": round(x["area_m2"], 4)} for x in r["rooms"]],
                   "openings": [{"kind": o.get("kind"), "width_m": round(o.get("width_m") or 0, 3)} for o in r["openings"]],
                   "wall_thickness_mm": r["wall_thickness_mm"], "deskew_deg": r["deskew_deg"]}
print(json.dumps(res, indent=1))
