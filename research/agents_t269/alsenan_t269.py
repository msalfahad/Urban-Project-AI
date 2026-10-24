"""T-269 Alsenan: the floor-area closure blockers settled from the drawings (research; nothing applied to any line).

Usage (Python 3.11; drawings stay in the private folder, outside every worktree):
    python3 -I research/agents_t269/alsenan_t269.py --arch <P7757.dxf> --st <ST7757 dxf.dxf> --v29 <v29.pkl> --out <dir>
    (v29.pkl = tools.urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9"), pickled (boq, arch, extra))
Every input is located by its entity HANDLE on the Drive drawings (listed in HANDLES below), never by a coordinate
stored here. Writes summary_t269.json (areas, statuses, handles, sha256 prefixes; no coordinates)."""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ezdxf  # noqa: E402
from shapely.geometry import LineString  # noqa: E402

import floor_blockers as FB  # noqa: E402
from engine.source import stair_floor_residue as SFR  # noqa: E402

HANDLES = {
    # 1F plan, main stair ST-01, east lane = ground-to-first upper flight MS1-U arriving at the +5.50 landing
    "east_risers_L2": ["A93", "A94", "A9E", "AA0", "A9F", "A9D", "AA4", "AA3", "AA2", "AA1", "ABD"],
    "east_nosings_L5": ["A92", "A95", "AA5", "AA6", "AA7", "AA8", "AA9", "AAA", "AAB", "AAC", "ABE"],
    "landing_dim_1950": "10DF", "stair_width_dim_2500": "D25", "west_landing_nosing_L5": "AC0",
    # ST7757 GF-roof slab plan (1F floor slab): its stair copy draws the east lane's 12th riser line
    "st_east_riser_at_landing_edge": "459", "st_east_risers": ["459", "270", "264", "265", "266", "267", "260", "262",
                                                               "263", "261", "25C", "25B"],
    # frame check arch 1F <-> ST slab sheet: the same two 0.60 x 0.25 column outlines
    "col_pair_arch": ["2FE7", "3008"], "col_pair_st": ["332", "374"],
    # 1F round stair ST-02: band beside RS-A (D-23 / RL-06), stair outline lines, the column at the wall
    "band_faces_L5": ["AF5", "AF6"], "band_top_L5": "D23", "stair_west_edge_L5": "B75", "st_slab_edge_L1": "289",
    "col_at_band_arch": "3008",
    # GF pantry box line (layer 5)
    "pantry_box_L5": ["B3", "AD"],
}
CLOSED_LAYERS = ("1", "W", "S-COL.BON")  # walls, windows, columns on this set
SOLID_STAIR_LAYER = "5"  # this drawing set's visible / cut stair layer (T-122, T-129); dashed overhead = layer 2
SECTION_COUNT_MS1_U = 12  # section A-A, owner Q-46 A; counted and VERIFIED by the Checker in T-111 (MERGED c0e8443)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


def _line(doc, h):
    e = doc.entitydb.get(h)
    if e is None or e.dxftype() != "LINE":
        raise SystemExit(f"handle {h}: not a LINE in this drawing")
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)


def _col(doc, h):
    e = doc.entitydb.get(h)
    pts = [(p[0], p[1]) for p in e.get_points("xy")]
    return min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts)


