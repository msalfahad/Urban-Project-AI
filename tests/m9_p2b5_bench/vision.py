"""VISION PROTOTYPE - Phase 2B-5 Stage F, an isolated, deterministic baseline (no trained model; no network; never
part of the production BOQ). Two readers of a drawing that has no CAD entities:

    raster_rooms(png, meta)       a raster plan (scan or render) at a known scale (mm per pixel):
        1. dark pixels (a median filter first on a scan) -> wall faces; closing (5 px) merges the two faces of a wall
           into a band; opening (3 px) removes thin features (door leaves and swings, text, hatch noise)
        2. door gaps: wall pixels added by closing the bands along rows and columns with a line of the largest door
           width (1.10 m) - only gaps bounded by wall on both sides close
        3. rooms: 4-connected components of free space less the gaps, the component touching the border (outside) and
           components smaller than 0.25 m2 (column cores, wall cavities) removed
        4. each room's polygon: the union of its pixel runs, grown by half a face line (the face line's centre is the
           wall face), simplified by 0.75 px; its label: the Tesseract word whose box centre lies in the room
        5. gaps next to removed thin linework (a swing) are doors, others passages; the wall-band thickness gives a
           scale check (a 200 mm wall at the given scale)
    vector_pdf_rooms(pdf, meta)   a vector PDF at a known scale: its stroked paths as segments (PyMuPDF), the wall
        faces kept (a segment with a parallel partner at a wall thickness, or a short jamb between two faces), then
        the same closures and polygonisation as the CAD reference reader; labels from the PDF words.

Every result carries NOT_SUPPORTED where a step cannot be done (no OCR, no scale, no PDF engine)."""

from __future__ import annotations

import math
import shutil
import subprocess
import time

MAX_GAP_MM = 1100.0
MIN_ROOM_M2 = 0.25


