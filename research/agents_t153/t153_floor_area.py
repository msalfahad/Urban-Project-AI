"""T-153 floor area room by room (research only, NO REPO CODE: no engine module is changed or imported).

Two parts:
1. `classify` / `floor_area`: the general hand rules this table applies to every space (any villa):
   - interior / exterior under UP-SPACE-001 evidence order (project decision UP-SPACE-002 > exterior room word >
     interior room word > unlabelled with a doorless facade opening -> POSSIBLY_EXTERIOR > UNKNOWN; never assumed
     interior). An exterior word on a space the drawing encloses AND roofs is a CONFLICT (UP-SPACE-001 "never: a label
     alone defines every construction property"): HELD, never a guess.
   - wet / dry under UP-WET-001 (bathroom, W.C., kitchen, pantry, laundry, ironing: wet), owner Q-06 A (a basin-only
     hand-wash space is wet), UP-WET-002 (an unlabelled space with no fixture evidence is REVIEW: no wet and no dry scope).
   - floor family: URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 (dry interior floors porcelain unless a specification overrides),
     URBAN-WET-FLOOR-TILED@v1 (wet / service floors tiled, type by specification); exterior, roof, stair: no default.
   - floor area = the space polygon to the finished wall face, less voids, shafts, stair treads / footprint and the
     footprint of walls, plinths and curbs inside it (a half wall included); fixed cabinetry is NOT deducted
     (URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1: the floor finish runs under it).
   - UP-QTY-STATUS-001: every labelled space once: MEASURED / CALCULATED, HELD (with cause) or EXCLUDED (with reason);
     a held quantity is never 0 and never added to a confirmed total.
2. `alsenan_ledger`: the Alsenan rows (areas only, no coordinates), each with its source (merged hand tables, the
   ARCH_TAKEOFF_V2.9 floor reconciliation, or this run's measurement on the Drive DXF), and the per-floor totals against
   the freelancer's floor rows.

Usage:  python3 -I t153_floor_area.py --check            synthetic non-Alsenan fixture (hand values) + Alsenan re-adds
        python3 -I t153_floor_area.py --out <dir>         writes SPACES_T153.csv, FLOORS_T153.csv, summary.json
"""
import csv
import json
import math
import sys
from pathlib import Path

EXTERIOR_WORDS = {"COURT", "YARD", "GARDEN", "POOL", "ROOF", "TERRACE", "BALCONY", "حوش", "حديقة", "حمام سباحة", "سطح"}
INTERIOR_WORDS = {"BEDROOM", "MASTER BED ROOM", "LIVING", "DINING", "RECEPTION", "SALOON", "MAJLIS", "DEWANEYA", "DRIVER",
                  "MAID", "KITCHEN", "PANTRY", "LAUNDRY", "BATH", "W.C", "WASH", "LOBBY", "CORRIDOR", "HALL"}
WET_WORDS = {"BATH", "W.C", "KITCHEN", "PANTRY", "LAUNDRY", "IRONING"}


def classify(label=None, project_decision=None, enclosed=None, roofed=None, facade_opening_doorless=False):
    """UP-SPACE-001 / UP-SPACE-002: INTERIOR, EXTERIOR, POSSIBLY_EXTERIOR, UNKNOWN or HELD_CONFLICT."""
    if project_decision:
        return project_decision, "UP-SPACE-002 project decision"
    words = {w.strip().upper() if w.isascii() else w.strip() for w in (label or "").split("/") if w.strip()}
    if words & {w.upper() if w.isascii() else w for w in EXTERIOR_WORDS}:
        if enclosed and roofed:
            return "HELD_CONFLICT", "exterior word on a space the drawing encloses and roofs (UP-SPACE-001: a label alone never decides)"
        return "EXTERIOR", "UP-SPACE-001 exterior room word"
    if words & INTERIOR_WORDS:
        return "INTERIOR", "UP-SPACE-001 interior room word"
    if facade_opening_doorless:
        return "POSSIBLY_EXTERIOR", "UP-SPACE-001 unlabelled, doorless facade opening"
    return "UNKNOWN", "UP-SPACE-001 no evidence (never assumed interior)"


def wet_dry(label=None, fixtures=(), basin_only=False):
    """UP-WET-001 / UP-WET-002 / owner Q-06 A."""
    words = {w.strip().upper() for w in (label or "").split("/") if w.strip()}
    if words & WET_WORDS:
        return "WET", "UP-WET-001 wet room word"
    if basin_only:
        return "WET", "owner Q-06 A: basin-only hand-wash space is wet"
    if any(f in ("WC", "SHOWER", "BATH") for f in fixtures):
        return "WET", "UP-WET-002 fixture evidence"
    if label:
        return "DRY", "UP-WET-001 not a wet room"
    return "REVIEW", "UP-WET-002 unlabelled, no fixture: no wet and no dry scope"


