"""T-303 on the development villa (P7757): the WP.WET_AREA and WP.ROOF scope inventories and the WP.POOL_TANK presence
ruling, joined to the waterproofing lines of the candidate of record. Reads only committed, merged ledgers; writes
counts, statuses, quantities, DXF handles and run / element ids (no coordinate, no name, no drawing content).

    python3 -I research/agents_t303/t303_alsenan.py [--out DIR]

Candidate lines: research/agents_t301/CANDIDATE_V3017_WP.json (T-301's extract of the ARCH_TAKEOFF_V3.0.17 run, read
only). V3.0.18 (T-266, Gate B PASS MERGED ceeb5135, Verifier 2026-10-25 22:49) changed 5 stair lines and added 5 lines
(stairs, landing marble, the pantry FIN.FLOOR.WET_TILE piece 1.100 m2); 3,695 lines byte-identical, no waterproofing line
among the changed or added ones: the 150 WP line ids, states and nets below are V3.0.18's too (the pantry piece lies
inside the printed 4.50 x 3.00 box the 13.500 m2 pantry membrane line already covers, t266_inputs.py 'downstream').

Element sources (each merged and Checker-verified or Checker-cited; none is the engine's line list):
  wet rooms    research/agents_t074/wet_areas_hand_table.json: 17 wet areas by own polygonisation of the wall faces
               (floor m2, boundary lm, doorways with block, width, wall depth; T-074 merged; Q-35 owner table) and the
               pantry (Q-37 A: printed 4500 x 3000 box, T-286 MERGED, DIMENSION 5E1 / 5D5); presence cross-checked with
               the T-209 wet-room set (18 rooms, research/agents_t209/ALSENAN_T209_INPUT.json)
  doors        research/agents_t249/OPENINGS_T249.csv (engine-independent opening inventory, T-249 MERGED 2a2d15af,
               Verifier 2026-10-24 02:48): door id, DXF insert handle, block; each door's wet rooms from the T-074 /
               T-209 room door lists; block widths re-read this run on P7757.dxf (D315 800, D120 1000, d220 900 mm; all
               20 inserts of the three blocks at |scale| 1)
  open edges   T-074 addendum (Q-35: lobby to the stair hall 1.26, basin space to the passage 0.90), T-209 / T-128 r3
               (arch to the dewaneya 1.00, no leaf; pantry open side to the dining 4.49)
  roofs        research/agents_t062/T-062_ROOF_POOL_VOID_TRACE.md hand trace (T-062 merged; Verifier T-071 2026-10-19
               re-multiplied 55.560 / 32.721 / 115.816 m2): roof faces by printed label and level, parapet / building /
               closure upturn runs, the 2F dome footprints and rings; Q-24, Q-29 (S0 / S1, owner 2026-10-22), Q-34 (2F top
               roof HELD)
  pool / tank  research/agents_t183/T-183_POOL_RC.md (T-183 r2 MERGED 6380294): ST7757.pdf p.7 DETAIL OF SWIMMING POOL,
               TEXT 1876 '5cm INSULATION MEMBRANE.' / 1874 '5cm SECREED.', hatch 1851 S-INSU.D; S8.2 register row
               PL-BUILDUP-INSULATION_MEMBRANE (family WATERPROOFING_OR_INSULATION, BLOCKED_UNQUANTIFIED);
               research/alsenan_water_tank_s8_4/00_README.md + research/agents_t204/T-204_LIFT_TANK.md (tank place only)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import t303_wp_families as F  # noqa: E402

W = F.W
EXTRACT = ROOT / "research/agents_t301/CANDIDATE_V3017_WP.json"
T074 = ROOT / "research/agents_t074/wet_areas_hand_table.json"
T209 = ROOT / "research/agents_t209/ALSENAN_T209_INPUT.json"
T249 = ROOT / "research/agents_t249/OPENINGS_T249.csv"
TOL = 0.0005                       # a residual that prints 0.000 at 3 decimals (stated; the T-301 core keeps 1e-6)
WET, ROOF, POOL = "WP.WET_AREA", "WP.ROOF", "WP.POOL_TANK"
S074 = "T-074 wet-area hand table (merged; owner Q-35 table)"
S286 = "T-286 pantry box (MERGED; Q-37 A, printed 4500 x 3000)"
S249 = "T-249 opening inventory (MERGED 2a2d15af) + T-074 / T-209 room door lists"
S062 = "T-062 roof hand trace (merged; Verifier T-071 re-multiplied)"

# T-209 room id -> (T-074 index or None, engine face id). Engine face by the T-086 face census (floor + area within
# 0.02 m2 of the T-074 row, exact to 1e-3 here) and, for the two equal 1F west baths, by the T-249 door each carries
# (C2B on the upper bath, C2E on the lower: OP-004 / DOOR-1F-0c35dbd6 at the same plan point).
ROOMS = {
    "GF-02": (0, "GF-R8496F0"), "GF-03": (1, "GF-RB62B55"), "GF-05": (2, "GF-RFAD3C4"), "GF-06": (3, "GF-RA3AD49"),
    "GF-07": (None, "GF-RC99C2A"), "GF-10": (4, "GF-RDF7D28"), "GF-11": (5, "GF-RD36087"), "GF-12": (6, "GF-RF38DAF"),
    "GF-13": (7, "GF-RB28769"), "GF-14": (8, "GF-RDBD4F9"), "GF-16": (9, "GF-RD6F891"), "1F-02": (10, "1F-R48AA46"),
    "1F-03": (11, "1F-R8BDA49"), "1F-07": (12, "1F-R26FA0D"), "1F-08": (13, "1F-R52AC05"), "1F-09": (14, "1F-RED23B8"),
    "1F-12": (15, "1F-R48CDA5"), "2F-02": (16, "2F-RE83BED")}
# physical doors of the wet rooms: T-249 id -> (wet rooms it opens, width m, wall depth m). Width = the drawn door block
# (|scale| 1), depth = T-074; a door between two wet rooms is ONE element (Q-35 C, Lead reading 2026-10-19 18:15).
DOORS = {
    "D-GF-02": (("GF-02", "GF-03"), 0.80, 0.15), "D-GF-04": (("GF-05",), 0.80, 0.15),
    "D-GF-05": (("GF-06",), 1.00, 0.20), "D-GF-10": (("GF-10", "GF-11"), 0.80, 0.15),
    "D-GF-11": (("GF-12", "GF-14"), 0.80, 0.15), "D-GF-12": (("GF-13", "GF-14"), 0.80, 0.15),
    "D-GF-14": (("GF-16",), 0.80, 0.15), "D-1F-01": (("1F-02",), 0.80, 0.15), "D-1F-04": (("1F-03",), 0.80, 0.15),
    "D-1F-05": (("1F-07",), 0.90, 0.20), "D-1F-06": (("1F-07", "1F-08"), 0.80, 0.15),
    "D-1F-07": (("1F-09",), 0.80, 0.15), "D-1F-10": (("1F-12",), 0.80, 0.15), "D-2F-03": (("2F-02",), 0.80, 0.15),
    # the pantry's own D120 (T-128 r3 / T-209 GF-07 1.00, walked 0.99): no T-249 insert bound to it in a merged
    # ledger yet (named; its depth not tabled -> its doorway piece is blank, never 0)
    "D-GF-07-PANTRY": (("GF-07",), 1.00, None)}
LEAFLESS = {"GF-02": [("ARCH_TO_DEWANEYA", 1.00)], "GF-11": [("DOORWAY_P-GF-01", 0.90)]}
OPEN_EDGES = {"GF-14": [("OPEN_SIDE_STAIR_HALL", 1.26)], "GF-07": [("OPEN_SIDE_DINING", 4.49)]}
PANTRY_M2 = round(4.500 * 3.000, 6)

ITEM = {"floor": "FIN.WP.FLOOR", "upturn": "FIN.WP.WALL_UPTURN", "pen": "FIN.WP.PENETRATION",
        "rolls": "FIN.WP.MEMBRANE_ROLLS", "door": "FIN.WP.DOORWAY", "trans": "FIN.WP.DOORWAY_TRANSITION",
        "nr": "FIN.WP.DOORWAY_TRANSITION_NR", "term": "FIN.WP.TERMINATION", "roof": "FIN.WP.ROOF",
        "rup": "FIN.WP.ROOF_UPTURN"}


def _el(fam, item, unit, element, face, floor, src, qty=None, ref=None, note=None, scope=None):
    return {"family": fam, "item_code": item, "unit": unit, "element": element, "face": face, "floor": floor,
            "applicability": "APPLICABLE", "qty": qty, "source": src, "ref": ref, "owner": scope, "note": note}


def t074():
    return json.loads(T074.read_text(encoding="utf-8"))


def t249_doors():
    with open(T249, encoding="utf-8", newline="") as fh:
        return {r["ID"]: r for r in csv.DictReader(fh) if r["KIND"] == "DOOR"}


def wet_rooms():
    """{room: {"doors": [...], "open_edges": [...], ...}} from T-074 / T-209 / T-249 (never the engine lines)."""
    h = t074()
    out = {}
    for r, (i, face) in ROOMS.items():
        doors = sorted(d for d, (rs, _w, _t) in DOORS.items() if r in rs)
        out[r] = {"face": face, "floor": r[:2], "t074": i, "doors": doors,
                  "leafless": LEAFLESS.get(r, []), "open_edges": OPEN_EDGES.get(r, []) + LEAFLESS.get(r, []),
                  "fd": (h[i]["sanitary_drawing"] if i is not None else "FD (Q-37: sanitary-7757.pdf GF 'FD' in the "
                                                                          "pantry)")}
        if i is not None and len(h[i]["doorways"]) != len(doors):
            raise W.InventoryError(f"{r}: T-074 lists {len(h[i]['doorways'])} doorways, the door inventory {len(doors)}")
    return out


def wet_elements():
    h = t074()
    rooms = wet_rooms()
    out = []
    for r, x in sorted(rooms.items()):
        i, fl = x["t074"], x["floor"]
        if i is None:                                    # the pantry (Q-37 A)
            out.append(_el(WET, ITEM["floor"], "m2", r, "FLOOR", fl, S286, qty=PANTRY_M2, ref="printed 4500 x 3000",
                           scope=r))
            out.append(_el(WET, ITEM["upturn"], "m2", r, "WALLS", fl, S286, scope=r,
                           note="walls round the printed box less the 1.00 door and the 4.49 open side; candidate "
                                "line held (wall heights / closure, T-286)"))
        else:
            row = h[i]
            out.append(_el(WET, ITEM["floor"], "m2", r, "FLOOR", fl, S074, qty=float(row["floor_m2"]),
                           ref=row["outline_source"], scope=r))
            lm = F.walls_only_lm(row["boundary_lm"], [DOORS[d][1] for d in x["doors"]],
                                 [w for _n, w in x["leafless"]], [w for _n, w in OPEN_EDGES.get(r, [])])
            out.append(_el(WET, ITEM["upturn"], "m2", r, "WALLS", fl, S074, qty=round(lm * F.UPTURN_M, 6),
                           ref=f"boundary {row['boundary_lm']} lm - doors - leafless - open = {lm} lm x 0.20 "
                               "(Q-35 C walls only)", scope=r))
        out.append(_el(WET, ITEM["pen"], "pcs", r, "FLOOR_PENETRATIONS", fl, S074, scope=r,
                       ref=f"sanitary drawing: {x['fd']}", note="drain / pipe count not tabled: HELD"))
        out.append(_el(WET, ITEM["rolls"], "pcs", r, "SUPPLY", fl, S074, scope=r,
                       note="procurement count from the strip layout (Q-49 / UP-WP-005), not a face: no independent "
                            "count in this inventory"))
        for name, w in OPEN_EDGES.get(r, []) + x["leafless"]:
            out.append(_el(WET, ITEM["term"], "lm", f"{r}:{name}", "MEMBRANE_EDGE", fl,
                           "T-074 addendum / T-209 / T-128 r3", scope=r,
                           ref=f"opening {w:.2f} m with no wall and no leaf",
                           note="where the membrane stops on an open side (Q-37 A threshold line for the pantry)"))
    t249 = t249_doors()
    for d, (rs, w, t) in sorted(DOORS.items()):
        fl = rs[0][:2]
        ref = (f"{d} block {t249[d]['PLAN_SYMBOL']} insert {t249[d]['HANDLES']}" if d in t249 else
               "T-128 r3 / T-209 GF-07 'D120 1.00' (insert not bound)")
        sc = "|".join(rs)
        out.append(_el(WET, ITEM["door"], "m2", f"DOOR:{d}", "THRESHOLD_FLOOR", fl, S249,
                       qty=None if t is None else F.doorway_m2(w, t), ref=ref, scope=sc,
                       note=None if t is not None else "wall depth not tabled: HELD"))
        out.append(_el(WET, ITEM["trans"], "m2", f"DOOR:{d}", "TRANSITION", fl, S249, ref=ref, scope=sc,
                       note="one transition per physical door (Q-35 C); detail not printed"))
        out.append(_el(WET, ITEM["nr"], "pcs", f"DOOR:{d}", "TRANSITION", fl, S249, qty=1 if d in t249 else None,
                       ref=ref, scope=sc))
    W.validate_inventory(out)
    return out


def roof_elements():
    s1f = round(11.8 * 1.3 + 10.4 * 3.2 + (4.0 * 1.8 - (1.1 ** 2 - math.pi * 1.1 ** 2 / 4)), 6)     # 55.560332
    s1se = round(18.97 * 1.30 + 1.30 * 6.20, 6)                                                    # 32.721
    s2 = round(18.87 * 5.0 + 4.2 * 2.1 + 6.57 * 6.6, 6)                                            # 146.532
    dome_a = round(2 * math.pi * 2.211 ** 2, 6)                                                    # 30.715849
    ring = round(2 * 2 * math.pi * 2.211, 6)                                                       # 27.784246
    e = [_el(ROOF, ITEM["roof"], "m2", "1F-ROOF-AT220", "INSIDE_PARAPET", "1F", S062, qty=s1f, scope="1F-ROOF-AT220",
             ref="+4.30: 11.8 x 1.3 + 10.4 x 3.2 + (4.0 x 1.8 - corner fillet r 1.10)"),
         _el(ROOF, ITEM["rup"], "lm", "1F-ROOF-AT220", "PARAPET_BUILDING_CLOSURE", "1F", S062, qty=35.727,
             scope="1F-ROOF-AT220", ref="30.928 parapet + 4.600 building + 0.200 closure (printed total 35.727)"),
         _el(ROOF, ITEM["roof"], "m2", "1F-ROOF-AT216", "INSIDE_PARAPET", "1F", S062, qty=s1se, scope="1F-ROOF-AT216",
             ref="+5.50 L strip: 18.97 x 1.30 + 1.30 x 6.20"),
         _el(ROOF, ITEM["rup"], "lm", "1F-ROOF-AT216", "PARAPET_BUILDING_CLOSURE", "1F", S062, qty=52.940,
             scope="1F-ROOF-AT216", ref="28.665 + 23.870 + 0.405"),
         _el(ROOF, ITEM["roof"], "m2", "2F-ROOF-AT379", "INSIDE_PARAPET_OUTSIDE_DOMES", "2F", S062,
             qty=round(s2 - dome_a, 6), scope="2F-ROOF-AT379",
             ref="+9.70: 18.87 x 5.0 + 4.2 x 2.1 + 6.57 x 6.6 = 146.532 less 2 dome footprints pi 2.211^2"),
         F.scope_unknown(ROOF, ITEM["roof"], "m2", "2F-ROOF-AT379", "DOME_FOOTPRINTS", "2F", S062,
                         f"2 x pi 2.211^2 = {dome_a} m2 under the two detailed domes: approved design S0 keeps "
                         "concrete domes (owner 2026-10-22), the line deducts them as open skylights (S1); whether the "
                         "membrane runs under a dome is not settled (Q-24 reading, Q-29 option C, T-185)",
                         scope="2F-ROOF-AT379"),
         _el(ROOF, ITEM["rup"], "lm", "2F-ROOF-AT379", "PARAPET_BUILDING_CLOSURE", "2F", S062, qty=65.140,
             scope="2F-ROOF-AT379", ref="48.265 + 16.800 + 0.075"),
         _el(ROOF, ITEM["rup"], "lm", "2F-ROOF-AT379", "DOME_BASE_RINGS", "2F", S062, qty=ring, scope="2F-ROOF-AT379",
             ref="2 x 2 pi 2.211 (circle)", note="Q-24 owner: a dome standing above the slab gets the 0.20 m upturn "
                                                 "round its base (S0) / the skylight edge (S1): applicable either way"),
         _el(ROOF, ITEM["roof"], "m2", "2F-ROOF-TOP", "TOP_ROOF", "2F", "Q-34 (owner: HELD, ask later)",
             scope="2F-ROOF-TOP", note="+13.90 outline drawn on no plan: HELD"),
         _el(ROOF, ITEM["rup"], "lm", "2F-ROOF-TOP", "TOP_ROOF_PARAPET", "2F", "Q-34 (owner: HELD, ask later)",
             scope="2F-ROOF-TOP", note="HELD with the top roof"),
         F.scope_unknown(ROOF, ITEM["roof"], "m2", "1F-AT364-OVAL-VOID", "AREA_ROUND_VOID", "1F", S062,
                         "6.130 m2 net round the oval void at +5.50 (AT364) behind the D2:3035 / D2:3036 parapet pair: "
                         "no ROOF label printed, roof or not is not on the plan (T-062 held)", scope="1F-AT364-OVAL-VOID"),
         F.scope_unknown(ROOF, ITEM["rup"], "lm", "1F-AT364-OVAL-VOID", "AREA_ROUND_VOID", "1F", S062,
                         "upturn of the area round the oval void: same scope question", scope="1F-AT364-OVAL-VOID")]
    for rf in ("1F-ROOF-AT220", "1F-ROOF-AT216", "2F-ROOF-AT379", "2F-ROOF-TOP"):
        e.append(_el(ROOF, ITEM["rolls"], "pcs", rf, "SUPPLY", rf[:2], S062, scope=rf,
                     note="procurement count from the roof cutting plan (Q-49 / Q-58 A conditional): not a face"))
    W.validate_inventory(e)
    return e


def pool_tank_elements():
    pool_src = "T-183 r2 (MERGED 6380294) + S8.2 register PL-BUILDUP-INSULATION_MEMBRANE"
    printed = {"sheet": "ST7757.pdf p.7 DETAIL OF SWIMMING POOL / ST7757 dxf.dxf frame FR01",
               "ref": "TEXT 1876 '5cm INSULATION MEMBRANE.', hatch 1851 S-INSU.D: under the base and up the outer wall "
                      "faces to the wall top"}
    screed = {"sheet": printed["sheet"], "ref": "TEXT 1874 '5cm SECREED.': under the base and up the outer wall faces"}
    tank_np = {"sheet": "ST7757 dxf.dxf 2F roof slab SP-2F_ROOF_SLAB-01 / -02 + P7757 roof plan",
               "ref": "'WATER TANK PLACE' note and cloud only: no tank base, wall, member or WP layer drawn, noted or "
                      "scheduled in either discipline (S8.4 README; T-204 TANK-01 HELD)"}
    return [F.presence_ruling(POOL, "WP.POOL_TANK.POOL_MEMBRANE", "m2", "POOL-1", "BASE_AND_OUTER_WALLS", "GF",
                              pool_src, printed=printed,
                              note="T-183 r2 drawn extent 30.932 m2 (DRAWING-CONFIRMED, NOT VERIFIED); printed as an "
                                   "INSULATION membrane: waterproofing or insulation not stated (S8.2 "
                                   "WATERPROOFING_OR_INSULATION, BLOCKED_UNQUANTIFIED); product C3, termination C9"),
            F.presence_ruling(POOL, "WP.POOL_TANK.POOL_PROTECTION_SCREED", "m3", "POOL-1", "BASE_AND_OUTER_WALLS",
                              "GF", pool_src, printed=screed,
                              note="T-183 r2 1.591 m3 as drawn (DRAWING-CONFIRMED, NOT VERIFIED)"),
            F.presence_ruling(POOL, "WP.POOL_TANK.TANK_MEMBRANE", "m2", "TANK-01", "ALL_FACES", "2F",
                              "S8.4 water-tank region + T-204", not_printed=tank_np,
                              note="re-rule when a tank structure is drawn (T-204 holds the tank itself)")]


# ------------------------------------------------------------------------------------------------ candidate lines
def lines_of(fam):
    cand = json.loads(EXTRACT.read_text(encoding="utf-8"))["lines"]
    if fam == WET:
        return [x for x in cand if x["item_code"] in {ITEM[k] for k in ("floor", "upturn", "pen", "door", "trans", "nr",
                                                                          "term")}
                or (x["item_code"] == ITEM["rolls"] and "-ROOF-" not in (x["element_id"] or ""))]
    if fam == ROOF:
        return [x for x in cand if x["item_code"] in (ITEM["roof"], ITEM["rup"])
                or (x["item_code"] == ITEM["rolls"] and "-ROOF-" in (x["element_id"] or ""))]
    return [x for x in cand if x["item_code"].startswith("WP.POOL") or "TANK" in x["item_code"]]


def _door_of(ln, room, rooms, t249):
    """the T-249 door a doorway / transition line names: an OP / DOOR id bound by T-249, or the room's only door."""
    eid = ln["element_id"]
    ref = eid.split(":", 1)[1]
    for d, r in t249.items():
        eng = [s.strip() for s in r["ENGINE_REF"].split("/")]
        if r["FLOOR"] == ln["floor"] and any(s and (f" {s}" in f" {ref}" or ref.endswith(s)) for s in eng):
            if d in rooms[room]["doors"]:
                return d, f"{d} by T-249 engine ref {r['ENGINE_REF']}"
            return None, f"T-249 {d} ({r['ENGINE_REF']}) is not a door of {room}"
    if "CLOSURE" in ref and len(rooms[room]["doors"]) == 1:
        return rooms[room]["doors"][0], "the room's only door (closure-derived line)"
    return None, f"door not identified from {ref!r}"


