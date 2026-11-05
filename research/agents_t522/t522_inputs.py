"""T-522 training-villa declarations: entity handles and printed values only (no coordinate, no client data).

Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...), and the architectural PDF
part "Alsenan_Architectural_P7757_Pages_07-08" page 2 (NORTH WEST ELEVATION, 1:100), read this run by eye only.
"""
from __future__ import annotations

# ---- R-T522-1: the 1F bath window on the pool-court wall line (plan run C35, 0.500002 lm, T-494) --------------------
SILL_DIM = "2EEC"            # DXF elevation view NW: vertical DIMENSION, printed text '84' (cm), measured 839.27 mm
SILL_CHAIN_NEXT = "2EFA"     # the window height above it, printed '216' (window head 0.84 + 2.16 = 3.00 m)
WINDOW_WIDTH_DIM = "2D8D"    # the window width in the same view, printed '50' = plan run C35 0.500002 m
SLAB_TOP_DIM = "29D0"        # the +5.50 level dimension of the same view (5500 from +-0.00): its top = slab top line
SILL_PRINTED_M = 0.84        # '84' printed on the DXF view AND on the PDF NW elevation (chain '84 | 216 | 230')
SILL_SOURCE = {"drawing": "P7757.dxf (Drive 'Alsenan chalet project', P7757_DXF_COMPRESSED.zip)",
               "view": "NORTH WEST ELEVATION (section through the pool court at the plot line), 1F bath window",
               "dimension": "DIMENSION 2EEC printed '84' from the +5.50 slab-top line; PDF Pages_07-08 p.2 '84'"}

# ---- R-T522-2: the ledge's bounding face = the 1F curved bay (T-486 BAY_FACE), split by what stands on it ---------
BAY_PIECES = (("BCD", "SOLID"),             # layer 1, r 1.935, wall end (elevation chain '15' / '20' frame + wall)
              ("BCE", "GLAZING_ON_SLAB"),   # layer 5, r 1.935: its chord = printed '269' (2D53), the arched glazing
              ("BD0", "SOLID"))             # layer 1, r 1.935, wall end (elevation chain '17' / '5')
BAY_GLAZING_CHORD_DIM = "2D53"   # printed '269' (cm): chord of BCE, 2 x 1.935 x sin(88.14 / 2) = 2.692 m (asserted)
BAY_GLAZING_HEIGHT_DIM = "2E97"  # printed '305' from the +5.50 slab-top line to the arch spring: the frame stands on the slab
BAY_SOURCE = {"drawing": "P7757.dxf (Drive 'Alsenan chalet project', P7757_DXF_COMPRESSED.zip)",
              "view": "NORTH WEST ELEVATION: the bay's arched glazing '269' x '305' + '45', drawn down to the slab line",
              "dimension": "DIMENSION 2E97 printed '305' starting on the +5.50 slab-top line; 2D53 '269' = BCE chord; "
                           "PDF Pages_07-08 p.2 the same chain"}

# ---- R-T522-4: the ledge's cover -------------------------------------------------------------------------------------
COVER_LEVELS = ("+5.50", "+9.70")   # printed levels: ledge slab top (LEVEL 1251) and the roof terrace over it (134E..)
COVER_H_LEVEL_M = 4.20              # level to level; the slab soffit is lower by a thickness this slab does not print
COVER_EVIDENCE = ("2F plan (frame offset -44.85 m in x from the 1F frame): the ROOF +9.70 hatch runs to its parapet on "
                  "the 1F wall line with no opening over the bay, the ledge or the void part west of that line; the open "
                  "sky over the court starts at the wall line (T-494 / T-507)")

# ---- the V3.0.58 lines this piece narrows (T-507, research/agents_t507/T-507_EXPOSED_SLAB_WP.md s.6) -------------
V3058 = {
    "L-1954878bb02c91139e1b": ("FIN.WP.ROOF_UPTURN", "lm", "1F-POOLCOURT-550:wp_upturn window_face", 0.0, 0.500002),
    "L-2361d6ec13c952bd2ae3": ("FIN.WP.ROOF", "m2", "1F-POOLCOURT-550-LEDGE:wp_membrane", 0.0, 0.639573),
    "L-d7d1bf8c5991ccf69ea2": ("FIN.WP.ROOF_UPTURN", "lm", "1F-POOLCOURT-550-LEDGE:wp_upturn", 0.0, 3.528277),
}
V3058_TOTALS = {"FIN.WP.ROOF": (209.018867, "m2"), "FIN.WP.ROOF_UPTURN": (186.782544, "lm")}