def floor_family(status, kind):
    if status != "INTERIOR":
        return "NONE (no Urban default outside the enclosed building)"
    if kind == "WET":
        return "TILE BY_SPEC (URBAN-WET-FLOOR-TILED@v1)"
    if kind == "DRY":
        return "PORCELAIN (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1)"
    return "HELD (finish needs the wet / dry decision)"


def floor_area(space, deduct=(), cabinetry=()):
    """shapely polygons: space minus voids / shafts / treads / walls-plinths-curbs; cabinetry never deducted."""
    from shapely.ops import unary_union
    cut = unary_union(list(deduct)) if deduct else None
    g = space.difference(cut) if cut is not None else space
    _ = cabinetry  # URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1: the floor finish continues under fixed joinery
    return g.area


# ---------------------------------------------------------------------------------------------------------------- fixture
def _fixture(transform, unit):
    """Synthetic villa (not Alsenan), hand values in m2. transform maps (x, y) in metres; unit scales the drawing."""
    from shapely.geometry import Polygon, Point
    from shapely import affinity

    def P(pts):
        g = Polygon([(x * unit, y * unit) for x, y in pts])
        return transform(g)

    def m2(a):  # back to metres
        return a / unit / unit

    out = {}
    bed = P([(0, 0), (5, 0), (5, 4), (0, 4)])
    wardrobe = P([(0, 0), (2, 0), (2, 0.6), (0, 0.6)])
    out["bedroom with wardrobe"] = (m2(floor_area(bed, cabinetry=[wardrobe])), 20.0,
                                    classify("BEDROOM")[0], wet_dry("BEDROOM")[0])
    living = P([(5, 0), (11, 0), (11, 4), (5, 4)])
    half_wall = P([(8, 0), (8.1, 0), (8.1, 2), (8, 2)])  # split by a half wall: one space, its footprint not floor
    out["living split by a half wall"] = (m2(floor_area(living, deduct=[half_wall])), 23.8,
                                          classify("LIVING")[0], wet_dry("LIVING")[0])
    terrace = P([(0, 4), (3, 4), (3, 6), (0, 6)])  # covered, open on one side
    out["covered terrace"] = (m2(terrace.area), 6.0, classify("TERRACE", enclosed=False, roofed=True)[0], "-")
    court = P([(0, 6), (8, 6), (8, 11), (0, 11)])
    pool = transform(Point(6 * unit, 8.5 * unit).buffer(1.0 * unit, quad_segs=1024))
    out["open court less pool"] = (m2(floor_area(court, deduct=[pool])), 40.0 - math.pi, classify("COURT")[0], "-")
    out["pool (not a floor)"] = (m2(pool.area), math.pi, classify("POOL")[0], "-")
    bath = P([(11, 0), (13, 0), (13, 2), (11, 2)])
    out["bath"] = (m2(bath.area), 4.0, classify("BATH")[0], wet_dry("BATH")[0])
    basin = P([(11, 2), (12.5, 2), (12.5, 3), (11, 3)])
    out["basin-only lobby"] = (m2(basin.area), 1.5, classify(None)[0], wet_dry(None, basin_only=True)[0])
    nolabel = P([(12.5, 2), (13.5, 2), (13.5, 3.5), (12.5, 3.5)])
    out["unlabelled space"] = (m2(nolabel.area), 1.5, classify(None)[0], wet_dry(None)[0])
    garden_in = P([(5, 4), (11, 4), (11, 5.2), (5, 5.2)])
    out["garden strip enclosed and roofed"] = (m2(garden_in.area), 7.2, classify("GARDEN", enclosed=True, roofed=True)[0], "-")
    hall = P([(13, 0), (17, 0), (17, 4), (13, 4)])
    void = P([(14, 1), (16, 1), (16, 3), (14, 3)])
    out["hall with a light well"] = (m2(floor_area(hall, deduct=[void])), 12.0, classify("HALL")[0], wet_dry("HALL")[0])
    return out


EXPECT_CLASS = {"bedroom with wardrobe": ("INTERIOR", "DRY"), "living split by a half wall": ("INTERIOR", "DRY"),
                "covered terrace": ("EXTERIOR", "-"), "open court less pool": ("EXTERIOR", "-"),
                "pool (not a floor)": ("EXTERIOR", "-"), "bath": ("INTERIOR", "WET"),
                "basin-only lobby": ("UNKNOWN", "WET"), "unlabelled space": ("UNKNOWN", "REVIEW"),
                "garden strip enclosed and roofed": ("HELD_CONFLICT", "-"),
                "hall with a light well": ("INTERIOR", "DRY")}


