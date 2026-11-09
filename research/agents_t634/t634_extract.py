"""T-634 DRAWING READ (research, unwired): the dry-room wall faces behind the 31 UNKNOWN rows of statement V11 sections
T-552/plaster-internal (15) and T-561/paint-internal (16), re-measured by HANDLE on the architectural DXF (Drive
"Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only). Writes T634_DRAWN.json: handles,
lengths, widths and wall thicknesses only (no coordinate, no drawing text, no client name). The builder t634_alsenan.py
reads only that JSON.

    .work/venv/bin/python -I research/agents_t634/t634_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t634/t634_extract.py --dxf <P7757.dxf>          (re-read, compare)

How each figure is read (R-T634-1 step 1, see t634_rules.py):
  CHAIN    the room's inner wall faces as an ordered chain of drawn edges (R-T606-1 geometry, read only; the T-606 /
           T-621 merged chains): vertices at the intersections of consecutive edges (LINE-LINE or LINE-ARC), column
           polygons (closed S-COL.BON) cut notches whose return faces count as face. An ARC edge (the GF master bed
           room's curved glazing face 27D) is measured at its true length.
  OPENING  each declared opening is the gap between the layer-1 wall-face pieces on its own chain edge (masonry width);
           a WINDOW gap must be filled by window-frame lines (layer W), a DOOR / ARCH gap must not; any undeclared gap
           is refused. A whole edge on layer W (the curved glazing) is a glazing face: declared, its width = its length.
  JAMB     the wall thickness at a door = the length of the layer-1 jamb cap drawn perpendicular to the face at each end
           of the gap (both ends must agree within 2 mm; otherwise refused).
  SHAFT    the GF stair-hall / lobby piece outlines (T-621 PIECE_OUTLINES, merged) re-measured: evidence for the shaft
           residual row (which drawn faces lie inside the T-173 box).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t606"))
sys.path.insert(0, str(ROOT / "research" / "agents_t612"))
sys.path.insert(0, str(ROOT / "research" / "agents_t621"))
sys.path.insert(0, str(ROOT / "research" / "agents_t622"))
import t606_extract as X6  # noqa: E402  (storeys, T-606 chains; read only)
import t606_rules as R6  # noqa: E402  (outline geometry R-T606-1; read only)
import t621_extract as X21  # noqa: E402  (segments incl. LWPOLYLINE pieces, merged chains; read only)
import t622_extract as X22  # noqa: E402  (face pieces / gaps / window fill; read only)
import t634_rules as R  # noqa: E402

OUT = HERE / "T634_DRAWN.json"
TOL_MM = 2.0

# room -> (storey, chain source, chain handles, openings [(id, kind, edge handle)], note). Chains: T-621 OUTLINES
# (merged e8709e09) or T-606 OUTLINES (merged); the handles are re-measured here, never copied.
ROOMS = {
    "GF-15": ("GF", "T-621 GF-MASTER", None,
              [("W03", "glazing", "27D#1"), ("D-GF-13", "door", "2E2"), ("D-GF-14", "door", "2E7")],
              "GF master bed room 4.82 x 4.00 to the curved glazing face + the hall to its bath; column 2F85 notch"),
    "1F-01": ("1F", "T-621 1F-WEST-BED", None,
              [("D-1F-01", "door", "C2A"), ("D-1F-02", "door", "C1F"), ("W14", "window", "B40")],
              "1F master bed room west 4.25 x 4.50, two column notches"),
    "1F-04": ("1F", "T-621 1F-500x365", None,
              [("W24", "window", "AE6"), ("D-1F-03", "door", "AE9"), ("D-1F-04", "door", "C1E")],
              "1F master bed room 5.00 x 3.65, column notch"),
    "2F-03": ("2F", "T-606 2F-MAID", None,
              [("W29", "window", "1279"), ("D-2F-03", "door", "128B"), ("D-2F-02", "door", "128B")],
              "2F room 3.00 x 6.45"),
    "GF-02": ("GF", "T-621 GF-WASH-REC", None,
              [("A-GF-01", "arch", "12B"), ("D-GF-02", "door", "118")],
              "GF annex wash by the reception room 1.50 x 2.10 (WET space, Q-06 A)"),
}
SHAFT_PIECES = ["GF-STAIR-HALL", "GF-STAIR-LOBBY"]
# the other 17 valued door returns (FIN.PLASTER OPENING / REVEAL lines): door id -> (chain source, edge handle, gap
# index on that edge in face order). The door's host face is the merged chain of one of the rooms it opens into
# (T-175 SIDE_A / SIDE_B); width and jamb thickness re-read here.
DOORS = {
    "D-GF-03": ("T-621 GF-DRIVER", "11D", 0), "D-GF-04": ("T-621 GF-DRIVER", "130", 0),
    "D-GF-05": ("T-621 GF-KITCHEN", "A5", 0), "D-GF-10": ("T-621 GF-WC-STAIR", "2AF", 0),
    "D-GF-11": ("T-621 GF-WC-CORE-289", "31F", 0), "D-GF-12": ("T-621 GF-WC-CORE-245", "31D", 0),
    "D-GF-06": ("T-622 PANTRY", "158", 0), "D-GF-07": ("T-612 GF-OPEN.full", "AB", 0),
    "D-GF-08": ("PIECE GF-STAIR-HALL", "220", 0), "D-GF-09": ("PIECE GF-STAIR-LOBBY", "26F", 0),
    "D-1F-05": ("T-621 1F-LAUNDRY", "B17", 0), "D-1F-06": ("T-621 1F-WC-LAUNDRY", "AD3", 0),
    "D-1F-07": ("T-621 1F-BATH-LAUNDRY", "B02", 0), "D-1F-08": ("T-621 1F-380x430", "AD8", 0),
    "D-1F-09": ("T-606 1F-CUR.ours", "B1D", 0), "D-1F-10": ("T-621 1F-EAST-BATH", "C0E", 0),
    "D-2F-01": ("T-606 2F-CORR.ours", "1283", 0),
}


def chain_of(src):
    who, key = src.split(" ", 1)
    if who == "T-621":
        return list(X21.OUTLINES[key][1])
    if who == "T-606":
        return [h for h, _ in X6.OUTLINES[key][2]]
    if who == "T-612":
        import t612_extract as X12
        return [h for h, _ in X12.OUTLINES[key][2]]
    if who == "T-622" and key == "PANTRY":
        return [h for h, _ in X22.PANTRY_CHAIN]
    if who == "PIECE":
        return list(X21.PIECE_OUTLINES[key][1])
    raise R.RuleError(f"unknown chain source {src}")


def _verts(geom, chain):
    out = []
    n = len(chain)
    for i in range(n):
        ta, ga = geom[chain[i - 1]]
        tb, gb = geom[chain[i]]
        if ta == "LINE" and tb == "LINE":
            out.append(R6._line_line(ga, gb))
        elif ta == "LINE":
            out.append(R6._line_circle(ga, gb[0], gb[1]))
        elif tb == "LINE":
            out.append(R6._line_circle(gb, ga[0], ga[1]))
        else:
            raise R.RuleError("two consecutive arc edges")
    return out


def _jamb(geom, lay, pt, u):
    """the wall thickness at a gap end pt: the nearest layer-1 LINE parallel to the face (the other face of the same
    wall) that also ENDS at the same station along the face (2 mm), 50 .. 400 mm away: [(offset mm, handle)]. The
    drawing draws no jamb cap line (the door leaf is a block); the two face pieces ending at one station bound the
    jamb, so their offset is the masonry thickness."""
    best = []
    for h, (t, g) in geom.items():
        if t != "LINE" or "#" in h or lay.get(h) != "1":
            continue
        a, b = g
        L = math.dist(a, b)
        if L < 10:
            continue
        v = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        if abs(v[0] * u[1] - v[1] * u[0]) > 0.01:
            continue
        for x in (a, b):
            along = (x[0] - pt[0]) * u[0] + (x[1] - pt[1]) * u[1]
            off = abs((x[0] - pt[0]) * u[1] - (x[1] - pt[1]) * u[0])
            if abs(along) < TOL_MM and 50 < off < 400:
                best.append((off, h))
    return best


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise R.RuleError("drawing units are not mm")
    msp = doc.modelspace()
    geom, mids = X21.segs(msp)
    lay = X22._layers(msp)
    st = X6._storeys(msp, mids)
    cols = {k: [] for k in st}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append((e.dxf.handle, p))
    out = {"schema": "T634_DRAWN_V1", "rule": R.RULE_ID,
           "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55...)",
           "units": "m", "rooms": {}, "shaft_pieces": {}}
    for rid, (s, src, _, ops, note) in ROOMS.items():
        chain = chain_of(src)
        a0, b0 = st[s]
        for h in chain:
            if h not in geom:
                raise R.RuleError(f"{rid}: handle {h} not in the drawing")
        res = R6.outline(geom, [(h, "WALL") for h in chain], [p for _, p in cols[s]])
        verts = _verts(geom, chain)
        decl = {}
        for oid, kind, eh in ops:
            decl.setdefault(eh, []).append((oid, kind))
        op_out, edges = [], []
        for i, h in enumerate(chain):
            p, q = verts[i], verts[(i + 1) % len(chain)]
            lm = next(e["lm"] for e in res["edges"] if e["handle"] == h)
            edges.append({"handle": h, "type": geom[h][0], "layer": lay.get(h.split("#")[0]), "lm": str(lm)})
            want = decl.get(h, [])
            if geom[h][0] != "LINE":
                if lay.get(h.split("#")[0]) != "W":
                    raise R.RuleError(f"{rid}: arc edge {h} is not a glazing face")
                if [k for _, k in want] != ["glazing"]:
                    raise R.RuleError(f"{rid}: glazing face {h} not declared")
                op_out.append({"id": want[0][0], "kind": "glazing", "edge": h, "width": str(lm), "jambs_t": []})
                continue
            if lay.get(h.split("#")[0]) == "W":
                # a straight piece of the same glazing face (27D#0): glazing over its whole length
                op_out.append({"id": None, "kind": "glazing_piece", "edge": h, "width": str(lm), "jambs_t": []})
                continue
            pcs, L = X22._pieces(geom, lay, p, q)
            gaps = X22._gaps(pcs, L)
            if len(gaps) != len(want):
                raise R.RuleError(f"{rid}: edge {h}: {len(gaps)} gap(s) drawn, {len(want)} declared")
            u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
            for (oid, kind), (ga, gb) in zip(want, gaps):
                win = X22._filled(pcs, ga, gb, "W")
                if (kind == "window") != win:
                    raise R.RuleError(f"{rid}: {oid} declared {kind} but the gap is "
                                      f"{'window-framed' if win else 'not window-framed'}")
                ts = []
                if kind in ("door", "arch"):
                    for t in (ga, gb):
                        pt = (p[0] + u[0] * t, p[1] + u[1] * t)
                        j = _jamb(geom, lay, pt, u)
                        if j:
                            ts.append(min(j))
                    if len(ts) == 2 and abs(ts[0][0] - ts[1][0]) > TOL_MM:
                        raise R.RuleError(f"{rid}: {oid} jamb caps disagree {ts[0][0]:.1f} / {ts[1][0]:.1f} mm")
                op_out.append({"id": oid, "kind": kind, "edge": h, "width": str(R6.q6((gb - ga) / 1000)),
                               "jambs_t": [{"handle": hh, "t": str(R6.q6(Lj / 1000))} for Lj, hh in ts]})
        # the glazing pieces belong to the declared glazing opening on the same face
        gl = [o for o in op_out if o["kind"] == "glazing"]
        for o in [o for o in op_out if o["kind"] == "glazing_piece"]:
            if not gl:
                raise R.RuleError(f"{rid}: glazing piece {o['edge']} with no declared glazing face")
            gl[0]["width"] = str(R6.q6(float(gl[0]["width"]) + float(o["width"])))
            gl[0].setdefault("pieces", []).append(o["edge"])
        op_out = [o for o in op_out if o["kind"] != "glazing_piece"]
        out["rooms"][rid] = {"storey": s, "chain_source": src, "chain": chain, "edges": edges,
                             "perimeter": str(res["perimeter"]), "notch_lm": str(res["notch_lm"]),
                             "openings": op_out, "note": note}
    out["doors"] = {}
    for oid, (src, eh, k) in DOORS.items():
        chain = chain_of(src)
        verts = _verts(geom, chain)
        i = chain.index(eh)
        p, q = verts[i], verts[(i + 1) % len(chain)]
        pcs, L = X22._pieces(geom, lay, p, q)
        gaps = X22._gaps(pcs, L)
        if k >= len(gaps):
            raise R.RuleError(f"{oid}: no gap {k} on {eh}")
        ga, gb = gaps[k]
        if X22._filled(pcs, ga, gb, "W"):
            raise R.RuleError(f"{oid}: the gap on {eh} is window-framed, not a door")
        u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
        ts = []
        for t in (ga, gb):
            j = _jamb(geom, lay, (p[0] + u[0] * t, p[1] + u[1] * t), u)
            if j:
                ts.append(min(j))
        if not ts:
            raise R.RuleError(f"{oid}: no jamb read")
        if len(ts) == 2 and abs(ts[0][0] - ts[1][0]) > TOL_MM:
            raise R.RuleError(f"{oid}: jamb faces disagree")
        out["doors"][oid] = {"chain_source": src, "edge": eh, "width": str(R6.q6((gb - ga) / 1000)),
                             "jambs_t": [{"handle": hh, "t": str(R6.q6(Lj / 1000))} for Lj, hh in ts]}
    for key in SHAFT_PIECES:
        s, chain, note = X21.PIECE_OUTLINES[key]
        res = R6.outline(geom, [(h, "WALL") for h in chain], [p for _, p in cols[s]])
        out["shaft_pieces"][key] = {"storey": s, "chain": chain,
                                    "edges": [{"handle": e["handle"], "layer": lay.get(e["handle"]),
                                               "lm": str(e["lm"])} for e in res["edges"]],
                                    "perimeter": str(res["perimeter"]),
                                    "wall_layer_lm": str(R6.q6(sum(float(e["lm"]) for e in res["edges"]
                                                                   if lay.get(e["handle"]) == "1")))}
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
    else:
        print("re-read", "identical" if OUT.exists() and OUT.read_text(encoding="utf-8") == txt else "DIFFERS")
    for k, v in d["rooms"].items():
        print(f"{k:6s} per {v['perimeter']:>10s} ops {[(o['id'], o['width'], [j['t'] for j in o['jambs_t']]) for o in v['openings']]}")
    for k, v in d["doors"].items():
        print(k, v["width"], [j["t"] for j in v["jambs_t"]])
    for k, v in d["shaft_pieces"].items():
        print(k, v["perimeter"], v["wall_layer_lm"])


if __name__ == "__main__":
    main()
