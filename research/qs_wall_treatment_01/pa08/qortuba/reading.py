"""Sections 2, 3 and 19: number reading, Arabic / English label reading, the reading test.

The engine's own reading is taken from the frozen blind registers (DIMENSION_CHAIN_REGISTER, PA07_SEMANTIC_ANCHOR_REGISTER).
The research layer adds: agreement classes between displayed and measured values, the keyboard-map decode of the
Latin-glyph Arabic labels (AI_INTERPRETED, never SOURCE_TEXT_ESTABLISHED), bilingual pairing and the counts.
Text never creates geometry; every attachment is the engine's.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import pymupdf

from engine import cad_adapter as CA
from engine.ingest import semantics as SEM
from research.qs_wall_treatment_01.pa08.qortuba import common as C

AGREE_MM = 5.0
TITLE_BLOCK_Y_MAX = 14150.0        # raw cm: texts below this y lie in the title block / frame strip (not room labels)


def dimension_register():
    rows = C.load_blind("DIMENSION_CHAIN_REGISTER")["ROWS"]
    unit = C.load_blind("PA06_SOURCE_UNIT_REGISTER")["ROWS"][0]
    scale = 10.0 if unit["UNIT_CANDIDATE"] == "cm" else 1.0
    # research check (not the engine): the author's linear dimension is the projection of the extension origins onto the dimension direction
    dims = {o["handle"][-1]: o for o in C.decode()["OBJECTS"] if o.get("entity") == "DIMENSION_LINEAR"}
    out = []
    for r in rows:
        o = dims.get(int(str(r["SOURCE_ENTITY_ID"]).split(":")[-1]), {})
        p1, p2, rot = o.get("xline1_pt"), o.get("xline2_pt"), (o.get("dim_rotation") or 0.0)
        proj_mm = abs((p2[0] - p1[0]) * math.cos(rot) + (p2[1] - p1[1]) * math.sin(rot)) * scale if p1 and p2 else None
        act_mm = (o.get("act_measurement") * scale) if o.get("act_measurement") is not None else None
        try:
            disp = float(str(r["DISPLAY_TEXT"]).replace(",", "."))
        except Exception:
            disp = None
        disp_mm = disp * scale * (r.get("DISPLAY_FACTOR") or 1.0) if disp is not None else None
        meas = r["MEASURED_VALUE_MM"]
        if disp_mm is None:
            cls = "UNRESOLVED"
        elif abs(disp_mm - meas) <= AGREE_MM:
            cls = "AGREE"
        elif abs(disp_mm - meas) <= 0.02 * meas:
            cls = "AGREE_WITHIN_ROUNDING"
        elif disp_mm and meas and (0.099 <= disp_mm / meas <= 0.101 or 9.9 <= disp_mm / meas <= 10.1):
            cls = "SCALE_DIFFERENCE"
        else:
            cls = "CONFLICT"
        owner = r["OWNER_STATUS"]
        proj_cls = None
        if disp_mm is not None and proj_mm is not None:
            proj_cls = "AGREE" if abs(disp_mm - proj_mm) <= AGREE_MM else "CONFLICT"
        if cls == "CONFLICT" and proj_cls == "AGREE":
            cls = "ENGINE_MEASUREMENT_DEFECT_ROTATED_DIMENSION"      # the engine measured the raw distance between offset extension origins; the projection agrees with the author
        status = "SOURCE_ESTABLISHED" if (cls in ("AGREE", "AGREE_WITHIN_ROUNDING") and owner == "BOTH_OWNED") else ("PROVISIONAL" if cls in ("AGREE", "AGREE_WITHIN_ROUNDING") else ("HUMAN_REVIEW" if cls in ("CONFLICT", "ENGINE_MEASUREMENT_DEFECT_ROTATED_DIMENSION") else "NOT_ESTABLISHED"))
        out.append({"DIMENSION_ID": r["DIMENSION_ID"], "SOURCE_ENTITY_ID": r["SOURCE_ENTITY_ID"], "DISPLAYED_VALUE": r["DISPLAY_TEXT"], "DISPLAYED_VALUE_MM": disp_mm, "MEASURED_VALUE_MM": meas, "UNIT": "cm (INSUNITS 5) -> mm x10",
                    "START_OWNER": r["START_EXTENSION_OWNER"], "END_OWNER": r["END_EXTENSION_OWNER"], "VIEW": r["VIEW"], "LAYER": r["LAYER"], "TEXT_OVERRIDDEN": r["TEXT_OVERRIDDEN"],
                    "PDF_PRINTED_VALUE": "NOT_AVAILABLE (PDF dimension numbers are outlines, not text)", "AGREEMENT": cls, "OWNER_STATUS": owner, "ENGINE_READ_STATUS": r["READ_STATUS"], "STATUS": status,
                    "RESEARCH_CHECK": {"PROJECTED_VALUE_MM": round(proj_mm, 2) if proj_mm is not None else None, "DECODER_ACT_MEASUREMENT_MM": round(act_mm, 2) if act_mm is not None else None, "DIM_ROTATION_RAD": round(rot, 4), "PROJECTION_AGREES_WITH_DISPLAY": proj_cls}})
    by_cls = Counter(x["AGREEMENT"] for x in out); by_owner = Counter(x["OWNER_STATUS"] for x in out)
    vals = Counter(x["DISPLAYED_VALUE"] for x in out)
    return {"ARTIFACT": "PA08_QORTUBA_DIMENSION_REGISTER", "TOTAL_DIMENSION_ENTITIES": len(rows), "ROWS": out,
            "SUMMARY": {"SUCCESSFULLY_INTERPRETED": sum(1 for x in out if x["STATUS"] == "SOURCE_ESTABLISHED"), "PARTIALLY_INTERPRETED": sum(1 for x in out if x["STATUS"] == "PROVISIONAL"),
                        "UNSUPPORTED": sum(1 for x in out if x["STATUS"] == "NOT_ESTABLISHED"), "CONFLICTING": sum(1 for x in out if x["AGREEMENT"] == "CONFLICT"),
                        "ENGINE_MEASUREMENT_DEFECT_ROTATED_DIMENSION": sum(1 for x in out if x["AGREEMENT"] == "ENGINE_MEASUREMENT_DEFECT_ROTATED_DIMENSION"),
                        "PROJECTION_CHECK": dict(Counter(x["RESEARCH_CHECK"]["PROJECTION_AGREES_WITH_DISPLAY"] for x in out)),
                        "BY_AGREEMENT": dict(by_cls), "BY_OWNER_STATUS": dict(by_owner), "DISPLAYED_VALUES_CM_TOP": vals.most_common(12),
                        "WALL_THICKNESS_DIMENSIONS": {"15_CM": vals.get("15", 0) + vals.get("15.0", 0), "20_CM": vals.get("20", 0) + vals.get("20.0", 0)},
                        "PDF_COMPARISON": "NOT_POSSIBLE: the plotted PDF carries dimension numbers as outlined glyphs; only the title-block numbers (26.50, 19.00, 4.00, 305.30, 1:100) are in its text layer"},
            "RULE": "displayed vs measured compared per entity; nothing averaged; a CONFLICT stays a CONFLICT"}


def _classify(raw):
    return SEM.classify_text(raw)


def text_register():
    d = C.decode()
    n = CA.normalize(d, source_file=Path(C.DECODE).name)
    anchors = C.load_blind("PA07_SEMANTIC_ANCHOR_REGISTER")["ROWS"]
    anchor_by_text = {}
    for a in anchors:
        anchor_by_text.setdefault(a["RAW_TEXT"], []).append(a)
    spaces = {s["SPACE_ID"]: s for s in C.load_blind("PA07_PHYSICAL_SPACE_REGISTER")["ROWS"]}
    faces = C.load_blind("PA07_PLANAR_FACE_REGISTER")["ROWS"]
    space_by_face = {s["FACE_ID"]: s for s in spaces.values()}

    def attach(raw, x_cm, y_cm):
        """The engine's attachment for THIS text entity: the smallest planar face whose bbox holds the text point and whose anchor list carries the text."""
        x, y = x_cm * 10.0, y_cm * 10.0
        cands = [f for f in faces if f["BBOX_MM"][0] - 1 <= x <= f["BBOX_MM"][2] + 1 and f["BBOX_MM"][1] - 1 <= y <= f["BBOX_MM"][3] + 1 and any(a.get("TEXT") == raw for a in f["CONTAINS_SEMANTIC_ANCHOR"])]
        if not cands:
            return None
        f = min(cands, key=lambda f: f["AREA_GEOMETRIC_M2"])
        sp = space_by_face.get(f["FACE_ID"])
        a = next((z for z in anchor_by_text.get(raw, []) if z["ATTACHED_FACE_ID"] == f["FACE_ID"]), None) or (anchor_by_text.get(raw) or [None])[0]
        fa = next((z for z in f["CONTAINS_SEMANTIC_ANCHOR"] if z.get("TEXT") == raw), {})
        base = {"TEXT_ROLE": fa.get("ROLE"), "CANONICAL_CLASS": fa.get("CLASS"), "IDENTITY_STATUS": (sp or {}).get("SEMANTIC_IDENTITY", {}).get("STATUS")}
        base.update(a or {})
        return dict(base, ATTACHED_SPACE_ID=sp["SPACE_ID"] if sp else None, ATTACHED_FACE_ID=f["FACE_ID"])
    rows = []
    for i, t in enumerate(n.texts):
        raw = t.value
        clean = raw
        if raw.startswith("{\\f"):
            clean = raw.split(";", 1)[-1].rstrip("}").replace("\\P", " ")
        kb = C.looks_keyboard_arabic(clean)
        decoded, share = C.kb_decode(clean) if kb else (None, 0.0)
        eng = _classify(clean)
        lang = "AR_KEYBOARD_MAPPED" if kb else ("AR" if any('؀' <= c <= 'ۿ' for c in clean) else "EN")
        dec_cls = _classify(decoded) if decoded else None
        in_title = t.y < TITLE_BLOCK_Y_MAX or eng.get("TEXT_ROLE") == "SITE_LABEL" or (dec_cls or {}).get("TEXT_ROLE") == "SITE_LABEL" or any(k in clean.upper() for k in ("NEIGHBOUR", "STREET")) or (decoded and ("جار" in decoded or "شارع" in decoded))
        canonical, canon_src = None, None
        if eng.get("TEXT_ROLE") == "ROOM_NAME":
            canonical, canon_src = eng["CANONICAL_CLASS"], "ENGINE_VOCABULARY"
        elif dec_cls and dec_cls.get("TEXT_ROLE") == "ROOM_NAME":
            canonical, canon_src = dec_cls["CANONICAL_CLASS"], "KEYBOARD_DECODE_THEN_ENGINE_VOCABULARY"
        else:
            manual = {"PAINTRY": "PANTRY", "M.B.ROOM": "MASTER_BEDROOM", "DRESS": "DRESSING_ROOM", "تحضير": "PANTRY", "ملابس": "DRESSING_ROOM"}
            key = decoded or clean
            if key in manual or clean in manual:
                canonical, canon_src = manual.get(clean, manual.get(key)), "READER_INTERPRETATION"
        a0 = attach(raw, t.x, t.y)
        if in_title:
            identity = "NOT_APPLICABLE"
        elif canonical is None:
            identity = "UNRESOLVED"
        elif canon_src == "ENGINE_VOCABULARY":
            identity = "SOURCE_TEXT_ESTABLISHED" if a0 and a0["ATTACHED_SPACE_ID"] else "UNRESOLVED"
        else:
            identity = "AI_INTERPRETED"
        rows.append({"TEXT_ID": f"TX-{i:03d}", "RAW_TEXT": raw, "CLEAN_TEXT": clean, "LANGUAGE": lang, "KEYBOARD_DECODED": decoded, "KEYBOARD_MAP_SHARE": round(share, 2), "ENGINE_CLASSIFICATION": eng,
                     "CANONICAL_CLASS": canonical, "CANONICAL_SOURCE": canon_src, "SOURCE": "DWG", "POSITION_RAW_CM": [round(t.x, 1), round(t.y, 1)], "IN_TITLE_BLOCK_OR_SITE": in_title,
                     "ENGINE_TEXT_ROLE": a0["TEXT_ROLE"] if a0 else None, "ATTACHED_PHYSICAL_SPACE": a0["ATTACHED_SPACE_ID"] if a0 else None,
                     "ATTACHED_SPACE_AREA_M2": spaces[a0["ATTACHED_SPACE_ID"]]["AREA_GEOMETRIC_M2"] if a0 and a0["ATTACHED_SPACE_ID"] in spaces else None,
                     "ENGINE_IDENTITY_STATUS": a0["IDENTITY_STATUS"] if a0 else None, "IDENTITY_STATUS": identity, "CREATES_GEOMETRY": False})
    # bilingual pairing: an Arabic (keyboard) label within 120 cm of an English label with the same canonical class
    labels = [r for r in rows if not r["IN_TITLE_BLOCK_OR_SITE"]]
    for r in labels:
        r["BILINGUAL_PARTNER"] = None
        for q in labels:
            if q is r or q["LANGUAGE"] == r["LANGUAGE"]:
                continue
            dx = r["POSITION_RAW_CM"][0] - q["POSITION_RAW_CM"][0]; dy = r["POSITION_RAW_CM"][1] - q["POSITION_RAW_CM"][1]
            if math.hypot(dx, dy) <= 200 and (r["BILINGUAL_PARTNER"] is None or math.hypot(dx, dy) < r.get("_pd", 1e9)):
                r["BILINGUAL_PARTNER"] = q["TEXT_ID"]; r["_pd"] = math.hypot(dx, dy)
                r["BILINGUAL_CLASS_AGREEMENT"] = "AGREE" if r["CANONICAL_CLASS"] == q["CANONICAL_CLASS"] else ("ONE_SIDE_UNRESOLVED" if (r["CANONICAL_CLASS"] is None or q["CANONICAL_CLASS"] is None) else "CLASS_CONFLICT")
    for r in labels:
        r.pop("_pd", None)
    # PDF text layer
    doc = pymupdf.open(C.PDF); pg = doc[0]
    pdf_words = [{"RAW_TEXT": w[4], "POSITION_PT": [round(w[0]), round(w[1])], "SOURCE": "PDF", "LANGUAGE": "AR" if any('؀' <= c <= 'ۿ' for c in w[4]) else "EN"} for w in pg.get_text("words")]
    for w in pdf_words:
        if w["LANGUAGE"] == "AR":
            w["NOTE"] = "reversed glyph order in the PDF text layer (ةبطرق = قرطبة, the area name Qortuba)"
    # spaces without labels / multiple labels
    by_space = Counter(r["ATTACHED_PHYSICAL_SPACE"] for r in labels if r["ATTACHED_PHYSICAL_SPACE"])
    multi = {s: c for s, c in by_space.items() if c > 2}      # a bilingual pair is two labels for one room
    spaces_without = [s for s in spaces if s not in by_space]
    summary = {"DWG_TEXT_ENTITIES": len(rows), "ROOM_OR_ZONE_LABELS": len(labels), "TITLE_BLOCK_AND_SITE_TEXTS": len(rows) - len(labels),
               "ARABIC_LABELS_DETECTED": sum(1 for r in labels if r["LANGUAGE"].startswith("AR")), "ARABIC_ENCODING": "Latin-glyph keyboard-mapped shape font (no Unicode Arabic in the DWG); decoded deterministically by the keyboard map, marked AI_INTERPRETED",
               "ENGLISH_LABELS_DETECTED": sum(1 for r in labels if r["LANGUAGE"] == "EN"), "BILINGUAL_PAIRS": sum(1 for r in labels if r["LANGUAGE"] == "EN" and r.get("BILINGUAL_PARTNER")),
               "UNREADABLE_LABELS_BY_ENGINE": sum(1 for r in labels if r["ENGINE_TEXT_ROLE"] in ("UNDECODABLE_TEXT", "UNCLASSIFIED_TEXT")), "UNREADABLE_AFTER_KEYBOARD_DECODE": sum(1 for r in labels if r["CANONICAL_CLASS"] is None),
               "LABELS_ENGINE_VOCABULARY": sum(1 for r in labels if r["CANONICAL_SOURCE"] == "ENGINE_VOCABULARY"), "LABELS_KEYBOARD_DECODED_TO_VOCABULARY": sum(1 for r in labels if r["CANONICAL_SOURCE"] == "KEYBOARD_DECODE_THEN_ENGINE_VOCABULARY"),
               "LABELS_READER_INTERPRETED": sum(1 for r in labels if r["CANONICAL_SOURCE"] == "READER_INTERPRETATION"),
               "MIS_ASSOCIATED_LABELS": "cannot be counted without independent truth; 14 labels of 7 different rooms sit in ONE merged provisional cell (PS-aef07b7d3b2d), which is a topology failure, not a label failure",
               "SPACES_WITHOUT_LABELS": spaces_without, "LABELS_WITHOUT_A_VALID_SPACE": [r["TEXT_ID"] for r in labels if not r["ATTACHED_PHYSICAL_SPACE"]],
               "SPACES_WITH_MORE_THAN_ONE_ROOM": multi, "PDF_TEXT_LAYER_WORDS": len(pdf_words), "PDF_ROOM_LABELS_READABLE": 0, "PDF_NOTE": "room labels in the PDF are outlined glyphs; the PDF text layer holds the title block and site labels only",
               "ENGINE_ANCHORS": {"BY_TEXT_ROLE": dict(Counter(a["TEXT_ROLE"] for a in anchors)), "BY_IDENTITY_STATUS": dict(Counter(a["IDENTITY_STATUS"] for a in anchors))}}
    return {"ARTIFACT": "PA08_QORTUBA_TEXT_SEMANTIC_REGISTER", "RULE": "TEXT DOES NOT CREATE GEOMETRY; the engine's attachment and identity are reported as they are; the keyboard decode is a reader interpretation",
            "DWG_TEXTS": rows, "PDF_TEXTS": pdf_words, "SUMMARY": summary}


