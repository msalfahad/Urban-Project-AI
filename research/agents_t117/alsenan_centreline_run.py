"""T-117 read-only Alsenan run: MASONRY_CENTRELINE_V1 (T-027) on the walls of one ARCH_TAKEOFF run.
Usage (Python 3.11; the drawing stays outside the clone):
    python3 -I research/agents_t117/alsenan_centreline_run.py <P7757.dxf> --out <scratch>/t117.json [--method ARCH_TAKEOFF_V2.12]
Writes only to --out (outside the repository). Per floor: the piece record per thickness, and per wall band its id,
thickness, run, ends, column cut and centreline in LOCAL metres (origin = lower-left corner of that floor's walls),
so a reviewer can find each band on the plan without the drawing's absolute coordinates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--method", default="ARCH_TAKEOFF_V2.12")
    ap.add_argument("--dump", help="optional pickle (outside the repository) of each floor's entities, for plotting")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    from engine.source import masonry_centreline as MC
    from engine.source import arch_walls as AW
    cols, orig = {}, AW.walls

    def wrap(ents, roles, unit_m, faces, openings=(), columns=(), **kw):
        # the column outlines the wall stage itself uses (boxes + turned polygons), kept per call in metres
        polys = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)] for x0, y0, x1, y1 in columns] + \
                [list(q) for q in kw.get("column_polys") or ()]
        r = orig(ents, roles, unit_m, faces, openings, columns, **kw)
        cols.setdefault("calls", []).append((r, [[(x * unit_m, y * unit_m) for x, y in q] for q in polys]))
        cols.setdefault("ents", []).append((r, ents, roles))
        return r
    AW.walls = wrap
    try:
        try:
            _b, arch, _e = M.arch_compute(a.drawing, method=a.method)
        except M.CompletenessFailed as ex:
            arch = ex.arch
    finally:
        AW.walls = orig
    calls = cols.get("calls") or []
    wl = arch.get("walls") or []
    # the AW.walls call whose wall list IS the one in arch["walls"] (the run makes several passes)
    by_floor = {}
    for wf in wl:
        hit = [c for r, c in calls if r.get("walls") is wf.get("walls")]
        if len(hit) == 1:
            by_floor[wf.get("floor")] = hit[0]
    if len(by_floor) != len(wl):
        by_floor = {}
    res_band = MC.measure_arch(arch)
    res = MC.measure_arch(arch, columns_by_floor=by_floor) if by_floor else res_band
    out = {"method": a.method, "policy": MC.policy_record(), "column_outlines_matched": bool(by_floor),
           "band_basis": {k: r.get("by_thickness") for k, r in res_band.items()}, "floors": {}}
    for wf in arch.get("walls") or ():
        fl = wf.get("floor")
        key = fl if fl in res and res[fl].get("floor") == fl and fl not in out["floors"] else f"{fl}|{wf.get('region_id')}"
        rec = res.get(key) or res.get(fl)
        walls = wf.get("walls") or []
        u = rec.get("unit_m") or 1.0
        pts = [p for w in walls for p in (w.get("centreline") or [])]
        x0 = min(p[0] for p in pts) if pts else 0.0
        y0 = min(p[1] for p in pts) if pts else 0.0
        bands = []
        for w in walls:
            c = w.get("centreline") or []
            bands.append({"wall_id": w.get("wall_id"), "t_m": w.get("t_m"), "family": w.get("family"),
                          "layer": w.get("layer"), "gross_lm": w.get("gross_lm"), "net_lm": w.get("net_lm"),
                          "columns_in_wall_lm": w.get("columns_in_wall_lm"), "curved": bool(w.get("curved")),
                          "stub": w.get("stub"), "kind": w.get("kind"), "external": w.get("external"),
                          "local_m": [[round((p[0] - x0) * u, 3), round((p[1] - y0) * u, 3)] for p in c]})
        out["floors"][key] = {"region_id": wf.get("region_id"), "unit_m": u, "origin_drawing": (x0, y0),
                              "columns_local_m": [[[round(x - x0 * u, 3), round(y - y0 * u, 3)] for x, y in q]
                                                  for q in by_floor.get(fl, ())],
                              "record": {k: rec.get(k) for k in ("status", "by_thickness", "junctions", "held",
                                                                 "pieces", "column_basis", "openings_listed")},
                              "bands": bands}
    if a.dump:
        import pickle
        dump = {}
        for wf in wl:
            e = [(en, ro) for r, en, ro in cols.get("ents") or () if r.get("walls") is wf.get("walls")]
            if e:
                x0, y0 = out["floors"][wf.get("floor")]["origin_drawing"]
                dump[wf.get("floor")] = {"ents": e[0][0], "roles": e[0][1], "origin": (x0, y0),
                                         "unit_m": out["floors"][wf.get("floor")]["unit_m"]}
        pickle.dump(dump, open(a.dump, "wb"))
    Path(a.out).write_text(json.dumps(out, indent=1, default=str))
    for k, f in out["floors"].items():
        print(k, f["record"]["status"], [(b["family"], b["masonry_run_lm"], b["held_max_lm"], b["pieces"])
                                         for b in f["record"]["by_thickness"]])


if __name__ == "__main__":
    main()
