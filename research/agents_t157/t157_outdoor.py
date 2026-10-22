"""T-157 outdoor areas: inside / outside classification and outdoor finish lines (research only, NO REPO CODE).

No engine module is changed or imported. Two parts:

1. The general method (any villa or chalet), used by the synthetic fixture:
   - `classify`: INSIDE / OUTSIDE / OUTSIDE_COVERED / HELD from drawing evidence, in this order:
       open to the sky (no slab or roof drawn over it on the plan above, the roof plan or a section)  -> OUTSIDE;
       roofed but open to outside air (no enclosing wall, door or glazing on its open side)           -> OUTSIDE_COVERED;
       roofed and enclosed: an exterior word (GARDEN, COURT, ...) is a CONFLICT (UP-SPACE-001: a label alone never
       decides; designer list D-48) -> HELD_CONFLICT; otherwise INSIDE;
       no roof evidence (a missing upper plan or section)                                              -> HELD.
     A covered space whose printed level is missing cannot be told court-level from raised: HELD.
   - `finish`: the owner rule OUTDOOR_FLOORS (2026-10-21, answers OQ-04) with its additions of 20:45 and 23:20:
       chalet open court -> INTERLOCK; villa front / side area -> CERAMIC; a side strip or side passage along the
       house, any project type -> PORCELAIN_CERAMIC (part of the house, never interlock); outside steps and their
       landing -> MARBLE (owner rule + UP-STAIR-001: tread, riser and landing of every stair assembly incl. external
       steps); covered porch at court level -> area MEASURED, material HELD (owner decides); pool deck -> HELD;
       planter -> NONE (not a floor, deducted); project type unknown -> HELD (never guessed); a villa court that is not
       recorded as front or side -> HELD.
   - areas: shoelace on the drawn polygon, every element standing on an area (steps, landing, planter, the covered
     porch measured as its own line) deducted from the area that holds it, so no m2 is counted twice; units m or mm.
   - outside steps: UP-STAIR-002 drawn geometry governs; tread m2 = treads x tread x width, visible riser m2 = risers x
     (rise - tread build-up 0.030, UP-STAIR-006) x width (UP-STAIR-003, owner stair rule S-2); the owner stair
     calculator runs as a CHECK only (S-1): risers = ceil(H / 0.16) with a 1e-9 tolerance; a drawn riser above 0.16 m
     is a flagged finding, never a silent change.
   - UP-QTY-STATUS-001: a HELD line keeps its measured area (never 0) and is never added to a released total.

2. `alsenan_ledger`: the Alsenan outdoor lines (areas and printed dimensions only, no coordinates), their sheet
   evidence, the re-add to T-153 and the comparison with the freelancer's yard / entrance-marble rows.

Usage:  python3 -I t157_outdoor.py --check          synthetic non-Alsenan fixture + Alsenan re-adds (exit 1 on a fail)
        python3 -I t157_outdoor.py --out <dir>       writes AREAS_T157.csv and summary.json
"""
import csv
import json
import math
import sys
from pathlib import Path

EXTERIOR_WORDS = {"COURT", "YARD", "GARDEN", "POOL", "TERRACE", "PORCH", "حوش", "حديقة"}
MAX_RISER = 0.16
TREAD_BUILD_UP = 0.030  # UP-STAIR-006 default; a drawn tread detail replaces it


# ----------------------------------------------------------------------------------------------- general method
def area(poly, unit="m"):
    """Shoelace area of a simple polygon given as [(x, y), ...] in m or mm; result in m2."""
    k = 1000.0 if unit == "mm" else 1.0
    s = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0 / (k * k)


