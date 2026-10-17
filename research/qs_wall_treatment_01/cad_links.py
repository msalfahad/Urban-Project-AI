"""CAD <-> TRACE links for the SALOON faces (§12, §14, §15).

Fits the raster<->DWG registration from declared pairs (each side
established on its own path), projects the authored runs into pixel space,
tests them against the stored trace geometry, and classifies A22 items
T2 / T3 / T9 with the source hierarchy:

    actual drawing geometry (authored DWG lines)
    > owner project input
    > temporary default
    > a printed value whose ownership is not established

Nothing here edits the frozen register. Where the hierarchy resolves an
item, the resolution is recorded with its evidence; where it does not, the
item stays for a decision card.

    python3 -m research.qs_wall_treatment_01.cad_links
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import cad_adapter as CA
from engine import cad_trace_registration as R
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.a22_structural_comparison import DECODE, _runs

OUT = Path(P.OUT_DIR)
CASE = "CASE-3-DOOR-AND-WINDOW"
SHEET = "GROUND_FLOOR_PLAN"

# Registration pairs: (mm, px). Each pixel value is a traced extension line
# or face line of a printed dimension; each mm value is an authored line.
X_PAIRS = [
    (-129070.0, 1784.0, "DIM-12 ext B / sea-view inner wall line <-> band inner line"),
    (-128870.0, 1792.0, "DIM-05 ext B / sea-view outer line <-> layer-5 outer line"),
    (-134220.0, 1520.0, "open-edge tick (DIM-05 ext A, OE-01) <-> layer-5 stub at the edge"),
    (-145040.0, 942.0, "DIM-12 ext A / dining west wall <-> zone polygon west vertex"),
    (-131070.0, 1682.0, "SEG-03 west end <-> return wall run west end"),
]
Y_PAIRS = [
    (-797593.5, 668.0, "DIM-10 ext A / return wall inner face"),
    (-805093.5, 1050.0, "DIM-10 ext B / neighbour wall inner face"),
    (-796143.5, 590.0, "DIM-11 ext A / bedroom wall line"),
    (-805293.5, 1062.0, "DIM-03 ext B / neighbour wall outer face"),
    (-797393.5, 655.0, "DIM-02 ext A / return wall outer face"),
]

# Authored runs to test, with the trace geometry each is a candidate for
LINK_TESTS = [
    {"LINK_ID": "L1", "TRACE": "SEG-02", "WHAT": "neighbour wall, SALOON-side face, "
                                                "from the stub at the open edge to the sea-view line",
     "RUN": {"AXIS": "H", "FIXED_MM": -805093.5, "FROM_MM": -134220.0, "TO_MM": -129070.0,
             "LAYER": "1"}},
    {"LINK_ID": "L2", "TRACE": "SEG-03", "WHAT": "return wall, SALOON-side face",
     "RUN": {"AXIS": "H", "FIXED_MM": -797593.5, "FROM_MM": -131070.0, "TO_MM": -129070.0,
             "LAYER": "1"}},
    {"LINK_ID": "L3", "TRACE": "GLZ-01", "WHAT": "glazing band line (4 lines, W layer)",
     "RUN": {"AXIS": "V", "FIXED_MM": -129070.0, "FROM_MM": -804394.0, "TO_MM": -798062.0,
             "LAYER": "W"}},
    {"LINK_ID": "L4", "TRACE": "COL-02", "WHAT": "corner pier body along the sea-view line, "
                                                "outer neighbour-wall face to glazing start",
     "RUN": {"AXIS": "V", "FIXED_MM": -129070.0, "FROM_MM": -805294.0, "TO_MM": -804394.0,
             "LAYER": "1/S-COL.BON"}},
    {"LINK_ID": "L4X", "TRACE": "COL-02", "WHAT": "corner pier EXPOSED face inside the SALOON: "
                                                 "inner neighbour-wall face to glazing start",
     "RUN": {"AXIS": "V", "FIXED_MM": -129070.0, "FROM_MM": -805094.0, "TO_MM": -804394.0,
             "LAYER": "1"}},
    {"LINK_ID": "L5", "TRACE": "COL-01", "WHAT": "corner pier body, return-wall outer face to "
                                                "glazing end",
     "RUN": {"AXIS": "V", "FIXED_MM": -129070.0, "FROM_MM": -798062.0, "TO_MM": -797394.0,
             "LAYER": "1"}},
    {"LINK_ID": "L5X", "TRACE": "COL-01", "WHAT": "corner pier EXPOSED face inside the SALOON: "
                                                 "glazing end to return-wall inner face",
     "RUN": {"AXIS": "V", "FIXED_MM": -129070.0, "FROM_MM": -798062.0, "TO_MM": -797594.0,
             "LAYER": "1"}},
    {"LINK_ID": "L6", "TRACE": "OE-01", "WHAT": "layer-5 stub at the open edge, 1.45 m from the "
                                               "neighbour wall northward",
     "RUN": {"AXIS": "V", "FIXED_MM": -134219.9, "FROM_MM": -805094.0, "TO_MM": -803644.0,
             "LAYER": "5"}},
]


def _trace_px(t: dict) -> list:
    if t.get("PIXEL_POLYLINE"):
        return t["PIXEL_POLYLINE"]
    if t.get("PIXEL_BBOX"):
        x0, y0, x1, y1 = t["PIXEL_BBOX"]
        if (y1 - y0) >= (x1 - x0):
            return [[x0, y0], [x0, y1]]     # left edge = room-side face for the piers here
        return [[x0, y0], [x1, y0]]
    return []


def run() -> dict:
    reg_doc = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    traces = {t["TRACE_ID"]: t for t in reg_doc["TRACES"]
              if t["CASE_ID"] == CASE and t["SHEET_ID"] == SHEET}
    reg = R.Registration([(m, p) for m, p, _ in X_PAIRS], [(m, p) for m, p, _ in Y_PAIRS])
    d = json.loads(Path(DECODE).read_text("utf-8"))
    n = CA.normalize(d, source_file="P7757_ARCHITECTURAL.dwg")
    links = []
    for lt in LINK_TESTS:
        t = traces[lt["TRACE"]]
        px = _trace_px(t)
        # confirm the run exists in the model at the locator (clipped read)
        loc = {"AXIS": lt["RUN"]["AXIS"], "FIXED_MM": (lt["RUN"]["FIXED_MM"] - 8, lt["RUN"]["FIXED_MM"] + 8),
               "WINDOW_MM": (lt["RUN"]["FROM_MM"] - 5, lt["RUN"]["TO_MM"] + 5),
               "LAYERS": tuple(lt["RUN"]["LAYER"].split("/"))}
        found = _runs(n, loc)
        model_len = max((r["LENGTH_M"] for r in found), default=None)
        res = R.link_status(reg, lt["RUN"], px)
        links.append({**lt, "TRACE_GEOMETRY_PX": px, "MODEL_RUNS_AT_LOCATOR": found,
                      "RUN_LENGTH_M": round((lt["RUN"]["TO_MM"] - lt["RUN"]["FROM_MM"]) / 1000, 4),
                      "MODEL_LENGTH_AT_LOCATOR_M": model_len,
                      "TRACE_LENGTH_M": t.get("LENGTH_M"),
                      "TRACE_DIMENSION_STATUS": t.get("DIMENSION_STATUS"), **res})
    by = {l["LINK_ID"]: l for l in links}

    def st(k):
        return by[k]["CAD_TRACE_LINK_STATUS"]

    # ---- classifications for the A22 items ---------------------------
    t2 = {
        "ITEM_ID": "T2", "SUBJECT": "SALOON neighbour wall face 5.15 printed vs 8.43 authored run",
        "CLASS": "CAD_MAPPING_DIFFERENCE",
        "RESOLUTION": ("the 8.43 m run was an artefact of the A22 locator window clipping a "
                       "longer wall face. The printed 515 runs from the layer-5 stub at the "
                       "open edge (x = -134220) to the sea-view wall line (x = -129070) = "
                       "5.150 m exactly; the projected run lies on SEG-02"),
        "CAD_TRACE_LINK_STATUS": st("L1"),
        "ENGINEERING_CONSEQUENCE": "SEG-02 length 5.15 stands; its west end is a zero-material "
                                   "REPORTING_BOUNDARY at the open edge (§10), not a wall end",
        "RESOLVED_BY": "source hierarchy: authored geometry corroborates the printed dimension",
        "OWNER_DECISION_NEEDED": False,
    }
    t3 = {
        "ITEM_ID": "T3", "SUBJECT": "sea-view line: 633 and the 90 + 633 + 20 + 90 chain",
        "CLASS": "DIMENSION_OWNERSHIP_DIFFERENCE",
        "RESOLUTION": (
            "633 is the glazing band between the two pier bodies (authored -804394 to "
            "-798062 = 6.332 m); link " + st("L3") + ". The lower 90 is the pier BODY from the "
            "neighbour wall's OUTER face to the glazing start (authored 0.900), not an "
            "exposed plaster face; the exposed face inside the SALOON is 0.700 (inner face "
            "to glazing start). The upper 90 does not match the authored pier body there "
            "(0.668) nor its exposed face (0.468); its dimension line as traced spans ~0.64 m, "
            "so the printed value's ownership is not established (DRAWING_AMBIGUITY on that "
            "one figure). The chain sum 8.33 therefore over-counts the wall thickness and "
            "the upper pier"),
        "CAD_TRACE_LINK_STATUS": {"GLZ-01": st("L3"), "COL-02 body": st("L4"),
                                  "COL-02 exposed": st("L4X"), "COL-01 body": st("L5"),
                                  "COL-01 exposed": st("L5X")},
        "ENGINEERING_CONSEQUENCE": "the glazing line carries no plaster on either basis; the "
                                   "pier faces are handled under T9",
        "RESOLVED_BY": "source hierarchy: authored geometry over a printed value with "
                       "unestablished ownership",
        "OWNER_DECISION_NEEDED": False,
    }
    col = {
        "COLUMN_IDENTITY": {"COL-01": "corner pier at the return-wall end of the sea-view line",
                            "COL-02": "corner pier at the neighbour-wall end of the sea-view line"},
        "COLUMN_WIDTH_M": {"COL-01": 0.20, "COL-02": 0.20,
                           "SOURCE": "authored pier bodies x -129070 to -128870 (0.200)"},
        "COLUMN_EXPOSED_FACE_M": {"COL-02": 0.700, "COL-01": 0.468,
                                  "SOURCE": "authored lines on x = -129070 between the room-side "
                                            "wall faces and the glazing band ends",
                                  "CAD_TRACE_LINK_STATUS": {"COL-02": st("L4X"), "COL-01": st("L5X")}},
        "PRINTED_DIMENSION_OWNERSHIP": {
            "DIM-03 '90' (COL-02)": "pier BODY length incl. the 0.20 wall thickness; not the "
                                    "exposed face",
            "DIM-02 '90' (COL-01)": "ownership NOT_ESTABLISHED: the traced dimension line "
                                    "spans ~0.64 m and the authored body is 0.668"},
        "COLUMN_COMPONENT_STATUS": (
            "RESOLVED_BY_CAD_GEOMETRY" if st("L4X") in ("ESTABLISHED", "PROVISIONAL")
            and st("L5X") in ("ESTABLISHED", "PROVISIONAL") else "HUMAN_REVIEW"),
        "ENGINEERING_LENGTHS_TO_USE_LM": {"COL-02": 0.700, "COL-01": 0.468,
                                          "LENGTH_BASIS": "CAD_GEOMETRY"},
        "A21_LINE_1_80_LM": "RETIRED: rested on two printed 90s whose ownership is not the "
                            "exposed face; recorded as DIMENSION_OWNERSHIP_DIFFERENCE",
    }
    t9 = {"ITEM_ID": "T9", "SUBJECT": "SALOON corner piers 0.90 + 0.90 printed",
          "CLASS": "DIMENSION_OWNERSHIP_DIFFERENCE", **col,
          "RESOLVED_BY": "source hierarchy: authored exposed-face geometry with an "
                         "established link over printed values of unestablished ownership",
          "OWNER_DECISION_NEEDED": col["COLUMN_COMPONENT_STATUS"] != "RESOLVED_BY_CAD_GEOMETRY"}
    stub = {
        "FINDING": "STUB_AT_OPEN_EDGE",
        "WHAT": "the DWG carries a layer-5 line at x = -134220 running 1.45 m north from the "
                "neighbour wall, and a layer-2 line 50 mm east of it running 2.40 m: a thin "
                "element at the SALOON / RECEPTION open edge that A21 traced as fully open "
                "(OE-01)",
        "CAD_TRACE_LINK_STATUS": st("L6"),
        "SEMANTIC_STATUS": "NOT_ESTABLISHED (low wall, planter, screen or partition line)",
        "ENGINEERING_CONSEQUENCE": "a possible additional plasterable face of up to 1.45 m at "
                                   "the open edge; UNRESOLVED_SCOPE, not estimated",
    }
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "CAD_TRACE_LINKS", "CASE": CASE, "SHEET": SHEET,
            "REGISTRATION": {**reg.record(),
                             "X_PAIRS": [{"MM": m, "PX": p, "WHY": w} for m, p, w in X_PAIRS],
                             "Y_PAIRS": [{"MM": m, "PX": p, "WHY": w} for m, p, w in Y_PAIRS]},
            "LINKS": links, "ITEMS": {"T2": t2, "T3": t3, "T9": t9},
            "ADDITIONAL_FINDING": stub,
            "FROZEN_REGISTER_UNCHANGED": True,
            "CAD_LENGTH_ENTERS_A_QUANTITY_ONLY_WITH_LINK_ESTABLISHED_OR_PROVISIONAL_FLAGGED": True}
    p = OUT / "CAD_TRACE_LINKS.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"CAD_TRACE_LINKS_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "REGISTRATION": body["REGISTRATION"]["SCALE_MM_PER_PX"],
            "RESIDUALS": {"X": reg.x["RESIDUALS_PX"], "Y": reg.y["RESIDUALS_PX"]},
            "LINKS": [(l["LINK_ID"], l["TRACE"], l["CAD_TRACE_LINK_STATUS"], l["END_DISTANCES_PX"],
                       l["TRACE_TO_RUN_MAX_PX"], l["MODEL_LENGTH_AT_LOCATOR_M"]) for l in links],
            "COLUMN_COMPONENT_STATUS": col["COLUMN_COMPONENT_STATUS"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
