"""PA04 workstream F - structural beam / column exposure around the
reception from ST7757.pdf (beam labels on the GF-roof-slab plan p4 and the
two beam schedules p10 / p11, read visually on rendered pages; the PDF has
no text layer for these).  STRUCTURAL_EXISTENCE, EXPOSURE and
FINISH_FACE_OWNERSHIP are three separate facts.

    python3 -m research.qs_wall_treatment_01.pa04.structural
"""

from __future__ import annotations

from engine import self_checks as SC
from research.qs_wall_treatment_01.pa04 import common as C

# beam schedules (visual read of ST7757.pdf p10 'Schedule of Simple Beams' and p11 'Schedule of Continues Beams (2 span)'; cm)
SIMPLE = {"B1": (20, 40), "B2": (20, 40), "B3": (20, 40), "B4": (20, 50), "B5": (20, 50), "B6": (25, 50), "B7": (20, 75), "B8": (20, 75), "B9": (20, 75), "B10": (20, 75),
          "B11": (20, 75), "B12": (25, 75), "B13": (25, 75), "B14": (20, 75), "B15": (20, 120), "B16": (30, 75), "B17": (45, 75), "B18": (35, 75), "B19": (40, 75), "B20": (40, 75),
          "B21": (45, 75), "B22": (50, 75), "B23": (45, 75), "B24": (50, 75), "B25": (55, 75), "B26": (65, 85), "B27": (90, 85), "B28": (25, 75), "B29": (25, 75), "CA": (30, 50),
          "B.W": (20, 60), "SB1": (70, 50), "SB2": (100, 50), "SB3": (50, 40)}
CONTINUOUS = {"CB1": (35, 75, [7.5, 5.7]), "CB2": (20, 50, [4.0, 4.0]), "CB4": (20, 50, [3.3, 3.7]), "CB5": (20, 40, [2.5, 4.5]), "CB6": (20, 75, [4.4, 6.3]),
              "CB7": (20, 75, [6.0, 6.1]), "CB10": (25, 50, [3.0, 4.1]), "CB12": (25, 75, [6.1, 5.5]), "CB13": (30, 50, [3.7, 3.6])}
# p4 labels around the reception slab opening (visual read of the rendered p4 crop st_p4_reception_wide.png)
P4_LABELS = [
    {"LABEL": "CB6", "WHERE": "beam along the opening's north (+y) edge (the 1.8 pt line pair at y -799646 / -799447)", "ROLE": "edge beam under the FF gallery, spans 4.4 + 6.3", "CONFIDENCE": "MEDIUM"},
    {"LABEL": "CB5", "WHERE": "north-south beams east of the opening (x ~ -134800 pair and further north)", "ROLE": "beam beside the east strip, spans 2.5 + 4.5", "CONFIDENCE": "MEDIUM"},
    {"LABEL": "CB7", "WHERE": "beam along the NE wall line (y -803795) over the 800 and 600 columns", "ROLE": "beam over the D2 column line", "CONFIDENCE": "HIGH"},
    {"LABEL": "B1", "WHERE": "two short beams bounding the hatched panel B5 north and south; one runs north from the column line (x -134226, 2.4 m)", "ROLE": "beam north of the D2 column", "CONFIDENCE": "MEDIUM"},
    {"LABEL": "B4", "WHERE": "slab panel label west of the opening (GF roof slab panel between CB6 and CB7)", "ROLE": "slab panel, not a beam", "CONFIDENCE": "MEDIUM"},
    {"LABEL": "B5 / T 16", "WHERE": "hatched panel east of the opening with 'T 16' and 5o10/m, 6o10/m", "ROLE": "the flight-strip / landing panel (thickness 16); the hatched diagonal B27 crosses it", "CONFIDENCE": "MEDIUM"},
    {"LABEL": "B27", "WHERE": "inclined hatched band across the hatched panel", "ROLE": "stair flight beam / inclined slab (schedule 90 x 85)", "CONFIDENCE": "LOW"},
    {"LABEL": "P.C 20x70 10o16", "WHERE": "leader to the NE wall line beside the 800 column (D.C circle)", "ROLE": "beam / lintel 20 x 70 at the GF garden opening (RV-S-A), PROPOSED", "CONFIDENCE": "LOW"},
]


def beam(label):
    if label in CONTINUOUS:
        b, h, spans = CONTINUOUS[label]
        return {"B_CM": b, "D_CM": h, "SPANS_M": spans, "SCHEDULE": "p11 continuous"}
    if label in SIMPLE:
        b, h = SIMPLE[label]
        return {"B_CM": b, "D_CM": h, "SCHEDULE": "p10 simple"}
    return None