def _ocr_words(png, upscale=3):
    """Tesseract words with their boxes (pixels of the image given); the image is upscaled for the OCR (small plan
    text). [] and a reason if Tesseract is not installed."""
    import tempfile
    from pathlib import Path
    from PIL import Image
    exe = shutil.which("tesseract")
    if not exe:
        return [], "NOT_SUPPORTED: tesseract not installed"
    im = Image.open(png).convert("L")
    big = im.resize((im.width * upscale, im.height * upscale), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(dir=str(Path(png).parent), suffix=".png", delete=False) as f:
        tmp = Path(f.name)
    big.save(str(tmp))
    r = subprocess.run([exe, str(tmp), "stdout", "--psm", "11", "-l", "eng", "tsv"], capture_output=True, text=True)
    tmp.unlink()
    out = []
    for ln in r.stdout.splitlines()[1:]:
        f = ln.split("\t")
        if len(f) == 12 and f[11].strip() and f[10] not in ("-1",) and float(f[10]) >= 40:
            x, y, w, h = (int(v) / upscale for v in f[6:10])
            out.append({"text": f[11].strip(), "cx": x + w / 2, "cy": y + h / 2, "conf": float(f[10]),
                        "box": (int(x), int(y), int(math.ceil(x + w)), int(math.ceil(y + h)))})
    return out, "OK"


def _clean_marks(dark, mm, ndi, np):
    """removes isolated marks (text, symbols: dark components whose box is under 0.6 m that do not touch the wall
    network) and fills small hollow squares (column outlines) solid."""
    lab, n = ndi.label(dark, structure=np.ones((3, 3)))
    out = dark.copy()
    lim = 600.0 / mm
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if max(h, w) >= lim:
            continue
        comp = lab[sl] == i
        border = np.zeros_like(comp)
        border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
        if min(h, w) >= 3 and (comp & border).sum() >= 0.9 * border.sum() and abs(h - w) <= 2:
            out[sl] |= ndi.binary_fill_holes(comp)                 # a column outline: solid obstruction
        else:
            out[sl] &= ~comp                                          # text / mark
    return out


def _deskew(a, np, Image):
    """the rotation (degrees) that makes the plan's linework axis-parallel: the dominant gradient orientation modulo
    90 degrees (orientation quadrupling, gradient-energy weighted), its sign checked on the row / column profiles."""
    from scipy import ndimage as ndi
    f = ndi.gaussian_filter(a.astype(float), 1.0)
    gy, gx = np.gradient(f)
    w = gx * gx + gy * gy
    phi = np.arctan2(gy, gx)
    th = math.degrees(math.atan2((w * np.sin(4 * phi)).sum(), (w * np.cos(4 * phi)).sum()) / 4.0)
    m = Image.fromarray(((a < 160) * 255).astype("uint8"))

    def score(t):
        b = np.asarray(m.rotate(t, resample=Image.NEAREST, expand=True, fillcolor=0)) > 0
        return float(b.sum(0).var() + b.sum(1).var())
    th = max((th, -th), key=score)
    if abs(th) < 2.0:
        return 0.0                                                # a small skew is tolerated, never "corrected"
    return round(float(max(np.arange(th - 3.0, th + 3.0001, 0.1), key=score)), 2)


def raster_rooms(png, meta, debug=None):
    import tempfile
    from pathlib import Path
    import numpy as np
    from PIL import Image
    from scipy import ndimage as ndi
    from shapely.geometry import box
    from shapely.ops import unary_union
    t0 = time.time()
    img = Image.open(png).convert("L")
    w0, h0 = img.size
    a0 = np.asarray(img)
    th = _deskew(a0, np, Image)
    if abs(th) >= 0.05:
        img = img.rotate(th, resample=Image.BILINEAR, expand=True, fillcolor=255)
    W, H = img.size
    t = math.radians(th)

    def back(xp, yp):                                             # deskewed pixel -> original pixel
        dx, dy = xp - W / 2, yp - H / 2
        return (w0 / 2 + dx * math.cos(t) - dy * math.sin(t), h0 / 2 + dx * math.sin(t) + dy * math.cos(t))
    a = np.asarray(img)
    with tempfile.NamedTemporaryFile(dir=str(Path(png).parent), suffix=".png", delete=False) as f:
        tmp = Path(f.name)
    img.save(str(tmp))
    words, ocr_state = _ocr_words(tmp)
    tmp.unlink()
    mm = meta["mm_per_px"]
    # a word is a room word only if it reads as one: two letters or more, confident, of plan-text height
    words = [wd for wd in words if sum(ch.isalnum() for ch in wd["text"]) >= 2 and wd["conf"] >= 60
             and (wd["box"][3] - wd["box"][1]) * mm <= 400.0]
    dark = a < (200 if meta.get("scan") else 128)
    if meta.get("scan"):                                          # isolated noise pixels
        lab0, n0 = ndi.label(dark, structure=np.ones((3, 3)))
        sz = ndi.sum(np.ones_like(lab0), lab0, index=range(n0 + 1))
        dark &= sz[lab0] >= 4
    for wd in words:                                              # the room words are not linework
        x0w, y0w, x1w, y1w = wd["box"]
        dark[max(0, y0w - 1):y1w + 1, max(0, x0w - 1):x1w + 1] = False
    dark = _clean_marks(dark, mm, ndi, np)
    k = max(3, int(round(220.0 / mm)) | 1)                     # bridges the space between a 200 mm wall's faces
    walls = ndi.binary_closing(dark, structure=np.ones((k, k)), iterations=1)
    ko = max(2, int(round(150.0 / mm)))                         # thinner than a wall: leaves, swings, glazing, text
    walls_open = ndi.binary_opening(walls, structure=np.ones((ko, ko)))
    thin = (dark & ~walls_open) | (walls & ~walls_open)
    walls = walls_open
    L = int(math.ceil(MAX_GAP_MM / mm)) + 1
    gh = ndi.binary_closing(walls, structure=np.ones((1, L))) & ~walls
    gv = ndi.binary_closing(walls, structure=np.ones((L, 1))) & ~walls
    gaps = gh | gv
    glab0, gn0 = ndi.label(gaps)
    for j, sl in enumerate(ndi.find_objects(glab0), 1):           # a door gap is only a wall thickness deep
        if min(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start) * mm > 320.0:
            gaps[sl] &= glab0[sl] != j
    free = ~walls & ~gaps
    if debug is not None:
        debug.update(dark=dark, walls=walls, gaps=gaps, thin=thin, words=words)
    lab, n = ndi.label(free)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    px_m2 = (mm / 1000.0) ** 2
    sizes = ndi.sum(np.ones_like(lab), lab, index=range(n + 1))
    # small pockets (a door swing closed off by its leaf and arc) join the room they touch across thin linework
    big = {i for i in range(1, n + 1) if i not in border and sizes[i] * px_m2 >= 1.2}
    merged = {i: i for i in big}
    for i in range(1, n + 1):
        if i in border or i in big or sizes[i] * px_m2 < 0.05:
            continue
        ring = ndi.binary_dilation(lab == i, iterations=2)
        near = [j for j in np.unique(lab[ring]) if j in big]
        if len(near) == 1:
            merged[i] = near[0]
    rooms = []
    x0, y1 = meta["x0"], meta["y1"]
    for r in sorted(big):
        m = np.isin(lab, [i for i, j in merged.items() if j == r])
        rows = []
        ys, xs = np.nonzero(m)
        for y in np.unique(ys):
            xr = np.sort(xs[ys == y])
            starts = np.concatenate([[xr[0]], xr[1:][np.diff(xr) > 1]])
            ends = np.concatenate([xr[:-1][np.diff(xr) > 1], [xr[-1]]])
            rows += [box(s, y, e + 1, y + 1) for s, e in zip(starts, ends)]
        grow = (meta.get("face_pen_mm") or mm) / 2.0 / mm         # the face line's centre is the wall face
        poly = unary_union(rows).buffer(grow, join_style=2).simplify(0.75)
        if poly.geom_type != "Polygon":
            poly = max(poly.geoms, key=lambda g: g.area)
        ring = []
        for p in poly.exterior.coords:
            q = back(*p)
            ring.append((x0 + q[0] * mm, y1 - q[1] * mm))
        grown = ndi.binary_dilation(m, iterations=2)
        label = [wd["text"] for wd in words if 0 <= int(wd["cy"]) < m.shape[0] and 0 <= int(wd["cx"]) < m.shape[1]
                 and grown[int(wd["cy"]), int(wd["cx"])]]
        rooms.append({"label": " ".join(label) or None, "polygon_mm": ring, "area_m2": poly.area * px_m2,
                      "perimeter_m": poly.length * mm / 1000.0, "pixels": int(m.sum()), "component": int(r)})
    glab, gn = ndi.label(gaps)
    openings = []
    for j in range(1, gn + 1):
        g = glab == j
        ys, xs = np.nonzero(g)
        w_px = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) + 1    # jamb centre to jamb centre
        if w_px * mm < 300:
            continue
        touch = ndi.binary_dilation(g, iterations=1)
        rooms_touching = sorted({int(merged[int(v)]) for v in np.unique(lab[touch]) if v and int(v) in merged})
        beside = ndi.binary_dilation(g, iterations=int(math.ceil(400.0 / mm))) & ~g & ~walls
        if (g & thin).sum() >= 0.3 * g.sum():
            kind = "WINDOW"                                       # glazing lines inside the wall gap
        elif (beside & thin).sum() >= 0.5 * w_px:
            kind = "DOOR"                                         # a leaf / swing beside the gap
        else:
            kind = "PASSAGE"
        openings.append({"kind": kind, "width_m": round(float(w_px * mm) / 1000.0, 3), "rooms": rooms_touching})
    # scale check: the wall bands' thickness - twice the distance-transform ridge less one pixel and one face line
    dt = ndi.distance_transform_edt(walls)
    ridge = dt[(dt >= 1) & (dt >= ndi.maximum_filter(dt, size=3))]
    wall_mm = float((2 * np.median(ridge) - 2) * mm) if ridge.size else None
    if wall_mm is None:
        scale_check = "SCALE_SUSPECT: no wall band at the stated scale"
    elif abs(wall_mm - 200.0) > 50.0:
        scale_check = f"SCALE_SUSPECT: walls read {wall_mm:.0f} mm at the stated scale"
    else:
        scale_check = "OK"
    return {"rooms": rooms, "openings": openings, "ocr": ocr_state, "deskew_deg": th, "wall_thickness_mm": wall_mm,
            "scale_check": scale_check,
            "runtime_s": round(time.time() - t0, 3), "status": "OK"}