def classify(label=None, roofed=None, enclosed=None, level=None, covered_needs_level=True):
    """Inside / outside from drawing evidence (UP-SPACE-001 order; a label alone never decides)."""
    words = {w.strip().upper() if w.isascii() else w.strip() for w in (label or "").split("/") if w.strip()}
    if roofed is None:
        return "HELD", "no roof evidence (upper plan / roof plan / section missing)"
    if not roofed:
        return "OUTSIDE", "open to the sky"
    if not enclosed:
        if covered_needs_level and level is None:
            return "HELD", "covered, open to outside air, but no printed level: court level or raised not known"
        return "OUTSIDE_COVERED", "roofed, open to outside air (no enclosing wall, door or glazing)"
    if words & EXTERIOR_WORDS:
        return "HELD_CONFLICT", "exterior word on a space the drawing encloses and roofs (UP-SPACE-001; D-48)"
    return "INSIDE", "enclosed and roofed"


def finish(kind, cls, project_type):
    """Owner rule OUTDOOR_FLOORS 2026-10-21 (+ additions 20:45 / 23:20) and UP-STAIR-001."""
    if cls in ("HELD", "HELD_CONFLICT"):
        return "HELD", "classification held"
    if cls == "INSIDE":
        return "NOT_OUTDOOR", "interior floor: T-153 ledger"
    if kind == "planter":
        return "NONE", "planter: not a floor, deducted from the area that holds it"
    if kind in ("steps", "landing"):
        return "MARBLE", "owner rule: outside stairs marble; UP-STAIR-001 tread, riser and landing"
    if kind in ("side", "side_passage"):
        return "PORCELAIN_CERAMIC", "owner addition 20:45: sides are never interlock, part of the house"
    if kind == "porch":
        return "MATERIAL_HELD", "owner 23:20: porch at court level, own measured line, kind and price decided later"
    if kind == "pool_deck":
        return "HELD", "owner: pool deck not decided"
    if project_type not in ("chalet", "villa"):
        return "HELD", "project type not recorded (never guessed)"
    if kind == "court":
        if project_type == "chalet":
            return "INTERLOCK", "owner rule: chalet outdoor court interlock"
        return "HELD", "villa court not recorded as front or side area"
    if kind == "front" and project_type == "villa":
        return "CERAMIC", "owner rule: house outdoor front area ceramic"
    return "HELD", "no owner rule for this outdoor kind"


def risers_needed(height, max_riser=MAX_RISER):
    """Owner stair rule step 1 with the 1e-9 tolerance of its implementation note."""
    return int(math.ceil(height / max_riser - 1e-9))


def outside_steps(rise_total, risers_drawn, treads_drawn, tread, width, build_up=TREAD_BUILD_UP):
    """UP-STAIR-002 drawn geometry; UP-STAIR-003 visible riser; owner stair rule as a check (S-1)."""
    actual = rise_total / risers_drawn
    flags = []
    if actual > MAX_RISER + 1e-9:
        flags.append("drawn riser %.3f m above %.2f m (owner stair rule check, drawing governs)" % (actual, MAX_RISER))
    if tread < 0.28 - 1e-9:
        flags.append("tread under 0.28 m")
    if treads_drawn != risers_drawn - 1:
        flags.append("drawn treads %d != risers - 1 (single flight)" % treads_drawn)
    return {
        "risers": risers_drawn, "treads": treads_drawn, "actual_riser": round(actual, 4),
        "visible_riser": round(actual - build_up, 4),
        "tread_m2": round(treads_drawn * tread * width, 4),
        "riser_m2": round(risers_drawn * (actual - build_up) * width, 4),
        "rule_check_risers": risers_needed(rise_total), "flags": flags,
    }


def ledger(spaces, project_type, unit="m"):
    """Measure each space, deduct the pieces it holds, classify and give its finish; returns {name: row}."""
    rows = {}
    for s in spaces:
        a = area(s["poly"], unit) - sum(area(p, unit) for p in s.get("holds", []))
        cls, why = classify(s.get("label"), s.get("roofed"), s.get("enclosed"), s.get("level"),
                            covered_needs_level=s["kind"] not in ("side_passage",))
        fin, fwhy = finish(s["kind"], cls, project_type)
        rows[s["name"]] = {"area": round(a, 4), "class": cls, "finish": fin, "why": why + "; " + fwhy}
    return rows


