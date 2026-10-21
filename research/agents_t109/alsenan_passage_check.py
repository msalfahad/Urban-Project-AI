"""T-109 reproduction (research only, not a method): FACADE_PASSAGE_WALLS_V1 on the facade outline of each floor.

    python3 -I research/agents_t109/alsenan_passage_check.py <plan.dxf> <out_dir> [facts.json]

1. runs ARCH_TAKEOFF_V2.9 (facade unchanged in V2.10 .. V2.12) and captures each floor's plan topology;
2. builds the passage check inputs from the run and the drawing: the outline with the face behind each edge, the
   bounded faces, room label points (every room the run names), the lines of the layers that are not building layers
   (layer roles as T-014 / T-016a: 1 = WALL, D = DOOR, W = WINDOW, S-COL.BON = COLUMN), the printed level marks
   (layer LEVEL), and the plate above (the next floor's outline, moved by the offset between the two plan frames);
3. checks the frame offset independently: the columns of the two frames that coincide after the shift;
4. prints lengths, areas, counts and the state of each passage only: no coordinates, no names.
The drawing stays outside the repository (Drive, read-only)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v29 as V29                                   # noqa: E402
from engine.source import facade_passage_walls as P                         # noqa: E402

BUILDING_LAYERS = {"1", "D", "W", "S-COL.BON"}
ORDER = ("GF", "1F", "2F")


def engine_run(dxf, out, facts):
    cap = []
    orig = V29.facade_outlines

    def patched(arr, unit_m, min_space_m2):
        res = orig(arr, unit_m, min_space_m2)
        cap.append((arr, unit_m))
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


def drawing_lines(dxf, unit):
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    lines, levels, cols = [], [], []

    def walk(ents):
        for e in ents:
            t = e.dxftype()
            if t == "INSERT":
                try:
                    walk(e.virtual_entities())
                except Exception:          # noqa: BLE001  (a block that cannot be exploded is skipped, counted below)
                    lines.append(None)
            elif t == "LINE" and e.dxf.layer not in BUILDING_LAYERS:
                lines.append({"a": (e.dxf.start.x * unit, e.dxf.start.y * unit),
                              "b": (e.dxf.end.x * unit, e.dxf.end.y * unit), "layer": e.dxf.layer})
            elif t == "LWPOLYLINE":
                pts = [(x * unit, y * unit) for x, y in e.get_points("xy")]
                if e.dxf.layer == "S-COL.BON":
                    cols.append(tuple(round(v, 3) for v in (min(p[0] for p in pts), min(p[1] for p in pts),
                                                            max(p[0] for p in pts), max(p[1] for p in pts))))
                elif e.dxf.layer not in BUILDING_LAYERS:
                    if e.closed:
                        pts.append(pts[0])
                    lines.extend({"a": a, "b": b, "layer": e.dxf.layer} for a, b in zip(pts, pts[1:]))
            elif t == "TEXT" and e.dxf.layer == "LEVEL":
                levels.append({"at": (e.dxf.insert.x * unit, e.dxf.insert.y * unit), "value": e.dxf.text})
    walk(doc.modelspace())
    skipped = sum(1 for x in lines if x is None)
    return [x for x in lines if x is not None], levels, cols, skipped


def main():
    dxf, out = Path(sys.argv[1]), Path(sys.argv[2])
    facts = sys.argv[3] if len(sys.argv) > 3 else None
    cap = engine_run(dxf, out, facts)
    fac = {f["floor"]: f for f in json.loads((out / "FACADE.json").read_text())["floors"]}
    plan = json.loads((out / "ARCH_PLAN.json").read_text())
    rooms = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    unit = 0.001                                           # the run reads this plan in mm (INSUNITS 4)
    box = {r["floor"]: [v * unit for v in r["box"]] for r in plan["regions"]}
    lines, levels, cols, skipped = drawing_lines(dxf, unit)
    print(f"drawing: {len(lines)} non-building straight lines, {len(levels)} level marks, {skipped} blocks skipped")

    def inside(p, b):
        return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]
    for i, floor in enumerate(ORDER):
        if floor not in fac:
            continue
        b = box[floor]
        per = fac[floor]["outlines"][0]["perimeter_m"]
        hit = None
        for arr, u in cap:
            for k, f in enumerate(arr.faces):
                if f["area"] <= 0 and f["cycle"] and abs(V29._outline(arr, k, u)["perimeter_m"] - per) < 1e-6:
                    hit = (arr, k, u)
                    break
            if hit:
                break
        arr, k, u = hit
        ring = P.ring_with_inner(arr, k, u)
        faces = P.faces_from_arrangement(arr, u)
        labels = [[r["point"][0] * unit, r["point"][1] * unit] for r in rooms
                  if r["floor"] == floor and r["class"] != "UNLABELLED"]
        other = [ln for ln in lines if inside(ln["a"], b) and inside(ln["b"], b)]
        lv = [x for x in levels if inside(x["at"], b)]
        above = None
        nxt = ORDER[i + 1] if i + 1 < len(ORDER) else None
        if nxt in fac:
            dx, dy = box[nxt][0] - b[0], box[nxt][1] - b[1]
            above = [[[x - dx, y - dy] for x, y in o["ring_m"]] for o in fac[nxt]["outlines"]]
            here = {c for c in cols if inside(c[:2], b)}
            moved = {(round(c[0] - dx, 3), round(c[1] - dy, 3), round(c[2] - dx, 3), round(c[3] - dy, 3))
                     for c in cols if inside(c[:2], box[nxt])}
            print(f"== {floor}: plate above = {nxt} outline moved by the frame offset ({dx:.6f}, {dy:.6f}) m; "
                  f"{len(here & moved)} of {len(moved)} {nxt} columns fall exactly on {floor} columns")
        else:
            print(f"== {floor}: no plate above read (top plan); a single-mouth passage would stay HELD")
        r = P.passage_walls(ring, faces, labels=labels, above=above, other_lines=other, levels=lv)
        print(f"   engine run {r['walked_m']:.6f} m -> FACADE_PASSAGE_WALLS_V1 {r['state']} {r['run_m']:.6f} m"
              + (f" range {r['range_m']}" if r.get("range_m") else "")
              + f"; not building openings {r['not_building_openings']}")
        for g in r.get("wall_end_gaps", []):
            print(f"   wall-end gap kept in the run: {g['opening_id']} {g['len_m']:.3f} m")
        for p in r["passages"]:
            print(f"   passage {p['state']}: mouths " +
                  ", ".join(f"{m['opening_id']} {m['len_m']:.3f} m {m['cls']}"
                            + (f" (element {m['element_t_m']:.3f} m, layer {m['element_layer']})"
                               if m.get("element_t_m") else "") for m in p["mouths"]))
            if "walls_m" in p:
                print(f"      walls {p['walls_m']:.6f} m (in {len(p['walls'])} pieces; openings in them "
                      f"{p['openings_onto']}), mouths removed {p['mouths_m']:.6f} m, delta {p['delta_m']:+.6f} m; "
                      f"element inner face not counted {p['element_inner_face_m']:.3f} m")
                print(f"      space {p['space_area_m2']:.4f} m2: under the plate above {p['covered_m2']} m2, open to "
                      f"the sky {p['open_sky_m2']} m2; walls under the plate {p['covered_walls_m']:.3f} m; "
                      f"level marks inside {[x['value'] for x in p['levels']]}")
            print(f"      why: {p['why']}")


if __name__ == "__main__":
    main()
