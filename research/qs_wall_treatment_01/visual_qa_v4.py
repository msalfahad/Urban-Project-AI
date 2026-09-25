"""VISUAL QA overlays on the ORIGINAL SOURCE pages (directive §20): physical
faces, source dimensions, extension endpoints, virtual closures, excluded
elements, face ids and quantity states, in distinct visual classes. QA
evidence only - no geometry authority.

    python3 -m research.qs_wall_treatment_01.visual_qa_v4
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.cad_links import X_PAIRS, Y_PAIRS

OUT = Path(P.OUT_DIR)
QA = OUT / "visual_qa"
PDF = "data/golden/7757/inputs/P7757_DRAWINGS.pdf"
CLASS = {"PHYSICAL_MATERIAL": (0, 150, 0), "OPENING": (200, 0, 0), "VIRTUAL_MEASUREMENT_CLOSURE": (120, 120, 120),
         "BALUSTRADE": (255, 140, 0), "COPING": (0, 90, 220), "STRUCTURAL_ONLY": (150, 0, 150), "UNRESOLVED": (110, 110, 110),
         "DIMENSION": (220, 0, 160)}


def _native(doc, page_1based):
    pg = doc[page_1based - 1]
    info = doc.extract_image(pg.get_images()[0][0])
    return Image.open(io.BytesIO(info["image"])).convert("RGB"), hashlib.sha256(info["image"]).hexdigest()


def _traces(sheet):
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    return {t["TRACE_ID"]: t for t in reg["TRACES"] if t["SHEET_ID"] == sheet}


def _geom(t):
    g = t["ORIGINAL_PAGE_GEOMETRY"]
    for k in ("PIXEL_POLYGON", "PIXEL_POLYLINE", "PIXEL_BBOX", "TEXT_BBOX", "DIMENSION_LINE_TRACE"):
        if k in g:
            return k, g[k]["COORDINATES"]
    return None, None


def _legend(img, title, lines):
    W = img.width
    pad = Image.new("RGB", (W, 16 * (len(lines) + 1) + 8), "white")
    d = ImageDraw.Draw(pad)
    d.text((6, 4), title, fill=(0, 0, 0))
    for i, (cls, txt) in enumerate(lines):
        d.rectangle([6, 22 + 16 * i, 18, 34 + 16 * i], fill=CLASS[cls])
        d.text((24, 20 + 16 * i), txt, fill=(0, 0, 0))
    out = Image.new("RGB", (W, pad.height + img.height), "white")
    out.paste(pad, (0, 0))
    out.paste(img, (0, pad.height))
    return out


def _dashed(d, a, b, fill, width=2, dash=10):
    (x0, y0), (x1, y1) = a, b
    L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    n = max(1, int(L // dash))
    for i in range(0, n, 2):
        t0, t1 = i / n, min(1.0, (i + 1) / n)
        d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=fill, width=width)


def se_elevation(doc, faces):
    tr = _traces("SOUTH_EAST_ELEVATION")
    img, sha = _native(doc, 4)
    box = (2600, 2450, 3520, 4450)          # native (x0, y0, x1, y1): x carries the levels, y the run
    # crop in native then rotate 90 ccw so the elevation reads upright
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    def T(p):
        return (p[0] - box[0], p[1] - box[1])
    def poly(tid, cls, w=3):
        k, c = _geom(tr[tid])
        pts = [T(p) for p in c] if k in ("PIXEL_POLYGON", "PIXEL_POLYLINE") else None
        if k == "PIXEL_POLYGON":
            d.polygon(pts, outline=CLASS[cls])
            d.line(pts + [pts[0]], fill=CLASS[cls], width=w)
        elif k == "PIXEL_POLYLINE":
            d.line(pts, fill=CLASS[cls], width=w)
        elif k == "PIXEL_BBOX":
            d.rectangle([T((c[0], c[1])), T((c[2], c[3]))], outline=CLASS[cls], width=w)
    for tid, cls in (("PAR-12", "PHYSICAL_MATERIAL"), ("PAR-11", "PHYSICAL_MATERIAL"), ("SEG-04", "PHYSICAL_MATERIAL"),
                     ("PAR-10", "PHYSICAL_MATERIAL"), ("BAL-03", "BALUSTRADE"), ("PAR-13", "COPING"), ("UNK-09", "UNRESOLVED")):
        poly(tid, cls)
    for tid in ("DIM-21", "DIM-20", "DIM-18", "DIM-19", "DIM-15"):
        g = tr[tid]["ORIGINAL_PAGE_GEOMETRY"]
        if "DIMENSION_LINE_TRACE" in g:
            c = g["DIMENSION_LINE_TRACE"]["COORDINATES"]
            d.line([T(c[0]), T(c[1])], fill=CLASS["DIMENSION"], width=2)
            for p in c:
                d.ellipse([T(p)[0] - 5, T(p)[1] - 5, T(p)[0] + 5, T(p)[1] + 5], outline=CLASS["DIMENSION"], width=2)
        for k in ("EXTENSION_LINE_A", "EXTENSION_LINE_B"):
            if k in g:
                c = g[k]["COORDINATES"]
                _dashed(d, T(c[0]), T(c[1]), CLASS["DIMENSION"], 1, 8)
        if "TEXT_BBOX" in g:
            c = g["TEXT_BBOX"]["COORDINATES"]
            d.rectangle([T((c[0], c[1])), T((c[2], c[3]))], outline=CLASS["DIMENSION"], width=2)
    crop = crop.rotate(90, expand=True)
    d = ImageDraw.Draw(crop)
    fx = {f["FACE_ID"]: f for f in faces}
    labels = [("F-SE-SOLID-EXT", 1350, 20), ("F-SE-KERB-EXT", 750, 20), ("F-SE-BAL", 750, 36), ("F-SE-CAP-EDGE-EXT", 1350, 36), ("F-SE-PIER-EXT", 600, 52), ("F-TOWER-RING-EXT", 40, 20)]
    for fid, x, y in labels:
        f = fx.get(fid)
        if f:
            a = f["AREA"]
            d.text((x, y), f"{fid}: h={f['FACE_HEIGHT']} L={f['FACE_LENGTH_M']} A={a['GROSS_AREA_M2']} {a['QUANTITY_STATE']}", fill=(0, 0, 0))
    k = 0.6
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - SOUTH EAST ELEVATION (original page 4, native scan) - faces, source dimensions, extension endpoints",
                  [("PHYSICAL_MATERIAL", "solid plasterable faces (PAR-12 solid portion, PAR-11 kerb, SEG-04 pier, PAR-10 tower ring)"),
                   ("BALUSTRADE", "open lattice BAL-03: PLASTERABLE_SOLID_FACE = 0"), ("COPING", "band / capping PAR-13: separate item"),
                   ("UNRESOLVED", "base line UNK-09 (+9.88 finish level candidate)"), ("DIMENSION", "printed dimensions DIM-21/20/18/19/15 with tick endpoints and witness lines")])
    p = QA / "SE_ELEVATION_FACES.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 4, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


def roof_plan(doc, link, asm):
    tr = _traces("SECOND_FLOOR_ROOF_PLAN")
    img, sha = _native(doc, 3)
    # PROVISIONAL registration for QA only: the PAR-01 outer face polyline spans the 7.50 m outer face
    k_, c = _geom(tr["SEG-01"])
    x_ne, x_sw = c[0][0], c[1][0]             # the straight outer-face span before the corner arc
    y_out = c[0][1]
    s = (x_sw - x_ne) / 7500.0                 # px per mm over the traced straight span (PROVISIONAL, QA only)
    outer = link["SE_ROOF_EDGE_AUTHORED"]["OUTER_FACE"]
    X0, Y0 = outer["X_MM"], outer["Y_FROM_MM"]
    def N(cx, cy):
        return (x_ne + (cy - Y0) * s, y_out + (cx - X0) * s)
    box = (1300, 2350, 2800, 5700)      # native (x0, y0, x1, y1)
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    def T(p):
        return (p[0] - box[0], p[1] - box[1])
    def line(cx0, cy0, cx1, cy1, cls, w=3, dashed=False):
        a, b = T(N(cx0, cy0)), T(N(cx1, cy1))
        (_dashed(d, a, b, CLASS[cls], w) if dashed else d.line([a, b], fill=CLASS[cls], width=w))
    sol = link["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"]
    lat = link["PORTIONS_PROPOSED"]["LATTICE_KERB_PORTION_SW"]
    line(X0, sol["Y_FROM_MM"], X0, sol["Y_TO_MM"], "PHYSICAL_MATERIAL")                 # SE solid portion outer face
    line(X0 + 200, sol["Y_FROM_MM"] + 200, X0 + 200, sol["Y_TO_MM"], "PHYSICAL_MATERIAL")  # roof-side face
    line(X0, lat["Y_FROM_MM"], X0, lat["Y_TO_MM"], "PHYSICAL_MATERIAL", 2)               # kerb outer
    line(X0 + 250, lat["Y_FROM_MM"], X0 + 250, lat["Y_TO_MM"], "BALUSTRADE", 3, dashed=True)  # lattice over the kerb
    for r in link["SE_ROOF_EDGE_AUTHORED"]["CROSS_LINES"]:
        line(r["X_FROM_MM"], r["Y_MM"], r["X_TO_MM"], r["Y_MM"], "UNRESOLVED", 2)
    for r in link["SE_ROOF_EDGE_AUTHORED"]["NE_INNER_RETURN"]:
        line(r["X_FROM_MM"], r["Y_MM"], r["X_TO_MM"], r["Y_MM"], "PHYSICAL_MATERIAL", 2)   # NE parapet roof-side 18.87
    line(X0, Y0, X0 + 18270, Y0, "PHYSICAL_MATERIAL", 2)                                   # NE outer 18.27
    for r in link["SE_ROOF_EDGE_AUTHORED"]["SW_EDGE_LINES"]:
        line(r["X_FROM_MM"], r["Y_MM"], r["X_TO_MM"], r["Y_MM"], "UNRESOLVED", 2, dashed=True)  # SW parapet: height NOT_ESTABLISHED
    for dm in link["ROOF_PLAN_COPY"]["DOMES"]:
        cx, cy = T(N(dm["CENTRE_MM"][0], dm["CENTRE_MM"][1]))
        r = dm["RADIUS_MM"] * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CLASS["STRUCTURAL_ONLY"], width=1)
    k_, c = _geom(tr["UNK-04"])
    d.polygon([T(p) for p in c], outline=CLASS["UNRESOLVED"])
    d.text(T((1440, 2300)), "NE parapet (F-NE-SOLID): 18.87 roof-side, h 1.65 (A-A) PROVISIONAL", fill=(0, 0, 0))
    d.text(T((1440 + 0.35 * (x_sw - x_ne), 2560)), "SE solid portion 3.683 PROVISIONAL", fill=(0, 0, 0))
    d.text(T((x_sw - 0.45 * (x_sw - x_ne), 2560)), "kerb 3.767 + lattice (zero) PROPOSED split", fill=(0, 0, 0))
    d.text(T((2700, 2620)), "SW parapet 4.33: height NOT_ESTABLISHED", fill=(0, 0, 0))
    d.text(T((1470, 5450)), "NW thin element 10 x 130: UNRESOLVED", fill=(0, 0, 0))
    crop = crop.rotate(90, expand=True)
    k = 0.45
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - SECOND FLOOR ROOF PLAN (original page 3) - DWG roof-edge lines projected by a PROVISIONAL registration (QA only)",
                  [("PHYSICAL_MATERIAL", "solid parapet faces (SE solid portion, NE parapet outer / roof-side)"),
                   ("BALUSTRADE", "lattice portion over the kerb (zero plaster)"), ("UNRESOLVED", "SW parapet (no height), cross line, NW thin element"),
                   ("STRUCTURAL_ONLY", "dome circles (locator only)")])
    p = QA / "ROOF_PLAN_EDGES.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 3, "SOURCE_SHA256": sha, "REGISTRATION": {"PX_PER_MM": round(s, 5), "STATUS": "PROVISIONAL_QA_ONLY"},
            "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


def gf_plan(doc, st):
    tr = _traces("GROUND_FLOOR_PLAN")
    any_t = next(iter(tr.values()))
    Tf = any_t["ORIGINAL_PAGE_COORDINATE_TRANSFORM"]
    img, sha = _native(doc, 1)
    def fit(pairs):
        n = len(pairs)
        sx = sum(m for m, _, _ in pairs); sy = sum(p for _, p, _ in pairs)
        sxx = sum(m * m for m, _, _ in pairs); sxy = sum(m * p for m, p, _ in pairs)
        b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        return (sy - b * sx) / n, b
    ax, bx = fit(X_PAIRS)
    ay, by = fit(Y_PAIRS)
    def N(cx, cy):
        px, py = ax + bx * cx, ay + by * cy                        # processed px
        xr, yr = px / Tf["scale"] + Tf["trim_x0"], py / Tf["scale"] + Tf["trim_y0"]
        return ((Tf["W_orig"] - 1) - yr, xr)                        # native
    loop = st["D2"]["LOCATION"]["CAD_LOOP_MM"]
    cx, cy = (loop[0] + loop[2]) / 2, (loop[1] + loop[3]) / 2
    c0 = N(cx, cy)
    box = (int(c0[0]) - 700, int(c0[1]) - 700, int(c0[0]) + 700, int(c0[1]) + 700)
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    def T(p):
        return (p[0] - box[0], p[1] - box[1])
    pts = [T(N(loop[0], loop[1])), T(N(loop[2], loop[1])), T(N(loop[2], loop[3])), T(N(loop[0], loop[3]))]
    d.polygon(pts, outline=CLASS["STRUCTURAL_ONLY"])
    d.line(pts + [pts[0]], fill=CLASS["STRUCTURAL_ONLY"], width=4)
    for name, beams in st["D2"]["STUB_LINE_CAD_783"]["EVIDENCE"].items():
        for b in beams:
            if b["LENGTH_M"] < 0.8:
                continue
            _dashed(d, T(N(*b["CAD_FROM_MM"])), T(N(*b["CAD_TO_MM"])), CLASS["STRUCTURAL_ONLY"], 2, 12)
    d.line([T(N(-129070, -805093.5)), T(N(-134219.9, -805093.5))], fill=CLASS["PHYSICAL_MATERIAL"], width=4)   # SEG-02 5.15 face
    _dashed(d, T(N(-134219.9, -805093.5)), T(N(-134219.9, -803793.5)), CLASS["VIRTUAL_MEASUREMENT_CLOSURE"], 3, 14)  # open edge, no material
    d.text((10, 10), "D2: LOOP-059 column 30x60 (ST7757 p1, registered <=55 mm): COLUMN_EXISTS ESTABLISHED", fill=(0, 0, 0))
    d.text((10, 26), "EXPOSED_TO_ROOM ESTABLISHED_PROVISIONAL (free-standing, beams to the wall p3/p4); OWNS_CLEAR_FACE: NO", fill=(0, 0, 0))
    d.text((10, 42), "column bonding girth 1.80 lm x 3.20 = 5.76 m2 PROVISIONAL (OWNER height)", fill=(0, 0, 0))
    crop = crop.rotate(90, expand=True)
    k = 0.6
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - GROUND FLOOR PLAN (original page 1) - D2 column at the SALOON / RECEPTION open edge",
                  [("STRUCTURAL_ONLY", "structural column (30 x 60) and beams (ST7757.pdf p3 ground beam, p4 GF roof-slab beams)"),
                   ("PHYSICAL_MATERIAL", "SEG-02 5.15 m owner-verified plaster face"), ("VIRTUAL_MEASUREMENT_CLOSURE", "open edge wall -> column: no material, never a wall")])
    p = QA / "GF_PLAN_D2_COLUMN.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 1, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


def run() -> dict:
    QA.mkdir(exist_ok=True)
    doc = pymupdf.open(PDF)
    faces = json.loads((OUT / "FACE_MEASUREMENT_REGISTER.json").read_text("utf-8"))["FACES"]
    link = json.loads((OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json").read_text("utf-8"))
    asm = json.loads((OUT / "PARAPET_ASSEMBLY_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "VISUAL_QA", "VISUAL_CLASSES": list(CLASS),
           "OVERLAYS": [se_elevation(doc, faces), roof_plan(doc, link, asm), gf_plan(doc, st)],
           "A_VISUAL_OVERLAY_IS_QA_EVIDENCE_NOT_GEOMETRY_AUTHORITY": True}
    (OUT / "VISUAL_QA.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