def selftest():
    from shapely import affinity
    variants = {
        "m": (lambda g: g, 1.0),
        "mm": (lambda g: g, 1000.0),
        "rot37": (lambda g: affinity.rotate(g, 37, origin=(0, 0)), 1.0),
        "mirror": (lambda g: affinity.scale(g, -1, 1, origin=(0, 0)), 1.0),
        "rot37+mirror mm": (lambda g: affinity.rotate(affinity.scale(g, -1, 1, origin=(0, 0)), 37, origin=(0, 0)), 1000.0),
    }
    n = bad = 0
    for vn, (tf, unit) in variants.items():
        for name, (got, want, st, kind) in _fixture(tf, unit).items():
            n += 1
            ok = abs(got - want) < 1e-3 and (st, kind) == EXPECT_CLASS[name]
            if not ok:
                bad += 1
                print("FAIL", vn, name, round(got, 4), want, st, kind)
    # missing never becomes 0: a held row keeps no number in a confirmed total
    rows = [{"status": "HELD", "m2": None}, {"status": "MEASURED", "m2": 2.0}]
    if sum(r["m2"] for r in rows if r["status"] == "MEASURED") != 2.0 or any(r["m2"] == 0 for r in rows):
        bad += 1
    print(f"fixture: {n} cases x hand values, {n - bad} PASS, {bad} FAIL")
    return bad == 0


# --------------------------------------------------------------------------------------------------------- Alsenan ledger
# area_m2 = the floor quantity of the row (None when HELD with no single value); range_m2 for a HELD range.
# status: MEASURED (geometry / printed), CALCULATED (derived), HELD (cause), EXCLUDED (reason), STAIR (stair element:
# stair lane, not floor area). Sources: V29 = ARCH_TAKEOFF_V2.9 floor reconciliation of the Drive DXF (sha ab54dd55),
# T-074 wet hand table (merged), T-086 finish table (merged), T-088 printed sizes, T-111 stair ledger, T-122 / T-129
# arrival landings, T-071 exterior spaces, T-123 side passage, T-127 pool court, T-147 room regions, T153 = this run.
def R(fl, sid, labels, space, ins, why_ins, kind, why_kind, family, status, area, src, fr=None, fr_m2=None, verdict="",
      note="", rng=None):
    return dict(floor=fl, id=sid, labels=labels, space=space, in_out=ins, in_out_evidence=why_ins, wet_dry=kind,
                wet_dry_rule=why_kind, floor_family=family, status=status, area_m2=area, range_m2=rng, source=src,
                freelancer_row=fr, freelancer_m2=fr_m2, verdict=verdict, note=note)


POR = "PORCELAIN (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1; no sheet specifies a floor finish, T-091)"
WET = "TILE, type BY_SPEC (URBAN-WET-FLOOR-TILED@v1)"
IW = "UP-SPACE-001 interior room word; enclosed by the wall network"
CAB = "; cabinetry not deducted (URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1)"

WET_T074 = [  # (floor, id, space, area, freelancer m2, verdict) - T-074 hand table, verified and merged
    ("GF", "GF-W01", "WASH / مغسلة by the dewaneya (basin-only, Q-06 A)", 3.1325, 3.15, "RULE_DIFFERENCE (T-074)"),
    ("GF", "GF-W02", "W.C. / مرحاض by the dewaneya", 3.375, 3.37, "AGREE"),
    ("GF", "GF-W03", "W.C. / مرحاض driver", 1.95, 1.95, "AGREE"),
    ("GF", "GF-W04", "KITCHEN / مطبخ", 9.63, 9.55, "ENGINE_RIGHT (T-074)"),
    ("GF", "GF-W05", "W.C. / مرحاض stair core 175 x 135", 2.3625, 2.36, "AGREE"),
    ("GF", "GF-W06", "basin space by the stair 110 x 135, no label (Q-06 A)", 1.485, 1.70, "RULE_DIFFERENCE (T-074)"),
    ("GF", "GF-W07", "W.C. / مرحاض core 289 x 167", 2.6752, 2.67, "AGREE"),
    ("GF", "GF-W08", "W.C. / مرحاض core 245 x 167", 2.3676, 2.30, "ENGINE_RIGHT (T-074)"),
    ("GF", "GF-W09", "Wash / مغسلة core lobby, 2 basins (Q-06 A)", 4.7321, 4.73, "AGREE"),
    ("GF", "GF-W10", "BATH / حمام of the master bed room", 3.7173, 3.70, "AGREE"),
    ("1F", "1F-W01", "BATH / حمام west, upper", 5.0225, 5.00, "AGREE"),
    ("1F", "1F-W02", "BATH / حمام west, lower", 5.0225, 5.00, "AGREE"),
    ("1F", "1F-W03", "LAUNDRY / غسيل", 10.151, 10.00, "ENGINE_RIGHT (T-074)"),
    ("1F", "1F-W04", "W.C. / مرحاض by the laundry", 2.646, 2.59, "ENGINE_RIGHT (T-074)"),
    ("1F", "1F-W05", "BATH / حمام by the laundry", 3.5775, 3.60, "AGREE"),
    ("1F", "1F-W06", "BATH / حمام east 210 x 225", 4.725, 4.72, "AGREE"),
    ("2F", "2F-W01", "W.C. / مرحاض roof floor", 5.55, 5.62, "ENGINE_RIGHT (T-074)"),
]