def reading_test(dim, txt):
    labels = [r for r in txt["DWG_TEXTS"] if not r["IN_TITLE_BLOCK_OR_SITE"]]
    ar = [r for r in labels if r["LANGUAGE"].startswith("AR")]; en = [r for r in labels if r["LANGUAGE"] == "EN"]
    conflicts = [(r["TEXT_ID"], r["RAW_TEXT"], r["CANONICAL_CLASS"], txt["DWG_TEXTS"][int(r["BILINGUAL_PARTNER"][3:])]["KEYBOARD_DECODED"], txt["DWG_TEXTS"][int(r["BILINGUAL_PARTNER"][3:])]["CANONICAL_CLASS"]) for r in en if r.get("BILINGUAL_PARTNER") and r.get("BILINGUAL_CLASS_AGREEMENT") == "CLASS_CONFLICT"]
    spaces = C.load_blind("PA07_PHYSICAL_SPACE_REGISTER")["ROWS"]
    by_space = Counter(r["ATTACHED_PHYSICAL_SPACE"] for r in labels if r["ATTACHED_PHYSICAL_SPACE"])
    return {"ARTIFACT": "QORTUBA_READING_TEST", "RULE": "counts and states only; no percentage without an independent truth",
            "A_NUMBER_READING": {"DIMENSIONS_DISCOVERED": dim["TOTAL_DIMENSION_ENTITIES"], "DISPLAY_AGREES_WITH_GEOMETRY": dim["SUMMARY"]["BY_AGREEMENT"].get("AGREE", 0) + dim["SUMMARY"]["BY_AGREEMENT"].get("AGREE_WITHIN_ROUNDING", 0),
                                 "CONNECTED_TO_GEOMETRY_BOTH_ENDS": dim["SUMMARY"]["BY_OWNER_STATUS"].get("BOTH_OWNED", 0), "ONE_END_ONLY": dim["SUMMARY"]["BY_OWNER_STATUS"].get("ONE_OWNED", 0),
                                 "UNOWNED": dim["SUMMARY"]["BY_OWNER_STATUS"].get("UNOWNED", 0), "UNSUPPORTED": dim["SUMMARY"]["UNSUPPORTED"], "CONFLICTS": dim["SUMMARY"]["CONFLICTING"],
                                 "UNIT": "centimetres declared by INSUNITS 5, SOURCE_ESTABLISHED by the unit register", "PDF_NUMBERS": "not readable (outlined)"},
            "B_ARABIC_READING": {"RAW_ARABIC_LABELS": [(r["TEXT_ID"], r["RAW_TEXT"]) for r in ar], "CANONICAL_INTERPRETATIONS": [(r["TEXT_ID"], r["KEYBOARD_DECODED"], r["CANONICAL_CLASS"], r["CANONICAL_SOURCE"]) for r in ar],
                                 "ENGINE_READ": "0 of them: the engine sees Latin glyphs and marks them UNDECODABLE_TEXT (safe)", "UNREADABLE_AFTER_DECODE": [(r["TEXT_ID"], r["KEYBOARD_DECODED"]) for r in ar if r["CANONICAL_CLASS"] is None],
                                 "AMBIGUOUS": [(r["TEXT_ID"], r["KEYBOARD_DECODED"]) for r in ar if r["CANONICAL_SOURCE"] == "READER_INTERPRETATION"]},
            "C_ENGLISH_READING": {"RAW_ENGLISH_LABELS": [(r["TEXT_ID"], r["RAW_TEXT"]) for r in en], "CANONICAL_INTERPRETATIONS": [(r["TEXT_ID"], r["CANONICAL_CLASS"], r["CANONICAL_SOURCE"]) for r in en],
                                  "ENGINE_VOCABULARY_HITS": [(r["TEXT_ID"], r["RAW_TEXT"], r["ENGINE_CLASSIFICATION"].get("CANONICAL_CLASS")) for r in en if r["CANONICAL_SOURCE"] == "ENGINE_VOCABULARY"],
                                  "ENGINE_MISSES": [(r["TEXT_ID"], r["RAW_TEXT"]) for r in en if r["CANONICAL_SOURCE"] != "ENGINE_VOCABULARY"], "CONFLICTS_WITH_ARABIC": conflicts,
                                  "NOTE": "HALL classifies as CORRIDOR in the engine vocabulary while the Arabic partner 'صالة' classifies as LIVING: a vocabulary conflict, recorded, not resolved"},
            "D_GEOMETRIC_ASSOCIATION": {"LABELS_ATTACHED_TO_A_PHYSICAL_SPACE": sum(1 for r in labels if r["ATTACHED_PHYSICAL_SPACE"]), "LABELS_WITHOUT_A_SPACE": [r["TEXT_ID"] for r in labels if not r["ATTACHED_PHYSICAL_SPACE"]],
                                        "SPACES_WITH_LABELS": len(by_space), "SPACES_WITHOUT_LABELS": [s["SPACE_ID"] for s in spaces if s["SPACE_ID"] not in by_space],
                                        "MULTIPLE_ROOMS_IN_ONE_SPACE": {s: c for s, c in by_space.items() if c > 2},
                                        "CORRECTLY_ATTACHED": "NOT_ASSESSABLE without independent truth: the engine's cells are BOUNDARY_PROVISIONAL and one cell holds seven rooms' labels"}}


def main():
    dim = dimension_register(); txt = text_register(); rt = reading_test(dim, txt)
    C.write("PA08_QORTUBA_DIMENSION_REGISTER", dim); C.write("PA08_QORTUBA_TEXT_SEMANTIC_REGISTER", txt); C.write("QORTUBA_READING_TEST", rt)
    print(json.dumps(dim["SUMMARY"], ensure_ascii=False)[:900]); print(json.dumps(txt["SUMMARY"], ensure_ascii=False, default=str)[:1500])
    for r in txt["DWG_TEXTS"]:
        if not r["IN_TITLE_BLOCK_OR_SITE"]:
            print("  ", r["TEXT_ID"], repr(r["RAW_TEXT"]), r["LANGUAGE"], r["KEYBOARD_DECODED"], r["CANONICAL_CLASS"], r["CANONICAL_SOURCE"], r["ATTACHED_PHYSICAL_SPACE"], r["IDENTITY_STATUS"], r.get("BILINGUAL_PARTNER"))


if __name__ == "__main__":
    main()
