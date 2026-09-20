"""PA02 visual QA overlays on the original pages: FF void / stair well
(page 2), SE facade openings (page 4), NE parapet top (page 7), NW roof
edge (page 6). QA evidence only.

    python3 -m research.qs_wall_treatment_01.pa02_visual_qa
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
from research.qs_wall_treatment_01.visual_qa_v4 import CLASS, _dashed, _legend, _native

OUT = Path(P.OUT_DIR)
QA = OUT / "visual_qa"
PDF = "data/golden/7757/inputs/P7757_DRAWINGS.pdf"
GF2FF = -44852.65


def _fit(pairs):
    n = len(pairs)
    sx = sum(m for m, _, _ in pairs); sy = sum(p for _, p, _ in pairs)
    sxx = sum(m * m for m, _, _ in pairs); sxy = sum(m * p for m, p, _ in pairs)
    b = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return (sy - b * sx) / n, b


def _gf_native_mapper(Tf):
    ax, bx = _fit(X_PAIRS)
    ay, by = _fit(Y_PAIRS)
    def N(cx, cy):
        px, py = ax + bx * cx, ay + by * cy
        xr, yr = px / Tf["scale"] + Tf["trim_x0"], py / Tf["scale"] + Tf["trim_y0"]
        return ((Tf["W_orig"] - 1) - yr, xr)
    return N


def ff_void_stair(doc):
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    Tf = next(t for t in reg["TRACES"] if t["SHEET_ID"] == "FIRST_FLOOR_PLAN")["ORIGINAL_PAGE_COORDINATE_TRANSFORM"]
    dh = json.loads((OUT / "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json").read_text("utf-8"))
    img, sha = _native(doc, 2)
    N = _gf_native_mapper(Tf)          # FF copy coords shifted into GF coords; the FF sheet layout matches the GF sheet (trim 254/240 vs 258/240)
    void = dh["DOUBLE_HEIGHT_FACE_REGISTER"]["VOID"]
    vx = [v - GF2FF for v in void["X_MM"]]
    vy = void["Y_MM"]
    c0 = N((vx[0] + vx[1]) / 2, (vy[0] + vy[1]) / 2)
    box = (int(c0[0]) - 900, int(c0[1]) - 900, int(c0[0]) + 900, int(c0[1]) + 900)
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    T = lambda p: (p[0] - box[0], p[1] - box[1])
    pts = [T(N(vx[0], vy[0])), T(N(vx[1], vy[0])), T(N(vx[1], vy[1])), T(N(vx[0], vy[1]))]
    for i in range(4):
        _dashed(d, pts[i], pts[(i + 1) % 4], CLASS["VIRTUAL_MEASUREMENT_CLOSURE"], 4, 16)
    st = dh["STAIR_WELL_FACE_REGISTER"]
    bx0, bx1 = -235045.2 + 89705.3, -232245.2 + 89705.3
    by0, by1 = -797193.5, -791993.5
    q = [T(N(bx0, by0)), T(N(bx1, by0)), T(N(bx1, by1)), T(N(bx0, by1))]
    d.line(q + [q[0]], fill=CLASS["PHYSICAL_MATERIAL"], width=4)
    sp0, sp1 = -233595.2 + 89705.3, -233395.2 + 89705.3
    d.rectangle([T(N(sp0, -796494)), T(N(sp1, -793144))], outline=CLASS["UNRESOLVED"], width=3)
    d.text((10, 10), f"FF VOID over the RECEPTION: {void['W_M']} x {void['D_M']} m (DWG X-ed rectangle) - stair well bounded by railings, NO double-height wall", fill=(0, 0, 0))
    d.text((10, 26), "block stair well box 2.8 x 5.2 (PROPOSED) - four wall faces per storey; spine element between flights UNRESOLVED", fill=(0, 0, 0))
    crop = crop.rotate(90, expand=True)
    k = 0.5
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - FIRST FLOOR PLAN (original page 2) - reception void and block stair well (GF sheet registration reused: PROVISIONAL, QA only)",
                  [("VIRTUAL_MEASUREMENT_CLOSURE", "FF void footprint (open well, railings): zero wall"), ("PHYSICAL_MATERIAL", "block stair well wall faces (box)"),
                   ("UNRESOLVED", "spine element between the flights: wall or balustrade wall")])
    p = QA / "FF_VOID_STAIR.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 2, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "REGISTRATION": "GF sheet pairs reused on the FF sheet (PROVISIONAL, QA only)"}


def se_openings(doc):
    ref = json.loads((OUT / "ROOF_EDGES_FACADE_FINISH_KERB.json").read_text("utf-8"))
    img, sha = _native(doc, 4)
    box = (1150, 2200, 3300, 3800)
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    T = lambda p: (p[0] - box[0], p[1] - box[1])
    for o in ref["SE_FACADE_OPENING_REGISTER"]:
        b = o.get("NATIVE_BOX_PAGE4")
        if not b:
            continue
        d.rectangle([T((b[0], b[1])), T((b[2], b[3]))], outline=CLASS["OPENING"], width=4)
    crop = crop.rotate(90, expand=True)
    d = ImageDraw.Draw(crop)
    y = 8
    for o in ref["SE_FACADE_OPENING_REGISTER"]:
        d.text((8, y), f"{o['OPENING_ID']}: {o['WIDTH']} x {o['HEIGHT']} {o['SHAPE']} A={o['AREA']} {o['STATUS']}", fill=(0, 0, 0))
        y += 14
    for fid, f in ref["SE_FACADE_FACES"].items():
        d.text((8, y), f"{fid}: gross {f['GROSS_M2']} - openings {f['OPENING_DEDUCTIONS_M2']} = net {f['NET_M2']} ({f['QUANTITY_STATE']})", fill=(0, 0, 0))
        y += 14
    k = 0.55
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - SOUTH EAST ELEVATION (original page 4) - facade openings (orchestrator reads, printed dimensions cited); finish system UNKNOWN",
                  [("OPENING", "openings: tower strip windows (arched top = rect + semicircle), base door, grill window 215 x 190, annex door 250 high")])
    p = QA / "SE_FACADE_OPENINGS.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 4, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


def ne_top(doc):
    img, sha = _native(doc, 7)
    box = (1950, 2050, 3150, 5350)
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    T = lambda p: (p[0] - box[0], p[1] - box[1])
    x0 = 1200
    for lvl, txt, cls in ((9.70, "+9.70 slab", "UNRESOLVED"), (11.10, "+11.10 face top / band underside", "PHYSICAL_MATERIAL"), (11.30, "+11.30 band top (raster)", "COPING")):
        x = x0 + lvl * 157.5
        _dashed(d, T((x, 2100)), T((x, 5300)), CLASS[cls], 3, 14)
    crop = crop.rotate(90, expand=True)
    d = ImageDraw.Draw(crop)
    d.text((8, 8), "NE elevation: parapet face +9.70 -> +11.10 (1.40) with a 0.20 band to +11.30; levels by the 1440 chain scale (157.5 px/m); PROVISIONAL", fill=(0, 0, 0))
    k = 0.3
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - NORTH EAST ELEVATION (original page 7) - NE parapet top corrected to +11.10 + 0.20 band",
                  [("PHYSICAL_MATERIAL", "solid face top +11.10"), ("COPING", "band top +11.30"), ("UNRESOLVED", "+9.70 slab")])
    p = QA / "NE_PARAPET_TOP.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 7, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


def nw_edge(doc):
    img, sha = _native(doc, 6)
    box = (2500, 2300, 3100, 3600)
    crop = img.crop(box).rotate(90, expand=True)
    d = ImageDraw.Draw(crop)
    d.text((8, 8), "NW (sea-view) roof edge: X-lattice balustrade (zero plaster) on a low curved solid kerb; printed 100 + 10; B-B 130 = lattice + cap", fill=(0, 0, 0))
    k = 0.6
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - NORTH WEST ELEVATION (original page 6) - the 10 cm x 1.30 sea-view element is a lattice balustrade on a kerb",
                  [("BALUSTRADE", "open X-lattice"), ("PHYSICAL_MATERIAL", "curved solid kerb (profile NOT_ESTABLISHED)")])
    p = QA / "NW_ROOF_EDGE.png"
    out.save(p)
    return {"IMAGE": str(p.relative_to(OUT)), "SOURCE_PAGE": 6, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}


def run() -> dict:
    QA.mkdir(exist_ok=True)
    doc = pymupdf.open(PDF)
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "VISUAL_QA_PA02", "OVERLAYS": [ff_void_stair(doc), se_openings(doc), ne_top(doc), nw_edge(doc)],
           "A_VISUAL_OVERLAY_IS_QA_EVIDENCE_NOT_GEOMETRY_AUTHORITY": True}
    (OUT / "VISUAL_QA_PA02.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