def alsenan_ledger():
    rows = []
    # ---------------------------------------------------------------- GF interior, dry
    rows += [
        R("GF", "GF-D01", "DEWANEYA / ديوانية", "dewaneya 400 x 630 less the R1.10 corner", "INTERIOR", IW, "DRY",
          "UP-WET-001 not a wet room", POR, "MEASURED", 24.940, "V29 face 24.9403 = T-088 printed 24.940 = T153 face 24.9391" + CAB,
          "ديوانيه", 24.84, "AGREE (+0.4 %, drawn face vs his rounded dimensions)"),
        R("GF", "GF-D02", "DRIVER / سائق", "driver room 175 x 450", "INTERIOR", IW, "DRY", "UP-WET-001", POR, "MEASURED",
          7.875, "printed 1.75 x 4.50 = V29 7.875 = T153 7.875", "سايق", 7.87, "AGREE"),
        R("GF", "GF-D03", "MASTER BED ROOM", "master bed room", "INTERIOR", IW, "DRY", "UP-WET-001", POR, "MEASURED",
          16.550, "V29 16.5496; T-147 region 16.557", "غرفه نوم رئيسيه", 16.66, "AGREE (-0.7 %)"),
        R("GF", "GF-D04", "DINING / RECEPTION / SALOON (+ entrance hall and the hall to the master bed room)",
          "open room, porcelain part", "INTERIOR", IW, "DRY", "UP-WET-001 (pantry split out as wet)", POR, "CALCULATED",
          108.033, "V29 open-plan floor 118.733 (face 126.928 less round-stair treads 8.194) - pantry 13.500 (printed, "
          "Q-37 A) + open-plan cell 2.800 west of the garden band; = T-086 candidate 108.033",
          "استقبال+طعام + مدخل (with pantry, garden band and stair)", 147.96,
          "RULE_DIFFERENCE like for like (see FLOORS_T153.csv)", "the open room's south limit is the GARDEN band edge "
          "(layer 2 / 5 lines, not walls: V2.9 REVIEW, defect B9 'GARDEN inside a floor zone'); +13.986 if GF-H01 is floor"),
        R("GF", "GF-H01", "GARDEN / حديقة", "garden band 1.30 (drawn) x 10.82 (printed 1082) inside the reception, "
          "south of the round stair", "HELD_CONFLICT", "exterior word GARDEN, but the band is inside the GF south facade "
          "wall (windows) and under the GF roof slab (the 1F plan's +5.50 roof strip 1.30 m wide lies over it, T-071)",
          "-", "-", "HELD (porcelain if floor; none if a planter)", "HELD", 13.986,
          "V29 faces 9.101 (GARDEN, RFI EXTERNAL) + 4.885 (merged band west part)", None, None,
          "UNRESOLVED (owner question proposal P-2)", "freelancer: inside his 137.50 reception + dining row (gross match "
          "147.96 vs 147.90, T-147)"),
        R("GF", "GF-H02", "(no label)", "closed face between the two wedge W.C.s, no door", "UNKNOWN",
          "UP-SPACE-001 no label, no door (a duct or a closed void: not stated)", "REVIEW", "UP-WET-002 no fixture",
          "HELD", "HELD", 1.373, "T153 face 1.3731 (= T-147 GF-X1); V2.9 has no room for it", None, None, "-",
          "not floor until the designer says what it is"),
    ]
    rows.append(R("GF", "GF-W11", "PANTRY / تحضير", "pantry 450 x 300 open to the dining (Q-37 A)", "INTERIOR", IW, "WET",
                  "UP-WET-001 (pantry) + owner Q-37 A", WET, "MEASURED", 13.500,
                  "printed 4.50 x 3.00 (Q-37 A); T-147 region 13.411; inside V29 open face", "(in his dry استقبال+طعام row)",
                  None, "RULE_DIFFERENCE (Q-37 A wet; he tiles it with the dry reception)"))
    for fl, sid, sp, a, fm, v in WET_T074:
        rows.append(R(fl, sid, sp.split(" ")[0], sp, "INTERIOR", IW if "no label" not in sp else
                      "enclosed by walls; basin linework (Q-06 A)", "WET",
                      "owner Q-06 A" if "Q-06" in sp else "UP-WET-001 wet room word", WET, "MEASURED", a,
                      "T-074 hand table (verified, merged)" + CAB, "wet floors row", fm, v))
    rows += [
        R("GF", "GF-S01", "(stair hall)", "main stair hall GF (flights 3.425 + landings 9.050)", "INTERIOR", IW,
          "-", "-", "marble (stair element)", "STAIR", 12.475, "V29 face 12.475; stair ledger T-111 / T-133",
          None, None, "-", "stair finishes are the stair line, not floor area"),
        R("GF", "GF-S02", "(round stair)", "round-stair treads drawn on the GF plan", "INTERIOR", IW, "-", "-",
          "marble (stair element)", "STAIR", 8.194, "V29 STAIR_FLIGHTS in the open face (T-135 union 8.234)",
          None, None, "-", "floor under the rising stair beyond the drawn treads: T-116 NOT_ASSESSED, stays in GF-D04"),
        R("GF", "GF-X01", "(lift)", "lift shaft 180 x 180", "INTERIOR", "shaft", "-", "-", "none", "EXCLUDED", 3.240,
          "printed 1.80 x 1.80 = V29 3.24", None, None, "-", "NOT_APPLICABLE_WITH_EVIDENCE: shaft"),
        R("GF", "GF-X02", "(side passage)", "side passage between annex and house 1.20 x 4.70 at +0.15", "EXTERIOR",
          "owner Q-67 A (condition MET, verifier 2026-10-20 21:05)", "-", "-", "NONE (exterior)", "EXCLUDED", 5.640,
          "T-123 1.560 + 0.240 + 3.600 + 0.240 (verifier); V29 counts its faces 3.600 + 1.560 as INTERNAL unallocated",
          None, None, "ENGINE DEFECT in V2.9 (5.160 m2 exterior counted internal)", "exterior area, finish HELD with the courts"),
    ]
    # ---------------------------------------------------------------- GF exterior (the T-061 held labels)
    ext = "UP-SPACE-001 exterior room word; open to the sky inside the plot boundary walls"
    rows += [
        R("GF", "GF-E01", "COURT / حوش (AT22, AT21)", "west court (street side, beside the annex), to the inner face of "
          "the plot boundary walls", "EXTERIOR", ext, "-", "-", "HELD (OQ-04: no exterior finish scope)", "MEASURED",
          138.761, "T153 polygonization of the GF plan inside the boundary walls (plot 31.37 x 15.00 printed, inner "
          "30.97 x 14.60), split at the building's north-west corner line; of which entrance porch under the 1F block "
          "19.181 (T-121 / T-127 PL-01) and entrance flight E1 footprint 4 x 0.30 x 2.80 = 3.360 (T-111, stair marble)",
          "الحوش الأرضى (one row for all courts)", 151.80, "UNRESOLVED (his row has no breakdown; scope OQ-04)"),
        R("GF", "GF-E02", "COURT / حوش (AT40, AT39)", "north court strip 1.30 wide along the master bed room block",
          "EXTERIOR", ext, "-", "-", "HELD (OQ-04)", "MEASURED", 21.348, "T153, same polygonization (strip 1.300 = "
          "boundary-wall inner face to the bedroom wall face)", "(in his 151.80)", None, "UNRESOLVED"),
        R("GF", "GF-E03", "swimming pool / حمام سباحة (AT20, AT19)", "pool court deck around the pool (east of the "
          "curved glazing), drawn face 17.007 less the pool to its outer shell 9.402", "EXTERIOR", ext + "; T-127 / "
          "Q-68 (slab over it with the printed VOID)", "-", "-", "HELD (OQ-04)", "MEASURED", 7.605,
          "T153: court face 17.007 (T-127 printed gross 16.5245: the drawn face takes in the 0.08 m recess before the "
          "curved frame, T-127 SX-02) - pool r 1.75 clipped at the boundary-wall face 9.402", "(in his 151.80?)", None,
          "UNRESOLVED"),
        R("GF", "GF-X03", "swimming pool / حمام سباحة (AT20, AT19)", "pool water inside the shell (r 1.55) ", "EXTERIOR",
          ext, "-", "-", "none: pool finish is pool scope (no Urban rule, T-071 POOL_NO_MEMBRANE_RULE)", "EXCLUDED", 7.548,
          "DXF arcs r 1.75 / 1.55 about one centre (layers 5 + 2); shell band 1.854", None, None, "-",
          "NOT_APPLICABLE_WITH_EVIDENCE: not a floor"),
    ]
    # ---------------------------------------------------------------- 1F
    rows += [
        R("1F", "1F-D01", "LIVING AREA (+ corridor, connector)", "living zone porcelain (Q-56 A rows)", "INTERIOR", IW,
          "DRY", "UP-WET-001", POR, "HELD", None, "T-122 (merged): face 75.983 = porcelain 33.594 .. 33.711 + landing "
          "4.865 + held 0.520 + void 16.005 + treads 15.405 + footprint 3.560 + residue 2.035", "معيشه", 38.96,
          "RULE_DIFFERENCE (landing marble Q-66 B; he keeps it porcelain)", "range by designer D-23 (0.1175)",
          rng=(33.594, 33.711)),
        R("1F", "1F-S01", "(arrival landing)", "main-stair arrival landing 250 x 195 at +5.50", "INTERIOR", IW, "-", "-",
          "marble (Q-66 B, own stair element)", "STAIR", 4.865, "T-122 drawn 4.865 (printed 4.875)", "(in معيشه)",
          None, "RULE_DIFFERENCE"),
        R("1F", "1F-D02", "MASTER BED ROOM", "west 425 x 450", "INTERIOR", IW, "DRY", "UP-WET-001", POR, "MEASURED",
          19.050, "V29 19.05 (printed 19.125: -0.075 drawn)" + CAB, "غرفه نوم 4", 19.00, "AGREE (+0.3 %)"),
        R("1F", "1F-D03", "MASTER BED ROOM", "east, curved W17, with its entry", "INTERIOR", IW, "DRY", "UP-WET-001",
          POR, "MEASURED", 19.017, "V29 19.0165 (T-147 region 18.829: closing line at the entry)", "غرفه نوم 2", 19.46,
          "UNRESOLVED (curved edge not dimensioned, T-086)"),
        R("1F", "1F-D04", "MASTER BED ROOM", "500 x 365", "INTERIOR", IW, "DRY", "UP-WET-001", POR, "MEASURED", 18.215,
          "V29 18.215 (printed 18.25)", "غرفه نوم 3", 18.25, "AGREE (-0.2 %)"),
        R("1F", "1F-D05", "MASTER BED ROOM", "380 x 430", "INTERIOR", IW, "DRY", "UP-WET-001", POR, "MEASURED", 16.340,
          "printed 3.80 x 4.30 = V29 16.34", "غرفه نوم 1", 17.29, "ENGINE_RIGHT on the room (T-088); his +0.95 is "
          "probably part of the 1.47 x 3.05 passage: UNRESOLVED for the passage"),
        R("1F", "1F-H01", "(no label)", "space by the arch (opens through OP-019), 1.80 x 1.65", "UNKNOWN",
          "UP-SPACE-001 no label (never assumed interior)", "REVIEW", "UP-WET-002 no fixture", "HELD", "HELD", 2.970,
          "V29 face 2.97 = T-147 1F-X1", None, None, "-", "type for the designer"),
        R("1F", "1F-X01", "(lift)", "lift shaft", "INTERIOR", "shaft", "-", "-", "none", "EXCLUDED", 3.240, "V29", None,
          None, "-", "shaft"),
        R("1F", "1F-X02", "VOID (AT215)", "light well over the GF reception (printed VOID 400 x 587)", "INTERIOR",
          "open to below", "-", "-", "none", "EXCLUDED", 16.005, "V29 VOID 16.005 (released UNSUPPORTED: correct)",
          None, None, "-", "no floor at 1F"),
        R("1F", "1F-X03", "VOID (AT225)", "opening in the 1F slab over the pool court (B7 ring inner faces)",
          "EXTERIOR", "open to the sky over the pool court (the 1F plan draws the same inner outline with VOID)", "-",
          "-", "none", "EXCLUDED", 3.690, "T-127 drawn opening 3.6901 (verifier 3.689)", None, None, "-",
          "NOT_APPLICABLE_WITH_EVIDENCE: no floor"),
        R("1F", "1F-E01", "ROOF (AT220)", "GF annex roof seen on the 1F plan, inside the parapet (+4.30)", "EXTERIOR",
          "UP-SPACE-001 exterior word ROOF; outside the 1F walls", "-", "-", "roof: membrane RELEASED (Q-24), screed / "
          "finish HELD (Q-41)", "MEASURED", 55.559, "T-071 55.559 = T-062 hand 55.560", "roof row 285.00 (all roofs)",
          None, "UNRESOLVED as a total (T-071)"),
        R("1F", "1F-E02", "ROOF (AT216)", "GF south-east roof strip seen on the 1F plan (+5.50)", "EXTERIOR",
          "UP-SPACE-001 ROOF; outside the 1F walls", "-", "-", "roof (as 1F-E01)", "MEASURED", 32.721,
          "T-071 32.721 = 18.97 x 1.30 + 1.30 x 6.20", "(in 285.00)", None, "UNRESOLVED as a total"),
    ]
    # ---------------------------------------------------------------- 2F
    rows += [
        R("2F", "2F-D01", "MAID R.", "maid room 300 x 645", "INTERIOR", IW, "DRY", "UP-WET-001", POR, "MEASURED", 19.350,
          "printed 3.00 x 6.45 = V29 19.35", "غرفه خادمه", 19.58, "AGREE (-1.2 %)"),
        R("2F", "2F-D02", "(no room name: area beyond the stair width)", "2F floor 200 x 125 beside the arrival landing",
          "INTERIOR", "enclosed, reached from the stair (no label printed, T-129)", "DRY", "UP-WET-001 not wet", POR,
          "MEASURED", 2.500, "T-129 2.500 (the finish table's 'lobby 8.775' is not a drawn area: 7.375)", "طرقه", 7.70,
          "RULE_DIFFERENCE (arrival marble Q-70 A); +0.325 m2 not traceable in his row"),
        R("2F", "2F-S01", "(arrival landing)", "main-stair arrival landing 250 x 195 at +9.70", "INTERIOR", IW, "-", "-",
          "marble (Q-70 A, condition MET T-129)", "STAIR", 4.875, "T-129", "(in طرقه)", None, "RULE_DIFFERENCE"),
        R("2F", "2F-X01", "(lift)", "lift shaft", "INTERIOR", "shaft", "-", "-", "none", "EXCLUDED", 3.240, "V29", None,
          None, "-", "shaft"),
        R("2F", "2F-E01", "ROOF (AT379, AT385)", "1F roof seen on the 2F plan (+9.70), one face, less the 2 open dome "
          "skylights", "EXTERIOR", "UP-SPACE-001 ROOF; outside the 2F walls", "-", "-", "roof (as 1F-E01)",
          "MEASURED", 115.832, "T-071 146.532 - 2 x 15.350 (verifier 115.817)", "(in 285.00)", None,
          "UNRESOLVED as a total"),
    ]
    return rows


