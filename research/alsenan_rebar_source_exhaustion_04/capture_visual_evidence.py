"""ALSENAN ROUND 4 - capture the deterministic evidence for every visual source claim (run once, output frozen).

    python3 research/alsenan_rebar_source_exhaustion_04/capture_visual_evidence.py [--pdf PATH]

For every detail crop of ST7757.pdf (pages 8, 13, 14, 15, 16) this records, without any AI reading:
  * the crop box (displayed-page points), dpi and the sha256 of the rendered pixel samples (crop_hash);
  * tesseract OCR text of the crop (engine version, language, page-segmentation mode);
  * PDF vector geometry where the claim has a geometric facet: bar-dot rows, closed section outlines (converted with the
    printed 1:20 scale), table rules.
The rendered crops go to data/evidence/alsenan_r4_crops/ (client drawing content - kept out of git, like the PDF);
only hashes, OCR text and measurements are written to evidence/VISUAL_EVIDENCE_CAPTURE.json.
The AI transcriptions themselves live in alsenan_rebar_v4.VISUAL_CLAIMS; build_rebar_v4.py joins the two.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import pdf_vector_evidence as PV  # noqa: E402

PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
PDF = ROOT / "data/inputs/by_sha256" / f"{PDF_SHA}.pdf"
CROPS = ROOT / "data/evidence/alsenan_r4_crops"
OUT = HERE / "evidence" / "VISUAL_EVIDENCE_CAPTURE.json"
DPI = 200

# crop id -> (page, displayed-page bbox in points, OCR language, OCR psm, geometry checks)
DETAILS = {
    "P08_NOTE_09_DEVELOPMENT": (8, (590, 625, 1180, 690), "ara+eng", 6, (), {"dpi": 220}),
    "P08_NOTES_18_21": (8, (120, 470, 600, 628), "ara+eng", 6, (), {"dpi": 220}),
    "P08_NOTE_22_COVER": (8, (120, 625, 600, 668), "ara+eng", 6, (), {"dpi": 220}),
    "P13_GB_GT5M": (13, (592, 530, 720, 694), "eng", 11, ("dots", "rects")),
    "P13_GB_LT5M": (13, (887, 610, 1011, 763), "eng", 11, ("dots", "rects")),
    "P13_GB_LT2_5M": (13, (592, 700, 720, 812), "eng", 11, ("dots", "rects")),
    "P13_GB_EXTERIOR": (13, (740, 560, 884, 812), "eng", 11, ("dots", "rects")),
    "P13_LINTEL_SCHEDULE": (13, (173, 655, 419, 792), "eng", 11, ("rules",)),
    "P13_LINTEL_DETAIL": (13, (62, 505, 419, 640), "eng", 11, ()),
    "P13_FOOTING_TYPICAL": (13, (510, 20, 1001, 517), "eng", 11, ()),
    "P13_FOOTING_DEEP": (13, (39, 26, 497, 497), "eng", 11, ()),
    "P13_STARTER_40D": (13, (780, 215, 830, 300), "eng", 11, (), {"dpi": 400, "rotate": 270}),
    "P14_LIFT_FOOTING": (14, (26, 26, 471, 412), "eng", 11, ("dots",)),
    "P14_BOUNDARY_WALL_PLAN": (14, (458, 170, 760, 330), "eng", 11, ()),
    "P14_BOUNDARY_WALL_SECTION": (14, (775, 20, 1015, 455), "eng", 11, ()),
    "P14_PARAPETS": (14, (60, 410, 1000, 812), "eng", 11, ()),
    "P15_TEMPERATURE_TABLE": (15, (530, 471, 676, 620), "eng", 11, ("rules",)),
    "P15_TEMPERATURE_NOTES": (15, (676, 471, 845, 610), "eng", 6, ()),
    "P15_SLAB_ON_BEAMS": (15, (110, 600, 720, 812), "eng", 11, ("slab_dims",)),
    "P15_SLAB_TOP_NONCONTINUOUS": (15, (190, 630, 340, 660), "eng", 6, (), {"dpi": 300}),
    "P15_SLAB_TOP_CONTINUOUS": (15, (400, 630, 560, 670), "eng", 11, (), {"dpi": 300}),
    "P15_SLAB_BOTTOM_STOP": (15, (380, 735, 620, 770), "eng", 6, (), {"dpi": 300}),
    "P15_TWISTED_COLUMN": (15, (30, 20, 500, 580), "eng", 11, ()),
    "P15_BEAM_IN_CASEMENT": (15, (520, 20, 960, 440), "eng", 11, ()),
    "P15_PLANTED_COLUMN": (15, (760, 445, 1010, 800), "eng", 11, ()),
    "P16_STAIR_SECTION": (16, (144, 118, 995, 812), "eng", 11, ()),
    "P16_STAIR_BEAM": (16, (39, 26, 524, 262), "eng", 11, ()),
    "P16_OPENING_IN_BEAM": (16, (26, 569, 452, 760), "eng", 11, ()),
    "P16_RIBS_TORSION": (16, (812, 419, 982, 668), "eng", 6, ()),
}


def slab_dimension_ratios(pdf, page, bbox) -> dict:
    """TYP. SLAB ON BEAMS - deterministic proportions of the drawn dimension lines (thin 0.48 pt pen):
    the clear span L1 runs between the two full-height extension ticks left of the beam; the '.125 L1' extension tick
    is the short tick inside L1; the '.25 L1' line starts at L1's left tick; the '.30 L' line ends at the beam face.
    A typical detail is drawn only approximately to proportion, so these ratios corroborate the printed fractions
    within a stated tolerance - they never replace them."""
    V = [v for v in PV.lines(pdf, page, bbox, stroke=(0.4, 0.5), min_len_pt=5.0, orient="V")]
    H = [h for h in PV.lines(pdf, page, bbox, stroke=(0.4, 0.5), min_len_pt=30.0, orient="H")]
    ymax = max(v["y1_pt"] for v in V)
    full = sorted(v["x_pt"] for v in V if v["y1_pt"] >= ymax - 1.0 and v["y1_pt"] - v["y0_pt"] >= 50.0)
    short = sorted(v["x_pt"] for v in V if v["y1_pt"] < ymax - 1.0 and v["y0_pt"] > 730.0)
    if len(full) < 3 or len(short) < 2:
        return {"state": "NOT_MEASURED", "full_ticks": full, "short_ticks": short}
    l1_a, l1_b, l2_a = full[0], full[1], full[2]
    L1 = l1_b - l1_a
    r125_1 = (l1_b - max(x for x in short if x < l1_b)) / L1
    r125_2_len = min(x for x in short if x > l2_a) - l2_a
    upper = [h for h in H if h["y_pt"] < 670.0]
    d25 = min(upper, key=lambda h: abs(h["x0_pt"] - l1_a))
    d30 = min(upper, key=lambda h: abs(h["x1_pt"] - l1_b - 2.7))
    return {"state": "MEASURED", "L1_pt": round(L1, 2), "ticks": {"L1": [l1_a, l1_b], "L2_start": l2_a},
            "ratio_125_L1": round(r125_1, 4), "len_125_L2_pt": round(r125_2_len, 2),
            "ratio_25_L1": round((d25["x1_pt"] - d25["x0_pt"]) / L1, 4),
            "ratio_30_L1": round((d30["x1_pt"] - d30["x0_pt"]) / L1, 4),
            "lines": {"d25": d25, "d30": d30}}


def capture(pdf: Path = PDF) -> dict:
    pdf_sha = hashlib.sha256(Path(pdf).read_bytes()).hexdigest()
    if pdf_sha != PDF_SHA:
        raise SystemExit(f"ST7757.pdf sha256 {pdf_sha} != frozen {PDF_SHA}")
    rows = {}
    for cid, spec in DETAILS.items():
        page, bbox, lang, psm, geo = spec[:5]
        opts = spec[5] if len(spec) > 5 else {}
        png = CROPS / f"{cid}.png"
        r = PV.render_crop(pdf, page, bbox, opts.get("dpi", DPI), out_png=png)
        passes = []
        for k, dpi_k in enumerate(sorted({opts.get("dpi", DPI), 300})):
            pk = CROPS / f"{cid}.ocr{dpi_k}.png"
            rk = PV.render_crop(pdf, page, bbox, dpi_k, out_png=pk)
            if opts.get("rotate"):
                from PIL import Image
                Image.open(pk).rotate(opts["rotate"], expand=True).save(pk)
            passes.append({"dpi": dpi_k, "crop_hash": rk["crop_hash"], "text": PV.ocr(pk, lang, psm)})
        rec = {"crop_id": cid, **r, "ocr": {"engine": PV.ocr_engine_version(), "lang": lang, "psm": psm,
                                             "rotate_deg": opts.get("rotate", 0), "passes": passes,
                                             "text": "\n".join(x["text"] or "" for x in passes)}}
        g = {}
        if "dots" in geo:
            g["bar_dots"] = PV.bar_dots(pdf, page, bbox)
        if "rects" in geo:
            g["section_rects"] = [dict(x, w_mm_at_1_20=round(PV.pt_to_mm(x["w_pt"], 20)),
                                       h_mm_at_1_20=round(PV.pt_to_mm(x["h_pt"], 20)))
                                  for x in PV.section_rects(pdf, page, bbox)[:3]]
        if "rules" in geo:
            g["horizontal_rules_pt"] = PV.horizontal_rules(pdf, page, bbox)
        if "slab_dims" in geo:
            g["dimension_lines"] = slab_dimension_ratios(pdf, page, bbox)
        rec["geometry"] = g
        rows[cid] = rec
    return {"SCHEMA": "ALSENAN_R4_VISUAL_EVIDENCE_CAPTURE_V1", "policy": PV.POLICY_ID, "drawing": "ST7757.pdf",
            "drawing_sha256": pdf_sha, "dpi": DPI, "page_size_pt": [1191, 842],
            "scale_note": "pages are at printed size (A3): a 30 cm section at 1:20 measures 42.5 pt",
            "crops_dir_not_in_git": str(CROPS.relative_to(ROOT)), "crops": rows}


if __name__ == "__main__":
    pdf = Path(sys.argv[sys.argv.index("--pdf") + 1]) if "--pdf" in sys.argv else PDF
    out = capture(pdf)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(OUT, len(out["crops"]))
