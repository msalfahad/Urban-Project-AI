"""T-606 DRAWING READ (research, unwired): room outlines re-measured by HANDLE chain (R-T606-1 step 1) on the
architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only), for
the four rooms that hold the T-574 UNRESOLVED 9.693234 lm and six further rooms (independent re-measures of the
engine's gross), plus the alternative drawn readings of each room and the drawn add-on pieces (door reveal returns and
strips) used to test his rows. Writes T606_DRAWN.json: handles, roles and lengths / areas only (no coordinate, no
drawing text, no client name). The builder t606_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t606/t606_extract.py --dxf <P7757.dxf> --write
    .work/venv/bin/python -I research/agents_t606/t606_extract.py --dxf <P7757.dxf>          (re-read, compare)

Columns: every closed S-COL.BON polyline of the chain's storey (storeys clustered as T-601 does: layer-1 LINE midpoints,
a jump > 8 m starts a new plan, the storey title insert picks its cluster); a column cuts the outline only where it
overlaps the room polygon (a notch), flush columns change nothing.
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
import t606_rules as R  # noqa: E402

OUT = HERE / "T606_DRAWN.json"
TITLES = {"GF": "GF", "FF": "1F", "SF": "2F"}
W, V, LE, Zn, CH = "WALL", "VOID_EDGE", "LANDING_EDGE", "ZONE_EDGE", "CHORD"

# outline id -> (storey, engine line or None, chain [(handle, role)], note)
OUTLINES = {
    # ---- the four T-574 UNRESOLVED groups: ours (engine-equivalent) and the alternative drawn readings
    "2F-CORR.ours": ("2F", "L-9ff582c9 + L-dff4f49f + slab edge", [("1283", W), ("1294", W), ("128A", W), ("129A", W),
                     ("138B", LE), ("12B7", W)], "lobby + arrival, landing edge at the printed 1.95 (T-443)"),
    "2F-CORR.east_foot": ("2F", None, [("1283", W), ("1294", W), ("128A", W), ("129A", W), ("1385", LE), ("1358", LE),
                          ("138B", LE), ("12B7", W)], "east flight's first line 0.30 beyond the printed landing"),
    "1F-LIV.ours": ("1F", "L-ba3599ec", [("AEC", W), ("B68", W), ("AF9", W), ("B10", W), ("AFE", W), ("B16", W),
                    ("ADE", W), ("C21", W), ("AEB", W), ("AF7", W)],
                    "walls round living + corridor + connector + the whole dog-leg well + the void zone walls"),
    "1F-LIV.well_cut": ("1F", None, [("AEC", W), ("B68", W), ("AF9", W), ("B10", W), ("AFE", W), ("B16", W),
                        ("ABE", LE), ("A8F", LE), ("AC0", LE), ("C21", W), ("AEB", W), ("AF7", W)],
                        "ours with the dog-leg well cut at the drawn landing edge; void zone walls kept"),
    "1F-LIV.floor_printed": ("1F", None, [("AEC", W), ("B68", W), ("AF9", W), ("B10", W), ("AFE", W), ("B16", W),
                             ("AC0", LE), ("C21", W), ("AEB", W), ("AF7", W), ("B74", V), ("B75", V), ("D24", V),
                             ("AF5", V)], "floor at +5.50 only: printed 1.95 landing edge; void / stair-box edges"),
    "1F-LIV.floor_drawn": ("1F", None, [("AEC", W), ("B68", W), ("AF9", W), ("B10", W), ("AFE", W), ("B16", W),
                           ("ABE", LE), ("A8F", LE), ("AC0", LE), ("C21", W), ("AEB", W), ("AF7", W), ("B74", V),
                           ("B75", V), ("D24", V), ("AF5", V)],
                           "floor at +5.50 only: east flight foot 0.35 beyond the printed landing (T-113 S3)"),
    "1F-CUR.ours": ("1F", "L-309f118f", [("B1D", W), ("C0F", W), ("C0A", W), ("BD2", W), ("B6B", W), ("ACE", W),
                    ("B0D", W), ("C09", W), ("C15", W), ("C0B", W), ("B0B", W)],
                    "bed room with its curved face + passage returns + lobby (one cell)"),
    "1F-CUR.chord": ("1F", None, [("B1D", W), ("C0F", W), ("C0A", W), ("B6A", CH), ("ACE", W), ("B0D", W), ("C09", W),
                     ("C15", W), ("C0B", W), ("B0B", W)], "the curved face read as the straight inner wall line"),
    "1F-CUR.room_only": ("1F", None, [("C09", Zn), ("BD2", W), ("B6B", W), ("ACE", W), ("B0D", W)],
                         "bed room alone, closed across the 1.30 passage on the bed room face"),
    "1F-CUR.room_only_chord": ("1F", None, [("C09", Zn), ("B6A", CH), ("ACE", W), ("B0D", W)],
                               "bed room alone, straight east line"),
    # ---- six further independent re-measures (engine gross from T-460 V3.0.51)
    "2F-MAID": ("2F", "L-d057b5b0", [("1284", W), ("1292", W), ("1279", W), ("128B", W)], "300 x 645"),
    "1F-380x430": ("1F", "L-a8aea284", [("AD8", W), ("AFF", W), ("AD0", W), ("B08", W)], "380 x 430"),
    "1F-500x365": ("1F", "L-2f58111e", [("AE7", W), ("AF8", W), ("AE9", W), ("C1E", W)], "500 x 365 + column notch"),
    "GF-DRIVER": ("GF", "L-bb0ea965", [("113", W), ("131", W), ("11E", W), ("12F", W)], "175 x 450"),
    "GF-DEWANEYA": ("GF", "L-d3241491", [("119", W), ("127", W), ("10E", W), ("139", W), ("124", W)],
                    "400 x 630 with the R1.10 corner"),
}
# drawn add-on pieces for testing his rows: id -> (storey, width ends (handle, handle), depth faces (handle, handle))
# a door reveal piece adds 2 x depth to a gross perimeter that walks into the opening and width x depth to its area
ADDONS = {
    "2F-CORR": {"lift door 1.00 reveals": ("2F", ("128A", "1289"), ("128A", "129C")),
                "maid door reveals": ("2F", ("1294", "1295"), ("1294", "128D")),
                "roof door reveals": ("2F", ("1282", "1283"), ("1283", "1281"))},
    "1F-CUR": {"lobby door reveals": ("1F", ("B1D", "B1C"), ("B1D", "AFA")),
               "bath door reveals": ("1F", ("C0F", "C10"), ("C0F", "C0D"))},
}


def _segs(msp):
    geom, mids = {}, []
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            geom[e.dxf.handle] = ("LINE", ((a.x, a.y), (b.x, b.y)))
            if e.dxf.layer == "1":
                mids.append((a.x + b.x) / 2)
        elif t == "ARC":
            c = e.dxf.center
            geom[e.dxf.handle] = ("ARC", ((c.x, c.y), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle))
    return geom, sorted(mids)


def _storeys(msp, mids):
    clusters, cur = [], []
    for x in mids:
        if cur and x - cur[-1] > 8000:
            clusters.append(cur)
            cur = []
        cur.append(x)
    clusters.append(cur)
    out = {}
    for e in msp.query("INSERT"):
        if e.dxf.name in TITLES:
            tx = e.dxf.insert.x
            near = [c for c in clusters if c[0] - 10000 <= tx <= c[-1] + 10000]
            c = max(near, key=len)
            out[TITLES[e.dxf.name]] = (c[0] - 1000, c[-1] + 1000)
    return out


def _gap(geom, ha, hb):
    pa, pb = geom[ha][1], geom[hb][1]
    return min(math.dist(p, q) for p in pa for q in pb)


def _depth(geom, ha, hb):
    (x1, y1), (x2, y2) = geom[ha][1]
    px, py = geom[hb][1][0]
    return abs((x2 - x1) * (y1 - py) - (x1 - px) * (y2 - y1)) / math.dist((x1, y1), (x2, y2))


def read(path):
    import ezdxf

    doc = ezdxf.readfile(path)
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    msp = doc.modelspace()
    geom, mids = _segs(msp)
    st = _storeys(msp, mids)
    cols = {k: [] for k in st}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append((e.dxf.handle, p))
    out = {"schema": "T606_DRAWN_V1", "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
           "units": "m / m2", "rule": R.RULE_ID, "outlines": {}, "addons": {}}
    for oid, (s, line, chain, note) in OUTLINES.items():
        a0, b0 = st[s]
        for h, _ in chain:
            g = geom[h][1]
            x = g[0][0] if geom[h][0] == "LINE" else g[0][0]
            if not a0 < x < b0:
                raise R.RuleError(f"{oid}: {h} is not on the {s} plan")
        res = R.outline(geom, chain, [p for _, p in cols[s]])
        out["outlines"][oid] = {"storey": s, "engine_line": line, "note": note, "perimeter": str(res["perimeter"]),
                                "area": str(res["area"]), "notch_lm": str(res["notch_lm"]),
                                "wall_lm": str(res["wall_lm"]), "virtual_lm": str(res["virtual_lm"]),
                                "edges": [{"handle": e["handle"], "role": e["role"], "lm": str(e["lm"])}
                                          for e in res["edges"]]}
    for grp, items in ADDONS.items():
        out["addons"][grp] = {}
        for name, (s, (wa, wb), (da, db)) in items.items():
            w, d = _gap(geom, wa, wb) / 1000, _depth(geom, da, db) / 1000
            out["addons"][grp][name] = {"width_handles": [wa, wb], "depth_handles": [da, db], "width": str(R.q6(w)),
                                        "depth": str(R.q6(d)), "dP": str(R.q6(2 * d)), "dA": str(R.q6(w * d))}
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
    for k, v in d["outlines"].items():
        print(k, v["perimeter"], v["area"], "notch", v["notch_lm"], "virtual", v["virtual_lm"])
    for g, it in d["addons"].items():
        for k, v in it.items():
            print(g, k, v["width"], v["depth"])


if __name__ == "__main__":
    main()