FREELANCER = {  # FIN workbook tiles sheet rows (FREELANCER_RAW_ROWS.json), m2
    "dry": {"GF": 137.5 + 16.66 + 10.46 + 24.84 + 7.87, "1F": 38.96 + 17.29 + 19.46 + 18.25 + 19.0, "2F": 19.58 + 7.7},
    "wet": {"GF": 4.73 + 1.7 + 3.7 + 2.3 + 2.67 + 2.36 + 9.55 + 1.95 + 3.37 + 3.15, "1F": 4.72 + 3.6 + 2.59 + 5.0 + 5.0 + 10.0,
            "2F": 5.62},
    "yard": 151.8,
}
DOORWAY_STRIPS = {"GF": 4.474, "1F": 0.77, "2F": 0.53}  # T-086 released doorway strips (in the wall thickness), porcelain


def totals(rows):
    out = {}
    for fl in ("GF", "1F", "2F"):
        fr = [r for r in rows if r["floor"] == fl]
        dry = sum(r["area_m2"] for r in fr if r["wet_dry"] == "DRY" and r["status"] in ("MEASURED", "CALCULATED"))
        dry_rng = [r["range_m2"] for r in fr if r["wet_dry"] == "DRY" and r["status"] == "HELD" and r["range_m2"]]
        lo = dry + sum(a for a, b in dry_rng)
        hi = dry + sum(b for a, b in dry_rng)
        wet = sum(r["area_m2"] for r in fr if r["wet_dry"] == "WET" and r["status"] == "MEASURED")
        held = {r["id"]: r["area_m2"] for r in fr if r["status"] == "HELD" and r["area_m2"] is not None}
        stair = sum(r["area_m2"] for r in fr if r["status"] == "STAIR")
        ext = sum(r["area_m2"] for r in fr if r["in_out"] == "EXTERIOR" and r["status"] == "MEASURED")
        out[fl] = {"dry_porcelain_low": round(lo, 3), "dry_porcelain_high": round(hi, 3),
                   "doorway_strips": DOORWAY_STRIPS[fl], "wet_tiled": round(wet, 3),
                   "interior_floor_low": round(lo + wet + DOORWAY_STRIPS[fl], 3),
                   "interior_floor_high": round(hi + wet + DOORWAY_STRIPS[fl], 3),
                   "held_interior_m2": {k: v for k, v in held.items()}, "stair_marble_listed": round(stair, 3),
                   "exterior_measured": round(ext, 3),
                   "freelancer_dry": round(FREELANCER["dry"][fl], 2), "freelancer_wet": round(FREELANCER["wet"][fl], 2)}
    return out


