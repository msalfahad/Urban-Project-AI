"""T-125 read-only Alsenan capture: one ARCH_TAKEOFF run, and per floor the inputs MASONRY_CENTRELINE_V2 needs (the wall
records, the openings, the wall stage's own column outlines in metres, and the floor's entities with their layer roles).
Usage (Python 3.11; the drawing and the pickle stay outside the clone):
    python3 -I research/agents_t125/alsenan_v2_dump.py <P7757.dxf> --out <scratch>/t125_inputs.pkl [--method ARCH_TAKEOFF_V2.12]
Writes only to --out (outside the repository)."""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", default="ARCH_TAKEOFF_V2.12")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    from engine.source import arch_walls as AW
    calls, orig = [], AW.walls

    def wrap(ents, roles, unit_m, faces, openings=(), columns=(), **kw):
        polys = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)] for x0, y0, x1, y1 in columns] + \
                [list(q) for q in kw.get("column_polys") or ()]
        r = orig(ents, roles, unit_m, faces, openings, columns, **kw)
        calls.append((r, [[(x * unit_m, y * unit_m) for x, y in q] for q in polys], ents, roles, unit_m))
        return r
    AW.walls = wrap
    try:
        try:
            _b, arch, _e = M.arch_compute(a.drawing, method=a.method)
        except M.CompletenessFailed as ex:
            arch = ex.arch
    finally:
        AW.walls = orig
    out = {"method": a.method, "floors": {}}
    for wf in arch.get("walls") or ():
        hit = [c for c in calls if c[0].get("walls") is wf.get("walls")]
        if len(hit) != 1:
            raise SystemExit(f"floor {wf.get('floor')}: the wall-stage call is not unique ({len(hit)})")
        _r, cols, ents, roles, unit_m = hit[0]
        fl = wf.get("floor")
        out["floors"][fl] = {"walls": wf.get("walls"), "columns_m": cols, "ents": ents, "roles": roles,
                             "unit_m": unit_m,
                             "openings": [o for o in arch.get("openings") or () if o.get("floor") == fl]}
    pickle.dump(out, open(a.out, "wb"))
    for fl, f in out["floors"].items():
        print(fl, len(f["walls"]), "walls", len(f["openings"]), "openings", len(f["columns_m"]), "columns")


if __name__ == "__main__":
    main()
