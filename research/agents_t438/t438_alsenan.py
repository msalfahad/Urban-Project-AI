"""T-438 development villa (Alsenan is one sample): the ST-02 straight part (RS-S, RS-LD corner landing, RS-A) as drawn
on three plans, and whether the architectural GF frame's '27 risers / 2.950 run with one 0.250 tread / landing
1.250 x 1.450' (T-432 s.3a, worker reading, unverified) is a different stair or a reading of a partial projection.

Build (needs the PRIVATE DXFs from Drive folder 'Alsenan chalet project', decoded into .work/private only):
    python3 -I research/agents_t438/t438_alsenan.py --arch <P7757.dxf> --st <ST7757 dxf.dxf> --write
reads BY HANDLE (type and layer asserted) the two ST-02 frames of the architectural DXF (registered on their own
S-OPENING-radius arcs: GF frame 23E / 23F, 1F frame BA1 / BA2) and ST p.4 (arcs 2DE / 2DD), sweeps each frame for
every line in the RS-LD / RS-A zone (so an omission is a fact, not a guess), and writes ALSENAN_T438.json beside this
file (positions relative to each frame's own arc centre in metres, handles, counts, levels; no drawing coordinates,
no drawing text, no client data).
Check (no private input):
    python3 -I research/agents_t438/t438_alsenan.py --check
re-derives the classification and every quantity effect from the committed JSON and prints REPRODUCED.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t438_rules as R  # noqa: E402

OUT = HERE / "ALSENAN_T438.json"
MM = 0.001
RISE = 4.50                 # GF FFL +1.00 -> 1F FFL +5.50 (Q-50 text; 1F frame LEVEL D16 '+5.50')
CURVED_RISERS = 12          # RS-C 2EA .. 2DF (T-415 MERGED, Checker own)
T_WAIST = 0.16              # 'T 16' block 5B6 in the RS-S panel (Q-47 A), the merged engine basis for RS-S / RS-LD / RS-A
RSC_TREAD_M2 = 4.443096     # T-415 MERGED 8c8372a4: RS-C treads on the structural lane
ARCH_LANE = 1.150           # architectural tread line length (T-412: nosing 5 x 1.150 on RS-A)
ENGINE = {"ST02-RS-S": 0.942732, "ST02-RS-LD": 0.216400, "ST02-RS-A": 0.377093}   # merged T-258 r2 ledger (cited)

# --- handles (walking order) -------------------------------------------------------------------------------------
GF = dict(arcs=("23E", "23F"),
          rss_nosing_vis=["22F", "233", "232", "230", "231", "13E", "13C"],     # layer 5, below the GF cut
          rss_face_hid=["234", "238", "237", "235", "236", "143", "142"],       # layer 2 (HIDDEN), below the cut
          rss_overhead=["13B", "13F", "140", "141"],                            # layer 2, single lines beyond the cut
          rsa_overhead=["144", "145", "146", "4B5"],                            # layer 2, single lines beyond the cut
          nosing7_far_half="13D", rss_void_edge_vis="22E", cut_block="147")
F1 = dict(arcs=("BA1", "BA2"),
          rss_nosing=["B43", "B4A", "B49", "B48", "B47", "B46", "B45", "B44", "B4B", "B4C", "B4D"],   # layer 5
          rss_face=["B4E", "B55", "B54", "B53", "B52", "B51", "B50", "B4F", "B56", "B57", "B58"],     # layer 2
          rsa_nosing=["B59", "B5A", "B5B", "B5C", "D22"],                                            # layer 5
          rsa_face=["B6E", "B6F", "B70", "B71", "D24"],                                              # layer 2
          void_edge="B76", dim_lane="1265", dim_landing_rsa="1257", level="D16")
ST = dict(arcs=("2DE", "2DD"),
          rss_face=["2BA", "2C1", "2C0", "2BF", "2BE", "2BD", "2BC", "2BB", "2C2", "2C3", "2C4"],
          rsa_face=["2C8", "2C9", "2CA", "2CB", "315"],
          wall="283", east="289", rsa_void="2CF", rss_void="2D0", column="374")


def build(arch_path: str, st_path: str) -> dict:
    import ezdxf

    def frame(doc, arcs):
        db = doc.entitydb
        a, b = db[arcs[0]], db[arcs[1]]
        assert a.dxftype() == b.dxftype() == "ARC"
        c = a.dxf.center
        assert math.hypot(b.dxf.center[0] - c[0], b.dxf.center[1] - c[1]) < 1e-3
        radii = sorted([round(a.dxf.radius * MM, 6), round(b.dxf.radius * MM, 6)])

        def ent(h, typ, layer):
            e = db[h]
            assert e.dxftype() == typ, (h, e.dxftype(), typ)
            assert e.dxf.layer == layer, (h, e.dxf.layer, layer)
            return e

        def line(h, layer):
            e = ent(h, "LINE", layer)
            p = ((e.dxf.start[0] - c[0]) * MM, (e.dxf.start[1] - c[1]) * MM)
            q = ((e.dxf.end[0] - c[0]) * MM, (e.dxf.end[1] - c[1]) * MM)
            return p, q

        return db, c, radii, ent, line

    def xpos(line, h, layer):          # an RS-S edge: x = const
        p, q = line(h, layer)
        assert abs(p[0] - q[0]) < 1e-6, h
        return round(p[0], 6)

    def ypos(line, h, layer):          # an RS-A edge: y = const
        p, q = line(h, layer)
        assert abs(p[1] - q[1]) < 1e-6, h
        return round(p[1], 6)

    arch = ezdxf.readfile(arch_path)
    st = ezdxf.readfile(st_path)
    lay = {ln.dxf.name: ln.dxf.linetype for ln in arch.layers}
    assert lay["2"] == "HIDDEN" and lay["5"] == "CONTINUOUS", lay

    # ---------- 1F frame: the plan whose cut lies above the whole straight part (VISIBLE) ----------
    db1, c1, rad1, ent1, line1 = frame(arch, F1["arcs"])
    f1 = dict(radii=rad1,
              rss_nosing=[xpos(line1, h, "5") for h in F1["rss_nosing"]],
              rss_face=[xpos(line1, h, "2") for h in F1["rss_face"]],
              rsa_nosing=[ypos(line1, h, "5") for h in F1["rsa_nosing"]],
              rsa_face=[ypos(line1, h, "2") for h in F1["rsa_face"]])
    vp, vq = line1(F1["void_edge"], "5")
    f1["void_edge_y"] = round(vp[1], 6)
    f1["void_edge_x"] = sorted([round(vp[0], 6), round(vq[0], 6)])
    d = db1[F1["dim_lane"]]
    f1["dim_lane_m"] = round(d.get_measurement() * MM, 6)
    d2 = db1[F1["dim_landing_rsa"]]
    f1["dim_landing_rsa_m"] = round(math.dist(d2.dxf.defpoint2, d2.dxf.defpoint3) * MM, 6)
    lv = ent1(F1["level"], "TEXT", "LEVEL")
    f1["level_text"] = lv.dxf.text

    # ---------- GF frame: the plan whose cut lies below RS-S 8 .. 11, RS-LD and RS-A (OVERHEAD there) ----------
    dbg, cg, radg, entg, lineg = frame(arch, GF["arcs"])
    assert radg == rad1
    gf = dict(radii=radg,
              rss_nosing_vis=[xpos(lineg, h, "5") for h in GF["rss_nosing_vis"]],
              rss_face_hid=[xpos(lineg, h, "2") for h in GF["rss_face_hid"]],
              rss_overhead=[xpos(lineg, h, "2") for h in GF["rss_overhead"]],
              rsa_overhead=[ypos(lineg, h, "2") for h in GF["rsa_overhead"]])
    # the 7th nosing is split at the cut: visible half 13C (layer 5) + far half 13D (layer 2), same x
    gf["nosing7_split"] = [xpos(lineg, GF["rss_nosing_vis"][-1], "5"), xpos(lineg, GF["nosing7_far_half"], "2")]
    p, q = lineg(GF["rss_void_edge_vis"], "5")
    gf["void_edge_vis_x_end"] = round(max(p[0], q[0]), 6)
    cut = entg(GF["cut_block"], "INSERT", "4")
    gf["cut_symbol_x"] = round((cut.dxf.insert[0] - cg[0]) * MM, 6)

    # sweep: every LINE / LWPOLYLINE segment (block contents exploded) in the RS-LD + RS-A zone of each frame
    def sweep(doc, c):
        segs = []
        x0, x1, y0, y1 = 3.0, 4.40, -2.80, -0.25

        def add(e, h):
            t = e.dxftype()
            if t == "LINE":
                pts = [(e.dxf.start[0], e.dxf.start[1]), (e.dxf.end[0], e.dxf.end[1])]
            elif t == "LWPOLYLINE":
                pts = [(p_[0], p_[1]) for p_ in e.get_points("xy")]
            else:
                return
            for a, b in zip(pts, pts[1:]):
                a = ((a[0] - c[0]) * MM, (a[1] - c[1]) * MM)
                b = ((b[0] - c[0]) * MM, (b[1] - c[1]) * MM)
                if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1 or max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1:
                    continue
                segs.append((h, e.dxf.layer, round(a[0], 4), round(a[1], 4), round(b[0], 4), round(b[1], 4)))

        for e in doc.modelspace():
            if e.dxftype() == "INSERT":
                ins = e.dxf.insert
                if abs((ins[0] - c[0]) * MM - 3.7) > 8 or abs((ins[1] - c[1]) * MM + 1.5) > 8:
                    continue
                for v in e.virtual_entities():
                    add(v, e.dxf.handle + "/blk")
            else:
                add(e, e.dxf.handle)
        return segs

    def horizontals_in_rsa_lane(segs, xa=3.0846, xb=4.2346):
        """horizontal segments that cross the RS-A lane (an edge candidate), y between the wall and the arrival."""
        out = []
        for h, layer, ax, ay, bx, by in segs:
            if abs(ay - by) < 1e-4 and min(ax, bx) <= xa + 0.06 and max(ax, bx) >= xb - 0.06 and -2.70 < ay < -0.30:
                out.append({"handle": h, "layer": layer, "y": ay, "x": sorted([ax, bx])})
        return sorted(out, key=lambda r: r["y"])

    gf["rsa_lane_horizontals"] = horizontals_in_rsa_lane(sweep(arch, cg))
    f1["rsa_lane_horizontals"] = horizontals_in_rsa_lane(sweep(arch, c1))
    # anything at the governing first RS-A nosing / face line y = -1.5804 / -1.5304 within the RS-A lane, any length
    segs_g = sweep(arch, cg)
    gf["lines_on_first_rsa_edge"] = sorted(
        {(h, ly) for h, ly, ax, ay, bx, by in segs_g
         if abs(ay - by) < 1e-4 and min(abs(ay + 1.5804), abs(ay + 1.5304)) < 0.002 and max(ax, bx) > 3.0846 + 0.01})

    # ---------- ST p.4 ----------
    dbs, cs, rads, ents, lines = frame(st, ST["arcs"])
    assert rads == rad1
    s = dict(radii=rads,
             rss_face=[xpos(lines, h, "2") for h in ST["rss_face"]],
             rsa_face=[ypos(lines, h, "2") for h in ST["rsa_face"]])
    s["wall_y"] = ypos(lines, ST["wall"], "1")
    s["east_x"] = xpos(lines, ST["east"], "1")
    s["rsa_void_x"] = xpos(lines, ST["rsa_void"], "S-OPENING")
    s["rss_void_y"] = ypos(lines, ST["rss_void"], "S-OPENING")
    col = ents(ST["column"], "LWPOLYLINE", "S-COL.BON")
    s["column"] = [[round((p_[0] - cs[0]) * MM, 6), round((p_[1] - cs[1]) * MM, 6)] for p_ in col.get_points("xy")]
    return {"arch_1f": f1, "arch_gf": gf, "st_p4": s}


def analyse(raw: dict) -> dict:
    f1, gf, s = raw["arch_1f"], raw["arch_gf"], raw["st_p4"]
    E = R.Edge
    # projection = nosing-to-face offset on the visible plan (every pair)
    pr = sorted({round(fa - no, 6) for no, fa in zip(f1["rss_nosing"], f1["rss_face"])}
                | {round(fa - no, 6) for no, fa in zip(f1["rsa_nosing"], f1["rsa_face"])})
    assert len(pr) == 1, pr
    proj = pr[0]

    # ----- RS-S -----
    rss = [
        R.Reading("ARCH_1F", R.VISIBLE, tuple([E(x, R.NOSING) for x in f1["rss_nosing"]] +
                                              [E(x, R.FACE) for x in f1["rss_face"]])),
        R.Reading("ST_P4", R.STRUCTURAL, tuple(E(x, R.FACE) for x in s["rss_face"])),
    ]
    # GF frame: below the cut, pairs (visible nosing + hidden face); beyond the cut, single hidden overhead lines.
    # Family of the overhead singles by coincidence with the GF frame's OWN pairs' spacing is not available beyond the
    # cut; R-T438-1: assign by coincidence with the governing positions (both families tried, reported).
    gov_rss = R.governing(rss, proj, +1)
    faces = gov_rss["faces"]
    nos = [round(f - proj, 6) for f in faces]
    over_as_nosing = all(any(abs(x - n) <= R.REG_TOL for n in nos) for x in gf["rss_overhead"])
    over_as_face = all(any(abs(x - f) <= R.REG_TOL for f in faces) for x in gf["rss_overhead"])
    gf_fam = R.NOSING if over_as_nosing and not over_as_face else (R.FACE if over_as_face and not over_as_nosing
                                                                    else None)
    assert gf_fam == R.NOSING, (over_as_nosing, over_as_face)
    gf_rss = R.Reading("ARCH_GF", R.OVERHEAD, tuple(
        [E(x, R.NOSING) for x in gf["rss_nosing_vis"]] + [E(x, R.FACE) for x in gf["rss_face_hid"]] +
        [E(x, R.NOSING) for x in gf["rss_overhead"]]))
    gov_rss = R.governing(rss + [gf_rss], proj, +1)
    # the T-432 worker reading: first hidden line to last hidden line, regardless of family
    layer2 = sorted(gf["rss_face_hid"] + gf["rss_overhead"])
    worker_run = round(layer2[-1] - layer2[0], 6)
    worker_goings = R.goings(layer2)
    # -- the GF frame's own pairs and singles, same family --
    gf_nosings = sorted(gf["rss_nosing_vis"] + gf["rss_overhead"])

    # ----- RS-LD + RS-A (axis y, rising toward +y) -----
    rsa = [
        R.Reading("ARCH_1F", R.VISIBLE, tuple([E(y, R.NOSING) for y in f1["rsa_nosing"]] +
                                              [E(y, R.FACE) for y in f1["rsa_face"]])),
        R.Reading("ST_P4", R.STRUCTURAL, tuple(E(y, R.FACE) for y in s["rsa_face"])),
    ]
    gf_rsa_fam_nos = all(any(abs(y - n) <= R.REG_TOL for n in f1["rsa_nosing"]) for y in gf["rsa_overhead"])
    gf_rsa_fam_face = all(any(abs(y - f) <= R.REG_TOL for f in f1["rsa_face"]) for y in gf["rsa_overhead"])
    assert gf_rsa_fam_nos and not gf_rsa_fam_face
    gf_rsa = R.Reading("ARCH_GF", R.OVERHEAD, tuple(E(y, R.NOSING) for y in gf["rsa_overhead"]))
    gov_rsa = R.governing(rsa + [gf_rsa], proj, +1)

    # ----- readings as whole stairs -----
    n28 = CURVED_RISERS + len(gov_rss["faces"]) + len(gov_rsa["faces"])
    n27 = CURVED_RISERS + len(gov_rss["faces"]) + len(gf["rsa_overhead"])
    G = round(faces[1] - faces[0], 6)
    rsa_run28 = round(gov_rsa["faces"][-1] - gov_rsa["faces"][0], 6)
    gf_rsa_faces = sorted(round(y + proj, 6) for y in gf["rsa_overhead"])
    rsa_run27 = round(gf_rsa_faces[-1] - gf_rsa_faces[0], 6)
    # wall face 283 to the arrival edge in the FACE family (the printed '240' runs to the face line, R-T438-1)
    land_rsa_28 = round(gov_rsa["faces"][-1] - s["wall_y"], 6)
    land_rsa_27 = round(gf_rsa_faces[-1] - s["wall_y"], 6)
    tab = {
        "28 (ARCH_1F + ST_P4)": R.checks(n28, RISE, G, land_rsa_28, f1["dim_landing_rsa_m"]),
        "27 (ARCH_GF overhead)": R.checks(n27, RISE, G, land_rsa_27, f1["dim_landing_rsa_m"]),
    }
    tab["28 (ARCH_1F + ST_P4)"].update(
        landing_m=[round(s["east_x"] - faces[-1], 6), round(gov_rsa["faces"][0] - s["wall_y"], 6)],
        rss_risers=len(faces), rsa_risers=len(gov_rsa["faces"]), rsa_run_m=rsa_run28,
        landing_level=round(1.00 + (CURVED_RISERS + len(faces)) * RISE / n28, 4))
    tab["27 (ARCH_GF overhead)"].update(
        landing_m=[round(s["east_x"] - faces[-1], 6), round(gf_rsa_faces[0] - s["wall_y"], 6)],
        rss_risers=len(faces), rsa_risers=len(gf_rsa_faces), rsa_run_m=rsa_run27,
        landing_level=round(1.00 + (CURVED_RISERS + len(faces)) * RISE / n27, 4))

    # ----- quantity effects (structural lane; R-T438-5) -----
    from shapely.geometry import Polygon, box
    colp = Polygon(s["column"])
    xw, xe, xv, yw, yv = faces[-1], s["east_x"], s["rsa_void_x"], s["wall_y"], s["rss_void_y"]
    assert abs(gov_rsa["faces"][0] - yv) < 1e-4       # first RS-A face on the RS-S void-edge line (T-432)

    def straight(first_rsa_face):
        land = box(xw, yw, xe, yv).union(box(xv, yv, xe, first_rsa_face)) if first_rsa_face > yv + 1e-9 \
            else box(xw, yw, xe, yv)
        land = land.difference(colp)
        rsa_a = box(xv, first_rsa_face, xe, gov_rsa["faces"][-1]).area
        rss_a = (faces[-1] - faces[0]) * (yv - yw)
        return round(rss_a, 6), round(land.area, 6), round(rsa_a, 6)

    out = {}
    for key, n, first in (("28", n28, gov_rsa["faces"][0]), ("27", n27, gf_rsa_faces[0])):
        Rr = RISE / n
        a_s, a_l, a_a = straight(first)
        v = {"riser_m": round(Rr, 6),
             "plan_m2": {"RS-S": a_s, "RS-LD": a_l, "RS-A": a_a},
             "m3": {"ST02-RS-S": round(R.flight_m3(a_s, T_WAIST, Rr, G), 6),
                    "ST02-RS-LD": round(R.plate_m3(a_l, T_WAIST), 6),
                    "ST02-RS-A": round(R.flight_m3(a_a, T_WAIST, Rr, G), 6),
                    "ST02-RS-C steps (AT_LEAST)": round(R.steps_m3(RSC_TREAD_M2, Rr), 6)}}
        v["m3_straight_total"] = round(v["m3"]["ST02-RS-S"] + v["m3"]["ST02-RS-LD"] + v["m3"]["ST02-RS-A"], 6)
        rsa_treads = (len(gov_rsa["faces"]) if key == "28" else len(gf_rsa_faces)) - 1
        v["b7"] = {"RS-S treads": len(faces) - 1, "RS-S tread m2": round((len(faces) - 1) * G * ARCH_LANE, 6),
                   "RS-A treads": rsa_treads, "RS-A tread m2": round(rsa_treads * G * ARCH_LANE, 6),
                   "RS-A step lm": round(rsa_treads * ARCH_LANE, 6),
                   "RS-A risers": rsa_treads + 1, "RS-A nosing lm": round((rsa_treads + 1) * ARCH_LANE, 6),
                   "ST-02 risers": n}
        out[key] = v
    d28, d27 = out["28"], out["27"]
    delta = {k: round(d27["m3"][k] - d28["m3"][k], 6) for k in d28["m3"]}
    delta["straight_total"] = round(d27["m3_straight_total"] - d28["m3_straight_total"], 6)
    engine_vs_28 = {k: round(ENGINE[k] - d28["m3"][k], 6) for k in ENGINE}

    return {
        "projection_m": proj, "going_m": G,
        "rss": {"governing": gov_rss["governing"], "agreeing": gov_rss["agreeing"], "risers": gov_rss["risers"],
                "run_faces_m": round(faces[-1] - faces[0], 6), "table": gov_rss["table"],
                "gf_overhead_family": gf_fam, "gf_nosings_goings": R.goings(gf_nosings),
                "worker_mixed_run_m": worker_run, "worker_mixed_goings": worker_goings},
        "rsa": {"governing": gov_rsa["governing"], "agreeing": gov_rsa["agreeing"], "risers": gov_rsa["risers"],
                "table": gov_rsa["table"], "gf_lines_on_first_edge": gf["lines_on_first_rsa_edge"],
                "gf_rsa_lane_horizontals": [r["y"] for r in gf["rsa_lane_horizontals"]],
                "f1_rsa_lane_horizontals": [r["y"] for r in f1["rsa_lane_horizontals"]]},
        "checks": tab, "effects": out, "delta_27_minus_28": delta, "engine_minus_28": engine_vs_28,
    }


def summarize(res: dict) -> dict:
    """the committed summary: classes, counts, goings, runs, lane / landing lengths, plan areas and m3 only.
    No position, no coordinate, no drawing text (the raw positions stay in .work/private)."""
    rss, rsa, ck, ef = res["rss"], res["rsa"], res["checks"], res["effects"]

    def cls(t):
        return {k: {"class": v["class"], "edges": v.get("edges"),
                    "missing_edges": len(v.get("missing_faces", []))} for k, v in t.items()}
    return {
        "projection_m": res["projection_m"], "going_m": res["going_m"],
        "rss": {"governing": rss["governing"], "agreeing": rss["agreeing"], "risers": rss["risers"],
                "run_faces_m": rss["run_faces_m"], "classes": cls(rss["table"]),
                "gf_overhead_family": rss["gf_overhead_family"], "gf_same_family_goings": rss["gf_nosings_goings"],
                "worker_mixed_run_m": rss["worker_mixed_run_m"], "worker_mixed_goings": rss["worker_mixed_goings"]},
        "rsa": {"governing": rsa["governing"], "agreeing": rsa["agreeing"], "risers": rsa["risers"],
                "classes": cls(rsa["table"]),
                "gf_missing_edge": "first RS-A edge (index 0 of the governing 5)"
                if len(rsa["table"]["ARCH_GF"].get("missing_faces", [])) == 1 else "other",
                "gf_lines_on_first_edge": len(rsa["gf_lines_on_first_edge"]),
                "gf_lane_lines": len(rsa["gf_rsa_lane_horizontals"]),
                "f1_lane_lines": len(rsa["f1_rsa_lane_horizontals"])},
        "checks": ck, "effects": ef, "delta_27_minus_28": res["delta_27_minus_28"],
        "engine_minus_28": res["engine_minus_28"],
    }


def recompute(sm: dict) -> dict:
    """--check: re-derive every check and every m3 / B7 figure from the committed lengths and counts."""
    G, out = sm["going_m"], {}
    for key in ("28", "27"):
        e = sm["effects"][key]
        n = e["b7"]["ST-02 risers"]
        assert n == CURVED_RISERS + sm["rss"]["risers"] + e["b7"]["RS-A risers"]
        Rr = RISE / n
        a = e["plan_m2"]
        m3 = {"ST02-RS-S": round(R.flight_m3(a["RS-S"], T_WAIST, Rr, G), 6),
              "ST02-RS-LD": round(R.plate_m3(a["RS-LD"], T_WAIST), 6),
              "ST02-RS-A": round(R.flight_m3(a["RS-A"], T_WAIST, Rr, G), 6),
              "ST02-RS-C steps (AT_LEAST)": round(R.steps_m3(RSC_TREAD_M2, Rr), 6)}
        assert m3 == e["m3"], (key, m3, e["m3"])
        k = [c for c in sm["checks"] if c.startswith(key)][0]
        c = R.checks(n, RISE, G, sm["checks"][k]["run_m"], sm["checks"][k]["printed_run_m"])
        for f in ("riser_m", "riser_check", "going_check", "run_check"):
            assert c[f] == sm["checks"][k][f], (key, f)
        out[key] = round(sum(m3[x] for x in ("ST02-RS-S", "ST02-RS-LD", "ST02-RS-A")), 6)
        assert out[key] == e["m3_straight_total"]
    # plan areas conserve: the 27 reading moves one going strip of the RS-A lane into the landing
    a28, a27 = sm["effects"]["28"]["plan_m2"], sm["effects"]["27"]["plan_m2"]
    assert abs(sum(a28.values()) - sum(a27.values())) < 1e-6
    assert sm["rss"]["classes"]["ARCH_GF"]["class"] == R.AGREES
    assert sm["rsa"]["classes"]["ARCH_GF"]["class"] == R.PARTIAL and sm["rsa"]["gf_lines_on_first_edge"] == 0
    assert all(v == 0.0 for v in sm["engine_minus_28"].values())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch")
    ap.add_argument("--st")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        recompute(json.loads(OUT.read_text())["summary"])
        print("REPRODUCED")
        return
    raw = build(a.arch, a.st)
    sm = summarize(analyse(raw))
    recompute(sm)
    doc = {"task": "T-438", "sources": {"arch": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
                                        "st": "Drive 'Alsenan chalet project' / ST7757 dxf.dxf (ST p.4)"},
           "handles": {"arch_gf": GF, "arch_1f": F1, "st_p4": ST},
           "units": "metres; counts, lengths, areas and m3 only (no positions)", "summary": sm}
    if a.write:
        OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(json.dumps(sm, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
