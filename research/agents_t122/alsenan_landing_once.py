"""T-122 read-only Alsenan check: first-floor living group under owner Q-66 B (main-stair arrival landing = marble,
once, as its own element) and Q-56 A (living, corridor, landing, connector in their own rows).

Method:
    1. one ARCH_TAKEOFF_V2.9 run (pickle of tools.urban_boq_m9.arch_compute, as T-113 / T-116) gives the face
       1F-R78C367, its outlined void (moved back from the plan below), its tread quads, segments and arcs;
    2. engine/source/stair_floor_residue.face_residue (STAIR_FLOOR_RESIDUE_V1, merged) is run UNCHANGED; a copy of
       its source is executed in memory with one extra line that keeps its local geometries (floor cells, residue
       pieces, held pieces), so the pieces it reports as areas only are available as polygons; the file is not edited;
    3. every m2 of the face is put in exactly one category (porcelain row / marble element / void / no finish / HELD)
       by an independent shapely partition: the printed rectangles of the 1F plan (T-113 regions, the printed chains
       read again from the DXF dimension entities) intersected with the residue piece polygons;
    4. checks: the categories re-add to the face (0.001 m2); the landing rectangle holds no residue / void / tread /
       held m2 (so moving it to marble moves exactly 4.875 m2 out of the porcelain range and nothing else); the
       landing is not in the stair-marble lines of the finish table (research/agents_t086/ALSENAN_FINISH_TABLE.csv).
Usage (Python 3.11; the drawing stays outside the clone):
    python3 -I research/agents_t122/alsenan_landing_once.py --v29 <scratch>/v29.pkl --out <scratch>/t122
Writes only to --out. Areas and local metres (from the face's south-west bounding-box corner); no CAD world coordinates.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

from engine.source import stair_floor_residue as SFR  # noqa: E402

ROOM = "1F-R78C367"
# printed rectangles, local metres (x east, y north from the face's south-west bounding-box corner); T-113 regions,
# chains re-read from the DXF dimension entities in this run (see the report)
LIVING = (9.670, 0.000, 14.470, 5.200)            # 480 x 520
CORRIDOR = (3.800, 4.000, 9.670, 5.200)           # 587 x 120
LANDING = (0.000, 5.150, 2.500, 7.100)            # (120 + 10 + 120) x 195; 195 dimension 7.10 -> 5.15
CONNECTOR = [(2.500, 5.150, 3.800, 6.400), (3.800, 5.200, 6.170, 6.400)]  # 125 depth; 20 + 347 chain less 130
OPENING = (3.800, 0.000, 9.670, 4.000)            # 587 x 400
WELL = (0.000, 7.100, 2.500, 11.600)              # 330 + 120 of the 645 chain, 250 wide
NORTH_BAND = (0.000, 10.450, 2.500, 11.600)       # turn of the dog-leg (winder F5 + square S1 + winder corner)
GAP = (1.150, 7.100, 1.350, 10.450)               # drawn gap between the flights (printed 10, drawn 0.20)
S3 = (1.350, 7.100, 2.500, 7.450)                 # foot of the east flight (D-13)
RS_QUARTER = (9.670, 0.000, 10.820, 1.150)        # round-stair quarter landing in the living rectangle
RS_EDGE = (9.670, 2.350, 10.820, 2.400)           # arrival edge strip of the round-stair box


def _residue_with_geometry(room, voids, segments, arcs, u, doors):
    """Run SFR.face_residue unchanged, keeping its local geometries (in-memory copy, one added line)."""
    src = inspect.getsource(SFR.face_residue)
    marker = "    return rec\n"
    assert src.endswith(marker)
    src = src[: -len(marker)] + "    rec['_geom'] = dict(F=F, V=V, T_own=T_own, T_below=T_below, R=R, held=held, " \
        "floor_cells=floor_cells, cat_geoms=locals().get('cat_geoms'))\n" + marker
    ns = dict(vars(SFR))
    exec(compile(src, SFR.__file__ + " (T-122 copy)", "exec"), ns)
    return ns["face_residue"](room, voids=voids, segments=segments, arcs=arcs, unit_m=u, floor_points=doors)


def _b(r, ox, oy):
    return box(ox + r[0], oy + r[1], ox + r[2], oy + r[3])


def _coords(g, ox, oy):
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or not hasattr(p, "exterior"):
            continue
        out.append([(round(x - ox, 3), round(y - oy, 3)) for x, y in list(p.exterior.coords)[:-1]])
    return out


def run(boq, arch, extra):
    u = arch["run"]["unit_m"]
    room = next(r for r in arch["rooms"] if r["room_id"] == ROOM)
    voids = []
    for v in arch["run"].get("double_height") or ():
        if v.get("state") == "APPLIED" and v["floor"] == room["floor"]:
            dx, dy = v["offset"]["dx"], v["offset"]["dy"]
            voids.append({"void_id": v["void_id"], "corners": [(x - dx, y - dy) for x, y in v["window"]]})
    doors = []
    for o in arch["openings"]:
        c = (o.get("position") or {}).get("centre_m")
        if c and ROOM in (o.get("rooms") or ()):
            doors.append((c[0] / u, c[1] / u))
    rec = _residue_with_geometry(room, voids, extra["segments"], extra["arcs"], u, doors)
    g = rec.pop("_geom")
    F, V, T_own, T_below, held = g["F"], g["V"], g["T_own"], g["T_below"], g["held"]
    ox, oy = F.bounds[0], F.bounds[1]
    cg = {k: unary_union(v) if v else Polygon() for k, v in (g["cat_geoms"] or {}).items()}
    VR, SF, SE = cg.get("VOID_RESIDUE", Polygon()), cg.get("STAIR_FOOTPRINT", Polygon()), \
        cg.get("SIDE_ELEMENT_UNSETTLED", Polygon())
    floor_low = F.difference(V).difference(T_own).difference(T_below).difference(VR).difference(SF) \
        .difference(SE).difference(held)
    # flights by id
    fl = {}
    for f in room["symbols_inside"]["stair_flights"]:
        P = unary_union([SFR._poly(q, u) for q in f["tread_quads"]]).intersection(F).difference(V)
        fl[f["flight_id"].split(":")[-1]] = {"g": P, "below": bool(f.get("drawn_on_plan_below")), "kind": f["kind"]}
    taken = Polygon()

    def piece(g):
        nonlocal taken
        g = g.difference(taken)
        taken = unary_union([taken, g])
        return g

    rows = []
    geoms = []

    def add(row_id, name, cat, g, finish, line, status, rule, note=""):
        rows.append({"row": row_id, "space": name, "category": cat, "m2": round(g.area, 4), "finish": finish,
                     "boq_line": line, "status": status, "rule": rule, "note": note,
                     "polygons_local_m": json.dumps(_coords(g, ox, oy))})
        geoms.append(g)

    # porcelain rows (floor cells inside each printed rectangle); landing first so it is taken once
    add("P-LD", "main-stair arrival landing (120 + 10 + 120) x 195 at +5.50", "MARBLE_LANDING",
        piece(floor_low.intersection(_b(LANDING, ox, oy))), "marble", "stair marble: new element ST-MS-LD-1F",
        "MEASURED (finish: owner Q-66 B)", "owner Q-66 B, UP-STAIR-005, Q-56 A (own row)")
    add("P-LV", "living 480 x 520 less the round-stair box", "PORCELAIN",
        piece(floor_low.intersection(_b(LIVING, ox, oy))), "porcelain", "FIN.FLOOR.PORCELAIN 1F living",
        "PROVISIONAL finish (Q-56 A)", "owner Q-56 A, arch_floor FLOOR AREA RECONCILIATION")
    add("P-CO", "corridor by the void 587 x 120", "PORCELAIN", piece(floor_low.intersection(_b(CORRIDOR, ox, oy))),
        "porcelain", "FIN.FLOOR.PORCELAIN 1F corridor", "PROVISIONAL finish (Q-56 A)", "owner Q-56 A")
    add("P-CN", "connector by the lift 130 x 125 + 237 x 120", "PORCELAIN",
        piece(floor_low.intersection(unary_union([_b(r, ox, oy) for r in CONNECTOR]))), "porcelain",
        "FIN.FLOOR.PORCELAIN 1F connector", "PROVISIONAL finish (Q-56 A)", "owner Q-56 A")
    rest = piece(floor_low)
    add("P-XX", "floor cells outside the four printed rectangles", "PORCELAIN", rest, "porcelain",
        "FIN.FLOOR.PORCELAIN 1F (unassigned)", "CHECK", "owner Q-56 A")
    # held pieces
    add("H-D13", "foot of the east flight 1.15 x 0.35 (designer D-13)", "HELD", piece(held), "marble in every reading "
        "(landing or flight; Q-66 B, UP-STAIR-005)", "none until D-13 / stair ledger", "HELD",
        "UP-QTY-STATUS-001, Q-66 B", "never porcelain under Q-66 B; may already be the 12th tread of the GF->1F "
        "upper flight in the marble table (12 treads counted, 10 drawn + this strip)")
    add("H-D23", "closed 0.05 x 2.35 element beside the arriving round-stair flight (designer D-23)", "HELD",
        piece(SE), "porcelain if floor (living row), else none", "none until D-23", "HELD", "UP-QTY-STATUS-001")
    # void, treads, residue
    add("V-01", "outlined void (open to below)", "VOID", piece(V), "none", "none (not floor)", "DEDUCTED",
        "arch_floor void rule")
    for fid in sorted(fl):
        f = fl[fid]
        add(f"T-{fid}", f"treads of flight {fid} ({f['kind'].lower()}, {'plan below' if f['below'] else 'own'})",
            "STAIR_TREADS", piece(f["g"]), "marble", "stair marble (flight lines)", "DEDUCTED from porcelain",
            "UP-STAIR-005")
    add("R-VR", "opening residue inside the printed 587 x 400 opening (touches the void)", "VOID_RESIDUE",
        piece(VR), "none", "none (open to below)", "DEDUCTED", "UP-STAIR-005 / opening")
    add("R-LC", "end of the well between the flights inside the printed landing (CAD closing line 0.05 short of the "
        "printed 195 edge: balustrade end)", "STAIR_FOOTPRINT", piece(SF.intersection(_b(LANDING, ox, oy))),
        "none in the drawn reading; marble if the printed landing 4.875 is taken", "landing (printed reading) / none",
        "DEDUCTED from porcelain", "UP-STAIR-005, Q-66 B")
    for rid, name, rect, line in (
            ("R-NB", "turn of the dog-leg outside the winder treads (square S1 + winder corner)", NORTH_BAND,
             "stair marble ST-MS2-LD (half landing 250 x 125, printed) / winder turn"),
            ("R-GP", "gap between the flights (drawn 0.20, printed 10)", GAP, "stair well: 2 x 0.05 under the printed "
             "120 flight widths, rest none"),
            ("R-RQ", "round-stair quarter landing inside the living rectangle", RS_QUARTER,
             "stair marble ST-RS-LD (HELD: size not printed)"),
            ("R-RE", "round-stair arrival edge strip", RS_EDGE, "stair marble (round stair, HELD)")):
        add(rid, name, "STAIR_FOOTPRINT", piece(SF.intersection(_b(rect, ox, oy))), "marble or none (stair)", line,
            "DEDUCTED from porcelain", "UP-STAIR-005")
    add("R-SF", "other stair-footprint cells (well foot, slivers along the curved flight)", "STAIR_FOOTPRINT",
        piece(SF), "stair", "stair (no porcelain)", "DEDUCTED", "UP-STAIR-005")
    left = F.difference(taken)
    add("Z-00", "face not in any category (must be 0)", "CHECK", left, "-", "-", "CHECK", "-")
    face = F.area
    tot = sum(r["m2"] for r in rows if r["category"] != "CHECK" or r["row"] == "P-XX")
    by = {}
    for r in rows:
        by[r["category"]] = round(by.get(r["category"], 0.0) + r["m2"], 4)
    # pairwise overlaps of all the row geometries (exactly once) and their union against the face
    ov = 0.0
    for i in range(len(geoms)):
        for j in range(i + 1, len(geoms)):
            ov += geoms[i].intersection(geoms[j]).area
    land = _b(LANDING, ox, oy)
    summary = {
        "face_m2": round(face, 4), "rows_sum_m2": round(tot, 4), "face_minus_rows_m2": round(face - tot, 4),
        "unassigned_m2": round(left.area, 6), "pairwise_overlap_of_row_geometries_m2": round(ov, 6),
        "union_of_rows_vs_face_m2": round(face - unary_union(geoms).area, 6),
        "by_category_m2": by,
        "engine_floor_low_m2": rec["floor_net_low_m2"], "engine_floor_high_m2": rec["floor_net_high_m2"],
        "landing_rect_m2": round(land.area, 4),
        "landing_rect_in_face_m2": round(land.intersection(F).area, 4),
        "landing_rect_in_void_treads_residue_held_m2": round(land.intersection(unary_union(
            [V, T_own, T_below, VR, SF, SE, held])).area, 6),
        "landing_rect_in_floor_low_m2": round(land.intersection(floor_low).area, 4),
        "flights": {k: {"m2": round(v["g"].area, 4), "below": v["below"], "kind": v["kind"],
                        "bounds_local": [round(v["g"].bounds[0] - ox, 3), round(v["g"].bounds[1] - oy, 3),
                                         round(v["g"].bounds[2] - ox, 3), round(v["g"].bounds[3] - oy, 3)]}
                    for k, v in fl.items()},
    }
    lo = rec["floor_net_low_m2"]
    hi = rec["floor_net_high_m2"]
    d13 = next(r["m2"] for r in rows if r["row"] == "H-D13")
    d23 = next(r["m2"] for r in rows if r["row"] == "H-D23")
    ld = next(r["m2"] for r in rows if r["row"] == "P-LD")
    summary["q66b"] = {
        "porcelain_low_m2": round(lo - ld, 4),
        "porcelain_high_as_owner_17_54_m2": round(hi - ld, 4),
        "porcelain_high_with_D13_never_porcelain_m2": round(lo - ld + d23, 4),
        "landing_marble_m2": ld, "landing_marble_if_D13_landing_m2": round(ld + d13, 4),
    }
    return rows, summary, rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    boq, arch, extra = pickle.load(open(a.v29, "rb"))
    rows, summary, rec = run(boq, arch, extra)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "LIVING_1F_ROWS_Q66B.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "living_1f_q66b_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for r in rows:
        print(f"{r['row']:6} {r['category']:16} {r['m2']:8.4f}  {r['space']}")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
