"""ALSENAN ROUND 4 - visual source claims for ST7757.pdf pages 8 and 13-16 (+ machine-read DXF details).

Every claim is an AI_VISUAL_TRANSCRIPTION of one crop of the PDF (read by this round's AI reader from the rendered crop)
joined to the DETERMINISTIC evidence captured once by research/alsenan_rebar_source_exhaustion_04/
capture_visual_evidence.py (crop hash, tesseract OCR, PDF vector geometry) and, where the Round-4 brief states it, to
the INDEPENDENT_REVIEW of pages 8 and 13-16 relayed by the owner. The source state is derived by
engine.source.visual_source_claim; a claim never sets its own state.

    AI reads (raw_visual_transcription, normalised_interpretation).
    Deterministic code checks (OCR tokens, dot rows, section outlines, table rules, dimension proportions, DXF).
    Only CROSS_VERIFIED / MACHINE_READ / HUMAN_VERIFIED claims may drive a VERIFIED quantity part.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import visual_source_claim as VS

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "research/alsenan_rebar_source_exhaustion_04/evidence/VISUAL_EVIDENCE_CAPTURE.json"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
DRAWING = "ST7757.pdf"
REVIEW_REF = ("Round-4 brief (owner, 2026-10-05): independent review of ST7757.pdf p.8 and pp.13-16 - "
              "§4 cover, §5 ground beam > 5 m, §6 lift, §7 temperature table rows, §8 slab-on-beams rules, "
              "§10 boxed bars")


def load_capture(path: Path = CAPTURE) -> dict:
    return json.loads(Path(path).read_text())


# ------------------------------------------------------------------------------------------------- geometry checks
def _geo(capture, crop, kind, expect, tol=None):
    g = capture["crops"][crop]["geometry"]
    if kind == "dot_rows":
        rows = [r["count"] for r in g.get("bar_dots", {}).get("rows", [])]
        return rows == list(expect), {"rows": rows, "expected": list(expect)}
    if kind == "section_mm":
        rs = g.get("section_rects") or []
        if not rs:
            return None, {"rects_mm": [], "expected": expect, "state": "NOT_MEASURABLE"}
        ok = any(abs(r["w_mm_at_1_20"] - expect[0]) <= (tol or 10) and
                 (expect[1] is None or abs(r["h_mm_at_1_20"] - expect[1]) <= (tol or 10)) for r in rs)
        return ok, {"rects_mm": [(r["w_mm_at_1_20"], r["h_mm_at_1_20"]) for r in rs], "expected": expect}
    if kind == "table_rows":
        n = len(g.get("horizontal_rules_pt") or []) - expect["rules_above_first_row"] - 1
        return n == expect["rows"], {"rules": g.get("horizontal_rules_pt"), "data_rows": n}
    if kind == "slab_ratio":
        d = g.get("dimension_lines") or {}
        v = d.get(expect["key"])
        if v is None:
            return None, {"state": "NOT_MEASURABLE", **expect}
        return v is not None and abs(v - expect["value"]) <= expect["tol"], {"measured": v, **expect}
    raise ValueError(kind)


# ------------------------------------------------------------------------------------------------- claim specs
# ocr: {token: min occurrences}; geo: [(kind, expect, facets, tol)]; review: facets the brief states independently
SPECS = [
    # ---------------- page 8 recommendations (raster page, Arabic) ----------------
    dict(claim_id="P8-N22-COVER-GENERAL", crop="P08_NOTE_22_COVER", element_type="ALL_MEMBERS",
         raw="22. يجب أن لا يقل سمك الغطاء الخرساني عن 2.5 سم في الأعمدة والبلاطات والجسور",
         norm="concrete cover >= 25 mm for columns, slabs and beams", value=25, unit="mm",
         facets=["cover_value", "member_scope"], ocr={"2.5": 1, "الأعمدة": 1, "والبلاطات": 1, "والجسور": 1},
         ocr_facets=["cover_value", "member_scope"], review=["cover_value", "member_scope"],
         consumer="PROJECT_REBAR_RULE COVER_GENERAL_25MM", applicability="APPLICABLE"),
    dict(claim_id="P8-N22-COVER-SOIL", crop="P08_NOTE_22_COVER", element_type="SOIL_CONTACT",
         raw="... وعن 7سم في الخرسانة الملاصقة للتربة", norm="concrete cover >= 70 mm for concrete in contact with soil",
         value=70, unit="mm", facets=["cover_value", "soil_scope"], ocr={"7سم": 1, "للتربة": 1},
         ocr_facets=["cover_value", "soil_scope"], review=["cover_value", "soil_scope"],
         consumer="PROJECT_REBAR_RULE COVER_AGAINST_SOIL_70MM", applicability="APPLICABLE"),
    dict(claim_id="P8-N09-STARTER-DEVELOPMENT", crop="P08_NOTE_09_DEVELOPMENT", element_type="STARTER_BARS",
         raw="9. يجب ان لا يقل طول رباط اشاير حديد التسليح (Development Length) عن (70) مرة قطر السيخ بمناطق الشد ، "
             "(40) مرة قطر السيخ بمناطق الضغط",
         norm="development / tie length of reinforcement STARTER bars (اشاير) >= 70 x bar diameter in tension zones, "
              ">= 40 x bar diameter in compression zones. It does not define hooks, bends or beam-end anchorage.",
         value={"tension_factor": 70, "compression_factor": 40, "scope": "starter bars (اشاير)"}, unit="x bar Ø",
         facets=["tension_factor", "compression_factor", "scope_starter_bars"],
         ocr={"(70)": 1, "(40)": 1, "Development Length": 1, "اشاير": 1, "الشد": 1},
         ocr_facets=["tension_factor", "compression_factor", "scope_starter_bars"], review=[],
         consumer="PROJECT_REBAR_RULE DEVELOPMENT_STARTER_70D_40D", applicability="APPLICABLE",
         notes="the brief asked to verify the wording: it names starter bars and 'Development Length'; it is not a "
               "hook, bend or end-anchorage rule"),
    dict(claim_id="P8-N18-SLAB-THICKNESS", crop="P08_NOTES_18_21", element_type="SLAB",
         raw="18. سمك بلاطات الاسقف العادية 16 سم ما لم يذكر خلاف ذلك",
         norm="ordinary roof / floor slab thickness 160 mm unless stated otherwise", value=160, unit="mm",
         facets=["thickness"], ocr={"16 سم": 1}, ocr_facets=["thickness"], review=[], dxf_slab_tags=True,
         consumer="TEMPERATURE_REBAR_RULE_REGISTER (thickness row lookup)", applicability="APPLICABLE"),
    dict(claim_id="P8-N19-LIFT-TIE-BEAMS", crop="P08_NOTES_18_21", element_type="LIFT_TIE_BEAM",
         raw="19. يتم عمل جسور لربط اعمدة المصعد على ارتفاع 3.00m اذا كان ارتفاع الدور أكثر من 4.30m وذلك حول بيت المصعد",
         norm="tie beams connecting the lift columns at 3.00 m height where the storey height exceeds 4.30 m, around "
              "the lift shaft (section and bars not printed)", value={"tie_height_m": 3.0, "storey_threshold_m": 4.3},
         unit="m", facets=["threshold", "tie_height"], ocr={"4.30": 1, "المصعد": 1}, ocr_facets=["threshold"],
         review=[], consumer="LIFT_TIE_BEAMS population (BLOCKED: section / bars not printed)",
         applicability="APPLICABLE"),
    dict(claim_id="P8-N21-SIDE-BARS", crop="P08_NOTES_18_21", element_type="BEAM",
         raw="21. يتم استخدام حديد اضافي جانبي (2Φ12 ، 3Φ12 ، 4Φ12) في الجسور ذات العمق أكبر من 60 سم حسب عرض الجسر",
         norm="additional side bars 2Ø12 / 3Ø12 / 4Ø12 in beams deeper than 60 cm 'according to the beam width' - the "
              "width -> count mapping and per-face meaning are NOT printed", value=["2Ø12", "3Ø12", "4Ø12"],
         unit="bars", facets=["options", "width_dependence"], ocr={"حسب عرض الجسر": 1},
         ocr_facets=["width_dependence"], review=[], consumer="SIDE_BARS components (BLOCKED mapping)",
         applicability="APPLICABLE"),
    # ---------------- page 13 ground beams ----------------
    dict(claim_id="P13-GB-GT5M", crop="P13_GB_GT5M", element_type="GROUND_BEAM",
         raw="Ground Beams. More than 5m length (1:20) without concentrated load: 30 x 60; 3Ø16 top; Ø8/15cm; 3Ø16; 3Ø16",
         norm="interior ground beam, length > 5 m, no concentrated load: 300 x 600; top 3Ø16; lower reinforcement TWO "
              "rows of 3Ø16 (6Ø16 total - two real rows, not a duplicate); stirrups Ø8 @ 150",
         value={"B_mm": 300, "D_mm": 600, "top": [3, 16], "lower_rows": [[3, 16], [3, 16]], "stirrup": [8, 150]},
         unit="mm", facets=["section", "top_count", "top_dia", "lower_rows", "lower_dia", "stirrup", "applicability"],
         ocr={"3Ø16": 3, "Ø8/15cm": 1, "More than 5m length": 1, "without concentrated load": 1},
         ocr_facets=["top_dia", "lower_dia", "stirrup", "applicability"],
         geo=[("dot_rows", [3, 3, 3], ["top_count", "lower_rows"], None),
              ("section_mm", (300, 600), ["section"], 10)],
         review=["section", "top_count", "top_dia", "lower_rows", "lower_dia", "stirrup", "applicability"],
         consumer="GROUND_BEAM_REBAR_V4", applicability="APPLICABLE"),
    dict(claim_id="P13-GB-LT5M", crop="P13_GB_LT5M", element_type="GROUND_BEAM",
         raw="Ground Beams. Less than 5m length (1:20) without concentrated load: 30 x 40; 3Ø14; Ø8/15cm; 3Ø14; 3Ø14",
         norm="interior ground beam, length < 5 m: 300 x 400; top 3Ø14; two lower rows 3Ø14; stirrups Ø8 @ 150",
         value={"B_mm": 300, "D_mm": 400, "top": [3, 14], "lower_rows": [[3, 14], [3, 14]], "stirrup": [8, 150]},
         unit="mm", facets=["section", "top_count", "top_dia", "lower_rows", "lower_dia", "stirrup", "applicability"],
         ocr={"3Ø14": 3, "Ø8/15cm": 1, "Less than 5m length": 1, "without concentrated load": 1},
         ocr_facets=["top_dia", "lower_dia", "stirrup", "applicability"],
         geo=[("dot_rows", [3, 3, 3], ["top_count", "lower_rows"], None),
              ("section_mm", (300, 400), ["section"], 10)],
         review=[], consumer="GROUND_BEAM_REBAR_V4", applicability="APPLICABLE"),
    dict(claim_id="P13-GB-LT2_5M-BARS", crop="P13_GB_LT2_5M", element_type="GROUND_BEAM",
         raw="Ground Beams. Less than 2.5m length (1:20): 3Ø14; 3Ø14; 3Ø14 (no stirrup callout printed)",
         norm="interior ground beam, length < 2.5 m: top 3Ø14; two lower rows 3Ø14. The stirrup is DRAWN but has no "
              "callout (size / spacing not printed)",
         value={"top": [3, 14], "lower_rows": [[3, 14], [3, 14]], "stirrup": None}, unit="bars",
         facets=["top_count", "top_dia", "lower_rows", "lower_dia", "applicability"],
         ocr={"3Ø14": 3, "Less than 2.5m length": 1}, ocr_facets=["top_dia", "lower_dia", "applicability"],
         geo=[("dot_rows", [3, 3, 3], ["top_count", "lower_rows"], None)], review=[],
         consumer="GROUND_BEAM_REBAR_V4", applicability="APPLICABLE"),
    dict(claim_id="P13-GB-LT2_5M-SECTION", crop="P13_GB_LT2_5M", element_type="GROUND_BEAM",
         raw="30 (depth) x 30 (width)", norm="section 300 x 300", value={"B_mm": 300, "D_mm": 300}, unit="mm",
         facets=["section"], ocr={}, ocr_facets=[], geo=[("section_mm", (300, 300), ["section"], 10)], review=[],
         consumer="GROUND_BEAM_REBAR_V4 (stirrup loop)", applicability="APPLICABLE"),
    dict(claim_id="P13-GB-EXTERIOR", crop="P13_GB_EXTERIOR", element_type="GROUND_BEAM_EXT",
         raw="Ground Beams. for exterior walls (1:20): width 30, depth FOLLOW ARCH. (Ground Floor slab level to below "
             "Outer Normal ground level); 3Ø16 top; 2Ø12/30cm; Ø8/15cm; 6Ø16",
         norm="exterior-wall ground beam: B 300, D follows the architecture (not printed); top 3Ø16; side bars 2Ø12 "
              "per 30 cm of depth; bottom 6Ø16 drawn as two rows of 3; stirrups Ø8 @ 150",
         value={"B_mm": 300, "D_mm": None, "top": [3, 16], "side": "2Ø12/30cm", "bottom": [6, 16],
                "bottom_rows": [[3, 16], [3, 16]], "stirrup": [8, 150]}, unit="mm",
         facets=["width", "top_count", "top_dia", "side", "bottom_count", "bottom_dia", "stirrup", "applicability"],
         ocr={"3Ø16": 1, "2Ø12/30cm": 1, "Ø8/15cm": 1, "6Ø16": 1, "for exterior walls": 1},
         ocr_facets=["top_dia", "side", "bottom_count", "bottom_dia", "stirrup", "applicability"],
         geo=[("dot_rows", [3, 2, 2, 3, 3], ["top_count", "side", "bottom_count"], None),
              ("section_mm", (300, None), ["width"], 10)], review=[],
         consumer="GROUND_BEAM_REBAR_V4", applicability="APPLICABLE"),
    # ---------------- page 13 lintels / footing ----------------
    dict(claim_id="P13-LINTEL-SCHEDULE", crop="P13_LINTEL_SCHEDULE", element_type="LINTEL",
         raw="LINTEL SCHEDULE: 0-100 Bx20 2Ø12 2Ø10 5Ø8/M | 101-200 Bx20 2Ø14 2Ø12 5Ø8/M | 201-300 Bx30 3Ø16 3Ø14 "
             "5Ø8/M | 301-500 Bx40 3Ø18 3Ø14 5Ø8/M | 501-750 Bx55 4Ø18 3Ø14 5Ø8/M; B = width of the block wall",
         norm="opening width (cm) -> lintel depth, bottom bars, top bars, stirrups 5Ø8 per metre; B = block-wall width",
         value=[{"max_cm": 100, "D_cm": 20, "bottom": [2, 12], "top": [2, 10], "stir_per_m": [5, 8]},
                {"max_cm": 200, "D_cm": 20, "bottom": [2, 14], "top": [2, 12], "stir_per_m": [5, 8]},
                {"max_cm": 300, "D_cm": 30, "bottom": [3, 16], "top": [3, 14], "stir_per_m": [5, 8]},
                {"max_cm": 500, "D_cm": 40, "bottom": [3, 18], "top": [3, 14], "stir_per_m": [5, 8]},
                {"max_cm": 750, "D_cm": 55, "bottom": [4, 18], "top": [3, 14], "stir_per_m": [5, 8]}],
         unit="cm / bars", facets=["row_count", "bars", "stirrups", "widths"],
         ocr={"2Ø12": 2, "2Ø10": 1, "2Ø14": 1, "3Ø16": 1, "3Ø18": 1, "4Ø18": 1, "3Ø14": 3, "5 Ø8/M": 5,
              "101 - 200": 1, "201 - 300": 1, "301 - 500": 1, "501 - 750": 1},
         ocr_facets=["bars", "stirrups", "widths"],
         geo=[("table_rows", {"rows": 5, "rules_above_first_row": 3}, ["row_count"], None)], review=[],
         consumer="LINTEL populations", applicability="APPLICABLE"),
    dict(claim_id="P13-LINTEL-BEARING", crop="P13_LINTEL_DETAIL", element_type="LINTEL",
         raw="LINTEL DETAIL: MIN.40cm (each side); TOB BARS; BOTTOM BARS; STIRRUPS; bar ends drawn bent",
         norm="lintel bears >= 400 mm into the wall on each side; bar ends are drawn bent (hook length not "
              "dimensioned)", value={"bearing_min_mm": 400}, unit="mm", facets=["bearing_min"],
         ocr={"MIN.40": 2}, ocr_facets=["bearing_min"], review=[], consumer="LINTEL bar extension",
         applicability="APPLICABLE"),
    dict(claim_id="P13-FOOTING-BOXED-BARS", crop="P13_FOOTING_TYPICAL", element_type="FOOTING",
         raw="TYP. DETAIL OF ISOLATED FOOTING: Boxed bars.; Long bars; Short bars; Min. 30cm; Max. 10cm",
         norm="the typical isolated footing carries a SEPARATE boxed-bar cage in addition to the bottom long / short "
              "bars; the schedule's BOXED values (3+4 ... 3+8) are not explained (diameter / shape not printed)",
         value={"boxed_bars_component_exists": True}, unit="-", facets=["boxed_exists"],
         ocr={"Boxed bars.": 1, "Long bars": 1, "Short_bars": 1}, ocr_facets=["boxed_exists"],
         review=["boxed_exists"], consumer="FOOTING BOXED components (BLOCKED_SEMANTICS kept)",
         applicability="APPLICABLE"),
    dict(claim_id="P13-STARTER-FOOT-MIN30", crop="P13_FOOTING_TYPICAL", element_type="STARTER_BARS",
         raw="Min. 30cm (horizontal leg of the column bars at the footing bottom)",
         norm="column starter bars end in a horizontal foot >= 300 mm on the footing bottom mesh", value=300, unit="mm",
         facets=["foot_min"], ocr={"Min. 30cm": 1}, ocr_facets=["foot_min"], review=[],
         consumer="COLUMN_STARTERS foot", applicability="APPLICABLE"),
    dict(claim_id="P13-STARTER-PROJECTION-40D", crop="P13_STARTER_40D", element_type="STARTER_BARS",
         raw="40 ø (dimension from the footing top along the column bars)",
         norm="starter bars project 40 x bar diameter above the footing top (the column-bar splice)", value=40,
         unit="x bar Ø", facets=["projection_factor"], ocr={"40": 1}, ocr_facets=["projection_factor"], review=[],
         independent_document={"ref": "P8-N09-STARTER-DEVELOPMENT (compression zones 40 x Ø, OCR-read)",
                                "facets": ["projection_factor"]},
         consumer="COLUMN_STARTERS projection", applicability="APPLICABLE"),
    dict(claim_id="P13-FOOTING-DEEP-LOWER-GB", crop="P13_FOOTING_DEEP", element_type="GROUND_BEAM_LOWER",
         raw="TYP. DETAIL OF ISOLATED FOOTING (WITH OUT BASEMENT) when the level difference between upper ground beam "
             "and footing is more than 2.5m: Upper Ground beam reinforcements; Lower Ground beam reinforcements",
         norm="if footing top is more than 2.5 m below the upper ground beam, a LOWER ground beam is added (bars as "
              "the ground-beam sections)", value={"threshold_m": 2.5}, unit="m", facets=["condition"],
         ocr={"Lower Ground beam reinforcements.": 1}, ocr_facets=["condition"], review=[],
         consumer="conditional population (founding level not printed)", applicability="APPLICABILITY_BLOCKED",
         applicability_why="the founding level is a site decision (p.8 note 12): the 2.5 m condition cannot be tested"),
    # ---------------- page 14 lift / boundary wall / parapets ----------------
    dict(claim_id="P14-LIFT-VALUES", crop="P14_LIFT_FOOTING", element_type="FOOTING_LIFT",
         raw="DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT): wall 20; 6Ø12/m; 6Ø16/m; 2Ø16; 2Ø16; 2Ø12 (wall "
             "top); AS PER SCHEDULE (footing); AS ARCH. (pit); AS PER SCH. (footing bars); As Per Lift Manufactures "
             "recommendations (pit depth)",
         norm="pit walls 200 thick with 6Ø12/m and 6Ø16/m; 2Ø16 bars at the wall base (two labelled pairs); 2Ø12 at "
              "the wall top; footing size and bars per the FF schedule row; pit plan per architecture; pit depth / wall "
              "height per the lift manufacturer (NOT printed)",
         value={"wall_mm": 200, "bars": ["6Ø12/m", "6Ø16/m"], "base": "2Ø16 x 2 labels", "top": "2Ø12",
                "height": "AS PER LIFT MANUFACTURER"}, unit="-",
         facets=["wall_thickness", "bar_12", "bar_16", "base_2d16", "manufacturer_height"],
         ocr={"6Ø12/m": 2, "6Ø16/m": 2, "2 Ø16": 1, "AS PER SCHEDULE": 1, "AS ARCH": 1},
         ocr_facets=["bar_12", "bar_16", "base_2d16"], dxf_lift_pit=True,
         review=["wall_thickness", "bar_12", "bar_16", "base_2d16", "manufacturer_height"],
         consumer="LIFT_REBAR_SOURCE_REGISTER / FF components", applicability="APPLICABLE"),
    dict(claim_id="P14-LIFT-ORIENTATION", crop="P14_LIFT_FOOTING", element_type="FOOTING_LIFT",
         raw="6Ø16/m leader to the vertical bar line; 6Ø12/m leader to the horizontal-bar dots; bars drawn on both "
             "faces of each wall",
         norm="interpretation: 6Ø16/m vertical, 6Ø12/m horizontal; whether each rate applies per face is not printed",
         value={"vertical": "6Ø16/m", "horizontal": "6Ø12/m", "per_face": "UNCERTAIN"}, unit="-",
         facets=["orientation", "per_face"], ocr={}, ocr_facets=[],
         geo=[("dot_rows", [4, 4, 4, 4, 4, 14, 14], ["per_face"], None)], review=[],
         consumer="LIFT wall components (BLOCKED_DIMENSION anyway)", applicability="APPLICABLE"),
    dict(claim_id="P14-BOUNDARY-WALL-TYPICAL", crop="P14_BOUNDARY_WALL_SECTION", element_type="BOUNDARY_WALL",
         raw="TYPICAL BOUNDARY WALL (N.I.S): (20x30) COLUMN 4Ø14; GROUND BEAM (20x40); 2Ø14 (T&B); Ø8/20 STIRRUPS; "
             "3Ø16 (T&B); 7Ø12; 4Ø12 (B.W); 80 x 30 pad; AS PER EXCAVATION DEPTH BELOW N.G. LEVEL; columns SEE ARCH "
             "PLAN; footing 130x80x30",
         norm="typical boundary wall: RC columns 20x30 4Ø14 at architectural spacing, ground beams 20x40 at N.G. level "
              "and at the pad, pads 130x80x30 with 7Ø12 / 4Ø12; depth per excavation (not printed)",
         value={"beam": "20x40", "beam_bars": ["2Ø14 (T&B)", "3Ø16 (T&B)"], "stirrups": "Ø8/20",
                "column": "20x30 4Ø14", "pad": "130x80x30 7Ø12 + 4Ø12"}, unit="-",
         facets=["beam", "beam_bars", "column", "pad"],
         ocr={"(T&B)": 4, "Ø8/20": 2, "4Ø14": 1, "7Ø12": 1, "4Ø12 (B.W)": 1}, ocr_facets=["beam_bars", "column", "pad"],
         review=[], consumer="BOUNDARY_WALL (SOURCE_CONFLICT with schedule row B.W)",
         applicability="APPLICABILITY_BLOCKED",
         applicability_why="the project schedule row B.W (20x60, 4Ø16 / 2Ø14, 7Ø8/m) disagrees with this N.I.S. "
                           "typical (20x40, 2Ø14 / 3Ø16 T&B, Ø8/20)"),
    dict(claim_id="P14-PARAPETS", crop="P14_PARAPETS", element_type="PARAPET",
         raw="TYPICAL DETAIL OF PARAPET SECTION (brick wall, RC coping 5Ø12/m + 5Ø10/m, beam AS PER SCH.); DETAIL OF "
             "PARAPET SECTION 130 high (6Ø10/m, 6Ø12/m, 5Ø10/m); DETAIL OF PARAPET SECTION 105 high (6Ø12/m, 5Ø10/m)",
         norm="three parapet details with RC reinforcement; none is bound to an Alsenan roof edge by a callout",
         value={"details": 3}, unit="-", facets=["details_present"], ocr={"5Ø10/m": 1, "6Ø12/m": 2},
         ocr_facets=["details_present"], review=[], consumer="PARAPET_RC population (BLOCKED applicability)",
         applicability="APPLICABILITY_BLOCKED", applicability_why="no plan / section callout binds a parapet detail "
                                                                  "to an Alsenan roof edge"),
    # ---------------- page 15 temperature / slab-on-beams / column-beam details ----------------
    dict(claim_id="P15-TEMPERATURE-SCHEDULE", crop="P15_TEMPERATURE_TABLE", element_type="SLAB",
         raw="TEMPERATURE REINFORCEMENT SCHEDULE: SLAB THICK / REINFORCEMENT: 100 Y10 Ø 200; 125 Y10 Ø 200; 150 Y10 Ø "
             "200; 175 Y12 Ø 200; 200 Y12 Ø 200; 250 Y12 Ø 200; 300 Y12 Ø 200",
         norm="exact rows: 100 / 125 / 150 mm -> Y10 @ 200; 175 / 200 / 250 / 300 mm -> Y12 @ 200",
         value=[[100, 10, 200], [125, 10, 200], [150, 10, 200], [175, 12, 200], [200, 12, 200], [250, 12, 200],
                [300, 12, 200]], unit="mm", facets=["row_count", "thicknesses", "values"],
         ocr={"Y10": 3, "Y12": 4, "200": 8, "100": 1, "125": 1, "150": 1, "175": 1, "250": 1, "300": 1},
         ocr_facets=["thicknesses", "values"],
         geo=[("table_rows", {"rows": 7, "rules_above_first_row": 0}, ["row_count"], None)],
         review=["thicknesses", "values"], consumer="TEMPERATURE_REBAR_RULE_REGISTER", applicability="APPLICABLE"),
    dict(claim_id="P15-TEMPERATURE-NOTES", crop="P15_TEMPERATURE_NOTES", element_type="SLAB",
         raw="NOTE: 1. LAP LENGHT FOR ALL TEMPERATUERE BARS SHALL BE 40xDIA. 2. WHERE BEAMS ARE PARALLEL TO MAIN SLAB "
             "REINFORCEMENT PROVIDE TEMP. REINF. X 2000 TOP OF SLAB AT RIGHT ANGLES TO BEAMS. 1000 Ø SPANDREL 3. WHERE "
             "TOP REINF. DIFFERS BETWEEN ADJACENT SPANS USE LAGER REINF.",
         norm="temperature-bar lap 40 x Ø; where a beam runs parallel to the main slab bars, temperature bars 2000 long "
              "across the beam at the slab top (1000 each side); where adjacent top bars differ, use the larger",
         value={"lap_factor": 40, "beam_parallel_bars_m": 2.0}, unit="x Ø / m", facets=["lap_factor", "notes_present"],
         ocr={"40xDIA": 1, "WHERE BEAMS ARE PARALLEL TO MAIN": 1, "USE LAGER REINF": 1},
         ocr_facets=["lap_factor", "notes_present"], review=["notes_present"],
         consumer="TEMPERATURE_REBAR_RULE_REGISTER", applicability="APPLICABLE"),
    dict(claim_id="P15-SLAB-TOP-NONCONTINUOUS", crop="P15_SLAB_TOP_NONCONTINUOUS", element_type="SLAB",
         raw="TYP. SLAB ON BEAMS: TOP ANCHOR BARS ... .25\"L1\" at the NON CONTINUOUS SUPPORT",
         norm="top anchor bars extend 0.25 x L1 (clear span) from the face of a non-continuous support",
         value=0.25, unit="x L1", facets=["fraction"], ocr={"25°L1": 1}, ocr_facets=["fraction"],
         geo=[("slab_ratio", {"key": "ratio_25_L1", "value": 0.25, "tol": 0.06}, ["fraction"], None, "P15_SLAB_ON_BEAMS")],
         review=["fraction"], consumer="SLAB_DETAIL_RULE_REGISTER", applicability="APPLICABLE"),
    dict(claim_id="P15-SLAB-TOP-CONTINUOUS", crop="P15_SLAB_TOP_CONTINUOUS", element_type="SLAB",
         raw="TYP. SLAB ON BEAMS: .30\"L1\" OR .30\"L2\" WHICHEVER LARGER (continuous support)",
         norm="top bars over a continuous support extend 0.30 x max(L1, L2) from the support face",
         value=0.30, unit="x max(L1, L2)", facets=["fraction", "whichever_larger"],
         ocr={".30°L1": 1, ".30°L2": 1, "WHICHEVER LARGER": 1}, ocr_facets=["fraction", "whichever_larger"],
         geo=[("slab_ratio", {"key": "ratio_30_L1", "value": 0.30, "tol": 0.06}, ["fraction"], None, "P15_SLAB_ON_BEAMS")],
         review=["fraction", "whichever_larger"], consumer="SLAB_DETAIL_RULE_REGISTER", applicability="APPLICABLE"),
    dict(claim_id="P15-SLAB-BOTTOM-STOP", crop="P15_SLAB_BOTTOM_STOP", element_type="SLAB",
         raw="STOP 50% OF BOT. REINF. BALANCE CONTINUOUS; .125\"L1\" .125\"L2\" (from the continuous support face)",
         norm="at a continuous support 50 % of the bottom bars stop 0.125 x L short of the support face; the other "
              "50 % continue through the support", value={"fraction_stopping": 0.5, "stop_from_face": 0.125},
         unit="x L", facets=["fraction_stopping", "stop_distance"],
         ocr={"OF BOT. REINF": 1, "CONTINUOUS": 1, ".125°L1": 1, ".125°L2": 1},
         ocr_facets=["fraction_stopping", "stop_distance"],
         geo=[("slab_ratio", {"key": "ratio_125_L1", "value": 0.125, "tol": 0.03}, ["stop_distance"], None, "P15_SLAB_ON_BEAMS")],
         review=[], consumer="SLAB_DETAIL_RULE_REGISTER / slab bottom-bar split", applicability="APPLICABLE"),
    dict(claim_id="P15-PLANTED-COLUMN", crop="P15_PLANTED_COLUMN", element_type="PLANTED_COLUMN",
         raw="BEAM CARRYING PLANTED COL. DETAIL: 4Ø16; DEPTH; STIRRUPS; 10 10",
         norm="the beam under a planted column takes 4Ø16 extra bars and extra stirrups over 'DEPTH' - lengths and "
              "stirrup size not printed", value={"extra_bars": [4, 16]}, unit="bars", facets=["extra_bars"],
         ocr={"4Ø16": 1, "BEAM CARRYING PLANTED COL. DETAIL": 1}, ocr_facets=["extra_bars"], review=[],
         consumer="PLANTED_COLUMN populations", applicability="APPLICABLE"),
    dict(claim_id="P15-TWISTED-CASEMENT", crop="P15_TWISTED_COLUMN", element_type="COLUMN",
         raw="TYP. DETAIL OF TWISTED COLUMN: 4Ø16 EXTRA, Spiral Stirrups 6Ø8/m; BEAM IN CASEMENT WITH COLUMN: 6Ø8/m, 5Ø18",
         norm="typical details for twisted columns and beams in casement - no Alsenan plan callout binds them",
         value={"twisted": "4Ø16 extra + spiral 6Ø8/m", "casement": "6Ø8/m + 5Ø18"}, unit="-", facets=["present"],
         ocr={"EXTRA": 1, "Spiral Stirrups": 2}, ocr_facets=["present"], review=[],
         consumer="none (applicability not established)", applicability="NOT_ASSESSED"),
    # ---------------- page 16 stairs (READ != APPLICABLE) ----------------
    dict(claim_id="P16-STAIR-TYPICAL", crop="P16_STAIR_SECTION", element_type="STAIR",
         raw="TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S): landing 2Ø12, 6Ø12/m top, 8Ø16/m bottom, 4Ø16 edge; flight "
             "6Ø14/m top, 8Ø16/m bottom, Ø12/20cm distribution, 1Ø12 + Ø8/15 at the nosings; lower flight 6Ø16/m; "
             "G.B 3Ø14 / 2Ø14/30cm / Ø8/15cm / 4Ø16 (30 x 50); levels 0.00, +2.00 (landing), +4.00; TYPICAL DETAIL OF "
             "STAIR BEAM: 2Ø12, 6Ø8/m, 4Ø16, AS PER SCH.",
         norm="typical two-flight stair with one landing at +2.00, rise 4.00; waist 'THICK' (no value)",
         value={"levels": [0.0, 2.0, 4.0], "landing": ["6Ø12/m", "8Ø16/m", "2Ø12", "4Ø16"],
                "flight": ["6Ø14/m", "8Ø16/m", "Ø12/20cm", "1Ø12", "Ø8/15"], "stair_beam": ["2Ø12", "6Ø8/m", "4Ø16"]},
         unit="-", facets=["bars_present"], ocr={"8Ø16/m": 2, "6Ø12/m": 2, "Ø8/15": 1, "LANDING": 1},
         ocr_facets=["bars_present"], review=[], consumer="TYPICAL_STAIR_DETAIL_SOURCE (G23 stays BLOCKED)",
         applicability="APPLICABILITY_BLOCKED",
         applicability_why="N.T.S. typical 0.00 / +2.00 / +4.00 one landing vs Alsenan GF->1F 4.50 m with two turns "
                           "and 1F->2F 4.20 m; no plan callout binds it; waist printed only as THICK"),
    dict(claim_id="P16-OPENING-RIBS", crop="P16_OPENING_IN_BEAM", element_type="BEAM",
         raw="TYPICAL DETAIL FOR OPENING IN BEAM (N.I.S): 3Ø20 EXTRA above / below, STIRR. Ø10/10cm, 3 No. Ø10 at 5cm "
             "adjacent; TORSION STEEL FOR RIBS table A-G",
         norm="typical details for openings in beams and rib torsion steel - no Alsenan callout binds them",
         value={"opening": "3Ø20 extra + Ø10/10cm"}, unit="-", facets=["present"], ocr={"EXTRA": 2},
         ocr_facets=["present"], review=[], consumer="none (applicability not established)",
         applicability="NOT_ASSESSED"),
]


def build_claims(capture, *, dxf_lift_pit=None, slab_tags_cm=None) -> list:
    """Join the AI transcriptions (SPECS) to the captured deterministic evidence and derive each claim's state."""
    out = []
    for s in SPECS:
        cap = capture["crops"][s["crop"]]
        cs = []
        if s.get("ocr"):
            cs.append(VS.ocr_corroboration(f"{s['crop']} tesseract psm {cap['ocr']['psm']}", s["ocr"],
                                           cap["ocr"]["text"] or "", s["ocr_facets"], engine=cap["ocr"]["engine"]))
        for g in s.get("geo", []):
            kind, expect, facets, tol = g[:4]
            gcrop = g[4] if len(g) > 4 else s["crop"]
            ok, det = _geo(capture, gcrop, kind, expect, tol)
            if ok is None:                                 # not measurable is not a disagreement - no channel
                continue
            cs.append(VS.corroboration("PDF_VECTOR_GEOMETRY", f"{gcrop} {kind}", ok, facets, det))
        if s.get("review"):
            cs.append(VS.corroboration("INDEPENDENT_REVIEW", REVIEW_REF, True, s["review"]))
        if s.get("independent_document"):
            d = s["independent_document"]
            cs.append(VS.corroboration("INDEPENDENT_DOCUMENT", d["ref"], True, d["facets"]))
        if s.get("dxf_lift_pit") and dxf_lift_pit is not None:
            cs.append(VS.corroboration("DXF_GEOMETRY", "ST7757.dxf S-BW pit outlines around the FF mark",
                                       abs(dxf_lift_pit["wall_mm"] - 200) <= 5, ["wall_thickness"], dxf_lift_pit))
        if s.get("dxf_slab_tags") and slab_tags_cm is not None:
            agree = all(v in (16, 18) for v in slab_tags_cm.values()) and 16 in slab_tags_cm.values()
            cs.append(VS.corroboration("DXF_TEXT", "slab-sheet thickness tags (S-TEXT-SLAB)", agree, ["thickness"],
                                       {"tags_cm": slab_tags_cm}))
        out.append(VS.claim(
            claim_id=s["claim_id"], drawing_sha256=capture["drawing_sha256"], drawing=DRAWING, page=cap["page"],
            crop_bbox=cap["bbox_pt"], crop_hash=cap["crop_hash"], raw_visual_transcription=s["raw"],
            normalised_interpretation=s["norm"], discipline="STRUCTURAL", element_type=s["element_type"],
            bar_role=s.get("bar_role"), value=s["value"], unit=s["unit"], facets=s["facets"], corroborations=cs,
            applicability=s["applicability"], applicability_why=s.get("applicability_why"), consumer=s["consumer"],
            notes=s.get("notes")))
        out[-1]["crop_id"] = s["crop"]
        out[-1]["crop_dpi"] = cap["dpi"]
    return out
