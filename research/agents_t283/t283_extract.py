"""T-283 extractor (research only, NOT engine code): the two R3 corrections measured on the Alsenan drawings.

Re-runs the T-271 overlay (research/agents_t271/t271_extract.py, imported, not edited) on the same inputs and adds, per
floor piece and per beam piece inside it:
  stair_beyond   the part of the stair drawn under the slab that lies OUTSIDE the stair-class face, over a beam / band /
                 column face inside the room (R-CEIL-R3-1). Stair footprint per slab plan = the T-271 r2b stair zone of
                 GF-130 (round flight, straight flight, landing, east flight; built from its handles) UNION the straight
                 flights traced from the plan's own hidden tread lines (layer 2, groups of >= 3 parallel lines on the
                 same two stringer lines, first to last tread; ceilings_r3.flight_footprints);
  borders        the beam piece's free edge split by what lies on its open side (decor / NO_CEILING / STAIR_ZONE /
                 DOME_OPEN; R-CEIL-R3-2).
Writes ONLY ids, marks, statuses, areas and lengths (no coordinates, no texts): ALSENAN_T283_DELTAS.json.

Usage: python -I t283_extract.py <v29.pkl> <st_faces.json> <align.json> <arch.dxf> <out.json> <structural.dxf>"""
import csv
import json
import math
import pickle
import sys
from pathlib import Path

from shapely import wkt
from shapely.affinity import translate
from shapely.geometry import Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "agents_t271")]
import ceilings_r3 as C3  # noqa: E402
import t271_extract as X  # noqa: E402

CR = X.CR
TREAD_LAYER = "2"
MIN_TREADS = 3


def treads(doc, win):
    x0, x1, y0, y1 = win
    out = []
    for e in doc.modelspace():
        if e.dxftype() != "LINE" or e.dxf.layer != TREAD_LAYER:
            continue
        s, t = e.dxf.start, e.dxf.end
        if not (x0 <= s.x <= x1 and y0 <= s.y <= y1):
            continue
        out.append((e.dxf.handle, (s.x / 1000, s.y / 1000), (t.x / 1000, t.y / 1000)))
    return out