@C.timed("F_structural")
def run():
    col = C.read("COLUMN_VERTICAL_EXPOSURE_REGISTER.json", C.OUT)["COLUMNS"][0]
    rv = C.read("RECEPTION_VERTICAL_FACE_REGISTER.json", C.OUT)
    items = []
    def item(iid, obj, existence, exposure, ownership, **k):
        items.append(dict({"ITEM_ID": iid, "OBJECT": obj, "STRUCTURAL_EXISTENCE": existence, "EXPOSURE": exposure, "FINISH_FACE_OWNERSHIP": ownership,
                           "THREE_FACTS_SEPARATE": True, "PLASTER_GEOMETRY_AUTOMATIC": False}, **k))
    cb7 = beam("CB7")
    soffit7 = round(C.LEVELS["FF_SLAB"] - cb7["D_CM"] / 100, 2)
    item("F-CB7", "continuous beam CB7 along the NE wall line over the D2 column", {"STATUS": "ESTABLISHED", "SOURCE": "p4 label CB7 + p11 schedule", "SIZE": cb7},
         {"STATUS": "PROVISIONAL", "NOTE": "the beam sits inside the 200 wall line above the GF opening / wall; its soffit is the top of the column's room-side exposure only if no ceiling finish drops below it", "SOFFIT_LEVEL": soffit7},
         {"STATUS": "NOT_AUTOMATIC", "NOTE": "a beam inside a wall line owns no separate plaster face; where it spans the GF garden opening (RV-S-A) its soffit and inner face are candidate faces (lintel), not established"})
    b1 = beam("B1")
    item("F-B1", "simple beam B1 north from the column line (x -134226, 2.4 m)", {"STATUS": "ESTABLISHED", "SOURCE": "p4 label B1 + p10 schedule", "SIZE": b1},
         {"STATUS": "PROVISIONAL", "SOFFIT_LEVEL": round(C.LEVELS["FF_SLAB"] - b1["D_CM"] / 100, 2), "NOTE": "a downstand 0.40 under the FF slab between the reception and the saloon side"},
         {"STATUS": "NOT_AUTOMATIC", "NOTE": "its two side faces (2.4 x 0.40 - slab) and soffit (2.4 x 0.20) are candidate ceiling-trade / plaster faces, not established"})
    cb6 = beam("CB6")
    item("F-CB6", "continuous beam CB6 along the opening's north edge", {"STATUS": "ESTABLISHED_PROVISIONAL", "SOURCE": "p4 label CB6 (label-to-line correspondence MEDIUM) + p11", "SIZE": cb6},
         {"STATUS": "PROVISIONAL", "SOFFIT_LEVEL": round(C.LEVELS["FF_SLAB"] - cb6["D_CM"] / 100, 2), "NOTE": "a 0.75 downstand along the opening's north edge: its opening-side face (5.87 x ~0.59 below the slab) is an exposed beam face in the double-height volume"},
         {"STATUS": "NOT_AUTOMATIC", "NOTE": "candidate plaster face RVF-N-BEAM (length 5.87, height 0.59 PROVISIONAL); trade eligibility not decided"})
    cb5 = beam("CB5")
    item("F-CB5", "continuous beam CB5 east of the opening", {"STATUS": "ESTABLISHED_PROVISIONAL", "SOURCE": "p4 label CB5 + p11", "SIZE": cb5},
         {"STATUS": "PROVISIONAL", "SOFFIT_LEVEL": round(C.LEVELS["FF_SLAB"] - cb5["D_CM"] / 100, 2)}, {"STATUS": "NOT_AUTOMATIC", "NOTE": "0.40 downstand beside the east strip; face not established"})
    pc = {"B_CM": 20, "D_CM": 70}
    item("F-PC-20x70", "P.C 20 x 70 at the NE wall line beside the 800 column", {"STATUS": "PROVISIONAL", "SOURCE": "p4 leader label (LOW confidence correspondence)", "SIZE": pc},
         {"STATUS": "PROVISIONAL", "SOFFIT_LEVEL": round(C.LEVELS["FF_SLAB"] - 0.70, 2), "NOTE": "if this is the lintel over the 3.82 m GF garden opening, the FF wall face RVF-S-A-FF starts at +4.80"},
         {"STATUS": "NOT_AUTOMATIC", "NOTE": "lintel inner face 3.82 x 0.70 would be a plaster face candidate; not established"})
    b27 = beam("B27")
    item("F-B27", "inclined element B27 across the hatched panel (stair)", {"STATUS": "ESTABLISHED_PROVISIONAL", "SOURCE": "p4 label B27 + p10 (90 x 85)", "SIZE": b27},
         {"STATUS": "UNKNOWN", "NOTE": "a stair flight beam; its soffit is the flight soffit seen from the reception"}, {"STATUS": "NOT_AUTOMATIC", "NOTE": "stair soffit belongs to the stair register"})
    item("F-SLAB-B5", "hatched slab panel B5 'T 16' east of the opening", {"STATUS": "ESTABLISHED", "SOURCE": "p4 hatch + label"}, {"STATUS": "PROVISIONAL", "NOTE": "landing / flight strip panel 160 thick"},
         {"STATUS": "NOT_AUTOMATIC", "NOTE": "soffit belongs to the ceiling / stair registers"})
    # D2 column vertical exposure with the beam
    girth = col["COLUMN_EXPOSED_GIRTH_LM"]
    h = round(soffit7 - C.LEVELS["GF_FFL"], 2)
    d2 = {"COLUMN_ID": "LOOP-059 (D2)", "STRUCTURAL_EXISTENCE": "ESTABLISHED (unchanged)", "COLUMN_EXPOSED_GIRTH_LM": girth,
          "COLUMN_EXPOSED_HEIGHT_M": {"VALUE": h, "STATE": "PROVISIONAL", "BASIS": f"GF FFL +1.00 to the CB7 soffit +{soffit7} (20 x 75 beam over the column line, FF slab top at +5.50 assumed = beam top)",
                                      "ALTERNATIVES": {"to_B1_soffit": round(C.LEVELS["FF_SLAB"] - b1["D_CM"] / 100 - C.LEVELS["GF_FFL"], 2), "to_slab_soffit_T16": round(C.LEVELS["FF_SLAB"] - 0.16 - C.LEVELS["GF_FFL"], 2)}, "SELECTED": "CB7 soffit (PROVISIONAL); alternatives kept"},
          "COLUMN_BONDING_AREA_M2": {"VALUE": round(girth["VALUE"] * h, 4), "STATE": "PROVISIONAL_QUANTITY", "BASIS": f"{girth['VALUE']} x {h}"},
          "OWNER_PARAMETRIC_AREA_M2": col["OWNER_PARAMETRIC_AREA_M2"], "FINISH_FACE_OWNERSHIP": "the column's room-side faces are plaster candidates (COLUMN_BONDING then plaster); the beam above is not part of the column face",
          "SUPERSEDES": "PA03 COLUMN_EXPOSED_HEIGHT_M NOT_ESTABLISHED -> PROVISIONAL from the beam schedule"}
    # overhanging FF faces on the opening edges
    over = [
        {"FACE_ID": "RVF-W-FF", "EDGE": "RV-W", "SUPPORT_BEAM": "not identified on p4 (no label read at x -141245; the small X at the SW corner is a separate opening)", "BOTTOM_LEVEL": None, "STATUS": "NOT_ESTABLISHED"},
        {"FACE_ID": "RVF-S-A-FF", "EDGE": "RV-S-A", "SUPPORT_BEAM": "P.C 20 x 70 (PROPOSED)", "BOTTOM_LEVEL": 4.80, "HEIGHT_TO_9_54": round(9.54 - 4.80, 2), "STATUS": "PROVISIONAL (label correspondence LOW)"},
        {"FACE_ID": "RVF-N-BEAM", "EDGE": "RV-N", "SUPPORT_BEAM": "CB6 20 x 75", "BOTTOM_LEVEL": round(C.LEVELS["FF_SLAB"] - 0.75, 2), "HEIGHT_BELOW_SLAB": 0.75, "STATUS": "PROVISIONAL (new candidate face: exposed beam side in the double-height volume)"},
        {"FACE_ID": "RVF-E-BEAM", "EDGE": "RV-E", "SUPPORT_BEAM": "CB5 20 x 40 (beside the east strip, not on the edge)", "BOTTOM_LEVEL": 5.10, "STATUS": "PROVISIONAL"},
    ]
    lines = [{"ID": i["ITEM_ID"], "SOURCE": i["STRUCTURAL_EXISTENCE"]["SOURCE"], "SOURCE_ENTITY_IDS": ["ST7757.pdf p4 / p10 / p11 visual read"]} for i in items]
    checks = SC.run_all({"ITEMS": items, "D2": d2}, lines)
    C.METRICS.setdefault("F_structural", {}).update({"AI_CALLS": 0, "AI_CALLS_NOTE": "orchestrator visual reads of 3 rendered pages (no cold challenge: schedule tables are low-ambiguity)", "DETERMINISTIC_OPS": len(items)})
    C.write("STRUCTURAL_EXPOSURE_REGISTER.json", {"ARTIFACT": "STRUCTURAL_EXPOSURE_REGISTER", "WORKSTREAM": "F", "SCHEDULES": {"SIMPLE": SIMPLE, "CONTINUOUS": CONTINUOUS, "SOURCE": "ST7757.pdf p10 / p11 visual read (no text layer)"},
                                                   "P4_LABELS": P4_LABELS, "ITEMS": items, "D2_COLUMN": d2, "OVERHANGING_FF_FACES": over, "SLAB_INTERRUPTIONS": ["B5 / T16 panel east of the opening (landing / flight strip)", "the opening itself (p4 X)"],
                                                   "SELF_CHECKS": checks})
    return {"D2_HEIGHT": d2["COLUMN_EXPOSED_HEIGHT_M"]["VALUE"], "D2_AREA": d2["COLUMN_BONDING_AREA_M2"]["VALUE"], "OVER": [(o["FACE_ID"], o["BOTTOM_LEVEL"], o["STATUS"]) for o in over], "CHECKS": checks["FAILED"]}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
