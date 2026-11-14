"""T-791 F-25 STAIR RAILINGS, GUARDS and STAIR-HALL SKIRTING blank lines to figures (DELIVERY MODE fix-row set;
worker 1, 2026-11-14). Nothing is wired here (Worker 3, T-770).

Reads the candidate line index ARCH_TAKEOFF_V3.0.86 (research/agents_t770/out/LINE_INDEX_V3_0_86.json, sha16
350770c0a813491f) and writes out/FIX_ROWS.json + out/FIX_ROWS.md: one row for each of the 14 blank lines of the Stairs
trade in BLANK_LINES_V3.0.86 (FIN.RAILING 5, MET.RAILING.GUARD 2, FIN.SKIRTING 7). Nothing else is touched.

Inputs (merged research records, values only; no drawing, coordinate or client text is committed):
  T-393 / T-476 / T-578  ST-01 run table: well-end turns plan 0.200 (R-T393-1 centreline path), rises 0.833333
                         (+2.667 -> +3.500, 5 winders) and 0.168 (MS2-TR closing riser); RL-09 band; F-T476-1 band
  T-164 / T-361          RL-04 plan band 6.127 (NW elevation piers 7.500 apart); RL-11 open edges E-11 1.200 (inclined,
                         ST-03 4 goings x 0.17 = 0.680) + E-12 0.200 (+1.00); E-13 south side is a wall
  T-766                  RS-C drawn step 7.790996 deg (12 goings), riser 4.50 / 28
  T-441 / T-443          GF stair-room faces by handle: closure 11.100 = children 6.050 + flight faces 4.850 + 0.200;
                         divider band faces at the cut 2.200 (T-418 outline 3.400); OP-020 jamb returns 2 x 0.200;
                         lobby west face 1.150 on x 1.35
  T-410 / T-501          landing pieces MS1-LD.N 1.150 (+3.50), MS2-LD.W13 0.150 (+7.516), MS2-LD.W25 1.000 (+7.684)
  T-201                  elevation heads: W25 1F stair hall +5.50 / +7.00; W13 1.20 x 2.30, sill 1.00 on +5.50
                         (+6.50 / +8.80)
  own reads this run     Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (P7757.dxf sha16 ab54dd554c31fe4a),
                         by handle, in .work/private only: ST-02 outer band GF 23D r 2730.5 / 23E r 2780.5 and 1F BA0 /
                         BA1, inner band 239 / B9C 175.97 -> 269.47 deg (= 12 x 7.790996); C85 / C86 6127.4; 368 1200.0 /
                         367 200.0; 47F 2750.0 / 4A4 2800.0. Pages_11-12 p.12 FENCE ELEVATION 1:100 at 400 dpi: street
                         wall drawn 913 px = 5.80 printed (scale 6.353 mm / px, check 0.05 %); X railing top rail drawn
                         between the dip faces 590 px = 3.748 m, 4 X panels at 137-139 px (0.877 m, = RL-01's panel).

  python3 -I research/agents_t791/t791_fill.py research/agents_t770/out/LINE_INDEX_V3_0_86.json [--check]
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
INDEX_SHA16 = "350770c0a813491f"
FAMILIES = ("FIN.RAILING", "MET.RAILING.GUARD", "FIN.SKIRTING")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
r3 = lambda x: round(x + 0.0, 3)

# ---- geometry (sources in the docstring) ---------------------------------------------------------------------------
TURN_PLAN = 0.150 + 0.025 + 0.025          # R-T393-1 centreline path round a 0.10 well end
RISE_WINDERS = 3.500 - (1.00 + 10 * 4.50 / 27)  # +2.667 (= +1.00 + 10 x 4.50/27) -> +3.500 printed: 0.833333 (T-766)
RISE_MS2TR = 0.168                         # MS2-TR closing riser +7.516 -> +7.684
RS_R_OUTER = (2.7305 + 2.7805) / 2         # outer band centreline (23D / 23E)
RS_STEP_DEG = 7.790996
RS_GOINGS = 12
RS_RISER = 4.50 / 28
E1_PLAN, E1_RISE, E1_TOP = 1.200, 4 * 0.17, 0.200
RL04_BAND = 6.127
FENCE_PX_WALL, FENCE_PX_RAIL, FENCE_WALL_M = 913, 590, 5.80


def figures():
    f = {}
    v = math.hypot(TURN_PLAN, RISE_WINDERS)
    f["RAIL:RL-07:ST-01:T-MS1-N"] = (v, "ESTIMATE",
        f"well-end turn over the 5 MS1-T winders: plan 0.200 (R-T393-1 centreline path) x rise 0.8333 (+2.667 -> +3.500 printed): "
        f"hypot = {v:.3f} (R-T476-1 pitch; profile ramp / wreath not drawn, = T-578 chord lower bound)")
    v = math.hypot(TURN_PLAN, RISE_MS2TR)
    f["RAIL:RL-07:ST-01:T-MS2-LD"] = (v, "ESTIMATE",
        f"well-end turn at the MS2-LD half landing: plan 0.200 x closing riser 0.168 (+7.516 -> +7.684): hypot = {v:.3f} "
        f"(T-393 bound 0.200 .. 0.261; riser place not drawn)")
    plan = RS_R_OUTER * math.radians(RS_STEP_DEG * RS_GOINGS)
    rise = RS_GOINGS * RS_RISER
    v = math.hypot(plan, rise)
    f["RAIL:RL-09"] = (v, "ESTIMATE",
        f"ST-02 RS-C outer band (DXF GF 23D / 23E, 1F BA0 / BA1, layer 5, 50 mm = the rail graphic of every run): centreline r 2.7555 x "
        f"12 x 7.790996 deg = plan {plan:.3f} (= inner band range 175.97 -> 269.47), rise 12 x 4.50/28 = {rise:.3f}: hypot = {v:.3f}; "
        f"guard vs string still a designer item (RFI-B, T-476)")
    v = math.hypot(E1_PLAN, E1_RISE) + E1_TOP
    f["RAIL:RL-11"] = (v, "ESTIMATE",
        f"ST-03 entrance stair open north side E-11: plan 1.200 (DXF 368) x pitch rise 4 x 0.17 = 0.680 -> {math.hypot(E1_PLAN, E1_RISE):.3f} "
        f"+ top strip E-12 0.200 at +1.00 (367) = {v:.3f}; south side is wall 15A / 158 (T-361), no guard; none drawn on plan, render "
        f"F04 shows a balustrade (T-164)")
    f["RAIL:ST-01b:GF east-lane band beyond D1"] = (None, "NOT_APPLICABLE",
        "no rail: band 4A4 2.800 / 47F 2.750 beyond D1 (0.900, RL-08) is the east face line of the solid divider (T-393 'solid to the "
        "cut'; T-441 east face 1.900 = 2.800 - 0.900, its skirting is SKIRT-T443 DIVIDER-BAND); the hall side is at +1.00 with no drop, "
        "section A-A draws no rail continuing at +1.00 (T-476 F-T476-1 read); F-T476-1 closed")
    f["RAIL:RL-04"] = (RL04_BAND, "DEFAULT",
        "1F sea balcony edge +5.50 in front of W15 / W16: plan band C85 / C86 (layer 5 rail layer) 6.127 own DXF read; NW elevation "
        "piers 7.500 apart: company default 'plan dimension governs a facade' -> 6.127; W15 / W16 drawn to +5.50 so the edge is open; "
        "type / height a designer item")
    rail = FENCE_PX_RAIL * FENCE_WALL_M / FENCE_PX_WALL
    f["RAIL:RL-10"] = (rail, "ESTIMATE",
        f"street fence X railing in the wall's dip, p.12 FENCE ELEVATION 1:100 scaled (no printed length): top rail between the dip "
        f"faces 590 px x 5.80 / 913 px (the printed 5.80 wall drawn) = {rail:.3f}; 4 X panels 0.877 each (= RL-01 panel)")
    # ---- skirting ------------------------------------------------------------------------------------------------
    f["GF-R31F8AE:stair hall skirting"] = (0.200, "ESTIMATE",
        "parent remainder only: GF stair-room run 11.100 (wall 9.8 + column 1.3) - children 6.050 (hall 4.650 + lobby 1.400) - T-410 "
        "flight faces 4.850 (west 2.800, MS1-T north 1.150, D1 east 0.900) = 0.200 = strip GF-ST-CN north face (T-441 / T-443 closure); "
        "the held children carry their own lines")
    f["SKIRT-T443:GF-ST-HALL:DIVIDER-BAND"] = (2.200, "DRAWING-READ",
        "faces of the solid divider at the hall floor +1.00 at the plan cut: east 1.900 (4A4 2.800 - D1 0.900) + west 0.100 + south end "
        "0.200 (155) = 2.200 (T-441 by handle); the T-418 outline 3.400 adds y 0.45 .. 1.05, drawn only as the hidden band above, not "
        "taken; a solid face at floor level carries skirting (UP-SKIRT-001)")
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
    f["STAIR-SKIRT:MS2-LD.W13"] = (None, "NOT_APPLICABLE",
        "MS2-LD +7.516 west face 0.150 is W13 glazing: W13 1.20 x 2.30, sill 1.00 on +5.50 = +6.50 / +8.80 (T-201 elevation heads) "
        "spans the landing level: no wall face at the floor, no skirting (below 1 % of FIN.SKIRTING)")
    return f


def build(index_path):
    raw = open(index_path, "rb").read()
    if hashlib.sha256(raw).hexdigest()[:16] != INDEX_SHA16:
        raise SystemExit("index is not ARCH_TAKEOFF_V3.0.86 (sha16 differs)")
    lines = json.loads(raw)["lines"]
    fig = figures()
    by_el = {}
    for l in lines:
        if l["element_id"] in fig and l["item_code"] in FAMILIES:
            by_el.setdefault(l["element_id"], []).append(l)
    rows = []
    for el, (val, lab, why) in fig.items():
        ls = by_el.get(el, [])
        if len(ls) != 1:
            raise SystemExit(f"{el}: {len(ls)} lines in the index")
        l = ls[0]
        if l["class"] != "HELD" or l["measured_net"] is not None:
            raise SystemExit(f"{el}: not a blank HELD line ({l['class']})")
        row = dict(line_id=l["line_id"], item_code=l["item_code"], unit=l["unit"], element_id=el, set="STAIRS",
                   before={"class": l["class"], "net": None, "low": l["held_low"], "high": l["held_high"]}, label=lab, basis=why)
        if lab == "NOT_APPLICABLE":
            row["after"] = {"class": "EXCLUDED", "net": None, "reason": "NOT_APPLICABLE_WITH_EVIDENCE"}
        else:
            if lab not in LABELS or val is None or not val > 0:
                raise SystemExit(f"{el}: a figure must be > 0 with a delivery label (never 0)")
            row["after"] = {"class": "RELEASED", "net": r3(val)}
        rows.append(row)
    if len(rows) != 14:
        raise SystemExit(f"expected 14 rows, got {len(rows)}")
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
    doc = dict(task="T-791", candidate_version="ARCH_TAKEOFF_V3.0.86", base="claude/access-permissions-setup-ii24ws @ c12c8eb4",
               index_sha16=INDEX_SHA16, rows=len(rows), blank_before=14, left_after=0, totals=totals(rows, lines),
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
    md = ["# T-791 stair railings, guards and stair-hall skirting fix rows (V3.0.86)", "",
          "| line | item | unit | element | before | after | label | basis |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        a = r["after"]
        aft = f"{a['net']}" if a["net"] is not None else a["reason"]
        md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {r['element_id']} | blank | {aft} | {r['label']} | {r['basis']} |")
    md += ["", "Totals (released before -> after these rows; blank lines before -> after): " + json.dumps(doc["totals"])]
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    print(f"T-791 wrote {len(rows)} rows; totals {doc['totals']}")


if __name__ == "__main__":
    main(sys.argv)
