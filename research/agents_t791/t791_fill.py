"""T-791 F-25 STAIR RAILINGS, GUARDS and STAIR-HALL SKIRTING blank lines to figures (DELIVERY MODE fix-row set;
worker 1; r1 2026-11-14 19:30, r2 2026-11-14 21:20 after the Checker's REJECTED r1). Nothing is wired here (Worker 3, T-770).

Reads the candidate line index ARCH_TAKEOFF_V3.0.87 (research/agents_t770/out/LINE_INDEX_V3_0_87.json, sha16
d92c44544119571c; the 14 lines are still blank there, as on V3.0.86) and writes out/FIX_ROWS.json + out/FIX_ROWS.md: one
row for each of the 14 blank lines of the Stairs trade (FIN.RAILING 5, MET.RAILING.GUARD 2, FIN.SKIRTING 7).

The geometry and the guards are pure functions (tested on a synthetic villa in tests/t791_stair_rails):
  rail_sloped(plan, rise)            R-T476-1: installed rail on a pitch = hypot(plan, rise); missing rise -> HELD, never 0
  arc_plan(r, step_deg, goings)      a curved flight's rail plan length on its band centreline
  level_run(band_c, covered, across, leg)  level guard beyond a stair rail along a band + its turn round a well end
  skirting_remainder(total, parts)   a parent skirting run minus its named children / faces; < 0 refused
  band_role(...)                     R-T791-1: a closed double outline in plan is a RAIL or a WALL by its evidence
  settle_rail_or_skirting(...)       the rail row and the skirting row of one band are mutually exclusive
  make_row(line, value, label, basis)  fix-row guards: HELD blank only, figure > 0 with a delivery label, NA with evidence

r2 changes (Checker F-V791-1, gate d):
  * F-V791-1 settled, RAIL: the GF well band 4A4 / 47F + 155 / 156 + 157 / 151 (all layer 5, thin continuous, NOT the
    cut-wall layer 1) is two 50 mm bands with a 100 mm open gap (47F x -143739.9 / 151 x -143839.9), the west leg turning
    hidden (layer 2: 152 / 153) exactly at the plan cut line C3 as the flight rises above the cut. Section A-A (Drive
    "Alsenan chalet project" / p7757_arch_sheet10.pdf, single sheet, raster 4672 x 6624 = 400 dpi, 1:100, read by pixel
    runs) draws at the +1.00 hall a LEVEL guard continuous with D1's sloped rail: two vertical posts and a top rail at
    0.99 m (156 px x 6.35 mm) + mid rail, 297 px = 1.886 m long, standing on the slab with no curb or upstand, the MS1-L
    flight visible THROUGH it (no solid divider). So: RAIL:ST-01b level piece = 2.050 lm DRAWING-READ; the divider-band
    skirting row is NOT_APPLICABLE (an open guard has no wall face at the floor). The r1 reading 'solid divider' (T-393 /
    T-441 / T-418) is withdrawn; T-476's 'no rail continuing at +1.00' is not what sheet10 draws.
  * RL-10 re-read: it CANNOT be read by DXF handle: the DXF (P7757.dxf) holds the plans and only the SE / NW elevations
    (titles 24DB, 2A69); the FENCE ELEVATION is only on PDF p.12, a raster page with no vector paths (0 drawings, 1 image).
    Own re-scale this run: wall 913 px = printed 5.80 (6.353 mm / px = 1:100 at 400 dpi); top rail outer edge 592 px
    (3.761 m), inner edge 557 px (3.539 m): the r1 figure 3.748 (590 px) stands, ESTIMATE, +-0.013 m.
  * Base moved to V3.0.87 (same 14 blank lines, same totals before).

  python3 -I research/agents_t791/t791_fill.py research/agents_t770/out/LINE_INDEX_V3_0_87.json [--check]
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
OUT_MD = os.path.join(HERE, "out", "FIX_ROWS.md")
INDEX_SHA16 = "d92c44544119571c"
INDEX_VERSION = "ARCH_TAKEOFF_V3.0.87"
FAMILIES = ("FIN.RAILING", "MET.RAILING.GUARD", "FIN.SKIRTING")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
NA = "NOT_APPLICABLE"
r3 = lambda x: round(x + 0.0, 3)


class Refused(ValueError):
    """A guard refused the input (the line stays HELD; nothing becomes 0)."""


# ---- pure geometry ------------------------------------------------------------------------------------------------
def rail_sloped(plan, rise):
    """R-T476-1: installed rail on a pitch, metres. A missing rise or plan is not 0: refused (line stays HELD)."""
    if plan is None or rise is None:
        raise Refused("pitch not known: plan and rise are both needed (HELD, never 0)")
    if plan <= 0 or rise < 0:
        raise Refused(f"bad pitch plan {plan} rise {rise}")
    if plan > 50 or rise > 50:
        raise Refused("pitch in mm? metres expected")
    return math.hypot(plan, rise)


def arc_plan(radius, step_deg, goings):
    """Plan length of a curved rail on its band centreline (radius m, equal drawn step angle per going)."""
    if radius is None or radius <= 0 or step_deg <= 0 or goings <= 0:
        raise Refused("arc needs radius > 0, step > 0, goings > 0")
    return radius * math.radians(step_deg * goings)


def level_run(band_centre_len, covered_plan, across=0.0, leg=0.0):
    """Level guard along a band beyond the part a stair rail already covers, plus its turn round a well end:
    (band centreline length - covered plan) + across (centre to centre) + leg (to the next run's first nosing)."""
    if max(band_centre_len, covered_plan, across, leg) > 50:
        raise Refused("lengths in mm? metres expected")
    beyond = band_centre_len - covered_plan
    if beyond <= 0 or across < 0 or leg < 0:
        raise Refused(f"nothing beyond the covered rail ({beyond:.3f})")
    return beyond + across + leg


def skirting_remainder(total, parts):
    """Parent skirting run minus its named children / faces; a negative remainder is a reading error, refused."""
    rem = total - sum(parts)
    if rem < -1e-9:
        raise Refused(f"children exceed the parent run by {-rem:.3f}")
    return max(rem, 0.0)


# ---- R-T791-1: role of a closed double outline in plan --------------------------------------------------------------
RAIL, WALL, UNRESOLVED = "RAIL", "WALL", "UNRESOLVED"


def band_role(on_cut_wall_layer, inner_gap_lines, section):
    """on_cut_wall_layer: the outline is on the plan's cut-wall layer; inner_gap_lines: the outline carries inner lines
    leaving an open gap (two thin bands, not one solid body); section: what a section through it draws there:
    'open_guard' (posts / rails, things visible through), 'solid' (a wall / upstand body to the floor) or None.
    A section governs; without one, a cut-wall outline is a wall, a split band is a rail, anything else unresolved."""
    if section == "solid":
        return WALL
    if section == "open_guard":
        return RAIL
    if section is not None:
        raise Refused(f"unknown section reading {section!r}")
    if on_cut_wall_layer:
        return WALL
    if inner_gap_lines:
        return RAIL
    return UNRESOLVED


def settle_rail_or_skirting(role, rail_len, skirt_len):
    """One band is either a rail (FIN.RAILING) or a wall face (FIN.SKIRTING), never both.
    Returns ((rail value or NA), (skirting value or NA)); UNRESOLVED is refused (one alternative pair stays HELD)."""
    if role == RAIL:
        return rail_len, NA
    if role == WALL:
        return NA, skirt_len
    raise Refused("band role unresolved: hold both lines as one alternative pair, never carry both")


# ---- fix-row guards -------------------------------------------------------------------------------------------------
def check_index(raw, sha16):
    if hashlib.sha256(raw).hexdigest()[:16] != sha16:
        raise Refused("index sha differs from the version these rows were written on")
    return json.loads(raw)["lines"]


def make_row(line, value, label, basis):
    if line.get("class") != "HELD" or line.get("measured_net") is not None:
        raise Refused(f"{line.get('element_id')}: not a blank HELD line ({line.get('class')})")
    row = dict(line_id=line["line_id"], item_code=line["item_code"], unit=line["unit"], element_id=line["element_id"],
               set="STAIRS", before={"class": "HELD", "net": None, "low": line.get("held_low"),
                                     "high": line.get("held_high")}, label=label, basis=basis)
    if label == NA:
        if value not in (None, NA) or not basis or len(basis.strip()) < 40:
            raise Refused(f"{line['element_id']}: NOT_APPLICABLE needs written evidence and no value")
        row["after"] = {"class": "EXCLUDED", "net": None, "reason": "NOT_APPLICABLE_WITH_EVIDENCE"}
        return row
    if label not in LABELS:
        raise Refused(f"{line['element_id']}: label {label!r} is not a delivery label")
    if value is None or isinstance(value, str) or not value > 0:
        raise Refused(f"{line['element_id']}: a figure must be > 0 (blank never becomes 0)")
    row["after"] = {"class": "RELEASED", "net": r3(value)}
    return row


# ---- Alsenan inputs (sources in the docstring; values only, no drawing content) ------------------------------------
TURN_PLAN = 0.150 + 0.025 + 0.025          # R-T393-1 centreline path round a 0.10 well end
RISE_WINDERS = 3.500 - (1.00 + 10 * 4.50 / 27)  # +2.667 -> +3.500 printed: 0.833333 (T-766)
RISE_MS2TR = 0.168                         # MS2-TR closing riser +7.516 -> +7.684
RS_R_OUTER = (2.7305 + 2.7805) / 2         # RL-09 outer band centreline (23D / 23E)
RS_STEP_DEG, RS_GOINGS, RS_RISER = 7.790996, 12, 4.50 / 28
E1_PLAN, E1_RISE, E1_TOP = 1.200, 4 * 0.17, 0.200
RL04_BAND = 6.127
FENCE_PX_WALL, FENCE_PX_RAIL, FENCE_WALL_M = 913, 590, 5.80
# GF well band (P7757.dxf by handle): east leg 4A4 x -143689.9 / 47F x -143739.9 from y -793143.5; south closure
# 155 y -795943.5 / 156 y -795893.5 (centre -795918.5); west leg 157 / 151 (centre x -143864.9); D1 nosings 481 y
# -793143.5 .. 490 y -794043.5 (3 x 0.300); MS1-L first nosing DC y -795893.5.
ST01B_BAND_C = (-793143.5 - (-795918.5)) / 1000  # 2.775 east-leg centreline to the closure centre
ST01B_D1_PLAN = 0.900
ST01B_ACROSS = (-143714.9 - (-143864.9)) / 1000  # 0.150 east to west band centres
ST01B_LEG = (-795893.5 - (-795918.5)) / 1000      # 0.025 closure centre to MS1-L first nosing
DIVIDER_SKIRT = 1.900 + 0.100 + 0.200      # r1 face reading, carried only if the band were a wall


def figures():
    f = {}
    v = rail_sloped(TURN_PLAN, RISE_WINDERS)
    f["RAIL:RL-07:ST-01:T-MS1-N"] = (v, "ESTIMATE",
        f"well-end turn over the 5 MS1-T winders: plan 0.200 (R-T393-1 centreline path) x rise 0.8333 (+2.667 -> +3.500 printed): "
        f"hypot = {v:.3f} (R-T476-1 pitch; profile ramp / wreath not drawn, = T-578 chord lower bound)")
    v = rail_sloped(TURN_PLAN, RISE_MS2TR)
    f["RAIL:RL-07:ST-01:T-MS2-LD"] = (v, "ESTIMATE",
        f"well-end turn at the MS2-LD half landing: plan 0.200 x closing riser 0.168 (+7.516 -> +7.684): hypot = {v:.3f} "
        f"(T-393 bound 0.200 .. 0.261; riser place not drawn)")
    plan = arc_plan(RS_R_OUTER, RS_STEP_DEG, RS_GOINGS)
    rise = RS_GOINGS * RS_RISER
    v = rail_sloped(plan, rise)
    f["RAIL:RL-09"] = (v, "ESTIMATE",
        f"ST-02 RS-C outer band (DXF GF 23D / 23E, 1F BA0 / BA1, layer 5, 50 mm = the rail graphic of every run): centreline r 2.7555 x "
        f"12 x 7.790996 deg = plan {plan:.3f} (= inner band range 175.97 -> 269.47), rise 12 x 4.50/28 = {rise:.3f}: hypot = {v:.3f}; "
        f"guard vs string still a designer item (RFI-B, T-476)")
    v = rail_sloped(E1_PLAN, E1_RISE) + E1_TOP
    f["RAIL:RL-11"] = (v, "ESTIMATE",
        f"ST-03 entrance stair open north side E-11: plan 1.200 (DXF 368) x pitch rise 4 x 0.17 = 0.680 -> {math.hypot(E1_PLAN, E1_RISE):.3f} "
        f"+ top strip E-12 0.200 at +1.00 (367) = {v:.3f}; south side is wall 15A / 158 (T-361), no guard; none drawn on plan, render "
        f"F04 shows a balustrade (T-164)")
    role = band_role(on_cut_wall_layer=False, inner_gap_lines=True, section="open_guard")
    rail_len = level_run(ST01B_BAND_C, ST01B_D1_PLAN, ST01B_ACROSS, ST01B_LEG)
    rail_v, skirt_v = settle_rail_or_skirting(role, rail_len, DIVIDER_SKIRT)
    f["RAIL:ST-01b:GF east-lane band beyond D1"] = (rail_v, "DRAWING-READ",
        f"R-T791-1 role {role}: plan band 4A4 / 47F + 155 / 156 + 157 / 151 all layer 5 (not cut-wall layer 1), two 50 mm bands "
        f"with a 100 mm open gap, west leg hidden (152 / 153) past cut line C3; section A-A (sheet10) draws a level guard at +1.00, "
        f"top rail 0.99 m + mid rail, 1.886 m, on the slab with no upstand, MS1-L visible through it, continuous with D1's rail. "
        f"Level piece from D1 top nosing (490) along the east-leg centreline 2.775 - 0.900 = 1.875 + turn across 0.150 + leg 0.025 "
        f"to MS1-L first nosing (DC) = {rail_v:.3f}, level (rise 0)")
    f["SKIRT-T443:GF-ST-HALL:DIVIDER-BAND"] = (skirt_v, NA,
        "the band is an open guard, not a wall (R-T791-1; section A-A sheet10: posts and rails standing on the +1.00 slab, no curb, "
        "flight visible through; plan: two 50 mm layer-5 bands with a 100 mm gap, no cut-wall line): no wall face at the floor, "
        "no skirting. Mutually exclusive with RAIL:ST-01b (carried there); r1's 2.200 withdrawn")
    f["RAIL:RL-04"] = (RL04_BAND, "DEFAULT",
        "1F sea balcony edge +5.50 in front of W15 / W16: plan band C85 / C86 (layer 5 rail layer) 6.127 own DXF read; NW elevation "
        "piers 7.500 apart: company default 'plan dimension governs a facade' -> 6.127; W15 / W16 drawn to +5.50 so the edge is open; "
        "type / height a designer item")
    rail = FENCE_PX_RAIL * FENCE_WALL_M / FENCE_PX_WALL
    f["RAIL:RL-10"] = (rail, "ESTIMATE",
        f"street fence X railing in the wall's dip, p.12 FENCE ELEVATION 1:100 scaled (no printed length; p.12 is a raster page and is "
        f"not in the DXF, so no handle read exists): top rail between the dip faces 590 px x 5.80 / 913 px (the printed 5.80 wall "
        f"drawn) = {rail:.3f}; r2 re-scale outer edge 592 px = 3.761, inner 557 px = 3.539; 4 X panels 0.877 each (= RL-01 panel)")
    # ---- skirting ------------------------------------------------------------------------------------------------
    v = skirting_remainder(11.100, (4.650, 1.400, 2.800, 1.150, 0.900))
    f["GF-R31F8AE:stair hall skirting"] = (v, "ESTIMATE",
        "parent remainder only: GF stair-room run 11.100 (wall 9.8 + column 1.3) - children 6.050 (hall 4.650 + lobby 1.400) - T-410 "
        f"flight faces 4.850 (west 2.800, MS1-T north 1.150, D1 east 0.900) = {v:.3f} = strip GF-ST-CN north face (T-441 / T-443 "
        "closure); the held children carry their own lines")
    f["SKIRT-T443:GF-ST-HALL:OP-020-JAMBS"] = (0.400, "DEFAULT",
        "doorless opening OP-020 (hall -> wash space): 2 jamb returns x wall 0.200 = 0.400 (owner URBAN-SKIRTING-OPENING-METHOD: "
        "doorless-opening jambs skirted); the wet-room tiled face itself carries none (owner 2026-11-02)")
    f["SKIRT-T443:GF-ST-LOBBY030:WEST-FACE"] = (1.150, "ESTIMATE",
        "GF back lobby +0.30 west side x 1.35: 1.150 (lobby depth, wall 21B 1.150 opposite); under-winder space drawn only hidden "
        "(49C / 2C6 / 49D): the lobby floor stops at the drawn line, one face carried")
    f["STAIR-SKIRT:MS1-LD.N"] = (1.150, "DEFAULT",
        "MS1-LD +3.50 north face 0.103 wall + 0.900 opening + 0.147 wall: the opening is GF door OP-013 of the +0.30 lobby, head at the "
        "2.20 default = +2.50 below the landing; 1F window W25 above starts at +5.50 (T-201): face solid at +3.50 -> 1.150 (as T-766 "
        "MS1-U.E2)")
    f["STAIR-SKIRT:MS2-LD.W25"] = (1.000, "DRAWING-READ",
        "MS2-LD +7.684 north face over W25 (1.00): W25 drawn +5.50 / +7.00 on the SW elevation (T-201 heads) lies below the landing: "
        "face solid at +7.684 -> 1.000")
    f["STAIR-SKIRT:MS2-LD.W13"] = (None, NA,
        "MS2-LD +7.516 west face 0.150 is W13 glazing: W13 1.20 x 2.30, sill 1.00 on +5.50 = +6.50 / +8.80 (T-201 elevation heads) "
        "spans the landing level: no wall face at the floor, no skirting (below 1 % of FIN.SKIRTING)")
    return f


def build(index_path, sha16=INDEX_SHA16):
    lines = check_index(open(index_path, "rb").read(), sha16)
    fig = figures()
    by_el = {}
    for l in lines:
        if l["element_id"] in fig and l["item_code"] in FAMILIES:
            by_el.setdefault(l["element_id"], []).append(l)
    rows = []
    for el, (val, lab, why) in fig.items():
        ls = by_el.get(el, [])
        if len(ls) != 1:
            raise Refused(f"{el}: {len(ls)} lines in the index")
        rows.append(make_row(ls[0], val, lab, why))
    if len(rows) != 14:
        raise Refused(f"expected 14 rows, got {len(rows)}")
    rows.sort(key=lambda r: (r["item_code"], r["element_id"]))
    return rows, lines


def totals(rows, lines):
    out = {}
    for code in FAMILIES:
        s = sum(l["measured_net"] or 0 for l in lines if l["item_code"] == code and l["class"] == "RELEASED")
        b = sum(1 for l in lines if l["item_code"] == code and l["class"] == "HELD" and l["measured_net"] is None)
        a = s + sum(r["after"]["net"] for r in rows if r["item_code"] == code and r["after"]["net"] is not None)
        left = b - sum(1 for r in rows if r["item_code"] == code)
        out[code] = {"released_before": round(s, 2), "after": round(a, 2), "blank_before": b, "blank_after": left}
    return out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    rows, lines = build(argv[1])
    doc = dict(task="T-791", revision="r2", candidate_version=INDEX_VERSION,
               base="claude/access-permissions-setup-ii24ws @ 0d3168e5", index_sha16=INDEX_SHA16, rows=len(rows),
               blank_before=14, left_after=0, totals=totals(rows, lines),
               freelancer={"internal railing lm (typed constant, T-578)": 18.95, "external / guard railing lm": "no row",
                           "stair skirting lm (ST-01 23.1 + ST-02 2.4 + E1 4.37, T-766)": 29.87,
                           "GF stair hall / lobby skirting": "no row (T-443)"},
               rows_detail=rows)
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--check" in argv:
        if open(OUT).read() != text:
            raise SystemExit("FIX_ROWS.json differs from a rebuild")
        print(f"T-791 --check OK {len(rows)} rows")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(text)
    md = [f"# T-791 r2 stair railings, guards and stair-hall skirting fix rows ({INDEX_VERSION.split('_')[-1]})", "",
          "| line | item | unit | element | before | after | label | basis |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a = r["after"]
        aft = f"{a['net']}" if a["net"] is not None else a["reason"]
        md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {r['element_id']} | blank | {aft} | {r['label']} | {r['basis']} |")
    md += ["", "Totals (released before -> after these rows; blank lines before -> after): " + json.dumps(doc["totals"]), "",
           "R-T791-1 (research rule, any villa): a closed double outline in plan is a RAIL or a WALL by its evidence; a section "
           "governs (open guard -> rail, solid body -> wall); without one, an outline on the cut-wall layer is a wall and two thin "
           "bands with an open gap are a rail; otherwise UNRESOLVED (held as one alternative pair). The rail row and the skirting "
           "row of one band are mutually exclusive."]
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    print(f"T-791 wrote {len(rows)} rows; totals {doc['totals']}")


if __name__ == "__main__":
    main(sys.argv)
