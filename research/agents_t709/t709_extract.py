"""T-709 DRAWING READ (research, unwired): own re-measure by HANDLE on the architectural DXF (Drive "Alsenan chalet
project" / P7757_DXF_COMPRESSED.zip, decoded by the wrapper into .work/private only) of
  (d) the face chains of the 9 dry rooms T-701 did not re-measure (merged T-606 / T-612 / T-621 chains, read only):
      perimeter (R-T606-1 outline incl. column notches) and every gap on every straight edge (masonry width, filled by
      window-frame lines or not), so the opening ledger can be checked edge by edge;
  (a) the ST-02 round-stair well (the freelancer's GF 'stair wall' row): the printed well dimensions read by handle
      (west 4000 / south 7020 on the 1F plan; the 150 there is the wall thickness, not a face), the column returns proud
      of the south face inside the well, the 1F wall faces, and the GF wall pieces that
      lie in the same south plane (where the wall is solid on both storeys, i.e. a double-height face).
Writes T709_DRAWN.json: handles, lengths and widths only (no coordinate, no drawing text, no client name).

    .work/venv/bin/python -I research/agents_t709/t709_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t709/t709_extract.py --dxf <P7757.dxf>          (re-read, compare)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("agents_t606", "agents_t612", "agents_t621", "agents_t622"):
    sys.path.insert(0, str(ROOT / "research" / sub))
import t606_extract as X6  # noqa: E402  (storeys, chains; read only)
import t606_rules as R6  # noqa: E402  (outline geometry R-T606-1; read only)
import t612_extract as X12  # noqa: E402  (GF open room chain; read only)
import t621_extract as X21  # noqa: E402  (segments, chains; read only)
import t622_extract as X22  # noqa: E402  (face pieces / gaps / window fill; read only)

OUT = HERE / "T709_DRAWN.json"

# room -> (storey, chain source). The 9 dry rooms of T-701 other than GF-04 / 1F-04 (Checker re-measure there).
ROOMS = {
    "GF-01": ("GF", "T-621 GF-DEWANEYA"),
    "GF-15": ("GF", "T-621 GF-MASTER"),
    "GF-08": ("GF", "T-612 GF-OPEN.full"),
    "1F-01": ("1F", "T-621 1F-WEST-BED"),
    "1F-10": ("1F", "T-621 1F-380x430"),
    "1F-11": ("1F", "T-606 1F-CUR.ours"),
    "1F-13": ("1F", "T-606 1F-LIV.ours"),
    "2F-03": ("2F", "T-606 2F-MAID"),
    "2F-01": ("2F", "T-606 2F-CORR.ours"),
}
# ST-02 well (1F plan): printed dimensions by handle, and the wall-face lines they bound.
WELL_DIMS = {"west": "E3E", "wall_thickness_west": "E56", "south": "D7B"}
WELL_COLUMNS_1F = ["300E", "3008"]   # S-COL.BON on the 1F south wall (proud returns counted inside the zone)
WELL_FACES_1F = {"south": "AEC", "west_piece": "AE7"}
# GF lines in the same south plane: hidden overhead line A8 (no wall below), solid wall face 336, columns 2FD2 / 2FC6.
WELL_ARCS = {"GF": "23E", "1F": "BA1"}
GF_SOUTH = {"overhead": "A8", "solid": "336", "col_w": "2FD2", "col_e": "2FC6"}


def chain_of(src):
    who, key = src.split(" ", 1)
    if who == "T-621":
        return list(X21.OUTLINES[key][1])
    if who == "T-606":
        return [h for h, _ in X6.OUTLINES[key][2]]
    if who == "T-612":
        return [h for h, _ in X12.OUTLINES[key][2]]
    raise SystemExit(f"unknown chain source {src}")


def _verts(geom, chain):
    out = []
    for i in range(len(chain)):
        ta, ga = geom[chain[i - 1]]
        tb, gb = geom[chain[i]]
        if ta == "LINE" and tb == "LINE":
            out.append(R6._line_line(ga, gb))
        elif ta == "LINE":
            out.append(R6._line_circle(ga, gb[0], gb[1]))
        elif tb == "LINE":
            out.append(R6._line_circle(gb, ga[0], ga[1]))
        else:
            out.append(None)
    return out


def q(x):
    return str(R6.q6(x))


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise SystemExit("drawing units are not mm")
    msp = doc.modelspace()
    geom, mids = X21.segs(msp)
    lay = X22._layers(msp)
    st = X6._storeys(msp, mids)
    cols = {k: [] for k in st}
    colpoly = {}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(v[0], v[1]) for v in e.get_points()]
            colpoly[e.dxf.handle] = p
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append(p)
    out = {"schema": "T709_DRAWN_V1", "units": "m",
           "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55...)",
           "rooms": {}, "st02_well": {}}
    for rid, (s, src) in ROOMS.items():
        chain = chain_of(src)
        for h in chain:
            if h not in geom:
                raise SystemExit(f"{rid}: handle {h} not in the drawing")
        res = R6.outline(geom, [(h, "WALL") for h in chain], cols[s])
        verts = _verts(geom, chain)
        edges = []
        for i, h in enumerate(chain):
            lm = next(e["lm"] for e in res["edges"] if e["handle"] == h)
            row = {"handle": h, "type": geom[h][0], "layer": lay.get(h.split("#")[0]), "lm": str(lm), "gaps": []}
            p, qq = verts[i], verts[(i + 1) % len(chain)]
            if geom[h][0] == "LINE" and p is not None and qq is not None and lay.get(h.split("#")[0]) == "1":
                pcs, L = X22._pieces(geom, lay, p, qq)
                for ga, gb in X22._gaps(pcs, L):
                    row["gaps"].append({"width": q((gb - ga) / 1000),
                                        "window_framed": bool(X22._filled(pcs, ga, gb, "W"))})
            edges.append(row)
        out["rooms"][rid] = {"storey": s, "chain_source": src, "chain": chain, "edges": edges,
                             "perimeter": str(res["perimeter"]), "notch_lm": str(res["notch_lm"]),
                             "gap_count": sum(len(e["gaps"]) for e in edges)}
    # ST-02 well: printed dims by handle
    by = {e.dxf.handle: e for e in msp}
    w = {}
    for k, h in WELL_DIMS.items():
        if h is None:
            continue
        e = by.get(h)
        if e is None or e.dxftype() != "DIMENSION":
            raise SystemExit(f"well dim {h} missing")
        w[k] = q(e.get_measurement() / 1000)
    for k, h in WELL_FACES_1F.items():
        e = by[h]
        if e.dxftype() != "LINE" or e.dxf.layer != "1":
            raise SystemExit(f"well face {h} not a layer-1 line")
        w["face_" + k + "_lm"] = q(e.dxf.start.distance(e.dxf.end) / 1000)
    # GF south plane: the stair zone runs from the 1F west well face (x of AEC start) over the printed 7.020
    a = by[WELL_FACES_1F["south"]]
    x_w = min(a.dxf.start[0], a.dxf.end[0])
    y1 = a.dxf.start[1]
    # 1F frame offset from GF: the ST-02 concentric outer opening arc on both plans (T-415: same arcs, same centre)
    ca, cb = by[WELL_ARCS["GF"]], by[WELL_ARCS["1F"]]
    if ca.dxftype() != "ARC" or cb.dxftype() != "ARC" or abs(ca.dxf.radius - cb.dxf.radius) > 0.5:
        raise SystemExit("ST-02 outer arcs do not match")
    dx = cb.dxf.center[0] - ca.dxf.center[0]
    if abs(cb.dxf.center[1] - ca.dxf.center[1]) > 0.5:
        raise SystemExit("ST-02 centres not on one y")
    zone = (x_w, x_w + float(w["south"]) * 1000)
    g = {}
    for k, h in GF_SOUTH.items():
        e = by[h]
        if e.dxftype() == "LINE":
            xs = sorted([e.dxf.start[0] + dx, e.dxf.end[0] + dx])
            yy = e.dxf.start[1]
            g[k] = {"handle": h, "layer": e.dxf.layer, "x": xs, "plane_offset_mm": round(abs(yy - y1), 1)}
        else:
            xs = sorted({v[0] + dx for v in colpoly[h]})
            g[k] = {"handle": h, "layer": e.dxf.layer, "x": [xs[0], xs[-1]]}

    def inside(span):
        lo, hi = max(span[0], zone[0]), min(span[1], zone[1])
        return max(0.0, hi - lo) / 1000

    # column returns proud of the 1F south face inside the well zone (room side = towards the well centre)
    cen_y = cb.dxf.center[1]
    side = 1 if cen_y > y1 else -1
    rets = []
    for h in WELL_COLUMNS_1F:
        p = colpoly[h]
        xs = [v[0] for v in p]
        far = max(v[1] for v in p) if side > 0 else min(v[1] for v in p)
        proud = (far - y1) * side
        if proud <= 1:
            continue
        for x in (min(xs), max(xs)):
            if zone[0] + 1 < x < zone[1] - 1:
                rets.append({"column": h, "proud_m": q(proud / 1000)})
    w["column_returns_in_zone"] = rets
    w["column_returns_lm"] = q(sum(float(r["proud_m"]) for r in rets))
    w["frame_dx_note"] = "GF pieces moved by the storey-frame offset onto the 1F frame (same well centre on both plans)"
    w["gf_overhead_line_in_zone_lm"] = q(inside(g["overhead"]["x"]))
    w["gf_solid_wall_in_zone_lm"] = q(inside(g["solid"]["x"]))
    w["gf_columns_in_zone_lm"] = q(inside(g["col_w"]["x"]) + inside(g["col_e"]["x"]))
    w["gf_pieces"] = {k: {"handle": v["handle"], "layer": v["layer"], "in_zone_lm": q(inside(v["x"])),
                          **({"plane_offset_mm": v["plane_offset_mm"]} if "plane_offset_mm" in v else {})}
                      for k, v in g.items()}
    out["st02_well"] = w
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    d = read(a.dxf)
    txt = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if a.write:
        OUT.write_text(txt, encoding="utf-8")
        print("written", OUT.name)
        return 0
    same = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
    print("REPRODUCED" if same else "DIFFERS")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
