"""T-439 extractor (research only, NOT engine code): the two GF pantry floor strips that carry a floor-finish line but no
ceiling and no skirting line (T-435 SILENT): what bounds each edge on the architectural plan, what the structural roof
slab draws over each strip, and which pantry wall faces each strip's edges lie on.

    python3 -I research/agents_t439/t439_extract.py <v29.pkl> <st_faces.json> <align.json> <P7757.dxf> <ST7757.dxf> <out.json>

v29.pkl = tools.urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9") pickled (boq, arch, extra);
st_faces.json = research/agents_t139/slab_faces.py on the structural DXF; align.json = research/agents_t147/scripts/
align.py (column-fit translation, arch -> structural metres). Drawings: Drive "Alsenan chalet project"
(P7757_DXF_COMPRESSED.zip -> P7757.dxf sha256 ab54dd55, "ST7757 dxf.dxf" sha256 9f9d1179), private folder only.
Writes ONLY handles, layers, lengths, areas, ids, marks and statuses (no coordinate, no text of the drawing)."""
from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path

from shapely import wkt
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
RES = HERE.parent
ROOT = RES.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(RES / "agents_t271"))
import ceilings_r2 as CR  # noqa: E402
import t271_extract as T271  # noqa: E402  (regmatch / _register / _r2, reused by import, never edited)

STRIP_ID = "SITE-0a31aaa10796d33a"            # V2.9 GF strip, 1.100 m2 (T-286 'doorway zone'; T-427)
OP003_STRIP = "SITE-baa7db7fb0d465b6"         # V2.9 OP-003 THRESHOLD strip 1.964 m2 along the prolonged band edge (T-427);
#                                               its part inside the printed pantry box is GF-OP-003-NO-OPENING (T-240)
H = {"west": "AE", "south": "A6", "north": "158", "east": ("B3", "AD"), "col": "2FAE",
     "east_counter": ("B2", "AA", "B4", "15D"), "west_counter": ("B1", "15C", "33F", "335"),
     "band_lines": ("A8", "A9", "4B4")}
EDGE_LAYERS = {"0", "1", "2", "5", "W", "D", "S-COL.BON", "DOOR", "DOORS", "WINDOW", "WINDOWS"}
TOL = 0.002   # m: a drawn line lies on a piece edge when it covers the edge within 2 mm


