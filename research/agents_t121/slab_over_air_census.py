"""T-121 reproduction (research only, not a method): every place where a structural floor plate or roof slab sits
over outside air, measured from the drawings' own faces.

    python3 -I research/agents_t121/slab_over_air_census.py <plan.dxf> <structural.dxf> <arch_run_dir> <out.json>
        [--extra-air <json>]

<arch_run_dir> is the output folder of `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9` on <plan.dxf> (FACADE.json,
ARCH_PLAN.json, ARCH_ROOMS.json are read). --extra-air: a JSON list of {"floor", "polygon_m"} spaces that lie INSIDE a
floor's facade outline but are outside air (an open-air passage the outline bridges, T-109); polygons in the floor's
own plan frame, metres. Kept outside the repository with the drawings.

Steps (nothing here names a project, a layer of the plan or a coordinate):
1. route G (tools/urban_boq_m2.compute, conventions V6, the scored basis) runs on the structural DXF; the slab faces of
   every SLAB_PLAN sheet are captured with their class (PANEL, BEAM strip, COLUMN, OPENING, ...), thickness and the
   STR.CONC.SLAB line that measures each panel;
2. each slab sheet is placed on the architectural plan of the storey it covers by the translation that the most
   column outlines of equal size agree on (columns of the plan's column layer vs the sheet's COLUMN faces);
3. outside air below a slab = everything outside that storey's facade outline (ARCH_TAKEOFF_V2.9 FACADE.json), plus the
   --extra-air spaces, less the storey's own column outlines;
4. a soffit piece = (PANEL + BEAM-strip faces) inside outside air; strips narrower than 0.10 m are drafting offsets
   between the slab edge line and the facade line and are listed apart; faces labelled VOID are open, never soffit;
5. what stands above each piece: the next storey's rooms (wet / dry), its walls, or nothing (outside its outline).
Prints areas, volumes, states and line ids only."""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

NEXT = {"GF": "1F", "1F": "2F", "2F": "ROOF"}
MIN_WIDTH_M = 0.10           # narrower strips are drafting offsets, listed apart (a hand reading, not a rule)


def route_g_faces(structural):
    from tools import urban_boq_m2 as M2
    cap = {}
    orig = M2.route_generic

    def rg(*a, **k):
        cap["res"] = orig(*a, **k)
        return cap["res"]
    M2.route_generic = rg
    try:
        M2.compute([structural], conventions=str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"),
                   route="G", completeness=True)
    finally:
        M2.route_generic = orig
    res = cap["res"]
    D = res["generic"]["D"]
    sheets = {}
    for sid, rec in D["sheets"].items():
        if rec["sheet"]["role"] == "SLAB_PLAN":
            sheets[sid] = {"storey": rec["sheet"]["storey"], "faces": (rec.get("slab") or {}).get("faces", [])}
    lines = {}
    for it in res["items"]:
        if it["trade"] == "CONCRETE" and it["family"] == "SLABS":
            lines[it["component_id"].split(":")[-1]] = (it.get("category"), it.get("item_id"), it.get("base"))
    return sheets, lines


def plan_columns(dxf, layer="S-COL.BON"):
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    cols = []

    def walk(ents, d=0):
        for e in ents:
            t = e.dxftype()
            if t == "INSERT" and d < 4:
                try:
                    walk(e.virtual_entities(), d + 1)
                except Exception:           # noqa: BLE001
                    pass
            elif t == "LWPOLYLINE" and e.dxf.layer == layer:
                p = list(e.get_points("xy"))
                cols.append((min(q[0] for q in p), min(q[1] for q in p), max(q[0] for q in p), max(q[1] for q in p)))
    walk(doc.modelspace())
    return cols