def links(fam, lines):
    rooms = wet_rooms()
    face2room = {x["face"]: r for r, x in rooms.items()}
    t249 = t249_doors()
    out, mapping = {}, []
    for ln in lines:
        ic, u, eid = ln["item_code"], ln["unit"], ln["element_id"] or ""
        base = eid.split(":", 1)[0]
        if fam == ROOF:
            faces = {ITEM["roof"]: {"1F-ROOF-AT220": ["INSIDE_PARAPET"], "1F-ROOF-AT216": ["INSIDE_PARAPET"],
                                    "2F-ROOF-AT379": ["INSIDE_PARAPET_OUTSIDE_DOMES"], "2F-ROOF-TOP": ["TOP_ROOF"]},
                     ITEM["rup"]: {"1F-ROOF-AT220": ["PARAPET_BUILDING_CLOSURE"],
                                   "1F-ROOF-AT216": ["PARAPET_BUILDING_CLOSURE"],
                                   "2F-ROOF-AT379": ["PARAPET_BUILDING_CLOSURE", "DOME_BASE_RINGS"],
                                   "2F-ROOF-TOP": ["TOP_ROOF_PARAPET"]},
                     ITEM["rolls"]: {k: ["SUPPLY"] for k in ("1F-ROOF-AT220", "1F-ROOF-AT216", "2F-ROOF-AT379",
                                                             "2F-ROOF-TOP")}}[ic].get(base)
            out[ln["line_id"]] = [f"{ic}[{u}]/{base}/{f}" for f in faces] if faces else [f"{ic}[{u}]/?/{eid}"]
            mapping.append((ln["line_id"], base, "roof face by the line's roof id"))
            continue
        room = face2room.get(base)
        if room is None:
            out[ln["line_id"]] = [f"{ic}[{u}]/?/{eid}"]
            mapping.append((ln["line_id"], None, "cell not an inventory wet room"))
            continue
        if ic in (ITEM["floor"], ITEM["upturn"], ITEM["pen"], ITEM["rolls"]):
            face = {ITEM["floor"]: "FLOOR", ITEM["upturn"]: "WALLS", ITEM["pen"]: "FLOOR_PENETRATIONS",
                    ITEM["rolls"]: "SUPPLY"}[ic]
            out[ln["line_id"]] = [f"{ic}[{u}]/{room}/{face}"]
            mapping.append((ln["line_id"], room, "room by the T-086 face census / T-249 door"))
        elif ic in (ITEM["door"], ITEM["trans"], ITEM["nr"]):
            d, why = _door_of(ln, room, rooms, t249)
            face = "THRESHOLD_FLOOR" if ic == ITEM["door"] else "TRANSITION"
            out[ln["line_id"]] = [f"{ic}[{u}]/DOOR:{d}/{face}" if d else f"{ic}[{u}]/?/{eid}"]
            mapping.append((ln["line_id"], d, why))
        elif ic == ITEM["term"]:
            edges = OPEN_EDGES.get(room, []) + LEAFLESS.get(room, [])
            kind = eid.split("termination ", 1)[-1].split(" ")[0]
            if len(edges) == 1 and kind in ("passage", "zone_line"):
                out[ln["line_id"]] = [f"{ic}[{u}]/{room}:{edges[0][0]}/MEMBRANE_EDGE"]
                mapping.append((ln["line_id"], edges[0][0], f"the room's only open edge ({kind})"))
            else:
                out[ln["line_id"]] = [f"{ic}[{u}]/?/{eid}"]
                mapping.append((ln["line_id"], None, f"termination '{kind}': no open edge / leafless opening of "
                                                      f"{room} in the inventory"))
        else:
            out[ln["line_id"]] = [f"{ic}[{u}]/?/{eid}"]
    return out, mapping


