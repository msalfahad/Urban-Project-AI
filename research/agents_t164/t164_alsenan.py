"""T-164 development villa: census of every railing / balustrade and shutter the DRAWINGS show (research only).

    python3 -I research/agents_t164/t164_alsenan.py <architectural plan DXF> [--write]

Reads the architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip, kept in .work/private, never
committed) by entity handle, measures each run with t164_railings (UP-STAIR-012 / -013), and with --write puts
RAILINGS_T164.csv, SHUTTERS_T164.csv and summary.json next to this file: lengths, counts, handles and sheet references
only (no coordinates, no drawing content). Stair flight counts come from the merged T-184 input (Checker-verified
source references, research/agents_t184/ALSENAN_STAIR_INPUT.json); a quantity of another task is never used as proof.
Printed values read on the PDF sheets (raster, read by eye, never scaled) are constants below with their sheet.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t164_railings as R  # noqa: E402

MM = 0.001
STAIR_INPUT = HERE.parent / "agents_t184" / "ALSENAN_STAIR_INPUT.json"

# printed on the PDF sheets (read, not scaled)
PRINTED = {
    "SE_RAIL_HEIGHT": (1.04, "Pages_05-06 p.6 SOUTH EAST ELEVATION: '104' from the parapet coping line to the rail top"),
    "NW_RAIL_HEIGHT": (1.10, "Pages_07-08 p.8 NORTH WEST ELEVATION: '110' from the +9.70 roof level to the rail top"),
    "W14": ("245 x 140", "p.6 SE: W14 '245' wide, '140' high"),
    "FENCE": ("580 + 250", "Pages_11-12 p.12 FENCE PLAN: 580 solid + 250 gate; FENCE SECTION 265 = 50 + 215"),
}


def _dxf(path):
    import ezdxf
    doc = ezdxf.readfile(path)
    return doc, doc.entitydb


def _ln(db, h):
    e = db[h]
    if e.dxftype() != "LINE":
        raise R.RailInputError(f"handle {h} is {e.dxftype()}, expected LINE")
    a, b = e.dxf.start, e.dxf.end
    return (a[0], a[1]), (b[0], b[1])


def _len(db, h):
    e = db[h]
    t = e.dxftype()
    if t == "LINE":
        a, b = _ln(db, h)
        return math.hypot(b[0] - a[0], b[1] - a[1]) * MM
    if t == "ARC":
        sw = (e.dxf.end_angle - e.dxf.start_angle) % 360.0
        return math.radians(sw) * e.dxf.radius * MM
    if t == "LWPOLYLINE":
        pts = [(x, y) for x, y, *_ in e.get_points()]
        return R.polyline_length(pts) * MM
    raise R.RailInputError(f"handle {h}: unsupported {t}")


def _layer(db, h):
    return db[h].dxf.layer


def st02(db):
    """Round reception stair: inner balustrade band from the volute, round the curved and straight flights, the corner
    landing, up the short flight and along the 1F void edge (one continuous drawn band, layer 5, 50 mm wide)."""
    arc_o, arc_i = db["B9C"], db["BA2"]                       # band edges r 1580.5 / 1530.5 round one centre
    c = (arc_o.dxf.center[0], arc_o.dxf.center[1])
    if math.hypot(arc_i.dxf.center[0] - c[0], arc_i.dxf.center[1] - c[1]) > 1.0:
        raise R.RailInputError("band arcs are not concentric")
    r = 0.5 * (arc_o.dxf.radius + arc_i.dxf.radius)            # band centreline
    curved = ["BB9", "BB7", "BB5", "BB3", "BB1", "BAF", "BAD", "BAB", "BA9", "BA7", "BA5", "BA3"]
    straight = ["B43", "B4A", "B49", "B48", "B47", "B46", "B45", "B44", "B4B", "B4C", "B4D"]
    short = ["B59", "B5A", "B5B", "B5C", "D22"]

    def inner_first(h):
        p, q = _ln(db, h)
        return (q, p) if math.hypot(p[0] - c[0], p[1] - c[1]) < math.hypot(q[0] - c[0], q[1] - c[1]) else (p, q)
    lines = [inner_first(h) for h in curved]
    arcs, angs = R.curved_tread_lengths(c, r, lines)
    arc_end = arc_o.dxf.end_angle % 360.0                     # where the band leaves the circle (straight run starts)
    end_pt = (c[0] + r * math.cos(math.radians(arc_end)), c[1] + r * math.sin(math.radians(arc_end)))
    xs = [_ln(db, h)[0][0] for h in straight]
    transition = r * math.radians(R.sweep_deg(angs[-1], arc_end)) + abs(xs[0] - end_pt[0])
    straights = [abs(b - a) for a, b in zip(xs, xs[1:])]
    treads_mm = arcs + [transition] + straights               # 11 + 1 + 10 = 22 goings, first riser to last riser
    data = json.loads(STAIR_INPUT.read_text())
    st = next(s for s in data["stairs"] if s["stair_id"] == "ST-02")
    riser = next(f for f in st["flights"] if f["id"] == "RS-S")["riser"]
    if len(treads_mm) != 22:
        raise R.RailInputError("ST-02 tread count changed")
    sloped = R.per_tread([t * MM for t in treads_mm], riser)
    plan = sum(treads_mm) * MM
    single = (R.seg_helical(r * MM, math.radians(R.sweep_deg(angs[0], arc_end)), 12 * riser)
              + R.seg_sloped(abs(xs[-1] - end_pt[0]) * MM, 10 * riser))
    # corner landing: band centre x vs last straight riser, band centre y vs first short-flight riser
    bx = _ln(db, "B75")[0][0] - 25.0                                   # right band centre (B75 outer, inner 50 west)
    by = _ln(db, "B76")[0][1] + 25.0                                   # bottom band centre (B76 outer, inner 50 north)
    landing = (abs(bx - xs[-1]) + abs(_ln(db, "B59")[0][1] - by)) * MM
    ys = [_ln(db, h)[0][1] for h in short]
    ra_h = abs(ys[-1] - ys[0]) * MM
    ra = R.seg_sloped(ra_h, (len(short) - 1) * riser)
    top_y = _ln(db, "B74")[0][1] - 25.0
    right = abs(top_y - ys[-1]) * MM
    top = abs(_ln(db, "B74")[0][0] - bx) * MM
    volute = 0.5 * (_len(db, "BBB") + _len(db, "BBD"))
    segs = [("volute at the first step (horizontal, mean of the two drawn edge arcs BBB / BBD)", volute),
            (f"curved + straight flights RS-C / RS-S, 22 goings per tread (riser {riser:.6f})", sloped),
            ("corner landing RS-LD, band corner", landing),
            ("short flight RS-A, 4 goings", ra),
            ("1F void edge beside RS-A to the void corner (+5.50, horizontal)", right),
            ("1F void edge, gallery (+5.50, horizontal) to the wall", top)]
    detail = {"rail_radius_m": r * MM, "curved_plan_m": sum(arcs) * MM, "transition_plan_m": transition * MM,
              "straight_plan_m": sum(straights) * MM, "flights_plan_m": plan, "flights_sloped_m": sloped,
              "single_segment_formula_m": single, "landing_m": landing, "RS-A_plan_m": ra_h, "RS-A_m": ra,
              "void_right_m": right, "void_top_m": top, "volute_m": volute,
              "plan_projection_whole_m": plan + landing + ra_h + right + top + volute}
    return segs, detail


def st01(db):
    data = json.loads(STAIR_INPUT.read_text())
    st = next(s for s in data["stairs"] if s["stair_id"] == "ST-01")
    segs = []
    for f in st["flights"]:
        h, v, l_ = R.flight_pitch(f["risers"], f["riser"], f["going"])
        segs.append((f"{f['id']} inner balustrade, pitch line H {h:.3f} V {v:.4f}", l_))
    segs.append(("1F well-end turn at the floor landing (AC3, 0.200, horizontal)", _len(db, "AC3")))
    segs.append(("half landing MS2-LD well-end turn (A9B, 0.200, horizontal)", _len(db, "A9B")))
    segs.append(("2F floor-edge guard over the opening (138A / 138B centreline, horizontal)",
                 R.centreline_of_pair(_len(db, "138A"), _len(db, "138B"))))
    held = [("MS1-T winder turn GF -> 1F (5 risers, 0.833 m rise; rail path round the 0.10 m well not dimensioned)",
             None),
            ("MS1-LD half-landing turn GF -> 1F (not drawn as a closure on the GF plan)", None)]
    bands = {h: round(_len(db, h), 3) for h in ("A8D", "A8E", "A8F", "A90", "1356", "1357", "1358", "1359")}
    d1 = next(s for s in data["stairs"] if s["stair_id"] == "ST-01b")["flights"][0]
    _, _, d1_l = R.flight_pitch(d1["risers"], d1["riser"], d1["going"])
    return segs + held, bands, d1_l


def roofs(db):
    """Roof-edge railings: 50 mm bands drawn inside the parapet line on the plans, cross-checked on the elevations."""
    street = R.polyline_length([(0, 0), (0, (_len(db, "12C8") + 0.025))])        # band 12C8 to the corner centre
    court = R.centreline_of_pair(_len(db, "12A8"), _len(db, "12A9"))
    nw = R.centreline_of_pair(_len(db, "1322"), _len(db, "1323"))
    annex_st = R.centreline_of_pair(_len(db, "B2D"), _len(db, "B2E"))
    annex_ct = R.centreline_of_pair(_len(db, "B27"), _len(db, "B28"))
    sea = R.centreline_of_pair(_len(db, "C85"), _len(db, "C86"))
    elev = {"SE_top_rail_223C": _len(db, "223C"), "SE_mid_rail_23BE": _len(db, "23BE"),
            "NW_top_rail_279F": _len(db, "279F"), "NW_mid_rail_27A0": _len(db, "27A0")}
    return {"street": street, "court": court, "nw": nw, "annex_st": annex_st, "annex_ct": annex_ct, "sea": sea,
            "elev": elev}


def other(db):
    out = {"d23": R.centreline_of_pair(_len(db, "AF5"), _len(db, "AF6")),
           "st02_outer_band_plan": (_len(db, "BA1"), _len(db, "BA0")),
           "fence_line_GF": _len(db, "10F"), "fence_gate_dashed_GF": _len(db, "110"),
           "projecting_outline_1F_SE": _len(db, "B3C") + _len(db, "B3D") + _len(db, "C49"),
           "beam_ends_1F_SE": 3,
           "W14_leaf_outer": ((abs(_ln(db, "1F55")[0][0] - _ln(db, "1D50")[0][0])) * MM,
                              (abs(_ln(db, "1D4D")[0][0] - _ln(db, "1D4F")[0][0])) * MM),
           "W14_leaf_panel": ((abs(_ln(db, "1F61")[0][0] - _ln(db, "2374")[0][0])) * MM,
                              (abs(_ln(db, "24F5")[0][0] - _ln(db, "2515")[0][0])) * MM),
           "W14_leaf_h": _len(db, "1F55")}
    for h in ("B3C", "B3D"):
        if _layer(db, h) != "D":
            raise R.RailInputError(f"{h} is not on layer D")
    return out


def build(dxf_path):
    _, db = _dxf(dxf_path)
    s2, s2d = st02(db)
    s1, bands, d1_l = st01(db)
    rf = roofs(db)
    ot = other(db)
    se_h, nw_h = PRINTED["SE_RAIL_HEIGHT"][0], PRINTED["NW_RAIL_HEIGHT"][0]
    runs = [
        R.run("RL-01", "ROOF_GUARD", [("1F roof street (SE) edge, band 12C8 to the corner", rf["street"]),
                                       ("1F roof court (SW) return, band 12A8 / 12A9", rf["court"])],
              height_m=se_h, source="2F plan (Pages_05-06 p.5) + DXF; SE elevation p.6 (X railing, '104'); "
              "SW elevation p.7 (return drawn)", note="on the low part of the wavy parapet, +9.70 roof"),
        R.run("RL-02", "ROOF_GUARD", [("1F roof sea (NW) edge, band 1322 / 1323", rf["nw"])], height_m=nw_h,
              source="2F plan + DXF; NW elevation p.8 (X railing, '110'); DXF NW top rail 279F",
              note="on the low part of the wavy parapet, +9.70 roof"),
        R.run("RL-03", "ROOF_GUARD", [("annex (dewaneya) roof street face, band B2D / B2E", rf["annex_st"]),
                                       ("annex roof court face, band B27 / B28", rf["annex_ct"])],
              source="1F plan (sheet04) + DXF; FENCE ELEVATION p.12 (X railing on the annex roof); SW p.7, NE p.9",
              note="+4.30 annex roof; height not printed"),
        R.run("RL-04", "BALCONY_GUARD", [("GF roof strip in front of W15 / W16 (sea), band C85 / C86", rf["sea"])],
              status="HELD", source="1F plan (sheet04) + DXF only",
              note="NW elevation p.8 draws end piers and NO infill between them: plan and elevation disagree on "
                   "what stands on this edge (railing, glazing, nothing); T-162 counts a +5.50 -> +6.00 parapet "
                   "chain here (cross-trade conflict)"),
        R.run("RL-05", "STAIR_GUARD", s2, source="1F plan (sheet04) + GF plan (sheet03) + DXF layer 5; T-184 "
              "riser counts", note="ST-02 inner balustrade + 1F gallery round the void; height / material not printed"),
        R.run("RL-06", "FLOOR_EDGE_GUARD", [("1F living floor edge beside RS-A and the corner landing (AF5 / AF6)",
                                             ot["d23"])],
              source="1F plan + DXF; GF plan draws it overhead (layer 2, single line 4AF)",
              note="classifies designer item D-23 (0.05 m element) as a balustrade band (same graphic as RL-05)"),
        R.run("RL-07", "STAIR_GUARD", s1, source="GF / 1F / 2F plans + DXF bands (central 0.10 m well); section "
              "A-A (sheet10) draws a balustrade on every flight", note="ST-01 dog-leg, inner side of each flight"),
        R.run("RL-08", "STAIR_GUARD", [("ST-01b lobby flight D1, one rail drawn on section A-A", d1_l)],
              source="section A-A (sheet10); T-184 D1 counts", note="a second side is not drawn: not added"),
        R.run("RL-09", "STAIR_GUARD_OR_STRING", [("ST-02 outer 50 mm band r 2.730 / 2.780 (plan only)", None)],
              status="UNKNOWN", source="GF + 1F plans + DXF BA0 / BA1 (23D / 23E)",
              note=f"plan length of the band {ot['st02_outer_band_plan'][0]:.3f} .. "
                   f"{ot['st02_outer_band_plan'][1]:.3f} m; guard or string not established (corner fill unknown)"),
        R.run("RL-10", "FENCE_RAILING", [("street fence, X railing in the wall's dip", None)], status="HELD",
              source="FENCE ELEVATION p.12 only (not in the DXF)", note="railing length not printed; never scaled"),
        R.run("RL-11", "STAIR_GUARD", [("ST-03 entrance stair +0.15 -> +1.00 and its +1.00 landing edge", None)],
              status="HELD", source="GF plan sheet03 + DXF: no railing drawn; render T-161 F04 shows a balustrade",
              note="open edges (0.85 m rise) with no guard drawn: designer item, never 0"),
        R.wall_handrail("RL-12", shown=False, source="ST-01 / ST-02 wall sides: none drawn (UP-STAIR-013)"),
    ]
    shutters = [R.shutter("W14", 2, ot["W14_leaf_outer"][0], ot["W14_leaf_h"],
                          source="SE elevation p.6 + DXF (left leaf 1F55..1D50, right 1D4D..1D4F)"),
                R.shutter("W11", 2, source="FENCE ELEVATION p.12 (dewaneya street face)"),
                R.shutter("W12", 2, source="FENCE ELEVATION p.12 (dewaneya street face)"),
                R.shutter("W02", 0, source="NW p.8 / sheet03: none drawn (render F23 shows shutters)"),
                R.shutter("W15 / W16 / W17 / W18 / W01 / W13 / W26", 0, source="elevations: none drawn")]
    return runs, shutters, {"st02": s2d, "st01_plan_bands_m": bands, "roofs": rf, "other": ot}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    runs, shutters, det = build(args[0])
    cen = R.census(runs)
    for r_ in runs:
        print(r_["id"], r_["kind"], r_["status"], r_.get("measured_lm"), r_.get("held_parts") or "")
    print(json.dumps(cen, indent=1))
    print(json.dumps(det, indent=1, default=float))
    if "--write" in sys.argv:
        with open(HERE / "RAILINGS_T164.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["RUN", "KIND", "SEGMENT", "LENGTH_LM", "RUN_STATUS", "HEIGHT_PRINTED_M", "SOURCE", "NOTE"])
            for r_ in runs:
                segs = r_.get("segments") or [("(excluded: " + r_.get("excluded", "") + ")", None)]
                for lab, v in segs:
                    w.writerow([r_["id"], r_["kind"], lab, "" if v is None else f"{v:.3f}", r_["status"],
                                r_.get("height_m") or "", r_.get("source", ""), r_.get("note", "")])
        with open(HERE / "SHUTTERS_T164.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["OPENING", "LEAVES_PCS", "LEAF_SIZE_M", "STATUS", "M2", "SOURCE"])
            for s in shutters:
                w.writerow([s["opening"], s["leaves_pcs"], s.get("leaf_size_m") or "", s["status"],
                            s.get("m2_status", ""), s["source"]])
        summ = {"census": cen, "runs": {r_["id"]: [r_["status"], r_.get("measured_lm")] for r_ in runs},
                "shutter_leaves_drawn": sum(s["leaves_pcs"] for s in shutters), "detail": det,
                "printed": {k: v[0] for k, v in PRINTED.items()}}
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