# ------------------------------------------------------------------------------------- synthetic fixture (not Alsenan)
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def fixture(level_porch=0.15):
    """A chalet on a 24.0 x 14.0 m plot (inner faces). House x 10..24, y 0..12.5; annex 0..5 x 0..6; store 6.2..10 x 0..5;
    roofed side passage 5..6.2 x 0..5 (upper floor over it, open mouth); covered porch under the upper-floor overhang
    7..10 x 8..12 with 4 outside steps 8.8..10 x 9..11.5; planter 0..6 x 13.4..14 in the court; north side strip
    10..24 x 12.5..14; a GARDEN band 12..22 x 0..1.3 inside the house (enclosed and roofed)."""
    court = [(0, 6), (5, 6), (5, 5), (10, 5), (10, 14), (0, 14)]  # plot west part less annex, store and passage
    porch = rect(7, 8, 10, 12)
    steps = rect(8.8, 9, 10, 11.5)
    planter = rect(0, 13.4, 6, 14)
    return [
        {"name": "court", "kind": "court", "label": "COURT", "poly": court, "holds": [porch, planter],
         "roofed": False, "enclosed": False, "level": 0.15},
        {"name": "porch", "kind": "porch", "label": "", "poly": porch, "holds": [steps],
         "roofed": True, "enclosed": False, "level": level_porch},
        {"name": "steps", "kind": "steps", "label": "", "poly": steps, "roofed": True, "enclosed": False, "level": 0.15},
        {"name": "planter", "kind": "planter", "label": "planter", "poly": planter, "roofed": False, "enclosed": False,
         "level": 0.15},
        {"name": "side_strip", "kind": "side", "label": "COURT", "poly": rect(10, 12.5, 24, 14), "roofed": False,
         "enclosed": False, "level": 0.15},
        {"name": "side_passage", "kind": "side_passage", "label": "", "poly": rect(5, 0, 6.2, 5), "roofed": True,
         "enclosed": False, "level": 0.15},
        {"name": "garden_band", "kind": "court", "label": "GARDEN", "poly": rect(12, 0, 22, 1.3), "roofed": True,
         "enclosed": True, "level": 1.00},
    ]


FIXTURE_EXPECTED = {  # hand values (m2) and expected classes / finishes
    "court": (140 - 30 - 19 - 6 - 12 - 3.6, "OUTSIDE", "INTERLOCK"),        # 69.4
    "porch": (12 - 3.0, "OUTSIDE_COVERED", "MATERIAL_HELD"),                 # 9.0
    "steps": (1.2 * 2.5, "OUTSIDE_COVERED", "MARBLE"),                       # 3.0
    "planter": (6 * 0.6, "OUTSIDE", "NONE"),                                 # 3.6
    "side_strip": (14 * 1.5, "OUTSIDE", "PORCELAIN_CERAMIC"),                # 21.0
    "side_passage": (1.2 * 5, "OUTSIDE_COVERED", "PORCELAIN_CERAMIC"),       # 6.0
    "garden_band": (10 * 1.3, "HELD_CONFLICT", "HELD"),                      # 13.0
}


def transform(spaces, fn):
    out = []
    for s in spaces:
        t = dict(s)
        t["poly"] = [fn(p) for p in s["poly"]]
        t["holds"] = [[fn(p) for p in h] for h in s.get("holds", [])]
        out.append(t)
    return out


