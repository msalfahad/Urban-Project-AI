"""T-546 development-villa inputs: candidate line values, the freelancer's per-room cells (numbers only, by sheet row)
and drawing-derived component values. No coordinate, client name or workbook text is stored.

Candidate: ARCH_TAKEOFF_V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json); V3.0.58 (T-507) changed
only five roof lines, so FIN.WP.FLOOR / FIN.WP.WALL_UPTURN are the same on the candidate of record V3.0.58.
Freelancer: his floors / waterproofing workbook (Drive "Alsenan chalet project"), waterproofing sheet rows 14-36, as
parsed in tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json: per room C = perimeter, D = floor area, F = 1
('height' column), G = C x F, H = D; H39 = SUM(H14:H36) = 72.01 (floors), G40 = SUM(G14:G38) = 144.61, and the summary
row H51 = G43 + G40 labels the upturn unit 'm.l' (lm): his multiplier 1 is not a height, his upturn is a length.
Hand basis per room: T-074 hand table (MERGED; own polygonization + printed dimensions; T-010 verifier reproduction
72.121 m2 / 144.727 lm), T-303 open edges, T-310 pantry column ruling; pantry handles re-read this run (test).
"""

FREELANCER_FLOOR_M2 = "72.01"   # H39
FREELANCER_UPTURN_LM = "144.61"  # G40, summary unit lm
V3041_FLOOR_M2 = "85.620710"     # scoreboard 85.621 (V3.0.41: pantry 13.500 before T-310)
UPTURN_H = "0.20"                # UP-WP-002 2.0.0, owner Q-03 (the engine's own rule height)
UPTURN_H_SRC = "UP-WP-002 2.0.0 / owner Q-03 (engine rule height of the m2 upturn lines)"

T074 = "T-074 hand table (MERGED)"
# room key, floor line id + value, upturn line id + value (m2) or None (HELD), freelancer sheet row, his D / C cells,
# hand boundary lm (T-074), doorway widths (UP-WP-002: own HELD rows), open edges without wall (T-303 / T-074).
ROOMS = [
    ("GF lobby wash (2 basins)", "L-e37ce315bbb83a4630cf", "4.730695", None, None, 14, "4.73", "9.5", "9.5002", ["0.80", "0.80"], [("lobby to stair hall, no wall", "1.256")]),
    ("GF basin space by the stair", "L-514c78e25600e261a37c", "1.485", None, None, 15, "1.7", "5.3", "4.9", ["0.80"], [("basin space to passage, no wall", "0.90")]),
    ("GF master bath", "L-538c929be1d81708f09f", "3.717683", None, None, 16, "3.7", "7.6", "7.6245", ["0.80"], []),
    ("GF core W.C. 245 x 167 (wedge)", "L-875de0625f00bf4128fc", "2.36761", None, None, 17, "2.3", "6.7", "6.8098", ["0.80"], []),
    ("GF core W.C. 289 x 167 (wedge)", "L-ed8d62f6e695b361d8f6", "2.675221", None, None, 18, "2.67", "7.4", "7.414", ["0.80"], []),
    ("GF stair-core W.C. 175 x 135", "L-3e5759e5282160f313b6", "2.3625", None, None, 19, "2.36", "6.2", "6.2", ["0.80"], []),
    ("GF kitchen", "L-2c557dad8748a2c2848b", "9.630001", None, None, 20, "9.55", "14.35", "14.5", ["1.00"], []),
    ("GF driver W.C.", "L-81e5c35fcaba34dd8e3e", "1.95", None, None, 21, "1.95", "5.58", "5.6", ["0.80"], []),
    ("GF W.C. by the reception room", "L-d7899629d78501dc3b66", "3.375", None, None, 22, "3.37", "7.5", "7.5", ["0.80"], []),
    ("GF wash by the reception room", "L-0c6db650bad175d34abb", "3.1325", None, None, 23, "3.15", "7.2", "7.2", ["0.80"], [("arch to the reception room, no leaf, no wall", "1.00")]),
    ("1F east bath 210 x 225", "L-ef429ae8e32c8b5cc641", "4.725", None, None, 27, "4.72", "8.7", "8.7", ["0.80"], []),
    ("1F bath by the laundry", "L-6477c7ef451aae374ecc", "3.5775", None, None, 28, "3.6", "7.6", "7.6", ["0.80"], []),
    ("1F W.C. by the laundry", "L-75a5ef579ff6ffa1cf0a", "2.646", None, None, 29, "2.59", "6.48", "6.54", ["0.80"], []),
    ("1F west bath A 245 x 205", "L-790a3049c29eda7dad2a", "5.0225", None, None, 30, "5", "9", "9.0", ["0.80"], []),
    ("1F west bath B 245 x 205", "L-f15325df772daa7ceec0", "5.0225", None, None, 31, "5", "8.9", "9.0", ["0.80"], []),
    ("1F laundry", "L-66501a74bc489a80d283", "10.151", None, None, 32, "10", "16.85", "16.94", ["0.90", "0.80"], []),
    ("2F roof-floor W.C. 300 x 185", "L-bed47a63708c41b2b150", "5.55", None, None, 36, "5.62", "9.75", "9.7", ["0.80"], []),
    ("GF pantry (wet zone, Q-37 A)", "L-f32abcdb3b4db6877c64", "13.455", None, None, None, None, None, None, [], []),
]
# engine upturn lines (m2) by room key; the pantry's is HELD (open side 4.49 m and its door not bound, T-303 / T-310)
UPTURN = {
    "GF lobby wash (2 basins)": ("L-519ae15dd6ff755f4aa5", "1.32864"),
    "GF basin space by the stair": ("L-017f9184994017c8a62b", "0.640592"),
    "GF master bath": ("L-8b981cb63e87f18b13d4", "1.364933"),
    "GF core W.C. 245 x 167 (wedge)": ("L-60d7c01f386770e2bf9c", "1.20102"),
    "GF core W.C. 289 x 167 (wedge)": ("L-0226eb38b2c6469296df", "1.322808"),
    "GF stair-core W.C. 175 x 135": ("L-8dd259ad89d2cd276ad2", "1.080592"),
    "GF kitchen": ("L-f77fe27244893dc1cc9b", "2.7"),
    "GF driver W.C.": ("L-31877d6c1cb33b74e5a7", "0.96"),
    "GF W.C. by the reception room": ("L-6c277fc130b921a7f83e", "1.34"),
    "GF wash by the reception room": ("L-5362cff3511074da962a", "1.08"),
    "1F east bath 210 x 225": ("L-60f100105399a9bdfb08", "1.58"),
    "1F bath by the laundry": ("L-a93486d24647a9e14445", "1.36"),
    "1F W.C. by the laundry": ("L-ace6533512ada47d1352", "1.148"),
    "1F west bath A 245 x 205": ("L-ba15212ec9887e6d4f73", "1.64"),
    "1F west bath B 245 x 205": ("L-6e6daedebef2db6a83bd", "1.64"),
    "1F laundry": ("L-2d478a44f042f938e4e7", "3.048"),
    "2F roof-floor W.C. 300 x 185": ("L-b842beb71b67af783cd7", "1.78"),
    "GF pantry (wet zone, Q-37 A)": ("L-8090ff20f2b547d1bc96", None),
}