def readd(rows):
    """re-add against the merged sets: 17 wet areas 72.12 (T-074) and the 10 dry-tile rooms 194.98 (T-086)."""
    by = {r["id"]: r for r in rows}
    wet17 = sum(a for _, _, _, a, _, _ in WET_T074)
    ten_old = {"dewaneya": 24.940332, "GF master": 16.54964, "driver": 7.875, "1F living": 44.869353,
               "1F west": 19.05, "1F east": 19.016545, "1F 500x365": 18.215001, "1F 380x430": 16.34,
               "maid": 19.350001, "2F lobby": 8.775}
    same = ["GF-D01", "GF-D03", "GF-D02", "1F-D02", "1F-D03", "1F-D04", "1F-D05", "2F-D01"]
    unchanged = sum(by[i]["area_m2"] for i in same)
    lo = unchanged + by["1F-D01"]["range_m2"][0] + by["2F-D02"]["area_m2"]
    hi = unchanged + by["1F-D01"]["range_m2"][1] + by["2F-D02"]["area_m2"]
    old = sum(ten_old.values())
    moved = {"1F landing to marble (Q-66 B)": 4.865, "1F held strips D-13 + D-23": 0.520,
             "1F treads / stair footprint the released line kept (T-116)": round(44.869353 - 33.594 - 4.865 - 0.520, 4),
             "2F arrival to marble (Q-70 A)": 4.875, "2F wall inside the printed 450 x 195 (T-129)": 1.400}
    return {"wet17_m2": round(wet17, 4), "wet17_merged": 72.122, "wet17_diff": round(wet17 - 72.122, 4),
            "wet_with_pantry": round(wet17 + 13.5, 4), "T086_wet_with_pantry": 85.62,
            "ten_dry_old_m2": round(old, 3), "ten_dry_now_low": round(lo, 3), "ten_dry_now_high": round(hi, 3),
            "ten_dry_change": [round(lo - old, 3), round(hi - old, 3)], "explained_by": moved}