def run_check():
    fails = []
    n = 0

    def ok(cond, msg):
        nonlocal n
        n += 1
        if not cond:
            fails.append(msg)

    c, s_ = math.cos(math.radians(37)), math.sin(math.radians(37))
    cases = {
        "m": (fixture(), "m"),
        "mm": (transform(fixture(), lambda p: (p[0] * 1000, p[1] * 1000)), "mm"),
        "rotated 37 deg": (transform(fixture(), lambda p: (p[0] * c - p[1] * s_ + 5, p[0] * s_ + p[1] * c - 3)), "m"),
        "mirrored": (transform(fixture(), lambda p: (-p[0], p[1])), "m"),
        "mirrored + rotated, mm": (transform(fixture(), lambda p: ((-p[0] * c - p[1] * s_) * 1000,
                                                                   (-p[0] * s_ + p[1] * c) * 1000)), "mm"),
    }
    for cname, (sp, unit) in cases.items():
        rows = ledger(sp, "chalet", unit)
        for name, (a, cls, fin) in FIXTURE_EXPECTED.items():
            r = rows[name]
            ok(abs(r["area"] - a) < 1e-6, "%s %s area %.4f != %.4f" % (cname, name, r["area"], a))
            ok(r["class"] == cls, "%s %s class %s != %s" % (cname, name, r["class"], cls))
            ok(r["finish"] == fin, "%s %s finish %s != %s" % (cname, name, r["finish"], fin))
        # re-add: the court face = court + porch + steps + planter (each m2 once)
        face = 140 - 30 - 19 - 6
        ok(abs(rows["court"]["area"] + rows["porch"]["area"] + rows["steps"]["area"] + rows["planter"]["area"] - face)
           < 1e-6, "%s court face re-add" % cname)
    # missing level: the covered porch is HELD, its area kept (never 0)
    rows = ledger(fixture(level_porch=None), "chalet")
    ok(rows["porch"]["class"] == "HELD" and rows["porch"]["finish"] == "HELD", "missing level porch not HELD")
    ok(abs(rows["porch"]["area"] - 9.0) < 1e-6 and rows["porch"]["area"] > 0, "missing level porch area lost")
    # project type unknown: court HELD, sides still porcelain / ceramic, steps still marble
    rows = ledger(fixture(), None)
    ok(rows["court"]["finish"] == "HELD", "unknown project type: court not HELD")
    ok(rows["side_strip"]["finish"] == "PORCELAIN_CERAMIC", "unknown project type: side not porcelain")
    ok(rows["steps"]["finish"] == "MARBLE", "unknown project type: steps not marble")
    # villa: a court not recorded as front / side is HELD; a front area is ceramic
    rows = ledger(fixture(), "villa")
    ok(rows["court"]["finish"] == "HELD", "villa court not HELD")
    ok(finish("front", "OUTSIDE", "villa")[0] == "CERAMIC", "villa front not ceramic")
    # no roof evidence -> HELD
    ok(classify("COURT", None, False, 0.15)[0] == "HELD", "no roof evidence not HELD")
    # outside steps: rise 0.85 drawn with 5 risers / 4 treads 0.30 x 2.50
    st = outside_steps(0.85, 5, 4, 0.30, 2.50)
    ok(abs(st["tread_m2"] - 3.0) < 1e-9, "steps tread m2")
    ok(abs(st["riser_m2"] - 5 * 0.14 * 2.5) < 1e-9, "steps visible riser m2")
    ok(st["rule_check_risers"] == 6 and st["flags"], "steps check flag (0.17 > 0.16)")
    st = outside_steps(0.64, 4, 3, 0.30, 1.20)
    ok(not st["flags"] and st["rule_check_risers"] == 4, "steps 0.16 exact: no flag")
    ok(risers_needed(4.48) == 28, "owner note: 4.48 m -> 28 risers")
    return n, fails


# ------------------------------------------------------------------------------------------------ Alsenan ledger
# Areas measured this run on the architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip): the GF
# plan polygonized inside the inner faces of the plot boundary walls (T-147 rooms.py, as T-153) = one open face 177.1154
# m2, cut along drawn lines (no coordinates are committed). Printed values from p7757_arch_sheet03 (GF), sheet04 (1F),
# sheet10 (section A-A), Pages_11-12 p.11 (section B-B).
T153 = {"west_court": 138.761, "north_strip": 21.348, "pool_court_face": 17.007, "deck": 7.605, "pool_outer": 9.402,
        "courts": 167.714, "face": 177.115, "side_passage": 5.640, "garden_band": 13.986}
FACE = 177.1154

