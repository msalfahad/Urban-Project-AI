"""T-321 on the development villa: roof / terrace build-up as a zone x layer ledger (research only, read by no method).

    python3 -I research/agents_t321/t321_alsenan.py [--out <dir>]     (default: print the summary only)

Inputs (all committed, local metres; no coordinates of the drawing, no client data):
  research/agents_t321/ALSENAN_ROOF_LAYERS_INPUT.json   t321_measure.py on P7757.dxf (edges by handle, finish hatches)
  research/agents_t221/ALSENAN_ROOF_INPUT.json + summary.json   T-221 (MERGED 63f4d90e): falls, outlets, mean rise
  research/agents_t311/PARAPET_RUN_LEDGER_T311.csv      T-311 (MERGED bd7b8c23): parapet runs per chain
  research/agents_t303/WP_WET_ROOF_POOL_INVENTORY_T303.csv   T-303 (MERGED 1d3f69b0): the roof WP lines of the candidate
Outputs (with --out): ZONE_LAYER_LEDGER_T321.csv, CLOSURE_T321.csv, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import roof_buildup as RB  # noqa: E402

sys.path.insert(0, str(ROOT / "research" / "agents_t221"))
import roof_falls_v1 as RF  # noqa: E402

# outlets per roof in this ledger's local frames (the drawn corner RWPs T-221 placed, sanitary-7757 p.2 / p.3)
OUTLETS = {"ROOF-430": [(0.0, 0.0)], "TERRACE-550": [(18.97, 0.0)],
           "ROOF-970": [(0.0, 0.0), (18.87, 0.0), (18.87, 11.6)]}

INPUT = HERE / "ALSENAN_ROOF_LAYERS_INPUT.json"
T221_IN = ROOT / "research" / "agents_t221" / "ALSENAN_ROOF_INPUT.json"
T221_SUM = ROOT / "research" / "agents_t221" / "summary.json"
T311 = ROOT / "research" / "agents_t311" / "PARAPET_RUN_LEDGER_T311.csv"
T303 = ROOT / "research" / "agents_t303" / "WP_WET_ROOF_POOL_INVENTORY_T303.csv"

# T-221 zone id -> the candidate's roof element (T-311 / T-303 naming) and the T-311 parapet chain bounding it
ZONES = {"ROOF-430": ("1F-ROOF-AT220", "ANNEX"), "TERRACE-550": ("1F-ROOF-AT216", "GF"),
         "ROOF-970": ("2F-ROOF-AT379", "1F"), "ROOF-1390": ("2F-ROOF-TOP", "2F")}

# segment kinds of each face_wall outline, vertex i -> i+1 (read on the drawing: t321_measure.ROOFS edges)
SEGMENTS = {
    "ROOF-430": [("parapet", "B34"), ("divider", "CEC"), ("building_wall", "ADF"), ("building_wall", "B3A"),
                 ("parapet+closure", "B35 6.200 + 0.200 across the D band to the wall face"), ("parapet", "B38"),
                 ("parapet", "B2B arc"), ("parapet", "B41"), ("parapet", "B37")],
    "TERRACE-550": [("parapet", "B25"), ("parapet", "B33"), ("gate_stub+closure", "BDB 0.894 + door C9E 0.406"),
                    ("building_wall", "B5D .. B60"), ("building_wall", "AE3 .."), ("divider", "CED")],
    "ROOF-970": [("parapet", "1285"), ("parapet", "12A7"), ("parapet", "1278"), ("building_wall", "1291"),
                 ("building_wall", "1281 / 1280"), ("building_wall", "1288"),
                 ("parapet+closure", "12B9 4.125 + 0.075 across the D band to the wall face"), ("parapet", "12C9")],
    "ROOF-1390": [("parapet", "1283 (2F south wall inner face)"), ("parapet", "1292"), ("parapet", "1279"),
                  ("parapet", "12B7")],
}
SPLIT = {"ROOF-430": {4: (6.2, 0.2)}, "TERRACE-550": {2: (0.894, 0.406)}, "ROOF-970": {6: (4.125, 0.075)}}

SEARCHED = ("searched: P7757.dxf all 109 TEXT entities (Arabic notes decoded: room names, title block only); "
            "ST7757 dxf.dxf all 374 texts (notes: excavation, soil, formwork, 'CHECK ARCHITECTURAL DETAIL OF "
            "PARAPET, BEFORE CASTING'); sanitary-7757.pdf p.1-3 (drainage only: RWP, 'SLOPE 1%'); "
            "p7757_arch_sheet10.pdf SECTION A-A roof bands (constant 0.05 / 0.20 drafting band, refused by T-214 / "
            "T-221); no roof detail, specification or finish schedule in the issued set")


def _spec(raw):
    return [("ARC", tuple(v[1]), v[2], v[3], v[4]) if v[0] == "ARC" else tuple(v) for v in raw]


def _segments(spec):
    """lengths of the outline's sides in order; an ARC item is one side (its arc length)."""
    pts, out = [], []
    items = list(spec)
    seq = []
    for it in items:
        if it[0] == "ARC":
            _, c, r, a0, a1 = it[:5]
            seq.append(("ARC", (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0))),
                        (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1))),
                        r * math.radians(abs(a1 - a0))))
        else:
            seq.append(("P", tuple(it)))
    # walk: a point followed by a point is a straight side; an arc replaces the side from its start to its end
    flat = []
    for s in seq:
        if s[0] == "P":
            flat.append(("P", s[1]))
        else:
            flat.append(("A", s[1], s[2], s[3]))
    n = len(flat)
    for i in range(n):
        a, b = flat[i], flat[(i + 1) % n]
        if a[0] == "A":
            out.append(a[3])
            end = a[2]
            nxt = b[1]
            if math.dist(end, nxt) > 1e-9:
                out.append(math.dist(end, nxt))
        else:
            if b[0] == "A":
                if math.dist(a[1], b[1]) > 1e-9:
                    out.append(math.dist(a[1], b[1]))
            else:
                out.append(math.dist(a[1], b[1]))
    return out


