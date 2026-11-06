"""T-547 development-villa inputs (numbers only: no coordinate, client name or workbook text).

Candidate: ARCH_TAKEOFF_V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json); T-507's V3.0.58 moved only
roof waterproofing lines, so the 18 FIN.WALL.TILE lines are the same on the candidate of record V3.0.58: 12 valued =
340.3038 m2, 6 HELD blank (unchanged since V3.0.21, T-315).
Faces, open sides and openings: the Checker-verified T-312 face ledger (research/agents_t312: ROOM_CLOSURE_T312.csv,
OPENINGS_T312.csv), which the V3.0.21 lines were built from.
Freelancer: his finishes workbook (Drive "Alsenan chalet project"), ceramic sheet, wet-room block rows 42-63: per room
C = length (lm), F = 3 (height), G = C x F (m2), G66 = SUM = 433.83, carried to H72 'walls' m2 and to the cover sheet
(B17); parsed in tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (file FIN). His F is a height here: his summary
unit is m2 (contrast T-546, where the same multiplier gave lm).
"""
from __future__ import annotations

ENGINE_TOTAL = "340.3038"
FREELANCER_TOTAL = "433.83"   # G66 = H72 (m2)
HIS_H = "3"

GF_H = "3.65"   # owner formula 4.50 - 0.60 - 0.15 - 0.10 (Q-43 / Q-48 A, OWNER_RECONCILIATION G1)
UP_H = "3.35"   # 4.20 - 0.85
H_BASIS = {"3.65": "Q-48 A tile to the decor-ceiling underside; owner formula 4.50 - 0.85 = 3.65 (G1)",
           "3.35": "Q-48 A tile to the decor-ceiling underside; owner formula 4.20 - 0.85 = 3.35 (G1)"}
FACE = "T-312 face ledger (Checker-verified): printed / drawn faces, room closure 0.0000 m"


def door(w, id_=""):
    return {"id": id_, "kind": "door", "w": w, "sill": "0", "head": "2.20"}   # Q-55 C


def win(w, sill, head, id_=""):
    return {"id": id_, "kind": "window", "w": w, "sill": sill, "head": head}  # T-201 heads


W60 = ("0.6", "1.7", "2.5")

VALUED = [
    # room, line id, line value, his sheet row, his length, face, H, open lm, openings
    ("GF-12 core W.C. wedge 289 x 167", "L-c34694477f67800ae2e3", "25.3011", 46, "7.4", "7.414", GF_H, "0", [door("0.8", "D-GF-11")]),
    ("GF-13 core W.C. wedge 245 x 167", "L-a3cb2c8a9b6080769ebc", "22.6165", 45, "6.7", "6.81", GF_H, "0", [door("0.8", "D-GF-12"), win(*W60, "W06")]),
    ("GF-14 wash lobby, 2 basins", "L-fa408571a8adcfaf1a1f", "26.6544", 42, "9.5", "8.267", GF_H, "1.245", [door("0.8", "D-GF-11"), door("0.8", "D-GF-12")]),
    ("GF-16 master bath", "L-ca4e74c59364f665b102", "25.5912", 44, "7.6", "7.625", GF_H, "0", [door("0.8", "D-GF-14"), win(*W60, "W07")]),
    ("1F-02 west bath upper 245 x 205", "L-a34d09209fb5aad3eb63", "27.9101", 58, "9", "9.0", UP_H, "0", [door("0.8", "D-1F-04"), win(*W60, "W20")]),
    ("1F-03 west bath lower 245 x 205", "L-88ed2535c1975adb702e", "27.9100", 59, "8.9", "9.0", UP_H, "0", [door("0.8", "D-1F-01"), win(*W60, "W19")]),
    ("1F-07 laundry", "L-b2077eee5a71a975bd74", "52.5290", 60, "16.85", "16.94", UP_H, "0", [door("0.8", "D-1F-06"), door("0.9", "D-1F-05"), win(*W60, "W21")]),
    ("1F-08 W.C. 147 x 180", "L-1090bb5c8226afec2235", "19.6691", 57, "6.48", "6.54", UP_H, "0", [door("0.8", "D-1F-06"), win(*W60, "W22")]),
    ("1F-09 bath by the laundry", "L-086e72207311265f81ab", "23.2201", 56, "7.6", "7.6", UP_H, "0", [door("0.8", "D-1F-07"), win(*W60, "W23")]),
    ("1F-12 east bath 210 x 225", "L-82cd58d4a16fb94ddfc6", "26.3051", 55, "8.7", "8.7", UP_H, "0", [door("0.8", "D-1F-10"), win("0.5", "0.84", "3.0", "W18")]),
    ("2F-02 roof-floor W.C. 300 x 185", "L-065bafe1b98e3a43881c", "30.2550", 63, "9.75", "9.7", UP_H, "0", [door("0.8", "D-2F-03"), win(*W60, "W28")]),
]

PANTRY = ("GF-07 open pantry (wet, Q-37 A)", "L-f5c5a1a9c9ee2b644cb5", "32.3422")

ANNEX_HI = {"H": "3.15", "source": "OWNER-METHOD UPPER END: owner formula with +4.30 as the highest possible structural "
                                   "datum, (4.30 - 0.30) - 0.85 = 3.15; a finished-roof reading of +4.30 (Q-54 B) can "
                                   "only lower the slab, never raise it"}
HEAD_LO = ("PHYSICAL LOWER END: the decor ceiling runs above the highest opening head in the room's walls "
           "(door head 2.20 Q-55 C ASSUMED - OWNER-APPROVED; window heads T-201)")