def write(outdir):
    rows = alsenan_ledger()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with open(out / "SPACES_T153.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["range_m2"] = "" if not r["range_m2"] else f"{r['range_m2'][0]} .. {r['range_m2'][1]}"
            w.writerow(r)
    t = totals(rows)
    with open(out / "FLOORS_T153.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["floor", "dry porcelain m2 (low..high)", "doorway strips m2", "wet tiled m2", "interior floor m2",
                    "held interior m2", "stair marble listed m2", "exterior measured m2", "freelancer dry m2",
                    "freelancer wet m2", "wet diff m2 (%)"])
        for fl, v in t.items():
            wd = v["wet_tiled"] - v["freelancer_wet"]
            w.writerow([fl, f"{v['dry_porcelain_low']} .. {v['dry_porcelain_high']}", v["doorway_strips"], v["wet_tiled"],
                        f"{v['interior_floor_low']} .. {v['interior_floor_high']}",
                        "; ".join(f"{k} {a}" for k, a in v["held_interior_m2"].items()), v["stair_marble_listed"],
                        v["exterior_measured"], v["freelancer_dry"], v["freelancer_wet"],
                        f"{wd:+.3f} ({wd / v['freelancer_wet'] * 100:+.1f} %)"])
    summ = {"task": "T-153", "rows": len(rows), "totals": t, "readd": readd(rows)}
    (out / "summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--check" in a:
        ok = selftest()
        r = readd(alsenan_ledger())
        print("re-add:", json.dumps(r, ensure_ascii=False))
        ok = ok and abs(r["wet17_diff"]) < 0.001
        sys.exit(0 if ok else 1)
    if "--out" in a:
        write(a[a.index("--out") + 1])