def scope_line(ln):
    base = (ln["element_id"] or "").split(":", 1)[0]
    if base.startswith(("1F-ROOF", "2F-ROOF")):
        return base
    face2room = {x[1]: r for r, x in ROOMS.items()}
    room = face2room.get(base, base)
    if ln["item_code"] in (ITEM["door"], ITEM["trans"], ITEM["nr"]):
        return "DOORS"
    return room


def scope_element(r):
    if r["item_code"] in (ITEM["door"], ITEM["trans"], ITEM["nr"]):
        return "DOORS-PER-DOOR"            # a door item is judged per door (its own key), not per room
    return r["owner"]


def family_report(fam):
    els = {WET: wet_elements, ROOF: roof_elements, POOL: pool_tank_elements}[fam]()
    lines = lines_of(fam)
    if fam == WET:
        F.check_wet_rooms(wet_rooms(), [r for r, x in wet_rooms().items()
                                        if x["face"] in {(ln["element_id"] or "").split(":")[0] for ln in lines}]
                          + [b for b in {(ln["element_id"] or "").split(":")[0] for ln in lines}
                             if b not in {x[1] for x in ROOMS.values()}])
    lk, mapping = links(fam, lines)
    rep = F.join_family(els, lines, lk)
    rep["line_rows"] = F.line_rows(rep, lines, lk, scope_line, scope_element, tol=TOL)
    rep["mapping"] = mapping
    rep["lines"] = len(lines)
    return els, lines, lk, rep


