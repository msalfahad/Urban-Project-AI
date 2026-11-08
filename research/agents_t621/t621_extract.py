"""T-621 DRAWING READ (research, unwired): every room and piece behind the 41 rows of the B3 floor tile line
(statement V10 section T-553/floor-tile) re-measured by HANDLE on the architectural DXF (Drive "Alsenan chalet
project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only). Writes T621_DRAWN.json: handles, roles and
lengths / areas only (no coordinate, no drawing text, no client name). The builder t621_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t621/t621_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t621/t621_extract.py --dxf <P7757.dxf>          (re-read, compare)

How each figure is read (R-T621-1 step 1):
  OUTLINE  an ordered chain of drawn edges (R-T606-1 geometry, reused read only): a LINE handle, an ARC handle, or one
           segment of an LWPOLYLINE written 'H#i' (straight -> LINE, bulge -> its circle as T-612 does); every vertex
           is the intersection of two consecutive edges, so a door gap in a wall face is closed on that face. Column
           polygons (closed S-COL.BON) cut a notch where they overlap the room. The chains were found by my own
           polygonization of the layer-1 wall faces round each room label insert (not from the engine), then fixed
           by handle; chains reused from merged T-606 / T-612 are re-measured by this run, not copied.
  GAP      a door / arch strip: width = the gap between the two collinear jamb faces (handle pair), depth = the
           distance between the two wall faces (handle pair); area = width x depth.
  DIM      a printed size: the DIMENSION entities' own measurements (handles), product of two.
  SOLID    a closed S-COL.BON polygon's own area, or the wall between two face lines over a drawn extent.
Storeys are clustered as T-601 / T-606 do (layer-1 LINE midpoints, the storey title insert picks its cluster).
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
import t606_extract as X6  # noqa: E402  (storeys, gap / depth helpers; read only)
import t606_rules as R6  # noqa: E402  (outline geometry R-T606-1; read only)
import t612_extract as X12  # noqa: E402  (bulge arcs, the GF open-room gross chain; read only)
import t612_rules as R12  # noqa: E402  (gross outline with interior solids; read only)
import t621_rules as R  # noqa: E402

OUT = HERE / "T621_DRAWN.json"
W = "WALL"

# outline id -> (storey, chain of handles, note). WALL role throughout (floor area only; R-T606-1 roles kept for lm).
OUTLINES = {
    # GF
    "GF-DEWANEYA": ("GF", ["119", "127", "10E", "139", "124"], "400 x 630 with the R1.10 corner arc (T-606 chain)"),
    "GF-MASTER": ("GF", ["2B5", "27D#0", "27D#1", "2E2", "2E0", "319", "2E7", "2DE"],
                  "room 4.82 x 4.00 to the curved glazing face (27D straight + bulge segment) + the hall to its bath "
                  "(2E0 / 319 / 2E7, door D115 to the open room in 2E1 / 2E2); column 2F85 notch"),
    "GF-DRIVER": ("GF", ["130", "11D", "12F", "113"], "175 x 450"),
    "GF-KITCHEN": ("GF", ["11A", "136", "14F", "135", "111", "A5"], "300 x 270 + 105 x 150, two piers notch"),
    "GF-WASH-REC": ("GF", ["11F", "12B", "118", "12E"], "150 x 210 less the column corner"),
    "GF-WC-REC": ("GF", ["115", "129", "114", "12D"], "W.C. by the reception room"),
    "GF-WC-STAIR": ("GF", ["271", "213", "2AF", "210"], "stair-core W.C. 175 x 135"),
    "GF-WC-CORE-245": ("GF", ["2B4", "327", "31D", "BD"], "core W.C. wedge 245 x 167, column notch"),
    "GF-WC-CORE-289": ("GF", ["31F", "326", "221", "217"], "core W.C. wedge 289 x 167"),
    "GF-BASIN-STAIR": ("GF", ["2B2", "215", "218", "211"], "basin space by the stair (to the reveal face)"),
    "GF-LOBBY-WASH": ("GF", ["31B", "31A", "324", "318", "BE", "D2", "222"],
                      "lobby with two basins: diagonal walls, closed on the step line D2 / 2DB to wall face 222"),
    "GF-MASTER-BATH": ("GF", ["273", "2DD", "2E5", "325", "2DF"], "2.10 x 2.00 less the diagonal-wall corner"),
    # 1F
    "1F-WEST-BED": ("1F", ["C2A", "C1F", "C24", "B40"], "425 x 450, two column notches"),
    "1F-380x430": ("1F", ["AD0", "B08", "AD8", "AFF"], "380 x 430 (T-606 chain)"),
    "1F-DRESSING": ("1F", ["B20", "B03", "AD5", "B00"], "dressing 165 x 180 beyond the arch OP-011"),
    "1F-500x365": ("1F", ["AE6", "AF8", "AE9", "C1E"], "500 x 365, column notch"),
    "1F-EAST-BATH": ("1F", ["B69", "C0C", "C0E", "B1B"], "210 x 225"),
    "1F-BATH-LAUNDRY": ("1F", ["B02", "B1F", "B09", "AD6"], "200 x 180 less the drawn jamb"),
    "1F-WC-LAUNDRY": ("1F", ["AD3", "B0E", "ADA", "B05"], "180 x 147"),
    "1F-WBATH-1": ("1F", ["C1C", "C26", "C22", "C25"], "west bath 245 x 205 (first of two congruent baths)"),
    "1F-WBATH-2": ("1F", ["AE4", "C23", "C27", "B3E"], "west bath 245 x 205 (second)"),
    "1F-LAUNDRY": ("1F", ["ADB", "B07", "ACF", "B0F", "B17", "B06", "B14", "B12"],
                   "L-shaped laundry: 1.85 wide north part beside the W.C., 3.47 x ... south part to the lift box and the "
                   "living door; column 2FF0 notch"),
    # 2F
    "2F-ROOF-WC": ("2F", ["127B", "1296", "1298", "1290"], "300 x 185"),
}
# chains reused from merged tasks, re-measured here: id -> (module, outline key)
REUSED = {
    "2F-MAID": ("T606", "2F-MAID"), "2F-CORR.ours": ("T606", "2F-CORR.ours"),
    "2F-CORR.east_foot": ("T606", "2F-CORR.east_foot"), "1F-CUR.ours": ("T606", "1F-CUR.ours"),
    "1F-CUR.chord": ("T606", "1F-CUR.chord"), "1F-CUR.room_only": ("T606", "1F-CUR.room_only"),
    "1F-CUR.room_only_chord": ("T606", "1F-CUR.room_only_chord"),
    "1F-LIV.floor_printed": ("T606", "1F-LIV.floor_printed"), "1F-LIV.floor_drawn": ("T606", "1F-LIV.floor_drawn"),
    "GF-OPEN.full": ("T612", "GF-OPEN.full"),
}
# pieces bounded by drawn lines (OUTLINE kind)
PIECE_OUTLINES = {
    "GF-BAND": ("GF", ["310", "104", "30F", "337"], "garden band: west end 310, facade face 104, east end 30F, north "
                "on the 1.30 line (337 / 4B4); column 2FD5 notch"),
    "GF-CURB": ("GF", ["310", "4B4", "2FD2#0", "A8"], "curb 0.20 between 4B4 and A8, from 310 to the west face of "
                "column 2FD2"),
    "GF-SOLID-WALL": ("GF", ["336", "2FC6#0", "337", "2FD2#2"], "wall 336 / 337 between the two columns"),
    "GF-STAIR-HALL": ("GF", ["220", "21C", "490", "47E", "47C", "157", "DE", "298"],
                      "hall at +1.00: south face 220 (door OP-010 closed on it), lift-wall face 21C, D1 top riser 490 "
                      "(layer 5), divider faces 47E / 47C / 157 (layer 2 / 5), MS1-L first riser DE (layer 2), west "
                      "face 298: 2.50 x 0.45 + 1.15 x 0.70 + 1.15 x 2.50"),
    "GF-STAIR-LOBBY": ("GF", ["481", "21B", "26F", "47E"],
                       "back-door lobby at +0.30 under the +3.50 half landing: D1 foot riser 481, wall faces 21B / 26F "
                       "(north door 0.90 closed on 26F), divider line 47E prolonged: 1.15 x 1.15"),
    "1F-ARRIVAL-DRAWN": ("1F", ["AC2", "A8D", "AC3", "A8F", "AC0", "B16", "AEB", "C21"],
                         "main-stair arrival +5.50 as drawn: west lane to its riser AC2 (nosing band 0.05), the well "
                         "end AC3 (0.05 into the printed rectangle), east lane on the printed edge AC0 prolonged"),
    "1F-ARRIVAL-RECT": ("1F", ["AC0", "B16", "AEB", "C21"], "the printed 2.50 x 1.95 rectangle by handle"),
}
SOLIDS = {"GF-SOLID-COL-2FD2": "2FD2", "GF-SOLID-COL-2FC6": "2FC6"}
# door / arch strips and lift landing doors: id -> (storey, width jamb pair, depth face pair, note)
GAPS = {
    "GF-OP-010": ("GF", ("20F", "20E"), ("20F", "220"), "stair-hall door D120 (open room | stair room)"),
    "GF-OP-012": ("GF", ("2E1", "2E2"), ("2E1", "2E3"), "door D115 (open room | master bed room hall)"),
    "1F-OP-005": ("1F", ("AFA", "AF9"), ("AFA", "B1D"), "door D215 BEF (living | curved bed room lobby)"),
    "1F-OP-006": ("1F", ("AD8", "AD9"), ("AD9", "AFA"), "door D215 C18 (living | bed room 380 x 430)"),
    "1F-OP-020": ("1F", ("C1F", "C20"), ("C1F", "C21"), "door D115 C31 (living | west bed room)"),
    "1F-D-1F-03": ("1F", ("AE8", "AE9"), ("AE8", "AEA"), "door D115 C32 (living | bed room 500 x 365)"),
    "1F-OP-011": ("1F", ("AD1", "AD0"), ("AD0", "AD4"), "arch 1.00 (bed room 380 x 430 | dressing)"),
    "2F-OP-007": ("2F", ("128E", "128D"), ("128E", "1295"), "door d220 12C2 (maid room | stair lobby)"),
    "GF-LIFT-DOOR": ("GF", ("20D", "20E"), ("20D", "21D"), "lift landing door (width only is used)"),
    "1F-LIFT-DOOR": ("1F", ("AFE", "AFD"), ("AFE", "B1A"), "lift landing door AR1 AC5 (width only is used)"),
    "2F-LIFT-DOOR": ("2F", ("128A", "1289"), ("128A", "129C"), "lift landing door AR1 138C (width only is used)"),
}
# printed sizes: id -> (storey, [DIMENSION handles], note)
DIMS = {
    "1F-ARRIVAL": ("1F", ["D25", "10DF"], "main-stair arrival +5.50, printed 2.50 x 1.95"),
    "2F-ARRIVAL": ("2F", ["138E", "14F1"], "main-stair arrival +9.70, printed 2.50 x 1.95"),
    "GF-BASIN-REVEAL": ("GF", ["70F", "672"], "passage reveal of the basin space, printed 1.10 x 0.20"),
}


def segs(msp):
    """LINE / ARC handles (T-606), bulge segments of LWPOLYLINEs as ARCs (T-612) and straight LWPOLYLINE segments
    as LINEs, each 'H#i'."""
    geom, mids = X6._segs(msp)
    g12, _ = X12._segs(msp)
    geom.update({k: v for k, v in g12.items() if "#" in k})
    for e in msp.query("LWPOLYLINE"):
        pts = [(q[0], q[1], q[4]) for q in e.get_points()]
        n = len(pts) if e.closed else len(pts) - 1
        for i in range(n):
            j = (i + 1) % len(pts)
            if not pts[i][2]:
                geom[f"{e.dxf.handle}#{i}"] = ("LINE", (pts[i][:2], pts[j][:2]))
    return geom, mids


def _on(geom, h, a0, b0):
    g = geom[h][1]
    x = g[0][0] if geom[h][0] == "LINE" else g[0][0]
    return a0 < x < b0


def _outline(oid, s, chain, geom, st, cols):
    a0, b0 = st[s]
    for h in chain:
        if h not in geom:
            raise R.RuleError(f"{oid}: handle {h} not in the drawing")
        if not _on(geom, h, a0, b0):
            raise R.RuleError(f"{oid}: {h} is not on the {s} plan")
    res = R6.outline(geom, [(h, W) for h in chain], [p for _, p in cols[s]])
    return {"storey": s, "kind": "OUTLINE", "source": "DRAWING", "handles": list(chain), "area": str(res["area"]),
            "perimeter": str(res["perimeter"]), "notch_m2": str(res["notch_m2"])}


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise R.RuleError("drawing units are not mm")
    msp = doc.modelspace()
    geom, mids = segs(msp)
    st = X6._storeys(msp, mids)
    cols = {k: [] for k in st}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append((e.dxf.handle, p))
    out = {"schema": "T621_DRAWN_V1", "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
           "units": "m / m2", "rule": R.RULE_ID, "measures": {}}
    m = out["measures"]
    for oid, (s, chain, note) in OUTLINES.items():
        m[oid] = dict(_outline(oid, s, chain, geom, st, cols), note=note)
    for oid, (s, chain, note) in PIECE_OUTLINES.items():
        m[oid] = dict(_outline(oid, s, chain, geom, st, cols), note=note)
    for oid, (src, key) in REUSED.items():
        if src == "T606":
            s, _, chain, note = X6.OUTLINES[key]
            m[oid] = dict(_outline(oid, s, [h for h, _ in chain], geom, st, cols), note=f"T-606 chain: {note}")
            if any(r != W for _, r in chain):   # keep the merged roles (virtual edges) for the record
                m[oid]["roles"] = [r for _, r in chain]
                res = R6.outline(geom, chain, [p for _, p in cols[s]])
                m[oid].update(area=str(res["area"]), perimeter=str(res["perimeter"]), notch_m2=str(res["notch_m2"]))
        else:
            s, _, chain, note = X12.OUTLINES[key]
            res = R12.outline_gross(geom, chain, cols[s])
            m[oid] = {"storey": s, "kind": "OUTLINE", "source": "DRAWING", "handles": [h for h, _ in chain],
                      "roles": [r for _, r in chain], "area": str(res["area"]), "perimeter": str(res["perimeter"]),
                      "notch_m2": "n/a (gross: interior solids kept)", "note": f"T-612 chain: {note}"}
    colmap = {h: p for s in cols for h, p in cols[s]}
    for oid, h in SOLIDS.items():
        from shapely.geometry import Polygon
        m[oid] = {"storey": "GF", "kind": "SOLID", "source": "DRAWING", "handles": [h],
                  "area": str(R6.q6(Polygon(colmap[h]).area * 1e-6)), "note": "closed S-COL.BON polygon"}
    for oid, (s, (wa, wb), (da, db), note) in GAPS.items():
        w, d = X6._gap(geom, wa, wb) / 1000, X6._depth(geom, da, db) / 1000
        m[oid] = {"storey": s, "kind": "GAP", "source": "DRAWING", "handles": [wa, wb, da, db],
                  "width": str(R6.q6(w)), "depth": str(R6.q6(d)), "area": str(R6.q6(w * d)), "note": note}
    db_ = doc.entitydb
    for oid, (s, hs, note) in DIMS.items():
        vals = [R6.q6(db_[h].get_measurement() / 1000) for h in hs]
        a = vals[0]
        for v in vals[1:]:
            a = R6.q6(a * v)
        m[oid] = {"storey": s, "kind": "DIM", "source": "DRAWING", "handles": hs, "values": [str(v) for v in vals],
                  "area": str(a), "note": note}
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
    for k, v in d["measures"].items():
        print(f"{k:24s} {v['kind']:8s} {v['area']:>12s} {v.get('width', '')} {v.get('depth', '')} "
              f"{v.get('values', '')} {' '.join(v['handles'])}")


if __name__ == "__main__":
    main()