def _sha8(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


def _seg(doc, h):
    e = doc.entitydb[h]
    return LineString([(e.dxf.start.x * 0.001, e.dxf.start.y * 0.001), (e.dxf.end.x * 0.001, e.dxf.end.y * 0.001)])


def _drawn_segments(doc, window):
    """Every straight drawn segment (LINE, LWPOLYLINE / POLYLINE edges, INSERT bounding lines left out) of the edge
    layers inside the window: (handle, layer, dxftype, LineString in metres)."""
    out = []
    msp = doc.modelspace()
    for e in msp.query("LINE LWPOLYLINE"):
        lay = e.dxf.layer
        if lay not in EDGE_LAYERS:
            continue
        if e.dxftype() == "LINE":
            pts = [(e.dxf.start.x * 0.001, e.dxf.start.y * 0.001), (e.dxf.end.x * 0.001, e.dxf.end.y * 0.001)]
            segs = [pts]
        else:
            p = [(x * 0.001, y * 0.001) for x, y in e.get_points("xy")]
            if e.closed and p:
                p = p + [p[0]]
            segs = [[a, b] for a, b in zip(p, p[1:])]
        for s in segs:
            ls = LineString(s)
            if ls.length > 1e-6 and ls.intersects(window):
                out.append((e.dxf.handle, lay, e.dxftype(), ls))
    return out


def _edges(piece, drawn, roles):
    """Each edge of the piece: the drawn segments lying on it (collinear within TOL and covering >= 50 % of it)."""
    out = []
    cs = list(piece.exterior.coords)
    for a, b in zip(cs, cs[1:]):
        e = LineString([a, b])
        if e.length < 1e-6:
            continue
        hits = []
        for h, lay, typ, s in drawn:
            cov = s.buffer(TOL, cap_style=2).intersection(e).length
            if cov >= 0.5 * e.length and e.buffer(TOL, cap_style=2).intersection(s).length > 0:
                hits.append({"handle": h, "layer": lay, "type": typ, "covers_m": round(min(cov, e.length), 4)})
        role = "ZONE_LINE_UNDRAWN"
        if hits:
            known = [roles.get(x["handle"]) for x in hits if roles.get(x["handle"])]
            role = known[0] if known else "DRAWN_OTHER"
        out.append({"length_m": round(e.length, 4), "role": role,
                    "drawn": sorted(hits, key=lambda x: x["handle"])})
    return out


def _depth(info):
    try:
        return float((info or {}).get("r2_depth") or "nan") if (info or {}).get("r2_status") == "CALCULATED" else None
    except ValueError:
        return None


def _box_bulkheads(slab, boxS, piecesS, tol=None):
    """Beam faces over the printed pantry, measured on the WHOLE pantry ceiling (the box net of its column; R-CEIL-R2-3
    on the box, so an engine zone line between two pieces never makes or hides a bulkhead). Each free face segment
    gets its neighbour (the slab face 5 mm outside it: SLAB, a beam with its r2 depth, an unregistered piece) and is
    split by piece: a face crossing pieces is clipped exactly, each part to its piece; a face running ON an engine zone
    line between two pieces is listed apart (never given to both)."""
    tol = CR.EDGE_TOL if tol is None else tol
    rb = boxS.boundary
    out = []
    for fid, c, fg, info in slab:
        if c not in CR.BEAMISH or not fg.intersects(boxS):
            continue
        x = fg.intersection(boxS)
        if x.area < 0.005:
            continue
        segs = []
        for g in getattr(x, "geoms", [x]):
            if g.is_empty or g.geom_type != "Polygon":
                continue
            cc = list(g.exterior.coords)
            for p0, p1 in zip(cc, cc[1:]):
                m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                if all(rb.distance(Point(q)) <= tol for q in (p0, p1, m)):
                    continue
                L = LineString([p0, p1]).length
                if L < 1e-6:
                    continue
                nx, ny = (p1[1] - p0[1]) / L, -(p1[0] - p0[0]) / L
                probe = Point(m[0] + 0.005 * nx, m[1] + 0.005 * ny)
                if g.buffer(1e-9).contains(probe):
                    probe = Point(m[0] - 0.005 * nx, m[1] - 0.005 * ny)
                nb = next(((f2, c2, i2) for f2, c2, g2, i2 in slab if f2 != fid and g2.contains(probe)), None)
                segs.append((LineString([p0, p1]), nb))
        segrecs = []
        for z, nb in segs:
            if nb is None:
                ncls, nmem, nd = "NONE", None, None
            else:
                ncls, nmem, nd = nb[1], (nb[2] or {}).get("member"), _depth(nb[2])
            along = sorted(pid for pid, pg in piecesS.items()
                           if z.intersection(pg.boundary.buffer(0.001)).length > 0.5 * z.length)
            if len(along) >= 2:          # the face runs ON an engine zone line between two pieces
                bp = {pid: 0.0 for pid in piecesS}
            else:                        # the face crosses pieces: exact clip, each part to the piece it lies in
                bp = {pid: round(z.intersection(pg).length, 4) for pid, pg in piecesS.items()}
            segrecs.append({"m": round(z.length, 4), "neighbour_cls": ncls, "neighbour_member": nmem,
                            "neighbour_r2_depth": nd, "by_piece_m": bp, "on_zone_line_between": along
                            if len(along) >= 2 else [], "on_zone_line_m": round(z.length - sum(bp.values()), 4)})
        rec = {"slab_face": fid, "cls": c, "piece_in_box_m2": round(x.area, 6),
               "free_edge_on_box_m": round(sum(z.length for z, _ in segs), 4), "segments": segrecs}
        rec.update(info or {"member": None, "mark": None, "r2_status": "NO_REGISTER_ROW", "r2_depth": ""})
        out.append(rec)
    return out


def main(argv=None):
    a = argv or sys.argv[1:]
    pkl, stf, alj, arch, st, outp = a[:6]
    import ezdxf
    boq, A, extra = pickle.load(open(pkl, "rb"))
    SF = json.load(open(stf))
    AL = json.load(open(alj))
    doc = ezdxf.readfile(arch)
    cls = {r["id"]: r["cls"] for r in __import__("csv").DictReader(open(RES / "agents_t139" / "PANELS.csv"))}
    reg, r2 = T271._register(), T271._r2()

    west = _seg(doc, H["west"]).coords[0][0]
    east = _seg(doc, "B3").coords[0][0]
    south = _seg(doc, H["south"]).coords[0][1]
    north = _seg(doc, H["north"]).coords[0][1]
    B = box(west, south, east, north)
    col = Polygon([(x * 0.001, y * 0.001) for x, y in doc.entitydb[H["col"]].get_points("xy")])
    box_net = B.difference(col)
    rooms = {r["room_id"]: r for r in A["rooms"]}
    from engine.source import stair_floor_residue as SFR
    u = A["run"]["unit_m"]
    rc06 = SFR._face_geom(rooms["GF-RC06FED"], u)
    rc99 = SFR._face_geom(rooms["GF-RC99C2A"], u).intersection(B)
    s1 = next(s for s in A["floor_areas"][0]["strips"] if s["strip_id"] == STRIP_ID)
    p1 = Polygon(s1["polygon_m"])
    # OP-003 doorway-strip face of V2.9 (the room record of the strip), clipped to the printed box = the 0.600 part
    s2 = next(s for s in A["floor_areas"][0]["strips"] if s["strip_id"] == OP003_STRIP)
    op_face = Polygon(s2["polygon_m"])
    p2 = op_face.intersection(B)
    p2_alt = B.difference(unary_union([rc06, rc99, p1, col]))       # T-286 route (box less the other pieces)

    xs = {h: _seg(doc, h) for h in H["east_counter"]}
    counter_e = unary_union([box(xs["B2"].coords[0][0], south, east, xs["AA"].coords[0][1]),
                             box(xs["B4"].coords[0][0], xs["AA"].coords[0][1], east, xs["15D"].coords[0][1])])
    wc = {h: _seg(doc, h) for h in H["west_counter"]}
    counter_w = unary_union([box(west, wc["335"].coords[0][1], wc["B1"].coords[0][0], north),
                             box(wc["B1"].coords[0][0], wc["15C"].coords[0][1], wc["33F"].coords[0][0], north)]
                            ).difference(col)

    roles = {}
    for h in ("AE", "A6", "158", "159", "AF", "A0", "B0"):
        roles[h] = "WALL_FACE"
    for h in ("B3", "AD"):
        roles[h] = "ROOM_EDGE_OPEN"
    for h in H["east_counter"] + H["west_counter"]:
        roles[h] = "FIXTURE_OUTLINE"
    window = B.buffer(1.0)
    drawn = _drawn_segments(doc, window)
    # every door / window insert near the box (jamb test): INSERT blocks on any layer whose insertion point is near
    inserts = []
    for e in doc.modelspace().query("INSERT"):
        p = Point(e.dxf.insert.x * 0.001, e.dxf.insert.y * 0.001)
        if p.distance(B) <= 0.5:
            inserts.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "block": e.dxf.name,
                            "dist_to_box_m": round(p.distance(B), 3),
                            "dist_to_strip1_m": round(p.distance(p1), 3), "dist_to_strip2_m": round(p.distance(p2), 3)})

    # structural slab over the strips (GF roof slab, arch -> structural frame by the column-fit translation)
    dx, dy = AL["GF"]
    slab = []
    for f in SF["GF"]:
        fg = wkt.loads(f["wkt"])
        c = cls.get(f["id"], "?")
        info = None
        if c in CR.BEAMISH:
            m = T271.regmatch(reg, "GF", fg)
            if m:
                stt, dep = T271.r2_status(r2.get(m["member_id"]))
                info = {"member": m["member_id"], "mark": m["mark"], "t110_status": m["status"],
                        "t110_depth": m["depth_m"], "r2_status": stt, "r2_depth": dep}
        slab.append((f["id"], c, fg, info))
    boxS = translate(box_net, dx, dy)

    def above(piece):
        g = translate(piece, dx, dy)
        return CR.overlay(g, slab)

    def piece_rec(pid, poly, extra_):
        return dict({"id": pid, "area_m2": round(poly.area, 6), "in_box_m2": round(poly.intersection(B).area, 6),
                     "in_column_m2": round(poly.intersection(col).area, 6),
                     "in_east_counter_m2": round(poly.intersection(counter_e).area, 6),
                     "in_west_counter_m2": round(poly.intersection(counter_w).area, 6),
                     "edges": _edges(poly, drawn, roles), "above": above(poly)}, **extra_)

    out = {
        "inputs": {"P7757.dxf": _sha8(arch), "ST7757.dxf": _sha8(st), "v29_method": "ARCH_TAKEOFF_V2.9",
                   "align_GF_m": [round(dx, 4), round(dy, 4)]},
        "box": {"m2": round(B.area, 6), "net_of_column_m2": round(box_net.area, 6),
                "west_to_B3_m": round(east - west, 4), "A6_to_158_m": round(north - south, 4),
                "pieces_m2": {"GF-RC06FED": round(rc06.area, 6), "GF-RC99C2A part": round(rc99.area, 6),
                              STRIP_ID: round(p1.area, 6), "OP-003 strip part": round(p2.area, 6)},
                "closure_m2": round(box_net.area - rc06.area - rc99.area - p1.area - p2.area, 6),
                "above": CR.overlay(boxS, slab),
                "beam_faces": _box_bulkheads(slab, boxS, {k: translate(v, dx, dy) for k, v in (
                    ("GF-RC06FED", rc06), ("GF-RC99C2A part", rc99), ("GF-SITE-" + STRIP_ID.split("SITE-")[1], p1),
                    ("GF-OP-003-NO-OPENING", p2))})},
        "strips": [
            piece_rec("GF-SITE-" + STRIP_ID.split("SITE-")[1], p1,
                      {"engine": {k: s1[k] for k in ("area_m2", "class", "disposition", "opening_ids",
                                                     "bounded_by_lm")}}),
            piece_rec("GF-OP-003-NO-OPENING", p2,
                      {"engine": {"strip": OP003_STRIP, "strip_m2": s2["area_m2"], "class": s2["class"],
                                  "disposition": s2["disposition"], "opening_ids": s2["opening_ids"],
                                  "bounded_by_lm": s2["bounded_by_lm"],
                                  "route_box_less_pieces_m2": round(p2_alt.area, 6),
                                  "routes_agree_m2": round(p2.symmetric_difference(p2_alt).area, 6)}}),
        ],
        "inserts_near_box": sorted(inserts, key=lambda x: x["handle"]),
        "ceiling_lines_on_pieces_v29": sorted({ln["location"].get("element_id") for ln in boq["lines"]
                                               if ln["item_code"] == "FIN.CEILING"
                                               and any(k in str(ln["location"].get("element_id"))
                                                       for k in ("OP-003", STRIP_ID, OP003_STRIP))}),
    }
    json.dump(out, open(outp, "w"), indent=1, sort_keys=True)
    print(json.dumps({k: out["box"][k] for k in ("m2", "pieces_m2", "closure_m2")}))
    for s in out["strips"]:
        print(s["id"], s["area_m2"], "counter E/W", s["in_east_counter_m2"], s["in_west_counter_m2"])
        for e in s["edges"]:
            print("   edge", e["length_m"], e["role"], [(d["handle"], d["layer"]) for d in e["drawn"]])
        print("   above", s["above"]["above"])
        for b in s["above"]["beams"]:
            print("   beam", {k: b[k] for k in b if k != "slab_face"})
    for b in out["box"]["beam_faces"]:
        print("BOXBEAM", b["slab_face"], b["mark"], b["r2_depth"], b["free_edge_on_box_m"])
        for z in b["segments"]:
            print("     seg", z)


if __name__ == "__main__":
    main()
