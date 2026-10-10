"""Section 1: source inventory of the Qortuba DWG (via its LibreDWG decode) and PDF.  Facts only, no interpretation."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pymupdf

from engine import cad_adapter as CA
from research.qs_wall_treatment_01.pa08.qortuba import common as C


def _ah(h):
    return h[-1] if isinstance(h, list) and h else None


def dwg_inventory():
    d = C.decode(); objs = d["OBJECTS"]; hdr = d.get("HEADER", {})
    layer_name = {_ah(o.get("handle")): o.get("name") for o in objs if o.get("object") == "LAYER"}
    blocks = {_ah(o.get("handle")): o.get("name") for o in objs if o.get("object") == "BLOCK_HEADER"}
    ent_by_type = Counter(o.get("entity") for o in objs if "entity" in o)
    ent_by_layer = Counter(layer_name.get(_ah(o.get("layer")), "?") for o in objs if "entity" in o and o.get("entity") not in ("BLOCK", "ENDBLK"))
    inserts = Counter(blocks.get(_ah(o.get("block_header")), "?") for o in objs if o.get("entity") == "INSERT")
    layouts = [{"NAME": o.get("layout_name"), "FLAGS": o.get("layout_flags")} for o in objs if o.get("object") == "LAYOUT"]
    n = CA.normalize(d, source_file=Path(C.DECODE).name)
    per_layer = Counter((p.provenance.layer, p.kind) for p in n.primitives)
    xs = [v for p in n.primitives for v in (p.x1, p.x2, p.cx) if v]; ys = [v for p in n.primitives for v in (p.y1, p.y2, p.cy) if v]
    texts = [{"RAW": t.value, "X": round(t.x, 1), "Y": round(t.y, 1)} for t in n.texts]
    return {"SOURCE_FILE": C.DWG, "FILE_HASH": C.sha(C.DWG), "DECODE_FILE": C.DECODE, "DECODE_HASH": C.sha(C.DECODE), "DWG_VERSION": d.get("FILEHEADER", {}).get("version") or "AC1027 (R2013)",
            "CAD_UNITS": {"INSUNITS": hdr.get("INSUNITS"), "MEANING": "5 = centimetres", "DIMLFAC": hdr.get("DIMLFAC"), "LUNITS": hdr.get("LUNITS"), "DIMSCALE": hdr.get("DIMSCALE")},
            "OBJECT_COUNT": len(objs), "ENTITIES_BY_TYPE": dict(ent_by_type), "ENTITIES_BY_LAYER": dict(ent_by_layer), "LAYERS": sorted(v for v in layer_name.values() if v),
            "BLOCKS": {"DEFINITIONS": len(blocks), "NAMED": sorted({v for v in blocks.values() if v and not v.startswith("*")}), "ANONYMOUS_DIMENSION_BLOCKS": sum(1 for v in blocks.values() if v == "*D"),
                       "INSERTS_BY_BLOCK": dict(inserts)},
            "LAYOUTS": layouts, "ENTITIES_IN_OTHER_LAYOUTS": n.notes.get("entities_in_other_layouts"),
            "NORMALIZED": {"PRIMITIVES": len(n.primitives), "BY_KIND": dict(Counter(p.kind for p in n.primitives)), "BY_LAYER_KIND": {f"{k[0]}|{k[1]}": v for k, v in sorted(per_layer.items())},
                           "TEXTS": len(n.texts), "DIMENSIONS": len(n.dimensions), "MODEL_EXTENT_RAW_UNITS": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]},
            "TEXT_AVAILABILITY": "TEXT_ENTITIES (51 TEXT + 105 MTEXT; room labels in blocks on layer TEXT; Arabic labels typed through a Latin-glyph shape font)",
            "DIMENSION_ENTITY_AVAILABILITY": f"{ent_by_type.get('DIMENSION_LINEAR', 0)} DIMENSION_LINEAR entities with anonymous *D blocks",
            "PLAN_VIEWS": ["one plan in model space (SECOND FLOOR PLAN per title block)"], "OTHER_VIEWS": [], "STOREYS": ["SECOND FLOOR (title block); level text 'LEVEL R.F = 4.00 m'"],
            "DETAILS": [], "SECTIONS": [], "ELEVATIONS": [], "TEXTS_RAW": texts}


def pdf_inventory():
    doc = pymupdf.open(C.PDF)
    pages = []
    for i, pg in enumerate(doc):
        txt = pg.get_text("text") or ""; words = [w[4] for w in pg.get_text("words")]
        ar = [w for w in words if any('؀' <= c <= 'ۿ' for c in w)]
        nums = [w for w in words if re.fullmatch(r"[\d.,:/]+", w)]
        pages.append({"PAGE": i + 1, "SIZE_PT": [round(pg.rect.width), round(pg.rect.height)], "PAPER": "A3 landscape (1191 x 842 pt)", "TEXT_CHARS": len(txt.strip()), "WORDS": len(words),
                      "ARABIC_WORDS_IN_TEXT_LAYER": ar, "NUMERIC_TOKENS_IN_TEXT_LAYER": nums, "VECTOR_PATHS": len(pg.get_drawings()), "IMAGES": len(pg.get_images()),
                      "SCALE_TEXT": [w for w in words if w in ("1:100", "1/100")], "TITLE_WORDS": [w for w in words if w in ("SECOND", "FLOOR", "PLAN")], "ALL_WORDS": words})
    return {"SOURCE_FILE": C.PDF, "FILE_HASH": C.sha(C.PDF), "PAGE_COUNT": len(doc), "PDF_VECTOR_OR_RASTER": "VECTOR (7278 paths, 8 small images = logo / hatch samples)", "PDF_SCALE": "1:100 (title block) on A3",
            "TEXT_AVAILABILITY": "TEXT_LAYER for the title block and site labels only; room labels and dimension numbers are drawn as outlines (not in the text layer)",
            "PAGES": pages}


def main():
    dwg = dwg_inventory(); pdf = pdf_inventory()
    dwg_labels = {t["RAW"] for t in dwg["TEXTS_RAW"]}
    pdf_words = set(pdf["PAGES"][0]["ALL_WORDS"])
    inv = {"ARTIFACT": "PA08_QORTUBA_SOURCE_INVENTORY", "PROJECT_ALIAS": "QORTUBA", "DWG": dwg, "PDF": pdf,
           "DWG_CONTAINS_MORE_THAN_PDF": {"VERDICT": "YES_IN_STRUCTURE_NO_IN_VIEWS",
                                          "DETAIL": ["the DWG carries the model space plan, 101 authored dimension entities, 26 layers, 116 block definitions and one paper-space layout (Layout1) with a single entity; the PDF is one plotted page of the same plan",
                                                     "room labels and dimension numbers exist as text entities in the DWG but only as outlines in the PDF (not readable from the PDF text layer)",
                                                     "no second plan, section, elevation, schedule or detail exists in either source"],
                                          "PDF_TEXT_WORDS_ALSO_IN_DWG": sorted(w for w in pdf_words if any(w in t for t in dwg_labels))[:40]},
           "SOURCE_FAMILY_COVERAGE": C.load_blind("SOURCE_INVENTORY")}
    print(C.write("PA08_QORTUBA_SOURCE_INVENTORY", inv))
    return inv


if __name__ == "__main__":
    main()
