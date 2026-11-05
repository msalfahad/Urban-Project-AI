"""T-529 training-villa declarations: entity handles and printed values only (no coordinate, no client data).

Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...), read this run.
"""
from __future__ import annotations

# ---- the ledge (T-486 'overhang' polygon, Checker 0.6396 AGREE; T-522 split of its bay face) ------------------------
BAY_RUNS = (("BCD", "WALL"), ("BCE", "GLAZING"), ("BD0", "WALL"))     # r 1.935, layers 1 / 5 / 1
BCE_HEAD_SOURCE = ("NW elevation: arched glazing '269' x '305' + '45' (DIMENSIONs 2D53 / 2E97), the wall above the "
                   "arch to the slab; the bay face is the building envelope (it does not decide the ledge: open sides)")
VOID_SOURCE = "1F plan: void edge BCF (r 1.735) / 2F1C, layer 5 single lines, nothing standing on them (T-486)"
SPLIT_SOURCE = ("1F plan: the 1F east wall line B62 / B61 (layer 1) produced across the bay recess: the zone split of "
                "T-486 / T-507; the slab continues as POOLCOURT-550 (no step, no joint, no upstand drawn)")

# ---- the cover above (2F plan; frame offset -44.85 m in x from the 1F frame, T-494 / T-522) -------------------------
FRAME_DX_M = 44.85
ROOF_HATCH = "2F21"          # 2F ROOF +9.70 hatch (layer 3, pattern LINE); its external paths are the slab top outline
BAND_WEST = "12A7"           # layer 5, vertical: the hatch's east edge (= the 2F parapet inner face over the 1F wall)
BAND_EAST = "1319"           # layer 5, vertical: east edge of the element drawn past the 1F wall line
BAND_SOUTH = "1311"          # layer 5, horizontal: its south end
BAND_NORTH_STEP = "130C"     # layer 5: north end of the straight east edge (the rounded corner 1313 begins there)
BAND_CORNER = "1313"         # layer 5 arc r 0.298: rounded north-east corner
FASCIA_BAND = ("1314", "1315", "1316", "1317", "1318")   # layer 5: 0.05 m strip outside BAND_EAST
WALL_BELOW = "131B"          # layer 2 (dashed, below): the 1F wall line seen from the 2F plan
DIM_PROJECTION = "19A6"      # printed '35' (cm): 1F wall line to the outer face of the fascia strip
DIM_TO_PLOT = "140A"         # printed '150' (cm): 1F wall line to the plot line (12A4)
COVER_SOURCE = ("2F plan (P7757.dxf, frame -44.85 m): ROOF +9.70 hatch 2F21 to its east edge 12A7, then the layer-5 "
                "element 12A7 / 1311 / 1319 / 130C / 1313 drawn 0.35 m past the 1F wall line (printed '35', DIMENSION "
                "19A6; '150' 140A to the plot line); 1F wall line seen below as 131B (layer 2)")
COVER_H_LEVEL_M = 4.20       # +5.50 -> +9.70 level to level (information only; V2 needs no height)

# ---- the V3.0.58 lines (T-507) and the T-522 state ---------------------------------------------------------------------
V3058 = {
    "L-2361d6ec13c952bd2ae3": ("FIN.WP.ROOF", "m2", "1F-POOLCOURT-550-LEDGE:wp_membrane", 0.0, 0.639573),
    "L-d7d1bf8c5991ccf69ea2": ("FIN.WP.ROOF_UPTURN", "lm", "1F-POOLCOURT-550-LEDGE:wp_upturn", 0.0, 3.528277),
}
V3058_TOTALS = {"FIN.WP.ROOF": (209.018867, "m2"), "FIN.WP.ROOF_UPTURN": (186.782544, "lm")}
T522_WINDOW_LM = 0.500002    # T-522 (merged, unwired): window run upturn
OPEN_SKY_M2_T507 = 4.906867  # T-507 POOLCOURT-550 open-sky membrane (wired in V3.0.58)
