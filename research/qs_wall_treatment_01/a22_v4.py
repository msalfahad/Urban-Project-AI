"""A22 RECONCILIATION REGISTER v4 (directive §13, §15): engineering lines
against the contractor / site basis on the SAME faces, every difference
decomposed and classified; agreement between two methods that share a
source is not independent confirmation. Every benchmark figure stays
conditional: IF_BENCHMARK_IS_P7757.

    python3 -m research.qs_wall_treatment_01.a22_v4
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
CLASSES = ("ENGINE_GEOMETRY_ERROR", "HUMAN_MEASUREMENT_ERROR_OR_OMISSION", "MEASUREMENT_BASIS_DIFFERENCE",
           "SCOPE_DIFFERENCE", "IDENTITY_MAPPING_ERROR", "DRAWING_AMBIGUITY", "RULE_DIFFERENCE", "UNRESOLVED", "AGREEMENT")
DRIVERS = ("GEOMETRY_DIFFERENCE", "HEIGHT_RULE_DIFFERENCE", "OPENING_RULE_DIFFERENCE", "REVEAL_RULE_DIFFERENCE",
           "SCOPE_DIFFERENCE", "MEASUREMENT_BASIS_DIFFERENCE", "IDENTITY_MAPPING_DIFFERENCE", "UNRESOLVED")


def _item(iid, where, eng, eng_basis, con, con_basis, drivers, cls, independence, shared, note=None):
    assert cls in CLASSES
    for d in drivers:
        assert d in DRIVERS
    delta = (round(con - eng, 4) if isinstance(eng, (int, float)) and isinstance(con, (int, float)) else None)
    return {"ITEM_ID": iid, "LOCATION": where, "ENGINEERING": eng, "ENGINEERING_BASIS": eng_basis,
            "CONTRACTOR": con, "CONTRACTOR_BASIS": con_basis, "DELTA_CONTRACTOR_MINUS_ENGINEERING": delta,
            "DRIVERS": drivers, "CLASS": cls, "SOURCE_INDEPENDENCE": independence, "SHARED_ASSUMPTIONS": shared,
            "NEVER_AVERAGED": True, "CONDITIONAL": "IF_BENCHMARK_IS_P7757", "NOTE": note}


def run() -> dict:
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    dual = json.loads((OUT / "DUAL_BASIS_v3.json").read_text("utf-8"))
    rb = dual["CONTRACTOR_RULEBOOK"]
    lines = {l["LINE_ID"]: l for l in tr["LINES"]}
    items = []
    # SALOON normal walls: carried from DUAL_BASIS_v3 (same faces, height 3.20 vs 3.60)
    pr = dual["PROJECT"]
    items.append(_item("A22-4-SALOON", "GF SALOON established faces", pr.get("ENGINEERING_ESTABLISHED_M2", 22.88), "MEASURED_NET: owner 3.20, full deduction",
                       pr["CONTRACTOR_ON_THE_SAME_FACES_M2"], "CONTRACTOR: site height 3.60, half deduction", ["HEIGHT_RULE_DIFFERENCE"],
                       "MEASUREMENT_BASIS_DIFFERENCE", "engineering: owner-verified 515 + CAD; contractor: site record", ["same faces"],
                       "unchanged from DUAL_BASIS_v3"))
    # parapets on the same faces: contractor 1.70 (main) / 0.70 (annex) heights from the site record
    h_main = 1.70
    h_annex = 0.70
    for fid, h_con, tag in (("FACE:F-SE-SOLID-ROOFSIDE", h_main, "SE solid portion roof-side"),
                            ("FACE:F-NE-SOLID-ROOFSIDE", h_main, "NE parapet roof-side"),
                            ("FACE:F-TOWER-RING-ROOFSIDE", h_annex, "+13.90 tower ring roof-side")):
        l = lines.get(fid)
        if not l or l.get("VALUE") is None:
            continue
        con = round(l["LENGTH_M"] * h_con, 4)
        items.append(_item(f"A22-4-{fid}", tag, l["VALUE"], f"face-specific: {l['HEIGHT_M']} x {l['LENGTH_M']} ({l['QUANTITY_STATE']})",
                           con, f"CONTRACTOR_MEASUREMENT_RULE parapet height {h_con} x the same length",
                           ["HEIGHT_RULE_DIFFERENCE"], "MEASUREMENT_BASIS_DIFFERENCE",
                           "engineering: DWG / structural / section dimensions; contractor: site convention", ["same length"],
                           "the contractor's parapet height is a payment convention, never converted into geometry"))
    # D2 column
    l = lines["D2:COLUMN:LOOP-059"]
    con = round(l["LENGTH_M"] * rb["HEIGHT_GROUND"]["VALUE"], 4)
    items.append(_item("A22-4-D2-COLUMN", "GF SALOON/RECEPTION free column LOOP-059", l["VALUE"], "girth 1.80 (structural 30x60) x owner 3.20",
                       con, f"girth 1.80 x site height {rb['HEIGHT_GROUND']['VALUE']}", ["HEIGHT_RULE_DIFFERENCE"], "MEASUREMENT_BASIS_DIFFERENCE",
                       "engineering: ST7757.pdf column plan registered to the DWG (30 inliers, <=55 mm); contractor: site record", ["girth"],
                       "the owner earlier flagged a 'column 5.76' item; the engineering line 1.80 x 3.20 = 5.76 is derived independently; "
                       "whether the flagged item is this column is IDENTITY NOT_ESTABLISHED"))
    # whole-house scope lines (conditional)
    eng_roof = tr["BY_CATEGORY"]["ROOF_SIDE_PARAPET"]["TOTALS_BY_UNIT_AND_STATE"].get("m2", {})
    eng_roof_total = round(sum(eng_roof.values()), 4)
    par = dual["PARAPETS"]["CONTRACTOR"]
    items.append(_item("A22-4-PARAPET-SCOPE", "all roof parapets", eng_roof_total, "traced roof-side faces only (SE solid + kerb, NE, tower ring); SW and second roof area unresolved",
                       par["MAIN_PARAPET"]["AREA_M2"], f"main parapet {par['MAIN_PARAPET']['LENGTH_LM']} lm x {par['MAIN_PARAPET']['HEIGHT_M']}",
                       ["SCOPE_DIFFERENCE", "HEIGHT_RULE_DIFFERENCE", "IDENTITY_MAPPING_DIFFERENCE"], "UNRESOLVED",
                       "different sources", ["none"], "which edges the contractor's 48.47 lm covers is not stated; engineering lengths: SE 3.48 + 3.77, NE 18.87, tower 28.40, SW 4.13 (no height)"))
    items.append(_item("A22-4-FACADE-SCOPE", "external facades", None, "gross SE facade 40.5 m2 with openings UNRESOLVED (net NOT_ESTABLISHED)",
                       dual["FACADES"].get("CONTRACTOR", {}).get("TOTAL_NET_M2") if isinstance(dual.get("FACADES"), dict) else None,
                       "whole-facade heights 14.40 / 10.00 / 6.00, half openings", ["SCOPE_DIFFERENCE", "HEIGHT_RULE_DIFFERENCE"], "SCOPE_DIFFERENCE",
                       "different sources", ["none"], "no engineering facade net exists yet: openings below the parapets are untraced"))
    # same-family corroboration is not independent confirmation
    indep = {"DWG_ELEVATION_vs_RASTER_ELEVATION": "SAME_DESIGN_FAMILY: the DWG elevation corroborates the base line (+9.86/+9.88) but "
                                                  "prints 110 (+9.70 -> +10.80) where the frozen raster prints 680 to +11.10; classified DRAWING_AMBIGUITY "
                                                  "(revision difference), the frozen raster remains the contract source",
             "ST7757_vs_DWG": "different discipline, same design office: corroborates column positions (30/30) and the 7.50 m roof edge; "
                              "not site truth",
             "CONTRACTOR_RECORD": "independent of the drawings (site record) but conditional on identity (D3)"}
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "A22_RECONCILIATION_REGISTER", "VERSION": "v4", "CLASSES": CLASSES, "DRIVERS": DRIVERS,
           "ITEMS": items, "SOURCE_INDEPENDENCE_NOTES": indep, "BENCHMARK_IDENTITY": "OWNER_CONFIRMATION_REQUIRED (D3)",
           "NO_TUNING": "no engineering geometry was changed to approach any contractor figure", "NOT_MAJORITY_VOTING": True}
    p = OUT / "A22_RECONCILIATION_REGISTER.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    return {"ITEMS": [(i["ITEM_ID"], i["ENGINEERING"], i["CONTRACTOR"], i["DELTA_CONTRACTOR_MINUS_ENGINEERING"], i["CLASS"]) for i in items],
            "SHA": hashlib.sha256(p.read_bytes()).hexdigest()[:16]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
