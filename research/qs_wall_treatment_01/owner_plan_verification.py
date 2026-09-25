"""OWNER-VERIFIED PLAN INTERPRETATION - a new evidence layer, reconciled
forward. Nothing frozen is rewritten.

The owner opened the architectural plan and verified, for the SALOON:

    515          runs from the SALOON-side wall to the column immediately
                 before the GARDEN               (OWNER_VERIFIED_DIMENSION_OWNERSHIP)
    90 + 633 + 90  the exterior chain; there is no +20 in it
    20           beside it is the block / wall thickness annotation
    both 90s     are legitimate external dimension segments - NOT two
                 exposed plaster faces
    40 + 452 + 45  the next exterior sequence, kept distinct
    150 = 20 + 110 + 20  overall vs clear opening, for THAT opening only

Each printed segment is then compared, as three different objects, with the
authored DWG:

    PRINTED_DIMENSION_OBJECT   what the printed value spans
    CAD_FACE_OBJECT            what the authored lines span at the locator
    PLASTER_CONTRIBUTING_FACE  what, if anything, receives plaster there

and the forward A22 layer separates DIMENSION_TEXT_CORRECTNESS,
DIMENSION_OWNERSHIP, CAD_OBJECT_CORRESPONDENCE and PLASTER_FACE_OWNERSHIP.

    python3 -m research.qs_wall_treatment_01.owner_plan_verification
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from engine import cad_adapter as CA
from engine import cad_trace_registration as R
from engine import dimension_roles as DR
from research.qs_wall_treatment_01 import decision_cards as DC
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.a22_structural_comparison import DECODE, _runs

OUT = Path(P.OUT_DIR)
CASE, SHEET = "CASE-3-DOOR-AND-WINDOW", "GROUND_FLOOR_PLAN"
X = -129070.0          # sea-view wall line / pier inner face, mm
X_OUT = -128870.0      # outer line

OWNER_VERIFIED = {
    "SOURCE": "ARCHITECTURAL_PLAN", "INTERPRETATION": "OWNER_VERIFIED_DIMENSION_OWNERSHIP",
    "VERIFIED_BY": "owner, manual check of the plan", "DATE": "2026-09-19",
    "ITEMS": {
        "515": {"TRACE": "DIM-05", "ROLE": "LINEAR_SPAN",
                "FROM": "the SALOON-side wall (sea-view wall line)",
                "TO": "the column immediately before the GARDEN"},
        "90+633+90": {"TRACES": ["DIM-03", "DIM-01", "DIM-02"], "ROLE": "SETTING_OUT_SEGMENT",
                      "NOTE": "exterior SALOON chain; no +20 in it; both 90s are legitimate "
                              "plan dimension segments, not two exposed plaster faces"},
        "20": {"TRACE": "DIM-04", "ROLE": "WALL_THICKNESS",
               "NOTE": "block / wall thickness annotation beside the chain, not a chain segment"},
        "40+452+45": {"ROLE": "SETTING_OUT_SEGMENT",
                      "NOTE": "next exterior sequence; distinct printed dimensions; not combined "
                              "with the previous chain unless extension-line ownership proves it"},
        "150-20-20=110": {"ROLE": "CLEAR_OPENING",
                          "NOTE": "overall 150 with 20 + 20 construction gives a 110 clear opening; "
                                  "for that specific opening only, never a universal door rule"},
        "20/15 generally": {"ROLE": "WALL_THICKNESS",
                            "NOTE": "20 often exterior block thickness, 15 internal block; never "
                                    "automatically a linear run"},
    },
}

# authored objects the owner's segments are compared with (mm, model space)
SEGMENTS = [
    {"ID": "90 (lower, DIM-03)", "AXIS": "V", "FIXED_MM": X, "FROM_MM": -805293.5, "TO_MM": -804393.5,
     "PRINTED_M": 0.90, "WHAT": "neighbour wall OUTER face -> glazing start", "LAYERS": ("1", "S-COL.BON")},
    {"ID": "633 (DIM-01)", "AXIS": "V", "FIXED_MM": X, "FROM_MM": -804393.5, "TO_MM": -798062.0,
     "PRINTED_M": 6.33, "WHAT": "glazing band", "LAYERS": ("W",)},
    {"ID": "90 (upper, DIM-02)", "AXIS": "V", "FIXED_MM": X, "FROM_MM": -798062.0, "TO_MM": -797162.0,
     "PRINTED_M": 0.90, "WHAT": "glazing end -> the layer-4 / door-layer line at -797162, past the "
                                "return wall outer face (-797393.5)", "LAYERS": ("1", "D", "4", "5")},
    {"ID": "40", "AXIS": "V", "FIXED_MM": X, "FROM_MM": -797162.0, "TO_MM": -796762.0,
     "PRINTED_M": 0.40, "WHAT": "door-layer jamb mark to jamb mark", "LAYERS": ("D", "5")},
    {"ID": "452", "AXIS": "V", "FIXED_MM": X, "FROM_MM": -796762.0, "TO_MM": -792240.6,
     "PRINTED_M": 4.52, "WHAT": "between door-layer jamb marks on the layer-5 line", "LAYERS": ("D", "5")},
    {"ID": "45", "AXIS": "V", "FIXED_MM": X, "FROM_MM": -792240.6, "TO_MM": -791793.5,
     "PRINTED_M": 0.45, "WHAT": "jamb mark to the wall line at -791793.5", "LAYERS": ("D", "1", "2", "5")},
]
SEG_515 = {"ID": "515 (DIM-05)", "AXIS": "H", "FIXED_MM": -805093.5, "FROM_MM": -134219.9,
           "TO_MM": X, "PRINTED_M": 5.15,
           "WHAT": "sea-view wall line -> the layer-5 return line at the column before the GARDEN"}
COLUMN_HATCHES = {
    "PIER_BOTTOM (COL-02)": {"X": (-129069.9, -128869.9), "Y": (-805293.5, -804893.5)},
    "PIER_TOP (COL-01)": {"X": (-129069.9, -128869.9), "Y": (-797893.5, -797393.5)},
    "IN_NEIGHBOUR_WALL (COL-04)": {"X": (-131069.9, -130369.9), "Y": (-805293.6, -805043.6)},
    "BEFORE_GARDEN": {"X": (-134769.9, -134169.9), "Y": (-803793.5, -803543.5)},
}
ROOM_FACE_Y = {"NEIGHBOUR_INNER": -805093.5, "RETURN_INNER": -797593.5, "RETURN_OUTER": -797393.5}


def _endpoints_present(n, seg) -> dict:
    """Do authored lines end / cross at both endpoints of the segment?"""
    loc = {"AXIS": seg["AXIS"], "FIXED_MM": (seg["FIXED_MM"] - 8, seg["FIXED_MM"] + 8),
           "WINDOW_MM": (min(seg["FROM_MM"], seg["TO_MM"]) - 5, max(seg["FROM_MM"], seg["TO_MM"]) + 5),
           "LAYERS": seg.get("LAYERS", ("1", "2", "4", "5", "W", "D", "S-COL.BON"))}
    runs = _runs(n, loc)
    ends = {r["FROM_MM"] for r in runs} | {r["TO_MM"] for r in runs}
    hit = lambda v: any(abs(e - v) <= 12 for e in ends)   # noqa: E731
    return {"RUNS": runs, "FROM_END_PRESENT": hit(seg["FROM_MM"]), "TO_END_PRESENT": hit(seg["TO_MM"]),
            "AUTHORED_SPAN_M": round(abs(seg["TO_MM"] - seg["FROM_MM"]) / 1000, 4)}


def run() -> dict:
    d = json.loads(Path(DECODE).read_text("utf-8"))
    n = CA.normalize(d, source_file="P7757_ARCHITECTURAL.dwg")
    links = json.loads((OUT / "CAD_TRACE_LINKS.json").read_text("utf-8"))
    reg_doc = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    traces = {t["TRACE_ID"]: t for t in reg_doc["TRACES"] if t["CASE_ID"] == CASE and t["SHEET_ID"] == SHEET}
    regis = R.Registration([(p["MM"], p["PX"]) for p in links["REGISTRATION"]["X_PAIRS"]],
                           [(p["MM"], p["PX"]) for p in links["REGISTRATION"]["Y_PAIRS"]])
    # ---- 1. printed segments vs authored objects -----------------------
    seg_rows = []
    for s in SEGMENTS + [SEG_515]:
        chk = _endpoints_present(n, s)
        seg_rows.append({**{k: v for k, v in s.items() if k != "LAYERS"},
                         "CAD_ENDPOINTS_PRESENT": [chk["FROM_END_PRESENT"], chk["TO_END_PRESENT"]],
                         "AUTHORED_SPAN_M": chk["AUTHORED_SPAN_M"],
                         "TEXT_VS_AUTHORED_DELTA_M": round(chk["AUTHORED_SPAN_M"] - s["PRINTED_M"], 4),
                         "DIMENSION_TEXT_CORRECTNESS": ("CORROBORATED" if abs(chk["AUTHORED_SPAN_M"] - s["PRINTED_M"]) <= 0.01
                                                        else "DIFFERS"),
                         "CAD_OBJECT_CORRESPONDENCE": ("ESTABLISHED" if chk["FROM_END_PRESENT"] and chk["TO_END_PRESENT"]
                                                       else "PROVISIONAL" if chk["FROM_END_PRESENT"] or chk["TO_END_PRESENT"]
                                                       else "NOT_ESTABLISHED"),
                         "RUNS_AT_LOCATOR": chk["RUNS"]})
    chain_a = DR.chain_is_continuous(SEGMENTS[:3])
    chain_b = DR.chain_is_continuous(SEGMENTS[3:])
    joined = DR.chain_is_continuous(SEGMENTS)
    # ---- 2. column hatches at the locators -----------------------------
    hatch = {}
    for k, h in COLUMN_HATCHES.items():
        loc = {"AXIS": "V", "FIXED_MM": (h["X"][0] - 8, h["X"][0] + 8), "WINDOW_MM": (h["Y"][0] - 5, h["Y"][1] + 5),
               "LAYERS": ("S-COL.BON",)}
        r = _runs(n, loc)
        hatch[k] = {"DECLARED": h, "FOUND_RUNS": r,
                    "PRESENT": any(abs(x["FROM_MM"] - h["Y"][0]) <= 12 and abs(x["TO_MM"] - h["Y"][1]) <= 12 for x in r)}
    # ---- 3. plaster-contributing faces: three objects side by side -------
    ownership = [
        {"PRINTED_DIMENSION_OBJECT": "90 (lower): outer neighbour-wall face -> glazing start, 0.900",
         "CAD_FACE_OBJECT": "pier inner face (room side, x=-129070) from the neighbour wall INNER face to "
                            "the glazing start: 0.700 (link L4X)",
         "PLASTER_CONTRIBUTING_FACE": {"COLUMN_BONDING": {"LENGTH_M": 0.200, "FROM_TO": "-805093.5 -> -804893.5",
                                                          "EVIDENCE": "S-COL.BON hatch 0.40 x 0.20 at the corner, "
                                                                      "0.20 of it inside the room"},
                                       "NORMAL_PLASTER_BLOCK": {"LENGTH_M": 0.500, "FROM_TO": "-804893.5 -> -804393.5"}},
         "PLASTER_FACE_OWNERSHIP": "PROVISIONAL (layer S-COL.BON hatch extent; no section or schedule)",
         "SETTING_OUT_ONLY_PORTION_M": 0.200, "WHY": "the 0.20 wall thickness inside the printed 90 is not a face"},
        {"PRINTED_DIMENSION_OBJECT": "633: glazing band, 6.332",
         "CAD_FACE_OBJECT": "four W-layer lines 6.332 / 6.232 (link L3 ESTABLISHED)",
         "PLASTER_CONTRIBUTING_FACE": None, "PLASTER_FACE_OWNERSHIP": "GLAZING: no plaster",
         "SETTING_OUT_ONLY_PORTION_M": 6.332, "WHY": "glazing"},
        {"PRINTED_DIMENSION_OBJECT": "90 (upper): glazing end -> the line at -797162, 0.900",
         "CAD_FACE_OBJECT": "pier inner face from the glazing end to the return wall INNER face: 0.468 "
                            "(link L5X); the printed 90 continues 0.432 past the room",
         "PLASTER_CONTRIBUTING_FACE": {"COLUMN_BONDING": {"LENGTH_M": 0.300, "FROM_TO": "-797893.5 -> -797593.5",
                                                          "EVIDENCE": "S-COL.BON hatch 0.50 x 0.20, 0.30 inside the room"},
                                       "NORMAL_PLASTER_BLOCK": {"LENGTH_M": 0.168, "FROM_TO": "-798062.0 -> -797893.5"}},
         "PLASTER_FACE_OWNERSHIP": "PROVISIONAL (layer S-COL.BON hatch extent)",
         "SETTING_OUT_ONLY_PORTION_M": 0.432, "WHY": "the return wall thickness and the 0.232 beyond it are setting-out"},
        {"PRINTED_DIMENSION_OBJECT": "515: sea-view wall line -> the column before the GARDEN, 5.150",
         "CAD_FACE_OBJECT": "neighbour wall inner face from x=-129070 to the layer-5 return line at -134220 (link L1)",
         "PLASTER_CONTRIBUTING_FACE": {"WALL_FACE_TOTAL": {"LENGTH_M": 5.150, "STATUS": "ESTABLISHED (owner-verified endpoints)"},
                                       "OF_WHICH_COLUMN_BONDING_CANDIDATE": {"LENGTH_M": 0.700, "FROM_TO": "x -131069.9 -> -130369.9",
                                                                              "EVIDENCE": "S-COL.BON hatch in the wall, protruding 50 mm",
                                                                              "STATUS": "TRADE_SPLIT_PENDING, not additive"}},
         "PLASTER_FACE_OWNERSHIP": "ESTABLISHED as a plastered run; trade split PROVISIONAL",
         "SETTING_OUT_ONLY_PORTION_M": 0.0, "WHY": "this dimension IS the room-side face run"},
    ]
    # ---- 4. forward A22 layer -------------------------------------------
    forward = {
        "T3_forward": {"DIMENSION_TEXT_CORRECTNESS": {s["ID"]: s["DIMENSION_TEXT_CORRECTNESS"] for s in seg_rows[:3]},
                       "DIMENSION_OWNERSHIP": "OWNER_VERIFIED: 90 + 633 + 90 exterior chain; the 20 is thickness",
                       "CAD_OBJECT_CORRESPONDENCE": {s["ID"]: s["CAD_OBJECT_CORRESPONDENCE"] for s in seg_rows[:3]},
                       "PLASTER_FACE_OWNERSHIP": "the 90s are setting-out segments; plaster faces inside them are "
                                                 "0.20 + 0.50 and 0.30 + 0.168 (PROVISIONAL)",
                       "PREVIOUS_STATEMENT_WITHDRAWN": "'the upper 90 matches no authored span' - it matches "
                                                       "glazing end -> -797162 exactly (0.900)"},
        "T9_forward": {"COLUMN_COMPONENT_STATUS": "PROVISIONAL_SPLIT",
                       "COLUMN_BONDING_FACES_LM": {"COL-02": 0.200, "COL-01": 0.300},
                       "PIER_BLOCK_FACES_LM": {"SEG-01 portions": 0.668},
                       "A21_1_80_LM": "stays retired", "CAD_0_700_0_468": "kept as pier inner-face runs, split by ownership"},
        "T2_forward": {"DIMENSION_OWNERSHIP": "OWNER_VERIFIED endpoints: SALOON-side wall -> column before the GARDEN",
                       "CAD_OBJECT_CORRESPONDENCE": seg_rows[-1]["CAD_OBJECT_CORRESPONDENCE"],
                       "PLASTER_FACE_OWNERSHIP": "5.15 established as the run; 0.70 of it a column-bonding candidate",
                       "D2_UPDATE": "the layer-5 line at the open edge runs from the neighbour wall to the column "
                                    "before the GARDEN: a return wall stub ending in a column, not a floor line"},
        "NEXT_CHAIN_40_452_45": {"CORROBORATED": [s["DIMENSION_TEXT_CORRECTNESS"] for s in seg_rows[3:6]],
                                 "CONTINUOUS_WITH_90_633_90": joined["CONTINUOUS"],
                                 "NOTE": "kept as distinct printed dimensions; both chains are continuous on the "
                                         "authored line but are reported separately as the owner set"},
        "CHAINS": {"90+633+90": chain_a, "40+452+45": chain_b, "JOINED": joined},
        "CLEAR_OPENING_RULE": {"EXAMPLE": DR.clear_opening_width(1.50, [0.20, 0.20]),
                               "APPLIED_TO_TRACED_OPENINGS": "none: no traced opening in the subset carries a "
                                                             "150 with 20 + 20 sides"},
    }
    # ---- 5. the SALOON card ---------------------------------------------
    gf = Image.open(Path(P.CASE_SANDBOX) / CASE / "GROUND_FLOOR_PLAN.jpeg").convert("RGB")
    box, k = (1480, 560, 1830, 1080), 2
    im = DC._crop(gf, box, k); dr = ImageDraw.Draw(im)
    DC._draw_traces(dr, traces, ["SEG-02", "DIM-05", "DIM-01", "DIM-02", "DIM-03", "DIM-04", "GLZ-01", "SEG-03"], box, k)
    runs = [{**{kk: s[kk] for kk in ("AXIS", "FIXED_MM", "FROM_MM", "TO_MM")}, "LABEL": s["ID"] + " setting-out"}
            for s in SEGMENTS[:3]]
    runs.append({**{kk: SEG_515[kk] for kk in ("AXIS", "FIXED_MM", "FROM_MM", "TO_MM")}, "LABEL": "515 face run"})
    DC._draw_cad(dr, regis, runs, box, k)
    green = (0, 150, 0)
    for lbl, y0, y1 in (("bonding 0.20", -805093.5, -804893.5), ("block 0.50", -804893.5, -804393.5),
                        ("block 0.168", -798062.0, -797893.5), ("bonding 0.30", -797893.5, -797593.5)):
        a = regis.to_px(X + 60, y0); b = regis.to_px(X + 60, y1)
        dr.line([((a[0] - box[0]) * k, (a[1] - box[1]) * k), ((b[0] - box[0]) * k, (b[1] - box[1]) * k)], fill=green, width=4)
        dr.text(((a[0] - box[0]) * k - 70, (a[1] - box[1]) * k), lbl, fill=green)
    a = regis.to_px(-130369.9, -805093.5 + 40); b = regis.to_px(-131069.9, -805093.5 + 40)
    dr.line([((a[0] - box[0]) * k, (a[1] - box[1]) * k), ((b[0] - box[0]) * k, (b[1] - box[1]) * k)], fill=green, width=4)
    dr.text(((b[0] - box[0]) * k, (b[1] - box[1]) * k + 6), "COL-04 bonding candidate 0.70 inside the 515", fill=green)
    CARDS = OUT / "decision_cards"
    p_img = CARDS / "S1_SALOON_DIMENSIONS.png"
    bar = Image.new("RGB", (im.width, 64), (255, 255, 255)); db = ImageDraw.Draw(bar)
    db.text((8, 4), "S1 - SALOON: printed dimension != plaster face length", fill=(0, 0, 0))
    db.text((8, 24), "red = A21 trace / printed text   magenta+purple = dimension and extension lines   "
                     "blue = authored CAD spans (setting-out 90+633+90; 515 face run)", fill=(60, 60, 60))
    db.text((8, 44), "green = plaster-contributing faces (bonding / block) - the 20 beside the chain is wall thickness", fill=green)
    outim = Image.new("RGB", (im.width, im.height + 64), (255, 255, 255)); outim.paste(bar, (0, 0)); outim.paste(im, (0, 64))
    outim.save(p_img)
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "OWNER_EVIDENCE_RECONCILIATION",
            "EVIDENCE_LAYER": OWNER_VERIFIED,
            "FROZEN_OUTPUTS_REWRITTEN": False,
            "PRINTED_SEGMENTS_VS_AUTHORED": seg_rows,
            "COLUMN_HATCHES": hatch,
            "PLASTER_FACE_OWNERSHIP": ownership,
            "FORWARD_A22": forward,
            "DIMENSION_ROLE_TAGS": {"DIM-04": "WALL_THICKNESS", "DIM-06": "WALL_THICKNESS", "DIM-09": "WALL_THICKNESS",
                                    "DIM-16": "WALL_THICKNESS", "DIM-01": "SETTING_OUT_SEGMENT (glazing)",
                                    "DIM-02": "SETTING_OUT_SEGMENT", "DIM-03": "SETTING_OUT_SEGMENT",
                                    "DIM-05": "LINEAR_SPAN (face run)", "CASE-1 DIM-10 '15'": "WALL_THICKNESS"},
            "SALOON_CARD": {"IMAGE": str(p_img.relative_to(OUT)),
                            "IMAGE_SHA256": hashlib.sha256(p_img.read_bytes()).hexdigest(),
                            "SHOWS": ["515 endpoints", "90 + 633 + 90 as setting-out spans", "20 as wall thickness",
                                      "CAD 0.700 / 0.468 pier faces split into bonding 0.20 / 0.30 and block 0.50 / 0.168",
                                      "which lines contribute plaster (green) and which are setting-out only (blue)"]},
            "D2_UPDATE": forward["T2_forward"]["D2_UPDATE"]}
    p = OUT / "OWNER_EVIDENCE_RECONCILIATION.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"OWNER_EVIDENCE_RECONCILIATION_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "SEGMENTS": [(s["ID"], s["PRINTED_M"], s["AUTHORED_SPAN_M"], s["DIMENSION_TEXT_CORRECTNESS"],
                          s["CAD_OBJECT_CORRESPONDENCE"]) for s in seg_rows],
            "HATCHES_PRESENT": {k: v["PRESENT"] for k, v in hatch.items()},
            "CHAINS": {k: v["CONTINUOUS"] for k, v in forward["CHAINS"].items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