def t236(fam, els, lines, lk):
    from engine.source import trade_completeness_v1 as TC
    clean, _d = F.split_doubles(lk, lines)
    inv, exc, ll = W.to_t236(els, clean, f"T-303 {fam} inventory")
    canon = [{"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"], "trade": "WATERPROOFING",
              "evidence_state": x["evidence_state"], "measured_net": x["measured_net"],
              "rfi": {"question": "held"} if x["measured_net"] is None else None} for x in lines]
    rep = TC.check(inventories=inv, lines=canon, line_links=ll, exclusions=exc)
    row = next(r for r in rep["trades"] if r["trade"] == "WATERPROOFING")
    return {k: row.get(k) for k in ("status", "found", "measured", "held", "missing", "excluded")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="directory for the inventory csv / report json")
    a = ap.parse_args(argv)
    summary = {"schema": W.SCHEMA, "rule_id": F.RULE_ID, "tol_m": TOL, "candidate": "ARCH_TAKEOFF_V3.0.17 = V3.0.18 "
               "for every WP line (T-266 changed / added no WP line)", "families": {}}
    all_rows, all_lines = [], []
    for fam in (WET, ROOF, POOL):
        els, lines, lk, rep = family_report(fam)
        cnt = Counter(r["countability"] for r in rep["line_rows"])
        summary["families"][fam] = {
            "elements": len(els), "lines": len(lines), "counts": rep["counts"],
            "scope_unknown": sum(1 for r in rep["elements"] if (r["note"] or "").startswith("SCOPE_UNKNOWN")),
            "register_only": rep["register_only"], "unlinked_lines": rep["unlinked_lines"],
            "double_carried": rep["double_carried"],
            "items": [{k: f[k] for k in ("item_code", "unit", "elements", "in_line", "in_line_quantity",
                                         "in_line_held", "not_applicable", "missing", "inventory_qty_in_line",
                                         "line_qty", "residual", "double_carried")} for f in rep["families"]],
            "line_countability": dict(sorted(cnt.items())),
            "t236": t236(fam, els, lines, lk) if lines else None}
        all_rows += rep["elements"]
        all_lines += rep["line_rows"]
        print(fam, "elements", len(els), "lines", len(lines), rep["counts"], "register_only", len(rep["register_only"]),
              "doubles", len(rep["double_carried"]), "countability", dict(cnt))
        for f in rep["families"]:
            print(f"  {f['item_code']:<34} {f['unit']:<4} el {f['elements']:>3} in {f['in_line']:>3} (q "
                  f"{f['in_line_quantity']:>3} h {f['in_line_held']:>3}) na {f['not_applicable']:>2} miss "
                  f"{f['missing']:>2} dbl {f['double_carried']}  inv {f['inventory_qty_in_line']}  line {f['line_qty']}"
                  f"  res {f['residual']}")
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        cols = ("key", "family", "item_code", "unit", "element", "face", "floor", "status", "line_id", "line_state",
                "qty", "owner", "evidence", "source", "note")
        with open(out / "WP_WET_ROOF_POOL_INVENTORY_T303.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            for r in all_rows:
                w.writerow({c: (json.dumps(r[c], sort_keys=True) if isinstance(r[c], dict) else
                                ("" if r[c] is None else r[c])) for c in cols})
        lc = ("line_id", "item_code", "unit", "scope", "line_state", "line_qty", "elements", "inventory_qty",
              "residual", "countability", "why")
        with open(out / "WP_LINE_COUNTABILITY_T303.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=lc, lineterminator="\n")
            w.writeheader()
            for r in all_lines:
                w.writerow({c: "" if r[c] is None else r[c] for c in lc})
        (out / "WP_FAMILIES_REPORT_T303.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n",
                                                          encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