ROWS = [
    # id, space / surface, classification, evidence, drawn m2, hand m2, hand formula, finish, status, rule, freelancer
    ("OD-01", "west court, open part (GF, street side, beside the annex)", "OUTSIDE",
     "open to the sky: section B-B p.11 (court +0.15 between the annex roof +4.30 and the house, nothing over it); 1F plan "
     "sheet04 draws no slab or roof over it; GF sheet03 COURT / حوش +0.15", 119.5416, None,
     "west court 138.760 less the area under the 1F overhang 19.218", "INTERLOCK (owner choice; renders show stone: "
     "'owner choice, differs from render', T-161)", "DRAWING-CONFIRMED area; finish ASSUMED — OWNER-APPROVED (owner "
     "rule OUTDOOR_FLOORS + decision 23:20)", "OUTDOOR_FLOORS chalet court", "yard 151.80 (part)"),
    ("OD-02", "covered porch at court level (under the 1F master-bedroom block, west of and north of the entrance "
     "steps)", "OUTSIDE_COVERED",
     "section B-B p.11: court +0.15 runs under the 1F slab (clear 5.35 printed to +5.50), open on the court side, no "
     "wall, door or glazing; GF sheet03 level +0.15 inside it, 1F outline dashed over it", 10.6785, 10.680,
     "2.00 x 4.30 (west of the steps) + 1.20 x 1.50 (north of the steps) + 1.40 x 0.20 (north of the 0.40 wall stub); "
     "4.30 = chain 0.20 slab edge (sheet04) + 0.40 + 0.90 + 2.80 (sheet03)", "MATERIAL HELD (owner decides: wood / "
     "ceramic / marble)", "DRAWING-CONFIRMED area; finish HELD", "owner 23:20 porch line", "yard 151.80 (part)"),
    ("OD-03", "entrance steps E1 (outside stairs), treads", "OUTSIDE_COVERED",
     "GF sheet03: 4 treads drawn 0.30 x 2.80 (printed 280), +0.15 to +1.00; section B-B p.11 draws 5 risers", 3.3594,
     3.360, "4 x 0.30 x 2.80", "MARBLE", "DRAWING-CONFIRMED; marble by owner rule + UP-STAIR-001",
     "OUTDOOR_FLOORS outside stairs; UP-STAIR-001/-002/-003/-006", "entrance marble: 5 steps x 2.80"),
    ("OD-04", "entrance steps E1, visible risers", "OUTSIDE_COVERED",
     "rise 1.00 - 0.15 = 0.85 printed levels, 5 risers drawn = 0.170 each; tread build-up 0.030 (UP-STAIR-006)", None,
     1.960, "5 x (0.170 - 0.030) x 2.80", "MARBLE", "DRAWING-CONFIRMED; FLAG: drawn riser 0.170 > 0.16 (owner stair "
     "rule check: 6 risers of 0.142 would be needed; drawing governs, S-1)", "UP-STAIR-003; owner stair rule S-1 / S-2",
     "entrance marble: 5 steps x 2.80"),
    ("OD-05", "entrance top landing (outside the main door, +1.00, under the 1F)", "OUTSIDE_COVERED",
     "GF sheet03 prints 140 x 370 outside the double door; section B-B p.11 landing at the hall level +1.00 at the top of "
     "the 5 risers", 5.1794, 5.180, "1.40 x 3.70", "MARBLE (landing of an external stair assembly)",
     "DRAWING-CONFIRMED area; marble by UP-STAIR-001 (tread, riser and landing of every assembly incl. external steps)",
     "UP-STAIR-001", "entrance marble: landing 5.10"),
    ("OD-06", "north side walk (strip between the north boundary wall and the stair / W.C. / master-bedroom / pool "
     "block)", "OUTSIDE",
     "section A-A sheet10: +0.15 strip open to the sky between the house north wall and the boundary wall; 1F plan "
     "sheet04 prints 150 there with nothing over it", 21.0142, 21.021,
     "1.30 x 16.17 (boundary-wall inner face to the house north face; NW corner column outer face to the east boundary "
     "inner face)", "PORCELAIN / CERAMIC (side, part of the house)", "DRAWING-CONFIRMED area; finish ASSUMED — "
     "OWNER-APPROVED (owner addition 20:45)", "OUTDOOR_FLOORS sides", "yard 151.80 (part)"),
    ("OD-06M", "north side walk, OWNER MANUAL METHOD (kept beside OD-06, never replaced)", "OUTSIDE", "owner 20:45: printed "
     "1500 x printed 15970", None, 23.955, "1.50 x 15.97", "PORCELAIN / CERAMIC", "ASSUMED — OWNER-APPROVED (manual "
     "method)", "owner manual method", "-"),
    ("OD-07", "pool court deck (east of the curved glazing, around the pool, incl. the 1.30 x 0.20-0.25 band under the "
     "1F edge at its mouth)", "OUTSIDE",
     "GF sheet03 +0.15; T-127 / Q-68: slab over it with the printed VOID", 7.9392, None,
     "pool court face 17.3414 less the pool to its outer shell r 1.75 clipped at the boundary face 9.4022",
     "HELD (owner: pool deck not decided)", "DRAWING-CONFIRMED area; finish HELD", "owner rule OUTDOOR_FLOORS",
     "not in his yard"),
    ("OD-08", "side passage between the annex and the house", "OUTSIDE_COVERED",
     "owner Q-67 A (condition met, verifier 2026-10-20 21:05): roofed by the 1F and the GF roof slab, open at the court "
     "mouth, no door or glazing", 5.640, 5.640, "1.20 x 4.70 (printed 120; 450 + 20)", "PORCELAIN / CERAMIC (side)",
     "DRAWING-CONFIRMED area; finish ASSUMED — OWNER-APPROVED (owner addition 20:45)", "OUTDOOR_FLOORS sides; Q-67 A",
     "not in his yard"),
    ("OD-09", "GF garden band (labelled GARDEN / حديقة, south of the round stair)", "HELD_CONFLICT (physically INSIDE)",
     "section A-A sheet10 cuts it: floor +1.00 continuous to the south facade wall (2 windows), slab +5.50 over it, no "
     "curb, soil or level change drawn; 1F plan sheet04: the +5.50 roof strip 1.50 wide over it; only the plan word "
     "says garden (designer D-48)", 13.986, None, "T-153 (V2.9 faces 9.101 + 4.885)", "HELD (designer D-48: planter "
     "or porcelain floor)", "HELD", "UP-SPACE-001", "inside his reception row"),
]

