"""T-553 development-villa inputs: candidate floor tile lines by element id (values read from the pinned line index,
never typed), the freelancer's floor cells (numbers only, by sheet row) and the drawing / ledger basis of each
component. No coordinate, client name or workbook text is stored.

Candidate: ARCH_TAKEOFF_V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json, sha256 pinned below);
V3.0.58 (T-507) changed only five roof waterproofing lines, so every floor tile line is the same on the candidate of
record V3.0.58 (and has been since V3.0.45: 58 lines, 387.094050 m2, identical in every index V3.0.45 .. V3.0.57).
Freelancer: his floors workbook (Drive "Alsenan chalet project"), tiles sheet, as parsed in
tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json: dry rows 13-29 (column D = m2, C = perimeter lm), D31 =
SUM(D13:E29) = 337.57; wet rows 42-63 (H = D), H65 = SUM = 72.01; H70 = H65 + D31 = 409.58 m2 'floors' (cover sheet
B15, unit m2). No multiplier, no waste column on any floor row (installed m2). No tile size on any row; the drawings
print none (R-T455-3: 276 DXF texts, 0 tile size notes) -> every row TILE_SIZE_NOT_GIVEN on both sides.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
INDEX_SHA = "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738"
CANDIDATE = "ARCH_TAKEOFF_V3.0.58 (floor tile lines = V3.0.57 index)"
FREELANCER_TOTAL = "409.58"   # tiles sheet H70 = H65 72.01 + D31 337.57
FREELANCER_DRY, FREELANCER_WET = "337.57", "72.01"

# owner (other-trade) lines named by components (full ids, checked against the index by the tests)
OWN = {
    "gf_stair_footprint": "L-6485382cd3b6f09c192c",   # ARCH.SPACE HELD 6.124412: round-stair footprint, treads B7
    "lift_gf": "L-c32effca1d7eae7f36f8", "lift_1f": "L-9840d1da235dd7583427", "lift_2f": "L-eba7ac43f3fce9bbd0b5",
    "garden_band": "L-5431fa278fbb44816a08",          # ARCH.EXTERIOR 9.101 (D-48 planter or floor)
    "band_curb": "L-554a525edce9a9235bee",            # ARCH.SPACE HELD 0.604 (D-48)
    "arrival_1f": "L-8011889d84788553a6b1",           # FIN.MARBLE.LANDING 4.9225 (Q-66 B)
    "arrival_2f": "L-5d2be30dd8d2ffeacc42",           # FIN.MARBLE.LANDING HELD 0 .. 9.225 (Q-70 A; holds 4.875)
}

T074 = "T-074 hand table (MERGED; printed sizes) as restated in T-546"
GF, F1, F2 = "GF", "1F", "2F"


def comp(name, qty, sign, cause, basis, owned_by=None):
    c = {"name": name, "qty": qty, "sign": sign, "cause": cause, "basis": basis}
    if owned_by:
        c["owned_by"] = OWN[owned_by]
    return c


# (room, floor, engine element ids, his cells [(row, m2)], his class, components, note)
DRY = [
    ("GF open room: dining / reception / saloon / entrance zone / open pantry (his reception + dining and entrance rows)",
     GF, ["GF-RC99C2A:floor", "HL:FLOOR_SCOPE:UNDER_STAIR:GF:GF-RC99C2A-UNDER-STAIR", "GF-RFD4E1D:SOUTH-FACADE-DINING",
          "HL:FLOOR_SCOPE:TO_WET:GF:GF-OP-003-NO-OPENING:pantry", "HL:FLOOR_SCOPE:WET:GF:SITE-0a31aaa10796d33a",
          "HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC06FED", "HL:FLOOR_SCOPE:WET:GF:GF-PANTRY-RC99C2A-PART"],
     [(13, "137.5"), (15, "10.46")], "DRY",
     [comp("round-stair footprint below the cut (treads are B7 marble)", "6.124412", -1, "RULE_DIFFERENCE",
           "UP-CER-001 (stair footprint out of the tile) + UP-STAIR-005; T-341 / T-345: face 126.927696 - treads "
           "8.194412 + under-stair floor 2.07 kept", "gf_stair_footprint"),
      comp("lift landing threshold, certain floor part 1.000 x 0.300", "0.300", -1, "RULE_DIFFERENCE",
           "UP-ELEV-005 / T-413 + T-421 s.2 (B6-07 owns it; 0 .. 0.200 more HELD by position)", "lift_gf"),
      comp("garden band x 6.80 .. 13.82, 7.02 x 1.30 - column notch 0.025", "9.101", -1, "HELD",
           "designer D-48 (planter or floor); T-427 s.2 drawn ends 310 / 30F; bound: 0 .. +9.101 m2 of tile",
           "garden_band"),
      comp("garden band curb strip 3.02 x 0.20", "0.604", -1, "HELD", "D-48 with the band (T-427 s.2)", "band_curb"),
      comp("wall 2.65 x 0.20 + columns 0.80 x 0.25 + 0.60 x 0.25 inside his gross outline", "0.880", -1,
           "ENGINE_RIGHT", "T-427 s.2-3: not floor; his rows re-add to the gross outline (T-147 147.90)"),
      comp("his two rows above the drawn outline", "0.302303", -1, "UNRESOLVED",
           "T-427 s.3: own polygonization 147.658 vs his 147.96; 0.1901 lobby-mouth strip (RFI-B-A10 (c)) would "
           "leave 0.1122; his rows carry no dimensions")],
     "pantry floor 13.454868 m2 is WET tile in the engine (Q-37 A) and inside his dry reception row: CLASS MOVE, "
     "no area effect (both tile it); T-286 closure 13.500 - 0.045 column - 0.000132 CAD"),
    ("GF dewaneya 400 x 630 less the R1.10 corner", GF, ["GF-R7512EA:floor"], [(16, "24.84")], "DRY",
     [comp("printed 4.00 x 6.30 - (1.21 - pi 1.21 / 4) = 24.9403 (DXF dims 568 / 57F re-read this run)", "0.100332",
           1, "ENGINE_RIGHT", "T-153 s.3 + own DXF read (DIMENSIONs 4000 / 6300); his 24.84 has no derivation")], ""),
    ("GF master bed room", GF, ["GF-R75FBAE:floor"], [(14, "16.66")], "DRY",
     [comp("drawn room face (V2.9 face 16.5496; T-147 own region 16.557)", "0.11036", -1, "ENGINE_RIGHT",
           "two drawing routes within 0.0074 m2 (T-153 / T-147); north face 4.82 printed (DIMENSION 890), "
           "4.00 printed (7B0); his 16.66 typed, no dimensions")], ""),
    ("GF driver room 175 x 450", GF, ["GF-R51E127:floor"], [(17, "7.87")], "DRY",
     [comp("his 7.875 truncated to 2 dp", "0.005", 1, "TOLERANCE", "printed 1.75 x 4.50 (DIMENSIONs 53A / 5C9)")], ""),
    ("GF stair room: hall at +1.00 and back-door lobby at +0.30 (material HELD: porcelain or landing marble)", GF,
     ["GF-R31F8AE:GF-ST-HALL", "GF-R31F8AE:GF-ST-LOBBY030", "GF-R31F8AE:GF-ST-CN"], [], None,
     [comp("stair-room floor parts in none of his floor rows", "6.1275", 1, "UNRESOLVED",
           "T-418 / T-421 (4.805 + 1.3225, DRAWING-CONFIRMED); T-427 s.3 / T-490: his 6.20 main-stair landing "
           "(marble sheet) has no breakdown; a match by figure is refused")],
     "GF-ST-CN HELD 0 .. 0.23 outside both totals"),
    ("GF doorway strips OP-010 (0.20) + OP-012 (0.15)", GF, ["GF-STRIP-OP-010:doorway strip",
                                                            "GF-STRIP-OP-012:doorway strip"], [], None,
     [comp("porcelain strips in door openings between dry rooms", "0.35", 1, "RULE_DIFFERENCE",
           "UP-THR-001 dry / T-240 / T-218 s.2 (one strip, one line); he measures rooms to the wall face")], ""),
    ("1F living / open stair hall", F1, ["1F-R78C367:floor"], [(21, "38.96")], "DRY",
     [comp("main-stair arrival +5.50 (marble, own line)", "4.9225", -1, "RULE_DIFFERENCE",
           "Q-66 B + UP-STAIR-005; printed 2.50 x 1.95 = 4.875 + 0.0475 (T-240 / T-269)", "arrival_1f"),
      comp("lift landing threshold, certain floor part", "0.300", -1, "RULE_DIFFERENCE", "UP-ELEV-005 / T-421 s.2",
           "lift_1f"),
      comp("his unsplit row vs porcelain 33.711036 + arrival 4.9225", "0.326464", -1, "UNRESOLVED",
           "T-345 s.6 / T-269: hand range 38.588 .. 38.990, his single row not split")], ""),
    ("1F curved east bed room with its lobby (his 'bed room 1')", F1, ["1F-R3CFCFD:floor"], [(22, "17.29")], "DRY",
     [comp("no reading reproduces his 17.29", "1.726545", 1, "UNRESOLVED",
           "T-218 s.3: room to the curved face 15.062 + strip 0.195 + lobby 3.761; drawn 15.062, rectangle 16.80, "
           "3.45 x 4.00 + lobby 17.58 all tried; his row typed")], ""),
    ("1F bed room 380 x 430 + dressing 165 x 180 + arch strip OP-011 (his 'bed room 2')", F1,
     ["1F-R0E919A:floor", "1F-STRIP-OP-011:doorway strip"], [(23, "19.46")], "DRY",
     [comp("dressing 1.65 x 1.80 has NO floor tile line (only ARCH.SPACE L-390e3b9f 2.970)", "2.970", -1,
           "ENGINE_WRONG", "T-223 / T-240 (area VERIFIED 2.970, DRY, material HELD); R-T553-1 (g) join; his 19.46 = "
           "16.340 + 2.970 + 0.150 and his perimeter 21.40 match exactly (T-218 two-key pairing)")], ""),
    ("1F bed room 500 x 365", F1, ["1F-RED0D19:floor"], [(24, "18.25")], "DRY",
     [comp("drawn column notch 0.035", "0.034999", -1, "ENGINE_RIGHT",
           "T-218 s.3: printed 5.00 x 3.65 = 18.25 less the drawn notch; a column is not floor")], ""),
    ("1F west bed room 425 x 450", F1, ["1F-RB72F22:floor"], [(25, "19")], "DRY",
     [comp("printed 4.25 x 4.50 = 19.125 less drawn column notches 0.075 vs his typed 19.00", "0.05", 1,
           "ENGINE_RIGHT", "T-153 / T-218 s.3")], ""),
    ("1F doorway strips OP-005 / OP-006 (0.135 each), OP-020, D-1F-03 (0.15 each)", F1,
     ["1F-STRIP-OP-005:doorway strip", "1F-STRIP-OP-006:doorway strip", "1F-STRIP-OP-020:doorway strip",
      "1F-THRESHOLD-D-1F-03:doorway strip"], [], None,
     [comp("porcelain strips in dry door openings", "0.57", 1, "RULE_DIFFERENCE", "UP-THR-001 dry / T-218 s.2")], ""),
    ("2F maid room 300 x 645", F2, ["2F-R1DB2D2:floor"], [(28, "19.58")], "DRY",
     [comp("printed 3.00 x 6.45 = 19.350 vs his typed 19.58", "0.229999", -1, "ENGINE_RIGHT",
           "T-147 s.6 / T-153: printed 300 x 645; 0.000001 polygon")], ""),
    ("2F lobby beyond the stair width (his 'corridor')", F2, ["2F-R4D1B62:2F-ST-LOBBY"], [(29, "7.7")], "DRY",
     [comp("main-stair arrival +9.70, printed 2.50 x 1.95 (marble)", "4.875", -1, "RULE_DIFFERENCE",
           "Q-70 A (condition met, T-129) + UP-STAIR-005; held inside the 2F landing line (T-490 F-1)", "arrival_2f"),
      comp("lift landing threshold, certain floor part", "0.300", -1, "RULE_DIFFERENCE", "UP-ELEV-005 / T-421 s.2",
           "lift_2f"),
      comp("his 7.70 vs the printed 450 x 195 lobby", "0.325", -1, "UNRESOLVED",
           "T-427 / T-153: (4.50 - 2.50) x 1.25 = 2.500 gross; 1.400 of wall inside the printed 450 x 195; his row "
           "has no dimensions")], ""),
    ("2F doorway strip OP-007 (stair room / maid room)", F2, ["2F-STRIP-OP-007:doorway strip"], [], None,
     [comp("porcelain strip 0.90 x 0.20", "0.18", 1, "RULE_DIFFERENCE", "UP-THR-001 dry / T-218 s.2")], ""),
]

# wet rooms: (room, element, his tiles-sheet row, his m2, causes as T-546 (identical areas; the membrane floor and the
# tile floor are the same drawn face), kitchen line coded PORCELAIN)
WET = [
    ("GF lobby wash (2 basins)", "GF-RDBD4F9:floor", 42, "4.73", [("2-dp rounding", "0.000695", 1, "TOLERANCE")]),
    ("GF basin space by the stair", "GF-RD36087:floor", 43, "1.7",
     [("passage reveal 0.20 x 1.10 taken into his room (threshold piece, not floor)", "0.220", -1, "RULE_DIFFERENCE"),
      ("his 1.705 truncated", "0.005", 1, "TOLERANCE")]),
    ("GF master bath", "GF-RD6F891:floor", 44, "3.7",
     [("diagonal-wall corner out of 2.10 x 2.00", "0.017683", 1, "ENGINE_RIGHT")]),
    ("GF core W.C. 245 x 167 (wedge)", "GF-RB28769:floor", 45, "2.3",
     [("wedge room by shoelace on the drawn faces", "0.06761", 1, "ENGINE_RIGHT")]),
    ("GF core W.C. 289 x 167 (wedge)", "GF-RF38DAF:floor", 46, "2.67", [("2-dp truncation", "0.005221", 1, "TOLERANCE")]),
    ("GF stair-core W.C. 175 x 135", "GF-RDF7D28:floor", 47, "2.36", [("2-dp truncation", "0.0025", 1, "TOLERANCE")]),
    ("GF kitchen (floor line coded FIN.FLOOR.PORCELAIN)", "GF-RA3AD49:floor", 48, "9.55",
     [("printed 300 x 270 + 105 x 150 less two drawn piers 0.045", "0.080001", 1, "ENGINE_RIGHT")]),
    ("GF driver W.C.", "GF-RFAD3C4:floor", 49, "1.95", []),
    ("GF W.C. by the reception room", "GF-RB62B55:floor", 50, "3.37", [("2-dp truncation", "0.005", 1, "TOLERANCE")]),
    ("GF wash by the reception room", "GF-R8496F0:floor", 51, "3.15",
     [("column corner out of the printed 150 x 210", "0.0175", -1, "ENGINE_RIGHT")]),
    ("1F east bath 210 x 225", "1F-R48CDA5:floor", 55, "4.72", [("2-dp truncation", "0.005", 1, "TOLERANCE")]),
    ("1F bath by the laundry", "1F-RED23B8:floor", 56, "3.6",
     [("drawn jamb 0.45 x 0.05 out of 2.00 x 1.80", "0.0225", -1, "ENGINE_RIGHT")]),
    ("1F W.C. by the laundry", "1F-R52AC05:floor", 57, "2.59",
     [("printed 180 x 147 against his 1.80 x 1.44", "0.056", 1, "ENGINE_RIGHT")]),
    ("1F west bath A 245 x 205", "1F-R48AA46:floor", 58, "5", [("printed 245 x 205", "0.0225", 1, "ENGINE_RIGHT")]),
    ("1F west bath B 245 x 205", "1F-R8BDA49:floor", 59, "5", [("printed 245 x 205", "0.0225", 1, "ENGINE_RIGHT")]),
    ("1F laundry", "1F-R26FA0D:floor", 60, "10",
     [("printed 347 x 300 / 185 with the W.C. corner, his typed 10.00", "0.151", 1, "ENGINE_RIGHT")]),
    ("2F roof-floor W.C. 300 x 185", "2F-RE83BED:floor", 63, "5.62",
     [("printed 185 against his 1.875", "0.07", -1, "ENGINE_RIGHT")]),
]

# outdoor (not in his 409.58; his yard row 151.80 is one unsplit row on the marble + yard sheet, H13)
OUTDOOR_ELEMENTS = ["GF-COURT#WEST-OPEN", "GF-COURT#NORTH-WALK", "GF-COURT#POOL-DECK", "GF-COURT#PORCH"]
FREELANCER_YARD = "151.8"


def load_index():
    raw = INDEX.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INDEX_SHA:
        raise RuntimeError("line index changed: re-pin")
    return json.loads(raw)


def floor_lines(d):
    from t553_floor_tile_reconcile import FLOOR_CODES
    return {v["line_id"]: v for v in d["lines"] if v["item_code"] in FLOOR_CODES}


def _line(by_el, el):
    v = by_el[el]
    ln = {"line_id": v["line_id"], "item_code": v["item_code"], "qty": v["measured_net"], "unit": v["unit"],
          "basis": "installed"}
    if v["measured_net"] is None:
        ln.update(state="HELD", bound=[v["held_low"], v["held_high"]])
    return ln


def rows(d):
    from t553_floor_tile_reconcile import FLOOR_CODES
    by_el = {}
    for v in d["lines"]:
        if v["item_code"] in FLOOR_CODES and v["class"] != "EXCLUDED":
            if v["element_id"] in by_el:
                raise RuntimeError(f"two floor lines on {v['element_id']}")
            by_el[v["element_id"]] = v
    out, used = [], set()
    for room, floor, els, cells, fcls, comps, note in DRY:
        moves = []
        if "open pantry" in room:
            moves = [{"what": "GF open pantry", "m2": "13.454868", "engine": "WET (Q-37 A)", "freelancer": "DRY row 13"}]
        out.append({"room": room, "floor": floor, "engine_lines": [_line(by_el, e) for e in els],
                    "freelancer": [{"row": r, "m2": m, "basis": "installed"} for r, m in cells],
                    "freelancer_class": fcls, "components": comps, "note": note, "class_moves": moves})
        used.update(els)
    for room, el, frow, fm2, cs in WET:
        moves = []
        if el == "GF-RA3AD49:floor":
            moves = [{"what": "GF kitchen", "m2": "9.630001", "engine": "DRY code FIN.FLOOR.PORCELAIN (its bed, membrane,"
                      " threshold are WET)", "freelancer": "WET row 48", "finding": "F-T553-2"}]
        out.append({"room": room, "floor": room[:2], "engine_lines": [_line(by_el, el)],
                    "freelancer": [{"row": frow, "m2": fm2, "basis": "installed"}], "freelancer_class": "WET",
                    "components": [comp(n, q, s, c, T074) for n, q, s, c in cs], "note": "", "class_moves": moves})
        used.add(el)
    missing = set(by_el) - used
    if missing:
        raise RuntimeError(f"floor tile lines not placed in a row: {sorted(missing)}")
    return out


def outdoor(d):
    from decimal import Decimal
    lines = [v for v in d["lines"] if v["element_id"] in OUTDOOR_ELEMENTS]
    valued = sum((Decimal(str(v["measured_net"])) for v in lines if v["measured_net"] is not None), Decimal(0))
    held = [(v["line_id"], v["element_id"], v["held_low"], v["held_high"]) for v in lines if v["measured_net"] is None]
    tile = [(v["line_id"], v["element_id"], v["measured_net"]) for v in lines if v["item_code"] == "EXT.FLOOR.PORCELAIN"]
    return {"lines": [(v["line_id"], v["item_code"], v["element_id"], v["measured_net"]) for v in lines],
            "valued_m2": str(valued), "held": held, "porcelain_tile": tile, "freelancer_yard_m2": FREELANCER_YARD}
