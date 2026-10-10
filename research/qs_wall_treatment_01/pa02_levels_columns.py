"""PA02.1 - D1 level identity (eight level fields, two bases, source
exhaustion) and the COLUMN FACE REGISTER.

    python3 -m research.qs_wall_treatment_01.pa02_levels_columns
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import column_faces as CF
from engine import level_identity as LI
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def run() -> dict:
    link = json.loads((OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    sol = link["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"]
    L_in = sol["ROOF_SIDE_FACE_LENGTH_M"]
    slab = LI.level(9.70, "LVL-01/LVL-03/LVL-05 (+9.70) and the structural roof-slab sheet printing +9.70 on the slab itself (ST7757 p6)",
                    "SOURCE_ESTABLISHED", ["DIM-15 chain 420 from +13.90", "structural sheets mark +9.70 on the +9.70 roof; structural sheets carry top-of-concrete levels"],
                    ["STRUCTURAL_SLAB_TOP"])
    arch_roof = LI.level(9.70, "architectural level mark on the roof plan (LVL-01)", "SOURCE_ESTABLISHED", ["same value as the structural level: the architectural roof level is the slab top; no separate finished level is printed"],
                         ["ARCHITECTURAL_ROOF_LEVEL = STRUCTURAL_SLAB_TOP"])
    finished = LI.level(9.88, "drawn base line on the SE elevation (UNK-09, ~+9.90 by the x=715 chain) and level lines at +9.856 / +9.883 in the DWG elevation blob (NW edge)",
                        "PROVISIONAL", ["two edges (SE raster, NW DWG) draw a line 0.16-0.18 above the slab", "B-B and A-A draw NO roof build-up layer: the parapet hatch starts at the slab top",
                                        "no roof build-up detail in the architectural or structural set (the 5 cm screed / 5 cm insulation / 10 cm plain concrete detail is the pool's)"],
                        ["FINISHED_ROOF_LEVEL (build-up ~0.18)", "FACADE_BAND_TOP_EDGE (drawing convention of the elevation)", "UNRESOLVED"])
    unknown = lambda what: LI.level(None, f"{what}: no source in the set", "NOT_ESTABLISHED", [], [])
    levels = LI.level_set(STRUCTURAL_SLAB_LEVEL=slab, ARCHITECTURAL_ROOF_LEVEL=arch_roof, FINISHED_ROOF_LEVEL=finished,
                          WATERPROOFING_LEVEL=unknown("waterproofing"), SCREED_FOAM_BUILDUP_LEVEL=unknown("screed / foam build-up"),
                          PARAPET_BASE_LEVEL=LI.level(9.70, "sections B-B / A-A: hatched parapet masonry starts at the hatched slab top", "SOURCE_ESTABLISHED",
                                                      ["PAR-04 (B-B) and PAR-07/08/09 (A-A) hatched from the slab top line"], ["PARAPET_BASE = STRUCTURAL_SLAB_TOP"]),
                          VISIBLE_FINISH_FACE_BOTTOM=LI.level(9.88, "= FINISHED_ROOF_LEVEL candidate", "PROVISIONAL", ["identity of +9.88 not established"], ["FINISHED_ROOF_LEVEL", "UNRESOLVED"]),
                          EXECUTED_PLASTER_FACE_BOTTOM=LI.level(9.70, "= PARAPET_BASE_LEVEL: plaster is executed on the masonry from the slab before any roof build-up", "PROVISIONAL",
                                                                ["no evidence of build-up; executed face assumed to start where the masonry starts"], ["PARAPET_BASE_LEVEL"]))
    top = LI.level(11.10, "DIM-21 680 from LVL-07 +4.30 (OWNER_ESTABLISHED, termination audit)", "SOURCE_ESTABLISHED", ["SE_ELEVATION_SOURCE_AUDIT DIM-21"], ["SOLID_WALL_TOP / BAND_UNDERSIDE"])
    cands = [LI.face_candidate(basis="ENGINEERING_VISIBLE_FINISH_BASIS", bottom=levels["VISIBLE_FINISH_FACE_BOTTOM"], top=top, length_m=L_in,
                               length_source="PROPOSED_CORRESPONDENCE", note="face visible above the finished roof if +9.88 is the finished roof level"),
             LI.face_candidate(basis="CONTRACTOR_EXECUTED_WORK_BASIS", bottom=levels["EXECUTED_PLASTER_FACE_BOTTOM"], top=top, length_m=L_in,
                               length_source="PROPOSED_CORRESPONDENCE", note="face plastered on the masonry from the slab; the lower 0.18 may later be concealed by roof build-up")]
    exhausted = [{"SOURCE": "SECTION_B_B (native)", "EXHAUSTED": True, "FOUND": "no build-up layer; kerb hatch from the slab top; outer skin element UNK-05 spans ~+8.6 to ~+10.5"},
                 {"SOURCE": "SECTION_A_A (native)", "EXHAUSTED": True, "FOUND": "tower ring hatched from the slab top; no build-up"},
                 {"SOURCE": "ROOF_PLAN (raster + DWG copy)", "EXHAUSTED": True, "FOUND": "+9.70 marks only; no finished-level mark"},
                 {"SOURCE": "ARCHITECTURAL_DWG elevation blob", "EXHAUSTED": True, "FOUND": "level lines at +9.856 / +9.883 (NW edge); no annotation of what they are"},
                 {"SOURCE": "STRUCTURAL ST7757.pdf", "EXHAUSTED": True, "FOUND": "+9.70 printed on the slab sheet; no roof build-up detail; pool build-up detail only"},
                 {"SOURCE": "ROOF BUILD-UP SPECIFICATION", "EXHAUSTED": True, "FOUND": "SOURCE_NOT_PROVIDED"}]
    d1 = LI.dual(candidates=cands, exhausted_sources=exhausted,
                 identity_open="what the drawn +9.88 line is (finished roof level vs an elevation drawing convention); the roof build-up thickness")
    d1["QUANTITY_DIFFERENCE_M2"] = round(abs(cands[0]["AREA_M2"] - cands[1]["AREA_M2"]), 3)
    d1["OWNER_QUESTION_FORM"] = ("information, not A/B: 'what is the roof build-up over the +9.70 slab (screed / insulation / tiles, total thickness)?' "
                                 "- if ~0.18 m, +9.88 is the finished roof level and both bases are carried as stated; if none, the two bases coincide")
    # ---- column faces --------------------------------------------------------
    cols = []
    cols.append(CF.column(column_id="LOOP-059 (GF SALOON/RECEPTION open edge)", width_m=0.30, depth_m=0.60,
                          exposures={"A": "EXPOSED", "B": "EXPOSED", "C": "EXPOSED", "D": "EXPOSED"},
                          host_wall_relation="FREE_STANDING: 1.3 m off the neighbour-wall face; beams to the wall (ST p3 ground beam, p4 ceiling beam), no wall drawn",
                          occlusion="the overhead beam line (CAD-783) is above the plaster zone; nothing occludes the faces on the GF plan",
                          bonding_required=True, plaster_required=True, source="PROVISIONAL",
                          exposure_source="PROVISIONAL", partial_lengths=None))
    cols[-1]["SOURCE_NOTE"] = "ST7757.pdf p1 (30x60) registered to the DWG (vector tier); architectural loop 25x60"
    cols[-1]["ALTERNATIVE_ARCHITECTURAL_LOOP"] = {"WIDTH": 0.25, "DEPTH": 0.60, "GIRTH_LM": 1.70,
                                                  "WHY": "the S-COL.BON hatch is 250 deep; the structural section is 300; finish thickness unknown"}
    cols.append(CF.column(column_id="COL-02 (SALOON sea-view corner pier)", width_m=0.20, depth_m=0.50,
                          exposures={"A": "EXPOSED", "B": "BURIED_IN_WALL", "C": "BURIED_IN_WALL", "D": "BURIED_IN_WALL"},
                          host_wall_relation="pier inside the sea-view wall; one face (0.20) exposed to the SALOON per the S-COL.BON hatch extent (estimate v3 CAD_LENGTHS_V3)",
                          occlusion=None, bonding_required=True, plaster_required=True, source="PROVISIONAL", exposure_source="PROVISIONAL"))
    cols[-1]["SOURCE_NOTE"] = "CAD S-COL.BON hatch extent (estimate v3 CAD_LENGTHS_V3)"
    cols.append(CF.column(column_id="COL-01 (SALOON return-wall pier)", width_m=0.30, depth_m=0.50,
                          exposures={"A": "EXPOSED", "B": "BURIED_IN_WALL", "C": "BURIED_IN_WALL", "D": "BURIED_IN_WALL"},
                          host_wall_relation="pier inside the return wall; 0.30 exposed per the hatch extent (v3)", occlusion=None,
                          bonding_required=True, plaster_required=True, source="PROVISIONAL", exposure_source="PROVISIONAL"))
    cols[-1]["SOURCE_NOTE"] = "CAD S-COL.BON hatch extent (estimate v3 CAD_LENGTHS_V3)"
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "D1_LEVEL_IDENTITY", "LEVEL_FIELDS": LI.LEVEL_FIELDS, "LEVELS": levels,
           "SOLID_TOP": top, "D1_DUAL_BASIS": d1,
           "D1_STATUS": "DUAL_BASIS_PRESERVED; +9.88 identity NOT_ESTABLISHED after source exhaustion; owner asked for build-up information, not A/B",
           "CORRECTION": "the DWG elevation blob previously labelled 'SE elevation (mirrored)' is the NORTH WEST elevation (its printed 155 / 269 / 305 / 230 "
                         "match the NW raster sheet); its +9.856 / +9.883 lines belong to the NW roof edge - a second edge drawing the same 0.18 offset"}
    (OUT / "D1_LEVEL_IDENTITY.json").write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    cf = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "COLUMN_FACE_REGISTER", "COLUMNS": cols,
          "RULE": "EXPOSED_PLASTERABLE_GIRTH counts exposed faces only; structural girth is a different fact"}
    (OUT / "COLUMN_FACE_REGISTER.json").write_text(json.dumps(cf, indent=2, default=str) + "\n", encoding="utf-8")
    return {"D1": {"CANDIDATES": [(c["MEASUREMENT_BASIS"], c["BOTTOM_LEVEL"], c["HEIGHT"], c["AREA_M2"], c["QUANTITY_STATE"]) for c in cands],
                   "DIFF": d1["QUANTITY_DIFFERENCE_M2"], "A_B_ALLOWED": d1["OWNER_A_B_QUESTION_ALLOWED"]},
            "COLUMNS": [(c["COLUMN_ID"][:12], c["STRUCTURAL_GIRTH_LM"], c["EXPOSED_PLASTERABLE_GIRTH_LM"], c["GIRTH_STATE"]) for c in cols]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