def main(argv=None):
    a = argv or sys.argv[1:]
    boq, A, extra = pickle.load(open(a[0], "rb"))
    SFJ = json.load(open(a[1]))
    AL = json.load(open(a[2]))
    import ezdxf
    from shapely.geometry import box as _box
    cls = {r["id"]: r["cls"] for r in csv.DictReader(open(X.RES / "agents_t139" / "PANELS.csv"))}
    st_doc = ezdxf.readfile(a[5])
    sys.path.insert(0, str(X.RES / "agents_t139"))
    import slab_faces as SFM
    reg, r2 = X._register(), X._r2()
    domes = [Point(*c).buffer(X.DOME_R, 256) for c in X.DOMES]
    # GF-130 split exactly as T-271 r2b, keeping the whole stair union (the spy keeps what split_structural_void got)
    cap = {}
    orig = CR.split_structural_void

    def spy(face, openings, stairs=(), **k):
        cap["stairs"] = unary_union(list(stairs))
        return orig(face, openings, stairs, **k)
    CR.split_structural_void = spy
    gf, vparts = [], None
    for f in SFJ["GF"]:
        if f["id"] != X.VOID_FACE:
            gf.append(f)
            continue
        vparts, _ = X.void_split(st_doc, wkt.loads(f["wkt"]))
        for lab, c, p in vparts:
            sid = f"{X.VOID_FACE}/{'POCKET' if 'pocket' in lab else 'LW' if 'light well' in lab else c}"
            gf.append({"id": sid, "wkt": p.wkt})
            cls[sid] = c
    CR.split_structural_void = orig
    SF = dict(SFJ, GF=gf)
    # stair footprint per slab plan
    report = {"stair_footprints": {}, "pieces": []}
    foot, open_parts = {}, {}
    for fl, win in SFM.SHEETS.items():
        tr = treads(st_doc, win)
        fls, loose = C3.flight_footprints(tr)
        fls = [(ids, p) for ids, p in fls if len(ids) >= MIN_TREADS]
        polys = [p for _, p in fls]
        if fl == "GF":
            polys.append(cap["stairs"])
        fp = unary_union(polys) if polys else None
        faces = [(f["id"], cls.get(f["id"], "?"), wkt.loads(f["wkt"])) for f in SF[fl]]
        info = {"flights": [{"treads": len(ids), "first": ids[0], "last": ids[-1], "m2": round(p.area, 4)}
                            for ids, p in fls], "loose_lines": len(loose)}
        if fp is not None:
            parts, outside = C3.stair_zone_parts(fp, [(i, c, p) for i, c, p in faces])
            info.update({"footprint_m2": round(fp.area, 4), "outside_every_face_m2": outside,
                         "parts": {i: {"cls": c, "m2": round(p.area, 4)} for i, c, p in parts}})
        report["stair_footprints"][fl] = info
        foot[fl] = fp
        nc = [p for i, c, p in faces if c in CR.NO_CEILING and not i.endswith("/STAIR")]
        stz = [p for i, c, p in faces if c in C3.STAIR_CLASSES] + ([fp] if fp is not None else [])
        op = []
        if nc:
            op.append(("NO_CEILING", unary_union(nc)))
        if stz:
            op.append(("STAIR_ZONE", unary_union(stz)))
        if fl == "1F":
            op.append(("DOME_OPEN", unary_union(domes)))
        open_parts[fl] = op
    pantry = None
    doc = ezdxf.readfile(a[3])
    pts = []
    for h in X.PANTRY_LINES:
        e = doc.entitydb.get(h)
        pts += [(e.dxf.start.x * 0.001, e.dxf.start.y * 0.001), (e.dxf.end.x * 0.001, e.dxf.end.y * 0.001)]
    xb, ylo, yhi = pts[0][0], min(p[1] for p in pts), max(p[1] for p in pts)
    pieces = []
    for room in A["rooms"]:
        g0 = X.face_geom(room)
        if room["room_id"] == X.PANTRY_FACE:
            pbox = _box(g0.bounds[0] - 1, ylo, xb, yhi)
            pieces.append((room, room["room_id"] + "/pantry", g0.intersection(pbox)))
            pieces.append((room, room["room_id"] + "/open", g0.difference(pbox)))
        else:
            pieces.append((room, room["room_id"], g0))
    for room, pid, g0 in pieces:
        fl = room["floor"]
        g = translate(g0, *AL[fl])
        rec = {"face": pid, "floor": fl, "stair_beyond": [], "beams": {}}
        for f in SF[fl]:
            c = cls.get(f["id"], "?")
            if c not in CR.BEAMISH:
                continue
            fg = wkt.loads(f["wkt"])
            if not fg.intersects(g):
                continue
            x = fg.intersection(g)
            if x.area < X.MIN_PIECE:
                continue
            m = X.regmatch(reg, fl, fg)
            st, dep = ("NO_REGISTER_ROW", "") if not m else X.r2_status(r2.get(m["member_id"]))
            if foot[fl] is not None:
                u = x.intersection(foot[fl]).area
                if u > X.MIN_PIECE:
                    rec["stair_beyond"].append([f["id"], round(u, 6)])
            free = CR.free_edge(x, g, X.EDGE_TOL)
            bd = C3.border_segments(x, g, open_parts[fl])
            rec["beams"][f["id"]] = {"mark": m["mark"] if m else None, "member": m["member_id"] if m else None,
                                     "status": st, "depth": CR._depth(dep), "piece_m2": round(x.area, 6),
                                     "free_edge_m": round(free, 4), "borders": bd}
        report["pieces"].append(rec)
    json.dump(report, open(a[4], "w"), indent=1, sort_keys=True)
    for r in report["pieces"]:
        ch = {k: v["borders"] for k, v in r["beams"].items() if len(v["borders"]) > 1 or "decor" not in v["borders"]}
        if r["stair_beyond"] or ch:
            print(r["face"], r["stair_beyond"], ch)


if __name__ == "__main__":
    main()
