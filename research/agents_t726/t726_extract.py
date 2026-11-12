"""T-726 DRAWING READ (research, unwired): the faces of the STAIR-HOUSE family (ST-01 dog-leg shaft box, its arrival
walls, the lift shaft V-03) and every PRINTED LEVEL on the architectural DXF (Drive "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip, P7757.dxf sha256 ab54dd55..., decoded by the wrapper into .work/private only), read by HANDLE,
so that the builder can test whether any drawn face of the family is 2.50 m wide and 5.40 m high (the freelancer's
'continued' stair-house row) and whether the room lines next to the shaft carry its faces once.

Writes T726_DRAWN.json: handles, lengths, level values and frame / scope classes only (no coordinate, no drawing text
other than the printed level figure, no client name). Every length is a difference of two drawn coordinates on the same
plan frame.

    .work/venv/bin/python -I research/agents_t726/t726_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t726/t726_extract.py --dxf <P7757.dxf>          (re-read, compare)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "T726_DRAWN.json"
ROUND = 6

# ---- handles: ST-01 box per plan frame (inner wall-face lines, layer 1) ---------------------------------------------
# W / E = the long faces (outer wall / lift-shaft wall), N = the far end, S = the GF south wall or, on 1F / 2F, the
# arrival wall across the landing (the box is longer above +5.50: the landing lies south of the GF south wall).
BOX = {
    "GF": {"W": "298", "E": "21C", "N": "26E", "S": "220", "S_outer": "20F"},
    "1F": {"W": "AF1", "E": "B16", "N": "ADE", "S": "AEB"},
    "2F": {"W": "12B7", "E": "129A", "N": "127E", "S": "1283"},
}
# the 1F / 2F W face pieces south of the GF south wall (arrival zone) and the 2F landing slab edge (layer 5, open side)
W_ARRIVAL = {"1F": "C21", "2F": "12B7"}
SLAB_EDGE_2F = "138B"
# lift shaft V-03, inner faces per frame: west x, east x, north y, south y (south = the lift door wall)
LIFT = {
    "GF": {"W": "216", "E": "212", "N": "219", "S": "21E"},
    "1F": {"W": "B13", "E": "B11", "N": "B15", "S": "B1A"},
    "2F": {"W": "1297", "E": "1293", "N": "1299", "S": "129C"},
}
LIFT_OUTER_E_GF = "222"            # the lift shaft's east outer wall face on GF (lift outer width = 21C .. 222)
ANNEX_ROOF_BLOCK_1F = "B8D"        # 'ROOF' block on the 1F plan beside the +4.30 level (the single-storey annex roof)
# plan / elevation frames: x bands in drawing units (mm), named from the frame titles read by hand this run
FRAMES = [("NW_ELEVATION", -400000, -330000), ("SE_ELEVATION", -300000, -250000), ("2F", -250000, -210000),
          ("1F", -210000, -165000), ("GF", -165000, -115000)]
LEVEL_RE = re.compile(r"^[+-]\d+\.\d+$")


def _q(x):
    return round(float(x), ROUND)


def _frame(x):
    for name, a, b in FRAMES:
        if a <= x < b:
            return name
    return None


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise SystemExit("drawing units are not mm")
    msp = doc.modelspace()
    E = {e.dxf.handle: e for e in msp}
    u = 0.001

    def line(h, want_layer=None):
        e = E[h]
        if e.dxftype() != "LINE":
            raise SystemExit(f"{h} is {e.dxftype()}, not a LINE")
        if want_layer and e.dxf.layer != want_layer:
            raise SystemExit(f"{h} on layer {e.dxf.layer}, expected {want_layer}")
        return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)

    def xv(h):
        a, b = line(h, "1")
        if abs(a[0] - b[0]) > 0.5:
            raise SystemExit(f"{h} is not a vertical face line")
        return a[0], (min(a[1], b[1]), max(a[1], b[1]))

    def yh(h, layer="1"):
        a, b = line(h, layer)
        if abs(a[1] - b[1]) > 0.5:
            raise SystemExit(f"{h} is not a horizontal face line")
        return a[1], (min(a[0], b[0]), max(a[0], b[0]))

    out = {"schema": "T726_DRAWN_V1", "units": "m",
           "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55...)",
           "box": {}, "lift": {}, "levels": []}
    boxes = {}
    for fl, hs in BOX.items():
        xw, _ = xv(hs["W"])
        xe, _ = xv(hs["E"])
        yn, _ = yh(hs["N"])
        ys, (s0, s1) = yh(hs["S"])
        boxes[fl] = (min(xw, xe), max(xw, xe), min(yn, ys), max(yn, ys))
        row = {"handles": hs, "width_m": _q((xe - xw) * u), "n_to_s_m": _q((yn - ys) * u),
               "s_line_inside_box_m": _q((min(s1, xe) - max(s0, xw)) * u)}   # < width: an opening / jamb piece in S
        if fl == "GF":
            yso, _ = yh(hs["S_outer"])
            row["s_wall_thickness_m"] = _q((ys - yso) * u)
            row["n_to_s_outer_m"] = _q((yn - yso) * u)
            xo, _ = xv(LIFT_OUTER_E_GF)
            row["lift_outer_width_m"] = _q((xo - xe) * u)       # stair E face (= lift wall west face) to lift east face
        else:
            wx, (w0, w1) = xv(W_ARRIVAL[fl])
            row["w_arrival_piece_handle"] = W_ARRIVAL[fl]
            row["w_face_n_to_arrival_m"] = _q((yn - ys) * u)
        out["box"][fl] = row
    # 2F landing slab edge (open side of the 2F corridor towards the shaft): its distance from the N face
    ye, (e0, e1) = yh(SLAB_EDGE_2F, "5")
    out["box"]["2F"]["slab_edge_handle"] = SLAB_EDGE_2F
    out["box"]["2F"]["slab_edge_u_from_n_m"] = _q((boxes["2F"][3] - ye) * u)
    out["box"]["2F"]["slab_edge_drawn_length_m"] = _q((e1 - e0) * u)
    for fl, hs in LIFT.items():
        xw, _ = xv(hs["W"])
        xe, _ = xv(hs["E"])
        yn, _ = yh(hs["N"])
        ys, _ = yh(hs["S"])
        out["lift"][fl] = {"handles": hs, "inner_w_m": _q((xe - xw) * u), "inner_d_m": _q((yn - ys) * u)}
    # every printed level figure: frame, and on the plan frames whether it lies inside the ST-01 box of that frame
    roof = E[ANNEX_ROOF_BLOCK_1F].dxf.insert
    for e in msp.query("TEXT MTEXT"):
        t = (e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()).strip().replace(" ", "")
        if not LEVEL_RE.match(t):
            continue
        p = e.dxf.insert
        fr = _frame(p[0])
        if fr is None:
            continue
        inside = None
        if fr in boxes:
            x0, x1, y0, y1 = boxes[fr]
            inside = bool(x0 - 250 <= p[0] <= x1 + 250 and y0 - 250 <= p[1] <= y1 + 250)
        near_roof = bool(fr == "1F" and abs(p[0] - roof[0]) < 3000 and abs(p[1] - roof[1]) < 3000)
        out["levels"].append({"handle": e.dxf.handle, "frame": fr, "value": t, "inside_st01_box": inside,
                              "beside_annex_roof_block": near_roof})
    out["levels"].sort(key=lambda r: (r["frame"], r["value"], r["handle"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    got = read(a.dxf)
    txt = json.dumps(got, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(txt, encoding="utf-8")
        print(f"wrote {OUT.name}")
        return 0
    same = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
    print("T726_DRAWN.json", "IDENTICAL" if same else "DIFFERS")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
