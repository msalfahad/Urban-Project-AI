"""T-159 stage 1 (research only, not a method): the facade outline of each floor as edges, from the released engine.

    python3 -I research/agents_t159/t159_extract.py <plan.dxf> <out_dir> [facts.json]

Runs ARCH_TAKEOFF_V2.9 (facade unchanged in V2.10 .. V2.12) exactly as T-109 / T-014 do, captures each floor's plan
topology, and writes <out_dir>/t159_rings.json: per floor the outer ring as edges (metres, plan frame of that floor;
arcs with centre / radius / sweep and their TRUE length), the GF side-passage reading of FACADE_PASSAGE_WALLS_V1 (the
mouths it removes and the wall pieces it adds, owner Q-67 A), and the column rectangles (layer S-COL.BON) used to
register the floor frames on each other. Coordinates stay in the scratch output: the repository gets lengths only.
The drawing stays outside the repository (Drive, read-only)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t109"))

from engine.source import arch_v29 as V29                                   # noqa: E402
from engine.source import facade_passage_walls as P                         # noqa: E402
import alsenan_passage_check as T109                                        # noqa: E402

ORDER = ("GF", "1F", "2F")


def main():
    dxf, out = Path(sys.argv[1]), Path(sys.argv[2])
    facts = sys.argv[3] if len(sys.argv) > 3 else None
    out.mkdir(parents=True, exist_ok=True)
    cap = T109.engine_run(dxf, out, facts)
    fac = {f["floor"]: f for f in json.loads((out / "FACADE.json").read_text())["floors"]}
    plan = json.loads((out / "ARCH_PLAN.json").read_text())
    rooms = json.loads((out / "ARCH_ROOMS.json").read_text())["rooms"]
    unit = 0.001
    box = {r["floor"]: [v * unit for v in r["box"]] for r in plan["regions"]}
    lines, levels, cols, _ = T109.drawing_lines(dxf, unit)

    def inside(p, b):
        return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]
    res = {"floors": {}, "columns": {}, "levels": {}}
    for i, floor in enumerate(ORDER):
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
        edges = []
        for e, (ei, fw) in zip(ring, arr.faces[k]["cycle"]):
            ae = arr.edges[ei]
            rec = {"a": e["a"], "b": e["b"], "len_m": e["len_m"], "straight": e["straight"], "roles": e["roles"],
                   "opening": next((s.split("|", 1)[1] for s in e["sources"] if s.startswith("THR|")), None)}
            if not e["straight"]:
                pr = ae["prim"]
                rec.update(c=[pr.c[0] * u, pr.c[1] * u], r=pr.r * u)
            edges.append(rec)
        rec = {"perimeter_m": per, "edges": edges, "box": b,
               "second_outlines": [o["perimeter_m"] for o in fac[floor]["outlines"][1:]]}
        if floor == "GF":
            faces = P.faces_from_arrangement(arr, u)
            labels = [[r["point"][0] * unit, r["point"][1] * unit] for r in rooms
                      if r["floor"] == floor and r["class"] != "UNLABELLED"]
            other = [ln for ln in lines if inside(ln["a"], b) and inside(ln["b"], b)]
            nxt = ORDER[i + 1]
            dx, dy = box[nxt][0] - b[0], box[nxt][1] - b[1]
            above = [[[x - dx, y - dy] for x, y in o["ring_m"]] for o in fac[nxt]["outlines"]]
            pw = P.passage_walls(ring, faces, labels=labels, above=above, other_lines=other,
                                 levels=[x for x in levels if inside(x["at"], b)])
            rec["passage"] = {"state": pw["state"], "run_m": pw["run_m"], "walked_m": pw["walked_m"],
                              "wall_end_gaps": [g["edge_index"] for g in pw.get("wall_end_gaps", [])],
                              "passages": [{"state": p["state"],
                                            "mouth_edges": [m["edge_index"] for m in p["mouths"]],
                                            "mouths": [{"edge_index": m["edge_index"], "len_m": m["len_m"],
                                                        "cls": m["cls"], "opening": m["opening_id"]}
                                                       for m in p["mouths"]],
                                            "walls": p.get("walls", [])} for p in pw["passages"]]}
        res["floors"][floor] = rec
        res["columns"][floor] = [c for c in cols if inside(c[:2], b)]
        res["levels"][floor] = [x for x in levels if inside(x["at"], b)]
    (out / "t159_rings.json").write_text(json.dumps(res, indent=1))
    for f in ORDER:
        r = res["floors"][f]
        print(f"{f}: {len(r['edges'])} edges, run {r['perimeter_m']:.6f} m, columns {len(res['columns'][f])}")
    print("GF passage:", res["floors"]["GF"]["passage"]["state"], res["floors"]["GF"]["passage"]["run_m"])


if __name__ == "__main__":
    main()
