"""T-014 reproduction (research only, not a method): the facade run of each floor of a plan DXF three ways.

    python3 -I research/agents_t014/alsenan_facade_check.py <plan.dxf> <out_dir> [facts.json]

1. the released engine outline (ARCH_TAKEOFF_V2.9 facade, unchanged in V2.10 .. V2.12), captured from the run;
2. FACADE_GAP_CLOSURE_V1 recess_closures() on that same outline (D-N10-01);
3. an independent outline: tools/indep_reader faces (its 0.30 - 2.60 m closures and curved closures) plus
   FACADE_GAP_CLOSURE_V1 glazed_gap_closures() over 2.60 m and glass_chain_closures() (D-N10-02).
Prints lengths, rooms enclosed and closures with their widths only: no coordinates, no names. The drawing stays
outside the repository (Drive, read-only). Layer roles as T-016a: 1=WALL D=DOOR W=WINDOW S-COL.BON=COLUMN."""
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v29 as V29                                   # noqa: E402
from engine.source import facade_gap_closure as G                          # noqa: E402

ROLES = {"1": "WALL", "D": "DOOR", "W": "WINDOW", "S-COL.BON": "COLUMN"}


def engine_run(dxf, out, facts):
    cap = []
    orig = V29.facade_outlines

    def patched(arr, unit_m, min_space_m2):
        res = orig(arr, unit_m, min_space_m2)
        cap.append((arr, unit_m, res))
        return res
    V29.facade_outlines = patched
    from tools import urban_boq_m9 as M
    argv = ["arch", "--drawings", str(dxf), "--out", str(out), "--method", "ARCH_TAKEOFF_V2.9", "--no-svg",
            "--no-m9-xlsx"] + (["--facts", str(facts)] if facts else [])
    try:
        M.main(argv)
    except SystemExit:
        pass
    V29.facade_outlines = orig
    return cap


def main():
    dxf, out = Path(sys.argv[1]), Path(sys.argv[2])
    facts = sys.argv[3] if len(sys.argv) > 3 else None
    cap = engine_run(dxf, out, facts)
    fac = json.loads((out / "FACADE.json").read_text())
    walls = json.loads((out / "ARCH_WALLS.json").read_text())["floors"]
    wt = {f["floor"]: {s: float(w["t_m"]) for w in f["walls"] for s in w["source_ids"]} for f in walls}
    from tools.indep_reader import Drawing, WALL, COLUMN, WINDOW, GRID_M
    import shapely
    from shapely.geometry import box, LineString, Polygon
    from shapely.ops import polygonize, unary_union
    D = Drawing(dxf, roles=ROLES, curved_closures=True)
    plan = json.loads((out / "ARCH_PLAN.json").read_text())
    rooms = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    for fl in fac["floors"]:
        floor = fl["floor"]
        main_ol = fl["outlines"][0]
        per = main_ol["perimeter_m"]
        hit = None
        for arr, u, _res in cap:
            for k, f in enumerate(arr.faces):
                if f["area"] <= 0 and f["cycle"] and abs(V29._outline(arr, k, u)["perimeter_m"] - per) < 1e-6:
                    hit = (arr, k, u)
                    break
            if hit:
                break
        arr, k, u = hit
        reg = next(r for r in plan["regions"] if r["floor"] == floor)
        B = box(*[v * D.k for v in reg["box"]])
        inb = lambda pts: all(B.contains(shapely.geometry.Point(p)) for p in pts)      # noqa: E731
        segs = [s for s in D._segments((WALL, COLUMN)) if inb(s[:2])]
        wins = [p["pts"] for p in D.pieces(role=WINDOW) if inb(p["pts"])]
        gl = [(a, b) for p in D.pieces(role=WINDOW) if inb(p["pts"]) and p["straight"]
              for a, b in zip(p["pts"], p["pts"][1:])]
        rc = G.recess_closures(G.ring_from_arrangement(arr, k, u, wt.get(floor)), glazing=gl)
        print(f"== {floor}: engine run {per:.6f} m; FACADE_GAP_CLOSURE_V1 {rc['state']} {rc['closed_m']:.6f} m"
              + (f" range {rc['range_m']}" if rc["range_m"] else ""))
        for r in rc["recesses"]:
            print(f"   {r['kind']} {r['state']}: walked {r['path_m']:.6f} m, chord {r['chord_m']:.6f} m, depth "
                  f"{r['depth_m']:.3f} m, wall {r['wall_t_m']}, glazing over the chord {r['glazing_cover']:.3f}, "
                  f"beside a column {r['beside_column']}: {r['why'][:70]}")
        D.faces()
        gaps = G.glazed_gap_closures([(a, b) for a, b, st in segs if st], wins, min_gap_m=2.60)
        chains = G.glass_chain_closures([(a, b) for a, b, _ in segs], wins)
        add = [c for g in gaps for c in g["closure"]] + [ln for c in chains["closed"] for ln in c["lines"]]
        print(f"   gaps over 2.60 m: " + ", ".join(f"{g['width_m']:.3f} {g['state']}" for g in gaps))
        print(f"   glass chains joining two walls: {[c['length_m'] for c in chains['closed']]}")
        pts = [Polygon(r["polygon_m"]).representative_point() for r in rooms if r["floor"] == floor]
        for name, extra in (("reader alone", []), ("reader + FACADE_GAP_CLOSURE_V1", add)):
            geo = [LineString([a, b]) for a, b, _ in segs] + [LineString([a, b]) for a, b in D._closure_lines] + \
                  [LineString([a, b]) for a, b in extra]
            fs = [f for f in polygonize(shapely.unary_union(geo, grid_size=GRID_M)) if f.area > 1e-6 and B.contains(f)]
            uu = unary_union(fs)
            polys = list(uu.geoms) if uu.geom_type == "MultiPolygon" else [uu]
            n, area, L = max((sum(1 for p in pts if g.contains(p)), g.area, g.exterior.length) for g in polys)
            state = "ESTABLISHED" if n == len(pts) else "NOT ESTABLISHED (leaks)"
            print(f"   independent outline, {name}: {state}, rooms {n} / {len(pts)}, plate {area:.6f} m2, "
                  f"run {L:.6f} m (engine plate {main_ol['plate_m2']:.6f} m2)")


if __name__ == "__main__":
    main()