def _pdf_segments(pdf, meta):
    try:
        import pymupdf
    except Exception:                                             # pragma: no cover
        return None, [], "NOT_SUPPORTED: no PDF engine"
    doc = pymupdf.open(str(pdf))
    page = doc[0]
    W, H = page.rect.width, page.rect.height
    sx = (meta["x1"] - meta["x0"]) / W
    sy = (meta["y1"] - meta["y0"]) / H
    T = lambda p: (meta["x0"] + p.x * sx, meta["y1"] - p.y * sy)                # noqa: E731
    segs = []
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                segs.append((T(it[1]), T(it[2])))
            elif it[0] == "re":
                r = it[1]
                if r.width >= 0.95 * W and r.height >= 0.95 * H:
                    continue                                      # the page background
                pts = [pymupdf.Point(r.x0, r.y0), pymupdf.Point(r.x1, r.y0), pymupdf.Point(r.x1, r.y1),
                       pymupdf.Point(r.x0, r.y1)]
                segs += [(T(pts[i]), T(pts[(i + 1) % 4])) for i in range(4)]
            elif it[0] == "qu":
                q = it[1]
                pts = [q.ul, q.ur, q.lr, q.ll]
                segs += [(T(pts[i]), T(pts[(i + 1) % 4])) for i in range(4)]
    words = [{"text": w[4], "x": meta["x0"] + (w[0] + w[2]) / 2 * sx, "y": meta["y1"] - (w[1] + w[3]) / 2 * sy}
             for w in page.get_text("words")]
    return segs, words, "OK"


