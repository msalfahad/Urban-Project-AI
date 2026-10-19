"""T-077 read-only runner: the opening omission guard on one architectural plan DXF (ARCH_TAKEOFF_V2.9 front end).

Not imported by any engine, tool or method file. Writes only the --out file (counts, metres, ids; no coordinates).

    python3 -I research/agents_t077/run_guard.py DRAWING.dxf RUN_DIR --out RESULT.json

RUN_DIR is the output folder of `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9` on the same drawing (its
DOOR_SCHEDULE.json gives the engine door elements). The plan frames, layer roles and openings are those of the
method's own run: arch_rooms.spaces is wrapped (in this process only) to keep each frame's entities and result; the
first result per frame (the main run, not a review scenario) is guarded. Printed dimensions are read with ezdxf.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import ezdxf  # noqa: E402

from engine.source import arch_rooms as AR  # noqa: E402
from engine.source import opening_omission_guard as G  # noqa: E402
from tools import urban_boq_m9 as M9  # noqa: E402


def _dims(path):
    doc = ezdxf.readfile(path)
    out = []
    for d in doc.modelspace().query("DIMENSION ARC_DIMENSION"):
        try:
            v = d.get_measurement()
        except Exception:                                    # noqa: BLE001 - a dimension without a measurement
            continue
        p1, p2 = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        if p1 is None or p2 is None or not isinstance(v, float):
            continue
        if d.dxftype() == "ARC_DIMENSION":
            # the arc length from the dimension's own geometry (its stored measurement carries the text scale)
            c = d.dxf.get("defpoint4")
            a0, a1 = d.dxf.get("start_angle"), d.dxf.get("end_angle")
            if c is None or a0 is None or a1 is None:
                continue
            r = ((p1.x - c.x) ** 2 + (p1.y - c.y) ** 2) ** 0.5
            sweep = (a1 - a0) % (2 * 3.141592653589793)
            out.append({"id": d.dxf.handle, "kind": "ARC", "value_du": r * sweep, "p1": (p1.x, p1.y),
                        "p2": (p2.x, p2.y), "centre": (c.x, c.y), "stored_measurement": float(v)})
        elif (d.dxf.get("dimtype", 0) & 7) in (0, 1):        # rotated / aligned linear dimensions
            out.append({"id": d.dxf.handle, "kind": "LINEAR", "value_du": float(v), "p1": (p1.x, p1.y),
                        "p2": (p2.x, p2.y), "centre": None})
    return out


def _in(box, p):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def run(dxf, run_dir):
    cap = []
    orig = AR.spaces

    def spaces(ents, roles, u, **kw):
        S = orig(ents, roles, u, **kw)
        cap.append({"region_id": kw.get("region_id"), "ents": ents, "roles": roles, "u": u, "S": S})
        return S
    AR.spaces = spaces
    try:
        M9.arch_compute(str(dxf), method="ARCH_TAKEOFF_V2.9")
    finally:
        AR.spaces = orig
    plan = json.loads((Path(run_dir) / "ARCH_PLAN.json").read_text(encoding="utf-8"))
    box_of = {r["floor"]: r["box"] for r in plan["regions"]}
    els = json.loads((Path(run_dir) / "DOOR_SCHEDULE.json").read_text(encoding="utf-8"))["doors"]["elements"]
    dims = _dims(str(dxf))
    seen, frames = set(), []
    for c in cap:
        rid = c["region_id"]
        if rid in seen:
            continue
        seen.add(rid)
        floor = rid.split(":")[-1]
        roles, ents, S, u = c["roles"], c["ents"], c["S"], c["u"]
        win = {l for l, r in roles.items() if r == "WINDOW"}
        wall = {l for l, r in roles.items() if r == "WALL"}
        door = {l for l, r in roles.items() if r == "DOOR"}
        glazing = {"segments": [s for s in ents["segments"] if s["layer"] in win],
                   "arcs": [a for a in ents["arcs"] if a["layer"] in win]}
        cols = [[(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])] for b in S["column_boxes"]] + \
               [list(p) for p in S.get("column_polys") or ()]
        box = box_of.get(floor)
        fdims = [d for d in dims if box is None or _in(box, d["p1"])]
        res = G.guard(S["openings"], glazing, swings=AR.door_swings(ents, door, u, path=True),
                      door_elements=[e for e in els if e["floor"] == floor],
                      walls=[s for s in ents["segments"] if s["layer"] in wall], columns=cols,
                      wall_arcs=[a for a in ents["arcs"] if a["layer"] in wall], dims=fdims, frame=floor, unit_m=u,
                      curved_rejected=(S.get("v29") or {}).get("rejected") or ())
        frames.append({"floor": floor, "summary": res["summary"], "rows": G.census_rows(res),
                       "held_windows": [{k: v for k, v in w.items() if k not in ("glazing_ids",)} |
                                        {"diagnosis": _strip(w["diagnosis"])}
                                        for w in res["windows"] if w["status"] == "HELD"],
                       "doors_without_block": [d for d in res["doors"] if "BLOCK" not in d["symbol"]]})
    return frames


def _strip(dg):
    dg = json.loads(json.dumps(dg))
    (dg.get("curved") or {}).pop("centre_du", None)
    return dg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    frames = run(a.dxf, a.run_dir)
    tot = {k: sum(f["summary"][k] for f in frames) for k in
           ("windows_drawn", "windows_engine", "windows_held", "doors_drawn", "doors_released", "doors_held",
            "swings_not_in_engine", "silent_omissions")}
    Path(a.out).write_text(json.dumps({"policy": G.POLICY, "totals": tot, "frames": frames}, indent=1,
                                      ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(tot))
    for f in frames:
        print(f["floor"], json.dumps(f["summary"]["held_by_cause"]), "doors", f["summary"]["door_symbols"])


if __name__ == "__main__":
    main()
