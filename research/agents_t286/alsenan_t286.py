"""T-286 Alsenan run: the GF pantry 'doorway zone' (engine strip SITE-0a31aaa10796d33a, 1.100 m2, BLOCKED_RFI) read
against the drawn lines around it, the pantry box closure, and the W03 room-side line re-read (T-250 MERGED 47390c9b).

Usage (Python 3.11; drawings stay in the private folder, outside every worktree):
    python3 -I research/agents_t286/alsenan_t286.py --arch <P7757.dxf> --v29 <v29.pkl> --out <dir>
    (v29.pkl = tools.urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9"), pickled (boq, arch, extra))
Writes summary_t286.json: handles, lengths and areas in metres, coordinates only RELATIVE to the pantry box corner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ezdxf  # noqa: E402
from shapely.geometry import LineString, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import pantry_zone as PZ  # noqa: E402
from engine.source import stair_floor_residue as SFR  # noqa: E402

STRIP_ID = "SITE-0a31aaa10796d33a"
H = {  # drawing handles on P7757.dxf (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip)
    "box_west_face": "AE", "box_south_face": "A6", "box_north_face": "158", "box_east_edge": ("B3", "AD"),
    "box_dims": ("5D5", "5E1"),  # printed 3000 (west face -> B3) and 4500 (A6 -> north face)
    "east_counter": ("B2", "AA", "B4", "15D"), "west_counter": ("B1", "15C", "33F", "335"),
    "column": "2FAE", "band_lines": ("A8", "A9", "4B4"),
    "w03_room_glass": "27D", "w03_glass_inner": ("27E", "27F", "280"), "w03_pool_face": "201",
    "w03_partition": ("2E2", "2E4"),
}
ROLE = {}  # handle -> bound kind (from the drawing reading in T-286 section 2)
for h in ("AE", "A6", "158", "159", "AF", "A0", "B0"):
    ROLE[h] = "WALL_FACE"
for h in ("B3", "AD"):
    ROLE[h] = "ROOM_EDGE"
for h in H["east_counter"] + H["west_counter"]:
    ROLE[h] = "FIXTURE_OUTLINE"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _seg(doc, h):
    e = doc.entitydb[h]
    return LineString([(e.dxf.start.x * 0.001, e.dxf.start.y * 0.001), (e.dxf.end.x * 0.001, e.dxf.end.y * 0.001)])


def _bounds(piece, doc, tol=0.002):
    """Every edge of the piece with the drawn line lying on it (by handle role) or ZONE_LINE_UNDRAWN."""
    cs = list(piece.exterior.coords)
    segs = {h: _seg(doc, h) for h in ROLE}
    out = []
    for a, b in zip(cs, cs[1:]):
        e = LineString([a, b])
        if e.length < 1e-6:
            continue
        hit = [h for h, s in segs.items() if s.buffer(tol).contains(e)]
        if hit:
            out.append({"kind": ROLE[hit[0]], "length_m": round(e.length, 6), "ref": "/".join(sorted(hit))})
        else:
            out.append({"kind": "ZONE_LINE_UNDRAWN", "length_m": round(e.length, 6), "ref": None})
    return out


def _rel(g, x0, y0):
    return [(round(x - x0, 4), round(y - y0, 4)) for x, y in g.exterior.coords]


def pantry(doc, A):
    u = A["run"]["unit_m"]
    west = _seg(doc, H["box_west_face"]).coords[0][0]
    east = _seg(doc, "B3").coords[0][0]
    south = _seg(doc, "A6").coords[0][1]
    north = _seg(doc, "158").coords[0][1]
    dim_w = doc.entitydb[H["box_dims"][0]].get_measurement() * 0.001
    dim_l = doc.entitydb[H["box_dims"][1]].get_measurement() * 0.001
    B = box(west, south, east, north)
    col = Polygon([(x * 0.001, y * 0.001) for x, y in doc.entitydb[H["column"]].get_points("xy")])
    notch = B.intersection(col).area
    rooms = {r["room_id"]: r for r in A["rooms"]}
    strip = next(s for s in A["floor_areas"][0]["strips"] if s["strip_id"] == STRIP_ID)
    piece = Polygon(strip["polygon_m"])
    rc06 = SFR._face_geom(rooms["GF-RC06FED"], u)
    rc99 = SFR._face_geom(rooms["GF-RC99C2A"], u).intersection(B)
    op003 = B.difference(unary_union([rc06, rc99, piece, col]))
    # east counter footprint from its drawn outline (B2 / AA / B4 / 15D + the box edge B3 + the wall face A6)
    xs = {h: _seg(doc, h) for h in H["east_counter"]}
    x_b2 = xs["B2"].coords[0][0]
    x_b4 = xs["B4"].coords[0][0]
    y_aa = xs["AA"].coords[0][1]
    y_15d = xs["15D"].coords[0][1]
    counter_e = unary_union([box(x_b2, south, east, y_aa), box(x_b4, y_aa, east, y_15d)])
    wc = {h: _seg(doc, h) for h in H["west_counter"]}
    x_b1 = wc["B1"].coords[0][0]
    y_335 = wc["335"].coords[0][1]
    y_15c = wc["15C"].coords[0][1]
    x_33f = wc["33F"].coords[0][0]
    counter_w = unary_union([box(west, y_335, x_b1, north), box(x_b1, y_15c, x_33f, north)]).difference(col)
    bounds = _bounds(piece, doc)
    res = PZ.reclass_piece(
        {"id": STRIP_ID, "polygon_m": list(piece.exterior.coords), "area_m2": strip["area_m2"],
         "engine_class": strip["class"]},
        bounds,
        [{"id": "GF pantry (printed 450 x 300)", "box_m": list(B.exterior.coords), "floor_class": "WET",
          "class_source": "owner Q-37 A (2026-10-19): the pantry is wet within its printed 4.50 x 3.00 box"}])
    clos = PZ.box_closure(round(B.area, 6), {"column 2FAE notch": round(notch, 6)},
                          {"GF-RC06FED": round(rc06.area, 6), "GF-RC99C2A part": round(rc99.area, 6),
                           "OP-003 strip part": round(op003.area, 6), "doorway zone " + STRIP_ID: round(piece.area, 6)})
    band_x = [min(_seg(doc, h).coords[0][0], _seg(doc, h).coords[1][0]) for h in H["band_lines"]]
    return {
        "box": {"west_face_to_B3_m": round(east - west, 4), "A6_to_north_face_m": round(north - south, 4),
                "printed_m": [round(dim_w, 4), round(dim_l, 4)], "area_m2": round(B.area, 6),
                "column_2FAE_notch_m2": round(notch, 6)},
        "doorway_zone": {"engine": {k: strip[k] for k in ("area_m2", "class", "disposition", "opening_ids")},
                         "engine_bounded_by_lm": strip["bounded_by_lm"],
                         "polygon_rel_m": _rel(piece, west, south), "bounds": bounds, "reclass": res,
                         "inside_east_counter_m2": round(piece.intersection(counter_e).area, 6),
                         "outside_east_counter_m2": round(piece.difference(counter_e).area, 6)},
        "east_counter": {"footprint_m2": round(counter_e.area, 6),
                         "in_doorway_zone_m2": round(counter_e.intersection(piece).area, 6),
                         "in_OP003_strip_m2": round(counter_e.intersection(op003).area, 6),
                         "in_RC99C2A_part_m2": round(counter_e.intersection(rc99).area, 6),
                         "in_RC06FED_m2": round(counter_e.intersection(rc06).area, 6)},
        "west_counter": {"footprint_net_of_column_m2": round(counter_w.area, 6),
                         "in_RC99C2A_part_m2": round(counter_w.intersection(rc99).area, 6)},
        "band_edge_lines_west_end_m_east_of_box": [round(x - east, 4) for x in band_x],
        "closure": clos,
    }


def w03(doc):
    e = doc.entitydb[H["w03_room_glass"]]
    pts = [(p[0] * 0.001, p[1] * 0.001, p[2]) for p in e.get_points("xyb")]
    pool = doc.entitydb[H["w03_pool_face"]]
    c = (pool.dxf.center.x * 0.001, pool.dxf.center.y * 0.001)
    r = None
    for a, b in zip(pts, pts[1:]):
        if abs(a[2]) > 1e-9:
            th = 4 * math.atan(abs(a[2]))
            r = math.dist(a[:2], b[:2]) / (2 * math.sin(th / 2))
    ends = []
    for h in H["w03_partition"]:
        s = doc.entitydb[h]
        p = min((s.dxf.start, s.dxf.end), key=lambda q: abs(math.dist((q.x * 0.001, q.y * 0.001), c) - r))
        ends.append((p.x * 0.001, p.y * 0.001))
    pe = PZ.arc_between(c, r, ends[0], ends[1])
    pool_len = math.radians((pool.dxf.end_angle - pool.dxf.start_angle) % 360) * pool.dxf.radius * 0.001
    out = PZ.room_side_line({"source": "DRAWN_LINE", "ref": "27D", "polyline_xyb": pts, "room_touches": True},
                            [{"ref": "2E2/2E4", "length_m": pe}], printed_width_m=6.57)
    out["pool_face_201_m"] = round(pool_len, 4)
    out["pool_face_201_radius_m"] = round(pool.dxf.radius * 0.001, 4)
    out["room_glass_radius_m"] = round(r, 4)
    out["T250_merged"] = {"worker": "6.726 .. 6.738", "checker_own": 6.7294, "T128_walk": 6.731}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--v29", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = ezdxf.readfile(a.arch)
    _, A, _ = pickle.load(open(a.v29, "rb"))
    out = {"drawing": {"P7757.dxf_sha256_8": _sha(a.arch)[:8]}, "pantry": pantry(doc, A), "w03": w03(doc)}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    p = Path(a.out) / "summary_t286.json"
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