def main():
    from shapely import affinity
    from shapely.geometry import Polygon, box as B
    from shapely.ops import unary_union
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("arch_run")
    ap.add_argument("out")
    ap.add_argument("--extra-air")
    a = ap.parse_args()
    run = Path(a.arch_run)
    fac = {f["floor"]: f for f in json.loads((run / "FACADE.json").read_text())["floors"]}
    regions = {r["floor"]: r["box"] for r in json.loads((run / "ARCH_PLAN.json").read_text())["regions"]}
    rooms = json.loads((run / "ARCH_ROOMS.json").read_text())["rooms"]
    unit = 0.001                                                    # the plan and the structural set are in mm
    cols = plan_columns(a.plan)
    sheets, lines = route_g_faces(a.structural)
    extra = json.loads(Path(a.extra_air).read_text()) if a.extra_air else []
    report = {"pieces": [], "slivers": {}, "alignment": {}}
    for sid, sh in sorted(sheets.items()):
        fl = sh["storey"]
        if fl not in regions:
            continue
        b = regions[fl]
        pc = [c for c in cols if b[0] <= c[0] <= b[2] and b[1] <= c[1] <= b[3]]
        sc = []
        for f in sh["faces"]:
            if f["class"] == "COLUMN" and len(f["polygon"]) >= 3:
                xs = [p[0] for p in f["polygon"]]
                ys = [p[1] for p in f["polygon"]]
                sc.append((min(xs), min(ys), max(xs), max(ys)))
        votes = collections.Counter()
        for p in pc:
            for s in sc:
                if abs((p[2] - p[0]) - (s[2] - s[0])) < 5 and abs((p[3] - p[1]) - (s[3] - s[1])) < 5:
                    votes[(round(p[0] - s[0]), round(p[1] - s[1]))] += 1
        (dx, dy), n = votes.most_common(1)[0]
        report["alignment"][sid] = {"storey": fl, "columns_agreeing": n, "plan_columns": len(pc), "sheet_columns": len(sc)}

        def poly(pts):
            return Polygon([((x + dx) * unit, (y + dy) * unit) for x, y in pts])
        fs = []
        for f in sh["faces"]:
            if len(f["polygon"]) < 3 or f["class"] not in ("PANEL", "BEAM", "JUNCTION_GAP", "OPEN_BOUNDARY"):
                continue
            P = poly(f["polygon"])
            fs.append((f, P if P.is_valid else P.buffer(0)))
        plate = unary_union([P.buffer(0.002) for f, P in fs]).buffer(-0.002)
        outline = Polygon(fac[fl]["outlines"][0]["ring_m"])
        world = B(*[v * unit for v in b]).buffer(50)
        air = world.difference(outline)
        for e in extra:
            if e["floor"] == fl:
                air = air.union(Polygon(e["polygon_m"]))
        air = air.difference(unary_union([B(*[v * unit for v in c]) for c in pc]))
        voids = unary_union([P for f, P in fs if "VOID" in (f.get("opening_labels") or [])] or [B(0, 0, 0, 0)])
        A = plate.intersection(air)
        core = A.buffer(-MIN_WIDTH_M / 2).buffer(MIN_WIDTH_M / 2).intersection(A)
        report["slivers"][sid] = round(A.difference(core).area, 3)
        up = NEXT.get(fl)
        up_outline = None
        if up in fac:
            ox = (regions[up][0] - b[0]) * unit
            up_outline = affinity.translate(Polygon(fac[up]["outlines"][0]["ring_m"]), -ox, 0)
        for g in sorted([g for g in getattr(core, "geoms", [core]) if g.area > 0.01], key=lambda g: -g.area):
            v = g.intersection(voids).area
            s = g.difference(voids)
            above = {}
            if up_outline is not None:
                for r in rooms:
                    if r["floor"] == up:
                        ox = (regions[up][0] - b[0]) * unit
                        ar = affinity.translate(Polygon(r["polygon_m"]), -ox, 0).intersection(s).area
                        if ar > 0.005:
                            above[f"{r['room_id']} [{r['kind']}]"] = round(ar, 3)
                out_up = s.difference(up_outline).area
            else:
                out_up = s.area
            panels, beam = [], 0.0
            for f, P in fs:
                ar = P.intersection(s).area
                if ar < 0.002 or "VOID" in (f.get("opening_labels") or []):
                    continue
                if f["class"] == "PANEL":
                    st = lines.get(f["face_id"], ("NO LINE", None, None))
                    panels.append({"face": f["face_id"], "m2": round(ar, 3), "t_m": f.get("t_m"), "t_basis": f.get("t_basis"),
                                   "line_state": st[0], "m3": round(ar * (f.get("t_m") or 0), 4)})
                else:
                    beam += ar
            rec = {"sheet": sid, "slab_over": fl, "soffit_m2": round(s.area, 3), "void_m2": round(v, 3),
                   "size_m": [round(s.bounds[2] - s.bounds[0], 3), round(s.bounds[3] - s.bounds[1], 3)],
                   "above_rooms_m2": above, "above_open_m2": round(out_up, 3),
                   "above_walls_m2": round(s.area - sum(above.values()) - out_up, 3),
                   "panel_m2": round(sum(p["m2"] for p in panels), 3), "panel_m3": round(sum(p["m3"] for p in panels), 4),
                   "beam_strip_m2": round(beam, 3), "panels": panels}
            report["pieces"].append(rec)
            print(f"{sid} over {fl}: soffit {rec['soffit_m2']:.3f} m2 (void {rec['void_m2']:.3f} excluded), size "
                  f"{rec['size_m']} m; above {above or '-'}, open above {rec['above_open_m2']:.3f}; slab panels "
                  f"{rec['panel_m2']:.3f} m2 = {rec['panel_m3']:.4f} m3 in lines "
                  f"{sorted({p['line_state'] for p in panels})}; beam strips {rec['beam_strip_m2']:.3f} m2")
        print(f"{sid}: strips narrower than {MIN_WIDTH_M} m (slab edge vs facade line) {report['slivers'][sid]:.3f} m2; "
              f"alignment {report['alignment'][sid]}")
    Path(a.out).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