def _t221_area(roof):
    spec = []
    for v in roof["outline"]:
        if v == "ARC":
            a = roof["outline_arc_corner"]
            c, r = a["centre"], a["radius"]
            a0 = math.degrees(math.atan2(a["to"][1] - c[1], a["to"][0] - c[0]))
            a1 = math.degrees(math.atan2(a["from"][1] - c[1], a["from"][0] - c[0]))
            spec.append(("ARC", tuple(c), r, a0, a1))
        else:
            spec.append(tuple(v))
    return RB.exact_area(spec)


def build():
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    t221 = {r["zone_id"]: r for r in json.loads(T221_IN.read_text(encoding="utf-8"))["roofs"]}
    t221s = {z["zone"] if "zone" in z else z.get("zone_id"): z for z in json.loads(T221_SUM.read_text(encoding="utf-8"))["roofs"]}
    runs = list(csv.DictReader(T311.open(encoding="utf-8")))
    wp = {(r["element"], r["item_code"], r["face"]): r for r in csv.DictReader(T303.open(encoding="utf-8"))}

    zones, rows, closures = {}, [], []
    for zid, (elem, chain) in ZONES.items():
        r = inp["roofs"][zid]
        wall = _spec(r["face_wall"])
        dband = _spec(r["face_dband"]) if r["face_dband"] else wall
        a_wall, a_d = RB.exact_area(wall), RB.exact_area(dband)
        fp = {k: math.pi * c["r"] ** 2 for k, c in r["footprint_circles"].items()}
        hatch = sum(h["outer_m2"] for h in r["finish_hatches"])
        # finish: to the designer's finish edge. Where the hatch edge IS a closed own outline (D band / parapet / wall
        # faces) the outline less the footprints the hatch leaves out; TERRACE-550's finish edge runs on the 0.10 sill
        # line and round a 0.90 x 0.30 door-step notch, so its hatch main paths are the finish edge itself.
        if not r["finish_hatches"]:
            finish = None
        elif zid == "TERRACE-550":
            finish = hatch
        else:
            finish = a_d - sum(fp.values())
        sides = _segments(wall)
        kinds = SEGMENTS[zid]
        assert len(sides) == len(kinds), (zid, len(sides), len(kinds))
        per = {}
        for i, (L, (kind, ref)) in enumerate(zip(sides, kinds)):
            if i in SPLIT.get(zid, {}):
                a, b = SPLIT[zid][i]
                assert abs(a + b - L) < 1e-6, (zid, i, L)
                k1, k2 = kind.split("+")
                per[k1] = per.get(k1, 0.0) + a
                per[k2] = per.get(k2, 0.0) + b
            else:
                per[kind] = per.get(kind, 0.0) + L
        rings = {k: 2 * math.pi * c["r"] for k, c in r["footprint_circles"].items()}
        chain_inner = sum(float(x["inner_top_arris_m"]) for x in runs if x["chain"] == chain)
        zones[zid] = {"element": elem, "label": r["label"], "face_wall_m2": round(a_wall, 6),
                      "face_dband_m2": round(a_d, 6), "dband_m2": round(a_wall - a_d, 6),
                      "footprints_m2": {k: round(v, 6) for k, v in fp.items()},
                      "finish_hatch_m2": round(hatch, 4), "finish_physical_m2": None if finish is None else round(finish, 6),
                      "perimeter_m": {k: round(v, 4) for k, v in per.items()},
                      "perimeter_total_m": round(sum(sides), 4),
                      "footprint_rings_m": {k: round(v, 4) for k, v in rings.items()},
                      "t311_chain": chain, "t311_chain_inner_m": round(chain_inner, 4)}

    z = zones
    # ---------------- closures (own - reference = named causes) ----------------
    def C(name, own, ref, causes, note="", tol=1e-4):
        c = RB.closure(own, ref, causes, tol)
        c.update({"closure": name, "note": note})
        closures.append(c)

    t221a = {k: _t221_area(v) for k, v in t221.items() if v.get("outline")}
    gap = [g["area_m2"] for g in inp["roofs"]["ROOF-970"]["hatch_vs_outline"]]
    C("ROOF-430 own wall-face plan vs T-221 52.848 (its outline recomputed exactly)", z["ROOF-430"]["face_wall_m2"],
      t221a["ROOF-430"],
      [("strip between the house SW wall line and the divider wall CEC, 1.599 x 1.300, not in T-221's outline",
        (11.8 - 10.201) * 1.3),
       ("3.2 m band to the 1F wall face B3A (T-221 to the D band, 10.201)", (10.4 - 10.201) * 3.2),
       ("T-221 corner rounding 4.001 / 6.302 / r 1.101 vs drawn 4.000 / 6.300 / 1.100",
        (4.0 * 1.8 - 1.1 ** 2 * (1 - math.pi / 4)) - (4.001 * 1.802 - 1.101 ** 2 * (1 - math.pi / 4)))],
      "T-221 reported 52.848; its own outline integrates to the reference here (difference = its arc sampling)")
    C("ROOF-970 own wall-face plan vs T-221 147.691", z["ROOF-970"]["face_wall_m2"], t221a["ROOF-970"],
      [("east wing north edge: T-221 to the parapet OUTER face 1273 (6.801), drawn inner face 1278 (6.600)",
        -6.57 * (6.801 - 6.6)),
       ("west wing: own wall face 1288 (4.200 x 2.100) vs T-221 4.125 x 2.099 (to the D band)",
        4.2 * 2.1 - 4.125 * 2.099)])
    C("ROOF-430 own wall-face plan vs candidate FIN.WP.ROOF AT220", z["ROOF-430"]["face_wall_m2"],
      float(wp[("1F-ROOF-AT220", "FIN.WP.ROOF", "INSIDE_PARAPET")]["qty"]), [],
      "same basis (T-062 hand trace, membrane to the wall face)")
    C("TERRACE-550 own wall-face plan vs candidate FIN.WP.ROOF AT216 (= Checker 21:05 screed / membrane 32.721)",
      z["TERRACE-550"]["face_wall_m2"], float(wp[("1F-ROOF-AT216", "FIN.WP.ROOF", "INSIDE_PARAPET")]["qty"]), [])
    domes = sum(z["ROOF-970"]["footprints_m2"].values())
    C("ROOF-970 own wall-face plan less the two dome discs vs candidate FIN.WP.ROOF AT379",
      z["ROOF-970"]["face_wall_m2"] - domes,
      115.832, [("candidate deducts the domes as polygons (2 x 15.350) not circles (2 x 15.3589)", -(domes - 30.700))],
      "candidate line value 115.832 (T-303: inventory 115.816517 vs line 115.832)")
    C("TERRACE-550 own finish (designer hatch main paths) vs Checker 21:05 own finish 31.681",
      z["TERRACE-550"]["finish_hatch_m2"], 31.681,
      [("hatch D1A symbol frame drawn as an external path across the 1F wall face (0.0352 outside the finish "
        "paths): drafting, not finish", -0.0352)],
      "the rest is unexplained at this precision; the Checker's computation is not on the board")
    C("ROOF-430 finish hatch vs own D-band outline", z["ROOF-430"]["finish_hatch_m2"],
      z["ROOF-430"]["finish_physical_m2"], [("arc flattening of the hatch boundary", -0.0000)])
    C("ROOF-970 finish hatch vs own finish (D-band outline less the dome discs)", z["ROOF-970"]["finish_hatch_m2"],
      z["ROOF-970"]["finish_physical_m2"],
      [("door swing of the 2F roof door drawn as a hatch boundary (0.89 quarter circle): drafting", -gap[0]),
       ("dome tangency cusps at the hatch split lines (finish exists there)", -(gap[1] + gap[2])),
       ("dome-circle flattening of the hatch boundary (pieces < 0.001 m2)", -sum(gap[3:]))],
      "tolerance 0.001 m2: the 11 gap pieces are rounded to 0.0001 m2 each and the hatch arcs flattened at 0.05 mm",
      tol=1e-3)
    # parapet face lengths vs T-311 runs
    par = {k: v["perimeter_m"].get("parapet", 0.0) for k, v in z.items()}
    C("ROOF-430 parapet faces vs T-311 ANNEX chain inner arris", par["ROOF-430"], z["ROOF-430"]["t311_chain_inner_m"],
      [("boundary parapet B34 between the house SW wall line and the divider (x 10.4 .. 11.8): on the roof face, in "
        "NO T-311 run (FINDING F-T321-02)", 1.4),
       ("T-311 SW-3 6.4001 runs to the wall face across the 0.20 D band; the parapet face B35 is 6.200", -0.2001),
       ("T-311 NE-6 10.4001 vs 10.400", -0.0001)])
    C("TERRACE-550 parapet faces + divider vs T-311 GF chain", par["TERRACE-550"] + z["TERRACE-550"]["perimeter_m"]
      ["divider"], z["TERRACE-550"]["t311_chain_inner_m"],
      [("T-311 NE-4 19.17 runs the boundary parapet body across the 0.20 divider; the roof face B25 is 18.970", -0.2),
       ("T-311 SW-9 1.2999 vs 1.300", 0.0001)])
    C("ROOF-970 parapet faces vs T-311 1F chain", par["ROOF-970"], z["ROOF-970"]["t311_chain_inner_m"],
      [("sea side: T-311 runs NW-1 .. NW-5 follow the shaped parapet TOP (arcs / steps, 12.0435); the roof-level "
        "inner face is the straight line 12A7, 11.600", -0.4435),
       ("T-311 SW-2 4.2001 runs to the 2F wall face across the 0.075 D band; parapet face 12B9 4.125", -0.0751),
       ("T-311 SW-3 6.5699 vs 1278 6.570", 0.0001)])
    C("ROOF-1390 parapet faces vs T-311 2F chain", par["ROOF-1390"], z["ROOF-1390"]["t311_chain_inner_m"], [])
    C("candidate roof upturns (FIN.WP.ROOF_UPTURN) vs own vertical faces round each roof",
      sum(v for k, v in z["ROOF-430"]["perimeter_m"].items()) + sum(z["TERRACE-550"]["perimeter_m"].values())
      + sum(z["ROOF-970"]["perimeter_m"].values()),
      35.727 + 52.940 + 65.140,
      [("ROOF-430 arc 1.7279 vs the trace's rounding", 0.0009)])

    # freelancer: one roof line 285.00 m2 (his cells NOT read here: workbook over the connector limit; figure from
    # T-303 / T-071, Verifier re-multiplied). Scope decomposition, a consistency check, not a proof.
    fl = 285.00
    cand3 = z["ROOF-430"]["face_wall_m2"] + z["TERRACE-550"]["face_wall_m2"] + z["ROOF-970"]["face_wall_m2"] - domes
    decomp = {"three roofs inside the parapet / wall faces, +9.70 domes deducted (own; = candidate basis)":
                  round(cand3, 4),
              "two +9.70 dome footprints (membrane under the domes, SCOPE_UNKNOWN in the candidate)": round(domes, 4),
              "+13.90 roof inside the parapet faces, third dome NOT deducted (HELD Q-34)":
                  round(z["ROOF-1390"]["face_wall_m2"], 4)}
    fl_res = fl - sum(decomp.values())

    # ---------------- zone x layer ledger ----------------
    # falls rise on THIS ledger's face outlines (T-221's model roof_falls_v1, unchanged; T-221 ran it on its own
    # outlines, two of which are corrected above): the volume above the t0 plane, both layouts (FALL_LAYOUT_NOT_DRAWN)
    rise, falls = {}, {}
    for zid, outs in OUTLETS.items():
        f = RF.falls_field(RB.outline(_spec(inp["roofs"][zid]["face_wall"])), outs, 0.01, step=0.05)
        ek, ax = f["models"]["EIKONAL"], f["models"]["AXIS"]
        falls[zid] = {"rise_max_m": [ek["rise_max_m"], ax["rise_max_m"]],
                      "rise_mean_m": [ek["rise_mean_m"], ax["rise_mean_m"]],
                      "volume_above_t0_m3": [ek["volume_above_t0_m3"], ax["volume_above_t0_m3"]],
                      "outline_area_m2": f["area_m2"],
                      "note": "over the whole face outline (dome footprints included where present)"}
        rise[zid] = falls[zid]["volume_above_t0_m3"]
    for zid, (elem, chain) in ZONES.items():
        zz = z[zid]
        held = "" if zid != "ROOF-1390" else ("owner Q-34: the +13.90 roof stays HELD (no number, never 0); "
                                               "drawing-derived values reported beside, not released")
        nfp = sum(zz["footprints_m2"].values())
        face = (zz["face_dband_m2"] - nfp, zz["face_wall_m2"] - nfp)   # net of the footprints (listed separately)
        fin = None if zz["finish_physical_m2"] is None else (zz["finish_physical_m2"], zz["finish_physical_m2"])
        foot = {k: (v, {"FINISH": "EXCLUDED (the finish hatch stops at the dome circle; no roof walking surface "
                                  "inside a dome in S0 or S1)",
                        "MEMBRANE": "SCOPE_UNKNOWN (T-303; Q-24 / Q-29 C / T-185)",
                        "FALLS_SCREED": "SCOPE_UNKNOWN (as the membrane)", "INSULATION": "SCOPE_UNKNOWN",
                        "PROTECTION": "SCOPE_UNKNOWN"})
                for k, v in zz["footprints_m2"].items()}
        upt = sum(zz["perimeter_m"].values())
        zone = RB.Zone(zid, face, fin, foot, (upt, upt), 0.01 if zid != "ROOF-1390" else None,
                       "sanitary-7757.pdf p.2 / p.3 'SLOPE 1%' (T-221)" if zid != "ROOF-1390" else
                       "no outlet, no fall on any sheet (DRAINS_NOT_DRAWN)", zid != "ROOF-1390", held)
        wp_line = wp.get((elem, "FIN.WP.ROOF", {"ROOF-430": "INSIDE_PARAPET", "TERRACE-550": "INSIDE_PARAPET",
                                                "ROOF-970": "INSIDE_PARAPET_OUTSIDE_DOMES",
                                                "ROOF-1390": "TOP_ROOF"}[zid]))
        layers = [
            RB.Layer("FALLS_SCREED", "OWNER_RULE",
                     "Q-41 (owner 2026-10-19 20:45: 'if it is roof or balconies it is screed', its own line); "
                     "falls: printed 1 % (T-221), Q-45 0.5 % only where none is printed"),
            RB.Layer("MEMBRANE", "OWNER_RULE", "UP-WP-ROOF-001 / Q-24 (membrane inside the parapet, 0.20 m upturn); "
                     "cross-reference only: WATERPROOFING lines (T-303 / T-310 own them)",
                     upturn_height_m=0.20, upturn_source="owner Q-24 / UP-WP-UPTURN-015 (0.20 m)",
                     line_id=wp_line["line_id"] if wp_line else None),
            RB.Layer("INSULATION", "UNKNOWN", SEARCHED + "; the only 'INSULATION' print is the POOL detail ST p.7 "
                     "TEXT 1876 (pool base / walls), not extended to a roof (ERS s.3)"),
            RB.Layer("PROTECTION", "UNKNOWN", SEARCHED + "; Q-41 gives ONE screed line on roofs ('falls / "
                     "protection'), a separate protection layer is neither printed nor ruled"),
            RB.Layer("FINISH", "PRINTED" if zz["finish_physical_m2"] is not None else "UNKNOWN",
                     ("designer finish hatch layer 3 " + ", ".join(h["handle"] for h in inp["roofs"][zid]
                                                                   ["finish_hatches"]) +
                      "; material unprinted (HELD), owner Q-42 gives roof tile joints 2 mm")
                     if zz["finish_physical_m2"] is not None else "no plan of the +13.90 roof (D-62, Q-34)"),
        ]
        for row in RB.zone_ledger(zone, layers):
            row["element"] = elem
            if row["layer"] == "FALLS_SCREED":
                mr = rise.get(zid)
                row["thickness_note"] = ("t0 at the outlets unprinted (D-39): HELD; the rise above the t0 plane is "
                                         "DRAWING-CONFIRMED (T-221 model on this outline)")
                if mr and row["plan_area_lo"] is not None:
                    row["above_t0_m3_lo"], row["above_t0_m3_hi"] = round(mr[0], 4), round(mr[1], 4)
                row["trade_conflict"] = ("Q-45 (owner 2026-10-19 21:40) puts the roof falls in the cement bed under "
                                         "the tiles ('roof depending on slope'); Q-41 puts a roof screed in its own "
                                         "line: ONE physical falls volume, carried ONCE here, the trade that books it "
                                         "is open (CONFLICT, Lead)")
            if row["layer"] == "FINISH" and row["plan_area_lo"] is not None:
                row["finish_hatch_literal_m2"] = zz["finish_hatch_m2"]
                row["material_status"] = "HELD (no tile / paving type printed; no owner rule for roofs)"
            rows.append(row)
    # the area round the oval void (+5.50, T-303 SCOPE_UNKNOWN): listed once, not re-measured
    rows.append({"zone": "AREA-OVAL-VOID-550", "element": "1F-AT364-OVAL-VOID", "layer": "ALL",
                 "status": "UNKNOWN", "scope": "UNKNOWN",
                 "scope_source": "T-303: 6.130 m2 net behind the D2:3035 / D2:3036 parapet pair; no ROOF label; roof "
                                 "or not is not on the plan (T-062 held)", "line_state": "NO_LINE"})

    drawing_derived_1390 = {"inside_parapet_faces_m2": z["ROOF-1390"]["face_wall_m2"],
                            "dome_3_footprint_m2": z["ROOF-1390"]["footprints_m2"]["DOME-3"],
                            "dome_3_ring_m": z["ROOF-1390"]["footprint_rings_m"]["DOME-3"],
                            "parapet_faces_m": par["ROOF-1390"],
                            "outer_wall_outline_m2": round(RB.exact_area(_spec(inp["roofs"]["ROOF-1390"]
                                                                                ["outer_wall"])), 6),
                            "open_items": ["third dome (Q-29: upper-roof position held; drawn on layer 2 as 'above' "
                                           "on the 2F plan, tangent to the east inner face)",
                                           "the 2.18 m box seen beyond in SECTION A-A, top +14.40 (T-221 s.5): not "
                                           "identified (lift overrun / stair head?), deduction HELD",
                                           "'WATER TANK PLACE' panel (ST p.6): no tank drawn (T-303 NOT_APPLICABLE)",
                                           "no outlet / fall on any sheet (DRAINS_NOT_DRAWN)"],
                            "status": "HELD (owner Q-34); DRAWING-DERIVED, NOT RELEASED"}
    return {"task": "T-321", "zones": zones, "rows": rows, "closures": closures, "falls": falls,
            "freelancer": {"roof_line_m2": fl, "decomposition": decomp, "residual_m2": round(fl_res, 4),
                           "residual_pct": round(100 * fl_res / fl, 2),
                           "note": "freelancer cells not read here (workbook over the connector limit); 285.00 from "
                                   "T-071 / T-303 (Verifier re-multiplied). A scope decomposition consistent with his "
                                   "figure, NOT a proof of his method"},
            "roof_1390_drawing_derived": drawing_derived_1390}


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v) for k, v in r.items()})
    return buf.getvalue()


LEDGER_COLS = ["zone", "element", "layer", "owner_trade", "in_b13_01", "scope", "status", "edge_basis", "plan_area_lo",
               "plan_area_hi", "sloped_area_lo", "sloped_area_hi", "footprints", "upturn_lm_lo", "upturn_lm_hi",
               "upturn_height_m", "upturn_status", "thickness_m", "thickness_status", "above_t0_m3_lo",
               "above_t0_m3_hi", "finish_hatch_literal_m2", "material_status", "line_id", "line_state", "zone_hold",
               "trade_conflict", "scope_source"]
CLOSURE_COLS = ["closure", "own", "reference", "residual", "named", "unexplained", "closes", "note"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    res = build()
    summary = {k: res[k] for k in ("task", "zones", "freelancer", "roof_1390_drawing_derived", "falls")}
    summary["closures"] = [{k: c[k] for k in ("closure", "residual", "unexplained", "closes")} for c in res["closures"]]
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "ZONE_LAYER_LEDGER_T321.csv").write_text(_csv(res["rows"], LEDGER_COLS), encoding="utf-8")
        (out / "CLOSURE_T321.csv").write_text(_csv(res["closures"], CLOSURE_COLS), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