# Floor causes per room (engine - freelancer), basis = hand reading, never his figure.
FLOOR_CAUSES = {
    "GF lobby wash (2 basins)": [("2-dp rounding", "0.000695", 1, "TOLERANCE", T074 + ": 10-edge trace 4.732")],
    "GF basin space by the stair": [
        ("passage reveal 0.20 x 1.10 taken into his room (1.55 x 1.10)", "0.220", -1, "RULE_DIFFERENCE",
         T074 + ": printed 110 x 135; the reveal is the doorway / threshold piece (UP-WP-003), not room floor"),
        ("his 1.705 truncated to 2 dp", "0.005", 1, "TOLERANCE", "arithmetic of the reveal reading")],
    "GF master bath": [("diagonal-wall corner 0.983 x 0.982 / 2 out of 2.10 x 2.00", "0.017683", 1, "ENGINE_RIGHT",
                        T074 + ": 4.200 - 0.483 = 3.717 on the drawn faces")],
    "GF core W.C. 245 x 167 (wedge)": [("wedge room by shoelace on the drawn wall faces", "0.06761", 1, "ENGINE_RIGHT",
                                        T074 + ": 2.368 m2 / 6.810 lm")],
    "GF core W.C. 289 x 167 (wedge)": [("2-dp truncation", "0.005221", 1, "TOLERANCE", T074 + ": shoelace 2.675")],
    "GF stair-core W.C. 175 x 135": [("2-dp truncation", "0.0025", 1, "TOLERANCE", T074 + ": printed 175 x 135")],
    "GF kitchen": [("printed 300 x 270 + 105 x 150 less two drawn piers 0.045", "0.080001", 1, "ENGINE_RIGHT",
                    T074 + ": 9.675 - 0.045 = 9.630 (0.000001 polygon); his 9.55 has no derivation")],
    "GF driver W.C.": [],
    "GF W.C. by the reception room": [("2-dp truncation", "0.005", 1, "TOLERANCE", T074 + ": printed 150 x 225")],
    "GF wash by the reception room": [("column corner out of the printed 150 x 210", "0.0175", -1, "ENGINE_RIGHT",
                                       T074 + " + T-310 ruling: a column is not floor (membrane turns up its face)")],
    "1F east bath 210 x 225": [("2-dp truncation", "0.005", 1, "TOLERANCE", T074 + ": printed 210 x 225")],
    "1F bath by the laundry": [("drawn jamb 0.45 x 0.05 out of 2.00 x 1.80", "0.0225", -1, "ENGINE_RIGHT",
                                T074 + ": 3.600 - 0.0225 on the drawn faces")],
    "1F W.C. by the laundry": [("printed 180 x 147 against his 1.80 x 1.44", "0.056", 1, "ENGINE_RIGHT", T074 + ": 2.646")],
    "1F west bath A 245 x 205": [("printed 245 x 205 against his 5.00", "0.0225", 1, "ENGINE_RIGHT", T074 + ": 5.0225")],
    "1F west bath B 245 x 205": [("printed 245 x 205 against his 5.00", "0.0225", 1, "ENGINE_RIGHT", T074 + ": 5.0225")],
    "1F laundry": [("printed 347 x 300 / 185 with the W.C. corner, against his typed 10.00", "0.151", 1, "ENGINE_RIGHT",
                    T074 + ": 5.550 + 1.701 + 1.764 + 1.136 = 10.151")],
    "2F roof-floor W.C. 300 x 185": [("printed 185 against his 1.875", "0.07", -1, "ENGINE_RIGHT", T074 + ": sheet 5, 300 x 185 = 5.550")],
    "GF pantry (wet zone, Q-37 A)": [("pantry box 4.50 x 3.00 less the column edge 0.900 x 0.050", "13.455", 1, "RULE_DIFFERENCE",
                                      "owner Q-37 A (pantry wet) + T-310 (P7757 AE / B3 / A6 / 158, DIMENSIONs 5D5 / 5E1, column 2FAE); "
                                      "he keeps the pantry in his dry reception row (T-153)")],
}