FREELANCER = {"yard": 151.80, "yard_perimeter": 81.32, "entrance_steps": "5 x 2.80 = 14.0", "entrance_landing": 5.10,
              "gate_steps_lm": [1.3, 2.5, 1.0, 1.0, 0.9, 1.0]}

# Level changes at outdoor openings, printed levels, no step drawn (widths = wall gaps on the DXF; HELD, see report)
THRESHOLDS = [
    ("street gate (west boundary)", 2.50, "±0.00 -> +0.15"),
    ("sea-side gate (east boundary, end of the north side walk)", 1.00, "±0.00 -> +0.15"),
    ("dewaneya door from the court", 1.00, "+0.15 -> +0.30"),
    ("driver door from the court", 0.90, "+0.15 -> +0.30"),
    ("annex lobby door from the side passage", 1.00, "+0.15 -> +0.30"),
    ("stair-hall door to the north side walk", 0.90, "+0.30 -> +0.15"),
]


def alsenan():
    r = {row[0]: row for row in ROWS}
    west = r["OD-01"][4] + r["OD-02"][4] + r["OD-03"][4] + r["OD-05"][4]
    pool_face = 17.3414
    checks = {
        "west court = open + porch + steps + landing (vs T-153 138.761)": (round(west, 4), T153["west_court"]),
        "face = west + north strip + pool court (vs T-153 177.115)": (round(west + r["OD-06"][4] + pool_face, 4),
                                                                       T153["face"]),
        "north strip + pool court (T-153 21.348 + 17.007)": (round(r["OD-06"][4] + pool_face, 4),
                                                             round(T153["north_strip"] + T153["pool_court_face"], 3)),
        "deck = pool court face - pool outer (T-153 7.605 + the moved band)": (round(pool_face - T153["pool_outer"], 4),
                                                                              round(r["OD-07"][4], 4)),
        "north strip polygon vs hand 1.30 x 16.17": (round(r["OD-06"][4], 4), round(1.30 * 16.17, 4)),
        "owner manual = hand + 0.20 x 15.97 - 0.20 x 1.30": (round(1.30 * 16.17 + 0.20 * 15.97 - 0.20 * 1.30, 4),
                                                             23.955),
        "steps tread m2 vs 4 x 0.30 x 2.80": (round(r["OD-03"][4], 4), 3.36),
        "landing vs 1.40 x 3.70": (round(r["OD-05"][4], 4), 5.18),
        "porch vs 2.00 x 4.30 + 1.20 x 1.50 + 1.40 x 0.20": (round(r["OD-02"][4], 4), 10.68),
        "covered under the 1F (porch + steps + landing) vs 4.60 x 4.30 - 1.40 x 0.40": (
            round(r["OD-02"][4] + r["OD-03"][4] + r["OD-05"][4], 4), round(4.60 * 4.30 - 1.40 * 0.40, 4)),
    }
    yard = r["OD-01"][4] + r["OD-02"][4] + r["OD-06"][4]
    comp = {
        "yard like for like (open court + porch + north side walk)": (round(yard, 3), FREELANCER["yard"],
                                                                      round(yard - FREELANCER["yard"], 3),
                                                                      round(100 * (yard / FREELANCER["yard"] - 1), 2)),
        "entrance landing": (5.179, 5.10, 0.079, round(100 * (5.179 / 5.10 - 1), 2)),
        "gate / door thresholds lm (drawn widths, HELD)": (round(sum(w for _, w, _ in THRESHOLDS), 2),
                                                           round(sum(FREELANCER["gate_steps_lm"]), 2),
                                                           round(sum(w for _, w, _ in THRESHOLDS) -
                                                                 sum(FREELANCER["gate_steps_lm"]), 2), None),
    }
    steps = outside_steps(1.00 - 0.15, 5, 4, 0.30, 2.80)
    return checks, comp, steps