def foot_strip(arch):
    u = 0.001
    ys = lambda hs: [(_line(arch, h)[0][1]) * u for h in hs]  # noqa: E731 - the flight runs along y on this sheet
    risers, nosings = ys(HANDLES["east_risers_L2"]), ys(HANDLES["east_nosings_L5"])
    dim = arch.entitydb.get(HANDLES["landing_dim_1950"])
    # the 1950 dimension runs from the wall face to the landing edge: its end farther from the wall is the edge
    p2, p3 = dim.dxf.defpoint2, dim.dxf.defpoint3
    edge = (p2.y if abs(p2.y - min(risers) / u) < abs(p3.y - min(risers) / u) else p3.y) * u
    xs = [_line(arch, h)[0][0] for h in HANDLES["east_risers_L2"]] + [_line(arch, h)[1][0] for h in HANDLES["east_risers_L2"]]
    width = round((max(xs) - min(xs)) * u, 4)
    first = max(risers) if edge < min(risers) else min(risers)
    rec = FB.arriving_flight_foot(first_riser=first, drawn_risers=risers, drawn_nosings=nosings,
                                  governing_risers=SECTION_COUNT_MS1_U, landing_edge=edge, width=width)
    rec.update({"drawn_risers": len(risers), "flight_width_m": width,
                "landing_edge_to_top_riser_m": round(abs(rec.get("top_riser", edge) - edge), 4)})
    rec.pop("top_riser", None)  # a drawing coordinate: not written out
    return rec


def st_check(arch, st):
    a = [_col(arch, h) for h in HANDLES["col_pair_arch"]]
    s = [_col(st, h) for h in HANDLES["col_pair_st"]]
    dx, dy = s[0][0] - a[0][0], s[0][1] - a[0][1]
    pair_resid = max(abs(s[1][0] - a[1][0] - dx), abs(s[1][1] - a[1][1] - dy))
    # ST 12th-riser line vs the arch landing edge (1950 end) and the arch west-lane landing nosing
    st459 = _line(st, HANDLES["st_east_riser_at_landing_edge"])[0][1] - dy
    ac0 = _line(arch, HANDLES["west_landing_nosing_L5"])[0][1]
    st_lines = sorted(_line(st, h)[0][1] for h in HANDLES["st_east_risers"])
    gaps = [round((b - a_) / 1000.0, 4) for a_, b in zip(st_lines, st_lines[1:])]
    return {"frame_pair_residual_mm": round(pair_resid, 3), "st_east_riser_lines": len(st_lines),
            "st_east_goings_m": sorted(set(gaps)),
            "st_459_minus_arch_landing_edge_mm": round(st459 - ac0, 3)}, (dx, dy)


def side_band(arch, st, d):
    dx, dy = d
    u = 0.001
    f5, f6 = _line(arch, HANDLES["band_faces_L5"][0]), _line(arch, HANDLES["band_faces_L5"][1])
    top = _line(arch, HANDLES["band_top_L5"])
    west = _line(arch, HANDLES["stair_west_edge_L5"])
    col = _col(arch, HANDLES["col_at_band_arch"])
    x5, x6 = f5[0][0] * u, f6[0][0] * u
    y1 = max(top[0][1], top[1][1]) * u
    y0 = col[3] * u  # the band starts at the column face (the column occupies the band's end at the wall)
    band = FB.rect(min(x5, x6), y0, max(x5, x6), y1)
    stair = FB.rect(west[0][0] * u, min(f5[0][1], f5[1][1]) * u, min(x5, x6), y1)
    e = _line(st, HANDLES["st_slab_edge_L1"])
    edge = LineString([((e[0][0] - dx) * u, (e[0][1] - dy) * u), ((e[1][0] - dx) * u, (e[1][1] - dy) * u)])
    rec = FB.side_band_floor(band, stair, [edge])
    rec["band_m2"] = round(band.area, 6)
    return rec


