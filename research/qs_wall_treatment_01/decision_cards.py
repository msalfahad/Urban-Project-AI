"""DECISION CARDS (§12, §17) - visual, one per residual item.

Each card carries the drawing crop with the trace overlay and, where a
registration exists, the authored CAD runs projected onto it; the printed
dimension and its extension lines; the A21, CAD and contractor positions;
the quantity impact; and a classification. Items the source hierarchy
resolved are rendered too, marked AUTO_RESOLVED, so the owner can see why;
only items marked OWNER_DECISION_REQUIRED need an answer.

    python3 -m research.qs_wall_treatment_01.decision_cards
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from engine import cad_trace_registration as R
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
CARDS = OUT / "decision_cards"
COL = {"trace": (255, 60, 60), "cad": (0, 140, 255), "dim": (230, 0, 160), "ext": (120, 0, 120)}


def _crop(sheet_img: Image.Image, box, k: int) -> Image.Image:
    c = sheet_img.crop(box)
    return c.resize((c.width * k, c.height * k), Image.LANCZOS)


def _draw_traces(d: ImageDraw.ImageDraw, traces: dict, ids: list, box, k):
    x0, y0 = box[0], box[1]
    for tid in ids:
        t = traces.get(tid)
        if not t:
            continue
        pts = None
        if t.get("PIXEL_POLYLINE"):
            pts = t["PIXEL_POLYLINE"]
        elif t.get("PIXEL_BBOX"):
            a, b, c2, e = t["PIXEL_BBOX"]
            pts = [[a, b], [c2, b], [c2, e], [a, e], [a, b]]
        if pts:
            d.line([((x - x0) * k, (y - y0) * k) for x, y in pts], fill=COL["trace"], width=3)
            d.text(((pts[0][0] - x0) * k + 4, (pts[0][1] - y0) * k + 4), tid, fill=COL["trace"])
        for key, col in (("DIMENSION_LINE_TRACE", COL["dim"]), ("EXTENSION_LINE_A", COL["ext"]),
                         ("EXTENSION_LINE_B", COL["ext"])):
            if t.get(key):
                d.line([((x - x0) * k, (y - y0) * k) for x, y in t[key]], fill=col, width=2)
        if t.get("TEXT_BBOX"):
            a, b, c2, e = t["TEXT_BBOX"]
            d.rectangle([(a - x0) * k, (b - y0) * k, (c2 - x0) * k, (e - y0) * k], outline=COL["dim"], width=2)


def _draw_cad(d: ImageDraw.ImageDraw, reg: R.Registration, runs: list, box, k):
    x0, y0 = box[0], box[1]
    for r in runs:
        if r["AXIS"] == "H":
            a = reg.to_px(r["FROM_MM"], r["FIXED_MM"]); b = reg.to_px(r["TO_MM"], r["FIXED_MM"])
        else:
            a = reg.to_px(r["FIXED_MM"], r["FROM_MM"]); b = reg.to_px(r["FIXED_MM"], r["TO_MM"])
        d.line([((a[0] - x0) * k, (a[1] - y0) * k), ((b[0] - x0) * k, (b[1] - y0) * k)],
               fill=COL["cad"], width=3)
        d.text(((a[0] - x0) * k + 4, (a[1] - y0) * k - 14), r.get("LABEL", ""), fill=COL["cad"])


def _legend(img: Image.Image, title: str) -> Image.Image:
    bar = Image.new("RGB", (img.width, 44), (255, 255, 255))
    d = ImageDraw.Draw(bar)
    d.text((8, 4), title, fill=(0, 0, 0))
    d.text((8, 24), "red = A21 trace   blue = authored CAD run (registered)   magenta = printed "
                    "dimension / text   purple = extension lines", fill=(60, 60, 60))
    out = Image.new("RGB", (img.width, img.height + 44), (255, 255, 255))
    out.paste(bar, (0, 0))
    out.paste(img, (0, 44))
    return out


def run() -> dict:
    CARDS.mkdir(parents=True, exist_ok=True)
    reg_doc = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    links = json.loads((OUT / "CAD_TRACE_LINKS.json").read_text("utf-8"))
    dual = json.loads((OUT / "DUAL_BASIS.json").read_text("utf-8"))
    est = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE_v2.json").read_text("utf-8"))
    regis = R.Registration([(p["MM"], p["PX"]) for p in links["REGISTRATION"]["X_PAIRS"]],
                           [(p["MM"], p["PX"]) for p in links["REGISTRATION"]["Y_PAIRS"]])
    gf = Image.open(Path(P.CASE_SANDBOX) / "CASE-3-DOOR-AND-WINDOW" / "GROUND_FLOOR_PLAN.jpeg").convert("RGB")
    se = Image.open(Path(P.CASE_SANDBOX) / "CASE-6-ROOF-PARAPET" / "SOUTH_EAST_ELEVATION.jpeg").convert("RGB")
    t3 = {t["TRACE_ID"]: t for t in reg_doc["TRACES"]
          if t["CASE_ID"] == "CASE-3-DOOR-AND-WINDOW" and t["SHEET_ID"] == "GROUND_FLOOR_PLAN"}
    t6 = {t["TRACE_ID"]: t for t in reg_doc["TRACES"]
          if t["CASE_ID"] == "CASE-6-ROOF-PARAPET" and t["SHEET_ID"] == "SOUTH_EAST_ELEVATION"}
    lk = {l["LINK_ID"]: l for l in links["LINKS"]}
    h = est["PARAMETER_REGISTRY"]["NORMAL_INTERNAL_PLASTER_HEIGHT"]["VALUE"]
    cards = []

    def card(cid, title, img, meta):
        p = CARDS / f"{cid}.png"
        _legend(img, f"{cid} - {title}").save(p)
        cards.append({"CARD_ID": cid, "TITLE": title, "IMAGE": str(p.relative_to(OUT)),
                      "IMAGE_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(), **meta})

    # ---- T2 (auto-resolved) ----------------------------------------
    box, k = (1480, 980, 1830, 1080), 3
    im = _crop(gf, box, k); d = ImageDraw.Draw(im)
    _draw_traces(d, t3, ["SEG-02", "DIM-05", "OE-01", "COL-02"], box, k)
    _draw_cad(d, regis, [{**lk["L1"]["RUN"], "LABEL": "CAD stub->wall line 5.150"},
                         {**lk["L6"]["RUN"], "LABEL": "CAD stub 1.45"}], box, k)
    card("T2", "SALOON neighbour wall face: printed 5.15 vs authored run", im, {
        "STATUS": "AUTO_RESOLVED", "CLASS": "CAD_MAPPING_DIFFERENCE",
        "DRAWING_LOCATION": "GROUND_FLOOR_PLAN, SALOON south wall, px x 1480-1830 y 980-1080",
        "PRINTED_DIMENSION": "DIM-05 '515' from the open-edge tick to the sea-view wall line",
        "A21_INTERPRETATION": "SEG-02 face 5.15 m", "CAD_INTERPRETATION":
            "authored face run from the layer-5 stub (x -134220) to the wall line (x -129070) = 5.150; "
            f"link {lk['L1']['CAD_TRACE_LINK_STATUS']}; the 8.43 in A22 was a window artefact",
        "CONTRACTOR_POSITION": "one 'صالة' perimeter line, zone extent unknown",
        "QUANTITY_IMPACT_M2": 0.0, "WHY_THEY_DIFFER": "locator window, not geometry",
        "OWNER_DECISION_REQUIRED": False})
    # ---- T3 / T9 (auto-resolved by hierarchy) -----------------------
    box, k = (1740, 630, 1830, 1080), 3
    im = _crop(gf, box, k); d = ImageDraw.Draw(im)
    _draw_traces(d, t3, ["SEG-01", "GLZ-01", "COL-01", "COL-02", "DIM-01", "DIM-02", "DIM-03", "DIM-04"], box, k)
    _draw_cad(d, regis, [{**lk["L3"]["RUN"], "LABEL": "CAD glazing 6.332"},
                         {**lk["L4"]["RUN"], "FIXED_MM": -129040.0, "LABEL": "pier body 0.900"},
                         {**lk["L4X"]["RUN"], "FIXED_MM": -129000.0, "LABEL": "exposed 0.700"},
                         {**lk["L5"]["RUN"], "FIXED_MM": -129040.0, "LABEL": "pier body 0.668"},
                         {**lk["L5X"]["RUN"], "FIXED_MM": -129000.0, "LABEL": "exposed 0.468"}], box, k)
    old = round(1.80 * h, 4); new = round((0.700 + 0.468) * h, 4)
    card("T3_T9", "sea-view line chain 90+633+20+90 and the corner piers", im, {
        "STATUS": "AUTO_RESOLVED", "CLASS": "DIMENSION_OWNERSHIP_DIFFERENCE",
        "DRAWING_LOCATION": "GROUND_FLOOR_PLAN, SALOON sea-view line, px x 1740-1830 y 630-1080",
        "PRINTED_DIMENSION": "DIM-02 '90', DIM-01 '633', DIM-04 '20', DIM-03 '90' (vertical chain at x 1810)",
        "A21_INTERPRETATION": "COL-01 0.90, GLZ-01 6.33, frame 0.20, COL-02 0.90 -> 8.33; column line 1.80 lm",
        "CAD_INTERPRETATION": ("633 = glazing band exactly (link ESTABLISHED); lower 90 = pier body "
                               "incl. 0.20 wall thickness (ESTABLISHED); exposed faces 0.700 and "
                               "0.468 (PROVISIONAL links); upper 90 matches no authored span"),
        "CONTRACTOR_POSITION": "corners and endings counted in lm at 2m=1m; no column m2 line",
        "QUANTITY_IMPACT_M2": {"A21_LINE_RETIRED": old, "CAD_LINE_PROVISIONAL": new,
                               "DELTA": round(new - old, 4)},
        "WHY_THEY_DIFFER": "the printed 90s measure pier bodies / an unowned span, not exposed plaster faces",
        "OWNER_DECISION_REQUIRED": False})
    # ---- D1 owner: SE parapet face basis ---------------------------
    box, k = (560, 600, 1140, 800), 2
    im = _crop(se, box, k); d = ImageDraw.Draw(im)
    _draw_traces(d, t6, ["PAR-11", "PAR-12", "PAR-13", "BAL-03", "DIM-20", "DIM-21", "DIM-18", "UNK-09"], box, k)
    card("D1", "SE terrace parapet: which solid face height is the engineering face?", im, {
        "STATUS": "OWNER_DECISION_REQUIRED", "CLASS": "DRAWING_AMBIGUITY",
        "DECISION_REQUIRED": "engineering solid-face height of the SE terrace parapet",
        "DRAWING_LOCATION": "SOUTH_EAST_ELEVATION px x 560-1140 y 600-800; B-B cut at plan y 750",
        "ENGINEERING_BASIS": "band underside +11.10 (DIM-21 680 from +4.30) -> face 1.22 above the "
                             "+9.88 base line; band 0.20 (DIM-20) is the capping band PAR-13; kerb "
                             "0.18 below the base line to the +9.70 slab",
        "CONTRACTOR_BASIS": "دروة 48.47 lm x 1.70 = 82.399 m2; what 1.70 includes is UNRESOLVED",
        "WHY_DIFFERENT": "the drawing shows a composite (kerb + lattice + capping) whose solid face is "
                         "1.22 or 1.42 depending on whether the band is a face or a capping; the site "
                         "record measured 1.70 on an unstated basis",
        "QUANTITY_IMPACT_M2": {"PER_7_10_M_RUN": {"OPTION_A_1_22": round(7.10 * 1.22, 3),
                                                  "OPTION_B_1_42": round(7.10 * 1.42, 3),
                                                  "DELTA": round(7.10 * 0.20, 3)}},
        "KWD_IMPACT": "no rate quoted (P7757_RATE_CARD: NO_RATE_HAS_BEEN_QUOTED)",
        "OPTION_A": "face 1.22 to the band underside; band 0.20 measured as ROOF_PARAPET_CAPPING",
        "OPTION_B": "face 1.42 including the band as wall face; no separate capping",
        "TECHNICAL_RECOMMENDATION": "OPTION_A: the band is traced as a distinct capping element on "
                                    "the elevation and the B-B cut (PAR-13 / PAR-05); keeping it as "
                                    "its own item avoids a double count and keeps the face measurable "
                                    "from printed dimensions",
        "OWNER_DECISION_REQUIRED": True})
    # ---- D2 owner: stub at the open edge ---------------------------
    box, k = (1480, 560, 1600, 1080), 2
    im = _crop(gf, box, k); d = ImageDraw.Draw(im)
    _draw_traces(d, t3, ["OE-01", "SEG-04", "SEG-02"], box, k)
    _draw_cad(d, regis, [{**lk["L6"]["RUN"], "LABEL": "CAD layer-5 stub 1.45"},
                         {"AXIS": "V", "FIXED_MM": -134169.9, "FROM_MM": -803594.0, "TO_MM": -801194.0,
                          "LABEL": "CAD layer-2 line 2.40"}], box, k)
    card("D2", "element at the SALOON / RECEPTION open edge", im, {
        "STATUS": "OWNER_DECISION_REQUIRED", "CLASS": "UNRESOLVED",
        "DECISION_REQUIRED": "what stands at the open edge: low wall, planter, screen or a line only",
        "DRAWING_LOCATION": "GROUND_FLOOR_PLAN px x 1480-1600 y 560-1080 (x 1520 = open edge)",
        "ENGINEERING_BASIS": "A21 traced OE-01 as fully open (no material, no plaster); the DWG "
                             "carries a layer-5 line 1.45 m from the neighbour wall and a layer-2 line "
                             "2.40 m further north, 50 mm apart",
        "CONTRACTOR_BASIS": "not separable in the record",
        "WHY_DIFFERENT": "the raster shows a dashed line the reader read as an open edge; the "
                         "authored lines may be a low wall or planter (plasterable) or a floor line",
        "QUANTITY_IMPACT_M2": {"IF_PLASTERABLE_LOW_WALL_1_45_x_h": "height unknown; up to "
                                                                   f"{round(1.45 * h, 3)} per face at {h}"},
        "KWD_IMPACT": "no rate quoted",
        "OPTION_A": "line only / floor edge: no face, scope closed",
        "OPTION_B": "low wall or planter: a plasterable face of 1.45 m with its own height",
        "TECHNICAL_RECOMMENDATION": "OPTION_A pending a section or site photo; CASE-3 SEG-06 "
                                    "('low wall / planter edge') is the same family of element and "
                                    "is already UNRESOLVED - decide both together",
        "OWNER_DECISION_REQUIRED": True})
    # ---- D3 owner: benchmark identity (no image needed) -------------
    bi = dual["BENCHMARK_IDENTITY"]
    cards.append({"CARD_ID": "D3", "TITLE": "benchmark workbook identity", "IMAGE": None,
                  "STATUS": "OWNER_DECISION_REQUIRED", "CLASS": "IDENTITY_MAPPING_DIFFERENCE",
                  "DECISION_REQUIRED": bi["OWNER_CONFIRMATION_REQUEST"],
                  "ENGINEERING_BASIS": "drawing-derived, frozen", "CONTRACTOR_BASIS": "site record",
                  "WHY_DIFFERENT": "no project identifier in the workbook",
                  "EVIDENCE": bi["EVIDENCE"], "QUANTITY_IMPACT_M2": "none until confirmed",
                  "KWD_IMPACT": "no rate quoted", "OPTION_A": "confirm P7757",
                  "OPTION_B": "not P7757: the reconciliation is withdrawn",
                  "TECHNICAL_RECOMMENDATION": "OPTION_A on the level-chain and overall-height matches",
                  "OWNER_DECISION_REQUIRED": True})
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "DECISION_CARDS", "CARDS": cards,
            "OWNER_DECISIONS_REQUIRED": [c["CARD_ID"] for c in cards if c["OWNER_DECISION_REQUIRED"]],
            "AUTO_RESOLVED": [c["CARD_ID"] for c in cards if not c["OWNER_DECISION_REQUIRED"]]}
    p = OUT / "DECISION_CARDS.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"DECISION_CARDS_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "OWNER_DECISIONS_REQUIRED": body["OWNER_DECISIONS_REQUIRED"],
            "AUTO_RESOLVED": body["AUTO_RESOLVED"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
