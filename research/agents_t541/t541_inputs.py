"""T-541 development-villa inputs: candidate line values and drawing-derived component values only.

No coordinate, drawing content, client name or workbook cell is stored. Drawing by Drive title: "Alsenan chalet
project", P7757_DXF_COMPRESSED.zip -> P7757.dxf (handles named, re-read this run, units mm -> m). The freelancer's row
totals (roof membrane 285.00 m2, roof upturn 194.00 lm) are the figures the board has carried since T-071; this run
read them in his workbook (Drive, same folder, the floors / waterproofing / decor / marble workbook, waterproofing
sheet): one row with a length 194.00 and an area 285.00 and multiplier 1.00, no sub-rows.
"""

FREELANCER_MEMBRANE_M2 = "285.00"
FREELANCER_UPTURN_LM = "194.00"

# Candidate FIN.WP.ROOF / FIN.WP.ROOF_UPTURN valued lines once T-529 / T-536 are wired (WIRING_MANIFEST_V2 s.3):
# V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json) + the five V3.0.58 lines (T-507) at their
# T-529 / T-536 values. 2F-ROOF-TOP (L-3e8fe55da71851816dd4 / L-aac1f35e08f85b643692) stays HELD (Q-34): not valued.
ENGINE_M2 = [
    {"line_id": "L-2f7502be6f501baf49b1", "element": "1F-ROOF-AT216:wp_membrane", "qty": "32.721", "unit": "m2"},
    {"line_id": "L-d57d2dc2fafac8bc72d8", "element": "1F-ROOF-AT220:wp_membrane", "qty": "55.559", "unit": "m2"},
    {"line_id": "L-636fd3ff1784a12e653b", "element": "2F-ROOF-AT379:wp_membrane", "qty": "115.832", "unit": "m2"},
    {"line_id": "L-eff54f96bfcfcf175d58", "element": "1F-POOLCOURT-550:wp_membrane", "qty": "4.906867", "unit": "m2"},
    {"line_id": "L-2361d6ec13c952bd2ae3", "element": "1F-POOLCOURT-550-LEDGE:wp_membrane", "qty": "0.639573", "unit": "m2"},
]
ENGINE_LM = [
    {"line_id": "L-994b88140f2ea50f1b31", "element": "1F-ROOF-AT216:wp_upturn", "qty": "52.94", "unit": "lm"},
    {"line_id": "L-d4c73babd2a275c28929", "element": "1F-ROOF-AT220:wp_upturn", "qty": "35.727", "unit": "lm"},
    {"line_id": "L-5ce5ba49792e8f9d1f6f", "element": "2F-ROOF-AT379:wp_upturn", "qty": "92.922", "unit": "lm"},
    {"line_id": "L-cf8d5ed40b0d546427d6", "element": "1F-POOLCOURT-550:wp_upturn", "qty": "5.193544", "unit": "lm"},
    {"line_id": "L-1954878bb02c91139e1b", "element": "1F-POOLCOURT-550:wp_upturn window_face", "qty": "0.500002", "unit": "lm"},
    {"line_id": "L-d7d1bf8c5991ccf69ea2", "element": "1F-POOLCOURT-550-LEDGE:wp_upturn", "qty": "0.551614", "unit": "lm"},
]

# Drawing values re-read this run (P7757.dxf, mm): +13.90 roof inner parapet faces 12B7 (x0) / 1292 (x0 + 7700) /
# 1279 (y0 + 6450) / 1283 (y0): 7.700 x 6.450 = 49.665000 m2, perimeter 28.300 lm (outer faces 1288 / 1291 / 1274 /
# 1281: 8.100 x 6.800 = 55.08, the printed 2F area). Third dome 1300 (layer 2) r 2.205018498, inside the box, tangent
# to the east inner face: pi r^2 = 15.274758 m2, 2 pi r = 13.854540 lm. +9.70 domes 12EB / 2F33 r 2.211091524:
# 2 x 15.359013 = 30.718026 m2, 2 x 13.892698 = 27.785396 lm.
TOP_ROOF_INNER_M2 = "49.665000"
TOP_ROOF_INNER_LM = "28.300"
THIRD_DOME_M2 = "15.274758"
THIRD_DOME_RING_LM = "13.854540"
DOMES_970_CIRCLE_M2 = "30.718026"
DOMES_970_CIRCLE_LM = "27.785396"
# Engine's own deduction on AT379: T-321 / T-071 gross inside the parapet 146.532 - line 115.832 = 30.700 (polygons);
# its dome rings in the AT379 upturn line: 27.782 (T-071).
ENGINE_DOME_DEDUCTION_M2 = "30.700"
ENGINE_DOME_RINGS_LM = "27.782"