def gf(arch, v29):
    boq, A, extra = pickle.load(open(v29, "rb"))
    u = A["run"]["unit_m"]
    rooms = {r["room_id"]: r for r in A["rooms"]}
    out = {}
    face = SFR._face_geom(rooms["GF-RC99C2A"], u)
    fls = rooms["GF-RC99C2A"]["symbols_inside"]["stair_flights"]
    # Overhead or below the cut, read from the drawing itself (the engine's also_drawn_on misses F2): a flight is drawn
    # below the cut when any SOLID stair line (layer 5 on this set: the cut / visible stair layer, T-122 / T-129) lies
    # inside its tread outline; only dashed overhead lines (layer 2) -> overhead.
    from shapely.geometry import Point
    from shapely.ops import unary_union
    flights = []
    for f in fls:
        quads = [SFR._poly(q, u) for q in f["tread_quads"]]
        inner = unary_union(quads).buffer(-0.01)
        solid = sum(1 for s in extra["segments"] if s["layer"] == SOLID_STAIR_LAYER and inner.contains(
            Point((s["a"][0] + s["b"][0]) / 2 * u, (s["a"][1] + s["b"][1]) / 2 * u)))
        flights.append({"id": f["flight_id"].split(":")[-1], "quads": quads, "drawn_overhead": solid == 0,
                        "solid_lines_inside": solid})
    # closed elements drawn on THIS plan under the flights: wall / column / window layers of this set
    fu = unary_union([fl["quads"][i] for fl in flights for i in range(len(fl["quads"]))])
    closed = [LineString([(s["a"][0] * u, s["a"][1] * u), (s["b"][0] * u, s["b"][1] * u)]).buffer(0.002)
              for s in extra["segments"] if s["layer"] in CLOSED_LAYERS and
              LineString([(s["a"][0] * u, s["a"][1] * u), (s["b"][0] * u, s["b"][1] * u)]).intersects(fu.buffer(-0.01))]
    under = FB.floor_under_rising_stair(face, flights, closed_under=closed)
    under["closed_segments_under_flights"] = len(closed)
    b3 = _line(arch, HANDLES["pantry_box_L5"][0])
    ad = _line(arch, HANDLES["pantry_box_L5"][1])
    xb = b3[0][0] * 0.001
    ylo = min(b3[0][1], b3[1][1], ad[0][1], ad[1][1]) * 0.001
    yhi = max(b3[0][1], b3[1][1], ad[0][1], ad[1][1]) * 0.001
    box = FB.rect(face.bounds[0] - 1, ylo, xb, yhi)
    pantry_part = face.intersection(box)
    quads = [q for f in flights for q in f["quads"]]
    f2 = SFR._face_geom(rooms["GF-RC06FED"], u)
    tq = FB.treads_in_piece
    near = min(q.distance(box) for q in quads)
    out["RC99C2A"] = {"face_m2": round(face.area, 4), "pantry_box_part_m2": round(pantry_part.area, 4),
                      "treads_in_face_m2": under["treads_m2"], "treads_in_pantry_part_m2": tq(pantry_part, quads),
                      "nearest_tread_to_pantry_box_m": round(near, 3), "flights": under["rows"],
                      "floor_under_overhead_m2": under["floor_m2"], "held_below_cut_m2": under["held_m2"],
                      "closed_segments_under_flights": under["closed_segments_under_flights"]}
    out["RC06FED"] = {"face_m2": round(f2.area, 4), "treads_in_piece_m2": tq(f2, quads),
                      "flights_inside": len(rooms["GF-RC06FED"]["symbols_inside"].get("stair_flights") or ())}
    out["solid_lines_inside_flight"] = {f["id"]: f["solid_lines_inside"] for f in flights}
    out["engine_also_drawn_on"] = {f["flight_id"].split(":")[-1]: [f.get("layer")] + list(f.get("also_drawn_on") or ())
                                   for f in fls}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", required=True)
    ap.add_argument("--st", required=True)
    ap.add_argument("--v29", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    arch, st = ezdxf.readfile(a.arch), ezdxf.readfile(a.st)
    chk, d = st_check(arch, st)
    res = {"inputs": {"arch_sha256_8": _sha(a.arch), "st_sha256_8": _sha(a.st)}, "handles": HANDLES,
           "section_count_ms1_u": SECTION_COUNT_MS1_U,
           "d13_foot_strip_1f": foot_strip(arch), "st_corroboration": chk, "d23_side_band_1f": side_band(arch, st, d),
           "gf_pantry_and_round_stair": gf(arch, a.v29)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary_t269.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "handles"}, indent=1, default=str))


if __name__ == "__main__":
    main()