def floor_rows():
    rows = []
    for key, lid, q, _u, _x, frow, fd, _fc, _b, _doors, _open in ROOMS:
        rows.append({"room": key, "engine_lines": [{"line_id": lid, "qty": q, "unit": "m2"}],
                     "freelancer": fd, "freelancer_row": frow,
                     "components": [{"name": n, "qty": v, "sign": s, "cause": c, "basis": b}
                                    for n, v, s, c, b in FLOOR_CAUSES[key]]})
    return rows


def upturn_rows():
    """lm table. Per room, engine lm - his perimeter = - doorway segments (HELD: their own rows, transition detail not
    printed) - open edges without wall (Q-35 C walls only; a termination, not an upturn) + (hand boundary - his cell)
    + (engine run - (hand boundary - segments)) closure tolerance (T-303 item 6)."""
    from decimal import Decimal
    rows = []
    for key, _lid, _q, _u, _x, frow, _fd, fc, b, doors, opens in ROOMS:
        lid, m2 = UPTURN[key]
        line = {"line_id": lid, "qty": m2, "unit": "m2", "rule_height": UPTURN_H, "height_source": UPTURN_H_SRC}
        if m2 is None:
            line = {"line_id": lid, "qty": None, "unit": "m2", "state": "HELD"}
            rows.append({"room": key, "engine_lines": [line], "freelancer": None,
                         "note": "upturn HELD: open side 4.49 m and the pantry door not bound (T-303 / T-310); not in his list"})
            continue
        comps = []
        for w in doors:
            comps.append({"name": f"doorway segment {w} m", "qty": w, "sign": -1, "cause": "HELD",
                          "basis": "UP-WP-002 2.0.0 / T-310 policy V3: each doorway segment its own row, HELD (detail not printed)"})
        for n, v in opens:
            comps.append({"name": n, "qty": v, "sign": -1, "cause": "RULE_DIFFERENCE",
                          "basis": "Q-35 C (upturn on walls only); T-303 open edges / T-074 trace"})
        bd = Decimal(b) - Decimal(fc)
        if bd:
            if key == "GF basin space by the stair":
                cause, basis = "RULE_DIFFERENCE", T074 + ": he takes the 0.20 reveal in (2 x 0.20 m)"
            elif abs(bd) < Decimal("0.010"):
                cause, basis = "TOLERANCE", T074 + " hand boundary " + b
            else:
                cause, basis = "ENGINE_RIGHT", T074 + " hand boundary " + b + " (printed / drawn faces)"
            comps.append({"name": "boundary: hand reading vs his perimeter", "qty": str(abs(bd)),
                          "sign": 1 if bd > 0 else -1, "cause": cause, "basis": basis})
        seg = sum((Decimal(w) for w in doors), Decimal(0)) + sum((Decimal(v) for _n, v in opens), Decimal(0))
        cl = Decimal(m2) / Decimal(UPTURN_H) - (Decimal(b) - seg)
        if cl:
            comps.append({"name": "engine run vs hand boundary less segments (closure / door block width)",
                          "qty": str(abs(cl)), "sign": 1 if cl > 0 else -1, "cause": "TOLERANCE",
                          "basis": "T-303 item 6 named residuals; drawn door block width vs walked jamb gap"})
        rows.append({"room": key, "engine_lines": [line], "freelancer": fc, "freelancer_row": frow, "components": comps})
    return rows


def engine_floor_total():
    from decimal import Decimal
    return str(sum((Decimal(r[2]) for r in ROOMS), Decimal(0)))


def engine_upturn_lm_total():
    from decimal import Decimal
    return str(sum((Decimal(v) / Decimal(UPTURN_H) for _l, v in UPTURN.values() if v is not None), Decimal(0)))
