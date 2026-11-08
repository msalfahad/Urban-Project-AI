"""T-622 DRAWING READ (research, unwired): the tiled wall faces, open sides and openings of the 12 valued wet-room wall
tile rooms behind statement V10 section T-547/wall-tile, re-measured by HANDLE on the architectural DXF (Drive
"Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only). Writes T622_DRAWN.json:
handles, lengths and widths only (no coordinate, no drawing text, no client name). The builder t622_alsenan.py reads
only that JSON.

    .work/venv/bin/python -I research/agents_t622/t622_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t622/t622_extract.py --dxf <P7757.dxf>          (re-read, compare)

How each figure is read (R-T622-1 step 1, see t622_rules.py):
  CHAIN    the room's inner wall faces as an ordered chain of drawn edges (R-T606-1 geometry, read only): vertices at the
           intersections of consecutive edges, so a door / window gap is closed on its own face; column polygons
           (closed S-COL.BON) cut notches and their return faces count as face. The 11 bath / W.C. / laundry chains are
           the merged T-621 chains (R-T621-1), re-measured here; the pantry chain is new (this run).
  OPEN     an open side is a NAMED drawn line that is not a wall face (threshold / step / counter-front line): its own
           length, checked collinear with the chain edge it lies on and ending on the chain's vertex.
  OPENING  each declared opening is the gap between the layer-1 wall-face pieces on its own chain edge (masonry width,
           frame included); a WINDOW gap must be filled by window-frame lines (layer W) on the face line, a DOOR gap
           must not; any undeclared gap on a tiled edge is refused (an opening is never silently dropped).
  DIM      a printed DIMENSION (W18 sill / height on the NW elevation chain): the entity's own measurement.
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
import t606_extract as X6  # noqa: E402  (storeys; read only)
import t606_rules as R6  # noqa: E402  (outline geometry R-T606-1; read only)
import t621_extract as X21  # noqa: E402  (segments incl. LWPOLYLINE pieces, merged chains; read only)
import t622_rules as R  # noqa: E402

OUT = HERE / "T622_DRAWN.json"
W, OPEN = "WALL", "ZONE_EDGE"
FACE_TOL_MM = 2.0     # a drawn piece lies on the face line when both ends are within 2 mm of it
GAP_MIN_MM = 5.0      # gaps under 5 mm are drafting joints, not openings

# room -> (storey, chain [(handle, role)], open side handles, openings [(id, kind, edge handle)], note)
# chains: T-621 OUTLINES (merged e8709e09) except GF-07 (new). GF-14: the T-621 chain closes the open side on the D2
# line prolonged; the open part is the drawn threshold line 2DB (layer 2), measured on its own.
ROOMS = {
    "GF-12": ("GF", "GF-WC-CORE-289", [], [("D-GF-11", "door", "31F")], "core W.C. wedge 289 x 167"),
    "GF-13": ("GF", "GF-WC-CORE-245", [], [("D-GF-12", "door", "31D"), ("W06", "window", "2B4")],
              "core W.C. wedge 245 x 167, column notch"),
    "GF-14": ("GF", "GF-LOBBY-WASH", [("2DB", "D2")], [("D-GF-11", "door", "31A"), ("D-GF-12", "door", "31A")],
              "wash lobby, 2 basins; open to the stair hall over the threshold line 2DB"),
    "GF-16": ("GF", "GF-MASTER-BATH", [], [("D-GF-14", "door", "2E5"), ("W07", "window", "273")], "master bath"),
    "1F-02": ("1F", "1F-WBATH-2", [], [("D-1F-04", "door", "C27"), ("W20", "window", "AE4")],
              "west bath upper 245 x 205 (T-621 second congruent bath)"),
    "1F-03": ("1F", "1F-WBATH-1", [], [("D-1F-01", "door", "C1C"), ("W19", "window", "C25")],
              "west bath lower 245 x 205 (T-621 first congruent bath)"),
    "1F-07": ("1F", "1F-LAUNDRY", [], [("D-1F-06", "door", "ACF"), ("D-1F-05", "door", "B17"),
                                       ("W21", "window", "ADB")], "L-shaped laundry, column 2FF0 notch"),
    "1F-08": ("1F", "1F-WC-LAUNDRY", [], [("D-1F-06", "door", "AD3"), ("W22", "window", "ADA")], "W.C. 147 x 180"),
    "1F-09": ("1F", "1F-BATH-LAUNDRY", [], [("D-1F-07", "door", "B02"), ("W23", "window", "B1F")],
              "bath by the laundry 200 x 180 less the drawn jamb"),
    "1F-12": ("1F", "1F-EAST-BATH", [], [("D-1F-10", "door", "C0E"), ("W18", "window", "B69")], "east bath 210 x 225"),
    "2F-02": ("2F", "2F-ROOF-WC", [], [("D-2F-03", "door", "1290"), ("W28", "window", "127B")],
              "roof-floor W.C. 300 x 185"),
    "GF-07": ("GF", None, [("B3", "B3")], [("D-GF-06", "door", "158"), ("W09", "window", "AE"), ("W10", "window", "AE")],
              "open pantry (Q-37 A wet): box 3.00 x 4.50 (DIMENSIONs 5D5 / 5E1), west face AE with W09 / W10, south "
              "A6, north 158 with the door, east side open on the counter-front line B3; column 2FAE notch"),
}
# the pantry chain (new this run): west face AE, south face A6, east open edge B3 (counter-front line, layer 5), north
# face 158; the 2FAE column front and its return are cut by R-T606-1's column notch.
PANTRY_CHAIN = [("AE", W), ("A6", W), ("B3", OPEN), ("158", W)]
PANTRY_DIMS = ["5D5", "5E1"]
# W18 (1F east bath): NW elevation chain, sill above the 1F floor and window height (printed 84 / 216)
W18_DIMS = {"sill": "2EEC", "height": "2EFA"}


def _layers(msp):
    return {e.dxf.handle: e.dxf.layer for e in msp.query("LINE ARC LWPOLYLINE")}


def _verts(geom, chain):
    n = len(chain)
    return [R6._line_line(geom[chain[i - 1][0]][1], geom[chain[i][0]][1]) for i in range(n)]


def _on_line(p, u, a, b):
    d1 = abs((a[0] - p[0]) * u[1] - (a[1] - p[1]) * u[0])
    d2 = abs((b[0] - p[0]) * u[1] - (b[1] - p[1]) * u[0])
    return d1 < FACE_TOL_MM and d2 < FACE_TOL_MM


def _pieces(geom, lay, p, q):
    """drawn LINE pieces on the face line p -> q, clipped to the edge: [(t0, t1, handle, layer)] in mm."""
    L = math.dist(p, q)
    u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
    out = []
    for h, (t, g) in geom.items():
        if t != "LINE" or "#" in h:
            continue
        a, b = g
        if not _on_line(p, u, a, b):
            continue
        ta = (a[0] - p[0]) * u[0] + (a[1] - p[1]) * u[1]
        tb = (b[0] - p[0]) * u[0] + (b[1] - p[1]) * u[1]
        lo, hi = sorted((ta, tb))
        if hi > GAP_MIN_MM and lo < L - GAP_MIN_MM:
            out.append((max(lo, 0.0), min(hi, L), h, lay.get(h)))
    return sorted(out), L


def _gaps(pieces, L, layer="1"):
    gaps, cur = [], 0.0
    for lo, hi, _, ly in pieces:
        if ly != layer:
            continue
        if lo > cur + GAP_MIN_MM:
            gaps.append((cur, lo))
        cur = max(cur, hi)
    if cur < L - GAP_MIN_MM:
        gaps.append((cur, L))
    return gaps


def _filled(pieces, a, b, layer):
    cur = a
    for lo, hi, _, ly in pieces:
        if ly == layer and lo <= cur + GAP_MIN_MM and hi > cur:
            cur = max(cur, hi)
    return cur >= b - GAP_MIN_MM


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise R.RuleError("drawing units are not mm")
    msp = doc.modelspace()
    geom, mids = X21.segs(msp)
    lay = _layers(msp)
    st = X6._storeys(msp, mids)
    cols = {k: [] for k in st}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append((e.dxf.handle, p))
    out = {"schema": "T622_DRAWN_V1", "rule": R.RULE_ID,
           "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55...)",
           "units": "m", "rooms": {}, "dims": {}}
    for rid, (s, key, opens, ops, note) in ROOMS.items():
        if key is None:
            chain = PANTRY_CHAIN
            src = "new chain (T-622)"
        else:
            chain = [(h, W) for h in X21.OUTLINES[key][1]]
            src = f"T-621 chain {key} (merged e8709e09), re-measured"
        a0, b0 = st[s]
        for h, _ in chain:
            if h not in geom:
                raise R.RuleError(f"{rid}: handle {h} not in the drawing")
            if not a0 < geom[h][1][0][0] < b0:
                raise R.RuleError(f"{rid}: {h} is not on the {s} plan")
        res = R6.outline(geom, chain, [p for _, p in cols[s]])
        verts = _verts(geom, chain)
        edges = []
        for i, (h, role) in enumerate(chain):
            p, q = verts[i], verts[(i + 1) % len(chain)]
            pcs, L = _pieces(geom, lay, p, q)
            edges.append({"handle": h, "role": role, "lm": str(R6.q6(L / 1000)), "_p": p, "_q": q, "_pcs": pcs})
        # open sides: own drawn line, collinear with its edge, sharing the edge's end vertex
        open_out = []
        for oh, eh in opens:
            e = next(x for x in edges if x["handle"] == eh)
            (a, b) = geom[oh][1]
            L = math.dist(e["_p"], e["_q"])
            u = ((e["_q"][0] - e["_p"][0]) / L, (e["_q"][1] - e["_p"][1]) / L)
            if not _on_line(e["_p"], u, a, b):
                raise R.RuleError(f"{rid}: open side {oh} is not on its edge {eh}")
            if min(math.dist(x, v) for x in (a, b) for v in (e["_p"], e["_q"])) > FACE_TOL_MM:
                raise R.RuleError(f"{rid}: open side {oh} does not end on a chain vertex")
            ol = math.dist(a, b) if eh != oh else L
            open_out.append({"handle": oh, "on_edge": eh, "layer": lay.get(oh), "lm": str(R6.q6(ol / 1000))})
        # openings: layer-1 gaps on each tiled edge, matched to the declaration
        op_out = []
        decl = {}
        for oid, kind, eh in ops:
            decl.setdefault(eh, []).append((oid, kind))
        for e in edges:
            if e["role"] != W:
                continue
            gaps = _gaps(e["_pcs"], math.dist(e["_p"], e["_q"]))
            # a gap that IS a named open side is not an opening
            ol = [o for o in open_out if o["on_edge"] == e["handle"]]
            if ol:
                gaps = [g for g in gaps if not any(abs((g[1] - g[0]) / 1000 - float(o["lm"])) < 0.002 for o in ol)]
            want = decl.get(e["handle"], [])
            if len(gaps) != len(want):
                raise R.RuleError(f"{rid}: edge {e['handle']}: {len(gaps)} gap(s) drawn, {len(want)} declared")
            for (oid, kind), (ga, gb) in zip(want, gaps):
                win = _filled(e["_pcs"], ga, gb, "W")
                if (kind == "window") != win:
                    raise R.RuleError(f"{rid}: {oid} declared {kind} but the gap is {'window-framed' if win else 'not window-framed'}")
                jambs = [h for lo, hi, h, ly in e["_pcs"] if ly == "1" and (abs(hi - ga) < 1 or abs(lo - gb) < 1)]
                op_out.append({"id": oid, "kind": kind, "edge": e["handle"], "jambs": jambs,
                               "width": str(R6.q6((gb - ga) / 1000))})
        out["rooms"][rid] = {
            "storey": s, "chain": [h for h, _ in chain], "roles": [r for _, r in chain], "chain_source": src,
            "edges": [{"handle": x["handle"], "role": x["role"], "lm": x["lm"]} for x in edges],
            "perimeter": str(res["perimeter"]), "notch_lm": str(res["notch_lm"]), "wall_lm": str(res["wall_lm"]),
            "open": open_out, "openings": op_out, "note": note}
    db = doc.entitydb
    out["dims"]["GF-07.box"] = {"handles": PANTRY_DIMS, "values": [str(R6.q6(db[h].get_measurement() / 1000)) for h in PANTRY_DIMS]}
    out["dims"]["W18"] = {"handles": [W18_DIMS["sill"], W18_DIMS["height"]],
                          "values": [str(R6.q6(db[W18_DIMS[k]].get_measurement() / 1000)) for k in ("sill", "height")],
                          "note": "NW elevation chain: sill above the 1F floor, window height (printed 84 / 216)"}
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
        print(f"{k:6s} per {v['perimeter']:>9s} wall {v['wall_lm']:>9s} open {[o['lm'] for o in v['open']]} "
              f"ops {[(o['id'], o['width']) for o in v['openings']]}")
    print(d["dims"])


if __name__ == "__main__":
    main()