LV_LO = "OWNER-METHOD, floor +1.00 (house level): 5.50 - 1.00 - 0.85 = 3.65"
LV_HI = ("OWNER-METHOD, floor +0.30 (court level) under the 1F floor +5.50: 5.20 - 0.85 = 4.35; a sunken or stair "
         "element above (not overlaid for these rooms) can only lower it")
W05_LO = "; W05 absolute +2.70 / +3.50 (T-201) -> sill 1.70 / head 2.50 above the floor"
W05_HI = "; W05 -> sill 2.40 / head 3.20 above the floor"
ANNEX_FACT = "annex tile top not established: +4.30 is a roof mark (G2; owner Q-54 B HOLD; D-39)"
LEVEL_FACT = "room floor level +0.30 or +1.00 not drawn (T-088; passage opens on the stair hall between both marks)"

HELD = [
    # room, line id, his row, his length, face, openings, lo spec, hi spec, fact
    ("GF-02 wash by the dewaneya", "L-d0858b30e0ea869bd047", 51, "7.2", "7.2",
     [door("0.8", "D-GF-02"), {"id": "A-GF-01", "kind": "arch", "w": "1.0", "sill": "0", "head": None,
                               "head_lo": "0", "head_hi": "3.15"}],
     {"H": "2.20", "source": HEAD_LO}, ANNEX_HI, ANNEX_FACT + "; arch A-GF-01 head not printed (0 .. full band)"),
    ("GF-03 W.C. by the dewaneya", "L-96d9839bd3bca4c08a67", 50, "7.5", "7.5", [door("0.8", "D-GF-02")],
     {"H": "2.20", "source": HEAD_LO}, ANNEX_HI, ANNEX_FACT),
    ("GF-05 driver W.C.", "L-88c11c5d8dc1dfd7c27e", 49, "5.58", "5.6", [door("0.8", "D-GF-04")],
     {"H": "2.20", "source": HEAD_LO}, ANNEX_HI, ANNEX_FACT),
    ("GF-06 kitchen", "L-c330b8dc47261d5ada7e", 48, "14.35", "14.5",
     [door("1.0", "D-GF-05"), win("1.501", "1.0", "2.5", "W08")],
     {"H": "2.50", "source": HEAD_LO + ": W08 head 2.50 above +0.30"}, ANNEX_HI, ANNEX_FACT),
    ("GF-10 W.C. 175 x 135 by the stair", "L-1341e0410a469089c3be", 47, "6.2", "6.2", None,
     {"H": "3.65", "source": LV_LO + W05_LO, "openings": [door("0.8", "D-GF-10"), win("0.6", "1.70", "2.50", "W05")]},
     {"H": "4.35", "source": LV_HI + W05_HI, "openings": [door("0.8", "D-GF-10"), win("0.6", "2.40", "3.20", "W05")]},
     LEVEL_FACT),
    ("GF-11 basin space 110 x 135", "L-de4088e7012e655bb071", 43, "5.3", "4.9",
     [door("0.8", "D-GF-10"), {"id": "P-GF-01", "kind": "doorway", "w": "0.9", "sill": "0", "head": None,
                               "head_lo": "0", "head_hi": "4.35"}],
     {"H": "3.65", "source": LV_LO + "; doorway P-GF-01 (no leaf, head not printed) at the full band"},
     {"H": "4.35", "source": LV_HI + "; doorway P-GF-01 head 0"}, LEVEL_FACT + "; doorway P-GF-01 head not printed"),
]

PRINTED_DIMS = {  # DIMENSION handles on P7757.dxf (ab54dd55) that print the HELD rooms' sizes (own read this run)
    "GF-10": [("726", 1750), ("749", 1350)], "GF-11": [("70F", 1100), ("749", 1350)],
    "GF-05": [("61E", 1300), ("658", 1500)], "GF-03": [("5A4", 2250), ("551", 1500)],
    "GF-02": [("5BD", 2100), ("551", 1500)], "GF-06": [("523", 2700), ("635", 3000), ("641", 1050)],
}


def rows() -> list[dict]:
    out = []
    for room, lid, line, frow, C, F, H, opn, ops in VALUED:
        out.append({"kind": "VALUED", "room": room, "line_id": lid, "line": line, "his_row": frow, "his_len": C,
                    "his_h": HIS_H, "face": F, "H": H, "open_lm": opn, "openings": ops, "h_basis": H_BASIS[H],
                    "face_basis": FACE, "open_basis": "T-312 / T-128 walk: 1.245 m open side to the stair hall, no wall"})
    room, lid, line = PANTRY
    out.append({"kind": "SCOPE", "room": room, "line_id": lid, "line": line, "cause": "RULE_DIFFERENCE",
                "basis": "owner Q-37 A (pantry wet) + UP-PANTRY-003 host walls full height (T-312 / T-315); he keeps "
                         "the pantry in his dry reception row (T-153 / T-546)"})
    for room, lid, frow, C, F, ops, lo, hi, fact in HELD:
        out.append({"kind": "HELD", "room": room, "line_id": lid, "line": None, "his_row": frow, "his_len": C,
                    "his_h": HIS_H, "face": F, "openings": ops or [], "bound_lo": lo, "bound_hi": hi, "held_fact": fact})
    return out


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from t547_wall_tile_reconcile import reconcile
    res = reconcile(rows=rows(), engine_total=ENGINE_TOTAL, freelancer_total=FREELANCER_TOTAL)
    print(json.dumps(res, indent=1, ensure_ascii=False))
