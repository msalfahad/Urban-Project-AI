"""T-718 own drawing read (worker 2, 2026-11-11): the stair geometry T-718 needs, by handle, as RELATIVE values only.

Writes research/agents_t718/T718_DRAWN.json: stations in metres along a flight from its first drawn front edge, radii
and perpendicular offsets from the round stair's centre, lengths, handles, layers. No absolute coordinate, no drawing
text, no client name. Inputs are the private Drive copies decoded by the wrapper into .work/private (never committed):
    bash scripts/agent_env.sh run --tree task-T-718 research/agents_t718/t718_extract.py \
        --arch .work/private/P7757_DXF_COMPRESSED/P7757.dxf --st .work/private/ST7757.dxf [--write]
(or the venv python with -I). The builder t718_alsenan.py reads only the committed JSON.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import ezdxf

HERE = Path(__file__).resolve().parent
OUT = HERE / "T718_DRAWN.json"
MM = 0.001

# straight flights whose skirting pieces are cut inside the flight (T-410 side table): front edges (the downhill line
# of each drawn pair, T-412) and riser faces (its companion 0.050 uphill), in walking order; the cut handles and the
# coordinate of each cut on the flight axis; plan = the plan sheet the cut is drawn on ('GF' cut moved to the flight's
# sheet by the stacked-column offset).
FLIGHTS = {
    "MS2-L": dict(sheet="1F", axis="y", fronts="AC0 ABF AB5 AB6 AB7 AB8 AAD AAE AB0 AAF A98 A97",
                  faces="AC2 AC1 AB9 ABA ABB ABC AB1 AB2 AB3 AB4 A99 A9A", wall="AF1",
                  cuts=[("column 3005 near face", "3005", "min"), ("column 3005 far face", "3005", "max"),
                        ("window jamb C5C", "C5C", "min")]),
    "MS1-L": dict(sheet="GF", axis="y", fronts="DC DD CE CF C6 C7 C9 C8 C5 485",
                  faces="DE DF D0 D1 CA CB CC CD - 486", wall="298",
                  cuts=[("column 2FBD near face", "2FBD", "min"), ("column 2FBD far face", "2FBD", "max"),
                        ("window jamb 354", "354", "min")]),
    "MS1-U": dict(sheet="1F", axis="-y", fronts="A92 A95 AA5 AA6 AA7 AA8 AA9 AAA AAB AAC ABE",
                  faces="A93 A94 A9E AA0 A9F A9D AA4 AA3 AA2 AA1 ABD", wall="B16",
                  cuts=[("GF face 21B end / hidden opening 33C start", "33C", "max"),
                        ("hidden opening 33C end / GF face 21C start", "33C", "min")]),
    "RS-S": dict(sheet="1F", axis="x", fronts="B43 B4A B49 B48 B47 B46 B45 B44 B4B B4C B4D",
                  faces="B4E B55 B54 B53 B52 B51 B50 B4F B56 B57 B58", wall="336",
                  cuts=[("column 2FD2 near face", "2FD2", "min"), ("column 2FD2 far face", "2FD2", "max")]),
}
GF_CUTS = {"2FBD", "354", "33C", "2FD2"}          # drawn on the GF sheet
STACK = ("3005", "2FBD")                           # the same column on 1F and GF: gives the sheet offset

# RS-C (ST-02 curved flight), architectural plan handles; the structural sheet's copies checked by a rigid fit
RS_C = dict(inner_edge="23F", outer_edge="23E", inner_band="239", outer_band="23D",
            fronts="256 254 252 250 24E 24C 24A 248 246 244 242 240",
            faces="257 255 253 251 24F 24D 24B 249 247 245 243 241",
            curtail_front={"1": "258", "2": "25A"}, curtail_face={"1": "259", "2": "25B"})
ST_FACES = "2EA 2E9 2E8 2E7 2E6 2E5 2E4 2E3 2E2 2E1 2E0 2DF"
ST_EDGES = ("2DE", "2DD")
# MS1-T turn: the GF winder fan seen through the 1F void (T-684 fact 5), and the two walls of the turn square
MS1_T = dict(fan_front="BE8 BE6 BEA", fan_face="BE9 BE7 BEB", west_wall="AF0", north_wall="ADE")


def sha8(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


def ends(e):
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)


def bbox(e):
    pts = [(p[0], p[1]) for p in e.get_points()] if e.dxftype() == "LWPOLYLINE" else list(ends(e))
    return min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)


def straight(arch):
    db = arch.entitydb
    a, g = bbox(db[STACK[0]]), bbox(db[STACK[1]])
    dx, dy = a[0] - g[0], a[2] - g[2]
    assert abs(dy) < 1e-6 and abs((a[1] - a[0]) - (g[1] - g[0])) < 1e-6, "stacked column offset not a pure x shift"
    out = {"sheet_offset_gf_to_1f_x_m": round(dx * MM, 4), "stack_pair": list(STACK), "flights": {}}
    for name, f in FLIGHTS.items():
        ax, sign = f["axis"].lstrip("-"), (-1 if f["axis"].startswith("-") else 1)
        k = 1 if ax == "y" else 0

        def pos(h, which="mid"):
            e = db[h]
            b = bbox(e)
            lo, hi = (b[2], b[3]) if ax == "y" else (b[0], b[1])
            if which == "mid":
                assert hi - lo < 1e-6, f"{h} not square to the flight axis"
                return lo
            return lo if which == "min" else hi
        fr = [pos(h) for h in f["fronts"].split()]
        s0 = fr[0]
        st = lambda v: round(sign * (v - s0) * MM, 6)      # noqa: E731  station from front edge 1, uphill positive
        fronts = [st(v) for v in fr]
        faces = [None if h == "-" else st(pos(h)) for h in f["faces"].split()]
        cuts = []
        for label, h, which in f["cuts"]:
            v = pos(h, which)
            if h in GF_CUTS and f["sheet"] == "1F" and ax == "x":
                v += dx
            cuts.append({"label": label, "handle": h, "station_m": st(v)})
        lens = sorted({round(math.dist(*ends(db[h])) * MM, 6) for h in f["fronts"].split()})
        proj = sorted({round(b - a, 6) for a, b in zip(fronts, faces) if b is not None})
        out["flights"][name] = {"sheet": f["sheet"], "front_handles": f["fronts"].split(),
                                "face_handles": f["faces"].split(), "front_stations_m": fronts,
                                "face_stations_m": faces, "nosing_projection_m": proj, "front_lengths_m": lens,
                                "cuts": sorted(cuts, key=lambda c: c["station_m"]), "wall_face": f["wall"]}
    return out


def circ(e):
    c = e.dxf.center
    return (c.x, c.y), e.dxf.radius


def line_vs_centre(e, C):
    a, b = ends(e)
    if math.dist(a, C) > math.dist(b, C):
        a, b = b, a
    n = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / n, (b[1] - a[1]) / n
    off = abs((a[0] - C[0]) * uy - (a[1] - C[1]) * ux)
    return n, math.dist(a, C), math.dist(b, C), off


def arc_len(e):
    return e.dxf.radius * math.radians((e.dxf.end_angle - e.dxf.start_angle) % 360)


def round_stair(arch, st):
    db = arch.entitydb
    C, ri = circ(db[RS_C["inner_edge"]])
    C2, ro = circ(db[RS_C["outer_edge"]])
    assert math.dist(C, C2) < 1e-6
    res = {"centre": "common centre of 23F / 23E / 239 / 23D (relative values only)",
           "inner_edge_r_m": round(ri * MM, 6), "outer_edge_r_m": round(ro * MM, 6),
           "inner_band_r_m": round(circ(db[RS_C["inner_band"]])[1] * MM, 6),
           "outer_band_r_m": round(circ(db[RS_C["outer_band"]])[1] * MM, 6), "lines": {}}
    for kind in ("fronts", "faces"):
        rows = []
        for i, h in enumerate(RS_C[kind].split(), 1):
            n, ra, rb, off = line_vs_centre(db[h], C)
            rows.append({"riser": i, "handle": h, "layer": db[h].dxf.layer, "drawn_m": round(n * MM, 6),
                         "r_in_m": round(ra * MM, 6), "r_out_m": round(rb * MM, 6), "offset_m": round(off * MM, 6)})
        res["lines"][kind] = rows
    res["curtail"] = {k: {i: {"handle": h, "layer": db[h].dxf.layer, "arc_m": round(arc_len(db[h]) * MM, 6),
                              "r_m": round(db[h].dxf.radius * MM, 6)}
                          for i, h in RS_C[f"curtail_{k}"].items()} for k in ("front", "face")}
    # the structural sheet's riser lines = the architectural faces under one rigid motion (fit residual reported)
    sdb = st.entitydb
    P, Q = [], []
    for hs, ha in zip(ST_FACES.split(), RS_C["faces"].split()):
        P += list(ends(sdb[hs]))
        Q += list(ends(db[ha]))
    import numpy as np
    P, Q = np.array(P), np.array(Q)
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    R = Vt.T @ U.T
    resid = float(np.abs((P - pc) @ R.T + qc - Q).max())
    sci, sri = circ(sdb[ST_EDGES[0]])
    sco, sro = circ(sdb[ST_EDGES[1]])
    res["structural_check"] = {"st_face_handles": ST_FACES.split(), "rigid_fit_det": round(float(np.linalg.det(R)), 9),
                               "rigid_fit_max_residual_mm": round(resid, 6),
                               "st_opening_r_m": [round(sri * MM, 6), round(sro * MM, 6)],
                               "st_opening_handles": list(ST_EDGES)}
    return res


def turn(arch):
    db = arch.entitydb
    rows = []
    corner = None
    for kind in ("fan_front", "fan_face"):
        for h in MS1_T[kind].split():
            a, b = ends(db[h])
            rows.append({"handle": h, "layer": db[h].dxf.layer, "kind": kind, "drawn_m": round(math.dist(a, b) * MM, 6)})
    a, _ = ends(db["BE6"])
    corner = a
    wx = ends(db[MS1_T["west_wall"]])[0][0]
    ny = ends(db[MS1_T["north_wall"]])[0][1]
    side_w = abs(corner[0] - wx) * MM
    side_n = abs(corner[1] - ny) * MM
    _, b6 = ends(db["BE6"])
    _, b7 = ends(db["BE7"])
    # signed overshoot of the companion BE7's far end past each wall face, measured away from the inner corner
    over_w = (corner[0] - b7[0]) * (1 if corner[0] > wx else -1) * MM - side_w
    over_n = (b7[1] - corner[1]) * (1 if ny > corner[1] else -1) * MM - side_n
    return {"inner_corner": "start of BE6 (the fan's common point)", "walls": [MS1_T["west_wall"], MS1_T["north_wall"]],
            "side_to_west_wall_m": round(side_w, 6), "side_to_north_wall_m": round(side_n, 6),
            "BE6_end_on_wall_corner_m": round(math.dist(b6, (wx, ny)) * MM, 6), "fan": rows,
            "BE7_end_past_west_face_m": round(over_w, 6), "BE7_end_past_north_face_m": round(over_n, 6),
            "note": "BE7 / BE9 / BEB (layer 2) are the 0.050 companions; BE7 is drawn as long as BE6, so its far end "
                    "passes the north face (drafting overshoot of an offset copy, not a longer riser: the walls bound it)"}


def main(argv):
    arch_p = argv[argv.index("--arch") + 1]
    st_p = argv[argv.index("--st") + 1]
    arch, st = ezdxf.readfile(arch_p), ezdxf.readfile(st_p)
    d = {"schema": "T718_DRAWN_V1", "read_by": "worker 2, T-718, 2026-11-11 (own read)",
         "sources": {"arch": {"drive": "Alsenan chalet project / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
                              "sha256_8": sha8(arch_p)},
                     "st": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256_8": sha8(st_p)}},
         "straight": straight(arch), "round_stair_rs_c": round_stair(arch, st), "turn_ms1_t": turn(arch)}
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(js)
    print(js)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