S_DXF = "P7757.dxf handles (re-read T-541)"


def membrane_components():
    pool = "5.546440"  # 4.906867 + 0.639573 (T-507 / T-529 lines)
    return [
        {"name": "2F block top roof +13.90 inside the parapet inner faces, less the third dome (Q-29 skylight)",
         "qty": "34.390242", "unit": "m2", "sign": 1, "cause": "HELD", "source": S_DXF + "; Q-34 parked",
         "note": "49.665000 - 15.274758; engine lines L-3e8fe55d / L-aac1f35e HELD, never 0"},
        {"name": "third dome footprint on the +13.90 roof", "qty": THIRD_DOME_M2, "unit": "m2", "sign": 1,
         "cause": "RULE_DIFFERENCE", "source": S_DXF + " 1300; Q-29 client change (open skylight)",
         "note": "inside the HELD roof; his row does not deduct it (hypothesis H1)"},
        {"name": "two +9.70 dome footprints (circles)", "qty": DOMES_970_CIRCLE_M2, "unit": "m2", "sign": 1,
         "cause": "RULE_DIFFERENCE", "source": S_DXF + " 12EB / 2F33; Q-24 / Q-29",
         "note": "engine stops the membrane at each skylight opening (owner Q-29); a design-scope count keeps it"},
        {"name": "engine arc discretisation of the two +9.70 dome deductions", "qty": "0.018026", "unit": "m2",
         "sign": -1, "cause": "TOLERANCE", "source": "T-321 closure AT379 (146.532 - 115.832 = 30.700 vs circles)",
         "note": "polygon chords; 0.016 % of the line; not a defect"},
        {"name": "pool-court slab +5.50 and its ledge (T-507 / T-529)", "qty": pool, "unit": "m2", "sign": -1,
         "cause": "ENGINE_RIGHT", "source": "candidate lines L-eff54f96 / L-2361d6ec (Checker 4.9069 AGREE)",
         "note": "exposed slab top; his row has no sub-row: whether his lump holds it is not printed"},
    ]


def upturn_components():
    return [
        {"name": "2F block top roof parapet inner faces", "qty": TOP_ROOF_INNER_LM, "unit": "lm", "sign": 1,
         "cause": "HELD", "source": S_DXF + "; T-311 2F 28.300; Q-34 parked", "note": "engine line L-aac1f35e HELD"},
        {"name": "two +9.70 dome rings (circles)", "qty": DOMES_970_CIRCLE_LM, "unit": "lm", "sign": -1,
         "cause": "RULE_DIFFERENCE", "source": S_DXF + " 12EB / 2F33; Q-24 answer (0.20 m round a skylight)",
         "note": "in the engine, not in a basis that keeps the domes in the area"},
        {"name": "engine arc discretisation of the two rings", "qty": "0.003396", "unit": "lm", "sign": 1,
         "cause": "TOLERANCE", "source": "T-071 ring 27.782 vs circles 27.785396", "note": ""},
        {"name": "pool-court upturns, bath-window face and ledge (T-507 / T-529)", "qty": "6.245160", "unit": "lm",
         "sign": -1, "cause": "ENGINE_RIGHT", "source": "candidate lines L-cf8d5ed4 / L-1954878b / L-d7d1bf8c",
         "note": "5.193544 + 0.500002 + 0.551614"},
    ]
