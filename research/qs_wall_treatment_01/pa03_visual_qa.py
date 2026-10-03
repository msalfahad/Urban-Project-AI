"""PA03 visual QA: (1) QA_RENDER_VALIDITY_REGISTER over every QA image the
phase has produced (SOURCE_IMAGE vs DERIVED_QA_OVERLAY, ink fraction,
target visibility, INFORMATIVE / PARTIALLY_INFORMATIVE / NOT_INFORMATIVE);
(2) the native source crops PA03 read (re-cropped here from the original
pages with their boxes recorded); (3) one new overlay drawing BOTH void
objects on the original FF page.

    python3 -m research.qs_wall_treatment_01.pa03_visual_qa
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image, ImageDraw

from engine import source_review as SR
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.cad_links import X_PAIRS, Y_PAIRS  # noqa: F401  (registration pairs used by the mapper)
from research.qs_wall_treatment_01.pa02_visual_qa import GF2FF, _gf_native_mapper
from research.qs_wall_treatment_01.visual_qa_v4 import CLASS, _dashed, _legend, _native

OUT = Path(P.OUT_DIR)
QA = OUT / "visual_qa"
SRC = QA / "source_crops"
PDF = "data/golden/7757/inputs/P7757_DRAWINGS.pdf"

# native crop boxes (x = level axis, y = run axis on elevation / section pages), rotated 90 deg for viewing
SOURCE_CROPS = {
    "se_tower_chain.png": {"PAGE": 4, "BOX": (1150, 2600, 3350, 3000), "SCALE": 0.6, "TARGET": "SE tower strip vertical dimension chain 185 / 200 / 250 / 8 / 5 / 230 / 200 / 170 with witness ticks", "VISIBLE": True},
    "se_mb_window.png": {"PAGE": 4, "BOX": (2100, 3250, 2800, 3850), "SCALE": 1.0, "TARGET": "SE main-block window with 215 / 190 / 139 and the 220 below", "VISIBLE": True},
    "se_base_chain.png": {"PAGE": 4, "BOX": (1100, 2300, 1500, 3800), "SCALE": 0.7, "TARGET": "SE base: the 185 rising from the +0.15 datum", "VISIBLE": True},
    "ne_top_full.png": {"PAGE": 7, "BOX": (2600, 800, 3150, 4200), "SCALE": 0.35, "TARGET": "NE parapet top line along the whole elevation (band line?)", "VISIBLE": "PARTIAL"},
    "ne_top_zoomL.png": {"PAGE": 7, "BOX": (2650, 1000, 3100, 1700), "SCALE": 1.0, "TARGET": "NE parapet band line near the left end", "VISIBLE": False},
    "ne_top_zoomR.png": {"PAGE": 7, "BOX": (2650, 3300, 3100, 4000), "SCALE": 1.0, "TARGET": "NE parapet band line near the right end", "VISIBLE": False},
}
PA02_OVERLAYS = {
    "visual_qa/FF_VOID_STAIR.png": ("FF opening and block stair well on page 2", True, "the X rectangle drawn is the SLAB_OPENING only; the caption 'void 5.82 x 2.75' is our annotation, the page prints 587 x 400"),
    "visual_qa/SE_FACADE_OPENINGS.png": ("SE facade openings on page 4", True, "opening boxes are our overlays; dimensions re-audited on native crops in PA03"),
    "visual_qa/NE_PARAPET_TOP.png": ("NE parapet top on page 7", "PARTIAL", "the wall top line is visible; the +11.10 / +11.30 lines are DERIVED (not printed); no band line exists on the page"),
    "visual_qa/NW_ROOF_EDGE.png": ("NW lattice on the kerb, page 6", True, "172 / 100 / 10 printed at the element are visible"),
    "visual_qa/SE_ELEVATION_FACES.png": ("SE roof-edge faces on page 4", True, None),
    "visual_qa/ROOF_PLAN_EDGES.png": ("roof plan edges on page 3", "PARTIAL", "registration PROVISIONAL (straight span / 7500)"),
    "visual_qa/GF_PLAN_D2_COLUMN.png": ("D2 column on page 1", "PARTIAL", "the column loop is visible; the abutting walls CAD-822 / 823 / 783 were not drawn on the overlay (PA01 missed them)"),
}


def _ink(path):
    im = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    return float(((r < 90) & (g < 90) & (b < 90)).mean())


def source_crops(doc):
    SRC.mkdir(parents=True, exist_ok=True)
    out = []
    cache = {}
    for name, spec in SOURCE_CROPS.items():
        if spec["PAGE"] not in cache:
            cache[spec["PAGE"]] = _native(doc, spec["PAGE"])
        img, sha = cache[spec["PAGE"]]
        im = img.crop(spec["BOX"]).rotate(90, expand=True)
        if spec["SCALE"] != 1.0:
            im = im.resize((int(im.width * spec["SCALE"]), int(im.height * spec["SCALE"])), Image.LANCZOS)
        p = SRC / name
        im.save(p)
        rec = SR.render_validity(image=str(p.relative_to(OUT)), kind="SOURCE_IMAGE", ink_fraction=_ink(p), target_object=spec["TARGET"], target_visible=spec["VISIBLE"],
                                 note="native crop, no overlay; box (x0, y0, x1, y1) in native page pixels, rotated 90 deg CCW for viewing")
        rec.update({"SOURCE_PAGE": spec["PAGE"], "SOURCE_SHA256": sha, "NATIVE_BOX": list(spec["BOX"]), "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()})
        out.append(rec)
    return out


def overlays_pa02():
    out = []
    for rel, (target, visible, note) in PA02_OVERLAYS.items():
        p = OUT / rel
        rec = SR.render_validity(image=rel, kind="DERIVED_QA_OVERLAY", ink_fraction=_ink(p), target_object=target, target_visible=visible, note=note)
        rec["SHA256"] = hashlib.sha256(p.read_bytes()).hexdigest()
        out.append(rec)
    return out


def ff_two_objects(doc):
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    Tf = next(t for t in reg["TRACES"] if t["SHEET_ID"] == "FIRST_FLOOR_PLAN")["ORIGINAL_PAGE_COORDINATE_TRANSFORM"]
    void = json.loads((OUT / "VOID_GEOMETRY_RECONCILIATION.json").read_text("utf-8"))["OBJECTS_PRESERVED"]
    img, sha = _native(doc, 2)
    N = _gf_native_mapper(Tf)
    def rect(bounds):
        xs = [v - GF2FF for v in bounds["X"]]
        ys = bounds["Y"]
        return [N(xs[0], ys[0]), N(xs[1], ys[0]), N(xs[1], ys[1]), N(xs[0], ys[1])]
    zone = rect(void["VOID_STAIR_ZONE"]["BOUNDS_FF_MM"])
    slab = rect(void["SLAB_OPENING"]["BOUNDS_FF_MM"])
    cx = sum(p[0] for p in zone) / 4; cy = sum(p[1] for p in zone) / 4
    box = (int(cx) - 800, int(cy) - 800, int(cx) + 800, int(cy) + 800)
    crop = img.crop(box)
    d = ImageDraw.Draw(crop)
    T = lambda p: (p[0] - box[0], p[1] - box[1])
    z = [T(p) for p in zone]; s = [T(p) for p in slab]
    d.line(z + [z[0]], fill=CLASS["OPENING"], width=5)
    for i in range(4):
        _dashed(d, s[i], s[(i + 1) % 4], CLASS["VIRTUAL_MEASUREMENT_CLOSURE"], 4, 16)
    d.text((10, 10), "VOID_STAIR_ZONE 5.87 x 4.00 (printed 587 x 400 = authored DWG dimensions) - solid red", fill=(0, 0, 0))
    d.text((10, 26), "SLAB_OPENING 5.82 x 2.75 (architectural X = structural p4 X) - dashed grey; the strip between them is the straight flight", fill=(0, 0, 0))
    d.text((10, 42), "both objects preserved; neither substituted; overlay lines are ours (DERIVED_QA_OVERLAY), the page is the source", fill=(0, 0, 0))
    crop = crop.rotate(90, expand=True)
    crop = crop.resize((int(crop.width * 0.55), int(crop.height * 0.55)), Image.LANCZOS)
    out = _legend(crop, "VISUAL QA - FIRST FLOOR PLAN (original page 2) - the two void objects (GF sheet registration reused: PROVISIONAL, QA only)",
                  [("OPENING", "VOID_STAIR_ZONE 5.87 x 4.00 to the NE wall face"), ("VIRTUAL_MEASUREMENT_CLOSURE", "SLAB_OPENING 5.82 x 2.75 (X)")])
    p = QA / "FF_VOID_TWO_OBJECTS.png"
    out.save(p)
    rec = SR.render_validity(image=str(p.relative_to(OUT)), kind="DERIVED_QA_OVERLAY", ink_fraction=_ink(p), target_object="FF opening with the two void objects", target_visible=True,
                             note="GF sheet registration reused on the FF sheet (PROVISIONAL, QA only)")
    rec.update({"SOURCE_PAGE": 2, "SOURCE_SHA256": sha, "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()})
    return rec


def run() -> dict:
    doc = pymupdf.open(PDF)
    crops = source_crops(doc)
    ovl = overlays_pa02() + [ff_two_objects(doc)]
    scratch = [
        {"IMAGE": "scratch bb_main_block.png (PA02 session crop of page 9, box not recorded)", "KIND": "SOURCE_IMAGE", "VALIDITY": "INFORMATIVE", "TARGET_OBJECT": "B-B main-block bay: +5.50 slab continuous, doors on both floors, no opening",
         "USED_FOR": "SECTION_CUT_RELATIONSHIP (B-B looks away from the opening)", "CAN_SUPPORT_CLAIM": True, "IS_SOURCE_AUTHORITY": False},
        {"IMAGE": "scratch AA_stair.png (PA02 session crop of page 8, box not recorded)", "KIND": "SOURCE_IMAGE", "VALIDITY": "INFORMATIVE", "TARGET_OBJECT": "block stair on A-A: two flights per storey, far flight and handrails visible through the well",
         "USED_FOR": "MID_ELEMENT excluded roles (full-height wall roles) - PROVISIONAL", "CAN_SUPPORT_CLAIM": True, "IS_SOURCE_AUTHORITY": False},
        {"IMAGE": "scratch ff_void_zoom.png / gf_void_zoom.png (DWG renders, no annotation)", "KIND": "SOURCE_IMAGE", "VALIDITY": "INFORMATIVE", "TARGET_OBJECT": "DWG FF / GF copies around the opening with the authored 587 / 400 dimension entities",
         "USED_FOR": "void reconciliation (the DWG entities themselves are the authority, read by id)", "CAN_SUPPORT_CLAIM": True, "IS_SOURCE_AUTHORITY": False},
    ]
    rules = ["a render whose ink fraction is below 1 % or whose claimed target is not visible is NOT_INFORMATIVE and supports nothing",
             "a DERIVED_QA_OVERLAY supports a QA check of a read; its own lines and captions are never source evidence",
             "a SOURCE_IMAGE is a crop of an original page: it shows the source; the page is the authority",
             "PA02's NE_PARAPET_TOP.png +11.30 line and FF_VOID_STAIR.png '5.82 x 2.75' caption are overlay annotations, not source (SR-08, SR-17)"]
    not_inf = [r["IMAGE"] for r in crops + ovl if r["VALIDITY"] == "NOT_INFORMATIVE"]
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "QA_RENDER_VALIDITY_REGISTER", "LAYER": "PA03_SOURCE_REVIEW_CORRECTION", "RULES": rules,
            "SOURCE_CROPS": crops, "DERIVED_QA_OVERLAYS": ovl, "SCRATCH_READS_REFERENCED": scratch, "NOT_INFORMATIVE": not_inf,
            "NE_BAND_CLAIM": "the two NE top zoom crops show a single top line and no band line: they cannot support 'a 0.20 band exists on the NE parapet'; BAND_EXISTS_STATUS stays NOT_ESTABLISHED",
            "A_VISUAL_OVERLAY_IS_QA_EVIDENCE_NOT_GEOMETRY_AUTHORITY": True}
    (OUT / "QA_RENDER_VALIDITY_REGISTER.json").write_text(json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8")
    return {"CROPS": [(c["IMAGE"], c["VALIDITY"], c["INK_FRACTION"]) for c in crops], "OVERLAYS": [(o["IMAGE"], o["VALIDITY"]) for o in ovl], "NOT_INFORMATIVE": not_inf}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