def _wall_faces(segs, lo=30.0, hi=320.0):
    """the segments that read as wall faces: a parallel partner at a wall thickness overlapping it, or a short jamb
    whose two ends touch such faces."""
    import ref_reader as RR
    keys = [RR._line_key(a, b) for a, b in segs]
    faces = set()
    for i, (a, b) in enumerate(segs):
        ang, u, off = keys[i]
        s0, s1 = sorted((u[0] * a[0] + u[1] * a[1], u[0] * b[0] + u[1] * b[1]))
        for j, (c, d) in enumerate(segs):
            if i == j:
                continue
            ang2, _, off2 = keys[j]
            if not RR._same_dir(ang, ang2) or not lo <= abs(off2 - off) <= hi:
                continue
            p0, p1 = sorted((u[0] * c[0] + u[1] * c[1], u[0] * d[0] + u[1] * d[1]))
            if min(p1, s1) - max(p0, s0) >= 0.5 * min(s1 - s0, p1 - p0) and min(s1 - s0, p1 - p0) > 1.0:
                faces.add(i)
                break

    def on_face(p):
        for k in faces:
            a, b = segs[k]
            ab = (b[0] - a[0], b[1] - a[1])
            t = ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / max(ab[0] ** 2 + ab[1] ** 2, 1e-9)
            q = (a[0] + max(0, min(1, t)) * ab[0], a[1] + max(0, min(1, t)) * ab[1])
            if math.dist(p, q) <= 2.0:
                return True
        return False
    jambs = {i for i, (a, b) in enumerate(segs) if i not in faces and math.dist(a, b) <= hi and on_face(a) and on_face(b)}
    # free-standing obstructions: the edges of small closed rectangles (columns)
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    cols = set()
    for f in polygonize(unary_union([LineString([a, b]) for a, b in segs])):
        q = f.minimum_rotated_rectangle
        if f.area < 1.0e6 and len(f.exterior.coords) == 5 and abs(f.area - q.area) <= 1e-3 * q.area:
            for i, (a, b) in enumerate(segs):
                if LineString([a, b]).within(f.exterior.buffer(1.0)):
                    cols.add(i)
    return [segs[i] for i in sorted(faces | jambs | cols)]


def vector_pdf_rooms(pdf, meta, labels=None):
    import ref_reader as RR
    from shapely.geometry import LineString, Point
    from shapely.ops import polygonize, unary_union
    t0 = time.time()
    segs, words, state = _pdf_segments(pdf, meta)
    if segs is None:
        return {"rooms": [], "status": state}
    walls = _wall_faces([(a, b) for a, b in segs if math.dist(a, b) > 0.5])
    cl = RR.closures(walls)
    faces = list(polygonize(unary_union([LineString([a, b]) for a, b in walls] + [LineString(list(c)) for c in cl])))
    rooms = []
    for w in words:
        if labels is not None and w["text"] not in labels:
            continue
        cand = [f for f in faces if f.contains(Point(w["x"], w["y"]))]
        if not cand:
            continue
        f = min(cand, key=lambda q: q.area)
        rooms.append({"label": w["text"], "polygon_mm": [tuple(p) for p in f.exterior.coords], "area_m2": f.area / 1e6,
                      "perimeter_m": f.exterior.length / 1000.0})
    return {"rooms": rooms, "closures": len(cl), "runtime_s": round(time.time() - t0, 3), "status": state}
