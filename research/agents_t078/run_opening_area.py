"""T-078 runner (read-only): door and window areas of one plan run with engine/source/opening_area.py.

    python3 -I research/agents_t078/run_opening_area.py DRAWING.dxf RUN_DIR [--curved-basis BASIS] [--json OUT]

RUN_DIR is the output folder of `tools/urban_boq_m9.py arch` (ARCH_PLAN.json, ARCH_OPENINGS.json,
CURVED_OPENINGS.json, DOOR_SCHEDULE.json). Elevation views = the run's non-plan frames whose titles include ELEVATION
(ARCH_PLAN.json other_frames). Floors are put in one plan frame by the run's own cross-floor registration
(ARCH_OPENINGS.json run.cross_plan_stairs offsets, measured by the run from repeated stair geometry); a floor the
run did not register is left in its own frame (its openings then bind to no elevation unless its own widths map).
Writes nothing unless --json is given. No layer, block or project name is coded here either.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import opening_area as OA  # noqa: E402


def plan_openings(run):
    run = Path(run)
    plan = json.loads((run / "ARCH_PLAN.json").read_text(encoding="utf-8"))
    ops = json.loads((run / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))
    cur = json.loads((run / "CURVED_OPENINGS.json").read_text(encoding="utf-8"))
    doors = json.loads((run / "DOOR_SCHEDULE.json").read_text(encoding="utf-8"))["doors"]["elements"]
    unit_m = ops["run"]["unit_m"]
    floors = [r["floor"] for r in plan["regions"]]
    shift = {floors[0]: (0.0, 0.0)}                                  # registered = own - shift (drawing units)
    for c in ops["run"].get("cross_plan_stairs") or ():
        if c.get("lower") in shift and c.get("upper"):
            lx, ly = shift[c["lower"]]
            shift[c["upper"]] = (lx + c["offset"]["dx"], ly + c["offset"]["dy"])

    def reg(fl, x, y):
        sx, sy = shift.get(fl, (0.0, 0.0))
        return [x - sx * unit_m, y - sy * unit_m]

    out = []
    for o in ops["openings"]:
        if o["kind"] == "DOOR":
            continue                                                 # doors come from the door schedule below
        c = o["position"]["centre_m"]
        out.append({"id": o["opening_id"], "floor": o["floor"], "kind": o["kind"], "xy": reg(o["floor"], *c),
                    "axis": o["position"]["wall_axis"], "width_m": o["width_m"]})
    for e in doors:
        c = e.get("centre")
        out.append({"id": e.get("opening_id") or e["element_id"], "floor": e["floor"], "kind": "DOOR",
                    "xy": reg(e["floor"], c[0] * unit_m, c[1] * unit_m) if c else None, "axis": e.get("u"),
                    "width_m": e.get("structural_opening_width_m"), "door_class": e.get("boq_class"),
                    "element_id": e["element_id"], "section": e.get("section"),
                    "faces_outside": any(sd.get("kind") == "FACADE" for sd in e.get("sides") or ())})
    return out, floors, unit_m, plan, cur


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("run")
    ap.add_argument("--curved-basis", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    import ezdxf
    pos, floors, unit_m, plan, cur = plan_openings(a.run)
    run = Path(a.run)
    ops = json.loads((run / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))["openings"]
    by_id = {(o["floor"], o["opening_id"]): o for o in ops}
    for co in cur.get("curved_openings") or ():
        o = by_id.get((co["floor"], co["opening_id"]))
        p = next((q for q in pos if q["floor"] == co["floor"] and q["id"] == co["opening_id"]), None)
        if p is not None:
            p["curved"] = {"chord_m": co["bases_m"].get("CHORD"), "bases_m": co["bases_m"],
                           "run_basis": co.get("width_basis")}
        elif o is None:
            pos.append({"id": co["opening_id"], "floor": co["floor"], "kind": co["kind"], "xy": None, "axis": None,
                        "width_m": co["width_m"], "curved": {"chord_m": co["bases_m"].get("CHORD"),
                                                             "bases_m": co["bases_m"]}})
    pos = [p for p in pos if p.get("xy") is not None or p.get("width_m") is not None]
    for p in pos:
        if p.get("xy") is None:
            p["axis"] = None
    doc = ezdxf.readfile(a.dxf)
    views = [OA.read_view(doc, f["box"], unit_m, f["sheet_id"]) for f in plan.get("other_frames") or ()
             if any("ELEVATION" in str(t).upper() for t in f.get("titles_seen") or ())]
    res = OA.measure([p for p in pos if p.get("xy") is not None] + [p for p in pos if p.get("xy") is None],
                     views, floors=floors, curved_width_basis=a.curved_basis)
    for v in res["views"]:
        print("VIEW", v["view_id"], json.dumps(v["mapping"], default=str)[:400], dict(v["printed"]))
    for r in sorted(res["records"], key=lambda r: (r["floor"], r["kind"], r["id"])):
        print(r["floor"], r["id"], r["kind"], r["status"], r["reason"], r["width_m"], r["height_m"], r["area_m2"],
              r.get("material"), json.dumps(r["evidence"], default=str)[:300])
    print("SUMMARY", json.dumps(res["summary"]))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