def main(argv):
    if "--check" in argv:
        n, fails = run_check()
        checks, comp, steps = alsenan()
        for k, (a, b) in checks.items():
            n += 1
            tol = 0.01
            if abs(a - b) > tol:
                fails.append("Alsenan %s: %s vs %s" % (k, a, b))
            print("%-90s %10.4f %10.4f %s" % (k, a, b, "PASS" if abs(a - b) <= tol else "FAIL"))
        print("entrance steps:", steps)
        for k, v in comp.items():
            print("vs freelancer:", k, v)
        print("fixture + re-add checks: %d, failed %d" % (n, len(fails)))
        for f in fails:
            print("FAIL", f)
        return 1 if fails else 0
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "AREAS_T157.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "space_surface", "classification", "evidence", "drawn_m2", "hand_m2", "hand_formula",
                        "finish", "status", "rule", "freelancer_row"])
            for row in ROWS:
                w.writerow(row)
            for name, width, lv in THRESHOLDS:
                w.writerow(["TH", name, "OUTSIDE opening", "printed levels " + lv + "; no step drawn", "", width,
                            "opening width (lm)", "HELD (no step drawn; no rule treats a 0.15 threshold as a stair)",
                            "HELD", "UP-STAIR-002 (geometry from the drawing)", "gate steps 7.70 lm (6 items)"])
        checks, comp, steps = alsenan()
        json.dump({"task": "T-157", "rows": len(ROWS), "checks": checks, "vs_freelancer": comp, "entrance_steps": steps,
                   "thresholds": THRESHOLDS}, open(out / "summary.json", "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print("written", out)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
