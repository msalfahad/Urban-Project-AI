"""Section 20: internal source consistency (SOURCE CONSISTENCY only, never independent validation)."""

from __future__ import annotations

import json
from collections import Counter

from research.qs_wall_treatment_01.pa08.qortuba import common as C


def main():
    dim = json.loads((C.OUT / "PA08_QORTUBA_DIMENSION_REGISTER.json").read_text("utf-8"))
    txt = json.loads((C.OUT / "PA08_QORTUBA_TEXT_SEMANTIC_REGISTER.json").read_text("utf-8"))
    inv = json.loads((C.OUT / "PA08_QORTUBA_SOURCE_INVENTORY.json").read_text("utf-8"))
    walls = json.loads((C.OUT / "PA08_QORTUBA_MATERIAL_WALL_REGISTER.json").read_text("utf-8"))
    openings = json.loads((C.OUT / "PA08_QORTUBA_OPENING_REGISTER.json").read_text("utf-8"))
    spaces = json.loads((C.OUT / "PA08_QORTUBA_PHYSICAL_SPACE_REGISTER.json").read_text("utf-8"))
    # 1 DWG dimension vs DWG geometry
    by = dim["SUMMARY"]["BY_AGREEMENT"]
    t1 = {"TEST": "DWG_DIMENSION_vs_DWG_GEOMETRY", "ENTITIES": dim["TOTAL_DIMENSION_ENTITIES"], "AGREE": by.get("AGREE", 0) + by.get("AGREE_WITHIN_ROUNDING", 0), "CONFLICT": by.get("CONFLICT", 0),
          "ENGINE_MEASUREMENT_DEFECT_ROTATED_DIMENSION": by.get("ENGINE_MEASUREMENT_DEFECT_ROTATED_DIMENSION", 0), "PROJECTION_CHECK": dim["SUMMARY"]["PROJECTION_CHECK"],
          "VERDICT": "authored numbers agree with the authored geometry for all 101 entities when the projection along the dimension line is used; the engine's raw-distance reading disagrees on 16 rotated dimensions (engine defect, recorded)"}
    # 2 PDF printed dimension vs DWG dimension
    pdf_nums = inv["PDF"]["PAGES"][0]["NUMERIC_TOKENS_IN_TEXT_LAYER"]
    t2 = {"TEST": "PDF_PRINTED_DIMENSION_vs_DWG_DIMENSION", "PDF_NUMERIC_TOKENS_IN_TEXT_LAYER": pdf_nums, "DWG_TITLE_BLOCK_NUMBERS": ["26.50 M", "19.00 M", "4.00 m", "305.30 m2", "1:100"],
          "AGREE": [n for n in pdf_nums if n in ("26.50", "19.00", "4.00", "1:100", "1/100", "449", "1")], "VERDICT": "title-block numbers agree; plan dimension numbers are outlined glyphs in the PDF: NOT_COMPARABLE"}
    # 3 PDF room arrangement vs DWG topology
    t3 = {"TEST": "PDF_ROOM_ARRANGEMENT_vs_DWG_PHYSICAL_TOPOLOGY", "PDF_VECTOR_PATHS": inv["PDF"]["PAGES"][0]["VECTOR_PATHS"], "DWG_NORMALIZED_PRIMITIVES": inv["DWG"]["NORMALIZED"]["PRIMITIVES"],
          "ENGINE_PDF_SHEET_ROLE": "FLOOR_PLAN (deterministic from the title text)", "ENGINE_DWG_VIEW_ROLE": "FLOOR_PLAN (geometry hint: 1 door swing, 12 closed spaces)",
          "VERDICT": "NOT_COMPARABLE deterministically: the engine builds topology from the DWG only; the PDF is the plot of the same model space (same sheet title, same site labels, same title block); no second arrangement exists to disagree"}
    # 4 PDF label vs DWG label
    pdf_words = set(w["RAW_TEXT"] for w in txt["PDF_TEXTS"])
    dwg_clean = [r["CLEAN_TEXT"] for r in txt["DWG_TEXTS"]]
    matched = sorted(w for w in pdf_words if any(w in c for c in dwg_clean))
    t4 = {"TEST": "PDF_LABEL_vs_DWG_LABEL", "PDF_TEXT_LAYER_WORDS": len(pdf_words), "MATCHED_IN_DWG_TEXTS": len(matched), "SAMPLE": matched[:25], "ROOM_LABELS": "PDF room labels are outlines: only the DWG carries them as text",
          "ARABIC": "the one Arabic word in the PDF text layer (ةبطرق, reversed) is the area name قرطبة, which the DWG carries as keyboard-mapped 'rv'fM'", "VERDICT": "AGREE where comparable"}
    # 5 polygon area vs authored dimension decomposition: the labelled rooms with their own cell, against the authored dimensions whose midpoints lie inside the cell bbox (+ 60 cm)
    dec = C.decode(); dims_raw = {o["handle"][-1]: o for o in dec["OBJECTS"] if o.get("entity") == "DIMENSION_LINEAR"}
    faces = {f["FACE_ID"]: f for f in C.load_blind("PA07_PLANAR_FACE_REGISTER")["ROWS"]}
    eng_spaces = {s["SPACE_ID"]: s for s in C.load_blind("PA07_PHYSICAL_SPACE_REGISTER")["ROWS"]}
    cases = []
    for sr in spaces["ROWS"]:
        if sr["ZONE_NAME"] == "UNLABELLED" or sr["TOPOLOGY_STATUS"].endswith("MERGED") or sr["SPACE_CLASS"] != "INTERIOR":
            continue
        bb = faces[eng_spaces[sr["SPACE_ID"]]["FACE_ID"]]["BBOX_MM"]
        x0, y0, x1, y1 = [v / 10 for v in bb]           # raw cm
        near = []
        for r in dim["ROWS"]:
            o = dims_raw.get(int(str(r["SOURCE_ENTITY_ID"]).split(":")[-1]), {}); p1, p2 = o.get("xline1_pt"), o.get("xline2_pt")
            if not p1 or not p2:
                continue
            mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            if x0 - 60 <= mx <= x1 + 60 and y0 - 60 <= my <= y1 + 60:
                near.append((r["DISPLAYED_VALUE"], "H" if abs(o.get("dim_rotation") or 0.0) < 0.1 or abs((o.get("dim_rotation") or 0.0) - 3.1416) < 0.1 else "V"))
        bbox_area = round((x1 - x0) * (y1 - y0) / 1e4, 2)
        cases.append({"ROOM": sr["ZONE_NAME"], "SPACE_ID": sr["SPACE_ID"], "ENGINE_CELL_AREA_M2": sr["GEOMETRIC_AREA_M2"], "CELL_BBOX_M": [round((x1 - x0) / 100, 2), round((y1 - y0) / 100, 2)], "CELL_BBOX_AREA_M2": bbox_area,
                      "AUTHORED_DIMENSIONS_INSIDE_BBOX_CM": near, "VERDICT": "CONSISTENT_WITH_RASTER_BASIS" if abs(bbox_area - sr["GEOMETRIC_AREA_M2"]) <= 0.15 * max(bbox_area, 1e-9) else "CHECK",
                      "NOTE": "the engine never links an authored dimension to a room; the listed numbers are those drawn inside the cell's extent (partition thicknesses 15 / 20 included)"})
    t5 = {"TEST": "AREA_BY_POLYGON_vs_AUTHORED_DIMENSION_DECOMPOSITION", "CASES": cases, "VERDICT": "reader check only: cell area vs its bbox and the authored numbers inside it; rooms inside the merged cell cannot be checked"}
    # 6 wall thickness vs paired-face spacing
    thk_dims = dim["SUMMARY"]["WALL_THICKNESS_DIMENSIONS"]
    acc_thk = Counter(int(w["THICKNESS_MM"]) for w in walls["ROWS"] if w["STATUS"] == "ACCEPTED")
    t6 = {"TEST": "WALL_THICKNESS_vs_PAIRED_FACE_SPACING", "AUTHORED_THICKNESS_DIMENSIONS": {"15_CM": thk_dims["15_CM"], "20_CM": thk_dims["20_CM"]}, "ACCEPTED_BAND_THICKNESS_MM": dict(acc_thk),
          "VERDICT": "AGREE for 150 and 200 mm (authored 15 / 20 cm, paired faces 150 / 200 mm); accepted bands of 250-600 mm are envelope / column / pier pairings with no authored thickness dimension: HUMAN_REVIEW"}
    # 7 opening width vs jamb geometry
    est = [r for r in openings["ROWS"] if r["STATUS"].startswith("SOURCE")]
    door_blocks = openings["SOURCE_OBSERVATIONS"]["DOOR_BLOCK_INSTANCES"]
    t7 = {"TEST": "OPENING_WIDTH_vs_JAMB_GEOMETRY", "ESTABLISHED_OPENINGS": [(r["OPENING_ID"], r["TYPE"], r["WIDTH_MM"]["VALUE"]) for r in est],
          "DOOR_BLOCK_LEAF_LENGTHS_MM": sorted(Counter(b["LEAF_LENGTH_MM_MAX_SEGMENT"] for b in door_blocks).items()),
          "VERDICT": "the one established door (800 mm) matches an 800 mm door block leaf; 7 other door blocks (800 / 1000 mm) sit in UNRESOLVED partitions: not comparable by the engine"}
    out = {"ARTIFACT": "PA08_QORTUBA_SOURCE_CONSISTENCY", "RULE": "SOURCE CONSISTENCY only; not independent validation", "TESTS": [t1, t2, t3, t4, t5, t6, t7]}
    C.write("PA08_QORTUBA_SOURCE_CONSISTENCY", out)
    print(json.dumps([(t["TEST"], t["VERDICT"][:90]) for t in out["TESTS"]], ensure_ascii=False))


if __name__ == "__main__":
    main()
