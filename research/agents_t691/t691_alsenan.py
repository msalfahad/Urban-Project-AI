"""T-691 WATERPROOFING ROUND 2 on the development villa (research, unwired; nothing released or wired).

    python3 -I research/agents_t691/t691_alsenan.py            # write out/T691_WP_ROUND2.{json,md}
    python3 -I research/agents_t691/t691_alsenan.py --check    # compare with the committed outputs
    python3 -I research/agents_t691/t691_alsenan.py --dxf <private P7757.dxf>   # re-measure from the drawing

Drawings by Drive title only: 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...)
and sanitary-7757.pdf (image read, sheet 1F at 300 dpi, sheets GF / 2F at 40 dpi). The --dxf re-measure reads named
entity handles only and prints lengths / areas (no coordinates); no drawing content is written to the repository.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "agents_t685"))
import t691_rules as R  # noqa: E402
import t685_rules as R685  # noqa: E402

OUT = HERE / "out"
CANDIDATE = "ARCH_TAKEOFF_V3.0.67 (T-682 LINE_INDEX_V3_0_67; FIN.WP.* lines unchanged since V3.0.66)"

# ------------------------------------------------------------------------------ (a) F-V685-1 main roof +9.70
ROOF = {
    "line": "L-636fd3ff1784a12e653b", "item": "FIN.WP.ROOF", "element": "2F-ROOF-AT379:wp_membrane",
    "released_m2": 115.832,
    "upturn_line": "L-5ce5ba49792e8f9d1f6f", "released_upturn_lm": 92.922,
    "dome_r_m": 2.211091523535753,          # CIRCLE 12EB and 2F33, layer 5, both this radius (own read)
    "sagitta_m": 0.001,                     # engine EXTERIOR_SPACES_V1 SAGITTA_M (1 mm chord tolerance)
    # own face outline this run (handles: parapets layer 5, walls layer 1, D band 12E2 / 12E6, door gap closed on
    # the 2F wall's outer face 1280 / 1281, the 2F block 1280 .. 1281 excluded): D-band reading and wall-face reading
    "outline_dband_m2": 146.37452, "outline_wallface_m2": 146.532, "dband_strip_m2": 0.1575,
    "dband_strip": "0.075 (12E2 at the 2F west wall foot to the wall face, 12E6) x 2.100 (12E6 .. the west-wing "
                   "parapet north face)",
    "band_t321": (115.65646, 115.81396),    # T-321 / T-328 merged, Checker-verified
    "parapet_upturn_lm": 65.140,             # T-062 / T-321 (48.265 + 16.800 + 0.075)
}


def roof_reconciliation():
    r, n = ROOF["dome_r_m"], R.chords_for_sagitta(ROOF["dome_r_m"], ROOF["sagitta_m"])
    true, poly, res = R.circle_true(r), R.circle_inscribed(r, n), R.chord_residual(r, n)
    lo_t321, hi_t321 = ROOF["band_t321"]
    own_hi = R.membrane_net(ROOF["outline_wallface_m2"], [r, r])
    own_lo = R.membrane_net(ROOF["outline_dband_m2"], [r, r])
    chk = R.check_inside_band(ROOF["released_m2"], lo_t321, hi_t321,
                              [("two dome holes taken as inscribed 105-chord polygons (1 mm sagitta), not circles: "
                                "2 x (pi r^2 - 105/2 r^2 sin(2 pi/105))", 2 * res["area_m2"])])
    up_true = ROOF["parapet_upturn_lm"] + 2 * true["ring_m"]
    up_chk = R.check_inside_band(ROOF["released_upturn_lm"], up_true, up_true,
                                 [("two dome rings as 105-chord perimeters, not circumferences",
                                   -2 * res["ring_m"])], unit="lm")
    return {
        "element": "flat roof membrane of the +9.70 terraces round the 2F block: the area inside the parapet / wall "
                   "faces where the membrane turns up (UP-WP-ROOF-001, Q-24), the two dome discs open (Q-24 / Q-29: "
                   "the membrane stops at the dome circle with a 0.20 upturn); flat m2 and upturn lm kept apart",
        "dome": {"r_m": round(r, 6), "chords_engine": n, "true_m2": round(true["area_m2"], 6),
                 "polygon_m2": round(poly["area_m2"], 6), "under_deduction_each_m2": round(res["area_m2"], 6),
                 "true_ring_m": round(true["ring_m"], 6), "polygon_ring_m": round(poly["ring_m"], 6),
                 "ring_short_each_m": round(res["ring_m"], 6)},
        "own_measure": {"outline_wallface_m2": ROOF["outline_wallface_m2"], "outline_dband_m2": ROOF["outline_dband_m2"],
                        "dband_strip_m2": ROOF["dband_strip_m2"], "dband_strip": ROOF["dband_strip"],
                        "net_high_m2": round(own_hi, 5), "net_low_m2": round(own_lo, 5),
                        "vs_t321_high": round(own_hi - hi_t321, 5), "vs_t321_low": round(own_lo - lo_t321, 5)},
        "released_vs_band": chk,
        "corrected": {"value_m2": round(hi_t321, 5), "basis": "the candidate's own basis (inside the wall / parapet "
                      "faces, domes as circles) = T-321 high end", "band_m2": [lo_t321, hi_t321],
                      "status": "OPEN_BOUND (D-BAND 0.1575 m2: what the 0.075 band at the 2F west wall foot is - "
                                "cladding, moulding or a thicker wall base - is printed nowhere; neither end chosen)",
                      "change_m2": round(hi_t321 - ROOF["released_m2"], 5),
                      "change_pct": round((hi_t321 - ROOF["released_m2"]) / ROOF["released_m2"] * 100, 4)},
        "upturn": {"released_lm": ROOF["released_upturn_lm"], "true_lm": round(up_true, 6), "check": up_chk,
                   "corrected_lm": round(up_true, 3)},
        "rolls": "FIN.WP.MEMBRANE_ROLLS 17 pcs: strips by length into whole 1.00 x 10.00 rolls (Q-49 A); a 0.018 m2 "
                 "change inside two dome discs moves no strip end by a roll: unchanged (not re-run)",
    }


# ------------------------------------------------------------------------------ (b) 4 MEASURABLE_NOW (pantry GF-07)
PANTRY_WALLS = [("north", "3.000"), ("west", "4.500"), ("south", "3.000")]   # face runs, open east side 4.500
PANTRY_DOORS = [("D120 33E", "1.000")]
PANTRY_WINDOWS = [("W10 (3CC frame, gap 1.000)", "1.000", None), ("W09 (3BF frame, gap 1.500)", "1.500", None)]
PANTRY_HANDLES = ("own read this run: DIMENSION 5E1 4500.0 / 5D5 3000.0; north 158 1.6591 + gap 1.000 (D120 33E rot "
                  "180) + 159 0.3409 = 3.000, 158 / 15A 0.200 apart; south A6 3.000; west B0 0.100 + gap 1.000 + AF "
                  "1.050 + gap 1.500 + AE 0.850 = 4.500 (W frames 3CC 0.900 / 3BF 1.400 inside the gaps); east B3 4.000 "
                  "+ AD 0.500 layer 5, no wall; column 2FAE 1.100 x 0.250 proud 0.050 over 0.900: run unchanged")


def pantry():
    up = R685.upturn_bound(PANTRY_WALLS, PANTRY_DOORS, PANTRY_WINDOWS)
    return [
        {"line": "L-8090ff20f2b547d1bc96", "item": "FIN.WP.WALL_UPTURN", "unit": "m2", "before": "blank (HELD)",
         "after": f"{up['low_m2']} .. {up['high_m2']}", "status": "OPEN_BOUND (W09 / W10 sills not printed, D-45)",
         "source": PANTRY_HANDLES, "agrees": "T-685 1.400 .. 1.900"},
        {"line": "MISSING FIN.WP.TERMINATION GF-07 open side", "item": "FIN.WP.TERMINATION", "unit": "lm",
         "before": "no line", "after": "4.500", "status": "ASSUMED - OWNER-APPROVED (Q-37 A box line)",
         "source": "B3 4.000 + AD 0.500, layer 5 = DIMENSION 5E1", "agrees": "T-685 4.500"},
        {"line": "MISSING FIN.WP.DOORWAY D-GF-07", "item": "FIN.WP.DOORWAY", "unit": "m2", "before": "no line",
         "after": "0.200", "status": "DRAWING-CONFIRMED", "source": "gap 1.000 x wall 0.200 (158 / 15A)",
         "agrees": "T-685 / T-336 0.200"},
        {"line": "MISSING FIN.WP.DOORWAY_TRANSITION_NR D-GF-07", "item": "FIN.WP.DOORWAY_TRANSITION_NR",
         "unit": "pcs", "before": "no line", "after": "1", "status": "DRAWING-CONFIRMED (m2 stays HELD, Q-35 C)",
         "source": "one door D120 33E", "agrees": "T-685 / T-336 1"},
    ]


# ------------------------------------------------------------------------------ (c) 18 OPEN_BOUND penetration lines
# (room, line id, printed room, FD printed, W.C. pans drawn, note). FD / W.C. from the drainage plans (T-010 kinds,
# re-read this run: sheet 1F at 300 dpi, the GF wet blocks at 300 dpi, 2F at 40 dpi; all AGREE with T-010 / T-685); the 1F west twin cells mapped by geometry (twins()).
PEN = [
    ("GF-R8496F0", "L-6375385673176b8b2c9c", "dewaneya wash", 1, 0, "2 basins: wastes drawn into the FD"),
    ("GF-RA3AD49", "L-229e7bf9e837e1d838bd", "kitchen", 1, 0, ""),
    ("GF-RB28769", "L-bcda623f9ad89eba41db", "core wedge W.C.", 1, 1, ""),
    ("GF-RB62B55", "L-f650522e7882dddccdfa", "dewaneya W.C.", 1, 1, ""),
    ("GF-RD36087", "L-a4bbc2efdb8425554344", "basin space", 1, 0, "basin waste drawn into the FD"),
    ("GF-RD6F891", "L-20dfb3cd1232128b3cb6", "master bath", 1, 1, "shower tray waste into the FD"),
    ("GF-RDBD4F9", "L-0db07ac89503dd3f5980", "wash lobby", 1, 0, "2 basins: wastes drawn into the FD"),
    ("GF-RDF7D28", "L-657bff4f4cc8e417bc6c", "W.C. by the stair", 1, 1, ""),
    ("GF-RF38DAF", "L-5f41701522d675c37b10", "core wedge W.C.", 1, 1, ""),
    ("GF-RFAD3C4", "L-345e907e572a363fb615", "driver W.C.", 1, 1, ""),
    ("GF-RC99C2A", "MISSING FIN.WP.PENETRATION GF-07", "pantry", 1, 0,
     "SS F\\A H/L is a stack at high level: no floor penetration"),
    ("1F-R26FA0D", "L-9971bd68a5150abebe0a", "laundry", 1, 0,
     "SS F\\A-T/B drawn on the north wall line (in the wall), not in the floor"),
    ("1F-R52AC05", "L-fb8f6c4b9b3044505557", "W.C. east of the laundry", 1, 1, "SS T/B in the north wall"),
    ("1F-RED23B8", "L-2af93ddb70a431b92800", "bath by the laundry", 1, 1, "basin waste drawn into the FD"),
    ("1F-R48CDA5", "L-a5f885a2f86ee05d5b8b", "east bath", 1, 1,
     "its soil run is printed 'P 4\" SLOPE 1% B.T.T.S.' (below the slab): the pan outlet passes the slab here, "
     "the strongest sign for the high end; the pan outlet type is still not printed"),
    ("1F-R48AA46", "L-3e6dbcb5614746978a87", "west twin, WEST cell", 1, 1,
     "walk-in zone: one FD 4\" at the screen line; SS T/B in the partition wall"),
    ("1F-R8BDA49", "L-2253a7ed9e80ac00c728", "west twin, EAST cell", 2, 1,
     "FD 3\" in the walk-in zone + FD 4\" by the W.C. / basin"),
    ("2F-RE83BED", "L-faa7232880f13c1e4a99", "W.C. by the stair", 1, 1, "SS T/B beside, in the wall"),
]

# twin mapping: west dome disc (r above, 2F -> 1F shift = x(B3E) - x(12C9) = 44.8527 m, dy 0) over the two 2.050 x
# 2.450 cells; T-283 merged ceiling ledger prints the dome overlap per engine room (1F-R48AA46 1.2410, 1F-R8BDA49
# 1.4227); own overlaps this run below. Cells: WEST x B3E .. C23, y AE4 / AE5 .. C28; EAST x C22 .. C1C, y C25 .. C26.
TWIN_OWN = {"WEST cell (B3E / C23 / C28 / AE4-AE5)": 1.2403, "EAST cell (C22 / C1C / C26 / C25)": 1.4221}
TWIN_T283 = {"1F-R48AA46": 1.2410, "1F-R8BDA49": 1.4227}


def penetrations():
    m = R.map_twin_cells(TWIN_OWN, TWIN_T283)
    rows, lo, hi = [], 0, 0
    for rid, line, name, fd, wc, note in PEN:
        b = R.penetration_bound({"drainage_read": True, "fd": fd, "wc": wc, "mapped": True})
        lo += b["low"]
        hi += b["high"]
        rows.append({"room": rid, "line": line, "name": name, "before": "blank; T-685 AT LEAST 1",
                     "after_low": b["low"], "after_high": b["high"], "status": b["status"], "fd_printed": fd,
                     "wc_drawn": wc, "open_term": b["why"], "note": note})
    return {"rows": rows, "low_pcs": lo, "high_pcs": hi, "twin_map": m,
            "missing_datum": "the W.C. pan outlet (floor S-trap through the slab or wall P-trap) is printed on no "
                             "sheet; the drainage legend defines B.T.T.S. but tags only the 1F east bath run; a "
                             "wet-room / W.C. installation detail fixes the high end",
            "not_counted": "stacks in walls / at high level; basin and shower wastes drawn into a floor drain"}


def build():
    roof = roof_reconciliation()
    pen = penetrations()
    return {"task": "T-691", "candidate": CANDIDATE, "rules": ["R-T691-1", "R-T691-2", "R-T691-3"],
            "roof_F_V685_1": roof, "measurable_now": pantry(), "penetrations": pen,
            "q34_lines": "3 lines (2F top roof membrane, upturn, rolls) stay HELD: owner Q-34 parked, not asked",
            "pool_court": "3 lines stay merged-unwired (T-522 / T-529 values in the overlay; wiring row)"}


def md(d):
    r = d["roof_F_V685_1"]
    c, o, dm = r["released_vs_band"], r["own_measure"], r["dome"]
    L = ["# T-691 waterproofing round 2 (generated by t691_alsenan.py; research, unwired)", "",
         f"Candidate {d['candidate']}.", "", "## (a) F-V685-1 main roof +9.70 membrane", "",
         f"Released {ROOF['released_m2']} m2; band {ROOF['band_t321'][0]} .. {ROOF['band_t321'][1]} m2; excess "
         f"{c['excess']} m2 = named {c['named']} (dome holes as {dm['chords_engine']}-chord polygons, "
         f"{dm['polygon_m2']} vs {dm['true_m2']} m2 each) + residual {c['residual']} m2 (rounding).",
         f"Own outline: wall face {o['outline_wallface_m2']} / D band {o['outline_dband_m2']} m2 -> net "
         f"{o['net_high_m2']} / {o['net_low_m2']} m2 (vs T-321 {o['vs_t321_high']:+} / {o['vs_t321_low']:+}).",
         f"Corrected: {r['corrected']['value_m2']} m2 ({r['corrected']['change_m2']:+} m2, "
         f"{r['corrected']['change_pct']:+} %), {r['corrected']['status']}.",
         f"Upturn: released {r['upturn']['released_lm']} lm, true {r['upturn']['true_lm']} lm "
         f"(rings short {dm['ring_short_each_m']} m each).", "", "## (b) MEASURABLE NOW (pantry GF-07)", "",
         "| line | unit | before | after | status |", "|---|---|---|---|---|"]
    L += [f"| {x['line']} | {x['unit']} | {x['before']} | {x['after']} | {x['status']} |" for x in d["measurable_now"]]
    p = d["penetrations"]
    L += ["", "## (c) floor penetrations (pcs)", "", "| room | line | FD | W.C. | low | high | status |",
          "|---|---|---|---|---|---|---|"]
    L += [f"| {x['room']} ({x['name']}) | {x['line']} | {x['fd_printed']} | {x['wc_drawn']} | {x['after_low']} | "
          f"{x['after_high']} | {x['status']} |" for x in p["rows"]]
    L += ["", f"Total {p['low_pcs']} .. {p['high_pcs']} pcs. Twin map: {p['twin_map']}.",
          f"Missing datum: {p['missing_datum']}.", ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------ --dxf re-measure (private drawing)
def remeasure(path):
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely.ops import unary_union
    doc = ezdxf.readfile(path)
    db, msp = doc.entitydb, doc.modelspace()

    def ln(h):
        e = db[h]
        return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
    d1, d2 = db["12EB"], db["2F33"]
    r = d1.dxf.radius
    assert abs(d2.dxf.radius - r) < 1e-6
    (ax0, ay), (ax1, _) = ln("1280")
    (bx0, _), (bx1, _) = ln("1281")
    door = LineString([(max(ax0, ax1), ay), (min(bx0, bx1), ay)])
    blk = box(min(ax0, ax1), ay, max(bx0, bx1), ay + 30000)
    cx, cy = (d1.dxf.center.x + d2.dxf.center.x) / 2, d1.dxf.center.y
    bb = box(cx - 17000, cy - 11000, cx + 17000, cy + 11000)
    segs = []
    for e in msp.query("LINE LWPOLYLINE ARC"):
        if e.dxf.layer not in ("1", "5", "D", "W"):
            continue
        if e.dxftype() == "LINE":
            g = LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
        elif e.dxftype() == "ARC":
            g = LineString([(p.x, p.y) for p in e.flattening(0.01)])
        else:
            pts = [(v[0], v[1]) for v in e.get_points()]
            if e.closed:
                pts.append(pts[0])
            if len(pts) < 2:
                continue
            g = LineString(pts)
        if g.intersects(bb):
            segs.append(g)
    U = unary_union(segs + [door])
    free = bb.difference(U.buffer(5, join_style="mitre", cap_style="flat"))
    pt = Point(cx, cy - r * 0.5)
    face = [c for c in getattr(free, "geoms", [free]) if c.contains(pt)][0]
    f = Polygon(face.buffer(5, join_style="mitre").difference(blk).exterior)
    (dx, _), (_, dy1) = ln("12E2")[0], ln("12E2")[1]
    ys = [y for x, y in f.exterior.coords if abs(x - dx) < 1]
    strip = box(dx, ay, ln("12E6")[0][0], max(ys))
    out = {"dome_r_m": r / 1000, "outline_dband_m2": round(f.area / 1e6, 5),
           "outline_wallface_m2": round(f.union(strip).area / 1e6, 5), "dband_strip_m2": round(strip.area / 1e6, 5)}
    shift = ln("B3E")[0][0] - ln("12C9")[0][0]
    disc = Point(d1.dxf.center.x + shift, cy).buffer(r, resolution=4096)
    xw0, xw1 = ln("B3E")[0][0], ln("C23")[0][0]
    xe0, xe1 = ln("C22")[0][0], ln("C1C")[0][0]
    y0, y1 = ln("AE4")[0][1], ln("C28")[0][1]
    out["twin_overlap_m2"] = {"WEST": round(box(xw0, y0, xw1, y1).intersection(disc).area / 1e6, 4),
                              "EAST": round(box(xe0, y0, xe1, y1).intersection(disc).area / 1e6, 4)}
    out["shift_m"] = round(shift / 1000, 4)
    return out


def main(argv):
    if "--dxf" in argv:
        print(json.dumps(remeasure(argv[argv.index("--dxf") + 1]), indent=1))
        return 0
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    m = md(d)
    if "--check" in argv:
        ok = (OUT / "T691_WP_ROUND2.json").read_text(encoding="utf-8") == js and \
            (OUT / "T691_WP_ROUND2.md").read_text(encoding="utf-8") == m
        print("T691 outputs", "AGREE" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "T691_WP_ROUND2.json").write_text(js, encoding="utf-8")
    (OUT / "T691_WP_ROUND2.md").write_text(m, encoding="utf-8")
    print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
