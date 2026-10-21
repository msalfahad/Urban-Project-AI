"""SOUTH EAST ELEVATION - owner manual source check, reconciled forward.

The owner opened the elevation and verified text existence for 155 and 50
(50 as the top link of 100 + 870 + 420 + 50 = 1440), saw no 130 and no 104,
and saw 139 / 93 / 97 / 155 / 193 / 20 nearby. This module:

  1. reopens the ORIGINAL page images (the embedded scans inside
     P7757_DRAWINGS.pdf, hash-verified against every trace's
     SOURCE_FILE_HASH) and crops each audited dimension at native
     resolution, in reading orientation, as evidence images;
  2. returns the exact frozen evidence record for every parapet / roof-edge
     dimension (sheet, page, trace, hashes, text bbox, dimension line,
     extension lines, tick endpoints) untouched;
  3. keeps TEXT_READ_STATUS apart from DIMENSION_OWNER_STATUS and records
     the physical owner candidate from witness-line TERMINATION, never
     from proximity;
  4. classifies 104 and 139 independently, and 130 on its own sheet with a
     CROSS_SHEET_RELATION_STATUS;
  5. audits the SE roof edge by material (solid / open / upstand / band /
     ogee / faces), reopens D1 as REOPENED_BY_NEW_OWNER_SOURCE_EVIDENCE,
     and resolves what the source hierarchy can;
  6. renders D1_SE_PARAPET_SOURCE_CARD.png over the original elevation.

No frozen output is rewritten; the historical 104 reading is preserved.

    python3 -m research.qs_wall_treatment_01.se_elevation_source_audit
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
CARDS = OUT / "decision_cards"
NATIVE = CARDS / "se_native"
PDF = "data/golden/7757/inputs/P7757_DRAWINGS.pdf"
CASE = "CASE-6-ROOF-PARAPET"

OWNER_VERIFIED_SE = {
    "SOURCE": "SOUTH_EAST_ELEVATION, manual owner inspection", "DATE": "2026-09-19",
    "TEXT_EXISTS": {"155": "upper-right of the tall curved / tower portion; not yet a parapet height",
                    "50": "top link of the overall vertical chain 100 + 870 + 420 + 50 = 1440"},
    "TEXT_NOT_SEEN_BY_OWNER": {"130": "may be on SECTION B-B", "104": "reopened; nearby 139 / 93 / 97 / 155 / 193 / 20"},
    "RULES": ["ownership from witness-line termination, never proximity",
              "50 and 155 enter no plaster arithmetic until OWNER_ESTABLISHED and PLASTERABLE_SOLID_FACE",
              "104 leaves forward use unless an exact source trace exists"],
}

PHYSICAL_OWNERS = ("SOLID_PARAPET", "SOLID_UPSTAND", "BALUSTRADE_RAILING", "HANDRAIL_TOP_RAIL",
                   "COPING_CAPPING", "CURVED_OGEE_SOLID_WALL", "TOWER_DOME_FEATURE",
                   "WALL_BELOW_PARAPET", "STOREY_LEVEL_HEIGHT_CHAIN", "OTHER", "UNRESOLVED")

# audited dimensions: trace id -> (printed, what each end terminates on at
# native resolution, owner candidate, termination-based owner status, role)
AUDIT = {
    "DIM-13": {"TEXT": "1440", "END_A": "tower top line (+14.40)", "END_B": "ground line ±0.00",
               "OWNER": "STOREY_LEVEL_HEIGHT_CHAIN", "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "overall vertical chain 100 + 870 + 420 + 50 = 1440", "PLASTER": False},
    "DIM-14": {"TEXT": "50", "END_A": "tower top line (solid)", "END_B": "DASHED +13.90 level line (a datum, not a drawn edge)",
               "OWNER": "STOREY_LEVEL_HEIGHT_CHAIN (top link); physical zone = tower wall between the +13.90 datum and the top",
               "OWNER_STATUS": "OWNER_PROVISIONAL",
               "ROLE": "chain link; the SOLID_PARAPET reading rests on A-A (DIM-10/DIM-11 hatched cut walls 0.50 above the slab), not on this sheet",
               "PLASTER": False},
    "DIM-15": {"TEXT": "420", "END_A": "dashed +13.90 line", "END_B": "dashed +9.70 line",
               "OWNER": "STOREY_LEVEL_HEIGHT_CHAIN", "OWNER_STATUS": "OWNER_ESTABLISHED", "ROLE": "datum to datum", "PLASTER": False},
    "DIM-16": {"TEXT": "155", "END_A": "tower top line (+14.40)", "END_B": "horizontal witness line at the DOME apex level, meeting the tower wall",
               "OWNER": "TOWER_DOME_FEATURE (tower top to dome apex)", "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "level difference between two objects; not a face", "PLASTER": False},
    "DIM-17": {"TEXT": "193", "END_A": "dome apex witness line", "END_B": "handrail top line",
               "OWNER": "HANDRAIL_TOP_RAIL vs TOWER_DOME_FEATURE", "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "level difference; not a face", "PLASTER": False},
    "DIM-18": {"TEXT": "104", "END_A": "handrail top line (tick on the rail line)", "END_B": "terrace base line (tick on the thick base line)",
               "OWNER": "BALUSTRADE_RAILING assembly: rail + open lattice + solid kerb above the base line",
               "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "assembly height; the solid part inside it (kerb) varies and is not 104", "PLASTER": False},
    "DIM-19": {"TEXT": "139", "END_A": "terrace base line", "END_B": "window head below",
               "OWNER": "WALL_BELOW_PARAPET (facade band to the window head)", "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "facade dimension; not a parapet dimension", "PLASTER": False},
    "DIM-20": {"TEXT": "20", "END_A": "upper line of the horizontal band", "END_B": "lower line of the band (= solid wall top)",
               "OWNER": "COPING_CAPPING candidate (band thickness)", "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "band thickness; band role settled on B-B (cap PAR-05 on the cut)", "PLASTER": False},
    "DIM-21": {"TEXT": "680", "END_A": "band underside = solid wall top (+11.10)", "END_B": "+4.30 annex roof slab (hatched)",
               "OWNER": "WALL_BELOW_PARAPET + SOLID_PARAPET external face, one continuous run", "OWNER_STATUS": "OWNER_ESTABLISHED",
               "ROLE": "top of the solid external face; the parapet / floor split inside it is a convention", "PLASTER": True},
    "DIM-07": {"TEXT": "130", "END_A": "top of the un-hatched outer NW roof-edge element", "END_B": "slab top +9.70",
               "OWNER": "UNRESOLVED (NW sea-view roof-edge element UNK-06)", "OWNER_STATUS": "OWNER_PROVISIONAL",
               "ROLE": "B-B only; NOT on the SE elevation", "PLASTER": False},
    "DIM-08": {"TEXT": "50", "END_A": "tower block top", "END_B": "dashed +13.90 line", "OWNER": "STOREY_LEVEL_HEIGHT_CHAIN / tower parapet seen in elevation",
               "OWNER_STATUS": "OWNER_PROVISIONAL", "ROLE": "B-B", "PLASTER": False},
    "DIM-10": {"TEXT": "50", "END_A": "parapet top line (hatched cut wall)", "END_B": "slab top line (hatched)",
               "OWNER": "SOLID_PARAPET (tower, NE wall, roof-side face)", "OWNER_STATUS": "OWNER_ESTABLISHED", "ROLE": "A-A cut", "PLASTER": True},
    "DIM-11": {"TEXT": "50", "END_A": "parapet top line (hatched cut wall)", "END_B": "dashed level line at the slab top",
               "OWNER": "SOLID_PARAPET (tower, SW wall)", "OWNER_STATUS": "OWNER_PROVISIONAL", "ROLE": "A-A cut", "PLASTER": True},
}
CROSS_SHEET = {
    "DIM-07 (130, B-B) vs SE elevation roof edge": "DIFFERENT_PHYSICAL_LOCATION: the 130 terminates on the NW (sea-view) "
                                                  "roof-edge element at the right end of B-B; the SE parapet is at the left end of B-B",
    "B-B cut PAR-04 / BAL-02 / PAR-05 vs SE elevation lattice portion": "SAME_PHYSICAL_LOCATION_PROVISIONAL: SEC-01 cuts the roof "
        "plan at y=750 inside PAR-01's run 592-980; by proportion that lands in the lattice zone of the elevation, where the kerb "
        "top in elevation (~0.57 above the base line) matches the hatched kerb 0.54 at the cut. Not a traced tick",
    "A-A PAR-08 / PAR-09 (50) vs SE elevation PAR-10 (50)": "SAME_PHYSICAL_OBJECT_DIFFERENT_FACE: one tower parapet ring; A-A cuts "
        "its NE / SW walls, the SE elevation shows its SE face",
}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _native(doc, trace) -> tuple:
    pg = doc[trace["ORIGINAL_PDF_PAGE"] - 1]          # ORIGINAL_PDF_PAGE is 1-based
    info = doc.extract_image(pg.get_images()[0][0])
    img = Image.open(io.BytesIO(info["image"])).convert("L")
    return img, _sha(info["image"]), trace["ORIGINAL_PAGE_COORDINATE_TRANSFORM"]


def _to_orig(T, x, y):
    xr = x / T["scale"] + T["trim_x0"]
    yr = y / T["scale"] + T["trim_y0"]
    return (T["W_orig"] - 1) - yr, xr


def _crop(img, T, x0, y0, x1, y1, k=1.0):
    pts = [_to_orig(T, x0, y0), _to_orig(T, x1, y0), _to_orig(T, x0, y1), _to_orig(T, x1, y1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    box = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
    c = img.crop(box).rotate(90, expand=True)
    if k != 1.0:
        c = c.resize((int(c.width * k), int(c.height * k)), Image.LANCZOS)
    return c, box


def run() -> dict:
    NATIVE.mkdir(parents=True, exist_ok=True)
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    c6 = {t["TRACE_ID"]: t for t in reg["TRACES"] if t["CASE_ID"] == CASE}
    owners = {r["TRACE_ID"]: r for r in json.loads(
        (OUT / "DIMENSION_OWNER_REGISTER.json").read_text("utf-8"))["PER_CASE"][CASE]}
    doc = pymupdf.open(PDF)
    pages, hashes = {}, {}
    for sheet in ("SOUTH_EAST_ELEVATION", "SECTION_B_B", "SECTION_A_A"):
        t = next(x for x in c6.values() if x["SHEET_ID"] == sheet)
        img, h, T = _native(doc, t)
        pages[sheet] = (img, T)
        hashes[sheet] = {"ORIGINAL_PAGE": t["ORIGINAL_PDF_PAGE"], "EMBEDDED_IMAGE_SHA256": h,
                         "MATCHES_TRACE_SOURCE_FILE_HASH": h == t["SOURCE_FILE_HASH"],
                         "NATIVE_SIZE": img.size}
    records = []
    for tid, a in AUDIT.items():
        t = c6[tid]
        img, T = pages[t["SHEET_ID"]]
        bb = t.get("TEXT_BBOX")
        dl = t.get("DIMENSION_LINE_TRACE")
        xs = [p[0] for p in (dl or [])] + ([bb[0], bb[2]] if bb else [])
        ys = [p[1] for p in (dl or [])] + ([bb[1], bb[3]] if bb else [])
        x0, y0, x1, y1 = min(xs) - 25, min(ys) - 15, max(xs) + 25, max(ys) + 15
        crop, box = _crop(img, T, x0, y0, x1, y1, k=1.0)
        p = NATIVE / f"{tid}_{a['TEXT']}.png"
        crop.save(p)
        det = owners.get(tid, {})
        records.append({
            "TRACE_ID": tid, "SHEET_ID": t["SHEET_ID"], "ORIGINAL_PAGE": t["ORIGINAL_PDF_PAGE"],
            "SOURCE_HASH": t["SOURCE_FILE_HASH"], "PRESENTATION_HASH": t["SOURCE_PRESENTATION_HASH"],
            "READ_TEXT": a["TEXT"], "TEXT_READ_STATUS": t.get("DIMENSION_STATUS"),
            "VALUE_M_AS_FROZEN": t.get("VALUE_M"),
            "TEXT_BBOX": bb, "DIMENSION_LINE_TRACE": dl,
            "EXTENSION_LINE_A": t.get("EXTENSION_LINE_A"), "EXTENSION_LINE_B": t.get("EXTENSION_LINE_B"),
            "TICK_ENDPOINTS_PX": ([dl[0], dl[-1]] if dl else None),
            "TICK_ENDPOINTS_NATIVE": ([list(map(round, _to_orig(T, *dl[0]))), list(map(round, _to_orig(T, *dl[-1])))]
                                      if dl else None),
            "NATIVE_EVIDENCE_IMAGE": str(p.relative_to(OUT)), "NATIVE_CROP_BOX": box,
            "ORCHESTRATOR_NATIVE_READ": a["TEXT"],
            "END_A_TERMINATES_ON": a["END_A"], "END_B_TERMINATES_ON": a["END_B"],
            "OWNER_OBJECT_CANDIDATE": a["OWNER"],
            "DIMENSION_OWNER_STATUS_DETERMINISTIC": det.get("DIMENSION_OWNER_STATUS"),
            "DIMENSION_OWNER_STATUS_TERMINATION_BASED": a["OWNER_STATUS"],
            "DIMENSION_ROLE": a["ROLE"],
            "USABLE_AS_PLASTER_HEIGHT": a["PLASTER"] and a["OWNER_STATUS"] == "OWNER_ESTABLISHED",
            "CROSS_SHEET_RELATION_STATUS": (
                "DIFFERENT_PHYSICAL_LOCATION (NW edge)" if tid == "DIM-07" else
                "SAME_PHYSICAL_OBJECT_DIFFERENT_FACE (tower parapet ring)" if tid in ("DIM-08", "DIM-10", "DIM-11", "DIM-14") else
                "SINGLE_SHEET"),
        })
    # ---- 104 / 139 / 93 / 97 -------------------------------------------
    img, T = pages["SOUTH_EAST_ELEVATION"]
    c, box = _crop(img, T, 660, 660, 790, 860, 1.0); (NATIVE / "chain_104_139.png").parent.mkdir(exist_ok=True)
    c.save(NATIVE / "chain_104_139.png")
    c, box97 = _crop(img, T, 330, 400, 600, 800, 0.5); c.save(NATIVE / "left_of_tower_97.png")
    c, boxb = _crop(img, T, 560, 780, 1140, 1000, 0.5); c.save(NATIVE / "below_parapet_139_windows.png")
    text_status = {
        "104_SOURCE_STATUS": {"STATUS": "ESTABLISHED", "WHERE": "SOUTH_EAST_ELEVATION page 4, printed vertically INSIDE the "
                              "X-lattice zone between the rail line and the base line, processed TEXT_BBOX [702,693,723,727], "
                              f"native crop box {box}", "EVIDENCE": "decision_cards/se_native/chain_104_139.png",
                              "WHY_THE_OWNER_MISSED_IT": "small text over the lattice hatching; readable at native 400 dpi",
                              "IS_IT_A_MISREAD_OF_139": False, "STAYS_IN_FORWARD_USE": "as a BALUSTRADE assembly height only; "
                              "it was never in plaster arithmetic and is not now"},
        "139_SOURCE_STATUS": {"STATUS": "ESTABLISHED", "WHERE": "same chain, immediately below the base line tick, "
                              "processed TEXT_BBOX [708,777,723,807]", "OWNER": "base line -> window head (facade)",
                              "INDEPENDENT_OF_104": True},
        "130_SOURCE_STATUS": {"STATUS": "ESTABLISHED_ON_SECTION_B_B_ONLY", "SE_ELEVATION": "not present",
                              "EVIDENCE": "decision_cards/se_native/DIM-07_130.png"},
        "93_97_SOURCE_STATUS": {"STATUS": "TEXT_PRESENT_NOT_TRACED", "WHERE": "97 (with 441, 170, 200) on the arched feature "
                                f"LEFT of the tower, processed region x 330-600 y 400-800, native crop {box97}; 93 not located "
                                "in the parapet chain", "EVIDENCE": "decision_cards/se_native/left_of_tower_97.png",
                                "RELATION_TO_PARAPET": "none; not in the A21 register"},
        "155_50_SAFETY": {"155": "OWNER_ESTABLISHED as tower-top-to-dome-apex; not a face; NOT usable",
                          "50 (SE)": "OWNER_PROVISIONAL (datum termination); NOT usable from this sheet; the tower parapet "
                                     "roof-side face 0.50 is OWNER_ESTABLISHED on A-A (DIM-10) with a hatched cut wall"},
        "DIMENSION_TEXT_CORRECTION": "none required: 104 and 139 are both printed; the frozen readings stand",
    }
    # ---- SE roof-edge material audit -------------------------------------
    material = {
        "SOLID_PLASTERABLE": [
            {"ELEMENT": "full-height solid wall portion (PAR-12, elevation x 835-1112)", "MATERIAL": "solid (drawn as wall face; "
             "the B-B cut is not through this portion)", "EXTERNAL_FACE_TOP": "+11.10 (band underside, DIM-21 chain)",
             "EXTERNAL_FACE_BOTTOM": "convention: +9.70 slab-top datum (1.40) / +9.88 base line (1.22) / owner storey sum +10.00 (1.10)",
             "LENGTH": "NOT_ESTABLISHED (no printed length of the solid portion; the 7.10 chain is the whole run)"},
            {"ELEMENT": "solid kerb / upstand under the lattice (PAR-11; B-B PAR-04 hatched 0.54 at the cut)",
             "MATERIAL": "solid masonry, hatched on B-B; curved (ogee) top in elevation, rounded outer edge in section",
             "HEIGHT": "varies 0.19 -> 0.80 above the base line (elevation trace), 0.54 above the slab at the cut", "LENGTH": "NOT_ESTABLISHED"},
            {"ELEMENT": "end pier (SEG-04)", "MATERIAL": "solid (drawn as a post with rounded top)", "STATUS": "UNRESOLVED dims"},
            {"ELEMENT": "tower parapet ring (PAR-10 / PAR-08 / PAR-09)", "MATERIAL": "solid, hatched on A-A",
             "ROOF_SIDE_FACE": "0.50 OWNER_ESTABLISHED (DIM-10)", "LENGTH": "NOT_ESTABLISHED (no roof plan at +13.90)"},
        ],
        "OPEN_ZERO_PLASTER": [{"ELEMENT": "X-lattice balustrade (BAL-03; B-B BAL-02 thin un-hatched)", "PLASTERABLE_SOLID_FACE": 0}],
        "SOLID_UPSTAND_UNDER_BALUSTRADE": "YES: the hatched kerb PAR-04 / PAR-11 stands under the lattice (SOLID_BASE_OF)",
        "HORIZONTAL_BAND": {"CANDIDATES": ["COPING_CAPPING", "HANDRAIL_TOP_RAIL", "slab edge", "decorative"],
                            "EVIDENCE": "20 thick on the flat portion (DIM-20); on B-B a 20-wide cap block PAR-05 sits on top of the "
                                        "lattice at the cut; in elevation the same band runs over the lattice as the rail zone and over "
                                        "the solid wall as its top band",
                            "STATUS": "COPING_CAPPING over the solid wall, HANDRAIL/cap over the lattice - PROVISIONAL"},
        "CURVED_OGEE_PORTION": "solid: the kerb's curved top is the rising top edge of the hatched kerb; its outer face is rounded "
                               "(B-B); PROVISIONAL (one cut)",
        "INTERNAL_VS_EXTERNAL_FACE_HEIGHTS": "NOT the same: externally the solid face is continuous with the facade down to +4.30; "
                                             "on the roof side the face rises from the roof finish (+9.70 slab top plus build-up, "
                                             "unknown). Roof-side height of the solid-wall portion is NOT_ESTABLISHED",
        "EXTERNAL_SKIN_NOTE": "B-B shows an un-hatched 10-px outline element on the OUTER face from the kerb top down to +4.30 "
                              "(UNK-05): an external finish layer whose material (plaster / cladding) is NOT_ESTABLISHED; "
                              "FINISHES_SPECIFICATION is SOURCE_NOT_PROVIDED",
        "PARENT_CHILD": "kerb (parent) / lattice (child, zero) / cap (child, separate item): no double count",
    }
    d1 = {
        "D1_STATUS": "REOPENED_BY_NEW_OWNER_SOURCE_EVIDENCE",
        "WHAT_THE_OLD_D1_RESTED_ON": "face 1.22 / 1.42 from DIM-21 + DIM-20 with the base line at +9.88 (chain 14.40-1.55-1.93-1.04), "
                                     "applied over the whole 7.10 m run",
        "WHAT_THE_RE_CHECK_ESTABLISHED": [
            "every dimension in the chain is printed where the traces say (104 included); no text correction",
            "155 / 193 / 104 / 139 own two objects each and none is a plaster face height",
            "the solid-wall external face top is +11.10 (DIM-21 from +4.30) with the 0.20 band above it (DIM-20)",
            "the band over the solid wall is the same element as the cap over the lattice on B-B: COPING_CAPPING, PROVISIONAL",
            "the full-height solid face spans only the flat portion (elevation x 835-1112), NOT the 7.10 run",
        ],
        "OLD_QUANTITY_IMPACT_WITHDRAWN": {"OLD": {"OPTION_A_1_22_x_7_10": 8.662, "OPTION_B_1_42_x_7_10": 10.082},
                                          "WHY": "a face height was applied over the lattice portion too; the solid portion "
                                                 "has no printed length", "FORWARD_USE": "withdrawn"},
        "RESOLVED_BY_SOURCE": {"BAND_ROLE": "COPING_CAPPING (separate item), PROVISIONAL via B-B PAR-05",
                               "FACE_TOP": "+11.10 ESTABLISHED (DIM-21 + LVL +4.30)",
                               "BALUSTRADE": "zero", "KERB": "solid upstand, curved, heights vary"},
        "RESIDUAL": {"KIND": "MEASUREMENT_BASIS (where the floor / parapet split lies), plus the identity of the base line",
                     "OPTIONS": {"A_SPLIT_AT_SLAB_TOP_DATUM_9_70": {"FACE_M": 1.40, "WHY": "drawing datum (DIM-15, DIM-09, LVL-03); "
                                                                  "consistent with the sections"},
                                 "B_SPLIT_AT_BASE_LINE_9_88": {"FACE_M": 1.22, "WHY": "the drawn base line; its identity "
                                                              "(slab edge / fascia / kerb foot) is NOT_ESTABLISHED"},
                                 "C_SPLIT_AT_OWNER_STOREY_SUM_10_00": {"FACE_M": 1.10, "WHY": "owner external storey heights "
                                                                       "4.00 + 4.50 from +1.00 = +9.50 ... not a drawing level"}},
                     "QUANTITY_DIFFERENCE_PER_METRE_RUN_M2": {"A_minus_B": 0.18, "A_minus_C": 0.30},
                     "LENGTH_STATUS": "NOT_ESTABLISHED for the solid portion; so no m2 is affected today",
                     "WHY_SOURCE_HIERARCHY_CANNOT_DECIDE": "the split is a convention between two drawing levels, not a fact "
                                                          "on the sheet; the base line's physical identity has no section through the flat portion",
                     "TECHNICAL_RECOMMENDATION": "OPTION A (split at the +9.70 slab-top datum, face 1.40 to the band underside; "
                                                 "band 0.20 as capping; kerb as a curved upstand from the same datum). It is the "
                                                 "only option built on established levels and it matches how B-B measures the kerb"},
        "ESTIMATE_V3_IMPACT": "none: every SE parapet face stays UNRESOLVED on length; capping 1.42 provisional unchanged",
        "OWNER_DECISION_REQUIRED": True,
    }
    # ---- D2 from existing sources (E1.4 + DWG + raster) ----------------
    d2 = {
        "D2_STATUS": "RESOLVED_PROVISIONAL_BY_SOURCE_HIERARCHY",
        "EVIDENCE": [
            "DWG: layer-5 line CAD-783 (1.45 m) from the neighbour wall inner face to a 550 x 250 loop on layers 5 + S-COL.BON "
            "(E1.4 LOOP-059) and a layer-2 line 50 mm east; no double line, no hatch along the 1.45 m",
            "E1.4 LINE_SEMANTICS: CAD-783 SEMANTIC_ENTITY_ROLE = COLUMN, VISIBLE_MATERIAL_FACE, 'IT_DOES_NOT_OWN_THE_ROOMS_CLEAR_FACE'",
            "E1.4 COLUMN_EXISTENCE LOOP-059: STRUCTURAL_COLUMN_UNRESOLVED, NOT_EXPOSED_TO_ROOM, 'an architectural wall face "
            "continues straight across this column'; LOOP-076 above it EXPOSED_TO_ROOM, also unresolved",
            "E1.4 ATOMIC_INTERVAL CAD-260#01: the neighbour wall face is split at exactly -134219.9, a 5.150 m MATERIAL_WALL_FACE "
            "interval (independent corroboration of the owner-verified 515 endpoints)",
            "raster: the reader saw a DASHED line at the open edge (OE-01), not a wall",
        ],
        "CLASSIFICATION": "EDGE_LEVEL_LINE / structural outline: no drawn wall, no low wall, no planter",
        "PLASTERABLE_FACE": "NONE established; scope closed provisionally",
        "RESIDUAL": "if the structural set (ST7757.dwg, PRESENT_NOT_DECODED) shows an exposed free-standing column here, its "
                    "exposed faces would be column bonding + plaster; not estimated now",
        "OWNER_DECISION_REQUIRED": False,
    }
    d3 = {"D3_STATUS": "OWNER_CONFIRMATION_REQUIRED", "NEW_EVIDENCE": "none this round (OLE metadata reader not available); "
          "reconciliation stays conditional on identity; benchmark data retained"}
    # ---- the card ------------------------------------------------------
    k = 0.6
    ratio = k / T["scale"]
    bx = (560, 400, 1140, 800)
    card, _ = _crop(img, T, *bx, k=k)
    card = card.convert("RGB"); d = ImageDraw.Draw(card)

    def P2(x, y):
        return ((x - bx[0]) * ratio, (y - bx[1]) * ratio)

    def poly(tid, col, w=3, label=None):
        t = c6[tid]
        pts = t.get("PIXEL_POLYGON") or t.get("PIXEL_POLYLINE")
        if not pts:
            return
        pp = [P2(*q) for q in pts]
        if t.get("PIXEL_POLYGON"):
            pp.append(pp[0])
        d.line(pp, fill=col, width=w)
        d.text((pp[0][0] + 4, pp[0][1] + 4), label or tid, fill=col)
    G, O, B, M, K = (0, 150, 0), (255, 120, 0), (0, 120, 255), (220, 0, 160), (90, 90, 90)
    poly("PAR-12", G, 4, "PAR-12 solid wall face (top +11.10; length NOT est.)")
    poly("PAR-11", G, 4, "PAR-11 solid kerb / upstand, curved")
    poly("BAL-03", O, 3, "BAL-03 open lattice = 0")
    poly("PAR-13", B, 3, "PAR-13 band: capping (prov.)")
    poly("SEG-04", G, 3, "SEG-04 pier")
    poly("UNK-09", K, 2, "base line +9.88 (identity NOT est.)")
    for tid in ("DIM-16", "DIM-17", "DIM-18", "DIM-19", "DIM-20", "DIM-21"):
        t = c6[tid]
        if t.get("DIMENSION_LINE_TRACE"):
            d.line([P2(*q) for q in t["DIMENSION_LINE_TRACE"]], fill=M, width=2)
        for key in ("EXTENSION_LINE_A", "EXTENSION_LINE_B"):
            if t.get(key):
                d.line([P2(*q) for q in t[key]], fill=(130, 0, 130), width=2)
        if t.get("TEXT_BBOX"):
            a, b, c2, e = t["TEXT_BBOX"]
            d.rectangle([*P2(a, b), *P2(c2, e)], outline=M, width=2)
            d.text((P2(c2, b)[0] + 4, P2(c2, b)[1]), f"{AUDIT[tid]['TEXT']}: {AUDIT[tid]['OWNER'].split(' (')[0].split(':')[0]}", fill=M)
    bar = Image.new("RGB", (card.width, 84), (255, 255, 255)); db = ImageDraw.Draw(bar)
    db.text((8, 4), "D1_SE_PARAPET_SOURCE_CARD - original SOUTH EAST ELEVATION (page 4, native scan, hash-verified)", fill=(0, 0, 0))
    db.text((8, 22), "green = solid plasterable   orange = open balustrade (zero)   blue = band / capping (prov.)   "
                     "magenta = printed dimension + text   purple = witness lines   grey = base line", fill=(60, 60, 60))
    db.text((8, 40), "PRINTED NUMBER != PHYSICAL OBJECT != PLASTERABLE FACE: 155 (tower top->dome apex), 193 (dome->rail), "
                     "104 (rail->base line, balustrade assembly), 139 (base line->window head) are not face heights", fill=(0, 0, 0))
    db.text((8, 58), "130 is on SECTION B-B (NW edge, different location). 50 is the top link of 100+870+420+50=1440 (SE); "
                     "the 0.50 solid parapet face is established on A-A only.", fill=(0, 0, 0))
    outc = Image.new("RGB", (card.width, card.height + 84), (255, 255, 255)); outc.paste(bar, (0, 0)); outc.paste(card, (0, 84))
    # B-B inset
    bbimg, Tbb = pages["SECTION_B_B"]
    ins, _ = _crop(bbimg, Tbb, 600, 470, 700, 580, 1.2)
    ins = ins.convert("RGB"); di = ImageDraw.Draw(ins)
    di.text((4, 2), "B-B cut (plan y=750): kerb 0.54 hatched / lattice / cap", fill=(0, 0, 0))
    outc.paste(ins, (outc.width - ins.width - 4, 88))
    pcard = CARDS / "D1_SE_PARAPET_SOURCE_CARD.png"
    outc.save(pcard)
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "SE_ELEVATION_SOURCE_AUDIT",
            "OWNER_VERIFIED": OWNER_VERIFIED_SE, "NATIVE_SOURCE": hashes,
            "PHYSICAL_OWNER_VOCABULARY": PHYSICAL_OWNERS,
            "DIMENSION_TRACE_AUDIT": records, "TEXT_SOURCE_STATUS": text_status,
            "CROSS_SHEET_RELATIONS": CROSS_SHEET,
            "SE_ROOF_EDGE_MATERIAL_AUDIT": material,
            "D1": d1, "D2": d2, "D3": d3,
            "CARD": {"IMAGE": str(pcard.relative_to(OUT)), "IMAGE_SHA256": _sha(pcard.read_bytes())},
            "FROZEN_OUTPUTS_REWRITTEN": False, "SALOON_WORK_REOPENED": False}
    p = OUT / "SE_ELEVATION_SOURCE_AUDIT.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"SE_ELEVATION_SOURCE_AUDIT_SHA256": _sha(p.read_bytes()),
            "NATIVE_SOURCE": hashes, "104": text_status["104_SOURCE_STATUS"]["STATUS"],
            "139": text_status["139_SOURCE_STATUS"]["STATUS"], "D1": d1["D1_STATUS"], "D2": d2["D2_STATUS"],
            "OWNER_STATUS": {r["TRACE_ID"]: (r["READ_TEXT"], r["DIMENSION_OWNER_STATUS_DETERMINISTIC"],
                                             r["DIMENSION_OWNER_STATUS_TERMINATION_BASED"]) for r in records}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
